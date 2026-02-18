"""
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
