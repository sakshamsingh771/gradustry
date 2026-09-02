from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    topic: Mapped[str] = mapped_column(String(120), default="General")
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")  # beginner|intermediate|advanced
    question_type: Mapped[str] = mapped_column(String(30), default="mcq")  # mcq|multi_select|true_false|scenario
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSON, default=list)  # list[str]
    correct_answer: Mapped[dict] = mapped_column(JSON, default=list)  # list[str] (indices or values)
    explanation: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(50), default="ai_generated")  # ai_generated|manual
    status: Mapped[str] = mapped_column(String(30), default="approved")  # pending_review|approved|rejected


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    topic_focus: Mapped[str] = mapped_column(String(255), default="")  # e.g. "OOP, Debugging" for gap-specific tests
    question_ids: Mapped[dict] = mapped_column(JSON, default=list)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    score_percent: Mapped[float] = mapped_column(Float, default=0.0)
    previous_score: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    skill = relationship("Skill")


class CareerRole(Base):
    """Target career role used by the Skill Gap Engine, e.g. 'Backend Developer'."""

    __tablename__ = "career_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")

    requirements = relationship("RoleSkillRequirement", back_populates="role", cascade="all, delete-orphan")


class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("career_roles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    target_proficiency: Mapped[float] = mapped_column(Float, default=70.0)
    importance: Mapped[str] = mapped_column(String(20), default="core")  # core|preferred

    role = relationship("CareerRole", back_populates="requirements")
    skill = relationship("Skill")


class RoadmapStep(Base):
    """A single step in a student's AI-generated gap-closure roadmap for one skill."""

    __tablename__ = "roadmap_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    resource_type: Mapped[str] = mapped_column(String(30), default="learning")  # learning|practice|project|assessment
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started|in_progress|completed
    baseline_score: Mapped[float] = mapped_column(Float, default=0.0)
    target_score: Mapped[float] = mapped_column(Float, default=70.0)

    skill = relationship("Skill")
