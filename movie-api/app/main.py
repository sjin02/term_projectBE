from fastapi import FastAPI
from app.db.session import init_db

app = FastAPI(
    title="Movie API",
    version="0.1.0"
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "buildTime": "local"
    }
