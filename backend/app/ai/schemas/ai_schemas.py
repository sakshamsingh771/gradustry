"""
AI Output Validation
---------------------
LLM output is never trusted directly. Every AI JSON response is parsed
through one of these Pydantic models; a ValidationError means the caller
falls back to its deterministic path, per the "AI + rule-based hybrid"
principle.
"""
from pydantic import BaseModel, Field, ValidationError  # noqa: F401


class ExtractedSkill(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = ""


class ResumeExtraction(BaseModel):
    name: str = ""
    education: list[str] = []
    experience: list[str] = []
    projects: list[str] = []
    skills: list[ExtractedSkill] = []
    programming_languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    cloud_tools: list[str] = []
    certifications: list[str] = []
    soft_skills: list[str] = []
    career_roles: list[str] = []


class GitHubSkill(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class GitHubAnalysisResult(BaseModel):
    repository: str
    skills: list[GitHubSkill] = []
    project_level: str = "beginner"  # beginner|intermediate|advanced
    evidence_quality: float = Field(ge=0.0, le=1.0, default=0.5)
    architecture_notes: str = ""


class EvidenceAIAnalysis(BaseModel):
    relevance_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    flags: list[str] = []


class AdaptiveQuestion(BaseModel):
    topic: str
    difficulty: str  # beginner|intermediate|advanced
    question_type: str = "mcq"
    prompt: str
    options: list[str]
    correct_answer: list[str]
    explanation: str


class AIRoadmapStep(BaseModel):
    week_label: str
    title: str
    description: str
    resource_type: str = "learning"
    estimated_hours: int = 4


class AIRoadmapResult(BaseModel):
    target_career: str
    priority_skills: list[str]
    steps: list[AIRoadmapStep]


class MatchExplanationAI(BaseModel):
    match_score_adjustment: float = Field(ge=-15.0, le=15.0, default=0.0)
    strengths: list[str] = []
    weaknesses: list[str] = []
    related_skills_recognized: list[str] = []
    recommendation_reason: str


class CopilotAnswer(BaseModel):
    answer: str
    used_data_points: list[str] = []
