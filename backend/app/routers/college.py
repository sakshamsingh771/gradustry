from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, CollegeProfile, StudentProfile
from app.models.academician import AcademicianProfile
from app.models.skill import StudentSkill, Skill
from app.models.opportunity import Application, Opportunity, OpportunitySkill
from app.models.college_membership import CollegeMembership, MembershipStatus
from app.ai import career_readiness

router = APIRouter(prefix="/api/college", tags=["college"])


# ---------------------------------------------------------------------------
# Institution-scoped data access helpers.
#
# Every analytics query in this file MUST start from one of these two
# functions. They are the single choke point that enforces institution data
# isolation: a college can only ever see users with a VERIFIED
# CollegeMembership row pointing at *its own* college_id. There is no
# endpoint below that accepts a student_id/college_id from the client and
# trusts it -- the scoping is always derived from the authenticated user's
# own CollegeProfile.
# ---------------------------------------------------------------------------

def _college_profile(db: Session, user: User) -> CollegeProfile:
    profile = db.query(CollegeProfile).filter(CollegeProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="College profile not found")
    return profile


def _verified_student_profiles(
    db: Session, college_id: int,
    branch: str | None = None, year_of_study: int | None = None,
    career_goal: str | None = None, skill: str | None = None,
) -> list[StudentProfile]:
    verified_user_ids = [
        m.user_id for m in db.query(CollegeMembership).filter(
            CollegeMembership.college_id == college_id, CollegeMembership.status == MembershipStatus.verified
        ).all()
    ]
    if not verified_user_ids:
        return []

    q = db.query(StudentProfile).filter(StudentProfile.user_id.in_(verified_user_ids))
    if branch:
        q = q.filter(StudentProfile.branch == branch)
    if year_of_study is not None:
        q = q.filter(StudentProfile.year_of_study == year_of_study)
    if career_goal:
        q = q.filter(StudentProfile.career_goal == career_goal)
    students = q.all()

    if skill:
        skill_row = db.query(Skill).filter(Skill.name == skill).first()
        if not skill_row:
            return []
        ids_with_skill = {
            r.student_id for r in db.query(StudentSkill.student_id).filter(
                StudentSkill.student_id.in_([s.id for s in students]), StudentSkill.skill_id == skill_row.id
            ).all()
        }
        students = [s for s in students if s.id in ids_with_skill]

    return students


def _verified_academician_profiles(db: Session, college_id: int) -> list[AcademicianProfile]:
    verified_user_ids = [
        m.user_id for m in db.query(CollegeMembership).filter(
            CollegeMembership.college_id == college_id, CollegeMembership.status == MembershipStatus.verified
        ).all()
    ]
    if not verified_user_ids:
        return []
    return db.query(AcademicianProfile).filter(AcademicianProfile.user_id.in_(verified_user_ids)).all()


def _skill_level_bucket(score: float) -> str:
    if score >= 70:
        return "Advanced"
    if score >= 40:
        return "Intermediate"
    return "Beginner"


# ---------------------------------------------------------------------------
# Membership management (unchanged from Phase 1)
# ---------------------------------------------------------------------------

