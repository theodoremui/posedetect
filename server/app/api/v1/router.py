from fastapi import APIRouter
from app.api.v1.endpoints import files, processing, stats

api_router = APIRouter()

api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(processing.router, prefix="/processing", tags=["processing"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"]) 