param(
  [string]$Creator = '',
  [string]$Project = 'E:\gameprogram\Blockudoku',
  [string]$LogDir = 'C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work',
  [int]$TimeoutMin = 8
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
. (Join-Path $PSScriptRoot '..\..\..\scripts\resolve_environment.ps1')
$creator = Resolve-GameToolPath -Name COCOS_2X -Path $Creator -Leaf CocosCreator.exe -Fallback @('C:\ProgramData\cocos\editors\Creator\2.4.13\CocosCreator.exe')
$log = Join-Path $LogDir 'build_android.log'
$err = Join-Path $LogDir 'build_android.err'

$p = Start-Process -FilePath $creator `
  -ArgumentList '--path', $Project, '--build', 'platform=android;debug=true' `
  -RedirectStandardOutput $log -RedirectStandardError $err -PassThru -WindowStyle Hidden
$deadline = (Get-Date).AddMinutes($TimeoutMin)
while (-not $p.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 5 }
if (-not $p.HasExited) {
  Stop-Process -Id $p.Id -Force
  Write-Host 'BUILD TIMEOUT'
  exit 1
}
Write-Host 'builder exited'
Get-Content -Encoding UTF8 $log | Select-String -Pattern 'Successfully|error|Error' | Select-Object -Last 5 | ForEach-Object { Write-Host $_.Line }
$out = Join-Path $Project 'build\jsb-link\frameworks\runtime-src\proj.android-studio'
if (Test-Path $out) { Write-Host "OUTPUT OK: $out" } else { Write-Host 'OUTPUT MISSING'; exit 1 }
