#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe replacement executor: dry-run plan, backup, atomic execute, rollback."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from common import (
    file_hash, image_info, now_iso, read_json, safe_mtime, safe_size, to_posix,
    write_json, write_utf8,
)


def _load_skin_map(path: Path, logger) -> Dict[str, Any]:
    if not path.is_file():
        logger.error("skin_map 不存在: %s" % path)
        raise SystemExit(3)
    return read_json(path)


def _eligible_pairs(skin_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [p for p in skin_map.get("pairs", [])
            if p.get("status") in ("matched",) and p.get("src") and p.get("dst")]


def _resolve_target(path_str: str, root) -> Path:
    p = Path(path_str)
    if p.is_absolute() or root is None:
        return p
    return root / p


def _plan_ops(pairs: List[Dict[str, Any]], logger, root=None) -> List[Dict[str, Any]]:
    ops = []
    for p in pairs:
        src = _resolve_target(p["src"], root)
        dst = Path(p["dst"])
        if not src.is_file():
            logger.warn("目标不存在，跳过: %s" % src, code="missing_target")
            continue
        if not dst.is_file():
            logger.warn("新素材不存在，跳过: %s" % dst, code="missing_new_asset")
            continue
        ops.append({
            "asset_id": p["asset_id"],
            "src": to_posix(src),
            "dst": to_posix(dst),
            "old_size": p.get("old_size"),
            "new_size": p.get("new_size"),
            "warnings": p.get("warnings", []),
        })
    return ops


def _backup_one(src: Path, backup_dir: Path, entry_id: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    bpath = backup_dir / ("%s_%s%s" % (entry_id, safe_size(src) or 0, src.suffix))
    n = 1
    while bpath.exists():
        bpath = backup_dir / ("%s_%s_%d%s" % (entry_id, safe_size(src) or 0, n, src.suffix))
        n += 1
    shutil.copy2(src, bpath)
    return bpath


def run_apply(args, logger) -> int:
    skin_map = _load_skin_map(Path(args.skin_map), logger)
    root = None
    if args.root:
        root = Path(args.root)
    elif skin_map.get("source_root"):
        root = Path(skin_map["source_root"])
    ops = _plan_ops(_eligible_pairs(skin_map), logger, root=root)
    backup_dir = Path(args.backup_dir) if args.backup_dir else Path(args.skin_map).parent / "backup"
    backup_index_path = backup_dir / "backup_index.json"

    if args.dry_run:
        logger.info("[dry-run] 计划替换 %d 个资源（不会写入任何文件）" % len(ops))
        for op in ops:
            logger.info("  replace: %s <- %s" % (op["src"], op["dst"]))
            for w in op["warnings"]:
                logger.warn("    %s" % w, code="pair_warning")
        if not ops and logger.fail_on_warning:
            return 2
        return 0

    backup_index_path = backup_dir / "backup_index.json"
    backup_index = {"schema_version": "1.0", "generated_at": now_iso(),
                    "skin_map": to_posix(Path(args.skin_map)), "entries": []}
    if backup_index_path.is_file():
        old = read_json(backup_index_path)
        if isinstance(old, dict) and isinstance(old.get("entries"), list):
            backup_index["entries"] = old["entries"]
            backup_index["previous_generated_at"] = old.get("generated_at")
    backed_up_targets = {e.get("target") for e in backup_index["entries"]}
    results: List[Dict[str, Any]] = []
    failed = 0
    for op in ops:
        src = Path(op["src"])
        dst = Path(op["dst"])
        try:
            src_posix = to_posix(src)
            if src_posix in backed_up_targets:
                logger.info("skip backup (already indexed): %s" % src)
                bpath = next(e["backup"] for e in backup_index["entries"]
                             if e.get("target") == src_posix)
            else:
                bpath = _backup_one(src, backup_dir, op["asset_id"][:24])
                backup_index["entries"].append({
                    "asset_id": op["asset_id"],
                    "target": src_posix,
                    "backup": to_posix(bpath),
                    "hash": file_hash(src),
                    "hash_algorithm": "blake2b-128",
                    "size": safe_size(src),
                    "mtime": safe_mtime(src),
                })
                backed_up_targets.add(src_posix)
            # atomic-ish write: temp file in target dir -> verify -> replace
            tmp = src.with_name(src.name + ".skinpipe.tmp" + src.suffix)
            shutil.copy2(dst, tmp)
            if src.suffix.lower() == ".png":
                info = image_info(tmp)
                if info is None:
                    raise RuntimeError("替换后 PNG header 校验失败")
            os.replace(tmp, src)
            results.append({**op, "status": "ok", "backup": to_posix(Path(bpath))})
            logger.info("replaced: %s <- %s (backup %s)" % (op["src"], op["dst"], bpath))
        except Exception as e:  # noqa: BLE001
            failed += 1
            tmp = src.with_name(src.name + ".skinpipe.tmp" + src.suffix)
            tmp.unlink(missing_ok=True)
            results.append({**op, "status": "failed", "error": str(e)})
            logger.error("替换失败（原文件已保留）: %s (%s)" % (op["src"], e))

    write_json(backup_index_path, backup_index)
    report = [
        "## 替换执行报告",
        "- 计划: %d, 成功: %d, 失败: %d" % (len(ops), len(results) - failed, failed),
        "- backup index: `%s`" % to_posix(backup_index_path),
        "- 回滚命令: `python scripts\\skinpipe.py rollback --backup-dir \"%s\"`" % backup_dir,
        "",
        "| 资源 | 新素材 | 状态 |",
        "|---|---|---|",
    ]
    for r in results:
        report.append("| `%s` | `%s` | %s |" % (r["src"], r["dst"], r["status"]))
    write_utf8(Path(args.skin_map).with_name("apply_report.md"), "\n".join(report))
    return 1 if failed else 0


def run_rollback(args, logger) -> int:
    backup_dir = Path(args.backup_dir)
    index_path = backup_dir / "backup_index.json"
    if not index_path.is_file():
        logger.error("backup index 不存在: %s" % index_path)
        return 3
    index = read_json(index_path)
    entries = index.get("entries", [])
    if not entries:
        logger.error("backup index 为空，无内容可回滚")
        return 3
    if args.dry_run:
        logger.info("[dry-run] 计划回滚 %d 个文件" % len(entries))
        for e in entries:
            logger.info("  restore: %s <- %s" % (e["target"], e["backup"]))
        return 0

    failed = 0
    results = []
    for e in entries:
        target = Path(e["target"])
        backup = Path(e["backup"])
        try:
            if not backup.is_file():
                raise RuntimeError("备份文件缺失: %s" % backup)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".rollback.tmp" + target.suffix)
            shutil.copy2(backup, tmp)
            if target.suffix.lower() == ".png" and image_info(tmp) is None:
                raise RuntimeError("恢复后 PNG header 校验失败")
            if file_hash(tmp) != e.get("hash"):
                raise RuntimeError("恢复文件 hash 与备份记录不一致")
            os.replace(tmp, target)
            results.append({"target": e["target"], "status": "ok"})
            logger.info("restored: %s" % e["target"])
        except Exception as err:  # noqa: BLE001
            failed += 1
            results.append({"target": e["target"], "status": "failed", "error": str(err)})
            logger.error("回滚失败: %s (%s)" % (e["target"], err))
    write_utf8(backup_dir / "rollback_report.md",
               "\n".join([
                   "## 回滚报告",
                   "- 总数: %d, 成功: %d, 失败: %d" % (len(entries), len(entries) - failed, failed),
                   "",
                   "| 目标 | 状态 |",
                   "|---|---|",
               ] + ["| `%s` | %s |" % (r["target"], r["status"]) for r in results]))
    return 1 if failed else 0
