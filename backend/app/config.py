from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Jordan Tourism AI-GIS"
    debug: bool = True

    # Database
    database_url: str = "postgresql://tourism:tourism@localhost:5433/tourism_gis"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ETL
    etl_upload_dir: str = "/tmp/tourism_uploads"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
