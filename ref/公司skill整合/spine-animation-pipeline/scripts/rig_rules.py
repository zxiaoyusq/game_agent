#!/usr/bin/env python3
"""Deterministic rigging rules: part name -> bone, parent, draw order, pivot.

This file exists so the agent never has to invent a skeleton from scratch. The
upstream project (GenielabsOpenSource/spine-animation-ai) asks the model to
"determine the bone hierarchy from the part names and visual layout"; that is
exactly the step a text-only model gets wrong. Here it is a lookup table, and
every value can still be overridden per part in the layout JSON.

Draw order follows the upstream layer stack, back to front:

    tail -> wings -> complete body -> rear limbs -> body-front limbs
         -> full head -> hair -> ears -> hat -> collar -> bell -> accessory
"""

from __future__ import annotations

import json
import re

# ── part classification ─────────────────────────────────────────────────────
# (regex, kind). First match wins, so the most specific patterns come first.
KIND_PATTERNS = [
    # Facial features, matched before anything else. They hang off the head, not
    # the torso, and they are the parts a desktop pet animates most - a blink, a
    # glance, a talking mouth - so a facial part that silently lands on an
    # accessory bone under the body is a rig that cannot show an expression.
    (r"(eyelid|eye|眼|眼睛)", "eye"),
    (r"(brow|eyebrow|眉)", "brow"),
    (r"(whisker|whisk|胡须|胡子|须)", "whisker"),
    (r"(cheek|blush|freckle|颊|腮红|斑点)", "cheek"),
    (r"(mouth|lip|嘴|口|唇)", "mouth"),
    (r"(nose|nostril|鼻)", "nose"),
    (r"(upper[-_ ]?arm|shoulder[-_ ]?arm|大臂|上臂|肩膀|肩)", "upper_arm"),
    (r"(lower[-_ ]?arm|fore[-_ ]?arm|小臂|前臂|下臂)", "lower_arm"),
    (r"(upper[-_ ]?leg|thigh|大腿)", "upper_leg"),
    (r"(lower[-_ ]?leg|shin|calf|小腿)", "lower_leg"),
    (r"(foot|feet|脚|足)", "foot"),
    # Generic limb names come after the specific ones, so "lower-leg" and
    # "thigh" win; a bare "leg" / "arm" still lands on a sensible joint.
    (r"(arm|臂|胳膊|上肢)", "upper_arm"),
    (r"(leg|腿|下肢)", "upper_leg"),
    (r"(hand|paw|fist|手|爪|掌)", "hand"),
    (r"(head|face|muzzle|snout|头部|脸|头|口鼻)", "head"),
    (r"(neck|脖子|颈)", "neck"),
    (r"(torso|body|chest|trunk|身体|躯干|身子|胸)", "torso"),
    (r"(pelvis|hip|waist|胯|腰|臀部)", "pelvis"),
    (r"(tail|尾巴|尾)", "tail"),
    (r"(ear|耳朵|耳)", "ear"),
    (r"(wing|翅膀|翼)", "wing"),
    (r"(hair|mane|fringe|头发|鬃毛|刘海)", "hair"),
    (r"(hat|cap|sombrero|helmet|帽子|帽|头盔)", "hat"),
    (r"(collar|scarf|tie|领子|领结|围巾)", "collar"),
    (r"(bell|铃铛|铃)", "bell"),
]

# Kinds that hang off the head, not the torso.
HEAD_CHILDREN = {"ear", "hair", "hat", "collar",
                 "eye", "brow", "whisker", "cheek", "mouth", "nose"}
# Kinds that hang off the pelvis.
PELVIS_CHILDREN = {"upper_leg", "tail"}


def classify(name):
    """Map a part name onto a rig kind; 'accessory' when nothing matches."""
    text = str(name).lower().replace("_", "-")
    for pattern, kind in KIND_PATTERNS:
        if re.search(pattern, text):
            return kind
    return "accessory"


def side_of(name):
    """'far', 'near' or None. Far limbs are drawn behind the body."""
    text = str(name).lower()
    if re.search(r"(back|rear|far|behind|后|背)", text):
        return "far"
    if re.search(r"(front|near|前)", text):
        return "near"
    return None


