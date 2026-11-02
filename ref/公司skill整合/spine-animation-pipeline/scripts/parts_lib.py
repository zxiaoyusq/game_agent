#!/usr/bin/env python3
"""Image helpers for turning generated art into Spine-ready transparent parts.

Everything here is deterministic and CLI-testable, because the agent driving
this skill may not be able to *see* the images it produces. Each check returns
numbers, so progress can be judged from text alone.

Requires: Pillow (required), numpy (recommended).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

try:  # numpy makes the passes fast; the fallbacks below still work without it
    import numpy as np
except Exception:  # pragma: no cover - numpy is present on the target machine
    np = None


# ── loading / saving ────────────────────────────────────────────────────────
def load_rgba(path):
    with Image.open(path) as source:
        return source.convert("RGBA").copy()


def to_pixels(image):
    """RGBA pixels as a list of [r, g, b, a]; avoids the deprecated getdata()."""
    rgba = image.convert("RGBA")
    if np is not None:
        return np.asarray(rgba).reshape(-1, 4).tolist()
    return [list(pixel) for pixel in rgba.getdata()]


def save_png(image, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    return path


# ── chroma key ──────────────────────────────────────────────────────────────
def chroma_key(image, key=(0, 255, 0), inner=60.0, outer=150.0):
    """Make pixels close to `key` transparent.

    `inner` is the radius fully removed, `outer` the radius fully kept; the band
    between them keeps a soft alpha ramp so anti-aliased art does not get a
    stair-stepped outline.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    if np is None:
        return _chroma_key_python(image, key, inner, outer)

    data = np.asarray(image).astype(np.float32)
    rgb = data[:, :, :3]
    key_array = np.array(key, dtype=np.float32)
    distance = np.sqrt(((rgb - key_array) ** 2).sum(axis=2))

    alpha = np.clip((distance - inner) / max(outer - inner, 1e-6), 0.0, 1.0)
    # Fully transparent pixels keep alpha 0; everything else keeps the smaller
    # of the existing alpha and the key-derived alpha.
    original = data[:, :, 3] / 255.0
    combined = np.minimum(original, alpha)
    out = data.copy()
    out[:, :, 3] = combined * 255.0
    # Neutralise the key colour where the pixel is mostly key, so a residual
    # green cast cannot survive the later edge decontamination.
    green_cast = np.clip(1.0 - combined * 3.0, 0.0, 1.0)[:, :, None]
    out[:, :, :3] = out[:, :, :3] * (1 - green_cast) + data[:, :, :3] * green_cast
    return Image.fromarray(out.astype("uint8"), "RGBA")


def _chroma_key_python(image, key, inner, outer):
    pixels = image.load()
    width, height = image.size
    out = Image.new("RGBA", (width, height))
    target = out.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            distance = math.dist((r, g, b), key)
            factor = max(0.0, min(1.0, (distance - inner) / max(outer - inner, 1e-6)))
            target[x, y] = (r, g, b, int(round(a * factor)))
    return out


