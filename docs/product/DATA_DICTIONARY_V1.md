# Data Dictionary V1

This dictionary covers the V1 build scope:

- shared case fields,
- shared safety fields,
- colonoscopy fields,
- Odoo draft fields for EGD, ERCP, and EUS,
- specimen and follow-up fields.

Current implementation note:

- The clinician PWA field map and validation remain colonoscopy-first.
- The Odoo draft workspace and Odoo draft payload now include procedure-specific fields for `egd`, `ercp`, and `eus`.

## Conventions

- `Type` uses application-oriented data types.
- `Required` means required before sign-off unless noted.
- `Editable By` lists primary roles permitted to update the field in draft state.
- `Screen Step` references the step names in the screen-field map.
- Surface ownership and Odoo parity rules are defined in `docs/architecture/ODOO_APP_FORM_OWNERSHIP.md`.

## 1. Case Header

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| case_id | Case ID | UUID | System | System | System | Internal identifier |
| procedure_type | Procedure Type | Enum | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Supported values in Odoo draft authoring: `colonoscopy`, `egd`, `ercp`, `eus` |
| case_status | Case Status | Enum | System | System | System | `draft`, `ready_for_signoff`, `finalized`, `draft_reopened` |
| patient_identifier | Patient Name or ID | String | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Local identifier rules still need stakeholder confirmation |
| procedure_datetime | Date and Time | DateTime | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Procedure start reference |
| dob_or_age | DOB or Age | String | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Model as string in UI, normalize later if DOB available |
| sex | Sex | Enum | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Current dropdown values: `female`, `male`, `intersex`, `unknown` |
| facility_unit | Facility or Unit | String | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Supports future multi-site use |
| endoscopist_user_id | Endoscopist | FK User | Yes | Endoscopist, Nurse, Unit Admin | Start Case | Signer must match or explicitly change at sign-off |
| referrer_service | Referrer or Service | String | No | Endoscopist, Nurse, Unit Admin | Start Case | Optional in V1 unless local policy says otherwise |
| assistant_nurse_user_id | Assistant or Nurse | FK User | No | Endoscopist, Nurse, Unit Admin | Start Case | Optional but recommended |

## 2. Shared Safety And Indication

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| indication | Indication | Text | Yes | Endoscopist, Nurse, Unit Admin | Safety | Free text in V1 |
| priority | Priority | Enum | Yes | Endoscopist, Nurse, Unit Admin | Safety | `elective`, `urgent`, `emergency` |
| relevant_history | Relevant History | Text | No | Endoscopist, Nurse, Unit Admin | Safety | Non-blocking but recommended |
| asa_class | ASA Class | Enum | Yes | Endoscopist, Nurse, Unit Admin | Safety | `I` to `V` |
| allergies | Allergies | Text | No | Endoscopist, Nurse, Unit Admin | Safety | Non-blocking unless local policy changes |
| antithrombotic_plan | Antithrombotic Plan | Enum | Yes | Endoscopist, Nurse, Unit Admin | Safety | `na`, `continue`, `hold`, `bridging_other` |
| consent_documented | Consent Documented | Boolean | Yes | Endoscopist, Nurse, Unit Admin | Safety | Blocking |
| team_pause_completed | Team Pause Completed | Boolean | Yes | Endoscopist, Nurse, Unit Admin | Safety | Blocking if required locally |
| sedation_anesthesia | Sedation or Anesthesia | String | Yes | Endoscopist, Nurse, Unit Admin | Safety | Text for V1 |
| monitor_spo2 | Monitor SpO2 | Boolean | No | Endoscopist, Nurse, Unit Admin | Safety | Stored as checklist values |
| monitor_hr | Monitor Heart Rate | Boolean | No | Endoscopist, Nurse, Unit Admin | Safety |  |
| monitor_bp | Monitor Blood Pressure | Boolean | No | Endoscopist, Nurse, Unit Admin | Safety |  |
| monitor_ecg | Monitor ECG | Boolean | No | Endoscopist, Nurse, Unit Admin | Safety |  |
| monitor_capnography | Monitor Capnography | Boolean | No | Endoscopist, Nurse, Unit Admin | Safety |  |
| antibiotics_status | Antibiotics | Enum | No | Endoscopist, Nurse, Unit Admin | Safety | `na`, `indicated_given` |
| pregnancy_status | Pregnancy Status | Enum | No | Endoscopist, Nurse, Unit Admin | Safety | `na`, `negative`, `positive_known` |

