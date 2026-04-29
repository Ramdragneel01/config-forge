from __future__ import annotations

from dataclasses import dataclass
import os


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: str
    allowed_hosts: list[str]
    cors_origins: list[str]
    max_payload_bytes: int
    enable_hsts: bool
    api_key: str


_DEFAULT_ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
_DEFAULT_CORS_ORIGINS = "http://localhost:8120,http://127.0.0.1:8120"


def get_settings() -> Settings:
    return Settings(
        host=os.getenv("CONFIG_FORGE_HOST", "0.0.0.0"),
        port=int(os.getenv("CONFIG_FORGE_PORT", "8040")),
        db_path=os.getenv("CONFIG_FORGE_DB_PATH", "./backend/data/config_forge.sqlite3"),
        allowed_hosts=_split_csv(os.getenv("CONFIG_FORGE_ALLOWED_HOSTS", _DEFAULT_ALLOWED_HOSTS)),
        cors_origins=_split_csv(os.getenv("CONFIG_FORGE_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS)),
        max_payload_bytes=int(os.getenv("CONFIG_FORGE_MAX_PAYLOAD_BYTES", "4194304")),
        enable_hsts=os.getenv("CONFIG_FORGE_ENABLE_HSTS", "false").lower() == "true",
        api_key=os.getenv("CONFIG_FORGE_API_KEY", "").strip(),
    )
