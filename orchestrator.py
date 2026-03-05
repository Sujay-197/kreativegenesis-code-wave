"""
Orchestrator Module — Multi-Agent Pipeline Coordinator

Coordinates the full code generation pipeline:
  prompt → planner → generator → file builder → done

Manages job lifecycle and status tracking.
"""

import uuid
import json
import asyncio
import io
import zipfile
import os
from datetime import datetime
from typing import Optional

from planner import generate_plan
from generator import generate_all_files
from project_builder import (
    create_project_structure,
    write_all_files,
    save_plan,
    get_project_dir,
    get_project_tree,
)
from database import SessionLocal, GenerationJob, GeneratedFile


# In-memory job status cache for fast lookups
_job_cache: dict[str, dict] = {}


def _create_job_id() -> str:
    """Generate a unique job ID."""
    return f"job_{uuid.uuid4().hex[:12]}"


def _update_job_status(job_id: str, status: str, detail: str = ""):
    """
    Update job status in both the in-memory cache and the database.

    Args:
        job_id: The job identifier.
        status: New status string (pending, planning, generating, building, completed, failed).
        detail: Optional detail/error message.
    """
    _job_cache[job_id] = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.utcnow().isoformat(),
    }

    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
        if job:
            job.status = status
            if status == "completed":
                job.completed_at = datetime.utcnow()
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _save_job_to_db(job_id: str, prompt: str, plan: Optional[dict] = None) -> None:
    """Persist a new job record to the database."""
    db = SessionLocal()
    try:
        job = GenerationJob(
            job_id=job_id,
            prompt=prompt,
            architecture_plan=json.dumps(plan) if plan else None,
            status="pending",
        )
        db.add(job)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _update_job_plan(job_id: str, plan: dict) -> None:
    """Update the stored architecture plan for a job."""
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
        if job:
            job.architecture_plan = json.dumps(plan)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _save_generated_files(job_id: str, generated_files: dict[str, str]) -> None:
    """Persist generated file contents for a job."""
    db = SessionLocal()
    try:
        for file_path, content in generated_files.items():
            file_row = GeneratedFile(
                job_id=job_id,
                file_path=file_path,
                content=content,
            )
            db.add(file_row)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def run_pipeline(prompt: str, provider: str = "groq") -> str:
    """
    Execute the full multi-agent code generation pipeline.

    Steps:
        1. Create a job and persist it
        2. Call planner LLM to generate architecture
        3. Parse and validate the plan
        4. Create project directory structure
        5. Generate code for each file via generator LLM
        6. Write all files to disk
        7. Mark job complete

    Args:
        prompt: The user's application description.
        provider: LLM provider — 'groq' or 'huggingface'.

    Returns:
        The job_id for tracking progress.
    """
    job_id = _create_job_id()

    # Step 1: Create job record
    _save_job_to_db(job_id, prompt)
    _update_job_status(job_id, "pending")

    # Launch the pipeline as a background task with proper error handling
    task = asyncio.create_task(_execute_pipeline(job_id, prompt, provider))
    # Add a callback to log any exceptions
    task.add_done_callback(lambda t: _handle_task_exception(t, job_id))

    return job_id


def _handle_task_exception(task, job_id: str) -> None:
    """Handle exceptions from background tasks."""
    try:
        task.result()
    except Exception as e:
        _update_job_status(job_id, "failed", f"Background task error: {str(e)}")