def remove_corner_background(image, tolerance=30, from_corners=80):
    """Flood-fill the connected background from the image border.

    The GPT-Image tool returns a solid background; this replaces the older
    `postprocess.py --remove-bg` behaviour, but on every corner at once so a
    single stray pixel cannot eat the subject.
    """
    if np is None:
        return image
    rgba = image.convert("RGBA")
    data = np.asarray(rgba).astype(np.int16)
    height, width = data.shape[:2]
    seed_rgb = []
    step = max(1, min(width, height) // 64)
    for cx in range(0, width, step):
        for cy in (0, height - 1):
            seed_rgb.append(data[cy, cx, :3])
    for cy in range(0, height, step):
        for cx in (0, width - 1):
            seed_rgb.append(data[cy, cx, :3])
    if not seed_rgb:
        return rgba
    seeds = np.array(seed_rgb)
    # Keep only the dominant border colour so a logo in one corner is ignored.
    median = np.median(seeds, axis=0)
    candidate = np.sqrt(((data[:, :, :3] - median) ** 2).sum(axis=2)) <= tolerance
    # Connected fill from the border only (4-neighbour BFS over a boolean grid).
    mask = np.zeros((height, width), dtype=bool)
    stack = []
    for x in range(width):
        for y in (0, height - 1):
            if candidate[y, x] and not mask[y, x]:
                mask[y, x] = True
                stack.append((y, x))
    for y in range(height):
        for x in (0, width - 1):
            if candidate[y, x] and not mask[y, x]:
                mask[y, x] = True
                stack.append((y, x))
    while stack:
        y, x = stack.pop()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < height and 0 <= nx < width and candidate[ny, nx] and not mask[ny, nx]:
                mask[ny, nx] = True
                stack.append((ny, nx))
    out = np.asarray(rgba).copy()
    out[:, :, 3] = np.where(mask, 0, out[:, :, 3])
    return Image.fromarray(out, "RGBA")


# ── edge hygiene ────────────────────────────────────────────────────────────
def edge_band(image, radius=2):
    """Visible pixels within `radius` px of transparency (the matte zone)."""
    if np is None:
        return None
    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba)[:, :, 3]
    transparent = alpha < 16
    grown = transparent.copy()
    for _ in range(max(1, int(radius))):
        shifted = grown.copy()
        shifted[1:, :] |= grown[:-1, :]
        shifted[:-1, :] |= grown[1:, :]
        shifted[:, 1:] |= grown[:, :-1]
        shifted[:, :-1] |= grown[:, 1:]
        grown = shifted
    return grown & ~transparent


def decontaminate_edges(image, passes=3, boundary_radius=2):
    """Pull interior colour into the matte zone; keep alpha exactly.

    Generated cut-outs blend the art into the background it was drawn on, so the
    outermost pixels are a mix of art and green screen. Chroma keying alone
    leaves them looking green, because a pixel that is 60 % art / 40 % green is
    "far from pure green" and keeps full alpha. Two things are therefore
    replaced:

    * partially transparent pixels (the classic halo), and
    * fully opaque pixels lying within `boundary_radius` px of transparency
      (the fringe a vision check sees as a green outline).

    Colour is filled in from the nearest clean interior pixels, alpha is never
    touched.
    """
    if np is None:
        return image
    rgba = image.convert("RGBA")
    data = np.asarray(rgba).astype(np.float32)
    alpha = data[:, :, 3]
    if alpha.max() == 0:
        return rgba

    band = edge_band(rgba, boundary_radius)
    if band is None:
        band = (alpha > 0) & (alpha < 250)
    known = (alpha >= 250) & ~band
    if not known.any():
        known = alpha >= 250
    if not known.any():
        return rgba
    unknown = (alpha > 0) & ~known
    if not unknown.any():
        return rgba

    rgb = data[:, :, :3].copy()
    filled = known.copy()
    for _ in range(max(1, passes)):
        if not unknown.any():
            break
        blurred, weight = _box_blur_rgb(rgb * (filled[:, :, None]), filled.astype(np.float32), 1)
        take = unknown & (weight > 0)
        rgb[take] = blurred[take] / weight[take][:, None]
        filled |= take
        unknown &= ~take
    out = data.copy()
    out[:, :, :3] = rgb
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGBA")


def _erode_mask(mask, iterations=1):
    """Binary erosion that pads instead of wrapping.

    np.roll looks like a cheap erosion and is a trap: it wraps the first row and
    last column around to the opposite side, so the outermost ring of an image
    is classified as interior. The border ring is exactly where chroma key
    residue lives, so a wrapping erosion silently skips the one place that
    needed cleaning.
    """
    out = mask
    for _ in range(max(1, int(iterations))):
        pad = np.pad(out, 1, mode="constant", constant_values=False)
        out = (pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2]
               & pad[1:-1, 2:] & pad[1:-1, 1:-1])
    return out


