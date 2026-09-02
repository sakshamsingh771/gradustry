import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Enum, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    college = "college"
    industry = "industry"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Enum(RoleEnum), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    college_profile = relationship("CollegeProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    industry_profile = relationship("IndustryProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("college_profiles.id"), nullable=True)
    branch: Mapped[str] = mapped_column(String(255), default="")
    year_of_study: Mapped[int] = mapped_column(Integer, default=1)
    career_goal: Mapped[str] = mapped_column(String(255), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    github_username: Mapped[str] = mapped_column(String(255), default="")
    profile_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="student_profile")
    college = relationship("CollegeProfile", back_populates="students")


class CollegeProfile(Base):
    __tablename__ = "college_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    college_name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255), default="")
    affiliation: Mapped[str] = mapped_column(String(255), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="college_profile")
    students = relationship("StudentProfile", back_populates="college")


class IndustryProfile(Base):
    __tablename__ = "industry_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    company_name: Mapped[str] = mapped_column(String(255))
    industry_sector: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="industry_profile")
