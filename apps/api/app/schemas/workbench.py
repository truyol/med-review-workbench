from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetKind, AssetStatus
from app.models.review import ReviewDecision


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    case_code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    title: str = Field(min_length=1, max_length=160)
    clinical_context: str | None = Field(default=None, max_length=2000)


class CaseRead(CaseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    kind: AssetKind
    status: AssetStatus
    source_label: str
    content_type: str | None
    size_bytes: int
    sha256: str
    preview_available: bool
    metadata_summary: dict[str, object]
    ingest_warnings: list[str]
    created_at: datetime
    updated_at: datetime


class ReviewCreate(BaseModel):
    decision: ReviewDecision
    note: str | None = Field(default=None, max_length=2000)
    reviewer_name: str = Field(min_length=1, max_length=80)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    decision: ReviewDecision
    note: str | None
    reviewer_name: str
    created_at: datetime
    updated_at: datetime


class ReviewBoardAsset(BaseModel):
    asset: AssetRead
    latest_review: ReviewRead | None


class ReviewBoard(BaseModel):
    case: CaseRead
    assets: list[ReviewBoardAsset]
