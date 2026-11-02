# start_cocos_mcp.ps1 - Launch Cocos Creator and wait for the Funplay MCP server port.
# Part of game-reverse-engineering / modules/cocos-mcp-channel
# Usage (from any harness):
#   powershell -ExecutionPolicy Bypass -File start_cocos_mcp.ps1 -ProjectPath "D:\path\to\cocos-project"
#   powershell ... -Port 8765            # force a known port to probe
#   powershell ... -NoLaunch    # only probe, never launch the editor
# Output: single JSON line with status, mcp_port, mcp_url, editor_running.

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$CocosExe = "",

    # 0 = auto-probe (8765 plus the 20000-20020 project-port band)
    [int]$Port = 0,

    [int]$WaitSeconds = 90,

    # Probe only; never launch the editor when supplied.
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

function Write-JsonResult([hashtable]$h) {
    $h | ConvertTo-Json -Compress -Depth 4 | Write-Output
}

function Test-McpPort([int]$p) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $r = $c.BeginConnect("127.0.0.1", $p, $null, $null)
        $ok = $r.AsyncWaitHandle.WaitOne(800, $false)
        if ($ok -and $c.Connected) { $c.Close(); return $true }
        $c.Close()
    } catch { }
    return $false
}

# --- 1. Validate inputs -----------------------------------------------------
$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath -ErrorAction SilentlyContinue).Path
if (-not $ProjectPath -or -not (Test-Path (Join-Path $ProjectPath "assets"))) {
    Write-JsonResult @{ status = 'ERROR_NOT_A_COCOS_PROJECT'; project = ''; mcp_port = 0; editor_running = $false }
    exit 1
}
if (-not $CocosExe) {
    if ($env:COCOS_3X) { $CocosExe = Join-Path $env:COCOS_3X 'CocosCreator.exe' }
    else { $CocosExe = 'C:\ProgramData\cocos\editors\Creator\3.8.7\CocosCreator.exe' }
}
if (-not $NoLaunch -and -not (Test-Path -LiteralPath $CocosExe)) {
    Write-JsonResult @{ status = 'ERROR_COCOS_EXE_NOT_FOUND'; project = $ProjectPath; mcp_port = 0; editor_running = $false }
    exit 1
}

function Get-EditorRunning {
    return [bool](Get-Process -Name "CocosCreator" -ErrorAction SilentlyContinue)
}

# --- 2. Probe first (idempotent: a live MCP port wins) ----------------------
$probeList = New-Object System.Collections.Generic.List[int]
if ($Port -gt 0) { $probeList.Add($Port) }
$probeList.Add(8765)
# New projects get a stable port in 20000-29999; probe the common front band.
for ($p = 20000; $p -le 20012; $p++) { $probeList.Add($p) }

foreach ($p in $probeList) {
    if (Test-McpPort $p) {
        Write-JsonResult @{ status = 'READY_ALREADY_RUNNING'; project = $ProjectPath; mcp_port = $p; mcp_url = ('http://127.0.0.1:{0}/' -f $p); editor_running = (Get-EditorRunning) }
        exit 0
    }
}

if ($NoLaunch) {
    Write-JsonResult @{ status = 'MCP_NOT_LISTENING'; project = $ProjectPath; mcp_port = 0; editor_running = (Get-EditorRunning) }
    exit 2
}

# --- 3. Launch the editor on the project ------------------------------------
# Lesson from prefab-bake: launch detached with Start-Process, never pipe the
# editor's stdout (EPIPE kills builds silently).
if (-not (Get-Process -Name "CocosCreator" -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $CocosExe -ArgumentList @("--project", ('"' + $ProjectPath + '"')) -WindowStyle Hidden | Out-Null
}

# --- 4. Poll for the MCP listener -------------------------------------------
$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    foreach ($p in $probeList) {
        if (Test-McpPort $p) {
            Write-JsonResult @{ status = 'READY'; project = $ProjectPath; mcp_port = $p; mcp_url = ('http://127.0.0.1:{0}/' -f $p); editor_running = $true }
            exit 0
        }
    }
    Start-Sleep -Seconds 3
}

Write-JsonResult @{ status = 'TIMEOUT_OPEN_FUNPLAY_PANEL_TO_CHECK_PORT'; project = $ProjectPath; mcp_port = 0; editor_running = $true }
exit 3
