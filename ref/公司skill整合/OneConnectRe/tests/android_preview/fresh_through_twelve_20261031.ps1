# This operates on the isolated copy; test scripts clear One Connect storage on port 18749.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $root
$target = Join-Path $root 'analysis/first_three_endtoend/game'
New-Item -ItemType Directory -Force -Path $target | Out-Null
Get-ChildItem -LiteralPath (Join-Path $root 'game') -Force | Copy-Item -Destination $target -Recurse -Force
& 'C:\Program Files\Python312\python.exe' 'tools/build_offline_worker.py' --game-dir $target
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$scripts = @('fresh_first_six_20261031.cjs','fresh_run_mumu-six-to-seven.cjs','fresh_run_mumu-seven-to-eight.cjs','fresh_run_mumu-eight-to-nine.cjs','fresh_run_mumu-nine-to-ten.cjs','fresh_run_mumu-ten-to-eleven.cjs','fresh_run_mumu-eleven-to-twelve.cjs','fresh_run_mumu-twelve-to-thirteen.cjs')
foreach ($script in $scripts) {
  node (Join-Path $PSScriptRoot $script)
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