def despill_edges(image, band=3, threshold=12, kill=40):
    """Strip green chroma-key spill from a cut-out.

    Segmentation commonly leaves the outermost ring of pixels with a green cast
    at full alpha - on a soft-shaded render that is a whole 1px green column
    down the edge of the part, invisible at fit-to-screen and obvious the moment
    anyone zooms in. Two rules, both safe because a chroma-keyed subject is by
    definition not the colour of the key:

    * a pixel whose green leads red and blue by more than `kill` is background
      bleed, wherever it sits, and becomes transparent;
    * any other green-leaning pixel within `band` pixels of the edge has its
      green clamped to the stronger of red and blue.
    """
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    r, g, b, a = (rgba[..., i].astype(np.int16) for i in range(4))
    lead = g - np.maximum(r, b)
    near_edge = (a > 0) & ~_erode_mask(a > 0, band)
    killed = (lead > kill) & (a > 0)
    rgba[..., 3] = np.where(killed, 0, a).astype(np.uint8)
    clamped = (lead > threshold) & (a > 0) & ~killed & (near_edge | (lead > kill))
    rgba[..., 1] = np.where(clamped, np.maximum(r, b), g).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def fringe_score(image, radius=2):
    """How far the matte zone's colour sits from the part's interior colour.

    A high value means a visible halo (green or white) that alpha statistics
    alone cannot detect, because those pixels are fully opaque.
    """
    if np is None:
        return None
    rgba = image.convert("RGBA")
    data = np.asarray(rgba).astype(np.float32)
    alpha = data[:, :, 3]
    band = edge_band(rgba, radius)
    if band is None or not band.any():
        return 0.0
    interior = (alpha >= 250)
    if not interior.any():
        return 0.0
    band_colour = data[:, :, :3][band].mean(axis=0)
    interior_colour = data[:, :, :3][interior].mean(axis=0)
    return float(np.abs(band_colour - interior_colour).mean() / 255.0)


