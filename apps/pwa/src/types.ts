import type { CaseSummary, FollowUpTask } from "@phd-ass/domain";

export type WorkflowStep = {
  id: string;
  label: string;
  description: string;
};

export type ProcedureType = "colonoscopy" | "egd" | "ercp" | "eus";
export type SexOption = "female" | "male" | "intersex" | "unknown";
export type WorkspaceRole = "endoscopist" | "nurse" | "operations_admin" | "workspace_admin";
export type CaseActionName = "preview" | "mark_ready_for_signoff" | "finalize" | "return_to_draft" | "reopen";
export type PriorityOption = "elective" | "urgent" | "emergency";
export type TaskStatus = FollowUpTask["status"];
export type TaskType = FollowUpTask["type"];

export type MetaPayload = {
  appName: string;
  odooRecommendedModule: string;
  odooRecommendedModuleLabel: string;
  workflowSteps: WorkflowStep[];
  workflowStepsByProcedure: Record<string, WorkflowStep[]>;
  dashboardSnapshot: {
    activeDrafts: number;
    openTasks: number;
    finalizedToday: number;
  };
};

export type HealthPayload = {
  status: string;
  service: string;
};

export type LoginPayload = {
  login: string;
  password: string;
};

export type AuthenticatedSessionPayload = {
  token: string;
  userId: string;
  login: string;
  displayName: string;
  primaryRole: WorkspaceRole;
  roles: WorkspaceRole[];
  facilityCodes: string[];
  expiresAt: string;
};

export type FacilityLookupOption = {
  code: string;
  label: string;
};

export type FacilityUnitLookupOption = {
  code: string;
  label: string;
  facilityCode?: string | null;
};

export type ClinicianLookupOption = {
  userId: string;
  label: string;
  role: WorkspaceRole;
  endoscopistUserIds?: string[];
  facilityCodes?: string[];
};

export type ValueLookupOption = {
  value: string;
  label: string;
};

export type ClinicalLookupsPayload = {
  facilities: FacilityLookupOption[];
  facilityUnits: FacilityUnitLookupOption[];
  endoscopists: ClinicianLookupOption[];
  nurses: ClinicianLookupOption[];
  referrerServices: ValueLookupOption[];
};

export type PatientRelationshipSuggestion = {
  relationshipId: number;
  patientIdentifier: string;
  facilityCode: string;
  facilityLabel: string;
  facilityUnitCode?: string | null;
  facilityUnitLabel?: string | null;
  endoscopistUserId: string;
  endoscopistLabel: string;
};

export type PatientLookupOption = {
  patientIdentifier: string;
  displayName: string;
  medicalRecordNumber?: string | null;
  dobOrAge?: string | null;
  sex?: SexOption | null;
};

export type StartCasePayload = {
  procedureType: ProcedureType;
  patientIdentifier: string;
  procedureDatetime: string;
  dobOrAge: string;
  sex: SexOption;
  facilityUnit: string;
  facilityCode?: string;
  endoscopistUserId: string;
  referrerService?: string;
  assistantNurseUserId?: string;
};

export type StartCaseResponse = {
  message: string;
  externalCaseId?: string;
  backend?: string;
  payload: Record<string, unknown>;
};

export type CaseSegmentPayload = {
  segment_name: string;
  normal: boolean;
  finding_note?: string | null;
  photo_taken: boolean;
};

export type CaseLesionPayload = {
  lesion_index?: number | null;
  lesion_location?: string | null;
  lesion_size_mm?: number | null;
  lesion_morphology?: string | null;
  resection_method?: string | null;
  complete_resection: boolean;
  retrieved: boolean;
  specimen_container_ref?: string | null;
};

export type CaseSpecimenPayload = {
  container_label?: string | null;
  specimen_site?: string | null;
  specimen_count?: number | null;
  test_question?: string | null;
  label_verified: boolean;
};

export type CaseImageAttachmentPayload = {
  external_image_id?: string | null;
  file_name: string;
  content_type?: string | null;
  caption?: string | null;
  size_bytes?: number | null;
  uploaded_at?: string | null;
  uploaded_by_user_id?: string | null;
  uploaded_by_user_ref?: string | null;
  asset_ref?: string | null;
};

export type ClinicalFollowUpTaskPayload = {
  external_task_id?: string | null;
  followup_task_id?: string | null;
  task_type: TaskType;
  task_owner_user_id?: string | null;
  task_owner_user_ref?: string | null;
  task_status: TaskStatus;
  due_date?: string | null;
  resolution_note?: string | null;
  closed_at?: string | null;
  closed_by_user_id?: string | null;
  closed_by_user_ref?: string | null;
};

