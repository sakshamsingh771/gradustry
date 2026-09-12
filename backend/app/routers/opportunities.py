from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile, IndustryProfile
from app.models.skill import Skill, StudentSkill, Evidence, SkillScoreHistory
from app.models.opportunity import Opportunity, OpportunitySkill, Application, IndustryFeedback
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityOut, OpportunityMatchOut, ApplyRequest,
    ApplicationOut, ApplicationStatusUpdate, IndustryFeedbackCreate,
)
from app.ai import matcher, evidence_engine, career_readiness

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


def _industry_profile(db: Session, user: User) -> IndustryProfile:
    profile = db.query(IndustryProfile).filter(IndustryProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Industry profile not found")
    return profile


def _student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _to_out(opp: Opportunity) -> OpportunityOut:
    company_name = opp.industry.company_name if opp.industry else "Unknown Company"
    
    required_skills_data = []
    for rs in opp.required_skills:
        skill_name = rs.skill.name if rs.skill else "Unknown Skill"
        required_skills_data.append({
            "skill_name": skill_name,
            "min_proficiency": rs.min_proficiency,
            "weight": rs.weight,
        })

    enrolled_count = sum(1 for a in opp.applications if a.status != "rejected")

    return OpportunityOut(
        id=opp.id,
        title=opp.title,
        role_type=opp.role_type,
        audience=opp.audience,
        description=opp.description,
        location=opp.location,
        company_name=company_name,
        min_year_of_study=opp.min_year_of_study,
        final_year_only=bool(opp.final_year_only),
        stipend_or_ctc=opp.stipend_or_ctc,
        duration=opp.duration,
        capacity=opp.capacity,
        eligibility_notes=opp.eligibility_notes,
        enrolled_count=enrolled_count,
        created_at=opp.created_at,
        required_skills=required_skills_data,
    )


def _student_skill_map(db: Session, student_id: int) -> Dict[str, Dict[str, Any]]:
    rows = db.query(StudentSkill).filter(StudentSkill.student_id == student_id).all()
    skills_map = {}
    for r in rows:
        if r.skill:
            skills_map[r.skill.name] = {
                "proficiency_score": r.proficiency_score,
                "evidence_count": len(r.evidences),
            }
    return skills_map


def _record_completion_evidence(db: Session, app_: Application) -> None:
    """Create verified 'industry_program_completion' evidence for each skill the
    opportunity actually declared, and recompute the affected StudentSkill rows
    through the existing evidence engine. No-op if the opportunity has no
    required_skills — completion alone (e.g. attending a guest lecture with no
    listed skills) never fabricates a skill score."""
    opp = app_.opportunity
    if not opp or not opp.required_skills:
        return
    company_name = opp.industry.company_name if opp.industry else "an industry partner"

    for rs in opp.required_skills:
        if not rs.skill:
            continue
        ss = db.query(StudentSkill).filter(
            StudentSkill.student_id == app_.student_id, StudentSkill.skill_id == rs.skill_id
        ).first()
        if not ss:
            ss = StudentSkill(student_id=app_.student_id, skill_id=rs.skill_id, proficiency_score=0.0, confidence_level="None")
            db.add(ss)
            db.flush()

        signal = evidence_engine.score_single_evidence("industry_program_completion", "verified")
        db.add(Evidence(
            student_skill_id=ss.id,
            type="industry_program_completion",
            title=f"Completed: {opp.title}",
            description=f"Verified completion recorded by {company_name} ({opp.role_type.replace('_', ' ')}).",
            status="verified",
            signal_score=signal,
        ))
        db.flush()

        evidences = [{"type": e.type, "status": e.status, "signal_score": e.signal_score} for e in ss.evidences]
        result = evidence_engine.recompute_student_skill(evidences)
        ss.proficiency_score = result["proficiency_score"]
        ss.confidence_level = result["confidence_level"]
        ss.last_assessed_at = datetime.utcnow()
        db.add(SkillScoreHistory(student_skill_id=ss.id, score=ss.proficiency_score, reason="industry program completion"))

    db.commit()


@router.get("/{opportunity_id}/candidates")
async def discover_candidates(
    opportunity_id: int, min_match_score: float = 50.0,
    db: Session = Depends(get_db), user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.industry_id == profile.id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    required = [{"skill_name": rs.skill.name, "min_proficiency": rs.min_proficiency, "weight": rs.weight} for rs in opp.required_skills if rs.skill]
    opp_dict = {"final_year_only": bool(opp.final_year_only), "min_year_of_study": opp.min_year_of_study}

    candidates = []
    visible_students = db.query(StudentProfile).filter(StudentProfile.profile_visible == True).all()  # noqa: E712
    for sp in visible_students:
        student_skills = _student_skill_map(db, sp.id)
        student_dict = {"year_of_study": sp.year_of_study}
        match = await matcher.build_match_hybrid(student_dict, opp_dict, student_skills, required)
        if not match["explanation"]["is_eligible"] or match["match_score"] < min_match_score:
            continue
        readiness = career_readiness.compute_for_student(db, sp)["overall_readiness"]
        already_applied = db.query(Application).filter(
            Application.opportunity_id == opportunity_id, Application.student_id == sp.id
        ).first()
        candidates.append({
            "student_id": sp.id, "career_readiness": readiness, "match_score": match["match_score"],
            "matched_skills": match["explanation"]["matched_skills"],
            "evidence_backed_skill_count": match["explanation"]["relevant_evidence_count"],
            "already_applied": already_applied is not None,
            "application_status": already_applied.status if already_applied else None,
        })
    candidates.sort(key=lambda c: c["match_score"], reverse=True)
    return candidates


@router.post("/{opportunity_id}/candidates/{student_id}/invite", response_model=ApplicationOut)
def invite_candidate(
    opportunity_id: int, student_id: int,
    db: Session = Depends(get_db), user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.industry_id == profile.id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id, StudentProfile.profile_visible == True).first()  # noqa: E712
    if not student:
        raise HTTPException(status_code=404, detail="Candidate not found or not visible")

    existing = db.query(Application).filter(
        Application.opportunity_id == opportunity_id, Application.student_id == student_id
    ).first()
    if not existing:
        existing = Application(opportunity_id=opportunity_id, student_id=student_id, status="invited")
        db.add(existing)
        db.commit()
        db.refresh(existing)

    return ApplicationOut(
        id=existing.id, opportunity_id=opp.id, opportunity_title=opp.title,
        company_name=profile.company_name, student_id=student_id, student_name=None,
        status=existing.status, match_score=existing.match_score, applied_at=existing.applied_at,
    )


@router.post("", response_model=OpportunityOut)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    opp = Opportunity(
        industry_id=profile.id,
        title=payload.title,
        role_type=payload.role_type,
        audience=payload.audience if payload.audience in ("student", "academician") else "student",
        description=payload.description,
        location=payload.location,
        min_year_of_study=payload.min_year_of_study,
        final_year_only=int(payload.final_year_only),
        stipend_or_ctc=payload.stipend_or_ctc,
        duration=payload.duration,
        capacity=payload.capacity,
        eligibility_notes=payload.eligibility_notes,
    )
    db.add(opp)
    db.flush()

    for rs in payload.required_skills:
        skill = db.query(Skill).filter(Skill.name == rs.skill_name).first()
        if not skill:
            skill = Skill(name=rs.skill_name, category="General")
            db.add(skill)
            db.flush()
        db.add(OpportunitySkill(
            opportunity_id=opp.id,
            skill_id=skill.id,
            min_proficiency=rs.min_proficiency,
            weight=rs.weight,
        ))

    db.commit()
    db.refresh(opp)
    return _to_out(opp)


@router.get("", response_model=List[OpportunityOut])
def list_opportunities(db: Session = Depends(get_db)):
    opps = db.query(Opportunity).filter(
        Opportunity.is_active == 1, Opportunity.audience == "student"
    ).order_by(Opportunity.created_at.desc()).all()
    return [_to_out(o) for o in opps]


@router.get("/industry/mine", response_model=List[OpportunityOut])
def my_opportunities(db: Session = Depends(get_db), user: User = Depends(require_roles("industry"))):
    profile = _industry_profile(db, user)
    opps = db.query(Opportunity).filter(Opportunity.industry_id == profile.id).order_by(Opportunity.created_at.desc()).all()
    return [_to_out(o) for o in opps]


@router.get("/matches/for-me", response_model=List[OpportunityMatchOut])
async def matches_for_student(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    student_skills = _student_skill_map(db, profile.id)
    student_dict = {"year_of_study": profile.year_of_study}

    opps = db.query(Opportunity).filter(Opportunity.is_active == 1, Opportunity.audience == "student").all()
    results = []

    for opp in opps:
        required = []
        for rs in opp.required_skills:
            if rs.skill:
                required.append({
                    "skill_name": rs.skill.name,
                    "min_proficiency": rs.min_proficiency,
                    "weight": rs.weight,
                })

        opp_dict = {"final_year_only": bool(opp.final_year_only), "min_year_of_study": opp.min_year_of_study}
        match = await matcher.build_match_hybrid(student_dict, opp_dict, student_skills, required)
        
        results.append(OpportunityMatchOut(
            opportunity=_to_out(opp),
            match_score=match["match_score"],
            explanation=match["explanation"],
        ))

    results.sort(key=lambda r: r.match_score, reverse=True)
    return results


@router.post("/apply", response_model=ApplicationOut)
async def apply(payload: ApplyRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opp.audience != "student":
        raise HTTPException(status_code=400, detail="This opportunity is not open to students")

    existing = db.query(Application).filter(
        Application.opportunity_id == opp.id, Application.student_id == profile.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this opportunity")

    if opp.capacity is not None:
        active_count = db.query(Application).filter(
            Application.opportunity_id == opp.id, Application.status != "rejected"
        ).count()
        if active_count >= opp.capacity:
            raise HTTPException(status_code=400, detail="This program has reached its seat capacity")

    student_skills = _student_skill_map(db, profile.id)
    required = []
    for rs in opp.required_skills:
        if rs.skill:
            required.append({
                "skill_name": rs.skill.name,
                "min_proficiency": rs.min_proficiency,
                "weight": rs.weight,
            })

    match = await matcher.build_match_hybrid(
        {"year_of_study": profile.year_of_study},
        {"final_year_only": bool(opp.final_year_only), "min_year_of_study": opp.min_year_of_study},
        student_skills,
        required,
    )

    application = Application(
        opportunity_id=opp.id,
        student_id=profile.id,
        match_score=match["match_score"],
        match_explanation=match["explanation"],
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    company_name = opp.industry.company_name if opp.industry else "Unknown Company"

    return ApplicationOut(
        id=application.id,
        opportunity_id=opp.id,
        opportunity_title=opp.title,
        company_name=company_name,
        applicant_type="student",
        student_id=profile.id,
        student_name=user.full_name,
        status=application.status,
        match_score=application.match_score,
        applied_at=application.applied_at,
    )


@router.get("/applications/mine", response_model=List[ApplicationOut])
def my_applications(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)
    apps = db.query(Application).filter(Application.student_id == profile.id).order_by(Application.applied_at.desc()).all()
    
    results = []
    for a in apps:
        opp_title = a.opportunity.title if a.opportunity else "Unknown Opportunity"
        company_name = a.opportunity.industry.company_name if (a.opportunity and a.opportunity.industry) else "Unknown Company"
        
        results.append(ApplicationOut(
            id=a.id,
            opportunity_id=a.opportunity_id,
            opportunity_title=opp_title,
            company_name=company_name,
            applicant_type="student",
            student_id=profile.id,
            student_name=user.full_name,
            status=a.status,
            match_score=a.match_score,
            applied_at=a.applied_at,
        ))
    return results


@router.get("/{opportunity_id}/applications", response_model=List[ApplicationOut])
def applications_for_opportunity(
    opportunity_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.industry_id == profile.id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    apps = db.query(Application).filter(Application.opportunity_id == opportunity_id).order_by(Application.match_score.desc()).all()
    
    results = []
    for a in apps:
        if a.academician_id is not None:
            academician_name = a.academician.user.full_name if (a.academician and a.academician.user) else "Unknown Academician"
            results.append(ApplicationOut(
                id=a.id,
                opportunity_id=a.opportunity_id,
                opportunity_title=opp.title,
                company_name=profile.company_name,
                applicant_type="academician",
                academician_id=a.academician_id,
                academician_name=academician_name,
                status=a.status,
                match_score=a.match_score,
                applied_at=a.applied_at,
            ))
        else:
            student_name = a.student.user.full_name if (a.student and a.student.user) else "Unknown Student"
            results.append(ApplicationOut(
                id=a.id,
                opportunity_id=a.opportunity_id,
                opportunity_title=opp.title,
                company_name=profile.company_name,
                applicant_type="student",
                student_id=a.student_id,
                student_name=student_name,
                status=a.status,
                match_score=a.match_score,
                applied_at=a.applied_at,
            ))
    return results


@router.patch("/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int, payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db), user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    app_ = db.query(Application).filter(Application.id == application_id).first()
    
    if not app_ or not app_.opportunity or app_.opportunity.industry_id != profile.id:
        raise HTTPException(status_code=404, detail="Application not found")
        
    valid_statuses = {
        "applied", "shortlisted", "assessment", "interview", "selected", "rejected",
        "accepted", "in_progress", "completed",
    }
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(valid_statuses)}")

    old_status = app_.status
    app_.status = payload.status
    db.commit()
    db.refresh(app_)

    # STEP 3 (Phase 3): a genuine transition into "completed" for a student
    # applicant creates real, verified evidence tied to the opportunity's
    # declared required skills, then recomputes the Skill Passport through
    # the existing evidence engine. Guarded so it only fires once per
    # transition (not on repeated no-op status writes), and only when the
    # opportunity actually declared skills — no skill is ever awarded
    # without a concrete evidence record backing it.
    if payload.status == "completed" and old_status != "completed" and app_.student_id is not None:
        _record_completion_evidence(db, app_)
    
    opp_title = app_.opportunity.title if app_.opportunity else "Unknown Opportunity"

    if app_.academician_id is not None:
        academician_name = app_.academician.user.full_name if (app_.academician and app_.academician.user) else "Unknown Academician"
        return ApplicationOut(
            id=app_.id,
            opportunity_id=app_.opportunity_id,
            opportunity_title=opp_title,
            company_name=profile.company_name,
            applicant_type="academician",
            academician_id=app_.academician_id,
            academician_name=academician_name,
            status=app_.status,
            match_score=app_.match_score,
            applied_at=app_.applied_at,
        )

    student_name = app_.student.user.full_name if (app_.student and app_.student.user) else "Unknown Student"

    return ApplicationOut(
        id=app_.id,
        opportunity_id=app_.opportunity_id,
        opportunity_title=opp_title,
        company_name=profile.company_name,
        applicant_type="student",
        student_id=app_.student_id,
        student_name=student_name,
        status=app_.status,
        match_score=app_.match_score,
        applied_at=app_.applied_at,
    )


@router.post("/feedback")
def submit_feedback(
    payload: IndustryFeedbackCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("industry")),
):
    profile = _industry_profile(db, user)
    app_ = db.query(Application).filter(Application.id == payload.application_id).first()
    
    if not app_ or not app_.opportunity or app_.opportunity.industry_id != profile.id:
        raise HTTPException(status_code=404, detail="Application not found")

    if app_.feedback is not None:
        raise HTTPException(status_code=400, detail="Feedback has already been submitted for this application")



    feedback = IndustryFeedback(
        application_id=app_.id,
        technical_skill=payload.technical_skill,
        problem_solving=payload.problem_solving,
        communication=payload.communication,
        teamwork=payload.teamwork,
        professionalism=payload.professionalism,
        comments=payload.comments,
    )
    db.add(feedback)

    if app_.student_id is not None:
        for rs in app_.opportunity.required_skills:
            ss = db.query(StudentSkill).filter(
                StudentSkill.student_id == app_.student_id, StudentSkill.skill_id == rs.skill_id
            ).first()

            if not ss:
                ss = StudentSkill(student_id=app_.student_id, skill_id=rs.skill_id, proficiency_score=0.0, confidence_level="None")
                db.add(ss)
                db.flush()

            signal = evidence_engine.score_single_evidence(
                "industry_feedback", "verified", override_score=payload.technical_skill * 10
            )
            db.add(Evidence(
                student_skill_id=ss.id,
                type="industry_feedback",
                title=f"Industry feedback — {app_.opportunity.title}",
                description=payload.comments,
                status="verified",
                signal_score=signal,
            ))
            db.flush()

            evidences = [{"type": e.type, "status": e.status, "signal_score": e.signal_score} for e in ss.evidences]
            result = evidence_engine.recompute_student_skill(evidences)
            ss.proficiency_score = result["proficiency_score"]
            ss.confidence_level = result["confidence_level"]

    db.commit()
    return {"detail": "Feedback submitted and added to the student's Skill Passport"}