from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industry_profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    role_type: Mapped[str] = mapped_column(String(50), default="internship")  # internship|job
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), default="Remote")
    min_year_of_study: Mapped[int] = mapped_column(Integer, default=1)
    final_year_only: Mapped[bool] = mapped_column(Integer, default=0)  # 0/1 as sqlite-friendly bool
    stipend_or_ctc: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    industry = relationship("IndustryProfile")
    required_skills = relationship("OpportunitySkill", back_populates="opportunity", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="opportunity", cascade="all, delete-orphan")


class OpportunitySkill(Base):
    __tablename__ = "opportunity_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    min_proficiency: Mapped[float] = mapped_column(Float, default=60.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    opportunity = relationship("Opportunity", back_populates="required_skills")
    skill = relationship("Skill")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="applied")
    # applied -> shortlisted -> assessment -> interview -> selected / rejected
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    match_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    opportunity = relationship("Opportunity", back_populates="applications")
    student = relationship("StudentProfile")
    feedback = relationship("IndustryFeedback", back_populates="application", uselist=False, cascade="all, delete-orphan")


class IndustryFeedback(Base):
    __tablename__ = "industry_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    technical_skill: Mapped[float] = mapped_column(Float, default=0.0)
    problem_solving: Mapped[float] = mapped_column(Float, default=0.0)
    communication: Mapped[float] = mapped_column(Float, default=0.0)
    teamwork: Mapped[float] = mapped_column(Float, default=0.0)
    professionalism: Mapped[float] = mapped_column(Float, default=0.0)
    comments: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="feedback")
