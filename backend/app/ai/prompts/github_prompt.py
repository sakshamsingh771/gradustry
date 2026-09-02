SYSTEM_PROMPT = (
    "You analyze a public GitHub repository's metadata (README, languages, dependency files) "
    "to estimate demonstrated technical skills. Respond with ONLY valid JSON. "
    "Use 'AI-derived evidence confidence', never claim verified authorship or mastery. "
    "Base every skill strictly on the provided repo data — do not guess technologies absent from it."
)

SCHEMA_HINT = """{
  "repository": "", "skills": [{"name": "", "confidence": 0.0}],
  "project_level": "beginner|intermediate|advanced", "evidence_quality": 0.0,
  "architecture_notes": ""
}"""


def build_prompt(repo_name: str, readme: str, languages: dict, dependency_files: dict) -> str:
    return (
        f"Repository: {repo_name}\n"
        f"Languages (bytes): {languages}\n"
        f"Dependency file contents: {dependency_files}\n"
        f"README (truncated): {readme[:3000]}\n\n"
        f"Analyze and return this JSON schema:\n{SCHEMA_HINT}"
    )
