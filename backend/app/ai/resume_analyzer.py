"""
AI Resume Analyzer
-------------------
1. Extract raw text from an uploaded PDF/DOCX resume.
2. Ask the AI provider to extract structured career info as JSON.
3. Validate against ResumeExtraction; on any failure (no API key, timeout,
   malformed JSON), fall back to a deterministic keyword-matching extractor
   so the feature still works with zero AI configuration.

Either way, results are surfaced to the student as "AI detected / pending
verification" — never as an already-verified skill.
"""
import io
import re
from pydantic import ValidationError

from app.ai.ai_provider import ai_provider
from app.ai.prompts.resume_prompt import SYSTEM_PROMPT, build_prompt
from app.ai.schemas.ai_schemas import ResumeExtraction, ExtractedSkill

# Deterministic fallback vocabulary — matched against resume text if AI is unavailable.
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "React", "Angular", "Vue", "FastAPI", "Django", "Flask", "Express.js", "Spring Boot",
    "Node.js", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "CI/CD", "Linux",
    "Machine Learning", "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy",
    "HTML", "CSS", "Tailwind CSS", "REST API", "GraphQL", "System Design",
]


def extract_text_from_file(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if lower.endswith(".docx"):
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    # plain text fallback
    return content.decode("utf-8", errors="ignore")


def _fallback_extraction(resume_text: str) -> ResumeExtraction:
    found = []
    text_lower = resume_text.lower()
    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            # crude evidence: the sentence/line the skill was mentioned in
            idx = text_lower.find(skill.lower())
            snippet = resume_text[max(0, idx - 40): idx + len(skill) + 40].strip().replace("\n", " ")
            found.append(ExtractedSkill(name=skill, confidence=0.55, evidence=f"Keyword match: \u2026{snippet}\u2026"))

    # very rough email/name heuristics so the fallback isn't empty-handed
    name_match = re.search(r"^([A-Z][a-zA-Z.]+(?:\s+[A-Z][a-zA-Z.]+){1,2})", resume_text.strip())
    name = name_match.group(1) if name_match else ""

    return ResumeExtraction(name=name, skills=found)


async def analyze_resume(filename: str, content: bytes) -> tuple[ResumeExtraction, bool]:
    """Returns (extraction, used_ai: bool)."""
    text = extract_text_from_file(filename, content)
    if not text.strip():
        return ResumeExtraction(), False

    ai_json = await ai_provider.generate_json(build_prompt(text), SYSTEM_PROMPT)
    if ai_json is not None:
        try:
            return ResumeExtraction(**ai_json), True
        except ValidationError:
            pass  # fall through to deterministic fallback

    return _fallback_extraction(text), False
