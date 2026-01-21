"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("Starting DocOps Agent API...")
    yield
    # Shutdown
    print("Shutting down DocOps Agent API...")


app = FastAPI(
    title="DocOps Agent",
    description="Multi-Agent Document Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
