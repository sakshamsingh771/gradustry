from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RequiredSkillIn(BaseModel):
    skill_name: str
    min_proficiency: float = 60.0
    weight: float = 1.0


class OpportunityCreate(BaseModel):
    title: str
    role_type: str = "internship"
    description: str = ""
    location: str = "Remote"
    min_year_of_study: int = 1
    final_year_only: bool = False
    stipend_or_ctc: str = ""
    required_skills: list[RequiredSkillIn]


class RequiredSkillOut(BaseModel):
    skill_name: str
    min_proficiency: float
    weight: float

    class Config:
        from_attributes = True


class OpportunityOut(BaseModel):
    id: int
    title: str
    role_type: str
    description: str
    location: str
    company_name: str
    min_year_of_study: int
    final_year_only: bool
    stipend_or_ctc: str
    required_skills: list[RequiredSkillOut]
    created_at: datetime

    class Config:
        from_attributes = True


class MatchExplanation(BaseModel):
    matched_skills: list[str]
    below_target_skills: list[str]
    missing_eligibility: list[str]
    relevant_evidence_count: int
    is_eligible: bool
    strengths: list[str] = []
    weaknesses: list[str] = []
    related_skills_recognized: list[str] = []
    recommendation_reason: str = ""
    ai_enhanced: bool = False


class OpportunityMatchOut(BaseModel):
    opportunity: OpportunityOut
    match_score: float
    explanation: MatchExplanation


class ApplyRequest(BaseModel):
    opportunity_id: int


class ApplicationOut(BaseModel):
    id: int
    opportunity_id: int
    opportunity_title: str
    company_name: str
    student_id: int
    student_name: Optional[str] = None
    status: str
    match_score: float
    applied_at: datetime

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str


class IndustryFeedbackCreate(BaseModel):
    application_id: int
    technical_skill: float
    problem_solving: float
    communication: float
    teamwork: float
    professionalism: float
    comments: str = ""
