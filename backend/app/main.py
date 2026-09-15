from app.core.config import settings
from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.ticket import router as ticket_router
from app.api.rescue_team import router as rescue_team_router
from app.api.vehicle import router as vehicle_router
from app.api.missions import router as mission_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(ticket_router)
app.include_router(rescue_team_router)
app.include_router(vehicle_router)
app.include_router(mission_router)

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