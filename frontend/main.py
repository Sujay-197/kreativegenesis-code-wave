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
LLAMA_PROMPT = """You are AppForge AI's Simple Mode Companion—a warm, insightful guide who genuinely understands the challenges small business owners, NGOs, educators, and independent operators face daily.

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

Connection Strategy:
- Reference their specific context (bakery → orders/inventory, school → student records, etc.)
- Acknowledge time/stress: "So you're juggling this manually right now..."
- Paint a picture: "Imagine being able to..."
- Show empathy for their constraints (budget, time, technical comfort)

Output ONLY your conversational response (the next question). Do not output JSON.
"""

# System prompt for HF Qwen 7B
QWEN_PROMPT = """You are a seasoned technical analyzer. Review the conversation history and extract the user's requirements into 6 dimensions.
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
Specific details only. If unknown, write "Not yet discussed".
Output ONLY the JSON object, with no markdown formatting.
"""

# Pydantic Models for JSON structure
class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str

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

CODE_PROMPT_WITH_TEMPLATE = """You are an expert Frontend Developer. You are given an SB Admin 2 (Bootstrap 4) dashboard TEMPLATE. Your job is to ADAPT this template into a new, fully working app that matches the requirements below.

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
4. CHANGE: JavaScript data models and logic — use localStorage for data persistence. Create proper CRUD operations.
5. If the app needs charts, adapt the Chart.js pattern with correct labels/data.
6. If the app needs data tables, adapt the DataTables pattern with correct columns.
7. All functionality must work standalone — no server required. Use localStorage for all data persistence.

IMPORTANT: Your output MUST contain exactly three code blocks:

```html
<!-- Full single-page HTML with vendor references, sidebar, topbar, content area -->
```
```css
/* Additional CSS beyond sb-admin-2 -->
```
```javascript
// All app logic: CRUD, charts, tables, form handling, localStorage
```

Do not include any explanations outside of the code blocks. Give me only the code.
"""

CODE_PROMPT_NO_TEMPLATE = """You are an expert Frontend Developer. Your task is to generate a fully functioning web application based on the following requirements:

Problem/Domain: {problem_statement_or_domain}
Authentication/Users: {auth_and_users}
Data/Storage: {data_and_storage}
UI Complexity: {ui_complexity}
Business Logic: {business_logic}
Integrations: {integrations}

Generate the code using HTML, CSS (Tailwind via CDN is okay), and plain JavaScript.
Use localStorage for data persistence.
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

# ===== TEMPLATE LOADING =====
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "template")

def _load_template_assets() -> dict:
    assets = {}
    if not os.path.isdir(TEMPLATE_DIR):
        return assets
    SKIP_DIRS = {"vendor", "node_modules", "scss", "less", "sprites", "svgs", "webfonts", "metadata", ".git"}
    ALLOWED_EXTS = {".html", ".css", ".js"}
    SKIP_SUFFIXES = {".min.css", ".min.js", ".map"}
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
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    assets[rel] = f.read()
            except Exception:
                pass
    return assets

def _build_asset_context(assets: dict) -> str:
    if not assets:
        return ""
    PRIORITY = [
        "index.html", "login.html", "tables.html", "charts.html",
        "css/sb-admin-2.css", "js/sb-admin-2.js",
        "js/demo/chart-area-demo.js", "js/demo/datatables-demo.js",
    ]
    ordered = [p for p in PRIORITY if p in assets]
    ordered += [k for k in sorted(assets) if k not in ordered]
    parts, total = [], 0
    for path in ordered:
        content = assets[path]
        if len(content) > 8000:
            content = content[:8000] + "\n... (truncated)"
        if total + len(content) > 48000:
            parts.append(f"-- {path} -- (skipped, budget reached)")
            continue
        parts.append(f"-- {path} --\n{content}")
        total += len(content)
    return "\n\n".join(parts)

_CACHED_TEMPLATE = None

def _get_template_context() -> str:
    global _CACHED_TEMPLATE
    if _CACHED_TEMPLATE is None:
        _CACHED_TEMPLATE = _build_asset_context(_load_template_assets())
    return _CACHED_TEMPLATE

def _build_code_prompt(spec: dict) -> str:
    fields = dict(
        problem_statement_or_domain=spec.get("problem_statement_or_domain", ""),
        auth_and_users=spec.get("auth_and_users", ""),
        data_and_storage=spec.get("data_and_storage", ""),
        ui_complexity=spec.get("ui_complexity", ""),
        business_logic=spec.get("business_logic", ""),
        integrations=spec.get("integrations", ""),
    )
    ctx = _get_template_context()
    if ctx:
        return CODE_PROMPT_WITH_TEMPLATE.format(**fields, template_context=ctx)
    return CODE_PROMPT_NO_TEMPLATE.format(**fields)

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

def get_genai_response(conversation_history: list) -> str:
    """Takes the history and returns a strictly typed JSON response string."""
    if not groq_client:
        raise Exception("GROQ_API_KEY not configured")
    if not hf_client:
        raise Exception("HUGGINGFACE_API_KEY not configured")
        
    # 1. Fetch next question using Groq (Llama 3 8B)
    messages = [{"role": "system", "content": LLAMA_PROMPT}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["parts"][0]})
        
    llama_response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages,  # type: ignore[arg-type]
        temperature=0.7,
        max_tokens=200
    )
    llama_content = llama_response.choices[0].message.content
    next_question = llama_content.strip() if llama_content else ""

    # 2. Extract requirements using HF Qwen 7B
    extraction_messages = [{"role": "system", "content": QWEN_PROMPT}]
    extraction_messages.extend(messages[1:]) # Add conversation history
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
    import re
    json_match = re.search(r'\{.*\}', requirements_json_str, re.DOTALL)
    if json_match:
        requirements_json_str = json_match.group(0)
        
    try:
        req_data = json.loads(requirements_json_str)
    except Exception:
        req_data = {}
        
    # Construct final output
    final_output = {
        "next_question": next_question,
        "requirements_object": {
            "problem_statement_or_domain": req_data.get("problem_statement_or_domain", "Not yet discussed"),
            "auth_and_users": req_data.get("auth_and_users", "Not yet discussed"),
            "data_and_storage": req_data.get("data_and_storage", "Not yet discussed"),
            "ui_complexity": req_data.get("ui_complexity", "Not yet discussed"),
            "business_logic": req_data.get("business_logic", "Not yet discussed"),
            "integrations": req_data.get("integrations", "Not yet discussed")
        },
        "confidence_score": float(req_data.get("confidence_score", 0.0))
    }
    
    return json.dumps(final_output)

@app.post("/api/chat/simple", response_model=ChatResponseOuter)
async def simple_mode_chat(request: ChatRequest):
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "history": []
        }
    
    history = sessions[session_id]["history"]
    history.append({
        "role": "user",
        "parts": [request.user_message]
    })
    
    try:
        loop = asyncio.get_event_loop()
        response_text = await asyncio.wait_for(
            loop.run_in_executor(None, get_genai_response, history),
            timeout=30.0
        )
        
        response_data = json.loads(response_text)
        
        history.append({
            "role": "model",
            "parts": [response_data.get("next_question", "")]
        })
        
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
    
    reqs = request.requirements_object
    prompt = _build_code_prompt(reqs.model_dump())
    
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
        
        # Save to SQLite
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
