# Production Deployment

This runbook turns the active React PWA and FastAPI clinical API into a production deployment path.

## Recommended Topology

- one public HTTPS host for the clinician PWA
- Nginx serving the built PWA and proxying `/api` and `/health` to the clinical API on `127.0.0.1:8000`
- FastAPI bound only to localhost behind systemd
- PostgreSQL for the clinical API database
- Odoo reachable only from the clinical API or an internal reverse-proxy path

Reference files in this repo:

- [apps/pwa/.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/apps/pwa/.env.production.example)
- [services/clinical_api/.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/.env.production.example)
- [deploy/nginx/phd-ass.conf.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/deploy/nginx/phd-ass.conf.example)
- [deploy/systemd/phd-ass-clinical-api.service.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/deploy/systemd/phd-ass-clinical-api.service.example)

## Host Assumptions

- Ubuntu or Debian-like Linux host
- `systemd`
- `nginx`
- TLS certificate path managed outside the repo
- PostgreSQL already installed or managed separately
- deployment checkout at `/srv/phd-ass/current`
- Python virtual environment at `/srv/phd-ass/.venvs/phd-ass-clinical-api`
- built PWA assets published to `/srv/phd-ass/pwa/current`

## 1. Prepare Runtime Secrets

Create `/etc/phd-ass/clinical-api.env` from [services/clinical_api/.env.production.example](C:/Users/charl/OneDrive/Documents/GitHub/PhD-Ass/services/clinical_api/.env.production.example).

Required production values:

- `CLINICAL_API_LOCAL_AUTH_PASSWORD`
- `DATABASE_URL`
- `ALLOW_ORIGINS`
- `CLINICAL_API_TRUSTED_HOSTS`
- `ODOO_BRIDGE_API_KEY` if the Odoo bridge is enabled
- `ODOO_BRIDGE_BASE_URL` and `ODOO_BRIDGE_DB_NAME` if the Odoo bridge is enabled

Recommended ownership and permissions:

- owner `root:phdass`
- mode `0640`

## 2. Build And Publish The PWA

From the repo root:

```bash
npm ci
npm run build:pwa
```

Publish `apps/pwa/dist` to `/srv/phd-ass/pwa/current`.

Recommended production PWA env:

- leave `VITE_CLINICAL_API_BASE_URL` blank when Nginx proxies the API on the same public host
- set it explicitly only if the API is exposed on a different public origin

### GitHub Actions deployment

The repository workflow at `.github/workflows/ci-cd.yml` runs PWA type checks and builds plus the clinical API acceptance suite for pull requests and pushes to `develop` or `main`. A successful push to `main` deploys through AWS Systems Manager, builds the exact Git commit on the instance, publishes it as an immutable release, and atomically repoints `/srv/phd-ass/pwa/current`. It also restarts the clinical API and, when exactly one Odoo systemd service is present and its configuration explicitly includes `/srv/phd-ass/current/services/odoo_addons`, restarts Odoo so code-only bridge safeguards take effect. It fails safely if Odoo is present but that add-ons contract cannot be verified.

Create a GitHub Environment named `production`, protect it with the required reviewer(s), then configure these environment variables:

- `AWS_DEPLOY_ROLE_ARN`: IAM role assumed through GitHub Actions OIDC, restricted to the production environment
- `PRODUCTION_INSTANCE_ID`: the managed EC2 instance ID for `app.kumbuo.com`
- `AWS_REGION`: optional; defaults to `eu-north-1`
- `PRODUCTION_SMOKE_URL`: optional public health URL, for example `https://app.kumbuo.com/health`

The instance must be registered with Systems Manager (`AmazonSSMManagedInstanceCore`) and its local checkout at `/srv/phd-ass/current` must have a read-only GitHub deploy credential supplied through the approved secret manager. The GitHub OIDC role needs only `ssm:SendCommand` and command-invocation read access for this instance and the `AWS-RunShellScript` document. The current `app.kumbuo.com` instance (`i-05d3d64d172807382`, `eu-north-1`) needs an IAM instance profile before this job can run. The workflow deploys only the PWA; FastAPI service or database changes continue to use the controlled host release procedure below.

## 3. Provision The Clinical API Runtime

From the deployment checkout:

```bash
cd /srv/phd-ass/current/services/clinical_api
python3 -m venv /srv/phd-ass/.venvs/phd-ass-clinical-api
source /srv/phd-ass/.venvs/phd-ass-clinical-api/bin/activate
pip install --upgrade pip
pip install -e .
```

The systemd example runs `alembic upgrade head` before the API starts, so database migrations remain part of service startup.

## 4. Install The Systemd Service

Install the example unit:

```bash
sudo cp deploy/systemd/phd-ass-clinical-api.service.example /etc/systemd/system/phd-ass-clinical-api.service
sudo systemctl daemon-reload
sudo systemctl enable phd-ass-clinical-api.service
sudo systemctl start phd-ass-clinical-api.service
```

Validate:

```bash
sudo systemctl status phd-ass-clinical-api.service
curl -I http://127.0.0.1:8000/health
```

## 5. Install The Nginx Proxy

Install the example config:

```bash
sudo cp deploy/nginx/phd-ass.conf.example /etc/nginx/sites-available/phd-ass.conf
sudo ln -s /etc/nginx/sites-available/phd-ass.conf /etc/nginx/sites-enabled/phd-ass.conf
sudo nginx -t
sudo systemctl reload nginx
```

Before reloading in production, replace:

- `app.example.com`
- certificate paths
- any filesystem paths that differ from the recommended layout

## 6. Cutover Validation

Validate these behaviors against the public origin:

- `GET /health` returns `200`
- sign-in succeeds with production credentials
- draft create and save work
- ready-for-sign-off and finalize work
- finalized PDF download opens correctly
- reopen works only for `operations_admin` and `workspace_admin`
- follow-up task closure still requires a resolution note

## 7. Rollback Notes

- keep the previous PWA build as a separate directory such as `/srv/phd-ass/pwa/releases/<timestamp>`
- keep the previous systemd environment file until the new deployment is accepted
- restart the API with `sudo systemctl restart phd-ass-clinical-api.service`
- reload the previous static release by repointing the PWA `current` symlink and reloading Nginx
