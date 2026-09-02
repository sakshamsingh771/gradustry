from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class StudentRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    branch: str = ""
    year_of_study: int = 1
    career_goal: str = ""


class CollegeRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    college_name: str
    city: str = ""
    affiliation: str = ""


class IndustryRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    company_name: str
    industry_sector: str = ""
    website: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True
