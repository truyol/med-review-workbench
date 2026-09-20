from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.db.session import check_database
from app.observability.request_id import get_request_id
from app.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthData(BaseModel):
    status: Literal["ok"]
    service: Literal["medreview-api"]


class HealthMeta(BaseModel):
    request_id: str


class HealthResponse(BaseModel):
    data: HealthData
    meta: HealthMeta


class ReadyDependency(BaseModel):
    database: Literal["ok", "failed"]
    storage: Literal["ok", "failed"]


class ReadyData(HealthData):
    dependencies: ReadyDependency


class ReadyResponse(BaseModel):
    data: ReadyData
    meta: HealthMeta


@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        data=HealthData(status="ok", service="medreview-api"),
        meta=HealthMeta(request_id=get_request_id()),
    )


@router.get("/ready", response_model=ReadyResponse)
def readiness(response: Response) -> ReadyResponse:
    settings = get_settings()
    database: Literal["ok", "failed"] = "ok"
    storage: Literal["ok", "failed"] = "ok"

    try:
        settings.ensure_runtime_dirs()
        check_database()
    except Exception:
        database = "failed"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if not settings.storage_root.exists() or not settings.preview_root.exists():
        storage = "failed"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        data=ReadyData(
            status="ok",
            service="medreview-api",
            dependencies=ReadyDependency(database=database, storage=storage),
        ),
        meta=HealthMeta(request_id=get_request_id()),
    )
