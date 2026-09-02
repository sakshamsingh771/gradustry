SYSTEM_PROMPT = (
    "You write a single technical assessment question targeted at a student's weak topic. "
    "Respond with ONLY valid JSON. The question must be answerable from the given topic and "
    "difficulty, with exactly one unambiguous correct option."
)

SCHEMA_HINT = """{
  "topic": "", "difficulty": "beginner|intermediate|advanced", "question_type": "mcq",
  "prompt": "", "options": ["", "", "", ""], "correct_answer": ["1"], "explanation": ""
}"""


def build_prompt(skill_name: str, topic: str, difficulty: str) -> str:
    return f"Skill: {skill_name}\nWeak topic: {topic}\nDifficulty: {difficulty}\n\nGenerate one question as JSON:\n{SCHEMA_HINT}"