## 3. Colonoscopy Preparation And Completeness

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| bowel_prep_agent | Bowel Prep Agent | String | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Optional in V1 |
| prep_quality | Prep Quality | Enum | Yes | Endoscopist, Nurse, Unit Admin | Prep And Completeness | `adequate`, `inadequate` |
| bbps_right | BBPS Right | Integer | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | 0 to 3 |
| bbps_transverse | BBPS Transverse | Integer | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | 0 to 3 |
| bbps_left | BBPS Left | Integer | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | 0 to 3 |
| bbps_total | BBPS Total | Integer | Derived | System | Prep And Completeness | Sum of segment scores |
| insertion_time | Insertion Time | DateTime or Time | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Optional in V1 |
| cecum_reached | Cecum Reached | Boolean | Yes | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Blocking |
| cecal_landmark_appendiceal_orifice | Appendiceal Orifice Seen | Boolean | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness |  |
| cecal_landmark_ileocecal_valve | Ileocecal Valve Seen | Boolean | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness |  |
| photo_cecum | Cecum Photo | Boolean | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness |  |
| photo_pathology | Pathology Photo | Boolean | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Shared with findings |
| terminal_ileum_status | Terminal Ileum | Enum | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | `not_attempted`, `intubated`, `abnormal` |
| withdrawal_time_minutes | Withdrawal Time Minutes | Integer | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Excluding therapy |
| technical_limitation | Technical Limitation | Enum | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | `none`, `poor_prep`, `stricture`, `pain`, `other` |
| technical_limitation_note | Technical Limitation Note | Text | Conditional | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Required when `other` |
| adverse_event_during_procedure | Adverse Event | Boolean | No | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Immediate procedural event flag |
| adverse_event_note | Adverse Event Note | Text | Conditional | Endoscopist, Nurse, Unit Admin | Prep And Completeness | Required when adverse event is true |

## 4. Colonoscopy Segmental Examination

Each segment row shares the same structure.

| Field Group | Rows | Fields |
| --- | --- | --- |
| segment_exam | terminal_ileum, cecum, ascending_colon, transverse_colon, descending_colon, sigmoid_colon, rectum_retroflexion | `normal:boolean`, `finding_note:text`, `photo_taken:boolean` |

### Stored Shape

- segment_name
- normal
- finding_note
- photo_taken

At least one of `normal` or `finding_note` should be present per segment before sign-off.

## 5. IBD Activity

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| uc_mayo_score | Ulcerative Colitis Mayo Score | Enum | No | Endoscopist | Segment Exam | `0`, `1`, `2`, `3` |
| crohn_score | Crohn Score | String | No | Endoscopist | Segment Exam | Text to allow SES-CD or validated alternative |
| disease_extent | Disease Extent | Text | No | Endoscopist | Segment Exam | Optional |

## 6. Polyp And Lesion Log

Repeatable collection with minimum support for six rows in V1.

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| lesion_index | Row Number | Integer | System | System | Lesion Log | Sequence only |
| lesion_location | Location | String | Conditional | Endoscopist, Unit Admin | Lesion Log | Required for non-empty row |
| lesion_size_mm | Size mm | Integer | Conditional | Endoscopist, Unit Admin | Lesion Log | Required for non-empty row |
| lesion_morphology | Morphology | String | Conditional | Endoscopist, Unit Admin | Lesion Log | V1 text or controlled options later |
| resection_method | Resection Method | String | Conditional | Endoscopist, Unit Admin | Lesion Log | Text in V1 |
| complete_resection | Complete Resection | Boolean | Conditional | Endoscopist, Unit Admin | Lesion Log | Required for non-empty row |
| retrieved | Retrieved | Boolean | Conditional | Endoscopist, Nurse, Unit Admin | Lesion Log | Required for non-empty row |
| specimen_container_ref | Container | String | No | Endoscopist, Nurse, Unit Admin | Lesion Log | Links to specimen record where applicable |

