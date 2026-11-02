#!/usr/bin/env python3
"""Spine JSON wire-format profiles and conversion between Spine 3.8 and 4.x.

WHY THIS FILE EXISTS
--------------------
Spine changed the JSON animation encoding between 3.8 and 4.0. A file written in
one encoding cannot be imported by the other editor -- the import aborts with
`Error reading animation: <name>` and no useful detail.

The differences (verified against the real Spine 3.8.75 CLI, see
references/spine-version-matrix.md):

  3.8 wire format                       4.x wire format
  ---------------------------------------------------------------------------
  rotate value key: "angle"             rotate value key: "value"
  bezier stored as 4 scalar keys on     bezier stored as ONE array on the
    the segment-start keyframe:           segment-start keyframe:
    {"curve": cx1, "c2": cy1,             {"curve": [cx1, cy1, cx2, cy2]}
     "c3": cx2, "c4": cy2}                (single-property timelines)
  control points NORMALIZED 0..1        control points ABSOLUTE in time/value
  4 scalars serve both x and y of a     two-property timelines need 8 numbers
    two-property timeline                 (x quartet, then y quartet)

Both encodings put the curve on the keyframe that STARTS the segment, and
neither writes a curve on the last keyframe of a timeline.

This module is the single source of truth for those rules. Everything else in
the skill calls `normalize_to_target()` before writing a skeleton JSON.
"""

from __future__ import annotations

# ── timeline bookkeeping ────────────────────────────────────────────────────
# Every animated property of a bone timeline, in wire order. The FIRST entry is
# the one Spine 3.8's single scalar bezier describes.
BONE_TIMELINE_PROPERTIES = {
    "rotate": (("angle", "value", 0.0),),
    "translate": (("x", "x", 0.0), ("y", "y", 0.0)),
    "scale": (("x", "x", 1.0), ("y", "y", 1.0)),
    "shear": (("x", "x", 0.0), ("y", "y", 0.0)),
}

# Slot timelines and constraint timelines keep their property keys across
# versions; only the curve array differs. Value counts come from the Spine
# runtime (one bezier quartet per animated property).
OTHER_TIMELINE_ARITY = {
    "color": 4,
    "twoColor": 8,
    "rgb": 3,
    "rgba": 4,
    "rgb2": 3,
    "rgba2": 4,
    "alpha": 1,
    "attachment": 1,
    "deform": 1,
    "sequence": 1,
    "drawOrder": 1,
    "path": 3,
    "ik": 2,
    "transform": 6,
    "physics": 2,
    "mix": 1,
}

V38_KEYS = ("curve", "c2", "c3", "c4")


class VersionError(ValueError):
    """Raised when a document cannot be represented in the target version."""


# ── version parsing ─────────────────────────────────────────────────────────
def parse_version(text):
    """Parse "3.8.75" / "4.2.0" / "4.2" into (major, minor, patch)."""
    if not text:
        return None
    parts = str(text).split(".")
    out = []
    for part in parts[:3]:
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    while len(out) < 3:
        out.append(0)
    return tuple(out)


def is_legacy(version):
    """True when `version` uses the Spine 3.8-style JSON encoding."""
    parsed = parse_version(version)
    if parsed is None:
        return False
    return parsed[0] < 4


def version_family(version):
    """Return '3.8' or '4.x' style label for reporting."""
    parsed = parse_version(version)
    if parsed is None:
        return "unknown"
    return "3.8" if parsed[0] < 4 else "4.x"


# ── curve helpers ───────────────────────────────────────────────────────────
def _property_pairs(timeline, count):
    """Yield (value_key, default, index) for the animated properties."""
    first = BONE_TIMELINE_PROPERTIES[timeline]
    return first


def normalize_curve_absolute_to_unit(curve, time_start, time_end, value_start, value_end):
    """Absolute 4-number bezier -> normalized (nx1, ny1, nx2, ny2)."""
    span = (time_end - time_start) or 1.0
    delta = value_end - value_start
    nx1 = (curve[0] - time_start) / span
    nx2 = (curve[2] - time_start) / span
    ny1 = (curve[1] - value_start) / delta if delta else 0.0
    ny2 = (curve[3] - value_start) / delta if delta else 0.0
    return nx1, ny1, nx2, ny2


