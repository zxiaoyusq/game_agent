<#
.SYNOPSIS
  Hosted store mini-game bulk harvester (generic).

.DESCRIPTION
  Resolves games from a hosted storefront API, downloads the ORIGINAL package
  bodies (MD5-verified) plus art assets (icon/hotgame/banner/theme/preview) and
  copy text, then writes/updates manifest.csv + art_manifest.csv.

  Endpoint paths/shapes are parameters because every store differs; the AHA case
  values are only the defaults. See ../references/store-api-contract.md.

  Target file lines, either form:
      <gameId>|<DisplayName>      -> resolved by id (preferred, no ambiguity)
      <DisplayName>               -> resolved by keyword search

.NOTES
  ASCII-only on purpose: PowerShell 5.1 misreads non-BOM UTF-8 .ps1 files.
  See ../references/powershell-harvest-pitfalls.md
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TargetFile,
  [string]$Root = ".\out",

  # --- API wiring ---
  [string]$ApiBase       = "https://api.ahagamecenter.com",
  [string]$DetailPath    = "/ahaGames/detail/game?gameId={0}",
  [string]$SearchPath    = "/searcher/v2/search",
  # search body template; {0}=keyword {1}=pageNo {2}=pageSize
  [string]$SearchBody    = '{"query":{"keyword":"{0}","pageNo":{1},"pageSize":{2}}}',
  [string]$BatchPath     = "/app/game/offline-home",   # returns hotGameImageLink; may cap silently
  [int]   $BatchSize     = 6,
  [int]   $PageSize      = 20,

  # --- asset field names in the detail payload ---
  [string]$FieldIcon     = "iconPictureLink",
  [string]$FieldBanner   = "banner",
  [string]$FieldTheme    = "themePictureLink",
  [string]$FieldPreview  = "imageLink",
  [string]$FieldHot      = "hotGameImageLink",

  [int]   $DelayMs       = 1300,
  [switch]$SkipDownload,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$HDR = @{ "User-Agent"="okhttp/4.9.0"; "Content-Type"="application/json; charset=utf-8"; "Accept"="application/json" }

function Safe([string]$s){
  if([string]::IsNullOrWhiteSpace($s)){ return "unnamed" }
  $x = $s -replace '[^\w\u4e00-\u9fff\-\. ]','_'
  $x = $x -replace '\s+','_'
  if($x.Length -gt 60){ $x = $x.Substring(0,60) }
  return $x.Trim('_')
}