def _box_blur_rgb(values, weights, radius):
    """3x3 weighted neighbour sum (separable, edge clamped)."""
    padded_values = np.pad(values, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    padded_weights = np.pad(weights, ((radius, radius), (radius, radius)), mode="edge")
    accum_values = np.zeros_like(values)
    accum_weights = np.zeros_like(weights)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            accum_values += padded_values[radius + dy:radius + dy + values.shape[0],
                                          radius + dx:radius + dx + values.shape[1], :]
            accum_weights += padded_weights[radius + dy:radius + dy + values.shape[0],
                                            radius + dx:radius + dx + values.shape[1]]
    return accum_values, accum_weights


def keep_largest_component(image, min_area_ratio=0.01, max_components=1):
    """Drop speckles left over from background removal."""
    if np is None:
        return image
    rgba = image.convert("RGBA")
    data = np.asarray(rgba)
    alpha = data[:, :, 3] > 8
    if not alpha.any():
        return rgba
    height, width = alpha.shape
    labels = np.zeros((height, width), dtype=np.int32)
    current = 0
    areas = []
    for start_y in range(height):
        for start_x in range(width):
            if not alpha[start_y, start_x] or labels[start_y, start_x]:
                continue
            current += 1
            stack = [(start_y, start_x)]
            labels[start_y, start_x] = current
            area = 0
            while stack:
                y, x = stack.pop()
                area += 1
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < height and 0 <= nx < width and alpha[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            areas.append((area, current))
    if len(areas) <= max_components:
        return rgba
    areas.sort(reverse=True)
    keep = {label for _, label in areas[:max_components]}
    mask = np.isin(labels, list(keep))
    out = data.copy()
    out[:, :, 3] = np.where(mask, out[:, :, 3], 0)
    return Image.fromarray(out, "RGBA")


def strip_solid_background(image, tolerance=18):
    """Erase a uniform backdrop (white, grey, green) so silhouettes are honest.

    Reference art is usually drawn on a flat colour. Without this, "does the
    composite match the reference" would compare against a full canvas instead
    of the character, and every overlap score would be meaningless.
    """
    rgba = image.convert("RGBA")
    corners = [rgba.getpixel((0, 0)), rgba.getpixel((rgba.width - 1, 0)),
               rgba.getpixel((0, rgba.height - 1)),
               rgba.getpixel((rgba.width - 1, rgba.height - 1))]
    opaque = [corner for corner in corners if corner[3] > 8]
    if not opaque or len(opaque) < 3:
        return rgba
    base = opaque[0]
    if any(max(abs(corner[i] - base[i]) for i in range(3)) > tolerance for corner in opaque):
        return rgba  # corners disagree: assume there is no flat backdrop
    data = to_pixels(rgba)
    cleaned = [
        (pixel[0], pixel[1], pixel[2], 0)
        if pixel[3] > 8 and max(abs(pixel[i] - base[i]) for i in range(3)) <= tolerance
        else pixel
        for pixel in data
    ]
    out = Image.new("RGBA", rgba.size)
    # putdata wants tuples; to_pixels hands back lists.
    out.putdata([tuple(pixel) for pixel in cleaned])
    return out


def trim_to_alpha(image, padding=0):
    """Crop to the alpha bounding box; returns (image, bbox)."""
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("image has no opaque pixels")
    if padding:
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(rgba.width, bbox[2] + padding)
        bottom = min(rgba.height, bbox[3] + padding)
        bbox = (left, top, right, bottom)
    return rgba.crop(bbox).copy(), bbox


# ── reporting ───────────────────────────────────────────────────────────────
def alpha_report(image, key=(0, 255, 0)):
    """Numeric description of a part, used by the pipeline's gates."""
    rgba = image.convert("RGBA")
    if np is None:
        alpha = rgba.getchannel("A")
        histogram = alpha.histogram()
        total = rgba.width * rgba.height
        transparent = sum(histogram[:16])
        opaque = sum(histogram[250:])
        return {
            "size": [rgba.width, rgba.height],
            "transparent_ratio": round(transparent / total, 4),
            "opaque_ratio": round(opaque / total, 4),
            "has_transparent": transparent > 0,
            "has_opaque": opaque > 0,
            "chroma_residue": None,
            "edge_alpha_ratio": None,
            "fringe_distance": None,
        }
    data = np.asarray(rgba).astype(np.float32)
    alpha = data[:, :, 3]
    total = alpha.size
    transparent = int((alpha < 16).sum())
    opaque = int((alpha >= 250).sum())
    partial = int(((alpha >= 16) & (alpha < 250)).sum())
    rgb = data[:, :, :3]
    distance = np.sqrt(((rgb - np.array(key, dtype=np.float32)) ** 2).sum(axis=2))
    visible = alpha > 0
    residue = int(((distance < 90) & visible).sum())
    fringe = fringe_score(rgba)
    return {
        "size": [rgba.width, rgba.height],
        "transparent_ratio": round(transparent / total, 4),
        "opaque_ratio": round(opaque / total, 4),
        "edge_alpha_ratio": round(partial / total, 4),
        "has_transparent": transparent > 0,
        "has_opaque": opaque > 0,
        "chroma_residue": round(residue / max(1, int(visible.sum())), 4),
        "fringe_distance": None if fringe is None else round(fringe, 4),
    }


def validate_part(path, max_chroma_residue=0.02, min_opaque=0.01, max_fringe=0.16):
    """Return (ok, report, problems) for one part file."""
    problems = []
    try:
        image = load_rgba(path)
    except Exception as error:
        return False, {}, [f"cannot open {path}: {error}"]
    report = alpha_report(image)
    if not report.get("has_transparent"):
        problems.append("part has no transparent pixels (chroma key did not run?)")
    if not report.get("has_opaque"):
        problems.append("part has no opaque pixels (empty cut-out)")
    if report.get("opaque_ratio", 0) < min_opaque:
        problems.append(f"opaque area {report.get('opaque_ratio')} below {min_opaque}")
    residue = report.get("chroma_residue")
    if residue is not None and residue > max_chroma_residue:
        problems.append(f"chroma residue {residue} above {max_chroma_residue} (re-run decontamination)")
    fringe = report.get("fringe_distance")
    if fringe is not None and fringe > max_fringe:
        problems.append(
            f"edge colour differs from the interior by {fringe:.3f} of full scale "
            f"(limit {max_fringe}); the cut-out has a visible halo - re-run chroma key "
            f"with decontamination, or tighten --inner/--outer")
    report["path"] = str(path)
    report["ok"] = not problems
    report["problems"] = problems
    return not problems, report, problems


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def filmstrip(images, path, background=(32, 34, 40, 255), gap=8, columns=4):
    """Tile frames into one PNG so a single vision call can review them all."""
    if not images:
        raise ValueError("filmstrip needs at least one frame")
    columns = max(1, min(columns, len(images)))
    rows = math.ceil(len(images) / columns)
    cell_w = max(image.width for image in images)
    cell_h = max(image.height for image in images)
    sheet = Image.new("RGBA", (columns * cell_w + (columns + 1) * gap,
                               rows * cell_h + (rows + 1) * gap), background)
    for index, image in enumerate(images):
        row, column = divmod(index, columns)
        x = gap + column * (cell_w + gap) + (cell_w - image.width) // 2
        y = gap + row * (cell_h + gap) + (cell_h - image.height) // 2
        sheet.alpha_composite(image.convert("RGBA"), (x, y))
    save_png(sheet, path)
    return path


# ── self description ────────────────────────────────────────────────────────
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="Part image tools: chroma key, edge decontamination, alpha metrics")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", nargs="+", metavar="PNG",
                       help="report alpha/fringe metrics and flag halo artefacts")
    group.add_argument("--chroma", metavar="PNG", help="green screen -> transparent PNG")
    group.add_argument("--filmstrip", nargs="+", metavar="PNG")
    parser.add_argument("--out", default=None, help="output file for --chroma/--filmstrip")
    parser.add_argument("--key", default="0,255,0", help="chroma key colour (r,g,b)")
    parser.add_argument("--inner", type=float, default=40.0)
    parser.add_argument("--outer", type=float, default=150.0)
    parser.add_argument("--max-fringe", type=float, default=0.16)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        reports = []
        failed = []
        # Accept directories as well as files: naming the parts folder is the
        # obvious thing to do, and it used to be opened as if it were an image.
        targets = []
        for item in args.check:
            if Path(item).is_dir():
                targets.extend(sorted(Path(item).glob("*.png")))
            else:
                targets.append(Path(item))
        if not targets:
            print("no part images found", file=sys.stderr)
            return 1
        args.check = targets
        for item in args.check:
            ok, report, problems = validate_part(item, max_fringe=args.max_fringe)
            report["file"] = str(item)
            reports.append(report)
            if not ok:
                failed.append((item, problems))
        if args.json:
            print(json.dumps({"ok": not failed, "reports": reports}, ensure_ascii=False, indent=2))
        else:
            print(f"{'file':<24} {'opaque':>7} {'edge':>7} {'residue':>8} {'fringe':>7}  status")
            for report in reports:
                name = Path(report.get("file", "?")).name
                if "opaque_ratio" not in report:
                    # validate_part could not read it; say so instead of dying.
                    print(f"{name:<24} {'-':>7} {'-':>7} {'-':>8} {'-':>7}  UNREADABLE")
                    continue
                print(f"{name:<24} {report['opaque_ratio']:>7} "
                      f"{report['edge_alpha_ratio']:>7} {report['chroma_residue']:>8} "
                      f"{report['fringe_distance']:>7}  {'ok' if report['ok'] else 'FAIL'}")
            for item, problems in failed:
                print(chr(10) + Path(item).name + ":")
                for problem in problems:
                    print(f"  - {problem}")
            print(chr(10) + f"{len(reports) - len(failed)}/{len(reports)} parts clean")
        return 0 if not failed else 2

    if args.chroma:
        key = tuple(int(part) for part in args.key.split(","))
        image = load_rgba(args.chroma)
        keyed = chroma_key(image, key=key, inner=args.inner, outer=args.outer)
        keyed = keep_largest_component(keyed)
        try:
            trimmed, _ = trim_to_alpha(keyed)
        except ValueError as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        cleaned = decontaminate_edges(trimmed, boundary_radius=3)
        out = Path(args.out) if args.out else Path(args.chroma).with_name(
            Path(args.chroma).stem + "-keyed.png")
        save_png(cleaned, out)
        report = alpha_report(cleaned)
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json
              else f"{out}  {report}")
        return 0

    out = Path(args.out) if args.out else Path("filmstrip.png")
    strip = filmstrip([load_rgba(item) for item in args.filmstrip])
    save_png(strip, out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
