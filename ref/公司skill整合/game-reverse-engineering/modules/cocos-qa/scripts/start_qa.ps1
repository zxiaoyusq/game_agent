param(
  [string]$WorkDir = 'C:\Users\Administrator\Documents\Codex\2026-08-04\c-users-administrator-documents-codex-2026\work',
  [string]$BuildDir = 'E:\gameprogram\Blockudoku\build\web-mobile',
  [int]$Port = 8123,
  [int]$CdpPort = 9224
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$profile = Join-Path $WorkDir ('chrome_profile_qa_' + [DateTime]::Now.ToString('HHmmss'))
New-Item -ItemType Directory -Path $profile -Force | Out-Null

$server = Start-Process -FilePath 'python' -ArgumentList '-m','http.server',$Port,'--directory',$BuildDir -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
Write-Host "server pid $($server.Id)"

$p = Start-Process -FilePath $chrome -ArgumentList @(
  '--headless=new',
  '--no-sandbox',
  '--disable-gpu',
  "--remote-debugging-port=$CdpPort",
  "--user-data-dir=$profile",
  '--window-size=720,1280',
  "http://127.0.0.1:$Port/index.html"
) -PassThru -WindowStyle Hidden
Write-Host "chrome pid $($p.Id) profile $profile"
Start-Sleep -Seconds 4
try {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1:$CdpPort/json/version" -UseBasicParsing -TimeoutSec 5
  Write-Host "CDP OK $($r.StatusCode)"
} catch {
  Write-Host "CDP not ready: $($_.Exception.Message)"
}
