#!/usr/bin/env python3
"""Pack transparent character parts and emit a Spine 4.2 JSON/atlas package."""

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image

from decontaminate_alpha_edges import edge_decontaminate


PADDING = 4


def next_power_of_two(value):
    value = max(1, int(value))
    return 1 << (value - 1).bit_length()


def read_layout(layout_path):
    with Path(layout_path).open("r", encoding="utf-8") as handle:
        layout = json.load(handle)
    if not layout.get("name"):
        raise ValueError("layout must contain a non-empty name")
    if not layout.get("parts"):
        raise ValueError("layout must contain at least one part")
    return layout


def retain_largest_alpha_component(image):
    """Drop disconnected extraction debris while preserving anti-aliased alpha."""
    alpha = image.getchannel("A")
    width, height = image.size
    values = list(alpha.getdata())
    visited = bytearray(width * height)
    largest = []
    for start, value in enumerate(values):
        if value == 0 or visited[start]:
            continue
        component = []
        stack = [start]
        visited[start] = 1
        while stack:
            index = stack.pop()
            component.append(index)
            x = index % width
            y = index // width
            for neighbor_y in range(max(0, y - 1), min(height, y + 2)):
                row = neighbor_y * width
                for neighbor_x in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = row + neighbor_x
                    if not visited[neighbor] and values[neighbor] > 0:
                        visited[neighbor] = 1
                        stack.append(neighbor)
        if len(component) > len(largest):
            largest = component
    kept = [0] * len(values)
    for index in largest:
        kept[index] = values[index]
    cleaned = image.copy()
    mask = Image.new("L", image.size)
    mask.putdata(kept)
    cleaned.putalpha(mask)
    return cleaned