@router.get("/memberships/pending")
def list_pending_memberships(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    rows = db.query(CollegeMembership).filter(
        CollegeMembership.college_id == college.id, CollegeMembership.status == MembershipStatus.pending
    ).all()
    out = []
    for m in rows:
        role = m.user.role if m.user else None
        out.append({
            "membership_id": m.id, "user_id": m.user_id, "student_name": m.user.full_name if m.user else None,
            "email": m.user.email if m.user else None, "requested_at": m.created_at, "role": role,
        })
    return out


@router.post("/memberships/{membership_id}/approve")
def approve_membership(membership_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
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


# ---------------------------------------------------------------------------
# STEP 1 -- Institution dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db), user: User = Depends(require_roles("college")),
    branch: str | None = Query(None), year_of_study: int | None = Query(None),
    career_goal: str | None = Query(None), skill: str | None = Query(None),
):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id, branch, year_of_study, career_goal, skill)
    student_ids = [s.id for s in students]
    academicians = _verified_academician_profiles(db, college.id)
    academician_ids = [a.id for a in academicians]

    if not student_ids:
        return {
            "college_name": college.college_name, "total_students": 0, "total_academicians": len(academicians),
            "average_readiness": 0.0, "students_by_skill_level": {"Beginner": 0, "Intermediate": 0, "Advanced": 0},
            "skill_development_progress": {"has_data": False, "current_avg": 0.0, "previous_avg": 0.0, "delta": 0.0},
            "internship_participation": {"students_applied": 0, "students_selected": 0, "participation_rate": 0.0},
            "placement_readiness": {"ready_count": 0, "ready_rate": 0.0, "average_readiness": 0.0},
            "opportunities": {"active_engaged": 0, "completed_engagements": 0},
            "industry_collaboration": {"distinct_industry_partners": 0, "total_engagements": 0},
        }

    skill_rows = db.query(StudentSkill).options(joinedload(StudentSkill.skill)).filter(
        StudentSkill.student_id.in_(student_ids)
    ).all()

    per_student_scores = defaultdict(list)
    for r in skill_rows:
        per_student_scores[r.student_id].append(r.proficiency_score)

    skill_level_counts = {"Beginner": 0, "Intermediate": 0, "Advanced": 0}
    for sid in student_ids:
        scores = per_student_scores.get(sid, [])
        avg = sum(scores) / len(scores) if scores else 0.0
        skill_level_counts[_skill_level_bucket(avg)] += 1

    readiness_map = career_readiness.compute_bulk(db, students)
    readiness_scores = [readiness_map[s.id]["overall_readiness"] for s in students]
    average_readiness = round(sum(readiness_scores) / len(readiness_scores), 1) if readiness_scores else 0.0
    ready_count = sum(1 for r in readiness_scores if r >= 70)

    from app.models.skill import SkillScoreHistory
    skill_ids = [r.id for r in skill_rows]
    cutoff = datetime.utcnow() - timedelta(days=30)
    history_rows = db.query(SkillScoreHistory).filter(
        SkillScoreHistory.student_skill_id.in_(skill_ids), SkillScoreHistory.recorded_at <= cutoff
    ).order_by(SkillScoreHistory.recorded_at.desc()).all() if skill_ids else []
    seen_skill_ids = set()
    previous_scores = []
    for h in history_rows:
        if h.student_skill_id not in seen_skill_ids:
            previous_scores.append(h.score)
            seen_skill_ids.add(h.student_skill_id)
    current_avg = round(sum(s.proficiency_score for s in skill_rows) / len(skill_rows), 1) if skill_rows else 0.0
    has_history = len(previous_scores) > 0
    previous_avg = round(sum(previous_scores) / len(previous_scores), 1) if has_history else 0.0

    student_apps = db.query(Application).options(joinedload(Application.opportunity)).filter(
        Application.student_id.in_(student_ids)
    ).all()
    students_applied = len({a.student_id for a in student_apps})
    students_selected = len({a.student_id for a in student_apps if a.status == "selected"})

    active_opp_ids = {a.opportunity_id for a in student_apps if a.opportunity and a.opportunity.is_active}
    completed_student_engagements = sum(1 for a in student_apps if a.status == "selected")

    academician_apps = db.query(Application).options(joinedload(Application.opportunity)).filter(
        Application.academician_id.in_(academician_ids)
    ).all() if academician_ids else []
    active_opp_ids |= {a.opportunity_id for a in academician_apps if a.opportunity and a.opportunity.is_active}
    completed_academician_engagements = sum(1 for a in academician_apps if a.status == "completed")

    industry_ids = {a.opportunity.industry_id for a in student_apps if a.opportunity}
    industry_ids |= {a.opportunity.industry_id for a in academician_apps if a.opportunity}

    return {
        "college_name": college.college_name,
        "total_students": len(students),
        "total_academicians": len(academicians),
        "average_readiness": average_readiness,
        "students_by_skill_level": skill_level_counts,
        "skill_development_progress": {
            "has_data": has_history, "current_avg": current_avg, "previous_avg": previous_avg,
            "delta": round(current_avg - previous_avg, 1) if has_history else 0.0,
        },
        "internship_participation": {
            "students_applied": students_applied, "students_selected": students_selected,
            "participation_rate": round(students_applied / len(students) * 100, 1) if students else 0.0,
        },
        "placement_readiness": {
            "ready_count": ready_count,
            "ready_rate": round(ready_count / len(students) * 100, 1) if students else 0.0,
            "average_readiness": average_readiness,
        },
        "opportunities": {
            "active_engaged": len(active_opp_ids),
            "completed_engagements": completed_student_engagements + completed_academician_engagements,
        },
        "industry_collaboration": {
            "distinct_industry_partners": len(industry_ids),
            "total_engagements": len(student_apps) + len(academician_apps),
        },
    }


