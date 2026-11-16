"""只读展示公司小游戏参考资料，不解压、执行或下载第三方游戏。

实际目录与 gameInfo 决定可见游戏和本地文件状态。CSV 只补充介绍文案，
历史 Windows 路径、采集成功字段和远程链接都不能证明当前原包存在。
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from pathlib import Path

REFERENCE_GAMES_ROOT = Path(__file__).resolve().parents[3] / "ref" / "公司skill整合" / "AHAgames"
REFERENCE_PREFIX = "公司skill整合/AHAgames"
ASSET_ROLES = {"icon", "banner", "hotgame", "theme", "preview"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


def _root(root: Path | None = None) -> Path:
    """拒绝固定来源自身或任何祖先是符号链接，避免绕过只读来源边界。"""
    root = Path(REFERENCE_GAMES_ROOT if root is None else root).absolute()
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("游戏参考资料目录不能使用符号链接")
    return root


def _child(root: Path, relative: str) -> Path:
    """所有来源文件逐段验证；下载接口不接受任意文件路径。"""
    parts = relative.split("/")
    if any(not part or part.startswith(".") or "\\" in part or "\x00" in part for part in parts):
        raise ValueError("参考资料路径无效")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("参考资料文件不能使用符号链接")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("参考资料路径超出允许目录")
    return current


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _identifier(info: dict, directory: Path) -> str:
    """优先使用稳定 gameId；元数据没有标识时才使用安全目录名。"""
    raw = info.get("gameId")
    identifier = str(raw) if isinstance(raw, (int, str)) and not isinstance(raw, bool) else ""
    if IDENTIFIER.fullmatch(identifier):
        return identifier
    if IDENTIFIER.fullmatch(directory.name):
        return directory.name
    return "folder-" + hashlib.sha256(directory.name.encode("utf-8")).hexdigest()[:20]


def _discover_games(root: Path) -> tuple[list[tuple[str, Path, dict]], list[str]]:
    """仅发现实际存在的元数据；坏文件被列为问题，不阻断其它参考资料。"""
    games, warnings = [], []
    if not root.is_dir():
        return games, ["本地公司游戏参考资料目录尚不存在"]
    for directory in sorted(root.iterdir()):
        if directory.is_symlink() or not directory.is_dir() or directory.name.startswith("."):
            continue
        try:
            metadata = _child(root, directory.name + "/gameInfo.json")
            if not metadata.is_file():
                continue
            if metadata.stat().st_size > 1024 * 1024:
                raise ValueError("元数据文件过大")
            info = json.loads(metadata.read_text(encoding="utf-8-sig"))
            if not isinstance(info, dict):
                raise ValueError("元数据应为对象")
            games.append((_identifier(info, directory), directory, info))
        except (ValueError, OSError) as error:
            warnings.append(f"未加载 {directory.name}：{error}")
    # 重复标识不能随目录遍历顺序指向不同游戏；从可服务集合移除并明确记录。
    duplicates = {identifier for identifier, _, _ in games if sum(row[0] == identifier for row in games) > 1}
    if duplicates:
        warnings.append("重复的游戏标识未对外提供：" + "、".join(sorted(duplicates)))
        games = [row for row in games if row[0] not in duplicates]
    return games, warnings


def _csv_rows(root: Path, filename: str) -> list[dict]:
    path = _child(root, filename)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _assets(root: Path, identifier: str, directory: Path) -> list[dict]:
    """只暴露五类实际商店图片，动态图由界面按需加载。"""
    try:
        art = _child(root, directory.name + "/art")
    except ValueError:
        return []
    if not art.is_dir():
        return []
    assets = []
    for path in sorted(art.iterdir()):
        if (path.is_symlink() or not path.is_file() or path.stem not in ASSET_ROLES
                or path.suffix.lower() not in ASSET_SUFFIXES):
            continue
        assets.append({"name": path.name, "role": path.stem, "bytes": path.stat().st_size,
                       "url": f"/api/workflow/reference-games/{identifier}/assets/{path.name}"})
    return assets


def _item(root: Path, identifier: str, directory: Path, info: dict, art_info: dict) -> dict:
    """包体状态以实际同目录 ZIP 为准，不解析历史 localFile 的绝对路径。"""
    packages = [{"name": path.name, "bytes": path.stat().st_size}
                for path in sorted(directory.iterdir())
                if not path.is_symlink() and path.is_file() and path.suffix.lower() == ".zip"]
    assets = _assets(root, identifier, directory)
    name = _text(info.get("apiName")) or _text(art_info.get("name")) or directory.name
    return {
        "id": identifier, "name": name, "category": _text(info.get("category")) or "未分类",
        "description": _text(art_info.get("description")), "introduction": _text(art_info.get("introduction")),
        "source": _text(info.get("source")), "match": _text(info.get("match")),
        "directory": directory.name,
        "reference_path": f"{REFERENCE_PREFIX}/{directory.name}/gameInfo.json",
        "directory_reference_path": f"{REFERENCE_PREFIX}/{directory.name}",
        "package_status": "present" if packages else "missing",
        "package": packages[0] if packages else None, "package_files": packages,
        "package_note": "本地文件存在，当前接口未验证完整性" if packages else "当前资料目录未提供本地原包",
        "assets": assets, "icon_url": next((item["url"] for item in assets if item["role"] == "icon"), ""),
    }


def _research_summary(root: Path, name: str, *, prefix: str = REFERENCE_PREFIX) -> dict:
    """清点附带研究目录，只给小型 Markdown 文档建立阅读入口。"""
    directory = _child(root, name)
    count, size = 0, 0
    documents = []
    if directory.is_dir():
        for base, directories, files in os.walk(directory, followlinks=False):
            directories[:] = sorted(item for item in directories if not item.startswith(".")
                                    and item not in {"node_modules", "__pycache__"} and not (Path(base) / item).is_symlink())
            for filename in sorted(files):
                path = Path(base) / filename
                if not filename.startswith(".") and not path.is_symlink() and path.is_file():
                    count += 1
                    size += path.stat().st_size
                    if path.suffix.lower() == ".md" and path.stat().st_size <= MAX_DOCUMENT_BYTES:
                        documents.append({"name": path.stem, "reference_path": f"{prefix}/{path.relative_to(root).as_posix()}",
                                          "bytes": path.stat().st_size})
    return {"name": name, "reference_path": f"{prefix}/{name}", "file_count": count, "bytes": size,
            "documents": documents}


def _research_sources(root: Path) -> tuple[list[dict], list[str]]:
    """案例工程与 Skill 分开索引；不把整套源码、截图和历史结果导入技能上下文。"""
    sources, warnings = [], []
    company_root = _root(root.parent)
    for base, name, prefix in [(root, "reskin_review", REFERENCE_PREFIX),
                                (root, "art_direction", REFERENCE_PREFIX),
                                (company_root, "OneConnectRe", "公司skill整合")]:
        try:
            if _child(base, name).is_dir():
                sources.append(_research_summary(base, name, prefix=prefix))
        except (ValueError, OSError) as error:
            warnings.append(f"未统计 {name}：{error}")
    return sources, warnings


def read_research_document(reference_path: str) -> dict:
    """只读当前研究索引中的 Markdown，以 JSON 文本返回，不执行 HTML 或源码。"""
    root = _root()
    sources, _ = _research_sources(root)
    document = next((item for source in sources for item in source["documents"]
                     if item["reference_path"] == reference_path), None)
    if document is None:
        raise FileNotFoundError("研究文档不存在或不在可读目录中")
    path = _child(_root(root.parent), reference_path.removeprefix("公司skill整合/"))
    with path.open("rb") as source:
        content = source.read(MAX_DOCUMENT_BYTES + 1)
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError("研究文档超过 2 MB")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeError as error:
        raise ValueError("研究文档必须是 UTF-8 文本") from error
    return {**document, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(), "content": text}


def list_reference_games(*, root: Path | None = None, include_research: bool = True) -> dict:
    """读取本地参考清单，分别报告当前磁盘状态和历史清单的一致性。"""
    root = _root(root)
    games, warnings = _discover_games(root)
    art_rows, csv_rows, json_count = [], [], None
    if root.is_dir():
        for filename in ("art_manifest.csv", "manifest.csv"):
            try:
                rows = _csv_rows(root, filename)
                if filename == "art_manifest.csv":
                    art_rows = rows
                else:
                    csv_rows = rows
            except (ValueError, OSError, csv.Error) as error:
                warnings.append(f"未读取 {filename}：{error}")
        try:
            path = _child(root, "manifest.json")
            if path.is_file():
                records = json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(records, list):
                    raise ValueError("清单应为数组")
                json_count = len(records)
        except (ValueError, OSError) as error:
            warnings.append(f"未读取 manifest.json：{error}")
    art_by_id = {str(row.get("id", "")): row for row in art_rows}
    items = [_item(root, identifier, directory, info, art_by_id.get(identifier, {})) for identifier, directory, info in games]
    if json_count is not None and json_count != len(csv_rows):
        warnings.append(f"历史清单数量不一致：manifest.json 为 {json_count} 条，manifest.csv 为 {len(csv_rows)} 条；游戏列表按实际 gameInfo 生成")
    present = sum(item["package_status"] == "present" for item in items)
    research = []
    if include_research:
        research, research_warnings = _research_sources(root)
        warnings.extend(research_warnings)
    return {"items": items, "total": len(items), "summary": {
        "reference_path": REFERENCE_PREFIX, "local_package_games": present, "missing_package_games": len(items) - present,
        "package_file_count": sum(len(item["package_files"]) for item in items),
        "package_bytes": sum(file["bytes"] for item in items for file in item["package_files"]),
        "art_file_count": sum(len(item["assets"]) for item in items),
        "categories": sorted({item["category"] for item in items}),
        "manifest_json_records": json_count, "manifest_csv_records": len(csv_rows),
        "art_manifest_records": len(art_rows), "warnings": warnings, "research": research,
        "note": "仅供竞品与美术研究；历史采集状态不代表本地包体存在，资料收录不等于商业授权或已完成逆向分析",
    }}


def get_reference_game(identifier: str) -> dict:
    """返回单个实际游戏资料；未知标识或重复标识均不能指向任意目录。"""
    if not IDENTIFIER.fullmatch(identifier):
        raise ValueError("游戏参考标识无效")
    root = _root()
    games, _ = _discover_games(root)
    game = next((item for item in games if item[0] == identifier), None)
    if game is None:
        raise FileNotFoundError("游戏参考资料不存在")
    # 单条读取不重复遍历研究目录；缺失的文案清单不影响图片与元数据访问。
    try:
        rows = _csv_rows(root, "art_manifest.csv")
    except (ValueError, OSError, csv.Error):
        rows = []
    art_info = next((row for row in rows if str(row.get("id", "")) == identifier), {})
    return _item(root, *game, art_info)


def reference_game_asset(identifier: str, asset_name: str) -> Path:
    """下载只限已列出的本地商店图片；不开放 HTML、脚本、原包或通用文件读取。"""
    if "/" in asset_name or "\\" in asset_name or "\x00" in asset_name:
        raise ValueError("商店图片名称无效")
    game = get_reference_game(identifier)
    if asset_name not in {item["name"] for item in game["assets"]}:
        raise FileNotFoundError("商店图片不存在或不在允许列表中")
    path = _child(_root(), f"{game['directory']}/art/{asset_name}")
    if not path.is_file():
        raise FileNotFoundError("商店图片已不存在")
    return path