export type ClinicalDraftCasePayload = {
  [key: string]: unknown;
  external_case_id: string;
  case_status: CaseSummary["status"];
  procedure_type: ProcedureType;
  patient_identifier: string;
  procedure_datetime: string;
  dob_or_age?: string | null;
  sex: SexOption;
  facility_unit: string;
  facility_code?: string | null;
  facility_unit_code?: string | null;
  endoscopist_user_id?: string | null;
  endoscopist_user_ref?: string | null;
  assistant_nurse_user_id?: string | null;
  assistant_nurse_user_ref?: string | null;
  referrer_service?: string | null;
  indication?: string | null;
  priority?: PriorityOption | null;
  relevant_history?: string | null;
  asa_class?: string | null;
  allergies?: string | null;
  antithrombotic_plan?: string | null;
  consent_documented?: boolean;
  patient_identity_verified?: boolean;
  team_pause_completed?: boolean;
  sedation_anesthesia?: string | null;
  monitor_spo2?: boolean;
  monitor_hr?: boolean;
  monitor_bp?: boolean;
  monitor_ecg?: boolean;
  monitor_capnography?: boolean;
  antibiotics_status?: string | null;
  pregnancy_status?: string | null;
  bowel_prep_agent?: string | null;
  prep_quality?: string | null;
  bbps_right?: number | null;
  bbps_transverse?: number | null;
  bbps_left?: number | null;
  bbps_total?: number | null;
  insertion_time?: string | null;
  cecum_reached?: boolean;
  cecal_landmark_appendiceal_orifice?: boolean;
  cecal_landmark_ileocecal_valve?: boolean;
  photo_cecum?: boolean;
  terminal_ileum_status?: string | null;
  withdrawal_time_minutes?: number | null;
  technical_limitation?: string | null;
  technical_limitation_note?: string | null;
  adverse_event_during_procedure?: boolean;
  adverse_event_note?: string | null;
  photo_pathology?: boolean;
  surveillance_interval_reason?: string | null;
  surveillance_interval_reason_note?: string | null;
  small_polyp_technique?: string | null;
  small_polyp_technique_note?: string | null;
  advanced_resection_type?: string[];
  tattoo_status?: string | null;
  tattoo_location_note?: string | null;
  hemostasis_or_closure?: string | null;
  impression?: string | null;
  pathology_status?: string | null;
  surveillance_interval_value?: string | null;
  surveillance_interval_pending_pathology?: boolean;
  adverse_event_plan?: string | null;
  informed_patient?: boolean;
  informed_referrer?: boolean;
  written_instructions_given?: boolean;
  egd_extent_reached?: string | null;
  egd_exam_esophagus_note?: string | null;
  egd_stomach_finding?: string | null;
  egd_duodenum_finding?: string | null;
  egd_specimens_obtained?: boolean;
  egd_impression?: string | null;
  egd_followup_surveillance?: string | null;
  egd_h_pylori_plan?: string | null;
  egd_medication_therapy?: string | null;
  egd_result_communication_planned?: boolean;
  egd_referrer_communication_planned?: boolean;
  ercp_papilla_status?: string | null;
  ercp_therapeutic_intent?: string | null;
  ercp_radiation_protection_verified?: boolean;
  ercp_technical_success?: string | null;
  ercp_drainage_achieved?: string | null;
  ercp_repeat_intervention?: string | null;
  ercp_repeat_intervention_timing?: string | null;
  ercp_patient_contact_note?: string | null;
  ercp_tracking_register_entered?: boolean;
  ercp_temporary_stent?: boolean;
  ercp_impression?: string | null;
  eus_route?: string | null;
  eus_echoendoscope?: string | null;
  eus_intent?: string | null;
  eus_relevant_anatomy_documented?: string | null;
  eus_fna_performed?: boolean;
  eus_fnb_performed?: boolean;
  eus_passes_count?: number | null;
  eus_adequacy_status?: string | null;
  eus_clinical_plan?: string | null;
  eus_followup_imaging_or_procedure?: string | null;
  eus_multidisciplinary_referral?: string | null;
  eus_impression?: string | null;
  finalized_at?: string | null;
  finalized_by_user_id?: string | null;
  finalized_by_user_ref?: string | null;
  template_version?: string | null;
  report_narrative_snapshot?: string | null;
  pdf_asset_ref?: string | null;
  validation_summary?: string | null;
  reopen_reason?: string | null;
  reopened_at?: string | null;
  reopened_by_user_id?: string | null;
  reopened_by_user_ref?: string | null;
  segment_exam: CaseSegmentPayload[];
  lesions: CaseLesionPayload[];
  specimens: CaseSpecimenPayload[];
  image_attachments: CaseImageAttachmentPayload[];
  followup_tasks: ClinicalFollowUpTaskPayload[];
};

export type CaseActionPayload = {
  reason?: string;
};

export type FollowUpTaskUpdatePayload = {
  task_owner_user_id?: string;
  task_owner_user_ref?: string;
  due_date?: string;
  task_status?: TaskStatus;
  resolution_note?: string;
};

export type CaseDraftWriteResponse = {
  message: string;
  externalCaseId: string;
  backend: string;
  payload: ClinicalDraftCasePayload;
};

export type FollowUpTaskWriteResponse = {
  message: string;
  taskId: string;
  caseId: string;
  backend: string;
  payload: ClinicalFollowUpTaskPayload;
};

export type CaseRevisionPayload = {
  revisionNumber: number;
  finalizedAt?: string | null;
  finalizedBy?: string | null;
  templateVersion?: string | null;
  pdfAssetRef?: string | null;
  reportNarrativeSnapshot?: string | null;
};

export type AuditEventPayload = {
  id: string;
  createdAt: string;
  actorDisplayName?: string | null;
  actorRole?: string | null;
  eventType: string;
  entityType: string;
  entityRef?: string | null;
  reason?: string | null;
  payload?: Record<string, unknown> | unknown[] | string | null;
};

export type CaseHistoryPayload = {
  caseId: string;
  revisions: CaseRevisionPayload[];
  auditEvents: AuditEventPayload[];
};

export type ApiBundle = {
  health: HealthPayload;
  meta: MetaPayload;
  cases: CaseSummary[];
  tasks: FollowUpTask[];
  lookups: ClinicalLookupsPayload;
  warnings?: string[];
};
