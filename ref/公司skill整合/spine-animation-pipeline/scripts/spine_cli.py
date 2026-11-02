#!/usr/bin/env python3
"""Locate and drive the official Spine CLI, so the pipeline can be gated on a
real editor import instead of on our own opinion of the JSON.

The CLI is the referee: if `Spine -i skeleton.json -o proj.spine -r` says
"Complete." the package really opens in the user's editor.

Usage:
    python spine_cli.py --find
    python spine_cli.py --gate out/skeleton.json            # import gate
    python spine_cli.py --roundtrip out/skeleton.json --work .build
    python spine_cli.py --unpack out/hero.atlas --out unpacked/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# The user's own shortcut is the best answer to "which Spine is installed",
# so it is checked before any hard-coded path. Spine.com and Spine.exe are
# both launchers that take the same CLI arguments and print the same stdout;
# they differ only in which console they attach to.
DESKTOP_SHORTCUT_NAMES = ("Spine.lnk", "Spine 4.lnk", "Spine Trial.lnk")
SHORTCUT_FOLDERS = ("Desktop", "OneDrive/Desktop", "OneDrive/桌面", "桌面")

# Candidate executables, most specific first. `Spine.com` is the console build
# that prints to stdout on Windows; `Spine.exe` launches a GUI and is useless
# for scripting, so it is only a last resort.
WINDOWS_CANDIDATES = [
    r"D:\Spine3.8.75Pro\Spine.com",
    r"D:\Spine3.8.75Pro\Spine.exe",
    r"C:\Program Files\Spine\Spine.com",
    r"C:\Program Files (x86)\Spine\Spine.com",
    r"E:\Program Files\Spine\Spine.com",
    r"D:\Program Files\Spine\Spine.com",
    r"D:\Program Files\Spine Trial\SpineTrial.com",
]
UNIX_CANDIDATES = [
    "/Applications/Spine.app/Contents/MacOS/Spine",
    "/opt/spine/Spine",
    "/usr/local/bin/Spine",
]

# Import of a real export legitimately prints these; they are not failures.
BENIGN_PATTERNS = (
    "welcome data download failed",
    "server error: 410",
    "not found:",           # images living beside an atlas we did not import
    "image for slot",
)


def _printable_runs(data, minimum=2):
    return [run.decode("latin-1")
            for run in re.findall(rb"[\x20-\x7e]{%d,}" % minimum, data)]


def _path_from_idlist(blob):
    r"""Rebuild a target path from an MS-SHLLINK LinkTargetIDList.

    A link with no LinkInfo block (LinkFlags 0x81, which is what Windows writes
    for a plain desktop shortcut) stores the path only as shell items: one for
    the drive and one per component. Scanning the file for a path string finds
    nothing in that case, so the items are reassembled instead.
    """
    offset = 76
    if len(blob) < offset + 2:
        return None
    size = struct.unpack_from("<H", blob, offset)[0]
    if size <= 0 or offset + 2 + size > len(blob):
        return None
    idlist = blob[offset + 2:offset + 2 + size]
    root = None
    parts = []
    position = 0
    while position + 2 <= len(idlist):
        item_size = struct.unpack_from("<H", idlist, position)[0]
        if item_size < 2 or position + item_size > len(idlist):
            break
        item = idlist[position:position + item_size]
        position += item_size
        # The longest printable run in an item is its name; the surrounding
        # bytes are the item type byte and a trailing extension block.
        runs = sorted(_printable_runs(item), key=len, reverse=True)
        for run in runs:
            candidate = run.lstrip("/")
            if re.match(r"^[A-Za-z]:[\\/]", candidate):
                root = candidate
                break
            if len(run) >= 2 and re.match(r"^[A-Za-z0-9._ -]+$", run):
                parts.append(run)
                break
    if not root:
        return None
    tail = "\\".join(part for part in parts if part)
    combined = root.rstrip("\\/") + "\\" + tail if tail else root
    return combined


def _resolve_via_powershell(link):
    """Last resort: ask the shell. Slow, but exact."""
    script = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"
              + str(link).replace("'", "''") + "'); Write-Output $s.TargetPath")
    for shell in ("powershell", "pwsh"):
        if shutil.which(shell) is None:
            continue
        try:
            proc = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", script],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        target = (proc.stdout or "").strip().splitlines()
        if target and Path(target[0]).is_file():
            return Path(target[0])
    return None


def resolve_shortcut(path):
    r"""Resolve a Windows .lnk to its target, without needing pywin32.

    A shortcut is the honest answer to "where is Spine": the user repoints it
    after an upgrade and detection follows. Three strategies, cheapest first: a
    path string stored literally in the file, the shell item list, and finally
    the shell itself.
    """
    path = Path(path)
    if path.suffix.lower() != ".lnk" or not path.is_file():
        return path

    candidates = []
    try:
        blob = path.read_bytes()
    except OSError:
        blob = b""

    if blob:
        # 1. A literal path (present when the link carries a LinkInfo block).
        literal = re.compile(rb"[A-Za-z]:\\[^\x00<>|\r\n\"]{0,240}?\.(?:exe|com)",
                             re.IGNORECASE)
        for match in literal.finditer(blob):
            candidates.append(match.group(0).decode("latin-1"))
        text = blob.decode("utf-16-le", errors="ignore")
        for match in re.compile(r"[A-Za-z]:\\[^\x00<>|\r\n\"]{0,240}?\.(?:exe|com)",
                                re.IGNORECASE).finditer(text):
            candidates.append(match.group(0))
        # 2. Reassemble the shell item list.
        rebuilt = _path_from_idlist(blob)
        if rebuilt:
            candidates.append(rebuilt)

    for candidate in candidates:
        target = Path(candidate)
        if target.is_file():
            return target

    # 3. Ask Windows.
    resolved = _resolve_via_powershell(path)
    if resolved is not None:
        return resolved
    return path


def _shortcut_candidates():
    """Spine shortcuts on the Desktop / Start Menu, in preference order."""
    folders = [Path.home() / name for name in SHORTCUT_FOLDERS]
    public = os.environ.get("PUBLIC")
    if public:
        folders.append(Path(public) / "Desktop")
    found = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for name in DESKTOP_SHORTCUT_NAMES:
            link = folder / name
            if link.is_file():
                found.append(link)
    return found


def _candidate_roots():
    """Extra places worth a shallow scan, derived from the user's Spine home."""
    roots = []
    for home in (Path.home() / "Spine", Path.home() / "SpineTrial"):
        if home.is_dir():
            roots.append(home)
    for drive in ("D:", "E:", "C:"):
        for folder in ("Spine", "Spine Trial", "Program Files", "Program Files (x86)"):
            path = Path(f"{drive}\\") / folder
            if path.is_dir():
                roots.append(path)
    return roots


