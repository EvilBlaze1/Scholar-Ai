from fastapi import FastAPI

app = FastAPI(title="Scholar AI API")


@app.get("/")
def root():
    return {
        "message": "Scholar AI API is running"
    }