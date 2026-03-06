import uuid
import os
import json
import re
import asyncio
from typing import Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import groq
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sqlalchemy.orm import Session
from database import SessionLocal, GeneratedApp, ChatSession

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

# ─── Deterministic dimension routing (prevents question repetition) ───
DIMENSION_ORDER = [
    "problem_statement_or_domain",
    "auth_and_users",
    "data_and_storage",
    "ui_complexity",
    "business_logic",
    "integrations",
]

DIMENSION_FRIENDLY = {
    "problem_statement_or_domain": "what problem this app solves and what their day-to-day challenge is",
    "auth_and_users": "who will use this tool — just them, or do they have a team/customers who need access",
    "data_and_storage": "what key information and records they need to keep track of",
    "ui_complexity": "how they imagine using this — what the main screen should show, how it should look",
    "business_logic": "any rules, calculations, or automated workflows the app should handle",
    "integrations": "whether this needs to connect to any external services or tools they already use",
}

DEFAULT_REQUIREMENTS = {
    "problem_statement_or_domain": "Not yet discussed",
    "auth_and_users": "Not yet discussed",
    "data_and_storage": "Not yet discussed",
    "ui_complexity": "Not yet discussed",
    "business_logic": "Not yet discussed",
    "integrations": "Not yet discussed"
}


def _is_filled(val: str | None) -> bool:
    if not val:
        return False
    return val.strip().lower() not in ("not yet discussed", "n/a", "none", "unknown", "")


def _normalize_requirements(requirements: dict | None) -> dict:
    normalized = DEFAULT_REQUIREMENTS.copy()
    if requirements:
        for k, v in requirements.items():
            normalized[k] = v
    if requirements and "_discussed" in requirements:
        normalized["_discussed"] = requirements["_discussed"]
    elif "_discussed" not in normalized:
        normalized["_discussed"] = []
    if requirements and "_last_asked" in requirements:
        normalized["_last_asked"] = requirements["_last_asked"]
    return normalized


# ─── DB-backed session helpers ───
def _load_session(db: Session, session_id: str | None) -> tuple[str, list, dict]:
    if session_id:
        db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if db_session:
            history = json.loads(db_session.conversation_history)
            requirements = _normalize_requirements(json.loads(db_session.requirements_json))
            return session_id, history, requirements
    new_id = str(uuid.uuid4())
    new_session = ChatSession(
        id=new_id,
        conversation_history=json.dumps([]),
        requirements_json=json.dumps(DEFAULT_REQUIREMENTS.copy())
    )
    db.add(new_session)
    db.commit()
    return new_id, [], DEFAULT_REQUIREMENTS.copy()


def _save_session(db: Session, session_id: str, history: list, requirements: dict):
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.conversation_history = json.dumps(history)
        db_session.requirements_json = json.dumps(requirements)
        db.commit()


# System prompt for Groq Llama 3 8B
LLAMA_PROMPT = """You are AppForge AI's Simple Mode Companion—a warm, insightful guide who genuinely understands the challenges small business owners, NGOs, educators, and independent operators face daily.

Your core mission: Help them visualize and build the perfect software solution by drawing out what they truly need, making them feel heard, and helping them see how this tool will make their life easier.

Tone & Approach:
- Be genuinely warm and conversational—like talking to a trusted mentor, not a form-filling bot
- Show that you truly understand their world and the specific challenges they mentioned
- Validate their struggles before asking the next question
- Use their own language and context naturally throughout
- Help them see the bigger picture: how solving this problem will free up time, reduce stress, or unlock growth

Question Guidelines:
1. Always reference something specific they said—builds trust and shows you're listening
2. Ask ONLY ONE exploratory question at a time; let it feel natural and inevitable
3. Lead with curiosity about their situation, not about technical requirements
4. Avoid buzzwords completely (no "database," "authentication," "REST APIs," "UI components," etc.)
5. Never use lists or multiple-choice—keep it like a conversation between two people

Output ONLY your conversational response (the next question). Do not output JSON.
"""

