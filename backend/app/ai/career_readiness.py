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
