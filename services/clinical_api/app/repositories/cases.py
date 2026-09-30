from __future__ import annotations

import base64
import mimetypes
import textwrap
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, object_session

from app.auth import AuthenticatedSession
from app.core.settings import get_settings
from app.database import (
    ClinicalAuditEventRecord,
    ClinicalCaseRecord,
    ClinicalCaseImageRecord,
    ClinicalCaseRevisionRecord,
    ClinicalTaskRecord,
    session_scope,
)
from app.integrations.odoo_bridge import OdooBridgeClient, OdooBridgeError
from app.reference_data import (
    DEFAULT_CLINICIANS,
    DEFAULT_FACILITIES,
    DEFAULT_FACILITY_UNITS,
    DEFAULT_REFERRER_SERVICES,
    LOCAL_TEMPLATE_VERSION,
    build_sample_cases,
)
from app.schemas import (
    AuditEventPayload,
    CaseActionType,
    CaseHistoryPayload,
    CaseImageAttachmentPayload,
    CaseRevisionPayload,
    CaseStatus,
    CaseStoreMode,
    CaseSummary,
    ClinicalDraftCasePayload,
    ClinicalLookupsPayload,
    ClinicianLookupOption,
    DashboardSnapshot,
    DashboardLanePayload,
    FacilityLookupOption,
    FacilityUnitLookupOption,
    FollowUpTask,
    FollowUpTaskUpdatePayload,
    OdooDraftCasePayload,
    OdooFollowUpTaskPayload,
    StartCasePayload,
    ValueLookupOption,
    PatientRelationshipSuggestion,
    PatientLookupOption,
    WorkspaceRole,
    RoleDashboardPayload,
)
from app.workflow import ensure_case_action_allowed


MAX_CASE_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}


def get_case_store_mode() -> CaseStoreMode:
    settings = get_settings()
    if settings.odoo_bridge_base_url.strip() and settings.odoo_bridge_db_name.strip() and settings.odoo_bridge_api_key.strip():
        return "odoo_bridge"
    return "database"


def bootstrap_local_database() -> None:
    if get_case_store_mode() != "database" or not get_settings().clinical_api_seed_sample_data:
        return

    with session_scope() as db:
        existing = db.scalar(select(func.count()).select_from(ClinicalCaseRecord)) or 0
        if existing:
            return

        for payload in build_sample_cases():
            _upsert_database_case(
                db,
                payload,
                actor=None,
                log_case_update=False,
                ensure_revision_on_finalized=True,
            )


def list_cases(session: AuthenticatedSession | None = None) -> list[CaseSummary]:
    client = _get_odoo_client(session)
    if client and session:
        return [_summary_from_remote(item) for item in client.list_cases(session.odoo_session_id)]

    with session_scope() as db:
        records = db.scalars(
            select(ClinicalCaseRecord).order_by(ClinicalCaseRecord.procedure_datetime.desc(), ClinicalCaseRecord.created_at.desc())
        ).all()
        return [_summary_from_case_record(record) for record in records if _session_can_access_draft(_draft_from_case_record(record), session)]


def list_tasks(session: AuthenticatedSession | None = None) -> list[FollowUpTask]:
    client = _get_odoo_client(session)
    if client and session:
        return [_task_from_remote(item) for item in client.list_tasks(session.odoo_session_id)]

    with session_scope() as db:
        records = db.scalars(
            select(ClinicalTaskRecord).order_by(ClinicalTaskRecord.due_date.asc(), ClinicalTaskRecord.created_at.asc())
        ).all()
        return [_task_from_case_record(record) for record in records if record.case and _session_can_access_draft(_draft_from_case_record(record.case), session)]


def get_case_draft(external_case_id: str, session: AuthenticatedSession | None = None) -> ClinicalDraftCasePayload | None:
    client = _get_odoo_client(session)
    if client and session:
        remote_payload = client.get_case(session.odoo_session_id, external_case_id)
        return ClinicalDraftCasePayload.model_validate(remote_payload) if remote_payload else None

    with session_scope() as db:
        record = _database_case_record(db, external_case_id)
        if not record:
            return None
        draft = _draft_from_case_record(record)
        return draft if _session_can_access_draft(draft, session) else None


def save_case_draft(
    payload: ClinicalDraftCasePayload,
    session: AuthenticatedSession | None = None,
) -> tuple[ClinicalDraftCasePayload, CaseStoreMode]:
    draft = ClinicalDraftCasePayload.model_validate(payload)
    client = _get_odoo_client(session)
    if client and session:
        client.sync_case(session.odoo_session_id, draft.model_dump(mode="json", exclude_none=False))
        stored = get_case_draft(draft.external_case_id, session=session) or draft
        return stored, "odoo_bridge"

    with session_scope() as db:
        stored = _upsert_database_case(db, draft, actor=session)
        return stored, "database"


def create_start_case(
    payload: StartCasePayload,
    session: AuthenticatedSession | None = None,
) -> tuple[ClinicalDraftCasePayload, CaseStoreMode]:
    external_case_id = f"case-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    unit_option = _find_unit_option(payload.facilityUnit)
    if payload.facilityCode and unit_option and unit_option.get("facilityCode") != payload.facilityCode:
        unit_option = None
    inferred_facility_code = _infer_facility_code(payload.endoscopistUserId, session)
    facility_code = unit_option.get("facilityCode") if unit_option else payload.facilityCode or inferred_facility_code
    if not facility_code:
        raise ValueError("Select a facility when the endoscopist can work at more than one facility.")
    draft = ClinicalDraftCasePayload(
        external_case_id=external_case_id,
        case_status="draft",
        procedure_type=payload.procedureType,
        patient_identifier=payload.patientIdentifier,
        procedure_datetime=payload.procedureDatetime,
        dob_or_age=payload.dobOrAge,
        sex=payload.sex,
        patient_identity_verified=payload.patientIdentityVerified,
        facility_unit=unit_option["label"] if unit_option else payload.facilityUnit or "",
        facility_code=facility_code,
        facility_unit_code=unit_option.get("code") if unit_option else None,
        endoscopist_user_id=payload.endoscopistUserId,
        endoscopist_user_ref=_lookup_user_label(payload.endoscopistUserId),
        assistant_nurse_user_id=payload.assistantNurseUserId,
        assistant_nurse_user_ref=_lookup_user_label(payload.assistantNurseUserId) if payload.assistantNurseUserId else None,
        referrer_service=payload.referrerService,
        followup_tasks=[],
    )
    return save_case_draft(draft, session=session)


def get_lookups(session: AuthenticatedSession | None = None) -> ClinicalLookupsPayload:
    client = _get_odoo_client(session)
    if client and session:
        remote_payload = client.get_lookups(session.odoo_session_id)
        return ClinicalLookupsPayload.model_validate(remote_payload)

    with session_scope() as db:
        payloads = [_draft_from_case_record(record) for record in db.scalars(select(ClinicalCaseRecord)).all()]
    visible_payloads = [payload for payload in payloads if _session_can_access_draft(payload, session)]
    return _build_lookups_from_payloads(visible_payloads, session=session)


def get_patient_relationship(
    patient_identifier: str,
    session: AuthenticatedSession | None = None,
) -> PatientRelationshipSuggestion | None:
    client = _get_odoo_client(session)
    if client and session:
        payload = client.get_patient_relationship(session.odoo_session_id, patient_identifier)
        return PatientRelationshipSuggestion.model_validate(payload) if payload else None
    return None


def search_patients(query: str, session: AuthenticatedSession | None = None) -> list[PatientLookupOption]:
    client = _get_odoo_client(session)
    if client and session:
        return [PatientLookupOption.model_validate(item) for item in client.search_patients(session.odoo_session_id, query)]
    return []


