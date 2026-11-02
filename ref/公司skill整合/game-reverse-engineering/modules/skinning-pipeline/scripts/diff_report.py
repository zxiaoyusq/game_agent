#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skin_diff.md / skin_diff.json generation from before/after manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from common import now_iso, read_json, to_posix, write_json, write_utf8


def _key(asset: Dict[str, Any]) -> str:
    return str(asset.get("id") or asset.get("path"))


def run_diff(args, logger) -> int:
    before_path, after_path = Path(args.before), Path(args.after)
    for p in (before_path, after_path):
        if not p.is_file():
            logger.error("manifest 不存在: %s" % p)
            return 3
    before = read_json(before_path)
    after = read_json(after_path)
    skin_map = read_json(Path(args.skin_map)) if args.skin_map and Path(args.skin_map).is_file() else None

    bmap = {_key(a): a for a in before.get("assets", [])}
    amap = {_key(a): a for a in after.get("assets", [])}
    pair_by_asset = {}
    if skin_map:
        for p in skin_map.get("pairs", []):
            pair_by_asset[p.get("asset_id")] = p

    replaced, added, removed, unchanged = [], [], [], []
    size_changes = []
    for kid, a in amap.items():
        b = bmap.get(kid)
        if b is None:
            added.append(a)
            continue
        if b.get("hash") != a.get("hash"):
            replaced.append((b, a))
            if (b.get("width"), b.get("height")) != (a.get("width"), a.get("height")):
                size_changes.append((b, a))
        else:
            unchanged.append(a)
    for kid, b in bmap.items():
        if kid not in amap:
            removed.append(b)

    lines: List[str] = []
    lines.append("# 换皮差异报告 (skin_diff)")
    lines.append("")
    lines.append("> 生成时间: `%s`" % now_iso())
    lines.append("> 输入: before=`%s` after=`%s`" % (to_posix(before_path), to_posix(after_path)))
    if skin_map:
        lines.append("> skin_map: `%s`" % to_posix(Path(args.skin_map)))
    lines.append("")
    lines.append("## 数字摘要")
    lines.append("")
    lines.append("| 类别 | 数量 |")
    lines.append("|---|---|")
    lines.append("| 已替换 (hash 变化) | %d |" % len(replaced))
    lines.append("| 新增 (before 中没有) | %d |" % len(added))
    lines.append("| 移除 (after 中消失) | %d |" % len(removed))
    lines.append("| 未替换 (hash 相同) | %d |" % len(unchanged))
    lines.append("| 尺寸变化 | %d |" % len(size_changes))
    lines.append("")

    if replaced:
        lines.append("## 已替换资源")
        lines.append("")
        lines.append("| 原路径 | 新素材 | 尺寸变化 | 引用者 |")
        lines.append("|---|---|---|---|")
        for b, a in sorted(replaced, key=lambda x: x[0].get("path", "")):
            pair = pair_by_asset.get(_key(a), {})
            dst = pair.get("dst", "-") if pair else "-"
            size = "%sx%s -> %sx%s" % (b.get("width"), b.get("height"),
                                       a.get("width"), a.get("height"))
            refs = ",".join(a.get("referenced_by") or []) or "-"
            lines.append("| `%s` | `%s` | %s | %s |" % (b.get("path"), dst, size, refs))
        lines.append("")
    if size_changes:
        lines.append("## 尺寸变化清单")
        lines.append("")
        for b, a in size_changes:
            lines.append("- `%s`: %sx%s -> %sx%s" % (b.get("path"), b.get("width"),
                                                      b.get("height"), a.get("width"), a.get("height")))
        lines.append("")
    if added:
        lines.append("## 新增资源")
        lines.append("")
        for a in sorted(added, key=lambda x: x.get("path", "")):
            lines.append("- `%s` (%s)" % (a.get("path"), a.get("type")))
        lines.append("")
    if removed:
        lines.append("## 移除资源")
        lines.append("")
        for b in sorted(removed, key=lambda x: x.get("path", "")):
            lines.append("- `%s` (%s)" % (b.get("path"), b.get("type")))
        lines.append("")
    if skin_map and skin_map.get("unused_new_assets"):
        lines.append("## 未进入包的新素材（防止误以为已替换）")
        lines.append("")
        for u in skin_map["unused_new_assets"]:
            lines.append("- `%s`" % u)
        lines.append("")

    output = Path(args.output) if args.output else Path(args.before).with_name("skin_diff.md")
    write_utf8(output, "\n".join(lines))
    logger.info("diff 报告写入: %s" % output)
    if args.json:
        jout = Path(args.json)
        write_json(jout, {
            "generated_at": now_iso(),
            "before": to_posix(before_path),
            "after": to_posix(after_path),
            "summary": {"replaced": len(replaced), "added": len(added),
                        "removed": len(removed), "unchanged": len(unchanged),
                        "size_changes": len(size_changes)},
            "replaced": [{"id": b.get("id"), "path": b.get("path"), "dst": pair_by_asset.get(_key(b), {}).get("dst")}
                         for b, _ in replaced],
            "added": [a.get("path") for a in added],
            "removed": [b.get("path") for b in removed],
        })
        logger.info("diff json 写入: %s" % jout)
    logger.info("摘要: replaced=%d added=%d removed=%d unchanged=%d size_changes=%d"
                % (len(replaced), len(added), len(removed), len(unchanged), len(size_changes)))
    return 0
