
from app.database.student_repository import get_student
from app.database.scholarship_repository import get_scholarship
from app.services.eligibility_engine import evaluate_eligibility


def _build_explanation(result: dict) -> dict:
    """Build an explanation using the eligibility engine's actual results."""

    status = str(
        result.get("status") or "NEEDS_VERIFICATION"
    ).upper()

    rule_results = result.get("rule_results") or []

    passed = []
    failed = []
    unknown = []

    for rule in rule_results:
        if not isinstance(rule, dict):
            continue

        rule_status = str(rule.get("status") or "UNKNOWN").upper()

        item = {
            "rule_id": rule.get("rule_id"),
            "status": rule_status,
            "reason": rule.get("reason") or "No explanation is available.",
        }

        if rule_status == "PASS":
            passed.append(item)
        elif rule_status == "FAIL":
            failed.append(item)
        else:
            unknown.append(item)

    verification_required = bool(
        result.get("verification_required", False)
        or status == "NEEDS_VERIFICATION"
    )

    next_steps = []

    if failed:
        next_steps.append(
            "Review the failed eligibility requirements. "
            "You may not qualify unless the scholarship rules or your "
            "information have been interpreted incorrectly."
        )

    if unknown:
        next_steps.append(
            "Complete or confirm the missing student information and "
            "check the corresponding scholarship requirements."
        )

    if verification_required:
        next_steps.append(
            "Open the official scholarship website and confirm the "
            "eligibility conditions, benefits, application process, "
            "and deadline."
        )

    if not failed and not unknown and not verification_required:
        next_steps.append(
            "Review the official scholarship conditions and prepare "
            "the required documents before applying."
        )

    return {
        "status": status,
        "passed_rules": passed,
        "failed_rules": failed,
        "unknown_rules": unknown,
        "verification_required": verification_required,
        "next_steps": next_steps,
    }


def get_scholarship_explanation(
    student_id: str,
    scholarship_id: str,
):
    """Return scholarship details, eligibility results, and explanations."""

    student = get_student(student_id)

    if student is None:
        return {"error": "Student not found"}

    scholarship = get_scholarship(scholarship_id)

    if scholarship is None:
        return {"error": "Scholarship not found"}

    result = evaluate_eligibility(student, scholarship)

    if not isinstance(result, dict):
        return {"error": "Could not evaluate scholarship eligibility"}

    return {
        "scholarship": scholarship,
        "eligibility": result,
        "explanation": _build_explanation(result),
    }
