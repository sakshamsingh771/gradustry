from app.models.user import User, StudentProfile, CollegeProfile, IndustryProfile, RoleEnum  # noqa
from app.models.skill import Skill, StudentSkill, SkillScoreHistory, Evidence  # noqa
from app.models.profile_extras import Education 
from app.models.assessment import (  # noqa
    Question,
    AssessmentAttempt,
    CareerRole,
    RoleSkillRequirement,
    RoadmapStep,
)
from app.models.opportunity import (  # noqa
    Opportunity,
    OpportunitySkill,
    Application,
    IndustryFeedback,
)
from app.models.ai import (  # noqa
    ResumeAnalysis,
    GitHubAnalysis,
    AdaptiveAssessmentSession,
    AIConversation,
)
