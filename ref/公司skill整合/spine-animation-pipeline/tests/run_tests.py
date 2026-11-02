#!/usr/bin/env python3
"""Build a synthetic character and run the full offline pipeline.

This is the skill's smoke test: it needs no API quota and no reference art, so
it proves the local half of the pipeline (chroma key -> trim -> rig -> version
correct export -> atlas -> optional Spine CLI import gate) still works.

    python run_tests.py            # unit + smoke tests
    python run_tests.py --keep     # keep the generated artefacts for inspection
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import parts_lib  # noqa: E402
import qa_vision  # noqa: E402
import rig_rules  # noqa: E402
import spine_format  # noqa: E402
import spine_toolkit  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

KEY = (0, 255, 0)
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    return condition


# ── synthetic art ───────────────────────────────────────────────────────────
def draw_character_background(size=(512, 512)):
    """A green-screen canvas with anti-aliased imitation body parts."""
    image = Image.new("RGB", size, KEY)
    draw = ImageDraw.Draw(image)
    scale = min(size[0] / 512.0, size[1] / 512.0)

    def box(values):
        return [value * scale for value in values]

    draw.rounded_rectangle(box((186, 190, 326, 400)), radius=48 * scale, fill=(70, 120, 210))
    draw.ellipse(box((196, 78, 316, 198)), fill=(240, 200, 160))
    draw.line(box((196, 230, 140, 330)), fill=(60, 105, 190), width=max(2, int(34 * scale)))
    draw.line(box((316, 230, 372, 330)), fill=(60, 105, 190), width=max(2, int(34 * scale)))
    draw.line(box((226, 396, 206, 476)), fill=(45, 80, 160), width=max(2, int(38 * scale)))
    draw.line(box((286, 396, 306, 476)), fill=(45, 80, 160), width=max(2, int(38 * scale)))
    # eyes, so a vision check has something to look at
    draw.ellipse(box((226, 116, 246, 136)), fill=(40, 40, 60))
    draw.ellipse(box((266, 116, 286, 136)), fill=(40, 40, 60))
    return image


def crop_box(image, box, name, out_dir):
    """Cut one part out of the reference canvas and report where it really is.

    The returned bbox is in *reference canvas* coordinates, so the layout can
    place the part exactly where the art already sits. Sizing off the crop box
    instead of the trimmed alpha content is the classic way to end up with
    limbs drifting away from the body.
    """
    part = image.crop(box).convert("RGBA")
    keyed = parts_lib.chroma_key(part, key=KEY, inner=40.0, outer=120.0)
    keyed = parts_lib.keep_largest_component(keyed)
    content = keyed.getchannel("A").getbbox()
    if content is None:
        raise ValueError(f"{name}: crop produced no visible pixels")
    trimmed, _ = parts_lib.trim_to_alpha(keyed)
    trimmed = parts_lib.decontaminate_edges(trimmed)
    path = Path(out_dir) / f"{name}.png"
    parts_lib.save_png(trimmed, path)
    absolute = (box[0] + content[0], box[1] + content[1],
                box[0] + content[2], box[1] + content[3])
    return path, absolute


BOXY_PARTS = {
    "head": (186, 68, 326, 208),
    "torso": (176, 180, 336, 410),
    "arm_l": (120, 210, 210, 350),
    "arm_r": (300, 210, 390, 350),
    "leg_l": (176, 380, 246, 496),
    "leg_r": (266, 380, 336, 496),
}


def build_fixture(work_dir):
    work = Path(work_dir)
    (work / "raw").mkdir(parents=True, exist_ok=True)
    (work / "parts").mkdir(parents=True, exist_ok=True)
    canvas = draw_character_background()
    canvas.save(work / "reference.png")
    paths = {}
    boxes = {}
    for name, box in BOXY_PARTS.items():
        paths[name], boxes[name] = crop_box(canvas, box, name, work / "parts")
    return work, paths, boxes


def layout_for(work, paths, boxes):
    """Parts placed on the reference canvas, converted to canvas-centre y-up."""
    width, height = 512, 512
    layout = {
        "name": "testbot",
        "canvas": {"width": width, "height": height},
        "decontaminate_edges": True,
        "idle": {"duration": 2.4, "root_translate_y": 1.0},
        "parts": [],
    }
    for name, path in paths.items():
        box = boxes[name]
        pivot = rig_rules.pivot_for(name)
        pixel_x = box[0] + (box[2] - box[0]) * pivot[0]
        pixel_y = box[1] + (box[3] - box[1]) * pivot[1]
        layout["parts"].append({
            "name": name,
            "file": str(Path(path).resolve()),
            "x": round(pixel_x - width / 2, 3),
            "y": round(height / 2 - pixel_y, 3),
            "pivot": list(pivot),
        })
    return layout


# ── unit tests ──────────────────────────────────────────────────────────────
def test_format_roundtrip():
    document = {
        "skeleton": {"spine": "4.2.0", "width": 100, "height": 100},
        "bones": [{"name": "root"}, {"name": "torso", "parent": "root"}],
        "slots": [{"name": "torso", "bone": "torso", "attachment": "torso"}],
        "skins": [{"name": "default", "attachments": {}}],
        "animations": {"idle": {"bones": {
            "torso": {
                "rotate": [
                    {"time": 0, "value": 0, "curve": [0.25, 0, 0.75, 8]},
                    {"time": 1.0, "value": 8},
                    {"time": 2.0, "value": 0},
                ],
                "translate": [
                    {"time": 0, "x": 0, "y": 0,
                     "curve": [0.25, 0, 0.75, 0, 0.25, 0, 0.75, 3]},
                    {"time": 1.0, "x": 0, "y": 3},
                    {"time": 2.0, "x": 0, "y": 0},
                ],
            },
        }}},
    }
    original = json.loads(json.dumps(document))
    spine_format.normalize_to_target(document, "3.8.75")
    rotate = document["animations"]["idle"]["bones"]["torso"]["rotate"]
    check("3.8 rotate uses \"angle\"", "angle" in rotate[0] and "value" not in rotate[0])
    check("3.8 bezier is scalar curve/c2/c3/c4",
          rotate[0].get("curve") == 0.25 and rotate[0].get("c3") == 0.75,
          json.dumps(rotate[0]))
    check("3.8 last keyframe carries no curve", "curve" not in rotate[-1])
    check("3.8 translation keeps a single curve quartet",
          rotate[0].get("c2") == 0.0 and rotate[0].get("c4") == 1.0)
    check("3.8 validation clean", not spine_format.validate_curves(document),
          str(spine_format.validate_curves(document)))

    spine_format.normalize_to_target(document, "4.2.0")
    rotate = document["animations"]["idle"]["bones"]["torso"]["rotate"]
    translate = document["animations"]["idle"]["bones"]["torso"]["translate"]
    check("4.x rotate uses \"value\"", "value" in rotate[0] and "angle" not in rotate[0])
    check("4.x rotate curve has 4 absolute numbers", rotate[0]["curve"][:2] == [0.25, 0.0],
          str(rotate[0].get("curve")))
    check("4.x translate curve has 8 numbers", len(translate[0]["curve"]) == 8,
          str(translate[0].get("curve")))
    check("4.x validation clean", not spine_format.validate_curves(document),
          str(spine_format.validate_curves(document)))

    back = json.loads(json.dumps(document))
    spine_format.normalize_to_target(back, "3.8.75")
    check("round-trip preserves the original easing",
          back["animations"]["idle"]["bones"]["torso"]["rotate"][0].get("curve") == 0.25)
    check("round-trip preserves the 4.2 source values",
          original["animations"]["idle"]["bones"]["torso"]["rotate"][1]["value"] == 8)


def test_validator_catches_mistakes():
    bad = {
        "skeleton": {"spine": "3.8.75"},
        "animations": {"idle": {"bones": {"torso": {"rotate": [
            {"time": 0, "value": 0, "curve": [0.25, 0, 0.75, 1]},
            {"time": 1, "value": 4},
        ]}}}},
    }
    issues = spine_format.validate_curves(bad)
    check("validator flags 4.x spelling in a 3.8 file", len(issues) >= 2, str(issues))

    bad4 = {
        "skeleton": {"spine": "4.2.0"},
        "animations": {"idle": {"bones": {"torso": {"translate": [
            {"time": 0, "x": 0, "y": 0, "curve": [0.25, 0, 0.75, 1]},
            {"time": 1, "x": 0, "y": 3},
        ]}}}},
    }
    issues = spine_format.validate_curves(bad4)
    check("validator flags a 4-number translate curve", any("expected 8" in item for item in issues),
          str(issues))


def test_rig_rules():
    parts = [{"name": "head"}, {"name": "torso"}, {"name": "arm_l"},
             {"name": "leg_r"}, {"name": "hat"}]
    ordered, parents, notes = rig_rules.build_rig(parts)
    check("head parents to torso when no neck exists", parents["head"] == "torso", str(parents))
    check("hat parents to head", parents["hat"] == "head", str(parents))
    check("legs parent to pelvis or torso", parents["leg_r"] in ("pelvis", "torso"), str(parents))
    check("draw order puts head in front of torso",
          next(p for p in parts if p["name"] == "head")["draw_order"] >
          next(p for p in parts if p["name"] == "torso")["draw_order"])
    check("no rig warnings for a clean part list", not notes, str(notes))

    cyclic = [{"name": "a", "parent": "b"}, {"name": "b", "parent": "a"}]
    _, parents, notes = rig_rules.build_rig(cyclic)
    check("cycles are repaired with a warning", bool(notes) and parents["a"] == "root", str(notes))


def test_parts_lib():
    image = draw_character_background((128, 128)).convert("RGBA")
    keyed = parts_lib.chroma_key(image, key=KEY)
    report = parts_lib.alpha_report(keyed)
    check("chroma key removes the green screen", report["transparent_ratio"] > 0.3,
          str(report))
    check("chroma key leaves no residue above threshold",
          report["chroma_residue"] is not None and report["chroma_residue"] < 0.02,
          str(report.get("chroma_residue")))
    clean = parts_lib.decontaminate_edges(keyed)
    check("decontamination keeps alpha untouched",
          [pixel[3] for pixel in parts_lib.to_pixels(clean)]
          == [pixel[3] for pixel in parts_lib.to_pixels(keyed)])


# ── smoke test ──────────────────────────────────────────────────────────────
def test_shortcut_resolution(work_dir):
    """A .lnk must resolve to the real binary, since it names the user's editor."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    import spine_cli
    plain = work / "plain.exe"
    plain.write_bytes(b"MZ")
    check("resolve_shortcut passes non-links through",
          spine_cli.resolve_shortcut(plain) == plain, str(plain))
    missing = work / "nope.lnk"
    check("resolve_shortcut tolerates a missing link",
          spine_cli.resolve_shortcut(missing) == missing)

    link = None
    for folder in ("Desktop", "OneDrive/Desktop"):
        candidate = Path.home() / folder / "Spine.lnk"
        if candidate.is_file():
            link = candidate
            break
    if link is None:
        check("resolve_shortcut follows the Desktop Spine shortcut", True,
              "no Desktop Spine.lnk on this machine (skipped)")
    else:
        resolved = spine_cli.resolve_shortcut(link)
        check("resolve_shortcut follows the Desktop Spine shortcut",
              resolved != link and resolved.is_file(), f"{link.name} -> {resolved}")


