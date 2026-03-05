import os
import uuid
import json
import zipfile
import io
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API Keys
HF_API_KEY = os.getenv("HF_API_KEY")  # Single HF token — covers companion, analyzer, and code generation

app = FastAPI(title="AppForge AI Backend — Tailored Mode")

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
# structure: { session_id: { "history": [], "technical_spec": {}, "code": {} } }
sessions: Dict[str, Dict[str, Any]] = {}

# ── Pydantic models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class GenerateRequest(BaseModel):
    session_id: str

# ── System Prompts ─────────────────────────────────────────────────────────────

# Conversational companion — asks ONE question at a time (no JSON output)
LLAMA_PROMPT = """You are AppForge AI's Tailored Mode Companion. Your goal is to empower non-technical users (small business owners, NGOs, educators, etc.) by helping them plan software tools that solve their daily problems.
Think of yourself as a supportive, empathetic product consultant, not a technical interrogator.
Rules:
1. Always adapt your questions based on the user's previous responses. Use their context (e.g., if they are a bakery, mention cakes/orders).
2. Acknowledge and validate their situation before asking the next question.
3. Ask ONLY ONE gently exploratory question at a time.
4. DO NOT use technical buzzwords (e.g., database schema, auth providers, REST APIs, UI components).
5. DO NOT present long lists or multiple-choice questions. Keep it conversational.
6. Quietly figure out their requirements across 5 dimensions: Authentication & Users, Data & Storage, UI Complexity, Business Logic & Workflows, and External Integrations.
Output ONLY your conversational response (the next question). Do not output JSON.
"""

# Silent analyst — reads full history and extracts structured requirements as JSON
QWEN_PROMPT = """You are a seasoned technical analyzer. Review the conversation history and extract the user's requirements into 5 dimensions.
You MUST output ONLY valid JSON matching this exact structure:
{
  "auth_and_users": "string",
  "data_and_storage": "string",
  "ui_complexity": "string",
  "business_logic": "string",
  "integrations": "string",
  "confidence_score": float (0.0 to 100.0)
}
Specific details only. If unknown, write "Not yet discussed".
Output ONLY the JSON object, with no markdown formatting.
"""

# ── Session helpers ────────────────────────────────────────────────────────────

def get_or_create_session(session_id: Optional[str] = None) -> str:
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "history": [],
            "technical_spec": {
                "auth_and_users": "Not yet discussed",
                "data_and_storage": "Not yet discussed",
                "ui_complexity": "Not yet discussed",
                "business_logic": "Not yet discussed",
                "integrations": "Not yet discussed",
            },
            "code": None,
        }
    return session_id

# ── LLM Callers ────────────────────────────────────────────────────────────────

def _hf_token() -> str:
    """Return the HF API token."""
    if not HF_API_KEY:
        raise ValueError("No Hugging Face API key configured. Set HF_API_KEY in your .env file.")
    return HF_API_KEY


def call_qwen_companion(history: list, current_message: str) -> str:
    """
    Calls Mistral-7B-Instruct-v0.3 via HF Inference API acting as the conversational companion.
    Returns a plain-text follow-up question (no JSON).
    """
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {_hf_token()}"}

    # Build a minimal chat context for the model
    conversation = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history[:-1]  # exclude the just-appended user message; we pass it separately
    )

    prompt = (
        f"[INST] {LLAMA_PROMPT}\n\n"
        f"Conversation so far:\n{conversation}\n\n"
        f"Latest user message: {current_message} [/INST]"
    )

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.7}},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        generated = result[0]["generated_text"]
        # Strip the echoed prompt if the model includes it
        if "[/INST]" in generated:
            generated = generated.split("[/INST]")[-1].strip()
        return generated
    except Exception as e:
        print(f"Qwen Companion Error: {e}")
        return "I'd love to understand more — could you tell me a bit about who will be using this app and what they need to do in it?"


