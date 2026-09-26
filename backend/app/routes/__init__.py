from fastapi import APIRouter

from app.routes.properties import router as properties_router
from app.routes.search import router as search_router

api_router = APIRouter()
api_router.include_router(properties_router)
api_router.include_router(search_router)

__all__ = ["api_router"]
