from pydantic import BaseModel
from typing import Optional


class ScholarshipSearchResult(BaseModel):
    name: str
    provider: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None

    application_deadline: Optional[str] = None
    scholarship_amount: Optional[str] = None

    eligible_categories: list[str] = []
    eligible_genders: list[str] = []
    maximum_family_income: Optional[float] = None

    eligibility_status: str
    passed_rules: int
    failed_rules: int
    verification_required: bool


class PersonalizedSearchResponse(BaseModel):
    student_id: str
    queries: list[str]
    count: int
    results: list[ScholarshipSearchResult]