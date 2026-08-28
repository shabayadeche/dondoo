#!/usr/bin/env bash
set -euo pipefail

clinical_api_path="${1:?missing clinical api path}"

cd "$clinical_api_path"
source /home/shabaya/.venvs/phd-ass-clinical-api/bin/activate
export PYTHONPATH="$clinical_api_path"
alembic upgrade head
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
