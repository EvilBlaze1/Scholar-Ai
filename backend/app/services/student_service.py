from app.database.student_repository import (
    create_student,
    get_student,
    get_student_by_user_id,
    update_student,
)


def register_student(student_data: dict):
    return create_student(student_data)


def fetch_student(student_id: str):
    return get_student(student_id)


def fetch_student_by_user_id(user_id: str):
    return get_student_by_user_id(user_id)


def modify_student(
    student_id: str,
    student_data: dict
):
    return update_student(
        student_id,
        student_data
    )