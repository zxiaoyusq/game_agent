#!/usr/bin/env python3
"""The validation, inspection and transform half of the pipeline.

Adapted from Attrom/spine-mpc-attrom (a Spine MCP server in TypeScript that
wraps the Spine CLI). Its useful ideas are kept, minus the Node build, the MCP
host and the ingestion corpus:

    validate          syntax -> structure -> references -> version/import readiness
    inspect           counts, hierarchy, attachment inventory
    doc               a skeleton document: bones, what each bone drives, animation
                      profiles (the MCP's spine_build_skeleton_doc)
    diff              semantic diff between two exports
    transform         rename/prefix/clone/remap/rewrite/scale/patch + dry-run preview
    roundtrip         transform -> validate -> optional Spine CLI import -> compare
    report            workspace-wide validation report

Everything prints a machine-readable result so a text-only agent can act on it.

    python spine_toolkit.py validate out/testbot.json
    python spine_toolkit.py doc out/testbot.json --out out/spine-doc.md
    python spine_toolkit.py transform out/testbot.json --set prefix_bones=char_ --preview
    python spine_toolkit.py diff a.json b.json
    python spine_toolkit.py roundtrip out/testbot.json --work .rt --gate
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import spine_format

SAFE = "SAFE"
BEST_EFFORT = "BEST_EFFORT"
EXPERIMENTAL = "EXPERIMENTAL"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path, document):
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return Path(path)


# ── validation ──────────────────────────────────────────────────────────────
def validate(document, target_version=None, atlas_path=None):
    """Four layers, like the MCP, plus the atlas/attachment cross-check."""
    issues = []

    def add(layer, severity, message, path=""):
        issues.append({"layer": layer, "severity": severity, "message": message, "path": path})

    # layer 1: syntax / top level
    if not isinstance(document, dict):
        add("syntax", "error", "document is not a JSON object")
        return issues
    for key in ("bones", "slots", "skins"):
        if key not in document:
            add("syntax", "warning", f"missing top-level \"{key}\"")
    if "skeleton" not in document:
        add("syntax", "error", "missing \"skeleton\" metadata")
    elif not document["skeleton"].get("spine"):
        add("syntax", "warning", "skeleton.spine version missing; editors use it to pick a reader")

    version = target_version or document.get("skeleton", {}).get("spine")

    # layer 2: structure
    bone_names = []
    seen_bones = set()
    for index, bone in enumerate(document.get("bones") or []):
        name = bone.get("name")
        if not name:
            add("structure", "error", f"bone #{index} has no name", f"bones[{index}]")
            continue
        if name in seen_bones:
            add("structure", "error", f"duplicate bone name \"{name}\"", f"bones[{index}]")
        seen_bones.add(name)
        bone_names.append(name)
    bone_set = set(bone_names)

    if not bone_names:
        add("structure", "error", "skeleton has no bones")
    elif bone_names[0] != "root":
        add("structure", "warning",
            f"first bone is \"{bone_names[0]}\", usually \"root\"; some runtimes assume it")

    position = {name: index for index, name in enumerate(bone_names)}
    for index, bone in enumerate(document.get("bones") or []):
        parent = bone.get("parent")
        if not parent:
            continue
        if parent not in bone_set:
            add("structure", "error",
                f"bone \"{bone.get('name')}\" references missing parent \"{parent}\"",
                f"bones[{index}].parent")
        elif position.get(parent, 0) > position.get(bone.get("name"), 0):
            add("structure", "error",
                f"bone \"{bone.get('name')}\" appears before its parent \"{parent}\"; "
                "Spine needs parent-before-child order", f"bones[{index}]")

    slot_names = []
    for index, slot in enumerate(document.get("slots") or []):
        name = slot.get("name")
        if not name:
            add("structure", "error", f"slot #{index} has no name", f"slots[{index}]")
            continue
        if name in slot_names:
            add("structure", "error", f"duplicate slot name \"{name}\"", f"slots[{index}]")
        slot_names.append(name)
        if slot.get("bone") and slot["bone"] not in bone_set:
            add("references", "error",
                f"slot \"{name}\" uses missing bone \"{slot['bone']}\"", f"slots[{index}].bone")
    slot_set = set(slot_names)

    # layer 3: references (skins, attachments, animation targets)
    attachment_names = set()
    for skin_index, skin in enumerate(document.get("skins") or []):
        for slot_name, values in (skin.get("attachments") or {}).items():
            if slot_name not in slot_set:
                add("references", "error",
                    f"skin \"{skin.get('name')}\" attaches to missing slot \"{slot_name}\"",
                    f"skins[{skin_index}]")
            for attachment_name, values2 in (values or {}).items():
                attachment_names.add(attachment_name)
                for key in ("width", "height"):
                    if key not in values2:
                        add("structure", "warning",
                            f"attachment \"{attachment_name}\" has no \"{key}\"",
                            f"skins[{skin_index}].{slot_name}.{attachment_name}")
                if values2.get("width", 0) <= 0 or values2.get("height", 0) <= 0:
                    add("structure", "error",
                        f"attachment \"{attachment_name}\" has a non-positive size",
                        f"skins[{skin_index}].{slot_name}.{attachment_name}")

    for slot in document.get("slots") or []:
        attachment = slot.get("attachment")
        if attachment and attachment not in attachment_names:
            add("references", "error",
                f"slot \"{slot['name']}\" points at missing attachment \"{attachment}\"")
        if slot.get("attachment") and slot["name"] not in (document.get("skins") or [{}])[0].get(
                "attachments", {}):
            add("references", "warning",
                f"slot \"{slot['name']}\" has no entry in the default skin")

    for animation_name, animation in (document.get("animations") or {}).items():
        for bone_name in (animation.get("bones") or {}):
            if bone_name not in bone_set:
                add("references", "error",
                    f"animation \"{animation_name}\" animates missing bone \"{bone_name}\"")
        for slot_name in (animation.get("slots") or {}):
            if slot_name not in slot_set:
                add("references", "error",
                    f"animation \"{animation_name}\" animates missing slot \"{slot_name}\"")
        for timeline in ("translate", "rotate", "scale", "shear"):
            for bone_name, tracks in (animation.get("bones") or {}).items():
                frames = tracks.get(timeline)
                if not isinstance(frames, list) or len(frames) < 2:
                    continue
                if float(frames[-1].get("time", 0.0)) <= 0:
                    add("structure", "error",
                        f"{animation_name}.{bone_name}.{timeline} has no duration")

    # layer 4: version / import readiness
    for issue in spine_format.validate_curves(document, version):
        add("version", "error", issue)
    family = spine_format.version_family(version)
    if version and family == "unknown":
        add("version", "warning", f"cannot parse skeleton.spine \"{version}\"")

    # atlas cross-check
    if atlas_path:
        try:
            import spine_runtime
            atlas = spine_runtime.read_atlas(atlas_path)
            page = Path(atlas_path).parent / atlas["page"]
            if not page.is_file():
                add("references", "error", f"atlas page image is missing: {page.name}")
            for name in sorted(attachment_names):
                if name not in atlas["regions"]:
                    add("references", "error",
                        f"attachment \"{name}\" has no region in {Path(atlas_path).name}")
            for name in sorted(atlas["regions"]):
                if name not in attachment_names:
                    add("references", "warning", f"atlas region \"{name}\" is unused")
        except Exception as error:  # pragma: no cover
            add("references", "error", f"cannot read atlas: {error}")

    return issues


def summarize_issues(issues):
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "ok": not errors,
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": issues,
        "summary": (f"{len(errors)} error(s), {len(warnings)} warning(s)"
                    if issues else "clean"),
    }


# ── inspection ──────────────────────────────────────────────────────────────
def inspect(document):
    bones = document.get("bones") or []
    slots = document.get("slots") or []
    skins = document.get("skins") or []
    animations = document.get("animations") or {}
    children = {}
    for bone in bones:
        children.setdefault(bone.get("parent") or "", []).append(bone.get("name"))
    return {
        "version": document.get("skeleton", {}).get("spine"),
        "canvas": [document.get("skeleton", {}).get("width"),
                   document.get("skeleton", {}).get("height")],
        "bones": len(bones),
        "bone_names": [bone.get("name") for bone in bones],
        "roots": [bone.get("name") for bone in bones if not bone.get("parent")],
        "slots": len(slots),
        "slot_order_back_to_front": [slot.get("name") for slot in slots],
        "skins": [skin.get("name") for skin in skins],
        "attachments": sum(len(values or {}) for skin in skins
                           for values in (skin.get("attachments") or {}).values()),
        "animations": sorted(animations.keys()),
        "animation_profile": {name: animation_profile(animation)
                              for name, animation in animations.items()},
    }


def animation_profile(animation):
    bones = {}
    duration = 0.0
    for bone_name, tracks in (animation.get("bones") or {}).items():
        kinds = []
        for timeline, frames in tracks.items():
            if not isinstance(frames, list) or not frames:
                continue
            duration = max(duration, float(frames[-1].get("time", 0.0)))
            kinds.append(timeline)
        if kinds:
            bones[bone_name] = kinds
    return {"duration": round(duration, 4),
            "loops": bool(duration) and duration > 0,
            "animated_bones": len(bones),
            "most_active": sorted(bones.items(), key=lambda item: -len(item[1]))[:5]}


def skeleton_doc(document, name=None):
    """Markdown skeleton document, mirroring the MCP's spine_build_skeleton_doc."""
    info = inspect(document)
    slots_by_bone = {}
    for slot in document.get("slots") or []:
        slots_by_bone.setdefault(slot.get("bone"), []).append(slot.get("name"))
    attachments = {}
    for skin in document.get("skins") or []:
        for slot_name, values in (skin.get("attachments") or {}).items():
            for attachment_name, spec in (values or {}).items():
                attachments.setdefault(slot_name, []).append(
                    f"{attachment_name} ({spec.get('width')}x{spec.get('height')})")

    lines = [f"# Skeleton doc: {name or 'skeleton'}", "",
             f"- Spine version: `{info['version']}`",
             f"- Canvas: {info['canvas'][0]} x {info['canvas'][1]}",
             f"- Bones: {info['bones']}   Slots: {info['slots']}   "
             f"Attachments: {info['attachments']}",
             f"- Animations: {', '.join(info['animations']) or 'none'}", "",
             "## Bone hierarchy", "", "| Bone | Parent | Drives (slots) |", "| --- | --- | --- |"]
    for bone in document.get("bones") or []:
        drives = ", ".join(slots_by_bone.get(bone.get("name"), [])) or "-"
        lines.append(f"| {bone.get('name')} | {bone.get('parent') or '-'} | {drives} |")
    lines += ["", "## Draw order (back to front)", ""]
    for index, slot in enumerate(document.get("slots") or []):
        region = ", ".join(attachments.get(slot.get("name"), [])) or "-"
        lines.append(f"{index + 1}. `{slot.get('name')}` on bone `{slot.get('bone')}` -> {region}")
    lines += ["", "## Animation profiles", ""]
    for animation_name, profile in info["animation_profile"].items():
        lines += [f"### {animation_name}",
                  f"- duration {profile['duration']}s",
                  f"- animated bones: {profile['animated_bones']}"]
        for bone_name, kinds in profile["most_active"]:
            lines.append(f"  - `{bone_name}`: {', '.join(kinds)}")
        lines.append("")
    lines += ["## Transform guidance", "",
              "- Renaming bones/slots is SAFE: every reference in skins and animations is rewritten.",
              "- Adding a bone is SAFE when it is appended after its parent.",
              "- Lesson learned the hard way: rotation keyframes use `value` in Spine 4.x and "
              "`angle` in 3.8, and the bezier encoding differs. Let `spine_format` do the rewrite.",
              "- After any structural edit, re-run the import gate before shipping.", ""]
    return "\n".join(lines)


