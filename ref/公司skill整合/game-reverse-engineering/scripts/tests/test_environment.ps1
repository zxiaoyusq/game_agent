$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\resolve_environment.ps1')
$testBase = [IO.Path]::GetTempPath()
$testRoot = Join-Path $testBase ('game-skill-env-' + [Guid]::NewGuid().ToString('N'))
$previous = [Environment]::GetEnvironmentVariable('CODEX_TEST_GAME_TOOL','Process')
try {
    $toolDir = Join-Path $testRoot 'tool directory'
    New-Item -ItemType Directory -Path $toolDir -Force | Out-Null
    $tool = Join-Path $toolDir 'tool.exe'
    [IO.File]::WriteAllText($tool,'test fixture')
    [Environment]::SetEnvironmentVariable('CODEX_TEST_GAME_TOOL',$toolDir,'Process')
    if ((Resolve-GameToolPath -Name CODEX_TEST_GAME_TOOL -Leaf tool.exe) -ne $tool) { throw 'directory environment path did not resolve' }
    [Environment]::SetEnvironmentVariable('CODEX_TEST_GAME_TOOL',$tool,'Process')
    if ((Resolve-GameToolPath -Name CODEX_TEST_GAME_TOOL -Leaf tool.exe) -ne $tool) { throw 'file path had an extra suffix appended' }
    [Environment]::SetEnvironmentVariable('CODEX_TEST_GAME_TOOL',$null,'Process')
    if ((Resolve-GameToolPath -Name CODEX_TEST_GAME_TOOL -Path $tool) -ne $tool) { throw 'explicit path did not resolve' }
    if ((Resolve-GameToolPath -Name CODEX_TEST_GAME_TOOL -Fallback @($tool)) -ne $tool) { throw 'discovered fallback did not resolve' }
    $failed=$false
    try { Resolve-GameToolPath -Name CODEX_TEST_GAME_TOOL -Path (Join-Path $testRoot 'missing') | Out-Null } catch { $failed=$true }
    if (-not $failed) { throw 'missing tool was accepted' }
    Write-Output 'PASS: environment directory/file/explicit/fallback/missing path contracts'
} finally {
    [Environment]::SetEnvironmentVariable('CODEX_TEST_GAME_TOOL',$previous,'Process')
    $checked=[IO.Path]::GetFullPath($testRoot)
    if (-not $checked.StartsWith([IO.Path]::GetFullPath($testBase),[StringComparison]::OrdinalIgnoreCase) -or (Split-Path -Leaf $checked) -notlike 'game-skill-env-*') { throw 'unsafe fixture cleanup path' }
    if (Test-Path -LiteralPath $checked) { Remove-Item -LiteralPath $checked -Recurse -Force }
}
