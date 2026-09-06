from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ---------- Education ----------

class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str = ""
    start_year: int
    end_year: Optional[int] = None
    is_current: bool = False
    grade: str = ""


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    is_current: Optional[bool] = None
    grade: Optional[str] = None


class EducationOut(EducationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Project ----------

class ProjectBase(BaseModel):
    title: str
    description: str = ""
    technologies: str = ""
    github_url: str = ""
    live_url: str = ""
    role: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: Optional[bool] = None


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Experience ----------

class ExperienceBase(BaseModel):
    organization: str
    role: str
    description: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    skills_used: str = ""


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    organization: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    skills_used: Optional[str] = None


class ExperienceOut(ExperienceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Certification ----------

class CertificationBase(BaseModel):
    name: str
    issuer: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: str = ""
    credential_url: str = ""
    proof_url: str = ""


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    proof_url: Optional[str] = None


class CertificationOut(CertificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Achievement ----------

class AchievementBase(BaseModel):
    title: str
    organization: str = ""
    date: Optional[date] = None
    description: str = ""
    proof_url: str = ""


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None
    proof_url: Optional[str] = None


class AchievementOut(AchievementBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True