# ── diff ────────────────────────────────────────────────────────────────────
# Spine omits fields that equal their default when it re-exports (a first
# keyframe loses `time: 0`, a frame with no rotation loses `angle: 0`, and a
# bezier keeps only the control points that differ from 0/1). A byte diff would
# call a perfect round trip "7 changes", so compare canonical forms instead:
# missing means default, and every number is rounded.
TIMELINE_VALUE_KEYS = {
    "rotate": ("angle", "value"),
    "translate": ("x", "y"),
    "scale": ("x", "y"),
    "shear": ("x", "y"),
}
# In the 3.8 scalar bezier form, c2/c4 default to 0 and 1.
CURVE_DEFAULTS = {"curve": 0.0, "c2": 0.0, "c3": 0.0, "c4": 1.0}


def canonical_frames(frames, timeline, legacy):
    """Normalise one timeline's keyframes so defaults can be compared."""
    if not isinstance(frames, list):
        return frames
    value_keys = TIMELINE_VALUE_KEYS.get(timeline, ())
    out = []
    for frame in frames:
        if not isinstance(frame, dict):
            out.append(frame)
            continue
        item = {}
        for key, value in frame.items():
            if isinstance(value, bool):
                item[key] = value
            elif isinstance(value, (int, float)):
                item[key] = round(float(value), 6)
            elif isinstance(value, list):
                item[key] = [round(float(part), 6) if isinstance(part, (int, float)) else part
                             for part in value]
            else:
                item[key] = value
        item["time"] = round(float(item.get("time", 0.0)), 6)
        for key in value_keys:
            item.setdefault(key, 0.0)
        carries_curve = any(key in frame for key in CURVE_DEFAULTS)
        if carries_curve:
            if isinstance(frame.get("curve"), list):
                pass  # absolute array form; already normalised
            else:
                for key, default in CURVE_DEFAULTS.items():
                    item[key] = round(float(frame.get(key, default)), 6)
        out.append(item)
    return out


