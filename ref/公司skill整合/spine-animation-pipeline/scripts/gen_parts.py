#!/usr/bin/env python3
"""Generate the transparent body parts with the local GPT image tool.

This is the bridge between this skill and the user's `azure-image2-generation`
("gpt生图") skill: it does not reimplement the Azure OpenAI GPT-Image-2 call,
it drives that skill's `azure_image2.py`, then does the part-specific work that
the generic image tool cannot do:

    reference art --(azure_image2.py, edit mode)--> green-screen render
                  --(chroma key + decontaminate + trim)--> transparent part PNG
                  --(alpha checks)--> parts_manifest.json + generation_report.json

Two strategies:

  --strategy per-part   one call per part. Best silhouette quality and the
                        cheapest way to fix a single bad limb. Costs one call
                        per part.
  --strategy sheet      one call for a deconstructed sprite sheet, then segment
                        it by connected components (the upstream split_character
                        idea). Cheaper, but the model often merges parts.

Always run `--dry-run` first: it prints every command and spends nothing.

    python gen_parts.py --reference ref.png --parts head,torso,arm_l,arm_r \\
        --out work/ --dry-run
    python gen_parts.py --reference ref.png --parts parts_spec.json --out work/ \\
        --quality medium
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import parts_lib
import rig_rules

IMAGE_TOOL_HTML = Path(r"E:\AI生图\ai_image_tool.html")
AZURE_SCRIPT_CANDIDATES = [
    Path.home() / ".agents/skills/azure-image2-generation/scripts/azure_image2.py",
    Path.home() / ".codex/skills/azure-image2-generation/scripts/azure_image2.py",
    Path.home() / ".dsh/skills/azure-image2-generation/scripts/azure_image2.py",
]

# Prompt scaffold. The occlusion-complete rules come from the Codex skill's
# hard-won list: a part cut to its visible silhouette cannot be animated,
# because the hidden half is missing the moment the bone rotates.
BASE_RULES = (
    "Single isolated 2D game asset: {part}. "
    "Flat solid pure green background (#00FF00). No shadow, no ground plane, "
    "no gradient in the background, no text, no watermark, no border, no frame. "
    "Only {part} is shown, centred, drawn at the same viewing angle as the reference. "
    "{style_lock} {occlusion} {extra}"
    "Match the reference art style, palette, line weight and shading exactly."
)

STYLE_LOCK = (
    "Use image 1 as the style, colour and proportion reference and reproduce its "
    "art style exactly."
)

# Per-kind notes: what "complete" means for that part.
OCCLUSION_NOTES = {
    "head": "Draw the COMPLETE head including the crown and the whole face; do not "
            "crop the top or hide the far ear.",
    "hair": "Draw the complete hair shape as it would look with the head in front of it.",
    "hat": "Draw the complete hat including the brim that would sit behind the head.",
    "torso": "Draw the COMPLETE torso as one unbroken shape, including the areas "
             "hidden behind the arms and the legs. Do not cut notches where limbs overlap.",
    "pelvis": "Draw the complete hip/pelvis shape including the area under the torso.",
    "upper_arm": "Draw the whole upper arm including the shoulder end that is hidden "
                 "behind the torso.",
    "lower_arm": "Draw the whole forearm including the elbow end that is hidden "
                 "behind the upper arm.",
    "hand": "Draw the complete hand including the wrist end that is hidden behind the arm.",
    "arm": "Draw the whole arm including the shoulder end hidden behind the torso.",
    "upper_leg": "Draw the whole thigh including the hip end that is hidden behind "
                 "the body.",
    "lower_leg": "Draw the whole lower leg including the knee end that is hidden "
                 "behind the thigh.",
    "foot": "Draw the complete foot including the ankle end hidden behind the leg.",
    "leg": "Draw the whole leg including the hip end hidden behind the body.",
    "tail": "Draw the complete tail including its base that is hidden behind the body.",
    "ear": "Draw the complete ear including the base that is hidden behind the head.",
    "wing": "Draw the complete wing including the root hidden behind the body.",
    "collar": "Draw the complete collar including the part hidden behind the neck.",
    "bell": "Draw the complete bell with its ring.",
    "accessory": "Draw the complete object, including any part hidden behind the character.",
}


def find_azure_script(explicit=None):
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    for candidate in AZURE_SCRIPT_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def choose_size(reference_path, explicit=None):
    """Pick a generation size; single parts get a square, wide art stays wide."""
    if explicit:
        return explicit
    try:
        with Image.open(reference_path) as image:
            ratio = image.width / image.height
    except Exception:
        return "1024x1024"
    if ratio >= 1.55:
        return "2048x1152"
    if ratio >= 1.1:
        return "1536x1024"
    if ratio <= 0.65:
        return "1152x2048"
    if ratio <= 0.9:
        return "1024x1536"
    return "1024x1024"


def build_prompt(name, spec, with_reference=True):
    kind = spec.get("kind") or rig_rules.classify(name)
    part_label = spec.get("label") or name.replace("_", " ").replace("-", " ")
    occlusion = OCCLUSION_NOTES.get(kind, OCCLUSION_NOTES["accessory"])
    if spec.get("occlusion") == "visible-only":
        occlusion = "Draw only the visible silhouette of this part."
    extra = spec.get("extra", "")
    if isinstance(extra, list):
        extra = " ".join(extra)
    prompt = BASE_RULES.format(
        part=part_label,
        style_lock=STYLE_LOCK if with_reference else "",
        occlusion=occlusion,
        extra=(extra + " ") if extra else "",
    )
    if spec.get("negative"):
        prompt += f" Do not include: {spec['negative']}."
    return " ".join(prompt.split())


# ── generation ──────────────────────────────────────────────────────────────
def call_azure(script, html, prompt, reference, out_dir, size, quality, filename,
               refs=(), dry_run=False, timeout=300, retries=1):
    command = [sys.executable, str(script), "--html", str(html), "--mode", "edit",
               "--prompt", prompt, "--size", size, "--quality", quality,
               "--out", str(out_dir), "--filename", filename, "--timeout", str(timeout),
               "--refs", *[str(item) for item in (reference,) + tuple(refs)]]
    if dry_run:
        return {"ok": True, "dry_run": True, "command": command}

    last = ""
    for attempt in range(retries + 1):
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout + 60)
        output = (proc.stdout or "") + (proc.stderr or "")
        produced = out_dir / f"{filename}.png"
        if proc.returncode == 0 and produced.is_file():
            return {"ok": True, "path": str(produced), "attempts": attempt + 1,
                    "log": output.strip()[-500:]}
        last = output.strip()[-500:]
    return {"ok": False, "error": last or "azure_image2.py produced no PNG"}


def segment_sheet(sheet_path, out_dir, min_area=800, keep=12):
    """Split a deconstructed sprite sheet into parts by connected components."""
    sheet = parts_lib.load_rgba(sheet_path)
    keyed = parts_lib.chroma_key(sheet, inner=40.0, outer=130.0)
    alpha = np.asarray(keyed)[:, :, 3] > 24
    height, width = alpha.shape
    mask = alpha.astype(np.uint8)
    try:
        import cv2
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        boxes = []
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < min_area:
                continue
            boxes.append((int(stats[label, cv2.CC_STAT_LEFT]), int(stats[label, cv2.CC_STAT_TOP]),
                          int(stats[label, cv2.CC_STAT_WIDTH]), int(stats[label, cv2.CC_STAT_HEIGHT]),
                          area))
    except ImportError:
        boxes = _flood_components(alpha, min_area)
    boxes.sort(key=lambda item: -item[4])
    boxes = boxes[:keep]
    out_dir.mkdir(parents=True, exist_ok=True)
    produced = []
    for index, (x, y, box_width, box_height, _) in enumerate(boxes):
        crop = keyed.crop((x, y, x + box_width, y + box_height))
        crop = parts_lib.decontaminate_edges(crop)
        crop, _ = parts_lib.trim_to_alpha(crop)
        path = out_dir / f"sheet_part_{index:02d}.png"
        parts_lib.save_png(crop, path)
        produced.append({"name": path.stem, "file": str(path),
                         "size": [crop.width, crop.height], "origin": [x, y]})
    return produced


def _flood_components(alpha, min_area):
    """connected components without OpenCV."""
    height, width = alpha.shape
    seen = np.zeros_like(alpha, dtype=bool)
    boxes = []
    for start_y in range(height):
        for start_x in range(width):
            if not alpha[start_y, start_x] or seen[start_y, start_x]:
                continue
            stack = [(start_y, start_x)]
            seen[start_y, start_x] = True
            min_x = max_x = start_x
            min_y = max_y = start_y
            area = 0
            while stack:
                y, x = stack.pop()
                area += 1
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)
                for ny in range(max(0, y - 1), min(height, y + 2)):
                    for nx in range(max(0, x - 1), min(width, x + 2)):
                        if alpha[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            if area >= min_area:
                boxes.append((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1, area))
    return boxes


# ── driver ──────────────────────────────────────────────────────────────────
def load_spec(parts_arg):
    """Accept 'head,torso,arm_l' or a JSON spec file."""
    path = Path(parts_arg)
    if path.is_file() and path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "parts" in data:
            entries = data["parts"]
        else:
            entries = data
        specs = []
        for entry in entries:
            if isinstance(entry, str):
                specs.append({"name": entry})
            elif isinstance(entry, dict) and entry.get("name"):
                specs.append(dict(entry))
        return specs
    return [{"name": item.strip()} for item in parts_arg.split(",") if item.strip()]


def generate(reference, parts_arg, out_dir, strategy="per-part", quality="medium",
             size=None, html=None, azure_script=None, dry_run=False, style_refs=(),
             sheet_name="sheet", min_area=800, keep=12):
    reference = Path(reference).resolve()
    if not reference.is_file():
        raise FileNotFoundError(f"reference art not found: {reference}")
    out_dir = Path(out_dir).resolve()
    raw_dir = out_dir / "raw_generations"
    parts_dir = out_dir / "parts"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    parts_dir.mkdir(parents=True, exist_ok=True)

    html = Path(html) if html else IMAGE_TOOL_HTML
    script = find_azure_script(azure_script)
    size = choose_size(reference, size)
    specs = load_spec(parts_arg)
    if not specs and strategy == "per-part":
        raise ValueError("--parts is empty")
    if not dry_run:
        if script is None:
            raise FileNotFoundError(
                "azure_image2.py not found; pass --azure-script or install the "
                "azure-image2-generation skill")
        if not html.is_file():
            raise FileNotFoundError(f"ai_image_tool.html not found: {html}")

    report = {"ok": True, "strategy": strategy, "quality": quality, "size": size,
              "reference": str(reference), "html": str(html),
              "azure_script": str(script) if script else None,
              "dry_run": dry_run, "parts": [], "warnings": []}

    if strategy == "sheet":
        prompt = (f"A 2D game sprite sheet that deconstructs the character in image 1 into "
                  f"separated, isolated, non-overlapping body parts: {', '.join(s['name'] for s in specs) or 'head, torso, upper arms, lower arms, hands, upper legs, lower legs, feet'}. "
                  f"Lay every part flat with clear space between them, nothing overlapping, "
                  f"each part drawn COMPLETE (include the areas normally hidden behind other "
                  f"parts). Flat solid pure green background (#00FF00). No shadow, no text, "
                  f"no watermark, no pose, no assembled character. Match the art style, "
                  f"palette and line weight of image 1 exactly.")
        outcome = call_azure(script, html, prompt, reference, raw_dir, size, quality,
                             sheet_name, refs=style_refs, dry_run=dry_run)
        report["generation"] = outcome
        if dry_run or not outcome.get("ok"):
            report["ok"] = bool(outcome.get("ok"))
            report["parts"] = []
        else:
            segmented = segment_sheet(Path(outcome["path"]), parts_dir, min_area=min_area,
                                      keep=keep)
            report["parts"] = segmented
            report["warnings"].append(
                "sheet segmentation names parts positionally; rename them before export "
                "so the rigging rules can classify each part")
            report["ok"] = bool(segmented)
    else:
        for spec in specs:
            name = spec["name"]
            prompt = build_prompt(name, spec, with_reference=True)
            outcome = call_azure(script, html, prompt, reference, raw_dir, size, quality,
                                 name, refs=style_refs, dry_run=dry_run)
            entry = {"name": name, "kind": spec.get("kind") or rig_rules.classify(name),
                     "prompt": prompt, "generation": outcome}
            if dry_run:
                report["parts"].append(entry)
                continue
            if not outcome.get("ok"):
                entry["ok"] = False
                entry["problems"] = [outcome.get("error", "generation failed")]
                report["ok"] = False
                report["parts"].append(entry)
                continue
            # green screen -> transparent part
            image = parts_lib.load_rgba(outcome["path"])
            keyed = parts_lib.chroma_key(image, inner=40.0, outer=130.0)
            keyed = parts_lib.keep_largest_component(keyed)
            try:
                trimmed, _ = parts_lib.trim_to_alpha(keyed)
            except ValueError as error:
                entry["ok"] = False
                entry["problems"] = [f"nothing survived chroma key: {error}"]
                report["ok"] = False
                report["parts"].append(entry)
                continue
            cleaned = parts_lib.decontaminate_edges(trimmed, boundary_radius=3)
            part_path = parts_dir / f"{name}.png"
            parts_lib.save_png(cleaned, part_path)
            part_report = parts_lib.alpha_report(cleaned)
            ok, _, problems = parts_lib.validate_part(part_path)
            entry.update({"ok": ok, "file": str(part_path), "size": [cleaned.width, cleaned.height],
                          "alpha": part_report, "problems": problems})
            if not ok:
                report["ok"] = False
            report["parts"].append(entry)

    manifest_path = out_dir / "parts_manifest.json"
    parts_lib.write_json(manifest_path, report)
    for entry in report["parts"]:
        if entry.get("file"):
            entry["file"] = str(Path(entry["file"]).relative_to(out_dir)
                                 if out_dir in Path(entry["file"]).parents else entry["file"])
    parts_lib.write_json(manifest_path, report)
    report["manifest"] = str(manifest_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate transparent parts with the GPT image tool")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--parts", required=True,
                        help="comma list of part names, or a JSON spec file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--strategy", choices=["per-part", "sheet"], default="per-part")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"],
                        help="low for exploration, medium for production art")
    parser.add_argument("--size", default=None, help="WxH (default: from the reference aspect)")
    parser.add_argument("--html", default=None, help="path to ai_image_tool.html")
    parser.add_argument("--azure-script", default=None, help="path to azure_image2.py")
    parser.add_argument("--style-ref", action="append", default=[],
                        help="extra reference image (repeatable) for style consistency")
    parser.add_argument("--min-area", type=int, default=800, help="sheet mode: drop specks")
    parser.add_argument("--keep", type=int, default=12, help="sheet mode: max parts to keep")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the commands and spend no quota")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = generate(args.reference, args.parts, args.out, strategy=args.strategy,
                          quality=args.quality, size=args.size, html=args.html,
                          azure_script=args.azure_script, dry_run=args.dry_run,
                          style_refs=args.style_ref, min_area=args.min_area, keep=args.keep)
    except (ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2

    if args.dry_run:
        print(f"DRY RUN -- {len(report['parts'])} generation(s) that would be sent:")
        print(f"  size {report['size']}  quality {report['quality']}  tool {report['html']}")
        for entry in report["parts"]:
            print(f"\n[{entry['name']}] {entry['prompt']}")
            print("  " + " ".join(entry["generation"]["command"][:6]) + " ...")
        return 0

    for entry in report["parts"]:
        if entry.get("generation", {}).get("dry_run"):
            continue
        status = "ok" if entry.get("ok") else "FAILED"
        detail = ", ".join(entry.get("problems", [])) or f"{entry.get('size')}"
        print(f"{entry['name']:<14} {status:<7} {detail}")
    print(f"\nmanifest: {report.get('manifest')}")
    print("RESULT:", "OK" if report["ok"] else "FAILED")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
