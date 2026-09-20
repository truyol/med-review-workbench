from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./var/medreview.db"
    storage_root: Path = Path("./var/uploads")
    preview_root: Path = Path("./var/previews")
    max_upload_mb: int = 100
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
    )

    def ensure_runtime_dirs(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.preview_root.mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
