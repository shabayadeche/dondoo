param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "odoo-wsl-host.pid"
$odooConfigWindowsPath = Join-Path $runtimeDir "odoo-local.conf"

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

if (Test-Path $odooConfigWindowsPath) {
  $odooConfigLinuxPath = Convert-ToWslPath -WindowsPath $odooConfigWindowsPath
  if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    if ($pidValue) {
      $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
      if ($process) {
        Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
      }
    }
  }

  $stopCommand = "pkill -f '^python3 -m odoo -c $odooConfigLinuxPath$' 2>/dev/null || true"
  & wsl.exe -d $Distro -- bash -lc $stopCommand | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to submit Odoo stop command to WSL."
  }
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

for ($attempt = 0; $attempt -lt 10; $attempt++) {
  if (-not (Test-WslPortListening -Port "8069" -CurrentDistro $Distro)) {
    Write-Output "Odoo stopped."
    exit 0
  }
  Start-Sleep -Seconds 1
}

throw "Odoo is still listening on port 8069 after the stop request."
