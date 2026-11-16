# Runs on an isolated URL; caller must back up and restore the MuMu local storage.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $root
$revision = (& git rev-parse --short HEAD).Trim()
$name = "fresh_regression_$revision"
$base = Join-Path $root "analysis/$name"
$game = Join-Path $base 'game'
New-Item -ItemType Directory -Force -Path $game | Out-Null
Get-ChildItem -LiteralPath (Join-Path $root 'game') -Force | Copy-Item -Destination $game -Recurse -Force
& 'C:\Program Files\Python312\python.exe' 'tools/build_offline_worker.py' --game-dir $game
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$scripts = @('fresh_first_six_20261031.cjs','fresh_run_mumu-six-to-seven.cjs','fresh_run_mumu-seven-to-eight.cjs','fresh_run_mumu-eight-to-nine.cjs','fresh_run_mumu-nine-to-ten.cjs','fresh_run_mumu-ten-to-eleven.cjs','fresh_run_mumu-eleven-to-twelve.cjs','fresh_run_mumu-twelve-to-thirteen.cjs')
foreach ($script in $scripts) {
  $text = [IO.File]::ReadAllText((Join-Path $PSScriptRoot $script)).Replace('first_three_endtoend',$name).Replace('tests/evidence/mumu_fresh',"analysis/$name/mumu_fresh")
  $copy = Join-Path $base $script
  [IO.File]::WriteAllText($copy,$text,[Text.UTF8Encoding]::new($false))
  node $copy
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
