#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""game-skinning-pipeline shared helpers (standard library only)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import struct
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCRIPT_VERSION = "1.0.0"
SCHEMA_MANIFEST = "1.0"
SCHEMA_SKIN_MAP = "1.0"
SCHEMA_ATLAS_INDEX = "1.0"

# Exit codes (plan section 11)
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_WARNING = 2
EXIT_INVALID = 3
EXIT_AMBIGUOUS = 4

# Directories skipped by default during scans (plan section 11)
DEFAULT_SKIP_DIRS = {
    ".git", "node_modules", "library", "Library", "temp", "Temp",
    "build", "Build", ".import", "obj", "bin",
}

# P0 supported extensions (plan section 12.4). .txt added for handoff parity
# with the sudoku-re TextAsset exports (164 text assets).
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTS = {".wav", ".ogg", ".mp3"}
FONT_EXTS = {".ttf", ".otf"}
MESH_EXTS = {".fbx", ".obj"}
UNITY_TEXT_EXTS = {".prefab", ".unity", ".asset", ".mat", ".controller",
                   ".overridecontroller", ".anim", ".spriteatlas"}
COCOS_REF_EXTS = {".fire", ".prefab", ".scene", ".anim", ".json"}
UNITY_REF_EXTS = {".prefab", ".unity", ".asset", ".mat", ".controller",
                  ".overridecontroller"}
ALL_SUPPORTED_EXTS = (IMAGE_EXTS | AUDIO_EXTS | FONT_EXTS | MESH_EXTS
                      | {".json", ".plist", ".meta", ".txt"}
                      | {".atlas"} | UNITY_TEXT_EXTS | COCOS_REF_EXTS)

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
UNITY_GUID_RE = re.compile(r"guid:\s*([0-9a-fA-F]{32})")
UNITY_FILEID_RE = re.compile(r"fileID:\s*(-?\d+)")

CN_TZ = timezone(timedelta(hours=8), "CN")


def now_iso() -> str:
    return datetime.now(CN_TZ).isoformat(timespec="seconds")


def to_posix(p: Path) -> str:
    return p.as_posix()


def norm_rel(p: Path, root: Path) -> str:
    """Stable posix relative path with forward slashes (case preserved)."""
    return p.relative_to(root).as_posix()


def norm_key(p: str) -> str:
    """Case-insensitive normalized path key for comparisons on Windows."""
    return p.replace("\\", "/").lower()


def norm_name(name: str) -> str:
    """Normalized name for fuzzy matching: lower, strip spaces and -/_."""
    return re.sub(r"[\s\-_]+", "", name).lower()


def stable_sort(items: Iterable[Dict[str, Any]], keys: Tuple[str, ...] = ("type", "path", "id")) -> List[Dict[str, Any]]:
    """Sort asset dicts stably by the given keys so diffs are readable."""
    return sorted(items, key=lambda d: tuple(str(d.get(k) or "") for k in keys))


