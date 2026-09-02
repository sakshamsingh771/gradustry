"""
Skill Gap Engine
----------------
Compares a student's demonstrated proficiency against a target career role's
required skills, and explains WHY each gap exists rather than just stating
a number.
"""


def severity_for_gap(gap: float) -> str:
    if gap <= 0:
        return "matched"
    if gap <= 15:
        return "low"
    if gap <= 35:
        return "medium"
    return "high"


def reason_for(current: float, target: float, confidence: str, evidence_count: int) -> str:
    if current >= target:
        return "Demonstrated proficiency already meets the target for this role."
    if evidence_count == 0:
        return "No evidence submitted yet for this skill — score is starting from zero."
    if confidence in ("Low", "None"):
        return "Some signal exists, but evidence confidence is too low to trust the score yet — add certificates, projects, or take an assessment."
    return "Evidence shows partial proficiency; targeted practice and a re-assessment should close the remaining gap."


def build_gap_report(role_title: str, requirements: list[dict], student_skills: dict[str, dict]) -> dict:
    """
    requirements: [{skill_name, target_proficiency, importance}]
    student_skills: {skill_name: {proficiency_score, confidence_level, evidence_count}}
    """
    matched, low_gap, medium_gap, high_gap = [], [], [], []
    weighted_sum = 0.0
    weight_total = 0.0

    for req in requirements:
        name = req["skill_name"]
        target = req["target_proficiency"]
        weight = 1.5 if req.get("importance") == "core" else 1.0
        s = student_skills.get(name, {"proficiency_score": 0.0, "confidence_level": "None", "evidence_count": 0})
        current = s["proficiency_score"]
        gap = round(max(target - current, 0.0), 1)
        severity = severity_for_gap(gap)
        item = {
            "skill_name": name,
            "current_score": current,
            "target_score": target,
            "gap": gap,
            "severity": severity,
            "reason": reason_for(current, target, s["confidence_level"], s["evidence_count"]),
        }
        {"matched": matched, "low": low_gap, "medium": medium_gap, "high": high_gap}[severity].append(item)

        # readiness contribution is capped at target (over-qualification doesn't inflate readiness)
        weighted_sum += min(current, target) * weight
        weight_total += target * weight

    readiness = round((weighted_sum / weight_total) * 100, 1) if weight_total > 0 else 0.0

    return {
        "role_title": role_title,
        "career_readiness": readiness,
        "matched": matched,
        "low_gap": low_gap,
        "medium_gap": medium_gap,
        "high_gap": high_gap,
    }
