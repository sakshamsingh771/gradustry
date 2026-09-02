from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, CollegeProfile, StudentProfile
from app.models.skill import StudentSkill
from app.models.opportunity import Application

router = APIRouter(prefix="/api/college", tags=["college"])


def _college_profile(db: Session, user: User) -> CollegeProfile:
    profile = db.query(CollegeProfile).filter(CollegeProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="College profile not found")
    return profile


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    students = db.query(StudentProfile).filter(StudentProfile.college_id == college.id).all()
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

    all_scores = [s.proficiency_score for s in skills]
    average_readiness = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

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
    students = db.query(StudentProfile).filter(StudentProfile.college_id == college.id).all()
    out = []
    for s in students:
        skills = db.query(StudentSkill).filter(StudentSkill.student_id == s.id).all()
        readiness = round(sum(sk.proficiency_score for sk in skills) / len(skills), 1) if skills else 0.0
        out.append({
            "student_id": s.id, "full_name": s.user.full_name, "branch": s.branch,
            "year_of_study": s.year_of_study, "career_goal": s.career_goal, "readiness": readiness,
        })
    return out
