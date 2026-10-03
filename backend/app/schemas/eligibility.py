from pydantic import BaseModel
from typing import Optional


class RuleResult(BaseModel):
    rule_id: str
    rule_type: str
    status: str

    actual_value: Optional[str] = None
    required_value: Optional[str] = None

    reason: str


class EligibilityResult(BaseModel):
    scholarship_id: str
    student_id: str

    status: str

    evaluated_at: str

    rule_results: list[RuleResult]

    passed_rules: int
    failed_rules: int
    verification_required: bool