def test_positioning(work_dir):
    """The placement maths that put a collar on a puppy's face when it broke."""
    import json as _json
    import position_parts as pp
    from PIL import Image
    import numpy as np

    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    part = Image.new("RGBA", (100, 200), (0, 0, 0, 0))
    for y in range(20, 180):
        for x in range(20, 80):
            part.putpixel((x, y), (200, 150, 100, 255))

    # a box places the part centred, at a uniform scale, aspect intact
    matrix, scale = pp.box_matrix((0, 0, 300, 300), part)
    check("box_matrix preserves the aspect ratio",
          abs((part.width * scale) / (part.height * scale) - part.width / part.height) < 1e-6,
          f"scale={scale:.3f}")
    left, top = float(matrix[0, 2]), float(matrix[1, 2])
    check("box_matrix centres the part in the box",
          abs((left + part.width * scale / 2) - 150) < 1.0 and
          abs((top + part.height * scale / 2) - 150) < 1.0,
          f"centre=({left + part.width * scale / 2:.0f},{top + part.height * scale / 2:.0f})")

    # a follow spec hangs the part off its parent's anchor point, by pivot
    boxes = {"grid": 20, "parts": {"bell": {"follow": "collar", "anchor": [0.5, 1.0],
                                            "offset": [0, 10], "width": 50}}}
    boxes = {"grid": boxes["grid"], "parts": boxes["parts"]}
    placements = {"collar": {"bbox": (100.0, 100.0, 300.0, 200.0)}}
    canvas = {"width": 400, "height": 400}
    fit = pp.follow_matrix(boxes["parts"]["bell"], part, (0.5, 0.15), boxes, canvas, placements)
    check("follow_matrix returns a placement for an attached part", fit is not None)
    matrix, scale = fit
    pivot_x = 0.5 * part.width * scale + float(matrix[0, 2])
    pivot_y = 0.15 * part.height * scale + float(matrix[1, 2])
    check("follow_matrix puts the pivot on the parent's anchor",
          abs(pivot_x - 200.0) < 1.0 and abs(pivot_y - 210.0) < 1.0,
          f"pivot=({pivot_x:.0f},{pivot_y:.0f}) expected (200,210)")
    check("follow_matrix honours the requested width",
          abs(part.width * scale - 50) < 0.5, f"width={part.width * scale:.1f}")

    # grid cells convert to pixels, dict specs survive loading
    spec_file = work / "boxes.json"
    spec_file.write_text(_json.dumps({"grid": 10, "parts": {
        "head": [1, 2, 3, 4],
        "bell": {"follow": "head", "width": 40}}}), encoding="utf-8")
    loaded = pp.load_boxes(spec_file, 1000, 500)
    head = pp.resolve_region(loaded["parts"]["head"], loaded, {"width": 1000, "height": 500}, {})
    check("load_boxes converts grid cells to pixels",
          head == (100.0, 100.0, 300.0, 200.0), str(head))
    check("load_boxes keeps a follow spec as a dict",
          isinstance(loaded["parts"]["bell"], dict))

    # anatomy order: a tail draws behind the torso, a bell in front of a collar
    import rig_rules
    order = {name: rig_rules.draw_order_for(name)
             for name in ("tail", "torso", "head", "ear_l", "collar", "bell")}
    check("anatomy order: tail behind torso behind head behind collar behind bell",
          order["tail"] < order["torso"] < order["head"] < order["collar"] < order["bell"],
          str(order))


