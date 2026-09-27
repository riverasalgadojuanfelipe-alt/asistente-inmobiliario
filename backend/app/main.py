import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.routes import api_router

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,  # forzado a False en prod por Settings
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Estás enviando búsquedas muy seguido. Por favor espera un "
                "momento antes de intentar de nuevo (límite: 10 búsquedas por "
                "minuto)."
            )
        },
        headers={"Retry-After": "60"},
    )


# ---------------------------------------------------------------------------
# 500 sin traceback (aunque debug=True, este handler es cinturón + tirantes)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Logueamos completo para poder debuggear en Render logs; al cliente
    # SOLO le devolvemos un mensaje genérico. Nunca fugamos internals.
    logger.exception("Excepción no controlada en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Vuelve a intentar en un momento."},
    )


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade headers de seguridad básicos a todas las respuestas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # HSTS 2 años, subdominios. En HTTP los navegadores lo ignoran
        # (spec), así que es seguro emitirlo también en dev.
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        # Bonus barato: no filtrar URLs completas al navegar cross-origin.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# CORS (sin cambios — controlado desde Settings.cors_origins)
# ---------------------------------------------------------------------------
_cors_origins = settings.cors_origins_list
_allow_wildcard = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _allow_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
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
