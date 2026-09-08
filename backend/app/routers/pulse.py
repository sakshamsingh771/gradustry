from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.skill import StudentSkill
from app.models.assessment import CareerRole
from app.models.pulse import PulseArticle, SavedPulseArticle

router = APIRouter(prefix="/api/pulse", tags=["pulse"])


def _student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _article_out(article: PulseArticle, saved_ids: set[int]) -> dict:
    return {
        "id": article.id, "title": article.title, "category": article.category,
        "summary": article.summary, "source": article.source, "source_url": article.source_url,
        "tags": article.tags_list(), "relevant_skills": article.skills_list(),
        "impact": article.impact, "published_at": article.published_at,
        "saved": article.id in saved_ids,
    }


@router.get("/articles")
def list_articles(
    category: str | None = Query(None),
    db: Session = Depends(get_db), user: User = Depends(require_roles("student")),
):
    q = db.query(PulseArticle)
    if category:
        q = q.filter(PulseArticle.category == category)
    articles = q.order_by(PulseArticle.published_at.desc()).limit(100).all()
    saved_ids = {s.article_id for s in db.query(SavedPulseArticle).filter(SavedPulseArticle.user_id == user.id).all()}
    return [_article_out(a, saved_ids) for a in articles]


@router.get("/for-you")
def personalized_feed(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _student_profile(db, user)

    tracked_skills = {
        ss.skill.name for ss in db.query(StudentSkill).filter(StudentSkill.student_id == profile.id).all() if ss.skill
    }

    target_role_skills: set[str] = set()
    role = None
    if profile.career_goal:
        role = db.query(CareerRole).filter(CareerRole.title == profile.career_goal).first()
        if role:
            target_role_skills = {r.skill.name for r in role.requirements if r.skill}

    relevant_pool = tracked_skills | target_role_skills
    articles = db.query(PulseArticle).order_by(PulseArticle.published_at.desc()).limit(100).all()
    saved_ids = {s.article_id for s in db.query(SavedPulseArticle).filter(SavedPulseArticle.user_id == user.id).all()}

    results = []
    for a in articles:
        article_skills = set(a.skills_list())
        matched = sorted(article_skills & relevant_pool)
        out = _article_out(a, saved_ids)
        if matched and role:
            out["why_it_matters"] = {
                "personalized": True, "target_role": role.title, "matched_skills": matched,
                "recommended_action": f"Review this update and consider how it affects your {role.title} skill set: {', '.join(matched)}.",
            }
        elif matched:
            out["why_it_matters"] = {
                "personalized": True, "target_role": None, "matched_skills": matched,
                "recommended_action": f"This touches skills you're already tracking: {', '.join(matched)}.",
            }
        else:
            out["why_it_matters"] = {
                "personalized": False,
                "recommended_action": "Set a career goal and track skills on your Skill Passport to get personalized relevance here.",
            }
        results.append(out)

    results.sort(key=lambda r: (not r["why_it_matters"]["personalized"], -r["published_at"].timestamp() if hasattr(r["published_at"], "timestamp") else 0))
    return results


@router.post("/articles/{article_id}/save")
def save_article(article_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    if not db.query(PulseArticle).filter(PulseArticle.id == article_id).first():
        raise HTTPException(status_code=404, detail="Article not found")
    if not db.query(SavedPulseArticle).filter(
        SavedPulseArticle.user_id == user.id, SavedPulseArticle.article_id == article_id
    ).first():
        db.add(SavedPulseArticle(user_id=user.id, article_id=article_id))
        db.commit()
    return {"detail": "Saved"}


@router.delete("/articles/{article_id}/save")
def unsave_article(article_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    row = db.query(SavedPulseArticle).filter(
        SavedPulseArticle.user_id == user.id, SavedPulseArticle.article_id == article_id
    ).first()
    if row:
        db.delete(row)
        db.commit()
    return {"detail": "Unsaved"}


@router.get("/saved")
def list_saved(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    rows = db.query(SavedPulseArticle).filter(SavedPulseArticle.user_id == user.id).order_by(
        SavedPulseArticle.saved_at.desc()
    ).all()
    saved_ids = {r.article_id for r in rows}
    return [_article_out(r.article, saved_ids) for r in rows if r.article]