"""把已确认、未变更的 Web 构建发布到独立静态路径。

调用方必须在工作流锁内排除同工作区的运行，并传入既有上游确认检查。
本模块只处理构建门禁、私有归属记录和文件发布，不创建另一套 Agent。
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from app.services.workflow.validation import verify_validation_evidence
from app.services.workflow.workspace import resolve_workspace, source_fingerprint

MAX_BUILD_BYTES = 10_000_000
STATIC_SUFFIXES = {
    ".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".json", ".webmanifest",
    ".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg", ".ico",
    ".wav", ".mp3", ".ogg", ".m4a", ".aac", ".flac", ".mp4", ".webm",
    ".woff", ".woff2", ".ttf", ".otf", ".wasm", ".bin", ".glb", ".gltf",
    ".atlas", ".skel", ".cconb", ".fnt", ".txt", ".xml",
}
PRIVATE_FILENAMES = {
    "auth.json", "credentials.json", "secrets.json", "token.json", "tokens.env",
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "id_rsa", "id_ed25519",
}
SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,62}[a-z0-9]\Z")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


class _HTMLResources(HTMLParser):
    """只收集浏览器资源标签，不把普通导航链接当成构建资源。"""

    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "img", "audio", "video", "source", "iframe"} and attributes.get("src"):
            self.paths.append(attributes["src"])
        if tag == "link" and attributes.get("href"):
            relations = set(attributes.get("rel", "").lower().split())
            if relations.intersection({"stylesheet", "icon", "preload", "modulepreload"}):
                self.paths.append(attributes["href"])


def _verify_resource_links(dist: Path, files: list[dict]) -> None:
    """检查可静态识别的网页资源引用，运行时生成的路径仍由浏览器验收负责。"""
    for entry in files:
        file = dist / entry["path"]
        suffix = file.suffix.lower()
        if suffix not in {".html", ".htm", ".js", ".mjs", ".cjs", ".css"}:
            continue
        content = file.read_text(encoding="utf-8")
        references = []
        if suffix in {".html", ".htm"}:
            parser = _HTMLResources()
            parser.feed(content)
            references = parser.paths
        elif suffix == ".css":
            references = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", content)
            references += re.findall(r"@import\s+['\"]([^'\"]+)['\"]", content)
        else:
            # 只识别带字面量路径的 import/export 与资源URL，不执行构建中的脚本。
            references = re.findall(r"\b(?:import|export)\s+[^;\n]*?\bfrom\s*['\"]([^'\"]+)['\"]", content)
            references += re.findall(r"(?:^|[;\n])\s*import\s*['\"]([^'\"]+)['\"]", content)
            references += re.findall(r"\bimport\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
            references += re.findall(r"\bnew\s+URL\(\s*['\"]([^'\"]+)['\"]\s*,\s*import\.meta\.url", content)
        for reference in references:
            reference = reference.strip()
            parsed = urlsplit(reference)
            if not reference or reference.startswith("#") or parsed.scheme in {"data", "blob"}:
                continue
            if parsed.scheme or parsed.netloc or reference.startswith("/"):
                raise ValueError(f"网页资源必须使用包内相对路径，不能依赖域名根目录或远程资源：{entry['path']}")
            relative = unquote(parsed.path)
            target = (file.parent / relative).resolve()
            if not target.is_relative_to(dist.resolve()) or not target.is_file():
                raise ValueError(f"网页资源引用越界或文件不存在：{entry['path']} → {reference}")


def build_manifest(workspace: Path) -> dict:
    """读取完整 dist 清单；校验与发布共用同一字节指纹，不只比较源码。"""
    dist = workspace / "dist"
    if dist.is_symlink() or not (dist / "index.html").is_file():
        raise ValueError("发布需要真实的 dist/index.html 构建入口")
    files = []
    total = 0
    for directory, names, filenames in os.walk(dist, followlinks=False):
        for name in [*names, *filenames]:
            item = Path(directory) / name
            if item.is_symlink() or name.startswith("."):
                raise ValueError("构建不能包含隐藏文件或符号链接")
        for name in sorted(filenames):
            item = Path(directory) / name
            if not item.is_file() or item.suffix.lower() not in STATIC_SUFFIXES or name.lower() in PRIVATE_FILENAMES:
                raise ValueError(f"构建包含不可公开的文件类型：{item.relative_to(dist)}")
            size = item.stat().st_size
            total += size
            if total > MAX_BUILD_BYTES:
                raise ValueError("网页构建展开后超过 10MB，不能发布")
            files.append({"path": item.relative_to(dist).as_posix(), "bytes": size,
                          "sha256": hashlib.sha256(item.read_bytes()).hexdigest()})
            if len(files) > 10000:
                raise ValueError("网页构建文件数量超过允许上限")
    files.sort(key=lambda entry: entry["path"])
    entry = next((item for item in files if item["path"] == "index.html"), None)
    if not entry or entry["bytes"] == 0:
        raise ValueError("网页构建入口不能是空文件")
    _verify_resource_links(dist, files)
    return {"files": files, "bytes": total, "file_count": len(files), "sha256": _digest(files)}


def _public_base_url() -> str:
    """对外域名来自服务器配置，避免浏览器请求体指定任意发布域名。"""
    value = os.getenv("GAME_PUBLIC_BASE_URL", "https://pagent.ahagamecenter.com").rstrip("/")
    parsed = urlsplit(value)
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("游戏公开地址端口无效") from error
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path or parsed.scheme not in {"http", "https"}
            or any(character.isspace() for character in value)
            or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"})):
        raise ValueError("游戏公开地址必须是 HTTPS 域名，只有本机调试允许 HTTP")
    return value


def _require_plain_directory(root: Path, directory: Path) -> None:
    """拒绝公开路径祖先上的链接，防止借静态目录覆盖其他应用。"""
    cursor = root
    for part in directory.relative_to(root).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("静态发布目录不能经过符号链接")
        if cursor.exists() and not cursor.is_dir():
            raise ValueError("静态发布路径已被文件占用")


def _verify_ready(project: dict, test_run: dict, workspace: Path,
                  verify_dependencies: Callable[[dict, str], None]) -> dict:
    """先验证阶段交接，再同时验证当前源码与真正测试过的构建文件。"""
    stages = {stage["id"]: stage for stage in project.get("stages", [])}
    if any(stages.get(name, {}).get("status") != "completed" or not stages.get(name, {}).get("confirmed_at")
           for name in ("prototype", "art", "code", "test")):
        raise ValueError("必须先确认全部四个阶段，才能发布游戏")
    if (test_run.get("stage") != "test" or test_run.get("status") != "completed"
            or test_run.get("project_id") != project.get("id")
            or stages["test"].get("run_id") != test_run.get("id")):
        raise ValueError("只能发布本项目当前已确认的测试运行")
    verify_dependencies(project, "test")
    verify_validation_evidence(test_run, workspace)
    report = next((item for item in test_run.get("artifacts", []) if item.get("path") == "workflow/test.md"), None)
    report_file = workspace / "workflow" / "test.md"
    if (not report or not report_file.is_file() or report_file.is_symlink()
            or hashlib.sha256(report_file.read_bytes()).hexdigest() != report.get("sha256")):
        raise ValueError("测试报告已变化或缺少已确认快照，请重新验收")
    manifest = build_manifest(workspace)
    checks = [item["data"] for item in test_run.get("events", [])
              if item.get("type") == "validation_completed"
              and item.get("data", {}).get("command") == "npm run check"
              and item["data"].get("attempt") == test_run.get("attempt", 1)]
    if (not checks or checks[-1].get("exit_code") != 0
            or checks[-1].get("build_sha256") != manifest["sha256"]):
        raise ValueError("当前网页构建缺少相同字节版本的浏览器验收，请重新执行测试阶段")
    return manifest


def publish_game(root: Path, workspace: Path, project: dict, test_run: dict, slug: str,
                 *, verify_dependencies: Callable[[dict, str], None]) -> dict:
    """发布一个经确认的项目；调用方负责互斥、记录返回值和发布事件。"""
    if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("发布路径须为 3 至 64 位小写字母、数字或连字符，首尾不能是连字符")
    root = root.resolve()
    workspace = workspace.resolve()
    if workspace != resolve_workspace(root, project["workspace"]):
        raise ValueError("发布工作区与项目登记路径不一致")
    manifest = _verify_ready(project, test_run, workspace, verify_dependencies)
    source_hash = source_fingerprint(workspace)
    public_url = f"{_public_base_url()}/games/{slug}/index.html"
    public_root = root / "frontend" / "public" / "games"
    target = public_root / slug
    private_root = root / "backend" / "data" / "workflow" / "publications"
    owner_file = private_root / f"{slug}.json"
    _require_plain_directory(root, target)
    _require_plain_directory(root, private_root)
    if owner_file.is_symlink():
        raise ValueError("发布归属记录不能使用符号链接")
    previous = json.loads(owner_file.read_text(encoding="utf-8")) if owner_file.exists() else None
    if previous and previous.get("project_id") != project["id"]:
        raise ValueError("该发布路径已属于其他项目，请选择新的路径")
    if target.exists() and previous is None:
        raise ValueError("该发布路径已有非本工作流发布的内容，不能覆盖")
    public_root.mkdir(parents=True, exist_ok=True)
    private_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{slug}-", dir=public_root))
    record_tmp = private_root / f".{slug}-{uuid4().hex}.tmp"
    backup = private_root / "backups" / f"{slug}-{uuid4().hex}"
    published = False
    backed_up = False
    try:
        # 复制后逐文件对照已验证哈希，防止验证与复制之间原文件被外部修改。
        for entry in manifest["files"]:
            destination = staging / entry["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(workspace / "dist" / entry["path"], destination)
            if hashlib.sha256(destination.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("构建文件在发布期间改变，请重新验收")
        if source_fingerprint(workspace) != source_hash or build_manifest(workspace)["sha256"] != manifest["sha256"]:
            raise ValueError("项目在发布期间改变，请重新验收")
        publication = {"project_id": project["id"], "run_id": test_run["id"], "slug": slug,
                       "url": public_url, "bytes": manifest["bytes"], "file_count": manifest["file_count"],
                       "sha256": manifest["sha256"], "source_fingerprint": source_hash,
                       "published_at": datetime.now(timezone.utc).isoformat(), "files": manifest["files"]}
        record_tmp.write_text(json.dumps(publication, ensure_ascii=False, indent=2), encoding="utf-8")
        if target.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            target.rename(backup)
            backed_up = True
        staging.rename(target)
        published = True
        record_tmp.replace(owner_file)
        return publication
    except Exception:
        # 公开目录和私有归属记录作为一个发布结果处理；记录失败时恢复旧目录。
        if published:
            shutil.rmtree(target)
        if backed_up:
            backup.rename(target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        record_tmp.unlink(missing_ok=True)
