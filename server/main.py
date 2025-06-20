"""
Main FastAPI application entry point for PoseDetect backend server.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.core.background_tasks import BackgroundTaskManager
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Background task manager instance
task_manager = BackgroundTaskManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting PoseDetect API server...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start background task manager
    await task_manager.start()
    logger.info("Background task manager started")
    
    # Create upload and output directories
    settings = get_settings()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PoseDetect API server...")
    await task_manager.stop()
    logger.info("Background task manager stopped")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="PoseDetect API",
        description="Advanced pose detection and analysis API for videos and images",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Mount static files for serving outputs
    if Path(settings.OUTPUT_DIR).exists():
        app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "background_tasks": await task_manager.get_status()
        }
    
    return app


# Create the application instance
app = create_application()

def main() -> None:
    """Main entry point for the application."""
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main() 