from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProcedureType = Literal["colonoscopy", "egd", "ercp", "eus"]
CaseStatus = Literal["draft", "ready_for_signoff", "finalized", "draft_reopened"]
TaskType = Literal["pathology_review", "result_communication", "specimen_resolution", "surveillance_followup"]
TaskStatus = Literal["open", "in_progress", "closed", "cancelled"]
CaseActionType = Literal["preview", "mark_ready_for_signoff", "finalize", "return_to_draft", "reopen"]
SexOption = Literal["female", "male", "intersex", "unknown"]
CaseStoreMode = Literal["database", "odoo_bridge"]
WorkspaceRole = Literal["endoscopist", "nurse", "operations_admin", "workspace_admin"]
PriorityOption = Literal["elective", "urgent", "emergency"]
ASAClassOption = Literal["I", "II", "III", "IV", "V"]
AntithromboticPlanOption = Literal["na", "continue", "hold", "bridging_other"]
AntibioticsStatusOption = Literal["na", "indicated_given"]
PregnancyStatusOption = Literal["na", "negative", "positive_known"]
PrepQualityOption = Literal["adequate", "inadequate"]
TerminalIleumStatusOption = Literal["not_attempted", "intubated", "abnormal"]
TechnicalLimitationOption = Literal["none", "poor_prep", "stricture", "pain", "other"]
SmallPolypTechniqueOption = Literal["cold_snare", "hot_snare", "forceps", "other"]
TattooStatusOption = Literal["na", "placed"]
PathologyStatusOption = Literal["none", "pending_tracking_required"]
SurveillanceIntervalReasonOption = Literal["guideline_based", "prep_quality", "piecemeal_resection", "other"]
AdverseEventPlanOption = Literal["routine_discharge", "observe_admit", "other"]
SegmentNameOption = Literal[
    "terminal_ileum",
    "cecum",
    "ascending_colon",
    "transverse_colon",
    "descending_colon",
    "sigmoid_colon",
    "rectum_retroflexion",
]

CASE_FALSE_NULL_FIELDS = {
    "dob_or_age",
    "facility_code",
    "facility_unit_code",
    "endoscopist_user_id",
    "endoscopist_user_ref",
    "assistant_nurse_user_id",
    "assistant_nurse_user_ref",
    "referrer_service",
    "indication",
    "priority",
    "relevant_history",
    "asa_class",
    "allergies",
    "antithrombotic_plan",
    "sedation_anesthesia",
    "antibiotics_status",
    "pregnancy_status",
    "bowel_prep_agent",
    "prep_quality",
    "insertion_time",
    "terminal_ileum_status",
    "technical_limitation",
    "technical_limitation_note",
    "adverse_event_note",
    "uc_mayo_score",
    "crohn_score",
    "disease_extent",
    "small_polyp_technique",
    "small_polyp_technique_note",
    "tattoo_status",
    "tattoo_location_note",
    "hemostasis_or_closure",
    "impression",
    "pathology_status",
    "surveillance_interval_value",
    "surveillance_interval_reason",
    "surveillance_interval_reason_note",
    "adverse_event_plan",
    "adverse_event_plan_note",
    "patient_identity_verified",
    "finalized_at",
    "finalized_by_user_id",
    "finalized_by_user_ref",
    "template_version",
    "report_narrative_snapshot",
    "pdf_asset_ref",
    "validation_summary",
    "payload_version",
}

TASK_FALSE_NULL_FIELDS = {
    "external_task_id",
    "followup_task_id",
    "task_owner_user_id",
    "task_owner_user_ref",
    "due_date",
    "resolution_note",
    "closed_at",
    "closed_by_user_id",
    "closed_by_user_ref",
}


def _normalize_odoo_false_nulls(data: dict[str, Any], field_names: set[str]) -> dict[str, Any]:
    for field_name in field_names:
        if data.get(field_name) is False:
            data[field_name] = None
    return data


class WorkflowStep(BaseModel):
    id: str
    label: str
    description: str


class DashboardSnapshot(BaseModel):
    activeDrafts: int
    openTasks: int
    finalizedToday: int


