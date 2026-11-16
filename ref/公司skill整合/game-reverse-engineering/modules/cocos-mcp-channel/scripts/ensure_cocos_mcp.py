#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ensure_cocos_mcp.py —— 无人值守保证「Cocos 编辑器 + CDP + MCP 服务」三级就绪。

做三件事，缺哪级补哪级（幂等，可反复调用）：
  1. 编辑器在跑吗？不在 → 启动（**必须剔除 ELECTRON_RUN_AS_NODE**，见下方坑 1）
  2. CDP 调试端口在吗？不在且目标实例已退出 → 启动；目标仍活则停止并要求受控重启
  3. MCP 服务在监听吗？不在 → 通过 CDP 在渲染进程里调扩展的 start-server（见坑 2）

用法：
  python ensure_cocos_mcp.py --project E:\\DADAPET
  python ensure_cocos_mcp.py --project <proj> --exe <CocosCreator.exe> --package cocos-creator-mcp
  python ensure_cocos_mcp.py --project <proj> --check-only     # 只探测不启动

退出码：0=harady服务握手及工程身份通过，1=失败；不包含预览/桥接验收。
不会关闭编辑器；CDP工程不匹配或活实例无CDP时停止。不是常驻watchdog。
stdout末行 RESULT=OK|FAIL。端口用 --cdp-port / --mcp-port 指定。

依赖：requests、websockets（pip install requests websockets）

── 两个必读的坑 ───────────────────────────────────────────────
坑 1  ELECTRON_RUN_AS_NODE 污染
      harness 自身若是 Electron 应用（DSH / VS Code / Cursor …），环境里会带
      ELECTRON_RUN_AS_NODE=1。子进程继承后 Electron 以 **Node 模式**运行：
      不建窗口、拒绝 --project 这类 GUI 开关、**退出码 0 静默退出**。
      直接证据：重定向 stderr 会看到 `CocosCreator.exe: bad option: --project`。
      本脚本启动编辑器时会剔除该变量。

坑 2  扩展面板必须人工点（自举死锁）
      MCP 服务跑在编辑器进程内，传统上要人点开扩展面板才 start-server。
      而 UI 自动化点不了：编辑器是 Chromium 渲染（Chrome_WidgetWin_1），
      没有原生菜单栏，UI Automation 找不到 MenuBar；改 window.json 布局
      把面板塞进去也无效（多个 panel id 写法都试过）。
      解法是 CDP 逃生舱：带 --remote-debugging-port 启动，用 DevTools Protocol
      在渲染进程里执行 JS，直接调 Editor.Message.request(pkg, 'start-server')。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import socket
import subprocess
import sys
import time

DEFAULT_EXE = r"C:\ProgramData\cocos\editors\Creator\3.8.7\CocosCreator.exe"
DEFAULT_PKG = "cocos-creator-mcp"
CDP_PORT = 9222
MCP_PORT = 3000

# 会让 Electron 变 Node 模式，启动编辑器前必须剔除
POISON_ENV = ("ELECTRON_RUN_AS_NODE", "NODE_OPTIONS")


def log(msg: str) -> None:
    print("  " + msg, flush=True)


# ── 基础探测 ──────────────────────────────────────────────────────

def editor_procs(project: str | None = None) -> int:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "@(Get-CimInstance Win32_Process -Filter \"Name='CocosCreator.exe'\" | "
         "Where-Object { $_.CommandLine -notmatch '--type=' } | "
         "Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress"],
        capture_output=True, text=True)
    try:
        if r.returncode != 0:
            raise RuntimeError("无法读取编辑器实例，停止启动")
        rows = json.loads(r.stdout) if r.stdout.strip() else []
        if isinstance(rows, dict):
            rows = [rows]
        if project is None:
            return len(rows)
        count = 0
        for row in rows:
            cmd = row.get("CommandLine") or ""
            match = re.search(r'--project(?:=|\s+)(?:"([^"]+)"|(\S+))', cmd)
            if match and same_project(match.group(1) or match.group(2), project):
                count += 1
        return count
    except (ValueError, TypeError):
        raise RuntimeError("编辑器实例返回无法解析，停止启动")


def same_project(left: str, right: str) -> bool:
    return os.path.normcase(os.path.realpath(left)) == os.path.normcase(os.path.realpath(right))


def cdp_identity_matches(project: str) -> bool:
    try:
        identity = cdp_eval("JSON.stringify({path:Editor.Project.path})", timeout=15)
        found = json.loads(identity)["path"]
        if same_project(found, project):
            return True
        log("CDP 工程不匹配: %s；要求 %s。未关闭任何实例。" % (found, project))
    except Exception as exc:
        log("CDP 身份检查失败: %s" % exc)
    return False