## 7. Resection And Follow-Up Detail

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| small_polyp_technique | Small Polyp Technique | Enum | No | Endoscopist | Resection And Plan | `cold_snare`, `hot_snare`, `forceps`, `other` |
| small_polyp_technique_note | Technique Note | Text | Conditional | Endoscopist | Resection And Plan | Required when `other` |
| advanced_resection_type | Advanced Resection | Enum Multi | No | Endoscopist | Resection And Plan | EMR, ESD, piecemeal, en_bloc, not_applicable |
| tattoo_status | Tattoo | Enum | No | Endoscopist | Resection And Plan | `na`, `placed` |
| tattoo_location_note | Tattoo Location | Text | Conditional | Endoscopist | Resection And Plan | Required when placed |
| hemostasis_or_closure | Hemostasis Or Defect Closure | String | No | Endoscopist | Resection And Plan | Text in V1 |
| impression | Impression | Text | Yes | Endoscopist | Resection And Plan | Blocking |
| pathology_status | Pathology | Enum | Yes | Endoscopist | Resection And Plan | `none`, `pending_tracking_required` |
| surveillance_interval_value | Surveillance Interval Value | String | No | Endoscopist | Resection And Plan | Use string to allow years or months in V1 |
| surveillance_interval_pending_pathology | Interval Pending Pathology | Boolean | No | Endoscopist | Resection And Plan |  |
| surveillance_interval_reason | Interval Reason | Enum | No | Endoscopist | Resection And Plan | `guideline_based`, `prep_quality`, `piecemeal_resection`, `other` |
| surveillance_interval_reason_note | Interval Reason Note | Text | Conditional | Endoscopist | Resection And Plan | Required when `other` |
| adverse_event_plan | Adverse Event Plan | Enum | Yes | Endoscopist | Resection And Plan | `routine_discharge`, `observe_admit`, `other` |
| adverse_event_plan_note | Adverse Event Plan Note | Text | Conditional | Endoscopist | Resection And Plan | Required when `other` |
| informed_patient | Patient Informed | Boolean | No | Endoscopist, Nurse | Resection And Plan |  |
| informed_referrer | Referrer Informed | Boolean | No | Endoscopist, Nurse | Resection And Plan |  |
| written_instructions_given | Written Instructions Given | Boolean | No | Endoscopist, Nurse | Resection And Plan |  |

## 8. Specimen Records

Repeatable collection.

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| specimen_id | Specimen ID | UUID | System | System | Specimens | Internal identifier |
| container_label | Container | String | Conditional | Endoscopist, Nurse, Unit Admin | Specimens | Required when a specimen row exists |
| specimen_site | Site | String | Conditional | Endoscopist, Nurse, Unit Admin | Specimens |  |
| specimen_count | Number | Integer | No | Endoscopist, Nurse, Unit Admin | Specimens | Optional in V1 |
| test_question | Test Or Question | Text | No | Endoscopist, Nurse, Unit Admin | Specimens | Optional |
| label_verified | Label Verified | Boolean | Conditional | Endoscopist, Nurse, Unit Admin | Specimens | Required when specimen row exists |

## 9. Follow-Up Tasks

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| followup_task_id | Follow-Up Task ID | UUID | System | System | Tasks | Internal identifier |
| case_id_ref | Case Reference | FK Case | System | System | Tasks | Parent case |
| task_type | Task Type | Enum | Yes | System, Endoscopist, Nurse, Unit Admin | Tasks | `pathology_review`, `result_communication`, `specimen_resolution`, `surveillance_followup` |
| task_owner_user_id | Task Owner | FK User | Yes | Endoscopist, Nurse, Unit Admin | Tasks |  |
| due_date | Due Date | Date | No | Endoscopist, Nurse, Unit Admin | Tasks | Optional in V1 |
| task_status | Task Status | Enum | System | Endoscopist, Nurse, Unit Admin | Tasks | `open`, `in_progress`, `closed`, `cancelled` |
| resolution_note | Resolution Note | Text | Conditional | Endoscopist, Nurse, Unit Admin | Tasks | Required when closing or cancelling |
| closed_at | Closed At | DateTime | System | System | Tasks |  |
| closed_by_user_id | Closed By | FK User | System | System | Tasks |  |

## 10. Finalization Snapshot

| Field ID | Label | Type | Required | Editable By | Screen Step | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| finalized_at | Finalized At | DateTime | System | System | Review And Sign-Off | Set on sign-off |
| finalized_by_user_id | Finalized By | FK User | System | System | Review And Sign-Off | Signer |
| template_version | Template Version | String | System | System | Review And Sign-Off | Preserved snapshot |
| report_narrative_snapshot | Narrative Snapshot | Text | System | System | Review And Sign-Off | Locked at finalization |
| pdf_asset_ref | PDF Asset Reference | String | System | System | Review And Sign-Off | Generated final PDF pointer |
