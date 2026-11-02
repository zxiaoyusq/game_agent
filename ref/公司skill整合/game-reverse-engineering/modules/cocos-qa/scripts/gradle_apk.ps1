param(
  [string]$AndroidSdk = '',
  [string]$AndroidNdk = '',
  [string]$JavaHome = '',
  [string]$ProjAndroid = 'E:\gameprogram\Blockudoku\build\jsb-link\frameworks\runtime-src\proj.android-studio',
  [string]$LogDir = 'C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work'
)
$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

. (Join-Path $PSScriptRoot '..\..\..\scripts\resolve_environment.ps1')
$env:NDK_ROOT = Resolve-GameToolPath -Name ANDROID_NDK -Path $AndroidNdk -Fallback @('E:\AndroidSdk\ndk\23.2.8568313')
$env:ANDROID_SDK_ROOT = Resolve-GameToolPath -Name ANDROID_SDK -Path $AndroidSdk -Fallback @('E:\AndroidSdk')
$env:ANDROID_HOME = $env:ANDROID_SDK_ROOT
$jdkCandidate = Get-Command javac -ErrorAction SilentlyContinue
$jdkFallback = if ($jdkCandidate) { Split-Path -Parent (Split-Path -Parent $jdkCandidate.Source) } else { '' }
$env:JAVA_HOME = Resolve-GameToolPath -Name JAVA_HOME -Path $JavaHome -Fallback @($jdkFallback)
$ProjAndroid = (Resolve-Path -LiteralPath $ProjAndroid).Path

# CRITICAL: wipe the incremental merge cache or stale index.js ships in the APK
$assets = Join-Path $ProjAndroid 'app\build\intermediates\assets\release'
$checkedAssets = [IO.Path]::GetFullPath($assets)
$checkedProject = [IO.Path]::GetFullPath($ProjAndroid).TrimEnd('\') + '\'
if (-not $checkedAssets.StartsWith($checkedProject, [StringComparison]::OrdinalIgnoreCase)) { throw 'Gradle cache target escaped the project' }
if (Test-Path -LiteralPath $checkedAssets) {
  Remove-Item -LiteralPath $checkedAssets -Recurse -Force
  Write-Host 'stale mergeAssets cache removed'
}

$gradleLog = Join-Path $LogDir 'gradle_release.log'
$gradleErr = Join-Path $LogDir 'gradle_release.err'
Push-Location $ProjAndroid
try {
  # run gradlew via cmd with stdout/stderr redirected to files: avoids
  # PowerShell turning native stderr warnings into terminating errors
  $proc = Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/c','gradlew.bat','assembleRelease','--no-daemon' `
    -RedirectStandardOutput $gradleLog -RedirectStandardError $gradleErr `
    -PassThru -Wait -NoNewWindow
  $gradleCode = $proc.ExitCode
} finally {
  Pop-Location
}
if ($gradleCode -ne 0) {
  Write-Host "GRADLE FAILED exit=$gradleCode"
  Get-Content -Encoding UTF8 $gradleErr | Select-Object -Last 20 | ForEach-Object { Write-Host $_ }
  exit 1
}
Write-Host 'BUILD SUCCESSFUL'
Get-Content -Encoding UTF8 $gradleLog | Select-String -Pattern 'BUILD SUCCESSFUL|BUILD FAILED' | Select-Object -Last 1 | ForEach-Object { Write-Host $_.Line }

$apk = Join-Path $ProjAndroid 'app\build\outputs\apk\release\Blockudoku-release.apk'
if (-not (Test-Path -LiteralPath $apk)) { Write-Host 'APK MISSING'; exit 1 }
Write-Host "APK OK: $apk ($((Get-Item $apk).Length) bytes)"

# Content check: extract the game bundle and grep for build markers
$tmp = Join-Path $env:TEMP ('apk_check_' + [DateTime]::Now.ToString('HHmmss'))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  $zip = Join-Path $tmp 'apk.zip'
  Copy-Item -LiteralPath $apk -Destination $zip -Force
  Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
  $js = @(
    (Join-Path $tmp 'assets\assets\main\index.js'),
    (Join-Path $tmp 'assets\index.js')
  ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $js) { Write-Host 'game index.js NOT FOUND in APK'; exit 1 }
  $content = Get-Content -Raw -Encoding UTF8 $js
  foreach ($marker in @('var CELL = 38;', 'SMOOTH_DAMP_TIME')) {
    if ($content.Contains($marker)) { Write-Host "MARKER OK: $marker" } else { Write-Host "MARKER MISSING: $marker" }
  }
} finally {
  Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
