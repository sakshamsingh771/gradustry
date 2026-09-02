from typing import Optional
from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: int
    topic: str
    difficulty: str
    question_type: str
    prompt: str
    options: list[str]

    class Config:
        from_attributes = True


class StartAssessmentRequest(BaseModel):
    skill_name: str
    topic_focus: Optional[str] = None  # if omitted, engine derives weakest sub-topics
    num_questions: int = 5


class StartAssessmentResponse(BaseModel):
    attempt_id: int
    skill_name: str
    topic_focus: str
    questions: list[QuestionOut]


class SubmitAssessmentRequest(BaseModel):
    attempt_id: int
    answers: dict[str, list[str]]  # question_id (str) -> selected option(s)


class SubmitAssessmentResponse(BaseModel):
    attempt_id: int
    score_percent: float
    previous_score: float
    delta: float
    skill_name: str
    new_proficiency: float
    confidence_level: str
    gap_status: str  # "Gap Closed" | "Gap Partially Closed" | "Needs More Work"
    per_question_feedback: list[dict]
