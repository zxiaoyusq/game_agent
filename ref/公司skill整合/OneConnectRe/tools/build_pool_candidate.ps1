param(
  [Parameter(Mandatory=$true)][string]$PoolFile
)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$pool = (Resolve-Path -LiteralPath $PoolFile).Path
if (-not (Test-Path -LiteralPath $pool -PathType Leaf)) { throw 'Pool file not found.' }
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
  $python = 'C:\Program Files\Python312\python.exe'
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Python runtime not found.' }
$name = 'pool_candidate_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$destination = Join-Path (Join-Path $project 'analysis') $name
if (Test-Path -LiteralPath $destination) { throw 'Candidate destination already exists; retry later.' }
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_gameplay_layout_candidate.py') --output $destination --pools $pool
if ($LASTEXITCODE -ne 0) { throw 'Candidate build failed. Review the error above.' }
Write-Output "Candidate: $destination\game\game.html"
Write-Output "Local server: powershell.exe -NoProfile -File `"$PSScriptRoot\open_layout_candidate.ps1`" -Candidate $name -Port 18762"
Write-Output 'Choose another port if 18762 is already in use.'
Write-Output 'Independent candidate only. Actual display and gameplay require user verification.'
