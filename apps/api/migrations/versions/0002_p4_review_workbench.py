"""p4 review workbench schema

Revision ID: 0002_p4_review_workbench
Revises: 0001_baseline
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_p4_review_workbench"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cases",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("case_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("clinical_context", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "case_code", name="uq_cases_project_case_code"),
    )
    op.create_index(op.f("ix_cases_project_id"), "cases", ["project_id"], unique=False)
    op.create_table(
        "assets",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("source_label", sa.String(length=120), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("preview_path", sa.String(length=500), nullable=True),
        sa.Column("metadata_summary", sa.JSON(), nullable=False),
        sa.Column("ingest_warnings", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.String(length=40), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_case_id"), "assets", ["case_id"], unique=False)
    op.create_index(op.f("ix_assets_sha256"), "assets", ["sha256"], unique=False)
    op.create_table(
        "reviews",
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=24), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=80), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviews_asset_id"), "reviews", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_asset_id"), table_name="reviews")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_assets_sha256"), table_name="assets")
    op.drop_index(op.f("ix_assets_case_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_cases_project_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_table("projects")
