from pydantic import BaseModel, Field
from typing import Optional


class ScholarshipCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    provider: str = Field(..., min_length=2, max_length=200)

    description: Optional[str] = None
    source_url: Optional[str] = None

    application_start_date: Optional[str] = None
    application_deadline: Optional[str] = None
    academic_year: Optional[str] = None

    minimum_age: Optional[int] = Field(
        default=None,
        ge=0
    )

    maximum_age: Optional[int] = Field(
        default=None,
        ge=0
    )

    eligible_categories: list[str] = []
    eligible_states: list[str] = []
    eligible_education_levels: list[str] = []
    eligible_courses: list[str] = []
    eligible_genders: list[str] = []

    maximum_family_income: Optional[float] = Field(
        default=None,
        ge=0
    )

    minimum_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    minimum_score_type: Optional[str] = None

    disability_required: Optional[bool] = None

    scholarship_amount: Optional[float] = Field(
        default=None,
        ge=0
    )

    amount_type: Optional[str] = None
    benefits_description: Optional[str] = None

    required_documents: list[str] = []

    verification_status: Optional[str] = None
    last_verified_at: Optional[str] = None