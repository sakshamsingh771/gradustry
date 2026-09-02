from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.skill import Skill, StudentSkill, Evidence, SkillScoreHistory
from app.models.assessment import AssessmentAttempt, CareerRole
from app.models.opportunity import Application, Opportunity
from app.models.ai import ResumeAnalysis, GitHubAnalysis, AdaptiveAssessmentSession, AIConversation

from app.ai import resume_analyzer, github_analyzer, evidence_verifier, adaptive_assessment
from app.ai import roadmap_generator, skill_gap_engine, career_readiness, career_copilot, matcher
from app.ai.ai_provider import ai_provider
from app.ai.github_analyzer import InvalidRepoUrl, GitHubRateLimited

router = APIRouter(prefix="/api/ai", tags=["ai"])


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
    ss = db.query(StudentSkill).filter(StudentSkill.student_id == student_id, StudentSkill.skill_id == skill_id).first()
    if not ss:
        ss = StudentSkill(student_id=student_id, skill_id=skill_id, proficiency_score=0.0, confidence_level="None")
        db.add(ss)
        db.flush()
    return ss


def _recompute(db: Session, ss: StudentSkill, reason: str):
    from app.ai import evidence_engine
    evidences = [{"type": e.type, "status": e.status, "signal_score": e.signal_score} for e in ss.evidences]
    result = evidence_engine.recompute_student_skill(evidences)
    ss.proficiency_score = result["proficiency_score"]
    ss.confidence_level = result["confidence_level"]
    db.add(SkillScoreHistory(student_skill_id=ss.id, score=ss.proficiency_score, reason=reason))
    db.commit()


@router.get("/status")
def ai_status(user: User = Depends(require_roles("student", "college", "industry", "admin"))):
    """Whether a real AI provider is configured — the frontend uses this to label results honestly."""
    return {"ai_configured": ai_provider.is_configured(), "provider": ai_provider.provider if ai_provider.is_configured() else "none"}


# ============================== Resume Analyzer ==============================

class AcceptSkillsRequest(BaseModel):
    skills: List[Dict[str, Any]]  # [{name, confidence, evidence}]
    source: str  # "resume" | "github"
    source_title: str = ""


@router.post("/resume/analyze")
async def analyze_resume(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)

    # Safe Guard: Validate filename presence and type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing or invalid")

    filename: str = file.filename

    if not filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(status_code=400, detail="Upload a PDF, DOCX, or plain text resume")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    extraction, used_ai = await resume_analyzer.analyze_resume(filename, content)

    record = ResumeAnalysis(
        student_id=profile.id, filename=filename, result_json=extraction.model_dump(),
        used_ai=used_ai, model_name=ai_provider.model if used_ai else "deterministic-fallback",
    )
    db.add(record)
    db.commit()

    return {
        "analysis_id": record.id, "used_ai": used_ai,
        "extraction": extraction.model_dump(),
        "note": "AI detected — pending your review. Nothing is added to your Skill Passport until you accept it below.",
    }


# ============================== GitHub Analyzer ==============================

class GitHubAnalyzeRequest(BaseModel):
    repo_url: str


