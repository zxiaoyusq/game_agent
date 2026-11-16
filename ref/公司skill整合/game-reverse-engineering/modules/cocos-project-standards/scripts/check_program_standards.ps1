<#
.SYNOPSIS
  Cocos 工程规范门禁（cocos-project-standards 模块）

.DESCRIPTION
  只检查「机械可判」的工程规范缺陷。PASS 不等于工程合规，只等于下列硬缺陷不存在。
  判不了的东西（命名语义是否恰当、分层是否合理、抽象是否过度）必须人工核对，
  范围与边界见 -ShowCoverage 输出。

  判定用词：PASS / FAIL / INFO（与模块 delivery-checklist.md 一致）。
  退出码：存在任一 FAIL 时为 1，否则 0。

.PARAMETER ProjectRoot
  工程根目录（含 assets/ 的那一层）。默认当前目录。

.PARAMETER BundleRelative
  业务 bundle 相对工程根的路径。默认 assets/bundle。

.PARAMETER DeprecatedPathPatterns
  代码中禁止出现的废弃路径字面量（正则）。项目专有，默认空。

.PARAMETER SkipEventCheck
  跳过事件 on/off 启发式检查（该检查为启发式，存在已知误报边界）。

.EXAMPLE
  pwsh -File check_program_standards.ps1 -ProjectRoot E:\DADAPET -ShowCoverage
#>
param(
    [Parameter(Mandatory = $false)][string]$ProjectRoot = (Get-Location).Path,
    [Parameter(Mandatory = $false)][string]$BundleRelative = 'assets/bundle',
    [Parameter(Mandatory = $false)][string[]]$DeprecatedPathPatterns = @(),
    [Parameter(Mandatory = $false)][switch]$SkipEventCheck,
    [Parameter(Mandatory = $false)][switch]$ShowCoverage
)

$ErrorActionPreference = 'Stop'

$results = New-Object System.Collections.Generic.List[object]
function Add-Result {
    param([string]$Section, [string]$Status, [string]$Detail)
    $results.Add([PSCustomObject]@{ Section = $Section; Status = $Status; Detail = $Detail })
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    Add-Result 'precheck' 'FAIL' "ProjectRoot 不存在: $ProjectRoot"
    $results | Format-Table -AutoSize -Wrap
    exit 1
}

$assetsPath = Join-Path $ProjectRoot 'assets'
$bundlePath = Join-Path $ProjectRoot $BundleRelative

Add-Result 'precheck' 'INFO' "ProjectRoot = $ProjectRoot"

