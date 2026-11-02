#!/usr/bin/env python3
"""Repair mangled json assets in a reconstructed Cocos project.

cc-reverse may merge multiple same-path assets (SkeletonData / DragonBones
asset + atlas native cc.Asset + SpriteFrame) into one corrupt json
(json.loads fails with 'Extra data'). This script finds such files, resolves
their uuid from the sidecar .meta, locates the intact asset in the decrypted
import tree (by uuid, falling back to same-bundle name match), and rewrites
the project json in the standard dict format.

Usage:
  python restore_skeleton_data.py --project <project> --decrypted <decrypted>
      [--dry-run]
"""
import argparse
import json
import pathlib
import sys

ASSET_TYPES = ("sp.SkeletonData", "dragonBones.DragonBonesAsset",
               "dragonBones.DragonBonesAtlasAsset")


def decode_serialized(arr):
    classes = arr[3] if len(arr) > 3 else []
    data = arr[5] if len(arr) > 5 else []
    for cls in classes:
        if not isinstance(cls, list) or not cls:
            continue
        typ, fields = cls[0], cls[1]
        if typ in ASSET_TYPES and data:
            rec = dict(zip(fields, data[0][1:]))
            for key in ("_skeletonJson", "_dragonBonesJson", "_atlasJson"):
                if isinstance(rec.get(key), str):
                    rec[key] = json.loads(rec[key])
            rec["__type__"] = typ
            return rec
    for cls in classes:
        if isinstance(cls, list) and cls and cls[0] in ("cc.SpriteFrame",
                                                        "cc.Asset"):
            rec = {"__type__": cls[0]}
            if data and len(cls) > 1 and isinstance(cls[1], list):
                rec.update(dict(zip(cls[1], data[0][1:])))
            return rec
    return None


def find_asset_by_uuid(dec, uuid):
    raise NotImplementedError("use build_index instead")


def bundle_of(proj, js):
    rel = js.relative_to(proj).parts
    # project layout: assets/<bundle>/... -> bundle = parts[1]
    return rel[1] if len(rel) > 1 else None


def build_index(dec):
    """Return (by_uuid, by_bundle_name).

    by_uuid: uuid -> decoded asset dict (ASSET_TYPES or SpriteFrame/Asset).
    by_bundle_name: (bundle, name) -> (asset, uuid) for ASSET_TYPES assets.
    """
    by_uuid = {}
    by_bundle_name = {}
    import_root = dec / "assets" / "assets"
    for h in import_root.rglob("import/**/*.json"):
        rel = h.relative_to(import_root).parts
        bundle = rel[0] if rel else None
        uuid = h.name.split(".")[0]
        try:
            asset = decode_serialized(json.loads(h.read_text(encoding="utf-8")))
        except Exception:
            continue
        if asset is None:
            continue
        by_uuid[uuid] = asset
        if asset.get("__type__") in ASSET_TYPES and asset.get("_name"):
            key = (bundle, asset["_name"])
            by_bundle_name.setdefault(key, (asset, uuid))
    return by_uuid, by_bundle_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--decrypted", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    dec = pathlib.Path(a.decrypted)
    by_uuid, by_bundle_name = build_index(dec)
    fixed, skipped = [], []
    for js in proj.rglob("*.json"):
        meta = js.with_suffix(".json.meta")
        if not meta.exists():
            continue
        try:
            json.loads(js.read_text(encoding="utf-8"))
            # File is already valid json (SpriteFrame / SkeletonData / cc.Asset):
            # never rewrite it, even if a same-name asset of another type exists.
            # Rewriting here corrupted valid files in past runs.
            skipped.append((str(js), "already valid json"))
            continue
        except Exception:
            pass
        try:
            uuid = json.loads(meta.read_text(encoding="utf-8"))["uuid"]
        except Exception:
            skipped.append((str(js), "no uuid in meta"))
            continue
        asset = by_uuid.get(uuid)
        new_uuid = None
        if asset and asset.get("__type__") not in ASSET_TYPES:
            stem = js.stem.replace(".json", "")
            alt = by_bundle_name.get((bundle_of(proj, js), stem))
            if alt:
                asset, new_uuid = alt
        if not asset:
            skipped.append((str(js), "no intact asset in decrypted"))
            continue
        payload = [dict(asset)]
        if not a.dry_run:
            js.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                          encoding="utf-8")
            if new_uuid:
                m = json.loads(meta.read_text(encoding="utf-8"))
                m["uuid"] = new_uuid
                m["importer"] = "spine" if asset["__type__"] == "sp.SkeletonData" \
                    else m.get("importer", "asset")
                meta.write_text(json.dumps(m, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        fixed.append(str(js))
    print("fixed:", len(fixed))
    for f in fixed:
        print("  ", f)
    print("skipped:", len(skipped))
    for s in skipped[:20]:
        print("  ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
