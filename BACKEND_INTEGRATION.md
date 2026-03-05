# Backend Integration Guide

## Overview
The AppForge AI backend has been unified into a single `backend_mode.py` file that supports both **Simple Mode** and **Tailored Mode**.

## File Structure

### Current Setup
- `backend_mode.py` - **PRIMARY BACKEND FILE** (Unified Simple + Tailored Modes)
- `simple_mode.py` - Reference copy of original Simple Mode implementation
- `frontend_app/tailored_mode.py` - Reference copy of original Tailored Mode implementation
- `main.py` - Original (kept for legacy reference)

## Running the Backend

### Start the Unified Backend
```bash
cd c:\Users\asus\Desktop\kghack01
python -m uvicorn backend_mode:app --host 127.0.0.1 --port 8000 --reload
```

## API Endpoints

### Simple Mode
- **POST** `/api/chat/simple` - Send user message and get conversational response
  ```json
  {
    "session_id": "optional-uuid",
    "user_message": "I want to build..."
  }
  ```

- **POST** `/api/generate` - Generate app from requirements
  ```json
  {
    "session_id": "session-uuid",
    "requirements_object": {
      "auth_and_users": "...",
      "data_and_storage": "...",
      "ui_complexity": "...",
      "business_logic": "...",
      "integrations": "..."
    }
  }
  ```

- **GET** `/api/apps/{app_id}` - Retrieve generated app HTML/CSS/JS

- **POST** `/api/chat/reset` - Reset a session

### Tailored Mode
- **POST** `/api/chat/tailored` - Send user message and get response with updated spec
  ```json
  {
    "session_id": "optional-uuid",
    "message": "I want to build..."
  }
  ```

- **POST** `/api/generate/tailored` - Generate app from accumulated requirements
  ```json
  {
    "session_id": "session-uuid"
  }
  ```

- **GET** `/api/download/{session_id}` - Download generated app as ZIP file

### Health Check
- **GET** `/api/health` - Basic health check

## Configuration

### Required Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key          # For Simple Mode (Llama 3 8B)
HUGGINGFACE_API_KEY=your_hf_api_key     # For both modes (Qwen & Mistral)
```

Alternative HF API key name:
```bash
HF_API_KEY=your_hf_api_key              # Alternative to HUGGINGFACE_API_KEY
```

## Key Features

### Simple Mode
- Uses **Groq Llama 3 8B** for conversational questions (via groq_client)
- Uses **HF Qwen 2.5 7B** for requirements extraction via HF Inference API
- Uses **Qwen 2.5 Coder** (via HF/Groq) for code generation (replacing earlier Mistral 7B)
- Stores apps in SQLite database (`GeneratedApp` model)
- Keeps full conversation history with model responses

### Tailored Mode
- Uses **Mistral 7B Instruct v0.3** via HF Inference API for both discovery and code generation
- Silent requirements extraction (updates after each turn, not visible to user)
- In-memory session storage (no database required)
- Ability to download apps as ZIP files
- Single unified conversation interface

### Shared Features
- **Warm, Compassionate Prompts** - Both modes use similar supportive, empathetic questioning approach
- **Flexible Code Generation** - Supports HTML, CSS (Tailwind via CDN), and plain JavaScript
- **CORS Enabled** - Frontend can communicate with backend on any origin
- **Error Handling** - Graceful timeout, rate-limit, and error responses
- **Session Management** - Both in-memory (tailored) and database-backed (simple)

## Prompts

All prompts have been updated to be:
- **Warm & Conversational** - Like talking to a trusted mentor
- **Validating** - Acknowledging user struggles before asking questions
- **Context-Aware** - Referencing specific details from conversation
- **Empathetic** - Showing understanding of constraints (time, budget, technical comfort)
- **Non-Technical** - Avoiding buzzwords completely

## Migration Notes

If switching from separate backends:
1. Update frontend API calls to use appropriate `/api/chat/simple` or `/api/chat/tailored` endpoints
2. Session IDs are compatible between both modes (stored in `sessions` dict with mode tracking)
3. Database apps (Simple Mode) can be queried with `/api/apps/{app_id}`
4. Downloaded apps (Tailored Mode) are ZIP files containing index.html, styles.css, script.js

## Next Steps

1. Verify all environment variables are set
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `uvicorn backend_mode:app --reload`
4. Test endpoints using frontend or API client
5. Monitor console for any errors or rate-limiting issues
