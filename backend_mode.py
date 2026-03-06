import uuid
import os
import json
import asyncio
import zipfile
import io
import requests
import re
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import groq
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sqlalchemy.orm import Session
from database import SessionLocal, GeneratedApp
from orchestrator import run_pipeline, get_job_status, get_job_file, list_all_jobs, build_job_zip

load_dotenv()

app = FastAPI(title="AppForge AI Backend — Unified")

# CORS Setup — restrict origins in production via ALLOWED_ORIGINS env var
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in _allowed_origins.split(",")] if _allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory sessions for both modes
sessions: Dict[str, Dict[str, Any]] = {}

# API Keys
groq_api_key = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_API_KEY")

groq_client = groq.Groq(api_key=groq_api_key) if groq_api_key else None
hf_client = InferenceClient(api_key=hf_token) if hf_token else None


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: Optional[str] = None  # For Simple Mode
    message: Optional[str] = None  # For Tailored Mode


class RequirementsObject(BaseModel):
    problem_statement_or_domain: str = Field(default="Not yet discussed", description="What core problem the app solves and in which domain/context it will be used.")
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
    session_id: str
    requirements_object: Optional[RequirementsObject] = None


class DebugGenerateRequest(BaseModel):
    specification: Dict[str, str]


class DebugGenerateResponse(BaseModel):
    message: str
    code: Dict[str, str]


