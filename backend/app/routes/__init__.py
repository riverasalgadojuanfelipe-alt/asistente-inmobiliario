from fastapi import APIRouter

from app.routes.properties import router as properties_router

api_router = APIRouter()
api_router.include_router(properties_router)

__all__ = ["api_router"]
