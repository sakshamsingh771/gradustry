"""
AI Career Copilot (Phase 10)
------------------------------
NOT a generic chatbot: every answer is grounded in a context object built
from the authenticated student's own data (Skill Passport, gap report for
their career goal, applications, roadmap progress). Never fabricates —
if the context doesn't support an answer, it says so.

Falls back to a deterministic, template-based answer built from the exact
same context object when the AI provider is unavailable — the spec's own
example answer format ("Strong areas / Priority gaps / Recommended next
action") is deterministic-friendly by design, so the fallback is not a
degraded experience, just a non-AI-phrased one.
"""
from pydantic import ValidationError

from app.ai.ai_provider import ai_provider
from app.ai.prompts.copilot_prompt import SYSTEM_PROMPT, build_prompt
from app.ai.schemas.ai_schemas import CopilotAnswer


def _fallback_answer(question: str, context: dict) -> CopilotAnswer:
    q = question.lower()
    readiness = context.get("career_readiness")
    goal = context.get("career_goal") or "your target role"
    matched = context.get("gap_matched", [])
    high_gaps = context.get("gap_high", [])
    medium_gaps = context.get("gap_medium", [])
    best_match = context.get("best_opportunity")
    used = []

    if readiness is None:
        return CopilotAnswer(
            answer="I don't have enough data yet — set a career goal and add some evidence to your Skill Passport first, and I'll be able to give you a grounded answer.",
            used_data_points=[],
        )
    used.append("career_readiness")

    if "ready" in q or "readiness" in q:
        gaps_txt = ", ".join(g["skill_name"] for g in high_gaps) or "none major"
        used += ["gap_high"]
        return CopilotAnswer(
            answer=f"Your current {goal} readiness is {readiness}%. "
                   f"Strong areas: {', '.join(matched) or 'still building these'}. "
                   f"Priority gaps: {gaps_txt}.",
            used_data_points=used,
        )

    if "missing" in q or "gap" in q or "learn next" in q:
        used += ["gap_high", "gap_medium"]
        top = (high_gaps + medium_gaps)[:3]
        if not top:
            return CopilotAnswer(answer="No significant gaps detected against your current career goal right now — nice work.", used_data_points=used)
        lines = [f"{g['skill_name']} ({g['current_score']:.0f}% → {g['target_score']:.0f}%)" for g in top]
        return CopilotAnswer(answer="Your priority gaps right now: " + "; ".join(lines) + ". Start with the first one — build a roadmap for it from the Skill Gap page.", used_data_points=used)

    if "match" in q and ("low" in q or "why" in q):
        if not best_match:
            return CopilotAnswer(answer="You don't have any opportunity matches yet — add more evidence or check back once opportunities are posted.", used_data_points=used)
        used.append("best_opportunity")
        used_ai_note = ', '.join(best_match.get('below_target_skills', [])) or "nothing major — you're close"
        return CopilotAnswer(
            answer=f"Your best current match is '{best_match['title']}' at {best_match['match_score']:.0f}%. "
                   f"It's held back by: {used_ai_note}.",
            used_data_points=used,
        )

    if "opportunit" in q and "fit" in q:
        if not best_match:
            return CopilotAnswer(answer="No opportunities are matched to your profile yet.", used_data_points=used)
        used.append("best_opportunity")
        return CopilotAnswer(answer=f"Right now, '{best_match['title']}' is your strongest fit at {best_match['match_score']:.0f}% match.", used_data_points=used)

    if "this week" in q or "what should i do" in q:
        used += ["gap_high"]
        if high_gaps:
            return CopilotAnswer(answer=f"Focus on {high_gaps[0]['skill_name']} this week — it's your biggest gap toward {goal}. Generate a roadmap for it and complete the first step.", used_data_points=used)
        return CopilotAnswer(answer="You're in good shape — consider taking a re-assessment on a skill you haven't tested recently to keep your Skill Passport current.", used_data_points=used)

    # generic fallback: the spec's own example shape
    gaps_txt = ", ".join(f"{g['skill_name']}" for g in high_gaps[:3]) or "none major right now"
    return CopilotAnswer(
        answer=f"Your current {goal} readiness is {readiness}%. Strong areas: {', '.join(matched) or 'still building these'}. "
               f"Priority gaps: {gaps_txt}. Recommended next action: open the Skill Gap page and build a roadmap for your top gap.",
        used_data_points=used,
    )


async def answer_question(question: str, context: dict) -> tuple[CopilotAnswer, bool]:
    ai_json = await ai_provider.generate_json(build_prompt(question, context), SYSTEM_PROMPT)
    if ai_json is not None:
        try:
            return CopilotAnswer(**ai_json), True
        except ValidationError:
            pass
    return _fallback_answer(question, context), False
