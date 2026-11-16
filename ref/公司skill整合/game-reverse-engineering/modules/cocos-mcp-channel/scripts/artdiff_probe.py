# -*- coding: utf-8 -*-
"""美术差异复核 · 桥就绪探测：先跑资源新鲜度门禁 → 启动预览 → pages/closeAll/enterLobby 三连。

通过 = 当前美术已导入 asset-db、桥已编译进构建、预览存活、Stage 门禁已解除，可以逐屏实拍。
资源门禁防的坑：git 拉取带来的新背景/模型若 asset-db 未重新导入，预览会用旧导入缓存，
截出与真实画面不一致的图（时间戳却像本次）——DADAPET 2026-10-19 第 4 轮实拍踩到。
失败排查顺序：编辑器进程/3000 端口 → debug_preview start → 编译错误（read_console）
→ 桥是否接进 GameApp → 桥是否调用了主线已删除的 API（"(intermediate value)..."）。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_http import McpHttp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:3000/mcp")
    ap.add_argument("--project", default="", help="工程根目录；提供则先跑资源新鲜度门禁")
    ap.add_argument("--asset-roots", default="assets", help="逗号分隔美术目录（传给门禁）")
    ap.add_argument("--refresh", action="store_true", help="门禁判定滞后时尝试 MCP 触发 reimport")
    ap.add_argument("--skip-gate", action="store_true", help="跳过资源新鲜度门禁")
    a = ap.parse_args()

    # 前置：资源新鲜度门禁，防「预览用旧导入缓存」
    if a.project and not a.skip_gate:
        gate = str(Path(__file__).parent / "artdiff_asset_gate.py")
        gargs = [sys.executable, "-X", "utf8", gate, "--project", a.project,
                 "--asset-roots", a.asset_roots, "--url", a.url]
        if a.refresh:
            gargs.append("--refresh")
        if subprocess.run(gargs).returncode != 0:
            print("!! 资源新鲜度门禁未通过：先让 asset-db 导入完新美术再实拍，否则截图会与"
                  "真实画面不一致。确认无碍可加 --skip-gate。")
            return
        print("— 资源新鲜度门禁通过，继续桥探测 —\n")

    m = McpHttp(a.url, call_timeout=60)
    sid = m.session()

    def cmd(ctype, timeout=25000):
        r = m.call("debug_game_command", {"type": ctype, "args": {}, "timeout": timeout}, sid)
        try:
            return json.loads(m.text(r))
        except Exception:
            return {"raw": m.text(r)[:200]}

    try:
        r = m.call("debug_preview", {"action": "start"}, sid)
        print("preview:", m.text(r).replace("\n", " ")[:120])
    except Exception as e:
        print("preview EXC:", str(e)[:150])
    time.sleep(20)

    ok_all = True
    for c in ("pages", "closeAll", "enterLobby"):
        r = cmd(c)
        ok = bool(r.get("success"))
        ok_all &= ok
        print("%-11s %s  %s" % (c, "OK  " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:160]))
    print("\n结论：", "桥就绪，可以开跑" if ok_all else "桥未就绪，按文件头排查顺序定位")


if __name__ == "__main__":
    main()
