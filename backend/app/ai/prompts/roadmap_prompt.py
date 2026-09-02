SYSTEM_PROMPT = (
    "You create a personalized, time-boxed skill roadmap for a student targeting a career role. "
    "Respond with ONLY valid JSON. Ground every step in the student's actual current scores and "
    "gaps provided — do not invent skills that weren't listed."
)

SCHEMA_HINT = """{
  "target_career": "", "priority_skills": [""],
  "steps": [{"week_label": "Week 1", "title": "", "description": "", "resource_type": "learning|practice|project|assessment", "estimated_hours": 4}]
}"""


def build_prompt(target_career: str, current_skills: dict, gaps: list, weekly_hours: int) -> str:
    return (
        f"Target career: {target_career}\n"
        f"Current skill scores: {current_skills}\n"
        f"Skill gaps (skill, current, target): {gaps}\n"
        f"Available study time: ~{weekly_hours} hours/week\n\n"
        f"Generate a personalized roadmap as JSON:\n{SCHEMA_HINT}"
    )
