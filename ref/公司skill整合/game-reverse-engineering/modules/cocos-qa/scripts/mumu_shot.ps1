param(
  [string]$AdbPath = '',
  [string]$Apk = 'E:\gameprogram\Blockudoku\build\jsb-link\frameworks\runtime-src\proj.android-studio\app\build\outputs\apk\release\Blockudoku-release.apk',
  [string]$OutDir = 'C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work\mumu_qa',
  [string]$Prefix = 'shot',
  [int]$Shots = 1,
  [int]$IntervalSec = 3,
  [int]$BootWaitSec = 8,
  [switch]$SkipInstall
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\..\scripts\resolve_environment.ps1')
$adb = Resolve-GameToolPath -Name ANDROID_PLATFORM_TOOLS -Path $AdbPath -Leaf adb.exe -Fallback @('E:\AndroidSdk\platform-tools\adb.exe')
$mumu = 'F:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe'

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# ensure the emulator instance is running
$info = (& $mumu info -v 0 2>&1 | Out-String | ConvertFrom-Json)
if (-not $info.is_android_started) {
  Write-Host 'MuMu not running, launching...'
  & $mumu control -v 0 launch
  Start-Sleep -Seconds 25
}

# resolve the adb endpoint from mumu-cli (printed by `adb -c connect`)
$endpoint = (& $mumu adb -v 0 -c connect 2>&1 | Out-String).Trim()
if ($endpoint -match '(\d+\.\d+\.\d+\.\d+:\d+)') { $endpoint = $Matches[1] }
if (-not $endpoint) { $endpoint = '127.0.0.1:16384' }
Write-Host "adb endpoint: $endpoint"
& $adb connect $endpoint
Start-Sleep -Seconds 2

if (-not $SkipInstall) {
  if (-not (Test-Path -LiteralPath $Apk)) { throw "APK not found: $Apk" }
  & $adb install -r $Apk
  if ($LASTEXITCODE -ne 0) { throw 'adb install failed' }
}

& $adb shell am start -n org.cocos2d.blockudoku/org.cocos2dx.javascript.AppActivity
Write-Host "boot wait ${BootWaitSec}s"
Start-Sleep -Seconds $BootWaitSec

for ($i = 1; $i -le $Shots; $i++) {
  $file = Join-Path $OutDir ("$Prefix" + '_' + $i.ToString('00') + '.png')
  $proc = Start-Process -FilePath $adb -ArgumentList 'exec-out','screencap','-p' `
    -RedirectStandardOutput $file -NoNewWindow -Wait -PassThru
  if ($proc.ExitCode -eq 0 -and (Get-Item $file).Length -gt 0) {
    Write-Host "shot OK: $file"
  } else {
    Write-Host "shot FAILED: $file"
  }
  if ($i -lt $Shots) { Start-Sleep -Seconds $IntervalSec }
}
