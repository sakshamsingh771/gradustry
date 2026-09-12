"""
Standard Skill Taxonomy (Phase 4)
----------------------------------
Every part of Gradustry that turns free text into a Skill row — resume
extraction, GitHub analysis, assessments, industry-posted requirements,
student self-entry, Learning Hub programs — MUST go through
`get_or_create_skill()` here instead of querying/inserting `Skill` directly.

Before this module, five separate call sites each did their own
`db.query(Skill).filter(Skill.name == name).first()` with no
normalization, so "Python", "python", and "Python Programming" could
silently become three different Skill rows with three different
StudentSkill/proficiency tracks. This module is the single choke point
that prevents that.

This is a deterministic, rule-based normalizer (a lookup table + string
rules) — NOT a machine-learning or embedding-based system. It is
intentionally simple and explainable: every normalization is a literal
alias in ALIASES or a mechanical casing rule, never a similarity guess.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.skill import Skill

# Deterministic alias table: raw (lowercased) text -> canonical display name.
# Add to this list as real duplicate variants are observed in production data.
ALIASES: dict[str, str] = {
    "js": "JavaScript", "javascript": "JavaScript",
    "reactjs": "React", "react.js": "React", "react js": "React",
    "nodejs": "Node.js", "node js": "Node.js", "node": "Node.js",
    "py": "Python", "python programming": "Python", "python3": "Python",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "docker": "Docker",
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "html": "HTML", "css": "CSS", "html5": "HTML", "css3": "CSS",
    "sql": "SQL", "mysql": "MySQL",
    "git": "Git", "github": "Git",
    "communication": "Communication", "communication skills": "Communication",
    "oop": "Object-Oriented Programming", "object oriented programming": "Object-Oriented Programming",
    "dsa": "Data Structures & Algorithms", "data structures and algorithms": "Data Structures & Algorithms",
    "rest api": "REST APIs", "rest apis": "REST APIs", "restful api": "REST APIs",
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "typescript": "TypeScript", "ts": "TypeScript",
}

# Words/acronyms that should stay all-uppercase when title-casing an
# unrecognized skill name (deterministic rule, not a lookup miss handler).
_KEEP_UPPER = {"sql", "html", "css", "aws", "gcp", "api", "apis", "ai", "ml", "ui", "ux", "ci", "cd", "qa"}

# Deterministic category inference — a fixed keyword->category map, not AI.
_CATEGORY_KEYWORDS: dict[str, str] = {
    "python": "Programming Languages", "javascript": "Programming Languages", "typescript": "Programming Languages",
    "java": "Programming Languages", "c++": "Programming Languages", "c#": "Programming Languages",
    "react": "Frontend", "html": "Frontend", "css": "Frontend", "vue": "Frontend", "angular": "Frontend",
    "node.js": "Backend", "fastapi": "Backend", "flask": "Backend", "django": "Backend", "rest apis": "Backend",
    "docker": "DevOps", "kubernetes": "DevOps", "ci/cd": "DevOps",
    "aws": "Cloud", "gcp": "Cloud", "azure": "Cloud",
    "sql": "Databases", "postgresql": "Databases", "mysql": "Databases", "mongodb": "Databases",
    "machine learning": "AI/ML", "deep learning": "AI/ML",
    "git": "Tools",
    "communication": "Soft Skills", "teamwork": "Soft Skills", "leadership": "Soft Skills",
}


def normalize_skill_name(raw_name: str) -> str:
    """Deterministic canonicalization: trim/collapse whitespace, apply the
    alias table (case-insensitive), and otherwise title-case while keeping
    known acronyms upper-case."""
    cleaned = " ".join(raw_name.strip().split())
    if not cleaned:
        return cleaned

    alias = ALIASES.get(cleaned.lower())
    if alias:
        return alias

    words = []
    for w in cleaned.split(" "):
        words.append(w.upper() if w.lower() in _KEEP_UPPER else w[:1].upper() + w[1:])
    return " ".join(words)


def infer_category(canonical_name: str) -> str:
    return _CATEGORY_KEYWORDS.get(canonical_name.lower(), "General")


def get_or_create_skill(db: Session, raw_name: str) -> Skill:
    """The single source of truth for turning any free-text skill mention
    into a Skill row. Looks up case-insensitively against the canonical
    name so re-normalized text always resolves to the same row."""
    canonical = normalize_skill_name(raw_name)
    existing = db.query(Skill).filter(func.lower(Skill.name) == canonical.lower()).first()
    if existing:
        return existing
    skill = Skill(name=canonical, category=infer_category(canonical))
    db.add(skill)
    db.flush()
    return skill


def find_skill(db: Session, raw_name: str) -> Skill | None:
    """Read-only, case-insensitive lookup — for endpoints that should 404
    on an unknown skill rather than silently create one."""
    canonical = normalize_skill_name(raw_name)
    return db.query(Skill).filter(func.lower(Skill.name) == canonical.lower()).first()
