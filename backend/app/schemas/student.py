from pydantic import BaseModel, Field
from typing import Optional


class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    state: Optional[str] = None

    education_level: Optional[str] = None
    course: Optional[str] = None
    specialization: Optional[str] = None
    college: Optional[str] = None
    academic_year: Optional[str] = None

    score: Optional[float] = None
    score_type: Optional[str] = None

    annual_family_income: Optional[float] = None

    category: Optional[str] = None
    domicile_state: Optional[str] = None
    disability_status: Optional[bool] = None