# AWS Deployment Prerequisites

The GitHub Actions workflow deploys the PWA through AWS Systems Manager, not SSH. This keeps the SSH private key outside GitHub and avoids exposing a remote login path to CI.

## Current production target

- Application/API: `app.kumbuo.com`
- Restricted Odoo host: `odoo.kumbuo.com`
- Region: `eu-north-1`
- EC2 instance: `i-05d3d64d172807382`

## Instance setup

Attach an instance profile with `AmazonSSMManagedInstanceCore` to the EC2 instance. It must then appear as a managed node in Systems Manager. The host also needs Node.js 22, the repository checkout at `/srv/phd-ass/current`, and an approved secret-manager-backed, read-only Git credential for `git fetch origin main`.

Create `/srv/phd-ass/pwa/releases` and make the deployment account able to update its `current` symlink. Nginx should serve `/srv/phd-ass/pwa/current` as described in the production runbook.

## GitHub environment setup

Create the protected `production` GitHub Environment and configure these variables:

- `AWS_DEPLOY_ROLE_ARN`
- `PRODUCTION_INSTANCE_ID` set to `i-05d3d64d172807382`
- `AWS_REGION` set to `eu-north-1`
- `PRODUCTION_SMOKE_URL` set to `https://app.kumbuo.com/health` once TLS and DNS are live

The IAM role used by GitHub Actions must trust GitHub OIDC for `repo:shabayadeche/dondoo:environment:production`, and be limited to `ssm:SendCommand`, `ssm:GetCommandInvocation`, and `ssm:ListCommandInvocations` for this instance and the `AWS-RunShellScript` document.

## Security follow-up

The production root volume is encrypted with AWS KMS, detailed monitoring is enabled, and the instance is online in Systems Manager. Keep SSH restricted to the administrator CIDR; do not add a CI SSH key when Systems Manager is available.
