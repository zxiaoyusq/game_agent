#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_algo_traits.py -- 从 JS 代码窗口提取"算法方法 + Trait 关联"线索

背景：Cocos/JS 项目里，算法（洗牌、权重、种子、哈希、随机数、AI 决策）往往散布在
      多个类方法中，并挂载在 Trait（数据包/配置目录）上。本脚本以正则启发式做第一遍
      定性提取，产物是证据线索，不是最终结论；结论需与远端 bundle/Trait 目录证据
      互相印证（见 gen_remote_manifest / trait_dir_evidence / build_trait_acceptance）。

用法：
  python extract_algo_traits.py --code-windows code_windows.json --out algo_traits.json
  python extract_algo_traits.py --window-dir windows/ --out algo_traits.json

输入 code_windows.json 结构（extract_js_from_heap.py 产物）：
  { "<key>": ["<src>", "<code>"] }  或  [["<src>", "<code>"], ...]
输出：
  { "clues": [{"class","method","algorithm","traits","snippet"}], "summary": {...} }
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 通用算法特征：常量表 / 位运算 / 随机 / 权重 / 哈希 / 洗牌 / 决策分值
ALGO_PATTERNS = [
    (r"\b(Math\.random|getRandom|randomInt|shuffle|shuffled)\(", "random"),
    (r"\b(weight|ratio|probab)\w*", "weight/probability"),
    (r"\b(seed|hash|md5|sha|xxtea|xxhash)\w*", "hashing/seed"),
    (r"0x[0-9a-fA-F]{4,}", "hex-constant"),
    (r"\[(--|\+\+|[0-9]+(?:,\s*[0-9]+)+)\]", "numeric-table"),
    (r"<<|>>|& 0xff|\| 0x", "bitwise"),
    (r"\b(score|eval|heuristic|value)\s*[=+\-]", "scoring"),
    (r"function\s+[A-Za-z_$][\w$]*\s*\(", "function-decl"),
]

# Trait 目录常见命名模式（仅示例，项目用 --trait-patterns 覆盖）
TRAIT_PATTERNS = [
    r"\b([A-Za-z_][\w]*[Tt]rait)\b",
    r"[\"']([\w./-]+(?:trait|trait_dir|traits)[\w./-]*)[\"']",
    r"\b(dataset|catalog|configdb|resource_dir)\b",
]


def load_windows(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        items = []
        for k, v in data.items():
            if isinstance(v, list) and len(v) == 2:
                items.append((k, v[0], v[1]))
            elif isinstance(v, str):
                items.append((k, "", v))
        return items
    if isinstance(data, list):
        out = []
        for v in data:
            if isinstance(v, list) and len(v) == 2:
                out.append((str(v[0]), v[0], v[1]))
        return out
    return []


def load_windows_dir(root):
    items = []
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".js"):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                items.append((fn, fn, fh.read()))
        except OSError:
            continue
    return items


def find_methods(code):
    methods = []
    for m in re.finditer(r"(?:^|\n)\s*(?:async\s+)?(?:([A-Za-z_$][\w$]*)[.]([A-Za-z_$][\w$]*)\s*=|function\s+([A-Za-z_$][\w$]*)\s*\()", code):
        methods.append(m.group(1) or m.group(3) or "anon")
    if not methods:
        methods = ["<global>"]
    return methods


def main():
    ap = argparse.ArgumentParser(description="从代码窗口提取算法+Trait 线索")
    ap.add_argument("--code-windows", default="", help="code_windows.json")
    ap.add_argument("--window-dir", default="", help="JS 窗口目录")
    ap.add_argument("--out", default="algo_traits.json")
    ap.add_argument("--trait-patterns", default="", help="附加 trait 正则，逗号分隔")
    args = ap.parse_args()

    if args.code_windows:
        windows = load_windows(args.code_windows)
    elif args.window_dir:
        windows = load_windows_dir(args.window_dir)
    else:
        print("需要 --code-windows 或 --window-dir", file=sys.stderr)
        sys.exit(2)

    extra_trait = []
    if args.trait_patterns:
        extra_trait = [re.compile(p) for p in args.trait_patterns.split(",") if p.strip()]
    trait_res = [re.compile(p, re.I) for p in TRAIT_PATTERNS] + extra_trait
    algo_res = [(re.compile(p, re.I), label) for p, label in ALGO_PATTERNS]

    clues = []
    for key, src, code in windows:
        methods = find_methods(code)
        for meth in methods[:8]:
            mctx = code[:60000]
            algos = sorted({label for rx, label in algo_res if rx.search(mctx)})
            traits = sorted({m.group(0) for rx in trait_res for m in rx.finditer(mctx)})[:20] if trait_res else []
            if algos or traits:
                clues.append({
                    "window": key, "src": str(src)[:120], "method": meth,
                    "algorithms": algos, "traits": traits,
                    "snippet": mctx[:400].strip(),
                })

    summary = {
        "windows": len(windows),
        "clues": len(clues),
        "algo_label_counts": {},
        "trait_counts": {},
    }
    for c in clues:
        for a in c["algorithms"]:
            summary["algo_label_counts"][a] = summary["algo_label_counts"].get(a, 0) + 1
        for t in c["traits"]:
            summary["trait_counts"][t] = summary["trait_counts"].get(t, 0) + 1

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"clues": clues, "summary": summary}, fh, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
