from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import api_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "status": "ok",
        "env": settings.app_env,
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
