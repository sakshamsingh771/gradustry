from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, StudentProfile
from app.models.profile_extras import Education, Project, Experience, Certification, Achievement
from app.schemas.profile_extras import (
    EducationCreate, EducationUpdate, EducationOut,
    ProjectCreate, ProjectUpdate, ProjectOut,
    ExperienceCreate, ExperienceUpdate, ExperienceOut,
    CertificationCreate, CertificationUpdate, CertificationOut,
    AchievementCreate, AchievementUpdate, AchievementOut,
)

router = APIRouter(prefix="/api/students", tags=["profile-extras"])


def _get_student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile

def _get_owned(db: Session, model, profile: StudentProfile, record_id: int, label: str):
    record = db.query(model).filter(model.id == record_id, model.student_id == profile.id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return record


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
    
# ==========================================================
# Projects
# ==========================================================

@router.get("/me/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    return db.query(Project).filter(Project.student_id == profile.id).order_by(Project.created_at.desc()).all()


@router.post("/me/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    if payload.end_date and payload.start_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    record = Project(student_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/me/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Project, profile, project_id, "Project")
    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_date", record.start_date)
    new_end = updates.get("end_date", record.end_date)
    if new_end and new_start and new_end < new_start:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    for field, value in updates.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Project, profile, project_id, "Project")
    db.delete(record)
    db.commit()


# ==========================================================
# Experience
# ==========================================================

@router.get("/me/experience", response_model=list[ExperienceOut])
def list_experience(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    return db.query(Experience).filter(Experience.student_id == profile.id).order_by(Experience.created_at.desc()).all()


@router.post("/me/experience", response_model=ExperienceOut, status_code=201)
def create_experience(payload: ExperienceCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    if payload.end_date and payload.start_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    record = Experience(student_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/me/experience/{experience_id}", response_model=ExperienceOut)
def update_experience(experience_id: int, payload: ExperienceUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Experience, profile, experience_id, "Experience")
    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_date", record.start_date)
    new_end = updates.get("end_date", record.end_date)
    if new_end and new_start and new_end < new_start:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    for field, value in updates.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/experience/{experience_id}", status_code=204)
def delete_experience(experience_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Experience, profile, experience_id, "Experience")
    db.delete(record)
    db.commit()


# ==========================================================
# Certifications
# ==========================================================

@router.get("/me/certifications", response_model=list[CertificationOut])
def list_certifications(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    return db.query(Certification).filter(Certification.student_id == profile.id).order_by(Certification.created_at.desc()).all()


@router.post("/me/certifications", response_model=CertificationOut, status_code=201)
def create_certification(payload: CertificationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = Certification(student_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/me/certifications/{certification_id}", response_model=CertificationOut)
def update_certification(certification_id: int, payload: CertificationUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Certification, profile, certification_id, "Certification")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/certifications/{certification_id}", status_code=204)
def delete_certification(certification_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Certification, profile, certification_id, "Certification")
    db.delete(record)
    db.commit()


# ==========================================================
# Achievements
# ==========================================================

@router.get("/me/achievements", response_model=list[AchievementOut])
def list_achievements(db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    return db.query(Achievement).filter(Achievement.student_id == profile.id).order_by(Achievement.created_at.desc()).all()


@router.post("/me/achievements", response_model=AchievementOut, status_code=201)
def create_achievement(payload: AchievementCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = Achievement(student_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/me/achievements/{achievement_id}", response_model=AchievementOut)
def update_achievement(achievement_id: int, payload: AchievementUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Achievement, profile, achievement_id, "Achievement")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/achievements/{achievement_id}", status_code=204)
def delete_achievement(achievement_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    profile = _get_student_profile(db, user)
    record = _get_owned(db, Achievement, profile, achievement_id, "Achievement")
    db.delete(record)
    db.commit()