"""
Planner Module — Multi-Agent Architecture Planner

Takes a user prompt and generates an architecture JSON via LLM,
defining the project structure, tech stack, and file list.
"""

import os
import json
import re
import asyncio
from typing import Optional, Any

import groq
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

PLANNER_SYSTEM_PROMPT = """You are an expert software architect. Given a user's application description, produce an architecture plan as a JSON object.

RULES:
1. Use ONLY this tech stack: Python (FastAPI) for backend, SB Admin 2 (Bootstrap 4) template for frontend, SQLite for database.
2. Keep the design lightweight but clean — separate concerns properly.
3. Backend must have: main entry point, models, routes separated by domain, and a database module.
4. Frontend is built on the SB Admin 2 dashboard template (Bootstrap 4, sidebar navigation, topbar, card-based content areas). Frontend files should adapt this template — NOT start from scratch.
5. Include a requirements.txt for Python dependencies.
6. Every file must have a clear single responsibility.

IMPORTANT — FRONTEND TEMPLATE:
The project includes an SB Admin 2 Bootstrap 4 template with:
- Sidebar navigation (gradient primary), topbar, card-based content
- Vendor libraries: Bootstrap, jQuery, FontAwesome, Chart.js, DataTables (already available in vendor/ folder)
- CSS: css/sb-admin-2.css (plus custom styles)
- JS: js/sb-admin-2.js (plus custom app logic)
Frontend files should ADAPT this template structure. Use vendor CDN paths like vendor/jquery/jquery.min.js, vendor/bootstrap/js/bootstrap.bundle.min.js, etc.
All data persistence on the frontend should use localStorage.

You MUST output ONLY valid JSON matching this EXACT structure (no markdown, no explanation):
{
  "project_name": "snake_case_name",
  "description": "Brief description of the app",
  "backend": "FastAPI",
  "frontend": "SB Admin 2 (Bootstrap 4)",
  "database": "SQLite",
  "files": [
    {
      "path": "backend/main.py",
      "description": "FastAPI application entry point with CORS and route mounting"
    },
    {
      "path": "backend/database.py",
      "description": "SQLAlchemy engine, session, and Base setup for SQLite"
    }
  ]
}

IMPORTANT: The SB Admin 2 template's vendor/, css/, js/, and img/ directories are AUTOMATICALLY copied into the frontend/ folder. Do NOT include them in the files list. Only list files you want GENERATED (custom HTML, custom CSS, custom JS, backend code).

GUIDELINES for file planning:
- backend/ folder: main.py, database.py, models.py (or split by domain), routes/ folder with domain-separated route files
- frontend/ folder: index.html (main dashboard adapting SB Admin 2 layout), custom.css (app-specific styles on top of sb-admin-2.css), js/ folder with feature-separated JS files (e.g. app.js, api.js, components.js)
- Frontend HTML files MUST reference template assets via relative paths: vendor/jquery/jquery.min.js, css/sb-admin-2.min.css, js/sb-admin-2.min.js, etc.
- Root: requirements.txt
- Keep file count reasonable (5-15 files typically). Don't over-engineer.
- Each file description must clearly state what that file does — this will be used as the generation prompt.
- For HTML file descriptions, mention that they should use the SB Admin 2 sidebar+topbar+card layout.

Output ONLY the JSON object.
"""


def _get_groq_client() -> groq.Groq:
    """Return a configured Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")
    return groq.Groq(api_key=api_key)


def _get_hf_client() -> InferenceClient:
    """Return a configured HuggingFace Inference client."""
    token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_API_KEY")
    if not token:
        raise ValueError("HUGGINGFACE_API_KEY not configured")
    return InferenceClient(api_key=token)


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM output, stripping markdown fences if present."""
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No valid JSON found in LLM output: {text[:200]}")


async def generate_plan(prompt: str, provider: str = "groq") -> dict:
    """
    Generate an architecture plan from a user prompt.

    Args:
        prompt: The user's application description.
        provider: LLM provider to use — 'groq' or 'huggingface'.

    Returns:
        Architecture plan as a dict with project_name, files, etc.

    Raises:
        ValueError: If the LLM output cannot be parsed as valid JSON.
    """
    loop = asyncio.get_event_loop()
    plan = await loop.run_in_executor(None, _generate_plan_sync, prompt, provider)
    return plan


def _generate_plan_sync(prompt: str, provider: str) -> dict:
    """Synchronous version of plan generation (runs in executor)."""
    # type: ignore[list-item]
    messages: list[Any] = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    if provider == "groq":
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=3000,
        )
        raw = response.choices[0].message.content or ""
    else:
        client = _get_hf_client()
        response = client.chat_completion(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or ""

    plan = _extract_json(raw)

    # Validate required keys
    required = {"project_name", "files"}
    missing = required - set(plan.keys())
    if missing:
        raise ValueError(f"Architecture plan missing required keys: {missing}")

    if not isinstance(plan["files"], list) or len(plan["files"]) == 0:
        raise ValueError("Architecture plan must contain a non-empty 'files' list")

    # Normalize file entries
    normalized_files = []
    for f in plan["files"]:
        if isinstance(f, str):
            normalized_files.append({"path": f, "description": f"Implementation for {f}"})
        elif isinstance(f, dict) and "path" in f:
            normalized_files.append({
                "path": f["path"],
                "description": f.get("description", f"Implementation for {f['path']}"),
            })
        else:
            continue
    plan["files"] = normalized_files

    # Ensure defaults
    plan.setdefault("backend", "FastAPI")
    plan.setdefault("frontend", "SB Admin 2 (Bootstrap 4)")
    plan.setdefault("database", "SQLite")
    plan.setdefault("description", prompt[:200])

    return plan
