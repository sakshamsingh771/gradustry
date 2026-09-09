"""
Static skill taxonomy: subskills + prerequisite chains.
Deterministic on purpose — the gap engine must not hallucinate subskills
or dependency chains, so this is hand-curated data, not AI output.
"""

SUBSKILLS: dict[str, list[str]] = {
    "Deep Learning": ["CNN", "RNN", "Transformers", "PyTorch"],
    "Machine Learning": ["Regression", "Classification", "Feature Engineering", "Scikit-learn"],
    "React": ["Hooks", "State Management", "Component Design", "Routing"],
    "Docker": ["Images", "Dockerfile", "Docker Compose", "Networking"],
    "Kubernetes": ["Pods", "Deployments", "Services", "Helm"],
    "SQL": ["Joins", "Indexing", "Normalization", "Query Optimization"],
    "System Design": ["Scalability", "Caching", "Load Balancing", "Database Sharding"],
}

# skill -> list of prerequisite skill names that should be reasonably solid
# before this skill's score can be trusted / prioritized.
PREREQUISITES: dict[str, list[str]] = {
    "Machine Learning": ["Python"],
    "Deep Learning": ["Python", "Machine Learning"],
    "Gen AI": ["Deep Learning"],
    "React": ["JavaScript", "HTML"],
    "JavaScript": ["HTML"],
    "Kubernetes": ["Docker"],
    "Cloud": ["Kubernetes"],
}

PREREQUISITE_PASS_THRESHOLD = 55.0  # a prerequisite is "solid enough" at/above this score


def missing_subskills_for(skill_name: str) -> list[str]:
    return SUBSKILLS.get(skill_name, [])


def prerequisites_for(skill_name: str) -> list[str]:
    return PREREQUISITES.get(skill_name, [])


def unmet_prerequisites(skill_name: str, student_skills: dict[str, dict]) -> list[str]:
    unmet = []
    for prereq in prerequisites_for(skill_name):
        score = student_skills.get(prereq, {}).get("proficiency_score", 0.0)
        if score < PREREQUISITE_PASS_THRESHOLD:
            unmet.append(prereq)
    return unmet