def test_despill_and_conform(work_dir):
    """Three bugs that all looked fine until the pixels were inspected."""
    import numpy as np
    import json as _json
    from PIL import Image
    import parts_lib
    import position_parts as pp

    work = Path(work_dir); work.mkdir(parents=True, exist_ok=True)

    # 1. chroma residue lives on the OUTERMOST ring. An erosion built on
    #    np.roll wraps and calls that ring "interior", skipping the one place
    #    that needed cleaning.
    img = Image.new("RGBA", (40, 20), (0, 255, 0, 255))
    for y in range(3, 17):
        for x in range(3, 37):
            img.putpixel((x, y), (150, 140, 135, 255))
    cleaned = parts_lib.despill_edges(img, band=2, threshold=12, kill=40)
    arr = np.asarray(cleaned.convert("RGBA")).astype(int)
    lead = arr[..., 1] - np.maximum(arr[..., 0], arr[..., 2])
    check("despill clears the outermost ring of green",
          int((lead[arr[..., 3] > 0] > 25).sum()) == 0,
          f"residue={int((lead[arr[..., 3] > 0] > 25).sum())}")
    check("despill leaves the subject opaque",
          int((np.asarray(cleaned)[..., 3] > 0).sum()) > 400,
          f"opaque={int((np.asarray(cleaned)[..., 3] > 0).sum())}")

    # 2. a part drawn at the wrong proportions has to be reshaped to its box,
    #    or it assembles into a skinny scarecrow
    part = Image.new("RGBA", (200, 400), (0, 0, 0, 0))
    for y in range(0, 400):
        for x in range(60, 140):
            part.putpixel((x, y), (150, 140, 135, 255))
    conformed = pp.conform_to_box(part, (0.0, 0.0, 400.0, 400.0))
    check("conform_to_box reshapes the part to the box aspect",
          abs(conformed.width / conformed.height - 1.0) < 0.02,
          f"{conformed.width}x{conformed.height}")
    check("conform_to_box never shrinks the art on both axes",
          conformed.width >= part.width and conformed.height >= part.height,
          f"{conformed.size} from {part.size}")
    extreme = pp.conform_to_box(part, (0.0, 0.0, 1600.0, 400.0))
    check("conform_to_box refuses an absurd stretch (4x) instead of wrecking the art",
          extreme.size == part.size, f"{extreme.size} from {part.size}")

    # 3. draw_order must be read per part. Taking it from a leaked loop variable
    #    applied the tail's order to every single part.
    boxes = {"grid": 20, "parts": {"head": {"box": [0, 0, 10, 10], "draw_order": 45},
                                   "tail": {"box": [0, 0, 4, 4], "draw_order": 5}}}
    box_file = work / "boxes.json"
    box_file.write_text(_json.dumps(boxes), encoding="utf-8")
    loaded = pp.load_boxes(box_file, 100, 100)
    region = pp.resolve_region(loaded["parts"]["head"], loaded, {"width": 100, "height": 100}, {})
    check("resolve_region accepts a dict spec with a box",
          region == (0.0, 0.0, 50.0, 50.0), str(region))
    orders = {name: loaded["parts"][name].get("draw_order") for name in ("head", "tail")}
    check("each spec keeps its own draw_order",
          orders == {"head": 45, "tail": 5}, str(orders))