function Get-RelativeTo {
    param([string]$Base, [string]$Full)
    if ($Full.Length -le $Base.Length) { return $Full }
    return $Full.Substring($Base.Length).TrimStart('\')
}

# ── A. 逻辑层目录骨架（INFO：是否适用由项目决定，脚本不判适用性）────────────
$scriptsPath = Join-Path $assetsPath 'scripts'
$expectedLayers = @('common', 'config', 'logic', 'userData')
if (Test-Path -LiteralPath $scriptsPath) {
    $present = @()
    $missing = @()
    foreach ($layer in $expectedLayers) {
        if (Test-Path -LiteralPath (Join-Path $scriptsPath $layer)) { $present += $layer } else { $missing += $layer }
    }
    Add-Result 'A.逻辑层骨架' 'INFO' ("存在: " + ($(if ($present.Count) { $present -join ', ' } else { '(无)' })))
    if ($missing.Count) {
        Add-Result 'A.逻辑层骨架' 'INFO' ("未见: " + ($missing -join ', ') + "  ← 需人工判定是否适用（非缺陷）")
    }
} else {
    Add-Result 'A.逻辑层骨架' 'INFO' "未见 assets/scripts（可能非逻辑层工程或路径不同）"
}

# ── B. 图标 meta：trimType=none + 未裁边 + 方形 ────────────────────────────
# 注意：icons/ 不在 bundle 根下，而在资源域之下（如 <域>/images/icons），故递归查找。
$iconRoots = @()
if (Test-Path -LiteralPath $bundlePath) {
    $iconRoots = @(Get-ChildItem -LiteralPath $bundlePath -Recurse -Directory -Filter 'icons' -ErrorAction SilentlyContinue)
}
if ($iconRoots.Count -eq 0) {
    Add-Result 'B.图标meta' 'INFO' "未在 $BundleRelative 下找到任何 icons/ 目录（跳过）"
} else {
    $metaFiles = @()
    foreach ($r in $iconRoots) {
        $metaFiles += @(Get-ChildItem -LiteralPath $r.FullName -Recurse -File -Filter '*.png.meta' -ErrorAction SilentlyContinue)
    }
    if ($metaFiles.Count -eq 0) {
        Add-Result 'B.图标meta' 'INFO' ("找到 {0} 个 icons/ 目录，但无 *.png.meta" -f $iconRoots.Count)
    } else {
        $badTrim = @()
        $badSize = @()
        $badSquare = @()
        foreach ($mf in $metaFiles) {
            $ud = $null
            try {
                $j = [System.IO.File]::ReadAllText($mf.FullName) | ConvertFrom-Json
                if ($j.subMetas -and $j.subMetas.f9941) { $ud = $j.subMetas.f9941.userData }
            } catch {
                Add-Result 'B.图标meta' 'FAIL' ("meta 解析失败: " + $mf.Name)
                continue
            }
            if (-not $ud) { continue }
            $rel = Get-RelativeTo -Base $bundlePath -Full $mf.FullName
            if ($ud.trimType -ne 'none') {
                $badTrim += ("{0} (trimType={1})" -f $rel, $ud.trimType)
            }
            if (($ud.width -ne $ud.rawWidth) -or ($ud.height -ne $ud.rawHeight)) {
                $badSize += ("{0} ({1}x{2} != raw {3}x{4})" -f $rel, $ud.width, $ud.height, $ud.rawWidth, $ud.rawHeight)
            }
            if ($ud.width -ne $ud.height) {
                $badSquare += ("{0} ({1}x{2})" -f $rel, $ud.width, $ud.height)
            }
        }
        Add-Result 'B.图标meta' 'INFO' ("扫描 {0} 个图标 meta（位于 {1} 个 icons/ 目录）" -f $metaFiles.Count, $iconRoots.Count)
        if ($badTrim.Count) {
            Add-Result 'B.图标meta' 'FAIL' ("trimType != none（会被裁边→卡片拉伸）共 {0} 个；前 10：`n    " -f $badTrim.Count + (($badTrim | Select-Object -First 10) -join "`n    "))
        } else {
            Add-Result 'B.图标meta' 'PASS' "全部 trimType=none"
        }
        if ($badSize.Count) {
            Add-Result 'B.图标meta' 'FAIL' ("已裁边（w/h != raw）共 {0} 个；前 10：`n    " -f $badSize.Count + (($badSize | Select-Object -First 10) -join "`n    "))
        } else {
            Add-Result 'B.图标meta' 'PASS' "全部未裁边（w/h == raw）"
        }
        if ($badSquare.Count) {
            Add-Result 'B.图标meta' 'FAIL' ("非方形图标共 {0} 个（方形格中会变形）；前 10：`n    " -f $badSquare.Count + (($badSquare | Select-Object -First 10) -join "`n    "))
        } else {
            Add-Result 'B.图标meta' 'PASS' "全部为方形"
        }
    }
}

# ── C. 禁止进入工程的产物 ──────────────────────────────────────────────────
if (Test-Path -LiteralPath $assetsPath) {
    $webp = @(Get-ChildItem -LiteralPath $assetsPath -Recurse -File -Filter '*.webp' -ErrorAction SilentlyContinue)
    if ($webp.Count) {
        Add-Result 'C.禁用产物' 'FAIL' ("assets 下存在 .webp 共 {0} 个（Cocos 不认，须先转 PNG）；前 10：`n    " -f $webp.Count + (($webp | Select-Object -First 10 | ForEach-Object { Get-RelativeTo -Base $assetsPath -Full $_.FullName }) -join "`n    "))
    } else {
        Add-Result 'C.禁用产物' 'PASS' "无 .webp"
    }
    $bak = @(Get-ChildItem -LiteralPath $assetsPath -Recurse -File -Filter '*.bak' -ErrorAction SilentlyContinue)
    if ($bak.Count) {
        Add-Result 'C.禁用产物' 'FAIL' ("assets 下存在 .bak 共 {0} 个（会被当资源打进包）；前 10：`n    " -f $bak.Count + (($bak | Select-Object -First 10 | ForEach-Object { Get-RelativeTo -Base $assetsPath -Full $_.FullName }) -join "`n    "))
    } else {
        Add-Result 'C.禁用产物' 'PASS' "无 .bak"
    }
} else {
    Add-Result 'C.禁用产物' 'INFO' "未见 assets/（跳过）"
}

# ── D. 事件 on/off 成对（启发式）───────────────────────────────────────────
if ($SkipEventCheck) {
    Add-Result 'D.事件成对' 'INFO' "已按 -SkipEventCheck 跳过"
} elseif (Test-Path -LiteralPath $scriptsPath) {
    $tsFiles = @(Get-ChildItem -LiteralPath $scriptsPath -Recurse -File -Filter '*.ts')
    $unbalanced = @()
    foreach ($t in $tsFiles) {
        $text = [System.IO.File]::ReadAllText($t.FullName)
        $on = ([regex]::Matches($text, 'CFW\.event\.on\(')).Count
        $off = ([regex]::Matches($text, 'CFW\.event\.off\(')).Count
        if ($on -gt $off) {
            $unbalanced += ("{0} (on={1} off={2})" -f $t.Name, $on, $off)
        }
    }
    if ($unbalanced.Count) {
        Add-Result 'D.事件成对' 'FAIL' ("同文件内 on > off 共 {0} 个文件`n    启发式边界：常驻单例（如静态 DataMgr）/ 常驻 Stage 的全局监听按约定无需 off，属已知误报；须逐个人工确认。`n    " -f $unbalanced.Count + ($unbalanced -join "`n    "))
    } else {
        Add-Result 'D.事件成对' 'PASS' ("{0} 个 .ts 文件均无 on > off" -f $tsFiles.Count)
    }
} else {
    Add-Result 'D.事件成对' 'INFO' "未见 assets/scripts（跳过）"
}

# ── E. 预制体节点命名反模式 ────────────────────────────────────────────────
if (Test-Path -LiteralPath $bundlePath) {
    $prefabs = @(Get-ChildItem -LiteralPath $bundlePath -Recurse -File -Filter '*.prefab' -ErrorAction SilentlyContinue)
    $badNames = @{}
    $badByFile = @{}
    foreach ($pf in $prefabs) {
        $text = [System.IO.File]::ReadAllText($pf.FullName)
        foreach ($m in [regex]::Matches($text, '"_name"\s*:\s*"([^"]+)"')) {
            $n = $m.Groups[1].Value
            if ($n -match '^(panelB\d|img\d{3,}|node\d+|Sprite\d+|Label\d+|Layer\d+)$') {
                if (-not $badNames.ContainsKey($n)) { $badNames[$n] = 0 }
                $badNames[$n] = $badNames[$n] + 1
                $relPf = Get-RelativeTo -Base $bundlePath -Full $pf.FullName
                if (-not $badByFile.ContainsKey($relPf)) { $badByFile[$relPf] = @() }
                if ($badByFile[$relPf] -notcontains $n) { $badByFile[$relPf] += $n }
            }
        }
    }
    if ($badNames.Count) {
        $lines = @()
        foreach ($k in ($badNames.Keys | Sort-Object)) {
            $lines += ("{0} x{1}" -f $k, $badNames[$k])
        }
        $fileLines = @()
        foreach ($f in ($badByFile.Keys | Sort-Object)) {
            $fileLines += ("{0}: {1}" -f $f, ($badByFile[$f] -join ', '))
        }
        Add-Result 'E.节点命名' 'FAIL' ("发现无语义节点名（设计稿编号/自动名泄漏）共 {0} 种、{1} 处：`n    " -f $badNames.Count, (($badNames.Values | Measure-Object -Sum).Sum) + ($lines -join "`n    ") + "`n  按文件（前 15）：`n    " + (($fileLines | Select-Object -First 15) -join "`n    "))
    } else {
        Add-Result 'E.节点命名' 'PASS' ("{0} 个 prefab 中无 panelB*/img###/node*/Sprite#/Label# 类命名" -f $prefabs.Count)
    }
} else {
    Add-Result 'E.节点命名' 'INFO' "未见 $BundleRelative（跳过）"
}

# ── F. 配置派生物存在且可解析 ──────────────────────────────────────────────
$dataJson = Join-Path $bundlePath 'config\data.json'
if (-not (Test-Path -LiteralPath $dataJson)) {
    if (Test-Path -LiteralPath $bundlePath) {
        $found = @(Get-ChildItem -LiteralPath $bundlePath -Recurse -File -Filter 'data.json' -ErrorAction SilentlyContinue)
        if ($found.Count -gt 0) { $dataJson = $found[0].FullName }
    }
}
$schemaTs = Join-Path $scriptsPath 'config\schema\schema.ts'
if (Test-Path -LiteralPath $dataJson) {
    try {
        $null = [System.IO.File]::ReadAllText($dataJson) | ConvertFrom-Json
        Add-Result 'F.配置产物' 'PASS' ("{0} 存在且可解析" -f (Get-RelativeTo -Base $ProjectRoot -Full $dataJson))
    } catch {
        Add-Result 'F.配置产物' 'FAIL' "data.json 解析失败（启动会黑屏）: $($_.Exception.Message)"
    }
} else {
    Add-Result 'F.配置产物' 'INFO' "未找到 data.json（可能未使用配置表）"
}
if (Test-Path -LiteralPath $schemaTs) {
    Add-Result 'F.配置产物' 'INFO' "schema.ts 存在（派生文件，禁止手改；应改 Excel 后重跑导表）"
}

# ── G. 代码中写死的废弃路径 ────────────────────────────────────────────────
if ($DeprecatedPathPatterns.Count -gt 0 -and (Test-Path -LiteralPath $scriptsPath)) {
    $hits = @()
    $tsAll = @(Get-ChildItem -LiteralPath $scriptsPath -Recurse -File -Filter '*.ts')
    foreach ($t in $tsAll) {
        $text = [System.IO.File]::ReadAllText($t.FullName)
        foreach ($pat in $DeprecatedPathPatterns) {
            if ($text -match $pat) { $hits += ("{0}  <- /{1}/" -f $t.Name, $pat) }
        }
    }
    if ($hits.Count) {
        Add-Result 'G.废弃路径' 'FAIL' ("代码中命中废弃路径字面量：`n    " + ($hits -join "`n    "))
    } else {
        Add-Result 'G.废弃路径' 'PASS' "未命中给定模式"
    }
} else {
    Add-Result 'G.废弃路径' 'INFO' "未提供 -DeprecatedPathPatterns（跳过；该清单为项目专有）"
}

# ── 输出 ───────────────────────────────────────────────────────────────────
$results | Format-Table -AutoSize -Wrap

$fails = @($results | Where-Object { $_.Status -eq 'FAIL' })
Write-Output ''
Write-Output ("合计: {0} 条记录，其中 FAIL {1} 条" -f $results.Count, $fails.Count)

if ($ShowCoverage) {
    Write-Output ''
    Write-Output '── 覆盖范围（本脚本能判的）─────────────────────────────'
    Write-Output '  A 逻辑层目录存在性（只报存在/缺失，不判适用性）'
    Write-Output '  B 图标 meta：trimType=none / w==raw / 方形（递归找 icons/）'
    Write-Output '  C 禁用产物：assets 下 .webp 与 .bak'
    Write-Output '  D 事件 on/off：同文件内 CFW.event.on > off（启发式）'
    Write-Output '  E prefab 节点名反模式：panelB*/img###/node*/Sprite#/Label#'
    Write-Output '  F data.json 可解析 + schema.ts 存在'
    Write-Output '  G 代码中写死的废弃路径（需传 -DeprecatedPathPatterns）'
    Write-Output ''
    Write-Output '── 本脚本判不了的（必须人工核对）───────────────────────'
    Write-Output '  · 命名语义是否恰当、节点名与 @property 是否一致'
    Write-Output '  · 分层是否合理、依赖方向是否反向（框架层是否 import 了业务）'
    Write-Output '  · 抽象是否过度、是否引入非必需依赖'
    Write-Output '  · 空数据兜底是否真的可见、日志是否带足够上下文'
    Write-Output '  · 事件解除是否跨文件（D 的误报来源）'
    Write-Output '  · 配置与 Excel 的真源一致性（须比对 git diff / 差异表清单）'
    Write-Output '  · 派生物是否被手改（须比对生成器双跑哈希或 git diff）'
    Write-Output '  · 工程是否真的能构建、能跑（走 cocos-qa + vision-device-testing）'
    Write-Output ''
    Write-Output 'PASS 只表示上述硬缺陷不存在，不表示工程合规。'
}

if ($fails.Count -gt 0) { exit 1 } else { exit 0 }
