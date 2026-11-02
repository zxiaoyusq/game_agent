#!/usr/bin/env python3
"""Draw a numbered grid over an image so a vision model can read off part boxes.

    python make_grid.py --image reference.png --out grid.png --cells 20
    python make_grid.py --image reference.png --out grid.png --cells 10 --major 2

Why this exists: the agent driving this skill usually cannot see images at all,
and the vision bridge it does have is bad at absolute pixel coordinates but good
at reading a labelled grid. Every second (or fifth) line is drawn thick and
numbered, so "head: 3,1,17,9" is a reliable answer, and `position_parts.py
--boxes` turns those cell numbers straight into pixels.

Write the numbers the model reports into a JSON file:

    {
      "grid": 20,
      "image": "reference_flat.png",
      "parts": {"head": [3, 1, 17, 9], "torso": [2, 9, 18, 19],
                "collar": {"follow": "head", "anchor": [0.5, 1.0], "width": 580}}
    }

A plain list is a box in grid cells. A dict places a part relative to another
one, which is the reliable way to hang a small piece (a bell) off a bigger one
(a collar).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("ERROR: Pillow is required (pip install pillow)", file=sys.stderr)
    raise SystemExit(1)


def load_font(size):
    for candidate in ("C:/Windows/Fonts/arialbd.ttf",
                      "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_grid(image_path, out_path, cells=20, major=2, flatten=True):
    image = Image.open(image_path)
    if flatten and image.mode in ("RGBA", "LA", "P"):
        # A transparent PNG shown as-is can composite onto black, which hides
        # the art. A white card keeps the whole silhouette visible.
        rgba = image.convert("RGBA")
        card = Image.new("RGB", rgba.size, (255, 255, 255))
        card.paste(rgba, (0, 0), rgba)
        image = card
    else:
        image = image.convert("RGB")
    width, height = image.size
    board = image.copy()
    draw = ImageDraw.Draw(board)
    font = load_font(max(12, min(width, height) // 45))
    for index in range(cells + 1):
        x = int(index * width / cells)
        y = int(index * height / cells)
        thick = (index % major == 0)
        draw.line([(x, 0), (x, height)],
                  fill=(210, 0, 0) if thick else (255, 185, 185), width=2 if thick else 1)
        draw.line([(0, y), (width, y)],
                  fill=(0, 80, 220) if thick else (165, 195, 255), width=2 if thick else 1)
    for index in range(0, cells + 1, major):
        x = int(index * width / cells)
        y = int(index * height / cells)
        draw.text((min(x + 3, width - 24), 3), str(index), fill=(190, 0, 0), font=font)
        draw.text((3, min(y + 3, height - 20)), str(index), fill=(0, 60, 200), font=font)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out)
    return out, board.size, cells


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", required=True, help="reference art")
    parser.add_argument("--out", required=True, help="grid image to write")
    parser.add_argument("--cells", type=int, default=20,
                        help="cells per axis (20 gives 5%% per cell)")
    parser.add_argument("--major", type=int, default=2,
                        help="number every Nth line")
    parser.add_argument("--keep-alpha", action="store_true",
                        help="do not flatten transparency onto white")
    args = parser.parse_args(argv)
    out, size, cells = make_grid(args.image, args.out, cells=args.cells,
                                 major=args.major, flatten=not args.keep_alpha)
    print(f"{out}  {size[0]}x{size[1]}  {cells}x{cells} cells "
          f"({100.0 / cells:.1f}% each)")
    print("Ask the vision bridge for [col_start,row_start,col_end,row_end] cell numbers "
          "and save them under \"parts\" with \"grid\": %d" % cells)
    return 0


if __name__ == "__main__":
    sys.exit(main())
