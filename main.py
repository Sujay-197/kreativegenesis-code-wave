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

# ─── Sample app templates for reference during question generation ───
APP_TEMPLATES = {
    "calories_tracker": {
        "name": "Calories Tracker",
        "auth_and_users": "Single user, no login needed — personal use only",
        "data_and_storage": "Meals with food name, calories, protein, carbs, fat, date/time; daily calorie goals; weight log entries with date and weight",
        "ui_complexity": "Dashboard showing today's calories vs goal, meal log list with add form, weekly summary chart, progress view",
        "business_logic": "Calculate remaining daily calories, track macros, streak counting for consecutive days logged, weekly averages",
        "integrations": "No external integrations — all data stored locally"
    },
    "inventory_manager": {
        "name": "Inventory Manager",
        "auth_and_users": "Staff login with admin and standard roles; admin can add/remove products, standard can view and update stock",
        "data_and_storage": "Products with name, SKU, category, quantity, price, reorder level; stock movements (in/out) with date and reason; suppliers with contact info",
        "ui_complexity": "Dashboard with low-stock alerts and total value; product list with search/filter; add/edit product form; stock movement history",
        "business_logic": "Auto-alert when stock falls below reorder level; calculate total inventory value; track stock movement history",
        "integrations": "No external integrations required"
    },
    "appointment_scheduler": {
        "name": "Appointment Scheduler",
        "auth_and_users": "Staff login to manage appointments; customers book via a public page (no login required for booking)",
        "data_and_storage": "Appointments with client name, phone, service type, date/time, duration, status; services offered with name and duration; availability slots",
        "ui_complexity": "Calendar view showing all appointments; booking form for clients; daily schedule list for staff; appointment detail modal",
        "business_logic": "Prevent double-booking same time slot; auto-set status from booked→confirmed→completed; time slot availability check",
        "integrations": "No external integrations required"
    },
    "expense_tracker": {
        "name": "Expense Tracker",
        "auth_and_users": "Single user, personal use — no authentication needed",
        "data_and_storage": "Expenses with amount, category, description, date; income entries; monthly budgets per category",
        "ui_complexity": "Dashboard with spending overview and category breakdown chart; expense list with filters; add expense form; monthly comparison view",
        "business_logic": "Calculate totals by category and time period; compare spending vs budget; track income vs expenses balance",
        "integrations": "No external integrations required"
    },
    "task_manager": {
        "name": "Task Manager",
        "auth_and_users": "Single user or small team with names (no complex auth)",
        "data_and_storage": "Tasks with title, description, priority, status, due date, assigned person; projects/categories to group tasks",
        "ui_complexity": "Kanban board with drag columns (To Do, In Progress, Done); task list view with filters; add/edit task form",
        "business_logic": "Status transitions (open→in progress→done); overdue task highlighting; priority-based sorting",
        "integrations": "No external integrations required"
    },
    "student_records": {
        "name": "Student Records",
        "auth_and_users": "Teacher/admin login to manage records; view-only access for other staff",
        "data_and_storage": "Students with name, ID, grade/class, contact; attendance records by date; grades/marks by subject and term",
        "ui_complexity": "Student list with search; individual student profile with attendance and grades; class overview dashboard; attendance marking form",
        "business_logic": "Calculate attendance percentage; compute grade averages; flag students with low attendance or failing grades",
        "integrations": "No external integrations required"
    }
}

DEFAULT_REQUIREMENTS = {
    "problem_statement_or_domain": "Not yet discussed",
    "auth_and_users": "Not yet discussed",
    "data_and_storage": "Not yet discussed",
    "ui_complexity": "Not yet discussed",
    "business_logic": "Not yet discussed",
    "integrations": "Not yet discussed"
}

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


def _normalize_requirements(requirements: dict | None) -> dict:
    """Ensure requirements dict always has all expected keys for backward compatibility."""
    normalized: dict[str, Any] = dict(DEFAULT_REQUIREMENTS)
    if requirements:
        for k, v in requirements.items():
            normalized[k] = v
    # Preserve discussed dimensions tracking
    if requirements and "_discussed" in requirements:
        normalized["_discussed"] = requirements["_discussed"]
    elif "_discussed" not in normalized:
        normalized["_discussed"] = []
    if requirements and "_last_asked" in requirements:
        normalized["_last_asked"] = requirements["_last_asked"]
    return normalized


