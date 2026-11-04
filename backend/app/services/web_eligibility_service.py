from app.services.eligibility_engine import evaluate_eligibility
from app.services.web_scholarship_converter import (
    convert_web_scholarship_to_schema,
)


def evaluate_web_scholarship(
    student: dict,
    scholarship_data: dict,
) -> dict:
    """
    Evaluate a discovered scholarship conservatively.

    Official sources (government portals, verified foundations) can be
    marked ELIGIBLE if all rules pass. Unverified third-party sources
    retain NEEDS_VERIFICATION status.
    """
    if not isinstance(student, dict):
        raise ValueError("Student data must be a dictionary.")

    if not isinstance(scholarship_data, dict):
        raise ValueError("Scholarship data must be a dictionary.")

    # Convert raw extracted information unless it already has the
    # fields expected by the eligibility engine.
    if (
        "eligible_categories" in scholarship_data
        and "source_url" in scholarship_data
    ):
        scholarship = scholarship_data
    else:
        scholarship = convert_web_scholarship_to_schema(
            scholarship_data
        )

    result = evaluate_eligibility(student, scholarship)

    if not isinstance(result, dict):
        raise ValueError("Eligibility engine returned an invalid result.")

    failed_rules = result.get("failed_rules", 0)
    verification_status = str(
        scholarship.get("verification_status") or "UNVERIFIED"
    ).upper()

    # Trusted official platforms (e.g. scholarships.gov.in, UGC, AICTE)
    is_official_or_verified = verification_status in ("VERIFIED", "OFFICIAL")
    verification_required = not is_official_or_verified

    if verification_required:
        if isinstance(failed_rules, (int, float)) and failed_rules > 0:
            result["status"] = "INELIGIBLE"
        else:
            result["status"] = "NEEDS_VERIFICATION"

    result["verification_required"] = verification_required
    result["verification_status"] = verification_status

    return {
        "scholarship": scholarship,
        "eligibility": result,
    }
