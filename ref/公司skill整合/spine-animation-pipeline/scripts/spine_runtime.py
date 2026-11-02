#!/usr/bin/env python3
"""A small Spine pose sampler and renderer.

It is deliberately narrow: region attachments only, no meshes, constraints,
IK or skins beyond `default`. That covers everything this skill generates, and
it runs with just Pillow -- no runtime, no browser, no internet.

Two jobs depend on it:

* `make_preview.py` renders the setup pose (so the composite can be compared
  with the reference art) and samples the animation into frames/GIF.
* the QA gate measures how much the animation actually moves, which is the only
  way a text-only agent can tell "the idle loop is exported" from "the idle
  loop is empty".
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import parts_lib  # noqa: E402

THRESHOLD = 1e-6


# ── atlas ───────────────────────────────────────────────────────────────────
def read_atlas(path):
    """Parse a .atlas file -> {'page': name, 'regions': {name: rect}}."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"empty atlas: {path}")
    page = lines[0].strip()
    regions = {}
    pending = None
    for raw in lines[1:]:
        bare = raw.strip()
        if not bare:
            continue
        indented = raw[:1].isspace()
        if not indented:
            if ":" in bare:
                continue  # header line: size / format / filter / repeat / pma
            pending = bare
            regions[pending] = {"xy": (0, 0), "size": (0, 0)}
            continue
        if pending is None:
            continue
        if bare.startswith("xy:"):
            x, y = _split_pair(bare.split(":", 1)[1])
            regions[pending]["xy"] = (x, y)
        elif bare.startswith("size:"):
            width, height = _split_pair(bare.split(":", 1)[1])
            regions[pending]["size"] = (width, height)
    return {"page": page, "regions": regions}


def _split_pair(text):
    parts = [chunk.strip() for chunk in text.split(",")]
    values = []
    for chunk in parts[:2]:
        try:
            values.append(float(chunk))
        except ValueError:
            values.append(0.0)
    while len(values) < 2:
        values.append(0.0)
    return values[0], values[1]


def load_atlas(path):
    """Parse the atlas and load its page image next to it."""
    info = read_atlas(path)
    page_path = Path(path).parent / info["page"]
    info["image"] = Image.open(page_path).convert("RGBA").copy()
    return info


def region_image(atlas, name):
    rect = atlas["regions"].get(name)
    if rect is None:
        raise KeyError(f"atlas has no region '{name}'")
    x, y = int(round(rect["xy"][0])), int(round(rect["xy"][1]))
    width, height = int(round(rect["size"][0])), int(round(rect["size"][1]))
    return atlas["image"].crop((x, y, x + width, y + height))


# ── document model ──────────────────────────────────────────────────────────
class Skeleton:
    def __init__(self, document):
        self.document = document
        meta = document.get("skeleton", {})
        self.version = meta.get("spine")
        self.origin_x = float(meta.get("x", 0.0))
        self.origin_y = float(meta.get("y", 0.0))
        self.width = float(meta.get("width", 512))
        self.height = float(meta.get("height", 512))
        self.bones = {}
        for bone in document.get("bones", []):
            self.bones[bone["name"]] = {
                "parent": bone.get("parent"),
                "x": float(bone.get("x", 0.0)),
                "y": float(bone.get("y", 0.0)),
                "rotation": float(bone.get("rotation", 0.0)),
                "scaleX": float(bone.get("scaleX", 1.0)),
                "scaleY": float(bone.get("scaleY", 1.0)),
                "length": float(bone.get("length", 0.0)),
            }
        self.slots = []
        for slot in document.get("slots", []):
            self.slots.append({"name": slot["name"], "bone": slot["bone"],
                               "attachment": slot.get("attachment")})
        self.attachments = {}
        for skin in document.get("skins", []):
            if skin.get("name") != "default":
                continue
            for slot_name, values in (skin.get("attachments") or {}).items():
                self.attachments[slot_name] = values
        self.animations = document.get("animations") or {}

    def animation_names(self):
        return sorted(self.animations.keys())

    def animation_duration(self, name):
        longest = 0.0
        for timelines in (self.animations.get(name, {}).get("bones") or {}).values():
            for keyframes in timelines.values():
                if isinstance(keyframes, list) and keyframes:
                    longest = max(longest, float(keyframes[-1].get("time", 0.0)))
        return longest

    def setup_pose(self):
        return {name: {"x": bone["x"], "y": bone["y"], "rotation": bone["rotation"],
                       "scaleX": bone["scaleX"], "scaleY": bone["scaleY"]}
                for name, bone in self.bones.items()}


