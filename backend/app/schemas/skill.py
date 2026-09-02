from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EvidenceOut(BaseModel):
    id: int
    type: str
    title: str
    description: str
    source_url: str
    status: str
    signal_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceCreate(BaseModel):
    skill_name: str
    type: str  # certificate | github | project
    title: str
    description: str = ""
    source_url: str = ""


class SkillHistoryPoint(BaseModel):
    score: float
    recorded_at: datetime
    reason: str

    class Config:
        from_attributes = True


class StudentSkillOut(BaseModel):
    id: int
    skill_name: str
    category: str
    proficiency_score: float
    confidence_level: str
    last_assessed_at: Optional[datetime]
    evidence_count: int
    evidences: list[EvidenceOut] = []

    class Config:
        from_attributes = True


class SkillPassportOut(BaseModel):
    student_id: int
    full_name: str
    career_goal: str
    career_readiness: float
    skills: list[StudentSkillOut]
