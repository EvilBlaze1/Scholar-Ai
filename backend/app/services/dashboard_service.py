
from datetime import date, datetime
import re

from app.database.student_repository import get_student_by_user_id
from app.database.saved_scholarship_repository import get_saved_scholarships
from app.database.application_repository import get_user_applications
from app.services.matching_service import find_matching_scholarships


def _parse_deadline(value):
    """Parse common date formats without guessing missing deadlines."""
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()
    cleaned = re.sub(r'(\d+)(?:st|nd|rd|th)\b', r'\1', value, flags=re.IGNORECASE)

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    return None


def _upcoming_deadlines(matches, saved_scholarships=None, limit=5):
    """Return scholarships with parseable, future application deadlines."""
    today = date.today()
    candidates = list(matches or [])

    if saved_scholarships:
        for saved in saved_scholarships:
            snap = saved.get("scholarship")
            if isinstance(snap, dict):
                candidates.append({
                    "scholarship_id": saved.get("scholarship_id") or snap.get("id"),
                    "name": snap.get("name") or snap.get("title"),
                    "application_deadline": snap.get("application_deadline") or snap.get("deadline"),
                    "status": snap.get("status") or snap.get("eligibility_status"),
                    "source_url": snap.get("source_url"),
                })

    seen = set()
    upcoming = []

    for item in candidates:
        deadline_str = item.get("application_deadline") or item.get("deadline")
        deadline = _parse_deadline(deadline_str)

        if deadline is None or deadline < today:
            continue

        item_id = item.get("scholarship_id") or item.get("id") or item.get("name")
        if item_id in seen:
            continue
        seen.add(item_id)

        upcoming.append({
            "scholarship_id": item.get("scholarship_id") or item.get("id"),
            "name": item.get("name") or item.get("title"),
            "application_deadline": deadline_str,
            "status": item.get("status"),
            "source_url": item.get("source_url"),
        })

    upcoming.sort(
        key=lambda item: _parse_deadline(item["application_deadline"]) or today
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
        "upcoming_deadlines": _upcoming_deadlines(matches, saved_scholarships),
    }