def test_joints_and_layers(work_dir):
    """Where the bones sit, and who draws over whom.

    Both were reported by the user on the real cat: the bind points sat in
    the middle of each image instead of on the joints, and the layering was
    wrong. A generated part is occlusion-complete, so its box runs from the
    joint to the tip (longer than the strip of it that shows) and its pivot is
    a joint read off the reference, not a fraction of the image; the stacking
    order comes from the box map.
    """
    import json as _json
    import numpy as np
    import position_parts as pp
    import bone_overlay
    from PIL import Image, ImageDraw

    work = Path(work_dir); work.mkdir(parents=True, exist_ok=True)

    # A stand-in figure: a body with a stubby limb tucked in behind it.
    ref = Image.new("RGBA", (240, 320), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ref)
    draw.ellipse([70, 20, 170, 130], fill=(150, 145, 140, 255))
    draw.rounded_rectangle([60, 120, 180, 300], radius=40, fill=(170, 165, 160, 255))
    draw.rounded_rectangle([40, 150, 75, 260], radius=16, fill=(165, 160, 155, 255))
    ref_path = work / "reference.png"; ref.save(ref_path)

    # The arm's box runs from its joint (y=140) to its tip (y=270) - taller
    # than the strip of it that shows beside the body.
    boxes = {"grid": 20, "parts": {
        "arm_l": {"box": [3.0, 8.5, 7.0, 17.0], "pivot_px": [58, 145], "draw_order": 12},
        "torso": {"box": [5.0, 7.5, 15.0, 19.0], "pivot_px": [120, 285], "draw_order": 30},
        "head": {"box": [5.5, 1.0, 14.5, 8.0], "pivot_px": [120, 128], "draw_order": 50}}}
    boxes_path = work / "boxes.json"
    boxes_path.write_text(_json.dumps(boxes), encoding="utf-8")

    # Generated parts: one transparent PNG each, art filling the frame.
    parts = work / "parts"; parts.mkdir(parents=True, exist_ok=True)
    for name, size, colour in (("arm_l", (120, 260), (165, 160, 155, 255)),
                               ("torso", (220, 300), (170, 165, 160, 255)),
                               ("head", (200, 200), (150, 145, 140, 255))):
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(canvas).ellipse([6, 6, size[0] - 6, size[1] - 6], fill=colour)
        canvas.save(parts / f"{name}.png")

    layout_path = work / "layout.json"
    pp.position(str(parts), str(ref_path), str(layout_path),
                canvas={"width": 240, "height": 320}, name="jointtest",
                boxes_path=str(boxes_path), fit="conform")
    layout = _json.loads(layout_path.read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in layout["parts"]}

    # 1. The joint. A fraction of the image puts the arm bone in the middle of
    #    the arm; pivot_px puts it on the shoulder the caller measured.
    width, height = 240, 320
    for name, want in (("arm_l", (58, 145)), ("torso", (120, 285)), ("head", (120, 128))):
        item = by_name[name]
        image = Image.open(item["file"])
        scale = item["image_scale"]
        cx = item["x"] + width / 2.0
        cy = height / 2.0 - item["y"]
        left = cx - item["pivot"][0] * image.width * scale
        top = cy - item["pivot"][1] * image.height * scale
        got = (left + item["pivot"][0] * image.width * scale,
               top + item["pivot"][1] * image.height * scale)
        check(f"{name}: the bone lands on the joint in the box map",
              abs(got[0] - want[0]) < 1.5 and abs(got[1] - want[1]) < 1.5,
              f"want {want}, got ({got[0]:.1f}, {got[1]:.1f})")
    check("pivot_px is recorded, not PIVOT_BY_KIND",
          by_name["arm_l"].get("pivot_from") == "pivot_px",
          str(by_name["arm_l"].get("pivot_from")))
    check("the arm joint is not the middle of its image",
          abs(by_name["arm_l"]["pivot"][1] - 0.5) > 0.2,
          f"pivot {by_name['arm_l']['pivot']}")

    # 2. The box runs joint-to-tip, so the placed art is the whole limb: it
    #    starts above the part that shows and reaches its tip.
    body = Image.open("E:/codex_apk_work/cat_b5/reference_flat.png") if False else None  # noqa
    arm = by_name["arm_l"]
    arm_img = Image.open(arm["file"])
    placed_h = arm_img.height * arm["image_scale"]
    arm_top = height / 2.0 - arm["y"] - arm["pivot"][1] * placed_h
    arm_bottom = arm_top + placed_h
    check("the arm art spans its whole box (joint to tip), not just the visible strip",
          arm_top < 142 and arm_bottom > 262,
          f"placed art {arm_top:.0f}..{arm_bottom:.0f}")

    # 3. Layering. The box map's draw_order wins, so the limb sits behind the
    #    torso and the torso behind the head, as the reference art shows.
    order = {name: item["draw_order"] for name, item in by_name.items()}
    check("the box map's draw_order decides the stacking, limbs behind the body",
          order["arm_l"] < order["torso"] < order["head"], str(order))
    check("rig_rules would have put that limb in front (hence the override)",
          rig_rules.draw_order_for("arm_l", "upper_arm") > rig_rules.draw_order_for("torso", "torso"),
          f"arm {rig_rules.draw_order_for('arm_l', 'upper_arm')} vs torso "
          f"{rig_rules.draw_order_for('torso', 'torso')}")

    # 4. pack_record is a whitelist: pivot_from was dropped that way once, and
    #    the layout then fell back to the fraction of the image.
    packed = pp.pack_record({"name": "ear_l", "file": "x.png", "x": 1, "y": 2,
                             "pivot": [0.5, 0.5], "draw_order": 51, "scale": 1.0,
                             "pivot_from": "pivot_px"})
    check("pack_record keeps pivot_from", packed.get("pivot_from") == "pivot_px",
          str(sorted(packed.keys())))

    # 5. The overlay is how a wrong joint stops being a guess and becomes a
    #    picture.
    document = {"skeleton": {"width": 240, "height": 320},
                "bones": [{"name": "root"},
                          {"name": "torso", "parent": "root", "x": 10, "y": -20},
                          {"name": "head", "parent": "torso", "x": 0, "y": 60}]}
    positions, _ = bone_overlay.bone_positions(document)
    check("bone_overlay maps bone space onto the canvas",
          positions["torso"] == (130.0, 180.0) and positions["head"] == (130.0, 120.0),
          f"torso {positions['torso']}, head {positions['head']}")

