
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.student import router as student_router
from app.api.scholarship import router as scholarship_router
from app.api.eligibility import router as eligibility_router
from app.api.matching import router as matching_router
from app.api.explanation import router as explanation_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from app.api.saved_scholarship import router as saved_scholarship_router
from app.api.application import router as application_router
from app.api.search import router as search_router
from app.api.personalized_search import router as personalized_search_router
from app.api.scholarship_discovery import router as discovery_router

app = FastAPI(title="Scholar AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://scholar-ai-ebon.vercel.app",
        "https://scholar-ai-git-master-evilblaze1.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router)
app.include_router(scholarship_router)
app.include_router(eligibility_router)
app.include_router(matching_router)
app.include_router(explanation_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(saved_scholarship_router)
app.include_router(application_router)
app.include_router(search_router)
app.include_router(personalized_search_router)
app.include_router(discovery_router)


@app.get("/")
def root():
    return {"message": "Scholar AI API is running"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Scholar AI API",
    }
