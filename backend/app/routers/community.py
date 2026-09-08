from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles, get_current_user
from app.models.user import User, StudentProfile
from app.models.community import Community, CommunityType, CommunityMembership, CommunityPost, CommunityComment
from app.models.college_membership import CollegeMembership, MembershipStatus

router = APIRouter(prefix="/api/communities", tags=["communities"])


def _is_member(db: Session, user_id: int, community_id: int) -> bool:
    return db.query(CommunityMembership).filter(
        CommunityMembership.user_id == user_id, CommunityMembership.community_id == community_id
    ).first() is not None


def _assert_can_access(db: Session, user: User, community: Community) -> None:
    if community.type == CommunityType.interest:
        return
    verified = db.query(CollegeMembership).filter(
        CollegeMembership.user_id == user.id,
        CollegeMembership.college_id == community.college_id,
        CollegeMembership.status == MembershipStatus.verified,
    ).first()
    if not verified:
        raise HTTPException(status_code=403, detail="You must be a verified member of this college to access its community")


@router.get("/interest")
def list_interest_communities(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    rows = db.query(Community).filter(Community.type == CommunityType.interest).all()
    return [
        {
            "id": c.id, "name": c.name, "description": c.description,
            "member_count": db.query(CommunityMembership).filter(CommunityMembership.community_id == c.id).count(),
            "is_member": _is_member(db, user.id, c.id),
        }
        for c in rows
    ]


@router.get("/college/mine")
def my_college_community(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile or not profile.college_id:
        return None
    verified = db.query(CollegeMembership).filter(
        CollegeMembership.user_id == user.id,
        CollegeMembership.college_id == profile.college_id,
        CollegeMembership.status == MembershipStatus.verified,
    ).first()
    if not verified:
        return {"verified": False}
    community = db.query(Community).filter(
        Community.type == CommunityType.college, Community.college_id == profile.college_id
    ).first()
    if not community:
        from app.models.user import CollegeProfile
        college = db.query(CollegeProfile).filter(CollegeProfile.id == profile.college_id).first()
        if not college:
            raise HTTPException(status_code=404, detail="College not found")
        community = Community(
            name=f"{college.college_name} Community", type=CommunityType.college,
            college_id=profile.college_id, description=f"Private community for verified {college.college_name} students.",
        )
        db.add(community)
        db.commit()
        db.refresh(community)
    return {"verified": True, "community": {"id": community.id, "name": community.name, "description": community.description}}


@router.post("/{community_id}/join")
def join_community(community_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    if community.type == CommunityType.college:
        raise HTTPException(status_code=400, detail="College communities are joined automatically once your college membership is verified — not via this endpoint")
    if not _is_member(db, user.id, community_id):
        db.add(CommunityMembership(user_id=user.id, community_id=community_id))
        db.commit()
    return {"detail": f"Joined {community.name}"}


@router.get("/{community_id}/posts")
def list_posts(community_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    _assert_can_access(db, user, community)
    posts = db.query(CommunityPost).filter(CommunityPost.community_id == community_id).order_by(
        CommunityPost.created_at.desc()
    ).all()
    return [
        {
            "id": p.id, "content": p.content, "created_at": p.created_at,
            "author_name": p.author.full_name if p.author else "Unknown",
            "comment_count": db.query(CommunityComment).filter(CommunityComment.post_id == p.id).count(),
        }
        for p in posts
    ]


@router.post("/{community_id}/posts", status_code=201)
def create_post(community_id: int, content: str, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    _assert_can_access(db, user, community)
    if not content.strip():
        raise HTTPException(status_code=422, detail="Post content cannot be empty")

    if community.type == CommunityType.interest and not _is_member(db, user.id, community_id):
        db.add(CommunityMembership(user_id=user.id, community_id=community_id))

    post = CommunityPost(community_id=community_id, author_user_id=user.id, content=content.strip())
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"id": post.id, "content": post.content, "created_at": post.created_at, "author_name": user.full_name}


@router.get("/posts/{post_id}/comments")
def list_comments(post_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    _assert_can_access(db, user, post.community)
    comments = db.query(CommunityComment).filter(CommunityComment.post_id == post_id).order_by(CommunityComment.created_at).all()
    return [
        {"id": c.id, "content": c.content, "created_at": c.created_at, "author_name": c.author.full_name if c.author else "Unknown"}
        for c in comments
    ]


@router.post("/posts/{post_id}/comments", status_code=201)
def create_comment(post_id: int, content: str, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    _assert_can_access(db, user, post.community)
    if not content.strip():
        raise HTTPException(status_code=422, detail="Comment content cannot be empty")
    comment = CommunityComment(post_id=post_id, author_user_id=user.id, content=content.strip())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "content": comment.content, "created_at": comment.created_at, "author_name": user.full_name}