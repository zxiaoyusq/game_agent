"""从实际 Web 产物生成游戏目录，工作流记录只补充名称和分类。"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from app.config import DATA_DIR

ROOT = Path(__file__).resolve().parents[3]
PROJECTS_DIR = DATA_DIR / "workflow" / "projects"
IDENTIFIER = re.compile(r"[a-zA-Z0-9_-]{1,100}\Z")
# 运行接口只暴露构建资源，不把工程、密钥或源码包作为公开文件。
WEB_SUFFIXES = {".html", ".htm", ".js", ".mjs", ".css", ".json", ".wasm", ".bin",
                ".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg", ".ico",
                ".mp3", ".ogg", ".wav", ".m4a", ".aac", ".mp4", ".webm",
                ".woff", ".woff2", ".ttf", ".otf", ".atlas", ".skel", ".cconb", ".fnt",
                ".glb", ".gltf", ".webmanifest", ".manifest", ".xml", ".txt", ".ccm", ".plist"}
PRIVATE_NAMES = {"package.json", "package-lock.json", "auth.json", "credentials.json", "secrets.json", "token.json"}
COVER_PATHS = ("evidence/desktop-lobby.jpg", "evidence/screenshots/B01-menu.png",
               "evidence/classic-desktop.png", "evidence/mobile.png")


def _child(root: Path, relative: str) -> Path:
    """逐级拒绝隐藏路径、穿越和链接，文件入口始终限制在指定目录。"""
    parts = relative.split("/")
    if any(not part or part.startswith(".") or "\\" in part or "\x00" in part for part in parts):
        raise ValueError("游戏资源路径无效")
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("游戏目录不能使用符号链接")
    path = root
    for part in parts:
        path /= part
        if path.is_symlink():
            raise ValueError("游戏资源不能使用符号链接")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("游戏资源超出允许目录")
    return path


def _locations(identifier: str) -> tuple[Path, Path]:
    """优先提供已分发版本，其次提供工作区构建；仅有策划或源码不算可运行。"""
    if not IDENTIFIER.fullmatch(identifier):
        raise ValueError("游戏标识无效")
    workspace = _child(ROOT, f"games/{identifier}")
    for relative in (f"frontend/public/games/{identifier}", f"games/{identifier}/dist"):
        base = _child(ROOT, relative)
        if _child(base, "index.html").is_file():
            return workspace, base
    raise FileNotFoundError("该游戏尚无可运行的 Web 产物")


class _PageMetadata(HTMLParser):
    """从入口读取展示信息，不执行游戏脚本。"""

    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""
        self.description = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            attrs = dict(attrs)
            if attrs.get("name") == "description":
                self.description = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def _project_metadata() -> dict:
    """损坏或尚在创建的记录不会影响已存在游戏；同工作区仅展示一个条目。"""
    projects = {}
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        if path.is_symlink():
            continue
        try:
            project = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(project, dict) and isinstance(project.get("workspace"), str):
                previous = projects.get(project["workspace"], {})
                if str(project.get("created_at", "")) >= str(previous.get("created_at", "")):
                    projects[project["workspace"]] = project
        except (OSError, ValueError):
            continue
    return projects


def _import_metadata(identifier: str) -> dict:
    """导入游戏可补充展示信息；运行地址仍由真实构建决定，不信任清单中的 URL。"""
    try:
        path = _child(ROOT, f"games/{identifier}/game.json")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return {}
        metadata = {key: value[key].strip() for key in ("name", "description", "category", "unavailable_reason")
                    if isinstance(value.get(key), str) and value[key].strip()}
        # 显式的展示顺序用于置顶游戏，旧清单与无效值继续使用默认顺序。
        if type(value.get("sort_order")) is int:
            metadata["sort_order"] = value["sort_order"]
        return metadata
    except (OSError, ValueError):
        return {}


def cover_file(identifier: str) -> Path:
    """仅允许预定义的自产验收截图作为封面，不能读取任意工程文件。"""
    workspace, _ = _locations(identifier)
    for relative in COVER_PATHS:
        path = _child(workspace, relative)
        if path.is_file():
            return path
    raise FileNotFoundError("该游戏暂无封面")


def _pending_deletions() -> dict:
    """保留清理失败的入口，刷新页面后仍可重试，且不会误启动残缺的运行包。"""
    directory = _child(PROJECTS_DIR.parent, "deletions")
    pending = {}
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink() or not IDENTIFIER.fullmatch(path.stem):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                continue
            aliases = record.get("aliases", [])
            if not isinstance(aliases, list):
                aliases = []
            # 项目清理的日志标识不是游戏标识，仅在作品库保留实际游戏入口供重试。
            catalog_ids = aliases if record.get("kind") == "project" else [path.stem, *aliases]
            for identifier in catalog_ids:
                if isinstance(identifier, str) and IDENTIFIER.fullmatch(identifier):
                    pending[identifier] = {"id": catalog_ids[0], "name": record.get("name")}
        except (OSError, ValueError):
            continue
    return pending


def list_games() -> dict:
    """合并工作区和已分发目录，去重并实时发现新增构建，不混入公司竞品包。"""
    identifiers = set()
    for relative in ("games", "frontend/public/games"):
        directory = _child(ROOT, relative)
        if directory.is_dir():
            identifiers.update(path.name for path in directory.iterdir()
                               if path.is_dir() and not path.is_symlink() and IDENTIFIER.fullmatch(path.name))
    projects = _project_metadata()
    pending = _pending_deletions()
    identifiers.update(record["id"] for record in pending.values())
    items = []
    for identifier in sorted(identifiers):
        try:
            imported = _import_metadata(identifier)
            if identifier in pending:
                base = None
            else:
                try:
                    _, base = _locations(identifier)
                except FileNotFoundError:
                    # 显式导入但包体不完整的游戏保留说明，不把广告测试页当成游戏运行。
                    if not imported.get("name"):
                        continue
                    base = None
            metadata = _PageMetadata()
            if base:
                metadata.feed((base / "index.html").read_text(encoding="utf-8", errors="replace"))
            project = projects.get(f"games/{identifier}", {})
            profile = project.get("production_profile")
            profile = profile if isinstance(profile, dict) else {}
            genre = profile.get("genre")
            genre = genre if isinstance(genre, dict) else {}
            name = pending.get(identifier, {}).get("name") or imported.get("name") or project.get("name")
            name = name if isinstance(name, str) and name.strip() else metadata.title.strip() or identifier
            try:
                cover_file(identifier)
                cover_url = f"/api/produced-games/{identifier}/cover"
            except (FileNotFoundError, ValueError):
                cover_url = None
            items.append({
                "id": identifier, "name": name,
                "description": imported.get("description") or metadata.description or "选择游戏，开启一段新的游玩体验。",
                "category": imported.get("category") or genre.get("label") or "休闲游戏",
                "sort_order": imported.get("sort_order", 0),
                "available": base is not None,
                "deletion_pending": identifier in pending,
                "unavailable_reason": "删除尚未完成，请点击删除按钮继续清理剩余产出。" if identifier in pending
                else None if base else imported.get("unavailable_reason", "尚未提供完整的 H5 运行包。"),
                "play_url": f"/api/produced-games/{identifier}/play/index.html" if base else None,
                "cover_url": cover_url,
            })
        except (OSError, ValueError):
            # 无构建的需求项目或不安全目录不占用游戏名额，其余成品照常可用。
            continue
    items.sort(key=lambda item: (item["sort_order"], item["id"]))
    return {"items": items, "total": len(items), "playable": sum(item["available"] for item in items)}


def game_file(identifier: str, relative: str) -> Path:
    """从该游戏的运行包读取相对资源，禁止回退到工程根目录。"""
    _, base = _locations(identifier)
    path = _child(base, relative)
    if path.suffix.lower() not in WEB_SUFFIXES or path.name.lower() in PRIVATE_NAMES or not path.is_file():
        raise FileNotFoundError("游戏运行资源不存在")
    return path
