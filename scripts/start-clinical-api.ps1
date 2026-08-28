param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "clinical-api-wsl-host.pid"
$stdoutLogFile = Join-Path $runtimeDir "clinical-api-wsl-host.out.log"
$stderrLogFile = Join-Path $runtimeDir "clinical-api-wsl-host.err.log"
$clinicalApiWindowsPath = Join-Path $repoRoot "services\\clinical_api"
$launcherWindowsPath = Join-Path $PSScriptRoot "wsl-start-clinical-api.sh"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

function Convert-ToWslPath {
  param([string]$WindowsPath)

  $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
  $drive = $fullPath.Substring(0, 1).ToLowerInvariant()
  $suffix = $fullPath.Substring(2).Replace("\", "/")
  return "/mnt/$drive$suffix"
}

function Test-WslPortListening {
  param(
    [string]$Port,
    [string]$CurrentDistro
  )

  $check = & wsl.exe -d $CurrentDistro -- bash -lc "ss -ltn '( sport = :$Port )' | grep -q LISTEN"
  return $LASTEXITCODE -eq 0
}

if (Test-WslPortListening -Port "8000" -CurrentDistro $Distro) {
  Write-Output "Clinical API already running on WSL port 8000."
  exit 0
}

if (-not (Test-Path $launcherWindowsPath)) {
  throw "Clinical API launcher script not found at $launcherWindowsPath"
}

$clinicalApiLinuxPath = Convert-ToWslPath -WindowsPath $clinicalApiWindowsPath
$launcherLinuxPath = Convert-ToWslPath -WindowsPath $launcherWindowsPath

Remove-Item $stdoutLogFile, $stderrLogFile -Force -ErrorAction SilentlyContinue

$process = Start-Process -FilePath "wsl.exe" `
  -ArgumentList @("-d", $Distro, "--", "bash", $launcherLinuxPath, $clinicalApiLinuxPath) `
  -RedirectStandardOutput $stdoutLogFile `
  -RedirectStandardError $stderrLogFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -NoNewline

for ($attempt = 0; $attempt -lt 20; $attempt++) {
  Start-Sleep -Seconds 1
  if (Test-WslPortListening -Port "8000" -CurrentDistro $Distro) {
    $pidValue = if (Test-Path $pidFile) { (Get-Content $pidFile -Raw).Trim() } else { "" }
    Write-Output "Clinical API started. WSL PID $pidValue."
    Write-Output "Host URL: http://127.0.0.1:8000/openapi.json"
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
throw "Clinical API failed to start.`nSTDOUT:`n$stdoutLog`nSTDERR:`n$stderrLog"