def perform_case_action(
    external_case_id: str,
    action: CaseActionType,
    payload: dict[str, str | None] | None = None,
    session: AuthenticatedSession | None = None,
) -> tuple[ClinicalDraftCasePayload | None, CaseStoreMode]:
    client = _get_odoo_client(session)
    action_payload = payload or {}
    if client and session:
        result = client.case_action(session.odoo_session_id, external_case_id, action, action_payload)
        if result.get("status") == "not_found":
            return None, "odoo_bridge"
        case_payload = result.get("case")
        if not case_payload:
            raise OdooBridgeError("Odoo bridge case action returned no case payload.")
        return ClinicalDraftCasePayload.model_validate(case_payload), "odoo_bridge"

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record:
            return None, "database"

        draft = _draft_from_case_record(case_record)
        _ensure_session_can_access_draft(draft, session)
        ensure_case_action_allowed(
            action=action,
            status=draft.case_status,
            role=session.primary_role if session else None,
            reopen_reason=str(action_payload.get("reason") or ""),
        )
        next_payload = draft.model_dump(mode="json", exclude_none=False)
        errors = _local_case_action_validation_errors(draft)
        now_iso = _format_datetime(_utcnow())

        if action == "preview":
            next_payload["template_version"] = LOCAL_TEMPLATE_VERSION
            next_payload["report_narrative_snapshot"] = _local_narrative(draft)
            next_payload["validation_summary"] = _local_validation_summary(errors)
            stored = _upsert_database_case(db, ClinicalDraftCasePayload.model_validate(next_payload), actor=session, log_case_update=False)
            _log_database_audit_event(
                db,
                case_record,
                session,
                "report_preview_generated",
                payload={"validation_errors": errors, "template_version": LOCAL_TEMPLATE_VERSION},
            )
            return stored, "database"

        if action == "mark_ready_for_signoff":
            ensure_case_action_allowed(action=action, status=draft.case_status, role=session.primary_role if session else None)
            if errors:
                raise ValueError(_local_validation_summary(errors))
            next_payload["case_status"] = "ready_for_signoff"
            next_payload["template_version"] = LOCAL_TEMPLATE_VERSION
            next_payload["report_narrative_snapshot"] = _local_narrative(draft)
            next_payload["validation_summary"] = "Ready for sign-off."
            stored = _upsert_database_case(db, ClinicalDraftCasePayload.model_validate(next_payload), actor=session, log_case_update=False)
            _log_database_audit_event(
                db,
                case_record,
                session,
                "ready_for_signoff_marked",
                payload={"template_version": LOCAL_TEMPLATE_VERSION},
            )
            return stored, "database"

        if action == "finalize":
            ensure_case_action_allowed(action=action, status=draft.case_status, role=session.primary_role if session else None)
            if errors:
                raise ValueError(_local_validation_summary(errors))

            finalized_at = _utcnow()
            narrative = _local_narrative(draft)
            next_payload["case_status"] = "finalized"
            next_payload["finalized_at"] = _format_datetime(finalized_at)
            next_payload["finalized_by_user_id"] = session.login
            next_payload["finalized_by_user_ref"] = session.display_name
            next_payload["template_version"] = LOCAL_TEMPLATE_VERSION
            next_payload["report_narrative_snapshot"] = narrative
            next_payload["validation_summary"] = f"Finalized on {now_iso} by {session.display_name}."
            next_payload["pdf_asset_ref"] = _current_pdf_path(external_case_id)
            stored = _upsert_database_case(db, ClinicalDraftCasePayload.model_validate(next_payload), actor=session, log_case_update=False)
            refreshed_record = _database_case_record(db, external_case_id)
            if refreshed_record:
                _create_final_assets(db, refreshed_record, stored)
                _log_database_audit_event(
                    db,
                    refreshed_record,
                    session,
                    "report_finalized",
                    payload={
                        "revision_number": _latest_revision_number(refreshed_record),
                        "template_version": LOCAL_TEMPLATE_VERSION,
                        "followup_state": "open" if stored.followup_tasks else "not_required",
                    },
                )
                stored = _draft_from_case_record(refreshed_record)
            return stored, "database"

        if action == "return_to_draft":
            ensure_case_action_allowed(action=action, status=draft.case_status, role=session.primary_role if session else None)
            next_payload["case_status"] = "draft"
            next_payload["validation_summary"] = None
            stored = _upsert_database_case(db, ClinicalDraftCasePayload.model_validate(next_payload), actor=session, log_case_update=False)
            _log_database_audit_event(db, case_record, session, "returned_to_draft")
            return stored, "database"

        if action == "reopen":
            reason = str(action_payload.get("reason") or "").strip()
            ensure_case_action_allowed(action=action, status=draft.case_status, role=session.primary_role if session else None, reopen_reason=reason)

            next_payload["case_status"] = "draft_reopened"
            next_payload["finalized_at"] = None
            next_payload["finalized_by_user_id"] = None
            next_payload["finalized_by_user_ref"] = None
            next_payload["template_version"] = None
            next_payload["report_narrative_snapshot"] = None
            next_payload["pdf_asset_ref"] = None
            next_payload["validation_summary"] = "Case reopened for amendment."
            next_payload["reopen_reason"] = reason
            next_payload["reopened_at"] = now_iso
            next_payload["reopened_by_user_id"] = session.login
            next_payload["reopened_by_user_ref"] = session.display_name
            stored = _upsert_database_case(db, ClinicalDraftCasePayload.model_validate(next_payload), actor=session, log_case_update=False)
            refreshed_record = _database_case_record(db, external_case_id)
            if refreshed_record:
                refreshed_record.current_pdf_bytes = None
                refreshed_record.current_pdf_filename = None
                _log_database_audit_event(
                    db,
                    refreshed_record,
                    session,
                    "report_reopened",
                    reason=reason,
                    payload={
                        "revision_count": len(refreshed_record.revisions),
                        "reopened_by": session.display_name,
                    },
                )
                stored = _draft_from_case_record(refreshed_record)
            return stored, "database"

        raise ValueError(f"Unsupported case action: {action}")


def update_followup_task(
    external_task_id: str,
    payload: FollowUpTaskUpdatePayload,
    session: AuthenticatedSession | None = None,
) -> tuple[OdooFollowUpTaskPayload | None, str | None, CaseStoreMode]:
    updates = payload.model_dump(mode="json", exclude_unset=True)
    client = _get_odoo_client(session)
    if client and session:
        result = client.update_task(session.odoo_session_id, external_task_id, updates)
        if result.get("status") == "not_found":
            return None, None, "odoo_bridge"
        task_payload = result.get("task")
        if not task_payload:
            raise OdooBridgeError("Odoo bridge task update returned no task payload.")
        case_id = str(result.get("external_case_id") or result.get("case_id") or "")
        return OdooFollowUpTaskPayload.model_validate(task_payload), case_id or None, "odoo_bridge"

    with session_scope() as db:
        task_record = db.scalar(select(ClinicalTaskRecord).where(ClinicalTaskRecord.external_task_id == external_task_id))
        if not task_record:
            return None, None, "database"

        case_record = task_record.case
        _ensure_session_can_access_draft(_draft_from_case_record(case_record), session)
        previous_owner = task_record.task_owner_user_ref
        previous_status = task_record.task_status
        previous_resolution = task_record.resolution_note

        if "task_owner_user_id" in updates:
            task_record.task_owner_user_id = updates["task_owner_user_id"] or None
            task_record.task_owner_user_ref = _lookup_user_label(updates["task_owner_user_id"]) if updates["task_owner_user_id"] else None
        if "task_owner_user_ref" in updates:
            task_record.task_owner_user_ref = updates["task_owner_user_ref"] or task_record.task_owner_user_ref
        if "due_date" in updates:
            task_record.due_date = _parse_date(updates["due_date"])
        if "task_status" in updates and updates["task_status"]:
            task_record.task_status = updates["task_status"]
        if "resolution_note" in updates:
            task_record.resolution_note = updates["resolution_note"] or None

        if task_record.task_status in {"closed", "cancelled"} and not task_record.resolution_note:
            raise ValueError("A resolution note is required when closing or cancelling a follow-up task.")

        if task_record.task_status in {"closed", "cancelled"}:
            task_record.closed_at = _utcnow()
            task_record.closed_by_user_id = session.login if session else task_record.closed_by_user_id
            task_record.closed_by_user_ref = session.display_name if session else task_record.closed_by_user_ref
        else:
            task_record.closed_at = None
            task_record.closed_by_user_id = None
            task_record.closed_by_user_ref = None

        _refresh_case_payload_tasks(case_record)

        if previous_owner != task_record.task_owner_user_ref:
            _log_database_audit_event(
                db,
                case_record,
                session,
                "followup_task_reassigned",
                entity_type="followup_task",
                entity_ref=task_record.external_task_id,
                payload={"task_owner_changed": True},
            )
        if previous_status != task_record.task_status and task_record.task_status in {"closed", "cancelled"}:
            _log_database_audit_event(
                db,
                case_record,
                session,
                "followup_task_closed",
                entity_type="followup_task",
                entity_ref=task_record.external_task_id,
                payload={
                    "status": task_record.task_status,
                    "resolution_documented": bool(task_record.resolution_note),
                    "closed_by_user_id": task_record.closed_by_user_id,
                },
            )
        elif previous_resolution != task_record.resolution_note and task_record.task_status in {"closed", "cancelled"}:
            _log_database_audit_event(
                db,
                case_record,
                session,
                "followup_task_closed",
                entity_type="followup_task",
                entity_ref=task_record.external_task_id,
                payload={
                    "status": task_record.task_status,
                    "resolution_documented": bool(task_record.resolution_note),
                    "closed_by_user_id": task_record.closed_by_user_id,
                },
            )

        return _task_payload_from_record(task_record), case_record.external_case_id, "database"


def shadow_upsert_odoo_draft_case(payload: OdooDraftCasePayload) -> OdooDraftCasePayload:
    draft = ClinicalDraftCasePayload.model_validate(payload)
    with session_scope() as db:
        stored = _upsert_database_case(
            db,
            draft,
            actor=None,
            log_case_update=False,
            ensure_revision_on_finalized=draft.case_status == "finalized",
        )
    return OdooDraftCasePayload.model_validate(stored.model_dump(mode="json", exclude_none=False))


