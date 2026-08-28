from app.schemas import ClinicalDraftCasePayload, WorkspaceRole


LOCAL_TEMPLATE_VERSION = "clinical-api-db-v1"

DEFAULT_FACILITIES = [
    {"code": "MAIN", "label": "Main Unit"},
    {"code": "DAY", "label": "Day Procedure"},
    {"code": "THER", "label": "Therapeutic Suite"},
]

DEFAULT_FACILITY_UNITS = [
    {"code": "MAIN-R1", "label": "Main Unit / Room 1", "facilityCode": "MAIN"},
    {"code": "MAIN-R2", "label": "Main Unit / Room 2", "facilityCode": "MAIN"},
    {"code": "DAY-BAY", "label": "Day Procedure Bay", "facilityCode": "DAY"},
    {"code": "THER-SUITE", "label": "Therapeutic Suite", "facilityCode": "THER"},
]

DEFAULT_CLINICIANS = [
    {"userId": "dr.njoroge", "label": "Dr. A. Njoroge", "role": "endoscopist", "facilityCodes": ["MAIN", "THER"]},
    {"userId": "dr.kamau", "label": "Dr. B. Kamau", "role": "endoscopist", "facilityCodes": ["DAY"]},
    {"userId": "nurse.akinyi", "label": "Nurse W. Akinyi", "role": "nurse", "endoscopistUserIds": ["dr.njoroge"], "facilityCodes": ["MAIN", "THER"]},
    {"userId": "nurse.atieno", "label": "Nurse C. Atieno", "role": "nurse", "endoscopistUserIds": ["dr.kamau"], "facilityCodes": ["DAY"]},
]

DEFAULT_LOCAL_AUTH_USERS: dict[str, dict[str, str | list[WorkspaceRole]]] = {
    "dr.njoroge": {
        "user_id": "local-dr-njoroge",
        "display_name": "Dr. A. Njoroge",
        "primary_role": "endoscopist",
        "roles": ["endoscopist"],
        "facility_codes": ["MAIN", "THER"],
    },
    "dr.kamau": {
        "user_id": "local-dr-kamau",
        "display_name": "Dr. B. Kamau",
        "primary_role": "endoscopist",
        "roles": ["endoscopist"],
        "facility_codes": ["DAY"],
    },
    "nurse.akinyi": {
        "user_id": "local-nurse-akinyi",
        "display_name": "Nurse W. Akinyi",
        "primary_role": "nurse",
        "roles": ["nurse"],
        "facility_codes": ["MAIN", "THER"],
    },
    "nurse.atieno": {
        "user_id": "local-nurse-atieno",
        "display_name": "Nurse C. Atieno",
        "primary_role": "nurse",
        "roles": ["nurse"],
        "facility_codes": ["DAY"],
    },
    "ops.admin": {
        "user_id": "local-ops-admin",
        "display_name": "Operations Admin",
        "primary_role": "operations_admin",
        "roles": ["operations_admin"],
        "facility_codes": ["MAIN"],
    },
    "workspace.admin": {
        "user_id": "local-workspace-admin",
        "display_name": "Workspace Admin",
        "primary_role": "workspace_admin",
        "roles": ["workspace_admin"],
        "facility_codes": ["MAIN", "DAY", "THER"],
    },
}

DEFAULT_REFERRER_SERVICES = [
    {"value": "Gastroenterology Clinic", "label": "Gastroenterology Clinic"},
    {"value": "Upper GI Clinic", "label": "Upper GI Clinic"},
    {"value": "General Surgery", "label": "General Surgery"},
    {"value": "Internal Medicine", "label": "Internal Medicine"},
    {"value": "Oncology", "label": "Oncology"},
    {"value": "Emergency Department", "label": "Emergency Department"},
]