def find_cli(explicit=None):
    """Return ``(path, version)`` for the first usable Spine CLI, else ``(None, None)``.

    The version is part of the contract, not a nicety: the editor refuses any
    export whose keyframe encoding belongs to another major version, so callers
    must know what they are writing for. The search trail is kept on
    ``find_cli.last_tried`` for diagnostics.
    """
    tried = []
    candidates = []
    env = os.environ.get("SPINE_CLI_PATH")
    for value in (explicit, env):
        if value:
            candidates.append(Path(value))
    if os.name == "nt":
        candidates += _shortcut_candidates()
    candidates += [Path(p) for p in (WINDOWS_CANDIDATES if os.name == "nt" else UNIX_CANDIDATES)]

    for path in candidates:
        if path.is_file():
            resolved = resolve_shortcut(path)
            tried.append(f"{path} -> {resolved}" if resolved != path else str(path))
            if not resolved.is_file():
                continue
            find_cli.last_tried = tried
            find_cli.shortcut = str(path) if resolved != path else None
            return resolved, cli_version(resolved)
        tried.append(str(path))

    # Shallow scan: <root>/Spine.com, <root>/Spine.exe, <root>/*/Spine.com
    for root in _candidate_roots():
        for pattern in ("Spine.com", "Spine.exe", "SpineTrial.com", "SpineTrial.exe",
                        "*/Spine.com", "*/*/Spine.com"):
            for hit in sorted(root.glob(pattern)):
                if hit.is_file():
                    find_cli.last_tried = tried
                    return hit, cli_version(hit)
    find_cli.last_tried = tried
    find_cli.shortcut = None
    return None, None


