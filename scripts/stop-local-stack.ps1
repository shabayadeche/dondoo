param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-odoo-localhost-proxy.ps1")
if ($LASTEXITCODE -ne 0) {
  throw "Failed to stop the Odoo localhost proxy."
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-clinical-api.ps1") -Distro $Distro
if ($LASTEXITCODE -ne 0) {
  throw "Failed to stop the Clinical API."
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-odoo.ps1") -Distro $Distro
if ($LASTEXITCODE -ne 0) {
  throw "Failed to stop Odoo."
}

Write-Output "Local stack stopped."
