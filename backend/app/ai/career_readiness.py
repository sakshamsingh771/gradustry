"""
Career Readiness Intelligence (Phase 9)
-----------------------------------------
A transparent, fully deterministic weighted score — explicitly NOT a black
box. Every component and its weight is returned to the client so the
student can see exactly why their readiness is what it is.

Weights (fixed, documented — not arbitrary per-call tuning):
    Skills              35%
    Assessments         20%
    Evidence            15%
    Projects            15%
    Industry feedback   10%
    Consistency          5%
"""
from datetime import datetime, timedelta

WEIGHTS = {
    "skills": 0.35,
    "assessments": 0.20,
    "evidence": 0.15,
    "projects": 0.15,
    "industry_feedback": 0.10,
    "consistency": 0.05,
}

def compute_for_student(db, profile) -> dict:
    from app.models.skill import StudentSkill
    from app.models.assessment import AssessmentAttempt
    from app.models.opportunity import Application

    rows = db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all()
    student_skills = [
        {"proficiency_score": r.proficiency_score, "confidence_level": r.confidence_level,
         "evidence_count": len(r.evidences), "evidences": [{"type": e.type} for e in r.evidences]}
        for r in rows
    ]
    recent_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id == profile.id, AssessmentAttempt.completed_at.isnot(None)
    ).order_by(AssessmentAttempt.completed_at.desc()).limit(10).all()
    assessment_scores = [a.score_percent for a in recent_attempts]
    applications = db.query(Application).filter(Application.student_id == profile.id).all()
    feedback_scores = [a.feedback.technical_skill for a in applications if a.feedback]
    history_dates = []
    for r in rows:
        history_dates += [h.recorded_at for h in r.history]
    return compute_readiness_breakdown(student_skills, assessment_scores, feedback_scores, history_dates)


def compute_bulk(db, profiles: list) -> dict:
    """N+1-free version of compute_for_student for a batch of StudentProfile rows.

    Runs a fixed 4 queries total (skills, evidences, assessment attempts,
    applications+feedback) regardless of how many students are passed in,
    instead of ~4 queries PER student. Returns {student_id: breakdown_dict}.
    Institutional dashboards (college/academician) should use this instead
    of looping compute_for_student.
    """
    from collections import defaultdict
    from sqlalchemy.orm import joinedload
    from app.models.skill import StudentSkill, Evidence, SkillScoreHistory
    from app.models.assessment import AssessmentAttempt
    from app.models.opportunity import Application

    student_ids = [p.id for p in profiles]
    if not student_ids:
        return {}

    skill_rows = db.query(StudentSkill).filter(StudentSkill.student_id.in_(student_ids)).all()
    skill_ids = [r.id for r in skill_rows]
    skill_id_to_student = {r.id: r.student_id for r in skill_rows}

    evidences_by_skill = defaultdict(list)
    history_by_skill = defaultdict(list)
    if skill_ids:
        for e in db.query(Evidence).filter(Evidence.student_skill_id.in_(skill_ids)).all():
            evidences_by_skill[e.student_skill_id].append(e)
        for h in db.query(SkillScoreHistory).filter(SkillScoreHistory.student_skill_id.in_(skill_ids)).all():
            history_by_skill[h.student_skill_id].append(h)

    skills_by_student = defaultdict(list)
    history_dates_by_student = defaultdict(list)
    for r in skill_rows:
        evs = evidences_by_skill.get(r.id, [])
        skills_by_student[r.student_id].append({
            "proficiency_score": r.proficiency_score, "confidence_level": r.confidence_level,
            "evidence_count": len(evs), "evidences": [{"type": e.type} for e in evs],
        })
        history_dates_by_student[r.student_id] += [h.recorded_at for h in history_by_skill.get(r.id, [])]

    attempts_by_student = defaultdict(list)
    for a in db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id.in_(student_ids), AssessmentAttempt.completed_at.isnot(None)
    ).order_by(AssessmentAttempt.completed_at.desc()).all():
        attempts_by_student[a.student_id].append(a.score_percent)

    feedback_by_student = defaultdict(list)
    for a in db.query(Application).options(joinedload(Application.feedback)).filter(
        Application.student_id.in_(student_ids)
    ).all():
        if a.feedback:
            feedback_by_student[a.student_id].append(a.feedback.technical_skill)

    return {
        p.id: compute_readiness_breakdown(
            skills_by_student.get(p.id, []),
            attempts_by_student.get(p.id, [])[:10],
            feedback_by_student.get(p.id, []),
            history_dates_by_student.get(p.id, []),
        )
        for p in profiles
    }

def compute_readiness_breakdown(
    student_skills: list[dict],       # [{proficiency_score, confidence_level, evidence_count, evidences:[{type,status,created_at}]}]
    assessment_scores: list[float],   # recent AssessmentAttempt.score_percent values
    industry_feedback_scores: list[float],  # technical_skill values (0-10) from IndustryFeedback
    history_recorded_ats: list[datetime],   # SkillScoreHistory.recorded_at across all skills
) -> dict:
    # --- Skills: average demonstrated proficiency across tracked skills ---
    skills_component = (
        sum(s["proficiency_score"] for s in student_skills) / len(student_skills)
        if student_skills else 0.0
    )

    # --- Assessments: average of recent assessment scores ---
    assessments_component = sum(assessment_scores) / len(assessment_scores) if assessment_scores else 0.0

    # --- Evidence: fraction of skills backed by High/Medium confidence evidence ---
    if student_skills:
        confidence_points = {"High": 100, "Medium": 65, "Low": 30, "None": 0}
        evidence_component = sum(confidence_points.get(s["confidence_level"], 0) for s in student_skills) / len(student_skills)
    else:
        evidence_component = 0.0

    # --- Projects: number of project/github evidences submitted, capped ---
    project_evidence_count = sum(
        1 for s in student_skills for e in s.get("evidences", []) if e.get("type") in ("project", "github")
    )
    projects_component = min(100.0, (project_evidence_count / 5) * 100)

    # --- Industry feedback: average technical_skill rating (0-10) scaled to 0-100 ---
    industry_component = (
        (sum(industry_feedback_scores) / len(industry_feedback_scores)) * 10
        if industry_feedback_scores else 0.0
    )

    # --- Consistency: recent activity in the last 30 days across skill history ---
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent_activity = sum(1 for ts in history_recorded_ats if ts >= cutoff)
    consistency_component = min(100.0, recent_activity * 20)  # 5+ updates in 30 days = full marks

    components = {
        "skills": round(skills_component, 1),
        "assessments": round(assessments_component, 1),
        "evidence": round(evidence_component, 1),
        "projects": round(projects_component, 1),
        "industry_feedback": round(industry_component, 1),
        "consistency": round(consistency_component, 1),
    }

    overall = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)

    return {
        "overall_readiness": round(overall, 1),
        "weights": WEIGHTS,
        "components": components,
        "weighted_contributions": {k: round(components[k] * WEIGHTS[k], 1) for k in WEIGHTS},
    }
