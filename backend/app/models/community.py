import enum
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CommunityType(str, enum.Enum):
    interest = "interest"
    college = "college"


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(Enum(CommunityType), index=True)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("college_profiles.id"), nullable=True, index=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    college = relationship("CollegeProfile")


class CommunityMembership(Base):
    __tablename__ = "community_memberships"
    __table_args__ = (UniqueConstraint("user_id", "community_id", name="uq_user_community"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    community = relationship("Community")


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    community = relationship("Community")
    author = relationship("User")


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post = relationship("CommunityPost")
    author = relationship("User")