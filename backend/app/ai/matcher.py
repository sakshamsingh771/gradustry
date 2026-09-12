"""
Candidate/Opportunity Matcher
-----------------------------
Deterministic eligibility rules + weighted scoring model, with a
human-readable explanation. Per spec: do not rely purely on an LLM for
ranking — this module IS the ranking model. An LLM would only be used
downstream to phrase the explanation in natural language, which the
frontend already does from structured fields here.

Phase 5: skill-level match now reuses the exact same verification-state
classifier as the Skill Gap Engine (app.ai.skill_gap_engine), so a
"required skill" drives both Opportunity Matching and Skill Gap Analysis
from one shared rule set — never two competing definitions of what counts
as demonstrated/unverified/missing.
"""

try:
    from app.ai.skill_gap_engine import verification_state_for  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback when the engine is unavailable
    def verification_state_for(
        current_score: float,
        required_score: float,
        confidence_level: str | None = None,
        evidence_count: int = 0,
    ) -> str:
        """Fallback verification-state classifier used when the shared engine is unavailable."""
        if current_score >= required_score:
            return "demonstrated"
        if evidence_count > 0 and confidence_level not in {"None", "Low"}:
            return "unverified"
        return "missing"


def check_eligibility(student: dict, opportunity: dict) -> list[dict]:
    """Returns itemized eligibility checks: [{check, passed, detail}].
    Only checks backed by real fields on the student/opportunity — no
    fabricated criteria (e.g. no location/assessment gating that the data
    model doesn't actually support)."""
    checks = []

    if opportunity.get("final_year_only"):
        passed = student.get("year_of_study", 1) >= 4
        checks.append({
            "check": "Final-year eligibility", "passed": passed,
            "detail": "Open to final-year students only." if not passed else "Meets final-year requirement.",
        })

    min_year = opportunity.get("min_year_of_study", 1)
    if min_year > 1:
        passed = student.get("year_of_study", 1) >= min_year
        checks.append({
            "check": f"Minimum year of study ({min_year})", "passed": passed,
            "detail": f"Requires year {min_year}+; student is year {student.get('year_of_study', 1)}.",
        })

    return checks


def score_match(student_skills: dict[str, dict], required_skills: list[dict]) -> dict:
    """
    student_skills: {skill_name: {proficiency_score, evidence_count, confidence_level}}
    required_skills: [{skill_name, min_proficiency, weight}]
    Returns match_score (0-100) + matched/below-target skill lists + a
    per-skill breakdown with verification state (Phase 5).
    """
    if not required_skills:
        return {
            "match_score": 0.0, "matched_skills": [], "below_target_skills": [],
            "relevant_evidence_count": 0, "skill_breakdown": [],
        }

    weighted_sum = 0.0
    weight_total = 0.0
    matched, below_target = [], []
    evidence_count = 0
    skill_breakdown = []

    for req in required_skills:
        name = req["skill_name"]
        min_p = req["min_proficiency"]
        weight = req.get("weight", 1.0)
        s = student_skills.get(name, {"proficiency_score": 0.0, "evidence_count": 0, "confidence_level": "None"})
        current = s["proficiency_score"]
        evidence_count += s.get("evidence_count", 0)

        # score contribution: 1.0 if meets/exceeds min, else partial credit scaled to min_p
        contribution = 1.0 if current >= min_p else (current / min_p if min_p > 0 else 0.0)
        weighted_sum += contribution * weight
        weight_total += weight

        if current >= min_p:
            matched.append(name)
        else:
            below_target.append(name)

        verification_state = verification_state_for(current, min_p, s.get("confidence_level", "None"), s.get("evidence_count", 0))
        skill_breakdown.append({
            "skill_name": name,
            "current_score": current,
            "required_score": min_p,
            "percent_of_requirement": round(min(current / min_p, 1.0) * 100, 1) if min_p > 0 else 100.0,
            "verification_state": verification_state,
            "weight": weight,
        })

    match_score = round((weighted_sum / weight_total) * 100, 1) if weight_total > 0 else 0.0
    return {
        "match_score": match_score,
        "matched_skills": matched,
        "below_target_skills": below_target,
        "relevant_evidence_count": evidence_count,
        "skill_breakdown": skill_breakdown,
    }


def build_match(student: dict, opportunity: dict, student_skills: dict, required_skills: list[dict]) -> dict:
    eligibility_checks = check_eligibility(student, opportunity)
    missing_eligibility = [c["check"] for c in eligibility_checks if not c["passed"]]
    score_result = score_match(student_skills, required_skills)
    is_eligible = len(missing_eligibility) == 0

    return {
        "match_score": score_result["match_score"] if is_eligible else score_result["match_score"] * 0.5,
        "explanation": {
            "matched_skills": score_result["matched_skills"],
            "below_target_skills": score_result["below_target_skills"],
            "missing_eligibility": missing_eligibility,
            "eligibility_checks": eligibility_checks,
            "skill_breakdown": score_result["skill_breakdown"],
            "relevant_evidence_count": score_result["relevant_evidence_count"],
            "is_eligible": is_eligible,
        },
    }