def verify_mcp(project: str) -> bool:
    """harady: HTTP + 握手 + 当前工具面 + Resource 工程身份，不靠 TCP。"""
    import requests
    base = "http://127.0.0.1:%d" % MCP_PORT
    try:
        health = requests.get(base + "/health", timeout=10)
        health.raise_for_status()
        if health.json().get("status") != "ok":
            return False
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        def rpc(method, params, request_id=1):
            response = requests.post(base + "/mcp", json={"jsonrpc": "2.0", "id": request_id,
                                      "method": method, "params": params}, headers=headers, timeout=15)
            response.raise_for_status()
            if response.headers.get("Mcp-Session-Id"):
                headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
            raw = response.text
            if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
                raw = "\n".join(line[5:].strip() for line in raw.splitlines() if line.startswith("data:"))
            obj = json.loads(raw)
            if "error" in obj or obj.get("result", {}).get("isError"):
                raise RuntimeError("MCP 语义错误: %s" % obj)
            return obj.get("result", {})
        rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                          "clientInfo": {"name": "cocos-readiness-check", "version": "1"}})
        notice = requests.post(base + "/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                               headers=headers, timeout=15)
        notice.raise_for_status()
        tools = rpc("tools/list", {}, 2).get("tools", [])
        if not tools:
            return False
        resources = rpc("resources/list", {}, 3).get("resources", [])
        if not any(r.get("uri") == "cocos://project/info" for r in resources):
            raise RuntimeError("当前服务未暴露项目身份 Resource，不能判就绪")
        info = rpc("resources/read", {"uri": "cocos://project/info"}, 4)
        paths = [json.loads(c["text"]).get("path") for c in info.get("contents", []) if "text" in c]
        if not any(p and same_project(p, project) for p in paths):
            raise RuntimeError("MCP 工程不匹配: %s" % paths)
        log("MCP 握手、工具面与工程身份通过: %s" % project)
        return True
    except Exception as exc:
        log("MCP 验证失败: %s" % exc)
        return False


def port_open(port: int, timeout: float = 1.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        s.close()
        return False


def clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in POISON_ENV}


# ── 编辑器生命周期 ────────────────────────────────────────────────

def launch_editor(exe: str, project: str, debug: bool) -> None:
    args = [exe, "--project", project, "--can-show-upgrade-dialog", "true"]
    if debug:
        args.append("--remote-debugging-port=%d" % CDP_PORT)
    subprocess.Popen(args, env=clean_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── CDP ──────────────────────────────────────────────────────────

async def _cdp_eval(expr: str, timeout: float = 60):
    import websockets  # 延迟导入，避免没装就整个脚本不可用
    import requests

    tl = requests.get("http://127.0.0.1:%d/json" % CDP_PORT, timeout=5).json()
    target = next((x for x in tl if "main.html" in (x.get("url") or "")), None)
    if target is None:
        raise RuntimeError("CDP 没有 Creator main.html target；不回退到其他页面")

    async with websockets.connect(target["webSocketDebuggerUrl"],
                                  max_size=16 * 1024 * 1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {"expression": expr, "returnByValue": True, "awaitPromise": True},
        }))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if msg.get("id") == 1:
                if "error" in msg or "exceptionDetails" in msg.get("result", {}):
                    raise RuntimeError("CDP evaluate 失败: %s" % msg)
                res = ((msg.get("result") or {}).get("result") or {})
                return res.get("value")


def cdp_eval(expr: str, timeout: float = 60):
    return asyncio.run(_cdp_eval(expr, timeout))


# 先 get-server-status 判断，未运行再 start-server（幂等）
START_JS_TMPL = r"""
(async function(){
  var P = %s;
  try {
    var st = await Editor.Message.request(P,'get-server-status');
    if (st && st.running) return 'ALREADY_RUNNING ' + JSON.stringify(st);
    var r = await Editor.Message.request(P,'start-server');
    return 'STARTED ' + JSON.stringify(r);
  } catch(e) { return 'ERR ' + e.message; }
})()
"""

# 包名探测：同机可能并存多个同类扩展，调错包会报
# "The 'methods' of the module is undefined"
LIST_PKGS_JS = r"""
(async function(){
  try {
    var ps = await Editor.Package.getPackages();
    return JSON.stringify(ps.filter(function(p){return /mcp/i.test(p.name);})
      .map(function(p){return {name:p.name, enable:p.enable, invalid:p.invalid, version:p.version};}));
  } catch(e) { return 'ERR ' + e.message; }
})()
"""


