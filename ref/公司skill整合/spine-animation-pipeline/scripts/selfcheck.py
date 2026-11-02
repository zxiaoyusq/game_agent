#!/usr/bin/env python3
"""One command that answers: will this skill actually work on this machine?

Every step reports a machine-readable status plus, when something is missing,
the exact next action. Run it before starting a task, and again after changing
anything about the environment.

    python selfcheck.py
    python selfcheck.py --json
    python selfcheck.py --quick        # skip the Spine CLI round trip
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SKILL_ROOT = HERE.parent


def check(name, ok, detail="", action="", level="required", extra=None):
    return {"name": name, "ok": bool(ok), "detail": detail, "action": action,
            "level": level, "extra": extra or {}}


def python_checks():
    results = []
    version = ".".join(str(item) for item in sys.version_info[:3])
    results.append(check("python", sys.version_info >= (3, 9), f"{version} at {sys.executable}",
                         "install Python 3.9 or newer"))
    try:
        import PIL  # noqa: F401
        from PIL import Image
        results.append(check("pillow", True, f"Pillow {PIL.__version__}"))
    except Exception as error:
        results.append(check("pillow", False, str(error), "pip install pillow"))
    try:
        import numpy
        results.append(check("numpy", True, f"numpy {numpy.__version__}"))
    except Exception as error:
        results.append(check("numpy", False, str(error), "pip install numpy"))
    try:
        import cv2
        results.append(check("opencv", True, f"opencv {cv2.__version__} (auto-positioning)",
                             "", level="optional"))
    except Exception as error:
        results.append(check("opencv", False, str(error),
                             "pip install opencv-python-headless  (without it parts fall back "
                             "to template matching)", level="optional"))
    return results


def spine_cli_checks(quick=False):
    results = []
    try:
        import spine_cli
    except Exception as error:
        return [check("spine_cli module", False, str(error), "reinstall the skill")]
    cli, version = spine_cli.find_cli()
    if cli is None:
        results.append(check("spine CLI", False, "not found",
                             "install Spine, or set SPINE_CLI_PATH to Spine.com "
                             "(Spine.com is the licensed binary, SpineTrial.exe the trial)",
                             level="optional"))
        return results
    shortcut = getattr(spine_cli.find_cli, "shortcut", None)
    detail = f"{version or 'version unknown'} at {cli}"
    if shortcut:
        detail += f"  (via {Path(shortcut).name})"
    results.append(check("spine CLI", True, detail,
                         extra={"path": str(cli), "version": version,
                                "shortcut": shortcut}))
    results.append(check("spine CLI version", True, f"{version or 'unknown'}",
                         "the exporter writes this version's encoding automatically"))
    if not quick:
        sample = SKILL_ROOT / "tests" / "fixtures" / "probe"
        probe = _write_probe(sample)
        try:
            gate = spine_cli.import_gate(cli, probe, work_dir=sample / "out", name="probe")
            results.append(check("spine CLI import", gate["ok"],
                                 (gate.get("project") or gate.get("output", "")[-160:]),
                                 "run `spine_toolkit.py roundtrip <package> --gate` to see the "
                                 "full CLI output"))
        except Exception as error:
            results.append(check("spine CLI import", False, str(error),
                                 "check the CLI path and that the install is licensed"))
    return results


def _write_probe(directory):
    """A minimal skeleton that exercises the part that actually breaks.

    A headerless, animation-free export imports into almost any Spine build, so
    it proves nothing. This probe carries a bezier-curved timeline, which is
    exactly what the editor rejects when the version encoding is wrong.
    """
    import spine_format
    directory.mkdir(parents=True, exist_ok=True)
    document = {
        "skeleton": {"spine": "3.8.75", "x": 0, "y": 0, "width": 64, "height": 64},
        "bones": [{"name": "root"}, {"name": "body", "parent": "root", "length": 32}],
        "slots": [{"name": "body", "bone": "body", "attachment": "body"}],
        "skins": [{"name": "default", "attachments": {
            "body": {"body": {"width": 32, "height": 32}}}}],
        "animations": {"idle": {"bones": {"body": {"rotate": [
            {"time": 0.0, "angle": 0.0},
            {"time": 0.6, "angle": 4.0, "curve": 0.25, "c2": 0.0, "c3": 0.75, "c4": 1.0},
            {"time": 1.2, "angle": 0.0},
        ]}}}},
    }
    cli_version = None
    try:
        import spine_cli
        _, cli_version = spine_cli.find_cli()
    except Exception:
        pass
    if cli_version:
        spine_format.normalize_to_target(document, cli_version)
    path = directory / "probe.json"
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return path


def companion_skill_checks():
    results = []
    try:
        import gen_parts
        script = gen_parts.find_azure_script()
        if script:
            results.append(check("gpt生图 skill", True, str(script),
                                 extra={"path": str(script)}))
        else:
            results.append(check("gpt生图 skill", False, "azure_image2.py not found",
                                 "install the azure-image2-generation skill under "
                                 "~/.agents/skills/, or pass --azure-script"))
        html = gen_parts.IMAGE_TOOL_HTML
        results.append(check("ai_image_tool.html", html.is_file(), str(html),
                             "pass --html <path to ai_image_tool.html>"))
    except Exception as error:
        results.append(check("gpt生图 skill", False, str(error), "reinstall the skill"))

    try:
        import qa_vision
        script = qa_vision.find_vision_script()
        if script:
            results.append(check("vision QA route", True, str(script), "", level="optional",
                                 extra={"path": str(script)}))
        else:
            results.append(check("vision QA route", False, "vision_call.py not found",
                                 "install the gpt52-vision-router skill to let a text-only "
                                 "model check the art visually", level="optional"))
    except Exception as error:
        results.append(check("vision QA route", False, str(error), "reinstall the skill",
                             level="optional"))
    return results


def self_test_checks():
    results = []
    tests = SKILL_ROOT / "tests" / "run_tests.py"
    if not tests.is_file():
        return [check("self test", False, "tests/run_tests.py missing", "reinstall the skill")]
    proc = subprocess.run([sys.executable, str(tests)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    output = (proc.stdout or "") + (proc.stderr or "")
    tail = [line for line in output.strip().splitlines() if line.strip()][-1:] or [""]
    results.append(check("self test", proc.returncode == 0, tail[0].strip(),
                         "run tests/run_tests.py directly to see the failing check"))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify this skill's environment")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quick", action="store_true", help="skip the Spine CLI import probe")
    parser.add_argument("--no-tests", action="store_true", help="skip the unit tests")
    args = parser.parse_args(argv)

    groups = [
        ("runtime", python_checks()),
        ("spine", spine_cli_checks(quick=args.quick)),
        ("companion skills", companion_skill_checks()),
    ]
    if not args.no_tests:
        groups.append(("pipeline", self_test_checks()))

    blocked = [item for _, items in groups for item in items
               if not item["ok"] and item["level"] == "required"]
    payload = {
        "ok": not blocked,
        "skill_root": str(SKILL_ROOT),
        "groups": [{"group": name, "checks": items} for name, items in groups],
        "blocking": [item["name"] for item in blocked],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 2

    for name, items in groups:
        print(f"\n{name}")
        for item in items:
            mark = "ok  " if item["ok"] else ("MISS" if item["level"] == "optional" else "FAIL")
            print(f"  [{mark}] {item['name']:<22} {item['detail']}")
            if not item["ok"] and item["action"]:
                print(f"         -> {item['action']}")
    print()
    if payload["ok"]:
        print("RESULT: OK - the pipeline is ready")
        return 0
    print("RESULT: BLOCKED - " + ", ".join(payload["blocking"]))
    return 2


if __name__ == "__main__":
    sys.exit(main())
