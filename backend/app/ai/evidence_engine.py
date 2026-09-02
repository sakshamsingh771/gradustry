"""
Evidence Confidence Engine
--------------------------
Turns a bag of evidence signals (certificates, GitHub activity, projects,
assessment scores, industry feedback) into:
  - a 0-100 proficiency_score for a StudentSkill
  - a Low/Medium/High confidence_level

Design intent (per product spec):
  - This is NOT a "proof of truth" detector. It is an evidence-weighted
    estimate, and every score should be explainable ("Why?").
  - Different evidence types carry different base signal strength and are
    modulated by verification status.
"""

TYPE_BASE_SIGNAL = {
    "certificate": 55.0,
    "github": 50.0,
    "project": 45.0,
    "assessment": 70.0,          # objective, so weighted highest
    "industry_feedback": 75.0,   # real-world validation, weighted highest
    "resume": 35.0,              # AI-extracted from a resume, least verified — lowest base signal
}

STATUS_MULTIPLIER = {
    "verified": 1.0,
    "pending_review": 0.6,
    "needs_review": 0.4,
    "suspicious": 0.1,
}


def score_single_evidence(evidence_type: str, status: str, override_score: float | None = None) -> float:
    """Signal strength (0-100) contributed by one piece of evidence."""
    base = override_score if override_score is not None else TYPE_BASE_SIGNAL.get(evidence_type, 40.0)
    multiplier = STATUS_MULTIPLIER.get(status, 0.5)
    return round(base * multiplier, 1)


def aggregate_proficiency(evidence_signals: list[float]) -> float:
    """
    Aggregate multiple evidence signals into one proficiency score.
    Uses a diminishing-returns sum so that having *multiple* independent
    signals (cert + github + assessment) pushes the score up, but a single
    strong signal alone can't claim near-100 mastery.
    """
    if not evidence_signals:
        return 0.0
    signals = sorted(evidence_signals, reverse=True)
    score = 0.0
    decay = 1.0
    for s in signals:
        score += s * decay
        decay *= 0.55  # each additional signal contributes less
    return round(min(score, 100.0), 1)


def confidence_level(evidence_count: int, verified_count: int, proficiency: float) -> str:
    if evidence_count == 0:
        return "None"
    if verified_count >= 2 and proficiency >= 60:
        return "High"
    if verified_count >= 1 or evidence_count >= 2:
        return "Medium"
    return "Low"


def explain(evidences: list[dict]) -> list[str]:
    """Human-readable 'Why?' lines for the Skill Passport UI."""
    lines = []
    for e in evidences:
        label = {
            "certificate": "Certificate",
            "github": "GitHub project",
            "project": "Project submission",
            "assessment": "Assessment",
            "industry_feedback": "Industry feedback",
        }.get(e["type"], e["type"].title())
        lines.append(f"{label} — {e['status'].replace('_', ' ')} (signal {e['signal_score']}/100)")
    return lines


def recompute_student_skill(evidences: list[dict]) -> dict:
    """
    evidences: list of {type, status, signal_score}
    Returns {proficiency_score, confidence_level, why}
    """
    signals = [e["signal_score"] for e in evidences]
    proficiency = aggregate_proficiency(signals)
    verified = sum(1 for e in evidences if e["status"] == "verified")
    confidence = confidence_level(len(evidences), verified, proficiency)
    return {
        "proficiency_score": proficiency,
        "confidence_level": confidence,
        "why": explain(evidences),
    }
