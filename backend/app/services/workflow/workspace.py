"""项目路径边界、文件快照与运行输入指纹；根目录由调用方显式提供。"""

import hashlib
import json
import os
from pathlib import Path


def checked_child(base: Path, relative: str) -> Path:
    """所有输入路径与符号链接解析后仍须位于授权根目录。"""
    path = (base / relative.lstrip("/")).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("路径超出授权目录")
    return path


def resolve_workspace(root: Path, relative: str) -> Path:
    """只接受 games 内的独立目录；拒绝根目录、符号链接和目录穿越。"""
    raw = Path(relative)
    path = (root / raw).resolve()
    games = (root / "games").resolve()
    if raw.is_absolute() or not path.is_relative_to(games) or path == games or ".." in raw.parts:
        raise ValueError("项目工作区必须是 games/ 下的独立目录")
    cursor = root
    for part in raw.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("项目工作区不能使用符号链接")
    return path


def normalize_reference(root: Path, path: str) -> str:
    """接受相对 ref/ 的路径或显式 ref/ 前缀，拒绝绝对路径和目录穿越。"""
    raw = Path(path)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError("参考资料必须位于工程 ref/ 目录内")
    relative = raw.relative_to("ref").as_posix() if raw.parts and raw.parts[0] == "ref" else raw.as_posix()
    checked_child(root / "ref", relative)
    return relative


def snapshot(workspace: Path) -> dict[str, str]:
    """记录源文件哈希，忽略依赖、缓存及大型构建输出。"""
    excluded = {"node_modules", ".git", ".cache", "dist", "build", "temp", "library"}
    result = {}
    for directory, dirs, files in os.walk(workspace):
        dirs[:] = [name for name in dirs if name not in excluded and not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink() and path.stat().st_size < 5_000_000:
                result[path.relative_to(workspace).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_fingerprint(workspace: Path) -> str:
    """指纹覆盖真实运行输入及测试脚本；报告、证据、依赖、构建输出不影响指纹。

    与产物快照不同，此处不设单文件大小限制，确保大型引擎与资源同样参与校验。
    """
    excluded = {"workflow", "evidence", "node_modules", ".git", ".cache", "dist", "build", "releases", "temp", "library",
                "coverage", "test-results", "playwright-report", "reports", "docs", "__pycache__"}
    entries = {}
    for directory, dirs, files in os.walk(workspace):
        for name in dirs:
            if name not in excluded and (Path(directory) / name).is_symlink():
                raise ValueError("运行输入目录不能使用未纳入指纹的符号链接")
        dirs[:] = [name for name in dirs if name not in excluded and not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() in {".md", ".log"}:
                continue
            # 内部符号链接内容也影响运行；指向工作区外的链接拒绝参与可信验证。
            resolved = path.resolve()
            if not resolved.is_relative_to(workspace.resolve()):
                raise ValueError("运行输入包含指向工作区外的文件链接")
            entries[path.relative_to(workspace).as_posix()] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

