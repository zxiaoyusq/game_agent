#!/usr/bin/env python3
"""Ask a vision model about the art, because the driving model may be text-only.

deepseek-v4-flash (and the other text-only relays) cannot look at a PNG, but
part generation and layout QA are fundamentally visual. This script gives the
agent a structured way to outsource the pixels and get a machine-readable
verdict back.

It reuses the local `gpt52-vision-router` skill when present (MiMo by default),
and falls back to any OpenAI-compatible vision endpoint given on the command
line. No key is ever printed.

Verdict contract: the prompt demands the answer begin with `VERDICT: PASS` or
`VERDICT: FAIL`, so the caller never has to interpret prose.

    python qa_vision.py --task parts   --image parts/head.png --image parts/torso.png
    python qa_vision.py --task composite --reference reference.png --image out/preview/setup_pose.png
    python qa_vision.py --task loop    --image out/preview/filmstrip.png
    python qa_vision.py --prompt "..." --image anything.png
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

VISION_SCRIPT_CANDIDATES = [
    Path.home() / ".agents/skills/gpt52-vision-router/scripts/vision_call.py",
    Path.home() / ".codex/skills/gpt52-vision-router/scripts/vision_call.py",
    Path.home() / ".dsh/skills/gpt52-vision-router/scripts/vision_call.py",
    Path.home() / ".agents/skills/gpt52-vision-router/mcp/server.py",
]

CONTRACT = ("Start your reply with a single line `VERDICT: PASS` or `VERDICT: FAIL`, "
            "then give at most five short bullet points of evidence. ")

TASKS = {
    "parts": (
        "These are transparent character parts cut out of a green screen, for a 2D "
        "skeletal (Spine) rig. For each image judge: is the whole part present and "
        "uncropped; is the silhouette clean without a green or white fringe; is the "
        "art style consistent between the parts. " + CONTRACT +
        "FAIL if any part is cut off, has a coloured halo, or mixes art styles."
    ),
    "composite": (
        "Image 1 is a character composited from an exported Spine skeleton; image 2 is "
        "the reference art it must reproduce. Judge whether the composite looks like "
        "the same assembled character: same part placement, no floating or detached "
        "limbs, no obviously misplaced or mirrored pieces. " + CONTRACT +
        "FAIL if any body part sits clearly in the wrong place or is missing."
    ),
    "overlay": (
        "This overlay compares a rendered rig (coloured red where only the render "
        "exists) with the reference art (blue where only the reference exists). Grey "
        "means both agree. Judge how well they agree and where the disagreement is "
        "concentrated. " + CONTRACT +
        "FAIL if red or blue dominates any large region, which means a part is offset."
    ),
    "loop": (
        "These frames sample one loop of an idle animation, left to right, top to "
        "bottom. Judge whether the motion is a restrained idle (breathing, small sway) "
        "with every body part staying attached and no frame where a limb jumps or "
        "detaches, and whether the last frame returns to the first pose. " + CONTRACT +
        "FAIL if parts visibly detach, jump, or the motion is wildly exaggerated."
    ),
}


def find_vision_script(explicit=None):
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    for candidate in VISION_SCRIPT_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def run_via_script(script, images, prompt, model=None, timeout=300):
    command = [sys.executable, str(script)]
    for image in images:
        command += ["--image", str(image)]
    command += ["--prompt", prompt]
    if model:
        command += ["--model", model]
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "vision call failed").strip()[:400])
    text = proc.stdout or ""
    # Strip the helper's own "[vision 24.7s api]" timing line.
    lines = [line for line in text.splitlines() if not line.strip().startswith("[vision")]
    return "\n".join(lines).strip()


def load_config():
    """Read base_url / model / key from the vision-router skill config."""
    config_path = None
    script = find_vision_script()
    if script:
        for candidate in (script.parent.parent / "vision_config.json",
                          script.parent / "vision_config.json"):
            if candidate.is_file():
                config_path = candidate
                break
    if config_path is None:
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {"base_url": data.get("base_url"), "model": data.get("model"),
            "api_key": data.get("api_key")}


def run_direct(images, prompt, config, model=None, timeout=300, max_tokens=1200):
    base_url = (config.get("base_url") or "").rstrip("/")
    api_key = config.get("api_key")
    if not base_url or not api_key:
        raise RuntimeError("no vision endpoint configured (need base_url + api_key)")
    content = [{"type": "text", "text": prompt}]
    for image in images:
        data = base64.b64encode(Path(image).read_bytes()).decode("ascii")
        suffix = Path(image).suffix.lower().lstrip(".") or "png"
        mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{data}"}})
    body = json.dumps({
        "model": model or config.get("model"),
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    request = urllib.request.Request(f"{base_url}/chat/completions", data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"].strip()


def parse_verdict(text):
    match = re.search(r"VERDICT\s*:\s*(PASS|FAIL)", text or "", re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Vision QA bridge for text-only agents")
    parser.add_argument("--task", choices=sorted(TASKS), default=None)
    parser.add_argument("--prompt", default=None, help="free-form question (overrides --task)")
    parser.add_argument("--image", action="append", required=True)
    parser.add_argument("--reference", default=None,
                        help="for --task composite: the reference art to show as image 2")
    parser.add_argument("--vision-script", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    images = [Path(item) for item in args.image]
    missing = [str(item) for item in images if not item.is_file()]
    if missing:
        print(f"ERROR: image not found: {', '.join(missing)}", file=sys.stderr)
        return 1

    # A reference image is always attached when one is given. It used to be
    # honoured only by --task composite, so a free-form --prompt silently
    # dropped it and the model then answered about an image it could not see.
    if args.reference:
        reference = Path(args.reference)
        if not reference.is_file():
            print(f"ERROR: reference not found: {reference}", file=sys.stderr)
            return 1
        if reference not in images:
            images = images + [reference]

    if args.prompt:
        prompt = args.prompt
        if args.reference:
            prompt = f"Image 1 is the subject and image {len(images)} is its reference. " + prompt
        if "VERDICT" not in prompt:
            prompt = prompt + " " + CONTRACT
    else:
        if not args.task:
            print("ERROR: pass --task or --prompt", file=sys.stderr)
            return 1
        prompt = TASKS[args.task]
        if args.task == "composite":
            if not args.reference:
                print("ERROR: --task composite needs --reference", file=sys.stderr)
                return 1
            prompt = ("Image 1 is the composite to judge and image 2 is the reference. " + prompt)

    started = time.time()
    script = find_vision_script(args.vision_script)
    try:
        if script and not args.model:
            answer = run_via_script(script, images, prompt, timeout=args.timeout)
            route = f"script:{script.name}"
        else:
            answer = run_direct(images, prompt, load_config(), model=args.model,
                                timeout=args.timeout)
            route = "direct"
    except Exception as error:
        result = {"ok": False, "verdict": None, "route": None,
                  "error": str(error)[:500], "images": [str(item) for item in images]}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
              f"vision QA unavailable: {error}", file=sys.stderr)
        return 2

    verdict = parse_verdict(answer)
    result = {
        "ok": verdict == "PASS",
        "verdict": verdict,
        "route": route,
        "task": args.task or "custom",
        "images": [str(item) for item in images],
        "elapsed_seconds": round(time.time() - started, 1),
        "answer": answer,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{verdict or 'NO VERDICT'}] via {route} in {result['elapsed_seconds']}s")
        print(answer)
    if verdict == "PASS":
        return 0
    return 2 if verdict == "FAIL" else 3


if __name__ == "__main__":
    sys.exit(main())