def curve_unit_to_absolute(unit, time_start, time_end, value_start, value_end):
    """Normalized (nx1, ny1, nx2, ny2) -> absolute 4-number bezier."""
    nx1, ny1, nx2, ny2 = unit
    span = (time_end - time_start) or 1.0
    delta = value_end - value_start
    return [
        time_start + span * nx1,
        value_start + delta * ny1,
        time_start + span * nx2,
        value_start + delta * ny2,
    ]


def _keyframe_time(keyframes, index):
    if index < 0 or index >= len(keyframes):
        raise VersionError("curve has no following keyframe to describe a segment")
    return float(keyframes[index].get("time", 0.0))


def _read_curve_387(keyframe):
    """Read a 3.8-spelled bezier: ('unit', 4 normalized numbers) / ('stepped', None).

    A raw absolute array inside a 3.8 file is tolerated and reported as
    ('absolute', numbers).
    """
    if "curve" not in keyframe:
        return None
    value = keyframe["curve"]
    if value == "stepped":
        return ("stepped", None)
    if isinstance(value, (int, float)):
        return ("unit", (float(value), float(keyframe.get("c2", 0.0)),
                         float(keyframe.get("c3", 1.0)), float(keyframe.get("c4", 1.0))))
    if isinstance(value, list):
        return ("absolute", value)
    return None


def _strip_387_curve(keyframe):
    for key in V38_KEYS:
        keyframe.pop(key, None)


def _read_curve_4x(keyframe):
    if "curve" not in keyframe:
        return None
    value = keyframe["curve"]
    if value == "stepped":
        return ("stepped", None)
    if isinstance(value, list):
        return ("absolute", value)
    if isinstance(value, (int, float)):
        # Tolerate the 3.8 scalar spelling inside a 4.x file.
        return ("unit", (float(value), float(keyframe.get("c2", 0.0)),
                         float(keyframe.get("c3", 1.0)), float(keyframe.get("c4", 1.0))))
    return None


# ── bone timeline conversion ────────────────────────────────────────────────
def _convert_bone_timeline(timeline, keyframes, target_legacy):
    props = BONE_TIMELINE_PROPERTIES.get(timeline)
    if props is None or not isinstance(keyframes, list) or len(keyframes) < 1:
        return

    if target_legacy:
        # 4.x -> 3.8
        for keyframe in keyframes:
            if "value" in keyframe:
                keyframe["angle"] = keyframe.pop("value")
        for index, keyframe in enumerate(keyframes):
            state = _read_curve_4x(keyframe)
            if state is None:
                continue
            kind, payload = state
            _strip_387_curve(keyframe)
            keyframe.pop("curve", None)
            if kind == "stepped":
                keyframe["curve"] = "stepped"
                continue
            if index + 1 >= len(keyframes):
                # A trailing curve describes no segment; the format forbids it.
                continue
            pair_key, _, default = props[0]
            value_key = "angle" if timeline == "rotate" else pair_key
            if kind == "unit":
                unit = payload
            else:
                v1 = float(keyframe.get(value_key, keyframes[index + 1].get(value_key, default)))
                v2 = float(keyframes[index + 1].get(value_key, default))
                unit = normalize_curve_absolute_to_unit(
                    payload, _keyframe_time(keyframes, index),
                    _keyframe_time(keyframes, index + 1), v1, v2)
            keyframe["curve"] = round(unit[0], 6)
            keyframe["c2"] = round(unit[1], 6)
            keyframe["c3"] = round(unit[2], 6)
            keyframe["c4"] = round(unit[3], 6)
    else:
        # 3.8 -> 4.x
        for keyframe in keyframes:
            if "angle" in keyframe:
                keyframe["value"] = keyframe.pop("angle")
        for index, keyframe in enumerate(keyframes):
            state = _read_curve_387(keyframe)
            if state is None:
                continue
            kind, payload = state
            _strip_387_curve(keyframe)
            keyframe.pop("curve", None)
            if kind == "stepped":
                keyframe["curve"] = "stepped"
                continue
            if index + 1 >= len(keyframes):
                continue
            time_start = _keyframe_time(keyframes, index)
            time_end = _keyframe_time(keyframes, index + 1)
            arrays = []
            for pair_key, value_key, default in props:
                if timeline == "rotate":
                    value_key = "value"
                v1 = float(keyframe.get(value_key, default))
                v2 = float(keyframes[index + 1].get(value_key, default))
                if kind == "unit":
                    arrays.append(curve_unit_to_absolute(payload, time_start, time_end, v1, v2))
                else:
                    # Already absolute: keep the first quartet, rebuild the rest.
                    if not arrays:
                        arrays.append([float(item) for item in payload[:4]])
                    else:
                        span = (time_end - time_start) or 1.0
                        delta = v2 - v1
                        nx = [(payload[0] - time_start) / span, (payload[2] - time_start) / span]
                        arrays.append([time_start + span * nx[0], v1 + delta * 0.0,
                                       time_start + span * nx[1], v1 + delta * 1.0])
            flat = []
            for array in arrays:
                flat.extend(round(float(item), 6) for item in array)
            keyframe["curve"] = flat


