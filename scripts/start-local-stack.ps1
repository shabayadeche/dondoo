param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

function Get-HttpStatus {
  param([string]$Url)

  $status = & curl.exe -s -o NUL -w "%{http_code}" --max-time 5 $Url
  if ($LASTEXITCODE -ne 0) {
    return "unreachable"
  }
  return $status
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-odoo.ps1") -Distro $Distro
if ($LASTEXITCODE -ne 0) {
  throw "Failed to start Odoo."
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-clinical-api.ps1") -Distro $Distro
if ($LASTEXITCODE -ne 0) {
  throw "Failed to start the Clinical API."
}

if ((Get-HttpStatus -Url "http://127.0.0.1:8069/web/login") -eq "200") {
  Write-Output "Odoo is directly reachable from Windows localhost; proxy startup skipped."
} else {
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-odoo-localhost-proxy.ps1") -Distro $Distro
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to start the Odoo localhost proxy."
  }
}

Write-Output "Local stack started."
Write-Output "Clinical API: http://127.0.0.1:8000/openapi.json"
Write-Output "Odoo: http://127.0.0.1:8069/web/login"
