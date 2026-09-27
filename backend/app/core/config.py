from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Asistente Inmobiliario"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
