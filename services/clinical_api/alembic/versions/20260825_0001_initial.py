"""Initial clinical API persistence schema.

Revision ID: 20260825_0001
Revises:
Create Date: 2026-08-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260825_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_case_id", sa.String(length=64), nullable=False),
        sa.Column("case_status", sa.String(length=32), nullable=False),
        sa.Column("procedure_type", sa.String(length=32), nullable=False),
        sa.Column("patient_identifier", sa.String(length=128), nullable=False),
        sa.Column("procedure_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("facility_unit", sa.String(length=128), nullable=False),
        sa.Column("endoscopist_name", sa.String(length=128), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("current_pdf_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("current_pdf_filename", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_case_id"),
    )
    op.create_index(op.f("ix_clinical_cases_case_status"), "clinical_cases", ["case_status"], unique=False)
    op.create_index(op.f("ix_clinical_cases_external_case_id"), "clinical_cases", ["external_case_id"], unique=False)
    op.create_index(op.f("ix_clinical_cases_finalized_at"), "clinical_cases", ["finalized_at"], unique=False)
    op.create_index(op.f("ix_clinical_cases_patient_identifier"), "clinical_cases", ["patient_identifier"], unique=False)
    op.create_index(op.f("ix_clinical_cases_procedure_datetime"), "clinical_cases", ["procedure_datetime"], unique=False)
    op.create_index(op.f("ix_clinical_cases_procedure_type"), "clinical_cases", ["procedure_type"], unique=False)

    op.create_table(
        "clinical_followup_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_task_id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("task_owner_user_id", sa.String(length=128), nullable=True),
        sa.Column("task_owner_user_ref", sa.String(length=128), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("task_status", sa.String(length=32), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("closed_by_user_ref", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["clinical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_task_id"),
    )
    op.create_index(op.f("ix_clinical_followup_tasks_case_id"), "clinical_followup_tasks", ["case_id"], unique=False)
    op.create_index(op.f("ix_clinical_followup_tasks_due_date"), "clinical_followup_tasks", ["due_date"], unique=False)
    op.create_index(op.f("ix_clinical_followup_tasks_external_task_id"), "clinical_followup_tasks", ["external_task_id"], unique=False)
    op.create_index(op.f("ix_clinical_followup_tasks_task_status"), "clinical_followup_tasks", ["task_status"], unique=False)
    op.create_index(op.f("ix_clinical_followup_tasks_task_type"), "clinical_followup_tasks", ["task_type"], unique=False)

    op.create_table(
        "clinical_case_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("finalized_by_user_ref", sa.String(length=128), nullable=True),
        sa.Column("template_version", sa.String(length=128), nullable=True),
        sa.Column("report_narrative_snapshot", sa.Text(), nullable=True),
        sa.Column("pdf_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("pdf_filename", sa.String(length=255), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["clinical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_case_revisions_case_id"), "clinical_case_revisions", ["case_id"], unique=False)
    op.create_index(op.f("ix_clinical_case_revisions_revision_number"), "clinical_case_revisions", ["revision_number"], unique=False)

    op.create_table(
        "clinical_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=128), nullable=True),
        sa.Column("actor_display_name", sa.String(length=128), nullable=True),
        sa.Column("actor_role", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_ref", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["clinical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinical_audit_events_case_id"), "clinical_audit_events", ["case_id"], unique=False)
    op.create_index(op.f("ix_clinical_audit_events_created_at"), "clinical_audit_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_clinical_audit_events_event_type"), "clinical_audit_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_audit_events_event_type"), table_name="clinical_audit_events")
    op.drop_index(op.f("ix_clinical_audit_events_created_at"), table_name="clinical_audit_events")
    op.drop_index(op.f("ix_clinical_audit_events_case_id"), table_name="clinical_audit_events")
    op.drop_table("clinical_audit_events")

    op.drop_index(op.f("ix_clinical_case_revisions_revision_number"), table_name="clinical_case_revisions")
    op.drop_index(op.f("ix_clinical_case_revisions_case_id"), table_name="clinical_case_revisions")
    op.drop_table("clinical_case_revisions")

    op.drop_index(op.f("ix_clinical_followup_tasks_task_type"), table_name="clinical_followup_tasks")
    op.drop_index(op.f("ix_clinical_followup_tasks_task_status"), table_name="clinical_followup_tasks")
    op.drop_index(op.f("ix_clinical_followup_tasks_external_task_id"), table_name="clinical_followup_tasks")
    op.drop_index(op.f("ix_clinical_followup_tasks_due_date"), table_name="clinical_followup_tasks")
    op.drop_index(op.f("ix_clinical_followup_tasks_case_id"), table_name="clinical_followup_tasks")
    op.drop_table("clinical_followup_tasks")

    op.drop_index(op.f("ix_clinical_cases_procedure_type"), table_name="clinical_cases")
    op.drop_index(op.f("ix_clinical_cases_procedure_datetime"), table_name="clinical_cases")
    op.drop_index(op.f("ix_clinical_cases_patient_identifier"), table_name="clinical_cases")
    op.drop_index(op.f("ix_clinical_cases_finalized_at"), table_name="clinical_cases")
    op.drop_index(op.f("ix_clinical_cases_external_case_id"), table_name="clinical_cases")
    op.drop_index(op.f("ix_clinical_cases_case_status"), table_name="clinical_cases")
    op.drop_table("clinical_cases")
