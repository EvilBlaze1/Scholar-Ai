from fastapi import APIRouter

from app.schemas import StudentCreate
from app.services.student_service import register_student, fetch_student


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


@router.post("/")
def create_student(student: StudentCreate):
    student_data = student.model_dump()

    return register_student(student_data)

@router.get("/{student_id}")
def get_student(student_id: str):
    student = fetch_student(student_id)

    if student is None:
        return {
            "message": "Student not found"
        }

    return student