def _is_filled(val: str | None) -> bool:
    """Check if a requirement dimension has real info (not empty/placeholder)."""
    if not val:
        return False
    return val.strip().lower() not in ("not yet discussed", "n/a", "none", "unknown", "")


def _get_deficits(requirements: dict) -> list[str]:
    """Return list of dimension names that are still unfilled or have only defaults."""
    deficits = []
    labels = {
        "problem_statement_or_domain": "What problem this app solves and its domain/context",
        "auth_and_users": "Who will use this app (single user or multiple, any login needs)",
        "data_and_storage": "What information/data the app needs to track",
        "ui_complexity": "How the app should look and feel (views, layout, device)",
        "business_logic": "Rules, calculations, or workflows the app should handle automatically",
        "integrations": "Whether the app needs to connect to external services"
    }
    for key, label in labels.items():
        val = requirements.get(key, "Not yet discussed")
        if not _is_filled(val):
            deficits.append(label)
        elif val and "(default — refine if needed)" in val:
            deficits.append(f"{label} (has default — confirm or refine)")
    return deficits


def _find_matching_template(requirements: dict, history: list) -> dict | None:
    """Try to match user's description to a sample template for reference."""
    all_text = " ".join(
        msg["parts"][0].lower() for msg in history if msg["role"] == "user"
    )
    scores = {}
    keywords_map = {
        "calories_tracker": ["calorie", "calories", "food", "meal", "nutrition", "diet", "macro", "eating", "weight loss"],
        "inventory_manager": ["inventory", "stock", "warehouse", "product", "sku", "supply", "goods"],
        "appointment_scheduler": ["appointment", "booking", "schedule", "salon", "clinic", "reservation", "slot"],
        "expense_tracker": ["expense", "budget", "spending", "money", "finance", "income", "cost"],
        "task_manager": ["task", "todo", "to-do", "kanban", "project", "assign", "deadline"],
        "student_records": ["student", "school", "grade", "attendance", "teacher", "class", "marks"]
    }
    for key, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in all_text)
        if score > 0:
            scores[key] = score
    if scores:
        best = max(scores, key=lambda k: scores[k])
        return APP_TEMPLATES[best]
    return None


