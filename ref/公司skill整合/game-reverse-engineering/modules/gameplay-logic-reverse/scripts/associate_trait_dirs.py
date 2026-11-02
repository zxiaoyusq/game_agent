#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
associate_trait_dirs.py -- 把远程 Bundle 与本地资产目录做关联

用途：APK 解包后的 assets/ 目录结构与 CDN 上的远程 bundle 结构往往不一致
      （版本号目录、命名带指纹、资源散列目录等）。本脚本按"名字 / 版本 /
      目录名包含 / config.json 所在位置"等信号，输出
      { remote_bundle -> { local_dir, confidence, reason } } 映射，
      供后续 trait_dir_evidence.py 与 build_trait_acceptance.py 对账。

用法：
  python associate_trait_dirs.py --local <decoded>/assets --remote remote_manifest_full.json --out mapping.json
  python associate_trait_dirs.py --local assets --remote m.json --extra-assets <decoded>/assets/remote_seed --out mapping.json

说明：输出是"候选关联"，不是硬结论；每组都带 confidence 与 reason，人工复核
      低置信度条目。
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def scan_dirs(root):
    """返回 [{abs, rel, basename}] 目录列表。"""
    out = []
    for base, dirs, files in os.walk(root):
        rel = os.path.relpath(base, root).replace("\\", "/")
        out.append({"abs": base, "rel": rel if rel != "." else "", "basename": os.path.basename(base)})
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
    return out


def score_dir(dirinfo, bundle):
    """打分：名字完全/部分/版本/URL 片段匹配。"""
    score = 0
    reasons = []
    name = bundle.get("name", "")
    version = str(bundle.get("version", ""))
    url = bundle.get("url", "")
    parts = [p for p in re.split(r"[/:.]", url) if p]
    base = dirinfo["basename"].lower()
    rel = dirinfo["rel"].lower()
    if base == name.lower():
        score += 10
        reasons.append("basename==bundle.name")
    elif name.lower() in rel or rel.endswith(name.lower()):
        score += 6
        reasons.append("rel contains bundle.name")
    if version and version != "latest" and (version.lower() in rel or version.lower() == base):
        score += 4
        reasons.append("version marker present")
    if parts and any(p.lower() == base for p in parts):
        score += 3
        reasons.append("url path fragment matches")
    # config.json 存在与否
    if os.path.exists(os.path.join(dirinfo["abs"], "config.json")):
        score += 2
        reasons.append("config.json present")
    return score, reasons


def main():
    ap = argparse.ArgumentParser(description="关联远程 Bundle 与本地目录")
    ap.add_argument("--local", required=True, help="本地资产根目录（解包 assets/）")
    ap.add_argument("--remote", required=True, help="remote_manifest_full.json")
    ap.add_argument("--out", default="mapping.json")
    ap.add_argument("--min-score", type=int, default=3)
    args = ap.parse_args()

    with open(args.remote, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    dirs = scan_dirs(args.local)
    mapping = {"mapping": [], "unmatched_bundles": [], "low_confidence": []}
    for bundle in manifest.get("bundles", []):
        best = None
        for d in dirs:
            score, reasons = score_dir(d, bundle)
            if best is None or score > best[0]:
                best = (score, reasons, d)
        if best and best[0] >= args.min_score:
            score, reasons, d = best
            entry = {"bundle": bundle["name"], "version": bundle.get("version"),
                     "local_dir": d["rel"], "abs": d["abs"],
                     "confidence": "high" if score >= 10 else ("medium" if score >= 6 else "low"),
                     "score": score, "reasons": reasons}
            mapping["mapping"].append(entry)
            if entry["confidence"] == "low":
                mapping["low_confidence"].append(entry["bundle"])
        else:
            mapping["unmatched_bundles"].append(bundle["name"])

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"matched": len(mapping["mapping"]), "unmatched": len(mapping["unmatched_bundles"]),
                      "low_confidence": len(mapping["low_confidence"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
