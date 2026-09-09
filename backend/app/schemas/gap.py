from pydantic import BaseModel


class SkillGapItem(BaseModel):
    skill_name: str
    current_score: float
    target_score: float
    gap: float
    severity: str  # matched|low|medium|high
    priority: str  # High|Medium|Low
    reason: str
    reasons: list[str] = []
    missing_subskills: list[str] = []
    blocked_by_prerequisites: list[str] = []

class SkillGapReport(BaseModel):
    role_title: str
    career_readiness: float
    matched: list[SkillGapItem]
    low_gap: list[SkillGapItem]
    medium_gap: list[SkillGapItem]
    high_gap: list[SkillGapItem]


class RoadmapStepOut(BaseModel):
    id: int
    order_index: int
    title: str
    description: str
    resource_type: str
    status: str

    class Config:
        from_attributes = True


# --- MOVED UP: LearningResourceOut is now defined before it is used ---
class LearningResourceOut(BaseModel):
    id: int
    topic: str
    title: str
    provider: str
    url: str
    difficulty: str
    duration_minutes: int
    
    class Config:
        from_attributes = True


class SkillRoadmapOut(BaseModel):
    skill_name: str
    baseline_score: float
    target_score: float
    current_score: float
    steps: list[RoadmapStepOut]
    resources: list[LearningResourceOut] = []


class CareerRoleOut(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True