@router.get("/students")
def list_students(
    db: Session = Depends(get_db), user: User = Depends(require_roles("college")),
    branch: str | None = Query(None), year_of_study: int | None = Query(None),
    career_goal: str | None = Query(None), skill: str | None = Query(None),
):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id, branch, year_of_study, career_goal, skill)
    readiness_map = career_readiness.compute_bulk(db, students)
    return [
        {
            "student_id": s.id, "full_name": s.user.full_name if s.user else "Unknown", "branch": s.branch,
            "year_of_study": s.year_of_study, "career_goal": s.career_goal,
            "readiness": readiness_map.get(s.id, {}).get("overall_readiness", 0.0),
        }
        for s in students
    ]


@router.get("/filters")
def available_filters(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id)
    branches = sorted({s.branch for s in students if s.branch})
    years = sorted({s.year_of_study for s in students if s.year_of_study})
    goals = sorted({s.career_goal for s in students if s.career_goal})
    student_ids = [s.id for s in students]
    skills = []
    if student_ids:
        rows = db.query(Skill.name).join(StudentSkill, StudentSkill.skill_id == Skill.id).filter(
            StudentSkill.student_id.in_(student_ids)
        ).distinct().all()
        skills = sorted({r[0] for r in rows})
    return {"branches": branches, "years_of_study": years, "career_goals": goals, "skills": skills}


# ---------------------------------------------------------------------------
# STEP 2 -- Skill analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/skills")
def skill_analytics(
    db: Session = Depends(get_db), user: User = Depends(require_roles("college")),
    branch: str | None = Query(None), year_of_study: int | None = Query(None),
    career_goal: str | None = Query(None), skill: str | None = Query(None),
):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id, branch, year_of_study, career_goal, skill)
    student_ids = [s.id for s in students]

    if not student_ids:
        return {
            "top_skills": [], "common_gaps": [], "proficiency_distribution": [],
            "readiness_trend": [], "emerging_skills": [],
        }

    skill_rows = db.query(StudentSkill).options(joinedload(StudentSkill.skill)).filter(
        StudentSkill.student_id.in_(student_ids)
    ).all()

    per_skill_scores = defaultdict(list)
    for r in skill_rows:
        per_skill_scores[r.skill.name].append(r.proficiency_score)

    skill_stats = [
        {"skill_name": name, "average_score": round(sum(scores) / len(scores), 1), "student_count": len(scores)}
        for name, scores in per_skill_scores.items()
    ]
    top_skills = sorted(skill_stats, key=lambda x: (-x["average_score"], -x["student_count"]))[:5]
    common_gaps = sorted(skill_stats, key=lambda x: x["average_score"])[:5]

    buckets = [("0-20", 0, 20), ("20-40", 20, 40), ("40-60", 40, 60), ("60-80", 60, 80), ("80-100", 80, 100.0001)]
    proficiency_distribution = []
    for label, lo, hi in buckets:
        count = sum(1 for r in skill_rows if lo <= r.proficiency_score < hi)
        proficiency_distribution.append({"range": label, "count": count})

    from app.models.skill import SkillScoreHistory
    skill_ids = [r.id for r in skill_rows]
    readiness_trend = []
    if skill_ids:
        history_rows = db.query(SkillScoreHistory).filter(SkillScoreHistory.student_skill_id.in_(skill_ids)).all()
        if history_rows:
            by_week = defaultdict(list)
            for h in history_rows:
                week_key = h.recorded_at.strftime("%Y-W%W")
                by_week[week_key].append(h.score)
            for week in sorted(by_week.keys()):
                scores = by_week[week]
                readiness_trend.append({"week": week, "average_score": round(sum(scores) / len(scores), 1), "data_points": len(scores)})

    demand_rows = db.query(OpportunitySkill).join(Opportunity, OpportunitySkill.opportunity_id == Opportunity.id).options(
        joinedload(OpportunitySkill.skill)
    ).filter(Opportunity.is_active == 1).all()
    demand_counts = defaultdict(int)
    for d in demand_rows:
        demand_counts[d.skill.name] += 1
    emerging_skills = []
    for name, demand in sorted(demand_counts.items(), key=lambda kv: -kv[1])[:5]:
        emerging_skills.append({
            "skill_name": name, "opportunities_requiring": demand,
            "students_with_skill": len(per_skill_scores.get(name, [])),
        })

    return {
        "top_skills": top_skills, "common_gaps": common_gaps,
        "proficiency_distribution": proficiency_distribution,
        "readiness_trend": readiness_trend, "emerging_skills": emerging_skills,
    }


