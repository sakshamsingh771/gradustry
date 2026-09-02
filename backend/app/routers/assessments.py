from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.skill import Skill, StudentSkill, SkillScoreHistory, Evidence
from app.models.assessment import Question, AssessmentAttempt
from app.schemas.assessment import (
    StartAssessmentRequest, StartAssessmentResponse, QuestionOut,
    SubmitAssessmentRequest, SubmitAssessmentResponse,
)
from app.ai import question_bank, evidence_engine, roadmap_generator

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def _student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _get_or_create_skill(db: Session, name: str) -> Skill:
    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name, category="General")
        db.add(skill)
        db.flush()
    return skill


def _get_or_create_student_skill(db: Session, student_id: int, skill_id: int) -> StudentSkill:
    ss = db.query(StudentSkill).filter(
        StudentSkill.student_id == student_id, StudentSkill.skill_id == skill_id
    ).first()
    if not ss:
        ss = StudentSkill(student_id=student_id, skill_id=skill_id, proficiency_score=0.0, confidence_level="None")
        db.add(ss)
        db.flush()
    return ss


def _persist_questions(db: Session, skill_id: int, generated: List[Dict[str, Any]]) -> List[Question]:
    """Persist AI-generated questions so they can be answered/reviewed; re-use if prompt already exists."""
    saved = []
    for g in generated:
        existing = db.query(Question).filter(
            Question.skill_id == skill_id, Question.prompt == g["prompt"]
        ).first()
        if existing:
            saved.append(existing)
            continue
        q = Question(
            skill_id=skill_id, topic=g["topic"], difficulty=g["difficulty"],
            question_type=g["question_type"], prompt=g["prompt"], options=g["options"],
            correct_answer=g["correct_answer"], explanation=g["explanation"],
            source=g["source"], status=g["status"],
        )
        db.add(q)
        db.flush()
        saved.append(q)
    return saved


@router.post("/start", response_model=StartAssessmentResponse)
def start_assessment(
    payload: StartAssessmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    skill = _get_or_create_skill(db, payload.skill_name)

    topics = [payload.topic_focus] if payload.topic_focus else None
    generated = question_bank.generate_questions(payload.skill_name, topics, payload.num_questions)
    questions = _persist_questions(db, skill.id, generated)

    ss = _get_or_create_student_skill(db, profile.id, skill.id)

    attempt = AssessmentAttempt(
        student_id=profile.id,
        skill_id=skill.id,
        topic_focus=payload.topic_focus or "General",
        question_ids=[q.id for q in questions],
        previous_score=ss.proficiency_score,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return StartAssessmentResponse(
        attempt_id=attempt.id,
        skill_name=skill.name,
        topic_focus=attempt.topic_focus,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.post("/submit", response_model=SubmitAssessmentResponse)
def submit_assessment(
    payload: SubmitAssessmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == payload.attempt_id, AssessmentAttempt.student_id == profile.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="This assessment has already been submitted")

    question_ids = attempt.question_ids or []
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
    q_by_id = {q.id: q for q in questions}

    correct = 0
    feedback = []
    for qid in question_ids:
        q = q_by_id.get(qid)
        if not q:
            continue
        given = payload.answers.get(str(qid), [])
        correct_ans = q.correct_answer or []
        is_correct = sorted(given) == sorted(correct_ans)
        if is_correct:
            correct += 1
        feedback.append({
            "question_id": qid, "prompt": q.prompt, "your_answer": given,
            "correct_answer": correct_ans, "is_correct": is_correct, "explanation": q.explanation,
        })

    total_questions = len(question_ids)
    score_percent = round((correct / total_questions) * 100, 1) if total_questions > 0 else 0.0
    attempt.score_percent = score_percent
    attempt.answers = payload.answers
    attempt.completed_at = datetime.utcnow()

    ss = _get_or_create_student_skill(db, profile.id, attempt.skill_id)

    # Assessment results become evidence, feeding the Evidence Confidence Engine.
    signal = evidence_engine.score_single_evidence("assessment", "verified", override_score=score_percent)
    db.add(Evidence(
        student_skill_id=ss.id, type="assessment", title=f"Assessment — {attempt.topic_focus}",
        description=f"Scored {score_percent}% on a focused assessment.", status="verified",
        signal_score=signal,
    ))
    db.flush()

    evidences = [{"type": e.type, "status": e.status, "signal_score": e.signal_score} for e in ss.evidences]
    result = evidence_engine.recompute_student_skill(evidences)
    baseline = attempt.previous_score or 0.0
    ss.proficiency_score = result["proficiency_score"]
    ss.confidence_level = result["confidence_level"]
    ss.last_assessed_at = datetime.utcnow()

    db.add(SkillScoreHistory(student_skill_id=ss.id, score=ss.proficiency_score, reason="assessment re-evaluation"))
    db.commit()

    gap_status = roadmap_generator.gap_status_after_reassessment(baseline, ss.proficiency_score, target=70.0)
    
    # Resolves Pylance Optional Member Access safely
    skill_record = db.query(Skill).filter(Skill.id == attempt.skill_id).first()
    skill_name = skill_record.name if skill_record else "Assessment Skill"

    return SubmitAssessmentResponse(
        attempt_id=attempt.id, score_percent=score_percent, previous_score=baseline,
        delta=round(ss.proficiency_score - baseline, 1), skill_name=skill_name,
        new_proficiency=ss.proficiency_score, confidence_level=ss.confidence_level,
        gap_status=gap_status, per_question_feedback=feedback,
    )