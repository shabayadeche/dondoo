# Odoo Addons Workspace

This workspace holds custom Odoo modules for the self-hosted hybrid architecture.

## Current Modules

- `phd_ass_bridge`
- `phd_ass_patient_admin`
- `phd_ass_scheduling`
- `phd_ass_pathology_tracking`
- `zxs_entp_theme`

## Odoo Package Target

This scaffold is aligned to the locally available installer:

- `odoo_19.0.20260818_all.deb`

The package metadata was inspected locally and reports:

- Package: `odoo`
- Version: `19.0.20260818`
- Architecture: `all`
- Maintainer: `Odoo S.A.`

## Role In The Hybrid Architecture

These addons support:

- back-office administration
- integration settings
- controlled bridge endpoints
- patient registry management
- room and schedule operations
- specimen and pathology queue visibility
- backend theme customization for Odoo Community

These addons do not own:

- clinical procedure workflow state
- finalized report logic
- structured clinical source-of-truth data in V1

## Form Strategy

- Odoo should expose the same V1 field groups for visibility and operational review.
- Clinical fields must remain owned by the clinical API even when they are shown in Odoo.
- If an Odoo screen needs clinical editing later, it should submit through bridge endpoints instead of persisting a second clinical workflow in Odoo.