# ---------------------------------------------------------------------------
# STEP 3 -- Internship & placement analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/internships")
def internship_analytics(
    db: Session = Depends(get_db), user: User = Depends(require_roles("college")),
    branch: str | None = Query(None), year_of_study: int | None = Query(None),
    career_goal: str | None = Query(None), skill: str | None = Query(None),
):
    college = _college_profile(db, user)
    students = _verified_student_profiles(db, college.id, branch, year_of_study, career_goal, skill)
    student_ids = [s.id for s in students]

    if not student_ids:
        return {
            "total_applications": 0, "shortlisted": 0, "selected": 0, "rejected": 0, "in_process": 0,
            "distinct_students_participated": 0, "distinct_students_selected": 0,
            "placement_readiness": {"ready_count": 0, "ready_rate": 0.0},
            "monthly_trend": [],
        }

    apps = db.query(Application).filter(Application.student_id.in_(student_ids)).all()

    status_counts = defaultdict(int)
    for a in apps:
        status_counts[a.status] += 1

    in_process = status_counts["shortlisted"] + status_counts["assessment"] + status_counts["interview"]

    readiness_map = career_readiness.compute_bulk(db, students)
    ready_count = sum(1 for s in students if readiness_map.get(s.id, {}).get("overall_readiness", 0) >= 70)

    monthly = defaultdict(int)
    for a in apps:
        monthly[a.applied_at.strftime("%Y-%m")] += 1
    monthly_trend = [{"month": m, "applications": monthly[m]} for m in sorted(monthly.keys())]

    return {
        "total_applications": len(apps),
        "shortlisted": status_counts["shortlisted"], "selected": status_counts["selected"],
        "rejected": status_counts["rejected"], "in_process": in_process,
        "distinct_students_participated": len({a.student_id for a in apps}),
        "distinct_students_selected": len({a.student_id for a in apps if a.status == "selected"}),
        "placement_readiness": {
            "ready_count": ready_count,
            "ready_rate": round(ready_count / len(students) * 100, 1) if students else 0.0,
        },
        "monthly_trend": monthly_trend,
    }


# ---------------------------------------------------------------------------
# STEP 4 -- Collaboration analytics (industry + academician engagement)
# ---------------------------------------------------------------------------

@router.get("/analytics/collaboration")
def collaboration_analytics(db: Session = Depends(get_db), user: User = Depends(require_roles("college"))):
    college = _college_profile(db, user)
    academicians = _verified_academician_profiles(db, college.id)
    academician_ids = [a.id for a in academicians]

    if not academician_ids:
        return {
            "total_academicians": 0, "total_engagements": 0, "distinct_industry_partners": 0,
            "by_category": [], "by_status": {},
        }

    apps = db.query(Application).options(joinedload(Application.opportunity)).filter(
        Application.academician_id.in_(academician_ids)
    ).all()

    by_category = defaultdict(lambda: defaultdict(int))
    by_status = defaultdict(int)
    industry_ids = set()
    for a in apps:
        if not a.opportunity:
            continue
        by_category[a.opportunity.role_type][a.status] += 1
        by_status[a.status] += 1
        industry_ids.add(a.opportunity.industry_id)

    category_out = [
        {"category": cat, "total": sum(statuses.values()), "by_status": dict(statuses)}
        for cat, statuses in by_category.items()
    ]
    category_out.sort(key=lambda x: -x["total"])

    return {
        "total_academicians": len(academicians),
        "total_engagements": len(apps),
        "distinct_industry_partners": len(industry_ids),
        "by_category": category_out,
        "by_status": dict(by_status),
    }
