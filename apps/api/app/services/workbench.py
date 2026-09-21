from collections.abc import Sequence
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.errors import (
    annotation_not_found,
    asset_delete_restricted,
    asset_file_missing,
    asset_not_found,
    case_not_found,
    duplicate_case_code,
    model_not_available,
    preview_not_available,
    project_not_found,
)
from app.models.annotation import Annotation
from app.models.asset import Asset, AssetKind, AssetStatus
from app.models.case import Case
from app.models.project import Project
from app.models.review import Review, ReviewDecision
from app.repositories.workbench import WorkbenchRepository
from app.schemas.workbench import (
    AnnotationCreate,
    AssetUpdate,
    CaseCreate,
    ProjectCreate,
    ReviewCreate,
)
from app.services.asset_processing import prepare_asset_upload
from app.settings import Settings


def clamp_limit(limit: int) -> int:
    return min(max(limit, 1), 100)


class WorkbenchService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.repo = WorkbenchRepository(db)
        self.settings = settings

    def create_project(self, payload: ProjectCreate) -> Project:
        return self.repo.add_project(
            Project(name=payload.name, description=payload.description),
        )

    def list_projects(self, *, limit: int, offset: int) -> Sequence[Project]:
        return self.repo.list_projects(limit=clamp_limit(limit), offset=offset)

    def create_case(self, *, project_id: str, payload: CaseCreate) -> Case:
        self._require_project(project_id)
        if self.repo.get_case_by_code(project_id=project_id, case_code=payload.case_code):
            raise duplicate_case_code()

        try:
            return self.repo.add_case(
                Case(
                    project_id=project_id,
                    case_code=payload.case_code,
                    title=payload.title,
                    clinical_context=payload.clinical_context,
                ),
            )
        except IntegrityError as exc:
            raise duplicate_case_code() from exc

    def list_cases(self, *, project_id: str, limit: int, offset: int) -> Sequence[Case]:
        self._require_project(project_id)
        return self.repo.list_cases(
            project_id=project_id,
            limit=clamp_limit(limit),
            offset=offset,
        )

    def ingest_asset(
        self,
        *,
        case_id: str,
        content: bytes,
        filename: str | None,
        content_type: str | None,
    ) -> Asset:
        self._require_case(case_id)
        prepared = prepare_asset_upload(
            content=content,
            filename=filename,
            content_type=content_type,
            settings=self.settings,
        )
        return self.repo.add_asset(
            Asset(
                case_id=case_id,
                kind=prepared.kind,
                source_label=prepared.source_label,
                content_type=prepared.content_type,
                size_bytes=prepared.size_bytes,
                sha256=prepared.sha256,
                storage_path=prepared.storage_path,
                preview_path=prepared.preview_path,
                metadata_summary=prepared.metadata_summary,
                ingest_warnings=prepared.ingest_warnings,
            ),
        )

    def list_assets(
        self,
        *,
        case_id: str,
        limit: int,
        offset: int,
        kind: AssetKind | None = None,
        status: AssetStatus | None = None,
        tag: str | None = None,
    ) -> Sequence[Asset]:
        self._require_case(case_id)
        return self.repo.list_case_assets(
            case_id=case_id,
            limit=clamp_limit(limit),
            offset=offset,
            kind=kind,
            status=status,
            tag=tag,
        )

    def update_asset(self, *, asset_id: str, payload: AssetUpdate) -> Asset:
        asset = self._require_asset(asset_id)
        if payload.tags is not None:
            asset.tags = payload.tags
        if payload.note is not None:
            asset.note = payload.note
        return self.repo.update_asset(asset)

    def add_annotation(self, *, asset_id: str, payload: AnnotationCreate) -> Annotation:
        self._require_asset(asset_id)
        return self.repo.add_annotation(
            Annotation(
                asset_id=asset_id,
                label=payload.label,
                data=payload.data,
                note=payload.note,
            ),
        )

    def list_annotations(self, *, asset_id: str) -> Sequence[Annotation]:
        self._require_asset(asset_id)
        return self.repo.list_annotations(asset_id)

    def delete_annotation(self, *, annotation_id: str) -> None:
        annotation = self.repo.get_annotation(annotation_id)
        if annotation is None:
            raise annotation_not_found()
        self.repo.delete_annotation(annotation)

    def review_asset(self, *, asset_id: str, payload: ReviewCreate) -> Review:
        asset = self.repo.get_asset(asset_id)
        if asset is None:
            raise asset_not_found()

        asset.status = _status_for_decision(payload.decision)
        review = Review(
            asset_id=asset_id,
            decision=payload.decision,
            note=payload.note,
            reviewer_name=payload.reviewer_name,
        )
        return self.repo.add_review(review)

    def get_review_board(self, *, case_id: str) -> Case:
        case = self.repo.get_case_for_review_board(case_id)
        if case is None:
            raise case_not_found()
        return case

    def get_preview_path(self, *, asset_id: str) -> Path:
        asset = self._require_asset(asset_id)
        if asset.preview_path is None:
            raise preview_not_available()
        preview_path = Path(asset.preview_path)
        if not preview_path.exists():
            raise asset_file_missing()
        return preview_path

    def get_model_path(self, *, asset_id: str) -> Path:
        asset = self._require_asset(asset_id)
        if asset.kind != AssetKind.STL:
            raise model_not_available()
        model_path = Path(asset.storage_path)
        if not model_path.exists():
            raise asset_file_missing()
        return model_path

    def delete_asset(self, *, asset_id: str) -> None:
        asset = self._require_asset(asset_id)
        if asset.reviews:
            raise asset_delete_restricted()
        Path(asset.storage_path).unlink(missing_ok=True)
        if asset.preview_path:
            Path(asset.preview_path).unlink(missing_ok=True)
        self.repo.db.delete(asset)
        self.repo.db.commit()

    def _require_project(self, project_id: str) -> Project:
        project = self.repo.get_project(project_id)
        if project is None:
            raise project_not_found()
        return project

    def _require_case(self, case_id: str) -> Case:
        case = self.repo.get_case(case_id)
        if case is None:
            raise case_not_found()
        return case

    def _require_asset(self, asset_id: str) -> Asset:
        asset = self.repo.get_asset(asset_id)
        if asset is None:
            raise asset_not_found()
        return asset


def _status_for_decision(decision: ReviewDecision) -> AssetStatus:
    if decision == ReviewDecision.ACCEPT:
        return AssetStatus.ACCEPTED
    if decision == ReviewDecision.NEEDS_CHANGES:
        return AssetStatus.NEEDS_CHANGES
    return AssetStatus.REJECTED
