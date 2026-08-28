# Odoo Deployment Notes

## Current Installer Artifact

Local installer provided:

- `C:\Users\charl\Downloads\odoo_19.0.20260818_all.deb`

Local metadata inspection showed:

- Package: `odoo`
- Version: `19.0.20260818`
- Architecture: `all`
- Maintainer: `Odoo S.A. <info@odoo.com>`

## Important Constraint

This is a Debian package.

It should be deployed on a supported Linux host, typically Debian or Ubuntu, not on the Windows workspace used for planning and scaffolding.

## Package Characteristics Observed

- Includes `control.tar.zst` and `data.tar.zst`
- Depends on Python 3 runtime packages, PostgreSQL client, font packages, and related system libraries
- Recommends PostgreSQL and `python3-ldap`

## Deployment Recommendation

### Use Odoo On A Separate Linux Host Or Container

Recommended shape:

- Odoo on Linux
- PostgreSQL for Odoo
- Separate PostgreSQL for the clinical service, unless you intentionally choose a shared database server with separate databases
- Reverse proxy in front of Odoo and the clinical API

## Hybrid Architecture Note

The presence of the Odoo installer does not change the main architecture rule:

- Odoo remains the back-office and bridge layer
- the clinical API remains the owner of procedure workflow, finalization, audit, and report generation

## Suggested Next Odoo Tasks

1. Prepare a Linux deployment target for Odoo 19.
2. Install the base Odoo package there.
3. Mount or copy `services/odoo_addons/phd_ass_bridge` into the Odoo addons path.
4. Configure the bridge settings in Odoo after the clinical API has a reachable base URL.
