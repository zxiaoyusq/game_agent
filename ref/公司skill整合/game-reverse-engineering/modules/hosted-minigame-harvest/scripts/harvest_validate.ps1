<#
.SYNOPSIS
  Validate a harvested mini-game set against gates G1-G5.

.DESCRIPTION
  G1 package magic (PK)      G2 package MD5 == manifest md5
  G3 art magic == declared extension
  G4 every local asset referenced by index.html exists
  G5 no mojibake in index.html
  (G6 catalog completeness is checked by harvest_store_pull.ps1)

  Exit code 0 = all green, 1 = at least one gate failed.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$Html = "index.html"
)

$ErrorActionPreference="Stop"
[Console]::OutputEncoding=[Text.Encoding]::UTF8

function Get-Magic([string]$path){
  $fs=[System.IO.File]::OpenRead($path)
  try{
    $b=New-Object byte[] 16; $n=$fs.Read($b,0,16)
    return ,@($b[0..([Math]::Max(0,$n-1))])
  } finally { $fs.Dispose() }
}

$manPath = Join-Path $Root "manifest.csv"
$artPath = Join-Path $Root "art_manifest.csv"
$htmlPath= Join-Path $Root $Html
$fail = 0

# ---------------- G1 / G2 ----------------
Write-Host "== G1/G2 package integrity ==" -ForegroundColor Cyan
$man = @(Import-Csv $manPath -Encoding UTF8)
$g1=0;$g2=0;$bad=@()
foreach($m in $man){
  $zip = $null
  if($m.dir){ $d = Join-Path $Root $m.dir; if(Test-Path $d){ $zip = Get-ChildItem $d -Filter *.zip -ErrorAction SilentlyContinue | Select-Object -First 1 } }
  if(-not $zip){ $bad += "MISSING  $($m.apiName)"; $g1++; continue }
  $b = Get-Magic $zip.FullName
  if(-not ($b.Length -ge 2 -and $b[0] -eq 0x50 -and $b[1] -eq 0x4B)){ $bad += "NOT_PK   $($m.apiName)"; $g1++; continue }
  if($m.md5){
    $h=(Get-FileHash $zip.FullName -Algorithm MD5).Hash.ToLower()
    if($h -ne $m.md5){ $bad += "MD5BAD   $($m.apiName)"; $g2++; continue }
  }
}
Write-Host ("  G1 failures: {0}    G2 failures: {1}   (checked {2})" -f $g1,$g2,$man.Count)
$bad | Select-Object -First 15 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
if($g1 -or $g2){ $fail++ }