def get_case_history(external_case_id: str, session: AuthenticatedSession | None = None) -> CaseHistoryPayload | None:
    client = _get_odoo_client(session)
    if client and session:
        payload = client.get_case_history(session.odoo_session_id, external_case_id)
        if payload.get("status") == "not_found":
            return None
        return CaseHistoryPayload.model_validate(payload)

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record:
            return None
        draft = _draft_from_case_record(case_record)
        return _history_from_case_record(case_record) if _session_can_access_draft(draft, session) else None


def get_case_pdf(
    external_case_id: str,
    session: AuthenticatedSession | None = None,
    revision_number: int | None = None,
) -> tuple[bytes, str] | None:
    client = _get_odoo_client(session)
    if client and session:
        if revision_number is None:
            case_payload = client.get_case(session.odoo_session_id, external_case_id)
            if not case_payload or not case_payload.get("pdf_asset_ref"):
                return None
            return client.download_asset(session.odoo_session_id, str(case_payload["pdf_asset_ref"]), _current_pdf_filename(external_case_id))

        history_payload = client.get_case_history(session.odoo_session_id, external_case_id)
        for revision in history_payload.get("revisions") or []:
            if int(revision.get("revisionNumber") or 0) == revision_number and revision.get("pdfAssetRef"):
                return client.download_asset(
                    session.odoo_session_id,
                    str(revision["pdfAssetRef"]),
                    _revision_pdf_filename(external_case_id, revision_number),
                )
        return None

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record:
            return None
        _ensure_session_can_access_draft(_draft_from_case_record(case_record), session)
        if revision_number is None:
            if not case_record.current_pdf_bytes:
                return None
            return case_record.current_pdf_bytes, case_record.current_pdf_filename or _current_pdf_filename(external_case_id)

        revision = db.scalar(
            select(ClinicalCaseRevisionRecord).where(
                ClinicalCaseRevisionRecord.case_id == case_record.id,
                ClinicalCaseRevisionRecord.revision_number == revision_number,
            )
        )
        if not revision or not revision.pdf_bytes:
            return None
        return revision.pdf_bytes, revision.pdf_filename or _revision_pdf_filename(external_case_id, revision_number)


def add_case_image(
    external_case_id: str,
    *,
    file_name: str,
    content_type: str | None,
    image_bytes: bytes,
    caption: str | None = None,
    session: AuthenticatedSession | None = None,
) -> tuple[ClinicalDraftCasePayload | None, CaseStoreMode]:
    safe_name = _safe_attachment_filename(file_name, fallback="case-image")
    normalized_content_type = _normalized_image_content_type(content_type, safe_name)
    _validate_image_upload(image_bytes, normalized_content_type)

    client = _get_odoo_client(session)
    if client and session:
        draft = get_case_draft(external_case_id, session=session)
        if not draft:
            return None, "odoo_bridge"
        _ensure_case_images_editable(draft)

        image_payload = CaseImageAttachmentPayload(
            external_image_id=_new_image_id(),
            file_name=safe_name,
            content_type=normalized_content_type,
            caption=_normalized_optional_text(caption),
            size_bytes=len(image_bytes),
            uploaded_at=_format_datetime(_utcnow()),
            uploaded_by_user_id=session.login,
            uploaded_by_user_ref=session.display_name,
            content_base64=base64.b64encode(image_bytes).decode("ascii"),
        )
        next_payload = draft.model_dump(mode="json", exclude_none=False)
        next_payload["image_attachments"] = [
            _image_payload_without_binary(item).model_dump(mode="json", exclude_none=False)
            for item in draft.image_attachments
        ] + [image_payload.model_dump(mode="json", exclude_none=False)]
        client.sync_case(session.odoo_session_id, next_payload)
        return get_case_draft(external_case_id, session=session), "odoo_bridge"

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record:
            return None, "database"
        draft = _draft_from_case_record(case_record)
        _ensure_session_can_access_draft(draft, session)
        _ensure_case_images_editable(draft)

        image_record = ClinicalCaseImageRecord(
            external_image_id=_new_image_id(),
            case=case_record,
            file_name=safe_name,
            content_type=normalized_content_type,
            caption=_normalized_optional_text(caption),
            size_bytes=len(image_bytes),
            uploaded_at=_utcnow(),
            uploaded_by_user_id=session.login if session else None,
            uploaded_by_user_ref=session.display_name if session else None,
            image_bytes=image_bytes,
        )
        db.add(image_record)
        db.flush()
        _refresh_case_payload_images(case_record)
        _log_database_audit_event(
            db,
            case_record,
            session,
            "case_image_attached",
            entity_type="case_image",
            entity_ref=image_record.external_image_id,
            payload={
                "file_name": image_record.file_name,
                "content_type": image_record.content_type,
                "size_bytes": image_record.size_bytes,
                "has_caption": bool(image_record.caption),
            },
        )
        return _draft_from_case_record(case_record), "database"


def delete_case_image(
    external_case_id: str,
    external_image_id: str,
    session: AuthenticatedSession | None = None,
) -> tuple[ClinicalDraftCasePayload | None, CaseStoreMode]:
    client = _get_odoo_client(session)
    if client and session:
        draft = get_case_draft(external_case_id, session=session)
        if not draft:
            return None, "odoo_bridge"
        _ensure_case_images_editable(draft)
        matching = [item for item in draft.image_attachments if item.external_image_id == external_image_id]
        if not matching:
            return None, "odoo_bridge"

        next_payload = draft.model_dump(mode="json", exclude_none=False)
        next_payload["image_attachments"] = [
            _image_payload_without_binary(item).model_dump(mode="json", exclude_none=False)
            for item in draft.image_attachments
            if item.external_image_id != external_image_id
        ]
        client.sync_case(session.odoo_session_id, next_payload)
        return get_case_draft(external_case_id, session=session), "odoo_bridge"

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record:
            return None, "database"
        draft = _draft_from_case_record(case_record)
        _ensure_session_can_access_draft(draft, session)
        _ensure_case_images_editable(draft)
        image_record = db.scalar(
            select(ClinicalCaseImageRecord).where(
                ClinicalCaseImageRecord.case_id == case_record.id,
                ClinicalCaseImageRecord.external_image_id == external_image_id,
            )
        )
        if not image_record:
            return None, "database"

        deleted_payload = {
            "file_name": image_record.file_name,
            "content_type": image_record.content_type,
            "size_bytes": image_record.size_bytes,
        }
        db.delete(image_record)
        db.flush()
        db.expire(case_record, ["image_attachments"])
        _refresh_case_payload_images(case_record)
        _log_database_audit_event(
            db,
            case_record,
            session,
            "case_image_removed",
            entity_type="case_image",
            entity_ref=external_image_id,
            payload=deleted_payload,
        )
        return _draft_from_case_record(case_record), "database"


def get_case_image(
    external_case_id: str,
    external_image_id: str,
    session: AuthenticatedSession | None = None,
) -> tuple[bytes, str, str] | None:
    client = _get_odoo_client(session)
    if client and session:
        draft = get_case_draft(external_case_id, session=session)
        if not draft:
            return None
        image_payload = next((item for item in draft.image_attachments if item.external_image_id == external_image_id), None)
        if not image_payload or not image_payload.asset_ref:
            return None
        payload, downloaded_name = client.download_asset(
            session.odoo_session_id,
            image_payload.asset_ref,
            image_payload.file_name,
        )
        return payload, downloaded_name or image_payload.file_name, _normalized_image_content_type(image_payload.content_type, image_payload.file_name)

    with session_scope() as db:
        case_record = _database_case_record(db, external_case_id)
        if not case_record or not _session_can_access_draft(_draft_from_case_record(case_record), session):
            return None
        image_record = db.scalar(
            select(ClinicalCaseImageRecord)
            .join(ClinicalCaseRecord)
            .where(
                ClinicalCaseRecord.external_case_id == external_case_id,
                ClinicalCaseImageRecord.external_image_id == external_image_id,
            )
        )
        if not image_record:
            return None
        return image_record.image_bytes, image_record.file_name, image_record.content_type or _normalized_image_content_type(None, image_record.file_name)


def get_dashboard_snapshot(session: AuthenticatedSession | None = None) -> DashboardSnapshot:
    client = _get_odoo_client(session)
    if client and session:
        cases = list_cases(session=session)
        tasks = list_tasks(session=session)
        today = _utcnow().date()
        finalized_today = 0
        for item in cases:
            dt_value = _parse_datetime(item.procedureDatetime)
            if item.status == "finalized" and dt_value and dt_value.date() == today:
                finalized_today += 1
        return DashboardSnapshot(
            activeDrafts=sum(1 for item in cases if item.status in {"draft", "draft_reopened"}),
            openTasks=sum(1 for item in tasks if item.status in {"open", "in_progress"}),
            finalizedToday=finalized_today,
        )

    today_text = _utcnow().date().isoformat()
    cases = list_cases(session=session)
    tasks = list_tasks(session=session)
    return DashboardSnapshot(
        activeDrafts=sum(1 for item in cases if item.status in {"draft", "draft_reopened"}),
        openTasks=sum(1 for item in tasks if item.status in {"open", "in_progress"}),
        finalizedToday=sum(1 for item in cases if item.status == "finalized" and item.procedureDatetime[:10] == today_text),
    )


