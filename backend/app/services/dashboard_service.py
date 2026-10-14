
from datetime import date, datetime

from app.database.student_repository import get_student_by_user_id
from app.database.saved_scholarship_repository import get_saved_scholarships
from app.database.application_repository import get_user_applications
from app.services.matching_service import find_matching_scholarships


def _parse_deadline(value):
    """Parse common date formats without guessing missing deadlines."""
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _upcoming_deadlines(matches, limit=5):
    """Return scholarships with parseable, future application deadlines."""
    today = date.today()
    upcoming = []

    for match in matches:
        deadline = _parse_deadline(match.get("application_deadline"))

        if deadline is None or deadline < today:
            continue

        upcoming.append({
            "scholarship_id": match.get("scholarship_id"),
            "name": match.get("name"),
            "application_deadline": match.get("application_deadline"),
            "status": match.get("status"),
            "source_url": match.get("source_url"),
        })

    upcoming.sort(
        key=lambda item: _parse_deadline(item["application_deadline"])
    )

    return upcoming[:limit]


def get_user_dashboard(user_id: str):
    """Build the student dashboard from existing application services."""
    student = get_student_by_user_id(user_id)

    if student is None:
        return None

    student_id = student.get("id")

    if not student_id:
        return None

    matches = find_matching_scholarships(student_id) or []
    saved_scholarships = get_saved_scholarships(user_id) or []
    applications = get_user_applications(user_id) or []

    eligible_count = sum(
        1 for match in matches
        if match.get("status") == "ELIGIBLE"
    )

    verification_count = sum(
        1 for match in matches
        if match.get("status") == "NEEDS_VERIFICATION"
    )

    ineligible_count = sum(
        1 for match in matches
        if match.get("status") == "INELIGIBLE"
    )

    summary = {
        "total_scholarships": len(matches),
        "eligible_scholarships": eligible_count,
        "needs_verification": verification_count,
        "ineligible_scholarships": ineligible_count,
        "saved_scholarships": len(saved_scholarships),
        "applications": len(applications),
    }

    return {
        "student": student,
        "summary": summary,
        "matches": matches,
        "saved_scholarships": saved_scholarships,
        "applications": applications,
        "upcoming_deadlines": _upcoming_deadlines(matches),
    }
