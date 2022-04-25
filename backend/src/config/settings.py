from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    upload_folder = "files"
    projects_folder = "projects"
    base_url = "/api"
    log_level = "DEBUG"

    db_user = "postgres"
    db_pw = "password"
    db_url = "localhost"
    db_database = "postgres"
    db_port = "5432"

    redis_url = "localhost"
    redis_port = 6379

    DATA_PER_SECOND = 700000
    MAX_SAMPLES = 500000
    MAX_DATA_POINTS = 25000000
    INTEGRATION_PROGRESS_CHANNEL = "integration-progress"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
