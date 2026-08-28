# Development Readiness Pack

This folder now anchors the implementation baseline for the React PWA, FastAPI clinical API, and Odoo bridge.

## Build Scope Locked For V1

- Shared procedure workflow
- Colonoscopy-complete app workflow
- Odoo draft templates for EGD, colonoscopy, ERCP, and EUS
- Generated narrative report
- PDF output
- Specimen logging
- Follow-up task queue
- Final sign-off and audit trail

## Document Index

### Product

- [PRD](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/PRD.md)
- [Data Dictionary V1](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/DATA_DICTIONARY_V1.md)
- [Screen Field Map V1](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/SCREEN_FIELD_MAP_V1.md)
- [Roles And Permissions](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/ROLES_AND_PERMISSIONS.md)
- [Audit And Sign-Off Rules](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/AUDIT_AND_SIGNOFF_RULES.md)
- [MVP Acceptance Criteria](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/MVP_ACCEPTANCE_CRITERIA.md)
- [Backlog V1](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/BACKLOG_V1.md)
- [Dondoo Brand Guidelines](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/DONDOO_BRAND_GUIDELINES.md)
- [Dondoo Branding Guide (canonical)](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/product/DONDOO_BRANDING_GUIDE.md)

### Architecture

- [ADR-001 Universal App Monorepo](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ADR-001-universal-app-monorepo.md)
- [ADR-003 React PWA And FastAPI Direction](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ADR-003-react-pwa-fastapi.md)
- [ADR-002 Self-Hosted Hybrid Odoo Architecture](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ADR-002-self-hosted-hybrid-odoo.md)
- [Integration Boundaries](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/INTEGRATION_BOUNDARIES.md)
- [Odoo And App Form Ownership](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ODOO_APP_FORM_OWNERSHIP.md)
- [Odoo Deployment Notes](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/ODOO_DEPLOYMENT_NOTES.md)
- [Schema V1](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/SCHEMA_V1.md)
- [Repo Structure](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/architecture/REPO_STRUCTURE.md)

### Operations

- [Production Deployment](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/operations/PRODUCTION_DEPLOYMENT.md)
- [Production Release Checklist](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/docs/operations/PRODUCTION_RELEASE_CHECKLIST.md)

## Implementation Baseline As Of August 25, 2026

- React PWA is the primary clinician frontend.
- FastAPI clinical API is the canonical clinical backend and session owner.
- Database persistence, case revisions, PDF downloads, follow-up tasks, and audit history are active in the clinical API.
- Odoo is optional for identity, mirrors, reference-data administration, and bridge workflows.
- `apps/app` and `services/api` remain only as legacy references during cleanup.

## V1 Working Defaults As Of August 25, 2026

- Report identity is anchored by the external case ID, patient identifier, and procedure datetime.
- Patient demographics are entered locally in V1; broader master-data integration is deferred.
- Only `operations_admin` and `workspace_admin` may return a ready case to draft or reopen a finalized case, and a reopen reason is mandatory.
- Pathology results are entered and tracked manually in V1.
- Mobile sign-off is allowed only for `endoscopist` users under the same validation and role checks as desktop sign-off.
- The clinical API owns canonical authentication, session state, clinical persistence, and audit rules; Odoo remains an optional integration layer.

## Still Pending Outside The Repo

- Stakeholder sign-off on the working defaults above
- Pilot usability validation with real clinicians
- Production deployment execution, TLS certificate issuance, and secret provisioning
- Mobile install and release acceptance checks on iPhone and Android