def get_role_dashboard(session: AuthenticatedSession) -> RoleDashboardPayload:
    """Return the server-selected dashboard priority for the authenticated role."""
    snapshot = get_dashboard_snapshot(session=session)
    ready_count = sum(1 for item in list_cases(session=session) if item.status == "ready_for_signoff")
    counts = {
        "drafts": snapshot.activeDrafts,
        "ready": ready_count,
        "tasks": snapshot.openTasks,
    }
    if session.primary_role == "endoscopist":
        order = ("ready", "drafts", "tasks")
        headline = "Review ready reports first."
    elif session.primary_role == "nurse":
        order = ("drafts", "tasks", "ready")
        headline = "Keep active documentation moving."
    else:
        order = ("tasks", "ready", "drafts")
        headline = "Clear operational delays first."
    labels = {"drafts": "Active drafts", "ready": "Ready for sign-off", "tasks": "Open follow-up"}
    return RoleDashboardPayload(
        role=session.primary_role,
        headline=headline,
        primaryLane=order[0],
        lanes=[DashboardLanePayload(key=key, label=labels[key], count=counts[key]) for key in order],
        finalizedToday=snapshot.finalizedToday,
    )


def _get_odoo_client(session: AuthenticatedSession | None = None) -> OdooBridgeClient | None:
    client = OdooBridgeClient.from_settings()
    if not session and get_case_store_mode() == "odoo_bridge":
        raise OdooBridgeError("A clinician session is required for Odoo-backed case access.")
    return client if client.enabled else None


def _database_case_record(db: Session, external_case_id: str) -> ClinicalCaseRecord | None:
    return db.scalar(select(ClinicalCaseRecord).where(ClinicalCaseRecord.external_case_id == external_case_id))


def _upsert_database_case(
    db: Session,
    draft: ClinicalDraftCasePayload,
    actor: AuthenticatedSession | None,
    *,
    log_case_update: bool = True,
    ensure_revision_on_finalized: bool = False,
) -> ClinicalDraftCasePayload:
    record = _database_case_record(db, draft.external_case_id)
    is_new = record is None
    if record:
        _ensure_session_can_access_draft(_draft_from_case_record(record), actor)
    _ensure_session_can_save_draft(draft, actor)
    before_payload = dict(record.payload_json) if record else None

    working_payload = draft.model_dump(mode="json", exclude_none=False)
    if not record:
        record = ClinicalCaseRecord(
            external_case_id=draft.external_case_id,
            case_status=draft.case_status,
            procedure_type=draft.procedure_type,
            patient_identifier=draft.patient_identifier,
            procedure_datetime=_parse_datetime(draft.procedure_datetime) or _utcnow(),
            facility_unit=draft.facility_unit,
            endoscopist_name=draft.endoscopist_user_ref or draft.endoscopist_user_id or "Unassigned",
            finalized_at=_parse_datetime(draft.finalized_at),
            payload_json=working_payload,
        )
        db.add(record)
        db.flush()

    normalized_tasks = _synchronize_case_tasks(db, record, draft.followup_tasks, actor)
    normalized_images = _synchronize_case_image_metadata(db, record, draft.image_attachments, actor)
    working_payload["followup_tasks"] = [task.model_dump(mode="json", exclude_none=False) for task in normalized_tasks]
    working_payload["image_attachments"] = [image.model_dump(mode="json", exclude_none=False) for image in normalized_images]
    stored_draft = ClinicalDraftCasePayload.model_validate(working_payload)

    record.case_status = stored_draft.case_status
    record.procedure_type = stored_draft.procedure_type
    record.patient_identifier = stored_draft.patient_identifier
    record.procedure_datetime = _parse_datetime(stored_draft.procedure_datetime) or _utcnow()
    record.facility_unit = stored_draft.facility_unit
    record.endoscopist_name = stored_draft.endoscopist_user_ref or stored_draft.endoscopist_user_id or "Unassigned"
    record.finalized_at = _parse_datetime(stored_draft.finalized_at)
    record.payload_json = stored_draft.model_dump(mode="json", exclude_none=False)

    if stored_draft.case_status != "finalized":
        record.current_pdf_bytes = None
        record.current_pdf_filename = None

    if ensure_revision_on_finalized and stored_draft.case_status == "finalized":
        _ensure_final_assets(db, record, stored_draft)
        stored_draft = _draft_from_case_record(record)

    if log_case_update:
        if is_new:
            _log_database_audit_event(
                db,
                record,
                actor,
                "case_created",
                payload={
                    "case_status": stored_draft.case_status,
                    "procedure_type": stored_draft.procedure_type,
                    "has_followup_tasks": bool(stored_draft.followup_tasks),
                },
            )
        else:
            changed_fields = _changed_payload_fields(before_payload or {}, stored_draft.model_dump(mode="json", exclude_none=False))
            if changed_fields:
                _log_database_audit_event(
                    db,
                    record,
                    actor,
                    "case_updated",
                    payload={"changed_fields": changed_fields},
                )

    return _draft_from_case_record(record)


def _synchronize_case_tasks(
    db: Session,
    case_record: ClinicalCaseRecord,
    task_payloads: list[OdooFollowUpTaskPayload],
    actor: AuthenticatedSession | None,
) -> list[OdooFollowUpTaskPayload]:
    existing = {task.external_task_id: task for task in case_record.tasks}
    seen: set[str] = set()

    for incoming in task_payloads:
        normalized = OdooFollowUpTaskPayload.model_validate(incoming.model_dump(mode="json", exclude_none=False))
        external_task_id = normalized.followup_task_id or normalized.external_task_id or _new_task_id()
        normalized = normalized.model_copy(
            update={
                "external_task_id": external_task_id,
                "followup_task_id": external_task_id,
                "task_owner_user_ref": normalized.task_owner_user_ref or _lookup_user_label(normalized.task_owner_user_id),
            }
        )
        seen.add(external_task_id)

        record = existing.get(external_task_id)
        is_new = record is None
        if not record:
            record = ClinicalTaskRecord(
                external_task_id=external_task_id,
                case=case_record,
                task_type=normalized.task_type,
                task_status=normalized.task_status,
            )
            db.add(record)

        previous_owner = record.task_owner_user_ref
        previous_status = record.task_status
        record.task_type = normalized.task_type
        record.task_owner_user_id = normalized.task_owner_user_id
        record.task_owner_user_ref = normalized.task_owner_user_ref or normalized.task_owner_user_id
        record.due_date = _parse_date(normalized.due_date)
        record.task_status = normalized.task_status
        record.resolution_note = normalized.resolution_note

        if record.task_status in {"closed", "cancelled"} and not record.resolution_note:
            raise ValueError("A resolution note is required when closing or cancelling a follow-up task.")

        if record.task_status in {"closed", "cancelled"}:
            record.closed_at = _parse_datetime(normalized.closed_at) or _utcnow()
            record.closed_by_user_id = normalized.closed_by_user_id or (actor.login if actor else None)
            record.closed_by_user_ref = normalized.closed_by_user_ref or (actor.display_name if actor else None)
        else:
            record.closed_at = None
            record.closed_by_user_id = None
            record.closed_by_user_ref = None

        if is_new:
            _log_database_audit_event(
                db,
                case_record,
                actor,
                "followup_task_created",
                entity_type="followup_task",
                entity_ref=external_task_id,
                payload={
                    "task_type": record.task_type,
                    "task_status": record.task_status,
                    "task_owner_assigned": bool(record.task_owner_user_id or record.task_owner_user_ref),
                },
            )
        elif previous_owner != record.task_owner_user_ref:
            _log_database_audit_event(
                db,
                case_record,
                actor,
                "followup_task_reassigned",
                entity_type="followup_task",
                entity_ref=external_task_id,
                payload={"task_owner_changed": True},
            )
        elif previous_status != record.task_status and record.task_status in {"closed", "cancelled"}:
            _log_database_audit_event(
                db,
                case_record,
                actor,
                "followup_task_closed",
                entity_type="followup_task",
                entity_ref=external_task_id,
                payload={
                    "status": record.task_status,
                    "resolution_documented": bool(record.resolution_note),
                    "closed_by_user_id": record.closed_by_user_id,
                },
            )

    for stale_task in list(case_record.tasks):
        if stale_task.external_task_id in seen:
            continue
        _log_database_audit_event(
            db,
            case_record,
            actor,
            "followup_task_deleted",
            entity_type="followup_task",
            entity_ref=stale_task.external_task_id,
            payload={"task_type": stale_task.task_type},
        )
        db.delete(stale_task)

    db.flush()
    current_tasks = db.scalars(
        select(ClinicalTaskRecord).where(ClinicalTaskRecord.case_id == case_record.id).order_by(ClinicalTaskRecord.created_at.asc())
    ).all()
    return [_task_payload_from_record(task) for task in current_tasks]


def _synchronize_case_image_metadata(
    db: Session,
    case_record: ClinicalCaseRecord,
    image_payloads: list[CaseImageAttachmentPayload],
    actor: AuthenticatedSession | None,
) -> list[CaseImageAttachmentPayload]:
    existing = {image.external_image_id: image for image in case_record.image_attachments}
    for incoming in image_payloads:
        normalized = CaseImageAttachmentPayload.model_validate(incoming.model_dump(mode="json", exclude_none=False))
        external_image_id = normalized.external_image_id
        if not external_image_id:
            continue

        image_record = existing.get(external_image_id)
        if image_record:
            image_record.file_name = _safe_attachment_filename(normalized.file_name, fallback=image_record.file_name)
            image_record.content_type = _normalized_image_content_type(normalized.content_type, image_record.file_name)
            image_record.caption = _normalized_optional_text(normalized.caption)
            image_record.size_bytes = normalized.size_bytes or image_record.size_bytes
            image_record.uploaded_at = _parse_datetime(normalized.uploaded_at) or image_record.uploaded_at
            image_record.uploaded_by_user_id = normalized.uploaded_by_user_id or image_record.uploaded_by_user_id
            image_record.uploaded_by_user_ref = normalized.uploaded_by_user_ref or image_record.uploaded_by_user_ref
            continue

        if not normalized.content_base64:
            continue

        try:
            image_bytes = base64.b64decode(normalized.content_base64, validate=True)
        except (ValueError, TypeError):
            continue
        file_name = _safe_attachment_filename(normalized.file_name, fallback="case-image")
        content_type = _normalized_image_content_type(normalized.content_type, file_name)
        _validate_image_upload(image_bytes, content_type)
        db.add(
            ClinicalCaseImageRecord(
                external_image_id=external_image_id,
                case=case_record,
                file_name=file_name,
                content_type=content_type,
                caption=_normalized_optional_text(normalized.caption),
                size_bytes=len(image_bytes),
                uploaded_at=_parse_datetime(normalized.uploaded_at) or _utcnow(),
                uploaded_by_user_id=normalized.uploaded_by_user_id or (actor.login if actor else None),
                uploaded_by_user_ref=normalized.uploaded_by_user_ref or (actor.display_name if actor else None),
                image_bytes=image_bytes,
            )
        )

    db.flush()
    current_images = db.scalars(
        select(ClinicalCaseImageRecord)
        .where(ClinicalCaseImageRecord.case_id == case_record.id)
        .order_by(ClinicalCaseImageRecord.uploaded_at.asc(), ClinicalCaseImageRecord.created_at.asc())
    ).all()
    return [_image_payload_from_record(case_record.external_case_id, image) for image in current_images]


def _draft_from_case_record(record: ClinicalCaseRecord) -> ClinicalDraftCasePayload:
    payload = dict(record.payload_json or {})
    payload["followup_tasks"] = [
        _task_payload_from_record(task).model_dump(mode="json", exclude_none=False)
        for task in sorted(record.tasks, key=lambda item: item.created_at)
    ]
    payload["image_attachments"] = [
        _image_payload_from_record(record.external_case_id, image).model_dump(mode="json", exclude_none=False)
        for image in sorted(record.image_attachments, key=lambda item: item.uploaded_at or item.created_at)
    ]
    payload["pdf_asset_ref"] = _current_pdf_path(record.external_case_id) if record.current_pdf_bytes else None
    return ClinicalDraftCasePayload.model_validate(payload)


def _summary_from_case_record(record: ClinicalCaseRecord) -> CaseSummary:
    draft = _draft_from_case_record(record)
    return CaseSummary(
        id=draft.external_case_id,
        patientIdentifier=draft.patient_identifier,
        procedureType=draft.procedure_type,
        status=draft.case_status,
        procedureDatetime=draft.procedure_datetime,
        endoscopistName=draft.endoscopist_user_ref or draft.endoscopist_user_id or "Unassigned",
    )


def _task_from_case_record(record: ClinicalTaskRecord) -> FollowUpTask:
    return FollowUpTask(
        id=record.external_task_id,
        caseId=record.case.external_case_id,
        type=record.task_type,
        status=record.task_status,
        ownerName=record.task_owner_user_ref or record.task_owner_user_id or "Unassigned",
        dueDate=record.due_date.isoformat() if record.due_date else None,
    )


def _task_payload_from_record(record: ClinicalTaskRecord) -> OdooFollowUpTaskPayload:
    return OdooFollowUpTaskPayload(
        external_task_id=record.external_task_id,
        followup_task_id=record.external_task_id,
        task_type=record.task_type,
        task_owner_user_id=record.task_owner_user_id,
        task_owner_user_ref=record.task_owner_user_ref,
        due_date=record.due_date.isoformat() if record.due_date else None,
        task_status=record.task_status,
        resolution_note=record.resolution_note,
        closed_at=_format_datetime(record.closed_at),
        closed_by_user_id=record.closed_by_user_id,
        closed_by_user_ref=record.closed_by_user_ref,
    )


def _image_payload_from_record(external_case_id: str, record: ClinicalCaseImageRecord) -> CaseImageAttachmentPayload:
    return CaseImageAttachmentPayload(
        external_image_id=record.external_image_id,
        file_name=record.file_name,
        content_type=record.content_type,
        caption=record.caption,
        size_bytes=record.size_bytes,
        uploaded_at=_format_datetime(record.uploaded_at),
        uploaded_by_user_id=record.uploaded_by_user_id,
        uploaded_by_user_ref=record.uploaded_by_user_ref,
        asset_ref=_case_image_path(external_case_id, record.external_image_id),
    )


def _history_from_case_record(record: ClinicalCaseRecord) -> CaseHistoryPayload:
    revisions = [
        CaseRevisionPayload(
            revisionNumber=item.revision_number,
            finalizedAt=_format_datetime(item.finalized_at),
            finalizedBy=item.finalized_by_user_ref,
            templateVersion=item.template_version,
            pdfAssetRef=_revision_pdf_path(record.external_case_id, item.revision_number) if item.pdf_bytes else None,
            reportNarrativeSnapshot=item.report_narrative_snapshot,
        )
        for item in sorted(record.revisions, key=lambda row: row.revision_number, reverse=True)
    ]
    audit_events = [
        AuditEventPayload(
            id=item.id,
            createdAt=_format_datetime(item.created_at) or "",
            actorDisplayName=item.actor_display_name,
            actorRole=item.actor_role,
            eventType=item.event_type,
            entityType=item.entity_type,
            entityRef=item.entity_ref,
            reason=item.reason,
            payload=item.payload_json,
        )
        for item in sorted(record.audit_events, key=lambda row: row.created_at, reverse=True)
    ]
    return CaseHistoryPayload(caseId=record.external_case_id, revisions=revisions, auditEvents=audit_events)


def _ensure_final_assets(db: Session, record: ClinicalCaseRecord, draft: ClinicalDraftCasePayload) -> None:
    if record.current_pdf_bytes and record.revisions:
        return

    narrative = draft.report_narrative_snapshot or _local_narrative(draft)
    finalized_at = _parse_datetime(draft.finalized_at) or _utcnow()
    pdf_bytes = _render_pdf_bytes(
        title=f"Procedure Report - {draft.external_case_id}",
        subtitle=f"{draft.patient_identifier} | {draft.procedure_type.upper()}",
        narrative=narrative,
    )
    filename = _current_pdf_filename(draft.external_case_id)

    next_payload = draft.model_dump(mode="json", exclude_none=False)
    next_payload["template_version"] = draft.template_version or LOCAL_TEMPLATE_VERSION
    next_payload["report_narrative_snapshot"] = narrative
    next_payload["pdf_asset_ref"] = _current_pdf_path(draft.external_case_id)
    next_payload["finalized_at"] = _format_datetime(finalized_at)

    record.finalized_at = finalized_at
    record.current_pdf_bytes = pdf_bytes
    record.current_pdf_filename = filename
    record.payload_json = next_payload

    if not record.revisions:
        record.revisions.append(
            ClinicalCaseRevisionRecord(
                revision_number=1,
                finalized_at=finalized_at,
                finalized_by_user_id=draft.finalized_by_user_id,
                finalized_by_user_ref=draft.finalized_by_user_ref,
                template_version=next_payload["template_version"],
                report_narrative_snapshot=narrative,
                pdf_bytes=pdf_bytes,
                pdf_filename=filename,
                snapshot_json=next_payload,
            )
        )


def _create_final_assets(db: Session, record: ClinicalCaseRecord, draft: ClinicalDraftCasePayload) -> None:
    narrative = draft.report_narrative_snapshot or _local_narrative(draft)
    finalized_at = _parse_datetime(draft.finalized_at) or _utcnow()
    pdf_bytes = _render_pdf_bytes(
        title=f"Procedure Report - {draft.external_case_id}",
        subtitle=f"{draft.patient_identifier} | {draft.procedure_type.upper()}",
        narrative=narrative,
    )
    filename = _current_pdf_filename(draft.external_case_id)

    record.finalized_at = finalized_at
    record.current_pdf_bytes = pdf_bytes
    record.current_pdf_filename = filename
    next_payload = draft.model_dump(mode="json", exclude_none=False)
    next_payload["pdf_asset_ref"] = _current_pdf_path(draft.external_case_id)
    record.payload_json = next_payload

    next_revision = _latest_revision_number(record) + 1
    record.revisions.append(
        ClinicalCaseRevisionRecord(
            revision_number=next_revision,
            finalized_at=finalized_at,
            finalized_by_user_id=draft.finalized_by_user_id,
            finalized_by_user_ref=draft.finalized_by_user_ref,
            template_version=draft.template_version,
            report_narrative_snapshot=narrative,
            pdf_bytes=pdf_bytes,
            pdf_filename=filename,
            snapshot_json=next_payload,
        )
    )
    db.flush()


def _latest_revision_number(record: ClinicalCaseRecord) -> int:
    return max((item.revision_number for item in record.revisions), default=0)


def _refresh_case_payload_tasks(record: ClinicalCaseRecord) -> None:
    payload = dict(record.payload_json or {})
    payload["followup_tasks"] = [
        _task_payload_from_record(task).model_dump(mode="json", exclude_none=False)
        for task in sorted(record.tasks, key=lambda item: item.created_at)
    ]
    payload["image_attachments"] = [
        _image_payload_from_record(record.external_case_id, image).model_dump(mode="json", exclude_none=False)
        for image in sorted(record.image_attachments, key=lambda item: item.uploaded_at or item.created_at)
    ]
    payload["pdf_asset_ref"] = _current_pdf_path(record.external_case_id) if record.current_pdf_bytes else None
    record.payload_json = payload


def _refresh_case_payload_images(record: ClinicalCaseRecord) -> None:
    db = object_session(record)
    payload = dict(record.payload_json or {})
    payload["followup_tasks"] = [
        _task_payload_from_record(task).model_dump(mode="json", exclude_none=False)
        for task in sorted(record.tasks, key=lambda item: item.created_at)
    ]
    current_images = (
        db.scalars(
            select(ClinicalCaseImageRecord)
            .where(ClinicalCaseImageRecord.case_id == record.id)
            .order_by(ClinicalCaseImageRecord.uploaded_at.asc(), ClinicalCaseImageRecord.created_at.asc())
        ).all()
        if db
        else list(record.image_attachments)
    )
    payload["image_attachments"] = [
        _image_payload_from_record(record.external_case_id, image).model_dump(mode="json", exclude_none=False)
        for image in current_images
    ]
    payload["pdf_asset_ref"] = _current_pdf_path(record.external_case_id) if record.current_pdf_bytes else None
    record.payload_json = payload


def _log_database_audit_event(
    db: Session,
    case_record: ClinicalCaseRecord,
    actor: AuthenticatedSession | None,
    event_type: str,
    *,
    entity_type: str = "case",
    entity_ref: str | None = None,
    reason: str | None = None,
    payload: dict | list | str | None = None,
) -> None:
    db.add(
        ClinicalAuditEventRecord(
            case=case_record,
            actor_user_id=actor.login if actor else "system",
            actor_display_name=actor.display_name if actor else "System Seeder",
            actor_role=actor.primary_role if actor else "workspace_admin",
            event_type=event_type,
            entity_type=entity_type,
            entity_ref=entity_ref,
            reason=reason,
            payload_json=payload,
        )
    )


def _build_lookups_from_payloads(
    payloads: list[ClinicalDraftCasePayload],
    session: AuthenticatedSession | None = None,
) -> ClinicalLookupsPayload:
    return ClinicalLookupsPayload(
        facilities=_facility_lookups(payloads, session=session),
        facilityUnits=_facility_unit_lookups(payloads, session=session),
        endoscopists=_clinician_lookups("endoscopist", payloads, session=session),
        nurses=_clinician_lookups("nurse", payloads, session=session),
        referrerServices=_referrer_service_lookups(payloads),
    )


def _facility_lookups(
    payloads: list[ClinicalDraftCasePayload],
    session: AuthenticatedSession | None = None,
) -> list[FacilityLookupOption]:
    allowed_codes = _session_facility_codes(session)
    by_code = {
        item["code"]: item["label"]
        for item in DEFAULT_FACILITIES
        if _session_can_use_facility_code(str(item["code"]), session, allowed_codes=allowed_codes)
    }
    for payload in payloads:
        facility_code = payload.facility_code or _facility_code_from_label(payload.facility_unit)
        facility_label = _facility_label_from_unit(payload.facility_unit)
        if facility_code and facility_label and _session_can_use_facility_code(facility_code, session, allowed_codes=allowed_codes):
            by_code[facility_code] = facility_label
    return [FacilityLookupOption(code=code, label=by_code[code]) for code in sorted(by_code, key=lambda item: by_code[item])]


def _facility_unit_lookups(
    payloads: list[ClinicalDraftCasePayload],
    session: AuthenticatedSession | None = None,
) -> list[FacilityUnitLookupOption]:
    allowed_codes = _session_facility_codes(session)
    by_code = {
        item["code"]: item
        for item in DEFAULT_FACILITY_UNITS
        if _session_can_use_facility_code(str(item.get("facilityCode") or ""), session, allowed_codes=allowed_codes)
    }
    for payload in payloads:
        unit_code = payload.facility_unit_code or payload.facility_unit
        if not unit_code or not payload.facility_unit:
            continue
        facility_code = payload.facility_code or _facility_code_from_label(payload.facility_unit)
        if not _session_can_use_facility_code(facility_code, session, allowed_codes=allowed_codes):
            continue
        by_code[unit_code] = {
            "code": unit_code,
            "label": payload.facility_unit,
            "facilityCode": facility_code,
        }
    return [FacilityUnitLookupOption(**item) for item in sorted(by_code.values(), key=lambda item: item["label"])]


def _clinician_lookups(
    role: WorkspaceRole,
    payloads: list[ClinicalDraftCasePayload],
    session: AuthenticatedSession | None = None,
) -> list[ClinicianLookupOption]:
    allowed_codes = _session_facility_codes(session)
    by_user_id = {
        item["userId"]: dict(item)
        for item in DEFAULT_CLINICIANS
        if item["role"] == role and _session_can_use_any_facility_code(item.get("facilityCodes") or [], session, allowed_codes=allowed_codes)
    }
    for payload in payloads:
        facility_code = payload.facility_code or _facility_code_from_label(payload.facility_unit)
        if not _session_can_use_facility_code(facility_code, session, allowed_codes=allowed_codes):
            continue
        if role == "endoscopist":
            user_id = payload.endoscopist_user_id
            label = payload.endoscopist_user_ref or payload.endoscopist_user_id
        else:
            user_id = payload.assistant_nurse_user_id
            label = payload.assistant_nurse_user_ref or payload.assistant_nurse_user_id
        if user_id:
            next_payload = dict(by_user_id.get(user_id) or {"userId": user_id, "label": label or user_id, "role": role})
            next_payload["label"] = label or next_payload["label"]
            if facility_code:
                facility_codes = set(next_payload.get("facilityCodes") or [])
                facility_codes.add(facility_code)
                next_payload["facilityCodes"] = sorted(facility_codes)
            if role == "nurse" and payload.endoscopist_user_id:
                endoscopist_ids = set(next_payload.get("endoscopistUserIds") or [])
                endoscopist_ids.add(payload.endoscopist_user_id)
                next_payload["endoscopistUserIds"] = sorted(endoscopist_ids)
            by_user_id[user_id] = next_payload
    return [ClinicianLookupOption(**item) for item in sorted(by_user_id.values(), key=lambda item: item["label"])]


def _referrer_service_lookups(payloads: list[ClinicalDraftCasePayload]) -> list[ValueLookupOption]:
    by_value = {item["value"]: item["label"] for item in DEFAULT_REFERRER_SERVICES}
    for payload in payloads:
        if payload.referrer_service:
            by_value[payload.referrer_service] = payload.referrer_service
    return [ValueLookupOption(value=value, label=by_value[value]) for value in sorted(by_value)]


def _summary_from_remote(payload: dict) -> CaseSummary:
    return CaseSummary(
        id=str(payload.get("external_case_id") or payload.get("case_id") or ""),
        patientIdentifier=str(payload.get("patient_identifier") or ""),
        procedureType=payload.get("procedure_type") or "colonoscopy",
        status=payload.get("case_status") or "draft",
        procedureDatetime=str(payload.get("procedure_datetime") or ""),
        endoscopistName=str(payload.get("endoscopist_user_ref") or payload.get("endoscopist_user_id") or "Unassigned"),
    )


def _task_from_remote(payload: dict) -> FollowUpTask:
    return FollowUpTask(
        id=str(payload.get("followup_task_id") or payload.get("external_task_id") or ""),
        caseId=str(payload.get("external_case_id") or payload.get("case_id") or ""),
        type=payload.get("task_type") or "pathology_review",
        status=payload.get("task_status") or "open",
        ownerName=str(payload.get("task_owner_user_ref") or payload.get("task_owner_user_id") or "Unassigned"),
        dueDate=payload.get("due_date"),
    )


def _draft_value(draft: ClinicalDraftCasePayload, field_name: str, default=None):
    if hasattr(draft, field_name):
        return getattr(draft, field_name)
    extras = getattr(draft, "model_extra", None) or {}
    return extras.get(field_name, default)


def _session_facility_codes(session: AuthenticatedSession | None) -> set[str]:
    if not session or session.primary_role == "workspace_admin":
        return set()
    return {code.strip() for code in session.facility_codes if code and code.strip()}


def _session_can_use_facility_code(
    facility_code: str | None,
    session: AuthenticatedSession | None,
    *,
    allowed_codes: set[str] | None = None,
) -> bool:
    if not session or session.primary_role == "workspace_admin":
        return True
    scoped_codes = allowed_codes if allowed_codes is not None else _session_facility_codes(session)
    return bool(facility_code and facility_code in scoped_codes)


def _session_can_use_any_facility_code(
    facility_codes: list[str],
    session: AuthenticatedSession | None,
    *,
    allowed_codes: set[str] | None = None,
) -> bool:
    if not session or session.primary_role == "workspace_admin":
        return True
    scoped_codes = allowed_codes if allowed_codes is not None else _session_facility_codes(session)
    return bool(scoped_codes.intersection({code for code in facility_codes if code}))


def _draft_facility_code(draft: ClinicalDraftCasePayload) -> str | None:
    return draft.facility_code or _facility_code_from_label(draft.facility_unit)


def _session_can_access_draft(draft: ClinicalDraftCasePayload, session: AuthenticatedSession | None) -> bool:
    if not session or session.primary_role == "workspace_admin":
        return True
    if not _session_can_use_facility_code(_draft_facility_code(draft), session):
        return False
    if session.primary_role == "operations_admin":
        return True

    actor_refs = {session.login, session.user_id, session.display_name}
    assigned_refs = {
        draft.endoscopist_user_id,
        draft.endoscopist_user_ref,
        draft.assistant_nurse_user_id,
        draft.assistant_nurse_user_ref,
    }
    return bool({str(item).strip() for item in actor_refs if item}.intersection({str(item).strip() for item in assigned_refs if item}))


def _ensure_session_can_access_draft(draft: ClinicalDraftCasePayload, session: AuthenticatedSession | None) -> None:
    if not _session_can_access_draft(draft, session):
        raise PermissionError("You do not have access to this facility or assigned case.")


def _ensure_session_can_save_draft(draft: ClinicalDraftCasePayload, session: AuthenticatedSession | None) -> None:
    _ensure_session_can_access_draft(draft, session)


def _local_case_action_validation_errors(draft: ClinicalDraftCasePayload) -> list[str]:
    errors: list[str] = []
    if not draft.patient_identifier:
        errors.append("Patient identifier is required.")
    if not draft.procedure_datetime:
        errors.append("Procedure date and time are required.")
    if not (draft.endoscopist_user_id or draft.endoscopist_user_ref):
        errors.append("An endoscopist must be assigned.")
    if not _draft_value(draft, "indication"):
        errors.append("Indication is required.")
    if not _draft_value(draft, "consent_documented", False):
        errors.append("Consent must be documented before sign-off.")
    if not _draft_value(draft, "patient_identity_verified", False):
        errors.append("Two patient identifiers must be verified before sign-off.")
    if not _draft_value(draft, "team_pause_completed", False):
        errors.append("Team pause must be completed before sign-off.")
    if not _draft_value(draft, "sedation_anesthesia"):
        errors.append("Sedation or anesthesia status is required.")
    if not _local_procedure_impression(draft):
        errors.append("A procedure impression is required.")
    if not _local_communication_plan_present(draft):
        errors.append("A communication or follow-up plan is required.")
    if _local_requires_followup(draft) and not draft.followup_tasks:
        errors.append("At least one follow-up task is required for cases with specimens or pending pathology.")

    if draft.procedure_type == "colonoscopy":
        if not _draft_value(draft, "prep_quality"):
            errors.append("Bowel prep quality is required for colonoscopy sign-off.")
        if any(_draft_value(draft, field) is None for field in ("bbps_right", "bbps_transverse", "bbps_left")):
            errors.append("Record BBPS for the right, transverse, and left colon before sign-off.")
        if not _draft_value(draft, "cecum_reached", False) and not _draft_value(draft, "technical_limitation_note"):
            errors.append("Record cecal completion or document why the cecum was not reached.")
        if _draft_value(draft, "cecum_reached", False):
            if not _draft_value(draft, "cecal_landmark_appendiceal_orifice", False) or not _draft_value(draft, "cecal_landmark_ileocecal_valve", False):
                errors.append("Document both cecal landmarks when the cecum is reached.")
            if not _draft_value(draft, "photo_cecum", False):
                errors.append("Capture cecal photodocumentation when the cecum is reached.")
        if not draft.segment_exam:
            errors.append("At least one segment examination row is required.")
    if _draft_value(draft, "adverse_event_during_procedure", False) and not _draft_value(draft, "adverse_event_note"):
        errors.append("Document the adverse event, response, and escalation plan.")
    elif draft.procedure_type == "egd":
        if not _draft_value(draft, "egd_extent_reached"):
            errors.append("Extent reached is required for EGD sign-off.")
        if not _local_egd_exam_documented(draft):
            errors.append("Document the key EGD examination findings before sign-off.")
        if _draft_value(draft, "egd_specimens_obtained", False) and not draft.specimens:
            errors.append("Add specimen records for an EGD with specimens obtained.")
    elif draft.procedure_type == "ercp":
        if not _draft_value(draft, "ercp_papilla_status"):
            errors.append("Papilla status is required for ERCP sign-off.")
        if not _draft_value(draft, "ercp_technical_success"):
            errors.append("Technical success is required for ERCP sign-off.")
        if not _draft_value(draft, "ercp_drainage_achieved"):
            errors.append("Drainage outcome is required for ERCP sign-off.")
        if not _draft_value(draft, "ercp_radiation_protection_verified", False):
            errors.append("Radiation protection verification is required for ERCP sign-off.")
    elif draft.procedure_type == "eus":
        if not _draft_value(draft, "eus_route"):
            errors.append("EUS route is required for sign-off.")
        if not _draft_value(draft, "eus_echoendoscope"):
            errors.append("Echoendoscope type is required for EUS sign-off.")
        if not _draft_value(draft, "eus_intent"):
            errors.append("EUS intent is required for sign-off.")
        if not _draft_value(draft, "eus_relevant_anatomy_documented"):
            errors.append("Relevant anatomy documentation status is required for EUS sign-off.")
        if (_draft_value(draft, "eus_fna_performed", False) or _draft_value(draft, "eus_fnb_performed", False)) and not _draft_value(
            draft, "eus_passes_count"
        ):
            errors.append("Document pass count for EUS tissue acquisition before sign-off.")
        if (_draft_value(draft, "eus_fna_performed", False) or _draft_value(draft, "eus_fnb_performed", False)) and not _draft_value(
            draft, "eus_adequacy_status"
        ):
            errors.append("Adequacy status is required when EUS tissue acquisition is performed.")

    return errors


def _local_validation_summary(errors: list[str]) -> str:
    if not errors:
        return "Ready for sign-off."
    return "\n".join(["Sign-off blocked until these issues are resolved:"] + [f"- {item}" for item in errors])


def _local_procedure_impression(draft: ClinicalDraftCasePayload) -> str | None:
    if draft.procedure_type == "egd":
        return _draft_value(draft, "egd_impression")
    if draft.procedure_type == "ercp":
        return _draft_value(draft, "ercp_impression")
    if draft.procedure_type == "eus":
        return _draft_value(draft, "eus_impression")
    return _draft_value(draft, "impression")


def _local_communication_plan_present(draft: ClinicalDraftCasePayload) -> bool:
    if draft.procedure_type == "egd":
        return any(
            [
                _draft_value(draft, "egd_followup_surveillance"),
                _draft_value(draft, "egd_h_pylori_plan"),
                _draft_value(draft, "egd_medication_therapy"),
                _draft_value(draft, "egd_result_communication_planned", False),
                _draft_value(draft, "egd_referrer_communication_planned", False),
            ]
        )
    if draft.procedure_type == "ercp":
        return any(
            [
                _draft_value(draft, "ercp_repeat_intervention"),
                _draft_value(draft, "ercp_repeat_intervention_timing"),
                _draft_value(draft, "ercp_patient_contact_note"),
                _draft_value(draft, "ercp_tracking_register_entered", False),
                _draft_value(draft, "ercp_temporary_stent", False),
            ]
        )
    if draft.procedure_type == "eus":
        return any(
            [
                _draft_value(draft, "eus_clinical_plan"),
                _draft_value(draft, "eus_followup_imaging_or_procedure"),
                _draft_value(draft, "eus_multidisciplinary_referral"),
                _draft_value(draft, "informed_patient", False),
                _draft_value(draft, "informed_referrer", False),
            ]
        )
    return any(
        [
            _draft_value(draft, "adverse_event_plan"),
            _draft_value(draft, "surveillance_interval_value"),
            _draft_value(draft, "informed_patient", False),
            _draft_value(draft, "informed_referrer", False),
            _draft_value(draft, "written_instructions_given", False),
        ]
    )


def _local_requires_followup(draft: ClinicalDraftCasePayload) -> bool:
    return bool(draft.specimens) or _draft_value(draft, "pathology_status") == "pending_tracking_required"


def _local_egd_exam_documented(draft: ClinicalDraftCasePayload) -> bool:
    return any(
        [
            _draft_value(draft, "egd_esophagus_finding"),
            _draft_value(draft, "egd_stomach_finding"),
            _draft_value(draft, "egd_duodenum_finding"),
            _draft_value(draft, "egd_exam_esophagus_note"),
            _draft_value(draft, "egd_exam_z_line_note"),
            _draft_value(draft, "egd_exam_cardia_fundus_note"),
            _draft_value(draft, "egd_exam_gastric_body_note"),
            _draft_value(draft, "egd_exam_incisura_antrum_note"),
            _draft_value(draft, "egd_exam_pylorus_note"),
            _draft_value(draft, "egd_exam_duodenal_bulb_note"),
            _draft_value(draft, "egd_exam_second_duodenum_note"),
        ]
    )


def _local_narrative(draft: ClinicalDraftCasePayload) -> str:
    impression = _local_procedure_impression(draft) or "Impression pending."
    return f"{draft.patient_identifier} {draft.procedure_type.upper()} on {draft.procedure_datetime}. {impression}"


def _changed_payload_fields(before: dict, after: dict) -> list[str]:
    ignore_fields = {"report_narrative_snapshot", "validation_summary", "pdf_asset_ref"}
    return sorted(field for field in set(before) | set(after) if field not in ignore_fields and before.get(field) != after.get(field))


def _facility_label_from_unit(facility_unit: str | None) -> str | None:
    if not facility_unit:
        return None
    if " / " in facility_unit:
        return facility_unit.split(" / ", 1)[0]
    if facility_unit.endswith(" Bay"):
        return "Day Procedure"
    return facility_unit


def _facility_code_from_label(label: str | None) -> str | None:
    if not label:
        return None
    normalized = label.strip().lower()
    if "main" in normalized:
        return "MAIN"
    if "day" in normalized:
        return "DAY"
    if "therapeutic" in normalized:
        return "THER"
    return label.strip().upper().replace(" ", "-")


def _find_unit_option(code_or_label: str | None) -> dict[str, str] | None:
    if not code_or_label:
        return None
    normalized = code_or_label.strip().lower()
    for option in DEFAULT_FACILITY_UNITS:
        if option["code"].lower() == normalized or option["label"].lower() == normalized:
            return option
    return None


def _infer_facility_code(endoscopist_user_id: str | None, session: AuthenticatedSession | None) -> str | None:
    if not endoscopist_user_id:
        return None
    for clinician in DEFAULT_CLINICIANS:
        if clinician["role"] == "endoscopist" and clinician["userId"] == endoscopist_user_id:
            codes = {str(code).strip() for code in clinician.get("facilityCodes", []) if str(code).strip()}
            return next(iter(codes)) if len(codes) == 1 else None
    if session and session.login == endoscopist_user_id:
        codes = _session_facility_codes(session)
        return next(iter(codes)) if len(codes) == 1 else None
    return None


def _lookup_user_label(user_id: str | None) -> str | None:
    if not user_id:
        return None
    for user in DEFAULT_CLINICIANS:
        if user["userId"] == user_id:
            return user["label"]
    return user_id


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_date(value: str | date | None) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if "T" in raw:
        raw = raw.split("T", 1)[0]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _format_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_task_id() -> str:
    return f"task-{uuid4().hex[:12]}"


def _new_image_id() -> str:
    return f"img-{uuid4().hex[:12]}"


def _safe_attachment_filename(file_name: str | None, fallback: str) -> str:
    cleaned = str(file_name or "").replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = cleaned.replace("\r", "").replace("\n", "").replace('"', "").strip()
    return cleaned[:255] or fallback


def _normalized_optional_text(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _image_payload_without_binary(payload: CaseImageAttachmentPayload) -> CaseImageAttachmentPayload:
    return payload.model_copy(update={"content_base64": None})


def _normalized_image_content_type(content_type: str | None, file_name: str | None) -> str:
    normalized = str(content_type or "").split(";", 1)[0].strip().lower()
    if normalized == "image/jpg":
        normalized = "image/jpeg"
    if not normalized or normalized == "application/octet-stream":
        guessed, _ = mimetypes.guess_type(file_name or "")
        normalized = (guessed or "image/jpeg").lower()
    if normalized == "image/jpg":
        normalized = "image/jpeg"
    return normalized


def _validate_image_upload(image_bytes: bytes, content_type: str) -> None:
    if not image_bytes:
        raise ValueError("Attach a non-empty image file.")
    if len(image_bytes) > MAX_CASE_IMAGE_BYTES:
        raise ValueError("Image uploads are limited to 10 MB.")
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValueError("Only JPEG, PNG, WebP, GIF, BMP, and TIFF images can be attached.")
    if not _image_signature_matches(image_bytes, content_type):
        raise ValueError("The uploaded file does not match the selected image type.")


def _image_signature_matches(image_bytes: bytes, content_type: str) -> bool:
    signatures = {
        "image/bmp": lambda payload: payload.startswith(b"BM"),
        "image/gif": lambda payload: payload.startswith((b"GIF87a", b"GIF89a")),
        "image/jpeg": lambda payload: payload.startswith(b"\xff\xd8\xff"),
        "image/png": lambda payload: payload.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/tiff": lambda payload: payload.startswith((b"II*\x00", b"MM\x00*")),
        "image/webp": lambda payload: len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP",
    }
    matcher = signatures.get(content_type)
    return bool(matcher and matcher(image_bytes))


def _ensure_case_images_editable(draft: ClinicalDraftCasePayload) -> None:
    if draft.case_status == "finalized":
        raise PermissionError("Finalized cases are locked. Reopen the case before changing attached images.")


def _current_pdf_path(external_case_id: str) -> str:
    return f"/api/cases/{external_case_id}/pdf"


def _case_image_path(external_case_id: str, external_image_id: str) -> str:
    return f"/api/cases/{external_case_id}/images/{external_image_id}"


def _revision_pdf_path(external_case_id: str, revision_number: int) -> str:
    return f"/api/cases/{external_case_id}/revisions/{revision_number}/pdf"


def _current_pdf_filename(external_case_id: str) -> str:
    return f"{external_case_id}-final-report.pdf"


def _revision_pdf_filename(external_case_id: str, revision_number: int) -> str:
    return f"{external_case_id}-revision-{revision_number}.pdf"


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _render_pdf_bytes(title: str, subtitle: str, narrative: str) -> bytes:
    wrapped_lines = [title, subtitle, ""]
    for paragraph in narrative.splitlines() or [""]:
        wrapped_lines.extend(textwrap.wrap(paragraph, width=88) or [""])

    page_lines = 38
    pages = [wrapped_lines[index : index + page_lines] for index in range(0, len(wrapped_lines), page_lines)] or [[]]

    objects: list[bytes] = []
    pages_object_id = 2
    font_object_id = 3

    for lines in pages:
        commands = ["BT", "/F1 12 Tf", "40 780 Td", "16 TL"]
        first_line = True
        for line in lines:
            escaped = _escape_pdf_text(line)
            if first_line:
                commands.append(f"({escaped}) Tj")
                first_line = False
            else:
                commands.append(f"T* ({escaped}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", "replace")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream")
        content_object_id = len(objects) + 3
        objects.append(
            f"<< /Type /Page /Parent {pages_object_id} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_object_id} 0 R >> >> /Contents {content_object_id} 0 R >>".encode(
                "ascii"
            )
        )

    page_ids = [index for index in range(5, len(objects) + 4, 2)]
    pages_dict = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] >>".encode("ascii")

    pdf_objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        pages_dict,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        *objects,
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(pdf_objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(pdf_objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return bytes(output)
