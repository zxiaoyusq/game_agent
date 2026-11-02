#!/usr/bin/env python3
"""Verify art assets in a reconstructed Cocos project.

Checks PNG decode integrity, atlas<->skeleton<->png pairing, SkeletonData
attachment coverage (own atlas + global index), and detects mangled jsons.

Usage:
  python verify_assets.py --project <project> [--out report.json]
      [--extract-skeletons] [--write-combined-atlas]
"""
import argparse
import json
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    Image = None


def parse_atlas(text):
    """Return (pages, regions) for a Spine atlas text.

    Page header: unindented name line followed by an unindented 'size:' line.
    Region: unindented name line; properties are indented.
    """
    lines = text.splitlines()
    pages, regions = [], []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s or line[:1].isspace():
            i += 1
            continue
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        is_page = (j < n and not lines[j][:1].isspace()
                   and lines[j].strip().lower().startswith("size:"))
        if is_page:
            pages.append(s)
            i = j + 1
            while i < n and not lines[i][:1].isspace():
                t = lines[i].strip().lower()
                if t.startswith(("format:", "filter:", "repeat:")):
                    i += 1
                else:
                    break
            continue
        if not s.lower().startswith(("size:", "rotate:", "xy:", "orig:",
                                     "offset:", "index:")):
            regions.append(s)
        i += 1
    return pages, regions


def atlas_blocks(atext):
    """Map page name -> page block text."""
    lines = atext.splitlines()
    blocks = {}
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if not line.strip() or line[:1].isspace():
            i += 1
            continue
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if (j < n and not lines[j][:1].isspace()
                and lines[j].strip().lower().startswith("size:")):
            start = i
            k = j + 1
            while k < n and lines[k].strip():
                k += 1
            blocks[line.strip()] = "\n".join(lines[start:k])
            i = k
        else:
            i += 1
    return blocks


def collect_attachments(sj):
    atts = set()
    skins = sj.get("skins", []) or []
    if isinstance(skins, dict):
        skins = list(skins.values())
    for skin in skins:
        if not isinstance(skin, dict):
            continue
        am = skin.get("attachments", {}) or {}
        for _slot, m in am.items():
            if not isinstance(m, dict):
                continue
            for name, att in m.items():
                if att is not None:
                    atts.add(name)
    return atts


def decode_serialized(arr):
    """Convert a Cocos serialized array into a dict asset (SkeletonData)."""
    classes = arr[3] if len(arr) > 3 else []
    data = arr[5] if len(arr) > 5 else []
    for cls in classes:
        if not isinstance(cls, list) or not cls:
            continue
        typ, fields = cls[0], cls[1]
        if typ == "sp.SkeletonData" and data:
            rec = dict(zip(fields, data[0][1:]))
            if isinstance(rec.get("_skeletonJson"), str):
                rec["_skeletonJson"] = json.loads(rec["_skeletonJson"])
            rec["__type__"] = "sp.SkeletonData"
            return rec
    for cls in classes:
        if isinstance(cls, list) and cls and cls[0] == "cc.SpriteFrame":
            return {"__type__": "cc.SpriteFrame"}
    return None


