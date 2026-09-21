"""add asset tags and annotations

Revision ID: 0003_tags_annotations
Revises: 0002_p4_review_workbench
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_tags_annotations"
down_revision: str | None = "0002_p4_review_workbench"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "assets",
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_table(
        "annotations",
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_annotations_asset_id"), "annotations", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_annotations_asset_id"), table_name="annotations")
    op.drop_table("annotations")
    op.drop_column("assets", "note")
    op.drop_column("assets", "tags")