class LoginPayload(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthenticatedSessionPayload(BaseModel):
    token: str
    userId: str
    login: str
    displayName: str
    primaryRole: WorkspaceRole
    roles: list[WorkspaceRole]
    facilityCodes: list[str] = Field(default_factory=list)
    expiresAt: str


class CaseSummary(BaseModel):
    id: str
    patientIdentifier: str
    procedureType: ProcedureType
    status: CaseStatus
    procedureDatetime: str
    endoscopistName: str


class FollowUpTask(BaseModel):
    id: str
    caseId: str
    type: TaskType
    status: TaskStatus
    ownerName: str
    dueDate: str | None = None


class StartCasePayload(BaseModel):
    procedureType: ProcedureType
    patientIdentifier: str = Field(min_length=1)
    procedureDatetime: str = Field(min_length=1)
    dobOrAge: str = Field(min_length=1)
    sex: SexOption
    facilityUnit: str = Field(min_length=1)
    facilityCode: str | None = None
    endoscopistUserId: str = Field(min_length=1)
    referrerService: str | None = None
    assistantNurseUserId: str | None = None


class OdooFollowUpTaskPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    external_task_id: str | None = None
    followup_task_id: str | None = None
    task_type: TaskType
    task_owner_user_id: str | None = None
    task_owner_user_ref: str | None = None
    task_status: TaskStatus = "open"
    due_date: str | None = None
    resolution_note: str | None = None
    closed_at: str | None = None
    closed_by_user_id: str | None = None
    closed_by_user_ref: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_task_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        external_task_id = normalized.get("external_task_id") or normalized.get("task_id") or normalized.get("followup_task_id")
        if external_task_id and not normalized.get("external_task_id"):
            normalized["external_task_id"] = external_task_id
        if external_task_id and not normalized.get("followup_task_id"):
            normalized["followup_task_id"] = external_task_id
        return _normalize_odoo_false_nulls(normalized, TASK_FALSE_NULL_FIELDS)


class CaseSegmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    segment_name: SegmentNameOption
    normal: bool = False
    finding_note: str | None = None
    photo_taken: bool = False


class CaseLesionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    lesion_index: int | None = None
    lesion_location: str | None = None
    lesion_size_mm: int | None = None
    lesion_morphology: str | None = None
    resection_method: str | None = None
    complete_resection: bool = False
    retrieved: bool = False
    specimen_container_ref: str | None = None


class CaseSpecimenPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    container_label: str | None = None
    specimen_site: str | None = None
    specimen_count: int | None = None
    test_question: str | None = None
    label_verified: bool = False


class CaseImageAttachmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    external_image_id: str | None = None
    file_name: str = Field(min_length=1)
    content_type: str | None = None
    caption: str | None = None
    size_bytes: int | None = None
    uploaded_at: str | None = None
    uploaded_by_user_id: str | None = None
    uploaded_by_user_ref: str | None = None
    asset_ref: str | None = None
    content_base64: str | None = None


class ClinicalDraftCasePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    external_case_id: str = Field(min_length=1)
    case_status: CaseStatus = "draft"
    procedure_type: ProcedureType = "colonoscopy"
    patient_identifier: str = Field(min_length=1)
    procedure_datetime: str = Field(min_length=1)
    dob_or_age: str | None = None
    sex: SexOption
    facility_unit: str = Field(min_length=1)
    facility_code: str | None = None
    facility_unit_code: str | None = None
    endoscopist_user_id: str | None = None
    endoscopist_user_ref: str | None = None
    assistant_nurse_user_id: str | None = None
    assistant_nurse_user_ref: str | None = None
    referrer_service: str | None = None

    indication: str | None = None
    priority: PriorityOption | None = None
    relevant_history: str | None = None
    asa_class: ASAClassOption | None = None
    allergies: str | None = None
    antithrombotic_plan: AntithromboticPlanOption | None = None
    consent_documented: bool = False
    patient_identity_verified: bool = False
    team_pause_completed: bool = False
    sedation_anesthesia: str | None = None
    monitor_spo2: bool = False
    monitor_hr: bool = False
    monitor_bp: bool = False
    monitor_ecg: bool = False
    monitor_capnography: bool = False
    antibiotics_status: AntibioticsStatusOption | None = None
    pregnancy_status: PregnancyStatusOption | None = None

    bowel_prep_agent: str | None = None
    prep_quality: PrepQualityOption | None = None
    bbps_right: int | None = None
    bbps_transverse: int | None = None
    bbps_left: int | None = None
    bbps_total: int | None = None
    insertion_time: str | None = None
    cecum_reached: bool = False
    cecal_landmark_appendiceal_orifice: bool = False
    cecal_landmark_ileocecal_valve: bool = False
    photo_cecum: bool = False
    photo_pathology: bool = False
    terminal_ileum_status: TerminalIleumStatusOption | None = None
    withdrawal_time_minutes: int | None = None
    technical_limitation: TechnicalLimitationOption | None = None
    technical_limitation_note: str | None = None
    adverse_event_during_procedure: bool = False
    adverse_event_note: str | None = None

    uc_mayo_score: Literal["0", "1", "2", "3"] | None = None
    crohn_score: str | None = None
    disease_extent: str | None = None

    small_polyp_technique: SmallPolypTechniqueOption | None = None
    small_polyp_technique_note: str | None = None
    advanced_resection_type: list[str] = Field(default_factory=list)
    tattoo_status: TattooStatusOption | None = None
    tattoo_location_note: str | None = None
    hemostasis_or_closure: str | None = None
    impression: str | None = None
    pathology_status: PathologyStatusOption | None = None
    surveillance_interval_value: str | None = None
    surveillance_interval_pending_pathology: bool = False
    surveillance_interval_reason: SurveillanceIntervalReasonOption | None = None
    surveillance_interval_reason_note: str | None = None
    adverse_event_plan: AdverseEventPlanOption | None = None
    adverse_event_plan_note: str | None = None
    informed_patient: bool = False
    informed_referrer: bool = False
    written_instructions_given: bool = False

    segment_exam: list[CaseSegmentPayload] = Field(default_factory=list)
    lesions: list[CaseLesionPayload] = Field(default_factory=list)
    specimens: list[CaseSpecimenPayload] = Field(default_factory=list)
    image_attachments: list[CaseImageAttachmentPayload] = Field(default_factory=list)
    followup_tasks: list[OdooFollowUpTaskPayload] = Field(default_factory=list)

    finalized_at: str | None = None
    finalized_by_user_id: str | None = None
    finalized_by_user_ref: str | None = None
    template_version: str | None = None
    report_narrative_snapshot: str | None = None
    pdf_asset_ref: str | None = None
    validation_summary: str | None = None
    payload_version: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_case_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        external_case_id = normalized.get("external_case_id") or normalized.get("case_id")
        if external_case_id and not normalized.get("external_case_id"):
            normalized["external_case_id"] = external_case_id
        if "segments" in normalized and "segment_exam" not in normalized:
            normalized["segment_exam"] = normalized.get("segments") or []
        if "tasks" in normalized and "followup_tasks" not in normalized:
            normalized["followup_tasks"] = normalized.get("tasks") or []
        if normalized.get("image_attachments") is False:
            normalized["image_attachments"] = []
        return _normalize_odoo_false_nulls(normalized, CASE_FALSE_NULL_FIELDS)


class OdooDraftCasePayload(ClinicalDraftCasePayload):
    pass


class CaseDraftWriteResponse(BaseModel):
    message: str
    externalCaseId: str
    backend: CaseStoreMode
    payload: ClinicalDraftCasePayload


class FacilityLookupOption(BaseModel):
    code: str
    label: str


class FacilityUnitLookupOption(BaseModel):
    code: str
    label: str
    facilityCode: str | None = None


class ClinicianLookupOption(BaseModel):
    userId: str
    label: str
    role: WorkspaceRole
    endoscopistUserIds: list[str] = Field(default_factory=list)
    facilityCodes: list[str] = Field(default_factory=list)


class ValueLookupOption(BaseModel):
    value: str
    label: str


class ClinicalLookupsPayload(BaseModel):
    facilities: list[FacilityLookupOption]
    facilityUnits: list[FacilityUnitLookupOption]
    endoscopists: list[ClinicianLookupOption]
    nurses: list[ClinicianLookupOption]
    referrerServices: list[ValueLookupOption]


class PatientRelationshipSuggestion(BaseModel):
    relationshipId: int
    patientIdentifier: str
    facilityCode: str
    facilityLabel: str
    facilityUnitCode: str | None = None
    facilityUnitLabel: str | None = None
    endoscopistUserId: str
    endoscopistLabel: str


class PatientLookupOption(BaseModel):
    patientIdentifier: str
    displayName: str
    medicalRecordNumber: str | None = None
    dobOrAge: str | None = None
    sex: SexOption | None = None


class CaseActionPayload(BaseModel):
    reason: str | None = None


class FollowUpTaskUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_owner_user_id: str | None = None
    task_owner_user_ref: str | None = None
    due_date: str | None = None
    task_status: TaskStatus | None = None
    resolution_note: str | None = None


class FollowUpTaskWriteResponse(BaseModel):
    message: str
    taskId: str
    caseId: str
    backend: CaseStoreMode
    payload: OdooFollowUpTaskPayload


class CaseRevisionPayload(BaseModel):
    revisionNumber: int
    finalizedAt: str | None = None
    finalizedBy: str | None = None
    templateVersion: str | None = None
    pdfAssetRef: str | None = None
    reportNarrativeSnapshot: str | None = None


class AuditEventPayload(BaseModel):
    id: str
    createdAt: str
    actorDisplayName: str | None = None
    actorRole: str | None = None
    eventType: str
    entityType: str = "case"
    entityRef: str | None = None
    reason: str | None = None
    payload: dict[str, Any] | list[Any] | str | None = None


class CaseHistoryPayload(BaseModel):
    caseId: str
    revisions: list[CaseRevisionPayload]
    auditEvents: list[AuditEventPayload]


class MetaPayload(BaseModel):
    appName: str
    odooRecommendedModule: str
    odooRecommendedModuleLabel: str
    workflowSteps: list[WorkflowStep]
    workflowStepsByProcedure: dict[ProcedureType, list[WorkflowStep]]
    dashboardSnapshot: DashboardSnapshot