# ── timeline sampling ───────────────────────────────────────────────────────
def _bezier(value, cx1, cy1, cx2, cy2):
    """Solve the cubic bezier for x=value, return y (both normalised 0..1)."""
    low, high = 0.0, 1.0
    for _ in range(24):
        mid = (low + high) / 2
        x = 3 * (1 - mid) ** 2 * mid * cx1 + 3 * (1 - mid) * mid ** 2 * cx2 + mid ** 3
        if x < value:
            low = mid
        else:
            high = mid
    t = (low + high) / 2
    return 3 * (1 - t) ** 2 * t * cy1 + 3 * (1 - t) * t ** 2 * cy2 + t ** 3


def keyframe_curve(keyframes, index, value_key, value_default, legacy):
    """Return (cx1, cy1, cx2, cy2) in normalised space, or None for linear."""
    keyframe = keyframes[index]
    curve = keyframe.get("curve")
    if curve is None:
        return None
    if curve == "stepped":
        return "stepped"
    time_start = float(keyframe.get("time", 0.0))
    time_end = float(keyframes[index + 1].get("time", 0.0))
    span = (time_end - time_start) or 1.0
    value_start = float(keyframe.get(value_key, value_default))
    value_end = float(keyframes[index + 1].get(value_key, value_default))
    delta = value_end - value_start

    if legacy or isinstance(curve, (int, float)):
        if isinstance(curve, (int, float)):
            return (float(curve), float(keyframe.get("c2", 0.0)),
                    float(keyframe.get("c3", 1.0)), float(keyframe.get("c4", 1.0)))
        return None
    if not isinstance(curve, list) or len(curve) < 4:
        return None
    cx1 = (curve[0] - time_start) / span
    cx2 = (curve[2] - time_start) / span
    cy1 = (curve[1] - value_start) / delta if abs(delta) > THRESHOLD else 0.0
    cy2 = (curve[3] - value_start) / delta if abs(delta) > THRESHOLD else 0.0
    return (cx1, cy1, cx2, cy2)


META_KEYS = ("time", "curve", "c2", "c3", "c4")


def sample_timeline(keyframes, time, value_key, value_default, legacy):
    """Interpolate one timeline at `time`, returning a dict of property values."""
    if not keyframes:
        return {}
    keys = sorted({key for keyframe in keyframes for key in keyframe
                   if key not in META_KEYS}) or [value_key]
    if time <= float(keyframes[0].get("time", 0.0)):
        index = 0
        fraction = 0.0
    elif time >= float(keyframes[-1].get("time", 0.0)):
        index = len(keyframes) - 1
        fraction = 0.0
    else:
        index = max(i for i, keyframe in enumerate(keyframes)
                    if float(keyframe.get("time", 0.0)) <= time)
        start = float(keyframes[index].get("time", 0.0))
        end = float(keyframes[index + 1].get("time", 0.0))
        fraction = (time - start) / ((end - start) or 1.0)

    out = {}
    for key in keys:
        first = float(keyframes[index].get(key, value_default))
        if index + 1 < len(keyframes) and fraction > 0:
            second = float(keyframes[index + 1].get(key, value_default))
            curve = keyframe_curve(keyframes, index, key, value_default, legacy)
            if curve == "stepped":
                out[key] = first
            elif curve is None:
                out[key] = first + (second - first) * fraction
            else:
                eased = _bezier(fraction, *curve)
                out[key] = first + (second - first) * eased
        else:
            out[key] = first
    return out


