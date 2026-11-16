# This is a local MuMu preview test. The same origin is shared by development copies.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $root
& 'C:\Program Files\Python312\python.exe' tests/setup-preinstalled-current.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
node tests/android_preview/performance-storage-guard.cjs save
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$result=0
try {
    node tests/android_preview/preinstalled_current_20261031.cjs
    $result=$LASTEXITCODE
    if($result -eq 0){node tests/android_preview/active_pairs_current_20261031.cjs;$result=$LASTEXITCODE}
} finally {
    & 'C:\Program Files\ADB\adb.exe' -s 127.0.0.1:16448 reverse tcp:18749 tcp:18750
    node tests/android_preview/performance-safe-menu.cjs
    node tests/android_preview/performance-storage-guard.cjs restore
    if($LASTEXITCODE -ne 0){$result=$LASTEXITCODE}
}
exit $result