# ---------------- G3 ----------------
# Covers BOTH on-disk art/ files AND base64 data: URIs inlined into the HTML.
Write-Host "== G3 art real format ==" -ForegroundColor Cyan
$g3=0; $g3disk=0; $g3inline=0
Get-ChildItem $Root -Recurse -Directory -Filter art | ForEach-Object {
  foreach($f in Get-ChildItem $_.FullName -File){
    $b = Get-Magic $f.FullName
    $ext = $f.Extension.ToLower()
    $ok=$false
    if($ext -eq '.jpg' -or $ext -eq '.jpeg'){ $ok = ($b[0] -eq 0xFF -and $b[1] -eq 0xD8 -and $b[2] -eq 0xFF) }
    elseif($ext -eq '.png'){ $ok = ($b[0] -eq 0x89 -and $b[1] -eq 0x50 -and $b[2] -eq 0x4E -and $b[3] -eq 0x47) }
    elseif($ext -eq '.gif'){ $ok = ($b[0] -eq 0x47 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46) }
    elseif($ext -eq '.webp'){ $ok = ($b.Length -ge 12 -and $b[0] -eq 0x52 -and $b[1] -eq 0x49 -and $b[2] -eq 0x46 -and $b[3] -eq 0x46 -and $b[8] -eq 0x57 -and $b[9] -eq 0x45 -and $b[10] -eq 0x42 -and $b[11] -eq 0x50) }
    $g3disk++
    if(-not $ok){ $g3++; Write-Host ("    {0} (declared {1})" -f $f.FullName.Replace("$Root\",''), $ext) -ForegroundColor Red }
  }
}

# inline base64 payloads: decode the head and compare magic against the DECLARED mime
if(Test-Path $htmlPath){
  $h3=[System.IO.File]::ReadAllText($htmlPath,[System.Text.Encoding]::UTF8)
  foreach($m in [regex]::Matches($h3,'src="data:image/([a-z]+);base64,([A-Za-z0-9+/=]+)"')){
    $decl=$m.Groups[1].Value
    $g3inline++
    $s=$m.Groups[2].Value
    $head=$s.Substring(0,[Math]::Min(64,$s.Length))
    while($head.Length % 4 -ne 0){ $head=$head.Substring(0,$head.Length-1) }
    $ok=$false
    try{
      $b=[Convert]::FromBase64String($head)
      $real = if($b[0] -eq 0xFF -and $b[1] -eq 0xD8){"jpeg"} elseif($b[0] -eq 0x89 -and $b[1] -eq 0x50){"png"} elseif($b[0] -eq 0x47 -and $b[1] -eq 0x49){"gif"} elseif($b.Length -ge 12 -and $b[0] -eq 0x52 -and $b[8] -eq 0x57){"webp"} else {"other"}
      $ok = ($real -eq $decl)
    }catch{ $ok=$false }
    if(-not $ok){ $g3++; Write-Host ("    inline payload declared={0} magic-mismatch" -f $decl) -ForegroundColor Red }
  }
}
Write-Host ("  G3 failures: {0}   (disk={1}, inline={2})" -f $g3,$g3disk,$g3inline)
if($g3){ $fail++ }

# ---------------- G4 / G5 ----------------
Write-Host "== G4/G5 catalog page ==" -ForegroundColor Cyan
if(-not (Test-Path $htmlPath)){
  Write-Host "  index.html missing -> G4 FAIL, G5 FAIL" -ForegroundColor Red
  $fail++
} else {
  $html=[System.IO.File]::ReadAllText($htmlPath,[System.Text.Encoding]::UTF8)
  # NOTE: collect only the src attribute values, and NEVER run Test-Path on a data: URI
  # (a multi-MB base64 path makes Test-Path take tens of seconds and always returns false).
  $allSrc=[regex]::Matches($html,'src="([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
  $dataRefs=@($allSrc | Where-Object { $_ -like 'data:*' })
  $fileRefs=@($allSrc | Where-Object { $_ -notlike 'data:*' } | Sort-Object -Unique)
  $missing=@()
  foreach($r in $fileRefs){
    if($r -match '^https?:'){ $missing += "REMOTE $r"; continue }
    if(-not (Test-Path -LiteralPath (Join-Path $Root ($r -replace '/','\')))){ $missing += "MISSING $r" }
  }
  $remote=([regex]::Matches($html,'src="http')).Count
  $repl=[string][char]0xFFFD
  $moji=([regex]::Matches($html,[regex]::Escape($repl))).Count
  $latin=([regex]::Matches($html,'[\u00C2\u00C3\u00E2\u00EF][\u0080-\u00BF]')).Count
  if($missing.Count -gt 0){ $fail++ }
  if($moji -or $latin){ $fail++ }
  Write-Host ("  inline-data={0}  file-refs={1}  missing={2}  remote-src={3}  U+FFFD={4}  latin1-pairs={5}" -f $dataRefs.Count,$fileRefs.Count,@($missing).Count,$remote,$moji,$latin)
  $missing | Select-Object -First 15 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
  # extra: basic structural count
  Write-Host ("  cards={0}   folder-divs={1}   img-tags={2}" -f `
    ([regex]::Matches($html,'<section class="card"')).Count, `
    ([regex]::Matches($html,'class="folder"')).Count, `
    ([regex]::Matches($html,'<img ')).Count)
}

Write-Host ""
if($fail -eq 0){ Write-Host "ALL GATES PASS (G1-G5)" -ForegroundColor Green; exit 0 }
else { Write-Host ("GATES FAILED: {0} group(s)" -f $fail) -ForegroundColor Red; exit 1 }
