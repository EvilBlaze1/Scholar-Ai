from app.database.student_repository import create_student, get_student
from app.database.student_repository import create_student
def register_student(student_data: dict):
    return create_student(student_data)

def fetch_student(student_id: str):
    return get_student(student_id)