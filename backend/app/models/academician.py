from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AcademicianProfile(Base):
    """Profile for the ACADEMICIAN/FACULTY role.

    Mirrors the pattern used by StudentProfile / CollegeProfile / IndustryProfile:
    a 1:1 extension of `User` keyed on user_id, holding role-specific fields.
    """

    __tablename__ = "academician_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Optional link to a registered CollegeProfile (mirrors StudentProfile.college_id).
    # Nullable because an academician may belong to an institution not yet on
    # the platform — `institution` free-text still captures that case.
    college_id: Mapped[int | None] = mapped_column(ForeignKey("college_profiles.id"), nullable=True)

    designation: Mapped[str] = mapped_column(String(255), default="")  # e.g. Assistant Professor
    institution: Mapped[str] = mapped_column(String(255), default="")  # free-text institution name
    department: Mapped[str] = mapped_column(String(255), default="")
    area_of_expertise: Mapped[str] = mapped_column(String(500), default="")
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str] = mapped_column(Text, default="")  # professional information / summary

    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="academician_profile")
    college = relationship("CollegeProfile")