def cli_version(cli_path):
    """Return '3.8.75' or None by asking the CLI itself."""
    ok, out = run_cli(cli_path, ["-v"], timeout=180)
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", out or "")
    if match:
        return match.group(1)
    # `-v` launches the editor on some builds; fall back to the shipped file.
    for probe in (Path(cli_path).parent / "Spine" / "version.txt",
                  Path.home() / "Spine" / "version.txt"):
        if probe.is_file():
            text = probe.read_text(encoding="utf-8", errors="ignore").strip()
            if re.match(r"^\d+(\.\d+)+$", text):
                return text
    return None


def run_cli(cli_path, args, cwd=None, timeout=900):
    """Run the CLI, returning (returncode_ok, combined_output)."""
    command = [str(cli_path)] + [str(item) for item in args]
    try:
        proc = subprocess.run(command, cwd=str(cwd) if cwd else None,
                              capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s: {' '.join(command)}"
    except OSError as error:
        return False, f"cannot execute {cli_path}: {error}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output


def cli_error(output):
    """True when CLI output reports a real failure (benign noise filtered)."""
    lowered = (output or "").lower()
    if "unable to import" in lowered or "error reading" in lowered:
        return True
    for line in lowered.splitlines():
        if "error" not in line and "exception" not in line and "fail" not in line:
            continue
        if any(pattern in line for pattern in BENIGN_PATTERNS):
            continue
        return True
    return False


# ── operations ──────────────────────────────────────────────────────────────
def import_gate(cli_path, data_path, work_dir=None, name=None):
    """Import a JSON/binary export into a throwaway .spine project.

    Returns dict(ok, project, version, output). This is the strongest check the
    skill can make without a human opening the editor.
    """
    data_path = Path(data_path).resolve()
    if not data_path.is_file():
        return {"ok": False, "project": None, "output": f"missing file: {data_path}"}
    work_dir = Path(work_dir).resolve() if work_dir else Path(tempfile.mkdtemp(prefix="spine-gate-"))
    work_dir.mkdir(parents=True, exist_ok=True)
    local = work_dir / data_path.name
    if data_path != local:
        shutil.copy(data_path, local)
    for extra in (data_path.with_suffix(".atlas"), data_path.with_suffix(".png")):
        if extra.is_file():
            try:
                shutil.copy(extra, work_dir / extra.name)
            except OSError:
                pass
    project = (work_dir / (name or data_path.stem)).with_suffix(".spine")
    args = ["-i", local.name, "-o", project.name]
    if name:
        args += ["-r", name]
    else:
        args += ["-r"]
    # A leftover project from an earlier run would make the existence check
    # meaningless, so clear it and let the run create it.
    if project.is_file():
        try:
            project.unlink()
        except OSError:
            pass

    # The Spine launcher is occasionally unavailable right after another
    # invocation exits (the JVM is still shutting down). That is a transient
    # failure, not a bad export, so retry before reporting anything.
    attempts = 0
    outputs = []
    for attempt in range(3):
        attempts = attempt + 1
        if attempt:
            time.sleep(1.5 * attempt)
        code_ok, output = run_cli(cli_path, args, cwd=work_dir)
        outputs.append(output)
        if project.is_file() and not cli_error(output):
            return {"ok": True, "project": str(project), "attempts": attempts,
                    "version": cli_version_cached(cli_path), "output": output}
        if cli_error(output):
            break  # a real parse error will not fix itself
    output = outputs[-1] if outputs else ""
    return {"ok": False, "project": None, "attempts": attempts,
            "version": cli_version_cached(cli_path), "output": output,
            "detail": "no project produced" if not cli_error(output)
                      else "the editor rejected the export"}


_VERSION_CACHE = {}


def cli_version_cached(cli_path):
    key = str(cli_path)
    if key not in _VERSION_CACHE:
        _VERSION_CACHE[key] = cli_version(cli_path)
    return _VERSION_CACHE[key]


def export_project(cli_path, project, settings_path, out_dir):
    settings_path = Path(settings_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    project = Path(project).resolve()
    ok, output = run_cli(cli_path, ["-i", project, "-o", out_dir, "-e", settings_path],
                         cwd=out_dir.parent)
    return {"ok": ok and not cli_error(output), "output": output, "dir": str(out_dir)}


def unpack_atlas(cli_path, atlas_path, out_dir):
    atlas_path = Path(atlas_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ok, output = run_cli(cli_path, ["-i", atlas_path.parent, "-c", atlas_path, "-o", out_dir])
    produced = sorted(p.name for p in out_dir.glob("*.png"))
    return {"ok": ok and bool(produced), "output": output, "files": produced, "dir": str(out_dir)}


def pack_atlas(cli_path, images_dir, out_dir, name, pack_settings=None):
    images_dir = Path(images_dir).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    args = ["-i", images_dir, "-o", out_dir, "-n", name]
    if pack_settings:
        args += ["-p", Path(pack_settings).resolve()]
    ok, output = run_cli(cli_path, args)
    files = sorted(p.name for p in out_dir.glob(f"{name}*"))
    return {"ok": ok and bool(files), "output": output, "files": files}


def roundtrip(cli_path, data_path, work_dir, name=None):
    """export -> import -> export -> compare. Requires a JSON export settings file."""
    data_path = Path(data_path).resolve()
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    report = {"steps": []}

    gate = import_gate(cli_path, data_path, work_dir=work_dir / "imported", name=name)
    report["steps"].append({"step": "import", "ok": gate["ok"], "detail": gate.get("project")})
    if not gate["ok"]:
        report["ok"] = False
        report["detail"] = "import failed; fix the JSON before round-tripping"
        return report

    settings = work_dir / "export-json.json"
    settings.write_text(json.dumps({
        "class": "json", "extension": ".json", "format": "JSON",
        "nonessential": True, "prettyPrint": True,
    }, indent=2), encoding="utf-8")

    reexport_dir = work_dir / "reexport"
    exported = export_project(cli_path, gate["project"], settings, reexport_dir)
    targets = sorted(reexport_dir.glob("*.json"))
    report["steps"].append({"step": "re-export", "ok": exported["ok"] and bool(targets),
                            "detail": [t.name for t in targets]})
    if not targets:
        report["ok"] = False
        report["detail"] = "re-export produced no JSON"
        return report

    import spine_toolkit  # sibling module
    original = json.loads(data_path.read_text(encoding="utf-8"))
    reexported = json.loads(targets[0].read_text(encoding="utf-8"))
    diff = spine_toolkit.semantic_diff(original, reexported)
    report["steps"].append({"step": "compare", "ok": diff["same"], "detail": diff["summary"]})
    report["ok"] = diff["same"]
    report["detail"] = diff["summary"]
    report["reexport"] = str(targets[0])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Spine CLI bridge (find / gate / unpack / pack)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--find", action="store_true", help="print the detected CLI path and version")
    group.add_argument("--gate", metavar="JSON", help="import a JSON export into a throwaway project")
    group.add_argument("--roundtrip", metavar="JSON", help="full import/export/compare cycle")
    group.add_argument("--unpack", metavar="ATLAS")
    group.add_argument("--pack", metavar="IMAGES_DIR")
    parser.add_argument("--cli", default=None, help="explicit path to the Spine CLI")
    parser.add_argument("--out", default=None, help="output directory")
    parser.add_argument("--work", default=None, help="working directory")
    parser.add_argument("--name", default=None)
    parser.add_argument("--json", action="store_true", help="emit a JSON result")
    args = parser.parse_args(argv)

    cli, version = find_cli(args.cli)
    if cli is None:
        tried = getattr(find_cli, "last_tried", [])
        message = ("No Spine CLI found. Set SPINE_CLI_PATH to Spine.com / the macOS "
                   "Spine binary.\nTried:\n  " + "\n  ".join(tried))
        if args.json:
            print(json.dumps({"ok": False, "detail": message}))
            return 1
        print(message, file=sys.stderr)
        return 1
    version = version or cli_version(cli)

    if args.find:
        result = {"ok": True, "cli": str(cli), "version": version,
                  "shortcut": getattr(find_cli, "shortcut", None)}
    elif args.gate:
        result = import_gate(cli, args.gate, work_dir=args.work, name=args.name)
    elif args.roundtrip:
        work = args.work or str(Path(args.roundtrip).resolve().parent / ".spine-roundtrip")
        result = roundtrip(cli, args.roundtrip, work, name=args.name)
    elif args.unpack:
        out = args.out or str(Path(args.unpack).resolve().parent / "unpacked")
        result = unpack_atlas(cli, args.unpack, out)
    else:
        out = args.out or str(Path(args.pack).resolve().parent / "packed")
        result = pack_atlas(cli, args.pack, out, args.name or Path(args.pack).name)

    if args.json or args.gate or args.roundtrip:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"cli: {cli}\nversion: {version}\n{json.dumps(result, ensure_ascii=False, indent=2)}")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