# System prompt for HF Qwen 7B
QWEN_PROMPT = """You are a seasoned technical analyzer. Review the FULL conversation history and extract ALL requirements into 6 dimensions.

IMPORTANT RULES:
1. Preserve and build upon previously extracted requirements. Never lose information.
2. If a dimension was discussed earlier, keep that information AND add any new details.
3. Only write "Not yet discussed" if the topic has genuinely NEVER been mentioned.

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
2. Use CDN links for ALL vendor libraries so the app works standalone in any browser:
   - https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css
   - https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css
   - https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/css/sb-admin-2.min.css
   - https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js
   - https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js
   - https://cdn.jsdelivr.net/npm/jquery.easing@1.4.1/jquery.easing.min.js
   - https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/js/sb-admin-2.min.js
   - https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js (if charts needed)
   - https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js (if tables needed)
   - https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap4.min.js (if tables needed)
   - https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap4.min.css (if tables needed)
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

# ─── Compact SB Admin 2 skeleton the model MUST follow ───
_SB_ADMIN_SKELETON = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>{{APP_TITLE}}</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/css/sb-admin-2.min.css" rel="stylesheet">
  <link href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap4.min.css" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body id="page-top">
  <div id="wrapper">
    <ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion" id="accordionSidebar">
      <a class="sidebar-brand d-flex align-items-center justify-content-center" href="#">
        <div class="sidebar-brand-icon rotate-n-15"><i class="fas fa-laugh-wink"></i></div>
        <div class="sidebar-brand-text mx-3">{{APP_TITLE}}</div>
      </a>
      <hr class="sidebar-divider my-0">
      <li class="nav-item active"><a class="nav-link" href="#"><i class="fas fa-fw fa-tachometer-alt"></i><span>Dashboard</span></a></li>
      <hr class="sidebar-divider">
      <div class="sidebar-heading">Management</div>
      <li class="nav-item"><a class="nav-link" href="#"><i class="fas fa-fw fa-table"></i><span>Records</span></a></li>
      <li class="nav-item"><a class="nav-link" href="#"><i class="fas fa-fw fa-chart-area"></i><span>Reports</span></a></li>
    </ul>
    <div id="content-wrapper" class="d-flex flex-column">
      <div id="content">
        <nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">
          <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3"><i class="fa fa-bars"></i></button>
          <ul class="navbar-nav ml-auto">
            <li class="nav-item dropdown no-arrow">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-toggle="dropdown"><span class="mr-2 d-none d-lg-inline text-gray-600 small">User</span><i class="fas fa-user-circle fa-fw"></i></a>
            </li>
          </ul>
        </nav>
        <div class="container-fluid">
          <div class="d-sm-flex align-items-center justify-content-between mb-4">
            <h1 class="h3 mb-0 text-gray-800">Dashboard</h1>
          </div>
          <div class="row">
            <div class="col-xl-3 col-md-6 mb-4">
              <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-primary text-uppercase mb-1">Total</div><div class="h5 mb-0 font-weight-bold text-gray-800">0</div></div><div class="col-auto"><i class="fas fa-calendar fa-2x text-gray-300"></i></div></div></div>
              </div>
            </div>
          </div>
          <div class="card shadow mb-4">
            <div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Records</h6></div>
            <div class="card-body"><div class="table-responsive"><table class="table table-bordered" id="dataTable" width="100%" cellspacing="0"><thead><tr><th>#</th><th>Name</th><th>Status</th></tr></thead><tbody></tbody></table></div></div>
          </div>
          <div class="row">
            <div class="col-xl-8 col-lg-7"><div class="card shadow mb-4"><div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Overview</h6></div><div class="card-body"><div class="chart-area"><canvas id="myAreaChart"></canvas></div></div></div></div>
            <div class="col-xl-4 col-lg-5"><div class="card shadow mb-4"><div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Breakdown</h6></div><div class="card-body"><div class="chart-pie pt-4 pb-2"><canvas id="myPieChart"></canvas></div></div></div></div>
          </div>
        </div>
      </div>
      <footer class="sticky-footer bg-white"><div class="container my-auto"><div class="copyright text-center my-auto"><span>AppForge AI &copy; 2026</span></div></div></footer>
    </div>
  </div>
  <div class="modal fade" id="addEditModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">Add / Edit</h5><button type="button" class="close" data-dismiss="modal">&times;</button></div><div class="modal-body"><form id="entityForm"><!-- form fields here --></form></div><div class="modal-footer"><button class="btn btn-secondary" data-dismiss="modal">Cancel</button><button class="btn btn-primary" id="saveBtn">Save</button></div></div></div></div>
  <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jquery.easing@1.4.1/jquery.easing.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/startbootstrap-sb-admin-2@4.1.3/js/sb-admin-2.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap4.min.js"></script>
  <script src="script.js"></script>
</body>
</html>
"""

