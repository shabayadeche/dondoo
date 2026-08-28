#!/usr/bin/env bash
set -euo pipefail

config_path="${1:?missing odoo config path}"

export PYTHONPATH=/opt/odoo-19.0.20260818/usr/lib/python3/dist-packages
exec python3 -m odoo -c "$config_path"
