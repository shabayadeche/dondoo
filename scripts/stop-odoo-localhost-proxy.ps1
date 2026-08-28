param()

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "odoo-localhost-proxy.pid"
$stdoutLogFile = Join-Path $runtimeDir "odoo-localhost-proxy.out.log"
$stderrLogFile = Join-Path $runtimeDir "odoo-localhost-proxy.err.log"

if (-not (Test-Path $pidFile)) {
  Write-Output "Proxy is not running."
  exit 0
}

$pidValue = (Get-Content $pidFile -Raw).Trim()
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }

if ($process) {
  Stop-Process -Id $process.Id -Force
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Remove-Item $stdoutLogFile -Force -ErrorAction SilentlyContinue
Remove-Item $stderrLogFile -Force -ErrorAction SilentlyContinue
Write-Output "Proxy stopped."
