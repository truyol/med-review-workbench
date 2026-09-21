from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.asset import Asset, AssetKind
from app.models.case import Case
from app.models.project import Project
from app.models.review import Review
from app.ops import seed_demo as seed_module
from app.ops.synthetic_samples import synthetic_stl
from app.services.asset_processing import _inspect_stl
from app.settings import Settings


def test_seed_demo_targets_configured_database_and_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_root = tmp_path / "sample-data"
    image_path = sample_root / "image" / "synthetic-cardiac-ct-baseline.png"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8), color="gray").save(image_path)

    database_path = tmp_path / "container-data" / "medreview.db"
    database_path.parent.mkdir(parents=True)
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        storage_root=tmp_path / "container-data" / "uploads",
        preview_root=tmp_path / "container-data" / "previews",
    )
    monkeypatch.setattr(seed_module, "SessionLocal", session_factory)
    monkeypatch.setattr(seed_module, "get_settings", lambda: settings)

    first = seed_module.seed_demo(sample_root)
    second = seed_module.seed_demo(sample_root)

    assert first == second
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 1
        assert session.scalar(select(func.count()).select_from(Case)) == 1
        assert session.scalar(select(func.count()).select_from(Asset)) == 3
        assert session.scalar(select(func.count()).select_from(Review)) == 1
        assert {asset.kind for asset in session.scalars(select(Asset))} == {
            AssetKind.IMAGE,
            AssetKind.DICOM,
            AssetKind.STL,
        }
        dicom = session.scalar(select(Asset).where(Asset.kind == AssetKind.DICOM))
        assert dicom is not None
        assert dicom.preview_path is not None
        assert dicom.metadata_summary["body_part_examined"] == "PHANTOM"


def test_seed_demo_prefers_bundled_heart_stl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_root = tmp_path / "sample-data"
    image_path = sample_root / "image" / "synthetic-cardiac-ct-baseline.png"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8), color="gray").save(image_path)
    heart_path = sample_root / "stl" / "vh-f-heart.stl"
    heart_path.parent.mkdir(parents=True)
    heart_bytes = b"heart seed test".ljust(80, b" ") + synthetic_stl()[80:]
    heart_path.write_bytes(heart_bytes)

    database_path = tmp_path / "database" / "medreview.db"
    database_path.parent.mkdir(parents=True)
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        storage_root=tmp_path / "database" / "uploads",
        preview_root=tmp_path / "database" / "previews",
    )
    monkeypatch.setattr(seed_module, "SessionLocal", session_factory)
    monkeypatch.setattr(seed_module, "get_settings", lambda: settings)

    seed_module.seed_demo(sample_root)
    seed_module.seed_demo(sample_root)

    with session_factory() as session:
        stl = session.scalar(select(Asset).where(Asset.kind == AssetKind.STL))
        assert stl is not None
        assert stl.sha256 == sha256(heart_bytes).hexdigest()
        assert "心脏参考模型" in stl.tags
        assert session.scalar(select(func.count()).select_from(Asset)) == 3


def test_bundled_heart_stl_matches_attribution() -> None:
    heart_path = Path(__file__).resolve().parents[3] / "sample-data/stl/vh-f-heart.stl"
    content = heart_path.read_bytes()

    assert len(content) == 4_295_784
    assert sha256(content).hexdigest() == (
        "00f3c3672a00ed2cb118e7fc3227fce867b48839eb11f4534fa5b7b58fa80763"
    )
    assert _inspect_stl(content) == {
        "format": "stl",
        "encoding": "binary",
        "triangle_count": 85_914,
    }