def read_json(path: Path) -> Any:
    """Read JSON, tolerant of a UTF-8 BOM (utf-8-sig)."""
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return json.loads(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode JSON file as UTF-8: {path}")


def write_json(path: Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def file_hash(path: Path, digest_size: int = 16) -> str:
    """Streaming blake2b hash (never loads the whole file into memory)."""
    h = hashlib.blake2b(digest_size=digest_size)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def png_info(path: Path) -> Dict[str, Any]:
    """Read PNG width/height/bit-depth/color-type from the IHDR header only."""
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        head = f.read(21)  # length(4) + 'IHDR'(4) + data(13)
        if len(head) < 21 or head[4:8] != b"IHDR":
            raise ValueError("PNG missing IHDR chunk")
        width, height = struct.unpack(">II", head[8:16])
        return {
            "width": width,
            "height": height,
            "bit_depth": head[16],
            "color_type": head[17],
            "interlace": head[20],
        }


def jpeg_info(path: Path) -> Dict[str, Any]:
    """Read JPEG dimensions by walking markers (SOF0/1/2/9/10/11)."""
    with open(path, "rb") as f:
        data = f.read(64 * 1024)
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG file")
    pos = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker == 0xD8 or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xD9 or marker == 0xDA:
            break
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if marker in sof:
            height = struct.unpack(">H", data[pos + 5:pos + 7])[0]
            width = struct.unpack(">H", data[pos + 7:pos + 9])[0]
            return {"width": width, "height": height}
        pos += 2 + length
    raise ValueError("JPEG dimensions not found (progressive/truncated?)")


def webp_info(path: Path) -> Dict[str, Any]:
    """Read WebP dimensions for VP8 / VP8L / VP8X containers."""
    with open(path, "rb") as f:
        head = f.read(30)
    if head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        raise ValueError("not a WebP file")
    if head[12:16] == b"VP8X":
        # 24-bit canvas width/height little-endian, 1px granularity
        w = int.from_bytes(head[24:27], "little") + 1
        h = int.from_bytes(head[27:30], "little") + 1
        return {"width": w, "height": h}
    if head[12:16] == b"VP8L":
        bits = int.from_bytes(head[21:25], "little")
        w = (bits & 0x3FFF) + 1
        h = ((bits >> 14) & 0x3FFF) + 1
        return {"width": w, "height": h}
    if head[12:16] == b"VP8 ":
        w = int.from_bytes(head[26:28], "little") & 0x3FFF
        h = int.from_bytes(head[28:30], "little") & 0x3FFF
        return {"width": w, "height": h}
    raise ValueError("unknown WebP variant")


def image_info(path: Path) -> Optional[Dict[str, Any]]:
    """Return {width,height} for png/jpg/jpeg/webp or None if not readable."""
    ext = path.suffix.lower()
    try:
        if ext == ".png":
            return png_info(path)
        if ext in (".jpg", ".jpeg"):
            return jpeg_info(path)
        if ext == ".webp":
            return webp_info(path)
    except Exception:
        return None
    return None


def safe_size(path: Path) -> Optional[int]:
    try:
        return path.stat().st_size
    except OSError:
        return None


def safe_mtime(path: Path) -> Optional[str]:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, CN_TZ).isoformat(timespec="seconds")
    except OSError:
        return None


def find_uuids(text: str) -> List[str]:
    return sorted(set(m.group(0).lower() for m in UUID_RE.finditer(text)))


def find_unity_refs(text: str) -> List[Dict[str, str]]:
    """Best-effort guid/fileID reference scan (plan 12.5, not semantic)."""
    out: List[Dict[str, str]] = []
    for m in UNITY_GUID_RE.finditer(text):
        out.append({"guid": m.group(1).lower()})
    for m in UNITY_FILEID_RE.finditer(text):
        # attach fileID to the most recently seen guid if present
        if out and "fileID" not in out[-1]:
            out[-1]["fileID"] = m.group(1)
        else:
            out.append({"guid": None, "fileID": m.group(1)})
    return out


class Logger:
    """Console + optional machine-readable JSON log writer."""

    def __init__(self, verbose: bool = False, json_log: Optional[Path] = None,
                 fail_on_warning: bool = False):
        self.verbose = verbose
        self.json_log = Path(json_log) if json_log else None
        self.fail_on_warning = fail_on_warning
        self.warnings: List[Dict[str, str]] = []
        self.logged: List[Dict[str, Any]] = []
        self._init_logging()

    def _init_logging(self) -> None:
        logging.basicConfig(level=logging.DEBUG if self.verbose else logging.INFO,
                            format="%(levelname)s %(message)s", stream=sys.stdout)

    def _record(self, level: str, msg: str) -> None:
        entry = {"ts": now_iso(), "level": level, "message": msg}
        self.logged.append(entry)
        if self.json_log:
            self.json_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def info(self, msg: str) -> None:
        logging.info(msg)
        self._record("info", msg)

    def debug(self, msg: str) -> None:
        if self.verbose:
            logging.debug(msg)
            self._record("debug", msg)

    def warn(self, msg: str, code: str = "warning") -> None:
        logging.warning(msg)
        self.warnings.append({"code": code, "message": msg})
        self._record("warning", msg)

    def error(self, msg: str) -> None:
        logging.error(msg)
        self._record("error", msg)


def write_report(path: Path, header: Dict[str, Any], sections: List[Dict[str, Any]]) -> None:
    """Write a markdown report with a reproducible header block."""
    lines = [f"# {header['title']}", ""]
    lines.append("> 脚本版本: `%s` | 生成时间: `%s`" % (SCRIPT_VERSION, now_iso()))
    lines.append(">")
    lines.append("> 命令行参数: `%s`" % header.get("command_line", ""))
    lines.append(">")
    lines.append("> 输入: `%s`" % header.get("input", ""))
    lines.append(">")
    lines.append("> 输出: `%s`" % header.get("output", ""))
    lines.append("")
    for sec in sections:
        lines.append("## %s" % sec["title"])
        lines.append("")
        lines.append(sec.get("body", ""))
        lines.append("")
    write_utf8(path, "\n".join(lines))


def write_utf8(path: Path, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def read_utf8(path: Path) -> str:
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def ensure_safe_outside_input(output: Path, input_root: Path) -> None:
    """Warn if output lives inside the input tree (scanner excludes it anyway)."""
    try:
        output.resolve().relative_to(input_root.resolve())
        return True
    except ValueError:
        return False


def id_from_path(rel: str) -> str:
    """Stable id for assets without uuid: lowercase normalized path hash."""
    return "path-" + hashlib.blake2b(rel.lower().encode("utf-8"), digest_size=8).hexdigest()


def relpath_safe(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
