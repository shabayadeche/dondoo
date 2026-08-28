param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"

function Test-WslPortListening {
  param(
    [string]$Port,
    [string]$CurrentDistro
  )

  $check = & wsl.exe -d $CurrentDistro -- bash -lc "ss -ltn '( sport = :$Port )' | grep -q LISTEN"
  return $LASTEXITCODE -eq 0
}

function Get-HostPidValue {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    return ""
  }

  return (Get-Content $Path -Raw).Trim()
}

function Get-HttpStatus {
  param([string]$Url)

  $status = & curl.exe -s -o NUL -w "%{http_code}" --max-time 5 $Url
  if ($LASTEXITCODE -ne 0) {
    return "unreachable"
  }
  return $status
}

$odooPidFile = Join-Path $runtimeDir "odoo-wsl-host.pid"
$clinicalPidFile = Join-Path $runtimeDir "clinical-api-wsl-host.pid"
$proxyPidFile = Join-Path $runtimeDir "odoo-localhost-proxy.pid"
$odooPidValue = Get-HostPidValue -Path $odooPidFile
$clinicalPidValue = Get-HostPidValue -Path $clinicalPidFile
$proxyPidValue = Get-HostPidValue -Path $proxyPidFile
$odooHostRunning = $false
$clinicalHostRunning = $false
$proxyRunning = $false

if ($odooPidValue) {
  $odooProcess = Get-Process -Id $odooPidValue -ErrorAction SilentlyContinue
  $odooHostRunning = [bool]$odooProcess
}

if ($clinicalPidValue) {
  $clinicalProcess = Get-Process -Id $clinicalPidValue -ErrorAction SilentlyContinue
  $clinicalHostRunning = [bool]$clinicalProcess
}

if ($proxyPidValue) {
  $proxyProcess = Get-Process -Id $proxyPidValue -ErrorAction SilentlyContinue
  $proxyRunning = [bool]$proxyProcess
}

Write-Output "WSL distro: $Distro"
Write-Output "Odoo WSL port 8069: $(if (Test-WslPortListening -Port '8069' -CurrentDistro $Distro) { 'listening' } else { 'stopped' })"
Write-Output "Clinical API WSL port 8000: $(if (Test-WslPortListening -Port '8000' -CurrentDistro $Distro) { 'listening' } else { 'stopped' })"
Write-Output "Odoo WSL host process: $(if ($odooHostRunning) { "running (PID $odooPidValue)" } else { 'stopped' })"
Write-Output "Clinical API WSL host process: $(if ($clinicalHostRunning) { "running (PID $clinicalPidValue)" } else { 'stopped' })"
Write-Output "Odoo proxy on Windows: $(if ($proxyRunning) { "running (PID $proxyPidValue)" } else { 'stopped' })"
Write-Output "Host Odoo URL status: $(Get-HttpStatus -Url 'http://127.0.0.1:8069/web/login')"
Write-Output "Host Clinical API status: $(Get-HttpStatus -Url 'http://127.0.0.1:8000/openapi.json')"
Write-Output "Odoo host PID file: $odooPidValue"
Write-Output "Clinical API host PID file: $clinicalPidValue"