def convert_animations(animations, target_version):
    """Convert every timeline in `animations` to the `target_version` encoding."""
    if not isinstance(animations, dict):
        return animations
    legacy = is_legacy(target_version)

    def walk_section(section):
        for element in (section or {}).values():
            if not isinstance(element, dict):
                continue
            for timeline, keyframes in list(element.items()):
                if not isinstance(keyframes, list):
                    continue
                if timeline in BONE_TIMELINE_PROPERTIES:
                    _convert_bone_timeline(timeline, keyframes, legacy)
                else:
                    _convert_other_timeline(timeline, keyframes, legacy)

    for animation in animations.values():
        if not isinstance(animation, dict):
            continue
        for name in ("bones", "slots", "ik", "transform", "path", "physics", "deform"):
            walk_section(animation.get(name))
    return animations


def _convert_other_timeline(timeline, keyframes, target_legacy):
    """Curves for slot/constraint timelines: only the encoding changes."""
    for index, keyframe in enumerate(keyframes):
        state = _read_curve_387(keyframe) if target_legacy else _read_curve_4x(keyframe)
        if state is None:
            continue
        kind, payload = state
        _strip_387_curve(keyframe)
        keyframe.pop("curve", None)
        if kind in ("stepped",):
            keyframe["curve"] = "stepped"
            continue
        if index + 1 >= len(keyframes):
            continue
        time_start = _keyframe_time(keyframes, index)
        time_end = _keyframe_time(keyframes, index + 1)
        span = (time_end - time_start) or 1.0
        if target_legacy:
            # absolute -> normalized time handles only (values stay untouched:
            # slot/constraint curves carry one quartet per property and 3.8
            # stores just the time handles plus both value handles of the
            # FIRST property).
            if kind == "unit":
                unit = payload
            else:
                unit = ((payload[0] - time_start) / span, 0.0,
                        (payload[2] - time_start) / span, 1.0)
            keyframe["curve"] = round(unit[0], 6)
            keyframe["c2"] = round(unit[1], 6)
            keyframe["c3"] = round(unit[2], 6)
            keyframe["c4"] = round(unit[3], 6)
        else:
            if kind == "unit":
                unit = payload
                flat = [round(time_start + span * unit[0], 6), round(unit[1], 6),
                        round(time_start + span * unit[2], 6), round(unit[3], 6)]
            else:
                flat = [round(float(item), 6) for item in payload]
            keyframe["curve"] = flat


# ── document level ──────────────────────────────────────────────────────────
def document_version(document):
    return (document or {}).get("skeleton", {}).get("spine")


def normalize_to_target(document, target_version):
    """Rewrite `document` in place so `target_version`'s editor can import it."""
    target = parse_version(target_version)
    if target is None:
        raise VersionError("target_version must look like 3.8.75 or 4.2.0")
    skeleton = document.setdefault("skeleton", {})
    source = skeleton.get("spine")
    convert_animations(document.get("animations") or {}, target_version)
    skeleton["spine"] = _version_string(target_version, source)

    if is_legacy(target_version):
        # `fps` arrived with 4.1; 3.8 wrote `images` and `audio` itself, so both
        # of those stay (the editor uses `images` to resolve attachment paths).
        skeleton.pop("fps", None)
        for slot in document.get("slots") or []:
            if "color" in slot and isinstance(slot["color"], str):
                slot["color"] = _hex_color_to_rgba(slot["color"])
    else:
        skeleton.setdefault("images", "")
        skeleton.setdefault("fps", 30)
    return document


def _version_string(target_version, source):
    """Keep the caller's spelling when it already matches the target family."""
    target = parse_version(target_version)
    source_parsed = parse_version(source)
    if source_parsed and source_parsed[0] == target[0]:
        return str(source)
    parts = [target[0], target[1], target[2]]
    while len(parts) > 2 and parts[-1] == 0:
        parts.pop()
    return ".".join(str(part) for part in parts)


