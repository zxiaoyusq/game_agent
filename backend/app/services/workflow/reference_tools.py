"""面向本地参考 ZIP 的只读研究与按件取材，不执行来源代码或整包复制。"""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from langchain_core.tools import BaseTool, tool

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 5000
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250
MAX_EXTRACTED_BYTES = 8 * 1024 * 1024
TEXT_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".json", ".html", ".css", ".md", ".txt",
                 ".xml", ".plist", ".atlas", ".yaml", ".yml", ".glsl", ".frag", ".vert"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".svg", ".wav", ".mp3",
                  ".ogg", ".m4a", ".ttf", ".otf", ".woff", ".woff2", ".json", ".atlas"}
OUTPUT_PREFIXES = (("reference-assets",), ("reference-inputs",), ("public", "assets"))


def _relative(value: str, *, directory: bool = False) -> Path:
    """ZIP 与输出统一拒绝绝对路径、Windows 路径、隐藏段和隐式归一化。"""
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError("参考路径必须是非空的普通相对路径")
    name = value[:-1] if directory and value.endswith("/") else value
    parts = name.split("/")
    if ("\\" in name or any(ord(char) < 32 for char in name)
            or any(not part or part.startswith(".") or ":" in part for part in parts)):
        raise ValueError("参考路径包含不允许的目录段")
    path = Path(name)
    if path.is_absolute():
        raise ValueError("参考路径不能是绝对路径")
    return path


def _inside(base: Path, relative: Path) -> Path:
    """显式检查全部父目录和最终文件，不跟随链接读取或写入别处。"""
    if base.is_symlink():
        raise ValueError("参考目录或工作区不能是符号链接")
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("参考路径不能经过符号链接")
    if not current.resolve().is_relative_to(base.resolve()):
        raise ValueError("参考路径超出授权目录")
    return current


@contextmanager
def _open_archive(root: Path, value: str) -> Iterator[tuple[zipfile.ZipFile, dict, dict[str, zipfile.ZipInfo]]]:
    """先核对整个目录表，再允许读取任何一项，哈希与 ZIP 共用同一文件句柄。"""
    relative = _relative(value)
    if relative.parts[0] == "ref":
        relative = Path(*relative.parts[1:])
    archive_path = _inside(root / "ref", relative)
    if archive_path.suffix.lower() != ".zip" or not archive_path.is_file():
        raise ValueError("请提供 ref/ 内真实存在的 ZIP 文件")
    if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("参考 ZIP 超过 64MB，不能直接研究")
    try:
        with archive_path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
            source.seek(0)
            with zipfile.ZipFile(source) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_ENTRIES:
                    raise ValueError("参考 ZIP 文件数超过允许上限")
                members = {}
                total = 0
                for info in entries:
                    canonical = _relative(info.filename, directory=info.is_dir()).as_posix()
                    if canonical in members:
                        raise ValueError("参考 ZIP 包含重复或冲突的条目名称")
                    mode = info.external_attr >> 16
                    if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                        raise ValueError("参考 ZIP 包含符号链接或特殊文件")
                    if info.flag_bits & 1:
                        raise ValueError("参考 ZIP 包含加密条目，不能自动读取")
                    if (info.file_size > MAX_MEMBER_BYTES
                            or info.file_size > max(info.compress_size, 1) * MAX_COMPRESSION_RATIO):
                        raise ValueError("参考 ZIP 条目超过大小或压缩比限制")
                    total += info.file_size
                    if total > MAX_EXPANDED_BYTES:
                        raise ValueError("参考 ZIP 展开总大小超过 128MB")
                    members[canonical] = info
                # 文件不能同时成为另一项的父目录，避免研究名称与写出含义不同。
                for name in members:
                    if any(parent.as_posix() in members and not members[parent.as_posix()].is_dir()
                           for parent in Path(name).parents if parent.as_posix() != "."):
                        raise ValueError("参考 ZIP 文件与目录路径冲突")
                metadata = {"archive": relative.as_posix(), "archive_sha256": digest,
                            "total_entries": len(members), "total_uncompressed_bytes": total}
                yield archive, metadata, members
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as error:
        raise ValueError("参考 ZIP 损坏或使用了不支持的压缩格式") from error


