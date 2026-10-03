from datetime import datetime, timezone

from app.database.student_repository import get_student
from app.database.scholarship_repository import get_scholarship
from app.services.eligibility_engine import evaluate_eligibility


def check_student_eligibility(student_id: str, scholarship_id: str):
    student = get_student(student_id)

    if student is None:
        return {
            "error": "Student not found"
        }

    scholarship = get_scholarship(scholarship_id)

    if scholarship is None:
        return {
            "error": "Scholarship not found"
        }

    result = evaluate_eligibility(
        student,
        scholarship
    )

    result["student_id"] = student_id
    result["scholarship_id"] = scholarship_id
    result["evaluated_at"] = datetime.now(timezone.utc).isoformat()

    return result