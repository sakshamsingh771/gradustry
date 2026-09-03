"""
Profile Strength — deterministic, explainable, like Career Readiness.
Never a fixed/fake percentage: every checklist item is a real fact about
the student's data.
"""

CHECKLIST_WEIGHTS = {
    "personal_info": 15,   # bio present
    "education": 15,       # branch + career_goal set
    "github_linked": 10,   # github_username set
    "skills": 25,          # at least one tracked skill
    "evidence": 20,        # at least one skill has evidence
    "assessment": 15,      # at least one completed assessment
}


def compute_profile_strength(
    bio: str,
    branch: str,
    career_goal: str,
    github_username: str,
    skill_count: int,
    evidence_count: int,
    assessment_count: int,
) -> dict:
    checklist = {
        "personal_info": bool(bio.strip()),
        "education": bool(branch.strip() and career_goal.strip()),
        "github_linked": bool(github_username.strip()),
        "skills": skill_count > 0,
        "evidence": evidence_count > 0,
        "assessment": assessment_count > 0,
    }
    score = sum(CHECKLIST_WEIGHTS[k] for k, done in checklist.items() if done)
    return {"score": float(score), "checklist": checklist}