#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trait_dir_evidence.py -- 逐 Trait 目录的堆/代码证据核对

用途：把 trait_catalog.txt（每行一个 Trait 目录名/数据包名）与代码窗口/堆字符串
      交叉比对，输出每个 Trait 在代码中的出现窗口、出现次数、上下文样例，
      形成"该 Trait 是否被代码真实引用、引用强度如何"的证据表。

用法：
  python trait_dir_evidence.py --heap code_windows.json --catalog trait_catalog.txt --json-out trait_dir_evidence.json
  python trait_dir_evidence.py --window-dir windows/ --catalog trait_catalog.txt --json-out evidence.json

说明：
  - 只做"引用存在性"证据，不证明引用路径（路径证明见 associate_trait_dirs）。
  - catalog 文件按行读取，支持 # 注释与空行。
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


def load_catalog(path):
    items = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            items.append(line)
    return items


def load_windows(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        out = []
        for k, v in data.items():
            if isinstance(v, list) and len(v) == 2:
                out.append((k, v[1]))
            elif isinstance(v, str):
                out.append((k, v))
        return out
    if isinstance(data, list):
        return [("%s" % v[0], v[1]) for v in data if isinstance(v, list) and len(v) == 2]
    return []


def main():
    ap = argparse.ArgumentParser(description="逐 Trait 目录证据")
    ap.add_argument("--heap", default="", help="code_windows.json")
    ap.add_argument("--window-dir", default="", help="或 JS 窗口目录")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--json-out", default="trait_dir_evidence.json")
    ap.add_argument("--case-insensitive", action="store_true")
    args = ap.parse_args()

    if args.heap:
        windows = load_windows(args.heap)
    elif args.window_dir:
        windows = []
        for fn in sorted(os.listdir(args.window_dir)):
            if fn.endswith(".js"):
                with open(os.path.join(args.window_dir, fn), "r", encoding="utf-8", errors="replace") as fh:
                    windows.append((fn, fh.read()))
    else:
        print("需要 --heap 或 --window-dir", file=sys.stderr)
        sys.exit(2)

    catalog = load_catalog(args.catalog)
    flag = re.I if args.case_insensitive else 0
    evidences = []
    for trait in catalog:
        pat = re.compile(re.escape(trait), flag)
        hits = []
        total = 0
        for name, code in windows:
            count = len(pat.findall(code))
            if count:
                total += count
                idx = pat.search(code)
                ctx = code[max(0, idx.start() - 120): idx.start() + 160].replace("\n", " ")
                hits.append({"window": name, "count": count, "context": ctx})
        evidences.append({
            "trait": trait,
            "referenced_windows": len(hits),
            "total_occurrences": total,
            "windows": sorted(hits, key=lambda h: -h["count"])[:200],
            "verdict": "referenced" if total > 0 else "no-hit",
        })

    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump({"catalog_size": len(catalog), "windows": len(windows), "evidences": evidences},
                  fh, ensure_ascii=False, indent=2)
    summary = {e["trait"]: e["verdict"] for e in evidences}
    print(json.dumps({"catalog": len(catalog), "windows": len(windows), "summary": summary},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