def load_skeleton_data(js_path):
    """Return dict asset or None; raises on parse error."""
    arr = json.loads(js_path.read_text(encoding="utf-8"))
    if isinstance(arr, list) and arr and isinstance(arr[0], dict):
        return arr[0]
    return decode_serialized(arr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--extract-skeletons", action="store_true",
                    help="write <stem>.skeleton.json next to each atlas")
    ap.add_argument("--write-combined-atlas", action="store_true",
                    help="write <stem>_full.atlas for multi-atlas skeletons")
    a = ap.parse_args()
    root = pathlib.Path(a.project)
    report = {"png_ok": 0, "png_broken": [], "spine": 0, "spriteframe": 0,
              "mangled": [], "missing_texture": [], "dead_attachments": [],
              "multi_atlas": [], "atlas_summary": []}

    for p in root.rglob("*.png"):
        try:
            with Image.open(p) as im:
                im.load()
            report["png_ok"] += 1
        except Exception as e:
            report["png_broken"].append((str(p), repr(e)))

    global_regions = {}

    def index_atlas_text(atext, src):
        _pages, regions = parse_atlas(atext)
        for r in regions:
            global_regions.setdefault(r, set()).add(str(src))

    # Pass 1: build the full global region index from every standalone .atlas
    # and every embedded _atlasText before evaluating coverage.
    skeleton_files = []
    for a_file in sorted(root.rglob("*.atlas")):
        try:
            index_atlas_text(a_file.read_text(encoding="utf-8", errors="replace"),
                             a_file)
        except Exception:
            pass
        js = a_file.parent / (a_file.stem + ".json")
        if not js.exists():
            continue
        try:
            asset = load_skeleton_data(js)
        except Exception:
            continue
        if asset and asset.get("__type__") == "sp.SkeletonData":
            skeleton_files.append((a_file, js, asset))
            index_atlas_text(asset.get("_atlasText", ""), js)

    # Pass 2: per-atlas checks
    for a_file, js, asset in skeleton_files:
        d, stem = a_file.parent, a_file.stem
        entry = {"atlas": str(a_file)}
        typ = asset.get("__type__")
        entry["type"] = typ
        report["spine"] += 1
        atext = asset.get("_atlasText", "")
        pages, regions = parse_atlas(atext)
        for tn in asset.get("textureNames", []) or []:
            cand = d / tn
            if not cand.exists():
                hit = next((x for x in d.iterdir() if x.is_file()
                            and x.name.lower() == tn.lower()), None)
                if hit is None:
                    report["missing_texture"].append((str(a_file), tn))
                    continue
                cand = hit
            try:
                with Image.open(cand) as im:
                    im.load()
            except Exception as e:
                report["png_broken"].append((str(cand), repr(e)))
        sj = asset.get("_skeletonJson")
        if not isinstance(sj, dict):
            report["mangled"].append((str(a_file), "no _skeletonJson"))
            report["atlas_summary"].append(entry)
            continue
        atts = collect_attachments(sj)
        missing = sorted(atts - set(regions))
        dead, elsewhere = [], []
        for att in missing:
            if att in global_regions:
                elsewhere.append(att)
            else:
                dead.append(att)
        if elsewhere:
            report["multi_atlas"].append((str(a_file), elsewhere))
        if dead:
            report["dead_attachments"].append((str(a_file), dead))
        if a.extract_skeletons:
            (d / (stem + ".skeleton.json")).write_text(
                json.dumps(sj, ensure_ascii=False, indent=2), encoding="utf-8")
        if a.write_combined_atlas and elsewhere:
            build_combined_atlas(d, stem, atext, js, global_regions, report)
        entry.update({"pages": len(pages), "regions": len(regions),
                      "attachments": len(atts), "missing_own": len(missing)})
        report["atlas_summary"].append(entry)

    # Report standalone atlases whose sibling json is not SkeletonData
    for a_file in sorted(root.rglob("*.atlas")):
        if a_file.stem.endswith("_full") or a_file.stem.endswith(".skeleton"):
            continue  # generated artifacts (combined atlas / skeleton dump)
        js = a_file.parent / (a_file.stem + ".json")
        if not js.exists():
            report["mangled"].append((str(a_file), "no sibling json"))
            continue
        try:
            asset = load_skeleton_data(js)
        except Exception as e:
            report["mangled"].append((str(a_file), "parse err " + repr(e)))
            continue
        typ = asset.get("__type__") if asset else None
        if typ == "cc.SpriteFrame":
            report["spriteframe"] += 1
            report["atlas_summary"].append({"atlas": str(a_file), "type": typ})
        elif typ not in ("sp.SkeletonData", None):
            report["mangled"].append((str(a_file), "unexpected type " + str(typ)))
            report["atlas_summary"].append({"atlas": str(a_file), "type": typ})

    report["png_total"] = report["png_ok"] + len(report["png_broken"])
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if a.out:
        pathlib.Path(a.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print("report written:", a.out)
    return 1 if (report["png_broken"] or report["mangled"]
                 or report["missing_texture"]) else 0


def build_combined_atlas(d, stem, own_atext, own_js, global_regions, report):
    """Collect page blocks from every atlas text that has extra regions."""
    blocks = atlas_blocks(own_atext)
    extra_sources = set()
    for srcset in global_regions.values():
        for s in srcset:
            if s != str(own_js):
                extra_sources.add(pathlib.Path(s))
    for src in extra_sources:
        try:
            asset = load_skeleton_data(src)
            atext = asset.get("_atlasText", "") if asset else ""
        except Exception:
            continue
        for pg, blk in atlas_blocks(atext).items():
            if pg not in blocks:
                blocks[pg] = blk
                png = d / pg
                if not png.exists():
                    src_png = src.parent / pg
                    if src_png.exists():
                        png.write_bytes(src_png.read_bytes())
    text = "\n\n".join(blocks.values())
    (d / (stem + "_full.atlas")).write_text(text, encoding="utf-8")
    report.setdefault("combined_atlas", []).append(str(d / (stem + "_full.atlas")))


if __name__ == "__main__":
    sys.exit(main())
