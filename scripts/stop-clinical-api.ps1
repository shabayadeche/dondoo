param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "clinical-api-wsl-host.pid"

function Test-WslPortListening {
  param(
    [string]$Port,
    [string]$CurrentDistro
  )

  $check = & wsl.exe -d $CurrentDistro -- bash -lc "ss -ltn '( sport = :$Port )' | grep -q LISTEN"
  return $LASTEXITCODE -eq 0
}

if (Test-Path $pidFile) {
  $pidValue = (Get-Content $pidFile -Raw).Trim()
  if ($pidValue) {
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }
  }
}

$stopCommand = "pkill -f '^.*/uvicorn app.main:app --host 127.0.0.1 --port 8000$' 2>/dev/null || true"
& wsl.exe -d $Distro -- bash -lc $stopCommand | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "Failed to submit Clinical API stop command to WSL."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

for ($attempt = 0; $attempt -lt 10; $attempt++) {
  if (-not (Test-WslPortListening -Port "8000" -CurrentDistro $Distro)) {
    Write-Output "Clinical API stopped."
    exit 0
  }
  Start-Sleep -Seconds 1
}

throw "Clinical API is still listening on port 8000 after the stop request."
