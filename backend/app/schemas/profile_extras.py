from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str = ""
    start_year: int
    end_year: Optional[int] = None
    is_current: bool = False
    grade: str = ""

    @field_validator("start_year")
    @classmethod
    def start_year_reasonable(cls, v: int) -> int:
        if v < 1950 or v > 2100:
            raise ValueError("start_year must be a realistic year")
        return v


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