# ---------------------------------------------------------------------------
# Hybrid AI Opportunity Matching (Phase 8)
# Architecture: Hard Eligibility -> existing Weighted Matcher (above,
# untouched) -> AI Semantic Understanding -> Final Recommendation.
# The deterministic score above is NEVER overridden by more than a small,
# bounded nudge — AI adds understanding of related skills and an
# explanation, it does not replace the eligibility/weighted core.
# ---------------------------------------------------------------------------

# Deterministic fallback for "semantic understanding" when no AI provider is
# configured: related-technology clusters, so e.g. a Django/Flask background
# still earns partial recognition against a FastAPI requirement.
SKILL_SYNONYM_CLUSTERS: list[set[str]] = [
    {"FastAPI", "Django", "Flask", "Express.js", "Spring Boot"},
    {"React", "Vue", "Angular"},
    {"PostgreSQL", "MySQL", "SQL"},
    {"AWS", "Azure", "GCP"},
    {"Docker", "Kubernetes"},
    {"PyTorch", "TensorFlow", "scikit-learn"},
]


def _related_skills_fallback(student_skills: dict, required_skills: list[dict]) -> list[str]:
    related = []
    for req in required_skills:
        name = req["skill_name"]
        if name in student_skills:
            continue  # already directly matched/considered above
        cluster = next((c for c in SKILL_SYNONYM_CLUSTERS if name in c), None)
        if not cluster:
            continue
        for alt in cluster - {name}:
            if alt in student_skills and student_skills[alt].get("proficiency_score", 0) >= 50:
                related.append(f"{alt} (related to required {name})")
                break
    return related


async def build_match_hybrid(student: dict, opportunity: dict, student_skills: dict, required_skills: list[dict]) -> dict:
    """Async, AI-enriched version of build_match(). Falls back to deterministic-only when AI is unavailable."""
    from pydantic import ValidationError
    from app.ai.ai_provider import ai_provider
    from app.ai.schemas.ai_schemas import MatchExplanationAI

    base = build_match(student, opportunity, student_skills, required_skills)
    related_fallback = _related_skills_fallback(student_skills, required_skills)

    prompt = (
        "Opportunity requires: " + str([r["skill_name"] for r in required_skills]) + "\n"
        "Student's demonstrated skills and scores: " + str({k: v.get("proficiency_score", 0) for k, v in student_skills.items()}) + "\n"
        "Deterministic matched skills: " + str(base["explanation"]["matched_skills"]) + "\n"
        "Deterministic below-target skills: " + str(base["explanation"]["below_target_skills"]) + "\n\n"
        "Recognize related/adjacent technologies (e.g. Django Rest Framework relates to FastAPI) and explain "
        "the match in 1-2 sentences grounded ONLY in the data above. Respond as JSON: "
        '{"match_score_adjustment": -15..15, "strengths": [...], "weaknesses": [...], '
        '"related_skills_recognized": [...], "recommendation_reason": "..."}'
    )
    system_prompt = (
        "You explain job/internship match scores for a career platform. Ground every claim strictly in "
        "the provided data — never invent skills or scores. Keep match_score_adjustment small and only "
        "use it to reflect genuinely related/adjacent skills the deterministic scorer couldn't see."
    )

    ai_json = await ai_provider.generate_json(prompt, system_prompt)
    ai_enrichment = None
    used_ai = False
    if ai_json is not None:
        try:
            ai_enrichment = MatchExplanationAI(**ai_json)
            used_ai = True
        except ValidationError:
            ai_enrichment = None

    if ai_enrichment is None:
        matched = base["explanation"]["matched_skills"]
        below = base["explanation"]["below_target_skills"]
        reason = (
            f"Strong match on {', '.join(matched)}." if matched else "Limited overlap with required skills yet."
        )
        if below:
            reason += f" Primary gap: {below[0]}, where your current proficiency is below the required level."
        ai_enrichment = MatchExplanationAI(
            match_score_adjustment=0.0,
            strengths=matched,
            weaknesses=below,
            related_skills_recognized=related_fallback,
            recommendation_reason=reason,
        )

    final_score = round(min(100.0, max(0.0, base["match_score"] + ai_enrichment.match_score_adjustment)), 1)

    return {
        "match_score": final_score,
        "explanation": {
            **base["explanation"],
            "strengths": ai_enrichment.strengths,
            "weaknesses": ai_enrichment.weaknesses,
            "related_skills_recognized": ai_enrichment.related_skills_recognized,
            "recommendation_reason": ai_enrichment.recommendation_reason,
            "ai_enhanced": used_ai,
        },
    }
