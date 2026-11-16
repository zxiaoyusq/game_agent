param(
  [ValidateRange(1024,65535)][int]$Port = 18761,
  [string]$Candidate = 'gameplay_layout_candidate'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$analysis = [IO.Path]::GetFullPath((Join-Path $project 'analysis'))
if ($Candidate -notmatch '^[A-Za-z0-9_-]+$') { throw 'Candidate must be a simple directory name.' }
$candidate = Join-Path (Join-Path $analysis $Candidate) 'game'
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath (Join-Path $candidate 'game.html'))) { throw 'Layout candidate is missing.' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = 'C:\Program Files\Python312\python.exe' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Python is missing; start an equivalent local HTTP server manually.' }
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { throw "Port $Port is already in use. Choose another port." }
$arguments = @('-m', 'http.server', "$Port", '--bind', '127.0.0.1', '--directory', ('"' + $analysis + '"'))
$server = Start-Process -FilePath $python -ArgumentList $arguments -WindowStyle Hidden -PassThru
$url = "http://127.0.0.1:$Port/$Candidate/game/game.html"
Write-Output "Candidate server PID: $($server.Id)"
Write-Output "Candidate directory: $candidate"
Write-Output "Desktop URL: $url"
Write-Output "MuMu: use adb reverse tcp:$Port tcp:$Port for the selected device, then open the same URL in its browser."
Write-Output 'This port has a separate browser storage origin from the formal preview when their ports differ; existing data on this port is retained.'
Write-Output 'Each candidate directory has a distinct service-worker scope; browser storage is still shared by pages on the same port.'