def _sanitize_qwen_value(val: Any) -> str | None:
    """Normalize Qwen field values to non-empty strings when possible."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=True)
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        cleaned = val.strip()
        return cleaned if cleaned else None
    return None


def _validate_qwen_requirements(req_data: dict) -> dict:
    """Return only expected keys from Qwen with sanitized string values."""
    if not isinstance(req_data, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key in DIMENSION_ORDER:
        if key in req_data:
            cleaned_val = _sanitize_qwen_value(req_data.get(key))
            if cleaned_val:
                cleaned[key] = cleaned_val
    if "confidence_score" in req_data:
        try:
            score_val = req_data.get("confidence_score")
            if score_val is not None:
                cleaned["confidence_score"] = float(score_val)
        except Exception:
            pass
    return cleaned


def _apply_last_answer_fallback(
    merged_requirements: dict,
    last_user_text: str,
    last_asked_dim: str | None,
) -> None:
    """Backfill the last asked dimension when Qwen fails on short answers."""
    if not last_user_text or not last_asked_dim:
        return
    if _is_filled(merged_requirements.get(last_asked_dim)):
        return
    negative = {
        "no", "nope", "none", "nah", "not really", "n/a", "na", "nothing"
    }
    normalized = last_user_text.strip().lower().strip(".!?")
    if normalized in negative:
        merged_requirements[last_asked_dim] = "User has no additional requirements for this area."
    else:
        merged_requirements[last_asked_dim] = f"User said: {last_user_text.strip()}"


# ─── DB-backed session helpers ───

def _load_session(db: Session, session_id: str | None) -> tuple[str, list, dict]:
    """Load or create a session from the database. Returns (session_id, history, requirements)."""
    if session_id:
        db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if db_session:
            history = json.loads(db_session.conversation_history)
            requirements = _normalize_requirements(json.loads(db_session.requirements_json))
            return session_id, history, requirements

    # Create new session
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
    """Persist session state back to the database."""
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.conversation_history = json.dumps(history)
        db_session.requirements_json = json.dumps(requirements)
        db.commit()


# System prompt for Groq Llama 3 8B — now deficit-driven
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

def build_llama_prompt(current_requirements: dict, history: list, target_dimension: str | None = None) -> str:
    """Build the Llama system prompt focused on a specific dimension to ask about."""
    _internal = {"_discussed", "_last_asked"}
    req_summary = "\n".join(
        f"  - {dim}: {val}" for dim, val in current_requirements.items()
        if dim not in _internal
    )

    # Deterministic dimension targeting — tell Llama EXACTLY what to ask about
    if target_dimension and target_dimension in DIMENSION_FRIENDLY:
        dimension_instruction = (
            f"\n\nYour ONLY task right now: Ask ONE warm, conversational question about "
            f"{DIMENSION_FRIENDLY[target_dimension]}. "
            f"Do NOT ask about any other topic. Frame it naturally, referencing what the user already shared."
        )
    else:
        dimension_instruction = (
            "\n\nAll key areas have been covered. Warmly let them know you have a good picture "
            "of what they need, and ask if there's anything else they'd like to add or adjust "
            "before you build their app."
        )

    # Try to match a template for richer context
    template = _find_matching_template(current_requirements, history)
    template_block = ""
    if template:
        template_block = (
            f"\n\nREFERENCE TEMPLATE (use as inspiration — '{template['name']}'):\n"
            f"  - Users: {template['auth_and_users']}\n"
            f"  - Data: {template['data_and_storage']}\n"
            f"  - UI: {template['ui_complexity']}\n"
            f"  - Logic: {template['business_logic']}\n"
            f"  - Integrations: {template['integrations']}\n"
            "Use this template as a guide for the DEPTH of detail needed, but tailor questions to the user's specific app."
        )

    return (
        LLAMA_BASE_PROMPT
        + f"\n\nRequirements gathered so far:\n{req_summary}"
        + dimension_instruction
        + template_block
    )

# System prompt for HF Qwen 7B
QWEN_BASE_PROMPT = """You are a seasoned technical analyzer. Review the FULL conversation history and extract ALL of the user's requirements into 6 dimensions.

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

def build_qwen_prompt(previous_requirements: dict, history: list) -> str:
    """Build Qwen prompt with previous requirements and template reference for better extraction."""
    prompt = QWEN_BASE_PROMPT

    _internal = {"_discussed", "_last_asked"}
    prev_only = {k: v for k, v in previous_requirements.items() if k not in _internal}
    if not all(v == "Not yet discussed" for v in prev_only.values()):
        req_json = json.dumps(prev_only, indent=2)
        prompt += f"\nPreviously extracted requirements (update and expand these, do NOT lose any info):\n{req_json}\n"

    # Provide template reference so Qwen knows the expected detail level
    template = _find_matching_template(previous_requirements, history)
    if template:
        prompt += (
            f"\nREFERENCE TEMPLATE for a '{template['name']}' app (use as a guide for expected detail level):\n"
            + json.dumps({k: v for k, v in template.items() if k != "name"}, indent=2)
            + "\nExtract at LEAST this level of detail from the conversation. Fill in reasonable defaults from the template for dimensions the user hasn't explicitly discussed IF the app type clearly matches.\n"
        )

    return prompt

# Pydantic Models for JSON structure
class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str

class RequirementsObject(BaseModel):
    problem_statement_or_domain: str = Field(description="What core problem the app solves and in which domain/context it will be used.")
    auth_and_users: str = Field(description="Details regarding user accounts, roles, or authentication needs.")
    data_and_storage: str = Field(description="Details on what data needs to be stored and tracked.")
    ui_complexity: str = Field(description="Details on the user interface requirements and devices it will be used on.")
    business_logic: str = Field(description="Specific workflows, calculations, or logic needed.")
    integrations: str = Field(description="Any needed connections to outside services (e.g., email, payments).")

class GeminiChatResponse(BaseModel):
    next_question: str = Field(description="The friendly, empathetic companion's single question acknowledging their context.")
    requirements_object: RequirementsObject
    chat_summary: str = Field(description="A natural-language paragraph summarizing the user's app needs so far.")
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

# ─── Template loading ───
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")


