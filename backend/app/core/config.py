from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Homev"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True

    database_url: str

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-lite-latest"

    # CORS: lista separada por comas, o "*" para todos.
    # En producción, apuntar al dominio del frontend (ej. https://xxx.vercel.app).
    cors_origins: str = "*"

    ciudades_soportadas: tuple[str, ...] = ("cali", "medellin", "bogota", "tulua")

    @property
    def cors_origins_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @model_validator(mode="after")
    def _force_debug_off_in_prod(self) -> "Settings":
        # En producción NUNCA exponemos debug/tracebacks, sin importar lo que
        # diga el .env o la variable de entorno.
        if self.is_production:
            self.debug = False
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
