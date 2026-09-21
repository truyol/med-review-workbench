from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.domain.errors import persistence_failed
from app.models.annotation import Annotation
from app.models.asset import Asset, AssetKind, AssetStatus
from app.models.case import Case
from app.models.project import Project
from app.models.review import Review


class WorkbenchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_project(self, project: Project) -> Project:
        self.db.add(project)
        self._commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def list_projects(self, *, limit: int, offset: int) -> list[Project]:
        return list(
            self.db.scalars(
                select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset),
            ),
        )

    def add_case(self, case: Case) -> Case:
        self.db.add(case)
        self._commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: str) -> Case | None:
        return self.db.get(Case, case_id)

    def get_case_by_code(self, *, project_id: str, case_code: str) -> Case | None:
        return self.db.scalar(
            select(Case).where(Case.project_id == project_id, Case.case_code == case_code),
        )

    def list_cases(self, *, project_id: str, limit: int, offset: int) -> list[Case]:
        return list(
            self.db.scalars(
                select(Case)
                .where(Case.project_id == project_id)
                .order_by(Case.created_at.desc())
                .limit(limit)
                .offset(offset),
            ),
        )

    def add_asset(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self._commit()
        self.db.refresh(asset)
        return asset

    def get_asset(self, asset_id: str) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def list_case_assets(
        self,
        *,
        case_id: str,
        limit: int,
        offset: int,
        kind: AssetKind | None = None,
        status: AssetStatus | None = None,
        tag: str | None = None,
    ) -> list[Asset]:
        filters = [Asset.case_id == case_id, Asset.deleted_at.is_(None)]
        if kind is not None:
            filters.append(Asset.kind == kind)
        if status is not None:
            filters.append(Asset.status == status)

        assets = list(
            self.db.scalars(
                select(Asset).where(*filters).order_by(Asset.created_at.desc()),
            ),
        )
        # JSON tag containment is not portable across backends; filter in Python
        # before slicing. Case asset counts are small in this workbench.
        if tag is not None:
            assets = [asset for asset in assets if tag in (asset.tags or [])]
        return assets[offset : offset + limit]

    def update_asset(self, asset: Asset) -> Asset:
        self._commit()
        self.db.refresh(asset)
        return asset

    def add_annotation(self, annotation: Annotation) -> Annotation:
        self.db.add(annotation)
        self._commit()
        self.db.refresh(annotation)
        return annotation

    def list_annotations(self, asset_id: str) -> list[Annotation]:
        return list(
            self.db.scalars(
                select(Annotation)
                .where(Annotation.asset_id == asset_id)
                .order_by(Annotation.created_at),
            ),
        )

    def get_annotation(self, annotation_id: str) -> Annotation | None:
        return self.db.get(Annotation, annotation_id)

    def delete_annotation(self, annotation: Annotation) -> None:
        self.db.delete(annotation)
        self._commit()

    def add_review(self, review: Review) -> Review:
        self.db.add(review)
        self._commit()
        self.db.refresh(review)
        return review

    def get_case_for_review_board(self, case_id: str) -> Case | None:
        return self.db.scalar(
            select(Case)
            .where(Case.id == case_id)
            .options(selectinload(Case.assets).selectinload(Asset.reviews)),
        )

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise persistence_failed() from exc
