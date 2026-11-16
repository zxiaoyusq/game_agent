# -*- coding: utf-8 -*-
"""美术差异复核 · 逐屏运行态实拍（泛化自 DSH runtime_shots.py，2026-10-19 实测版）。

前置：
  1) 编辑器已打开目标工程，MCP 扩展服务已启动（/mcp 可达）
  2) 游戏内已装 DebugBridge（见 references/art-diff-reaudit.md 的恢复-不提交模式）
  3) 界面清单 JSON（项目事实，不写死在脚本）：
     {
       "pages":      [{"page": "LobbyMain"}, {"page": "Breed"}],   // 采集顺序
       "root_of":    {"Language": "Setting", "Nickname": "Setting"},// 子视图 -> 所属预制体根
       "never_kill": ["StateBubble", "LobbyFunc"],                  // 常驻层，清残留时跳过
       "extra_kill": ["TextTipsTop", "GlobalTipsTop"]               // closeAll 管不到的 toast 层
     }

用法:
    py -X utf8 artdiff_runtime_shots.py --pages-json pages.json --out E:\\artindex\\runtime
    py -X utf8 artdiff_runtime_shots.py --pages-json pages.json --only Breed,Shop --redo

坑（详见 references/art-diff-reaudit.md）：
  - 编辑器失焦 → 预览游戏循环被节流 → 命令间歇超时；先把编辑器窗口拉前台
  - FAIL ≠ 没截图：重试前查时间戳；skip 按"文件存在"会跳过旧构建旧图 → --redo 强制
  - 桥与主线 API 漂移 → navigate 返回 "(intermediate value)..." → 改未提交的桥代码
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_http import McpHttp  # noqa: E402

NAV_WAIT = 1.6
SHOT_WAIT = 0.5


def foreground_editor(proc_names=("CocosCreator",)):
    """把编辑器窗口拉前台（SW_RESTORE + SetForegroundWindow）。

    harady 预览跑在编辑器 GameView 里，编辑器失焦时预览游戏循环被节流，
    命令会间歇超时、积压帧在重新聚焦时倾泻——是本模块实拍的头号不稳定源。
    纯 ctypes 找主窗口，不依赖外部 ps1；找不到窗口就静默返回。"""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        target_pids = set()
        # 用进程快照枚举 CocosCreator 主进程 pid
        PSAPI = 0x00000002  # TH32CS_SNAPPROCESS
        class PE32(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                        ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]
        snap = kernel32.CreateToolhelp32Snapshot(PSAPI, 0)
        try:
            pe = PE32(); pe.dwSize = ctypes.sizeof(PE32)
            if kernel32.Process32First(snap, ctypes.byref(pe)):
                while True:
                    name = pe.szExeFile.decode("utf-8", "ignore").lower().replace(".exe", "")
                    if name in [p.lower() for p in proc_names]:
                        target_pids.add(pe.th32ProcessID)
                    if not kernel32.Process32Next(snap, ctypes.byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(snap)

        found = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_cb(hwnd, _l):
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in target_pids and user32.GetWindowTextLengthW(hwnd) > 5:
                found.append(hwnd)
            return True

        user32.EnumWindows(enum_cb, 0)
        for h in found:
            user32.ShowWindow(h, 9)   # SW_RESTORE
            user32.SetForegroundWindow(h)
        return bool(found)
    except Exception:
        return False


def run_ensure(ensure_path, project, extra=None, timeout=600):
    """MCP/编辑器死亡时自愈：跑 ensure_cocos_mcp.py（幂等）。"""
    if not ensure_path:
        return False
    cmd = [sys.executable, "-X", "utf8", ensure_path]
    if project:
        cmd += ["--project", project]
    if extra:
        cmd += extra
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        tail = ((rc.stdout or "") + (rc.stderr or "")).strip()
        print("     ensure ->", ("RESULT=OK" if "RESULT=OK" in tail else "RESULT=FAIL"),
              "| " + tail.replace("\n", " ")[-200:], flush=True)
        return "RESULT=OK" in tail
    except Exception as ex:
        print("     自愈脚本异常:", str(ex)[:120], flush=True)
        return False


def load_pages(path):
    cfg = json.load(open(path, encoding="utf-8"))
    pages = [p["page"] if isinstance(p, dict) else str(p) for p in cfg["pages"]]
    root_of = cfg.get("root_of", {})
    never = set(cfg.get("never_kill", []))
    extra = list(cfg.get("extra_kill", []))
    all_roots = sorted({root_of.get(n, n) for n in pages} - never)
    return pages, root_of, never, extra, all_roots


def save_shot(raw_bytes: bytes, dst: Path, thresh=30, ratio=0.98):
    """把截图字节统一解码为真 PNG 落盘，并尽力裁掉上下纯黑带。

    不同工程的桥 screenshot 落盘格式不一（DADAPET 返回 webp 到 temp/screenshots/*.webp），
    文件名扩展名不能只信，一律按**内容**解码再存成 dst 指定的真 PNG。PIL 不可用时原样落盘。"""
    try:
        import io
        import numpy as np
        from PIL import Image
        im = Image.open(io.BytesIO(raw_bytes))
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        a = np.asarray(im.convert("RGB"))
        h, w = a.shape[0], a.shape[1]
        black = lambda y: (a[y].sum(axis=1) < thresh).mean() >= ratio
        top = 0
        while top < h - 1 and black(top):
            top += 1
        bot = h
        while bot > top + 1 and black(bot - 1):
            bot -= 1
        if top or bot < h:
            im = im.crop((0, top, w, bot))
        im.save(dst, "PNG")
    except Exception:
        dst.write_bytes(raw_bytes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:3000/mcp")
    ap.add_argument("--pages-json", required=True, help="界面清单 JSON（见文件头）")
    ap.add_argument("--out", required=True, help="截图输出目录")
    ap.add_argument("--only", default="", help="只跑这些界面（逗号分隔）")
    ap.add_argument("--redo", action="store_true", help="已存在的旧图也重截（本 run 刚产出的仍会 resume 跳过）")
    ap.add_argument("--project", default="", help="工程根目录：崩溃自愈时传给 ensure_cocos_mcp")
    ap.add_argument("--ensure-mcp", default="", help="MCP 死亡时的自愈脚本路径（如 ensure_cocos_mcp.py），空=不自动拉起")
    ap.add_argument("--no-foreground", action="store_true", help="不自动把编辑器拉前台")
    ap.add_argument("--max-width", type=int, default=750)
    a = ap.parse_args()

    pages, root_of, never, extra, all_roots = load_pages(a.pages_json)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    want = {s.strip() for s in a.only.split(",") if s.strip()} or None
    run_start = time.time()          # 用于 resume：本 run 刚产出的文件不重复截

    def fg():
        if not a.no_foreground:
            foreground_editor()

    m = McpHttp(a.url, call_timeout=60)
    sid = None

    def connect():
        """建立会话；连接被拒（编辑器已死）则先 ensure 再重试。"""
        nonlocal sid
        for attempt in range(3):
            try:
                m.call_timeout = 30
                sid = m.session()
                print("MCP 会话就绪")
                return True
            except Exception as e:
                print("连接 MCP 失败(第%d次): %s" % (attempt + 1, str(e)[:120]), flush=True)
                if a.ensure_mcp:
                    print("     触发自愈 ensure ...", flush=True)
                    run_ensure(a.ensure_mcp, a.project)
                    fg()
                else:
                    time.sleep(5)
        return False

    def cmd(ctype, args=None, timeout=15000):
        r = m.call("debug_game_command",
                   {"type": ctype, "args": args or {}, "timeout": timeout,
                    "maxWidth": a.max_width, "imageFormat": "png"}, sid)
        try:
            return json.loads(m.text(r))
        except Exception:
            return {"raw": m.text(r)[:200]}

    def healthy(timeout=8):
        try:
            m.call_timeout = timeout
            return "result" in m.call("server_status", {"action": "port"}, sid)
        except Exception:
            return False
        finally:
            m.call_timeout = 60

    def start_preview_clean():
        """干净重启预览：先 stop 再 start（裸 start 在预览已起时会卡住）。"""
        m.call_timeout = 90
        try:
            m.call("debug_preview", {"action": "stop"}, sid)
        except Exception:
            pass
        time.sleep(1.5)
        try:
            m.call("debug_preview", {"action": "start"}, sid)
        except Exception as e:
            print("  启动预览异常:", str(e)[:120])

    def wait_bridge(trips=16, per=6):
        for _ in range(trips):
            time.sleep(per)
            m.call_timeout = 40
            try:
                if cmd("pages", timeout=12000).get("success"):
                    return True
            except Exception:
                pass
        return False

    def enter_lobby_retry(trips=5):
        """全新预览默认走引导 Stage；enterLobby 未成功则退避重试。"""
        for i in range(trips):
            try:
                if cmd("enterLobby", timeout=30000).get("success"):
                    time.sleep(2.0)
                    return True
            except Exception:
                pass
            time.sleep(4 + i * 2)
        return False

    fg()
    if not connect():
        print("!! 无法连接 MCP（编辑器未起或端口不通）。加 --ensure-mcp + --project 可自动拉起。")
        return

    # 桥就绪；不在线则干净启动预览并等待
    if not wait_bridge(trips=1, per=1) and not cmd("pages", timeout=8000).get("success"):
        print("桥接未连接，干净启动游戏预览 ...")
        start_preview_clean()
        if not wait_bridge():
            print("预览起了但桥未连，跑 ensure 再来一次 ...")
            if run_ensure(a.ensure_mcp, a.project):
                fg()
                connect(); start_preview_clean(); wait_bridge()
    if not cmd("pages", timeout=10000).get("success"):
        print("!! DebugBridge 未连接：① 预览是否启动 ② MCP 是否存活 ③ 桥是否接进 GameApp")
        return
    print("DebugBridge 在线，支持 %d 个界面" % len((cmd('pages', timeout=10000).get('data') or [])))

    if not enter_lobby_retry():
        print("!! enterLobby 多次失败（桥未实现该命令 / 未重编译 / 引导态卡住）")
        return
    print("已进入大厅")

    ok, skip, fail = [], [], []
    todo = [p for p in pages if not want or p in want]
    for i, page in enumerate(todo, 1):
        root = root_of.get(page, page)
        dst = out / ("%s.png" % page)
        # resume：本 run 刚产出的直接跳过；否则按 --redo 决定是否重截旧图
        if dst.exists() and dst.stat().st_mtime >= run_start - 1:
            skip.append(page)
            print("[%2d/%d] SKIP %-14s 本 run 已产出（resume）" % (i, len(todo), page), flush=True)
            continue
        if dst.exists() and not a.redo:
            skip.append(page)
            print("[%2d/%d] SKIP %-14s 已存在旧图（用 --redo 强制）" % (i, len(todo), page), flush=True)
            continue

        # 自愈：MCP 死亡 → ensure 拉起 + 干净重启预览 + 重新 enterLobby，恢复后**继续本批**
        if not healthy():
            print("     MCP 无响应，尝试自愈 ...", flush=True)
            run_ensure(a.ensure_mcp, a.project)
            fg()
            connect()
            start_preview_clean()
            recovered = wait_bridge()
            if recovered:
                enter_lobby_retry()
            if not recovered:
                fail.append((page, "恢复失败"))
                print("     恢复失败，中止本批（重跑同命令会 resume 续采）", flush=True)
                break
            print("     已恢复，续采", flush=True)

        fg()   # 每屏前拉前台，压住失焦节流引起的间歇超时
        t0 = time.time()
        try:
            ca = cmd("closeAll", timeout=10000)
            if not ca.get("success"):
                raise RuntimeError("closeAll 失败: " + json.dumps(ca, ensure_ascii=False)[:120])
            left = (ca.get("data") or {}).get("after")
            if isinstance(left, int) and left > 0:
                cmd("navigate", {"page": pages[0]}, timeout=15000)
                time.sleep(0.8)
                cmd("closeAll", timeout=10000)
            time.sleep(0.5)

            others = [n for n in all_roots if n != root] + [n for n in extra if n != root]
            if others:
                kn = cmd("killnodes", {"names": others}, timeout=10000)
                kd = (kn.get("data") or {}) if kn.get("success") else {}
                if kd.get("killed"):
                    print("      清残留 %s 个节点" % kd.get("killed"), flush=True)
            time.sleep(0.3)

            nav = cmd("navigate", {"page": page}, timeout=20000)
            if not nav.get("success"):
                raise RuntimeError("navigate: " + json.dumps(nav, ensure_ascii=False)[:140])
            time.sleep(NAV_WAIT)

            shot = cmd("screenshot", timeout=25000)
            if not shot.get("success"):
                raise RuntimeError("screenshot: " + json.dumps(shot, ensure_ascii=False)[:140])
            # 桥落盘/内联两种模式，且 path/dataUrl 可能在顶层或 data 内 —— 两种形状都吃
            data = shot.get("data") or {}
            src_path = data.get("path") or shot.get("path")
            src_url = data.get("dataUrl") or shot.get("dataUrl")
            if src_path:
                srcp = Path(src_path)
                if not srcp.exists():
                    raise RuntimeError("截图文件不存在: %s" % srcp)
                raw_bytes = srcp.read_bytes()
            elif src_url:
                raw_bytes = base64.b64decode(src_url.split(",", 1)[-1])
            else:
                raise RuntimeError("screenshot 返回无 path/dataUrl: %s" % json.dumps(shot)[:160])
            save_shot(raw_bytes, dst)          # 按内容解码为真 PNG（源常为 webp），并裁黑边
            time.sleep(SHOT_WAIT)
            ok.append(page)
            print("[%2d/%d] OK   %-14s %.1fs" % (i, len(todo), page, time.time() - t0), flush=True)
        except Exception as e:
            fail.append((page, str(e)[:130]))
            print("[%2d/%d] FAIL %-14s %s" % (i, len(todo), page, str(e)[:130]), flush=True)

    print("\n成功 %d / 跳过 %d / 失败 %d" % (len(ok), len(skip), len(fail)))
    for p, e in fail:
        print("  FAIL %-14s %s" % (p, e))
    (out / "_result.json").write_text(
        json.dumps({"ok": ok, "skip": skip, "fail": fail}, ensure_ascii=False, indent=1),
        encoding="utf-8")


if __name__ == "__main__":
    main()
