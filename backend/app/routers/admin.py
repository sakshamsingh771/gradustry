from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile, CollegeProfile, IndustryProfile
from app.models.skill import Evidence, SkillScoreHistory
from app.ai import evidence_engine
from app.models.opportunity import Opportunity, Application
from app.models.assessment import CareerRole, Question

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return {
        "students": db.query(StudentProfile).count(),
        "colleges": db.query(CollegeProfile).count(),
        "companies": db.query(IndustryProfile).count(),
        "opportunities": db.query(Opportunity).count(),
        "applications": db.query(Application).count(),
        "pending_evidence": db.query(Evidence).filter(Evidence.status == "pending_review").count(),
        "pending_colleges": db.query(CollegeProfile).filter(CollegeProfile.verified == False).count(),  # noqa: E712
        "pending_companies": db.query(IndustryProfile).filter(IndustryProfile.verified == False).count(),  # noqa: E712
        "pending_questions": db.query(Question).filter(Question.status == "pending_review").count(),
        "career_roles": db.query(CareerRole).count(),
    }


@router.get("/moderation/evidence")
def evidence_queue(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    items = db.query(Evidence).filter(Evidence.status.in_(["pending_review", "needs_review", "suspicious"])).all()
    return [
        {
            "id": e.id, "type": e.type, "title": e.title, "status": e.status,
            "signal_score": e.signal_score, "student_name": e.student_skill.student.user.full_name,
            "skill_name": e.student_skill.skill.name,
        } for e in items
    ]


@router.patch("/moderation/evidence/{evidence_id}")
def moderate_evidence(
    evidence_id: int, new_status: str,
    db: Session = Depends(get_db), user: User = Depends(require_roles("admin")),
):
    valid = {"verified", "pending_review", "needs_review", "suspicious"}
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(valid)}")
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
        evidence.status = new_status
    evidence.signal_score = evidence_engine.score_single_evidence(evidence.type, new_status)
    db.flush()

    student_skill = evidence.student_skill
    evidences = [{"type": e.type, "status": e.status, "signal_score": e.signal_score} for e in student_skill.evidences]
    result = evidence_engine.recompute_student_skill(evidences)
    student_skill.proficiency_score = result["proficiency_score"]
    student_skill.confidence_level = result["confidence_level"]
    db.add(SkillScoreHistory(student_skill_id=student_skill.id, score=result["proficiency_score"],
                              reason=f"admin moderation: {evidence.title} -> {new_status}"))
    db.commit()
    return {"detail": "Updated", "evidence_status": evidence.status,
            "skill_proficiency_score": student_skill.proficiency_score,
            "skill_confidence_level": student_skill.confidence_level}


@router.get("/colleges")
def list_colleges(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    colleges = db.query(CollegeProfile).all()
    return [{"id": c.id, "college_name": c.college_name, "city": c.city, "verified": c.verified} for c in colleges]


@router.patch("/colleges/{college_id}/verify")
def verify_college(college_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    college = db.query(CollegeProfile).filter(CollegeProfile.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    college.verified = True
    db.commit()
    return {"detail": f"{college.college_name} verified"}


@router.get("/companies")
def list_companies(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    companies = db.query(IndustryProfile).all()
    return [{"id": c.id, "company_name": c.company_name, "verified": c.verified} for c in companies]


@router.patch("/companies/{company_id}/verify")
def verify_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    company = db.query(IndustryProfile).filter(IndustryProfile.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.verified = True
    db.commit()
    return {"detail": f"{company.company_name} verified"}


@router.post("/career-roles")
def create_career_role(
    title: str, description: str = "",
    db: Session = Depends(get_db), user: User = Depends(require_roles("admin")),
):
    if db.query(CareerRole).filter(CareerRole.title == title).first():
        raise HTTPException(status_code=400, detail="A role with this title already exists")
    role = CareerRole(title=title, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return {"id": role.id, "title": role.title}
