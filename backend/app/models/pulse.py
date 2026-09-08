from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

CATEGORIES = [
    "AI & Machine Learning", "Web Development", "Data Science", "Cybersecurity",
    "Cloud & DevOps", "Programming", "Mobile Development", "IoT", "Startups",
    "Developer Tools", "Industry Trends", "Career & Hiring",
]
IMPACT_LEVELS = ["low", "medium", "high"]


class PulseArticle(Base):
    __tablename__ = "pulse_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), index=True)
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[str] = mapped_column(String(500), default="")
    relevant_skills: Mapped[str] = mapped_column(String(500), default="")
    impact: Mapped[str] = mapped_column(String(20), default="medium")
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def skills_list(self) -> list[str]:
        return [s.strip() for s in self.relevant_skills.split(",") if s.strip()]

    def tags_list(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class SavedPulseArticle(Base):
    __tablename__ = "saved_pulse_articles"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_user_article"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pulse_articles.id"), index=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    article = relationship("PulseArticle")