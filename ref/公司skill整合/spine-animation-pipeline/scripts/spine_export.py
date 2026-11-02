#!/usr/bin/env python3
"""Turn transparent parts + a layout into a Spine package the local editor can open.

Output (in --out):
    <name>.json      skeleton + idle animation, written in the TARGET version's
                     wire format (Spine 3.8 and 4.x are NOT interchangeable)
    <name>.atlas     texture atlas metadata
    <name>.png       packed atlas page
    images/<part>.png  trimmed parts, so the editor's Images path resolves
    manifest.json    every part with its atlas rect, pivot and source file
    export_report.json  gates, warnings and the version that was targeted

Layout coordinates are x-right / y-UP with the origin at the canvas CENTER.

    python spine_export.py --layout layout.json --out out/ \
        [--spine-version auto|3.8.75|4.2.0] [--gate] [--cli PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import parts_lib
import rig_rules
import spine_format

DEFAULT_PADDING = 4


# ── layout loading ──────────────────────────────────────────────────────────
def resolve_paths(layout, layout_path):
    base = Path(layout_path).resolve().parent
    for part in layout.get("parts", []):
        file_value = part.get("file") or f"parts/{part['name']}.png"
        path = Path(file_value)
        part["file"] = str(path if path.is_absolute() else (base / path))
    return layout


def read_layout(path):
    path = Path(path)
    layout = json.loads(path.read_text(encoding="utf-8"))
    if not layout.get("name"):
        raise ValueError("layout needs a non-empty \"name\"")
    if not layout.get("parts"):
        raise ValueError("layout needs at least one entry in \"parts\"")
    apply_coordinate_system(layout)
    return resolve_paths(layout, path)


def apply_coordinate_system(layout):
    """Accept part coordinates as image pixels, then convert to canvas space.

    Everyone reads positions off a reference image in pixels with y pointing
    down, so `"coordinate_system": "pixels-top-left"` lets a layout be written
    straight from those numbers. The canonical form used by the exporter is
    origin at the canvas centre with y pointing up.
    """
    system = str(layout.get("coordinate_system") or "canvas-center").lower()
    if system in ("canvas-center", "center", "centered", ""):
        return layout
    if system not in ("pixels-top-left", "pixels", "top-left", "image"):
        raise ValueError(f"unknown coordinate_system \"{system}\"; use "
                         "\"canvas-center\" or \"pixels-top-left\"")
    canvas = layout.get("canvas") or {}
    width = float(canvas.get("width") or 0)
    height = float(canvas.get("height") or 0)
    if not width or not height:
        raise ValueError("coordinate_system \"pixels-top-left\" needs "
                         "canvas.width and canvas.height")
    for part in layout["parts"]:
        if part.get("x") is not None:
            part["x"] = round(float(part["x"]) - width / 2.0, 6)
        if part.get("y") is not None:
            part["y"] = round(height / 2.0 - float(part["y"]), 6)
    layout["coordinate_system"] = "canvas-center"
    return layout


# ── image preparation ───────────────────────────────────────────────────────
def prepare_part(part, layout):
    image = parts_lib.load_rgba(part["file"])
    if part.get("keep_largest_component") or layout.get("keep_largest_component"):
        image = parts_lib.keep_largest_component(image, max_components=1)
    image, bbox = parts_lib.trim_to_alpha(image)
    if part.get("decontaminate_edges", layout.get("decontaminate_edges")):
        image = parts_lib.decontaminate_edges(image, boundary_radius=3)
    scale = float(part.get("image_scale", 1.0))
    if scale <= 0:
        raise ValueError(f"{part['name']}: image_scale must be positive")
    if abs(scale - 1.0) > 1e-9:
        image = image.resize((max(1, round(image.width * scale)),
                              max(1, round(image.height * scale))),
                             Image.Resampling.LANCZOS)
    return {"image": image, "bbox": list(bbox), "source": str(Path(part["file"]).resolve())}


# ── rig ─────────────────────────────────────────────────────────────────────
def bone_world_positions(parts, extra_bones):
    """Resolve each part bone's world position from its layout pivot.

    A part's `x`/`y` is the location of its joint (the bone). The image is then
    hung off that bone by `attachment_x/y`, so the art lands where the layout
    says while the bone sits at the joint.
    """
    world = {"root": (0.0, 0.0)}
    for bone in extra_bones:
        parent = bone.get("parent", "root")
        parent_x, parent_y = world.get(parent, (0.0, 0.0))
        world[bone["name"]] = (parent_x + float(bone.get("x", 0.0)),
                               parent_y + float(bone.get("y", 0.0)))
    for part in parts:
        world[part["bone"]] = (float(part.get("x", 0.0)), float(part.get("y", 0.0)))
    return world


def attachment_offset(part, image):
    """Offset from the bone to the image centre, in bone-local units."""
    pivot_x, pivot_y = part.get("pivot", (0.5, 0.5))
    offset_x = (0.5 - float(pivot_x)) * image.width
    offset_y = -(0.5 - float(pivot_y)) * image.height  # pivot y counts from the top
    return (offset_x + float(part.get("attachment_x", 0.0)),
            offset_y + float(part.get("attachment_y", 0.0)))


def order_bones(parents, extra_bones):
    """Emit bones parent-before-child; Spine requires that order."""
    children = {}
    for name, parent in parents.items():
        children.setdefault(parent, []).append(name)
    ordered = []
    queue = ["root"]
    while queue:
        current = queue.pop(0)
        for child in sorted(children.get(current, [])):
            ordered.append(child)
            queue.append(child)
    missing = set(parents) - set(ordered)
    if missing:
        raise ValueError(f"bones unreachable from root (cycle?): {sorted(missing)}")
    return ordered


# ── animation authoring (3.8-normalized form, converted later if needed) ────
def idle_timeline(kind, amount, duration, phase):
    """Three keyframes with an ease-in-out bezier, in 3.8 spelled form."""
    midpoint = round(duration * float(phase), 4)
    ease = {"curve": 0.25, "c2": 0.0, "c3": 0.75, "c4": 1.0}
    # The ease goes on both segment-start keyframes so the motion eases out and
    # back; the last keyframe carries no curve, as Spine requires.
    if kind == "rotate":
        return [
            {"time": 0, "angle": 0, **ease},
            {"time": midpoint, "angle": round(float(amount), 4), **ease},
            {"time": duration, "angle": 0},
        ]
    if kind == "translate":
        return [
            {"time": 0, "x": 0, "y": 0, **ease},
            {"time": midpoint, "x": 0, "y": round(float(amount), 4), **ease},
            {"time": duration, "x": 0, "y": 0},
        ]
    if kind == "scale":
        return [
            {"time": 0, "x": 1, "y": 1, **ease},
            {"time": midpoint, "x": 1, "y": round(1 + float(amount), 4), **ease},
            {"time": duration, "x": 1, "y": 1},
        ]
    raise ValueError(f"unknown timeline kind: {kind}")


# ── skeleton assembly ───────────────────────────────────────────────────────
def build_skeleton(layout, ordered_parts, parents, extra_bones, prepared):
    canvas = layout.get("canvas", {})
    canvas_width = int(canvas.get("width", 512))
    canvas_height = int(canvas.get("height", 512))
    duration = float(layout.get("idle", {}).get("duration", 2.4))
    if duration <= 0:
        raise ValueError("idle.duration must be positive")
    animation_name = layout.get("animation", "idle")

    world = bone_world_positions(ordered_parts, extra_bones)
    bones = [{"name": "root"}]
    for name in order_bones(parents, extra_bones):
        parent = parents[name]
        parent_x, parent_y = world.get(parent, (0.0, 0.0))
        local_x, local_y = world.get(name, (0.0, 0.0))
        bone = {"name": name, "parent": parent,
                "x": round(local_x - parent_x, 4), "y": round(local_y - parent_y, 4)}
        spec = next((item for item in extra_bones if item["name"] == name), None)
        if spec:
            for field in ("rotation", "length", "scaleX", "scaleY", "transform", "skin"):
                if field in spec:
                    bone[field] = spec[field]
        bones.append(bone)

    slots = []
    attachments = {}
    timelines = {}
    manifest_parts = []
    for part in ordered_parts:
        name = part["name"]
        image = prepared[name]["image"]
        bone_name = part["bone"]
        slot_name = part.get("slot", name)
        offset_x, offset_y = attachment_offset(part, image)
        attachment = {
            "x": round(offset_x, 4),
            "y": round(offset_y, 4),
            "width": image.width,
            "height": image.height,
        }
        if part.get("attachment_rotation"):
            attachment["rotation"] = float(part["attachment_rotation"])
        if float(part.get("scaleX", 1.0)) != 1.0:
            attachment["scaleX"] = float(part["scaleX"])
        if float(part.get("scaleY", 1.0)) != 1.0:
            attachment["scaleY"] = float(part["scaleY"])
        # Attachment name == atlas region name == part name, so neither "path"
        # nor "type" has to be written. That is the form every Spine version
        # reads back most reliably.
        slots.append({"name": slot_name, "bone": bone_name, "attachment": name})
        attachments[slot_name] = {name: attachment}

        timeline = timelines.setdefault(bone_name, {})
        if part.get("idle_rotate"):
            timeline["rotate"] = idle_timeline("rotate", part["idle_rotate"], duration,
                                               part.get("idle_phase", 0.5))
        if part.get("idle_translate_y"):
            timeline["translate"] = idle_timeline("translate", part["idle_translate_y"],
                                                  duration, part.get("idle_phase", 0.5))
        if part.get("idle_scale_y"):
            timeline["scale"] = idle_timeline("scale", part["idle_scale_y"], duration,
                                              part.get("idle_phase", 0.5))

        manifest_parts.append({
            "name": name,
            "slot": slot_name,
            "bone": bone_name,
            "parent": part.get("parent", "root"),
            "kind": part.get("kind"),
            "draw_order": part.get("draw_order"),
            "pivot": list(part.get("pivot", (0.5, 0.5))),
            "attachment": [round(offset_x, 4), round(offset_y, 4)],
            "size": [image.width, image.height],
            "bbox": prepared[name]["bbox"],
            "source": prepared[name]["source"],
            "world": [round(world.get(bone_name, (0.0, 0.0))[0], 4),
                      round(world.get(bone_name, (0.0, 0.0))[1], 4)],
        })

    idle = layout.get("idle", {})
    root_timeline = {}
    if idle.get("root_translate_y"):
        root_timeline["translate"] = idle_timeline("translate", idle["root_translate_y"],
                                                   duration, idle.get("root_phase", 0.5))
    if idle.get("root_scale_y"):
        root_timeline["scale"] = idle_timeline("scale", idle["root_scale_y"],
                                               duration, idle.get("root_phase", 0.5))
    if root_timeline:
        timelines["root"] = root_timeline
    timelines = {bone: data for bone, data in timelines.items() if data}

    digest = hashlib.md5(json.dumps(layout, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:20]
    document = {
        "skeleton": {
            "hash": digest,
            "spine": "3.8.75",
            "x": -canvas_width / 2,
            "y": -canvas_height / 2,
            "width": canvas_width,
            "height": canvas_height,
            "images": "images/",
        },
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {animation_name: {"bones": timelines}},
    }
    return document, manifest_parts


# ── atlas packing ───────────────────────────────────────────────────────────
def next_power_of_two(value):
    value = max(1, int(math.ceil(value)))
    return 1 << (value - 1).bit_length()


def pack_rows(images, padding=DEFAULT_PADDING, max_side=4096):
    """Shelf packer: tall parts first, power-of-two page, no rotation."""
    ordered = sorted(images.items(), key=lambda item: (-item[1].height, item[0]))
    largest = max(max(image.width, image.height) for _, image in ordered) + padding * 2
    area = sum((image.width + padding) * (image.height + padding) for _, image in ordered)
    width = next_power_of_two(max(largest, math.sqrt(area) * 1.3))
    while True:
        x = y = padding
        row_height = 0
        placements = {}
        for name, image in ordered:
            if x + image.width + padding > width:
                x = padding
                y += row_height + padding
                row_height = 0
            placements[name] = (x, y, image.width, image.height)
            x += image.width + padding
            row_height = max(row_height, image.height)
        height = next_power_of_two(y + row_height + padding)
        if height <= max_side or width >= max_side:
            if width > max_side or height > max_side:
                raise ValueError(
                    f"parts do not fit a {max_side}x{max_side} page "
                    f"(needed {width}x{height}); scale the art down first")
            return width, height, placements
        width *= 2


def atlas_text(page_name, width, height, placements, frame_names=None):
    """Standard .atlas text -- the same 6 header lines 3.8 and 4.x both accept."""
    lines = [page_name, f"size: {width},{height}", "format: RGBA8888",
             "filter: Linear,Linear", "repeat: none"]
    for name, (x, y, part_width, part_height) in placements.items():
        lines += [name, "  rotate: false", f"  xy: {x}, {y}",
                  f"  size: {part_width}, {part_height}",
                  f"  orig: {part_width}, {part_height}",
                  "  offset: 0, 0", "  index: -1"]
    return "\n".join(lines) + "\n"


# ── driver ──────────────────────────────────────────────────────────────────
def export(layout_path, out_dir, spine_version="auto", cli=None, gate=False, max_side=4096):
    layout = read_layout(layout_path)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    images_dir = output / "images"
    images_dir.mkdir(exist_ok=True)

    # 1. target version -------------------------------------------------------
    detected = None
    cli_path = None
    if spine_version in (None, "auto"):
        try:
            import spine_cli
            cli_path, _ = spine_cli.find_cli(cli)
            if cli_path:
                detected = spine_cli.cli_version(cli_path)
        except Exception:
            detected = None
        spine_version = layout.get("spine_version") or detected or "4.2.0"
        version_source = ("layout" if layout.get("spine_version")
                          else "spine-cli" if detected else "default")
    else:
        version_source = "argument"

    # 2. parts ----------------------------------------------------------------
    prepared = {}
    for part in layout["parts"]:
        name = part.get("name")
        if not name:
            raise ValueError("every part needs a name")
        if name in prepared:
            raise ValueError(f"duplicate part name: {name}")
        prepared[name] = prepare_part(part, layout)

    # 3. rig ------------------------------------------------------------------
    ordered, parents, notes = rig_rules.build_rig(layout["parts"],
                                                 layout.get("extra_bones", ()))
    document, manifest_parts = build_skeleton(layout, ordered, parents,
                                             layout.get("extra_bones", ()), prepared)
    spine_format.normalize_to_target(document, spine_version)

    # 4. atlas ----------------------------------------------------------------
    pages = {name: item["image"] for name, item in prepared.items()}
    atlas_width, atlas_height, placements = pack_rows(pages, max_side=max_side)
    page = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for name, rect in placements.items():
        page.alpha_composite(pages[name], (rect[0], rect[1]))

    name = layout["name"]
    page_path = output / f"{name}.png"
    atlas_path = output / f"{name}.atlas"
    json_path = output / f"{name}.json"
    manifest_path = output / "manifest.json"
    report_path = output / "export_report.json"

    page.save(page_path)
    for part_name, item in prepared.items():
        item["image"].save(images_dir / f"{part_name}.png")
    atlas_path.write_text(atlas_text(page_path.name, atlas_width, atlas_height, placements),
                          encoding="utf-8")
    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")

    for entry in manifest_parts:
        rect = placements[entry["name"]]
        entry["atlas"] = list(rect)
        # Back-reference: where the part's own pivot landed on the page.
        entry["atlas_pivot"] = [rect[0] + round(entry["pivot"][0] * entry["size"][0], 4),
                                rect[1] + round(entry["pivot"][1] * entry["size"][1], 4)]
    manifest = {
        "name": name,
        "spine_version": document["skeleton"]["spine"],
        "spine_version_source": version_source,
        "canvas": {"width": document["skeleton"]["width"],
                   "height": document["skeleton"]["height"]},
        "page": {"file": page_path.name, "size": [atlas_width, atlas_height]},
        "atlas": atlas_path.name,
        "skeleton": json_path.name,
        "animation": layout.get("animation", "idle"),
        "duration": float(layout.get("idle", {}).get("duration", 2.4)),
        "parts": manifest_parts,
        "bones": [bone["name"] for bone in document["bones"]],
        "notes": notes,
    }
    parts_lib.write_json(manifest_path, manifest)

    # 5. gates ----------------------------------------------------------------
    curve_issues = spine_format.validate_curves(document)
    gate_result = None
    if gate or cli:
        try:
            import spine_cli
            cli_path = cli_path or spine_cli.find_cli(cli)[0]
            if cli_path:
                gate_result = spine_cli.import_gate(cli_path, json_path,
                                                    work_dir=output / ".import-gate")
                if gate_result.get("ok"):
                    gate_result.pop("output", None)  # keep the report readable
        except Exception as error:  # pragma: no cover
            gate_result = {"ok": False, "output": str(error)}

    report = {
        "ok": not curve_issues and (gate_result is None or gate_result["ok"]),
        "spine_version": document["skeleton"]["spine"],
        "version_family": spine_format.version_family(document["skeleton"]["spine"]),
        "version_source": version_source,
        "detected_cli_version": detected,
        "parts": len(manifest_parts),
        "bones": len(document["bones"]),
        "page": [atlas_width, atlas_height],
        "curve_issues": curve_issues,
        "warnings": notes,
        "import_gate": gate_result,
        "files": {"skeleton": str(json_path), "atlas": str(atlas_path),
                  "page": str(page_path), "manifest": str(manifest_path),
                  "images": str(images_dir)},
    }
    parts_lib.write_json(report_path, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export parts + layout as a Spine package")
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--spine-version", default="auto",
                        help="auto (use the local Spine CLI version) or e.g. 3.8.75 / 4.2.0")
    parser.add_argument("--cli", default=None, help="explicit Spine CLI path for the import gate")
    parser.add_argument("--gate", action="store_true", help="verify by importing into Spine CLI")
    parser.add_argument("--max-side", type=int, default=4096)
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)

    try:
        report = export(args.layout, args.out, spine_version=args.spine_version,
                        cli=args.cli, gate=args.gate, max_side=args.max_side)
    except (ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"skeleton : {report['files']['skeleton']}  (Spine {report['spine_version']})")
        print(f"atlas    : {report['files']['atlas']}  page {report['page'][0]}x{report['page'][1]}")
        print(f"parts    : {report['parts']}   bones: {report['bones']}")
        if report["curve_issues"]:
            print("CURVE ISSUES:")
            for issue in report["curve_issues"]:
                print("  -", issue)
        for warning in report["warnings"]:
            print("warning  :", warning)
        if report["import_gate"]:
            status = "PASS" if report["import_gate"]["ok"] else "FAIL"
            print(f"import gate (Spine {report['detected_cli_version']}): {status}")
        print("RESULT:", "OK" if report["ok"] else "FAILED")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
