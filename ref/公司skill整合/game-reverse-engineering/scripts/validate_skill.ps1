param(
    [Parameter(Mandatory = $false)]
    [string]$SkillRoot = (Split-Path -Parent $PSScriptRoot),

    [Parameter(Mandatory = $false)]
    [string[]]$CompareRoots = @()
)

$ErrorActionPreference = 'Stop'
$failures = [System.Collections.Generic.List[string]]::new()

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { $script:failures.Add($Message) }
}

$rootSkill = Join-Path $SkillRoot 'SKILL.md'
Assert-True (Test-Path -LiteralPath $rootSkill) "missing root SKILL.md: $rootSkill"
if (-not (Test-Path -LiteralPath $rootSkill)) { exit 1 }

$main = Get-Content -LiteralPath $rootSkill -Raw -Encoding UTF8
Assert-True ($main -match '(?m)^description:\s*"?Use when\b') 'root description must start with Use when'
Assert-True ($main -match '(?m)^metadata:\s*$') 'root frontmatter must use metadata for cross-harness extension fields'
# 根版本号必须与 CHANGELOG 最新条目一致（动态校验，写死版本号会让任何 bump 都挂）
$changelogPath = Join-Path $SkillRoot 'references\CHANGELOG.md'
$rootVersion = $null
if ($main -match '(?m)^\s*version:\s*"([0-9]+\.[0-9]+\.[0-9]+)"') { $rootVersion = $Matches[1] }
Assert-True ($null -ne $rootVersion) 'root metadata version missing'
if ($rootVersion -and (Test-Path -LiteralPath $changelogPath)) {
    $clHead = Get-Content -LiteralPath $changelogPath -TotalCount 10 -Encoding UTF8
    Assert-True (($clHead -join "`n") -match [regex]::Escape("$rootVersion (")) "root version $rootVersion must match newest CHANGELOG entry"
}

# 8.0.0: version history lives in references/CHANGELOG.md, not in the root router.
$changelog = Join-Path $SkillRoot 'references\CHANGELOG.md'
Assert-True (Test-Path -LiteralPath $changelog) 'missing references/CHANGELOG.md'
if (Test-Path -LiteralPath $changelog) {
    $changeText = Get-Content -LiteralPath $changelog -Raw -Encoding UTF8
    foreach ($marker in @(
        '8.0.0 (2026-10-04)',
        '7.13.0 (2026-10-02)',
        '7.2.0 (2026-09-06)',
        '5.3.0 (2026-09-01)',
        '7.10.1 (2026-09-13)',
        '7.12.0 (2026-09-14)'
    )) {
        Assert-True ($changeText.Contains($marker)) "changelog missing entry: $marker"
    }
}

