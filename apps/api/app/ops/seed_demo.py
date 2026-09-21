from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.asset import Asset, AssetStatus
from app.models.case import Case
from app.models.project import Project
from app.models.review import Review, ReviewDecision
from app.ops.synthetic_samples import synthetic_dicom, synthetic_stl
from app.services.asset_processing import prepare_asset_upload
from app.settings import get_settings

DEMO_PROJECT_NAME = "Demo - SHD preoperative asset review"
DEMO_CASE_CODE = "DEMO-TAVR-001"


def seed_demo(sample_root: Path) -> tuple[str, str]:
    settings = get_settings()
    sample_files = [
        (
            sample_root / "image" / "synthetic-cardiac-ct-baseline.png",
            "image/png",
            ["基线图"],
            None,
        ),
        (
            sample_root / "dicom" / "CT_small_anonymized.dcm",
            "application/dicom",
            ["CT", "已脱敏"],
            synthetic_dicom,
        ),
        (
            sample_root / "stl" / "vh-f-heart.stl",
            "model/stl",
            ["心脏参考模型", "3D 模型"],
            synthetic_stl,
        ),
    ]
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == DEMO_PROJECT_NAME))
        if project is None:
            project = Project(
                name=DEMO_PROJECT_NAME,
                description="Repository-safe, de-identified demonstration assets only.",
            )
            db.add(project)
            db.flush()
        case = db.scalar(
            select(Case).where(
                Case.project_id == project.id,
                Case.case_code == DEMO_CASE_CODE,
            ),
        )
        if case is None:
            case = Case(
                project_id=project.id,
                case_code=DEMO_CASE_CODE,
                title="TAVR preoperative asset review",
            )
            db.add(case)
            db.flush()
        existing = {
            asset.sha256 for asset in db.scalars(select(Asset).where(Asset.case_id == case.id))
        }
        for path, content_type, tags, fallback in sample_files:
            if not path.exists() and fallback is None:
                continue
            if path.exists():
                content = path.read_bytes()
            elif fallback is not None:
                content = fallback()
            else:
                continue
            digest = hashlib.sha256(content).hexdigest()
            if digest in existing:
                continue
            prepared = prepare_asset_upload(
                content=content,
                filename=path.name,
                content_type=content_type,
                settings=settings,
            )
            asset = Asset(
                case_id=case.id,
                kind=prepared.kind,
                source_label=prepared.source_label,
                content_type=prepared.content_type,
                size_bytes=prepared.size_bytes,
                sha256=prepared.sha256,
                storage_path=prepared.storage_path,
                preview_path=prepared.preview_path,
                metadata_summary=prepared.metadata_summary,
                ingest_warnings=prepared.ingest_warnings,
                tags=tags,
            )
            db.add(asset)
            db.flush()
            existing.add(digest)
            if asset.kind.value == "image":
                asset.status = AssetStatus.ACCEPTED
                db.add(
                    Review(
                        asset_id=asset.id,
                        decision=ReviewDecision.ACCEPT,
                        note="Demo asset: preview and provenance verified.",
                        reviewer_name="demo-reviewer",
                    ),
                )
        db.commit()
        return project.id, case.id


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed idempotent demonstration data.")
    parser.add_argument("--sample-root", type=Path, default=Path("sample-data"))
    args = parser.parse_args()
    project_id, case_id = seed_demo(args.sample_root.resolve())
    print(f"Demo project ready: {project_id} / {case_id}")


if __name__ == "__main__":
    main()
