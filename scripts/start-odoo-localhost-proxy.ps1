param(
  [string]$Distro = "Ubuntu",
  [int]$ListenPort = 8069,
  [int]$TargetPort = 8069
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "odoo-localhost-proxy.pid"
$stdoutLogFile = Join-Path $runtimeDir "odoo-localhost-proxy.out.log"
$stderrLogFile = Join-Path $runtimeDir "odoo-localhost-proxy.err.log"
$scriptPath = Join-Path $PSScriptRoot "odoo-localhost-proxy.mjs"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

function Test-ProxyProcess {
  if (-not (Test-Path $pidFile)) {
    return $null
  }

  $pidValue = (Get-Content $pidFile -Raw).Trim()
  if (-not $pidValue) {
    Remove-Item $pidFile -Force
    return $null
  }

  $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if (-not $process) {
    Remove-Item $pidFile -Force
    return $null
  }

  return $process
}

$existing = Test-ProxyProcess
if ($existing) {
  Write-Output "Proxy already running with PID $($existing.Id)"
  exit 0
}

if (Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue) {
  throw "Port $ListenPort on 127.0.0.1 is already in use."
}

$node = (Get-Command node -ErrorAction Stop).Source

$env:WSL_DISTRO = $Distro
$env:LOCAL_PORT = [string]$ListenPort
$env:TARGET_PORT = [string]$TargetPort

$process = Start-Process `
  -FilePath $node `
  -ArgumentList @($scriptPath) `
  -WorkingDirectory $repoRoot `
  -RedirectStandardOutput $stdoutLogFile `
  -RedirectStandardError $stderrLogFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -NoNewline

Start-Sleep -Seconds 2

if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
  $stdoutLog = if (Test-Path $stdoutLogFile) { Get-Content $stdoutLogFile -Raw } else { "" }
  $stderrLog = if (Test-Path $stderrLogFile) { Get-Content $stderrLogFile -Raw } else { "" }
  throw "Proxy failed to start.`nSTDOUT:`n$stdoutLog`nSTDERR:`n$stderrLog"
}

Write-Output "Proxy started with PID $($process.Id)"