def _member_candidates(members: dict[str, zipfile.ZipInfo], name: str) -> list[str]:
    """只推荐同文件名或同逻辑名的真实文件，不自动改读相似但不同的资源。"""
    basename = Path(name).name
    # Cocos 导出文件常在扩展名前带内容哈希；只用于给出候选，不改变读取语义。
    logical_name = re.sub(r"\.[0-9a-f]{5,}(?=\.)", "", basename, flags=re.IGNORECASE)
    ranked = []
    for candidate, info in members.items():
        if info.is_dir():
            continue
        candidate_name = Path(candidate).name
        candidate_logical = re.sub(r"\.[0-9a-f]{5,}(?=\.)", "", candidate_name, flags=re.IGNORECASE)
        if candidate_name == basename:
            ranked.append((0, candidate))
        elif candidate_logical == logical_name:
            ranked.append((1, candidate))
    return [candidate for _, candidate in sorted(ranked)[:6]]


def _read_member(archive: zipfile.ZipFile, members: dict, member: str) -> tuple[bytes, str]:
    name = _relative(member, directory=True).as_posix()
    info = members.get(name)
    if info is None or info.is_dir():
        children = [path for path, value in members.items() if path.startswith(name + "/") and not value.is_dir()]
        directory = (info is not None and info.is_dir()) or any(path.startswith(name + "/") for path in members)
        reason = "指定条目是目录，不能作为文件读取" if directory else "包内不存在指定文件"
        candidates = children[:6] if directory else _member_candidates(members, name)
        query = name + "/" if directory else Path(name).name.split(".")[0]
        hint = ("实际存在的候选文件（仅供定位，尚未读取）：" + json.dumps(candidates, ensure_ascii=False) + "。"
                if candidates else "没有同名候选；该资源可能未收录或已合并打包。")
        raise ValueError(
            f"{reason}：{name}。"
            f"请调用 list_reference_archive，path 保持当前 ZIP，query={json.dumps(query, ensure_ascii=False)}；"
            "member 必须完整复制返回的 entries[].path。清单仍无匹配时如实记录缺失，不要重复猜路径。" + hint
        )
    # 读取上限不仅采信目录表；最终长度和 CRC 同时由 ZIP 解码验证。
    with archive.open(info) as stream:
        data = stream.read(MAX_MEMBER_BYTES + 1)
    if len(data) > MAX_MEMBER_BYTES or len(data) != info.file_size:
        raise ValueError("参考 ZIP 条目实际长度与目录表不符")
    return data, name