def build_sample_cases() -> list[ClinicalDraftCasePayload]:
    return [
        ClinicalDraftCasePayload(
            external_case_id="case-1001",
            case_status="draft",
            procedure_type="colonoscopy",
            patient_identifier="PT-2026-001",
            procedure_datetime="2026-08-18T08:30:00Z",
            dob_or_age="54 years",
            sex="female",
            facility_unit="Main Unit / Room 2",
            facility_code="MAIN",
            facility_unit_code="MAIN-R2",
            endoscopist_user_id="dr.njoroge",
            endoscopist_user_ref="Dr. A. Njoroge",
            assistant_nurse_user_id="nurse.akinyi",
            assistant_nurse_user_ref="Nurse W. Akinyi",
            referrer_service="Gastroenterology Clinic",
            indication="Positive FIT with intermittent rectal bleeding.",
            priority="elective",
            asa_class="II",
            consent_documented=True,
            team_pause_completed=True,
            sedation_anesthesia="Conscious sedation",
            prep_quality="adequate",
            bbps_right=2,
            bbps_transverse=3,
            bbps_left=2,
            bbps_total=7,
            cecum_reached=True,
            cecal_landmark_appendiceal_orifice=True,
            cecal_landmark_ileocecal_valve=True,
            photo_cecum=True,
            terminal_ileum_status="intubated",
            withdrawal_time_minutes=9,
            segment_exam=[
                {"segment_name": "cecum", "normal": True, "photo_taken": True},
                {"segment_name": "ascending_colon", "normal": True},
                {"segment_name": "sigmoid_colon", "normal": False, "finding_note": "6 mm sessile polyp removed with cold snare."},
            ],
            lesions=[
                {
                    "lesion_index": 1,
                    "lesion_location": "Sigmoid colon",
                    "lesion_size_mm": 6,
                    "lesion_morphology": "Sessile",
                    "resection_method": "Cold snare",
                    "complete_resection": True,
                    "retrieved": True,
                    "specimen_container_ref": "A",
                }
            ],
            specimens=[
                {
                    "container_label": "A",
                    "specimen_site": "Sigmoid colon polyp",
                    "specimen_count": 1,
                    "label_verified": True,
                }
            ],
            impression="Single small sigmoid polyp removed completely.",
            pathology_status="pending_tracking_required",
            surveillance_interval_pending_pathology=True,
            adverse_event_plan="routine_discharge",
            informed_patient=True,
            written_instructions_given=True,
            followup_tasks=[
                {
                    "followup_task_id": "task-2001",
                    "task_type": "pathology_review",
                    "task_owner_user_id": "dr.njoroge",
                    "task_owner_user_ref": "Dr. A. Njoroge",
                    "task_status": "open",
                    "due_date": "2026-08-20",
                }
            ],
        ),
        ClinicalDraftCasePayload(
            external_case_id="case-1002",
            case_status="finalized",
            procedure_type="egd",
            patient_identifier="PT-2026-002",
            procedure_datetime="2026-08-18T09:10:00Z",
            dob_or_age="48 years",
            sex="male",
            facility_unit="Day Procedure Bay",
            facility_code="DAY",
            facility_unit_code="DAY-BAY",
            endoscopist_user_id="dr.kamau",
            endoscopist_user_ref="Dr. B. Kamau",
            assistant_nurse_user_id="nurse.atieno",
            assistant_nurse_user_ref="Nurse C. Atieno",
            referrer_service="Upper GI Clinic",
            indication="Dyspepsia and iron deficiency anaemia.",
            sedation_anesthesia="Topical throat spray and conscious sedation",
            consent_documented=True,
            team_pause_completed=True,
            egd_extent_reached="second_duodenum",
            egd_exam_esophagus_note="No varices or erosive esophagitis.",
            egd_stomach_finding="Mild erythematous antral gastritis.",
            egd_duodenum_finding="Normal bulb and second part of duodenum.",
            egd_impression="Mild antral gastritis. Biopsies deferred.",
            egd_medication_therapy="Continue PPI for 8 weeks.",
            egd_result_communication_planned=True,
            finalized_at="2026-08-18T10:02:00Z",
            finalized_by_user_id="dr.kamau",
            finalized_by_user_ref="Dr. B. Kamau",
            followup_tasks=[
                {
                    "followup_task_id": "task-2002",
                    "task_type": "result_communication",
                    "task_owner_user_id": "nurse.atieno",
                    "task_owner_user_ref": "Nurse C. Atieno",
                    "task_status": "in_progress",
                }
            ],
        ),
    ]
