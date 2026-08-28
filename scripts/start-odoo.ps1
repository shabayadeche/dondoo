param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "odoo-wsl-host.pid"
$stdoutLogFile = Join-Path $runtimeDir "odoo-wsl-host.out.log"
$stderrLogFile = Join-Path $runtimeDir "odoo-wsl-host.err.log"
$odooConfigWindowsPath = Join-Path $runtimeDir "odoo-local.conf"
$launcherWindowsPath = Join-Path $PSScriptRoot "wsl-start-odoo.sh"

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

if (-not (Test-Path $odooConfigWindowsPath)) {
  throw "Odoo config file not found at $odooConfigWindowsPath"
}

if (-not (Test-Path $launcherWindowsPath)) {
  throw "Odoo launcher script not found at $launcherWindowsPath"
}

if (Test-WslPortListening -Port "8069" -CurrentDistro $Distro) {
  Write-Output "Odoo already running on WSL port 8069."
  exit 0
}

$odooConfigLinuxPath = Convert-ToWslPath -WindowsPath $odooConfigWindowsPath
$launcherLinuxPath = Convert-ToWslPath -WindowsPath $launcherWindowsPath

Remove-Item $stdoutLogFile, $stderrLogFile -Force -ErrorAction SilentlyContinue

$process = Start-Process -FilePath "wsl.exe" `
  -ArgumentList @("-d", $Distro, "--", "bash", $launcherLinuxPath, $odooConfigLinuxPath) `
  -RedirectStandardOutput $stdoutLogFile `
  -RedirectStandardError $stderrLogFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -NoNewline

for ($attempt = 0; $attempt -lt 30; $attempt++) {
  Start-Sleep -Seconds 1
  if (Test-WslPortListening -Port "8069" -CurrentDistro $Distro) {
    $pidValue = if (Test-Path $pidFile) { (Get-Content $pidFile -Raw).Trim() } else { "" }
    Write-Output "Odoo started. WSL PID $pidValue."
    Write-Output "WSL URL: http://127.0.0.1:8069 inside WSL"
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
throw "Odoo failed to start.`nSTDOUT:`n$stdoutLog`nSTDERR:`n$stderrLog"
