from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from app.schemas import StudentCreate

from app.core.security import (
    decode_access_token,
)

from app.core.search_cache import invalidate_cache

from app.services.student_service import (
    register_student,
    fetch_student,
    fetch_student_by_user_id,
    modify_student,
)


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user_id


@router.post("/me")
def create_my_student_profile(
    student: StudentCreate,
    user_id: str = Depends(get_current_user_id)
):

    existing_student = fetch_student_by_user_id(user_id)

    if existing_student:
        raise HTTPException(
            status_code=409,
            detail="Student profile already exists"
        )

    student_data = student.model_dump()

    student_data["user_id"] = user_id

    created = register_student(student_data)
    invalidate_cache("student_search")
    return created


@router.get("/me")
def get_my_student_profile(
    user_id: str = Depends(get_current_user_id)
):

    student = fetch_student_by_user_id(user_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found"
        )

    return student


@router.get("/{student_id}")
def get_student(student_id: str):

    student = fetch_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


@router.put("/{student_id}")
def update_student(
    student_id: str,
    student: StudentCreate
):

    updated_student = modify_student(
        student_id,
        student.model_dump()
    )

    if updated_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    invalidate_cache("student_search")
    return updated_student
