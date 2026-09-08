import enum
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MembershipStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class VerificationMethod(str, enum.Enum):
    self_reported = "self_reported"
    college_email = "college_email"
    admin_approval = "admin_approval"
    platform_admin = "platform_admin"


class CollegeMembership(Base):
    __tablename__ = "college_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("college_profiles.id"), index=True)

    status: Mapped[str] = mapped_column(Enum(MembershipStatus), default=MembershipStatus.pending, index=True)
    verification_method: Mapped[str] = mapped_column(Enum(VerificationMethod), default=VerificationMethod.self_reported)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    college = relationship("CollegeProfile")