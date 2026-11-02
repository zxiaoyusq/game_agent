#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skin_map.json generation: match user-provided new art against a manifest."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import (
    SCHEMA_SKIN_MAP, image_info, norm_key, norm_name, now_iso, read_json,
    relpath_safe, to_posix, write_json,
)


def _candidate_assets(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [a for a in manifest.get("assets", [])
            if a.get("path") and a.get("type") not in ("Scene", "Prefab", "Asset", "Material",
                                                        "AnimatorController", "AnimatorOverrideController",
                                                        "AnimationClip", "Json", "Plist", "TextAsset")]


def _new_files(root: Path) -> List[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() == ".meta":
            continue
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp",
                                ".wav", ".ogg", ".mp3", ".ttf", ".otf", ".fbx", ".obj"):
            out.append(p)
    return out


def _match_rules(asset: Dict[str, Any]) -> Dict[str, str]:
    rel = norm_key(asset.get("path", ""))
    name = Path(rel).name
    stem = Path(rel).stem
    return {
        "full_name": name,
        "stem": stem,
        "normalized": norm_name(stem),
        "rel_path": rel,
        "rel_stem": norm_key(rel)[:-len(Path(rel).suffix)] if Path(rel).suffix else rel,
    }


def run_map(args, logger) -> int:
    manifest_path = Path(args.manifest)
    new_root = Path(args.new_assets)
    if not manifest_path.is_file():
        logger.error("manifest 不存在: %s" % manifest_path)
        return 3
    if not new_root.is_dir():
        logger.error("新素材目录不存在: %s" % new_root)
        return 3
    manifest = read_json(manifest_path)
    assets = _candidate_assets(manifest)
    aliases: Dict[str, str] = {}
    if args.aliases and Path(args.aliases).is_file():
        aliases = read_json(Path(args.aliases)) or {}

    # index by rule value (case-insensitive for Windows)
    by_rule: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "full_name": defaultdict(list), "stem": defaultdict(list),
        "normalized": defaultdict(list), "rel_path": defaultdict(list),
        "rel_stem": defaultdict(list),
    }
    for a in assets:
        for rule, val in _match_rules(a).items():
            by_rule[rule][norm_key(val)].append(a)

    alias_map: Dict[str, Dict[str, Any]] = {}
    for k, v in aliases.items():
        # key can be asset id, rel path, or original name; value = new file name/rel path
        for a in assets:
            if (a.get("id") == k or norm_key(a.get("path", "")) == norm_key(k)
                    or a.get("original_name") == k):
                alias_map[a["id"]] = v
                break

    pairs: List[Dict[str, Any]] = []
    used_new: set = set()
    unused: List[str] = []
    ambiguous: List[Dict[str, Any]] = []

    new_files = _new_files(new_root)
    for nf in new_files:
        nf_rel = relpath_safe(nf, new_root)
        nf_name = nf.name
        nf_stem = nf.stem
        nf_norm = norm_name(nf_stem)
        match: Optional[Dict[str, Any]] = None
        rule_used = None
        nf_ambiguous = False
        # 1) explicit alias: value matches this file name/rel path
        for aid, alias_val in alias_map.items():
            if norm_key(alias_val) in (norm_key(nf_name), norm_key(nf_rel), norm_key(nf_stem)):
                asset = next((a for a in assets if a["id"] == aid), None)
                if asset:
                    match, rule_used = asset, "alias"
                break
        # 2) exact filename
        if match is None:
            cands = by_rule["full_name"][norm_key(nf_name)]
            if len(cands) == 1:
                match, rule_used = cands[0], "exact-name"
            elif len(cands) > 1:
                nf_ambiguous = True
                ambiguous.append({"new": nf_rel, "rule": "exact-name",
                                  "matches": [a["path"] for a in cands]})
        # 3) stem
        if match is None:
            cands = by_rule["stem"][norm_key(nf_stem)]
            if len(cands) == 1:
                match, rule_used = cands[0], "stem"
            elif len(cands) > 1:
                nf_ambiguous = True
                ambiguous.append({"new": nf_rel, "rule": "stem",
                                  "matches": [a["path"] for a in cands]})
        # 4) normalized name
        if match is None:
            cands = by_rule["normalized"][norm_key(nf_norm)]
            if len(cands) == 1:
                match, rule_used = cands[0], "normalized-name"
            elif len(cands) > 1:
                nf_ambiguous = True
                ambiguous.append({"new": nf_rel, "rule": "normalized-name",
                                  "matches": [a["path"] for a in cands]})
        # 5) rel path
        if match is None:
            cands = by_rule["rel_path"][norm_key(nf_rel)]
            if len(cands) == 1:
                match, rule_used = cands[0], "rel-path"
        if match is None:
            cands = by_rule["rel_stem"][norm_key(nf_rel)]
            if len(cands) == 1:
                match, rule_used = cands[0], "rel-stem"

        if match is None and not nf_ambiguous:
            unused.append(nf_rel)
            continue
        if match is None:
            continue
        used_new.add(nf_rel)

        status = "matched"
        warnings: List[str] = []
        if match.get("atlas"):
            status = "atlas-child"
            warnings.append("图集子图 %s 不能直接覆盖，需走 atlas-rebuild 流程" % match["path"])
        old_size = [match.get("width"), match.get("height")]
        new_size = None
        if match.get("format") in ("png", "jpg", "jpeg", "webp"):
            info = image_info(nf)
            if info:
                new_size = [info["width"], info["height"]]
                if old_size and old_size[0] is not None and old_size != new_size:
                    warnings.append("尺寸不一致 %s -> %s" % (old_size, new_size))
        if (match.get("format") and match.get("format") != "atlas-region"
                and nf.suffix.lstrip(".").lower() != match["format"].lower()):
            warnings.append("跨格式替换 %s -> %s（默认不执行，需显式确认）"
                            % (match["format"], nf.suffix.lstrip(".").lower()))
            if not args.allow_format_change:
                status = "format-mismatch"
        pairs.append({
            "asset_id": match["id"],
            "src": match["path"],
            "dst": to_posix(nf),
            "status": status,
            "match_rule": rule_used,
            "old_size": old_size,
            "new_size": new_size,
            "warnings": warnings,
        })

    # post-pass: multiple new files matched to the same asset -> ambiguous
    by_asset: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        by_asset[p["asset_id"]].append(p)
    demoted = []
    for aid, plist in by_asset.items():
        if len(plist) > 1:
            for p in plist[1:]:
                p["status"] = "ambiguous"
                p["warnings"].append("同一资源有多个新素材候选，需 aliases 或人工确认")
                demoted.append({"new": p["dst"], "rule": p["match_rule"],
                                "matches": [p["src"]]})
    if demoted:
        ambiguous.extend(demoted)
    pairs = [p for p in pairs if p["status"] != "ambiguous"]
    unmatched = [a["path"] for a in assets
                 if not any(p["asset_id"] == a["id"] for p in pairs)]
    skin_map = {
        "schema_version": SCHEMA_SKIN_MAP,
        "manifest": to_posix(manifest_path),
        "source_root": manifest.get("source_root"),
        "new_assets_root": to_posix(new_root),
        "generated_at": now_iso(),
        "pairs": sorted(pairs, key=lambda p: (p["src"], p["dst"])),
        "unmatched_source_assets": sorted(unmatched),
        "unused_new_assets": sorted(set(unused)),
        "ambiguous": sorted(ambiguous, key=lambda x: x["new"]),
        "warnings": [],
    }
    if ambiguous:
        skin_map["warnings"].append({
            "code": "ambiguous",
            "message": "%d 个新素材匹配到多个原资源，需要 aliases 或人工确认" % len(ambiguous),
            "items": ambiguous,
        })
    status_counts: Dict[str, int] = defaultdict(int)
    for p in pairs:
        status_counts[p["status"]] += 1
        for w in p.get("warnings", []):
            logger.warn("pair %s: %s" % (p["src"], w), code="pair_warning")
    if unused:
        logger.warn("%d 个新素材未匹配到任何资源" % len(unused), code="unused_new_assets")
    if skin_map["warnings"]:
        for w in skin_map["warnings"]:
            logger.warn(w["message"], code=w["code"])

    output = Path(args.output) if args.output else manifest_path.parent / "skin_map.json"
    write_json(output, skin_map)
    logger.info("skin_map 写入: %s" % output)
    logger.info("匹配统计: %s" % dict(status_counts))
    logger.info("unmatched_source: %d, unused_new: %d, ambiguous: %d"
                % (len(unmatched), len(unused), len(ambiguous)))
    rc = 0
    if logger.fail_on_warning and (skin_map["warnings"] or unused or ambiguous):
        rc = 2
    if ambiguous and args.fail_on_ambiguous:
        rc = 4
    return rc
