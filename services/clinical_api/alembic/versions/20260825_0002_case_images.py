"""Add clinical case image attachments.

Revision ID: 20260825_0002
Revises: 20260825_0001
Create Date: 2026-08-25 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260825_0002"
down_revision = "20260825_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_case_images",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_image_id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("uploaded_by_user_ref", sa.String(length=128), nullable=True),
        sa.Column("image_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["clinical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_image_id"),
    )
    op.create_index(op.f("ix_clinical_case_images_case_id"), "clinical_case_images", ["case_id"], unique=False)
    op.create_index(op.f("ix_clinical_case_images_external_image_id"), "clinical_case_images", ["external_image_id"], unique=False)
    op.create_index(op.f("ix_clinical_case_images_uploaded_at"), "clinical_case_images", ["uploaded_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_case_images_uploaded_at"), table_name="clinical_case_images")
    op.drop_index(op.f("ix_clinical_case_images_external_image_id"), table_name="clinical_case_images")
    op.drop_index(op.f("ix_clinical_case_images_case_id"), table_name="clinical_case_images")
    op.drop_table("clinical_case_images")