async def _execute_pipeline(job_id: str, prompt: str, provider: str) -> None:
    """
    Internal pipeline execution — runs as a background asyncio task.

    This allows the API to return the job_id immediately while
    generation proceeds in the background.
    """
    try:
        # Step 2: Planning
        _update_job_status(job_id, "planning", "Generating architecture plan...")
        plan = await generate_plan(prompt, provider)
        _update_job_plan(job_id, plan)
        save_plan(job_id, plan)

        # Step 3: Create directory structure
        _update_job_status(job_id, "building", "Creating project structure...")
        create_project_structure(job_id, plan)

        # Step 4: Generate code for all files
        _update_job_status(job_id, "generating", "Generating code files...")
        generated_files = await generate_all_files(plan, provider)

        # Persist generated files in the database
        _save_generated_files(job_id, generated_files)

        # Step 5: Write files to disk
        _update_job_status(job_id, "building", "Writing files to disk...")
        write_all_files(job_id, generated_files)

        # Step 6: Mark complete
        _update_job_status(job_id, "completed", f"Generated {len(generated_files)} files")

    except Exception as e:
        _update_job_status(job_id, "failed", str(e))


def get_job_status(job_id: str) -> dict:
    """
    Get the current status of a generation job.

    Args:
        job_id: The job identifier.

    Returns:
        Dict with status, detail, and file list (if completed).
    """
    # Check in-memory cache first
    if job_id in _job_cache:
        result = {**_job_cache[job_id], "job_id": job_id}
        if result["status"] == "completed":
            result["files"] = get_project_tree(job_id)
            result["project_dir"] = get_project_dir(job_id)
        return result

    # Fall back to database
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
        if not job:
            return {"job_id": job_id, "status": "not_found", "detail": "Job not found"}

        result = {
            "job_id": job_id,
            "status": job.status,
            "detail": "",
            "prompt": job.prompt,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

        if job.status == "completed":
            result["files"] = get_project_tree(job_id)
            result["project_dir"] = get_project_dir(job_id)

        if job.architecture_plan:
            try:
                result["architecture"] = json.loads(job.architecture_plan)
            except json.JSONDecodeError:
                pass

        return result
    finally:
        db.close()


def get_job_file(job_id: str, file_path: str) -> Optional[str]:
    """
    Read a specific generated file's content.

    Args:
        job_id: The job identifier.
        file_path: Relative path within the project.

    Returns:
        File content as string, or None if not found.
    """
    import os
    from project_builder import _sanitize_path

    # Try database first
    db = SessionLocal()
    try:
        file_row = (
            db.query(GeneratedFile)
            .filter(GeneratedFile.job_id == job_id, GeneratedFile.file_path == file_path)
            .first()
        )
        if file_row:
            return file_row.content
    finally:
        db.close()

    project_dir = get_project_dir(job_id)
    safe_path = _sanitize_path(file_path)
    full_path = os.path.join(project_dir, safe_path)

    # Verify the resolved path is within the project directory
    real_project = os.path.realpath(project_dir)
    real_file = os.path.realpath(full_path)
    if not real_file.startswith(real_project):
        return None

    if os.path.isfile(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def list_all_jobs() -> list[dict]:
    """
    List all generation jobs from the database.

    Returns:
        List of job summary dicts.
    """
    db = SessionLocal()
    try:
        jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).all()
        return [
            {
                "job_id": j.job_id,
                "status": j.status,
                "prompt": j.prompt[:100] if j.prompt else "",
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ]
    finally:
        db.close()


def build_job_zip(job_id: str) -> Optional[bytes]:
    """
    Build a ZIP archive for a job from stored DB files or disk fallback.

    Args:
        job_id: The job identifier.

    Returns:
        ZIP bytes if files exist, otherwise None.
    """
    db = SessionLocal()
    try:
        rows = db.query(GeneratedFile).filter(GeneratedFile.job_id == job_id).all()
        if rows:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for row in rows:
                    zf.writestr(row.file_path, row.content)
            return zip_buffer.getvalue()
    finally:
        db.close()

    project_dir = get_project_dir(job_id)
    if not project_dir or not os.path.isdir(project_dir):
        return None

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(project_dir):
            for fname in files:
                abs_path = os.path.join(root, fname)
                arc_name = os.path.relpath(abs_path, project_dir)
                zf.write(abs_path, arc_name)
    return zip_buffer.getvalue()
