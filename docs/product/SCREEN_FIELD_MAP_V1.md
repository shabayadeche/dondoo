# Screen Field Map V1

This document maps the V1 clinician PWA interface to the field dictionary.

Current implementation note:

- The clinician PWA workflow documented below remains colonoscopy-first.
- The Odoo clinical workspace now exposes additional procedure-specific pages for EGD, ERCP, and EUS draft authoring.

## Navigation Surfaces

### Web And Tablet

- Dashboard
- Cases
- New Procedure
- Tasks
- Reports
- Admin

### Mobile

- Home
- Tasks
- Case Review
- Reports

## Case Workflow Steps

### Step 1: Start Case

Purpose:
Create or open a case and establish identity and ownership.

Fields:

- procedure_type
- patient_identifier
- procedure_datetime
- dob_or_age
- sex
- facility_unit
- endoscopist_user_id
- referrer_service
- assistant_nurse_user_id

Actions:

- Save draft
- Continue to safety

## Step 2: Safety

Purpose:
Capture shared safety and indication fields before procedure-specific steps.

Fields:

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

Actions:

- Save draft
- Continue to prep and completeness

## Step 3: Prep And Completeness

Purpose:
Capture bowel prep and colonoscopy completeness.

Fields:

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

Actions:

- Save draft
- Continue to segment exam

## Step 4: Segment Exam

Purpose:
Capture segment-level findings and optional IBD activity.

Fields:

- segment_exam rows:
  - terminal_ileum
  - cecum
  - ascending_colon
  - transverse_colon
  - descending_colon
  - sigmoid_colon
  - rectum_retroflexion
- uc_mayo_score
- crohn_score
- disease_extent

Actions:

- Save draft
- Continue to lesion log

## Step 5: Lesion Log

Purpose:
Capture repeatable lesion and polyp entries.

Fields:

- lesion_index
- lesion_location
- lesion_size_mm
- lesion_morphology
- resection_method
- complete_resection
- retrieved
- specimen_container_ref

Actions:

- Add row
- Remove row
- Continue to specimens and plan

## Step 6: Specimens And Plan

Purpose:
Capture specimen data, resection notes, clinical interpretation, and communication plan.

Fields:

- specimen rows:
  - container_label
  - specimen_site
  - specimen_count
  - test_question
  - label_verified
- small_polyp_technique
- small_polyp_technique_note
- advanced_resection_type
- tattoo_status
- tattoo_location_note
- hemostasis_or_closure
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

Actions:

- Save draft
- Continue to review

## Step 7: Review And Sign-Off

Purpose:
Show validation state, preview generated report, and finalize.

Read-only or system fields:

- case_status
- blocking validation summary
- report_narrative_snapshot preview
- finalized_at preview once finalized
- finalized_by_user_id preview once finalized

Actions:

- Back to edit
- Finalize
- Export PDF after finalization

## Tasks Screen

Purpose:
Manage follow-up tasks.

Fields shown:

- followup_task_id
- task_type
- task_owner_user_id
- due_date
- task_status
- resolution_note
- closed_at
- closed_by_user_id

Actions:

- Reassign task
- Mark in progress
- Close task
- Cancel task with reason

## Reports Screen

Purpose:
Find and open finalized reports.

Fields shown:

- patient_identifier
- procedure_datetime
- endoscopist_user_id
- case_status
- finalized_at

Actions:

- Open report
- Export PDF

## Admin Screen

Purpose:
Govern users, template versions, and controlled reopen actions.

Fields shown:

- user list
- role assignments
- template versions
- reopen reason input

Actions:

- Update user role
- Create template version
- Reopen finalized case
