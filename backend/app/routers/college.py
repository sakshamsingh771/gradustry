from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, CollegeProfile, StudentProfile
from app.models.skill import StudentSkill
from app.models.opportunity import Application
from app.models.college_membership import CollegeMembership, MembershipStatus
from app.ai import career_readiness

router = APIRouter(prefix="/api/college", tags=["college"])


def _college_profile(db: Session, user: User) -> CollegeProfile:
    profile = db.query(CollegeProfile).filter(CollegeProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="College profile not found")
    return profile


def _verified_student_profiles(db: Session, college_id: int) -> list[StudentProfile]:
    verified_user_ids = [
        m.user_id for m in db.query(CollegeMembership).filter(
            CollegeMembership.college_id == college_id, CollegeMembership.status == MembershipStatus.verified
        ).all()
    ]
    if not verified_user_ids:
        return []
    return db.query(StudentProfile).filter(StudentProfile.user_id.in_(verified_user_ids)).all()


@router.get("/memberships/pending")
def list_pending_memberships(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    rows = db.query(CollegeMembership).filter(
        CollegeMembership.college_id == college.id, CollegeMembership.status == MembershipStatus.pending
    ).all()
    return [
        {"membership_id": m.id, "user_id": m.user_id, "student_name": m.user.full_name if m.user else None,
         "email": m.user.email if m.user else None, "requested_at": m.created_at}
        for m in rows
    ]


@router.post("/memberships/{membership_id}/approve")
def approve_membership(membership_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    from datetime import datetime
    from app.models.college_membership import VerificationMethod
    college = _college_profile(db, user)
    membership = db.query(CollegeMembership).filter(
        CollegeMembership.id == membership_id, CollegeMembership.college_id == college.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership request not found")
    membership.status = MembershipStatus.verified
    membership.verification_method = VerificationMethod.admin_approval
    membership.decided_at = datetime.utcnow()
    membership.decided_by_user_id = user.id
    db.commit()
    return {"detail": "Membership approved", "status": "verified"}


@router.post("/memberships/{membership_id}/reject")
def reject_membership(membership_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    from datetime import datetime
    college = _college_profile(db, user)
    membership = db.query(CollegeMembership).filter(
        CollegeMembership.id == membership_id, CollegeMembership.college_id == college.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership request not found")
    membership.status = MembershipStatus.rejected
    membership.decided_at = datetime.utcnow()
    membership.decided_by_user_id = user.id
    db.commit()
    return {"detail": "Membership rejected", "status": "rejected"}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id)
    student_ids = [s.id for s in students]

    if not student_ids:
        return {
            "college_name": college.college_name, "total_students": 0, "average_readiness": 0.0,
            "skill_distribution": [], "top_gaps": [], "placement_stats": {"applications": 0, "selected": 0},
        }

    skills = db.query(StudentSkill).filter(StudentSkill.student_id.in_(student_ids)).all()
    per_skill_scores = defaultdict(list)
    for s in skills:
        per_skill_scores[s.skill.name].append(s.proficiency_score)

    skill_distribution = [
        {"skill_name": name, "average_score": round(sum(scores) / len(scores), 1), "student_count": len(scores)}
        for name, scores in per_skill_scores.items()
    ]
    skill_distribution.sort(key=lambda x: x["average_score"])
    top_gaps = skill_distribution[:5]

    readiness_scores = [career_readiness.compute_for_student(db, s)["overall_readiness"] for s in students]
    average_readiness = round(sum(readiness_scores) / len(readiness_scores), 1) if readiness_scores else 0.0

    applications = db.query(Application).filter(Application.student_id.in_(student_ids)).all()
    selected = sum(1 for a in applications if a.status == "selected")

    return {
        "college_name": college.college_name,
        "total_students": len(students),
        "average_readiness": average_readiness,
        "skill_distribution": skill_distribution,
        "top_gaps": top_gaps,
        "placement_stats": {"applications": len(applications), "selected": selected},
    }


@router.get("/students")
def list_students(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id)
    out = []
    for s in students:
        readiness = career_readiness.compute_for_student(db, s)["overall_readiness"]
        out.append({
            "student_id": s.id, "full_name": s.user.full_name, "branch": s.branch,
            "year_of_study": s.year_of_study, "career_goal": s.career_goal, "readiness": readiness,
        })
    return out
