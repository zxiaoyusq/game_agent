# -*- coding: utf-8 -*-
"""美术差异复核 · 资源新鲜度门禁（2026-10-19 DADAPET 事故沉淀）。

要解决的坑：git 拉取/合并带来新美术（背景、模型等）后，Cocos 编辑器的 asset-db
**可能还没把这些新文件重新导入**，此时逐屏预览截图会用**旧导入缓存**，产出与
真实当前画面不一致的截图（时间戳却是"本次"的，骗过 freshness 检查）。本脚本先
比对"最新资源文件的落盘/提交时间"与"asset-db 最近一次导入时间"，导入滞后就拦截。

判定：
  newest_src  = max(mtime over --asset-roots 里的美术源文件)
  expected    = max(newest_src, git HEAD 提交时间)   # 未提交改动画资源也要算进
  imported_at = max(mtime over <project>/temp/asset-db/log/*.log、library/.assets*)
  fresh       = imported_at >= expected - grace

用法（独立跑，或作为实拍/探测前置）：
    py -X utf8 artdiff_asset_gate.py --project E:\\DADAPET
    py -X utf8 artdiff_asset_gate.py --project E:\\DADAPET --asset-roots assets/bundle/modle/back,assets/bundle/lobby --refresh --url http://127.0.0.1:3000/mcp

退出码：0=资源已导入(可开拍)；3=导入滞后(已尽力 refresh 仍旧，勿拍，需人工重导入)；2=参数/环境错。
--refresh 会用 MCP asset_manage 尽力触发刷新并轮询导入时间戳前进；无该能力时仅告警。
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ASSET_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp", ".psd",
             ".prefab", ".scene", ".anim", ".atlas", ".json", ".tsx", ".fnt",
             ".ttf", ".mp3", ".wav", ".ogg", ".mtl", ".material", ".effect"}


def _ts(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def newest_source(project: str, roots) -> float:
    newest = 0.0
    for r in roots:
        base = Path(project) / r
        if not base.exists():
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if fn.endswith((".meta",)):        # .meta 与源文件同批，跳过减噪
                    continue
                if os.path.splitext(fn)[1].lower() in ASSET_EXT:
                    m = _ts(Path(dirpath) / fn)
                    if m > newest:
                        newest = m
    return newest


def git_head_time(project: str) -> float:
    try:
        out = subprocess.run(["git", "-C", project, "log", "-1", "--format=%ct"],
                             capture_output=True, text=True, timeout=10)
        return float(out.stdout.strip()) if out.stdout.strip() else 0.0
    except Exception:
        return 0.0


def last_import(project: str) -> float:
    newest = 0.0
    pats = [str(Path(project) / "temp" / "asset-db" / "log" / "*.log"),
            str(Path(project) / "library" / ".assets*")]
    for pat in pats:
        for f in glob.glob(pat):
            newest = max(newest, _ts(Path(f)))
    return newest


def try_refresh(url: str, timeout: int) -> bool:
    """尽力触发 MCP 资源刷新（不同扩展 action 名不一，逐个试；失败不致命）。"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from mcp_http import McpHttp
    except Exception as e:
        print("  无法导入 mcp_http，跳过自动 refresh:", str(e)[:100])
        return False
    m = McpHttp(url, call_timeout=60)
    sid = m.session()
    for tool, args in (("asset_manage", {"action": "refresh"}),
                       ("asset_manage", {"action": "reimport"}),
                       ("asset_manage", {"action": "refresh-asset"}),
                       ("project_manage", {"action": "refresh-assets"})):
        try:
            r = m.call(tool, args, sid, timeout=30)
            txt = m.text(r)
            if "Unknown" not in txt and "not exist" not in txt and "invalid" not in txt.lower():
                print("  已触发 %s %s -> %s" % (tool, args.get("action"), txt[:80].replace("\n", " ")))
                return True
        except Exception as e:
            print("  refresh 尝试 %s/%s 异常: %s" % (tool, args.get("action"), str(e)[:80]))
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--asset-roots", default="assets",
                    help="逗号分隔、相对工程的美术目录（默认 assets；可缩到具体 bundle 目录）")
    ap.add_argument("--grace-min", type=int, default=5, help="允许的导入滞后（分钟）")
    ap.add_argument("--refresh", action="store_true", help="导入滞后时尝试 MCP 刷新并轮询")
    ap.add_argument("--url", default="http://127.0.0.1:3000/mcp")
    ap.add_argument("--wait-min", type=int, default=4, help="refresh 后最多再等导入完成多少分钟")
    a = ap.parse_args()

    if not os.path.isdir(os.path.join(a.project, "assets")):
        print("工程缺 assets 目录:", a.project)
        return 2

    roots = [r.strip() for r in a.asset_roots.split(",") if r.strip()]
    ns = newest_source(a.project, roots)
    ht = git_head_time(a.project)
    expected = max(ns, ht)
    imp = last_import(a.project)
    fmt = lambda t: datetime.fromtimestamp(t).strftime("%m-%d %H:%M") if t else "—"

    print("=== 资源新鲜度门禁 ===")
    print("  最新美术源文件: %s (%s)" % (fmt(ns), max([str(Path(a.project)/r) for r in roots])))
    print("  git HEAD 提交 : %s" % fmt(ht))
    print("  期望不早于    : %s" % fmt(expected))
    print("  asset-db 导入 : %s" % fmt(imp))

    if imp >= expected - a.grace_min * 60:
        print("\n结论：FRESH ✓ 资源已导入，可以开拍。")
        return 0

    print("\n结论：STALE ✗ 导入(%s) 落后于最新资源/提交(%s)，此刻预览会用旧导入缓存！"
          % (fmt(imp), fmt(expected)))
    if not a.refresh:
        print("  未加 --refresh：请在编辑器里对拉取到的资源目录做一次 右键→导入/重新导入，")
        print("  或加 --refresh 让脚本经 MCP 触发；导入日志时间戳前进后再实拍。")
        return 3

    print("  尝试经 MCP 触发刷新并等待导入完成（最多 %d 分钟）..." % a.wait_min)
    try_refresh(a.url, a.wait_min * 60)
    deadline = time.time() + a.wait_min * 60
    while time.time() < deadline:
        time.sleep(6)
        imp2 = last_import(a.project)
        if imp2 > imp and imp2 >= expected - a.grace_min * 60:
            print("\n结论：FRESH ✓ refresh 后导入已推进到 %s。" % fmt(imp2))
            return 0
        if imp2 > imp:
            print("  导入进行中… %s" % fmt(imp2))
            imp = imp2
    print("\n结论：仍 STALE ✗ refresh 后导入未越过期望时间，勿拍，需人工重导入并确认。")
    return 3


if __name__ == "__main__":
    sys.exit(main())