# PS 5.1 decodes bodies as Latin-1 -> decode raw bytes as UTF-8 explicitly (pitfall 3)
function Invoke-Json([string]$url,[string]$body=$null){
  for($t=1; $t -le 4; $t++){
    try{
      if($body){
        $r = Invoke-WebRequest -Uri $url -Method POST -UseBasicParsing -Headers $HDR `
             -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 40
      } else {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -Headers $HDR -TimeoutSec 40
      }
      return ([Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json)
    } catch {
      if($t -eq 4){ return $null }
      Start-Sleep -Milliseconds (700*$t)     # throttle; the API throttles bursts
    }
  }
  return $null
}

function Get-Detail([string]$id){
  $j = Invoke-Json ($ApiBase + ($DetailPath -f $id))
  if($j -and $j.code -eq 1000){ return $j.data }
  return $null
}

function Get-Search([string]$kw){
  $body = $SearchBody -f $kw, 1, $PageSize
  $j = Invoke-Json ($ApiBase + $SearchPath) $body
  if($j -and $j.code -eq 1000 -and $j.data.list){ return $j.data.list }
  return @()
}

function Norm([string]$s){ if($null -eq $s){return ""}; return ($s.ToLower() -replace '[^a-z0-9]','') }

# real image format from magic bytes (pitfall 5)
function Get-RealExt([string]$path){
  $fs=[System.IO.File]::OpenRead($path)
  try{
    $b=New-Object byte[] 16; $n=$fs.Read($b,0,16)
    if($n -lt 4){return $null}
    if($b[0] -eq 0xFF -and $b[1] -eq 0xD8 -and $b[2] -eq 0xFF){return '.jpg'}
    if($b[0] -eq 0x89 -and $b[1] -eq 0x50 -and $b[2] -eq 0x4E -and $b[3] -eq 0x47){return '.png'}
    if($b[0] -eq 0x47 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46){return '.gif'}
    if($n -ge 12 -and $b[0] -eq 0x52 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46 -and $b[3] -eq 0x46 -and
       $b[8] -eq 0x57 -and $b[9] -eq 0x45 -and $b[10] -eq 0x42 -and $b[11] -eq 0x50){return '.webp'}
    return $null
  } finally { $fs.Dispose() }
}

function Save-Art([string]$url,[string]$artDir,[string]$baseName,[string]$wantedExt){
  if([string]::IsNullOrWhiteSpace($url)){ return $null }
  $tmp = Join-Path $artDir ($baseName + $wantedExt)
  if(Test-Path $tmp){ return (Split-Path $tmp -Leaf) }
  try{
    Invoke-WebRequest -Uri (($url -split '\?')[0]) -OutFile $tmp -TimeoutSec 90 -UseBasicParsing
  } catch { return $null }
  if(-not (Test-Path $tmp) -or (Get-Item $tmp).Length -eq 0){ return $null }
  # rewrite to the REAL extension
  $real = Get-RealExt $tmp
  if($real -and $real -ne $wantedExt){
    $final = Join-Path $artDir ($baseName + $real)
    if(Test-Path $final){ Remove-Item $final -Force }
    Move-Item $tmp $final -Force
    return (Split-Path $final -Leaf)
  }
  return (Split-Path $tmp -Leaf)
}

# ---------------------------------------------------------------- main
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$manPath = Join-Path $Root "manifest.csv"
$artPath = Join-Path $Root "art_manifest.csv"

$lines = Get-Content $TargetFile -Encoding UTF8 | Where-Object { $_.Trim() -ne '' }
Write-Host ("== harvest: {0} targets -> {1} ==" -f $lines.Count, (Resolve-Path $Root)) -ForegroundColor Cyan

# parse targets
$targets = @()
foreach($ln in $lines){
  $ln = $ln.Trim()
  if($ln -match '\|'){ $p=$ln.Split('|'); $targets += [pscustomobject]@{ id=$p[0].Trim(); name=$p[1].Trim() } }
  else               { $targets += [pscustomobject]@{ id="";          name=$ln } }
}

# --- batch hotgame (chunked; assert returned == requested) ---
$hot = @{}
$ids = @($targets | Where-Object { $_.id -match '^\d+$' } | ForEach-Object { [int]$_.id })
if($ids.Count -gt 0 -and -not $SkipDownload){
  for($i=0; $i -lt $ids.Count; $i += $BatchSize){
    $slice = $ids[$i..([Math]::Min($i+$BatchSize-1,$ids.Count-1))]
    $body  = @{ ids = $slice } | ConvertTo-Json -Compress
    $j = Invoke-Json ($ApiBase + $BatchPath) $body
    $got = 0
    if($j -and $j.code -eq 1000){
      foreach($x in $j.data){
        $got++
        $h = $x.$FieldHot
        if($h){ $hot[[string]$x.id] = $h }
      }
    }
    # pitfalls 4: never trust a 200 alone
    if($got -ne $slice.Count){
      Write-Warning ("  batch {0}: requested {1} but got {2} - endpoint may silently cap" -f ($i/$BatchSize+1), $slice.Count, $got)
    }
    Start-Sleep -Milliseconds $DelayMs
  }
  Write-Host (" hotgame urls resolved: {0}" -f $hot.Count) -ForegroundColor Green
}

# --- load existing manifests (idempotent re-runs) ---
$manById=@{}; if(Test-Path $manPath){ foreach($r in Import-Csv $manPath -Encoding UTF8){ $manById[[string]$r.gameId]=$r } }
$artById=@{}; if(Test-Path $artPath){ foreach($r in Import-Csv $artPath -Encoding UTF8){ $artById[[string]$r.id]=$r } }

$n=0
foreach($t in $targets){
  $n++
  Write-Host ("[{0,3}/{1}] {2}" -f $n,$targets.Count, $(if($t.id){"$($t.id)  $($t.name)"}else{$t.name})) -ForegroundColor White

  # ---- resolve ----
  $d=$null; $how="BY_ID"
  if($t.id -match '^\d+$'){
    $d = Get-Detail $t.id
  } else {
    $cands = Get-Search $t.name
    $picked=$null
    if($cands.Count -gt 0){
      $nn = Norm $t.name
      $picked = $cands | Where-Object { (Norm $_.name) -eq $nn } | Select-Object -First 1
      if($picked){ $how="EXACT" } else {
        $picked = $cands | Where-Object { $cn=(Norm $_.name); $cn.Length -ge 5 -and ($nn -like "*$cn*" -or $cn -like "*$nn*") } | Select-Object -First 1
        if($picked){ $how="CONTAINS" } else { $picked=$cands[0]; $how="FUZZY" }
      }
    }
    if($picked){ $t.id=[string]$picked.id; $d = Get-Detail $t.id }
  }
  if(-not $d){ Write-Host "        !! resolve failed" -ForegroundColor Red; Start-Sleep -Milliseconds $DelayMs; continue }

  $name = if($d.name){ $d.name } else { $t.name }
  $dirName = "{0}_{1}" -f $t.id, (Safe $name)
  $dir = Join-Path $Root $dirName
  $artDir = Join-Path $dir "art"
  New-Item -ItemType Directory -Force -Path $artDir | Out-Null

  # ---- package ----
  $bUrl=""; $bMd5=""; $bSize=0; $bName=""; $status="NO_BUNDLE"
  $b = $null
  if($d.bundles -and $d.bundles.Count -gt 0){ $b = $d.bundles[0] }
  if($b){
    $bUrl=$b.url; $bMd5=$b.md5; $bSize=$b.size; $bName=$b.name; $status="OK"
    if(-not $SkipDownload){
      $zipPath = Join-Path $dir ((Safe $name) + ".zip")
      $need = $true
      if((Test-Path $zipPath) -and -not $Force){
        if((Get-FileHash $zipPath -Algorithm MD5).Hash.ToLower() -eq $bMd5){ $need=$false; $status="CACHED" }
      }
      if($need){
        try{
          Invoke-WebRequest -Uri $bUrl -OutFile $zipPath -TimeoutSec 600 -UseBasicParsing
          $got = (Get-FileHash $zipPath -Algorithm MD5).Hash.ToLower()
          if($got -eq $bMd5){ $status="OK" }
          else { $status="MD5_MISMATCH"; Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }
        } catch { $status="DL_FAIL" }
      }
    }
  }

  # ---- art ----
  $files=@()
  if(-not $SkipDownload){
    $fa = Save-Art $d.$FieldIcon    $artDir "icon"    ".webp"; if($fa){ $files+=$fa }
    $fh = Save-Art $hot[[string]$t.id] $artDir "hotgame" ".webp"; if($fh){ $files+=$fh }
    $fb = Save-Art $d.$FieldBanner  $artDir "banner"  ".webp"; if($fb){ $files+=$fb }
    $ft = Save-Art $d.$FieldTheme   $artDir "theme"   ".webp"; if($ft){ $files+=$ft }
    $fp = Save-Art $d.$FieldPreview $artDir "preview" ".gif";  if($fp){ $files+=$fp }
  }

  $tags = if($d.tags){ ($d.tags | ForEach-Object { $_.name }) -join ", " } else { "" }

  $manById[[string]$t.id] = [pscustomobject]@{
    target=$t.name; match=$how; gameId=$t.id; apiName=$name; sizeBytes=$bSize; md5=$bMd5
    bundleUrl=$bUrl; link=$d.link; dir=$dirName; status=$status
  }
  $artById[[string]$t.id] = [pscustomobject]@{
    id=$t.id; dir=$dirName; name=$name; targetName=$t.name
    category=$d.category; rate=$d.rate; sizeText=$d.size; byteSize=$d.byteSize
    source=$d.source; likeNum=$d.likeNum
    iconUrl=$d.$FieldIcon; bannerUrl=$d.$FieldBanner; hotUrl=$hot[[string]$t.id]
    themeUrl=$d.$FieldTheme; previewUrl=$d.$FieldPreview
    artFiles=($files -join ",")
    gameLink=$d.link; description=$d.description; introduction=$d.introduction; tags=$tags
  }

  # per-game metadata sidecar
  $meta = [ordered]@{
    gameId=$t.id; apiName=$name; targetName=$t.name; match=$how
    bundleName=$bName; bundleUrl=$bUrl; bundleMd5=$bMd5; bundleSize=$bSize
    gameLink=$d.link; category=$d.category; rate=$d.rate; gameType=$d.type
    localFile=$(if($b){ (Safe $name)+".zip" } else { "" })
    verifiedAt=(Get-Date).ToString("s")
  }
  $meta | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $dir "gameInfo.json") -Encoding UTF8

  $col = if($status -in @("OK","CACHED")){"Green"} else {"Yellow"}
  Write-Host ("        {0,-11} {1,-34} art={2}" -f $status,$name,($files.Count)) -ForegroundColor $col
  Start-Sleep -Milliseconds $DelayMs
}

$manById.Values | Sort-Object {[int]$_.gameId} | Export-Csv $manPath -NoTypeInformation -Encoding UTF8
$artById.Values | Sort-Object {[int]$_.id}     | Export-Csv $artPath -NoTypeInformation -Encoding UTF8

# ---- gate G6: catalog completeness ----
$miss = @($targets | Where-Object { -not $manById.ContainsKey([string]$_.id) })
Write-Host ""
Write-Host ("== manifest rows: {0}   art rows: {1} ==" -f $manById.Count, $artById.Count) -ForegroundColor Cyan
if($miss.Count -gt 0){
  Write-Warning ("G6 FAIL: {0} target(s) missing from manifest:" -f $miss.Count)
  $miss | ForEach-Object { Write-Warning ("   {0}  {1}" -f $_.id, $_.name) }
} else {
  Write-Host "G6 PASS: every target has a manifest row" -ForegroundColor Green
}
Write-Host "next: harvest_build_catalog.ps1  then validate (G1-G5)"
