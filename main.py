import uuid
import os
import json
import asyncio
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
LLAMA_PROMPT = """You are AppForge AI's Simple Mode Companion. Your goal is to empower non-technical users (small business owners, NGOs, educators, etc.) by helping them plan software tools that solve their daily problems. 
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

MISTRAL_PROMPT_TEMPLATE = """You are an expert Frontend Developer. Your task is to generate a fully functioning web application based on the following requirements:

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
        messages=messages,
        temperature=0.7,
        max_tokens=200
    )
    next_question = llama_response.choices[0].message.content.strip()

    # 2. Extract requirements using HF Qwen 7B
    extraction_messages = [{"role": "system", "content": QWEN_PROMPT}]
    extraction_messages.extend(messages[1:]) # Add conversation history
    extraction_messages.append({"role": "assistant", "content": next_question})
    
    qwen_response = hf_client.chat_completion(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=extraction_messages,
        temperature=0.1,
        max_tokens=600
    )
    requirements_json_str = qwen_response.choices[0].message.content.strip()
    
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
    
    # Format the prompt
    reqs = request.requirements_object
    prompt = MISTRAL_PROMPT_TEMPLATE.format(
        auth_and_users=reqs.auth_and_users,
        data_and_storage=reqs.data_and_storage,
        ui_complexity=reqs.ui_complexity,
        business_logic=reqs.business_logic,
        integrations=reqs.integrations
    )
    
    try:
        # Generate with Mistral
        # Using mistralai/Mistral-7B-Instruct-v0.2 as a reliable standard code generation model
        response = hf_client.chat_completion(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2
        )
        
        generated_text = response.choices[0].message.content
        
        # Parse blocks
        html, css, js = extract_code_blocks(generated_text)
        
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
        
        return GenerateResponse(app_id=new_app.id)

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