def call_qwen_analyzer(history: list) -> dict:
    """
    Calls Mistral-7B-Instruct-v0.3 via HF Inference API to silently analyze the full conversation and
    extract a structured technical spec as JSON.
    """
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {_hf_token()}"}

    conversation = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history
    )

    prompt = (
        f"[INST] {QWEN_PROMPT}\n\n"
        f"Full conversation:\n{conversation} [/INST]"
    )

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": 500, "temperature": 0.2}},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        generated = result[0]["generated_text"]
        if "[/INST]" in generated:
            generated = generated.split("[/INST]")[-1].strip()
        # Strip any accidental markdown fences
        generated = generated.replace("```json", "").replace("```", "").strip()
        return json.loads(generated)
    except Exception as e:
        print(f"Qwen Analyzer Error: {e}")
        return {
            "auth_and_users": "Not yet discussed",
            "data_and_storage": "Not yet discussed",
            "ui_complexity": "Not yet discussed",
            "business_logic": "Not yet discussed",
            "integrations": "Not yet discussed",
            "confidence_score": 0.0,
        }


def call_mistral(technical_spec: dict) -> dict:
    """
    Calls Mistral-7B-Instruct via HF Inference API to generate HTML/CSS/JS
    based on the extracted technical specification.
    """
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {_hf_token()}"}

    prompt = (
        "[INST] You are an expert web developer. Based on the following application specification, "
        "generate the complete source code for a functional web application using HTML, CSS (Tailwind allowed), "
        "and JavaScript. Provide the code in three clearly labelled blocks: HTML, CSS, and JS. "
        "Use modern best practices. Output code only — no explanations.\n\n"
        f"Specification:\n{json.dumps(technical_spec, indent=2)} [/INST]"
    )

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": 2000}},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        generated_text = result[0]["generated_text"]

        # Basic block extraction (robust regex can replace this in production)
        html_part = css_part = js_part = ""
        if "HTML" in generated_text:
            html_part = "<!-- Generated HTML -->\n" + generated_text
        else:
            html_part = generated_text

        return {"html": html_part, "css": css_part, "js": js_part}
    except Exception as e:
        print(f"Mistral API Error: {e}")
        return {
            "html": "<h1>App Generation Failed</h1><p>Please check backend console.</p>",
            "css": "",
            "js": "",
        }


# ── API Routes — Tailored Mode ─────────────────────────────────────────────────

@app.post("/chat/tailored")
async def chat_tailored_endpoint(req: ChatRequest):
    """
    Tailored Mode chat endpoint.
    - Qwen companion asks one empathetic question at a time.
    - Qwen analyzer silently updates the technical spec after every turn.
    """
    session_id = get_or_create_session(req.session_id)
    session = sessions[session_id]

    # Append user message to history
    session["history"].append({"role": "user", "content": req.message})

    # 1. Companion: generate the next conversational question
    next_question = call_qwen_companion(session["history"], req.message)

    # 2. Analyzer: silently extract / update the technical spec
    analyzed = call_qwen_analyzer(session["history"])
    confidence_score = analyzed.pop("confidence_score", 0.0)
    session["technical_spec"].update(analyzed)

    # Append assistant reply to history
    session["history"].append({"role": "assistant", "content": next_question})

    return {
        "session_id": session_id,
        "next_question": next_question,
        "technical_spec": session["technical_spec"],
        "confidence_score": confidence_score,
    }


@app.post("/generate/tailored")
async def generate_tailored_endpoint(req: GenerateRequest):
    """
    Tailored Mode generation endpoint.
    Passes the extracted technical spec to Mistral for code generation.
    """
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[req.session_id]
    generated_code = call_mistral(session["technical_spec"])
    session["code"] = generated_code

    return {"message": "Tailored app generated successfully", "code": generated_code}


@app.get("/download/{session_id}")
async def download_app_endpoint(session_id: str):
    """Download the generated app as a zip archive."""
    if session_id not in sessions or not sessions[session_id].get("code"):
        raise HTTPException(status_code=404, detail="Session or generated code not found")

    code_data = sessions[session_id]["code"]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", code_data.get("html", ""))
        zf.writestr("styles.css", code_data.get("css", ""))
        zf.writestr("script.js", code_data.get("js", ""))
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=appforge_tailored_{session_id[:8]}.zip"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)