#!/usr/bin/env python3
"""从堆转储中提取长可打印字符串（V8/SpiderMonkey JS 源码串），切窗产出代码窗口。

用法:
  python extract_js_from_heap.py <heap_dir> <out_dir> [min_run=80]

产出:
  <out_dir>/run_<idx>_<len>.js   每个源码窗口一个文件
  <out_dir>/_runs.json          元信息（src/offset/len）
  <out_dir>/_code_windows.json  按标记聚合的关键类/函数窗口（供后续枚举/装饰器恢复）
"""
import glob
import json
import os
import re
import sys

GOOD = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D, 0x00A0, 0x2028, 0x2029}
MARKS = [b"window.__require", b"cc._RF", b"use strict", b"classId(", b"TRAIT("]


def extract_runs(raw, min_run):
    runs = []
    n = len(raw) // 2
    cur = None
    buf = []
    for i in range(n):
        u = raw[i * 2] | (raw[i * 2 + 1] << 8)
        if u in GOOD:
            if cur is None:
                cur = i * 2
            buf.append(chr(u))
        else:
            if cur is not None and len(buf) >= min_run:
                runs.append((cur, "".join(buf)))
            cur = None
            buf = []
    if cur is not None and len(buf) >= min_run:
        runs.append((cur, "".join(buf)))
    return runs


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    min_run = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    os.makedirs(dst, exist_ok=True)

    all_runs = []
    for path in sorted(glob.glob(os.path.join(src, "*.bin"))):
        raw = open(path, "rb").read()
        for off, txt in extract_runs(raw, min_run):
            all_runs.append((os.path.basename(path), off, txt))
    all_runs.sort(key=lambda x: -len(x[2]))
    print("total runs:", len(all_runs))

    meta = []
    for idx, (fn, off, txt) in enumerate(all_runs):
        name = f"run_{idx:05d}_{len(txt):d}.js"
        with open(os.path.join(dst, name), "w", encoding="utf-8", errors="replace") as f:
            f.write(txt)
        meta.append({"file": name, "src": fn, "offset": off, "len": len(txt)})
    with open(os.path.join(dst, "_runs.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    # 聚合代码窗口：按 标记/常见类名 归组
    windows = {}
    key_re = re.compile(
        r"(Algo[A-Za-z0-9_]+|BinarySupport|AlgorithmStrategyLogic|canPutBlock|findPileUpPos|"
        r"applyReplaceAlgorithmV3|EntropyIncreaseBeforeFill|RandomNoDeath|UCBBlockPoolStrategy|"
        r"LightGBMAlgorithmStrategy|[A-Za-z0-9_]+Trait)")
    for idx, (fn, off, txt) in enumerate(all_runs):
        keys = set(key_re.findall(txt))
        for k in keys:
            windows.setdefault(k, []).append([f"run_{idx:05d}_{len(txt):d}.js", txt])
    with open(os.path.join(dst, "_code_windows.json"), "w", encoding="utf-8") as f:
        json.dump(windows, f, ensure_ascii=False)
    print("code windows:", len(windows))


if __name__ == "__main__":
    main()