def ensure_editor(exe: str, project: str, check_only: bool) -> bool:
    """保证编辑器 + CDP 端口在线"""
    if port_open(CDP_PORT, 2):
        return cdp_identity_matches(project)
    if check_only:
        log("编辑器或 CDP 不可用（--check-only，不启动）")
        return False

    if editor_procs(project) > 0:
        log("目标编辑器还活着但 CDP 不可用；停止，不强杀。保存场景并计划受控重启。")
        return False
    log("目标编辑器未运行 → 启动新实例；保留其他工程")
    launch_editor(exe, project, debug=True)

    for i in range(60):
        time.sleep(4)
        if port_open(CDP_PORT, 2):
            log("编辑器已起，CDP 就绪（第 %d 次探测）" % (i + 1))
            time.sleep(20)          # 留时间加载场景，否则后续消息易失败
            return cdp_identity_matches(project)

    log("!! 编辑器 4 分钟内未就绪")
    log("   若进程秒退且退出码 0 → 先查 $env:ELECTRON_RUN_AS_NODE")
    return False


def ensure_mcp(pkg: str, check_only: bool, project: str) -> bool:
    """保证 MCP 服务在监听"""
    if port_open(MCP_PORT, 2):
        log("MCP 服务已在监听 %d" % MCP_PORT)
        return verify_mcp(project)
    if check_only:
        log("MCP 未监听（--check-only，不启动）")
        return False

    log("MCP 未监听 → 经 CDP 启动扩展 %s" % pkg)

    # 先列出真实注册的 MCP 相关包，避免调错
    try:
        listed = cdp_eval(LIST_PKGS_JS, timeout=40)
        log("已注册的 MCP 类扩展: %s" % str(listed)[:300])
    except Exception as e:
        log("列举扩展失败（继续尝试）: %s" % str(e)[:120])

    for attempt in range(4):
        try:
            out = cdp_eval(START_JS_TMPL % json.dumps(pkg), timeout=60)
            log("CDP 返回: %s" % str(out)[:220])
            if out and str(out).startswith("ERR") and "methods" in str(out):
                log("   提示：包名 %r 的方法未注册，换一个包名重试"
                    "（用上面列出的实际注册名）" % pkg)
        except Exception as e:
            log("CDP 调用异常: %s" % str(e)[:150])

        for _ in range(10):
            time.sleep(2)
            if port_open(MCP_PORT, 2):
                log("MCP 已监听 %d ✓" % MCP_PORT)
                return verify_mcp(project)
        log("第 %d 次尝试后仍未监听，重试" % (attempt + 1))
    return False


def main() -> int:
    global CDP_PORT, MCP_PORT
    ap = argparse.ArgumentParser(description="保证 Cocos 编辑器 + MCP 服务就绪")
    ap.add_argument("--project", required=True, help="Cocos 工程根目录")
    ap.add_argument("--exe", default=DEFAULT_EXE, help="CocosCreator.exe 路径")
    ap.add_argument("--package", default=DEFAULT_PKG,
                    help="MCP 扩展的注册包名（默认 cocos-creator-mcp）")
    ap.add_argument("--check-only", action="store_true", help="只探测不启动")
    ap.add_argument("--cdp-port", type=int, default=9222, help="目标编辑器独立 CDP 端口")
    ap.add_argument("--mcp-port", type=int, default=3000, help="harady MCP transport 端口（不是预览端口）")
    a = ap.parse_args()
    CDP_PORT, MCP_PORT = a.cdp_port, a.mcp_port
    if not (1 <= CDP_PORT <= 65535 and 1 <= MCP_PORT <= 65535):
        ap.error("端口必须在 1..65535")
    if not os.path.isdir(os.path.join(a.project, "assets")):
        ap.error("工程缺少 assets 目录")

    print("=== ensure_cocos_mcp ===")
    print("  工程   : %s" % a.project)
    print("  编辑器 : %s" % a.exe)
    print("  扩展包 : %s" % a.package)
    print()

    if not ensure_editor(a.exe, a.project, a.check_only):
        print("RESULT=FAIL")
        return 1
    if not ensure_mcp(a.package, a.check_only, a.project):
        print("RESULT=FAIL")
        return 1

    print()
    print("结果: 就绪 ✓    MCP http://127.0.0.1:%d/mcp" % MCP_PORT)
    print("RESULT=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
