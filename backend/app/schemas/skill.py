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


class ProfileStrengthOut(BaseModel):
    score: float
    checklist: dict[str, bool]  # e.g. {"personal_info": True, "skills": False, ...}


class StudentProfileOut(BaseModel):
    full_name: str
    email: str
    branch: str
    year_of_study: int
    career_goal: str
    bio: str
    github_username: str
    profile_visible: bool
    college_name: Optional[str] = None
    strength: ProfileStrengthOut

    class Config:
        from_attributes = True


class StudentProfileUpdate(BaseModel):
    branch: Optional[str] = None
    year_of_study: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None
    github_username: Optional[str] = None
    profile_visible: Optional[bool] = None


class ActivityStatusOut(BaseModel):
    resume_analyzed: bool
    resume_last_analyzed_at: Optional[datetime]
    resume_skills_detected: int
    github_connected: bool
    github_last_analyzed_at: Optional[datetime]
    github_repos_analyzed: int