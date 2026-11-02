#!/usr/bin/env python3
"""Find where each transparent part sits in a reference image, then write a layout.

This is the upstream (GenielabsOpenSource/spine-animation-ai) SIFT + RANSAC idea,
kept because it is the one part of that pipeline that is pure maths: no model,
no quota, no opinion. What changed:

* the output is this skill's layout schema (pivot-accurate, canvas-centre y-up),
  not the upstream "layout.json" with its own bone conventions;
* a missing cv2 or a part that fails to match no longer aborts the run -- the
  part is placed by template matching, then by a centred fallback, and the
  layout records which method won so the agent can see what to trust;
* it reports a numeric positioning score (silhouette overlap of the assembled
  composite against the reference) so "did it work" is a number, not a guess.

    python position_parts.py --parts parts/ --reference reference.png --out layout.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import parts_lib
import rig_rules

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


# ── helpers ─────────────────────────────────────────────────────────────────
def mask_of(image):
    alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
    return alpha > 24


def apply_similarity(matrix, points):
    """Apply a 2x3 OpenCV similarity matrix to an (N,2) array of x/y points."""
    data = np.asarray(points, dtype=np.float32)
    ones = np.ones((data.shape[0], 1), dtype=np.float32)
    homogeneous = np.hstack([data, ones])
    return homogeneous @ matrix.T


def part_pivot_pixels(image, pivot):
    """Pivot location inside the part image, in pixels."""
    return (pivot[0] * image.width, pivot[1] * image.height)


# ── matching ────────────────────────────────────────────────────────────────
def sift_match(part, reference_gray, reference_keypoints, reference_descriptors,
               ratio=0.8, min_matches=4):
    if cv2 is None:
        return None, "opencv not installed"
    data = np.asarray(part.convert("RGBA"))
    alpha = data[:, :, 3]
    gray = cv2.cvtColor(data[:, :, :3], cv2.COLOR_RGB2GRAY)
    mask = (alpha > 24).astype(np.uint8) * 255
    if mask.sum() == 0:
        return None, "part has no visible pixels"
    detector = cv2.SIFT_create(contrastThreshold=0.02, edgeThreshold=20)
    keypoints, descriptors = detector.detectAndCompute(gray, mask)
    if descriptors is None or len(keypoints) < min_matches:
        return None, f"only {0 if descriptors is None else len(keypoints)} keypoints"

    matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
    matches = matcher.knnMatch(descriptors, reference_descriptors, k=2)
    good = [first for first, second in matches if first.distance < ratio * second.distance]
    if len(good) < min_matches:
        return None, f"only {len(good)} good matches"

    source = np.float32([keypoints[item.queryIdx].pt for item in good]).reshape(-1, 1, 2)
    target = np.float32([reference_keypoints[item.trainIdx].pt for item in good]).reshape(-1, 1, 2)
    matrix, inliers = cv2.estimateAffinePartial2D(source, target, method=cv2.RANSAC,
                                                  ransacReprojThreshold=6.0, maxIters=4000,
                                                  confidence=0.995)
    if matrix is None:
        return None, "RANSAC found no consistent transform"
    inlier_count = int(inliers.sum()) if inliers is not None else 0
    if inlier_count < min_matches:
        return None, f"only {inlier_count} inliers"
    scale = float(np.hypot(matrix[0, 0], matrix[1, 0]))
    rotation = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))
    return {"matrix": matrix, "inliers": inlier_count, "scale": scale,
            "rotation": rotation, "method": "sift"}, "ok"


def template_match(part, reference_rgb, reference_mask, scales=None):
    """Fallback for small or featureless parts."""
    if cv2 is None:
        return None, "opencv not installed"
    part_data = np.asarray(part.convert("RGBA"))
    part_rgb = part_data[:, :, :3]
    part_mask = (part_data[:, :, 3] > 24).astype(np.float32)
    if part_mask.sum() < 16:
        return None, "part is too small to template match"
    reference = reference_rgb.astype(np.float32)
    if scales is None:
        scales = [0.5, 0.6, 0.75, 0.9, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0, 2.5]
    best = None
    for scale in scales:
        width = max(4, int(round(part_rgb.shape[1] * scale)))
        height = max(4, int(round(part_rgb.shape[0] * scale)))
        if width >= reference.shape[1] or height >= reference.shape[0]:
            continue
        resized_rgb = cv2.resize(part_rgb, (width, height), interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(part_mask, (width, height), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(reference, resized_rgb.astype(np.float32), cv2.TM_SQDIFF,
                                   mask=resized_mask.astype(np.float32))
        result = np.nan_to_num(result, nan=np.inf, posinf=np.inf)
        # Penalise placements that hang outside the reference.
        minimum, _, location, _ = cv2.minMaxLoc(result)
        if minimum == np.inf:
            continue
        score = -minimum / float(resized_mask.sum())
        if best is None or score > best["score"]:
            best = {"top_left": location, "scale": scale, "score": score, "size": (width, height)}
    if best is None:
        return None, "no template placement fit inside the reference"
    x, y = best["top_left"]
    matrix = np.array([[best["scale"], 0.0, x], [0.0, best["scale"], y]], dtype=np.float32)
    return {"matrix": matrix, "inliers": 0, "scale": best["scale"], "rotation": 0.0,
            "method": "template", "score": round(best["score"], 4)}, "ok"


def side_of(name):
    """'l' / 'r' for parts named ..._l / ..._r, else None.

    A mirror-symmetric pair (two ears, two legs) fits a region about as well on
    either side, so the name is the only thing that can break the tie.
    """
    stem = str(name).lower()
    if re.search(r"[_.\-]l$", stem):
        return "l"
    if re.search(r"[_.\-]r$", stem):
        return "r"
    return None


def place_in_region(part, reference_rgb, reference_mask, region, steps=14,
                    spread=1.7, side=None, side_bonus=0.02):
    """Place a part inside a known region of the reference art.

    A silhouette alone cannot say which piece of the character a part is - every
    sub-shape "fits" a big blob equally well - so the search is confined to the
    region the caller supplies (from a part-box map, or a previous estimate) and
    ranked by two independent terms: how much of the part lands inside the
    character's silhouette, and how well its colours match the art underneath.
    The colour term is what separates a brown collar from a tan chest; the
    silhouette term is what keeps a part from floating in empty space or
    hanging off the outline. Both are correlations, so matchTemplate does the
    whole sweep at once.
    """
    if cv2 is None:
        return None, "opencv not installed"
    data = np.asarray(part.convert("RGBA"))
    part_alpha = (data[:, :, 3] > 96).astype(np.uint8)
    part_rgb = data[:, :, :3].astype(np.float32)
    if int(part_alpha.sum()) < 24:
        return None, "part has too few opaque pixels to place"

    target = (reference_mask > 0).astype(np.float32)
    art = reference_rgb.astype(np.float32)
    height, width = target.shape
    x0, y0, x1, y1 = (int(round(v)) for v in region)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, max(x1, x0 + 8)), min(height, max(y1, y0 + 8))

    box_w, box_h = x1 - x0, y1 - y0
    hint = min(box_w / max(1, part.width), box_h / max(1, part.height))
    if hint <= 0:
        return None, "empty region"

    best = None
    for index in range(steps):
        scale = hint * (spread ** (index / max(1, steps - 1)) * spread ** -0.5)
        part_w = int(round(part.width * scale))
        part_h = int(round(part.height * scale))
        if part_w < 4 or part_h < 4 or part_w >= width or part_h >= height:
            continue
        probe_alpha = cv2.resize(part_alpha, (part_w, part_h), interpolation=cv2.INTER_AREA)
        probe_alpha = (probe_alpha > 0.5).astype(np.float32)
        area = float(probe_alpha.sum())
        if area < 12:
            continue
        probe_rgb = cv2.resize(part_rgb, (part_w, part_h), interpolation=cv2.INTER_AREA)

        inside = cv2.matchTemplate(target, probe_alpha, cv2.TM_CCORR) / area
        ssd = cv2.matchTemplate(art, probe_rgb, cv2.TM_SQDIFF,
                                mask=probe_alpha.astype(np.float32))
        ssd = np.nan_to_num(ssd, nan=1e9, posinf=1e9) / (area * 3.0)
        # 70 is roughly the "same colour family" distance for flat cartoon art.
        colour = np.exp(-ssd / (70.0 ** 2))

        score = inside + 0.9 * colour
        if side:
            centres = (np.arange(score.shape[1])[None, :] + part_w / 2.0) / width
            score = score + side_bonus * ((centres < 0.5) if side == "l" else (centres > 0.5))

        # Confine the search to the region the caller gave us.
        allowed = np.zeros_like(score, dtype=bool)
        allowed[max(0, y0):min(score.shape[0], y1),
                max(0, x0):min(score.shape[1], x1)] = True
        masked = np.where(allowed, score, -np.inf)
        flat = int(np.argmax(masked))
        row, column = divmod(flat, masked.shape[1])
        value = float(masked[row, column])
        if not np.isfinite(value):
            continue
        if best is None or value > best["score"]:
            best = {"score": value, "scale": scale, "x": column, "y": row,
                    "inside": float(inside[row, column]),
                    "colour": float(colour[row, column])}

    if best is None:
        return None, "no scale of this part fits inside the given region"
    matrix = np.array([[best["scale"], 0.0, best["x"]],
                       [0.0, best["scale"], best["y"]]], dtype=np.float32)
    return ({"matrix": matrix, "inliers": 0, "scale": best["scale"], "rotation": 0.0,
             "method": "region-fit", "score": round(best["score"], 4)},
            f"region fit {best['score']:.3f} (inside {best['inside']:.2f}, "
            f"colour {best['colour']:.2f}) at scale {best['scale']:.3f}")


# ── z order ─────────────────────────────────────────────────────────────────
def occlusion_z_order(placements, reference_rgb, reference_size, defaults=None,
                      margin=0.06):
    """Order the parts back-to-front from pairwise occlusion evidence.

    Each overlapping pair votes: whichever part's colours match the reference
    better across the shared pixels is the one that must be in FRONT. Counting
    wins per part (as this used to) is wrong - the torso overlaps everything and
    collected the most wins, so it was drawn on top of the head. The pairwise
    verdicts are a partial order, so they are topologically sorted with the
    anatomical defaults breaking ties.
    """
    names = list(placements)
    beats = {name: set() for name in names}
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            overlap = placements[first]["mask"] & placements[second]["mask"]
            count = int(overlap.sum())
            if count < 12:
                continue
            reference = reference_rgb[overlap].astype(np.int16)
            error_first = float(np.abs(placements[first]["colors"][overlap].astype(np.int16)
                                       - reference).mean())
            error_second = float(np.abs(placements[second]["colors"][overlap].astype(np.int16)
                                        - reference).mean())
            worst = max(error_first, error_second, 1e-6)
            if abs(error_first - error_second) / worst < margin:
                continue                      # too close to call, leave it to anatomy
            winner, loser = ((first, second) if error_first < error_second
                             else (second, first))
            beats[winner].add(loser)

    defaults = defaults or default_order_scores(names)
    ordered = []
    remaining = set(names)
    while remaining:
        ready = [name for name in remaining
                 if not any(name in beats[other] for other in remaining if other != name)]
        if not ready:                          # a cycle: fall back to anatomy
            ready = list(remaining)
        ready.sort(key=lambda name: defaults.get(name, 0))
        pick = ready[0]
        ordered.append(pick)
        remaining.discard(pick)
    return ordered, beats


def default_order_scores(names):
    return {name: rig_rules.draw_order_for(name) for name in names}


# ── driver ──────────────────────────────────────────────────────────────────
def load_parts(parts_arg):
    path = Path(parts_arg)
    files = []
    if path.is_dir():
        files = sorted(item for item in path.iterdir()
                       if item.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"))
    elif path.is_file() and path.suffix.lower() == ".json":
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entries = manifest.get("parts", manifest)
        for entry in entries:
            if isinstance(entry, str):
                files.append(Path(entry))
            elif isinstance(entry, dict) and entry.get("file"):
                files.append(Path(entry["file"]))
    else:
        raise ValueError(f"--parts must be a directory or a manifest JSON: {parts_arg}")
    if not files:
        raise ValueError(f"no part images found in {parts_arg}")
    return files


def load_boxes(path, width, height):
    """Read a part-box map: grid cells or pixels, keyed by part name.

    Boxes come from a vision model reading a numbered grid, which is the only
    reliable way for a text-only agent to learn *which region* of the art a part
    belongs to. They only have to be roughly right - the region search refines
    the exact fit inside them.
    """
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    boxes = {"grid": float(data.get("grid") or 0), "parts": dict(data.get("parts") or {})}
    usable = {}
    for name, spec in boxes["parts"].items():
        if isinstance(spec, dict):
            usable[str(name)] = spec
        elif isinstance(spec, (list, tuple)) and len(spec) == 4:
            usable[str(name)] = spec
    boxes["parts"] = usable
    return boxes


def placement_bbox(matrix, part):
    """Canvas-space box (x0, y0, x1, y1) of a placed part, corners included."""
    scale = float(np.hypot(matrix[0, 0], matrix[1, 0]))
    corners = apply_similarity(matrix, np.array([[0, 0], [part.width, 0],
                                                 [0, part.height],
                                                 [part.width, part.height]],
                                                dtype=np.float32))
    return (float(corners[:, 0].min()), float(corners[:, 1].min()),
            float(corners[:, 0].max()), float(corners[:, 1].max()))


def resolve_region(spec, boxes, canvas, placements):
    """Turn a box spec into a pixel region.

    A plain list of four numbers is a box. A dict instead describes a part that
    hangs off another one - the collar sits at the base of the head, the bell
    dangles from the collar - which is how a small part is placed reliably:
    colour and silhouette alone cannot tell a gold bell from a gold-ish paw, but
    "the collar's front, just below" is not ambiguous.
    """
    width, height = canvas["width"], canvas["height"]
    if isinstance(spec, (list, tuple)) and len(spec) == 4:
        if boxes.get("grid"):
            cells = float(boxes["grid"])
            x0, y0, x1, y1 = (float(v) for v in spec)
            spec = (x0 / cells * width, y0 / cells * height,
                    x1 / cells * width, y1 / cells * height)
        x0, y0, x1, y1 = (float(v) for v in spec)
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    if isinstance(spec, dict) and spec.get("px"):
        # a pixel box: cutting parts out of the reference yields exact pixels,
        # and going back through grid cells would round them off again
        return tuple(float(v) for v in spec["px"])
    if isinstance(spec, dict) and spec.get("box"):
        # a dict spec can carry a plain box plus overrides (draw_order, pivot)
        return resolve_region([float(v) for v in spec["box"]], boxes, canvas, placements)
    if isinstance(spec, dict) and spec.get("follow"):
        parent = placements.get(str(spec["follow"]))
        if not parent:
            return None
        pb = parent["bbox"]
        anchor_x, anchor_y = spec.get("anchor", [0.5, 1.0])
        point_x = pb[0] + float(anchor_x) * (pb[2] - pb[0])
        point_y = pb[1] + float(anchor_y) * (pb[3] - pb[1])
        size = spec.get("size") or [0.55 * (pb[2] - pb[0]), 0.30 * (pb[3] - pb[1])]
        offset_x, offset_y = spec.get("offset", [0.0, 0.0])
        centre_x = point_x + float(offset_x)
        centre_y = point_y + float(offset_y)
        half_w, half_h = float(size[0]) / 2.0, float(size[1]) / 2.0
        return (centre_x - half_w, centre_y - half_h, centre_x + half_w, centre_y + half_h)
    return None


def follow_matrix(spec, part, pivot, boxes, canvas, placements):
    """Exact placement for a part that hangs off another part.

    Searching for a small attached piece by colour does not work - a gold bell
    matches the tan fur better than it matches the collar it hangs from - so a
    spec that names a `width` (or `scale`) is placed by its pivot at the
    parent's anchor point plus the offset, with no search at all. The pivot is
    the rig's own attachment point (a bell's pivot is its loop), which is what
    makes "hang from the collar" a single line of geometry.
    """
    if not isinstance(spec, dict) or not spec.get("follow"):
        return None
    parent = placements.get(str(spec["follow"]))
    if not parent:
        return None
    if not (spec.get("width") or spec.get("scale")):
        return None
    pb = parent["bbox"]
    anchor_x, anchor_y = spec.get("anchor", [0.5, 1.0])
    point_x = pb[0] + float(anchor_x) * (pb[2] - pb[0])
    point_y = pb[1] + float(anchor_y) * (pb[3] - pb[1])
    offset_x, offset_y = spec.get("offset", [0.0, 0.0])
    target_x, target_y = point_x + float(offset_x), point_y + float(offset_y)
    if spec.get("width"):
        scale = float(spec["width"]) / max(1.0, float(part.width))
    else:
        scale = float(spec["scale"])
    pivot_x, pivot_y = part_pivot_pixels(part, pivot)
    matrix = np.array([[scale, 0.0, target_x - scale * pivot_x],
                       [0.0, scale, target_y - scale * pivot_y]], dtype=np.float32)
    return matrix, scale


def box_matrix(region, part):
    """Place a part inside a box: uniform scale, centred, aspect preserved.

    When the box comes from someone looking at the artwork, matching its
    nesting is worth more than any pixel-level score: the head lands exactly
    where the head is and, crucially, its bottom edge meets the top of the
    torso. Searching for the best colour fit instead pulled the parts to
    opposite edges of their boxes and left an 80px hole where the neck is.
    """
    box_w = max(4.0, region[2] - region[0])
    box_h = max(4.0, region[3] - region[1])
    scale = min(box_w / max(1, part.width), box_h / max(1, part.height))
    left = region[0] + (box_w - part.width * scale) / 2.0
    top = region[1] + (box_h - part.height * scale) / 2.0
    return np.array([[scale, 0.0, left], [0.0, scale, top]], dtype=np.float32), scale


def conform_to_box(part, region, max_stretch=2.5):
    """Reshape a generated part to the aspect ratio of its box.

    A generated part is drawn at whatever proportions the image model felt like:
    a leg came back 2.7x taller than wide where the reference art's leg is 0.7,
    so fitting it into the box by uniform scale left it half as wide as the body
    it belongs to and the character assembled into a skinny scarecrow. Conforming
    the art to the box's aspect (stretching one axis) is what makes an assembly
    match the character it was taken from.

    Only the smaller scale factor is applied as an upscale, so the axis that
    would have been shrunk is never the one losing resolution.
    """
    box_w = max(4.0, region[2] - region[0])
    box_h = max(4.0, region[3] - region[1])
    sx = box_w / max(1, part.width)
    sy = box_h / max(1, part.height)
    if min(sx, sy) <= 0:
        return part
    stretch = max(sx, sy) / min(sx, sy)
    if stretch > max_stretch:
        return part
    k = 1.0 / min(sx, sy)
    size = (max(1, int(round(part.width * sx * k))), max(1, int(round(part.height * sy * k))))
    return part.resize(size, Image.LANCZOS)


def pack_record(item):
    """Serialise one part for the layout.

    The key list is explicit on purpose - `image_scale` in particular must be
    the exported name - but that also silently drops flags the rest of the
    pipeline sets on the record, so anything a later stage needs has to be
    named here. `pivot_from` was dropped that way once, and every joint then
    fell back to a fraction of the image.
    """
    record = {"name": item["name"], "file": item["file"], "x": item["x"], "y": item["y"],
              "pivot": item["pivot"], "draw_order": item["draw_order"],
              "image_scale": round(float(item.get("scale", 1.0)), 6)}
    for key in ("pivot_from", "kind", "bone", "parent"):
        if key in item:
            record[key] = item[key]
    return record


def position(parts_arg, reference_path, out_path, canvas=None, ratio=0.8, min_matches=4,
             debug_dir=None, name=None, boxes_path=None, order="anatomy", fit="box"):
    # Capture this before any loop: the loops below rebind `name` to a part name,
    # which would otherwise silently rename the skeleton after the last part.
    skeleton_name = name or Path(reference_path).stem
    reference = parts_lib.load_rgba(reference_path)
    width, height = reference.size
    canvas = canvas or {"width": width, "height": height}
    # Match against the raw art, but score the silhouette against the character
    # only, so a flat backdrop does not swallow the score.
    reference_silhouette = parts_lib.strip_solid_background(reference)
    reference_rgb = np.asarray(reference.convert("RGB"))
    reference_mask = mask_of(reference_silhouette)
    reference_gray = None
    reference_keypoints = reference_descriptors = None
    if cv2 is not None:
        reference_gray = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2GRAY)
        detector = cv2.SIFT_create(contrastThreshold=0.02, edgeThreshold=20)
        reference_keypoints, reference_descriptors = detector.detectAndCompute(reference_gray, None)

    boxes = load_boxes(boxes_path, width, height)
    if boxes and boxes.get("parts"):
        print(f"part boxes : {len(boxes['parts'])} region(s) supplied, the search is confined to them")
    files = load_parts(parts_arg)
    # Place in dependency order: a part that follows another has to come after
    # it, or its region cannot be derived yet.
    follows = {str(name): str(spec["follow"])
               for name, spec in (boxes.get("parts") or {}).items()
               if isinstance(spec, dict) and spec.get("follow")}
    stems = {item.stem for item in files}

    def depth(name, seen=None):
        seen = seen or set()
        target = follows.get(name)
        if not target or target in seen or target not in stems:
            return 0
        return 1 + depth(target, seen | {name})

    files.sort(key=lambda item: (depth(item.stem), item.stem))
    entries = []
    placements = {}
    for file in files:
        name = file.stem
        part = parts_lib.load_rgba(file)
        part, trim_box = parts_lib.trim_to_alpha(part)
        pivot = rig_rules.pivot_for(name)
        # A spec may override the pivot. The tail is the reason: rig_rules puts a
        # tail's pivot near its tip (0.85), which is right for a tail that hangs
        # down behind the body, but a tail sticking out sideways has to rotate
        # from its base instead.
        spec_pivot = (boxes.get("parts", {}).get(name) or {}) if boxes else {}
        if isinstance(spec_pivot, dict) and spec_pivot.get("pivot"):
            pivot = tuple(float(v) for v in spec_pivot["pivot"])
        record = {"name": name, "file": str(file.resolve()), "pivot": list(pivot),
                  "kind": rig_rules.classify(name)}

        matched = None
        detail = ""
        # A known region beats a feature match: features are texture, and a
        # flat generated limb often has none to find.
        spec = boxes.get("parts", {}).get(name) if boxes else None
        attached = follow_matrix(spec, part, pivot, boxes, canvas, placements)
        if attached is None and fit == "conform" and boxes:
            # Conforming comes before the box fit: the part is reshaped to the
            # box's aspect, then placed inside it at a single uniform scale.
            # The reshaped art must be WRITTEN OUT and referenced by the layout -
            # reshaping it in memory only would leave the export pointing at the
            # original file, so the character would still assemble from the
            # un-conformed widths while the score said otherwise.
            spec_region = resolve_region(spec, boxes, canvas, placements)
            if spec_region is not None:
                conformed = conform_to_box(part, spec_region)
                if conformed is not part:
                    conformed_dir = Path(out_path).resolve().parent / "conformed"
                    conformed_dir.mkdir(parents=True, exist_ok=True)
                    target = conformed_dir / file.name
                    conformed.save(target)
                    part = conformed
                    file = target
                    record["file"] = str(target.resolve())
                    record["conformed_from"] = file.name
        region = None
        if attached is None and fit in ("box", "conform") and boxes:
            plain = resolve_region(spec, boxes, canvas, placements)
            # A joint the caller measured off the art beats PIVOT_BY_KIND's
            # fraction of the image. The fractions assume the box hugs the part,
            # but a limb's box has to run from its joint to its tip (the
            # generated art is occlusion-complete and carries the hidden root),
            # so the fraction points somewhere else entirely.
            if plain is not None:
                joint = spec.get("pivot_px") if isinstance(spec, dict) else None
                if joint:
                    box_w = max(4.0, plain[2] - plain[0])
                    box_h = max(4.0, plain[3] - plain[1])
                    scale = min(box_w / max(1, part.width), box_h / max(1, part.height))
                    placed_w, placed_h = part.width * scale, part.height * scale
                    left = plain[0] + (box_w - placed_w) / 2.0
                    top = plain[1] + (box_h - placed_h) / 2.0
                    jx = min(max(float(joint[0]), left), left + placed_w)
                    jy = min(max(float(joint[1]), top), top + placed_h)
                    pivot = ((jx - left) / placed_w, (jy - top) / placed_h)
                    record["pivot"] = list(pivot)
                    record["pivot_from"] = "pivot_px"
            if plain:
                matrix, scale = box_matrix(plain, part)
                attached = (matrix, scale)
                detail = f"placed in box {[round(v) for v in plain]} at scale {scale:.3f}"
                attached_box = True
        if attached is not None:
            matrix, scale = attached
            method = "box-fit" if locals().pop("attached_box", False) else "attached"
            if method == "attached":
                detail = f"attached to {spec['follow']} at width {spec.get('width')}"
            matched = {"matrix": matrix, "inliers": 0, "scale": scale, "rotation": 0.0,
                       "method": method, "score": 1.0}
        else:
            region = resolve_region(spec, boxes, canvas, placements) if boxes else None
        if attached is None and region:
            # Grow a region just enough to recover from a coarse reading, but
            # never so much that a small part (a bell) can drift away from it.
            pad_x = min(50.0, max(16.0, (region[2] - region[0]) * 0.14))
            pad_y = min(50.0, max(16.0, (region[3] - region[1]) * 0.14))
            grown = (region[0] - pad_x, region[1] - pad_y,
                     region[2] + pad_x, region[3] + pad_y)
            matched, detail = place_in_region(part, reference_rgb, reference_mask,
                                              grown, side=side_of(name))
            if matched is not None:
                matched["region"] = [round(v, 1) for v in region]
        if matched is None and cv2 is not None and reference_descriptors is not None and \
                len(reference_descriptors) >= min_matches:
            matched, detail = sift_match(part, reference_gray, reference_keypoints,
                                         reference_descriptors, ratio=ratio,
                                         min_matches=min_matches)
        else:
            detail = "opencv unavailable or reference has too few features"
        if matched is None:
            fallback, fallback_detail = template_match(part, reference_rgb, reference_mask)
            if fallback is not None:
                matched = fallback
                detail = f"{detail}; template fallback: {fallback_detail}"
            else:
                matched = None
                detail = f"{detail}; {fallback_detail}"

        if matched is None:
            # Last resort: centre the part, and say so loudly.
            matrix = np.array([[1.0, 0.0, width / 2 - part.width / 2],
                               [0.0, 1.0, height / 2 - part.height / 2]], dtype=np.float32)
            method = "centered-fallback"
        else:
            matrix = matched["matrix"]
            method = matched["method"]

        pivot_x, pivot_y = part_pivot_pixels(part, pivot)
        mapped = apply_similarity(matrix, np.array([[pivot_x, pivot_y]], dtype=np.float32))[0]
        record.update({
            "x": round(float(mapped[0]) - width / 2, 3),
            "y": round(height / 2 - float(mapped[1]), 3),
            "scale": round(float(matched["scale"]), 4) if matched else 1.0,
            "rotation": round(float(matched["rotation"]), 3) if matched else 0.0,
            "method": method,
            "detail": detail,
            "world_size": [int(round(part.width * (matched["scale"] if matched else 1.0))),
                           int(round(part.height * (matched["scale"] if matched else 1.0)))],
        })
        entries.append(record)
        placements[name] = {"matrix": matrix, "part": part, "record": record,
                            "bbox": placement_bbox(matrix, part)}

    # draw order ------------------------------------------------------------
    names = [entry["name"] for entry in entries]
    masks, colors = {}, {}
    for name, item in placements.items():
        matrix = item["matrix"]
        part = item["part"]
        warped = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        resized = part
        scale = float(np.hypot(matrix[0, 0], matrix[1, 0]))
        if abs(scale - 1.0) > 1e-3:
            resized = part.resize((max(1, round(part.width * scale)),
                                   max(1, round(part.height * scale))),
                                  Image.Resampling.LANCZOS)
        top_left = apply_similarity(matrix, np.array([[0, 0]], dtype=np.float32))[0]
        canvas_part = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas_part.alpha_composite(resized, (int(round(top_left[0])), int(round(top_left[1]))))
        masks[name] = mask_of(canvas_part) & reference_mask
        colors[name] = np.asarray(canvas_part.convert("RGB"))
        warped.close()

    defaults = default_order_scores(names)
    if order == "evidence":
        ordered, beats = occlusion_z_order(
            {name: {"mask": masks[name], "colors": colors[name]} for name in names},
            reference_rgb, (width, height), defaults=defaults)
        depth = {name: index for index, name in enumerate(ordered)}
    else:
        ordered, beats, depth = [], {}, {}
    for name in names:
        record = next(item for item in entries if item["name"] == name)
        if order == "evidence":
            record["occlusion_wins"] = len(beats.get(name, ()))
            record["draw_order"] = round(depth[name] * 100.0 + defaults[name], 3)
        else:
            # The rig rules already know that a bell is in front of a collar and
            # a tail is behind a torso. Voting on colour made the torso cover
            # the head and the head cover the collar, so anatomy is the default.
            record["draw_order"] = float(defaults[name])
        # A spec may pin the draw order. A stubby limb whose artwork includes
        # its hidden shoulder needs to sit BEHIND the torso: the body's own
        # silhouette then covers the seam, where drawing it in front would show
        # a straight cut edge floating on the belly.
        # NB: read the spec by name here. `spec` from the placement loop is a
        # leaked loop variable (it holds whatever part was placed last), and
        # using it applied the last part's order to every part.
        entry_spec = (boxes.get("parts") or {}).get(name) if boxes else None
        override = entry_spec.get("draw_order") if isinstance(entry_spec, dict) else None
        if override is not None:
            record["draw_order"] = float(override)

    entries.sort(key=lambda item: (item["draw_order"], item["name"]))
    layout = {
        "name": skeleton_name,
        "canvas": canvas,
        # Edge decontamination exists to kill green-screen spill. Parts cut
        # straight out of the reference carry no spill, and running it anyway
        "decontaminate_edges": True,
        # image_scale is the name the exporter reads. Omitting it silently
        # placed every part at its native pixel size, which is how a collar
        # generated at 878px wide ended up covering the puppy's whole face.
        "parts": [pack_record(item) for item in entries],
    }
    stored = {item["name"]: item for item in entries}

    # assemble a composite for the score ------------------------------------
    composite = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for item in sorted(entries, key=lambda entry: entry["draw_order"]):
        matrix = placements[item["name"]]["matrix"]
        part = placements[item["name"]]["part"]
        scale = float(np.hypot(matrix[0, 0], matrix[1, 0]))
        resized = part
        if abs(scale - 1.0) > 1e-3:
            resized = part.resize((max(1, round(part.width * scale)),
                                   max(1, round(part.height * scale))),
                                  Image.Resampling.LANCZOS)
        top_left = apply_similarity(matrix, np.array([[0, 0]], dtype=np.float32))[0]
        composite.alpha_composite(resized, (int(round(top_left[0])), int(round(top_left[1]))))

    composite_data = np.asarray(composite)[:, :, 3] > 24
    reference_data = np.asarray(reference_silhouette)[:, :, 3] > 24
    intersection = int((composite_data & reference_data).sum())
    union = int((composite_data | reference_data).sum())
    score = intersection / union if union else 0.0

    report = {
        "ok": score >= 0.6,
        "positioning_score": round(score, 4),
        "reference": str(Path(reference_path).resolve()),
        "canvas": canvas,
        "parts": [{key: value for key, value in item.items() if key != "file"}
                  for item in entries],
        "methods": {item["name"]: item["method"] for item in entries},
        "unmatched": [item["name"] for item in entries if item["method"] == "centered-fallback"],
    }

    out_path = Path(out_path)
    layout["positioning"] = {"score": report["positioning_score"],
                             "methods": report["methods"]}
    parts_lib.write_json(out_path, layout)
    parts_lib.write_json(out_path.with_name(out_path.stem + "_report.json"), report)

    if debug_dir:
        debug = Path(debug_dir)
        debug.mkdir(parents=True, exist_ok=True)
        composite.save(debug / "composite.png")
        reference.save(debug / "reference.png")
        strip = Image.new("RGBA", (width * 3 + 24, height), (24, 24, 28, 255))
        strip.alpha_composite(reference.convert("RGBA"), (6, 0))
        strip.alpha_composite(composite, (width + 12, 0))
        overlay = Image.new("RGBA", (width, height), (24, 24, 28, 255))
        pixels = []
        composite_rgb = np.asarray(composite.convert("RGBA"))
        reference_full = np.asarray(reference_silhouette)
        for y in range(height):
            for x in range(width):
                a_on = composite_rgb[y, x, 3] > 24
                b_on = reference_full[y, x, 3] > 24
                if a_on and b_on:
                    pixels.append((120, 200, 140, 255))
                elif a_on:
                    pixels.append((235, 90, 90, 255))
                elif b_on:
                    pixels.append((90, 140, 235, 255))
                else:
                    pixels.append((24, 24, 28, 255))
        overlay.putdata(pixels)
        strip.alpha_composite(overlay, (width * 2 + 18, 0))
        strip.save(debug / "positioning_debug.png")
    return layout, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Auto-position parts against a reference image")
    parser.add_argument("--parts", required=True, help="parts directory or manifest JSON")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--out", default="layout.json")
    parser.add_argument("--canvas", default=None, help="WxH (default: the reference size)")
    parser.add_argument("--ratio", type=float, default=0.8, help="Lowe ratio test")
    parser.add_argument("--min-matches", type=int, default=4)
    parser.add_argument("--debug", default=None)
    parser.add_argument("--boxes", default=None,
                        help="JSON part-box map (grid cells or pixels) to confine each search")
    parser.add_argument("--fit", choices=("box", "conform", "search"), default="box",
                        help="box: place each part inside its supplied box (default); "
                             "conform: also reshape it to the box aspect; "
                             "search: refine by colour and silhouette")
    parser.add_argument("--order", choices=("anatomy", "evidence"), default="anatomy",
                        help="draw order: rig-rule defaults (default) or occlusion voting")
    parser.add_argument("--name", default=None, help="skeleton name (default: reference filename)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    canvas = None
    if args.canvas:
        width, height = args.canvas.lower().split("x")
        canvas = {"width": int(width), "height": int(height)}
    try:
        layout, report = position(args.parts, args.reference, args.out, canvas=canvas,
                 boxes_path=args.boxes, order=args.order, fit=args.fit,
                                  ratio=args.ratio, min_matches=args.min_matches,
                                  debug_dir=args.debug, name=args.name)
    except (ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"layout  : {args.out}")
        print(f"score   : {report['positioning_score']} (silhouette overlap vs the reference)")
        for item in report["parts"]:
            print(f"  {item['name']:<14} {item['method']:<18} "
                  f"x={item['x']:>9} y={item['y']:>9} order={item['draw_order']}")
        if report["unmatched"]:
            print("NOT MATCHED (centred fallback): " + ", ".join(report["unmatched"]))
        print("RESULT:", "OK" if report["ok"] else "NEEDS REVIEW")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