def validate_and_trim(part):
    path = Path(part["file"])
    if not path.is_file():
        raise ValueError(f"{part['name']}: source file does not exist: {path}")
    with Image.open(path) as source:
        if source.mode != "RGBA":
            raise ValueError(f"{part['name']}: source must be RGBA, got {source.mode}")
        source = source.copy()
        if part.get("keep_largest_component"):
            source = retain_largest_alpha_component(source)
        alpha = source.getchannel("A")
        extrema = alpha.getextrema()
        if extrema[0] != 0 or extrema[1] != 255:
            raise ValueError(
                f"{part['name']}: source must contain both transparent and opaque pixels"
            )
        bbox = alpha.getbbox()
        if bbox is None:
            raise ValueError(f"{part['name']}: source has no opaque pixels")
        cropped = source.crop(bbox).copy()
        if part.get("decontaminate_edges"):
            cropped = edge_decontaminate(cropped)
    scale = float(part.get("image_scale", 1))
    if scale <= 0:
        raise ValueError(f"{part['name']}: image_scale must be positive")
    if scale != 1:
        cropped = cropped.resize(
            (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
            Image.Resampling.LANCZOS,
        )
    return cropped, bbox


def pack_rows(images, padding=PADDING):
    ordered = sorted(images.items(), key=lambda item: (-item[1].height, item[0]))
    largest = max(max(image.width, image.height) for _, image in ordered) + padding * 2
    total_area = sum((image.width + padding) * (image.height + padding) for _, image in ordered)
    width = next_power_of_two(max(largest, math.sqrt(total_area) * 1.35))

    while True:
        x = padding
        y = padding
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
        if height <= 4096 or width >= 4096:
            return width, height, placements
        width *= 2


def atlas_text(page_name, width, height, placements):
    lines = [
        page_name,
        f"size: {width},{height}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
        "pma: false",
    ]
    for name, (x, y, part_width, part_height) in placements.items():
        lines.extend([
            "",
            name,
            "  rotate: false",
            f"  xy: {x}, {y}",
            f"  size: {part_width}, {part_height}",
            f"  orig: {part_width}, {part_height}",
            "  offset: 0, 0",
            "  index: -1",
        ])
    return "\n".join(lines) + "\n"


def keyframes(duration, kind, amount, axis=None, phase=0.5, spine_version="4.2.0"):
    midpoint = round(duration * phase, 4)
    if kind == "rotate":
        rotate_value = "angle" if spine_version.startswith("3.") else "value"
        return [
            {rotate_value: 0},
            {"time": midpoint, rotate_value: amount},
            {"time": duration, rotate_value: 0},
        ]
    if kind == "translate":
        x = amount if axis == "x" else 0
        y = amount if axis == "y" else 0
        return [{"x": 0, "y": 0}, {"time": midpoint, "x": x, "y": y}, {"time": duration, "x": 0, "y": 0}]
    if kind == "scale":
        x = 1 + amount if axis == "x" else 1
        y = 1 + amount if axis == "y" else 1
        return [{"x": 1, "y": 1}, {"time": midpoint, "x": x, "y": y}, {"time": duration, "x": 1, "y": 1}]
    raise ValueError(f"unknown timeline type: {kind}")


def build_skeleton(layout, part_images):
    canvas = layout.get("canvas", {})
    canvas_width = int(canvas.get("width", 1024))
    canvas_height = int(canvas.get("height", 1024))
    duration = float(layout.get("idle", {}).get("duration", 2.4))
    spine_version = str(layout.get("spine_version", "4.2.0"))
    if duration <= 0:
        raise ValueError("idle.duration must be positive")

    ordered_parts = sorted(layout["parts"], key=lambda item: (item.get("draw_order", 0), item["name"]))
    bone_specs = {}

    def add_bone_spec(bone):
        bone_name = bone.get("name")
        if not bone_name or bone_name == "root":
            raise ValueError("extra bones and part bones must have a non-root name")
        existing = bone_specs.get(bone_name)
        if existing and existing != bone:
            raise ValueError(f"{bone_name}: duplicate bones must use the same transform")
        bone_specs[bone_name] = bone

    for extra in layout.get("extra_bones", []):
        bone = {"name": extra.get("name"), "parent": extra.get("parent", "root")}
        for field in ("x", "y", "rotation", "scaleX", "scaleY", "length", "transform", "skin"):
            if field in extra:
                bone[field] = extra[field]
        add_bone_spec(bone)

    for part in ordered_parts:
        bone_name = part.get("bone", part["name"])
        bone = {"name": bone_name, "parent": part.get("parent", "root")}
        for field in ("x", "y", "rotation", "scaleX", "scaleY", "length", "transform", "skin"):
            if field in part:
                bone[field] = part[field]
        add_bone_spec(bone)

    bones = [{"name": "root"}]
    added_bones = {"root"}
    unresolved = list(bone_specs.values())
    while unresolved:
        next_unresolved = []
        for bone in unresolved:
            if bone["parent"] in added_bones:
                bones.append(bone)
                added_bones.add(bone["name"])
            else:
                next_unresolved.append(bone)
        if len(next_unresolved) == len(unresolved):
            unresolved_names = ", ".join(item["name"] for item in next_unresolved)
            raise ValueError(f"bones have missing or cyclic parents: {unresolved_names}")
        unresolved = next_unresolved

    slots = []
    attachments = {}
    timelines = {}

    for part in ordered_parts:
        name = part["name"]
        bone_name = part.get("bone", name)

        slot_name = part.get("slot", name)
        slots.append({"name": slot_name, "bone": bone_name, "attachment": name})
        image = part_images[name]
        attachment = {
            "type": "region",
            "path": name,
            "x": float(part.get("attachment_x", 0)),
            "y": float(part.get("attachment_y", 0)),
            "rotation": float(part.get("attachment_rotation", 0)),
            "width": image.width,
            "height": image.height,
        }
        attachments[slot_name] = {name: attachment}

        bone_timelines = timelines.setdefault(bone_name, {})
        if part.get("idle_rotate"):
            bone_timelines["rotate"] = keyframes(
                duration,
                "rotate",
                float(part["idle_rotate"]),
                phase=float(part.get("idle_phase", 0.5)),
                spine_version=spine_version,
            )
        if part.get("idle_translate_y"):
            bone_timelines["translate"] = keyframes(duration, "translate", float(part["idle_translate_y"]), axis="y", phase=float(part.get("idle_phase", 0.5)))
        if part.get("idle_scale_y"):
            bone_timelines["scale"] = keyframes(duration, "scale", float(part["idle_scale_y"]), axis="y", phase=float(part.get("idle_phase", 0.5)))

    idle = layout.get("idle", {})
    root_timeline = {}
    if idle.get("root_translate_y"):
        root_timeline["translate"] = keyframes(duration, "translate", float(idle["root_translate_y"]), axis="y")
    if idle.get("root_scale_y"):
        root_timeline["scale"] = keyframes(duration, "scale", float(idle["root_scale_y"]), axis="y")
    if root_timeline:
        timelines["root"] = root_timeline
    timelines = {bone: data for bone, data in timelines.items() if data}

    digest = hashlib.md5(json.dumps(layout, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return {
        "skeleton": {
            "hash": digest,
            "spine": spine_version,
            "x": -canvas_width / 2,
            "y": -canvas_height / 2,
            "width": canvas_width,
            "height": canvas_height,
            "images": "images/",
        },
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {"idle": {"bones": timelines}},
    }


def export_spine(layout_path, out_dir):
    layout = read_layout(layout_path)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized_dir = output / "preview_parts"
    normalized_dir.mkdir(exist_ok=True)
    editor_images_dir = output / "images"
    editor_images_dir.mkdir(exist_ok=True)

    images = {}
    trim_metadata = {}
    names = set()
    for part in layout["parts"]:
        name = part.get("name")
        if not name:
            raise ValueError("each part must contain a non-empty name")
        if name in names:
            raise ValueError(f"duplicate part name: {name}")
        names.add(name)
        effective_part = dict(part)
        if layout.get("decontaminate_edges"):
            effective_part["decontaminate_edges"] = True
        image, bbox = validate_and_trim(effective_part)
        images[name] = image
        trim_metadata[name] = {"source": str(Path(part["file"]).resolve()), "bbox": list(bbox), "size": [image.width, image.height]}
        image.save(normalized_dir / f"{name}.png")
        image.save(editor_images_dir / f"{name}.png")

    atlas_width, atlas_height, placements = pack_rows(images)
    page = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for name, (x, y, _, _) in placements.items():
        page.alpha_composite(images[name], (x, y))

    name = layout["name"]
    page_path = output / f"{name}.png"
    atlas_path = output / f"{name}.atlas"
    json_path = output / f"{name}.json"
    manifest_path = output / "manifest.json"
    page.save(page_path)
    atlas_path.write_text(atlas_text(page_path.name, atlas_width, atlas_height, placements), encoding="utf-8")
    skeleton = build_skeleton(layout, images)
    json_path.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "name": name,
        "page": page_path.name,
        "atlas": atlas_path.name,
        "skeleton": json_path.name,
        "parts": [{"name": item["name"], "atlas": list(placements[item["name"]]), **trim_metadata[item["name"]]} for item in layout["parts"]],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "page": page_path,
        "atlas": atlas_path,
        "json": json_path,
        "manifest": manifest_path,
        "editor_images": editor_images_dir,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export transparent parts as a Spine 4.2 JSON/atlas package")
    parser.add_argument("--layout", required=True, help="Layout JSON describing source parts and draw order")
    parser.add_argument("--out", required=True, help="New or existing output directory")
    args = parser.parse_args(argv)
    try:
        paths = export_spine(args.layout, args.out)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
