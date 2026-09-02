from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(120), default="General")


class StudentSkill(Base):
    """A student's demonstrated proficiency in one skill, derived from evidence."""

    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)

    proficiency_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100, evidence-weighted
    confidence_level: Mapped[str] = mapped_column(String(20), default="Low")  # Low/Medium/High
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    skill = relationship("Skill")
    evidences = relationship("Evidence", back_populates="student_skill", cascade="all, delete-orphan")
    history = relationship("SkillScoreHistory", back_populates="student_skill", cascade="all, delete-orphan")


class SkillScoreHistory(Base):
    """Time series snapshot for skill growth analytics."""

    __tablename__ = "skill_score_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_skill_id: Mapped[int] = mapped_column(ForeignKey("student_skills.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str] = mapped_column(String(255), default="")  # e.g. "assessment", "evidence added"

    student_skill = relationship("StudentSkill", back_populates="history")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_skill_id: Mapped[int] = mapped_column(ForeignKey("student_skills.id"), index=True)
    type: Mapped[str] = mapped_column(String(30))  # certificate | github | project | assessment | industry_feedback
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(30), default="pending_review")  # verified | pending_review | needs_review | suspicious
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # contribution weight in confidence engine
    signal_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 signal strength of this piece of evidence
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student_skill = relationship("StudentSkill", back_populates="evidences")