@router.post("/github/analyze")
async def analyze_github(payload: GitHubAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    try:
        result, used_ai = await github_analyzer.analyze_github_repo(payload.repo_url)
    except InvalidRepoUrl as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GitHubRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Couldn't reach GitHub — check the URL and try again")

    record = GitHubAnalysis(
        student_id=profile.id, repo_url=payload.repo_url, result_json=result.model_dump(),
        used_ai=used_ai, model_name=ai_provider.model if used_ai else "deterministic-fallback",
    )
    db.add(record)
    db.commit()

    return {
        "analysis_id": record.id, "used_ai": used_ai,
        "analysis": result.model_dump(),
        "note": "AI-derived evidence confidence — not a verified developer skill. Review before accepting.",
    }


@router.post("/skills/accept")
def accept_ai_skills(payload: AcceptSkillsRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    """Shared accept step for both Resume and GitHub extraction — student reviews before anything counts."""
    profile = _student_profile(db, user)
    if payload.source not in ("resume", "github"):
        raise HTTPException(status_code=400, detail="source must be 'resume' or 'github'")

    from app.ai import evidence_engine
    accepted = []
    for s in payload.skills:
        name, confidence = s.get("name"), float(s.get("confidence", 0.5))
        if not name:
            continue
        skill = _get_or_create_skill(db, str(name))
        ss = _get_or_create_student_skill(db, profile.id, skill.id)
        signal = round(evidence_engine.TYPE_BASE_SIGNAL[payload.source] * confidence, 1)
        db.add(Evidence(
            student_skill_id=ss.id, type=payload.source,
            title=f"AI detected via {payload.source}" + (f" — {payload.source_title}" if payload.source_title else ""),
            description=str(s.get("evidence", "")), status="pending_review", signal_score=signal,
        ))
        db.flush()
        _recompute(db, ss, reason=f"AI {payload.source} evidence accepted: {name}")
        accepted.append(name)

    return {"detail": f"Accepted {len(accepted)} skill(s) into your Skill Passport as pending review.", "skills": accepted}


# ============================== Evidence Intelligence ==============================

@router.post("/evidence/{evidence_id}/analyze")
async def analyze_evidence(evidence_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    
    # Safe Guard: Check evidence existence and relation
    if not evidence or not evidence.student_skill or evidence.student_skill.student_id != profile.id:
        raise HTTPException(status_code=404, detail="Evidence not found")

    skill_name = evidence.student_skill.skill.name
    result, used_ai = await evidence_verifier.analyze_evidence(skill_name, evidence.type, evidence.title, evidence.description)
    return {"used_ai": used_ai, "analysis": result.model_dump(), "note": "This assesses relevance and consistency — it does not verify authenticity."}


# ============================== Adaptive Assessment ==============================

class AdaptiveStartRequest(BaseModel):
    skill_name: str


class AdaptiveAnswerRequest(BaseModel):
    session_id: int
    answer: List[str]


def _public_question(q: dict) -> dict:
    return {k: v for k, v in q.items() if k not in ("correct_answer", "explanation")}


@router.post("/assessment/adaptive/start")
async def start_adaptive(payload: AdaptiveStartRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    skill = _get_or_create_skill(db, payload.skill_name)

    topic = adaptive_assessment.initial_topic(None, payload.skill_name)
    question, used_ai = await adaptive_assessment.generate_question(payload.skill_name, topic, "intermediate")

    session = AdaptiveAssessmentSession(
        student_id=profile.id, skill_id=skill.id, current_topic=topic, current_difficulty="intermediate",
        current_question=question, used_ai_any=used_ai,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"session_id": session.id, "skill_name": payload.skill_name, "step": 1, "max_steps": session.max_steps,
            "difficulty": session.current_difficulty, "question": _public_question(question), "used_ai": used_ai}


@router.post("/assessment/adaptive/next")
async def adaptive_next(payload: AdaptiveAnswerRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    session = db.query(AdaptiveAssessmentSession).filter(
        AdaptiveAssessmentSession.id == payload.session_id, AdaptiveAssessmentSession.student_id == profile.id
    ).first()
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=404, detail="No active adaptive session found")

    current_q = session.current_question
    is_correct = sorted(payload.answer) == sorted(current_q["correct_answer"])
    session.correct_count += int(is_correct)
    session.steps_completed += 1
    if not is_correct:
        weak = session.weak_topics or []
        if current_q["topic"] not in weak:
            weak.append(current_q["topic"])
        session.weak_topics = weak

    history = session.history or []
    history.append({
        "topic": current_q["topic"], "difficulty": current_q["difficulty"], "prompt": current_q["prompt"],
        "your_answer": payload.answer, "correct_answer": current_q["correct_answer"],
        "is_correct": is_correct, "explanation": current_q.get("explanation", ""),
    })
    session.history = history

    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Associated skill not found")

    if session.steps_completed >= session.max_steps:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.score_percent = round((session.correct_count / session.steps_completed) * 100, 1)

        ss = _get_or_create_student_skill(db, profile.id, session.skill_id)
        from app.ai import evidence_engine
        signal = evidence_engine.score_single_evidence("assessment", "verified", override_score=session.score_percent)
        db.add(Evidence(
            student_skill_id=ss.id, type="assessment",
            title=f"Adaptive AI assessment — {skill.name}",
            description=f"Scored {session.score_percent}% · weak topics: {', '.join(session.weak_topics) or 'none'}",
            status="verified", signal_score=signal,
        ))
        db.flush()
        _recompute(db, ss, reason="adaptive assessment completed")
        db.commit()

        return {
            "session_id": session.id, "status": "completed", "score_percent": session.score_percent,
            "correct_count": session.correct_count, "steps_completed": session.steps_completed,
            "weak_topics": session.weak_topics, "new_proficiency": ss.proficiency_score,
            "confidence_level": ss.confidence_level, "last_feedback": history[-1],
        }

    next_difficulty = adaptive_assessment.next_difficulty(session.current_difficulty, is_correct)
    next_topic = adaptive_assessment.pick_next_topic(skill.name, session.current_topic, is_correct)
    next_question, used_ai = await adaptive_assessment.generate_question(skill.name, next_topic, next_difficulty)

    session.current_difficulty = next_difficulty
    session.current_topic = next_topic
    session.current_question = next_question
    session.used_ai_any = session.used_ai_any or used_ai
    db.commit()

    return {
        "session_id": session.id, "status": "in_progress", "step": session.steps_completed + 1,
        "max_steps": session.max_steps, "difficulty": next_difficulty,
        "question": _public_question(next_question), "last_feedback": history[-1], "used_ai": used_ai,
    }


# ============================== AI Roadmap ==============================

class RoadmapRequest(BaseModel):
    target_career: str
    weekly_hours: int = 6


@router.post("/roadmap/generate")
async def ai_roadmap(payload: RoadmapRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    role = db.query(CareerRole).filter(CareerRole.title == payload.target_career).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"No career role found named '{payload.target_career}'")

    rows = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    current_skills = {r.skill.name: r.proficiency_score for r in rows if r.skill}

    requirements = [{"skill_name": r.skill.name, "target_proficiency": r.target_proficiency, "importance": r.importance} for r in role.requirements if r.skill]
    student_skill_map = {r.skill.name: {"proficiency_score": r.proficiency_score, "confidence_level": r.confidence_level, "evidence_count": len(r.evidences)} for r in rows if r.skill}
    report = skill_gap_engine.build_gap_report(role.title, requirements, student_skill_map)
    gaps = [{"skill_name": g["skill_name"], "current_score": g["current_score"], "target_score": g["target_score"]}
            for g in (report["high_gap"] + report["medium_gap"] + report["low_gap"])]

    ai_result, used_ai = await roadmap_generator.generate_ai_roadmap(payload.target_career, current_skills, gaps, payload.weekly_hours)
    if used_ai and ai_result:
        return {"used_ai": True, "roadmap": ai_result.model_dump()}

    steps = []
    for g in gaps[:4]:
        skill_steps = roadmap_generator.generate_roadmap(g["skill_name"], g["current_score"], g["target_score"])
        for i, s in enumerate(skill_steps):
            steps.append({"week_label": f"{g['skill_name']} — step {i + 1}", "title": s["title"], "description": s["description"], "resource_type": s["resource_type"], "estimated_hours": 4})
    return {
        "used_ai": False,
        "roadmap": {"target_career": payload.target_career, "priority_skills": [g["skill_name"] for g in gaps[:4]], "steps": steps},
        "note": "AI enhancement temporarily unavailable — showing the standard gap-closure roadmap.",
    }


# ============================== Career Readiness Insights ==============================

@router.get("/insights")
def readiness_insights(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    rows = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    student_skills = [
        {"proficiency_score": r.proficiency_score, "confidence_level": r.confidence_level, "evidence_count": len(r.evidences),
         "evidences": [{"type": e.type} for e in r.evidences]}
        for r in rows
    ]

    recent_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id == profile.id, AssessmentAttempt.completed_at.isnot(None)
    ).order_by(AssessmentAttempt.completed_at.desc()).limit(10).all()
    assessment_scores = [a.score_percent for a in recent_attempts]

    applications = db.query(Application).filter(Application.student_id == profile.id).all()
    feedback_scores = []
    for a in applications:
        if a.feedback:
            feedback_scores.append(a.feedback.technical_skill)

    history_dates = []
    for r in rows:
        history_dates += [h.recorded_at for h in r.history]

    breakdown = career_readiness.compute_readiness_breakdown(student_skills, assessment_scores, feedback_scores, history_dates)
    return breakdown


# ============================== Career Copilot ==============================

class CopilotChatRequest(BaseModel):
    question: str


def _build_copilot_context(db: Session, profile: StudentProfile) -> dict:
    rows = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    skills_map = {r.skill.name: {"proficiency_score": r.proficiency_score, "confidence_level": r.confidence_level, "evidence_count": len(r.evidences)} for r in rows if r.skill}
    readiness = round(sum(v["proficiency_score"] for v in skills_map.values()) / len(skills_map), 1) if skills_map else None

    context = {"career_goal": profile.career_goal, "career_readiness": readiness}

    if profile.career_goal:
        role = db.query(CareerRole).filter(CareerRole.title == profile.career_goal).first()
        if role:
            requirements = [{"skill_name": r.skill.name, "target_proficiency": r.target_proficiency, "importance": r.importance} for r in role.requirements if r.skill]
            report = skill_gap_engine.build_gap_report(role.title, requirements, skills_map)
            context["career_readiness"] = report["career_readiness"]
            context["gap_matched"] = [g["skill_name"] for g in report["matched"]]
            context["gap_high"] = report["high_gap"]
            context["gap_medium"] = report["medium_gap"]

    opps = db.query(Opportunity).filter(Opportunity.is_active == 1).all()
    best = None
    for opp in opps:
        required = [{"skill_name": rs.skill.name, "min_proficiency": rs.min_proficiency, "weight": rs.weight} for rs in opp.required_skills if rs.skill]
        m = matcher.score_match(skills_map, required)
        if best is None or m["match_score"] > best["match_score"]:
            best = {"title": opp.title, "match_score": m["match_score"], "below_target_skills": m["below_target_skills"]}
    context["best_opportunity"] = best
    return context


@router.post("/copilot/chat")
async def copilot_chat(payload: CopilotChatRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    context = _build_copilot_context(db, profile)
    answer, used_ai = await career_copilot.answer_question(payload.question, context)

    db.add(AIConversation(student_id=profile.id, question=payload.question, answer=answer.answer, used_data_points=answer.used_data_points, used_ai=used_ai))
    db.commit()

    return {"answer": answer.answer, "used_data_points": answer.used_data_points, "used_ai": used_ai}


@router.get("/copilot/history")
def copilot_history(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    convos = db.query(AIConversation).filter(AIConversation.student_id == profile.id).order_by(AIConversation.created_at.desc()).limit(20).all()
    return [{"id": c.id, "question": c.question, "answer": c.answer, "used_ai": c.used_ai, "created_at": c.created_at} for c in reversed(convos)]