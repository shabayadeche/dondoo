$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$html = Join-Path $root "endoscopy-app-approval-pack.html"
$pdf = Join-Path $root "endoscopy-app-approval-pack.pdf"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"

if (-not (Test-Path $chrome)) {
  throw "Chrome not found at $chrome"
}

$htmlUri = [Uri]::new($html)

& $chrome `
  --headless=new `
  --disable-gpu `
  --run-all-compositor-stages-before-draw `
  --virtual-time-budget=4000 `
  --print-to-pdf="$pdf" `
  $htmlUri.AbsoluteUri | Out-Null

if (-not (Test-Path $pdf)) {
  throw "PDF export failed: $pdf was not created."
}

Write-Output "Created $pdf"