def canonical_animation(animation, legacy):
    bones = {}
    for bone_name, tracks in (animation.get("bones") or {}).items():
        bones[bone_name] = {timeline: canonical_frames(frames, timeline, legacy)
                            for timeline, frames in (tracks or {}).items()}
    slots = {}
    for slot_name, tracks in (animation.get("slots") or {}).items():
        slots[slot_name] = {timeline: canonical_frames(frames, timeline, legacy)
                            for timeline, frames in (tracks or {}).items()}
    return {"bones": bones, "slots": slots}


def semantic_diff(before, after, limit=40):
    """Compare two exports on the things a re-import can actually break."""
    changes = []

    def collect(label, left, right):
        left_set, right_set = set(left or []), set(right or [])
        for name in sorted(right_set - left_set):
            changes.append(f"{label} added: {name}")
        for name in sorted(left_set - right_set):
            changes.append(f"{label} removed: {name}")

    collect("bone", [bone.get("name") for bone in before.get("bones") or []],
            [bone.get("name") for bone in after.get("bones") or []])
    collect("slot", [slot.get("name") for slot in before.get("slots") or []],
            [slot.get("name") for slot in after.get("slots") or []])
    collect("animation", list((before.get("animations") or {}).keys()),
            list((after.get("animations") or {}).keys()))
    collect("skin", [skin.get("name") for skin in before.get("skins") or []],
            [skin.get("name") for skin in after.get("skins") or []])

    def attachment_map(document):
        out = {}
        for skin in document.get("skins") or []:
            for slot_name, values in (skin.get("attachments") or {}).items():
                for attachment_name, spec in (values or {}).items():
                    out[f"{skin.get('name')}/{slot_name}/{attachment_name}"] = (
                        spec.get("width"), spec.get("height"),
                        round(float(spec.get("x") or 0.0), 6),
                        round(float(spec.get("y") or 0.0), 6))
        return out

    before_attachments = attachment_map(before)
    after_attachments = attachment_map(after)
    for key in sorted(set(before_attachments) | set(after_attachments)):
        if key not in before_attachments:
            changes.append(f"attachment added: {key}")
        elif key not in after_attachments:
            changes.append(f"attachment removed: {key}")
        elif before_attachments[key] != after_attachments[key]:
            changes.append(f"attachment geometry changed: {key} "
                           f"{before_attachments[key]} -> {after_attachments[key]}")

    before_animations = before.get("animations") or {}
    after_animations = after.get("animations") or {}
    legacy = spine_format.version_family(before.get("skeleton", {}).get("spine")) == "3.8"
    for name in sorted(set(before_animations) & set(after_animations)):
        left = canonical_animation(before_animations[name], legacy)
        right = canonical_animation(after_animations[name], legacy)
        if json.dumps(left, sort_keys=True) != json.dumps(right, sort_keys=True):
            changes.append(f"animation \"{name}\" keyframes differ")

    version_before = before.get("skeleton", {}).get("spine")
    version_after = after.get("skeleton", {}).get("spine")
    if version_before != version_after:
        changes.append(f"version changed: {version_before} -> {version_after}")

    return {"same": not changes, "count": len(changes),
            "changes": changes[:limit],
            "truncated": max(0, len(changes) - limit),
            "summary": "identical" if not changes else f"{len(changes)} change(s)"}


