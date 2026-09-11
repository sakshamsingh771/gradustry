from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, CollegeProfile, StudentProfile
from app.models.academician import AcademicianProfile
from app.models.college_membership import CollegeMembership, MembershipStatus, VerificationMethod
from app.models.opportunity import Opportunity, Application
from app.schemas.academician import AcademicianProfileOut, AcademicianProfileUpdate, AcademicianDashboardOut
from app.schemas.opportunity import OpportunityOut, ApplicationOut, ApplyRequest
from app.ai import career_readiness

router = APIRouter(prefix="/api/academician", tags=["academician"])


def _academician_profile(db: Session, user: User) -> AcademicianProfile:
    profile = db.query(AcademicianProfile).filter(AcademicianProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Academician profile not found")
    return profile


def _to_opp_out(opp: Opportunity) -> OpportunityOut:
    company_name = opp.industry.company_name if opp.industry else "Unknown Company"
    required_skills_data = []
    for rs in opp.required_skills:
        skill_name = rs.skill.name if rs.skill else "Unknown Skill"
        required_skills_data.append({
            "skill_name": skill_name,
            "min_proficiency": rs.min_proficiency,
            "weight": rs.weight,
        })
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
        created_at=opp.created_at,
        required_skills=required_skills_data,
    )


# ---------- Profile ----------

@router.get("/profile", response_model=AcademicianProfileOut)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(require_roles("academician"))):
    profile = _academician_profile(db, user)
    college_name = profile.college.college_name if profile.college else None
    return AcademicianProfileOut(
        full_name=user.full_name,
        email=user.email,
        designation=profile.designation,
        institution=profile.institution,
        department=profile.department,
        area_of_expertise=profile.area_of_expertise,
        experience_years=profile.experience_years,
        bio=profile.bio,
        verified=profile.verified,
        college_id=profile.college_id,
        college_name=college_name,
    )


