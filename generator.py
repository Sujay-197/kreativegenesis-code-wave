"""
Generator Module — Multi-Agent Code Generator

Loops through files from the architecture plan and generates
code for each file by calling the LLM with contextual prompts.
"""

import os
import re
import json
import asyncio
from typing import Optional, Any

import groq
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

GENERATOR_SYSTEM_PROMPT = """You are an expert full-stack developer. Generate clean, production-ready code for a single file in a web application project.

CONTEXT:
- Project: {project_name}
- Description: {project_description}
- Tech Stack: Backend={backend}, Frontend={frontend}, Database={database}
- File: {file_path}
- Purpose: {file_description}

SIBLING FILES (other files in this project for import/reference context):
{sibling_files}

RULES:
1. Output ONLY the raw code for this file. No markdown fences, no explanations, no comments like "here is the code".
2. Code must be modular with clear docstrings for every function and class.
3. Use async functions where appropriate (FastAPI route handlers, I/O operations).
4. Separate business logic from API route definitions.
5. Handle errors gracefully with try/except and proper HTTP status codes.
6. For Python backend files: use FastAPI, SQLAlchemy, Pydantic models.
7. For HTML files: use semantic HTML5, include proper meta tags, link CSS/JS files correctly.
8. For CSS files: use clean, responsive design. Tailwind CDN is acceptable.
9. For JS files: use modern ES6+, fetch API for HTTP calls, modular functions.
10. For requirements.txt: list only necessary packages with versions.
11. For database.py: use SQLAlchemy with SQLite, include engine setup and session factory.
12. Import paths must be correct relative to the project structure.
13. Backend main.py must mount routes from the routes/ directory and set up CORS.

Output ONLY the file content. No wrapping, no markdown.
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


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output if present."""
    text = text.strip()
    # Remove opening fence with optional language tag
    text = re.sub(r'^```[\w]*\s*\n?', '', text)
    # Remove closing fence
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()


def _build_sibling_context(files: list[dict], current_path: str) -> str:
    """Build a summary of sibling files for context."""
    siblings = []
    for f in files:
        if f["path"] != current_path:
            siblings.append(f"- {f['path']}: {f.get('description', 'No description')}")
    return "\n".join(siblings) if siblings else "None"


async def generate_file_code(
    file_info: dict,
    plan: dict,
    provider: str = "groq",
) -> str:
    """
    Generate code for a single file based on the architecture plan.

    Args:
        file_info: Dict with 'path' and 'description' keys.
        plan: The full architecture plan dict.
        provider: LLM provider — 'groq' or 'huggingface'.

    Returns:
        Generated code as a string.
    """
    loop = asyncio.get_event_loop()
    code = await loop.run_in_executor(None, _generate_file_code_sync, file_info, plan, provider)
    return code


def _generate_file_code_sync(file_info: dict, plan: dict, provider: str) -> str:
    """Synchronous version of file code generation (runs in executor)."""
    sibling_context = _build_sibling_context(plan.get("files", []), file_info["path"])

    prompt = GENERATOR_SYSTEM_PROMPT.format(
        project_name=plan.get("project_name", "app"),
        project_description=plan.get("description", ""),
        backend=plan.get("backend", "FastAPI"),
        frontend=plan.get("frontend", "HTML/CSS/JS"),
        database=plan.get("database", "SQLite"),
        file_path=file_info["path"],
        file_description=file_info.get("description", ""),
        sibling_files=sibling_context,
    )

    # type: ignore[list-item]
    messages: list[Any] = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Generate the complete code for: {file_info['path']}"},
    ]

    if provider == "groq":
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
        )
        raw = response.choices[0].message.content or ""
    else:
        client = _get_hf_client()
        response = client.chat_completion(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
        )
        raw = response.choices[0].message.content or ""

    return _strip_markdown_fences(raw)


async def generate_all_files(plan: dict, provider: str = "groq") -> dict[str, str]:
    """
    Generate code for every file in the architecture plan.

    Args:
        plan: The architecture plan dict containing a 'files' list.
        provider: LLM provider — 'groq' or 'huggingface'.

    Returns:
        Dict mapping file paths to generated code content.
    """
    generated_files: dict[str, str] = {}
    files = plan.get("files", [])

    # Generate files sequentially to keep rate limiting under control
    for file_info in files:
        path = file_info["path"]
        try:
            code = await generate_file_code(file_info, plan, provider)
            generated_files[path] = code
        except Exception as e:
            generated_files[path] = f"# ERROR: Code generation failed for {path}\n# {str(e)}"

    return generated_files
