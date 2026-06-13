#Requires -Version 5.1
<#
.SYNOPSIS
  一键同时启动 后端 (FastAPI) + 前端 (Vite) 的开发脚本（Windows / PowerShell 版本）。

.DESCRIPTION
  使用方式：
    .\dev.ps1                                # 同时启动前后端，Ctrl+C 一起退出
    .\dev.ps1 backend                        # 只起后端
    .\dev.ps1 frontend                       # 只起前端
    $env:BACKEND_PORT = 8001; .\dev.ps1      # 自定义后端端口
    $env:CONDA_ENV    = 'myenv'; .\dev.ps1   # 自定义 conda 环境

  默认端口：后端 8000，前端 由 vite 自行选择 (5173+)
  日志文件：.\logs\backend.log、.\logs\frontend.log

  注意：
    1. 首次执行可能被 PowerShell 执行策略拦截，可临时使用：
         powershell -ExecutionPolicy Bypass -File .\dev.ps1
       或一次性允许当前用户：
         Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
    2. 需要系统 PATH 中有 conda 与 npm。
#>

[CmdletBinding()]
param(
    [ValidateSet('all', 'backend', 'frontend')]
    [string]$Mode = 'all'
)

# ---- 路径常量 -------------------------------------------------------------

$RootDir     = $PSScriptRoot
$BackendDir  = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'
$LogDir      = Join-Path $RootDir 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$BackendLog  = Join-Path $LogDir 'backend.log'
$FrontendLog = Join-Path $LogDir 'frontend.log'

# 端口、conda 环境支持环境变量覆盖（与 dev.sh 行为保持一致）
$BackendPort = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$CondaEnv    = if ($env:CONDA_ENV)    { $env:CONDA_ENV }         else { '313' }

# ---- 工具函数 -------------------------------------------------------------

function Write-Info { param([string]$Msg) Write-Host "[dev] $Msg" -ForegroundColor Blue }
function Write-Warn { param([string]$Msg) Write-Host "[dev] $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "[dev] $Msg" -ForegroundColor Red }

# 端口是否被监听（仅检查 Listen 状态，等价于 lsof -sTCP:LISTEN）
function Test-PortInUse {
    param([int]$Port)
    try {
        $null = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# ---- 启动函数 -------------------------------------------------------------

# 脚本作用域记录子进程对象，便于在 finally 里统一清理
$script:BackendProc  = $null
$script:FrontendProc = $null

function Start-Backend {
    # 1) 端口预检
    if (Test-PortInUse -Port $BackendPort) {
        Write-Err "后端端口 $BackendPort 已被占用，请先释放或设置 `$env:BACKEND_PORT=其它端口"
        Write-Err "查看占用：Get-NetTCPConnection -LocalPort $BackendPort -State Listen"
        return $false
    }
    # 2) 入口文件预检
    $mainPy = Join-Path $BackendDir 'app\main.py'
    if (-not (Test-Path $mainPy)) {
        Write-Err "未找到 $mainPy，目录结构是否正确？"
        return $false
    }
    # 3) conda 预检
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Write-Err "PATH 中找不到 conda，请确认已安装 miniconda/anaconda 并把 Scripts 目录加入 PATH"
        return $false
    }

    Write-Info "启动后端 uvicorn @ 127.0.0.1:$BackendPort  (conda env: $CondaEnv)"
    Write-Info "日志：$BackendLog"

    # 清空旧日志，避免上一次内容残留
    Set-Content -Path $BackendLog -Value '' -Encoding UTF8

    # 通过 cmd /c "...> log 2>&1" 把 stdout+stderr 合并到同一份日志（PowerShell 的 Start-Process
    # 不允许把 stdout 和 stderr 同时重定向到同一个文件，借 cmd 来做合并是最干净的写法）。
    # 用 conda run 直接在指定 env 中执行命令，无需先 activate，跨 shell 通用。
    $cmdLine = "conda run --no-capture-output -n $CondaEnv uvicorn app.main:app --reload --port $BackendPort > `"$BackendLog`" 2>&1"
    $script:BackendProc = Start-Process -FilePath 'cmd.exe' `
        -ArgumentList @('/c', $cmdLine) `
        -WorkingDirectory $BackendDir `
        -NoNewWindow -PassThru
    Set-Content -Path (Join-Path $LogDir 'backend.pid') -Value $script:BackendProc.Id
    return $true
}

function Start-Frontend {
    # 1) package.json 预检
    $pkgJson = Join-Path $FrontendDir 'package.json'
    if (-not (Test-Path $pkgJson)) {
        Write-Err "未找到 $pkgJson"
        return $false
    }
    # 2) 首次启动自动 npm install
    if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
        Write-Warn "未发现 node_modules，先执行 npm install（首次启动）"
        Push-Location $FrontendDir
        try {
            & npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Err "npm install 失败"
                return $false
            }
        } finally {
            Pop-Location
        }
    }

    Write-Info "启动前端 vite，日志：$FrontendLog"
    Set-Content -Path $FrontendLog -Value '' -Encoding UTF8

    # 同样借 cmd 做 stdout+stderr 合并；npm 在 Windows 上是 npm.cmd，必须由 cmd 解析
    $cmdLine = "npm run dev > `"$FrontendLog`" 2>&1"
    $script:FrontendProc = Start-Process -FilePath 'cmd.exe' `
        -ArgumentList @('/c', $cmdLine) `
        -WorkingDirectory $FrontendDir `
        -NoNewWindow -PassThru
    Set-Content -Path (Join-Path $LogDir 'frontend.pid') -Value $script:FrontendProc.Id
    return $true
}

