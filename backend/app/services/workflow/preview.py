"""识别工作区里的开发构建与版本，只开放浏览器需要的静态文件。"""

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from app.services.workflow.publishing import PRIVATE_FILENAMES, STATIC_SUFFIXES, _HTMLResources
from app.services.workflow.workspace import checked_child

EXCLUDED_DIRECTORIES = {"node_modules", "workflow", "evidence", "tests", "reports", "coverage"}


def preview_file(base: Path, relative: str) -> Path:
    """预览只读静态构建，不能借入口读取凭据、隐藏文件或外部链接。"""
    raw = Path(relative)
    if (raw.is_absolute() or ".." in raw.parts or any(
            part.startswith(".") or part in EXCLUDED_DIRECTORIES for part in raw.parts)
            or raw.name.lower() in PRIVATE_FILENAMES or raw.suffix.lower() not in STATIC_SUFFIXES):
        raise ValueError("该文件不能作为游戏静态资源预览")
    cursor = base
    for part in raw.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("游戏预览不能经过符号链接")
    target = checked_child(base, relative)
    if not target.is_file():
        raise FileNotFoundError("游戏构建文件不存在")
    return target


def describe_preview(project_id: str, base: Path, entry: str) -> dict:
    """版本覆盖 JS、CSS、贴图等全部静态文件，日志变化不会触发游戏重载。

    文件至少静置一秒且 HTML 的本地资源齐全后才提供新版本；这仅表示可以
    加载开发预览，不代替正式的规则测试、浏览器验收或发布门禁。
    """
    waiting = {"status": "waiting", "url": None, "revision": None}
    try:
        index = preview_file(base, entry)
        if not index.stat().st_size:
            return {**waiting, "reason": "正在写入游戏入口"}
        records = []
        latest = 0
        for directory, names, filenames in os.walk(base, followlinks=False):
            names[:] = sorted(name for name in names if not name.startswith(".")
                              and name not in EXCLUDED_DIRECTORIES and not (Path(directory) / name).is_symlink())
            for name in sorted(filenames):
                file = Path(directory) / name
                if (file.is_symlink() or name.startswith(".") or name.lower() in PRIVATE_FILENAMES
                        or file.suffix.lower() not in STATIC_SUFFIXES):
                    continue
                stat = file.stat()
                latest = max(latest, stat.st_mtime_ns)
                records.append(f"{file.relative_to(base).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}")
                if len(records) > 10000:
                    return {**waiting, "reason": "构建文件过多，请检查输出目录"}
        if time.time_ns() - latest < 1_000_000_000:
            return {**waiting, "reason": "构建正在更新，准备好后自动加载"}
        parser = _HTMLResources()
        parser.feed(index.read_text(encoding="utf-8"))
        for reference in parser.paths:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            # 同域名根路径不是当前构建的相对路径，交给浏览器正常解析。
            if parsed.path.startswith("/"):
                continue
            preview_file(base, unquote(parsed.path))
        revision = hashlib.sha256("\n".join(records).encode()).hexdigest()[:20]
        return {"status": "ready", "url": f"/api/workflow/projects/{project_id}/preview/{quote(entry)}",
                "revision": revision, "file_count": len(records),
                "updated_at": datetime.fromtimestamp(latest / 1e9, timezone.utc).isoformat()}
    except (FileNotFoundError, ValueError, OSError, UnicodeError):
        return {**waiting, "reason": "等待完整的游戏构建，生成后自动加载"}
