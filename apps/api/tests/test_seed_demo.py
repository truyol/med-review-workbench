from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.asset import Asset
from app.models.case import Case
from app.models.project import Project
from app.models.review import Review
from app.ops import seed_demo as seed_module
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
        assert session.scalar(select(func.count()).select_from(Asset)) == 1
        assert session.scalar(select(func.count()).select_from(Review)) == 1
