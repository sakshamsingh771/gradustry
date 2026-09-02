from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.skill import Skill, StudentSkill, Evidence, SkillScoreHistory
from app.schemas.skill import EvidenceCreate, StudentSkillOut, SkillPassportOut
from app.ai import evidence_engine

router = APIRouter(prefix="/api/students", tags=["students"])


def _get_student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _get_or_create_student_skill(db: Session, student_id: int, skill_name: str) -> StudentSkill:
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        skill = Skill(name=skill_name, category="General")
        db.add(skill)
        db.flush()
    ss = db.query(StudentSkill).filter(
        StudentSkill.student_id == student_id, StudentSkill.skill_id == skill.id
    ).first()
    if not ss:
        ss = StudentSkill(student_id=student_id, skill_id=skill.id, proficiency_score=0.0, confidence_level="None")
        db.add(ss)
        db.flush()
    return ss


def _recompute_and_save(db: Session, student_skill: StudentSkill, reason: str):
    evidences = [
        {"type": e.type, "status": e.status, "signal_score": e.signal_score}
        for e in student_skill.evidences
    ]
    result = evidence_engine.recompute_student_skill(evidences)
    student_skill.proficiency_score = result["proficiency_score"]
    student_skill.confidence_level = result["confidence_level"]
    db.add(SkillScoreHistory(
        student_skill_id=student_skill.id,
        score=result["proficiency_score"],
        reason=reason,
    ))
    db.commit()
    db.refresh(student_skill)


@router.get("/colleges")
def list_colleges(db: Session = Depends(get_db)):
    from app.models.user import CollegeProfile
    colleges = db.query(CollegeProfile).all()
    return [{"id": c.id, "college_name": c.college_name, "city": c.city} for c in colleges]


@router.post("/me/join-college")
def join_college(
    college_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    from app.models.user import CollegeProfile
    profile = _get_student_profile(db, user)
    college = db.query(CollegeProfile).filter(CollegeProfile.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    profile.college_id = college.id
    db.commit()
    return {"detail": f"Joined {college.college_name}"}


@router.get("/me/skill-passport", response_model=SkillPassportOut)
def get_skill_passport(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    skills = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()

    skill_outs = []
    total, count = 0.0, 0
    for s in skills:
        total += s.proficiency_score
        count += 1
        skill_outs.append(StudentSkillOut(
            id=s.id,
            skill_name=s.skill.name,
            category=s.skill.category,
            proficiency_score=s.proficiency_score,
            confidence_level=s.confidence_level,
            last_assessed_at=s.last_assessed_at,
            evidence_count=len(s.evidences),
            evidences=s.evidences,
        ))

    readiness = round(total / count, 1) if count else 0.0
    return SkillPassportOut(
        student_id=profile.id,
        full_name=user.full_name,
        career_goal=profile.career_goal,
        career_readiness=readiness,
        skills=skill_outs,
    )


@router.post("/me/evidence", response_model=StudentSkillOut)
def add_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    ss = _get_or_create_student_skill(db, profile.id, payload.skill_name)

    signal = evidence_engine.score_single_evidence(payload.type, "pending_review")
    evidence = Evidence(
        student_skill_id=ss.id,
        type=payload.type,
        title=payload.title,
        description=payload.description,
        source_url=payload.source_url,
        status="pending_review",
        signal_score=signal,
    )
    db.add(evidence)
    db.commit()
    db.refresh(ss)

    _recompute_and_save(db, ss, reason=f"evidence added: {payload.title}")
    return StudentSkillOut(
        id=ss.id, skill_name=ss.skill.name, category=ss.skill.category,
        proficiency_score=ss.proficiency_score, confidence_level=ss.confidence_level,
        last_assessed_at=ss.last_assessed_at, evidence_count=len(ss.evidences), evidences=ss.evidences,
    )


@router.post("/me/evidence/{evidence_id}/verify", response_model=StudentSkillOut)
def verify_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student", "admin")),
):
    """MVP self-serve / admin verification step (stands in for OCR/cert-ID lookup)."""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence.status = "verified"
    evidence.signal_score = evidence_engine.score_single_evidence(evidence.type, "verified")
    db.commit()

    ss = evidence.student_skill
    _recompute_and_save(db, ss, reason=f"evidence verified: {evidence.title}")
    return StudentSkillOut(
        id=ss.id, skill_name=ss.skill.name, category=ss.skill.category,
        proficiency_score=ss.proficiency_score, confidence_level=ss.confidence_level,
        last_assessed_at=ss.last_assessed_at, evidence_count=len(ss.evidences), evidences=ss.evidences,
    )


@router.get("/me/skill-growth/{skill_name}")
def skill_growth(
    skill_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        return {"skill_name": skill_name, "history": []}
    ss = db.query(StudentSkill).filter(
        StudentSkill.student_id == profile.id, StudentSkill.skill_id == skill.id
    ).first()
    if not ss:
        return {"skill_name": skill_name, "history": []}
    history = sorted(ss.history, key=lambda h: h.recorded_at)
    return {
        "skill_name": skill_name,
        "history": [{"score": h.score, "recorded_at": h.recorded_at, "reason": h.reason} for h in history],
    }