class GenerateResponse(BaseModel):
    app_id: Optional[str] = None
    message: str = "App generation started successfully."
    code: Optional[Dict[str, str]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-AGENT PIPELINE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class PipelineRequest(BaseModel):
    prompt: str = Field(description="Application description for the multi-agent pipeline.")
    provider: str = Field(default="groq", description="LLM provider: 'groq' or 'huggingface'.")


class PipelineResponse(BaseModel):
    job_id: str
    message: str = "Pipeline started. Poll /api/pipeline/status/{job_id} for progress."


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    detail: str = ""
    files: Optional[list[str]] = None
    project_dir: Optional[str] = None
    architecture: Optional[dict] = None
    prompt: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobFileResponse(BaseModel):
    job_id: str
    file_path: str
    content: str


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

SIMPLE_MODE_LLAMA_PROMPT = """You are AppForge AI's Simple Mode Companion—a warm, insightful guide who genuinely understands the challenges small business owners, NGOs, educators, and independent operators face daily.

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
6. Subtly explore these 6 dimensions without them feeling like a checklist: What problem/domain is this for? Who uses this tool? What data matters most? How should it look and feel? What complex workflows run behind the scenes? Does this connect to other tools they use?

CRITICAL — DO NOT REPEAT:
- NEVER ask about a topic that has already been discussed or answered.
- Review the "Requirements gathered so far" section below. Any dimension marked as anything other than "Not yet discussed" has ALREADY been covered—move on to an uncovered dimension.
- If all 6 dimensions have some information, ask a deeper follow-up about the LEAST clear one, or ask if there's anything else they'd like to add.
- Each question must explore NEW ground. If the user has told you about their users, don't ask about users again. If they've described their data, don't ask about data again.

Connection Strategy:
- Reference their specific context (bakery → orders/inventory, school → student records, etc.)
- Acknowledge time/stress: "So you're juggling this manually right now..."
- Paint a picture: "Imagine being able to..."
- Show empathy for their constraints (budget, time, technical comfort)

Output ONLY your conversational response (the next question). Do not output JSON.
"""

# Dimension labels for deficit tracking
_DIMENSION_LABELS = {
    "problem_statement_or_domain": "What problem this app solves and its domain/context",
    "auth_and_users": "Who will use this app (single user or multiple, any login needs)",
    "data_and_storage": "What information/data the app needs to track",
    "ui_complexity": "How the app should look and feel (views, layout, device)",
    "business_logic": "Rules, calculations, or workflows the app should handle automatically",
    "integrations": "Whether the app needs to connect to external services",
}


def _is_filled(val: str | None) -> bool:
    """Check if a requirement dimension has real info (not empty/placeholder)."""
    if not val:
        return False
    return val.strip().lower() not in ("not yet discussed", "n/a", "none", "unknown", "")


def _get_deficits(requirements: dict) -> list[str]:
    """Return list of dimension names that are still unfilled."""
    deficits = []
    for key, label in _DIMENSION_LABELS.items():
        val = requirements.get(key, "Not yet discussed")
        if not _is_filled(val):
            deficits.append(label)
    return deficits


def build_simple_llama_prompt(current_requirements: dict) -> str:
    """Build the full Llama system prompt with deficit-driven question targeting."""
    req_summary = "\n".join(
        f"  - {dim}: {val}" for dim, val in current_requirements.items()
    )

    deficits = _get_deficits(current_requirements)

    if deficits:
        deficit_block = (
            "\n\n⚠️ MISSING INFORMATION — Your next question MUST explore ONE of these gaps:\n"
            + "\n".join(f"  • {d}" for d in deficits)
            + "\n\nPick the most natural gap to ask about given what the user just told you. "
            "Do NOT ask about dimensions that already have information."
        )
    else:
        deficit_block = (
            "\n\nAll 6 dimensions have some information gathered. "
            "Ask if there's anything else they'd like to add, or a deeper follow-up on the least detailed dimension."
        )

    return (
        SIMPLE_MODE_LLAMA_PROMPT
        + f"\n\nRequirements gathered so far:\n{req_summary}"
        + deficit_block
    )

TAILORED_MODE_COMPANION_PROMPT = """You are AppForge AI's Tailored Mode Companion—a warm, insightful guide who genuinely understands the challenges small business owners, NGOs, educators, and independent operators face daily.

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
- Each question must explore NEW ground.

Connection Strategy:
- Reference their specific context (bakery → orders/inventory, school → student records, etc.)
- Acknowledge time/stress: "So you're juggling this manually right now..."
- Paint a picture: "Imagine being able to..."
- Show empathy for their constraints (budget, time, technical comfort)

Output ONLY your conversational response (the next question). Do not output JSON.
"""

def build_tailored_llama_prompt(current_spec: dict) -> str:
    """Build the full Tailored Mode prompt with current spec context."""
    req_summary = "\n".join(
        f"  - {dim}: {val}" for dim, val in current_spec.items()
        if dim != "confidence_score"
    )
    return (
        TAILORED_MODE_COMPANION_PROMPT
        + f"\n\nRequirements gathered so far:\n{req_summary}\n\n"
        + "Focus your next question on a dimension that is still 'Not yet discussed' or needs more detail."
    )

REQUIREMENTS_EXTRACTION_PROMPT = """You are a seasoned technical analyzer. Review the FULL conversation history and extract ALL of the user's requirements into 6 dimensions.

IMPORTANT RULES:
1. You MUST preserve and build upon previously extracted requirements. Never lose information that was discussed earlier in the conversation.
2. If a dimension was discussed earlier, keep that information AND add any new details from the latest messages.
3. Only write "Not yet discussed" if the topic has genuinely NEVER been mentioned in the entire conversation.
4. The confidence_score should reflect how complete the overall picture is (0-100). Increase it as more dimensions get filled in. If 4+ dimensions have real info, score should be at least 70.

You MUST output ONLY valid JSON matching this exact structure:
{
  "problem_statement_or_domain": "string",
  "auth_and_users": "string",
  "data_and_storage": "string",
  "ui_complexity": "string",
  "business_logic": "string",
  "integrations": "string",
  "confidence_score": float (0.0 to 100.0)
}
Output ONLY the JSON object, with no markdown formatting, no code fences, no explanation.
"""

def build_extraction_prompt(previous_requirements: dict) -> str:
    """Build extraction prompt with previous requirements for accumulation."""
    if all(v == "Not yet discussed" for k, v in previous_requirements.items() if k != "confidence_score"):
        return REQUIREMENTS_EXTRACTION_PROMPT
    req_json = json.dumps({k: v for k, v in previous_requirements.items() if k != "confidence_score"}, indent=2)
    return (
        REQUIREMENTS_EXTRACTION_PROMPT
        + f"\nPreviously extracted requirements (update and expand these, do NOT lose any info):\n{req_json}\n"
    )

CODE_GENERATION_PROMPT_WITH_TEMPLATE = """You are an expert Frontend Developer. You are given an SB Admin 2 (Bootstrap 4) dashboard TEMPLATE. Your job is to ADAPT this template into a new, fully working app that matches the requirements below.

## REQUIREMENTS:
Problem/Domain: {problem_statement_or_domain}
Authentication/Users: {auth_and_users}
Data/Storage: {data_and_storage}
UI Complexity: {ui_complexity}
Business Logic: {business_logic}
Integrations: {integrations}

## TEMPLATE FILES (your starting base — adapt, don't start from scratch):
{template_context}

## INSTRUCTIONS:
1. KEEP the template's SB Admin 2 layout: sidebar navigation, topbar, card-based content, Bootstrap 4 classes, gradient primary sidebar.
2. KEEP vendor CDN references to Bootstrap, jQuery, FontAwesome, Chart.js, DataTables — use these same paths:
   - vendor/fontawesome-free/css/all.min.css
   - css/sb-admin-2.min.css
   - vendor/jquery/jquery.min.js
   - vendor/bootstrap/js/bootstrap.bundle.min.js
   - vendor/jquery-easing/jquery.easing.min.js
   - js/sb-admin-2.min.js
   - vendor/chart.js/Chart.min.js (if charts needed)
   - vendor/datatables/jquery.dataTables.min.js + dataTables.bootstrap4.min.js (if tables needed)
3. CHANGE: page title, sidebar brand name, sidebar nav items, card content, table columns, form fields — all to match the required app.
4. CHANGE: JavaScript data models and logic — use localStorage for data persistence. Create proper CRUD operations for the entities specified.
5. If the app needs charts, adapt the chart-demo.js pattern with the correct labels/data for the new app.
6. If the app needs data tables, adapt the DataTables pattern from tables.html with the correct columns.
7. If login is needed, adapt login.html with working localStorage-based auth. If no login needed, skip it.
8. All functionality must work standalone — no server required. Use localStorage for all data persistence.

IMPORTANT: Your output MUST contain exactly three code blocks:

```html
<!-- Full single-page HTML including all vendor script/css references, sidebar, topbar, content area -->
```
```css
/* Any additional CSS beyond sb-admin-2 — custom styles for this specific app */
```
```javascript
// All app logic: data models, CRUD, charts, tables, form handling, localStorage persistence
```

Do not include any explanations outside of the code blocks. Give me only the code.
"""

CODE_GENERATION_PROMPT_NO_TEMPLATE = """You are an expert Frontend Developer. Your task is to generate a fully functioning web application based on the following requirements:

Problem/Domain: {problem_statement_or_domain}
Authentication/Users: {auth_and_users}
Data/Storage: {data_and_storage}
UI Complexity: {ui_complexity}
Business Logic: {business_logic}
Integrations: {integrations}

Generate the code using HTML, CSS (Tailwind via CDN is okay), and plain JavaScript.
Use localStorage or IndexedDB for data persistence on the frontend.
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


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE LOADING
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")


def _load_template_assets() -> dict[str, str]:
    """Read core template files from the template/ folder.
    Skips vendor libraries, SVG icons, and other bulky assets."""
    assets: dict[str, str] = {}
    if not os.path.isdir(TEMPLATE_DIR):
        return assets

    SKIP_DIRS = {"vendor", "node_modules", "scss", "less", "sprites", "svgs", "webfonts", "metadata", ".git"}
    ALLOWED_EXTS = {".html", ".css", ".js", ".py", ".sql", ".json"}
    SKIP_SUFFIXES = {".min.css", ".min.js", ".map", ".min.map"}

    for root, dirs, files in os.walk(TEMPLATE_DIR):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, TEMPLATE_DIR).replace("\\", "/")
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTS:
                continue
            if any(fname.lower().endswith(s) for s in SKIP_SUFFIXES):
                continue
            if fname == "package-lock.json":
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    assets[rel] = f.read()
            except Exception:
                pass
    return assets


def _build_asset_context(assets: dict[str, str]) -> str:
    """Format loaded template files into a prompt-friendly block."""
    if not assets:
        return ""

    PRIORITY = [
        "index.html", "login.html", "register.html", "tables.html",
        "charts.html", "cards.html", "blank.html", "404.html",
        "css/sb-admin-2.css", "js/sb-admin-2.js",
        "js/demo/chart-area-demo.js", "js/demo/chart-bar-demo.js",
        "js/demo/chart-pie-demo.js", "js/demo/datatables-demo.js",
    ]

    ordered_keys = []
    for p in PRIORITY:
        if p in assets:
            ordered_keys.append(p)
    for k in sorted(assets.keys()):
        if k not in ordered_keys:
            ordered_keys.append(k)

    parts = []
    total_chars = 0
    MAX_TOTAL = 48000

    for path in ordered_keys:
        content = assets[path]
        if len(content) > 8000:
            content = content[:8000] + "\n... (truncated)"
        if total_chars + len(content) > MAX_TOTAL:
            parts.append(f"── {path} ── (skipped, context budget reached)")
            continue
        parts.append(f"── {path} ──\n{content}")
        total_chars += len(content)

    return "\n\n".join(parts)


# Cache template context once
_CACHED_TEMPLATE_CONTEXT: str | None = None


def _get_template_context() -> str:
    """Get cached template context string."""
    global _CACHED_TEMPLATE_CONTEXT
    if _CACHED_TEMPLATE_CONTEXT is None:
        assets = _load_template_assets()
        _CACHED_TEMPLATE_CONTEXT = _build_asset_context(assets)
    return _CACHED_TEMPLATE_CONTEXT


def _build_code_gen_prompt(technical_spec: dict) -> str:
    """Build the code generation prompt with or without template context."""
    template_context = _get_template_context()
    spec_fields = dict(
        problem_statement_or_domain=technical_spec.get("problem_statement_or_domain", ""),
        auth_and_users=technical_spec.get("auth_and_users", ""),
        data_and_storage=technical_spec.get("data_and_storage", ""),
        ui_complexity=technical_spec.get("ui_complexity", ""),
        business_logic=technical_spec.get("business_logic", ""),
        integrations=technical_spec.get("integrations", ""),
    )
    if template_context:
        return CODE_GENERATION_PROMPT_WITH_TEMPLATE.format(
            **spec_fields,
            template_context=template_context,
        )
    else:
        return CODE_GENERATION_PROMPT_NO_TEMPLATE.format(**spec_fields)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE DEPENDENCY
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_code_blocks(markdown_text: str) -> tuple[str, str, str]:
    """Extract HTML, CSS, and JS blocks from markdown."""
    html_match = re.search(r'```html\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    css_match = re.search(r'```css\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    js_match = re.search(r'```javascript\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    
    if not js_match:
        js_match = re.search(r'```js\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)

    html_content = html_match.group(1) if html_match else "<!-- HTML Generation Failed -->"
    css_content = css_match.group(1) if css_match else "/* CSS Generation Failed */"
    js_content = js_match.group(1) if js_match else "// JS Generation Failed"

    return html_content, css_content, js_content


def get_or_create_session(session_id: Optional[str] = None, mode: str = "simple") -> str:
    """Get or create a session for the given mode."""
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "mode": mode,
            "history": [],
            "technical_spec": {
                "problem_statement_or_domain": "Not yet discussed",
                "auth_and_users": "Not yet discussed",
                "data_and_storage": "Not yet discussed",
                "ui_complexity": "Not yet discussed",
                "business_logic": "Not yet discussed",
                "integrations": "Not yet discussed",
            },
            "code": None,
        }
    return session_id


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE MODE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_simple_mode_response(conversation_history: list, current_requirements: dict) -> str:
    """Simple Mode: Uses Groq Llama for questions and HF Qwen for requirements extraction."""
    if not groq_client:
        raise Exception("GROQ_API_KEY not configured")
    if not hf_client:
        raise Exception("HUGGINGFACE_API_KEY not configured")
        
    # 1. Fetch next question using Groq (Llama 3 8B) — with requirements context
    llama_prompt = build_simple_llama_prompt(current_requirements)
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
    extraction_prompt = build_extraction_prompt(current_requirements)
    extraction_messages = [{"role": "system", "content": extraction_prompt}]
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
    
    # Try to clean up output
    json_match = re.search(r'\{.*\}', requirements_json_str, re.DOTALL)
    if json_match:
        requirements_json_str = json_match.group(0)
        
    try:
        req_data = json.loads(requirements_json_str)
    except Exception:
        req_data = {}

    # Merge: keep previous value if Qwen returned empty / "Not yet discussed" for a field
    merged_requirements = {}
    for key in ["problem_statement_or_domain", "auth_and_users", "data_and_storage", "ui_complexity", "business_logic", "integrations"]:
        new_val = req_data.get(key, "Not yet discussed")
        old_val = current_requirements.get(key, "Not yet discussed")
        if (not new_val or new_val == "Not yet discussed") and old_val and old_val != "Not yet discussed":
            merged_requirements[key] = old_val
        else:
            merged_requirements[key] = new_val if new_val else "Not yet discussed"

    # Calculate confidence: count how many dimensions have real info
    filled = sum(1 for v in merged_requirements.values() if _is_filled(v))
    raw_confidence = float(req_data.get("confidence_score", 0.0))
    min_confidence = (filled / 6.0) * 100.0
    confidence = max(raw_confidence, min_confidence)
        
    final_output = {
        "next_question": next_question,
        "requirements_object": merged_requirements,
        "confidence_score": min(confidence, 100.0)
    }
    
    return json.dumps(final_output)


# ═══════════════════════════════════════════════════════════════════════════════
# TAILORED MODE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _hf_token_check() -> str:
    """Return the HF API token."""
    if not hf_token:
        raise ValueError("No Hugging Face API key configured. Set HUGGINGFACE_API_KEY in your .env file.")
    return hf_token


def call_tailored_companion(history: list, current_message: str, current_spec: dict) -> str:
    """Tailored Mode: Get conversational question via HF Inference API."""
    try:
        API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
        headers = {"Authorization": f"Bearer {_hf_token_check()}"}

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history[:-1]
        )

        tailored_prompt = build_tailored_llama_prompt(current_spec)

        prompt = (
            f"[INST] {tailored_prompt}\n\n"
            f"Conversation so far:\n{conversation}\n\n"
            f"Latest user message: {current_message} [/INST]"
        )

        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.7}},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        generated = result[0]["generated_text"]
        if "[/INST]" in generated:
            generated = generated.split("[/INST]")[-1].strip()
        return generated
    except Exception as e:
        print(f"Tailored Companion Error: {e}")
        return "I'd love to understand more — could you tell me a bit about who will be using this app and what they need to do in it?"


def call_tailored_analyzer(history: list, current_spec: dict) -> dict:
    """Tailored Mode: Extract requirements via HF Inference API."""
    try:
        API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
        headers = {"Authorization": f"Bearer {_hf_token_check()}"}

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history
        )

        extraction_prompt = build_extraction_prompt(current_spec)

        prompt = (
            f"[INST] {extraction_prompt}\n\n"
            f"Full conversation:\n{conversation} [/INST]"
        )

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
        generated = generated.replace("```json", "").replace("```", "").strip()
        return json.loads(generated)
    except Exception as e:
        print(f"Tailored Analyzer Error: {e}")
        return {
            "problem_statement_or_domain": "Not yet discussed",
            "auth_and_users": "Not yet discussed",
            "data_and_storage": "Not yet discussed",
            "ui_complexity": "Not yet discussed",
            "business_logic": "Not yet discussed",
            "integrations": "Not yet discussed",
            "confidence_score": 0.0,
        }


def generate_code_with_hf(technical_spec: dict) -> dict:
    """Generate code using HF Inference API with template-aware prompt."""
    if not hf_client:
        raise Exception("No HuggingFace client configured")
    try:
        prompt = _build_code_gen_prompt(technical_spec)

        response = hf_client.chat_completion(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )

        generated_text = response.choices[0].message.content
        if not generated_text:
            raise Exception("No content received from model")

        html, css, js = extract_code_blocks(generated_text)
        return {"html": html, "css": css, "js": js}
    except Exception as e:
        print(f"Code Generation Error: {e}")
        return {
            "html": "<h1>App Generation Failed</h1><p>Please check backend console.</p>",
            "css": "",
            "js": "",
        }


def generate_code_with_groq(technical_spec: dict) -> dict:
    """Generate code using Qwen Coder model via HuggingFace with template-aware prompt.

    Uses the Qwen2.5-Coder-32B-Instruct model for high-quality code generation.
    """
    if not hf_client:
        raise Exception("No HuggingFace client configured")

    prompt = _build_code_gen_prompt(technical_spec)
    
    try:
        response = hf_client.chat_completion(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2
        )
        
        generated_text = response.choices[0].message.content
        if not generated_text:
            raise Exception("No content received from model")
        
        html, css, js = extract_code_blocks(generated_text)
        return {"html": html, "css": css, "js": js}
    except Exception as e:
        print(f"Groq Code Generation Error: {e}")
        return {
            "html": "<h1>App Generation Failed</h1><p>Please check backend console.</p>",
            "css": "",
            "js": "",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# API ROUTES — SIMPLE MODE
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/chat/simple", response_model=ChatResponseOuter)
async def simple_mode_chat(request: ChatRequest):
    """Simple Mode chat endpoint."""
    session_id = get_or_create_session(request.session_id, "simple")
    
    history = sessions[session_id]["history"]
    current_requirements = sessions[session_id].get("technical_spec", {
        "problem_statement_or_domain": "Not yet discussed",
        "auth_and_users": "Not yet discussed",
        "data_and_storage": "Not yet discussed",
        "ui_complexity": "Not yet discussed",
        "business_logic": "Not yet discussed",
        "integrations": "Not yet discussed",
    })
    history.append({
        "role": "user",
        "parts": [request.user_message]
    })
    
    try:
        loop = asyncio.get_event_loop()
        response_text = await asyncio.wait_for(
            loop.run_in_executor(None, get_simple_mode_response, history, current_requirements),
            timeout=30.0
        )
        
        response_data = json.loads(response_text)
        
        history.append({
            "role": "model",
            "parts": [response_data.get("next_question", "")]
        })
        
        # Persist accumulated requirements in session
        if response_data.get("requirements_object"):
            sessions[session_id]["technical_spec"] = response_data["requirements_object"]
        
        response_data["session_id"] = session_id
        return response_data
    except asyncio.TimeoutError:
        history.pop()
        raise HTTPException(status_code=504, detail="AI response timed out. Please try again.")
    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            history.pop()
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment and try again.")
        history.pop()
        raise HTTPException(status_code=500, detail=err)


@app.post("/api/generate", response_model=GenerateResponse)
async def simple_mode_generate(request: GenerateRequest, db: Session = Depends(get_db)):
    """Simple Mode: Generate app using Groq client."""
    if not hf_client:
        raise HTTPException(status_code=500, detail="Hugging Face API key is missing.")
    
    reqs = request.requirements_object
    if not reqs:
        raise HTTPException(status_code=400, detail="requirements_object is required")
    
    try:
        code_data = generate_code_with_groq(reqs.model_dump())
        
        # Save to database
        new_app = GeneratedApp(
            session_id=request.session_id,
            html_content=code_data.get("html", ""),
            css_content=code_data.get("css", ""),
            js_content=code_data.get("js", "")
        )
        db.add(new_app)
        db.commit()
        db.refresh(new_app)
        
        app_id: str = new_app.id if isinstance(new_app.id, str) else str(new_app.id)
        return GenerateResponse(app_id=app_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"App generation failed: {str(e)}")


@app.get("/api/apps/{app_id}")
async def simple_mode_get_app(app_id: str, db: Session = Depends(get_db)):
    """Simple Mode: Retrieve generated app."""
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


@app.post("/api/chat/reset")
async def simple_mode_reset(request: ChatRequest):
    """Simple Mode: Reset session."""
    if request.session_id in sessions:
        del sessions[request.session_id]
        return {"status": "session reset"}
    return {"status": "session not found"}


# ═══════════════════════════════════════════════════════════════════════════════
# API ROUTES — TAILORED MODE
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/chat/tailored")
async def tailored_mode_chat(request: ChatRequest):
    """Tailored Mode chat endpoint."""
    if not request.message:
        raise HTTPException(status_code=400, detail="message is required for tailored mode")
    
    session_id = get_or_create_session(request.session_id, "tailored")
    session = sessions[session_id]

    session["history"].append({"role": "user", "content": request.message})

    next_question = call_tailored_companion(session["history"], request.message, session["technical_spec"])
    analyzed = call_tailored_analyzer(session["history"], session["technical_spec"])
    confidence_score = analyzed.pop("confidence_score", 0.0)

    # Merge: preserve previously gathered info
    for key in ["problem_statement_or_domain", "auth_and_users", "data_and_storage", "ui_complexity", "business_logic", "integrations"]:
        new_val = analyzed.get(key, "Not yet discussed")
        old_val = session["technical_spec"].get(key, "Not yet discussed")
        if (not new_val or new_val == "Not yet discussed") and old_val and old_val != "Not yet discussed":
            analyzed[key] = old_val

    session["technical_spec"].update(analyzed)

    session["history"].append({"role": "assistant", "content": next_question})

    return {
        "session_id": session_id,
        "next_question": next_question,
        "technical_spec": session["technical_spec"],
        "confidence_score": confidence_score,
    }


@app.post("/api/generate/tailored")
async def tailored_mode_generate(request: GenerateRequest):
    """Tailored Mode: Generate app using HF Inference API."""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    generated_code = generate_code_with_hf(session["technical_spec"])
    session["code"] = generated_code

    return {
        "message": "Tailored app generated successfully",
        "code": generated_code
    }


@app.get("/api/download/{session_id}")
async def download_app(session_id: str):
    """Download generated app as ZIP."""
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
        headers={"Content-Disposition": f"attachment; filename=appforge_{session_id[:8]}.zip"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG ENDPOINT — GENERATE APP FROM JSON
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/debug/generate", response_model=DebugGenerateResponse)
async def debug_generate_app(request: DebugGenerateRequest):
    """
    Debug endpoint: Accepts a JSON specification and generates a working app using Mistral.
    This endpoint is for testing/debugging purposes.
    
    Expected JSON structure:
    {
      "auth_and_users": "...",
      "data_and_storage": "...",
      "ui_complexity": "...",
      "business_logic": "...",
      "integrations": "..."
    }
    """
    if not hf_client:
        raise HTTPException(status_code=500, detail="Hugging Face API key is missing.")
    
    spec = request.specification
    
    # Validate required fields
    required_fields = ["auth_and_users", "data_and_storage", "ui_complexity", "business_logic", "integrations"]
    missing_fields = [f for f in required_fields if f not in spec]
    
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    try:
        # Generate code using HF Inference API with Mistral
        code_data = generate_code_with_hf(spec)
        
        return DebugGenerateResponse(
            message="App generated successfully from JSON specification",
            code=code_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# API ROUTES — MULTI-AGENT PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════


@app.post("/api/pipeline/start", response_model=PipelineResponse)
async def start_pipeline(request: PipelineRequest):
    """
    Start the multi-agent code generation pipeline.

    Accepts a prompt describing the desired application.
    Returns a job_id immediately — generation runs in the background.
    """
    if not request.prompt or len(request.prompt.strip()) < 10:
        raise HTTPException(status_code=400, detail="Prompt must be at least 10 characters.")

    provider = request.provider if request.provider in ("groq", "huggingface") else "groq"

    try:
        job_id = await run_pipeline(request.prompt.strip(), provider)
        return PipelineResponse(job_id=job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@app.get("/api/pipeline/status/{job_id}", response_model=JobStatusResponse)
async def pipeline_status(job_id: str):
    """Get the current status of a generation job."""
    result = get_job_status(job_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**result)


@app.get("/api/pipeline/file/{job_id}")
async def pipeline_file(job_id: str, path: str):
    """
    Retrieve a specific generated file's content.

    Query parameter 'path' specifies the relative file path within the project.
    """
    if not path:
        raise HTTPException(status_code=400, detail="'path' query parameter is required")

    content = get_job_file(job_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    return JobFileResponse(job_id=job_id, file_path=path, content=content)


@app.get("/api/pipeline/jobs")
async def pipeline_list_jobs():
    """List all generation jobs."""
    return list_all_jobs()


@app.get("/api/pipeline/download/{job_id}")
async def pipeline_download(job_id: str):
    """Download an entire generated project as a ZIP archive."""
    status = get_job_status(job_id)
    if status.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed (status: {status.get('status')})")

    zip_bytes = build_job_zip(job_id)
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="No generated files found for this job")

    zip_buffer = io.BytesIO(zip_bytes)
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={job_id}.zip"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
