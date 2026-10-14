
from app.database.student_repository import get_student
from app.database.scholarship_repository import get_all_scholarships
from app.services.eligibility_engine import evaluate_eligibility


STATUS_PRIORITY = {
    "ELIGIBLE": 3,
    "NEEDS_VERIFICATION": 2,
    "INELIGIBLE": 1,
}


def calculate_match_score(result: dict) -> float:
    """
    Calculate a rule-match percentage.

    This is a heuristic, not a probability of receiving a scholarship.
    Unknown rules are excluded when the engine explicitly identifies them.
    """
    if not isinstance(result, dict):
        return 0.0

    rule_results = result.get("rule_results") or []

    if not isinstance(rule_results, list) or not rule_results:
        return 0.0

    passed_rules = result.get("passed_rules", 0)
    failed_rules = result.get("failed_rules", 0)

    if not isinstance(passed_rules, (int, float)):
        return 0.0

    if not isinstance(failed_rules, (int, float)):
        return 0.0

    evaluated_rules = passed_rules + failed_rules

    if evaluated_rules <= 0:
        return 0.0

    return round((passed_rules / evaluated_rules) * 100, 2)


def _build_match(scholarship: dict, result: dict) -> dict:
    """Build the stable response format used by existing callers."""
    status = result.get("status", "NEEDS_VERIFICATION")

    return {
        "scholarship_id": scholarship.get("id"),
        "name": scholarship.get("name"),
        "provider": scholarship.get("provider"),
        "description": scholarship.get("description"),
        "scholarship_amount": scholarship.get("scholarship_amount"),
        "application_deadline": scholarship.get("application_deadline"),
        "source_url": scholarship.get("source_url"),
        "status": status,
        "match_score": calculate_match_score(result),
        "passed_rules": result.get("passed_rules", 0),
        "failed_rules": result.get("failed_rules", 0),
        "verification_required": result.get(
            "verification_required",
            status == "NEEDS_VERIFICATION",
        ),
    }


def find_matching_scholarships(student_id: str):
    """Evaluate and rank stored scholarships for a student."""
    student = get_student(student_id)

    if student is None:
        return None

    scholarships = get_all_scholarships() or []
    matches = []

    for scholarship in scholarships:
        if not isinstance(scholarship, dict):
            continue

        result = evaluate_eligibility(student, scholarship)

        if not isinstance(result, dict):
            continue

        matches.append(_build_match(scholarship, result))

    matches.sort(
        key=lambda item: (
            STATUS_PRIORITY.get(item["status"], 0),
            item["match_score"],
            item["name"] or "",
        ),
        reverse=True,
    )

    return matches
