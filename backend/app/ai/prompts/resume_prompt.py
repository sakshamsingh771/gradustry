SYSTEM_PROMPT = (
    "You extract structured career information from resume text. "
    "Respond with ONLY valid JSON matching the given schema — no prose, no markdown fences. "
    "Every skill must include a confidence between 0 and 1 and a short 'evidence' quote "
    "from the resume text justifying it. Never invent skills not supported by the text."
)

SCHEMA_HINT = """{
  "name": "", "education": [""], "experience": [""], "projects": [""],
  "skills": [{"name": "", "confidence": 0.0, "evidence": ""}],
  "programming_languages": [""], "frameworks": [""], "databases": [""],
  "cloud_tools": [""], "certifications": [""], "soft_skills": [""], "career_roles": [""]
}"""


def build_prompt(resume_text: str) -> str:
    return f"Resume text:\n---\n{resume_text[:8000]}\n---\n\nExtract into this JSON schema:\n{SCHEMA_HINT}"