@router.put("/profile", response_model=AcademicianProfileOut)
def update_my_profile(
    payload: AcademicianProfileUpdate,
    db: Session = Depends(get_db), user: User = Depends(require_roles("academician")),
):
    profile = _academician_profile(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    college_name = profile.college.college_name if profile.college else None
    return AcademicianProfileOut(
        full_name=user.full_name,
        email=user.email,
        designation=profile.designation,
        institution=profile.institution,
        department=profile.department,
        area_of_expertise=profile.area_of_expertise,
        experience_years=profile.experience_years,
        bio=profile.bio,
        verified=profile.verified,
        college_id=profile.college_id,
        college_name=college_name,
    )


# ---------- College linkage (Academician <-> College), reuses CollegeMembership ----------

@router.get("/colleges")
def list_colleges(db: Session = Depends(get_db)):
    colleges = db.query(CollegeProfile).all()
    return [{"id": c.id, "college_name": c.college_name, "city": c.city} for c in colleges]


@router.post("/join-college")
def join_college(
    college_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("academician")),
):
    college = db.query(CollegeProfile).filter(CollegeProfile.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    existing = db.query(CollegeMembership).filter(
        CollegeMembership.user_id == user.id, CollegeMembership.college_id == college_id
    ).first()
    if existing and existing.status == MembershipStatus.verified:
        return {"detail": f"Already a verified member of {college.college_name}", "status": "verified"}
    if existing:
        existing.status = MembershipStatus.pending
    else:
        db.add(CollegeMembership(
            user_id=user.id, college_id=college_id,
            status=MembershipStatus.pending, verification_method=VerificationMethod.self_reported,
        ))

    profile = _academician_profile(db, user)
    profile.college_id = college.id
    db.commit()
    return {"detail": f"Membership request sent to {college.college_name} — pending verification", "status": "pending"}


# ---------- Students (Academician <-> Student, mentorship view) ----------

@router.get("/students")
def list_college_students(db: Session = Depends(get_db), user: User = Depends(require_roles("academician"))):
    profile = _academician_profile(db, user)

    membership = db.query(CollegeMembership).filter(
        CollegeMembership.user_id == user.id,
        CollegeMembership.status == MembershipStatus.verified,
    ).first()
    if not membership:
        return []

    students = db.query(StudentProfile).join(
        CollegeMembership, CollegeMembership.user_id == StudentProfile.user_id
    ).filter(
        CollegeMembership.college_id == membership.college_id,
        CollegeMembership.status == MembershipStatus.verified,
    ).all()
    out = []
    for s in students:
        readiness = career_readiness.compute_for_student(db, s)["overall_readiness"]
        out.append({
            "student_id": s.id, "full_name": s.user.full_name if s.user else "Unknown",
            "branch": s.branch, "year_of_study": s.year_of_study,
            "career_goal": s.career_goal, "readiness": readiness,
        })
    return out


# ---------- Opportunity discovery + participation tracking ----------

@router.get("/opportunities", response_model=List[OpportunityOut])
def discover_opportunities(db: Session = Depends(get_db)):
    opps = db.query(Opportunity).filter(
        Opportunity.is_active == 1, Opportunity.audience == "academician"
    ).order_by(Opportunity.created_at.desc()).all()
    return [_to_opp_out(o) for o in opps]


@router.post("/opportunities/apply", response_model=ApplicationOut)
def apply_to_opportunity(
    payload: ApplyRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("academician")),
):
    profile = _academician_profile(db, user)
    opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opp.audience != "academician":
        raise HTTPException(status_code=400, detail="This opportunity is not open to academicians")

    existing = db.query(Application).filter(
        Application.opportunity_id == opp.id, Application.academician_id == profile.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this opportunity")

    application = Application(
        opportunity_id=opp.id,
        academician_id=profile.id,
        status="applied",
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
        applicant_type="academician",
        academician_id=profile.id,
        academician_name=user.full_name,
        status=application.status,
        match_score=application.match_score,
        applied_at=application.applied_at,
    )


@router.get("/applications/mine", response_model=List[ApplicationOut])
def my_applications(db: Session = Depends(get_db), user: User = Depends(require_roles("academician"))):
    profile = _academician_profile(db, user)
    apps = db.query(Application).filter(Application.academician_id == profile.id).order_by(Application.applied_at.desc()).all()

    results = []
    for a in apps:
        opp_title = a.opportunity.title if a.opportunity else "Unknown Opportunity"
        company_name = a.opportunity.industry.company_name if (a.opportunity and a.opportunity.industry) else "Unknown Company"
        results.append(ApplicationOut(
            id=a.id,
            opportunity_id=a.opportunity_id,
            opportunity_title=opp_title,
            company_name=company_name,
            applicant_type="academician",
            academician_id=profile.id,
            academician_name=user.full_name,
            status=a.status,
            match_score=a.match_score,
            applied_at=a.applied_at,
        ))
    return results


# ---------- Dashboard ----------

@router.get("/dashboard", response_model=AcademicianDashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles("academician"))):
    profile = _academician_profile(db, user)

    membership = db.query(CollegeMembership).filter(CollegeMembership.user_id == user.id).first()
    college_membership_status = membership.status if membership else None
    college_name = profile.college.college_name if profile.college else None

    total_students_visible = 0
    if membership and membership.status == MembershipStatus.verified:
        total_students_visible = db.query(StudentProfile).filter(
            StudentProfile.college_id == membership.college_id
        ).count()

    apps = db.query(Application).filter(Application.academician_id == profile.id).all()
    by_status: dict[str, int] = {}
    for a in apps:
        by_status[a.status] = by_status.get(a.status, 0) + 1

    open_opportunities = db.query(Opportunity).filter(
        Opportunity.is_active == 1, Opportunity.audience == "academician"
    ).count()

    profile_complete = bool(profile.designation and profile.institution and profile.department and profile.area_of_expertise)

    return AcademicianDashboardOut(
        full_name=user.full_name,
        institution=profile.institution,
        designation=profile.designation,
        profile_complete=profile_complete,
        college_membership_status=college_membership_status,
        college_name=college_name,
        total_students_visible=total_students_visible,
        applications_total=len(apps),
        applications_by_status=by_status,
        open_opportunities=open_opportunities,
    )
