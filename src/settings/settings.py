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

    postgresql_uri: str
    logging_level: str = "info"
    logging_format: str = "standard"

    host: str = "0.0.0.0"
    port: int = 2201
    reload: bool = False
    workers: int = 1

    env: str = "prod"

    access_token_expire_minutes: int = 60

settings = Settings()
print(settings.postgresql_uri)
