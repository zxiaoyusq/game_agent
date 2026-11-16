"""把工程与公司 Skill 包作为只读来源导入知识库，不加载或执行包内工具。"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import hashlib
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml

from app.services import knowledge

logger = logging.getLogger(__name__)
SYNC_LOCK = threading.RLock()

# 展示文案独立于源文件，导入时保留原目录名和原文，便于追溯来源。
SKILL_DESCRIPTIONS = {
    "apk-engineering-analysis": ("APK 工程拆解与资源分析", "分析 Android 安装包的引擎、代码、资源与配置，整理工程报告和离线资源浏览器。"),
    "game-competitor-analysis": ("游戏竞品拆解与融合设计", "研究游戏玩法、关卡、美术、成长、商业化与玩家反馈，形成有来源的竞品报告和原创设计建议。"),
    "ai-art-automation": ("AI 美术自动化", "从需求、策划和工程中拆分美术任务，组织生成、后处理、合入工程与验收。"),
    "azure-image2-generation": ("AI 生图与素材换皮", "提供生图、改图、真透明素材、批量换皮、结构锁定与图集处理流程，附提示词模板和脚本。"),
    "spine-animation-pipeline": ("Spine 动画制作流水线", "覆盖角色拆件、定位、绑骨、动画、图集导出、版本兼容与质量检查。"),
    "spine-imagegen-animation": ("ImageGen 角色与 Spine 动画", "配合图像生成制作角色部件，组织定位、骨骼、待机动画与 Spine 导出。"),
    "gpt52-vision-router": ("GPT-5.2 外部视觉路由", "为特定模型配置提供外部识图与视觉质检流程，附 MCP 服务和接入说明。"),
    "game-reverse-engineering": ("游戏逆向与二次开发总集", "从引擎识别、资源提取与玩法分析，到工程恢复、换皮、SDK 替换、Godot 迁移和设备验收，统筹各专项子模块。"),
    "casual-game-art-style": ("休闲游戏美术风格与视觉规范", "组织休闲游戏美术风格、色彩层级、区域配色、界面控件及竞品视觉证据。"),
    "cocos-project-standards": ("Cocos 项目工程规范", "约定 Cocos 工程边界、逻辑层、数据与配置、资源迁移、Prefab 和交付检查。"),
    "h5-canvas-reskin": ("H5 Canvas 游戏换皮", "从市场与风格方向、设计评审到素材生产、合入和运行验收，保留原有资源契约与修改范围。"),
    "hosted-minigame-harvest": ("托管小游戏采集与持续迭代", "从采集、原版还原到关卡、美术和宿主接口迭代，并按证据优化 H5 包体、加载与内存。"),
    "3d-asset-extraction": ("3D 模型与贴图提取", "整理 PC 游戏离线模型、贴图提取、未知容器分析、Blender 导入和资产验收流程。"),
    "engine-identification": ("游戏构建引擎识别", "识别 Cocos、Unity IL2CPP 等引擎指纹，为未知游戏构建选择后续分析路线。"),
    "cocos-reverse-engineering": ("Cocos 逆向与工程恢复", "覆盖 Cocos 构建解包、脚本解密、资源提取、JSB 运行时检查与工程恢复。"),
    "cocos-creator-repair": ("Cocos Creator 工程修复", "诊断项目打不开、黑屏、场景引用损坏和组件序列化错误等问题。"),
    "cocos-qa": ("Cocos 构建与交付验收", "整理构建、打包、设备实测、截图与日志验收，以及关卡图片和文案映射检查。"),
    "cocos-mcp-channel": ("Cocos 编辑器 MCP 通道", "说明 Cocos Creator 编辑器的 MCP 配置、UI 编辑、引用检查和实时操作流程。"),
    "godot-migration-port": ("Godot 迁移与游戏重建", "将已提取的工程和美术资源迁移为可运行、可编译、可二次开发的 Godot 游戏工程。"),
    "gameplay-logic-reverse": ("玩法算法与机制逆向", "分析出块策略、玩家分层、难度、机制开关、远程配置和运行时生命周期。"),
    "dragonbones-spine-convert": ("DragonBones 转 Spine", "转换 DragonBones 骨骼、图集与贴图，并检查 Spine 编辑器和运行时兼容性。"),
    "skinning-pipeline": ("游戏美术换皮流水线", "围绕资源清单、图集重建、替换映射、回滚和差异校验组织换皮工作。"),
    "unity-extract": ("Unity 美术资源提取", "提取或恢复 Unity 贴图、模型、动画、音频、场景、Prefab 与配置，并整理换皮资源。"),
    "deliverable-book-template": ("逆向拆解交付与报告模板", "将拆解证据组织为系列文档和交互式 HTML 设计解析全书。"),
    "prefab-bake": ("Prefab 烘焙与编辑器固化", "把运行时 UI 和换肤改动固化为可编辑的 Prefab，验证编辑器与运行结果一致。"),
    "ui-feature-pipeline": ("新功能 UI 开发流水线", "串联 UI 需求、效果图、控件切分、Prefab 重组、视觉验收与固化交付。"),
    "vision-device-testing": ("Android 真机视觉验收", "使用设备截图、OCR、图像基线、UI 结构和日志证据组织可重复的视觉测试。"),
    "sdk-replacement": ("SDK 替换与联网改造", "整理原厂联网隔离、内容本地化、广告与埋点替换、替代 SDK 接入及验收流程。"),
}

FOLDER_DESCRIPTIONS = {
    "references": "参考文档、流程说明与实践经验",
    "scripts": "配套脚本与工具源码",
    "assets": "模板、样例、配置和资源文件",
    "tests": "测试脚本与验证样例",
    "agents": "技能展示与调用配置",
    "modules": "技能专项子模块",
    "mcp": "MCP 服务源码与接入说明",
}

LEGACY_REVERSE_SUMMARY = "从引擎识别、资源提取与玩法分析，到工程恢复、换皮、SDK 替换、Godot 迁移和设备验收，统筹 16 个子模块。"
# 只迁移已发布过的自动文案；自定义标题、摘要和文件夹说明不随来源覆盖。
LEGACY_SKILL_DESCRIPTIONS = {
    "h5-canvas-reskin": ("H5 Canvas 游戏换皮", "检查 Canvas 运行时、资源替换和组件还原，按实际视觉差异与交互结果验收换皮。"),
    "hosted-minigame-harvest": ("托管小游戏资料采集", "整理托管小游戏目录、元信息和素材采集流程，核对数据接口、来源与交付清单。"),
}


def _excluded_source(path: Path) -> bool:
    """隐藏配置、版本控制和缓存不是技能资料，避免进入界面和复制清单。"""
    return any(part.startswith(".") or part in {"__pycache__", "node_modules"} for part in path.parts)


def _checked_path(root: Path, relative: Path) -> Path:
    """校验每级真实路径，读取和写入均拒绝链接、穿越及非目录父节点。"""
    if relative.is_absolute() or not relative.parts or any(part in {".", ".."} or "\\" in part for part in relative.parts):
        raise ValueError("同步路径必须是根目录内的普通相对路径")
    # 根目录的上级也必须检查；先 resolve 会掩盖父级链接并改变实际写入边界。
    for parent in [root.absolute(), *root.absolute().parents]:
        if parent.is_symlink():
            raise ValueError("同步资料根目录及其父级不能使用符号链接")
        if parent.exists() and not parent.is_dir():
            raise ValueError("同步资料根目录及其父级必须是目录")
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        if current.is_symlink():
            raise ValueError("同步资料不能使用符号链接")
        if index < len(relative.parts) - 1 and current.exists() and not current.is_dir():
            raise ValueError("同步路径的父节点不是目录")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("同步路径超出资料根目录")
    return current


def _read_import_state(base: Path) -> dict:
    """只读旧清单，兼容仅保存 paths 的历史版本，不在查询时创建目录。"""
    path = _checked_path(base, Path(".skill-import.json"))
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(state, dict) or not isinstance(state.get("paths", []), list):
        raise ValueError("技能导入清单格式错误")
    return state


def _was_deleted(relative: Path, imported_paths: set[str], base: Path) -> bool:
    """此前导入后消失的文件或父目录视为用户删除，不借新增文件恢复目录。"""
    return any(path.as_posix() in imported_paths and not (base / path).exists()
               for path in [relative, *relative.parents] if path != Path("."))


def _source_entries(project_root: Path) -> list[tuple[Path, Path, str]]:
    """枚举两处来源中的完整技能包及公司附带资料。"""
    entries = []
    for source_dir, source_label in (
        (project_root / "skills", "工程已有"),
        (project_root / "ref" / "公司skill整合", "公司整合"),
    ):
        _checked_path(project_root, source_dir.relative_to(project_root))
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.iterdir()):
            if source.is_symlink() or _excluded_source(Path(source.name)):
                continue
            if source.is_dir() and (source / "SKILL.md").is_file() and not (source / "SKILL.md").is_symlink():
                # 工程技能是显式维护的本地版本，公司同名来源不能混入它的目录。
                if source_label == "公司整合" and (project_root / "skills" / source.name).exists():
                    logger.warning("公司技能与工程技能同名，保留工程版本：%s", source.name)
                    continue
                entries.append((source, Path(source.name), source_label))
            elif source.is_file() and source_label == "公司整合":
                entries.append((source, Path("公司资料") / source.name, source_label))
    return entries


def _skill_metadata(path: Path, base: Path) -> tuple[str, str]:
    """读取新增包展示文案，展示配置也遵守知识库路径边界，不跟随链接。"""
    path = _checked_path(base, path.relative_to(base))
    metadata = {}
    content = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    if content.startswith("---"):
        try:
            loaded = yaml.safe_load(content.split("---", 2)[1])
            metadata = loaded if isinstance(loaded, dict) else {}
        except (yaml.YAMLError, IndexError):
            pass
    interface = {}
    config = path.parent / "agents" / "openai.yaml"
    try:
        config = _checked_path(base, config.relative_to(base))
        if config.is_file():
            loaded = yaml.safe_load(config.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("interface"), dict):
                interface = loaded["interface"]
    except (yaml.YAMLError, ValueError):
        # 展示配置是可选资料；无效配置及链接不能影响原始 Skill 元数据。
        pass
    extra = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
    title = extra.get("display_name") or interface.get("display_name") or metadata.get("name") or path.parent.name
    summary = metadata.get("description") or interface.get("short_description") or "技能使用说明。"
    return str(title), str(summary)


def _item_metadata(relative: Path, source_label: str, base: Path) -> tuple[str, list[str], str]:
    """区分技能入口、嵌套子模块和配套文件，避免所有入口同名。"""
    package = relative.parts[0]
    package_title, package_summary = SKILL_DESCRIPTIONS.get(package) or _skill_metadata(base / package / "SKILL.md", base)
    if relative.name == "SKILL.md":
        title, summary = SKILL_DESCRIPTIONS.get(relative.parent.name) or _skill_metadata(base / relative, base)
        kind = "主入口" if len(relative.parts) == 2 else "子模块"
        return title, [source_label, kind, package_title], summary
    if package == "公司资料":
        title = "公司技能整合说明" if relative.name == "README.md" else relative.stem
        return title, [source_label, "附带资料"], package_summary
    return relative.stem, [source_label, "配套资料", package_title], f"{package_title}的配套文件：{relative.as_posix()}"


def _refresh_metadata(base: Path, existing: dict, file_sources: dict[str, str], *, update_generated: bool = False) -> dict[str, int]:
    """仅补新条目文案；显式同步可替换旧自动文案，用户自定义字段保持原值。"""
    existing_item_keys = {(item.get("folder", ""), item.get("stored_name", "")) for item in existing["items"]}
    existing_folder_paths = {folder["path"] for folder in existing["folders"]}
    knowledge._sync_cache.pop(("skill", "docs"), None)
    items = knowledge._read_index("skill", "docs")
    folders = knowledge._read_folders("skill", "docs")
    for item in items:
        relative = Path(item.folder) / item.stored_name
        source_label = file_sources.get(relative.as_posix())
        if (item.folder, item.stored_name) not in existing_item_keys and source_label:
            item.title, item.tags, item.summary = _item_metadata(relative, source_label, base)
        elif update_generated and relative == Path("game-reverse-engineering/SKILL.md") and item.summary == LEGACY_REVERSE_SUMMARY:
            item.summary = SKILL_DESCRIPTIONS["game-reverse-engineering"][1]
        elif update_generated and relative.name == "SKILL.md" and relative.parent.name in LEGACY_SKILL_DESCRIPTIONS:
            old_title, old_summary = LEGACY_SKILL_DESCRIPTIONS[relative.parent.name]
            title, summary = SKILL_DESCRIPTIONS[relative.parent.name]
            if item.title == old_title:
                item.title = title
            if item.summary == old_summary:
                item.summary = summary
    for folder in folders:
        leaf = Path(folder.path).name
        if folder.path in existing_folder_paths:
            if update_generated and leaf in LEGACY_SKILL_DESCRIPTIONS:
                old_title, old_summary = LEGACY_SKILL_DESCRIPTIONS[leaf]
                if folder.desc == f"{old_title}：{old_summary}":
                    title, summary = SKILL_DESCRIPTIONS[leaf]
                    folder.desc = f"{title}：{summary}"
            if update_generated and folder.path == "game-reverse-engineering" and folder.desc == f"游戏逆向与二次开发总集：{LEGACY_REVERSE_SUMMARY}":
                folder.desc = "游戏逆向与二次开发总集：" + SKILL_DESCRIPTIONS["game-reverse-engineering"][1]
            elif update_generated and leaf == "modules" and folder.desc == "游戏逆向与二次开发的 16 个专项子模块":
                folder.desc = FOLDER_DESCRIPTIONS["modules"]
            continue
        if leaf in SKILL_DESCRIPTIONS:
            title, summary = SKILL_DESCRIPTIONS[leaf]
            folder.desc = f"{title}：{summary}"
        elif leaf == "公司资料":
            folder.desc = "公司技能整合说明与 BlockBlast 专项脚本、文档压缩包。"
        elif (base / folder.path / "SKILL.md").is_file():
            title, summary = _skill_metadata(base / folder.path / "SKILL.md", base)
            folder.desc = f"{title}：{summary}"
        else:
            folder.desc = FOLDER_DESCRIPTIONS.get(leaf, "技能包配套资料目录")
    knowledge._write_index("skill", "docs", items, folders)
    return {"skill_entries": sum(item.filename == "SKILL.md" for item in items), "files": len(items)}


def import_skill_library(
    project_root: Path | None = None,
    *,
    restore_deleted: bool = False,
) -> dict[str, int]:
    """串行补导新资料；显式来源同步与工程技能发布使用同一进程锁。"""
    with SYNC_LOCK:
        _checked_path(knowledge.KNOWLEDGE_DIR, Path("skill/docs"))
        return _import_skill_library(project_root, restore_deleted=restore_deleted)


def _import_skill_library(project_root: Path | None = None, *, restore_deleted: bool = False) -> dict[str, int]:
    """补充导入资料，保留原文件、既有内容及用户编辑的元数据。

    隐藏清单记录已导入路径。后续启动只引入新增来源文件，不复原用户删除的
    文件或文件夹；显式传入 restore_deleted 才补回缺失资料，仍不覆盖已有文件。
    列表和刷新接口不触发本函数，也不会执行任何导入包中的脚本。
    """
    project_root = project_root or Path(__file__).resolve().parents[3]
    base = knowledge._category_dir("skill", "docs")
    state_path = base / ".skill-import.json"
    state = _read_import_state(base)
    imported_paths = set(state.get("paths", []))
    existing = knowledge._read_raw_index("skill", "docs")
    file_sources: dict[str, str] = {}
    copied = 0
    entries = _source_entries(project_root)

    # 保留源包布局，逐文件补缺；复制后才记入清单，便于失败后重试。
    for source, relative, source_label in entries:
        paths = [source, *sorted(source.rglob("*"))] if source.is_dir() else [source]
        for path in paths:
            if path.is_symlink() or _excluded_source(path.relative_to(source.parent)):
                continue
            _checked_path(project_root, path.relative_to(project_root))
            target_relative = relative / path.relative_to(source) if source.is_dir() else relative
            key = target_relative.as_posix()
            target = _checked_path(base, target_relative)
            if path.is_file():
                file_sources[key] = source_label
            if key in imported_paths and not restore_deleted:
                continue
            if not restore_deleted and _was_deleted(target_relative, imported_paths, base):
                continue
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif path.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied += 1
            imported_paths.add(key)

    summary = _refresh_metadata(base, existing, file_sources)
    state["paths"] = sorted(imported_paths)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "packages": sum(source.is_dir() for source, _, _ in entries),
        **summary,
        "copied_files": copied,
    }
    if copied:
        logger.info("技能知识库导入完成：%d 个包，%d 份技能说明，本次新增 %d 个文件", result["packages"], result["skill_entries"], copied)
    return result


def _source_sync_inputs(project_root: Path) -> list[tuple[Path, Path, str | None]]:
    """枚举工程及公司技能来源；游戏资料等独立目录留给对应浏览器。"""
    result = []
    for source_relative, company_source in [(Path("skills"), False), (Path("ref/公司skill整合"), True)]:
        source_root = _checked_path(project_root, source_relative)
        if not source_root.exists():
            continue
        for source in sorted(source_root.iterdir()):
            if _excluded_source(Path(source.name)):
                continue
            if source.is_symlink():
                result.append((source, Path(source.name), "技能来源是符号链接，未读取"))
            elif source.is_file() and company_source:
                result.append((source, Path("公司资料") / source.name, None))
            elif source.is_dir() and (source / "SKILL.md").is_file():
                collision = company_source and ((project_root / "skills" / source.name).exists() or (project_root / "skills" / source.name).is_symlink())
                for directory, names, files in os.walk(source, followlinks=False):
                    # 链接目录只报冲突，不跟随；普通隐藏和缓存目录不参与同步。
                    names[:] = sorted(name for name in names if not _excluded_source(Path(name)))
                    for name in list(names):
                        path = Path(directory) / name
                        if path.is_symlink():
                            result.append((path, path.relative_to(source_root), "技能资料目录是符号链接，未读取"))
                            names.remove(name)
                    for name in sorted(files):
                        if _excluded_source(Path(name)):
                            continue
                        path = Path(directory) / name
                        problem = "工程 skills/ 已维护同名技能包，请先明确来源" if collision else None
                        if path.is_symlink():
                            problem = "技能资料文件是符号链接，未读取"
                        result.append((path, path.relative_to(source_root), problem))
    return result


def _file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _raw_metadata(base: Path) -> dict:
    """读取元数据但不触发目录创建或磁盘重建，供预览和写入前快照使用。"""
    index = _checked_path(base, Path("index.json"))
    if not index.exists():
        return {"items": [], "folders": []}
    value = json.loads(index.read_text(encoding="utf-8"))
    if isinstance(value, list):
        value = {"items": value, "folders": []}
    if not isinstance(value, dict) or not isinstance(value.get("items", []), list) or not isinstance(value.get("folders", []), list):
        raise ValueError("技能知识库索引格式错误")
    return {**value, "items": value.get("items", []), "folders": value.get("folders", [])}


def plan_company_skill_sync(project_root: Path | None = None) -> dict:
    """只读比较工程及公司来源；摘要绑定正文、索引和清单，防止过期覆盖。"""
    with SYNC_LOCK:
        project_root = project_root or Path(__file__).resolve().parents[3]
        base = _checked_path(knowledge.KNOWLEDGE_DIR, Path("skill/docs"))
        state = _read_import_state(base)
        imported = set(state.get("paths", []))
        files = []
        counts = dict.fromkeys(["added", "updated", "unchanged", "deleted_skipped", "conflicts"], 0)
        for source, relative, problem in _source_sync_inputs(project_root):
            item = {"path": relative.as_posix(), "source": source.relative_to(project_root).as_posix(),
                    "source_sha256": None, "target_sha256": None,
                    "origin": "工程已有" if source.relative_to(project_root).parts[0] == "skills" else "公司整合"}
            try:
                if problem:
                    raise ValueError(problem)
                source = _checked_path(project_root, source.relative_to(project_root))
                if not source.is_file():
                    raise ValueError("技能来源不是普通文件")
                target = _checked_path(base, relative)
                if target.exists() and not target.is_file():
                    raise ValueError("知识库目标不是普通文件")
                item.update(source_sha256=_file_hash(source), target_sha256=_file_hash(target), size=source.stat().st_size)
                if _was_deleted(relative, imported, base):
                    item.update(status="deleted_skipped", reason="此前已导入但被删除，保持删除状态")
                elif item["target_sha256"] is None:
                    item["status"] = "added"
                elif item["source_sha256"] == item["target_sha256"]:
                    item["status"] = "unchanged"
                else:
                    item.update(status="updated", reason="采用所示来源版本，覆盖前备份当前副本")
            except ValueError as error:
                item.update(status="conflicts", reason=str(error))
            counts[item["status"]] += 1
            files.append(item)
        files.sort(key=lambda item: item["path"])
        payload = {"files": files, "index_sha256": _file_hash(_checked_path(base, Path("index.json"))),
                   "import_state_sha256": _file_hash(_checked_path(base, Path(".skill-import.json")))}
        digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        return {"digest": digest, "counts": counts, "files": files}


def apply_company_skill_sync(reason: str, expected_digest: str, project_root: Path | None = None) -> dict:
    """显式同步复核过的工程与公司版本，先备份再替换，保留操作清单和原字节。"""
    if not reason.strip() or len(reason) > 2000:
        raise ValueError("同步必须填写不超过 2000 字的原因")
    with SYNC_LOCK:
        project_root = project_root or Path(__file__).resolve().parents[3]
        plan = plan_company_skill_sync(project_root)
        if not expected_digest or expected_digest != plan["digest"]:
            raise ValueError("同步计划已过期，请重新检查来源资料变动")
        if plan["counts"]["conflicts"]:
            first = next(item for item in plan["files"] if item["status"] == "conflicts")
            raise ValueError(f"技能资料存在来源或路径冲突：{first['path']}：{first['reason']}")
        base = _checked_path(knowledge.KNOWLEDGE_DIR, Path("skill/docs"))
        existing = _raw_metadata(base)
        changes = [item for item in plan["files"] if item["status"] in {"added", "updated"}]
        result = {"operation_id": None, "plan_digest": plan["digest"], "counts": plan["counts"], "backup_path": None}
        if not changes:
            return {**result, "summary": {"files": len(existing["items"]),
                                           "skill_entries": sum(item.get("filename") == "SKILL.md" for item in existing["items"])}}

        # 在修改任何目标前固定本批输入及原字节，遇到读取失败不会留下部分更新。
        payloads = []
        for item in changes:
            source = _checked_path(project_root, Path(item["source"]))
            target = _checked_path(base, Path(item["path"]))
            content = source.read_bytes()
            previous = target.read_bytes() if target.exists() else None
            if hashlib.sha256(content).hexdigest() != item["source_sha256"] or (hashlib.sha256(previous).hexdigest() if previous is not None else None) != item["target_sha256"]:
                raise ValueError("同步期间资料发生变化，请重新检查计划")
            payloads.append((item, target, content, previous))
        operation_id = uuid4().hex
        archive = _checked_path(base, Path(".skill-source-sync") / operation_id)
        archive.mkdir(parents=True)
        old_metadata = {}
        for name in ["index.json", ".skill-import.json"]:
            path = _checked_path(base, Path(name))
            old_metadata[name] = path.read_bytes() if path.exists() else None
            if old_metadata[name] is not None:
                (archive / ("before-" + name.lstrip("."))).write_bytes(old_metadata[name])
        for item, _, _, previous in payloads:
            if previous is not None:
                backup = archive / "previous" / item["path"]
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(previous)
        record = {"operation_id": operation_id, "time": datetime.now(timezone.utc).isoformat(), "reason": reason.strip(),
                  "plan_digest": plan["digest"], "sources": ["skills", "ref/公司skill整合"], "status": "prepared",
                  "counts": plan["counts"], "files": changes}
        manifest = archive / "manifest.json"
        manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        written = []
        try:
            for item, target, content, previous in payloads:
                target = _checked_path(base, Path(item["path"]))
                if _file_hash(target) != item["target_sha256"]:
                    raise ValueError("写入前目标已变化，同步已回滚，请重新检查")
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.{operation_id}.tmp")
                try:
                    with temporary.open("xb") as output:
                        output.write(content)
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)
                written.append((item, target, previous))
            state = _read_import_state(base)
            imported = set(state.get("paths", []))
            for item, _, _, _ in payloads:
                path = Path(item["path"])
                imported.update(part.as_posix() for part in [path, *path.parents] if part != Path("."))
            state["paths"] = sorted(imported)
            state["last_company_sync"] = operation_id
            (base / ".skill-import.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            summary = _refresh_metadata(base, existing, {item["path"]: item["origin"] for item in plan["files"]}, update_generated=True)
            record["status"] = "completed"
        except Exception as error:
            # 仅撤销仍为本批写入版本的文件，不覆盖另一写入方后来产生的内容。
            for item, target, previous in reversed(written):
                if _file_hash(target) == item["source_sha256"]:
                    target.unlink() if previous is None else target.write_bytes(previous)
            for name, content in old_metadata.items():
                path = base / name
                path.unlink(missing_ok=True) if content is None else path.write_bytes(content)
            knowledge._sync_cache.pop(("skill", "docs"), None)
            record.update(status="failed", error=str(error))
            raise
        finally:
            manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Skill 来源同步完成：新增 %d，更新 %d，操作 %s", plan["counts"]["added"], plan["counts"]["updated"], operation_id)
        return {**result, "operation_id": operation_id, "backup_path": archive.relative_to(base).as_posix(), "summary": summary}


def sync_skill_revision(relative_path: str, reason: str, run_id: str, project_root: Path | None = None) -> dict:
    """与来源同步共用锁，避免显式发布同时覆盖同一个知识库文件。"""
    with SYNC_LOCK:
        return _sync_skill_revision(relative_path, reason, run_id, project_root)


def _sync_skill_revision(relative_path: str, reason: str, run_id: str, project_root: Path | None = None) -> dict:
    """显式发布本次指定源文件；保留用户索引元数据，并存档前后版本与运行关联。

    普通启动仍只补缺。只有调用此函数才覆盖明确指定的知识库副本，避免把
    工程原始包的变化隐式覆盖到用户编辑后的整个知识库。
    """
    project_root = project_root or Path(__file__).resolve().parents[3]
    source_root = _checked_path(project_root, Path("skills"))
    source = _checked_path(source_root, Path(relative_path))
    if not source.is_file():
        raise ValueError("只能发布工程 skills/ 内明确指定的文件")
    if not reason.strip() or not run_id.strip():
        raise ValueError("技能修订必须关联运行并记录原因")
    content = source.read_text(encoding="utf-8")
    if source.name == "SKILL.md":
        if not content.startswith("---") or len(content.split("---", 2)) != 3:
            raise ValueError("Skill 缺少 YAML 元数据")
        metadata = yaml.safe_load(content.split("---", 2)[1])
        if not isinstance(metadata, dict) or not metadata.get("name") or not metadata.get("description"):
            raise ValueError("Skill 的 name/description 校验失败")
    base = _checked_path(knowledge.KNOWLEDGE_DIR, Path("skill/docs"))
    target = _checked_path(base, Path(relative_path))
    previous = target.read_text(encoding="utf-8") if target.is_file() else None
    revision = {"path": relative_path, "run_id": run_id, "reason": reason,
                "time": datetime.now(timezone.utc).isoformat(), "previous": previous, "content": content,
                "sha256": hashlib.sha256(content.encode()).hexdigest(), "validation": "源路径、UTF-8 与 Skill 元数据检查通过"}
    archive = _checked_path(base, Path(".skill-revisions"))
    archive.mkdir(parents=True, exist_ok=True)
    (archive / f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}.json").write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    knowledge._sync_cache.pop(("skill", "docs"), None)
    knowledge._read_index("skill", "docs")
    return revision


def main() -> None:
    """提供显式补导入口，需要恢复用户删除的文件时必须主动指定参数。"""
    parser = argparse.ArgumentParser(description="把工程和公司 Skill 资料导入知识库，保留现有文件与元数据。")
    parser.add_argument("--restore-deleted", action="store_true", help="补回此前导入后被删除的资料，不覆盖现有文件")
    args = parser.parse_args()
    result = import_skill_library(restore_deleted=args.restore_deleted)
    print(f"导入完成：{result['packages']} 个包，{result['skill_entries']} 份技能说明，共 {result['files']} 个文件，本次新增 {result['copied_files']} 个文件。")


if __name__ == "__main__":
    main()