# 8.0.0: global rules and case rules moved out of the root router into references/.
$globalRules = Join-Path $SkillRoot 'references\global-rules.md'
Assert-True (Test-Path -LiteralPath $globalRules) 'missing references/global-rules.md'
if (Test-Path -LiteralPath $globalRules) {
    $globalRulesText = Get-Content -LiteralPath $globalRules -Raw -Encoding UTF8
    foreach ($rule in @('owner', 'commit', '`HEK:`', 'v03 XOR', 'debug', 'SHA-256')) {
        Assert-True ($globalRulesText.Contains($rule)) "global rules missing: $rule"
    }
}
$blockmasterRules = Join-Path $SkillRoot $('references\' + 'blockmaster-case-rules.md')
Assert-True (Test-Path -LiteralPath $blockmasterRules) 'missing references/blockmaster-case-rules.md'
if (Test-Path -LiteralPath $blockmasterRules) {
    $blockmasterRulesText = Get-Content -LiteralPath $blockmasterRules -Raw -Encoding UTF8
    foreach ($rule in @('10.4.7', '9.5.0')) {
        Assert-True ($blockmasterRulesText.Contains($rule)) "blockmaster case rules missing: $rule"
    }
}
foreach ($ref in @('references/global-rules.md', 'references/blockmaster-case-rules.md', 'references/end-to-end-pipeline.md', 'references/CHANGELOG.md', 'references/scope-map.md')) {
    Assert-True ($main.Contains($ref)) "root must route to $ref"
}
Assert-True ($main.Contains('GENERAL_DEFAULT')) 'root must define GENERAL_DEFAULT'
Assert-True ($main.Contains('GENERALIZED_PATTERN')) 'root must define GENERALIZED_PATTERN'
Assert-True ($main.Contains('CASE_ONLY_BLOCKMASTER')) 'root must define CASE_ONLY_BLOCKMASTER'
Assert-True ($main.Contains('CASE_ONLY_JIGSAWCARD')) 'root must define CASE_ONLY_JIGSAWCARD'
$envExample = Get-Content -LiteralPath (Join-Path $SkillRoot 'env.example') -Raw -Encoding UTF8
foreach ($variable in @('HARNESS_WORKBUDDY','HARNESS_AGENTS','HARNESS_CODEX','HARNESS_OPENCODE','HARNESS_DSH','HARNESS_TRAE','HARNESS_CLAUDE')) {
    Assert-True ($envExample.Contains($variable + '=')) "env.example missing harness variable: $variable"
}

$modules = @(
    'engine-identification',
    'cocos-reverse-engineering',
    'cocos-creator-repair',
    'unity-extract',
    'gameplay-logic-reverse',
    'skinning-pipeline',
    'prefab-bake',
    'ui-feature-pipeline',
    'cocos-qa',
    'dragonbones-spine-convert',
    'vision-device-testing',
    'godot-migration-port',
    'sdk-replacement',
    'cocos-mcp-channel',
    '3d-asset-extraction',
    'deliverable-book-template'
)

foreach ($module in $modules) {
    $relative = "modules/$module/SKILL.md"
    $modulePath = Join-Path $SkillRoot ($relative -replace '/', '\')
    Assert-True ($main.Contains($relative)) "route missing from root: $relative"
    Assert-True (Test-Path -LiteralPath $modulePath) "module missing: $relative"
    if (Test-Path -LiteralPath $modulePath) {
        $moduleText = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8
        Assert-True ($moduleText -match '(?m)^description:\s*"?Use when\b') "module description must start with Use when: $relative"
    }
}

foreach ($moduleDir in (Get-ChildItem -LiteralPath (Join-Path $SkillRoot 'modules') -Directory)) {
    $route = "modules/$($moduleDir.Name)/SKILL.md"
    Assert-True ($main.Contains($route)) "unrouted module: $route"
    $cardText = Get-Content -LiteralPath (Join-Path $moduleDir.FullName 'SKILL.md') -Raw -Encoding UTF8
    foreach ($part in @('我管什么','第一步做什么','做完怎么算完成','红线')) {
        Assert-True ($cardText.Contains($part)) "module execution card missing $part : $route"
    }
}

$jigsawCardRef = Join-Path $SkillRoot 'modules\unity-extract\references\jigsawcard-puzzle-case.md'
Assert-True (Test-Path -LiteralPath $jigsawCardRef) 'missing jigsawcard case reference'
if (Test-Path -LiteralPath $jigsawCardRef) {
    $jigsawText = Get-Content -LiteralPath $jigsawCardRef -Raw -Encoding UTF8
    foreach ($marker in @('m_Script', 'latin-1', '.skel.bytes', 'manifest_ext.bs', 'mitmproxy', 'CASE_ONLY_JIGSAWCARD')) {
        Assert-True ($jigsawText.Contains($marker)) "jigsawcard case reference missing marker: $marker"
    }
}

# 8.0.0: literal case values live in module/case files now; the root router only carries scope labels.
$requiredRootTokens = @(
    'GENERAL_DEFAULT',
    'GENERALIZED_PATTERN',
    'CASE_ONLY_BLOCKMASTER',
    'CASE_ONLY_JIGSAWCARD',
    'DO_NOT_COPY_LITERAL_VALUES'
)
foreach ($rule in $requiredRootTokens) {
    Assert-True ($main.Contains($rule)) "required root token missing: $rule"
}

$regression = Join-Path $SkillRoot 'modules\gameplay-logic-reverse\references\blockmaster-v123-v124-lifecycle-regression.md'
Assert-True (Test-Path -LiteralPath $regression) 'missing V123/V124 lifecycle regression reference'
if (Test-Path -LiteralPath $regression) {
    $regressionText = Get-Content -LiteralPath $regression -Raw -Encoding UTF8
    foreach ($marker in @('bmCleanupPreEliminate', 'E_BlocksProducer_AnyTouchEnd', 'prepare', 'commit', 'BlockMaster_v124_stable_presentation_boundary_phone_qa_debug.apk')) {
        Assert-True ($regressionText.Contains($marker)) "regression reference missing marker: $marker"
    }
}

$trayRegression = Join-Path $SkillRoot 'modules\gameplay-logic-reverse\references\blockmaster-v128-tray-guard-regression.md'
Assert-True (Test-Path -LiteralPath $trayRegression) 'missing V128 tray guard regression reference'
if (Test-Path -LiteralPath $trayRegression) {
    $trayRegressionText = Get-Content -LiteralPath $trayRegression -Raw -Encoding UTF8
    foreach ($marker in @('BaubleTopic', 'existential', 'partial tray', '1x1', 'distribution')) {
        Assert-True ($trayRegressionText.Contains($marker)) "tray regression reference missing marker: $marker"
    }
}

$scopeMap = Join-Path $SkillRoot 'references\scope-map.md'
Assert-True (Test-Path -LiteralPath $scopeMap) 'missing references/scope-map.md'
if (Test-Path -LiteralPath $scopeMap) {
    $scopeText = Get-Content -LiteralPath $scopeMap -Raw -Encoding UTF8
    foreach ($marker in @('GENERAL_DEFAULT', 'GENERALIZED_PATTERN', 'CASE_ONLY_BLOCKMASTER', 'CASE_ONLY_BLOCKUDOKU', 'CASE_ONLY_JIGSAWCARD', 'DO_NOT_COPY_LITERAL_VALUES', 'sdk-replacement')) {
        Assert-True ($scopeText.Contains($marker)) "scope map missing marker: $marker"
    }
    foreach ($caseReference in @(
        'block-blast-case.md',
        'blockmaster-v123-v124-lifecycle-regression.md',
        'blockmaster-v128-tray-guard-regression.md',
        'android-blockmaster-runtime-effects-ads-regression.md',
        'android-blockmaster-v35-vendor-isolation-and-real-device-qa.md',
        'android-blockmaster-v31-ad-resource-and-ui-removal.md',
        'android-blockmaster-moregames-settings.md',
        'android-jsb-reskin-pitfalls.md',
        'jigsawcard-puzzle-case.md'
    )) {
        Assert-True ($scopeText.Contains($caseReference)) "scope map does not classify case reference: $caseReference"
    }

    # 8.0.0: every module directory must be indexed in the scope map.
    foreach ($moduleDir in (Get-ChildItem -LiteralPath (Join-Path $SkillRoot 'modules') -Directory)) {
        $moduleName = $moduleDir.Name
        Assert-True ($scopeText.Contains('`' + $moduleName + '`')) "scope-map does not index module: $moduleName"
    }
}

$contentMappingRef = Join-Path $SkillRoot 'modules\cocos-qa\references\content-image-mapping-qa.md'
Assert-True (Test-Path -LiteralPath $contentMappingRef) 'missing content-image-mapping QA reference'
if (Test-Path -LiteralPath $contentMappingRef) {
    $contentMappingText = Get-Content -LiteralPath $contentMappingRef -Raw -Encoding UTF8
    foreach ($marker in @('结构 PASS 不能代替语义 PASS', 'stable_id', '保存草稿', '写入工程', 'SEMANTIC_PENDING', 'Web 与 APK', 'expected_levels: 0', 'IntersectionObserver')) {
        Assert-True ($contentMappingText.Contains($marker)) "content-image-mapping reference missing marker: $marker"
    }
}

$contentEditorRoot = Join-Path $SkillRoot 'modules\cocos-qa\assets\content-mapping-editor'
foreach ($editorFile in @('index.html', 'server.py', 'editor.config.example.json', 'launch-editor.bat', 'README.md')) {
    Assert-True (Test-Path -LiteralPath (Join-Path $contentEditorRoot $editorFile)) "content editor asset missing: $editorFile"
}
$contentEditorHtml = Join-Path $contentEditorRoot 'index.html'
if (Test-Path -LiteralPath $contentEditorHtml) {
    $contentEditorText = Get-Content -LiteralPath $contentEditorHtml -Raw -Encoding UTF8
    foreach ($marker in @('固定编号', '保存草稿', '预览并写入', 'IntersectionObserver', '重新读取工程')) {
        Assert-True ($contentEditorText.Contains($marker)) "content editor HTML missing marker: $marker"
    }
}
$contentEditorServer = Join-Path $contentEditorRoot 'server.py'
if (Test-Path -LiteralPath $contentEditorServer) {
    $contentEditorServerText = Get-Content -LiteralPath $contentEditorServer -Raw -Encoding UTF8
    foreach ($marker in @('127.0.0.1', 'strict_content=False', 'source_hashes', 'atomic_write', 'apply-report.json')) {
        Assert-True ($contentEditorServerText.Contains($marker)) "content editor server missing marker: $marker"
    }
}

$artRemakeRef = Join-Path $SkillRoot 'modules\godot-migration-port\references\art-remake-playbook.md'
Assert-True (Test-Path -LiteralPath $artRemakeRef) 'missing Godot art-remake playbook'
if (Test-Path -LiteralPath $artRemakeRef) {
    $artRemakeText = Get-Content -LiteralPath $artRemakeRef -Raw -Encoding UTF8
    foreach ($marker in @('CASE_ONLY_MAGICSORT', '零绘制', '同纹理覆盖', '双证据', 'Spine 必须直接重绘真实 Atlas', 'root.size', 'Alpha 相同')) {
        Assert-True ($artRemakeText.Contains($marker)) "art-remake playbook missing marker: $marker"
    }
    Assert-True (-not $artRemakeText.Contains('30%~45%')) 'art-remake playbook still contains unproven Gemini scale statistics'
    Assert-True (-not $artRemakeText.Contains('missing_coverage_ratio <= 5.0%')) 'art-remake playbook still contains the rejected fixed coverage threshold'
    Assert-True ($artRemakeText.Contains('references/scope-map.md')) 'art-remake playbook scope-map path is not root-relative'
}

$installDep = Join-Path $SkillRoot 'modules\cocos-reverse-engineering\scripts\install-dep.sh'
Assert-True (Test-Path -LiteralPath $installDep) 'missing referenced install-dep.sh'
if (Test-Path -LiteralPath $installDep) {
    $installDepText = Get-Content -LiteralPath $installDep -Raw -Encoding UTF8
    foreach ($marker in @('set -euo pipefail', 'install_cc_reverse', 'install_p7zip', 'install_ffmpeg')) {
        Assert-True ($installDepText.Contains($marker)) "install-dep.sh missing marker: $marker"
    }
}

Assert-True (-not $main.Contains('Python 3.11.9')) 'root still hard-codes Python 3.11.9'
Assert-True (-not $main.Contains('36 checks plus real drag')) 'root still hard-codes a historical QA check count'

$generalVerify = Join-Path $SkillRoot 'modules\skinning-pipeline\scripts\verify.py'
if (Test-Path -LiteralPath $generalVerify) {
    $generalVerifyText = Get-Content -LiteralPath $generalVerify -Raw -Encoding UTF8
    Assert-True (-not $generalVerifyText.Contains('E:\\Gameprogram\\CocosCreator_2.4.13\\CocosCreator.exe')) 'general skinning verifier must not emit a machine-specific Cocos path'
}


$extRegistry = Join-Path $SkillRoot 'references\external-game-skills.md'
Assert-True (Test-Path -LiteralPath $extRegistry) 'missing references/external-game-skills.md'
if (Test-Path -LiteralPath $extRegistry) {
    $extText = Get-Content -LiteralPath $extRegistry -Raw -Encoding UTF8
    foreach ($marker in @('jame581/GodotPrompter', 'gstack-game', 'claude-code-game-studios', 'ai-game-art-pipeline-skill', '更新命令')) {
        Assert-True ($extText.Contains($marker)) "external registry missing marker: $marker"
    }
}

$landingLog = Join-Path $SkillRoot 'modules\godot-migration-port\references\landing-log.md'
Assert-True (Test-Path -LiteralPath $landingLog) 'missing godot-migration-port landing-log'
if (Test-Path -LiteralPath $landingLog) {
    $landingText = Get-Content -LiteralPath $landingLog -Raw -Encoding UTF8
    foreach ($marker in @('landing-log', '回填动作', '里程碑')) {
        Assert-True ($landingText.Contains($marker)) "landing-log missing marker: $marker"
    }
}

$sdkModuleRoot = Join-Path $SkillRoot 'modules\sdk-replacement'
foreach ($sdkScript in @('capture_network_evidence.py', 'scan_original_sdk_surfaces.py', 'prepare_offline_seed.py', 'generate_seed_copier.py', 'verify_vendor_isolation.py', 'gen_sdk_acceptance_report.py')) {
    $sdkScriptPath = Join-Path $sdkModuleRoot (Join-Path 'scripts' $sdkScript)
    Assert-True (Test-Path -LiteralPath $sdkScriptPath) "sdk-replacement script missing: $sdkScript"
    if (Test-Path -LiteralPath $sdkScriptPath) {
        $sdkScriptText = Get-Content -LiteralPath $sdkScriptPath -Raw -Encoding UTF8
        $sdkScriptHead = $sdkScriptText.Substring(0, [Math]::Min(500, $sdkScriptText.Length))
        Assert-True ($sdkScriptHead.Contains('"""')) "sdk-replacement script must start with docstring: $sdkScript"
        foreach ($caseLiteral in @('com.block.juggle', 'afafb.com', 'B83BD3645', '5ed39fe6')) {
            Assert-True (-not $sdkScriptText.Contains($caseLiteral)) "sdk-replacement script must not contain case literal ($caseLiteral): $sdkScript"
        }
    }
}

Assert-True (Test-Path -LiteralPath (Join-Path $SkillRoot 'modules/godot-migration-port/references/native-restoration-gates.md')) 'missing native restoration gates'
$jigsawLessons = Join-Path $SkillRoot 'modules\godot-migration-port\references\jigsawcard-restoration-lessons.md'
Assert-True (Test-Path -LiteralPath $jigsawLessons) 'missing JigsawCard restoration lessons'
if (Test-Path -LiteralPath $jigsawLessons) {
    $jigsawLessonsText = Get-Content -LiteralPath $jigsawLessons -Raw -Encoding UTF8
    foreach ($marker in @('CASE_ONLY_JIGSAWCARD', 'TextAsset', 'effect_firstwin_01', 'Last1', 'Last2', 'epoch', '530', '未完成')) {
        Assert-True ($jigsawLessonsText.Contains($marker)) "JigsawCard restoration lessons missing marker: $marker"
    }
}
$spineIntegration = Join-Path $SkillRoot 'modules\godot-migration-port\references\godot-spine-integration.md'
Assert-True (Test-Path -LiteralPath $spineIntegration) 'missing Godot Spine integration reference'
if (Test-Path -LiteralPath $spineIntegration) {
    $spineIntegrationText = Get-Content -LiteralPath $spineIntegration -Raw -Encoding UTF8
    foreach ($marker in @('GDExtension', 'SpineSprite', 'SkeletonData', 'Atlas', '.tscn', '.tres', 'overlay', 'Android')) {
        Assert-True ($spineIntegrationText.Contains($marker)) "Godot Spine integration missing marker: $marker"
    }
}
$gapQa = Join-Path $SkillRoot 'modules\godot-migration-port\references\restoration-gap-to-qa.md'
Assert-True (Test-Path -LiteralPath $gapQa) 'missing restoration gap-to-QA reference'
if (Test-Path -LiteralPath $gapQa) {
    $gapQaText = Get-Content -LiteralPath $gapQa -Raw -Encoding UTF8
    foreach ($marker in @('差距矩阵', '最小修复', '四层', 'Android', '失败后的定位循环', 'GENERALIZED_PATTERN', '受控原版数据探针', '当前快照默认值', '后期解锁系统', '粒子视觉 1:1')) {
        Assert-True ($gapQaText.Contains($marker)) "gap-to-QA reference missing marker: $marker"
    }
}

$godotModule = Join-Path $SkillRoot 'modules\godot-migration-port\SKILL.md'
$godotWorkflow = Join-Path $SkillRoot 'modules\godot-migration-port\references\end-to-end-restoration-workflow.md'
Assert-True (Test-Path -LiteralPath $godotWorkflow) 'missing Godot end-to-end restoration workflow'
if (Test-Path -LiteralPath $godotModule) {
    $godotText = Get-Content -LiteralPath $godotModule -Raw -Encoding UTF8
    Assert-True ($godotText -match '(?m)^version:\s*[0-9]+\.[0-9]+\.[0-9]+\s*$') 'Godot migration module must declare a semver version'
    Assert-True ($godotText.Contains('references/end-to-end-restoration-workflow.md')) 'Godot module must route to the end-to-end workflow'
    Assert-True ($godotText.Contains('S0–S7')) 'Godot module must expose the canonical S0-S7 lifecycle'
}
if (Test-Path -LiteralPath $godotWorkflow) {
    $workflowText = Get-Content -LiteralPath $godotWorkflow -Raw -Encoding UTF8
    foreach ($marker in @('snapshot defaults', 'controlled_runtime_confirmed', '最终 APK', 'finally', '页面 ready', 'S7：收口')) {
        Assert-True ($workflowText.Contains($marker)) "Godot end-to-end workflow missing marker: $marker"
    }
}

# New references must exist and remain discoverable through the root/module graph.
foreach ($reference in @(
    'references/native-code-evidence.md',
    'references/protected-runtime-recovery.md',
    'references/binary-version-diff.md',
    'references/minimaxh3-absorption.md',
    'modules/unity-extract/references/managed-native-code-recovery.md',
    'modules/gameplay-logic-reverse/references/observed-runtime-replay.md',
    'modules/sdk-replacement/references/custom-protocol-evidence.md',
    'scripts/native_address_map.py',
    'scripts/tests/test_native_address_map.py'
)) {
    Assert-True (Test-Path -LiteralPath (Join-Path $SkillRoot $reference)) "missing 7.13 resource: $reference"
}

$generatedCaches = @(Get-ChildItem -LiteralPath $SkillRoot -Recurse -File | Where-Object { $_.Extension -eq '.pyc' })
Assert-True ($generatedCaches.Count -eq 0) 'skill tree must not contain generated .pyc files'

# 8.0.0: superseded standalone predecessors must not reappear next to the umbrella,
# and no module may be shadowed by a same-named top-level skill directory.
$superseded = @(
    'game-build-engine-identification',
    'cocos-reverse-engineering',
    'cocos-creator-project-repair',
    'assetripper-unity-extract',
    'game-skinning-pipeline',
    'blockudoku-cocos-qa',
    'db2spine-spine38-qa',
    'vision-device-testing'
)
$poolSkillsDir = Split-Path -Parent $SkillRoot
foreach ($name in $superseded) {
    $candidate = Join-Path $poolSkillsDir $name
    Assert-True (-not (Test-Path -LiteralPath $candidate)) "superseded standalone skill reappeared next to the umbrella: $candidate"
}
foreach ($moduleDir in (Get-ChildItem -LiteralPath (Join-Path $SkillRoot 'modules') -Directory)) {
    $candidate = Join-Path $poolSkillsDir $moduleDir.Name
    Assert-True (-not (Test-Path -LiteralPath $candidate)) "module name shadowed by a top-level skill dir: $candidate"
}

# 8.0.0: path convention - backtick paths resolve from the skill root,
# markdown links resolve from the containing file.
$backtickPathPattern = '`((?:modules|references|scripts)/[A-Za-z0-9_\-./]+\.(?:md|py|sh|ps1|js|json))`'
$linkPathPattern = '\]\(([^)#\s]+)(?:#[^)]*)?\)'
foreach ($md in (Get-ChildItem -LiteralPath $SkillRoot -Recurse -File -Filter *.md)) {
    $mdText = Get-Content -LiteralPath $md.FullName -Raw -Encoding UTF8
    $relName = $md.FullName.Substring($SkillRoot.Length + 1)
    foreach ($m in [regex]::Matches($mdText, $backtickPathPattern)) {
        $p = $m.Groups[1].Value
        $resolved = Join-Path $SkillRoot ($p -replace '/', '\')
        Assert-True (Test-Path -LiteralPath $resolved) "backtick path not root-resolvable: $relName -> $p"
    }
    foreach ($m in [regex]::Matches($mdText, $linkPathPattern)) {
        $u = $m.Groups[1].Value
        if ($u -match '^(https?:|mailto:|#)') { continue }
        $resolved = Join-Path (Split-Path -Parent $md.FullName) ($u -replace '/', '\')
        Assert-True (Test-Path -LiteralPath $resolved) "markdown link broken: $relName -> $u"
    }
}

function Get-TreeHashMap {
    param([string]$Root)
    $map = @{}
    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
    Get-ChildItem -LiteralPath $Root -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($resolvedRoot.Length).TrimStart('\').Replace('\', '/')
        $map[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return $map
}

if ($CompareRoots.Count -gt 0) {
    $sourceMap = Get-TreeHashMap $SkillRoot
    foreach ($compareRoot in $CompareRoots) {
        Assert-True (Test-Path -LiteralPath $compareRoot) "compare root missing: $compareRoot"
        if (-not (Test-Path -LiteralPath $compareRoot)) { continue }
        $targetMap = Get-TreeHashMap $compareRoot
        foreach ($relative in $sourceMap.Keys) {
            Assert-True ($targetMap.ContainsKey($relative)) "sync target missing file: $compareRoot :: $relative"
            if ($targetMap.ContainsKey($relative)) {
                Assert-True ($sourceMap[$relative] -eq $targetMap[$relative]) "sync hash mismatch: $compareRoot :: $relative"
            }
        }
        foreach ($relative in $targetMap.Keys) {
            Assert-True ($sourceMap.ContainsKey($relative)) "sync target has stale extra file: $compareRoot :: $relative"
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Output "FAIL: $_" }
    exit 1
}

Write-Output 'PASS: game-reverse-engineering skill structure and rules'
if ($CompareRoots.Count -gt 0) {
    Write-Output 'PASS: all compared skill trees are byte-identical'
}