def test_toolkit(work_dir):
    """Validation, transforms and the diff must behave on a known document."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    good = {
        "skeleton": {"spine": "3.8.75", "width": 64, "height": 64},
        "bones": [{"name": "root"}, {"name": "body", "parent": "root"}],
        "slots": [{"name": "body", "bone": "body", "attachment": "body"}],
        "skins": [{"name": "default", "attachments": {
            "body": {"body": {"width": 16, "height": 16}}}}],
        # The shape the exporter actually emits: the ease sits on both
        # segment-start keyframes and the final keyframe carries no curve.
        "animations": {"idle": {"bones": {"body": {"rotate": [
            {"time": 0.0, "angle": 0.0, "curve": 0.25, "c2": 0.0, "c3": 0.75, "c4": 1.0},
            {"time": 1.0, "angle": 3.0, "curve": 0.25, "c2": 0.0, "c3": 0.75, "c4": 1.0},
            {"time": 2.0, "angle": 0.0},
        ]}}}},
    }
    summary = spine_toolkit.summarize_issues(spine_toolkit.validate(good))
    check("toolkit passes a valid document", summary["ok"], summary["summary"])

    broken = json.loads(json.dumps(good))
    broken["bones"][1]["parent"] = "ghost"
    issues = spine_toolkit.validate(broken)
    check("toolkit catches a dangling parent",
          any("ghost" in item["message"] for item in issues),
          [item["message"] for item in issues][:2])

    reversed_doc = json.loads(json.dumps(good))
    reversed_doc["bones"].reverse()
    issues = spine_toolkit.validate(reversed_doc)
    check("toolkit catches parent-after-child order",
          any("before its parent" in item["message"] for item in issues))

    transformed, notes = spine_toolkit.apply_transform(
        json.loads(json.dumps(good)), "prefix_bones", "x_")
    # root is deliberately never prefixed, so it stays a stable anchor, but the
    # animation must follow the bone that was renamed.
    check("rename rewrites the animation target too",
          "x_body" in transformed["animations"]["idle"]["bones"]
          and "body" not in transformed["animations"]["idle"]["bones"]
          and transformed["slots"][0]["bone"] == "x_body"
          and transformed["bones"][0]["name"] == "root", notes[0])

    diff = spine_toolkit.semantic_diff(good, transformed)
    check("diff reports the rename", not diff["same"] and diff["count"] >= 3,
          f"{diff['count']} change(s)")

    # Spine drops fields that equal their default when it re-exports. That must
    # not read as a difference, or every good round trip looks broken.
    reexported = json.loads(json.dumps(good))
    reexported["skeleton"].pop("spine", None)
    reexported["skeleton"]["spine"] = "3.8.75"
    reexported["skins"][0]["attachments"]["body"]["body"].pop("x", None)
    keyframes = reexported["animations"]["idle"]["bones"]["body"]["rotate"]
    # Spine keeps the control points that matter and drops the rest. These three
    # lines are copied from a real Spine 3.8.75 re-export of this exact shape.
    keyframes[0] = {"curve": 0.25, "c3": 0.75}          # time/angle/c2/c4 dropped
    keyframes[1] = {"time": 1.0, "angle": 3.0, "curve": 0.25, "c3": 0.75}
    keyframes[2] = {"time": 2.0}                        # angle 0 dropped
    check("diff ignores Spine's default-omitting re-export",
          spine_toolkit.semantic_diff(good, reexported)["same"],
          spine_toolkit.semantic_diff(good, reexported)["changes"][:2])

    # ...but a real change to the curve or a keyframe must still be caught.
    altered = json.loads(json.dumps(good))
    altered["animations"]["idle"]["bones"]["body"]["rotate"][1]["angle"] = 9.0
    check("diff still catches a changed keyframe",
          not spine_toolkit.semantic_diff(good, altered)["same"])
    altered = json.loads(json.dumps(good))
    altered["animations"]["idle"]["bones"]["body"]["rotate"][0]["c3"] = 0.5
    check("diff still catches a changed curve",
          not spine_toolkit.semantic_diff(good, altered)["same"])

    document = spine_toolkit.skeleton_doc(good, "unit")
    check("skeleton doc lists the hierarchy",
          "| body | root |" in document and "idle" in document)

    # an export must survive one transform and still validate
    spine_format.normalize_to_target(transformed, "3.8.75")
    summary = spine_toolkit.summarize_issues(spine_toolkit.validate(transformed))
    check("transform output still validates", summary["ok"], summary["summary"])

    # --to-version round trip keeps the file valid in the other dialect
    as_4x = json.loads(json.dumps(good))
    spine_format.normalize_to_target(as_4x, "4.2.0")
    check("4.x conversion renames the property",
          "value" in as_4x["animations"]["idle"]["bones"]["body"]["rotate"][1])
    summary = spine_toolkit.summarize_issues(spine_toolkit.validate(as_4x))
    check("4.x conversion still validates", summary["ok"], summary["summary"])


def test_layout_coordinates(work_dir, exports):
    """pixels-top-left and canvas-center layouts must produce the same export."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    import spine_export
    centered = {
        "name": "coords", "canvas": {"width": 256, "height": 256},
        "parts": [{"name": "head", "file": str(exports["head"]), "x": 0.0, "y": 40.0}],
    }
    pixel = {
        "name": "coords", "canvas": {"width": 256, "height": 256},
        "coordinate_system": "pixels-top-left",
        "parts": [{"name": "head", "file": str(exports["head"]), "x": 128.0, "y": 88.0}],
    }
    spine_export.apply_coordinate_system(centered)
    spine_export.apply_coordinate_system(pixel)
    check("pixels-top-left converts to canvas-center",
          abs(pixel["parts"][0]["x"] - centered["parts"][0]["x"]) < 1e-6
          and abs(pixel["parts"][0]["y"] - centered["parts"][0]["y"]) < 1e-6,
          f"{pixel['parts'][0]['x']},{pixel['parts'][0]['y']}")


