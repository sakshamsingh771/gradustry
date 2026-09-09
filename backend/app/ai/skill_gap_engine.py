"""
Skill Gap Engine
----------------
Compares a student's demonstrated proficiency against a target career role's
required skills, and explains WHY each gap exists rather than just stating
a number. Phase 11: adds priority, itemized reasons, missing subskills,
and prerequisite awareness (Phase 14).
"""

from app.data.skill_taxonomy import missing_subskills_for, unmet_prerequisites


def severity_for_gap(gap: float) -> str:
    if gap <= 0:
        return "matched"
    if gap <= 15:
        return "low"
    if gap <= 35:
        return "medium"
    return "high"


def priority_for(severity: str, importance: str, unmet_prereqs: list[str]) -> str:
    if severity == "matched":
        return "None"
    if severity == "high" or importance == "core":
        return "High" if not unmet_prereqs else "High"
    if severity == "medium":
        return "Medium"
    return "Low"


def reasons_for(current: float, target: float, confidence: str, evidence_count: int,
                 assessment_taken: bool, github_signal: bool, project_count: int,
                 unmet_prereqs: list[str]) -> list[str]:
    """Returns an itemized list of WHY the gap exists (Phase 11)."""
    if current >= target:
        return []

    reasons = []
    if not assessment_taken:
        reasons.append("low assessment score / no assessment taken yet")
    if evidence_count == 0:
        reasons.append("missing evidence for this skill")
    if not github_signal:
        reasons.append("weak or no GitHub signal")
    if project_count == 0:
        reasons.append("missing projects demonstrating this skill")
    if confidence in ("Low", "None"):
        reasons.append("evidence confidence too low to trust the current score")
    if unmet_prereqs:
        reasons.append(f"prerequisite skills not yet solid: {', '.join(unmet_prereqs)}")
    if not reasons:
        reasons.append("partial proficiency — targeted practice and re-assessment should close the gap")
    return reasons


def reason_for(current: float, target: float, confidence: str, evidence_count: int) -> str:
    """Kept for backwards compatibility — single-line summary."""
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
    student_skills: {skill_name: {proficiency_score, confidence_level, evidence_count,
                                   assessment_taken, github_signal, project_count}}
    """
    matched, low_gap, medium_gap, high_gap = [], [], [], []
    weighted_sum = 0.0
    weight_total = 0.0

    for req in requirements:
        name = req["skill_name"]
        target = req["target_proficiency"]
        importance = req.get("importance", "core")
        weight = 1.5 if importance == "core" else 1.0
        s = student_skills.get(name, {
            "proficiency_score": 0.0, "confidence_level": "None", "evidence_count": 0,
            "assessment_taken": False, "github_signal": False, "project_count": 0,
        })
        current = s["proficiency_score"]
        gap = round(max(target - current, 0.0), 1)
        severity = severity_for_gap(gap)
        unmet_prereqs = unmet_prerequisites(name, student_skills)
        priority = priority_for(severity, importance, unmet_prereqs)

        item = {
            "skill_name": name,
            "current_score": current,
            "target_score": target,
            "gap": gap,
            "severity": severity,
            "priority": priority,
            "reason": reason_for(current, target, s["confidence_level"], s["evidence_count"]),
            "reasons": reasons_for(
                current, target, s["confidence_level"], s["evidence_count"],
                s.get("assessment_taken", False), s.get("github_signal", False),
                s.get("project_count", 0), unmet_prereqs,
            ),
            "missing_subskills": missing_subskills_for(name) if severity != "matched" else [],
            "blocked_by_prerequisites": unmet_prereqs,
        }
        {"matched": matched, "low": low_gap, "medium": medium_gap, "high": high_gap}[severity].append(item)

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