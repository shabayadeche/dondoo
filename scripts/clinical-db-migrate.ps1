param(
  [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$clinicalApiWindowsPath = Join-Path $repoRoot "services\\clinical_api"

function Convert-ToWslPath {
  param([string]$WindowsPath)

  $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
  $drive = $fullPath.Substring(0, 1).ToLowerInvariant()
  $suffix = $fullPath.Substring(2).Replace("\", "/")
  return "/mnt/$drive$suffix"
}

$clinicalApiLinuxPath = Convert-ToWslPath -WindowsPath $clinicalApiWindowsPath
$command = "source /home/shabaya/.venvs/phd-ass-clinical-api/bin/activate && cd '$clinicalApiLinuxPath' && export PYTHONPATH='$clinicalApiLinuxPath' && alembic upgrade head"

& wsl.exe -d $Distro -- bash -lc $command
if ($LASTEXITCODE -ne 0) {
  throw "Clinical API migrations failed."
}

Write-Output "Clinical API migrations applied."
