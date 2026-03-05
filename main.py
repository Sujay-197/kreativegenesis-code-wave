import uuid
import os
import json
import asyncio
from typing import Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import groq
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sqlalchemy.orm import Session
from database import SessionLocal, GeneratedApp

load_dotenv()

app = FastAPI(title="AppForge AI Simple Mode Backend")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory dictionary mapped by UUID
sessions = {}

# System prompt for Groq Llama 3 8B
LLAMA_BASE_PROMPT = """You are AppForge AI's Simple Mode Companion—a warm, insightful guide who genuinely understands the challenges small business owners, NGOs, educators, and independent operators face daily.

Your core mission: Help them visualize and build the perfect software solution by drawing out what they truly need, making them feel heard, and helping them see how this tool will make their life easier.

Tone & Approach:
- Be genuinely warm and conversational—like talking to a trusted mentor, not a form-filling bot
- Show that you truly understand their world and the specific challenges they mentioned
- Validate their struggles before asking the next question (e.g., "It sounds like managing orders is eating up your time...")
- Use their own language and context naturally throughout
- Help them see the bigger picture: how solving this problem will free up time, reduce stress, or unlock growth
- Make them feel like a smart decision-maker for thinking through these details

Question Guidelines:
1. Always reference something specific they said—builds trust and shows you're listening
2. Ask ONLY ONE exploratory question at a time; let it feel natural and inevitable
3. Lead with curiosity about their situation, not about technical requirements
4. Avoid buzzwords completely (no "database," "authentication," "REST APIs," "UI components," etc.)
5. Never use lists or multiple-choice—keep it like a conversation between two people
6. Subtly explore these 5 dimensions without them feeling like a checklist: Who uses this tool? What data matters most? How should it look and feel? What complex workflows run behind the scenes? Does this connect to other tools they use?

CRITICAL — DO NOT REPEAT:
- NEVER ask about a topic that has already been discussed or answered.
- Review the "Requirements gathered so far" section below. Any dimension marked as anything other than "Not yet discussed" has ALREADY been covered—move on to an uncovered dimension.
- If all 5 dimensions have some information, ask a deeper follow-up about the LEAST clear one, or ask if there's anything else they'd like to add.
- Each question must explore NEW ground. If the user has told you about their users, don't ask about users again. If they've described their data, don't ask about data again.

Connection Strategy:
- Reference their specific context (bakery → orders/inventory, school → student records, etc.)
- Acknowledge time/stress: "So you're juggling this manually right now..."
- Paint a picture: "Imagine being able to..."
- Show empathy for their constraints (budget, time, technical comfort)

Output ONLY your conversational response (the next question). Do not output JSON.
"""

def build_llama_prompt(current_requirements: dict) -> str:
    """Build the full Llama system prompt with current requirements context."""
    req_summary = "\n".join(
        f"  - {dim}: {val}" for dim, val in current_requirements.items()
    )
    return (
        LLAMA_BASE_PROMPT
        + f"\n\nRequirements gathered so far:\n{req_summary}\n\n"
        + "Focus your next question on a dimension that is still 'Not yet discussed' or needs more detail."
    )

# System prompt for HF Qwen 7B
QWEN_BASE_PROMPT = """You are a seasoned technical analyzer. Review the FULL conversation history and extract ALL of the user's requirements into 5 dimensions.

IMPORTANT RULES:
1. You MUST preserve and build upon previously extracted requirements. Never lose information that was discussed earlier in the conversation.
2. If a dimension was discussed earlier, keep that information AND add any new details from the latest messages.
3. Only write "Not yet discussed" if the topic has genuinely NEVER been mentioned in the entire conversation.
4. The confidence_score should reflect how complete the overall picture is (0-100). Increase it as more dimensions get filled in. If 4+ dimensions have real info, score should be at least 70.

You MUST output ONLY valid JSON matching this exact structure:
{
  "auth_and_users": "string",
  "data_and_storage": "string",
  "ui_complexity": "string",
  "business_logic": "string",
  "integrations": "string",
  "confidence_score": float (0.0 to 100.0)
}
Output ONLY the JSON object, with no markdown formatting, no code fences, no explanation.
"""

def build_qwen_prompt(previous_requirements: dict) -> str:
    """Build Qwen prompt with previous requirements for accumulation."""
    if all(v == "Not yet discussed" for v in previous_requirements.values()):
        return QWEN_BASE_PROMPT
    req_json = json.dumps(previous_requirements, indent=2)
    return (
        QWEN_BASE_PROMPT
        + f"\nPreviously extracted requirements (update and expand these, do NOT lose any info):\n{req_json}\n"
    )