# ---- 清理：脚本退出时同步 kill 子进程 -------------------------------------

function Stop-Children {
    Write-Host ""
    Write-Info "正在停止子进程…"
    # uvicorn --reload 与 vite 都会派生子进程（reloader / esbuild 等），必须用 /T 连根杀掉，
    # 否则就会出现"脚本退出后端口仍被占用 / 日志被孤儿继续追写"的问题。
    foreach ($p in @($script:BackendProc, $script:FrontendProc)) {
        if ($null -eq $p) { continue }
        try {
            if (-not $p.HasExited) {
                & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-Null
            }
        } catch {
            # 忽略：进程可能在我们检查的瞬间已经退出
        }
    }
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $LogDir 'backend.pid')
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $LogDir 'frontend.pid')
    Write-Info "已退出。"
}

# ---- 主流程 ---------------------------------------------------------------

try {
    switch ($Mode) {
        'backend'  { if (-not (Start-Backend))  { exit 1 } }
        'frontend' { if (-not (Start-Frontend)) { exit 1 } }
        default    {
            if (-not (Start-Backend))  { exit 1 }
            if (-not (Start-Frontend)) { exit 1 }
        }
    }

    Write-Info "全部启动完成。"
    Write-Host ""
    Write-Host "   后端: http://127.0.0.1:$BackendPort/docs"
    Write-Host "   前端: 见下方 vite 输出的 Local 地址（默认 http://localhost:5173/）"
    Write-Host ""
    Write-Info "实时日志（Ctrl+C 退出）："
    Write-Host ""

    # ---- tail -F 的 PowerShell 实现 ---------------------------------------
    # 思路：记录每个日志当前读到的字节偏移，循环检查文件大小变化并把增量打到控制台；
    # 用 FileShare.ReadWrite 打开避免与正在写日志的子进程冲突。
    $tailFiles = @()
    if ($script:BackendProc)  { $tailFiles += $BackendLog }
    if ($script:FrontendProc) { $tailFiles += $FrontendLog }

    $positions = @{}
    foreach ($f in $tailFiles) {
        $positions[$f] = if (Test-Path $f) { (Get-Item $f).Length } else { 0 }
    }

    while ($true) {
        foreach ($f in $tailFiles) {
            if (-not (Test-Path $f)) { continue }
            $size = (Get-Item $f).Length
            if ($size -gt $positions[$f]) {
                $fs = [System.IO.File]::Open(
                    $f,
                    [System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::Read,
                    [System.IO.FileShare]::ReadWrite
                )
                try {
                    $fs.Seek($positions[$f], [System.IO.SeekOrigin]::Begin) | Out-Null
                    $sr = New-Object System.IO.StreamReader($fs)
                    $chunk = $sr.ReadToEnd()
                } finally {
                    $fs.Dispose()
                }
                if ($chunk) { Write-Host -NoNewline $chunk }
                $positions[$f] = $size
            } elseif ($size -lt $positions[$f]) {
                # 文件被截断（少见，比如有人手动清空日志），重置偏移
                $positions[$f] = 0
            }
        }

        # 任一子进程退出 -> 跳出循环，进入 finally 清理
        $backendDead  = $script:BackendProc  -and $script:BackendProc.HasExited
        $frontendDead = $script:FrontendProc -and $script:FrontendProc.HasExited
        if ($backendDead -or $frontendDead) {
            Write-Warn "检测到子进程已退出。"
            break
        }
        Start-Sleep -Milliseconds 300
    }
}
finally {
    # 不论是 Ctrl+C、子进程崩溃还是 exit，都会走到这里统一清理
    Stop-Children
}