def _hex_color_to_rgba(text):
    text = text.strip().lstrip("#")
    if len(text) == 6:
        text += "ff"
    try:
        value = int(text, 16)
    except ValueError:
        return [1, 1, 1, 1]
    if len(text) == 8:  # RRGGBBAA
        return [((value >> 24) & 0xFF) / 255.0, ((value >> 16) & 0xFF) / 255.0,
                ((value >> 8) & 0xFF) / 255.0, (value & 0xFF) / 255.0]
    return [1, 1, 1, 1]


# ── validation ──────────────────────────────────────────────────────────────
def expected_curve_length(timeline, section):
    if section in ("ik",):
        return 8
    if section in ("transform",):
        return 24
    if section in ("path",):
        return 12
    if timeline in BONE_TIMELINE_PROPERTIES:
        return 4 * len(BONE_TIMELINE_PROPERTIES[timeline])
    count = OTHER_TIMELINE_ARITY.get(timeline, 1)
    return 4 * count


def _walk_timelines(document):
    for anim_name, animation in (document.get("animations") or {}).items():
        if not isinstance(animation, dict):
            continue
        for section, elements in animation.items():
            if not isinstance(elements, dict):
                continue
            for element_name, timelines in elements.items():
                if not isinstance(timelines, dict):
                    continue
                for timeline, keyframes in timelines.items():
                    if isinstance(keyframes, list):
                        yield f"animations.{anim_name}.{section}.{element_name}.{timeline}", \
                              section, timeline, keyframes


def validate_curves(document, target_version=None):
    """Return a list of issue strings for the document's current encoding."""
    target_version = target_version or document_version(document)
    legacy = is_legacy(target_version)
    issues = []
    for path, section, timeline, keyframes in _walk_timelines(document):
        last = len(keyframes) - 1
        for index, keyframe in enumerate(keyframes):
            if not isinstance(keyframe, dict):
                issues.append(f"{path}[{index}]: keyframe must be an object")
                continue
            if "time" in keyframe and index and \
                    float(keyframe["time"]) < float(keyframes[index - 1].get("time", 0.0)):
                issues.append(f"{path}[{index}]: time {keyframe['time']} goes backwards")
            curve = keyframe.get("curve")
            if curve is None:
                continue
            if curve == "stepped":
                continue
            if legacy:
                if not isinstance(curve, (int, float)):
                    issues.append(
                        f"{path}[{index}]: Spine 3.8 needs \"curve\" as a single number "
                        f"(plus c2/c3/c4), got {type(curve).__name__}")
                    continue
                if index == last:
                    issues.append(f"{path}[{index}]: last keyframe must not carry a curve")
                for key in ("c2", "c3", "c4"):
                    if key not in keyframe:
                        issues.append(f"{path}[{index}]: 3.8 bezier needs {key} beside curve")
            else:
                if isinstance(curve, str):
                    issues.append(f'{path}[{index}]: curve string must be "stepped"')
                    continue
                if not isinstance(curve, list):
                    issues.append(f"{path}[{index}]: curve must be an array or \"stepped\"")
                    continue
                want = expected_curve_length(timeline, section)
                if len(curve) != want:
                    issues.append(
                        f"{path}[{index}]: expected {want} curve numbers, got {len(curve)}")
                if index == last:
                    issues.append(f"{path}[{index}]: last keyframe must not carry a curve")
    if legacy:
        for path, section, timeline, keyframes in _walk_timelines(document):
            for index, keyframe in enumerate(keyframes):
                if isinstance(keyframe, dict) and "value" in keyframe and timeline == "rotate":
                    issues.append(f"{path}[{index}]: 3.8 uses \"angle\", not \"value\"")
    else:
        for path, section, timeline, keyframes in _walk_timelines(document):
            for index, keyframe in enumerate(keyframes):
                if isinstance(keyframe, dict) and "angle" in keyframe and timeline == "rotate":
                    issues.append(f"{path}[{index}]: 4.x uses \"value\", not \"angle\"")
                if isinstance(keyframe, dict) and ("c2" in keyframe or "c4" in keyframe):
                    issues.append(f"{path}[{index}]: 4.x stores the bezier in \"curve\", not c2/c3/c4")
    return issues
