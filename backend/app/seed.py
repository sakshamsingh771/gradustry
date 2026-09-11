"""
Seed the database with enough data to demo Gradustry end-to-end:
  - a Super Admin account
  - career roles + required skills (Skill Gap Engine input)
  - a demo college, a demo student (with evidence -> proficiency already computed)
  - a demo industry account with one opportunity

Run with:  python -m app.seed
"""
from datetime import datetime

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app import models  # noqa: F401
from app.models.user import User, StudentProfile, CollegeProfile, IndustryProfile, RoleEnum
from app.models.academician import AcademicianProfile
from app.models.skill import Skill, StudentSkill, Evidence, SkillScoreHistory
from app.models.assessment import CareerRole, RoleSkillRequirement
from app.models.opportunity import Opportunity, OpportunitySkill, Application
from app.ai import evidence_engine

SKILLS = {
    "Python": "Programming", "FastAPI": "Backend", "React": "Frontend", "SQL": "Database",
    "Docker": "DevOps", "AWS": "Cloud", "Git": "Tools", "JavaScript": "Programming",
    "System Design": "Engineering", "Communication": "Soft Skill",
        "Machine Learning": "AI/ML", "Deep Learning": "AI/ML",
}

ROLES = {
    "Backend Developer": [
        ("Python", 80, "core"), ("FastAPI", 75, "core"), ("SQL", 70, "core"),
        ("Docker", 65, "core"), ("Git", 60, "preferred"), ("AWS", 55, "preferred"),
    ],
    "Full Stack Developer": [
        ("Python", 70, "core"), ("React", 75, "core"), ("JavaScript", 70, "core"),
        ("SQL", 60, "preferred"), ("Docker", 55, "preferred"),
    ],
        "AI Engineer": [
        ("Python", 80, "core"), ("Machine Learning", 75, "core"),
        ("Deep Learning", 75, "core"), ("SQL", 55, "preferred"),
    ],
}


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@gradustry.dev").first():
            print("Seed data already present — skipping.")
            return

        # --- Skills ---
        skill_objs = {}
        for name, category in SKILLS.items():
            s = Skill(name=name, category=category)
            db.add(s)
            db.flush()
            skill_objs[name] = s

        # --- Career roles ---
        for role_title, reqs in ROLES.items():
            role = CareerRole(title=role_title, description=f"Industry-benchmarked requirements for {role_title}.")
            db.add(role)
            db.flush()
            for skill_name, target, importance in reqs:
                db.add(RoleSkillRequirement(
                    role_id=role.id, skill_id=skill_objs[skill_name].id,
                    target_proficiency=target, importance=importance,
                ))
                # --- Learning resources (Phase 13 — verified, never AI-invented) ---
        from app.models.skill import LearningResource
        resource_seed = [
            ("Deep Learning", "CNN", "Convolutional Neural Networks", "deeplearning.ai", "https://www.coursera.org/learn/convolutional-neural-networks", "intermediate", 600),
            ("Deep Learning", "PyTorch", "PyTorch fundamentals", "PyTorch.org", "https://pytorch.org/tutorials/beginner/basics/intro.html", "beginner", 180),
            ("Docker", "Dockerfile", "Docker for Beginners", "Docker Docs", "https://docs.docker.com/get-started/", "beginner", 90),
        ]
        for skill_name, topic, title, provider, url, diff, dur in resource_seed:
            if skill_name in skill_objs:
                db.add(LearningResource(
                    skill_id=skill_objs[skill_name].id, topic=topic, title=title,
                    provider=provider, url=url, difficulty=diff, duration_minutes=dur,
                ))

        # --- Super Admin ---
        admin = User(
            email="admin@gradustry.dev", hashed_password=hash_password("admin123"),
            full_name="Platform Admin", role=RoleEnum.admin,
        )
        db.add(admin)

        # --- Demo College ---
        college_user = User(
            email="college@gradustry.dev", hashed_password=hash_password("college123"),
            full_name="Dr. Anita Rao", role=RoleEnum.college,
        )
        db.add(college_user)
        db.flush()
        college = CollegeProfile(
            user_id=college_user.id, college_name="Rashtriya Institute of Technology",
            city="Pune", affiliation="AICTE", verified=True,
        )
        db.add(college)
        db.flush()

        # --- Demo Student (with pre-populated evidence so the demo isn't empty) ---
        student_user = User(
            email="student@gradustry.dev", hashed_password=hash_password("student123"),
            full_name="Aarav Sharma", role=RoleEnum.student,
        )
        db.add(student_user)
        db.flush()
        student = StudentProfile(
            user_id=student_user.id, college_id=college.id, branch="AI & Data Science",
            year_of_study=3, career_goal="Backend Developer",
            bio="Third-year AI & DS student building full-stack projects.",
            github_username="aarav-dev",
        )
        db.add(student)
        db.flush()

        from app.models.college_membership import CollegeMembership, MembershipStatus, VerificationMethod
        db.add(CollegeMembership(
            user_id=student_user.id, college_id=college.id,
            status=MembershipStatus.verified, verification_method=VerificationMethod.platform_admin,
        ))

        demo_evidence = {
            "Python": [("certificate", "verified", "NPTEL Python Programming"), ("github", "verified", "5 Python repos analyzed"), ("assessment", "verified", "Assessment score 86%")],
            "FastAPI": [("project", "verified", "Gradustry backend project"), ("assessment", "pending_review", "Assessment score 65%")],
            "SQL": [("certificate", "pending_review", "Coursera SQL for Data Science")],
            "Docker": [("github", "needs_review", "Dockerfile detected in one repo")],
            "React": [("project", "verified", "Portfolio site built in React")],
            "Git": [("github", "verified", "Consistent commit history")],
        }
        for skill_name, evs in demo_evidence.items():
            ss = StudentSkill(student_id=student.id, skill_id=skill_objs[skill_name].id)
            db.add(ss)
            db.flush()
            signals = []
            for ev_type, status, title in evs:
                override = 86.0 if "86%" in title else (65.0 if "65%" in title else None)
                signal = evidence_engine.score_single_evidence(ev_type, status, override_score=override)
                db.add(Evidence(
                    student_skill_id=ss.id, type=ev_type, title=title, status=status, signal_score=signal,
                ))
                signals.append(signal)
            result = evidence_engine.recompute_student_skill(
                [{"type": t, "status": s, "signal_score": sig} for (t, s, _), sig in zip(evs, signals)]
            )
            ss.proficiency_score = result["proficiency_score"]
            ss.confidence_level = result["confidence_level"]
            ss.last_assessed_at = datetime.utcnow()
            db.add(SkillScoreHistory(student_skill_id=ss.id, score=ss.proficiency_score, reason="seed data"))

        # --- Demo Industry + Opportunity ---
        industry_user = User(
            email="industry@gradustry.dev", hashed_password=hash_password("industry123"),
            full_name="Priya Menon", role=RoleEnum.industry,
        )
        db.add(industry_user)
        db.flush()
        industry = IndustryProfile(
            user_id=industry_user.id, company_name="Nimbus Cloud Systems",
            industry_sector="Software / Cloud", website="https://nimbuscloud.example.com", verified=True,
        )
        db.add(industry)
        db.flush()

        opp = Opportunity(
            industry_id=industry.id, title="Backend Developer Intern", role_type="internship",
            audience="student",
            description="Work on a FastAPI-based microservice handling real production traffic.",
            location="Remote", min_year_of_study=3, final_year_only=0, stipend_or_ctc="₹25,000/month",
        )
        db.add(opp)
        db.flush()
        for skill_name, min_p, weight in [("Python", 75, 1.5), ("FastAPI", 65, 1.5), ("SQL", 55, 1.0), ("Docker", 40, 0.8)]:
            db.add(OpportunitySkill(opportunity_id=opp.id, skill_id=skill_objs[skill_name].id, min_proficiency=min_p, weight=weight))

        # --- Demo Academician + academician-facing opportunity + membership ---
        academician_user = User(
            email="academician@gradustry.dev", hashed_password=hash_password("academician123"),
            full_name="Dr. Meera Nair", role=RoleEnum.academician,
        )
        db.add(academician_user)
        db.flush()
        academician = AcademicianProfile(
            user_id=academician_user.id, college_id=college.id,
            designation="Associate Professor", institution=college.college_name,
            department="Computer Science & Engineering",
            area_of_expertise="Machine Learning, Distributed Systems",
            experience_years=9,
            bio="Researches applied ML and mentors final-year capstone projects.",
            verified=True,
        )
        db.add(academician)
        db.flush()

        db.add(CollegeMembership(
            user_id=academician_user.id, college_id=college.id,
            status=MembershipStatus.verified, verification_method=VerificationMethod.platform_admin,
        ))

        faculty_opp = Opportunity(
            industry_id=industry.id, title="Industry-Academia Research Collaboration on Cloud ML Pipelines",
            role_type="research_collaboration", audience="academician",
            description="Joint research engagement between faculty and our applied ML team on "
                        "cost-efficient cloud-native training pipelines. Demo/seed data — not a real posting.",
            location="Hybrid", stipend_or_ctc="Sponsored research grant",
        )
        db.add(faculty_opp)
        db.flush()

        db.add(Application(
            opportunity_id=faculty_opp.id, academician_id=academician.id, status="applied",
        ))

        from app.models.community import Community, CommunityType
        for name, description in [
            ("AI & Machine Learning", "Discuss ML models, papers, and projects."),
            ("Web Development", "Frontend, backend, and full-stack discussions."),
            ("DSA", "Data structures, algorithms, and interview prep."),
            ("Cybersecurity", "Security research, CTFs, and best practices."),
            ("Open Source", "Find projects to contribute to and share your own."),
        ]:
            if not db.query(Community).filter(Community.type == CommunityType.interest, Community.name == name).first():
                db.add(Community(name=name, type=CommunityType.interest, description=description))

        from app.models.pulse import PulseArticle
        for title, category, summary, skills, impact in [
            ("FastAPI releases a major version with native background workers", "Web Development",
             "The update simplifies async task handling without a separate queue for many use cases.", "Python,FastAPI,Backend Development", "high"),
            ("React introduces a new compiler-driven optimization mode", "Web Development",
             "Reduces the need for manual memoization in most component trees.", "React,JavaScript,TypeScript", "medium"),
            ("A widely-used open-source Docker base image patches a critical CVE", "Cybersecurity",
             "Teams should rebuild and redeploy images built on the affected base.", "Docker,DevOps,Cloud & DevOps", "high"),
            ("PostgreSQL 17 improves query planning for large joins", "Data Science",
             "Notably faster on analytical workloads with multiple joined tables.", "SQL,PostgreSQL,Data Science", "medium"),
            ("A major cloud provider cuts GPU inference pricing", "AI & Machine Learning",
             "Makes running small-to-mid sized open models in production notably cheaper.", "Machine Learning,Python,Cloud & DevOps", "medium"),
        ]:
            if not db.query(PulseArticle).filter(PulseArticle.title == title).first():
                db.add(PulseArticle(title=title, category=category, summary=summary, source="Gradustry Pulse Desk", tags=category, relevant_skills=skills, impact=impact))

        db.commit()
        print("Seed complete.")
        print("Login credentials:")
        print("  Admin:    admin@gradustry.dev / admin123")
        print("  College:  college@gradustry.dev / college123")
        print("  Student:  student@gradustry.dev / student123")
        print("  Industry: industry@gradustry.dev / industry123")
        print("  Academician: academician@gradustry.dev / academician123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