# Pydantic Models for JSON structure
class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str

class RequirementsObject(BaseModel):
    auth_and_users: str = Field(description="Details regarding user accounts, roles, or authentication needs.")
    data_and_storage: str = Field(description="Details on what data needs to be stored and tracked.")
    ui_complexity: str = Field(description="Details on the user interface requirements and devices it will be used on.")
    business_logic: str = Field(description="Specific workflows, calculations, or logic needed.")
    integrations: str = Field(description="Any needed connections to outside services (e.g., email, payments).")

class GeminiChatResponse(BaseModel):
    next_question: str = Field(description="The friendly, empathetic companion's single question acknowledging their context.")
    requirements_object: RequirementsObject
    confidence_score: float = Field(description="Confidence value from 0.0 to 100.0.")

class ChatResponseOuter(GeminiChatResponse):
    session_id: str

class GenerateRequest(BaseModel):
    session_id: str | None = None
    requirements_object: RequirementsObject

class GenerateResponse(BaseModel):
    app_id: str
    message: str = "App generation started successfully."

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = groq.Groq(api_key=groq_api_key) if groq_api_key else None

# Initialize Hugging Face Inference Client
hf_token = os.getenv("HUGGINGFACE_API_KEY")
hf_client = InferenceClient(api_key=hf_token) if hf_token else None

# Prompt template for code generation; originally named for Mistral but now targets Qwen coder
CODE_PROMPT_TEMPLATE = """You are an expert Frontend Developer. Your task is to generate a fully functioning web application based on the following requirements:

Authentication/Users: {auth_and_users}
Data/Storage: {data_and_storage}
UI Complexity: {ui_complexity}
Business Logic: {business_logic}
Integrations: {integrations}

Generate the code using HTML, CSS (Tailwind via CDN is okay), and plain JavaScript. 
IMPORTANT: Your output MUST contain exactly three code blocks formatted as follows:

```html
<!-- HTML code here -->
```
```css
/* CSS code here */
```
```javascript
// JS code here
```

Do not include any explanations outside of the code blocks. Give me only the code.
"""

