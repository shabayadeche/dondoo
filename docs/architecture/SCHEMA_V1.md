# Schema V1

This is the initial database design for the shared workflow and colonoscopy MVP.

## Core Entities

### users

- id
- full_name
- email
- role
- is_active
- created_at
- updated_at

### patients

- id
- patient_identifier
- full_name_optional
- dob_optional
- age_text_optional
- sex
- created_at
- updated_at

Use a minimal patient model in V1 because demographics are entered locally first and broader master-data integration is deferred.

### cases

- id
- patient_id
- procedure_type
- case_status
- procedure_datetime
- facility_unit
- endoscopist_user_id
- assistant_nurse_user_id
- referrer_service
- finalized_at
- finalized_by_user_id
- template_version
- report_narrative_snapshot
- pdf_asset_ref
- created_at
- updated_at

### case_safety

- id
- case_id
- indication
- priority
- relevant_history
- asa_class
- allergies
- antithrombotic_plan
- consent_documented
- team_pause_completed
- sedation_anesthesia
- monitor_spo2
- monitor_hr
- monitor_bp
- monitor_ecg
- monitor_capnography
- antibiotics_status
- pregnancy_status
- updated_at

### colonoscopy_details

- id
- case_id
- bowel_prep_agent
- prep_quality
- bbps_right
- bbps_transverse
- bbps_left
- bbps_total
- insertion_time
- cecum_reached
- cecal_landmark_appendiceal_orifice
- cecal_landmark_ileocecal_valve
- photo_cecum
- photo_pathology
- terminal_ileum_status
- withdrawal_time_minutes
- technical_limitation
- technical_limitation_note
- adverse_event_during_procedure
- adverse_event_note
- uc_mayo_score
- crohn_score
- disease_extent
- impression
- pathology_status
- surveillance_interval_value
- surveillance_interval_pending_pathology
- surveillance_interval_reason
- surveillance_interval_reason_note
- adverse_event_plan
- adverse_event_plan_note
- informed_patient
- informed_referrer
- written_instructions_given
- updated_at

### colonoscopy_segments

- id
- case_id
- segment_name
- normal
- finding_note
- photo_taken
- sort_order

Unique key:

- case_id + segment_name

### colonoscopy_lesions

- id
- case_id
- sort_order
- location
- size_mm
- morphology
- resection_method
- complete_resection
- retrieved
- specimen_container_ref

### specimens

- id
- case_id
- container_label
- specimen_site
- specimen_count
- test_question
- label_verified
- created_at
- updated_at

### followup_tasks

- id
- case_id
- task_type
- owner_user_id
- status
- due_date
- resolution_note
- closed_at
- closed_by_user_id
- created_at
- updated_at

### audit_events

- id
- case_id_optional
- actor_user_id
- actor_role
- event_type
- entity_type
- entity_id
- reason_optional
- payload_json
- created_at

## Design Notes

- Use relational tables for audit-critical and analytics-critical fields.
- Store audit diffs in `payload_json`.
- Preserve finalized narrative snapshot on `cases`.
- Keep future procedure modules in separate detail tables rather than forcing all procedures into a single sparse table.

## Future Extension Path

- `egd_details`
- `egd_findings`
- `ercp_details`
- `ercp_devices`
- `ercp_followup`
- `eus_details`
- `eus_lesions`
- `eus_tissue_acquisition`
