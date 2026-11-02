param(
  [string]$Root = 'E:\Gameprogram\blast-block-dragonbones-spine',
  [string]$Viewer = '',
  [string]$Report = 'E:\download\spine38_batch_report.csv',
  [string]$Progress = 'E:\download\spine38_batch_progress.log',
  [int]$Limit = 0
)
. (Join-Path $PSScriptRoot '..\..\..\scripts\resolve_environment.ps1')
$Viewer = Resolve-GameToolPath -Name SPINE_VIEWER -Path $Viewer
$ErrorActionPreference = 'Continue'
$java = (Get-Command java -ErrorAction SilentlyContinue).Source
if (-not $java) { $java = 'java' }

"group,result,stderr_bytes" | Set-Content -Path $Report -Encoding utf8
"" | Set-Content -Path $Progress -Encoding utf8

$dirs = Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -ne 'lib' }
$pass = 0; $fail = 0; $failures = @()
$i = 0
foreach ($d in $dirs) {
  $i++
  if ($Limit -gt 0 -and $i -gt $Limit) { break }
  $js = Get-ChildItem -LiteralPath $d.FullName -Filter '*.json' -File |
    Where-Object { $_.Name -ne 'index.json' } | Select-Object -First 1
  if (-not $js) {
    "{0},{1},{2}" -f $d.Name, 'NO_JSON', 0 | Add-Content -Path $Report -Encoding utf8
    $fail++; $failures += ($d.Name + ': no json')
    continue
  }
  $errLog = Join-Path $env:TEMP ('sv-err-' + $d.Name + '.txt')
  if (Test-Path -LiteralPath $errLog) { Remove-Item -LiteralPath $errLog -Force }
  $p = Start-Process -FilePath $java -ArgumentList @('-jar', $Viewer, ('"' + $js.FullName + '"')) `
    -RedirectStandardError $errLog -PassThru -WindowStyle Hidden
  Start-Sleep -Seconds 4
  $alive = -not $p.HasExited
  $errSize = if (Test-Path -LiteralPath $errLog) { (Get-Item -LiteralPath $errLog).Length } else { 0 }
  if ($alive -and $errSize -eq 0) {
    "{0},{1},{2}" -f $d.Name, 'PASS', $errSize | Add-Content -Path $Report -Encoding utf8
    $pass++
  } else {
    $errHead = ''
    if (Test-Path -LiteralPath $errLog) {
      $errHead = (Get-Content -LiteralPath $errLog -Raw -ErrorAction SilentlyContinue)
      if ($errHead.Length -gt 300) { $errHead = $errHead.Substring(0, 300) }
    }
    "{0},{1},{2}" -f $d.Name, 'FAIL', $errSize | Add-Content -Path $Report -Encoding utf8
    $fail++; $failures += ($d.Name + ': ' + ($errHead -replace "`r?`n", ' | '))
  }
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
  "{0}/{1} {2} pass={3} fail={4}" -f $i, $dirs.Count, $d.Name, $pass, $fail |
    Add-Content -Path $Progress -Encoding utf8
}
"SUMMARY pass={0} fail={1}" -f $pass, $fail | Add-Content -Path $Progress -Encoding utf8
if ($failures.Count -gt 0) {
  "FAILURES:" | Add-Content -Path $Progress -Encoding utf8
  $failures | ForEach-Object { Add-Content -Path $Progress -Encoding utf8 ('  ' + $_) }
}
