#!/usr/bin/env python3
"""Render a Spine package into pictures and numbers a text-only agent can judge.

Outputs (in --out, default <package>/preview):
    setup_pose.png            the package's own setup pose, drawn from the atlas
    compare_reference.png     side-by-side + silhouette overlay, when a reference exists
    frames/frame_00..NN.png   the animation sampled across one loop
    preview.gif               the loop, for a human (and for a vision model)
    filmstrip.png             every frame in one image, for a single vision call
    preview.html              self-contained scrubber/player
    preview_report.json       PASS/FAIL gates and the numbers behind them

The report is the point: it turns "does this look right?" into facts.

    python make_preview.py --package out/testbot.json [--reference reference.png]
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import parts_lib
import spine_runtime


def reference_canvas(reference_path, size):
    """Load reference art onto the skeleton canvas so the two are comparable."""
    reference = parts_lib.load_rgba(reference_path)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    scale = min(size[0] / reference.width, size[1] / reference.height, 1.0)
    if scale != 1.0:
        reference = reference.resize((max(1, round(reference.width * scale)),
                                      max(1, round(reference.height * scale))),
                                     Image.Resampling.LANCZOS)
    canvas.alpha_composite(reference, ((size[0] - reference.width) // 2,
                                       (size[1] - reference.height) // 2))
    # Reference art is usually opaque-backed; keep only what differs from the
    # corner colour so the silhouette comparison is meaningful.
    return parts_lib.strip_solid_background(canvas)



def side_by_side(images, labels=None, background=(28, 30, 36, 255), gap=10):
    width = sum(image.width for image in images) + gap * (len(images) + 1)
    height = max(image.height for image in images) + gap * 2
    sheet = Image.new("RGBA", (width, height), background)
    x = gap
    for image in images:
        sheet.alpha_composite(image.convert("RGBA"), (x, gap + (height - gap * 2 - image.height) // 2))
        x += image.width + gap
    return sheet


def overlay(rendered, reference):
    """Red = rendered only, blue = reference only, grey = agreement."""
    if rendered.size != reference.size:
        reference = reference.resize(rendered.size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", rendered.size, (24, 24, 28, 255))
    left = parts_lib.to_pixels(rendered)
    right = parts_lib.to_pixels(reference)
    pixels = []
    for a, b in zip(left, right):
        a_on, b_on = a[3] > 24, b[3] > 24
        if a_on and b_on:
            pixels.append(((a[0] + b[0]) // 2, (a[1] + b[1]) // 2, (a[2] + b[2]) // 2, 255))
        elif a_on:
            pixels.append((235, 90, 90, 255))
        elif b_on:
            pixels.append((90, 140, 235, 255))
        else:
            pixels.append((24, 24, 28, 255))
    out.putdata(pixels)
    return out


def data_uri(image):
    buffer = BytesIO()
    image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def build_html(frames, duration, title):
    frame_uris = [data_uri(frame) for frame in frames]
    payload = json.dumps({"frames": frame_uris, "duration": duration})
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
 :root {{ color-scheme: dark; }}
 body {{ margin:0; background:#16181d; color:#e8e8ea;
        font:14px/1.5 "Segoe UI", system-ui, sans-serif;
        display:flex; flex-direction:column; align-items:center; gap:14px; padding:20px; }}
 h1 {{ font-size:16px; font-weight:600; margin:0; letter-spacing:.02em; }}
 .stage {{ background:#22252c; border-radius:12px; padding:14px;
           box-shadow:0 8px 30px rgba(0,0,0,.45); }}
 img {{ display:block; image-rendering:auto; max-width:min(78vw, 640px); }}
 .row {{ display:flex; align-items:center; gap:12px; width:min(78vw, 640px); }}
 button {{ background:#2f343d; color:#e8e8ea; border:1px solid #414856;
           border-radius:8px; padding:7px 15px; cursor:pointer; font:inherit; }}
 button:hover {{ background:#3a404b; }}
 input[type=range] {{ flex:1; accent-color:#7aa2f7; }}
 code {{ color:#9ece6a; }}
</style></head>
<body>
<h1>{title}</h1>
<div class="stage"><img id="view" alt="frame"></div>
<div class="row">
  <button id="toggle">Pause</button>
  <input id="scrub" type="range" min="0" max="1000" value="0">
  <span id="label">--</span>
</div>
<p style="opacity:.7">Frames rendered from the exported package by <code>make_preview.py</code>.
Open <code>preview.gif</code> for the plain animation, or import the atlas + JSON in Spine for the real thing.</p>
<script>
const data = {payload};
const view = document.getElementById('view');
const scrub = document.getElementById('scrub');
const label = document.getElementById('label');
const toggle = document.getElementById('toggle');
let playing = true, index = 0, last = performance.now();
let frameMs = (data.duration * 1000) / Math.max(1, data.frames.length);
function show(i) {{
  index = ((i % data.frames.length) + data.frames.length) % data.frames.length;
  view.src = data.frames[index];
  scrub.value = Math.round(index / Math.max(1, data.frames.length - 1) * 1000);
  label.textContent = 'frame ' + (index + 1) + '/' + data.frames.length;
}}
function tick(now) {{
  if (playing && now - last >= frameMs) {{ last = now; show(index + 1); }}
  requestAnimationFrame(tick);
}}
toggle.onclick = () => {{ playing = !playing; toggle.textContent = playing ? 'Pause' : 'Play'; }};
scrub.oninput = () => {{ playing = false; toggle.textContent = 'Play';
  show(Math.round(scrub.value / 1000 * (data.frames.length - 1))); }};
show(0); requestAnimationFrame(tick);
</script>
</body></html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a Spine package for QA")
    parser.add_argument("--package", required=True, help="path to <name>.json")
    parser.add_argument("--reference", default=None, help="reference art to compare against")
    parser.add_argument("--out", default=None, help="preview output directory")
    parser.add_argument("--animation", default=None, help="animation name (default: the first)")
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--min-iou", type=float, default=0.55,
                        help="fail below this silhouette overlap with the reference")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    package = Path(args.package).resolve()
    out_dir = Path(args.out).resolve() if args.out else package.parent / "preview"
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    skeleton, atlas, document = spine_runtime.load_package(package)
    problems = []
    if atlas is None:
        problems.append("no .atlas beside the package; the page image cannot be located")
        print("ERROR: " + problems[0], file=sys.stderr)
        return 1

    # 1. every slot must resolve to a real atlas region
    missing = []
    for slot in skeleton.slots:
        name = slot["attachment"]
        if not name:
            continue
        values = (skeleton.attachments.get(slot["name"]) or {}).get(name)
        region = (values or {}).get("path", name)
        if region not in atlas["regions"]:
            missing.append(f"{slot['name']}->{region}")
    if missing:
        problems.append(f"atlas is missing regions for: {', '.join(missing)}")

    # 2. setup pose
    setup = spine_runtime.render(skeleton, atlas, skeleton.setup_pose())
    setup_path = out_dir / "setup_pose.png"
    setup.save(setup_path)
    coverage = parts_lib.alpha_report(setup)["opaque_ratio"]
    if coverage < 0.02:
        problems.append(f"setup pose renders almost nothing (opaque {coverage})")

    # 3. animation
    animations = skeleton.animation_names()
    animation = args.animation or (animations[0] if animations else None)
    motion = {"animation": animation, "samples": 0, "max_frame_delta": 0.0}
    frames = [setup]
    gif_path = filmstrip_path = None
    if animation:
        motion = spine_runtime.motion_report(skeleton, atlas, animation, samples=args.samples)
        frames = motion.pop("frames")
        for index, frame in enumerate(frames):
            frame.save(frames_dir / f"frame_{index:02d}.png")
        duration_ms = max(40, int(round(motion["duration"] * 1000 / max(1, len(frames)))))
        gif_path = out_dir / "preview.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                       duration=duration_ms, loop=0, disposal=2)
        filmstrip_path = parts_lib.filmstrip(frames, out_dir / "filmstrip.png", columns=4)
        if motion["max_frame_delta"] <= 0.0005:
            problems.append("animation produces no visible change between frames "
                            "(empty or constant timelines)")
        if motion["loop_closes"] > 0.02:
            problems.append(f"last frame does not match the first ({motion['loop_closes']}); "
                            "the loop will pop")
    else:
        problems.append("package has no animations")

    # 4. reference comparison
    comparison = None
    if args.reference:
        reference = reference_canvas(args.reference, setup.size)
        iou = spine_runtime.silhouette_iou(setup, reference)
        comparison = {
            "reference": str(Path(args.reference).resolve()),
            "silhouette_iou": round(iou, 4),
            "min_iou": args.min_iou,
            "ok": iou >= args.min_iou,
        }
        sheet = side_by_side([setup, reference, overlay(setup, reference)])
        sheet.save(out_dir / "compare_reference.png")
        if not comparison["ok"]:
            problems.append(f"setup pose overlaps the reference by only {iou:.1%} "
                            f"(need {args.min_iou:.0%}); re-run positioning or fix pivots")

    # 5. previews
    html_path = out_dir / "preview.html"
    html_path.write_text(build_html(frames, motion.get("duration", 1.0),
                                    f"{package.stem} - {animation or 'setup pose'} QA preview"),
                         encoding="utf-8")

    window = side_by_side([setup] + frames[:3])
    window.save(out_dir / "sample_window.png")

    report = {
        "ok": not problems,
        "package": str(package),
        "spine_version": skeleton.version,
        "animations": animations,
        "slots": len(skeleton.slots),
        "bones": len(skeleton.bones),
        "regions_used": sorted({slot["attachment"] for slot in skeleton.slots if slot["attachment"]}),
        "setup_opaque_ratio": coverage,
        "motion": motion,
        "reference_comparison": comparison,
        "problems": problems,
        "files": {
            "setup_pose": str(setup_path),
            "preview_html": str(html_path),
            "preview_gif": str(gif_path) if gif_path else None,
            "filmstrip": str(filmstrip_path) if filmstrip_path else None,
            "frames": str(frames_dir),
            "compare_reference": str(out_dir / "compare_reference.png") if comparison else None,
        },
    }
    parts_lib.write_json(out_dir / "preview_report.json", report)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"setup pose : {setup_path}  (opaque {coverage:.1%})")
        if gif_path:
            print(f"animation  : {animation}  {motion['duration']}s  "
                  f"max frame delta {motion['max_frame_delta']}")
            print(f"gif        : {gif_path}")
            print(f"filmstrip  : {filmstrip_path}")
        if comparison:
            print(f"reference  : IoU {comparison['silhouette_iou']:.3f} "
                  f"(need {comparison['min_iou']:.2f}) -> "
                  f"{'PASS' if comparison['ok'] else 'FAIL'}")
        print(f"html       : {html_path}")
        for problem in problems:
            print("PROBLEM    :", problem)
        print("RESULT:", "OK" if not problems else "FAILED")
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
