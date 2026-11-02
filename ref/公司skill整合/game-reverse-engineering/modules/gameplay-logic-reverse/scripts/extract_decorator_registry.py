#!/usr/bin/env python3
"""从 code_windows.json 恢复 Trait 装饰器注册表（算法方法 -> 挂载的 Trait 列表）。

用法:
  python extract_decorator_registry.py <code_windows.json> <out.json>

输入格式: { key: [[src, code], ...] }
输出格式: [[class, method, traitClassName], ...]
"""
import json
import re
import sys


def extract(code):
    """解析 类名: { 方法名: { decorators: [ { traitClassName: "X" } ] } } 片段。"""
    items = []
    # 宽松模式：捕获所有 traitClassName 前最近的 类名.方法名 上下文
    class_re = re.compile(
        r"([A-Za-z_$][\w$]*):\s*\{\s*([A-Za-z_$][\w$]*):\s*\{\s*decorators:\s*\[(.*?)\]\s*\}\s*\}",
        re.S)
    for m in class_re.finditer(code):
        cls, method = m.group(1), m.group(2)
        for t in re.findall(r'traitClassName:\s*"([^"]+)"', m.group(3)):
            items.append([cls, method, t])
    return items


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cw = json.load(open(sys.argv[1], encoding="utf-8"))
    items = []
    for key, windows in cw.items():
        for src, code in windows:
            for it in extract(code):
                if it not in items:
                    items.append(it)
    items.sort()
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print("registry pairs:", len(items))
    from collections import defaultdict
    by_cls = defaultdict(int)
    for c, _, _ in items:
        by_cls[c] += 1
    for c, n in sorted(by_cls.items(), key=lambda x: -x[1]):
        print(f"{c}: {n} hooks")


if __name__ == "__main__":
    main()
