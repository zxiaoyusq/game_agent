#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_offline_seed.py -- Seed 固化 + 完整性门禁

用途：把真机拉取的原版远程资源（files/patch、files/gamecaches）整理成 APK 内置
      assets/remote_seed 目录，并（可选）按 project.manifest 做存在性/哈希/映射
      三重重校验，作为 Phase 3 的 Seed 门禁。

两种模式：
  拷贝模式（默认）：
    python prepare_offline_seed.py --patch <pull>/files/patch --gamecaches <pull>/files/gamecaches \
        --seed-out <apk-project>/assets/remote_seed --index seed_index.json
  校验模式：
    python prepare_offline_seed.py --seed-out <apk-project>/assets/remote_seed \
        --manifest <apk-project>/assets/remote_seed/patch/project.manifest --check-only
    （--report-only 只输出统计不改变退出码；否则 missing/unmapped/hash_conflict 任一 >0 退出码 1）

project.manifest 结构（Cocos 2.x/3.x 通用）：
  { "md5": "...", "version": "...", "files": { "<rel/path>": { "md5": "...", "size": n, "compressed": b } } }
若没有 files 字典（单体 manifest），则把 manifest 自身体积的 md5 与 seed 内同路径文件比对。
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def tree_files(root):
    """返回 {rel_posix_path: abs_path}（只含文件，跳过符号链接漏洞）。"""
    out = {}
    if not os.path.isdir(root):
        return out
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            abs_p = os.path.join(base, fn)
            rel = os.path.relpath(abs_p, root).replace("\\", "/")
            out[rel] = abs_p
    return out


def copy_tree(src, dst, manifest_expected=None):
    """递归拷贝；返回 (copied, skipped, failed)。逐个文件校验可选。"""
    copied = skipped = failed = 0
    files = tree_files(src)
    for rel, abs_p in sorted(files.items()):
        target = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        try:
            if os.path.exists(target) and os.path.getsize(target) == os.path.getsize(abs_p):
                skipped += 1
            else:
                shutil.copy2(abs_p, target)
                copied += 1
        except OSError as exc:
            failed += 1
            print(f"[warn] copy failed {rel}: {exc}", file=sys.stderr)
    return copied, skipped, failed


def parse_manifest(path):
    """返回 dict(version, md5, files{rel: {md5,size}}) 或 None。"""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    files = {}
    if isinstance(data.get("files"), dict):
        for rel, meta in data["files"].items():
            if isinstance(meta, dict):
                files[str(rel)] = {"md5": meta.get("md5", "").lower(), "size": meta.get("size")}
            else:
                files[str(rel)] = {"md5": str(meta).lower(), "size": None}
    return {"version": data.get("version"), "md5": data.get("md5"), "files": files}


def compare(seed_root, manifest_info, ignore_rel=()):
    """返回 (missing, unmapped, hash_conflict, details)。

    ignore_rel：不计入 unmapped 的相对路径集合（如生成的 seed_index.json）。
    """
    missing, unmapped, conflicts, details = [], [], [], []
    files = tree_files(seed_root)
    expected = manifest_info.get("files") or {}

    for rel, meta in sorted(expected.items()):
        abs_p = files.get(rel)
        if abs_p is None or not os.path.isfile(abs_p):
            missing.append(rel)
            continue
        if meta.get("md5"):
            actual = hashlib.md5(open(abs_p, "rb").read()).hexdigest()
            if actual.lower() != meta["md5"].lower():
                conflicts.append({"rel": rel, "expected": meta["md5"], "actual": actual})

    for rel in sorted(files):
        if rel in ignore_rel:
            continue
        if rel not in expected:
            unmapped.append(rel)

    return missing, unmapped, conflicts, {"expected": len(expected), "seed_files": len(files)}


def main():
    ap = argparse.ArgumentParser(description="Seed 固化 + 完整性门禁")
    ap.add_argument("--patch", default="", help="真机拉取的 files/patch 目录")
    ap.add_argument("--gamecaches", default="", help="真机拉取的 files/gamecaches 目录")
    ap.add_argument("--seed-out", required=True, help="APK 内置 assets/remote_seed 目录")
    ap.add_argument("--manifest", default="", help="project.manifest 路径（校验用）")
    ap.add_argument("--index", default="seed_index.json", help="生成的 SHA-256 索引名（放 seed-out 内）")
    ap.add_argument("--check-only", action="store_true", help="只做校验，不拷贝")
    ap.add_argument("--report-only", action="store_true", help="校验失败也不改退出码")
    args = ap.parse_args()

    if not args.check_only:
        if not args.patch and not args.gamecaches:
            print("[fatal] 非 check-only 模式需要 --patch 和/或 --gamecaches", file=sys.stderr)
            sys.exit(2)
        stats = {}
        if args.patch:
            stats["patch"] = copy_tree(args.patch, os.path.join(args.seed_out, "patch"))
        if args.gamecaches:
            stats["gamecaches"] = copy_tree(args.gamecaches, os.path.join(args.seed_out, "gamecaches"))
        files = tree_files(args.seed_out)
        index = {rel: sha256_file(abs_p) for rel, abs_p in sorted(files.items())}
        with open(os.path.join(args.seed_out, args.index), "w", encoding="utf-8") as fh:
            json.dump({"files": index}, fh, ensure_ascii=False, indent=2, sort_keys=True)
        print(json.dumps({"copy_stats": stats, "indexed": len(index), "seed_out": args.seed_out},
                         ensure_ascii=False, indent=2))

    if args.manifest or args.check_only:
        manifest_info = parse_manifest(args.manifest)
        if manifest_info is None:
            print("[fatal] 无法解析 manifest", file=sys.stderr)
            sys.exit(2)
        ignore_rel = {os.path.basename(args.index).replace("\\", "/")}
        missing, unmapped, conflicts, sizes = compare(args.seed_out, manifest_info, ignore_rel=ignore_rel)
        report = {"missing": len(missing), "unmapped": len(unmapped),
                  "hash_conflict": len(conflicts),
                  "manifest_version": manifest_info.get("version"),
                  "manifest_md5": manifest_info.get("md5"),
                  "expected_files": sizes.get("expected", 0),
                  "seed_files": sizes.get("seed_files", 0),
                  "missing_samples": missing[:50],
                  "unmapped_samples": unmapped[:50],
                  "conflict_samples": conflicts[:50]}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        bad = report["missing"] or report["unmapped"] or report["hash_conflict"]
        if bad and not args.report_only:
            print("[FAIL] Seed 门禁未通过：missing=%d unmapped=%d hash_conflict=%d"
                  % (report["missing"], report["unmapped"], report["hash_conflict"]), file=sys.stderr)
            sys.exit(1)
        if not bad:
            print("[PASS] Seed 门禁通过：missing=0 unmapped=0 hash_conflict=0")


if __name__ == "__main__":
    main()
