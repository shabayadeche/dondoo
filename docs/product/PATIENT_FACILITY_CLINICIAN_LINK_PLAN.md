# Patient, Facility, and Clinician Link Plan

## Decision

Add a patient-facility-endoscopist relationship as a first-class, time-aware
record. Do not store only one permanent `endoscopist_user_id` on the patient.

This accommodates referrals, clinician changes, and treatment at more than one
facility, while preserving the facility and endoscopist recorded on every
procedure as the historical source of truth for that procedure.

## Current State

- A clinical case already links a patient, facility, facility unit, and
  endoscopist.
- A patient registry record already links to its clinical cases.
- A clinician already has permitted facilities, and care-team records link a
  facility, endoscopist, and nurse.
- There is no direct patient-level link that identifies the patient's usual
  facility or treating endoscopist, and no history of such assignments.

## Target Model

Create `phd.ass.patient.care.relationship` in the Odoo patient-admin module.

| Field | Purpose |
| --- | --- |
| `patient_id` | Required patient registry record |
| `facility_id` | Required facility where the relationship applies |
| `facility_unit_id` | Optional usual unit within that facility |
| `endoscopist_user_id` | Required endoscopist for this patient-facility relationship |
| `relationship_type` | `primary_endoscopist` or `historical_endoscopist` |
| `start_date`, `end_date` | Effective dates; an empty end date means current |
| `is_primary` | One current primary relationship per patient and relationship type |
| `active`, `note` | Administrative status and a non-clinical explanation |

Validate that the selected unit belongs to the facility and that the
endoscopist has access to that facility. Never alter an existing case when a
relationship changes.

## User Experience

1. Operations staff manage a patient's care relationships from a new
   **Care relationships** tab in the patient record.
2. When a user selects an existing patient for a new case, the app proposes
   that patient's active primary facility, unit, and endoscopist.
3. The user may override the suggestion for the current case. The case keeps
   the selected values as its own historical snapshot.
4. After facility selection, show only clinicians assigned to that facility;
   after endoscopist selection, show only the matching care-team nurses.
5. If the chosen case values differ from an active primary relationship, show
   a small confirmation such as "One-time referral / different treatment
   site"; do not block urgent work.

## Implementation Sequence

### 1. Confirm policy

- Agree which roles may create and retire care relationships.
- Confirm whether one primary endoscopist is required or merely suggested.

### 2. Build master data in Odoo

- Add the relationship model, constraints, access rules, patient tab, and
  patient list indicators for primary facility and endoscopist.
- Add an indexed active-relationship search for patient lookup.
- Migrate existing data conservatively: infer relationships only where a
  patient has a consistent recent case history; otherwise leave them blank for
  staff review.

### 3. Expose safe lookup data to the clinical API

- Extend the bridge with a read endpoint that returns the patient's active
  relationship suggestions.
- Return only the fields required to prefill a case and the relationship ID;
  keep full patient administration within Odoo.
- Keep the clinical API/PWA as the owner of the clinical case workflow and
  retain the case header values in its payload and final report.

### 4. Update the PWA case-start flow

- On patient selection, request the active relationship and prefill empty
  facility, unit, and endoscopist fields.
- Preserve a user's deliberate values; do not overwrite fields they have
  already changed.
- Reapply the existing facility-to-clinician filtering and add a clear
  indication when the values are suggestions rather than confirmed case data.

### 5. Verify and roll out

- Test multi-facility patients, changed endoscopists, referrals, inactive
  relationships, and cases without a default relationship.
- Test that finalized and historical cases remain unchanged after updates to
  the patient relationship.
- Pilot with operations staff before bulk migration; audit creation, updates,
  retirement, and case overrides.

## Acceptance Criteria

- A patient can have multiple current or historical facility/clinician
  relationships without duplicate ambiguity.
- A new case can use a valid active relationship as a prefill suggestion.
- An invalid clinician/facility or unit/facility combination cannot be saved.
- A user can document a legitimate one-off referral without changing the
  patient's primary relationship.
- Changing a patient relationship never changes an existing case or finalized
  report.
