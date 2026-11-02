#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_manifest.json generator for Unity (AssetRipper/UnityPy) and Cocos 2.x
project directories."""

from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from common import (
    ALL_SUPPORTED_EXTS, COCOS_REF_EXTS, DEFAULT_SKIP_DIRS, IMAGE_EXTS,
    SCHEMA_MANIFEST, UNITY_REF_EXTS, UUID_RE, find_uuids, file_hash, id_from_path,
    image_info, norm_rel, now_iso, read_json, safe_mtime, safe_size, stable_sort,
    to_posix, UNITY_GUID_RE, write_json,
)


def _type_for(path: Path, engine: str, rel: str, has_meta: bool) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        if engine.startswith("cocos"):
            return "SpriteFrame" if has_meta else "Texture2D"
        if "/sprite/" in "/" + rel.lower():
            return "SpriteFrame"
        return "Texture2D"
    if ext in (".wav", ".ogg", ".mp3"):
        return "AudioClip"
    if ext in (".ttf", ".otf"):
        return "Font"
    if ext in (".fbx", ".obj"):
        return "Mesh"
    if ext == ".prefab":
        return "Prefab"
    if ext == ".unity":
        return "Scene"
    if ext in (".fire", ".scene"):
        return "Scene"
    if ext == ".asset":
        return "Asset"
    if ext == ".mat":
        return "Material"
    if ext == ".controller":
        return "AnimatorController"
    if ext == ".overridecontroller":
        return "AnimatorOverrideController"
    if ext == ".anim":
        return "AnimationClip"
    if ext == ".spriteatlas":
        return "SpriteAtlas"
    if ext == ".atlas":
        return "SpineAtlas"
    if ext == ".plist":
        return "Plist"
    if ext == ".json":
        return "Json"
    if ext == ".txt":
        return "TextAsset"
    return "Unknown"


def _parse_cocos_meta(meta_path: Path) -> Dict[str, Any]:
    """Parse a Cocos 2.x texture/font/audio meta (compatible with the
    sudux_gen_metas.py 1.1.50 format and the 2.3.7/2.4.x editor format)."""
    try:
        data = read_json(meta_path)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    submetas: Dict[str, Any] = {}
    for name, sm in (data.get("subMetas") or {}).items():
        if not isinstance(sm, dict):
            continue
        submetas[name] = {
            "uuid": sm.get("uuid"),
            "importer": sm.get("importer"),
            "raw_texture_uuid": sm.get("rawTextureUuid"),
            "width": sm.get("width"),
            "height": sm.get("height"),
            "raw_width": sm.get("rawWidth"),
            "raw_height": sm.get("rawHeight"),
            "offset_x": sm.get("offsetX"),
            "offset_y": sm.get("offsetY"),
            "trim_x": sm.get("trimX"),
            "trim_y": sm.get("trimY"),
            "rotated": sm.get("rotated", False),
            "trim_type": sm.get("trimType"),
            "trim_threshold": sm.get("trimThreshold"),
            "border_top": sm.get("borderTop"),
            "border_bottom": sm.get("borderBottom"),
            "border_left": sm.get("borderLeft"),
            "border_right": sm.get("borderRight"),
            "pivot_x": sm.get("pivotX"),
            "pivot_y": sm.get("pivotY"),
            "pixels_to_units": sm.get("pixelsToUnits"),
            "packable": sm.get("packable", True),
        }
    return {
        "ver": data.get("ver"),
        "importer": data.get("importer"),
        "uuid": data.get("uuid"),
        "wrap_mode": data.get("wrapMode"),
        "filter_mode": data.get("filterMode"),
        "premultiply_alpha": data.get("premultiplyAlpha"),
        "packable": data.get("packable"),
        "width": data.get("width"),
        "height": data.get("height"),
        "submetas": submetas,
    }


def _parse_unity_meta(meta_path: Path) -> Dict[str, Any]:
    try:
        text = meta_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = UNITY_GUID_RE.search(text)
    return {"guid": m.group(1).lower() if m else None}


def _sprite_meta_from_cocos(sm: Dict[str, Any], warn) -> Dict[str, Any]:
    """Map Cocos subMeta fields into the unified sprite_meta schema."""
    trim_x = sm.get("trim_x") or 0
    trim_y = sm.get("trim_y") or 0
    width = sm.get("width") or 0
    raw_w = sm.get("raw_width") or 0
    raw_h = sm.get("raw_height") or 0
    actually_trimmed = bool(
        trim_x != 0 or trim_y != 0
        or (raw_w and width and width != raw_w)
    )
    meta = {
        "rotated": bool(sm.get("rotated", False)),
        "trimmed": actually_trimmed,
        "source_size": [raw_w or 0, raw_h or 0],
        "offset": [sm.get("offset_x") or 0, sm.get("offset_y") or 0],
        "pivot": [sm.get("pivot_x", 0.5), sm.get("pivot_y", 0.5)],
        "border": [
            sm.get("border_left") or 0, sm.get("border_bottom") or 0,
            sm.get("border_right") or 0, sm.get("border_top") or 0,
        ],
        "pixels_per_unit": sm.get("pixels_to_units"),
        "packable": sm.get("packable"),
        "trim_type": sm.get("trim_type"),
        "trim_threshold": sm.get("trim_threshold"),
    }
    return meta


def default_sprite_meta() -> Dict[str, Any]:
    return {
        "rotated": False,
        "trimmed": False,
        "source_size": [0, 0],
        "offset": [0, 0],
        "pivot": [0.5, 0.5],
        "border": [0, 0, 0, 0],
        "pixels_per_unit": None,
        "packable": None,
        "trim_type": None,
        "trim_threshold": None,
    }


def detect_engine(input_root: Path) -> str:
    """Auto-detect cocos vs unity from directory fingerprints."""
    if (input_root / "project.json").exists() or (input_root / "assets").is_dir() and any(
        p.suffix == ".fire" for p in (input_root / "assets").glob("*.fire")
    ):
        return "cocos-2.4"
    return "unknown"


class ManifestBuilder:
    def __init__(self, logger, input_root: Path, engine: str, game: str,
                 include_dirs: Optional[List[str]] = None,
                 exclude_dirs: Optional[List[str]] = None,
                 output_path: Optional[Path] = None):
        self.log = logger
        self.input_root = input_root.resolve()
        self.engine = engine
        self.game = game
        self.include_dirs = set(include_dirs or [])
        self.exclude_dirs = set(exclude_dirs or [])
        self.output_path = output_path.resolve() if output_path else None
        self.assets: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, str]] = []
        self.referenced_by: Dict[str, List[str]] = {}
        self.meta_cache: Dict[Path, Dict[str, Any]] = {}
        self.unity_guid_map: Dict[str, str] = {}

    # ---------- walking ----------
    def _should_skip_dir(self, d: Path) -> bool:
        name = d.name
        if name in DEFAULT_SKIP_DIRS and name not in self.include_dirs:
            return True
        if name in self.exclude_dirs:
            return True
        if self.output_path:
            op = self.output_path.resolve()
            dr = d.resolve()
            # skip the directory that contains the output file (unless it is the input root)
            if dr == op or dr in op.parents:
                return True
            # when writing inside the input tree, auto-exclude pipeline artifact dirs
            # so a rescan never picks up manifests/backups/indexes as game assets
            # (plan section 11: 输出目录位于输入目录内时必须自动排除本次输出目录)
            try:
                op.relative_to(self.input_root)
                inside = True
            except ValueError:
                inside = False
            if inside and name in ("backup", "atlas_extract", "skinpipe",
                                   "skinpipe-qa", "skinpipe_backup"):
                return True
        return False

    def walk_files(self) -> List[Path]:
        files: List[Path] = []
        for root, dirs, names in os.walk(self.input_root, topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not self._should_skip_dir(Path(root) / d)]
            for n in names:
                p = Path(root) / n
                if self.output_path and p.resolve() == self.output_path.resolve():
                    continue
                if self._is_pipeline_output(p):
                    continue
                if p.suffix.lower() in ALL_SUPPORTED_EXTS:
                    files.append(p)
        return files

    def _is_pipeline_output(self, p: Path) -> bool:
        """Skip our own json/jsonl artifacts when scanning inside the input tree
        (plan section 11: rescan must never pick up pipeline products)."""
        if not self.output_path:
            return False
        try:
            self.output_path.resolve().relative_to(self.input_root)
        except ValueError:
            return False
        low = p.name.lower()
        return (low.startswith(("asset_manifest", "skin_map", "skin_diff",
                                "verify_report", "apply_report", "rollback_report",
                                "atlas_rebuild_report", "backup_index"))
                or low.endswith(".jsonl"))

    # ---------- reference scan ----------
    def scan_references(self, files: List[Path]) -> None:
        for p in files:
            ext = p.suffix.lower()
            if ext == ".meta":
                continue
            if self.engine.startswith("cocos"):
                if ext not in COCOS_REF_EXTS:
                    continue
                try:
                    head = p.read_bytes()[:2]
                    if head == b"\x1f\x8b":
                        # gzip-compressed serialized bundle files (config.*.json /
                        # import/*.json) are binary here; skip text reference scan
                        continue
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = norm_rel(p, self.input_root)
                for u in find_uuids(text):
                    self.referenced_by.setdefault(u, []).append(rel)
            else:
                if ext not in UNITY_REF_EXTS:
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = norm_rel(p, self.input_root)
                for m in UNITY_GUID_RE.finditer(text):
                    self.referenced_by.setdefault(m.group(1).lower(), []).append(rel)

    def build(self) -> Dict[str, Any]:
        files = self.walk_files()
        metas = [p for p in files if p.suffix.lower() == ".meta"]
        for mp in metas:
            if self.engine.startswith("cocos"):
                self.meta_cache[mp] = _parse_cocos_meta(mp)
            else:
                self.meta_cache[mp] = _parse_unity_meta(mp)
                g = self.meta_cache[mp].get("guid")
                if g:
                    self.unity_guid_map[g] = norm_rel(mp, self.input_root)

        self.scan_references(files)

        for p in files:
            if p.suffix.lower() == ".meta":
                continue
            try:
                entry = self.build_asset(p)
            except Exception as e:  # noqa: BLE001 - per plan 12.6 single bad file must not abort
                self.log.warn("扫描失败: %s (%s)" % (to_posix(p), e), code="scan_failed")
                self.warnings.append({"code": "scan_failed",
                                      "path": norm_rel(p, self.input_root),
                                      "message": str(e)})
                continue
            if entry:
                self.assets.append(entry)

        if self.engine.startswith("cocos"):
            self.add_spine_regions(files)
        self.assets = stable_sort(self.assets)
        atlases = self.build_atlas_entries()
        manifest = {
            "schema_version": SCHEMA_MANIFEST,
            "game": self.game,
            "engine": self.engine,
            "engine_version": self.detect_engine_version(),
            "source_root": to_posix(self.input_root),
            "generated_at": now_iso(),
            "assets": self.assets,
            "atlases": atlases,
            "warnings": self.warnings,
        }
        return manifest

    def add_spine_regions(self, files: List[Path]) -> None:
        """Expand Spine text atlases (.atlas) into per-region SpriteFrame
        records with rect + rotated/trimmed metadata (plan 12.1)."""
        atlas_files = [p for p in files if p.suffix.lower() == ".atlas"]
        for ap in atlas_files:
            rel = norm_rel(ap, self.input_root)
            try:
                raw = ap.read_bytes()
                if raw[:2] == b"\x1f\x8b":
                    import gzip
                    raw = gzip.decompress(raw)
                text = raw.decode("utf-8", errors="replace")
            except OSError:
                continue
            pages = parse_spine_atlas(text)
            if not pages:
                continue
            base_id = id_from_path(rel)
            for pg in pages:
                for rg in pg.get("regions", []):
                    if "xy" not in rg or "size" not in rg:
                        continue
                    x, y = rg["xy"]
                    w, h = rg["size"]
                    orig = rg.get("orig") or rg["size"]
                    offset = rg.get("offset") or [0, 0]
                    rotated = rg.get("rotate") in (True, "true")
                    trimmed = bool(rotated
                                   or orig != rg["size"]
                                   or offset != [0, 0])
                    entry = {
                        "id": "%s#%s" % (base_id, rg.get("name", "region")),
                        "type": "SpriteFrame",
                        "path": rel,
                        "original_name": rg.get("name"),
                        "width": w,
                        "height": h,
                        "atlas_page_size": list(pg["size"]) if pg.get("size") else None,
                        "atlas": rel,
                        "atlas_rect": {"x": x, "y": y, "w": w, "h": h},
                        "sprite_meta": {
                            "rotated": bool(rotated),
                            "trimmed": trimmed,
                            "source_size": list(orig),
                            "offset": list(offset),
                            "pivot": [0.5, 0.5],
                            "border": [0, 0, 0, 0],
                            "pixels_per_unit": None,
                        },
                        "hash": file_hash(ap),
                        "hash_algorithm": "blake2b-128",
                        "byte_size": safe_size(ap),
                        "referenced_by": [],
                        "format": "atlas-region",
                        "meta_path": None,
                        "uuid": None,
                        "sub_uuid": None,
                        "spine_region": True,
                    }
                    self.assets.append(entry)

    def detect_engine_version(self) -> Optional[str]:
        try:
            v = Path(self.input_root, "project.json")
            if v.exists():
                data = read_json(v)
                return str(data.get("version") or data.get("engineVersion") or "")
        except Exception:
            pass
        return None

    # ---------- per-asset ----------
    def build_asset(self, path: Path) -> Optional[Dict[str, Any]]:
        rel = norm_rel(path, self.input_root)
        ext = path.suffix.lower()
        meta_path = Path(str(path) + ".meta")
        meta = self.meta_cache.get(meta_path) if meta_path.exists() else {}
        has_meta = bool(meta)
        info = image_info(path) if ext in IMAGE_EXTS else None
        if ext in IMAGE_EXTS and info is None:
            self.log.warn("图片头无法解析: %s" % rel, code="unreadable_image")
            self.warnings.append({"code": "unreadable_image", "path": rel,
                                  "message": "PNG/JPEG/WebP header 解析失败"})
        h = None
        try:
            h = file_hash(path)
        except OSError as e:
            self.log.warn("文件不可读: %s (%s)" % (rel, e), code="unreadable_file")
            self.warnings.append({"code": "unreadable_file", "path": rel, "message": str(e)})

        type_name = _type_for(path, self.engine, rel, has_meta)
        uuid = None
        sub_uuid = None
        sprite_meta = default_sprite_meta()
        atlas = None

        if self.engine.startswith("cocos") and meta:
            uuid = meta.get("uuid")
            sms = meta.get("submetas") or {}
            if sms:
                # prefer the subMeta whose key matches the file base name
                base = path.stem
                chosen = sms.get(base) or next(iter(sms.values()))
                if chosen:
                    sub_uuid = chosen.get("uuid")
                    type_name = "SpriteFrame"
                    if sub_uuid and uuid is None:
                        uuid = chosen.get("raw_texture_uuid") or meta.get("uuid")
                    sprite_meta = _sprite_meta_from_cocos(chosen, self.log)
                    if chosen.get("raw_texture_uuid"):
                        uuid = chosen["raw_texture_uuid"]
            else:
                importer = (meta.get("importer") or "").lower()
                if importer in ("font", "audio-clip"):
                    type_name = "Font" if importer == "font" else "AudioClip"
        elif self.engine.startswith("unity") and meta:
            uuid = meta.get("guid")

        if sub_uuid:
            asset_id = sub_uuid
        elif uuid:
            asset_id = uuid
        else:
            asset_id = id_from_path(rel)

        refs = self.referenced_by.get(str(sub_uuid or uuid or ""), [])
        if not refs and uuid:
            refs = self.referenced_by.get(str(uuid), [])

        if self.engine.startswith("unity"):
            refs = []
            g = (meta or {}).get("guid")
            if g:
                refs = self.referenced_by.get(g, [])
            # also reverse-map: files that reference this asset's guid

        if info is not None and type_name in ("SpriteFrame", "Texture2D"):
            if sprite_meta["source_size"] == [0, 0] or not sprite_meta["source_size"]:
                sprite_meta["source_size"] = [info["width"], info["height"]]

        return {
            "id": asset_id,
            "type": type_name,
            "path": rel,
            "original_name": path.stem,
            "width": info["width"] if info else None,
            "height": info["height"] if info else None,
            "atlas": atlas,
            "atlas_rect": None,
            "sprite_meta": sprite_meta if type_name in ("SpriteFrame", "Texture2D") else None,
            "hash": h,
            "hash_algorithm": "blake2b-128",
            "byte_size": safe_size(path),
            "referenced_by": refs,
            "format": ext.lstrip("."),
            "meta_path": rel + ".meta" if has_meta else None,
            "uuid": uuid,
            "sub_uuid": sub_uuid,
        }

    def build_atlas_entries(self) -> List[Dict[str, Any]]:
        """Collect atlas textures (named *atlas* or .spriteatlas) into the
        atlases array. Sprite membership is only known when rect data exists."""
        atlas_assets = [a for a in self.assets
                        if a["type"] == "SpriteAtlas"
                        or a["type"] == "SpineAtlas"
                        or (a["type"] in ("Texture2D", "SpriteFrame")
                            and _looks_like_atlas(a["path"]))]
        out = []
        for a in sorted(atlas_assets, key=lambda x: x["path"]):
            is_spine = a["type"] == "SpineAtlas"
            sprites = [s["id"] for s in self.assets
                       if s.get("spine_region") and s.get("atlas") == a["path"]]
            out.append({
                "name": a["original_name"],
                "file": a["path"],
                "sprite_count": len(sprites) if is_spine else 0,
                "sprites": sprites if is_spine else [],
                "rects_known": is_spine,
                "note": (("Spine 文本图集，rect 已知" if is_spine else
                          "AssetRipper 未导出 SpriteAtlas 子图 rect 元数据；"
                          "需要 Unity Editor 重打包或人工提供 rect 表")
                         if (is_spine or self.engine.startswith("unity"))
                         else "图集 rect 未知，需人工确认"),
            })
        return out


def _looks_like_atlas(path: str) -> bool:
    """Detect sprite-atlas textures (e.g. 'Ui-Elements-Sprite-Atlas-RGBA')
    without matching unrelated names like 'SDF Atlas' font textures."""
    low = path.lower()
    if re.search(r"sprite[-_ ]?atlas", low):
        return True
    if re.search(r"[-_ ]atlas[-_ ]", low) and "texture" not in low:
        return True
    return False


def parse_spine_atlas(text: str):
    """Parse Spine text atlas -> [{'page': name, 'size': [w,h],
        'regions': [{'name','rotate','xy','size','orig','offset','index'}]}]"""
    pages = []
    cur = None
    region = None
    for line in text.splitlines():
        if not line.strip():
            continue
        indented = line[:1] in (" ", "\t")
        stripped = line.strip()
        if indented:
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip()
            if region is not None:
                if key in ("rotate", "index"):
                    region[key] = {"true": True, "false": False}.get(val, val)
                elif key in ("xy", "size", "orig", "offset"):
                    region[key] = [int(x) for x in val.split(",")]
                else:
                    region[key] = val
            elif cur is not None and key == "size":
                cur["size"] = [int(x) for x in val.split(",")]
            continue
        # non-indented line
        if stripped.startswith(("size:", "format:", "filter:",
                                "repeat:", "pma:", "scale:")):
            if cur is not None and stripped.startswith("size:"):
                cur["size"] = [int(x) for x in stripped.split(":")[1].split(",")]
            continue
        if re.search(r"\.(png|jpg|jpeg|webp)$", stripped, re.I):
            cur = {"page": stripped, "size": None, "regions": []}
            region = None
            pages.append(cur)
            continue
        if cur is None:
            cur = {"page": None, "size": None, "regions": []}
            pages.append(cur)
        # region block starts
        region = {"name": stripped}
        cur["regions"].append(region)
    return pages


def run_manifest(args, logger) -> int:
    input_root = Path(args.input)
    if not input_root.is_dir():
        logger.error("输入目录不存在: %s" % input_root)
        return 3
    engine = args.engine or detect_engine(input_root)
    if engine == "unknown":
        logger.error("无法自动识别引擎，请显式传 --engine unity-il2cpp|cocos-2.4")
        return 3
    output = Path(args.output) if args.output else input_root / "skinpipe" / "asset_manifest.json"
    builder = ManifestBuilder(
        logger, input_root, engine, args.game or input_root.name,
        include_dirs=args.include_dir or [], exclude_dirs=args.exclude_dir or [],
        output_path=output,
    )
    manifest = builder.build()
    write_json(output, manifest)
    logger.info("manifest 写入: %s" % output)
    logger.info("资产总数: %d, warning: %d" % (len(manifest["assets"]), len(manifest["warnings"])))
    for code, count in _count_by(manifest["assets"], "type").items():
        logger.info("  %s: %d" % (code, count))
    return _exit_code(logger, manifest["warnings"])


def _count_by(items, key):
    from collections import Counter
    return Counter(str(i.get(key)) for i in items)


def _exit_code(logger, warnings) -> int:
    if warnings and logger.fail_on_warning:
        return 2
    return 0