def is_left(name):
    text = str(name).lower()
    if re.search(r"(^|[-_ ])(l|left)([-_ ]|$)|左", text):
        return True
    if re.search(r"(^|[-_ ])(r|right)([-_ ]|$)|右", text):
        return False
    return None


# ── default parents ─────────────────────────────────────────────────────────
PARENT_BY_KIND = {
    "head": "neck",
    "neck": "torso",
    "hair": "head",
    "ear": "head",
    "hat": "head",
    "collar": "neck",
    "bell": "collar",
    "upper_arm": "torso",
    "lower_arm": "upper_arm",
    "hand": "lower_arm",
    "torso": "pelvis",
    "pelvis": "root",
    "upper_leg": "pelvis",
    "lower_leg": "upper_leg",
    "foot": "lower_leg",
    "tail": "pelvis",
    "wing": "torso",
    "accessory": "torso",
    # Facial features ride the head bone: they must follow the head, never
    # wobble on a bone of their own.
    "eye": "head",
    "brow": "head",
    "whisker": "head",
    "cheek": "head",
    "mouth": "head",
    "nose": "head",
}


def default_parent(name, kind=None):
    """Parent kind for a part, or 'root' when the kind is self-supporting."""
    kind = kind or classify(name)
    parent_kind = PARENT_BY_KIND.get(kind, "root")
    return parent_kind


# ── draw order ──────────────────────────────────────────────────────────────
BASE_DRAW_ORDER = {
    "tail": 5,
    "wing": 8,
    "pelvis": 12,
    "torso": 14,
    "upper_leg": 20,
    "lower_leg": 22,
    "foot": 24,
    "upper_arm": 30,
    "lower_arm": 32,
    "hand": 34,
    "neck": 40,
    "head": 45,
    "hair": 50,
    "ear": 52,
    "hat": 56,
    "collar": 60,
    "bell": 62,
    "accessory": 70,
    # On the face, back to front. The spots are markings on the clay, the
    # whiskers and mouth sit on the muzzle, the nose is a solid piece and the
    # eyes are the topmost layer.
    "cheek": 51,
    "whisker": 52,
    "mouth": 53,
    "nose": 54,
    "eye": 55,
    "brow": 54,
}


def draw_order_for(name, kind=None):
    """Numeric draw order; lower is further back. Side offsets break ties."""
    kind = kind or classify(name)
    order = BASE_DRAW_ORDER.get(kind, 40)
    side = side_of(name)
    if side == "far":
        order -= 4
    elif side == "near":
        order += 4
    elif is_left(name) is True:
        order -= 1
    elif is_left(name) is False:
        order += 1
    return float(order)


def sort_back_to_front(parts):
    """Stable back-to-front ordering, honouring an explicit draw_order."""
    indexed = list(enumerate(parts))
    indexed.sort(key=lambda item: (float(item[1].get("draw_order", draw_order_for(item[1]["name"]))),
                                   item[1]["name"], item[0]))
    return [part for _, part in indexed]


# ── pivots ──────────────────────────────────────────────────────────────────
# Pivot = where the bone/joint sits inside the trimmed image, as a fraction of
# width/height measured from the TOP-LEFT of the image.
PIVOT_BY_KIND = {
    "head": (0.5, 0.90),
    "hair": (0.5, 0.15),
    "ear": (0.5, 0.85),
    "hat": (0.5, 0.95),
    "neck": (0.5, 0.90),
    "torso": (0.5, 0.85),
    "pelvis": (0.5, 0.20),
    "collar": (0.5, 0.40),
    "bell": (0.5, 0.15),
    "upper_arm": (0.5, 0.12),
    "lower_arm": (0.5, 0.12),
    "hand": (0.5, 0.25),
    "upper_leg": (0.5, 0.12),
    "lower_leg": (0.5, 0.12),
    "foot": (0.5, 0.30),
    "tail": (0.85, 0.5),
    "wing": (0.85, 0.5),
    "accessory": (0.5, 0.5),
    "eye": (0.5, 0.5),       # a glance is a translation, not a rotation
    "brow": (0.5, 0.9),
    "whisker": (0.0, 0.5),   # inner end: a twitch pivots at the cheek
    "cheek": (0.5, 0.5),
    "mouth": (0.5, 0.15),    # hinge at the top, so an open mouth swings down
    "nose": (0.5, 0.85),
}


