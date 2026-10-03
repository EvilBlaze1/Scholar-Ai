from fastapi import FastAPI

from app.api.student import router as student_router
from app.api.scholarship import router as scholarship_router
from app.api.eligibility import router as eligibility_router


app = FastAPI(title="Scholar AI API")


app.include_router(student_router)
app.include_router(scholarship_router)
app.include_router(eligibility_router)


@app.get("/")
def root():
    return {
        "message": "Scholar AI API is running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Scholar AI API"
    }