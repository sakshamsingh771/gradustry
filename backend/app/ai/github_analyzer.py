"""
AI GitHub Project Analyzer
---------------------------
Fetches real, public metadata for a GitHub repo (languages, README,
dependency manifests) via the GitHub REST API, derives skills/complexity
deterministically, and — if an AI provider is configured — asks it to add a
short architecture/complexity narrative on top of that real data.

Never claims to prove authorship or mastery: everything is surfaced as
"AI-derived evidence confidence", one signal among several in the Evidence
Confidence Engine, not a verified skill.
"""
import base64
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.ai.ai_provider import ai_provider
from app.ai.prompts.github_prompt import SYSTEM_PROMPT, build_prompt
from app.ai.schemas.ai_schemas import GitHubAnalysisResult, GitHubSkill

DEPENDENCY_FILES = ["requirements.txt", "package.json", "pyproject.toml", "Pipfile", "Dockerfile", "docker-compose.yml"]

LANGUAGE_TO_SKILL = {
    "Python": "Python", "JavaScript": "JavaScript", "TypeScript": "TypeScript",
    "Java": "Java", "Go": "Go", "Rust": "Rust", "C++": "C++", "C#": "C#", "HTML": "HTML", "CSS": "CSS",
}

DEPENDENCY_SIGNALS = {
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask", "express": "Express.js",
    "react": "React", "next": "Next.js", "vue": "Vue", "tailwindcss": "Tailwind CSS",
    "sqlalchemy": "SQLAlchemy", "psycopg2": "PostgreSQL", "pymongo": "MongoDB", "redis": "Redis",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "scikit-learn": "scikit-learn", "pandas": "Pandas",
}


class InvalidRepoUrl(ValueError):
    pass


class GitHubRateLimited(RuntimeError):
    pass


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise InvalidRepoUrl("URL must be a github.com repository link")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise InvalidRepoUrl("URL must look like https://github.com/owner/repo")
    return parts[0], parts[1].removesuffix(".git")


async def _fetch_github_data(owner: str, repo: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        repo_resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
        if repo_resp.status_code == 404:
            raise InvalidRepoUrl("Repository not found or is private")
        if repo_resp.status_code in (403, 429):
            raise GitHubRateLimited("GitHub API rate limit reached. Set GITHUB_TOKEN in the backend .env to raise the limit, then retry.")
        repo_resp.raise_for_status()
        repo_info = repo_resp.json()

        languages: dict = {}
        try:
            lang_resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/languages")
            if lang_resp.status_code == 200:
                languages = lang_resp.json()
        except httpx.HTTPError:
            pass

        readme = ""
        try:
            readme_resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/readme")
            if readme_resp.status_code == 200:
                content = readme_resp.json().get("content", "")
                readme = base64.b64decode(content).decode("utf-8", errors="ignore")
        except (httpx.HTTPError, Exception):
            pass

        dependency_files: dict = {}
        for fname in DEPENDENCY_FILES:
            try:
                resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{fname}")
                if resp.status_code == 200:
                    body = resp.json()
                    if isinstance(body, dict) and body.get("content"):
                        dependency_files[fname] = base64.b64decode(body["content"]).decode("utf-8", errors="ignore")[:2000]
                    else:
                        dependency_files[fname] = "(present)"
            except httpx.HTTPError:
                continue

    return {"repo_info": repo_info, "languages": languages, "readme": readme, "dependency_files": dependency_files}


def _deterministic_analysis(repo_name: str, data: dict) -> GitHubAnalysisResult:
    languages = data["languages"]
    dependency_files = data["dependency_files"]
    readme = data["readme"].lower()
    repo_info = data["repo_info"]

    skills: dict[str, float] = {}
    total_bytes = sum(languages.values()) or 1
    for lang, byte_count in languages.items():
        skill_name = LANGUAGE_TO_SKILL.get(lang, lang)
        skills[skill_name] = max(skills.get(skill_name, 0), round(0.5 + 0.4 * (byte_count / total_bytes), 2))

    all_dep_text = " ".join(dependency_files.values()).lower() + " " + readme
    for keyword, skill_name in DEPENDENCY_SIGNALS.items():
        if keyword in all_dep_text:
            skills[skill_name] = max(skills.get(skill_name, 0), 0.7)
    if "Dockerfile" in dependency_files or "docker-compose.yml" in dependency_files:
        skills["Docker"] = max(skills.get("Docker", 0), 0.75)

    # complexity heuristic from real, observable signals
    signal_count = len(languages) + len(dependency_files) + (1 if readme else 0)
    has_tests = "test" in all_dep_text or "spec" in all_dep_text
    size_kb = repo_info.get("size", 0)
    if signal_count >= 5 and has_tests and size_kb > 500:
        level = "advanced"
    elif signal_count >= 3:
        level = "intermediate"
    else:
        level = "beginner"

    evidence_quality = min(1.0, 0.3 + 0.1 * signal_count + (0.15 if has_tests else 0) + (0.1 if readme else 0))

    return GitHubAnalysisResult(
        repository=repo_name,
        skills=[GitHubSkill(name=k, confidence=round(v, 2)) for k, v in skills.items()],
        project_level=level,
        evidence_quality=round(evidence_quality, 2),
        architecture_notes="Deterministic analysis based on language mix, dependency manifests, and README presence.",
    )


async def analyze_github_repo(url: str) -> tuple[GitHubAnalysisResult, bool]:
    """Returns (result, used_ai: bool). Raises InvalidRepoUrl for bad input."""
    owner, repo = parse_github_url(url)
    data = await _fetch_github_data(owner, repo)
    repo_name = data["repo_info"].get("full_name", f"{owner}/{repo}")

    deterministic = _deterministic_analysis(repo_name, data)

    ai_json = await ai_provider.generate_json(
        build_prompt(repo_name, data["readme"], data["languages"], data["dependency_files"]),
        SYSTEM_PROMPT,
    )
    if ai_json is not None:
        try:
            ai_result = GitHubAnalysisResult(**ai_json)
            merged_skills = {s.name: s.confidence for s in deterministic.skills}
            for s in ai_result.skills:
                merged_skills[s.name] = max(merged_skills.get(s.name, 0), s.confidence)
            ai_result.skills = [GitHubSkill(name=k, confidence=v) for k, v in merged_skills.items()]
            return ai_result, True
        except ValidationError:
            pass

    return deterministic, False