def _resolve_template_dir() -> str | None:
    """Resolve the template directory from common runtime locations."""
    candidates = [
        TEMPLATE_DIR,
        os.path.join(os.getcwd(), "template"),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "index.html")):
            return candidate
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    return None


def _load_template_assets() -> dict[str, str]:
    """Read core template files from the template/ folder and return {relative_path: content}.
    Skips vendor libraries, SVG icons, and other bulky assets that the LLM doesn't need.
    Returns empty dict if folder is missing or empty."""
    assets: dict[str, str] = {}
    template_dir = _resolve_template_dir()
    if not template_dir:
        return assets

    # Folders to skip — vendor libs, font icons, build artifacts
    SKIP_DIRS = {"vendor", "node_modules", "scss", "less", "sprites", "svgs", "webfonts", "metadata", ".git"}
    # Only load files the LLM needs to understand the template structure
    ALLOWED_EXTS = {".html", ".css", ".js", ".py", ".sql", ".json"}
    # Skip minified duplicates — keep only the readable versions
    SKIP_SUFFIXES = {".min.css", ".min.js", ".map", ".min.map"}

    for root, dirs, files in os.walk(template_dir):
        # Prune dirs we don't need
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, template_dir).replace("\\", "/")
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTS:
                continue
            if any(fname.lower().endswith(s) for s in SKIP_SUFFIXES):
                continue
            # Skip package lock (huge, not useful)
            if fname == "package-lock.json":
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    assets[rel] = f.read()
            except Exception:
                pass
    return assets


def _build_asset_context(assets: dict[str, str]) -> str:
    """Format loaded template files into a prompt-friendly block.
    Prioritizes key structural files (index, login, tables, CSS, JS) and
    keeps total size under a budget to avoid exceeding LLM context."""
    if not assets:
        return ""

    # Priority order — most important files first
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
    # Add remaining files not already included
    for k in sorted(assets.keys()):
        if k not in ordered_keys:
            ordered_keys.append(k)

    parts = []
    total_chars = 0
    MAX_TOTAL = 48000  # ~12k tokens budget for template context

    for path in ordered_keys:
        content = assets[path]
        # Truncate individual large files
        if len(content) > 8000:
            content = content[:8000] + "\n... (truncated)"
        if total_chars + len(content) > MAX_TOTAL:
            parts.append(f"── {path} ── (skipped, context budget reached)")
            continue
        parts.append(f"── {path} ──\n{content}")
        total_chars += len(content)

    return "\n\n".join(parts)


# ─── Code generation prompts ───

# Used when template assets ARE available
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

