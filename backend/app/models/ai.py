from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    result_json: Mapped[dict] = mapped_column(JSON)
    used_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    model_name: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GitHubAnalysis(Base):
    __tablename__ = "github_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    result_json: Mapped[dict] = mapped_column(JSON)
    used_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    model_name: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdaptiveAssessmentSession(Base):
    __tablename__ = "adaptive_assessment_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress|completed
    current_topic: Mapped[str] = mapped_column(String(120), default="General")
    current_difficulty: Mapped[str] = mapped_column(String(20), default="intermediate")
    current_question: Mapped[dict] = mapped_column(JSON, default=dict)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    max_steps: Mapped[int] = mapped_column(Integer, default=5)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    history: Mapped[list] = mapped_column(JSON, default=list)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)
    used_ai_any: Mapped[bool] = mapped_column(Boolean, default=False)
    score_percent: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    skill = relationship("Skill")


class AIConversation(Base):
    """One turn of Career Copilot Q&A, kept for transparency/audit — not a generic chat log."""
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    used_data_points: Mapped[list] = mapped_column(JSON, default=list)
    used_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
