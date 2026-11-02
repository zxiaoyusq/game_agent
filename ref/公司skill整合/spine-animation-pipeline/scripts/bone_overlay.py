"""Draw a package's bones over its own setup pose, so the pivots can be checked.

The pivot is where a part rotates from, and it is invisible in a static render:
a bone at the wrong end of a limb looks fine until the limb moves. This renders
the package through the same renderer the previews use and stamps every bone's
origin on top, which turns "the rig looks wrong" into something you can point at.

    python bone_overlay.py --package out/hero.json --out bone_check.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import spine_runtime as runtime

COLORS = {"root": (255, 80, 80), "torso": (255, 190, 60), "head": (120, 220, 255),
          "collar": (170, 255, 120), "tail": (255, 130, 230)}


def bone_positions(document):
    bones = {bone["name"]: bone for bone in document.get("bones") or []}
    width = float(document["skeleton"].get("width") or 0)
    height = float(document["skeleton"].get("height") or 0)
    world = {}

    def place(name):
        if name in world:
            return world[name]
        bone = bones[name]
        parent = bone.get("parent")
        px, py = place(parent) if parent else (0.0, 0.0)
        # the document is y-up; the canvas is y-down
        world[name] = (px + float(bone.get("x") or 0.0), py + float(bone.get("y") or 0.0))
        return world[name]

    out = {}
    for name in bones:
        x, y = place(name)
        out[name] = (x + width / 2.0, height / 2.0 - y)
    return out, bones


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a package with its bones drawn on top")
    parser.add_argument("--package", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--scale", type=float, default=1.0, help="extra zoom for the output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    package = Path(args.package).resolve()
    document = json.loads(package.read_text(encoding="utf-8"))
    skeleton, atlas, _ = runtime.load_package(package)
    pose = skeleton.setup_pose()
    image = runtime.render(skeleton, atlas, pose).convert("RGBA")
    if args.scale != 1.0:
        image = image.resize((int(image.width * args.scale), int(image.height * args.scale)),
                             Image.LANCZOS)

    flat = Image.new("RGB", image.size, (255, 255, 255))
    flat.paste(image, (0, 0), image)
    draw = ImageDraw.Draw(flat)
    positions, bones = bone_positions(document)
    font = None
    for candidate in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, max(14, int(18 * args.scale)))
            break

    reported = []
    for name, (x, y) in positions.items():
        # skip the root: it sits at the canvas centre, not on any joint
        if name == "root":
            continue
        px, py = x * args.scale, y * args.scale
        parent = bones[name].get("parent")
        if parent and parent in positions:
            qx, qy = positions[parent]
            draw.line([(px, py), (qx * args.scale, qy * args.scale)], fill=(255, 120, 40, 200), width=2)
        color = COLORS.get(name, (230, 40, 40))
        size = max(6, int(8 * args.scale))
        draw.ellipse([px - size, py - size, px + size, py + size], outline=color, width=max(2, int(2 * args.scale)))
        draw.line([(px - size * 2, py), (px + size * 2, py)], fill=color, width=1)
        draw.line([(px, py - size * 2), (px, py + size * 2)], fill=color, width=1)
        if font:
            draw.text((px + size + 3, py - size - 10), name, fill=color, font=font)
        reported.append({"bone": name, "canvas": [round(x, 1), round(y, 1)],
                         "parent": parent})

    out_path = Path(args.out) if args.out else package.parent / "bone_check.png"
    flat.save(out_path)
    if args.json:
        print(json.dumps({"output": str(out_path), "bones": reported}, indent=2))
    else:
        for item in reported:
            print(f"  {item['bone']:<9} canvas {item['canvas'][0]:>7.1f},{item['canvas'][1]:>7.1f}  parent {item['parent']}")
        print(f"RESULT: OK - wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