def pivot_for(name, kind=None):
    kind = kind or classify(name)
    pivot = PIVOT_BY_KIND.get(kind, (0.5, 0.5))
    if is_left(name) is True:
        return (1.0 - pivot[0], pivot[1])
    return pivot


# ── idle defaults ───────────────────────────────────────────────────────────
# Restrained motion, per the upstream and Codex guidance: breathing on the
# body/head, small ear/hat follow-through, delayed bell swing.

IDLE_BY_KIND = {
    "head": {"idle_rotate": -2.4, "idle_phase": 0.5},
    "neck": {"idle_rotate": 1.0, "idle_phase": 0.45},
    "torso": {"idle_rotate": 1.6, "idle_phase": 0.35},
    "pelvis": {"idle_translate_y": 4.0, "idle_phase": 0.25},
    "hair": {"idle_rotate": 3.0, "idle_phase": 0.62},
    "ear": {"idle_rotate": 5.0, "idle_phase": 0.58},
    "hat": {"idle_rotate": 2.0, "idle_phase": 0.68},
    "collar": {"idle_rotate": 1.6, "idle_phase": 0.7},
    "bell": {"idle_rotate": 9.0, "idle_phase": 0.78},
    "tail": {"idle_rotate": 6.0, "idle_phase": 0.45},
    "wing": {"idle_rotate": 3.5, "idle_phase": 0.55},
    "upper_arm": {"idle_rotate": 2.4, "idle_phase": 0.6},
    "lower_arm": {"idle_rotate": 1.6, "idle_phase": 0.66},
    "hand": {"idle_rotate": 2.4, "idle_phase": 0.72},
    "upper_leg": {"idle_rotate": 0.8, "idle_phase": 0.3},
    "lower_leg": {"idle_rotate": 0.6, "idle_phase": 0.35},
    "foot": {"idle_rotate": 0.9, "idle_phase": 0.4},
    "accessory": {"idle_rotate": 2.4, "idle_phase": 0.6},
    # The eyes stay still on purpose: an eye that drifts on its own reads as a
    # bug, and it already rides the head bone. Everything else gets a whisker
    # of motion so a face is not a mask.
    "eye": {},
    "cheek": {},
    "brow": {"idle_translate_y": 1.5, "idle_phase": 0.55},
    "whisker": {"idle_rotate": 1.2, "idle_phase": 0.66},
    "mouth": {"idle_rotate": 0.8, "idle_phase": 0.7},
    "nose": {"idle_translate_y": 0.8, "idle_phase": 0.5},
}


def idle_for(name, kind=None):
    kind = kind or classify(name)
    return dict(IDLE_BY_KIND.get(kind, {}))


