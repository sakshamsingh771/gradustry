from typing import Optional
from pydantic import BaseModel


class AcademicianProfileOut(BaseModel):
    full_name: str
    email: str
    designation: str
    institution: str
    department: str
    area_of_expertise: str
    experience_years: int
    bio: str
    verified: bool
    college_id: Optional[int] = None
    college_name: Optional[str] = None

    class Config:
        from_attributes = True


class AcademicianProfileUpdate(BaseModel):
    designation: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    area_of_expertise: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None


class AcademicianDashboardOut(BaseModel):
    full_name: str
    institution: str
    designation: str
    profile_complete: bool
    college_membership_status: Optional[str] = None
    college_name: Optional[str] = None
    total_students_visible: int
    applications_total: int
    applications_by_status: dict[str, int]
    open_opportunities: int
