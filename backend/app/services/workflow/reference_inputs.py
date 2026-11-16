"""MCP 参考资料索引与受控文件上传；只保存输入，不执行或整包解压来源代码。"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import threading
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.services import reference_games
from app.services.workflow.reference_tools import _open_archive, _read_member
from app.services.workflow.submissions import describe_submission

MAX_UPLOAD_BYTES = 64 * 1024 * 1024
MAX_CLIENT_BYTES = 256 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
TEXT_SUFFIXES = {".txt", ".md", ".json", ".csv", ".yaml", ".yml", ".js", ".mjs", ".cjs", ".ts", ".html", ".css", ".xml"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_UPLOAD_SUFFIXES = TEXT_SUFFIXES | IMAGE_SUFFIXES | {".zip"}
UPLOAD_DIRECTORY = "mcp-inputs"
_UPLOAD_LOCK = threading.Lock()


def _client_id(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-z0-9_-]{1,128}", value) is None:
        raise ValueError("上传调用方标识无效")
    return value


def _relative(value: str) -> Path:
    """不隐式修正远端路径；Windows、本机绝对路径及隐藏目录必须显式报错。"""
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError("参考路径必须是非空相对路径，最多 1024 字符")
    name = value[4:] if value.startswith("ref/") else value
    if name.endswith("/"):
        name = name[:-1]
    parts = name.split("/")
    if ("\\" in name or any(ord(char) < 32 or ord(char) == 127 for char in name)
            or any(not part or part.startswith(".") or ":" in part for part in parts)):
        raise ValueError("参考路径包含不允许的目录段")
    path = Path(name)
    if path.is_absolute():
        raise ValueError("参考资料必须使用服务器 ref/ 内的相对路径")
    return path


def _plain_child(base: Path, relative: Path) -> Path:
    """检查全部祖先和每个路径段，避免通过目录链接读写其它客户端或工程文件。"""
    base = base.absolute()
    if any(path.is_symlink() for path in (base, *base.parents)):
        raise ValueError("参考资料目录不能经过符号链接")
    current = base
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("参考资料路径不能经过符号链接")
    if not current.resolve().is_relative_to(base.resolve()):
        raise ValueError("参考资料路径超出允许目录")
    return current


def validate_references(root: Path, client_id: str, paths: list[str]) -> list[str]:
    """创建项目与模板输入共用引用校验；公共资料可读，上传只允许调用方自己的命名空间。"""
    client_id = _client_id(client_id)
    if not isinstance(paths, list) or len(paths) > 100:
        raise ValueError("参考资料必须是最多 100 项的路径列表")
    result = []
    for value in paths:
        relative = _relative(value)
        if relative.parts[0] == UPLOAD_DIRECTORY:
            if len(relative.parts) < 2 or relative.parts[1] != client_id:
                raise PermissionError("无权引用其他客户端上传资料或整个上传目录")
        path = _plain_child(root / "ref", relative)
        if not path.is_file() and not path.is_dir():
            raise FileNotFoundError("参考资料不存在，请先查询服务器索引或上传本机文件")
        if relative.as_posix() not in result:
            result.append(relative.as_posix())
    return result


def _private_root(root: Path) -> Path:
    return _plain_child(root, Path("backend/data/workflow/reference_uploads"))


def _upload_records(root: Path, client_id: str) -> list[dict]:
    """只扫描本调用方的收据；记录存于私有目录，不跟随链接或输出内部路径。"""
    directory = _plain_child(_private_root(root), Path("receipts") / client_id)
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            raise ValueError("上传收据不是普通文件")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("client_id") != client_id or not isinstance(record.get("reference"), dict):
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            raise ValueError("上传收据损坏，请检查服务端记录") from None
        records.append(record)
    return records


def list_references(root: Path, client_id: str, query: str = "", offset: int = 0, limit: int = 20) -> dict:
    """分页查询公共顶层资料、现有游戏索引和自己的上传；不递归遍历 APK 拆解树。"""
    client_id = _client_id(client_id)
    if not isinstance(query, str) or len(query) > 200 or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("查询关键词最多 200 字符，offset 非负，limit 为 1 至 50")
    reference_root = _plain_child(root, Path("ref"))
    entries = {}
    if reference_root.is_dir():
        # 顶层目录可作为已有模板引用，但上传根目录不能暴露给客户端。
        for path in sorted(reference_root.iterdir()):
            if path.name.startswith(".") or path.name == UPLOAD_DIRECTORY or path.is_symlink():
                continue
            if path.is_dir() or path.is_file():
                try:
                    validate_references(root, client_id, [path.name])
                except (ValueError, PermissionError, FileNotFoundError):
                    continue
                entries[path.name] = {"name": path.name, "kind": "directory" if path.is_dir() else "file",
                                      "source": "library", "reference_path": path.name}
                if path.is_file():
                    entries[path.name]["bytes"] = path.stat().st_size

    games_root = reference_root / reference_games.REFERENCE_PREFIX
    catalog = reference_games.list_reference_games(root=games_root)
    for game in catalog["items"]:
        reference = game["directory_reference_path"]
        # 索引只提供存在性；完整 ZIP 检查在 Agent 实际读取时执行。
        entries[reference] = {"name": game["name"], "kind": "game", "source": "library",
                              "reference_path": reference, "description": game["description"][:1000],
                              "category": game["category"], "package_status": game["package_status"],
                              "package_paths": [reference + "/" + item["name"] for item in game["package_files"]]}
    # 远程 Agent 与页面共用案例索引；只提供按需引用的路径，不把全工程塞入上下文。
    for research in catalog["summary"]["research"]:
        reference = research["reference_path"]
        entries[reference] = {"name": research["name"], "kind": "directory", "source": "library",
                              "reference_path": reference, "description": "来源案例与研究资料，历史结果不代表当前项目已验收"}
        for document in research["documents"]:
            entries[document["reference_path"]] = {**document, "kind": "file", "source": "library"}
    for record in _upload_records(root, client_id):
        item = record["reference"]
        reference = item["reference_path"]
        validate_references(root, client_id, [reference])
        entries[reference] = item
    matches = [item for _, item in sorted(entries.items())
               if query.casefold() in (item["name"] + " " + item["reference_path"] + " " + item.get("description", "")).casefold()]
    start = min(offset, len(matches))
    selected = matches[start:start + limit]
    next_offset = start + len(selected)
    return {"items": selected, "total": len(matches), "query": query, "offset": start,
            "next_offset": next_offset, "has_more": next_offset < len(matches)}


def _filename(value: str) -> str:
    if not isinstance(value, str) or len(value) > 180 or len(value.encode("utf-8")) > 240:
        raise ValueError("上传文件名最多 180 字符，UTF-8 编码后最多 240 字节")
    path = _relative(value)
    if path.name != value or len(path.parts) != 1 or path.suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ValueError("上传须提供普通文件名，类型仅限 ZIP、UTF-8 文本或常见图片")
    return value


def _validate_content(temporary_root: Path, filename: str, size: int) -> dict:
    """上传校验与 Agent 的参考 ZIP 读取共用边界；校验只读，不解压或执行。"""
    path = temporary_root / "ref" / filename
    suffix = path.suffix.lower()
    if suffix == ".zip":
        with _open_archive(temporary_root, filename) as (archive, metadata, members):
            if not members:
                raise ValueError("参考 ZIP 不能为空")
            for name, info in members.items():
                if not info.is_dir():
                    _read_member(archive, members, name)
            return {"kind": "zip", "entries": metadata["total_entries"],
                    "uncompressed_bytes": metadata["total_uncompressed_bytes"]}
    if suffix in TEXT_SUFFIXES:
        if size > MAX_TEXT_BYTES:
            raise ValueError("文本参考资料最多 2MB")
        try:
            content = path.read_text(encoding="utf-8-sig")
            if "\x00" in content:
                raise ValueError("文本参考资料不能包含二进制内容")
            if suffix == ".json":
                json.loads(content)
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError("参考文本必须是有效 UTF-8；JSON 文件还须符合 JSON 格式") from None
        return {"kind": "text", "encoding": "utf-8"}
    if size > MAX_IMAGE_BYTES:
        raise ValueError("图片参考资料最多 10MB")
    formats = {"PNG": {".png"}, "JPEG": {".jpg", ".jpeg"}, "WEBP": {".webp"}, "GIF": {".gif"}}
    try:
        with Image.open(path) as image:
            if suffix not in formats.get(image.format, set()):
                raise ValueError("图片编码与文件后缀不一致")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("图片像素总量超过允许上限")
            metadata = {"kind": "image", "width": image.width, "height": image.height, "format": image.format}
            image.verify()
            return metadata
    except (OSError, Image.DecompressionBombError):
        raise ValueError("参考图片损坏或像素总量超过允许上限") from None


def _write_receipt(receipt: Path, record: dict) -> None:
    """先在私有目录写完收据再原子替换，任何写入失败都清理临时文件。"""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=receipt.parent,
                                         suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(record, temporary, ensure_ascii=False, indent=2)
        temporary_path.replace(receipt)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _commit_upload(root: Path, client_id: str, filename: str, request_id: str, source: Path,
                   digest: str, size: int, validation: dict) -> dict:
    """在进程内串行提交内容和收据；同请求异内容拒绝，文件不可覆盖。"""
    submission = describe_submission(request_id, f"mcp:{client_id}:reference-upload",
                                     {"filename": filename, "sha256": digest, "bytes": size})
    receipt_name = hashlib.sha256(request_id.encode()).hexdigest() + ".json"
    receipt = _plain_child(_private_root(root), Path("receipts") / client_id / receipt_name)
    relative = Path(UPLOAD_DIRECTORY) / client_id / digest / filename
    with _UPLOAD_LOCK:
        # 取得提交锁之后再次检查路径，排队中的请求不能沿用旧的路径检查结果。
        target = _plain_child(root / "ref", relative)
        records = _upload_records(root, client_id)
        previous = next((item for item in records if item.get("submission", {}).get("request_id") == request_id), None)
        if previous:
            if previous.get("submission") != submission:
                raise ValueError("request_id 已用于不同文件内容或文件名，请为新上传使用新标识")
            if not target.is_file():
                raise ValueError("此前上传资料已丢失或内容变化，不能沿用旧收据")
            with target.open("rb") as content:
                if hashlib.file_digest(content, "sha256").hexdigest() != digest:
                    raise ValueError("此前上传资料已丢失或内容变化，不能沿用旧收据")
            return previous["reference"]

        # 只统计已提交文件的唯一引用，同内容的网络重试不重复占用额度。
        existing = {item["reference"]["reference_path"]: item["reference"]["bytes"] for item in records}
        if relative.as_posix() not in existing and sum(existing.values()) + size > MAX_CLIENT_BYTES:
            raise ValueError("本客户端上传资料总量已达到 256MB 上限")
        target.parent.mkdir(parents=True, exist_ok=True)
        target = _plain_child(root / "ref", relative)
        created = False
        if target.exists():
            if not target.is_file():
                raise ValueError("上传目标不是普通文件，不能覆盖")
            with target.open("rb") as content:
                if hashlib.file_digest(content, "sha256").hexdigest() != digest:
                    raise ValueError("上传目标已存在但内容不一致，不能覆盖")
        else:
            try:
                with target.open("xb") as destination:
                    created = True
                    with source.open("rb") as content:
                        shutil.copyfileobj(content, destination, 1024 * 1024)
            except BaseException:
                if created:
                    target.unlink(missing_ok=True)
                raise
        result = {"name": filename, "kind": "file", "source": "uploaded", "reference_path": relative.as_posix(),
                  "bytes": size, "sha256": digest, "validation": validation,
                  "created_at": datetime.now(timezone.utc).isoformat()}
        record = {"client_id": client_id, "submission": submission, "reference": result}
        try:
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt = _plain_child(_private_root(root), Path("receipts") / client_id / receipt_name)
            _write_receipt(receipt, record)
        except BaseException:
            # 新文件和收据作为一次提交；失败时只移除本次创建的文件，保留复用的旧内容。
            if created:
                target.unlink(missing_ok=True)
            raise
        return result


async def upload_reference(root: Path, client_id: str, filename: str, request_id: str,
                           chunks: AsyncIterable[bytes]) -> dict:
    """接收认证 HTTP 请求的原始字节流；限制在读取过程中执行，不能信任 Content-Length。"""
    client_id = _client_id(client_id)
    filename = _filename(filename)
    if not isinstance(request_id, str):
        raise ValueError("上传必须提供 request_id")
    describe_submission(request_id, f"mcp:{client_id}:reference-upload", {})
    staging = _plain_child(_private_root(root), Path("staging"))
    staging.mkdir(parents=True, exist_ok=True)
    _plain_child(_private_root(root), Path("staging"))
    with tempfile.TemporaryDirectory(prefix="upload-", dir=staging) as directory:
        temporary_root = Path(directory)
        (temporary_root / "ref").mkdir()
        source = temporary_root / "ref" / filename
        size = 0
        digest = hashlib.sha256()
        with source.open("xb") as output:
            async for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise ValueError("上传请求体必须是文件字节流")
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise ValueError("上传文件超过 64MB 上限")
                output.write(chunk)
                digest.update(chunk)
        if not size:
            raise ValueError("参考文件不能为空")
        validation = _validate_content(temporary_root, filename, size)
        return _commit_upload(root, client_id, filename, request_id, source, digest.hexdigest(), size, validation)
