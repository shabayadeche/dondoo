# Endoscopy Reporting App Project Plan

## 1. Product Summary

This product is a clinician-facing progressive web application for structured endoscopy reporting, quality data capture, specimen tracking, and follow-up management.

It will run as:

- A web application for desktop and tablet use in the endoscopy unit
- An installable progressive web app experience for Android and iPhone users from the same codebase

The product is not a full EMR. Its first responsibility is to help clinical staff complete accurate procedure documentation quickly and consistently.

## 2. Product Vision

Create one system that allows staff to:

- Start a procedure case quickly
- Complete a structured report during or immediately after the procedure
- Generate a clean narrative procedure note automatically
- Track specimens, pathology, and follow-up tasks to closure
- Capture quality indicators in a format that can be audited later

## 3. Core Product Goals

- Reduce endoscopy documentation time
- Improve completion of mandatory safety and quality fields
- Standardize reporting across procedure types
- Support both workstation and mobile workflows without duplicating engineering effort
- Keep final signed records traceable and auditable

## 4. Non-Goals For V1

- Full patient registration or hospital master records
- Billing and coding automation
- Full anesthesia charting
- Scheduling and theater booking
- Deep EMR, LIS, or PACS integrations
- Advanced analytics beyond essential operational reporting

## 5. Users And Roles

### Primary Users

- Endoscopist
- Assisting nurse
- Unit administrator

### Secondary Users

- Quality reviewer
- Department lead

## 6. Supported Procedure Types

The system should be designed for four procedure families:

- EGD
- Colonoscopy
- ERCP
- EUS

Recommended rollout order:

1. Colonoscopy
2. EGD
3. ERCP
4. EUS

## 7. Product Principles

- Structured first: key data should be captured in structured fields, not buried in free text
- Narrative second: the app should generate a readable procedure note from structured inputs
- Fast at point of care: common actions must require minimal taps or clicks
- One workflow, adaptive sections: shared workflow across all procedures, with procedure-specific modules
- Final means locked: signed records must be versioned, locked, and auditable
- Mobile supports speed: mobile should optimize for review, draft completion, and follow-up, not long-form data entry only

## 8. Recommended Technical Direction

### Frontend

- React
- TypeScript
- Installable PWA shell
- Responsive layouts for desktop, tablet, iPhone, and Android

This supports a shared clinician-facing PWA for web and mobile users from one codebase.

### Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy and Alembic

### Shared Packages

- Form schemas
- Validation rules
- Domain types
- Report generation templates

## 9. High-Level Architecture

### Client Apps

- Universal app shell
- Shared components
- Shared form engine
- Shared validation
- Platform-specific layout adjustments for web and mobile

### Backend Services

- Authentication and authorization
- Procedure and report APIs
- Specimen and follow-up APIs
- Audit logging
- PDF generation
- Notification and reminder jobs

### Storage

- PostgreSQL for structured data
- Object storage for attachments and generated documents

## 10. MVP Scope

### V1 Must Include

- Login and role-based access
- Patient and case creation
- Shared preprocedure safety section
- Colonoscopy reporting module
- Draft autosave
- Final sign-off and record locking
- Narrative report generation
- PDF and print output
- Specimen log
- Follow-up task queue
- Audit trail

### V1 Should Include If Time Permits

- EGD module
- Basic operational dashboard
- Mobile push notifications for follow-up tasks

### V1 Excludes

- ERCP and EUS workflows
- Offline sync
- External system integrations
- Advanced image capture and annotation
- Detailed quality benchmarking dashboards

## 11. Information Architecture

### Main Navigation

- Dashboard
- Cases
- New Procedure
- Tasks
- Reports
- Admin

### Case Detail Structure

- Patient Summary
- Procedure Details
- Safety And Consent
- Findings
- Interventions
- Specimens
- Impression And Plan
- Generated Report
- Audit History

## 12. Core User Flows

### Flow 1: Create And Complete A New Procedure

1. User opens `New Procedure`
2. User selects procedure type
3. User searches or enters patient details
4. User completes shared safety fields
5. User completes procedure-specific sections
6. User reviews generated narrative note
7. User signs and finalizes report
8. System creates follow-up tasks if required

### Flow 2: In-Progress Case Resume

1. User opens `Cases`
2. User filters for drafts or active cases
3. User resumes incomplete documentation
4. User completes missing sections
5. User finalizes report

### Flow 3: Specimen And Follow-Up Tracking

1. User opens `Tasks`
2. User filters pending specimen or pathology actions
3. User reviews related case
4. User records result communication or closure action
5. System updates task status and audit log

## 13. UX Strategy

### UX Goals

- Minimize cognitive load during documentation
- Prevent omission of mandatory fields
- Make progress visible at all times
- Reduce duplicate entry
- Support interruption and resume

### UX Patterns

- Step-based wizard for procedure entry
- Sticky progress bar showing completion state
- Conditional sections that appear only when relevant
- Inline validation instead of end-of-form error floods
- Autosave with visible save state
- Summary review before final sign-off

### UX Rules

- Never show all fields at once
- Use defaults and recent values where clinically safe
- Use chips, toggles, and segmented controls for frequent choices
- Keep free-text fields secondary to structured fields
- Require explicit confirmation before final sign-off

## 14. UI Plan

### UI Direction

The UI should feel clinical, calm, and task-focused rather than consumer styled.

Design characteristics:

- Clean spacing and strong hierarchy
- High readability
- Clear section grouping
- Minimal decorative noise
- Strong status visibility for draft, pending, final, and overdue states

### Visual System

- Neutral base with one medical-trust accent color
- High-contrast text and form labels
- Large touch targets on tablet and mobile
- Consistent iconography for status, specimens, alerts, and follow-up

### Core Components

