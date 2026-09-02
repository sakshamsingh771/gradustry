from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.assessment import CareerRole, RoadmapStep
from app.models.skill import StudentSkill
from app.schemas.gap import SkillGapReport, CareerRoleOut, SkillRoadmapOut, RoadmapStepOut
from app.ai import skill_gap_engine, roadmap_generator

router = APIRouter(prefix="/api/gap", tags=["skill-gap"])


def _student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _student_skill_map(db: Session, student_id: int) -> dict:
    rows = db.query(StudentSkill).filter(StudentSkill.student_id == student_id).all()
    return {
        r.skill.name: {
            "proficiency_score": r.proficiency_score,
            "confidence_level": r.confidence_level,
            "evidence_count": len(r.evidences),
        }
        for r in rows
    }


@router.get("/roles", response_model=list[CareerRoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(CareerRole).all()


@router.get("/report", response_model=SkillGapReport)
def gap_report(
    role_title: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    role = db.query(CareerRole).filter(CareerRole.title == role_title).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"No career role found named '{role_title}'")

    requirements = [
        {"skill_name": r.skill.name, "target_proficiency": r.target_proficiency, "importance": r.importance}
        for r in role.requirements
    ]
    student_skills = _student_skill_map(db, profile.id)
    report = skill_gap_engine.build_gap_report(role.title, requirements, student_skills)
    return report


@router.post("/roadmap/{skill_name}/generate", response_model=SkillRoadmapOut)
def generate_roadmap(
    skill_name: str,
    target_score: float = 70.0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    student_skills = _student_skill_map(db, profile.id)
    current = student_skills.get(skill_name, {}).get("proficiency_score", 0.0)

    from app.models.skill import Skill
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        skill = Skill(name=skill_name, category="General")
        db.add(skill)
        db.flush()

    db.query(RoadmapStep).filter(RoadmapStep.student_id == profile.id, RoadmapStep.skill_id == skill.id).delete()

    steps_data = roadmap_generator.generate_roadmap(skill_name, current, target_score)
    steps = []
    for sd in steps_data:
        step = RoadmapStep(student_id=profile.id, skill_id=skill.id, **sd)
        db.add(step)
        steps.append(step)
    db.commit()
    for s in steps:
        db.refresh(s)

    return SkillRoadmapOut(
        skill_name=skill_name, baseline_score=current, target_score=target_score,
        current_score=current, steps=[RoadmapStepOut.model_validate(s) for s in steps],
    )


@router.get("/roadmap/{skill_name}", response_model=SkillRoadmapOut)
def get_roadmap(
    skill_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    from app.models.skill import Skill
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail="No roadmap generated yet for this skill")
    steps = db.query(RoadmapStep).filter(
        RoadmapStep.student_id == profile.id, RoadmapStep.skill_id == skill.id
    ).order_by(RoadmapStep.order_index).all()
    if not steps:
        raise HTTPException(status_code=404, detail="No roadmap generated yet for this skill")

    student_skills = _student_skill_map(db, profile.id)
    current = student_skills.get(skill_name, {}).get("proficiency_score", 0.0)
    return SkillRoadmapOut(
        skill_name=skill_name, baseline_score=steps[0].baseline_score, target_score=steps[0].target_score,
        current_score=current, steps=[RoadmapStepOut.model_validate(s) for s in steps],
    )


@router.patch("/roadmap/step/{step_id}/complete", response_model=RoadmapStepOut)
def complete_step(
    step_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _student_profile(db, user)
    step = db.query(RoadmapStep).filter(RoadmapStep.id == step_id, RoadmapStep.student_id == profile.id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Roadmap step not found")
    step.status = "completed"
    db.commit()
    db.refresh(step)
    return step
