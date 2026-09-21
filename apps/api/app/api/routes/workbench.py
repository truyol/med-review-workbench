from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.errors import upload_too_large
from app.models.asset import Asset, AssetKind, AssetStatus
from app.models.case import Case
from app.models.review import Review
from app.schemas.common import ApiResponse, response_with_meta
from app.schemas.workbench import (
    AssetRead,
    CaseCreate,
    CaseRead,
    ProjectCreate,
    ProjectRead,
    ReviewBoard,
    ReviewBoardAsset,
    ReviewCreate,
    ReviewRead,
)
from app.services.workbench import WorkbenchService
from app.settings import Settings, get_settings

router = APIRouter(tags=["workbench"])

LimitQuery = Annotated[int, Query(ge=1, le=100, description="Page size, max 100.")]
OffsetQuery = Annotated[int, Query(ge=0, description="Zero-based page offset.")]
UploadAssetFile = Annotated[UploadFile, File()]


def get_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkbenchService:
    return WorkbenchService(db=db, settings=settings)


@router.post(
    "/projects",
    response_model=ApiResponse[ProjectRead],
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> ApiResponse[ProjectRead]:
    return response_with_meta(ProjectRead.model_validate(service.create_project(payload)))


@router.get("/projects", response_model=ApiResponse[list[ProjectRead]])
def list_projects(
    service: Annotated[WorkbenchService, Depends(get_service)],
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> ApiResponse[list[ProjectRead]]:
    projects = service.list_projects(limit=limit, offset=offset)
    return response_with_meta([ProjectRead.model_validate(project) for project in projects])


@router.post(
    "/projects/{project_id}/cases",
    response_model=ApiResponse[CaseRead],
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    project_id: str,
    payload: CaseCreate,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> ApiResponse[CaseRead]:
    case = service.create_case(project_id=project_id, payload=payload)
    return response_with_meta(CaseRead.model_validate(case))


@router.get("/projects/{project_id}/cases", response_model=ApiResponse[list[CaseRead]])
def list_cases(
    project_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> ApiResponse[list[CaseRead]]:
    cases = service.list_cases(project_id=project_id, limit=limit, offset=offset)
    return response_with_meta([CaseRead.model_validate(case) for case in cases])


@router.post(
    "/cases/{case_id}/assets",
    response_model=ApiResponse[AssetRead],
    status_code=status.HTTP_201_CREATED,
)
def upload_asset(
    case_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
    file: UploadAssetFile,
) -> ApiResponse[AssetRead]:
    # The service performs synchronous parsing, preview generation and disk I/O.
    # Keep this endpoint synchronous so FastAPI runs the whole blocking path in
    # its worker thread instead of blocking the event loop from an async route.
    max_bytes = service.settings.max_upload_mb * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        raise upload_too_large()
    content = _read_upload_limited(
        file.file,
        max_bytes=max_bytes,
    )
    asset = service.ingest_asset(
        case_id=case_id,
        content=content,
        filename=file.filename,
        content_type=file.content_type,
    )
    return response_with_meta(_asset_read(asset))


@router.get("/cases/{case_id}/assets", response_model=ApiResponse[list[AssetRead]])
def list_assets(
    case_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    kind: AssetKind | None = None,
    asset_status: Annotated[AssetStatus | None, Query(alias="status")] = None,
) -> ApiResponse[list[AssetRead]]:
    assets = service.list_assets(
        case_id=case_id,
        limit=limit,
        offset=offset,
        kind=kind,
        status=asset_status,
    )
    return response_with_meta([_asset_read(asset) for asset in assets])


@router.post(
    "/assets/{asset_id}/reviews",
    response_model=ApiResponse[ReviewRead],
    status_code=status.HTTP_201_CREATED,
)
def review_asset(
    asset_id: str,
    payload: ReviewCreate,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> ApiResponse[ReviewRead]:
    review = service.review_asset(asset_id=asset_id, payload=payload)
    return response_with_meta(_review_read(review))


@router.get("/cases/{case_id}/review-board", response_model=ApiResponse[ReviewBoard])
def get_review_board(
    case_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> ApiResponse[ReviewBoard]:
    case = service.get_review_board(case_id=case_id)
    return response_with_meta(_review_board(case))


@router.get("/assets/{asset_id}/preview", response_class=FileResponse)
def get_asset_preview(
    asset_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> FileResponse:
    preview_path = service.get_preview_path(asset_id=asset_id)
    return FileResponse(path=preview_path, media_type="image/png")


@router.get("/assets/{asset_id}/model", response_class=FileResponse)
def get_asset_model(
    asset_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> FileResponse:
    model_path = service.get_model_path(asset_id=asset_id)
    return FileResponse(path=model_path, media_type="model/stl")


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    service: Annotated[WorkbenchService, Depends(get_service)],
) -> None:
    service.delete_asset(asset_id=asset_id)


def _asset_read(asset: Asset) -> AssetRead:
    return AssetRead(
        id=asset.id,
        case_id=asset.case_id,
        kind=asset.kind,
        status=asset.status,
        source_label=asset.source_label,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        sha256=asset.sha256,
        preview_available=asset.preview_path is not None,
        metadata_summary=asset.metadata_summary,
        ingest_warnings=asset.ingest_warnings,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _read_upload_limited(stream: BinaryIO, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while total <= max_bytes:
        chunk = stream.read(min(1024 * 1024, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks)


def _review_read(review: Review) -> ReviewRead:
    return ReviewRead.model_validate(review)


def _review_board(case: Case) -> ReviewBoard:
    visible_assets = [asset for asset in case.assets if asset.deleted_at is None]
    assets = [
        ReviewBoardAsset(
            asset=_asset_read(asset),
            latest_review=_review_read(asset.reviews[0]) if asset.reviews else None,
        )
        for asset in sorted(visible_assets, key=lambda item: item.created_at, reverse=True)
    ]
    return ReviewBoard(case=CaseRead.model_validate(case), assets=assets)
