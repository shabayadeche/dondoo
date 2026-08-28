param(
  [string]$HostName = "127.0.0.1",
  [string]$Port = "4174",
  [string]$ClinicalApiBaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pwaRoot = Join-Path $repoRoot "apps\pwa"
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "pwa-vite.pid"
$stdoutLogFile = Join-Path $runtimeDir "pwa-vite.out.log"
$stderrLogFile = Join-Path $runtimeDir "pwa-vite.err.log"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

$existingListener = Get-NetTCPConnection -State Listen -LocalPort ([int]$Port) -ErrorAction SilentlyContinue
if ($existingListener) {
  Write-Output "PWA already running on http://$HostName`:$Port/."
  exit 0
}

Remove-Item $stdoutLogFile, $stderrLogFile -Force -ErrorAction SilentlyContinue

$env:VITE_CLINICAL_API_BASE_URL = $ClinicalApiBaseUrl
$process = Start-Process -FilePath "npm.cmd" `
  -ArgumentList @("run", "dev", "--", "--host", $HostName, "--port", $Port) `
  -WorkingDirectory $pwaRoot `
  -RedirectStandardOutput $stdoutLogFile `
  -RedirectStandardError $stderrLogFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -NoNewline

for ($attempt = 0; $attempt -lt 20; $attempt++) {
  Start-Sleep -Seconds 1
  if (Get-NetTCPConnection -State Listen -LocalPort ([int]$Port) -ErrorAction SilentlyContinue) {
    Write-Output "PWA started on http://$HostName`:$Port/."
    exit 0
  }
}

$process = if (Test-Path $pidFile) {
  $pidValue = (Get-Content $pidFile -Raw).Trim()
  if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }
} else {
  $null
}
if ($process) {
  Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
}

$stdoutLog = if (Test-Path $stdoutLogFile) { Get-Content $stdoutLogFile -Raw } else { "" }
$stderrLog = if (Test-Path $stderrLogFile) { Get-Content $stderrLogFile -Raw } else { "" }
throw "PWA failed to start.`nSTDOUT:`n$stdoutLog`nSTDERR:`n$stderrLog"