# ── assembling a bone tree ──────────────────────────────────────────────────
def build_rig(parts, extra_bones=()):
    """Assign bone names, parents, draw order and idle defaults to `parts`.

    Returns (ordered_parts, bone_parents, notes). `parts` is mutated: every
    entry gains `kind`, `bone`, `parent`, `draw_order`, `pivot` and idle keys
    when the caller did not supply them.
    """
    notes = []
    by_kind = {}
    for part in parts:
        part.setdefault("kind", classify(part["name"]))
        if part["kind"] not in by_kind:
            by_kind[part["kind"]] = part["name"]

    # A part whose default parent kind has no matching part falls back to the
    # nearest existing ancestor instead of dangling.
    kind_parent_chain = {
        "head": ("neck", "torso", "pelvis"),
        "neck": ("torso", "pelvis"),
        "hair": ("head", "neck", "torso"),
        "ear": ("head", "neck", "torso"),
        "hat": ("head", "neck", "torso"),
        "collar": ("neck", "torso"),
        "bell": ("collar", "neck", "torso"),
        "upper_arm": ("torso", "pelvis"),
        "lower_arm": ("upper_arm", "torso"),
        "hand": ("lower_arm", "upper_arm", "torso"),
        "torso": ("pelvis",),
        "pelvis": (),
        # Legs hang off the pelvis, but a character that has no explicit pelvis
        # must still get a connected rig -- otherwise the legs would dangle.
        "upper_leg": ("pelvis", "torso"),
        "lower_leg": ("upper_leg", "pelvis", "torso"),
        "foot": ("lower_leg", "upper_leg", "pelvis", "torso"),
        "tail": ("pelvis", "torso"),
        "wing": ("torso", "pelvis"),
        "accessory": ("torso", "pelvis"),
        "eye": ("head", "neck", "torso"),
        "brow": ("head", "neck", "torso"),
        "whisker": ("head", "neck", "torso"),
        "cheek": ("head", "neck", "torso"),
        "mouth": ("head", "neck", "torso"),
        "nose": ("head", "neck", "torso"),
    }

    for part in parts:
        name = part["name"]
        part.setdefault("bone", name)
        if "parent" in part:
            continue
        chain = kind_parent_chain.get(part["kind"], ("torso",))
        parent = None
        for kind_name in chain:
            if kind_name in by_kind:
                parent = by_kind[kind_name]
                break
        if parent is None:
            parent = "root"
        # A limb segment whose natural parent is missing attaches to the
        # closest present ancestor rather than dangling.
        part["parent"] = parent

    # Explicit extra bones may be referenced as parents too.
    extra_names = {bone["name"] for bone in extra_bones}
    for part in parts:
        parent = part.get("parent", "root")
        if parent != "root" and parent not in extra_names and \
                parent not in {other["name"] for other in parts}:
            notes.append(f"{part['name']}: parent '{parent}' is unknown, attached to root")
            part["parent"] = "root"

    # Self-parenting and short cycles are the classic layout typo.
    by_name = {part["name"]: part for part in parts}
    for part in parts:
        seen = {part["name"]}
        cursor = part.get("parent")
        while cursor and cursor != "root":
            if cursor in seen:
                notes.append(f"{part['name']}: parent cycle through '{cursor}', attached to root")
                part["parent"] = "root"
                break
            seen.add(cursor)
            cursor = by_name.get(cursor, {}).get("parent")

    for part in parts:
        part.setdefault("draw_order", draw_order_for(part["name"], part["kind"]))
        part.setdefault("pivot", pivot_for(part["name"], part["kind"]))
        idle = idle_for(part["name"], part["kind"])
        for key, value in idle.items():
            part.setdefault(key, value)

    ordered = sort_back_to_front(parts)
    parents = {part["bone"]: part.get("parent", "root") for part in parts}
    for bone in extra_bones:
        parents.setdefault(bone["name"], bone.get("parent", "root"))
    return ordered, parents, notes


# ── self description ────────────────────────────────────────────────────────
def describe_kinds():
    """Every kind this module can classify, for `--list`."""
    rows = []
    for kind in sorted(set(PARENT_BY_KIND) | set(PIVOT_BY_KIND) | set(BASE_DRAW_ORDER)):
        pivot = PIVOT_BY_KIND.get(kind, (0.5, 0.5))
        rows.append({
            "kind": kind,
            "parent": PARENT_BY_KIND.get(kind, "root"),
            "pivot": list(pivot),
            "draw_order": BASE_DRAW_ORDER.get(kind, 60),
            "idle": IDLE_BY_KIND.get(kind, {}),
        })
    return rows


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Part naming rules for the Spine rig")
    parser.add_argument("--list", action="store_true", help="show every recognised kind")
    parser.add_argument("--classify", default=None, help="classify a comma-separated name list")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.classify:
        names = [item.strip() for item in args.classify.split(",") if item.strip()]
        result = {name: {"kind": classify(name), "parent": default_parent(name),
                         "pivot": list(pivot_for(name)),
                         "draw_order": draw_order_for(name)}
                  for name in names}
        rows = [f"{name:<14} {item['kind']:<12} parent={item['parent']:<12} "
                f"pivot={item['pivot']} order={item['draw_order']}"
                for name, item in result.items()]
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
              else chr(10).join(rows))
        return 0

    rows = describe_kinds()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print(f"{'kind':<12} {'parent':<12} {'pivot':<14} {'draw order':<11} idle")
    for row in rows:
        idle = ", ".join(f"{key}={value}" for key, value in row["idle"].items()) or "-"
        print(f"{row['kind']:<12} {row['parent']:<12} {str(row['pivot']):<14} "
              f"{row['draw_order']:<11} {idle}")
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
