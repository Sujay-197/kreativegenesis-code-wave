import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column

SQLALCHEMY_DATABASE_URL = "sqlite:///./code_storage.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ChatSession(Base):
    """Persists chat sessions across server restarts."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    conversation_history: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    requirements_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedApp(Base):
    """Stores simple/tailored mode generated apps (HTML/CSS/JS)."""
    __tablename__ = "generated_apps"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, index=True)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    css_content: Mapped[str] = mapped_column(Text, nullable=False)
    js_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GenerationJob(Base):
    """Tracks multi-agent pipeline generation jobs."""
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    architecture_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class GeneratedFile(Base):
    """Stores generated code files for a job."""
    __tablename__ = "generated_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)
