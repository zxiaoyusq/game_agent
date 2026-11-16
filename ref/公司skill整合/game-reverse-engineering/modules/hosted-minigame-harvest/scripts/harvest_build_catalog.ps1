<#
.SYNOPSIS
  Build a single self-contained HTML catalog page for a harvested mini-game set.

.DESCRIPTION
  Reads manifest.csv + art_manifest.csv from -Root and emits index.html with one
  card per game: folder name, art assets, meta badges and copy text.

  Art filenames are resolved from the artFiles column (real extensions), never
  hardcoded, so CDN format mismatches are handled (see pitfalls ref, item 5).

.NOTES
  This file contains non-ASCII (Chinese) literals and MUST be saved as UTF-8 WITH BOM,
  otherwise PowerShell 5.1 mis-decodes it and format strings break.
  See ../references/powershell-harvest-pitfalls.md item 1.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$Title = "小游戏资源总览",
  [string]$SourceNote = "",
  [string[]]$OrderFiles = @()
)

$ErrorActionPreference="Stop"
Add-Type -AssemblyName System.Web
[Console]::OutputEncoding=[Text.Encoding]::UTF8

function Esc([string]$s){
  if($null -eq $s){ return "" }
  return [System.Web.HttpUtility]::HtmlEncode($s)
}

$art = Import-Csv (Join-Path $Root "art_manifest.csv") -Encoding UTF8
$man = Import-Csv (Join-Path $Root "manifest.csv")     -Encoding UTF8
$bundle=@{}; foreach($m in $man){ $bundle[[string]$m.gameId]=$m }

# ordering: explicit target files first (preserve author intent), then by id
$order=@()
foreach($tf in $OrderFiles){
  if(Test-Path $tf){
    foreach($ln in (Get-Content $tf -Encoding UTF8)){
      $ln=$ln.Trim(); if($ln -eq ''){continue}
      if($ln -match '\|'){ $order += ($ln -split '\|')[1].Trim() } else { $order += $ln }
    }
  }
}
$games=@()
foreach($t in $order){
  $g = $art | Where-Object { $_.targetName -eq $t } | Select-Object -First 1
  if($g){ $games += $g; $art = $art | Where-Object { $_.id -ne $g.id } }
}
$games += ($art | Sort-Object { [int]$_.id })

