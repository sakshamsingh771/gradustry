from pydantic import BaseModel


class SkillGapItem(BaseModel):
    skill_name: str
    current_score: float
    target_score: float
    gap: float
    severity: str  # matched|low|medium|high
    reason: str


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


class SkillRoadmapOut(BaseModel):
    skill_name: str
    baseline_score: float
    target_score: float
    current_score: float
    steps: list[RoadmapStepOut]


class CareerRoleOut(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True