# ── transforms ──────────────────────────────────────────────────────────────
def _rename(document, kind, mapping, apply):
    """Rewrite bone/slot names and every reference to them."""
    changed = []
    if kind == "bones":
        for bone in document.get("bones") or []:
            old = bone.get("name")
            new = mapping(old)
            if new != old:
                bone["name"] = new
                changed.append((old, new))
        aliases = dict(changed)
        for bone in document.get("bones") or []:
            if bone.get("parent") in aliases:
                bone["parent"] = aliases[bone["parent"]]
        for slot in document.get("slots") or []:
            if slot.get("bone") in aliases:
                slot["bone"] = aliases[slot["bone"]]
        for animation in (document.get("animations") or {}).values():
            bones = animation.get("bones")
            if isinstance(bones, dict):
                animation["bones"] = {(aliases.get(name, name) if apply else name): value
                                      for name, value in bones.items()}
    else:
        for slot in document.get("slots") or []:
            old = slot.get("name")
            new = mapping(old)
            if new != old:
                slot["name"] = new
                changed.append((old, new))
        aliases = dict(changed)
        for skin in document.get("skins") or []:
            values = skin.get("attachments")
            if isinstance(values, dict):
                skin["attachments"] = {(aliases.get(name, name) if apply else name): value
                                       for name, value in values.items()}
        for animation in (document.get("animations") or {}).values():
            slots = animation.get("slots")
            if isinstance(slots, dict):
                animation["slots"] = {(aliases.get(name, name) if apply else name): value
                                      for name, value in slots.items()}
    return changed