def extract_code_blocks(markdown_text: str) -> tuple[str, str, str]:
    """Extremely basic parser to extract HTML, CSS, and JS blocks from markdown."""
    import re
    
    html_match = re.search(r'```html\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    css_match = re.search(r'```css\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    js_match = re.search(r'```javascript\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    
    # Fallbacks for JS block which is sometimes marked as 'js'
    if not js_match:
        js_match = re.search(r'```js\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)

    html_content = html_match.group(1) if html_match else "<!-- HTML Generation Failed -->"
    css_content = css_match.group(1) if css_match else "/* CSS Generation Failed */"
    js_content = js_match.group(1) if js_match else "// JS Generation Failed"

    return html_content, css_content, js_content

def get_genai_response(conversation_history: list, current_requirements: dict) -> str:
    """Takes the history and accumulated requirements, returns a JSON response string."""
    if not groq_client:
        raise Exception("GROQ_API_KEY not configured")
    if not hf_client:
        raise Exception("HUGGINGFACE_API_KEY not configured")

    import re

    # 1. Fetch next question using Groq (Llama 3 8B) — with requirements context
    llama_prompt = build_llama_prompt(current_requirements)
    messages = [{"role": "system", "content": llama_prompt}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["parts"][0]})
        
    llama_response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages,  # type: ignore[arg-type]
        temperature=0.7,
        max_tokens=250
    )
    llama_content = llama_response.choices[0].message.content
    next_question = llama_content.strip() if llama_content else ""

    # 2. Extract requirements using HF Qwen 7B — with previous requirements for accumulation
    qwen_prompt = build_qwen_prompt(current_requirements)
    extraction_messages = [{"role": "system", "content": qwen_prompt}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        extraction_messages.append({"role": role, "content": msg["parts"][0]})
    extraction_messages.append({"role": "assistant", "content": next_question})
    
    qwen_response = hf_client.chat_completion(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=extraction_messages,  # type: ignore[arg-type]
        temperature=0.1,
        max_tokens=600
    )
    qwen_content = qwen_response.choices[0].message.content
    requirements_json_str = qwen_content.strip() if qwen_content else ""
    
    # Try to clean up output (strip markdown fences, etc.)
    json_match = re.search(r'\{.*\}', requirements_json_str, re.DOTALL)
    if json_match:
        requirements_json_str = json_match.group(0)
        
    try:
        req_data = json.loads(requirements_json_str)
    except Exception:
        req_data = {}

    # Merge: keep previous value if Qwen returned empty / "Not yet discussed" for a field
    merged_requirements = {}
    for key in ["auth_and_users", "data_and_storage", "ui_complexity", "business_logic", "integrations"]:
        new_val = req_data.get(key, "Not yet discussed")
        old_val = current_requirements.get(key, "Not yet discussed")
        # Keep old value if new one is empty or "Not yet discussed" but old one had real info
        if (not new_val or new_val == "Not yet discussed") and old_val and old_val != "Not yet discussed":
            merged_requirements[key] = old_val
        else:
            merged_requirements[key] = new_val if new_val else "Not yet discussed"

    # Calculate confidence: count how many dimensions have real info
    filled = sum(1 for v in merged_requirements.values() if v and v != "Not yet discussed")
    raw_confidence = float(req_data.get("confidence_score", 0.0))
    # Ensure confidence reflects actual coverage
    min_confidence = filled * 16.0  # 5 filled = at least 80
    confidence = max(raw_confidence, min_confidence)

    final_output = {
        "next_question": next_question,
        "requirements_object": merged_requirements,
        "confidence_score": min(confidence, 100.0)
    }
    
    return json.dumps(final_output)

@app.post("/api/chat/simple", response_model=ChatResponseOuter)
async def simple_mode_chat(request: ChatRequest):
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "history": [],
            "requirements": {
                "auth_and_users": "Not yet discussed",
                "data_and_storage": "Not yet discussed",
                "ui_complexity": "Not yet discussed",
                "business_logic": "Not yet discussed",
                "integrations": "Not yet discussed"
            }
        }
    
    history = sessions[session_id]["history"]
    current_requirements = sessions[session_id]["requirements"]
    history.append({
        "role": "user",
        "parts": [request.user_message]
    })
    
    try:
        loop = asyncio.get_event_loop()
        response_text = await asyncio.wait_for(
            loop.run_in_executor(None, get_genai_response, history, current_requirements),
            timeout=30.0
        )
        
        response_data = json.loads(response_text)
        
        history.append({
            "role": "model",
            "parts": [response_data.get("next_question", "")]
        })
        
        # Persist accumulated requirements in session
        if response_data.get("requirements_object"):
            sessions[session_id]["requirements"] = response_data["requirements_object"]
        
        # Inject our session_id to let the frontend persist it
        response_data["session_id"] = session_id
        
        return response_data
    except asyncio.TimeoutError:
        # Remove the unanswered user message so session stays clean
        history.pop()
        raise HTTPException(status_code=504, detail="AI response timed out. Please try again.")
    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            history.pop()
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment and try again.")
        # Remove broken message from history
        history.pop()
        raise HTTPException(status_code=500, detail=err)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat/reset")
async def reset_session(request: ChatRequest):
    if request.session_id in sessions:
        del sessions[request.session_id]
        return {"status": "session reset"}
    return {"status": "session not found"}

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_app(request: GenerateRequest, db: Session = Depends(get_db)):
    if not hf_client:
        raise HTTPException(status_code=500, detail="Hugging Face API key is missing.")
    
    # Format the prompt
    reqs = request.requirements_object
    prompt = CODE_PROMPT_TEMPLATE.format(
        auth_and_users=reqs.auth_and_users,
        data_and_storage=reqs.data_and_storage,
        ui_complexity=reqs.ui_complexity,
        business_logic=reqs.business_logic,
        integrations=reqs.integrations
    )
    
    try:
        # Generate with Qwen coder model instead of Mistral
        # Using Qwen/Qwen2.5-coder for improved code generation
        response = hf_client.chat_completion(
            model="Qwen/Qwen2.5-coder",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2
        )
        
        generated_text = response.choices[0].message.content
        
        # Parse blocks
        if not generated_text:
            raise Exception("No content received from model")
        html, css, js = extract_code_blocks(generated_text)  # type: ignore[arg-type]
        
        # Save to SQLite User database
        new_app = GeneratedApp(
            session_id=request.session_id,
            html_content=html,
            css_content=css,
            js_content=js
        )
        db.add(new_app)
        db.commit()
        db.refresh(new_app)
        
        app_id: str = new_app.id if isinstance(new_app.id, str) else str(new_app.id)
        return GenerateResponse(app_id=app_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"App generation failed: {str(e)}")

@app.get("/api/apps/{app_id}")
async def get_app(app_id: str, db: Session = Depends(get_db)):
    app_record = db.query(GeneratedApp).filter(GeneratedApp.id == app_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="App not found in database.")
    
    return {
        "id": app_record.id,
        "session_id": app_record.session_id,
        "html": app_record.html_content,
        "css": app_record.css_content,
        "js": app_record.js_content,
        "created_at": app_record.created_at
    }
