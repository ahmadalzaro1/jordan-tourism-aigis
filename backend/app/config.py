from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "Jordan Tourism AI-GIS"
    debug: bool = True
    data_mode: Literal["official", "demo"] = "official"

    # Database
    database_url: str = "postgresql://tourism:tourism@localhost:5433/tourism_gis"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ETL
    etl_upload_dir: str = "/tmp/tourism_uploads"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings():
    return Settings()
