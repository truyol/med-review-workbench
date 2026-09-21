from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.annotation import Annotation
    from app.models.case import Case
    from app.models.review import Review


class AssetKind(StrEnum):
    DICOM = "dicom"
    STL = "stl"
    IMAGE = "image"


class AssetStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    NEEDS_CHANGES = "needs_changes"
    REJECTED = "rejected"


class Asset(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[AssetKind] = mapped_column(String(20), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        String(24),
        default=AssetStatus.PENDING,
        nullable=False,
    )
    source_label: Mapped[str] = mapped_column(String(120), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    ingest_warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    delete_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[Case] = relationship(back_populates="assets")
    reviews: Mapped[list[Review]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="Review.created_at.desc()",
    )
    annotations: Mapped[list[Annotation]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="Annotation.created_at",
    )
