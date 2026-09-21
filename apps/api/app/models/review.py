from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.asset import Asset


class ReviewDecision(StrEnum):
    ACCEPT = "accept"
    NEEDS_CHANGES = "needs_changes"
    REJECT = "reject"


class Review(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    asset_id: Mapped[str] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[ReviewDecision] = mapped_column(String(24), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_name: Mapped[str] = mapped_column(String(80), nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="reviews")
