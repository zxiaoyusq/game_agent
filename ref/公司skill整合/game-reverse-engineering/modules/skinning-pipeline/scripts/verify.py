#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_report.md generation: post-replacement completeness / build checks."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from common import (
    COCOS_REF_EXTS, UNITY_REF_EXTS, UUID_RE, UNITY_GUID_RE, file_hash,
    now_iso, read_json, safe_mtime, to_posix, write_utf8,
)


def _resolve_uuid_assets(manifest):
    out = {}
    for a in manifest.get("assets", []):
        if a.get("uuid"):
            out[str(a["uuid"]).lower()] = a["path"]
        if a.get("sub_uuid"):
            out[str(a["sub_uuid"]).lower()] = a["path"]
    return out


def _resolve_guid_assets(manifest):
    out = {}
    for a in manifest.get("assets", []):
        if a.get("uuid"):
            out[str(a["uuid"]).lower()] = a["path"]
    return out


def run_verify(args, logger):
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        logger.error("manifest 不存在: %s" % manifest_path)
        return 3
    manifest = read_json(manifest_path)
    source_root = Path(args.source_root) if args.source_root else Path(manifest.get("source_root", "."))
    if not source_root.is_dir():
        logger.error("source_root 不存在: %s" % source_root)
        return 3
    engine = args.engine or manifest.get("engine", "unknown")

    fails = []
    warnings = []
    evidence = []

    # 1) file existence + hash integrity (plan: never trust copy alone)
    missing, hash_mismatch, unreadable = [], [], []
    total = len(manifest.get("assets", []))
    for a in manifest.get("assets", []):
        p = source_root / a["path"]
        if not p.is_file():
            missing.append(a["path"])
            continue
        try:
            if a.get("hash") and file_hash(p) != a["hash"]:
                hash_mismatch.append(a["path"])
        except OSError:
            unreadable.append(a["path"])
    if missing:
        fails.append("缺失文件 %d 个: %s" % (len(missing), "、".join(missing[:10])))
    if hash_mismatch:
        fails.append("hash 不一致 %d 个: %s" % (len(hash_mismatch), "、".join(hash_mismatch[:10])))
    if unreadable:
        warnings.append("文件不可读 %d 个" % len(unreadable))
    evidence.append("- 文件存在性: %d/%d" % (total - len(missing), total))
    evidence.append("- hash 完整性: %d/%d 一致" % (total - len(hash_mismatch) - len(missing), total))

    # 2) reference resolution
    if engine.startswith("cocos"):
        known = _resolve_uuid_assets(manifest)
        unresolved = []
        gzip_skipped = 0
        for p in source_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in COCOS_REF_EXTS:
                try:
                    head = p.read_bytes()[:2]
                    if head == b"\x1f\x8b":
                        # gzip-compressed serialized bundle files are binary;
                        # text reference scan does not apply (plan 12.5 尽力而为)
                        gzip_skipped += 1
                        continue
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = p.relative_to(source_root).as_posix()
                for u in set(m.group(0).lower() for m in UUID_RE.finditer(text)):
                    if u not in known:
                        unresolved.append("%s -> %s" % (rel, u))
        evidence.append("- 引用扫描范围: 明文 .json/.fire/.prefab/.scene/.anim")
        evidence.append("- gzip 序列化 bundle 文件跳过引用扫描: %d 个（二进制，需引擎解码）" % gzip_skipped)
        if unresolved:
            if not known:
                # No uuid/sub_uuid index at all (e.g. APK bundle 树没有 .meta)：
                # 引用解析无解析目标，属覆盖范围限制，降级为 warning（plan 12.5）
                warnings.append(
                    "未解析的 uuid 引用 %d 个（manifest 无 uuid 索引：bundle 树缺少 .meta，"
                    "引用关系为尽力而为，不宣称完整语义解析）" % len(unresolved))
                evidence.append("- 未解析引用示例: %s" % "；".join(unresolved[:5]))
            else:
                fails.append("未解析的 uuid 引用 %d 个（场景/预制体引用会断裂）" % len(unresolved))
                evidence.append("- 未解析引用示例: %s" % "；".join(unresolved[:5]))
        else:
            evidence.append("- 引用解析: 全部 uuid 可在 manifest 找到")
        lib = source_root.parent / "library" / "imports"
        if lib.is_dir():
            found = sum(1 for a in manifest.get("assets", [])
                        if a.get("uuid") and (lib / str(a["uuid"])[:2] / (str(a["uuid"]) + ".json")).is_file())
            evidence.append("- library/imports 导入证据: %d/%d 主 uuid 已导入" % (found, total))
            if found == 0:
                warnings.append("library/imports 未找到导入证据（可能从未在编辑器中打开过该项目）")
    else:
        known = _resolve_guid_assets(manifest)
        unresolved = []
        for p in source_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in UNITY_REF_EXTS:
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = p.relative_to(source_root).as_posix()
                for m in UNITY_GUID_RE.finditer(text):
                    if m.group(1).lower() not in known:
                        unresolved.append("%s -> %s" % (rel, m.group(1)))
        if unresolved:
            warnings.append("未解析的 Unity guid 引用 %d 个（尽力而为扫描）" % len(unresolved))
            evidence.append("- 未解析 guid 示例: %s" % "；".join(unresolved[:5]))
        else:
            evidence.append("- 引用解析: 全部 guid 可在 manifest 找到")

    # 3) atlas rect validity
    rect_issues = 0
    for a in manifest.get("assets", []):
        rect = a.get("atlas_rect")
        if not rect:
            continue
        if rect["w"] <= 0 or rect["h"] <= 0 or rect["x"] < 0 or rect["y"] < 0:
            rect_issues += 1
            continue
        page = a.get("atlas_page_size")
        if page:
            rotated = bool((a.get("sprite_meta") or {}).get("rotated"))
            w, h = (rect["h"], rect["w"]) if rotated else (rect["w"], rect["h"])
            if rect["x"] + w > page[0] or rect["y"] + h > page[1]:
                rect_issues += 1
        elif a.get("width") and a["width"] and (rect["x"] + rect["w"] > a["width"]
                                                or rect["y"] + rect["h"] > a["height"]):
            rect_issues += 1
    if rect_issues:
        fails.append("图集 rect 越界/非法 %d 个" % rect_issues)
    else:
        evidence.append("- 图集 rect: 无越界/非法项")

    # 4) engine build strategy note
    if engine.startswith("cocos"):
        if args.cocos_build and Path(args.cocos_build).is_file():
            evidence.append("- 构建策略: 使用调用方提供的 Cocos Creator `%s`" % args.cocos_build)
            result, msg = _run_cocos_build(args.cocos_build, source_root.parent, logger)
            evidence.append("- CLI 构建: %s" % msg)
            if not result:
                fails.append("Cocos CLI 构建失败: %s" % msg)
        else:
            evidence.append("- 构建策略: 未假定本机 Cocos Creator 路径")
            evidence.append("- CLI 构建: 未执行（未传 --cocos-build），仅做素材完整性校验")
    else:
        evidence.append("- 构建策略: Unity 导出目录，未执行 Editor 构建，仅执行素材完整性校验")
        atlases = manifest.get("atlases", [])
        if atlases:
            evidence.append("- Unity SpriteAtlas 策略:")
            for at in atlases:
                strategy = ("需要 Unity Editor 重打包" if not at.get("rects_known")
                            else "可原位替换(rect 已知)")
                evidence.append("  - `%s` -> %s (%s)" % (at.get("file"), strategy,
                                                          at.get("note") or ""))
        else:
            evidence.append("- Unity SpriteAtlas: 未检测到图集纹理")

    status = "FAIL" if fails else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    lines = [
        "# 替换后验证报告 (verify_report)",
        "",
        "> 生成时间: `%s`" % now_iso(),
        "> 输入 manifest: `%s`" % to_posix(manifest_path),
        "> source_root: `%s`" % to_posix(source_root),
        "> engine: `%s`" % engine,
        "",
        "## 结论",
        "",
        "**%s**" % status,
        "",
        "## 校验证据",
        "",
    ]
    lines += [e for e in evidence]
    lines += ["", "## 问题清单", ""]
    if fails:
        lines.append("### FAIL 项 (%d)" % len(fails))
        lines.append("")
        lines += ["- [x] %s" % f for f in fails]
        lines.append("")
    if warnings:
        lines.append("### Warning 项 (%d)" % len(warnings))
        lines.append("")
        lines += ["- [ ] %s" % w for w in warnings]
        lines.append("")
    if not fails and not warnings:
        lines.append("无")
        lines.append("")
    lines.append("## 覆盖率说明")
    lines.append("")
    lines.append("- 引用关系为尽力而为扫描（%s），不宣称完整语义解析" % ("Cocos: .fire/.prefab/.scene/.anim/.json" if engine.startswith("cocos") else "Unity: .prefab/.unity/.asset/.mat/.controller/.overrideController"))
    lines.append("- hash 校验覆盖 manifest 全部 %d 个资产" % total)
    lines.append("")

    output = Path(args.output) if args.output else manifest_path.with_name("verify_report.md")
    write_utf8(output, "\n".join(lines))
    logger.info("verify 报告写入: %s" % output)
    logger.info("结论: %s (fails=%d warnings=%d)" % (status, len(fails), len(warnings)))
    rc = 1 if fails else 0
    if warnings and logger.fail_on_warning:
        rc = 2
    return rc


def _run_cocos_build(creator_exe, project, logger):
    """Best-effort web-mobile CLI build. Returns (ok, message)."""
    cmd = [str(creator_exe), "--path", str(project), "--build", "platform=web-mobile;debug=true"]
    logger.info("执行构建: %s" % " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=1800, cwd=str(project))
        out = (proc.stdout or "") + (proc.stderr or "")
        if "Built" in out and "successfully" in out:
            return True, "Built ... successfully 已出现 (exit=%d)" % proc.returncode
        return False, "构建未成功 (exit=%d): %s" % (proc.returncode, out[-800:])
    except Exception as e:  # noqa: BLE001
        return False, "构建异常: %s" % e