# Fallback: used when NO template assets are found
CODE_PROMPT_NO_TEMPLATE = """You are an expert Frontend Developer. Your task is to generate a fully functioning web application based on the following requirements:

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

def extract_code_blocks(markdown_text: str) -> tuple[str, str, str, str]:
    """Parse HTML, CSS, JS, and optional Python blocks from markdown output."""
    import re
    
    html_match = re.search(r'```html\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    css_match = re.search(r'```css\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    js_match = re.search(r'```javascript\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    py_match = re.search(r'```python\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)
    
    # Fallbacks for JS block which is sometimes marked as 'js'
    if not js_match:
        js_match = re.search(r'```js\n(.*?)\n```', markdown_text, re.DOTALL | re.IGNORECASE)

    html_content = html_match.group(1) if html_match else "<!-- HTML Generation Failed -->"
    css_content = css_match.group(1) if css_match else "/* CSS Generation Failed */"
    js_content = js_match.group(1) if js_match else "// JS Generation Failed"
    py_content = py_match.group(1) if py_match else ""

    return html_content, css_content, js_content, py_content


def _build_chat_summary(requirements: dict) -> str:
    """Create a frontend-friendly paragraph summary from extracted requirements."""
    problem = requirements.get("problem_statement_or_domain", "Not yet discussed")
    users = requirements.get("auth_and_users", "Not yet discussed")
    data = requirements.get("data_and_storage", "Not yet discussed")
    ui = requirements.get("ui_complexity", "Not yet discussed")
    logic = requirements.get("business_logic", "Not yet discussed")
    integrations = requirements.get("integrations", "Not yet discussed")

    def clean(v: str) -> str:
        return "still being refined" if not _is_filled(v) else v

    return (
        f"This app is for {clean(problem)}. It is intended for {clean(users)}. "
        f"It should manage {clean(data)} with an interface focused on {clean(ui)}. "
        f"Core behavior includes {clean(logic)}, and integrations are {clean(integrations)}."
    )

def get_genai_response(conversation_history: list, current_requirements: dict) -> str:
    """Takes the history and accumulated requirements, returns a JSON response string.
    Uses deterministic dimension routing to prevent question repetition."""
    if not groq_client:
        raise Exception("GROQ_API_KEY not configured")
    if not hf_client:
        raise Exception("HUGGINGFACE_API_KEY not configured")

    import re

    # 1) Extract requirements using Qwen
    qwen_prompt = build_qwen_prompt(current_requirements, conversation_history)
    extraction_messages = [{"role": "system", "content": qwen_prompt}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        extraction_messages.append({"role": role, "content": msg["parts"][0]})
    
    qwen_response = hf_client.chat_completion(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=extraction_messages,  # type: ignore[arg-type]
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

    req_data = _validate_qwen_requirements(req_data)

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

    # 3) Heuristic parser for short/typo user replies
    last_user_text = ""
    last_user_text_raw = ""
    for msg in reversed(conversation_history):
        if msg["role"] == "user":
            last_user_text_raw = msg["parts"][0].strip()
            last_user_text = last_user_text_raw.lower()
            break

    if last_user_text:
        if not _is_filled(merged_requirements.get("problem_statement_or_domain")):
            if any(x in last_user_text for x in ["tracker", "track", "manage", "system", "app", "for "]):
                merged_requirements["problem_statement_or_domain"] = f"User needs an app for: {last_user_text}"

        if (not _is_filled(merged_requirements.get("auth_and_users")) and
            any(x in last_user_text for x in ["just me", "jst me", "only me", "solo", "myself"])):
            merged_requirements["auth_and_users"] = "Single user, no authentication needed"

        if not _is_filled(merged_requirements.get("ui_complexity")):
            if "all of them" in last_user_text or "all" == last_user_text:
                merged_requirements["ui_complexity"] = "Needs adding records, list views, and summary dashboard"
            elif any(x in last_user_text for x in ["dashboard", "summary"]):
                merged_requirements["ui_complexity"] = "Dashboard-centric view with summaries"
            elif "list" in last_user_text:
                merged_requirements["ui_complexity"] = "List-centric interface"

    # Backfill the last asked dimension when Qwen fails on brief replies
    _last_asked = current_requirements.get("_last_asked", None)
    if last_user_text_raw:
        _apply_last_answer_fallback(merged_requirements, last_user_text_raw, _last_asked)

    # 4) Template pre-fill for remaining gaps
    template = _find_matching_template(merged_requirements, conversation_history)
    if template:
        for key in DIMENSION_ORDER:
            if merged_requirements[key] != "Not yet discussed":
                continue
            if key == "problem_statement_or_domain":
                merged_requirements[key] = f"A {template.get('name', 'software')} application (default — refine if needed)"
            elif template.get(key):
                merged_requirements[key] = template[key] + " (default — refine if needed)"

    # 5) Commit the dimension we asked about last turn (user just responded to it)
    # This guarantees we advance even when Qwen fails to extract a short/brief answer.
    _last_asked = current_requirements.get("_last_asked", None)
    discussed = set(current_requirements.get("_discussed", []))
    if _last_asked:
        discussed.add(_last_asked)  # user responded to this question — mark covered
    # Also add anything Qwen successfully extracted this turn
    for key in DIMENSION_ORDER:
        if _is_filled(merged_requirements.get(key)):
            discussed.add(key)
    merged_requirements["_discussed"] = list(discussed)

    # 6) Deterministic dimension selection — pick the NEXT uncovered dimension
    next_dim = None
    for key in DIMENSION_ORDER:
        if key not in discussed:
            next_dim = key
            break

    # Record which dimension we are about to ask so next turn can commit it
    merged_requirements["_last_asked"] = next_dim

    # 7) Generate next question using Llama, targeting the specific dimension
    llama_prompt = build_llama_prompt(merged_requirements, conversation_history, target_dimension=next_dim)
    messages = [{"role": "system", "content": llama_prompt}]
    for msg in conversation_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["parts"][0]})

    # Detect low-signal reply
    progressed = any(
        merged_requirements.get(k, "Not yet discussed") != current_requirements.get(k, "Not yet discussed")
        for k in DIMENSION_ORDER
    )
    token_count = len([t for t in re.split(r"\s+", last_user_text) if t]) if last_user_text else 0
    if last_user_text and (not progressed) and token_count <= 3:
        next_question = "Sorry, I didn't quite catch that. Could you rephrase it in a bit more detail?"
    else:
        llama_response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,  # type: ignore[arg-type]
            temperature=0.7,
            max_tokens=250
        )
        llama_content = llama_response.choices[0].message.content
        next_question = llama_content.strip() if llama_content else ""

    # Repetition guard: if Llama repeats the last question verbatim, force a fallback
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

    # Strip internal tracking keys from the output requirements_object
    _internal_keys = {"_discussed", "_last_asked"}
    output_requirements = {k: v for k, v in merged_requirements.items() if k not in _internal_keys}

    final_output = {
        "next_question": next_question,
        "requirements_object": merged_requirements,  # includes _discussed for session persistence
        "chat_summary": _build_chat_summary(output_requirements),
        "confidence_score": min(confidence, 100.0)
    }
    
    return json.dumps(final_output)

@app.post("/api/chat/simple", response_model=ChatResponseOuter)
async def simple_mode_chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Load session from DB (persistent across restarts)
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
        
        # Update requirements from response
        if response_data.get("requirements_object"):
            current_requirements = response_data["requirements_object"]
        
        # Persist session to DB
        _save_session(db, session_id, history, current_requirements)
        
        # Inject our session_id to let the frontend persist it
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

@app.get("/api/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieve a persisted session so the frontend can resume a conversation."""
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    history = json.loads(db_session.conversation_history)
    requirements = json.loads(db_session.requirements_json)
    requirements = _normalize_requirements(requirements)
    # Compute confidence from requirements
    filled = sum(1 for v in requirements.values() if _is_filled(v))
    confidence = min((filled / 6.0) * 100.0, 100.0)
    return {
        "session_id": db_session.id,
        "history": history,
        "requirements_object": requirements,
        "chat_summary": _build_chat_summary(requirements),
        "confidence_score": confidence
    }

