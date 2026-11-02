#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_acceptance_report.py -- 生成玩法逻辑/Trait 目录验收报告（对账三套口径）

用途：把"远程清单(manifest) / 本地目录(associate_trait_dirs) / 代码证据
      (trait_dir_evidence) / 目录验收(build_trait_acceptance)"四份 JSON 汇总成
      一页 Markdown，按 Trait 给出 覆盖/部分/缺失/仅远端 判定。

用法：
  python gen_acceptance_report.py --manifest remote_manifest_full.json \
      --mapping mapping.json --evidence trait_dir_evidence.json --out trait_acceptance_report.md
  python gen_acceptance_report.py --manifest m.json --mapping mapping.json \
      --evidence evidence.json --build build_trait_acceptance.json --out report.md
"""
import argparse
import datetime
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load(path, default=None):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return default


def main():
    ap = argparse.ArgumentParser(description="生成 Trait 验收报告")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--mapping", default="")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--build", default="", help="build_trait_acceptance.py 产物")
    ap.add_argument("--out", default="trait_acceptance_report.md")
    args = ap.parse_args()

    manifest = load(args.manifest, {})
    mapping = load(args.mapping, {}) or {}
    evidence = load(args.evidence, {}) or {}
    build = load(args.build, {}) or {}

    lines = []
    lines.append("# 玩法逻辑 / Trait 目录验收报告")
    lines.append("")
    lines.append("- 生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("- 远程清单 bundle 数：%d" % len(manifest.get("bundles", [])))
    lines.append("- 本地映射数：%d，未匹配：%s" %
                 (len(mapping.get("mapping", [])), ", ".join(mapping.get("unmatched_bundles", [])) or "-"))
    lines.append("")
    lines.append("## 1. 逐 Trait 对账")
    lines.append("")
    lines.append("| Trait/Bundle | 本地目录 | 置信度 | 代码引用窗口 | 合计出现 | 判定 |")
    lines.append("|---|---|---|---|---|---|")

    ev_map = {e.get("trait"): e for e in evidence.get("evidences", [])}
    mp_map = {m.get("bundle"): m for m in mapping.get("mapping", [])}
    names = set(ev_map) | set(mp_map)
    names |= {b["name"] for b in manifest.get("bundles", []) if isinstance(b, dict) and b.get("name")}
    if isinstance(build.get("catalog"), list):
        names |= set(build["catalog"])
    for name in sorted(names):
        ev = ev_map.get(name, {})
        mp = mp_map.get(name, {})
        loc = mp.get("local_dir", "-")
        conf = mp.get("confidence", "-")
        ref = ev.get("referenced_windows", 0)
        occ = ev.get("total_occurrences", 0)
        has_local = bool(mp) and loc != "-"
        has_ref = int(ref) > 0
        if has_local and has_ref:
            verdict = "覆盖"
        elif has_local:
            verdict = "仅本地(去重)"
        elif has_ref:
            verdict = "仅代码引用"
        else:
            verdict = "缺失/待确认"
        lines.append("| %s | %s | %s | %d | %d | %s |" % (name, loc, conf, ref, occ, verdict))
    lines.append("")

    lines.append("## 2. 未匹配与低置信度")
    lines.append("")
    um = "`, `".join(mapping.get("unmatched_bundles", [])) or "-"
    lc = "`, `".join(mapping.get("low_confidence", [])) or "-"
    lines.append("- 未匹配 bundles：`%s`" % um)
    lines.append("- 低置信度：`%s`" % lc)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("report written:", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