TRANSFORMS = {
    "prefix_bones": (SAFE, "b_"),
    "prefix_slots": (SAFE, "s_"),
    "rename_bones": (SAFE, None),
    "rename_slots": (SAFE, None),
    "rename_animations": (SAFE, None),
    "clone_skin": (SAFE, None),
    "normalize_names": (BEST_EFFORT, None),
    "rewrite_attachment_paths": (BEST_EFFORT, None),
    "scale_numeric_values": (BEST_EFFORT, None),
    "patch_raw_json": (EXPERIMENTAL, None),
}


def _slug(text):
    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "-", str(text)).strip("-")
    return cleaned or text


def apply_transform(document, name, argument=None, risk_tolerance="balanced"):
    """Run one transform; returns (document, notes)."""
    risk = TRANSFORMS.get(name, (None, None))[0]
    if risk is None:
        raise ValueError(f"unknown transform \"{name}\"; known: {', '.join(sorted(TRANSFORMS))}")
    if risk == EXPERIMENTAL and risk_tolerance == "balanced":
        raise ValueError("patch_raw_json is EXPERIMENTAL; pass --risk permissive to allow it")

    notes = []
    if name == "prefix_bones":
        prefix = argument or TRANSFORMS[name][1]
        changed = _rename(document, "bones", lambda old: f"{prefix}{old}" if old != "root" else old,
                          True)
        notes.append(f"prefixed {len(changed)} bone(s) with \"{prefix}\" (root untouched)")
    elif name == "prefix_slots":
        prefix = argument or TRANSFORMS[name][1]
        changed = _rename(document, "slots", lambda old: f"{prefix}{old}", True)
        notes.append(f"prefixed {len(changed)} slot(s) with \"{prefix}\"")
    elif name == "rename_bones":
        pairs = _parse_pairs(argument)
        changed = _rename(document, "bones", lambda old: pairs.get(old, old), True)
        notes.append(f"renamed {len(changed)} bone(s): {changed}")
    elif name == "rename_slots":
        pairs = _parse_pairs(argument)
        changed = _rename(document, "slots", lambda old: pairs.get(old, old), True)
        notes.append(f"renamed {len(changed)} slot(s): {changed}")
    elif name == "rename_animations":
        pairs = _parse_pairs(argument)
        animations = document.get("animations") or {}
        document["animations"] = {pairs.get(key, key): value for key, value in animations.items()}
        notes.append(f"animations now: {sorted(document['animations'])}")
    elif name == "clone_skin":
        source, _, target = (argument or "").partition(":")
        if not source or not target:
            raise ValueError("clone_skin needs source:target")
        for skin in document.get("skins") or []:
            if skin.get("name") == source:
                clone = copy.deepcopy(skin)
                clone["name"] = target
                document.setdefault("skins", []).append(clone)
                notes.append(f"cloned skin \"{source}\" -> \"{target}\"")
                break
        else:
            raise ValueError(f"no skin named \"{source}\"")
    elif name == "normalize_names":
        _rename(document, "bones", _slug, True)
        _rename(document, "slots", _slug, True)
        notes.append("bone and slot names sanitised to [A-Za-z0-9_-]")
    elif name == "rewrite_attachment_paths":
        old, _, new = (argument or "").partition(":")
        if not old:
            raise ValueError("rewrite_attachment_paths needs oldprefix:newprefix")
        count = 0
        for skin in document.get("skins") or []:
            for values in (skin.get("attachments") or {}).values():
                for attachment_name, spec in (values or {}).items():
                    if attachment_name.startswith(old):
                        spec["path"] = new + attachment_name[len(old):]
                        count += 1
        notes.append(f"rewrote {count} attachment path(s)")
    elif name == "scale_numeric_values":
        factor = float(argument or 1.0)
        if factor <= 0:
            raise ValueError("scale_numeric_values needs a positive factor")
        for bone in document.get("bones") or []:
            for key in ("x", "y", "length"):
                if key in bone:
                    bone[key] = round(float(bone[key]) * factor, 6)
        for skin in document.get("skins") or []:
            for values in (skin.get("attachments") or {}).values():
                for spec in (values or {}).values():
                    for key in ("x", "y", "width", "height"):
                        if key in spec:
                            spec[key] = round(float(spec[key]) * factor, 6)
        meta = document.setdefault("skeleton", {})
        for key in ("x", "y", "width", "height"):
            if key in meta:
                meta[key] = round(float(meta[key]) * factor, 6)
        notes.append(f"scaled bone/attachment geometry by {factor}")
    elif name == "patch_raw_json":
        spec = json.loads(argument) if argument else {}
        path = spec.get("path")
        if not path:
            raise ValueError("patch_raw_json needs {\"path\": \"animations.idle\", \"value\": ...}")
        target = document
        parts = path.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        if "remove" in spec:
            target.pop(parts[-1], None)
            notes.append(f"removed {path}")
        else:
            target[parts[-1]] = spec.get("value")
            notes.append(f"set {path}")
    return document, notes


