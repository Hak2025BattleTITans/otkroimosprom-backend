import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "prod"

    postgresql_uri: str
    logging_level: str = "info"
    logging_format: str = "standard"

    host: str = "0.0.0.0"
    port: int = 2201
    reload: bool = False
    workers: int = 1


    optimized_dir: str = "optimized"
    upload_dir: str = "uploads"
    max_file_size_bytes: int = 5 * 1024 * 1024 # 5 MB
    csv_content_types: list[str] = ["text/csv", "application/vnd.ms-excel"]

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 64 * 1024 # 64 MiB
    argon2_parallelism: int = 2

settings = Settings()

OPTIMIZED_DIR = Path(settings.optimized_dir).resolve()
OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = Path(settings.upload_dir).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

print(settings.postgresql_uri)
