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

# ─── Template loading (shared with main.py) ───
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")


def _resolve_template_dir() -> str | None:
    """Resolve template directory from common runtime locations."""
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
    """Read core template files from the template/ folder.
    Skips vendor libraries, SVG icons, and other bulky assets."""
    assets: dict[str, str] = {}
    template_dir = _resolve_template_dir()
    if not template_dir:
        return assets

    SKIP_DIRS = {"vendor", "node_modules", "scss", "less", "sprites", "svgs", "webfonts", "metadata", ".git"}
    ALLOWED_EXTS = {".html", ".css", ".js", ".py", ".sql", ".json"}
    SKIP_SUFFIXES = {".min.css", ".min.js", ".map", ".min.map"}

    for root, dirs, files in os.walk(template_dir):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, template_dir).replace("\\", "/")
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
    MAX_TOTAL = 32000  # ~8k tokens budget for template context per file

    for path in ordered_keys:
        content = assets[path]
        if len(content) > 6000:
            content = content[:6000] + "\n... (truncated)"
        if total_chars + len(content) > MAX_TOTAL:
            parts.append(f"── {path} ── (skipped, context budget reached)")
            continue
        parts.append(f"── {path} ──\n{content}")
        total_chars += len(content)

    return "\n\n".join(parts)


# Cache template assets once at module load
_TEMPLATE_ASSETS: dict[str, str] | None = None
_TEMPLATE_CONTEXT: str | None = None


def _get_template_context() -> str:
    """Get cached template context string."""
    global _TEMPLATE_ASSETS, _TEMPLATE_CONTEXT
    if _TEMPLATE_CONTEXT is None:
        _TEMPLATE_ASSETS = _load_template_assets()
        _TEMPLATE_CONTEXT = _build_asset_context(_TEMPLATE_ASSETS)
    # Avoid permanently caching empty context when template is temporarily unavailable.
    if not _TEMPLATE_CONTEXT:
        _TEMPLATE_ASSETS = _load_template_assets()
        refreshed = _build_asset_context(_TEMPLATE_ASSETS)
        if refreshed:
            _TEMPLATE_CONTEXT = refreshed
    return _TEMPLATE_CONTEXT

GENERATOR_SYSTEM_PROMPT = """You are an expert full-stack developer. Generate clean, production-ready code for a single file in a web application project.

CONTEXT:
- Project: {project_name}
- Description: {project_description}
- Tech Stack: Backend={backend}, Frontend={frontend}, Database={database}
- File: {file_path}
- Purpose: {file_description}

SIBLING FILES (other files in this project for import/reference context):
{sibling_files}

{template_section}

RULES:
1. Output ONLY the raw code for this file. No markdown fences, no explanations, no comments like "here is the code".
2. Code must be modular with clear docstrings for every function and class.
3. Use async functions where appropriate (FastAPI route handlers, I/O operations).
4. Separate business logic from API route definitions.
5. Handle errors gracefully with try/except and proper HTTP status codes.
6. For Python backend files: use FastAPI, SQLAlchemy, Pydantic models.
7. For HTML files: use the SB Admin 2 template structure (Bootstrap 4, sidebar, topbar, card-based content). Use CDN links for ALL vendor libraries so the app works standalone:
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
8. For CSS files: use clean, responsive design. Build on top of sb-admin-2.css, adding only custom styles.
9. For JS files: use modern ES6+, fetch API for HTTP calls, modular functions.
10. For requirements.txt: list only necessary packages with versions.
11. For database.py: use SQLAlchemy with SQLite, include engine setup and session factory.
12. Import paths must be correct relative to the project structure.
13. Backend main.py must mount routes from the routes/ directory and set up CORS.
14. All frontend functionality must work standalone — use localStorage for data persistence.

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

    # Build template section for HTML/CSS/JS files
    file_ext = os.path.splitext(file_info["path"])[1].lower()
    template_section = ""
    if file_ext in (".html", ".css", ".js"):
        template_ctx = _get_template_context()
        if template_ctx:
            template_section = (
                "TEMPLATE REFERENCE (SB Admin 2 — Bootstrap 4 dashboard template).\n"
                "The template vendor/, css/, js/, and img/ folders are ALREADY copied into the project.\n"
                "Use relative paths to reference them (e.g. vendor/jquery/jquery.min.js).\n"
                "ADAPT the template structure — sidebar, topbar, card-based content — don't start from scratch:\n\n"
                + template_ctx
            )

    prompt = GENERATOR_SYSTEM_PROMPT.format(
        project_name=plan.get("project_name", "app"),
        project_description=plan.get("description", ""),
        backend=plan.get("backend", "FastAPI"),
        frontend=plan.get("frontend", "HTML/CSS/JS"),
        database=plan.get("database", "SQLite"),
        file_path=file_info["path"],
        file_description=file_info.get("description", ""),
        sibling_files=sibling_context,
        template_section=template_section,
    )

    # type: ignore[list-item]
    messages: list[Any] = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Generate the complete code for: {file_info['path']}"},
    ]

    if provider == "groq":
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=8000,
        )
        raw = response.choices[0].message.content or ""
    else:
        client = _get_hf_client()
        response = client.chat_completion(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            messages=messages,
            temperature=0.2,
            max_tokens=8000,
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
