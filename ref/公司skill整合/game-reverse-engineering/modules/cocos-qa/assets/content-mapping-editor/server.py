#!/usr/bin/env python3
"""Dependency-free local editor for level image/caption/source mappings.

The server binds to 127.0.0.1 only. Drafts are separate from source writes;
project writes require an explicit preview hash and create byte-for-byte backups.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import mimetypes
import os
import re
import shutil
import struct
import tempfile
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


EDITOR_DIR = Path(__file__).resolve().parent
STATUS_VALUES = {"UNREVIEWED", "MATCH", "NEEDS_EDIT", "CONFIRMED"}
LEVEL_ITEM_RE = re.compile(
    r"\{\s*imagePath\s*:\s*(?P<quote>['\"])(?P<image>[^'\"]+)(?P=quote)\s*,"
    r"\s*width\s*:\s*(?P<width>\d+)\s*,\s*height\s*:\s*(?P<height>\d+)\s*,"
    r"\s*time\s*:\s*(?P<time>\d+)\s*\}"
)
LOCALE_ENTRY_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<key_quote>['\"])quote\.(?P<id>\d+)\."
    r"(?P<field>text|ref)(?P=key_quote)(?P<mid>[ \t]*:[ \t]*)"
    r"(?P<literal>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
    r"(?P<suffix>[ \t]*,?[ \t]*)$",
    re.MULTILINE,
)


class EditorError(Exception):
    def __init__(self, message: str, status: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = int(status)


@dataclass(frozen=True)
class TextFile:
    path: Path
    text: str
    has_bom: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_utf8_exact(path: Path) -> TextFile:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    payload = raw[3:] if has_bom else raw
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EditorError(f"文件不是有效 UTF-8：{path}（{exc}）") from exc
    return TextFile(path=path, text=text, has_bom=has_bom)


def encode_utf8_exact(text: str, has_bom: bool) -> bytes:
    raw = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + raw) if has_bom else raw


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def decode_ts_literal(literal: str) -> str:
    try:
        if literal.startswith('"'):
            return json.loads(literal)
        value = ast.literal_eval(literal)
        if not isinstance(value, str):
            raise ValueError("not a string")
        return value
    except (ValueError, SyntaxError, json.JSONDecodeError) as exc:
        raise EditorError(f"无法解析 TypeScript 字符串：{literal[:80]}") from exc


def encode_ts_literal(value: str, quote: str) -> str:
    if quote == '"':
        return json.dumps(value, ensure_ascii=False)
    escaped = (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return "'" + escaped + "'"


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    except OSError:
        return None
    return None


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


class EditorService:
    def __init__(self, config_path: Path):
        self.config_path = config_path.resolve()
        self.editor_dir = self.config_path.parent
        self.config = json.loads(read_utf8_exact(self.config_path).text)
        project_root = Path(self.config.get("project_root", "../..")).expanduser()
        if not project_root.is_absolute():
            project_root = (self.editor_dir / project_root).resolve()
        self.project_root = project_root
        self.level_path = self._project_path("level_file")
        self.locale_path = self._project_path("locale_file")
        self.image_dir = self._project_path("image_dir")
        self.draft_path = (self.editor_dir / self.config.get("draft_file", "data/story_levels.draft.json")).resolve()
        self.backup_root = (self.editor_dir / self.config.get("backup_dir", "backups")).resolve()
        self.expected_levels = int(self.config.get("expected_levels", 0))
        self.image_prefix = str(self.config.get("image_prefix", "lvPic/")).replace("\\", "/")
        self.image_extensions = tuple(self.config.get("image_extensions", [".png", ".jpg", ".jpeg", ".webp"]))
        self.allow_duplicate_images = bool(self.config.get("allow_duplicate_images", False))
        self.validate_images = bool(self.config.get("validate_images", True))
        self.lock = threading.RLock()
        for path, label in ((self.level_path, "关卡配置"), (self.locale_path, "中文文案")):
            if not path.is_file():
                raise EditorError(f"{label}文件不存在：{path}")
        if self.validate_images and not self.image_dir.is_dir():
            raise EditorError(f"图片目录不存在：{self.image_dir}")

    def _project_path(self, key: str) -> Path:
        value = self.config.get(key)
        if not value:
            raise EditorError(f"editor.config.json 缺少 {key}")
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

    def source_hashes(self) -> dict[str, str]:
        return {
            "level_file": sha256_file(self.level_path),
            "locale_file": sha256_file(self.locale_path),
        }

    def _level_region(self, text: str) -> tuple[int, int, str]:
        marker = "private readonly levelConfigs"
        start = text.find(marker)
        if start < 0:
            raise EditorError(f"未找到 {marker}")
        array_start = text.find("[", start)
        end = text.find("];", array_start)
        if array_start < 0 or end < 0:
            raise EditorError("无法定位 levelConfigs 数组边界")
        return array_start + 1, end, text[array_start + 1 : end]

    def parse_sources(self) -> list[dict[str, Any]]:
        level_file = read_utf8_exact(self.level_path)
        locale_file = read_utf8_exact(self.locale_path)
        _, _, region = self._level_region(level_file.text)
        level_rows: list[dict[str, Any]] = []
        for index, match in enumerate(LEVEL_ITEM_RE.finditer(region), start=1):
            line_end = region.find("\n", match.end())
            if line_end < 0:
                line_end = len(region)
            tail = region[match.end() : line_end].rstrip("\r")
            comment_pos = tail.find("//")
            title = tail[comment_pos + 2 :].strip() if comment_pos >= 0 else ""
            level_rows.append(
                {
                    "stable_id": index,
                    "display_order": index,
                    "image_path": match.group("image"),
                    "width": int(match.group("width")),
                    "height": int(match.group("height")),
                    "time": int(match.group("time")),
                    "config_title": title,
                }
            )
        if not level_rows:
            raise EditorError("levelConfigs 中未解析到关卡")
        if self.expected_levels and len(level_rows) != self.expected_levels:
            raise EditorError(f"关卡数量异常：期望 {self.expected_levels}，实际 {len(level_rows)}")

        localized: dict[int, dict[str, str]] = {}
        duplicates: list[str] = []
        for match in LOCALE_ENTRY_RE.finditer(locale_file.text):
            stable_id = int(match.group("id"))
            field = match.group("field")
            row = localized.setdefault(stable_id, {})
            if field in row:
                duplicates.append(f"quote.{stable_id}.{field}")
            row[field] = decode_ts_literal(match.group("literal"))
        if duplicates:
            raise EditorError("中文文案键重复：" + ", ".join(duplicates[:8]))

        output: list[dict[str, Any]] = []
        for row in level_rows:
            stable_id = row["stable_id"]
            strings = localized.get(stable_id, {})
            image_file = self.find_image(row["image_path"]) if self.validate_images else None
            issues: list[str] = []
            if "text" not in strings:
                issues.append("缺少通关配文")
            if "ref" not in strings:
                issues.append("缺少出处")
            if self.validate_images and image_file is None:
                issues.append("找不到图片")
            dimensions = png_dimensions(image_file) if image_file else None
            output.append(
                {
                    **row,
                    "caption": strings.get("text", ""),
                    "source": strings.get("ref", ""),
                    "review_status": "UNREVIEWED",
                    "reviewer_note": "",
                    "image_file": image_file.name if image_file else "",
                    "image_dimensions": list(dimensions) if dimensions else None,
                    "mapping_issues": issues,
                }
            )
        return output

    def find_image(self, image_path: str) -> Path | None:
        normalized = image_path.replace("\\", "/").strip()
        if self.image_prefix and normalized.startswith(self.image_prefix):
            normalized = normalized[len(self.image_prefix) :]
        relative = Path(normalized)
        if not normalized or relative.is_absolute() or ".." in relative.parts:
            return None
        base = (self.image_dir / relative).resolve()
        try:
            if os.path.commonpath((str(self.image_dir.resolve()), str(base))) != str(self.image_dir.resolve()):
                return None
        except ValueError:
            return None
        candidates = [base] if base.suffix else [base.with_suffix(ext) for ext in self.image_extensions]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def _merge_draft(self, levels: list[dict[str, Any]], hashes: dict[str, str]) -> tuple[list[dict[str, Any]], bool]:
        if not self.draft_path.is_file():
            return levels, False
        try:
            draft = json.loads(read_utf8_exact(self.draft_path).text)
        except (EditorError, json.JSONDecodeError):
            return levels, True
        draft_stale = draft.get("source_hashes") != hashes
        by_id = {int(row["stable_id"]): row for row in draft.get("levels", []) if isinstance(row, dict) and "stable_id" in row}
        for level in levels:
            saved = by_id.get(level["stable_id"])
            if not saved:
                continue
            for key in ("image_path", "caption", "source", "review_status", "reviewer_note"):
                if key in saved:
                    level[key] = saved[key]
            image_file = self.find_image(level["image_path"]) if self.validate_images else None
            dimensions = png_dimensions(image_file) if image_file else None
            level["image_file"] = image_file.name if image_file else ""
            level["image_dimensions"] = list(dimensions) if dimensions else None
            level["mapping_issues"] = []
            if not str(level.get("caption", "")).strip():
                level["mapping_issues"].append("缺少通关配文")
            if not str(level.get("source", "")).strip():
                level["mapping_issues"].append("缺少出处")
            if self.validate_images and image_file is None:
                level["mapping_issues"].append("找不到图片")
        return levels, draft_stale

    def load_payload(self) -> dict[str, Any]:
        with self.lock:
            hashes = self.source_hashes()
            levels, draft_stale = self._merge_draft(self.parse_sources(), hashes)
            return {
                "project_name": self.config.get("project_name", self.project_root.name),
                "project_root": str(self.project_root),
                "level_count": len(levels),
                "source_hashes": hashes,
                "draft_stale": draft_stale,
                "levels": levels,
            }

    def validate_payload(
        self,
        body: dict[str, Any],
        require_hashes: bool = True,
        strict_content: bool = True,
    ) -> list[dict[str, Any]]:
        levels = body.get("levels")
        if not isinstance(levels, list) or not levels:
            raise EditorError("请求缺少 levels")
        current_count = len(self.parse_sources())
        if len(levels) != current_count:
            raise EditorError(f"草稿关卡数异常：期望 {current_count}，实际 {len(levels)}")
        if require_hashes and body.get("source_hashes") != self.source_hashes():
            raise EditorError("工程文件已在编辑器外发生变化。请点击“重新读取工程”后再确认。", HTTPStatus.CONFLICT)

        normalized: list[dict[str, Any]] = []
        ids: list[int] = []
        images: list[str] = []
        for position, raw in enumerate(levels, start=1):
            if not isinstance(raw, dict):
                raise EditorError(f"第 {position} 行不是对象")
            try:
                stable_id = int(raw.get("stable_id"))
            except (TypeError, ValueError) as exc:
                raise EditorError(f"第 {position} 行 stable_id 无效") from exc
            image_path = str(raw.get("image_path", "")).strip().replace("\\", "/")
            caption = str(raw.get("caption", "")).strip()
            source = str(raw.get("source", "")).strip()
            status = str(raw.get("review_status", "UNREVIEWED"))
            note = str(raw.get("reviewer_note", ""))
            if stable_id != position:
                raise EditorError(f"stable_id 不可重排：第 {position} 行得到 {stable_id}")
            if strict_content and not caption:
                raise EditorError(f"第 {stable_id} 关配文不能为空")
            if strict_content and not source:
                raise EditorError(f"第 {stable_id} 关出处不能为空")
            if status not in STATUS_VALUES:
                raise EditorError(f"第 {stable_id} 关审核状态无效：{status}")
            if strict_content and self.validate_images and self.find_image(image_path) is None:
                raise EditorError(f"第 {stable_id} 关图片不存在：{image_path}")
            ids.append(stable_id)
            images.append(image_path.casefold())
            normalized.append(
                {
                    "stable_id": stable_id,
                    "image_path": image_path,
                    "caption": caption,
                    "source": source,
                    "review_status": status,
                    "reviewer_note": note,
                }
            )
        if ids != list(range(1, current_count + 1)):
            raise EditorError("stable_id 必须完整且连续")
        if strict_content and not self.allow_duplicate_images and len(images) != len(set(images)):
            raise EditorError("图片映射存在重复；当前配置禁止重复图片")
        return normalized

    def diff(self, levels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        current = self.parse_sources()
        changes: list[dict[str, Any]] = []
        for before, after in zip(current, levels):
            fields: dict[str, dict[str, str]] = {}
            for key in ("image_path", "caption", "source"):
                if before[key] != after[key]:
                    fields[key] = {"before": before[key], "after": after[key]}
            if fields:
                changes.append({"stable_id": after["stable_id"], "fields": fields})
        return changes

    def save_draft(self, body: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            levels = self.validate_payload(body, strict_content=False)
            payload = {
                "schema_version": 1,
                "updated_at": utc_now(),
                "source_hashes": self.source_hashes(),
                "levels": levels,
            }
            raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
            atomic_write(self.draft_path, raw)
            return {"saved": True, "path": str(self.draft_path), "updated_at": payload["updated_at"]}

    def preview(self, body: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            levels = self.validate_payload(body)
            changes = self.diff(levels)
            return {
                "valid": True,
                "change_count": len(changes),
                "changes": changes,
                "source_hashes": self.source_hashes(),
            }

    def _replace_level_images(self, text: str, levels: list[dict[str, Any]]) -> str:
        start, end, region = self._level_region(text)
        index = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal index
            level = levels[index]
            index += 1
            return match.group(0).replace(match.group("image"), level["image_path"], 1)

        updated = LEVEL_ITEM_RE.sub(replace, region)
        if index != len(levels):
            raise EditorError(f"关卡回写数量不一致：{index}/{len(levels)}")
        return text[:start] + updated + text[end:]

    def _replace_locale(self, text: str, levels: list[dict[str, Any]]) -> str:
        by_id = {row["stable_id"]: row for row in levels}
        seen: set[tuple[int, str]] = set()

        def replace(match: re.Match[str]) -> str:
            stable_id = int(match.group("id"))
            field = match.group("field")
            row = by_id.get(stable_id)
            if row is None:
                return match.group(0)
            key = (stable_id, field)
            if key in seen:
                raise EditorError(f"文案键重复：quote.{stable_id}.{field}")
            seen.add(key)
            value = row["caption"] if field == "text" else row["source"]
            quote = match.group("literal")[0]
            return (
                match.group("indent")
                + match.group("key_quote")
                + f"quote.{stable_id}.{field}"
                + match.group("key_quote")
                + match.group("mid")
                + encode_ts_literal(value, quote)
                + match.group("suffix")
            )

        updated = LOCALE_ENTRY_RE.sub(replace, text)
        expected = {(row["stable_id"], field) for row in levels for field in ("text", "ref")}
        missing = expected - seen
        if missing:
            closing = updated.rfind("};")
            if closing < 0:
                raise EditorError("无法定位中文文案字典结尾，不能安全补充新关卡")
            newline = "\r\n" if "\r\n" in updated else "\n"
            additions: list[str] = []
            for stable_id, field in sorted(missing):
                row = by_id[stable_id]
                value = row["caption"] if field == "text" else row["source"]
                additions.append(f'  "quote.{stable_id}.{field}": {json.dumps(value, ensure_ascii=False)},')
            prefix = "" if closing == 0 or updated[:closing].endswith(("\n", "\r")) else newline
            updated = updated[:closing] + prefix + newline.join(additions) + newline + updated[closing:]
        return updated

    def apply(self, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("confirm") is not True:
            raise EditorError("写入工程必须显式 confirm=true")
        with self.lock:
            levels = self.validate_payload(body)
            changes = self.diff(levels)
            if not changes:
                draft_result = self.save_draft(body)
                return {"applied": False, "change_count": 0, "backup_dir": None, "draft": draft_result}

            old_level = read_utf8_exact(self.level_path)
            old_locale = read_utf8_exact(self.locale_path)
            before_hashes = self.source_hashes()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_dir = (self.backup_root / timestamp).resolve()
            backup_dir.mkdir(parents=True, exist_ok=False)
            level_backup = backup_dir / self.level_path.name
            locale_backup = backup_dir / self.locale_path.name
            shutil.copy2(self.level_path, level_backup)
            shutil.copy2(self.locale_path, locale_backup)
            if self.draft_path.is_file():
                shutil.copy2(self.draft_path, backup_dir / self.draft_path.name)

            new_level_text = self._replace_level_images(old_level.text, levels)
            new_locale_text = self._replace_locale(old_locale.text, levels)
            try:
                atomic_write(self.level_path, encode_utf8_exact(new_level_text, old_level.has_bom))
                atomic_write(self.locale_path, encode_utf8_exact(new_locale_text, old_locale.has_bom))
                reparsed = self.parse_sources()
                for expected, actual in zip(levels, reparsed):
                    for key in ("stable_id", "image_path", "caption", "source"):
                        if expected[key] != actual[key]:
                            raise EditorError(f"写回复验失败：第 {expected['stable_id']} 关字段 {key}")
            except Exception:
                shutil.copy2(level_backup, self.level_path)
                shutil.copy2(locale_backup, self.locale_path)
                raise

            after_hashes = self.source_hashes()
            report = {
                "applied_at": utc_now(),
                "project_root": str(self.project_root),
                "before_hashes": before_hashes,
                "after_hashes": after_hashes,
                "change_count": len(changes),
                "changes": changes,
            }
            atomic_write(
                backup_dir / "apply-report.json",
                json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
            )
            draft_body = {"levels": levels, "source_hashes": after_hashes}
            draft_result = self.save_draft(draft_body)
            return {
                "applied": True,
                "change_count": len(changes),
                "backup_dir": str(backup_dir),
                "source_hashes": after_hashes,
                "draft": draft_result,
            }


class EditorHandler(BaseHTTPRequestHandler):
    server_version = "StoryEditor/1.0"

    @property
    def service(self) -> EditorService:
        return self.server.service  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'",
        )
        self.end_headers()

    def _send_bytes(self, raw: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self._headers(int(status), content_type, len(raw))
        self.wfile.write(raw)

    def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(raw, "application/json; charset=utf-8", status)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise EditorError("Content-Length 无效") from exc
        if length <= 0 or length > 8 * 1024 * 1024:
            raise EditorError("请求体为空或超过 8 MB")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EditorError("请求不是有效 UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise EditorError("请求 JSON 顶层必须是对象")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                raw = (EDITOR_DIR / "index.html").read_bytes()
                self._send_bytes(raw, "text/html; charset=utf-8")
                return
            if parsed.path == "/api/health":
                levels = self.service.parse_sources()
                self._json(
                    {
                        "ok": True,
                        "project_root": str(self.service.project_root),
                        "level_count": len(levels),
                        "source_hashes": self.service.source_hashes(),
                    }
                )
                return
            if parsed.path == "/api/levels":
                self._json(self.service.load_payload())
                return
            if parsed.path == "/api/image":
                values = parse_qs(parsed.query).get("path", [])
                if len(values) != 1:
                    raise EditorError("图片请求缺少 path")
                image_path = self.service.find_image(values[0])
                if image_path is None:
                    raise EditorError("图片不存在", HTTPStatus.NOT_FOUND)
                content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
                self._send_bytes(image_path.read_bytes(), content_type)
                return
            raise EditorError("接口不存在", HTTPStatus.NOT_FOUND)
        except EditorError as exc:
            self._json({"error": str(exc)}, exc.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        except Exception as exc:  # pragma: no cover - last-resort boundary
            self._json({"error": f"服务器错误：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            body = self._read_json()
            if parsed.path == "/api/draft":
                self._json(self.service.save_draft(body))
                return
            if parsed.path == "/api/preview":
                self._json(self.service.preview(body))
                return
            if parsed.path == "/api/apply":
                self._json(self.service.apply(body))
                return
            raise EditorError("接口不存在", HTTPStatus.NOT_FOUND)
        except EditorError as exc:
            self._json({"error": str(exc)}, exc.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        except Exception as exc:  # pragma: no cover - last-resort boundary
            self._json({"error": f"服务器错误：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)


class EditorHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], service: EditorService):
        super().__init__(address, EditorHandler)
        self.service = service


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="关卡编辑器_自检_") as raw_temp:
        root = Path(raw_temp)
        editor = root / "working" / "story_editor"
        assets = root / "assets"
        editor.mkdir(parents=True)
        assets.mkdir(parents=True)
        (assets / "store.level.ts").write_text(
            "private readonly levelConfigs: LevelConfig[] = [\r\n"
            "  { imagePath: 'lvPic/1', width: 3, height: 3, time: 180 }, // 一\r\n"
            "  { imagePath: 'lvPic/2', width: 4, height: 4, time: 180 }, // 二\r\n"
            "];\r\n",
            encoding="utf-8",
            newline="",
        )
        (assets / "zh-CN.ts").write_text(
            "const dict = {\n"
            '  "quote.1.text": "旧文一",\n'
            '  "quote.1.ref": "旧出处一",\n'
            "};\n",
            encoding="utf-8",
            newline="",
        )
        config = {
            "project_root": "../..",
            "level_file": "assets/store.level.ts",
            "locale_file": "assets/zh-CN.ts",
            "image_dir": "assets/images",
            "expected_levels": 0,
            "validate_images": False,
        }
        config_path = editor / "editor.config.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        service = EditorService(config_path)
        loaded = service.load_payload()
        assert loaded["level_count"] == 2
        assert loaded["levels"][1]["mapping_issues"] == ["缺少通关配文", "缺少出处"]
        loaded["levels"][1]["caption"] = "中文新配文"
        loaded["levels"][1]["source"] = "新出处 2:2"
        loaded["levels"][1]["review_status"] = "CONFIRMED"
        body = {"levels": loaded["levels"], "source_hashes": loaded["source_hashes"]}
        assert service.preview(body)["change_count"] == 1
        service.save_draft(body)
        result = service.apply({**body, "confirm": True})
        assert result["applied"] is True
        assert service.parse_sources()[1]["caption"] == "中文新配文"
        assert list((editor / "backups").glob("*/apply-report.json"))
        level_path = assets / "store.level.ts"
        locale_path = assets / "zh-CN.ts"
        level_path.write_text(
            level_path.read_text(encoding="utf-8").replace(
                "];",
                "  { imagePath: 'lvPic/3', width: 5, height: 5, time: 180 }, // 新增关卡\r\n];",
                1,
            ),
            encoding="utf-8",
            newline="",
        )
        locale_path.write_text(
            locale_path.read_text(encoding="utf-8").replace(
                "};",
                '  "quote.3.text": "新增配文",\n  "quote.3.ref": "新增出处",\n};',
                1,
            ),
            encoding="utf-8",
            newline="",
        )
        refreshed = service.load_payload()
        assert refreshed["level_count"] == 3
        assert refreshed["draft_stale"] is True
        assert refreshed["levels"][2]["mapping_issues"] == []
        print("PASS: parser, UTF-8 Chinese path, dynamic levels, missing-key append, draft, preview, backup, atomic apply, reparse")


def main() -> None:
    parser = argparse.ArgumentParser(description="本地关卡图片与配文编辑器")
    parser.add_argument("--config", type=Path, default=EDITOR_DIR / "editor.config.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("安全限制：仅允许监听 127.0.0.1 或 localhost")
    service = EditorService(args.config)
    port = args.port if args.port is not None else int(service.config.get("port", 8765))
    server = EditorHTTPServer((args.host, port), service)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"关卡编辑器已启动：{url}")
    print("关闭窗口或按 Ctrl+C 停止。")
    if args.open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
