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
6. Subtly explore these 5 dimensions without them feeling like a checklist: Who uses this tool? What data matters most? How should it look and feel? What complex workflows run behind the scenes? Does this connect to other tools they use?

Connection Strategy:
- Reference their specific context (bakery → orders/inventory, school → student records, etc.)
- Acknowledge time/stress: "So you're juggling this manually right now..."
- Paint a picture: "Imagine being able to..."
- Show empathy for their constraints (budget, time, technical comfort)

Output ONLY your conversational response (the next question). Do not output JSON.
"""

# System prompt for HF Qwen 7B
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
    <!-- Sidebar -->
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
    <!-- Content Wrapper -->
    <div id="content-wrapper" class="d-flex flex-column">
      <div id="content">
        <!-- Topbar -->
        <nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">
          <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3"><i class="fa fa-bars"></i></button>
          <ul class="navbar-nav ml-auto">
            <li class="nav-item dropdown no-arrow">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-toggle="dropdown"><span class="mr-2 d-none d-lg-inline text-gray-600 small">User</span><i class="fas fa-user-circle fa-fw"></i></a>
            </li>
          </ul>
        </nav>
        <!-- Begin Page Content -->
        <div class="container-fluid">
          <div class="d-sm-flex align-items-center justify-content-between mb-4">
            <h1 class="h3 mb-0 text-gray-800">Dashboard</h1>
          </div>
          <!-- Summary Cards Row -->
          <div class="row">
            <div class="col-xl-3 col-md-6 mb-4">
              <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-primary text-uppercase mb-1">Total</div><div class="h5 mb-0 font-weight-bold text-gray-800">0</div></div><div class="col-auto"><i class="fas fa-calendar fa-2x text-gray-300"></i></div></div></div>
              </div>
            </div>
          </div>
          <!-- DataTable -->
          <div class="card shadow mb-4">
            <div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Records</h6></div>
            <div class="card-body"><div class="table-responsive"><table class="table table-bordered" id="dataTable" width="100%" cellspacing="0"><thead><tr><th>#</th><th>Name</th><th>Status</th></tr></thead><tbody></tbody></table></div></div>
          </div>
          <!-- Charts -->
          <div class="row">
            <div class="col-xl-8 col-lg-7"><div class="card shadow mb-4"><div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Overview</h6></div><div class="card-body"><div class="chart-area"><canvas id="myAreaChart"></canvas></div></div></div></div>
            <div class="col-xl-4 col-lg-5"><div class="card shadow mb-4"><div class="card-header py-3"><h6 class="m-0 font-weight-bold text-primary">Breakdown</h6></div><div class="card-body"><div class="chart-pie pt-4 pb-2"><canvas id="myPieChart"></canvas></div></div></div></div>
          </div>
        </div>
      </div>
      <!-- Footer -->
      <footer class="sticky-footer bg-white"><div class="container my-auto"><div class="copyright text-center my-auto"><span>AppForge AI &copy; 2026</span></div></div></footer>
    </div>
  </div>
  <!-- Modal for Add/Edit -->
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

# Prompt template used for code generation — enforces SB Admin 2 template.
CODE_PROMPT_TEMPLATE = """You are an expert Frontend Developer specializing in Bootstrap 4 admin dashboards.

You MUST generate a fully working single-page web app using the SB Admin 2 dashboard template structure shown below.
Do NOT use Tailwind, dark themes, or any other framework. You MUST use Bootstrap 4 + SB Admin 2 CDN.

## APP REQUIREMENTS:
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
3. Sidebar nav items: replace with pages/entities relevant to the app (Dashboard, each entity list, Reports, etc.).
4. Summary cards (.border-left-primary etc.): show key metrics (totals, counts, amounts) for the app's domain.
5. DataTable: customize columns for the app's primary entity. Include Add/Edit/Delete buttons.
6. Charts: area chart for trends over time, pie chart for category breakdowns — both relevant to the app.
7. Modal (#addEditModal): add form fields matching the app's primary entity.
8. ALL data persistence via localStorage. Full CRUD operations.
9. Use ONLY these CDN links (already in skeleton) — do NOT add other CSS frameworks or dark-theme CSS.
10. The app must look like an SB Admin 2 dashboard — white background, gradient-primary blue sidebar, light topbar, card shadows.

## OUTPUT FORMAT — exactly three code blocks:

```html
<!-- Complete HTML page following the skeleton above with customized sidebar items, cards, table columns, chart canvases, and modal form fields -->
```
```css
/* ONLY additional custom styles — keep sb-admin-2 defaults. No dark themes. No Tailwind. */
```
```javascript
// Full app logic: localStorage CRUD, DataTable initialization, Chart.js setup, form handling, card metric updates
```

Do NOT add any text outside the code blocks. Give ONLY the code.
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
    
    # Format the prompt with SB Admin 2 skeleton
    reqs = request.requirements_object
    prompt = CODE_PROMPT_TEMPLATE.format(
        auth_and_users=reqs.auth_and_users,
        data_and_storage=reqs.data_and_storage,
        ui_complexity=reqs.ui_complexity,
        business_logic=reqs.business_logic,
        integrations=reqs.integrations,
        skeleton=_SB_ADMIN_SKELETON
    )
    
    try:
        # Generate with Qwen coder model (SB Admin 2 enforced)
        response = hf_client.chat_completion(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
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
