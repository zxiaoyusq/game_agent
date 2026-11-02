#!/usr/bin/env python3
"""Create a local HTML and static PNG QA preview for a Spine export layout."""

import argparse
import html
import json
import sys
from pathlib import Path

from PIL import Image


def read_layout(layout_path):
    with Path(layout_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_css_name(name):
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in name)


def world_positions(parts, extra_bones=()):
    """Resolve setup-pose bone translations so the preview matches parented parts."""
    bones_by_name = {extra["name"]: extra for extra in extra_bones}
    bones_by_name.update({part.get("bone", part["name"]): part for part in parts})
    resolved = {"root": (0.0, 0.0)}
    resolving = set()

    def resolve(bone_name):
        if bone_name in resolved:
            return resolved[bone_name]
        if bone_name in resolving:
            raise ValueError(f"cyclic preview parent: {bone_name}")
        bone = bones_by_name.get(bone_name)
        if bone is None:
            raise ValueError(f"missing preview parent bone: {bone_name}")
        resolving.add(bone_name)
        parent_x, parent_y = resolve(bone.get("parent", "root"))
        position = (parent_x + float(bone.get("x", 0)), parent_y + float(bone.get("y", 0)))
        resolving.remove(bone_name)
        resolved[bone_name] = position
        return position

    return {part["name"]: resolve(part.get("bone", part["name"])) for part in parts}


def part_geometry(part, image_size, canvas, world_position=None):
    width, height = image_size
    center_x = canvas["width"] / 2
    center_y = canvas["height"] / 2
    x, y = world_position or (float(part.get("x", 0)), float(part.get("y", 0)))
    attach_x = float(part.get("attachment_x", 0))
    attach_y = float(part.get("attachment_y", 0))
    return {
        "left": center_x + x + attach_x - width / 2,
        "top": center_y - y - attach_y - height / 2,
        "origin_x": width / 2 - attach_x,
        "origin_y": height / 2 + attach_y,
        "width": width,
        "height": height,
        "rotation": float(part.get("rotation", 0)),
    }


def render_static_preview(layout, output_dir):
    canvas = layout.get("canvas", {})
    width = int(canvas.get("width", 1024))
    height = int(canvas.get("height", 1024))
    image = Image.new("RGBA", (width, height), (255, 250, 239, 255))
    positions = world_positions(layout["parts"], layout.get("extra_bones", []))
    for part in sorted(layout["parts"], key=lambda item: (item.get("draw_order", 0), item["name"])):
        part_path = output_dir / "preview_parts" / f"{part['name']}.png"
        with Image.open(part_path) as source:
            source = source.convert("RGBA")
            geometry = part_geometry(part, source.size, {"width": width, "height": height}, positions[part["name"]])
            image.alpha_composite(source, (round(geometry["left"]), round(geometry["top"])))
    preview_path = output_dir / "preview.png"
    image.save(preview_path)
    return preview_path


def html_for_layout(layout, output_dir):
    canvas = layout.get("canvas", {})
    width = int(canvas.get("width", 1024))
    height = int(canvas.get("height", 1024))
    duration = float(layout.get("idle", {}).get("duration", 2.4))
    root_scale = float(layout.get("idle", {}).get("root_scale_y", 0))
    root_lift = float(layout.get("idle", {}).get("root_translate_y", 0))
    css = [
        "* { box-sizing: border-box; }",
        "body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f6efe1; font-family: system-ui, sans-serif; }",
        f"#stage {{ position: relative; width: {width}px; height: {height}px; overflow: hidden; background: #fffaf0; box-shadow: 0 16px 48px #8a6b4433; }}",
        f"#character {{ position: absolute; inset: 0; transform-origin: 50% 50%; animation: root-idle {duration}s ease-in-out infinite; }}",
        f"@keyframes root-idle {{ 0%,100% {{ transform: translateY(0) scaleY(1); }} 50% {{ transform: translateY({-root_lift}px) scaleY({1 + root_scale}); }} }}",
        ".part { position: absolute; will-change: transform; }",
    ]
    layers = []
    positions = world_positions(layout["parts"], layout.get("extra_bones", []))
    for part in sorted(layout["parts"], key=lambda item: (item.get("draw_order", 0), item["name"])):
        name = part["name"]
        part_path = output_dir / "preview_parts" / f"{name}.png"
        with Image.open(part_path) as source:
            geometry = part_geometry(part, source.size, {"width": width, "height": height}, positions[part["name"]])
        css_name = safe_css_name(name)
        rotation = -geometry["rotation"]
        idle_rotation = -float(part.get("idle_rotate", 0))
        idle_y = -float(part.get("idle_translate_y", 0))
        idle_scale_y = 1 + float(part.get("idle_scale_y", 0))
        phase = float(part.get("idle_phase", 0.5)) * 100
        css.extend([
            f".p-{css_name} {{ left: {geometry['left']:.2f}px; top: {geometry['top']:.2f}px; width: {geometry['width']}px; height: {geometry['height']}px; transform-origin: {geometry['origin_x']:.2f}px {geometry['origin_y']:.2f}px; z-index: {int(part.get('draw_order', 0))}; animation: idle-{css_name} {duration}s ease-in-out infinite; }}",
            f"@keyframes idle-{css_name} {{ 0%,100% {{ transform: rotate({rotation:.2f}deg) translateY(0) scaleY(1); }} {phase:.2f}% {{ transform: rotate({rotation + idle_rotation:.2f}deg) translateY({idle_y:.2f}px) scaleY({idle_scale_y:.4f}); }} }}",
        ])
        src = f"preview_parts/{name}.png"
        layers.append(f'<img class="part p-{css_name}" src="{html.escape(src)}" alt="{html.escape(name)}">')

    title = html.escape(layout.get("name", "Spine preview"))
    return "\n".join([
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        f"<title>{title} preview</title><style>{''.join(css)}</style></head>",
        f"<body><main id=\"stage\" aria-label=\"{title} Spine layout preview\"><div id=\"character\">",
        *layers,
        "</div></main></body></html>",
    ])


def make_preview(layout_path, out_dir):
    layout = read_layout(layout_path)
    output = Path(out_dir)
    if not (output / "preview_parts").is_dir():
        raise ValueError("preview_parts is missing; run spine_export.py first")
    missing = [part["name"] for part in layout.get("parts", []) if not (output / "preview_parts" / f"{part['name']}.png").is_file()]
    if missing:
        raise ValueError("missing exported preview parts: " + ", ".join(missing))
    html_path = output / "preview.html"
    html_path.write_text(html_for_layout(layout, output), encoding="utf-8")
    png_path = render_static_preview(layout, output)
    return html_path, png_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create an offline visual QA preview for a Spine layout")
    parser.add_argument("--layout", required=True, help="The layout JSON used by spine_export.py")
    parser.add_argument("--out", required=True, help="Existing Spine export directory")
    args = parser.parse_args(argv)
    try:
        html_path, png_path = make_preview(args.layout, args.out)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"html: {html_path}")
    print(f"image: {png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