def create_reference_tools(root: Path, workspace: Path, emit: Callable[[str, str, dict], None]) -> list[BaseTool]:
    """每次运行绑定明确根目录；事件记录包与条目哈希，便于核对真实研究来源。"""

    @tool
    def list_reference_archive(path: str, offset: int = 0, limit: int = 100, query: str = "") -> str:
        """分页列出 ZIP 内真实条目、尺寸、SHA256；query 按路径/文件名做不区分大小写的子串搜索。offset 按匹配结果分页，member 必须完整复制 entries[].path；path 相对 ref/。"""
        if len(query) > 256:
            raise ValueError("包内搜索关键词不能超过 256 字符")
        with _open_archive(root, path) as (archive, metadata, members):
            names = sorted(name for name in members if query.casefold() in name.casefold())
            start = min(max(offset, 0), len(names))
            end = min(start + min(max(limit, 1), 200), len(names))
            entries = []
            for name in names[start:end]:
                info = members[name]
                item = {"path": name, "size": info.file_size, "compressed_size": info.compress_size,
                        "is_directory": info.is_dir()}
                if not info.is_dir():
                    data, _ = _read_member(archive, members, name)
                    item["sha256"] = hashlib.sha256(data).hexdigest()
                entries.append(item)
            result = {**metadata, "query": query, "matched_entries": len(names), "offset": start, "end": end,
                      "has_more": end < len(names), "next_offset": end if end < len(names) else None, "entries": entries}
        emit("reference_archive_listed", "已核对并读取参考 ZIP 目录", {**metadata, "query": query, "matched_entries": len(names), "offset": start, "end": end})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def read_reference_archive(path: str, member: str, offset: int = 0, limit: int = 24000) -> str:
        """读取 ZIP 内 UTF-8 代码/配置文本；member 必须复制 list_reference_archive 返回的完整 path，不能按 UUID、旧哈希或网页 URL 猜测。offset/limit 按字符，最多60000字符；图片使用按件提取工具。"""
        with _open_archive(root, path) as (archive, metadata, members):
            data, name = _read_member(archive, members, member)
            if Path(name).suffix.lower() not in TEXT_SUFFIXES or b"\x00" in data:
                raise ValueError("该条目不是允许读取的代码或配置文本")
            try:
                content = data.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise ValueError("参考文本必须使用有效 UTF-8 编码") from error
            start = min(max(offset, 0), len(content))
            end = min(start + min(max(limit, 1), 60000), len(content))
            evidence = {**metadata, "member": name, "sha256": hashlib.sha256(data).hexdigest(),
                        "offset": start, "end": end, "total_chars": len(content)}
        emit("reference_archive_read", "已实际读取参考 ZIP 内文本", evidence)
        return json.dumps({**evidence, "content": content[start:end]}, ensure_ascii=False)

    @tool
    def extract_reference_asset(path: str, member: str, destination: str) -> str:
        """逐字节提取一个参考文件，不转换格式；member 完整复制 ZIP 清单，destination 保持原后缀。素材写 reference-assets/或public/assets/，代码只写reference-inputs/供阅读；不覆盖、不执行。PNG转WebP须先以.png提取，再在美术阶段调用process_art_image。"""
        output = _relative(destination)
        prefix = next((parts for parts in OUTPUT_PREFIXES if output.parts[:len(parts)] == parts), None)
        if prefix is None or len(output.parts) <= len(prefix):
            raise ValueError("取材目标必须是 reference-assets/、public/assets/ 或 reference-inputs/ 内的具体文件")
        with _open_archive(root, path) as (archive, metadata, members):
            data, name = _read_member(archive, members, member)
            suffix = Path(name).suffix.lower()
            allowed = TEXT_SUFFIXES if prefix == ("reference-inputs",) else ASSET_SUFFIXES
            if suffix not in allowed:
                raise ValueError(f"来源类型 {suffix} 不能写入所选取材目录；代码文本仅允许写 reference-inputs/ 供阅读")
            if output.suffix.lower() != suffix:
                suggested = output.with_suffix(suffix).as_posix()
                raise ValueError(
                    f"提取工具不转换格式：来源 member={name}，目标 destination={destination} 的后缀不同。"
                    f"请先保持原后缀，destination={suggested}；需要 PNG/WebP 转换时，再在美术阶段调用 process_art_image。"
                )
            if prefix == ("reference-inputs",):
                try:
                    if b"\x00" in data:
                        raise ValueError("来源代码不能是二进制")
                    data.decode("utf-8-sig")
                except UnicodeDecodeError as error:
                    raise ValueError("来源代码必须是 UTF-8 文本") from error
            target = _inside(workspace, output)
            digest = hashlib.sha256(data).hexdigest()
            reused = False
            if target.exists():
                if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise ValueError("目标已存在且内容不同，不能覆盖已有修改；请使用新的文件名")
                reused = True
            else:
                # 按件取材总量受限；原包研究不应把旧引擎和全部资源塞进新游戏。
                total = 0
                for parts in OUTPUT_PREFIXES:
                    directory = _inside(workspace, Path(*parts))
                    if directory.exists():
                        total += sum(item.stat().st_size for item in directory.rglob("*")
                                     if item.is_file() and not item.is_symlink())
                if total + len(data) > MAX_EXTRACTED_BYTES:
                    raise ValueError("取材目录总量超过 8MB，请只选择本次需要的资源")
                target.parent.mkdir(parents=True, exist_ok=True)
                _inside(workspace, output)
                # 独占创建保证并发取材也不能覆盖其他工具刚写出的文件。
                with target.open("xb") as destination_file:
                    destination_file.write(data)
            evidence = {**metadata, "member": name, "path": output.as_posix(), "sha256": digest,
                        "bytes": len(data), "reused": reused, "purpose": "reference_only" if prefix == ("reference-inputs",) else "reference_asset"}
        emit("reference_asset_copied", "已按件取出参考文件并记录真实来源", evidence)
        return json.dumps(evidence, ensure_ascii=False)

    return [list_reference_archive, read_reference_archive, extract_reference_asset]
