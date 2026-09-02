"""
AI Evidence Verifier
---------------------
Adds an AI-derived relevance/consistency signal alongside the existing
deterministic Evidence Confidence Engine (app/ai/evidence_engine.py), which
is untouched and remains the source of truth for proficiency_score.

IMPORTANT: this module NEVER declares a certificate authentic. Authenticity
still requires issuer/API/manual verification (see students.verify_evidence).
AI here only assesses whether the evidence *description* is relevant,
internally consistent, and plausible for the claimed skill.
"""
import difflib

from pydantic import ValidationError

from app.ai.ai_provider import ai_provider
from app.ai.schemas.ai_schemas import EvidenceAIAnalysis

SYSTEM_PROMPT = (
    "You assess whether a piece of student-submitted evidence plausibly supports a claimed "
    "skill. You are NOT verifying authenticity — only relevance, internal consistency, and "
    "description quality. Respond with ONLY valid JSON: "
    '{"relevance_score": 0-1, "consistency_score": 0-1, "explanation": "", "flags": [""]}. '
    "Flag vague, generic, or inconsistent descriptions."
)


def _fallback_analysis(skill_name: str, evidence_type: str, title: str, description: str) -> EvidenceAIAnalysis:
    """Deterministic proxy: lexical overlap + description length as a relevance/consistency proxy."""
    text = f"{title} {description}".lower()
    skill_lower = skill_name.lower()
    relevance = difflib.SequenceMatcher(None, skill_lower, text).ratio()
    relevance = max(relevance, 0.6 if skill_lower in text else 0.25)
    consistency = min(1.0, 0.4 + len(description.split()) / 40)
    flags = []
    if len(description.split()) < 4:
        flags.append("Description is very short — consider adding more detail.")
    if skill_lower not in text:
        flags.append(f"'{skill_name}' isn't explicitly mentioned in the title or description.")
    return EvidenceAIAnalysis(
        relevance_score=round(relevance, 2),
        consistency_score=round(consistency, 2),
        explanation="Deterministic lexical-overlap analysis (AI provider not available).",
        flags=flags,
    )


async def analyze_evidence(skill_name: str, evidence_type: str, title: str, description: str) -> tuple[EvidenceAIAnalysis, bool]:
    prompt = (
        f"Claimed skill: {skill_name}\nEvidence type: {evidence_type}\n"
        f"Title: {title}\nDescription: {description}\n\nAnalyze as JSON."
    )
    ai_json = await ai_provider.generate_json(prompt, SYSTEM_PROMPT)
    if ai_json is not None:
        try:
            return EvidenceAIAnalysis(**ai_json), True
        except ValidationError:
            pass
    return _fallback_analysis(skill_name, evidence_type, title, description), False
