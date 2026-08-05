from app.core.config import settings
from fastapi import FastAPI
from app.db.init_db import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {
        "project": "ARES",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }