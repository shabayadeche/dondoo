from secrets import compare_digest
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile, status

from app.auth import get_authenticated_session
from app.core.settings import get_settings
from app.integrations.odoo_bridge import OdooBridgeApplicationError, OdooBridgeError
from app.repositories.cases import (
    add_case_image,
    create_start_case,
    delete_case_image,
    get_lookups,
    get_patient_relationship,
    search_patients,
    get_case_draft,
    get_case_history,
    get_case_image,
    get_case_pdf,
    list_cases,
    list_tasks,
    perform_case_action,
    save_case_draft,
    shadow_upsert_odoo_draft_case,
    update_followup_task,
)
from app.schemas import (
    CaseActionPayload,
    CaseActionType,
    CaseDraftWriteResponse,
    CaseHistoryPayload,
    CaseSummary,
    ClinicalLookupsPayload,
    ClinicalDraftCasePayload,
    FollowUpTask,
    FollowUpTaskUpdatePayload,
    FollowUpTaskWriteResponse,
    OdooDraftCasePayload,
    StartCasePayload,
    PatientRelationshipSuggestion,
    PatientLookupOption,
)

router = APIRouter()


def _raise_bridge_http_error(exc: OdooBridgeError) -> None:
    if isinstance(exc, OdooBridgeApplicationError):
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


def _pdf_response(payload: bytes, filename: str) -> Response:
    safe_filename = filename.replace("\r", "").replace("\n", "").replace('"', "").strip() or "clinical-report.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{quote(safe_filename)}",
        },
    )


def _binary_attachment_response(payload: bytes, filename: str, media_type: str) -> Response:
    safe_filename = filename.replace("\r", "").replace("\n", "").replace('"', "").strip() or "case-attachment"
    return Response(
        content=payload,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename=\"{safe_filename}\"; filename*=UTF-8''{quote(safe_filename)}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/cases", response_model=list[CaseSummary])
def get_cases(session=Depends(get_authenticated_session)) -> list[CaseSummary]:
    try:
        return list_cases(session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)


@router.get("/cases/{external_case_id}", response_model=ClinicalDraftCasePayload)
def get_case(external_case_id: str, session=Depends(get_authenticated_session)) -> ClinicalDraftCasePayload:
    try:
        payload = get_case_draft(external_case_id, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical case not found.")
    return payload


@router.get("/cases/{external_case_id}/history", response_model=CaseHistoryPayload)
def get_case_history_view(external_case_id: str, session=Depends(get_authenticated_session)) -> CaseHistoryPayload:
    try:
        payload = get_case_history(external_case_id, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical case not found.")
    return payload


@router.get("/cases/{external_case_id}/pdf")
def get_case_pdf_view(external_case_id: str, session=Depends(get_authenticated_session)) -> Response:
    try:
        pdf_payload = get_case_pdf(external_case_id, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not pdf_payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finalized PDF not found.")

    payload, filename = pdf_payload
    return _pdf_response(payload, filename)


@router.get("/cases/{external_case_id}/revisions/{revision_number}/pdf")
def get_revision_pdf_view(external_case_id: str, revision_number: int, session=Depends(get_authenticated_session)) -> Response:
    try:
        pdf_payload = get_case_pdf(external_case_id, session=session, revision_number=revision_number)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not pdf_payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision PDF not found.")

    payload, filename = pdf_payload
    return _pdf_response(payload, filename)


@router.post("/cases/{external_case_id}/images", response_model=CaseDraftWriteResponse, status_code=status.HTTP_201_CREATED)
async def upload_case_image_view(
    external_case_id: str,
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
    session=Depends(get_authenticated_session),
) -> CaseDraftWriteResponse:
    try:
        stored, backend = add_case_image(
            external_case_id,
            file_name=file.filename or "case-image",
            content_type=file.content_type,
            image_bytes=await file.read(),
            caption=caption,
            session=session,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical case not found.")

    return CaseDraftWriteResponse(
        message="Image attached to the case record.",
        externalCaseId=stored.external_case_id,
        backend=backend,
        payload=stored,
    )


@router.get("/cases/{external_case_id}/images/{external_image_id}")
def get_case_image_view(external_case_id: str, external_image_id: str, session=Depends(get_authenticated_session)) -> Response:
    try:
        image_payload = get_case_image(external_case_id, external_image_id, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not image_payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case image not found.")

    payload, filename, media_type = image_payload
    return _binary_attachment_response(payload, filename, media_type)


@router.delete("/cases/{external_case_id}/images/{external_image_id}", response_model=CaseDraftWriteResponse)
def delete_case_image_view(
    external_case_id: str,
    external_image_id: str,
    session=Depends(get_authenticated_session),
) -> CaseDraftWriteResponse:
    try:
        stored, backend = delete_case_image(external_case_id, external_image_id, session=session)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case image not found.")

    return CaseDraftWriteResponse(
        message="Image removed from the case record.",
        externalCaseId=stored.external_case_id,
        backend=backend,
        payload=stored,
    )


@router.put("/cases/{external_case_id}", response_model=CaseDraftWriteResponse)
def upsert_case(
    external_case_id: str,
    payload: ClinicalDraftCasePayload,
    session=Depends(get_authenticated_session),
) -> CaseDraftWriteResponse:
    if payload.external_case_id != external_case_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path case ID does not match payload external_case_id.")

    try:
        stored, backend = save_case_draft(payload, session=session)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    message = (
        "Case draft synchronized to Odoo through the bridge."
        if backend == "odoo_bridge"
        else "Case draft updated in the clinical API database."
    )
    return CaseDraftWriteResponse(
        message=message,
        externalCaseId=stored.external_case_id,
        backend=backend,
        payload=stored,
    )


@router.get("/tasks", response_model=list[FollowUpTask])
def get_tasks(session=Depends(get_authenticated_session)) -> list[FollowUpTask]:
    try:
        return list_tasks(session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)


@router.get("/lookups", response_model=ClinicalLookupsPayload)
def get_lookup_bundle(session=Depends(get_authenticated_session)) -> ClinicalLookupsPayload:
    try:
        return get_lookups(session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)


@router.get("/patient-relationship", response_model=PatientRelationshipSuggestion | None)
def get_patient_relationship_suggestion(
    patient_identifier: str,
    session=Depends(get_authenticated_session),
) -> PatientRelationshipSuggestion | None:
    try:
        return get_patient_relationship(patient_identifier, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)


@router.get("/patients/search", response_model=list[PatientLookupOption])
def search_patient_records(query: str, session=Depends(get_authenticated_session)) -> list[PatientLookupOption]:
    if len(query.strip()) < 2:
        return []
    try:
        return search_patients(query, session=session)
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)


@router.post("/cases", response_model=CaseDraftWriteResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: StartCasePayload, session=Depends(get_authenticated_session)) -> CaseDraftWriteResponse:
    try:
        stored, backend = create_start_case(payload, session=session)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    message = (
        "Case draft created in Odoo through the bridge."
        if backend == "odoo_bridge"
        else "Case draft created in the clinical API database."
    )
    return CaseDraftWriteResponse(
        message=message,
        externalCaseId=stored.external_case_id,
        backend=backend,
        payload=stored,
    )


@router.post("/cases/{external_case_id}/actions/{action}", response_model=CaseDraftWriteResponse)
def run_case_action(
    external_case_id: str,
    action: CaseActionType,
    payload: CaseActionPayload | None = None,
    session=Depends(get_authenticated_session),
) -> CaseDraftWriteResponse:
    try:
        stored, backend = perform_case_action(
            external_case_id,
            action,
            payload.model_dump(mode="json", exclude_unset=True) if payload else {},
            session=session,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical case not found.")

    action_messages = {
        "preview": "Report preview generated.",
        "mark_ready_for_signoff": "Case marked ready for sign-off.",
        "finalize": "Case finalized.",
        "return_to_draft": "Case returned to draft.",
        "reopen": "Finalized case reopened.",
    }
    return CaseDraftWriteResponse(
        message=action_messages[action],
        externalCaseId=stored.external_case_id,
        backend=backend,
        payload=stored,
    )


@router.put("/tasks/{external_task_id}", response_model=FollowUpTaskWriteResponse)
def save_followup_task(
    external_task_id: str,
    payload: FollowUpTaskUpdatePayload,
    session=Depends(get_authenticated_session),
) -> FollowUpTaskWriteResponse:
    try:
        stored, case_id, backend = update_followup_task(external_task_id, payload, session=session)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OdooBridgeError as exc:
        _raise_bridge_http_error(exc)

    if not stored or not case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up task not found.")

    return FollowUpTaskWriteResponse(
        message="Follow-up task updated.",
        taskId=stored.followup_task_id or stored.external_task_id or external_task_id,
        caseId=case_id,
        backend=backend,
        payload=stored,
    )


@router.post("/odoo/cases/upsert-draft")
def upsert_odoo_case_draft(
    payload: OdooDraftCasePayload,
    x_phd_ass_api_key: str | None = Header(default=None),
) -> dict[str, str]:
    settings = get_settings()
    if not settings.odoo_bridge_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bridge API key is not configured.")
    if not compare_digest(x_phd_ass_api_key or "", settings.odoo_bridge_api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bridge API key.")

    stored = shadow_upsert_odoo_draft_case(payload)
    return {
        "status": "ok",
        "externalCaseId": stored.external_case_id,
        "payloadVersion": stored.payload_version or "odoo-draft-v1",
    }
