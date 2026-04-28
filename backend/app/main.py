from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .middleware import HostAllowlistMiddleware, PayloadSizeLimitMiddleware, SecurityHeadersMiddleware
from .models import ConfigCreate, ConfigVersion, PromotionRequest, ReleaseRecord, ValidationResult
from .service import ConfigService
from .store import Store

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = Store(settings.db_path)
    app.state.service = ConfigService(store)
    yield


app = FastAPI(
    title="config-forge API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HostAllowlistMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(PayloadSizeLimitMiddleware, max_payload_bytes=settings.max_payload_bytes)
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=settings.enable_hsts)


def get_service() -> ConfigService:
    return app.state.service


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(service: ConfigService = Depends(get_service)) -> dict[str, str]:
    _ = service.list_configs()
    return {"status": "ready"}


@app.post("/api/v1/configs", response_model=ConfigVersion)
def create_config(payload: ConfigCreate, service: ConfigService = Depends(get_service)) -> ConfigVersion:
    return service.create_config(payload)


@app.get("/api/v1/configs", response_model=list[ConfigVersion])
def list_configs(service: ConfigService = Depends(get_service)) -> list[ConfigVersion]:
    return service.list_configs()


@app.post("/api/v1/configs/{config_id}/validate", response_model=ValidationResult)
def validate_config(config_id: int, service: ConfigService = Depends(get_service)) -> ValidationResult:
    try:
        return service.validate_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/configs/{config_id}/validation", response_model=ValidationResult | None)
def latest_validation(config_id: int, service: ConfigService = Depends(get_service)) -> ValidationResult | None:
    return service.get_latest_validation(config_id)


@app.post("/api/v1/configs/{config_id}/promote", response_model=ReleaseRecord)
def promote_config(
    config_id: int,
    payload: PromotionRequest,
    service: ConfigService = Depends(get_service),
) -> ReleaseRecord:
    try:
        return service.promote_config(config_id, payload)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "config not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/v1/releases", response_model=list[ReleaseRecord])
def list_releases(service: ConfigService = Depends(get_service)) -> list[ReleaseRecord]:
    return service.list_releases()