def _parse_pairs(argument):
    if not argument:
        raise ValueError("this transform needs an argument (old:new,old2:new2 or JSON)")
    text = argument.strip()
    if text.startswith("{"):
        return json.loads(text)
    pairs = {}
    for item in text.split(","):
        old, _, new = item.partition(":")
        if old and new:
            pairs[old.strip()] = new.strip()
    if not pairs:
        raise ValueError(f"cannot parse mapping from \"{argument}\"")
    return pairs


# ── driver ──────────────────────────────────────────────────────────────────
def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate / inspect / diff / transform Spine JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="layered validation")
    validate_parser.add_argument("package")
    validate_parser.add_argument("--atlas", default=None, help="also cross-check the atlas")
    validate_parser.add_argument("--target-version", default=None)

    inspect_parser = sub.add_parser("inspect", help="counts and inventory")
    inspect_parser.add_argument("package")

    doc_parser = sub.add_parser("doc", help="write a skeleton document")
    doc_parser.add_argument("package")
    doc_parser.add_argument("--out", default=None)

    diff_parser = sub.add_parser("diff", help="semantic diff of two exports")
    diff_parser.add_argument("before")
    diff_parser.add_argument("after")

    transform_parser = sub.add_parser("transform", help="edit a skeleton JSON")
    transform_parser.add_argument("package")
    transform_parser.add_argument("--set", action="append", default=[],
                                  help="name=argument (repeatable, applied in order)")
    transform_parser.add_argument("--out", default=None, help="default: <package>.edited.json")
    transform_parser.add_argument("--preview", action="store_true", help="show the diff, write nothing")
    transform_parser.add_argument("--risk", default="balanced",
                                  choices=["strict", "balanced", "permissive"])
    transform_parser.add_argument("--to-version", default=None,
                                  help="also re-encode for this Spine version (e.g. 4.2.0)")

    roundtrip_parser = sub.add_parser("roundtrip", help="transform -> validate -> import -> compare")
    roundtrip_parser.add_argument("package")
    roundtrip_parser.add_argument("--work", default=None)
    roundtrip_parser.add_argument("--gate", action="store_true", help="run the Spine CLI import")
    roundtrip_parser.add_argument("--cli", default=None)
    roundtrip_parser.add_argument("--to-version", default=None)

    report_parser = sub.add_parser("report", help="validate every export under a directory")
    report_parser.add_argument("root")
    report_parser.add_argument("--json", action="store_true")

    for item in (validate_parser, inspect_parser, doc_parser, diff_parser,
                 transform_parser, roundtrip_parser):
        item.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate":
        atlas = args.atlas or str(Path(args.package).with_suffix(".atlas"))
        atlas_path = atlas if Path(atlas).is_file() else None
        document = _load(args.package)
        result = summarize_issues(validate(document, args.target_version, atlas_path))
        result["package"] = str(args.package)
        result["atlas_checked"] = atlas_path
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
              "\n".join(f"[{item['severity']}] {item['layer']}: {item['message']}"
                        for item in result["issues"]) or "clean" + f"\n{result['summary']}")
        if not args.json:
            print(f"\n{result['summary']}  -> {'OK' if result['ok'] else 'FAILED'}")
        return 0 if result["ok"] else 2

    if args.command == "inspect":
        result = inspect(_load(args.package))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "doc":
        document = _load(args.package)
        text = skeleton_doc(document, name=Path(args.package).stem)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(text)
        return 0

    if args.command == "diff":
        result = semantic_diff(_load(args.before), _load(args.after))
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
              "\n".join(result["changes"]) or "identical")
        return 0 if result["same"] else 2

    if args.command == "transform":
        if not args.set:
            print("ERROR: pass at least one --set name=argument", file=sys.stderr)
            return 1
        document = _load(args.package)
        original = copy.deepcopy(document)
        notes = []
        try:
            for item in args.set:
                name, _, argument = item.partition("=")
                document, more = apply_transform(document, name.strip(),
                                                 argument.strip() or None, args.risk)
                notes += more
        except (ValueError, KeyError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.to_version:
            spine_format.normalize_to_target(document, args.to_version)
            notes.append(f"re-encoded for Spine {args.to_version}")
        issues = summarize_issues(validate(document))
        result = {"ok": issues["ok"], "notes": notes, "validation": issues["summary"]}
        if args.preview:
            result["diff"] = semantic_diff(original, document)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if issues["ok"] else 2
        out = Path(args.out) if args.out else Path(args.package).with_suffix(".edited.json")
        _save(out, document)
        result["out"] = str(out)
        result["diff"] = semantic_diff(original, document)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if issues["ok"] else 2

    if args.command == "roundtrip":
        package = Path(args.package)
        work = Path(args.work) if args.work else package.parent / ".roundtrip"
        work.mkdir(parents=True, exist_ok=True)
        document = _load(package)
        if args.to_version:
            spine_format.normalize_to_target(document, args.to_version)
        staged = work / package.name
        _save(staged, document)
        report = {"steps": []}
        issues = summarize_issues(validate(document))
        report["steps"].append({"step": "validate", "ok": issues["ok"],
                                "detail": issues["summary"]})
        if args.gate:
            import spine_cli
            cli, _ = spine_cli.find_cli(args.cli)
            if cli is None:
                report["steps"].append({"step": "import", "ok": False,
                                        "detail": "no Spine CLI found"})
            else:
                gate = spine_cli.import_gate(cli, staged, work_dir=work / "import", name=package.stem)
                report["steps"].append({"step": "import", "ok": gate["ok"],
                                        "detail": gate.get("project") or gate.get("output", "")[:200]})
        report["ok"] = all(step["ok"] for step in report["steps"])
        report["package"] = str(package)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2

    root = Path(args.root)
    packages = sorted(path for path in root.rglob("*.json")
                      if path.name not in ("manifest.json", "export_report.json",
                                           "preview_report.json", "parts_manifest.json")
                      and not path.name.endswith(("_report.json", ".spine-doc.json")))
    results = []
    for package in packages:
        try:
            document = _load(package)
        except Exception:
            continue
        if "bones" not in document:
            continue
        atlas = package.with_suffix(".atlas")
        issues = summarize_issues(validate(document, None, atlas if atlas.is_file() else None))
        results.append({"package": str(package), "ok": issues["ok"],
                        "summary": issues["summary"]})
    failed = [item for item in results if not item["ok"]]
    payload = {"packages": len(results), "failed": len(failed), "results": results,
               "ok": not failed}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"[{'OK' if item['ok'] else 'FAIL'}] {item['package']}  {item['summary']}")
        print(f"\n{len(results) - len(failed)}/{len(results)} clean")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
