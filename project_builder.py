"""
Project Builder Module — File System Builder

Creates the project directory structure and writes generated
code files to the correct locations on disk.
"""

import os
import re
import shutil
from pathlib import Path

# Base directory where all generated apps are stored
GENERATED_APPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_apps")

# Template directory with SB Admin 2 assets
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


def _sanitize_path(path: str) -> str:
    """
    Sanitize a file path to prevent directory traversal attacks.
    Strips leading slashes, '..' components, and normalizes separators.
    """
    # Normalize separators
    path = path.replace("\\", "/")
    # Remove any leading slashes
    path = path.lstrip("/")
    # Reject path traversal
    parts = path.split("/")
    safe_parts = [p for p in parts if p and p != ".."]
    return "/".join(safe_parts)


def get_project_dir(job_id: str) -> str:
    """
    Get the absolute path to a job's project directory.

    Args:
        job_id: The unique job identifier.

    Returns:
        Absolute path to the project directory.
    """
    # Sanitize job_id to prevent path traversal
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', job_id)
    return os.path.join(GENERATED_APPS_DIR, safe_id)


def create_project_structure(job_id: str, plan: dict) -> str:
    """
    Create the project directory structure based on the architecture plan.

    Args:
        job_id: Unique job identifier — used as the project folder name.
        plan: Architecture plan dict containing the 'files' list.

    Returns:
        The absolute path to the created project directory.
    """
    project_dir = get_project_dir(job_id)
    os.makedirs(project_dir, exist_ok=True)

    # Pre-create all directories referenced in the file list
    for file_info in plan.get("files", []):
        safe_path = _sanitize_path(file_info["path"])
        full_path = os.path.join(project_dir, safe_path)
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    return project_dir


def write_file(job_id: str, file_path: str, content: str) -> str:
    """
    Write a single generated file to the project directory.

    Args:
        job_id: The job identifier.
        file_path: Relative path within the project (e.g. 'backend/main.py').
        content: The file content to write.

    Returns:
        The absolute path of the written file.
    """
    project_dir = get_project_dir(job_id)
    safe_path = _sanitize_path(file_path)
    full_path = os.path.join(project_dir, safe_path)

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return full_path


def write_all_files(job_id: str, generated_files: dict[str, str]) -> dict[str, str]:
    """
    Write all generated files to the project directory.

    Args:
        job_id: The job identifier.
        generated_files: Dict mapping relative file paths to code content.

    Returns:
        Dict mapping relative paths to their absolute written paths.
    """
    written = {}
    for rel_path, content in generated_files.items():
        abs_path = write_file(job_id, rel_path, content)
        written[rel_path] = abs_path
    return written


def save_plan(job_id: str, plan: dict) -> str:
    """
    Save the architecture plan as a JSON file inside the project directory.

    Args:
        job_id: The job identifier.
        plan: The architecture plan dict.

    Returns:
        Absolute path to the saved plan file.
    """
    import json
    project_dir = get_project_dir(job_id)
    os.makedirs(project_dir, exist_ok=True)
    plan_path = os.path.join(project_dir, "architecture_plan.json")

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    return plan_path


def copy_template_assets(job_id: str, plan: dict) -> None:
    """
    Copy SB Admin 2 template assets (vendor, css, js, img) into the generated
    project's frontend directory so that HTML files' relative references work.

    Detects the frontend folder from the plan's file list (e.g. 'frontend/').
    If no explicit frontend folder exists, copies assets to the project root.
    """
    template_dir = _resolve_template_dir()
    if not template_dir:
        return

    project_dir = get_project_dir(job_id)

    # Figure out where frontend files live in this plan
    frontend_prefix = ""
    for f in plan.get("files", []):
        path = f["path"] if isinstance(f, dict) else f
        if path.endswith(".html"):
            parts = path.replace("\\", "/").split("/")
            if len(parts) > 1:
                frontend_prefix = parts[0]
            break

    dest_base = os.path.join(project_dir, frontend_prefix) if frontend_prefix else project_dir

    # Asset directories to copy from template
    ASSET_DIRS = ["vendor", "css", "js", "img"]
    for dirname in ASSET_DIRS:
        src = os.path.join(template_dir, dirname)
        dst = os.path.join(dest_base, dirname)
        if os.path.isdir(src) and not os.path.isdir(dst):
            shutil.copytree(src, dst)


def get_project_tree(job_id: str) -> list[str]:
    """
    List all files in a generated project.

    Args:
        job_id: The job identifier.

    Returns:
        List of relative file paths within the project.
    """
    project_dir = get_project_dir(job_id)
    if not os.path.exists(project_dir):
        return []

    tree = []
    for root, _, files in os.walk(project_dir):
        for name in files:
            abs_path = os.path.join(root, name)
            rel_path = os.path.relpath(abs_path, project_dir)
            tree.append(rel_path.replace("\\", "/"))

    return sorted(tree)