def pose_at(skeleton, animation, time):
    """Setup pose + sampled animation deltas -> {bone: {x, y, rotation, scale}}."""
    pose = skeleton.setup_pose()
    timelines = (skeleton.animations.get(animation, {}) or {}).get("bones") or {}
    legacy = _legacy(skeleton.version)
    for bone_name, tracks in timelines.items():
        target = pose.setdefault(bone_name, {"x": 0.0, "y": 0.0, "rotation": 0.0,
                                             "scaleX": 1.0, "scaleY": 1.0})
        if isinstance(tracks.get("rotate"), list):
            values = sample_timeline(tracks["rotate"], time,
                                     "angle" if legacy else "value", 0.0, legacy)
            target["rotation"] += values.get("angle", values.get("value", 0.0))
        if isinstance(tracks.get("translate"), list):
            values = sample_timeline(tracks["translate"], time, "x", 0.0, legacy)
            target["x"] += values.get("x", 0.0)
            target["y"] += values.get("y", 0.0)
        if isinstance(tracks.get("scale"), list):
            values = sample_timeline(tracks["scale"], time, "x", 1.0, legacy)
            target["scaleX"] *= values.get("x", 1.0)
            target["scaleY"] *= values.get("y", 1.0)
    return pose


def _legacy(version):
    try:
        return int(str(version).split(".")[0]) < 4
    except (ValueError, AttributeError):
        return True


# ── transforms / rendering ──────────────────────────────────────────────────
def bone_world(skeleton, pose):
    """Resolve world translation and rotation for every bone."""
    resolved = {}

    def resolve(name, guard=()):
        if name in resolved:
            return resolved[name]
        if name in guard:
            raise ValueError(f"cyclic bone parent: {name}")
        bone = skeleton.bones.get(name)
        if bone is None:
            resolved[name] = (0.0, 0.0, 0.0)
            return resolved[name]
        state = pose.get(name, {})
        parent = bone["parent"]
        if not parent:
            parent_pos, parent_rot = (0.0, 0.0), 0.0
        else:
            parent_pos, parent_rot = resolve(parent, guard + (name,))
        local_x = float(state.get("x", bone["x"]))
        local_y = float(state.get("y", bone["y"]))
        angle = math.radians(parent_rot)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        world_x = parent_pos[0] + local_x * cos_a - local_y * sin_a
        world_y = parent_pos[1] + local_x * sin_a + local_y * cos_a
        rotation = parent_rot + float(state.get("rotation", bone["rotation"]))
        resolved[name] = ((world_x, world_y), rotation)
        return resolved[name]

    for name in skeleton.bones:
        resolve(name)
    return resolved


def render(skeleton, atlas, pose, size=None, background=(0, 0, 0, 0), scale=1.0):
    """Draw the pose; returns a PIL image the size of the skeleton canvas."""
    width = int(round(size[0] * scale)) if size else int(round(skeleton.width * scale))
    height = int(round(size[1] * scale)) if size else int(round(skeleton.height * scale))
    canvas = Image.new("RGBA", (width, height), background)
    world = bone_world(skeleton, pose)
    top_y = skeleton.origin_y + skeleton.height

    for slot in skeleton.slots:
        attachment_name = slot["attachment"]
        if not attachment_name:
            continue
        values = (skeleton.attachments.get(slot["name"]) or {}).get(attachment_name)
        if values is None:
            continue
        try:
            region = region_image(atlas, values.get("path", attachment_name))
        except KeyError:
            continue
        bone_pos, bone_rotation = world.get(slot["bone"], ((0.0, 0.0), 0.0))
        state = pose.get(slot["bone"], {})
        angle = math.radians(bone_rotation)
        offset_x = float(values.get("x", 0.0))
        offset_y = float(values.get("y", 0.0))
        center_x = bone_pos[0] + offset_x * math.cos(angle) - offset_y * math.sin(angle)
        center_y = bone_pos[1] + offset_x * math.sin(angle) + offset_y * math.cos(angle)

        rotation = bone_rotation + float(values.get("rotation", 0.0))
        scale_x = float(state.get("scaleX", skeleton.bones[slot["bone"]]["scaleX"]))
        scale_y = float(state.get("scaleY", skeleton.bones[slot["bone"]]["scaleY"]))
        scale_x *= float(values.get("scaleX", 1.0))
        scale_y *= float(values.get("scaleY", 1.0))

        sprite = region
        if abs(scale_x - 1.0) > THRESHOLD or abs(scale_y - 1.0) > THRESHOLD:
            sprite = sprite.resize((max(1, round(sprite.width * abs(scale_x) * scale)),
                                    max(1, round(sprite.height * abs(scale_y) * scale))),
                                   Image.Resampling.LANCZOS)
        elif abs(scale - 1.0) > THRESHOLD:
            sprite = sprite.resize((max(1, round(sprite.width * scale)),
                                    max(1, round(sprite.height * scale))),
                                   Image.Resampling.LANCZOS)
        if abs(rotation) > THRESHOLD:
            sprite = sprite.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)

        pixel_x = (center_x - skeleton.origin_x) * scale
        pixel_y = (top_y - center_y) * scale
        canvas.alpha_composite(sprite, (int(round(pixel_x - sprite.width / 2)),
                                        int(round(pixel_y - sprite.height / 2))))
    return canvas