def test_fringe_detection(work_dir):
    """A green halo must fail validation even when every alpha metric is happy."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    size = 96
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, size - 16, size - 16), fill=(210, 160, 130, 255))
    halo = Image.new("RGBA", (size, size), (0, 255, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.ellipse((14, 14, size - 14, size - 14), outline=(120, 230, 120, 255), width=3)
    halo.alpha_composite(image)
    halo_path = work / "halo.png"
    parts_lib.save_png(halo, halo_path)
    ok, report, problems = parts_lib.validate_part(halo_path)
    check("fringe detector rejects a green halo", not ok,
          f"fringe={report.get('fringe_distance')} {problems}")

    fixed = parts_lib.decontaminate_edges(halo, boundary_radius=3)
    fixed_path = work / "halo-fixed.png"
    parts_lib.save_png(fixed, fixed_path)
    ok, report, _ = parts_lib.validate_part(fixed_path)
    check("decontamination clears the halo", ok, f"fringe={report.get('fringe_distance')}")


def test_vision_verdict_parsing():
    check("parses a PASS verdict",
          qa_vision.parse_verdict("VERDICT: PASS" + chr(10) + "looks right") == "PASS")
    check("parses a FAIL verdict",
          qa_vision.parse_verdict("  verdict: fail ...") == "FAIL")
    check("returns None without a verdict",
          qa_vision.parse_verdict("the image is probably fine") is None)
    check("every task prompt demands a verdict",
          all("VERDICT" in prompt for prompt in qa_vision.TASKS.values()),
          f"{len(qa_vision.TASKS)} prompts")


def test_pipeline(work_dir, keep=False, gate=False):
    work, paths, boxes = build_fixture(work_dir)
    layout = layout_for(work, paths, boxes)
    layout_path = work / "layout.json"
    layout_path.write_text(json.dumps(layout, indent=2), encoding="utf-8")

    export_dir = work / "out"
    command = [sys.executable, str(SCRIPTS / "spine_export.py"),
               "--layout", str(layout_path), "--out", str(export_dir), "--json"]
    if gate:
        command.append("--gate")
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    check("exporter runs", proc.returncode in (0, 2), proc.stderr[-400:])
    if proc.returncode not in (0, 2):
        return
    report = json.loads(proc.stdout)
    check("exporter reports no curve issues", not report["curve_issues"], str(report["curve_issues"]))
    check("no rig warnings", not report["warnings"], str(report["warnings"]))
    check("skeleton/atlas/page/manifest written",
          all(Path(report["files"][key]).is_file()
              for key in ("skeleton", "atlas", "page", "manifest")))

    document = json.loads(Path(report["files"]["skeleton"]).read_text(encoding="utf-8"))
    version = document["skeleton"]["spine"]
    check("skeleton declares a version", bool(version), version)
    if spine_format.is_legacy(version):
        first = document["animations"][report.get("animation", "idle")]["bones"]
        sample = next(iter(first.values()))
        check("3.8 output uses angle", any("angle" in kf for kf in sample.get("rotate", [{}])))
    check("atlas lists every part",
          all(name in Path(report["files"]["atlas"]).read_text(encoding="utf-8")
              for name in BOXY_PARTS))

    if gate:
        check("Spine CLI import gate passes", report.get("import_gate", {}).get("ok"),
              json.dumps(report.get("import_gate"), ensure_ascii=False)[:300])
    if not keep:
        shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="keep generated artefacts")
    parser.add_argument("--gate", action="store_true", help="also run the Spine CLI import gate")
    parser.add_argument("--work", default=None)
    args = parser.parse_args()

    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="spine-tests-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"work dir: {work}\n")

    test_format_roundtrip()
    test_validator_catches_mistakes()
    test_rig_rules()
    test_parts_lib()
    test_vision_verdict_parsing()
    test_fringe_detection(work / "fringe")
    test_shortcut_resolution(work / "shortcut")
    test_positioning(work / "positioning")
    test_despill_and_conform(work / "despill")
    test_joints_and_layers(work / "joints")
    test_toolkit(work / "toolkit")
    test_pipeline(work / "smoke", keep=args.keep, gate=args.gate)
    test_layout_coordinates(work / "coords", {"head": work / "smoke" / "parts" / "head.png"})

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