CODE_PROMPT_NO_TEMPLATE = """You are an expert Frontend Developer specializing in Bootstrap 4 admin dashboards.

You MUST generate a fully working single-page web app using the SB Admin 2 dashboard template structure shown below.
Do NOT use Tailwind, dark themes, or any other framework. You MUST use Bootstrap 4 + SB Admin 2 CDN.

## APP REQUIREMENTS:
Problem/Domain: {problem_statement_or_domain}
Authentication/Users: {auth_and_users}
Data/Storage: {data_and_storage}
UI Complexity: {ui_complexity}
Business Logic: {business_logic}
Integrations: {integrations}

## MANDATORY SB ADMIN 2 SKELETON (you MUST keep this exact structure — customize content only):
{skeleton}

## ADAPTATION RULES:
1. KEEP the EXACT HTML structure above: #wrapper → sidebar (.bg-gradient-primary) → #content-wrapper → topbar → .container-fluid → cards → tables → charts → footer.
2. Replace {{{{APP_TITLE}}}} with the app name derived from the requirements.
3. Sidebar nav items: replace with pages/entities relevant to the app.
4. Summary cards (.border-left-primary etc.): show key metrics for the app's domain.
5. DataTable: customize columns for the app's primary entity. Include Add/Edit/Delete buttons.
6. Charts: area chart for trends over time, pie chart for category breakdowns.
7. Modal (#addEditModal): add form fields matching the app's primary entity.
8. ALL data persistence via localStorage. Full CRUD operations.
9. Use ONLY these CDN links (already in skeleton) — do NOT add other CSS frameworks or dark-theme CSS.
10. The app must look like an SB Admin 2 dashboard — white background, gradient-primary blue sidebar, light topbar, card shadows.

## OUTPUT FORMAT — exactly three code blocks:

```html
<!-- Complete HTML page following the skeleton above -->
```
```css
/* ONLY additional custom styles — keep sb-admin-2 defaults. No dark themes. No Tailwind. */
```
```javascript
// Full app logic: localStorage CRUD, DataTable initialization, Chart.js setup, form handling, card metric updates
```

Do NOT add any text outside the code blocks. Give ONLY the code.
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
    return CODE_PROMPT_NO_TEMPLATE.format(**fields, skeleton=_SB_ADMIN_SKELETON)

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
    """Takes the history and accumulated requirements, returns a JSON response string.
    Uses deterministic dimension routing to prevent question repetition."""
    if not groq_client:
        raise Exception("GROQ_API_KEY not configured")
    if not hf_client:
        raise Exception("HUGGINGFACE_API_KEY not configured")

    # 1) Extract requirements using Qwen
    qwen_messages = [{"role": "system", "content": QWEN_PROMPT}]
    # Include previous requirements for context
    _internal_keys = {"_discussed", "_last_asked"}
    prev_json = json.dumps({k: v for k, v in current_requirements.items() if k not in _internal_keys}, indent=2)
    qwen_messages.append({"role": "system", "content": f"Previously extracted requirements (preserve and expand):\n{prev_json}"})
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        qwen_messages.append({"role": role, "content": msg["parts"][0]})

    qwen_response = hf_client.chat_completion(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=qwen_messages,  # type: ignore[arg-type]
        temperature=0.1,
        max_tokens=600
    )
    qwen_content = qwen_response.choices[0].message.content
    requirements_json_str = qwen_content.strip() if qwen_content else ""

    json_match = re.search(r'\{.*\}', requirements_json_str, re.DOTALL)
    if json_match:
        requirements_json_str = json_match.group(0)

    try:
        req_data = json.loads(requirements_json_str)
    except Exception:
        req_data = {}

    # 2) Merge: keep previous value if Qwen lost it
    merged_requirements = {}
    for key in DIMENSION_ORDER:
        new_val = req_data.get(key, "Not yet discussed")
        old_val = current_requirements.get(key, "Not yet discussed")
        if not new_val or new_val.strip().lower() in ("not yet discussed", "n/a", "none", "unknown", ""):
            new_val = None
        if not old_val or old_val.strip().lower() in ("not yet discussed", "n/a", "none", "unknown", ""):
            old_val = None
        if new_val:
            merged_requirements[key] = new_val
        elif old_val:
            merged_requirements[key] = old_val
        else:
            merged_requirements[key] = "Not yet discussed"

    # 3) Commit the dimension we asked about last turn (user just responded to it)
    # This guarantees we advance even when Qwen fails to extract a short answer.
    _last_asked = current_requirements.get("_last_asked", None)
    discussed = set(current_requirements.get("_discussed", []))
    if _last_asked:
        discussed.add(_last_asked)  # user responded to this question — mark covered
    # Also add anything Qwen successfully extracted this turn
    for key in DIMENSION_ORDER:
        if _is_filled(merged_requirements.get(key)):
            discussed.add(key)
    merged_requirements["_discussed"] = list(discussed)

    # 4) Deterministic dimension selection — pick the NEXT uncovered dimension
    next_dim = None
    for key in DIMENSION_ORDER:
        if key not in discussed:
            next_dim = key
            break

    # Record which dimension we are about to ask, so next turn can commit it
    merged_requirements["_last_asked"] = next_dim

    # 5) Build targeted Llama prompt
    req_summary = "\n".join(f"  - {dim}: {val}" for dim, val in merged_requirements.items() if dim not in {"_discussed", "_last_asked"})
    if next_dim:
        dimension_instruction = (
            f"\n\nYour ONLY task right now: Ask ONE warm, conversational question about "
            f"{DIMENSION_FRIENDLY[next_dim]}. "
            f"Do NOT ask about any other topic. Frame it naturally, referencing what the user already shared."
        )
    else:
        dimension_instruction = (
            "\n\nAll key areas have been covered. Warmly let them know you have a good picture "
            "of what they need, and ask if there's anything else they'd like to add or adjust."
        )

    llama_system = LLAMA_PROMPT + f"\n\nRequirements gathered so far:\n{req_summary}" + dimension_instruction
    messages = [{"role": "system", "content": llama_system}]
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

    # Repetition guard
    last_model_question = ""
    for msg in reversed(conversation_history):
        if msg["role"] == "model":
            last_model_question = msg["parts"][0].strip().lower()
            break
    if next_question.strip().lower() == last_model_question:
        if next_dim:
            next_question = f"Thanks for sharing that! I'd love to understand more about {DIMENSION_FRIENDLY[next_dim]}. Could you tell me a bit about that?"
        else:
            next_question = "Thanks, that helps a lot. Is there anything else you'd like this app to do before we build it?"

    # Confidence based on covered dimensions (discussed + the one we're about to ask)
    covered = len(discussed) + (1 if next_dim else 0)
    raw_confidence = float(req_data.get("confidence_score", 0.0))
    min_confidence = (covered / 6.0) * 100.0
    confidence = max(raw_confidence, min_confidence)

    final_output = {
        "next_question": next_question,
        "requirements_object": merged_requirements,
        "confidence_score": min(confidence, 100.0)
    }

    return json.dumps(final_output)

@app.post("/api/chat/simple", response_model=ChatResponseOuter)
async def simple_mode_chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id, history, current_requirements = _load_session(db, request.session_id)

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

        if response_data.get("requirements_object"):
            current_requirements = response_data["requirements_object"]

        _save_session(db, session_id, history, current_requirements)
        response_data["session_id"] = session_id

        return response_data
    except asyncio.TimeoutError:
        history.pop()
        _save_session(db, session_id, history, current_requirements)
        raise HTTPException(status_code=504, detail="AI response timed out. Please try again.")
    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            history.pop()
            _save_session(db, session_id, history, current_requirements)
            raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment and try again.")
        history.pop()
        _save_session(db, session_id, history, current_requirements)
        raise HTTPException(status_code=500, detail=err)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat/reset")
async def reset_session(request: ChatRequest, db: Session = Depends(get_db)):
    if request.session_id:
        db_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if db_session:
            db.delete(db_session)
            db.commit()
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