@app.get("/api/templates")
async def list_templates():
    """Return available app templates for the frontend to display as suggestions."""
    return [
        {"id": k, "name": v["name"], "description": f"{v['data_and_storage'][:80]}..."}
        for k, v in APP_TEMPLATES.items()
    ]

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

    # Load template assets from the template/ folder
    template_assets = _load_template_assets()
    template_context = _build_asset_context(template_assets)

    # Pick prompt based on whether template assets exist
    if template_context:
        prompt = CODE_PROMPT_WITH_TEMPLATE.format(
            problem_statement_or_domain=reqs.problem_statement_or_domain,
            auth_and_users=reqs.auth_and_users,
            data_and_storage=reqs.data_and_storage,
            ui_complexity=reqs.ui_complexity,
            business_logic=reqs.business_logic,
            integrations=reqs.integrations,
            template_context=template_context
        )
    else:
        prompt = CODE_PROMPT_NO_TEMPLATE.format(
            problem_statement_or_domain=reqs.problem_statement_or_domain,
            auth_and_users=reqs.auth_and_users,
            data_and_storage=reqs.data_and_storage,
            ui_complexity=reqs.ui_complexity,
            business_logic=reqs.business_logic,
            integrations=reqs.integrations
        )
    
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
        html, css, js, py_backend = extract_code_blocks(generated_text)
        
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
        
        # If we got a Python backend block, save it alongside the app in generated_apps/
        if py_backend:
            app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_apps", str(new_app.id))
            os.makedirs(app_dir, exist_ok=True)
            with open(os.path.join(app_dir, "app.py"), "w", encoding="utf-8") as f:
                f.write(py_backend)
            with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            with open(os.path.join(app_dir, "style.css"), "w", encoding="utf-8") as f:
                f.write(css)
            with open(os.path.join(app_dir, "script.js"), "w", encoding="utf-8") as f:
                f.write(js)

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
