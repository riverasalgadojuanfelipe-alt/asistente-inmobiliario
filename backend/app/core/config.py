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

    ciudades_soportadas: tuple[str, ...] = ("cali", "medellin", "bogota", "tulua")


@lru_cache
def get_settings() -> Settings:
    return Settings()