# ── QA metrics ──────────────────────────────────────────────────────────────
def frame_difference(first, second):
    """Fraction of pixels that differ noticeably between two frames."""
    if first.size != second.size:
        second = second.resize(first.size, Image.Resampling.NEAREST)
    left = first.convert("RGBA")
    right = second.convert("RGBA")
    changed = 0
    total = left.width * left.height
    for a, b in zip(parts_lib.to_pixels(left), parts_lib.to_pixels(right)):
        if abs(a[3] - b[3]) > 8 or (a[3] > 8 and max(abs(a[i] - b[i]) for i in range(3)) > 8):
            changed += 1
    return changed / total


def silhouette_iou(rendered, reference_canvas):
    """Intersection-over-union of the two alpha/foreground silhouettes."""
    left = rendered.convert("RGBA")
    right = reference_canvas.convert("RGBA")
    if left.size != right.size:
        right = right.resize(left.size, Image.Resampling.LANCZOS)
    left_data = parts_lib.to_pixels(left)
    right_data = parts_lib.to_pixels(right)
    intersection = union = 0
    for a, b in zip(left_data, right_data):
        a_on = a[3] > 24
        b_on = b[3] > 24
        if a_on and b_on:
            intersection += 1
        if a_on or b_on:
            union += 1
    return intersection / union if union else 0.0


def motion_report(skeleton, atlas, animation, samples=12, size=None):
    """Render frames across the loop and describe how much moves."""
    duration = skeleton.animation_duration(animation) or 1.0
    frames = []
    for index in range(samples):
        time = duration * index / samples
        frames.append(render(skeleton, atlas, pose_at(skeleton, animation, time), size=size))
    deltas = [frame_difference(frames[index], frames[(index + 1) % len(frames)])
              for index in range(len(frames))]
    # The frames above stop just short of the end of the loop, so the closing
    # frame has to be rendered explicitly: comparing frames[0] with frames[-1]
    # measured a 2.2s pose against a 0s pose and reported a pop that was not
    # there.
    closing = render(skeleton, atlas,
                     pose_at(skeleton, animation, duration), size=size)
    return {
        "animation": animation,
        "duration": round(duration, 4),
        "samples": samples,
        "max_frame_delta": round(max(deltas), 5) if deltas else 0.0,
        "mean_frame_delta": round(sum(deltas) / len(deltas), 5) if deltas else 0.0,
        "loop_closes": round(frame_difference(frames[0], closing), 5) if frames else 0.0,
        "frames": frames,
    }


def load_package(json_path):
    """Load a skeleton + the atlas beside it."""
    json_path = Path(json_path)
    document = json.loads(json_path.read_text(encoding="utf-8"))
    skeleton = Skeleton(document)
    atlas_path = json_path.with_suffix(".atlas")
    atlas = load_atlas(atlas_path) if atlas_path.is_file() else None
    return skeleton, atlas, document
