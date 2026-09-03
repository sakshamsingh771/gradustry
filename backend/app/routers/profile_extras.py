from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.profile_extras import Education
from app.schemas.profile_extras import EducationCreate, EducationUpdate, EducationOut

router = APIRouter(prefix="/api/students", tags=["profile-extras"])


def _get_student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def _get_owned_education(db: Session, profile: StudentProfile, education_id: int) -> Education:
    record = db.query(Education).filter(
        Education.id == education_id, Education.student_id == profile.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Education record not found")
    return record


@router.get("/me/education", response_model=list[EducationOut])
def list_education(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    return (
        db.query(Education)
        .filter(Education.student_id == profile.id)
        .order_by(Education.start_year.desc())
        .all()
    )


@router.post("/me/education", response_model=EducationOut, status_code=201)
def create_education(
    payload: EducationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    if payload.end_year is not None and payload.end_year < payload.start_year:
        raise HTTPException(status_code=422, detail="end_year cannot be before start_year")

    record = Education(student_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/me/education/{education_id}", response_model=EducationOut)
def update_education(
    education_id: int,
    payload: EducationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    record = _get_owned_education(db, profile, education_id)

    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_year", record.start_year)
    new_end = updates.get("end_year", record.end_year)
    if new_end is not None and new_end < new_start:
        raise HTTPException(status_code=422, detail="end_year cannot be before start_year")

    for field, value in updates.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/education/{education_id}", status_code=204)
def delete_education(
    education_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("student")),
):
    profile = _get_student_profile(db, user)
    record = _get_owned_education(db, profile, education_id)
    db.delete(record)
    db.commit()