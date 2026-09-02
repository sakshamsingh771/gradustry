"""
Gap Closure Roadmap Generator
------------------------------
Turns "you need to learn X" into a concrete staged journey: learning ->
practice -> mini challenge -> project task -> re-assessment.

In production this would retrieve approved content via RAG (Approved Content
-> Embeddings -> Vector Store -> Retrieval -> LLM personalization). For the
MVP we use a template library keyed by skill, with a sensible generic
fallback, so the roadmap is always populated even for skills without a
custom template — and never invents unvetted "facts", only structure.
"""

SKILL_TEMPLATES: dict[str, list[dict]] = {
    "Docker": [
        {"title": "Docker fundamentals", "resource_type": "learning", "description": "Containers vs VMs, images, the Docker CLI."},
        {"title": "Images and containers", "resource_type": "learning", "description": "Build, tag, and run images; layers and caching."},
        {"title": "Write a Dockerfile", "resource_type": "practice", "description": "Containerize a small script end to end."},
        {"title": "Dockerize a FastAPI service", "resource_type": "project", "description": "Apply it to a real API project with a multi-stage build."},
        {"title": "Docker Compose", "resource_type": "practice", "description": "Multi-container setup: API + Postgres + networking."},
        {"title": "Re-assessment", "resource_type": "assessment", "description": "Verify improvement with a focused assessment."},
    ],
    "SQL": [
        {"title": "Relational fundamentals", "resource_type": "learning", "description": "Tables, keys, normalization."},
        {"title": "Joins and aggregation", "resource_type": "practice", "description": "Write queries across multiple related tables."},
        {"title": "Query optimization", "resource_type": "learning", "description": "Indexes, EXPLAIN plans, common pitfalls."},
        {"title": "Schema design project", "resource_type": "project", "description": "Design and query a schema for a real use case."},
        {"title": "Re-assessment", "resource_type": "assessment", "description": "Verify improvement with a focused assessment."},
    ],
    "AWS": [
        {"title": "Cloud fundamentals", "resource_type": "learning", "description": "Regions, IAM, core compute/storage services."},
        {"title": "Deploy a static app to S3", "resource_type": "practice", "description": "Hands-on with storage + hosting basics."},
        {"title": "Deploy an API with EC2 or Lambda", "resource_type": "project", "description": "Ship a working backend to the cloud."},
        {"title": "Re-assessment", "resource_type": "assessment", "description": "Verify improvement with a focused assessment."},
    ],
}

GENERIC_TEMPLATE: list[dict] = [
    {"title": "Core concepts", "resource_type": "learning", "description": "Build a solid mental model of the fundamentals."},
    {"title": "Guided practice", "resource_type": "practice", "description": "Apply the concepts in small, focused exercises."},
    {"title": "Mini challenge", "resource_type": "practice", "description": "A slightly harder problem to stress-test understanding."},
    {"title": "Applied project task", "resource_type": "project", "description": "Use the skill in a realistic, portfolio-worthy task."},
    {"title": "Re-assessment", "resource_type": "assessment", "description": "Verify improvement with a focused assessment."},
]


def generate_roadmap(skill_name: str, current_score: float, target_score: float) -> list[dict]:
    template = SKILL_TEMPLATES.get(skill_name, GENERIC_TEMPLATE)
    steps = []
    for i, step in enumerate(template):
        steps.append({
            "order_index": i,
            "title": step["title"],
            "description": step["description"],
            "resource_type": step["resource_type"],
            "status": "not_started",
            "baseline_score": current_score,
            "target_score": target_score,
        })
    return steps


def gap_status_after_reassessment(baseline: float, new_score: float, target: float) -> str:
    if new_score >= target:
        return "Gap Closed"
    if new_score > baseline:
        return "Gap Partially Closed"
    return "Needs More Work"


# ---------------------------------------------------------------------------
# AI-personalized roadmap (Phase 7). Falls back to generate_roadmap() above —
# per-skill template roadmap remains untouched and is still used whenever the
# AI provider is unavailable or its output fails validation.
# ---------------------------------------------------------------------------
async def generate_ai_roadmap(target_career: str, current_skills: dict, gaps: list, weekly_hours: int = 6):
    """
    current_skills: {skill_name: score}
    gaps: [{skill_name, current_score, target_score}]
    Returns (AIRoadmapResult | None, used_ai: bool)
    """
    from pydantic import ValidationError
    from app.ai.ai_provider import ai_provider
    from app.ai.prompts.roadmap_prompt import SYSTEM_PROMPT, build_prompt
    from app.ai.schemas.ai_schemas import AIRoadmapResult

    ai_json = await ai_provider.generate_json(
        build_prompt(target_career, current_skills, gaps, weekly_hours), SYSTEM_PROMPT
    )
    if ai_json is not None:
        try:
            return AIRoadmapResult(**ai_json), True
        except ValidationError:
            pass
    return None, False
