from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RequiredSkillIn(BaseModel):
    skill_name: str
    min_proficiency: float = 60.0
    weight: float = 1.0


class OpportunityCreate(BaseModel):
    title: str
    role_type: str = "internship"
    audience: str = "student"  # "student" | "academician"
    description: str = ""
    location: str = "Remote"
    min_year_of_study: int = 1
    final_year_only: bool = False
    stipend_or_ctc: str = ""
    duration: str = ""              # e.g. "6 weeks" — Learning Hub programs
    capacity: Optional[int] = None  # seats available; None = unlimited
    eligibility_notes: str = ""     # free-text eligibility beyond year/final_year
    application_deadline: Optional[datetime] = None
    required_skills: list[RequiredSkillIn] = []


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
    audience: str = "student"
    description: str
    location: str
    company_name: str
    min_year_of_study: int
    final_year_only: bool
    stipend_or_ctc: str
    duration: str = ""
    capacity: Optional[int] = None
    eligibility_notes: str = ""
    application_deadline: Optional[datetime] = None
    enrolled_count: int = 0
    required_skills: list[RequiredSkillOut]
    created_at: datetime

    class Config:
        from_attributes = True


class EligibilityCheckOut(BaseModel):
    check: str
    passed: bool
    detail: str


class SkillBreakdownItem(BaseModel):
    skill_name: str
    current_score: float
    required_score: float
    percent_of_requirement: float
    verification_state: str  # demonstrated|partially_demonstrated|missing|unverified — same as Skill Gap Engine
    weight: float


class MatchExplanation(BaseModel):
    matched_skills: list[str]
    below_target_skills: list[str]
    missing_eligibility: list[str]
    eligibility_checks: list[EligibilityCheckOut] = []
    skill_breakdown: list[SkillBreakdownItem] = []
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
    applicant_type: str = "student"  # "student" | "academician"
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    academician_id: Optional[int] = None
    academician_name: Optional[str] = None
    status: str
    match_score: float
    applied_at: datetime

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str


class SkillRatingIn(BaseModel):
    skill_name: str
    rating: float = Field(ge=0, le=5)  # observed proficiency, out of 5 — only for skills actually evaluated


class IndustryFeedbackCreate(BaseModel):
    application_id: int
    technical_skill: float = Field(ge=0, le=10)
    problem_solving: float = Field(ge=0, le=10)
    communication: float = Field(ge=0, le=10)
    teamwork: float = Field(ge=0, le=10)
    professionalism: float = Field(ge=0, le=10)
    comments: str = ""
    # Phase 5 — skill-specific ratings for skills genuinely observed/evaluated.
    # Only these (not every one of the opportunity's required_skills) become
    # Skill Passport evidence, so feedback never touches a skill that wasn't
    # actually assessed.
    skill_ratings: list[SkillRatingIn] = []