- App shell
- Side navigation on web
- Bottom tab or drawer navigation on mobile
- Stepper
- Procedure cards
- Section headers with completion state
- Structured input controls
- Repeating table or list rows for lesions and specimens
- Task cards
- Report preview pane
- Signature and confirmation modal

## 15. Responsive Behavior

### Web And Tablet

- Primary environment for full documentation
- Two-column layouts where useful
- Persistent side navigation
- Report preview available beside form on larger screens
- Tables for lesion and specimen logs

### Mobile

- Single-column task-focused layout
- Bottom navigation
- Large sticky primary actions
- Collapse long sections into progressive steps
- Prioritize case lookup, draft completion, task follow-up, and sign-off

## 16. Key Screens

### 1. Login

- Username or email
- Password
- Forgot password
- Facility branding

### 2. Dashboard

- Active drafts
- Pending follow-up tasks
- Recent finalized cases
- Quick actions for new procedure and resume draft

### 3. New Procedure Start

- Procedure type selector
- Patient search or new patient entry
- Staff assignment
- Start case action

### 4. Procedure Workspace

- Stepper navigation
- Form sections
- Save state
- Validation highlights
- Generated narrative preview

### 5. Findings And Lesion Log

- Repeating rows
- Structured descriptors
- Inline summary generation

### 6. Specimen Log

- Container label
- Site
- Method
- Tracking state

### 7. Review And Sign-Off

- Missing field summary
- Generated report preview
- Final confirmation
- Signature action

### 8. Tasks

- Filter by status
- Overdue indicators
- Quick complete actions

### 9. Reports

- Search and filter finalized reports
- Open PDF
- Export or print

### 10. Admin

- Users
- Roles
- Facility settings
- Template versions

## 17. Form Design Approach

Use a hybrid form model:

- Hard-model critical data in relational tables
- Store versioned section payloads for flexible procedure-specific content

This avoids two common failures:

- Over-hardcoding every procedure variation
- Over-generalizing the system into an analytics-poor form builder

## 18. Data And Compliance Requirements

- Audit every create, edit, finalize, and close action
- Lock finalized procedure records
- Preserve template version used at sign-off
- Track who entered and who signed data
- Keep follow-up and communication events time-stamped
- Support exportable reporting and record retrieval

## 19. Delivery Phases

### Phase 0: Discovery And Definition

Duration: 1 to 2 weeks

- Confirm workflow with stakeholders
- Confirm mandatory fields
- Confirm legal and clinical sign-off requirements
- Confirm whether patient data is created locally or sourced externally
- Produce PRD and data dictionary

### Phase 1: Foundations

Duration: 2 weeks

- Set up monorepo
- Create FastAPI backend and database schema
- Create clinician PWA shell
- Implement auth, roles, audit log, and design system

### Phase 2: Colonoscopy MVP

Duration: 3 to 4 weeks

- Build case creation
- Build shared safety workflow
- Build colonoscopy module
- Build draft/final flow
- Build generated report output
- Build specimen log and tasks

### Phase 3: UX Hardening And Pilot

Duration: 2 weeks

- Test with real users
- Reduce completion friction
- Improve validation and defaults
- Fix performance and responsiveness

### Phase 4: EGD Rollout

Duration: 2 to 3 weeks

- Add EGD module
- Reuse shared reporting engine
- Validate module-specific narrative generation

### Phase 5: Advanced Procedures

Duration: 4 to 6 weeks

- Add ERCP
- Add EUS
- Add advanced procedural sections

### Phase 6: Phase 2 Enhancements

- Basic analytics dashboards
- Notification improvements
- Integrations
- Offline support

## 20. Suggested Backlog By Epic

### Epic A: Platform Foundation

- Repository setup
- App shell
- Routing
- Authentication
- Role permissions

### Epic B: Case Management

- Patient lookup and entry
- Case creation
- Drafts and status management

### Epic C: Shared Procedure Engine

- Stepper workflow
- Shared safety fields
- Validation
- Autosave

### Epic D: Colonoscopy Module

- Procedure details
- Bowel prep
- Segmental exam
- Polyp and lesion log
- Follow-up recommendations

### Epic E: Report Generation

- Narrative template engine
- Review screen
- PDF export

### Epic F: Specimens And Tasks

- Specimen data capture
- Follow-up queue
- Closure workflow

### Epic G: Admin And Governance

- User management
- Template versions
- Audit review

## 21. Success Metrics

- Median procedure documentation time under 5 minutes after procedure completion
- More than 95 percent mandatory-field completion on finalized reports
- More than 90 percent same-day finalization
- Zero final record edits without audit trace
- All specimen-bearing cases linked to a follow-up state

## 22. Risks And Controls

### Risk: Scope Creep

Control:
Keep V1 limited to one main procedure module and essential follow-up features.

### Risk: Poor Mobile Usability

Control:
Design mobile as a focused workflow surface, not a compressed desktop form.

### Risk: Weak Clinical Adoption

Control:
Pilot with real clinicians early and optimize for completion speed.

### Risk: Analytics Failure

Control:
Model critical quality fields structurally from the start.

### Risk: Compliance Gaps

Control:
Implement locking, audit history, and versioned templates in the foundation phase.

## 23. Recommended Immediate Deliverables

The next planning outputs should be:

1. Product Requirements Document
2. Data dictionary for shared and colonoscopy-specific fields
3. Wireframes for the ten key screens
4. Database schema v1
5. Monorepo scaffold for clinician PWA plus backend

## 24. Build Recommendation

Build this as one universal product with:

- Web as the primary documentation surface
- Mobile as an installable PWA optimized for quick actions, review, and follow-up
- A shared Python clinical backend and shared design system from the beginning

This gives the product one source of truth, one engineering foundation, and a cleaner path to scale across procedures.