$zips = @(Get-ChildItem $Root -Recurse -Filter *.zip)
$arts = @(Get-ChildItem $Root -Recurse -Directory -Filter art | ForEach-Object { Get-ChildItem $_.FullName -File })
$totalZip = ($zips | Measure-Object Length -Sum).Sum
$cats = ($games | Where-Object {$_.category} | Select-Object -ExpandProperty category -Unique).Count

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('<!DOCTYPE html>')
[void]$sb.AppendLine('<html lang="zh-CN"><head><meta charset="utf-8">')
[void]$sb.AppendLine('<meta name="viewport" content="width=device-width,initial-scale=1">')
[void]$sb.AppendLine(('<title>{0}</title>' -f (Esc $Title)))
[void]$sb.AppendLine(@'
<style>
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--fg:#e8eaed;
--dim:#9aa3b2;--accent:#4c8dff;--accent2:#22c55e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Roboto,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:20;backdrop-filter:blur(12px);
background:rgba(15,17,21,.86);border-bottom:1px solid var(--line);padding:16px 28px}
h1{margin:0 0 6px;font-size:20px;letter-spacing:.3px}
.sub{color:var(--dim);font-size:13px}
.stats{display:flex;gap:22px;flex-wrap:wrap;margin-top:10px;font-size:13px}
.stats b{color:var(--fg);font-size:15px}.stats span{color:var(--dim)}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;align-items:center}
input[type=search],select{background:var(--panel2);border:1px solid var(--line);color:var(--fg);
border-radius:8px;padding:8px 12px;font-size:14px;outline:none;min-width:220px}
input[type=search]:focus,select:focus{border-color:var(--accent)}
.count{color:var(--dim);font-size:13px;margin-left:auto}
main{padding:24px 28px 80px;max-width:1500px;margin:0 auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin-bottom:22px;overflow:hidden}
.card-head{display:flex;gap:18px;padding:18px 20px;align-items:flex-start}
.icon{width:88px;height:88px;border-radius:18px;flex:0 0 88px;object-fit:cover;
background:var(--panel2);border:1px solid var(--line)}
.head-main{flex:1;min-width:0}
.title-row{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.name{font-size:19px;font-weight:650}
.idx{color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.badge{background:var(--panel2);border:1px solid var(--line);border-radius:999px;
padding:2px 11px;font-size:12px;color:var(--dim);white-space:nowrap}
.badge.rate{color:#ffd166;border-color:#3a3320;background:#241f12}
.badge.cat{color:var(--accent);border-color:#22334f;background:#141c2b}
.badge.dev{color:#c084fc;border-color:#35244a;background:#1d1527}
.folder{margin-top:9px;font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;
color:var(--accent2);background:#10151a;border:1px solid #1d2a22;border-radius:7px;
padding:5px 10px;display:inline-block;word-break:break-all}
.desc{margin-top:10px;font-size:14px}
.desc .lead{font-weight:600}.desc .body{color:var(--dim);margin-top:5px;font-size:13.5px}
.art{display:flex;gap:14px;flex-wrap:wrap;padding:0 20px 18px;align-items:flex-start}
.art figure{margin:0;background:var(--panel2);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.art figcaption{font-size:11px;color:var(--dim);padding:5px 10px;border-top:1px solid var(--line);letter-spacing:.4px}
.art img{display:block;background:#0a0c10}
.img-banner img{width:560px;height:auto;max-width:100%}
.img-hot img{width:236px;height:auto}
.img-theme img{width:196px;height:auto}
.img-preview img{width:132px;height:auto}
.links{padding:0 20px 18px;font-size:13px;color:var(--dim);display:flex;gap:16px;flex-wrap:wrap}
.taglist{color:var(--dim);font-size:12.5px}
footer{color:var(--dim);font-size:12.5px;text-align:center;padding:30px;border-top:1px solid var(--line);margin-top:10px}
.hidden{display:none}
@media(max-width:720px){.card-head{flex-direction:column}.icon{width:72px;height:72px;flex-basis:72px}
.img-banner img{width:100%}}
</style>
'@)
[void]$sb.AppendLine('</head><body><header>')
[void]$sb.AppendLine(('<h1>{0}</h1>' -f (Esc $Title)))
[void]$sb.AppendLine(('<div class="sub">{0}生成于 {1}</div>' -f (Esc $SourceNote), (Get-Date).ToString('yyyy-MM-dd HH:mm')))
[void]$sb.AppendLine('<div class="stats">')
[void]$sb.AppendLine(('  <div><b>{0}</b> <span>个游戏</span></div>' -f $games.Count))
[void]$sb.AppendLine(('  <div><b>{0:N1} MB</b> <span>原包体</span></div>' -f ($totalZip/1MB)))
[void]$sb.AppendLine(('  <div><b>{0}</b> <span>张美术素材</span></div>' -f $arts.Count))
[void]$sb.AppendLine(('  <div><b>{0}</b> <span>个分类</span></div>' -f $cats))
[void]$sb.AppendLine('</div><div class="toolbar">')
[void]$sb.AppendLine('  <input type="search" id="q" placeholder="搜索游戏名 / 文件夹名 / 分类 / 标签 …">')
[void]$sb.AppendLine('  <select id="cat"><option value="">全部分类</option>')
foreach($c in ($games | Where-Object {$_.category} | Select-Object -ExpandProperty category | Sort-Object -Unique)){
  [void]$sb.AppendLine(('    <option value="{0}">{0}</option>' -f (Esc $c)))
}
[void]$sb.AppendLine('  </select>')
[void]$sb.AppendLine('  <span class="count" id="cnt"></span>')
[void]$sb.AppendLine('</div></header><main id="list">')

$n=0
foreach($g in $games){
  $n++
  $rel = ($g.dir -replace '\\','/')
  $bm  = $bundle[[string]$g.id]
  # map basename -> real filename (honours CDN format mismatches)
  $af=@{}
  foreach($fn in ($g.artFiles -split ',')){ $fn=$fn.Trim(); if($fn){ $af[[IO.Path]::GetFileNameWithoutExtension($fn)]=$fn } }
  $blob = (("{0} {1} {2} {3} {4}" -f $g.name,$g.dir,$g.category,$g.targetName,$g.tags) -replace '\s+',' ').ToLower()

  [void]$sb.AppendLine(('<section class="card" data-cat="{0}" data-s="{1}">' -f (Esc $g.category),(Esc $blob)))
  [void]$sb.AppendLine('<div class="card-head">')
  if($af['icon']){ [void]$sb.AppendLine(('  <img class="icon" src="{0}/art/{1}" alt="" loading="lazy">' -f $rel,$af['icon'])) }
  else { [void]$sb.AppendLine('  <div class="icon"></div>') }
  [void]$sb.AppendLine('  <div class="head-main">')
  [void]$sb.AppendLine(('    <div class="title-row"><span class="name">{0}</span><span class="idx">#{1:00} · id {2}</span></div>' -f (Esc $g.name),$n,(Esc $g.id)))
  [void]$sb.AppendLine('    <div class="badges">')
  if($g.category){ [void]$sb.AppendLine(('      <span class="badge cat">{0}</span>' -f (Esc $g.category))) }
  if($g.rate){ [void]$sb.AppendLine(('      <span class="badge rate">★ {0}</span>' -f (Esc $g.rate))) }
  if($g.sizeText){ [void]$sb.AppendLine(('      <span class="badge">{0}</span>' -f (Esc $g.sizeText))) }
  if($bm -and $bm.sizeBytes){ [void]$sb.AppendLine(('      <span class="badge">包体 {0:N1} MB</span>' -f ([double]$bm.sizeBytes/1MB))) }
  if($g.likeNum){ [void]$sb.AppendLine(('      <span class="badge">♥ {0}</span>' -f (Esc $g.likeNum))) }
  if($g.source){ [void]$sb.AppendLine(('      <span class="badge dev">开发商 {0}</span>' -f (Esc $g.source))) }
  [void]$sb.AppendLine('    </div>')
  [void]$sb.AppendLine(('    <div class="folder">📁 {0}</div>' -f (Esc $g.dir)))
  if($g.description -or $g.introduction){
    [void]$sb.AppendLine('    <div class="desc">')
    if($g.description){ [void]$sb.AppendLine(('      <div class="lead">{0}</div>' -f (Esc $g.description))) }
    if($g.introduction){ [void]$sb.AppendLine(('      <div class="body">{0}</div>' -f (Esc $g.introduction))) }
    [void]$sb.AppendLine('    </div>')
  }
  [void]$sb.AppendLine('  </div></div>')

  $ah=New-Object System.Collections.Generic.List[string]
  if($af['banner']){ $ah.Add(('    <figure class="img-banner"><img src="{0}/art/{1}" alt="banner" loading="lazy"><figcaption>BANNER</figcaption></figure>' -f $rel,$af['banner'])) }
  if($af['hotgame']){ $ah.Add(('    <figure class="img-hot"><img src="{0}/art/{1}" alt="hotgame" loading="lazy"><figcaption>HOT GAME</figcaption></figure>' -f $rel,$af['hotgame'])) }
  if($af['theme']){ $ah.Add(('    <figure class="img-theme"><img src="{0}/art/{1}" alt="theme" loading="lazy"><figcaption>THEME</figcaption></figure>' -f $rel,$af['theme'])) }
  if($af['preview']){ $ah.Add(('    <figure class="img-preview"><img src="{0}/art/{1}" alt="preview" loading="lazy"><figcaption>PREVIEW</figcaption></figure>' -f $rel,$af['preview'])) }
  if($ah.Count -gt 0){ [void]$sb.AppendLine('<div class="art">'); foreach($l in $ah){ [void]$sb.AppendLine($l) }; [void]$sb.AppendLine('</div>') }

  [void]$sb.AppendLine('<div class="links">')
  if($bm -and $bm.bundleUrl){
    [void]$sb.AppendLine(('  <span>原包体：<a href="{0}" target="_blank" rel="noreferrer">{1}</a></span>' -f (Esc $bm.bundleUrl),(Esc (Split-Path $bm.bundleUrl -Leaf))))
  }
  if($bm -and $bm.md5){ [void]$sb.AppendLine(('  <span>MD5 <code>{0}</code></span>' -f (Esc $bm.md5))) }
  if($g.gameLink){ [void]$sb.AppendLine(('  <span>在线入口：<a href="{0}" target="_blank" rel="noreferrer">打开</a></span>' -f (Esc $g.gameLink))) }
  if($g.tags){ [void]$sb.AppendLine(('  <span class="taglist">标签：{0}</span>' -f (Esc $g.tags))) }
  [void]$sb.AppendLine('</div></section>')
}

[void]$sb.AppendLine('</main>')
[void]$sb.AppendLine(@'
<footer>仅作逆向 / 对标研究留存 · 美术素材版权归各自开发商所有 · 本页自动生成</footer>
<script>
const cards=[...document.querySelectorAll('.card')];
const q=document.getElementById('q'),cat=document.getElementById('cat'),cnt=document.getElementById('cnt');
function apply(){const t=q.value.trim().toLowerCase(),c=cat.value;let n=0;
for(const el of cards){const okT=!t||el.dataset.s.includes(t);const okC=!c||el.dataset.cat===c;
const show=okT&&okC;el.classList.toggle('hidden',!show);if(show)n++;}
cnt.textContent=`显示 ${n} / ${cards.length}`;}
q.addEventListener('input',apply);cat.addEventListener('change',apply);apply();
</script></body></html>
'@)

$out = Join-Path $Root "index.html"
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("catalog written: {0}  games={1}" -f $out, $games.Count) -ForegroundColor Green
