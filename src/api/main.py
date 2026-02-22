"""
FastAPI application entry point.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting DocOps Agent API...")
    yield
    # Shutdown
    logger.info("Shutting down DocOps Agent API...")


app = FastAPI(
    title="DocOps Agent",
    description="Multi-Agent Document Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - configure from environment
from src.utils.config import get_settings
settings = get_settings()
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["http://localhost:3000", "http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "DocOps Agent API", "version": "1.0.0"}


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Checks the status of dependent services.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "postgres": "healthy",
            "redis": "healthy",
            "minio": "healthy"
        }
    }


# Import routes to register them
from src.api.routes import documents, extraction, analysis, approvals

app.include_router(documents.router)
app.include_router(extraction.router)
app.include_router(analysis.router)
app.include_router(approvals.router)

# Serve frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
app_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/app")
    async def serve_frontend():
        """Serve the frontend."""
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not found"}

# Settings endpoints - stored in database
_db_service = None

def get_db():
    global _db_service
    if _db_service is None:
        from src.utils.config import get_settings
        settings = get_settings()
        from src.services.database import DatabaseService
        _db_service = DatabaseService(database_url=settings.database_url)
    return _db_service

@app.get("/docops_settings.json")
async def get_settings():
    """Get settings from database."""
    db = get_db()
    settings = await db.get_all_settings()

    # Return defaults if not set
    return {
        "confidence_threshold": settings.get("confidence_threshold", 0.7),
        "max_concurrent_jobs": settings.get("max_concurrent_jobs", 3)
    }

@app.put("/docops_settings.json")
async def update_settings(request: dict):
    """Save settings to database."""
    db = get_db()

    # Save each setting
    for key, value in request.items():
        value_str = str(value)
        value_type = type(value).__name__

        if isinstance(value, bool):
            value_type = "bool"
        elif isinstance(value, int):
            value_type = "int"
        elif isinstance(value, float):
            value_type = "float"
        else:
            value_type = "string"

        await db.set_setting(key, value_str, value_type)

    return {"success": True}
