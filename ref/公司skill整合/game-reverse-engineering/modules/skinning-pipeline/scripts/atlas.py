#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atlas record (atlas-extract) and in-place PNG atlas rebuild (atlas-rebuild)."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import (
    SCHEMA_ATLAS_INDEX, file_hash, image_info, now_iso, read_json, safe_mtime,
    safe_size, to_posix, write_json, write_utf8,
)


def _rect_hash(pil_img, rect: Dict[str, int]) -> str:
    """Hash the pixels of a rect region (for before/after crop comparison)."""
    region = pil_img.crop((rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"]))
    data = region.tobytes()
    return hashlib.blake2b(data, digest_size=16).hexdigest()


def _load_pil():
    try:
        from PIL import Image  # noqa: PLC0415
        return Image
    except ImportError:
        raise SystemExit(
            "需要 Pillow 才能执行图集像素合成。安装: pip install Pillow\n"
            "无 Pillow 的退化路径: 仅执行 备份/校验/复制，不进行像素贴回。"
        )


def run_atlas_extract(args, logger) -> int:
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        logger.error("manifest 不存在: %s" % manifest_path)
        return 3
    manifest = read_json(manifest_path)
    output_dir = Path(args.output) if args.output else manifest_path.parent / "atlas_extract"
    output_dir.mkdir(parents=True, exist_ok=True)

    sprites: List[Dict[str, Any]] = []
    for a in manifest.get("assets", []):
        if a.get("type") not in ("SpriteFrame", "Texture2D"):
            continue
        rect = a.get("atlas_rect")
        review_reasons: List[str] = []
        sm = a.get("sprite_meta") or {}
        if a.get("type") == "Texture2D" and not a.get("atlas"):
            # standalone texture, not an atlas child
            pass
        if rect is None and a.get("atlas"):
            review_reasons.append("atlas_rect 未知")
        if rect is None and not a.get("atlas"):
            # standalone single image: nothing to record beyond meta
            pass
        if sm.get("rotated"):
            review_reasons.append("rotated=true 不允许自动重建")
        if sm.get("trimmed"):
            review_reasons.append("trimmed=true 不允许自动重建")
        if sm.get("source_size") and rect and sm["source_size"] != [rect["w"], rect["h"]]:
            review_reasons.append("source_size != rect size 不允许自动重建")

        out_rel = None
        if rect is not None:
            out_rel = "sprites/%s.png" % a["id"]

        sprites.append({
            "asset_id": a["id"],
            "name": a.get("original_name"),
            "type": a.get("type"),
            "src": a.get("path"),
            "atlas": a.get("atlas"),
            "atlas_rect": rect,
            "sprite_meta": sm,
            "uuid": a.get("uuid"),
            "sub_uuid": a.get("sub_uuid"),
            "needs_manual_review": bool(review_reasons),
            "review_reason": review_reasons,
            "output": out_rel,
        })

    atlases = []
    for at in manifest.get("atlases", []):
        atlases.append({
            "name": at.get("name"),
            "file": at.get("file"),
            "sprite_count": at.get("sprite_count", 0),
            "sprites": at.get("sprites", []),
            "rects_known": at.get("rects_known", False),
            "note": at.get("note"),
        })

    index = {
        "schema_version": SCHEMA_ATLAS_INDEX,
        "manifest": to_posix(manifest_path),
        "generated_at": now_iso(),
        "sprites": sprites,
        "atlases": atlases,
        "warnings": [],
    }
    manual = [s for s in sprites if s["needs_manual_review"]]
    no_rect = [s for s in sprites if s["atlas_rect"] is None and s["atlas"]]
    if manual:
        index["warnings"].append({
            "code": "needs_manual_review",
            "message": "%d 个子图需要人工确认（rotated/trimmed/rect 缺失）" % len(manual),
            "count": len(manual),
        })
    if no_rect:
        index["warnings"].append({
            "code": "atlas_rect_missing",
            "message": "%d 个图集子图缺少 rect 信息" % len(no_rect),
            "count": len(no_rect),
        })
    out = output_dir / "index.json"
    write_json(out, index)
    logger.info("atlas index 写入: %s" % out)
    logger.info("sprites: %d, manual_review: %d, atlas: %d"
                % (len(sprites), len(manual), len(atlases)))
    for w in index["warnings"]:
        logger.warn(w["message"], code=w["code"])
    return 2 if (index["warnings"] and logger.fail_on_warning) else 0


def _find_new_asset(new_root: Path, sprite: Dict[str, Any], skin_map: Optional[Dict],
                    logger) -> Optional[Path]:
    """Locate the replacement image for a sprite using skin_map pairs first,
    then filename matching inside the new-assets root."""
    if skin_map:
        for pair in skin_map.get("pairs", []):
            if (pair.get("asset_id") == sprite["asset_id"]
                    and pair.get("status") in ("matched", "atlas-child")):
                cand = Path(pair["dst"])
                if cand.is_file():
                    return cand
    base = sprite.get("name") or Path(sprite.get("src", "")).stem
    for p in sorted(new_root.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            if p.stem.lower() == str(base).lower():
                return p
    return None


def run_atlas_rebuild(args, logger) -> int:
    Image = _load_pil()
    index_path = Path(args.index)
    if not index_path.is_file():
        logger.error("atlas index 不存在: %s" % index_path)
        return 3
    index = read_json(index_path)
    atlas_path = Path(args.atlas)
    if not atlas_path.is_file():
        logger.error("atlas PNG 不存在: %s" % atlas_path)
        return 3

    atlas_name = Path(atlas_path).stem
    atlas_low = atlas_path.name.lower()
    sprites = [s for s in index.get("sprites", [])
               if Path(str(s.get("atlas") or "")).stem == atlas_name
               or Path(str(s.get("src") or "")).stem == atlas_name
               or Path(str(s.get("atlas_png") or "")).name.lower() == atlas_low]
    if not sprites:
        logger.error("index 中没有属于图集 %s 的子图记录" % atlas_name)
        return 3

    skin_map = read_json(Path(args.skin_map)) if args.skin_map and Path(args.skin_map).is_file() else None
    new_root = Path(args.new_assets)
    if not new_root.is_dir():
        logger.error("新素材目录不存在: %s" % new_root)
        return 3

    # --- plan ---
    plan: List[Dict[str, Any]] = []
    manual: List[Dict[str, Any]] = []
    for s in sprites:
        rect = s.get("atlas_rect")
        if rect is None:
            manual.append({**s, "reason": "atlas_rect 未知"})
            continue
        if s.get("needs_manual_review") or s.get("sprite_meta", {}).get("rotated") \
                or s.get("sprite_meta", {}).get("trimmed"):
            manual.append({**s, "reason": "rotated/trimmed/元数据异常，不允许自动重建"})
            continue
        new_path = _find_new_asset(new_root, s, skin_map, logger)
        if new_path is None:
            continue  # not replaced
        info = image_info(new_path)
        if info is None:
            manual.append({**s, "reason": "新素材图片头无法解析: %s" % new_path})
            continue
        new_size = [info["width"], info["height"]]
        rect_size = [rect["w"], rect["h"]]
        resize = None
        if new_size != rect_size:
            if not args.allow_resize:
                manual.append({**s, "reason": "尺寸不一致 %s -> %s（需 --allow-resize）"
                                % (new_size, rect_size)})
                continue
            resize = rect_size
            logger.warn("子图 %s 尺寸不一致 %s -> %s，将缩放后贴回" % (s["name"], new_size, rect_size),
                        code="atlas_resize")
        plan.append({**s, "new_path": to_posix(new_path), "new_size": new_size,
                     "resize": resize})

    if args.dry_run:
        logger.info("[dry-run] 图集 %s 计划替换 %d 张子图，人工处理 %d 张"
                    % (atlas_path.name, len(plan), len(manual)))
        for p in plan:
            logger.info("  replace %s -> %s @ %s" % (p["name"], p["new_path"], p["atlas_rect"]))
        for m in manual:
            logger.warn("  人工处理: %s (%s)" % (m["name"], m["reason"]), code="manual_review")
        if plan and logger.fail_on_warning:
            return 0
        return 4 if manual and args.fail_on_manual else 0

    for m in manual:
        logger.warn("人工处理: %s (%s)" % (m["name"], m["reason"]), code="manual_review")
    if not plan:
        logger.info("没有可替换的子图，跳过重建")
        if manual and args.fail_on_manual:
            return 4
        if manual and logger.fail_on_warning:
            return 2
        return 0

    # --- backup original (PNG + meta if present) ---
    backup_dir = Path(args.backup_dir) if args.backup_dir else atlas_path.parent / "skinpipe_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_index = {"schema_version": SCHEMA_ATLAS_INDEX, "generated_at": now_iso(),
                    "entries": []}
    backup_list = [atlas_path]
    meta_path = Path(str(atlas_path) + ".meta")
    if meta_path.exists():
        backup_list.append(meta_path)
    for bf in backup_list:
        bname = "atlas_%s%s" % (atlas_path.stem, bf.suffix)
        bpath = backup_dir / bname
        shutil.copy2(bf, bpath)
        backup_index["entries"].append({
            "target": to_posix(bf), "backup": to_posix(bpath),
            "hash": file_hash(bf), "size": safe_size(bf),
            "mtime": safe_mtime(bf),
        })
    write_json(backup_dir / "backup_index.json", backup_index)

    # --- pixel compositing ---
    img = Image.open(atlas_path).convert("RGBA")
    before_crops = {}
    for p in plan:
        r = p["atlas_rect"]
        before_crops[p["asset_id"]] = _rect_hash(img, r)

    for p in plan:
        r = p["atlas_rect"]
        new_img = Image.open(p["new_path"]).convert("RGBA")
        if p.get("resize") and new_img.size != tuple(p["resize"]):
            new_img = new_img.resize(tuple(p["resize"]), Image.LANCZOS)
        region = Image.new("RGBA", (r["w"], r["h"]), (0, 0, 0, 0))
        region.paste(new_img, (0, 0))
        img.paste(region, (r["x"], r["y"]), region)

    out_path = Path(args.output) if args.output else (atlas_path if args.in_place else None)
    if out_path is None:
        logger.error("需要 --output 或 --in-place")
        return 3
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".skinpipe.tmp.png")
    img.save(tmp, format="PNG")
    img_check = image_info(tmp)
    if img_check is None:
        logger.error("重建后的 PNG header 校验失败，已保留原文件")
        tmp.unlink(missing_ok=True)
        return 1
    shutil.move(str(tmp), str(out_path))

    after_img = Image.open(out_path).convert("RGBA")
    changed, unchanged = [], []
    for p in plan:
        before = before_crops[p["asset_id"]]
        after = _rect_hash(after_img, p["atlas_rect"])
        (changed if before != after else unchanged).append(p["asset_id"])

    report = [
        "## 重建结果",
        "- 图集: `%s`" % to_posix(out_path),
        "- 替换子图: %d, 人工处理: %d" % (len(plan), len(manual)),
        "- 像素变化(rect crop hash 变化): %d" % len(changed),
        "- 未变化: %d" % len(unchanged),
        "",
        "### 已替换子图",
    ]
    for p in plan:
        report.append("- `%s` %s -> %s (before=%s)" % (p["name"], p["new_path"], p["atlas_rect"], before_crops[p["asset_id"]]))
    if manual:
        report.append("")
        report.append("### 人工处理清单")
        for m in manual:
            report.append("- `%s`: %s" % (m["name"], m["reason"]))
    report_path = out_path.with_name("atlas_rebuild_report.md")
    write_utf8(report_path, "\n".join(report))
    logger.info("图集重建完成: %s (替换 %d, 人工 %d, crop 变化 %d)"
                % (out_path, len(plan), len(manual), len(changed)))
    for m in manual:
        logger.warn("人工处理: %s (%s)" % (m["name"], m["reason"]), code="manual_review")
    rc = 0
    if manual and logger.fail_on_warning:
        rc = 2
    if args.fail_on_manual and manual:
        rc = 4
    return rc
