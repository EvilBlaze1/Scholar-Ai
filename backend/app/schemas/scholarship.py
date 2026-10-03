from pydantic import BaseModel, Field
from typing import Optional


class ScholarshipCreate(BaseModel):
    name: str = Field(..., min_length=2)
    provider: str
    description: Optional[str] = None
    source_url: Optional[str] = None

    application_start_date: Optional[str] = None
    application_deadline: Optional[str] = None
    academic_year: Optional[str] = None

    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None

    eligible_categories: list[str] = []
    eligible_states: list[str] = []
    eligible_education_levels: list[str] = []
    eligible_courses: list[str] = []
    eligible_genders: list[str] = []

    maximum_family_income: Optional[float] = None

    minimum_score: Optional[float] = None
    minimum_score_type: Optional[str] = None

    disability_required: Optional[bool] = None

    scholarship_amount: Optional[float] = None
    amount_type: Optional[str] = None
    benefits_description: Optional[str] = None

    required_documents: list[str] = []

    verification_status: Optional[str] = None
    last_verified_at: Optional[str] = None