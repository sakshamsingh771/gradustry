from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, StudentProfile, CollegeProfile, IndustryProfile, RoleEnum
from app.schemas.auth import StudentRegister, CollegeRegister, IndustryRegister, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _ensure_email_free(db: Session, email: str):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )


def _issue_token(user: User) -> TokenResponse:
    # Role string format me convert karein taaki JWT aur Pydantic easily read karein
    role_str = user.role.value if isinstance(user.role, RoleEnum) else str(user.role)
    
    token = create_access_token(subject=str(user.id), role=role_str)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=role_str,
        full_name=user.full_name,
        user_id=user.id
    )


@router.post("/register/student", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegister, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    _ensure_email_free(db, email)
    
    try:
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=RoleEnum.student.value,
            is_active=True
        )
        db.add(user)
        db.flush()  # Generates user.id for foreign key

        profile = StudentProfile(
            user_id=user.id,
            branch=payload.branch,
            year_of_study=payload.year_of_study,
            career_goal=payload.career_goal,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        return _issue_token(user)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register student account due to database error"
        )


@router.post("/register/college", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_college(payload: CollegeRegister, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    _ensure_email_free(db, email)

    try:
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=RoleEnum.college.value,
            is_active=True
        )
        db.add(user)
        db.flush()

        profile = CollegeProfile(
            user_id=user.id,
            college_name=payload.college_name,
            city=payload.city,
            affiliation=payload.affiliation,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        return _issue_token(user)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register college account"
        )


@router.post("/register/industry", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_industry(payload: IndustryRegister, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    _ensure_email_free(db, email)

    try:
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=RoleEnum.industry.value,
            is_active=True
        )
        db.add(user)
        db.flush()

        profile = IndustryProfile(
            user_id=user.id,
            company_name=payload.company_name,
            industry_sector=payload.industry_sector,
            website=payload.website,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        return _issue_token(user)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register industry account"
        )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()

    # Verify credentials
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account state
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    return _issue_token(user)