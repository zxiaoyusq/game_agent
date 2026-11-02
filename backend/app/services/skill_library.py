"""把工程与公司 Skill 包作为只读来源导入知识库，不加载或执行包内工具。"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.services import knowledge

logger = logging.getLogger(__name__)

# 展示文案独立于源文件，导入时保留原目录名和原文，便于追溯来源。
SKILL_DESCRIPTIONS = {
    "apk-engineering-analysis": ("APK 工程拆解与资源分析", "分析 Android 安装包的引擎、代码、资源与配置，整理工程报告和离线资源浏览器。"),
    "game-competitor-analysis": ("游戏竞品拆解与融合设计", "研究游戏玩法、关卡、美术、成长、商业化与玩家反馈，形成有来源的竞品报告和原创设计建议。"),
    "ai-art-automation": ("AI 美术自动化", "从需求、策划和工程中拆分美术任务，组织生成、后处理、合入工程与验收。"),
    "azure-image2-generation": ("AI 生图与素材换皮", "提供生图、改图、真透明素材、批量换皮、结构锁定与图集处理流程，附提示词模板和脚本。"),
    "spine-animation-pipeline": ("Spine 动画制作流水线", "覆盖角色拆件、定位、绑骨、动画、图集导出、版本兼容与质量检查。"),
    "spine-imagegen-animation": ("ImageGen 角色与 Spine 动画", "配合图像生成制作角色部件，组织定位、骨骼、待机动画与 Spine 导出。"),
    "gpt52-vision-router": ("GPT-5.2 外部视觉路由", "为特定模型配置提供外部识图与视觉质检流程，附 MCP 服务和接入说明。"),
    "game-reverse-engineering": ("游戏逆向与二次开发总集", "从引擎识别、资源提取与玩法分析，到工程恢复、换皮、SDK 替换、Godot 迁移和设备验收，统筹 16 个子模块。"),
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
    "modules": "游戏逆向与二次开发的 16 个专项子模块",
    "mcp": "MCP 服务源码与接入说明",
}


def _source_entries(project_root: Path) -> list[tuple[Path, Path, str]]:
    """枚举两处来源中的完整技能包及公司附带资料。"""
    entries = []
    for source_dir, source_label in (
        (project_root / "skills", "工程已有"),
        (project_root / "ref" / "公司skill整合", "公司整合"),
    ):
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.iterdir()):
            if source.is_symlink():
                continue
            if source.is_dir() and (source / "SKILL.md").is_file():
                entries.append((source, Path(source.name), source_label))
            elif source.is_file() and source_label == "公司整合":
                entries.append((source, Path("公司资料") / source.name, source_label))
    return entries


def _skill_metadata(path: Path) -> tuple[str, str]:
    """从 Skill 元数据和界面配置读取新增包展示文案，旧包保留已有中文映射。"""
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
    if config.is_file():
        try:
            loaded = yaml.safe_load(config.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("interface"), dict):
                interface = loaded["interface"]
        except yaml.YAMLError:
            pass
    extra = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
    title = extra.get("display_name") or interface.get("display_name") or metadata.get("name") or path.parent.name
    summary = metadata.get("description") or interface.get("short_description") or "技能使用说明。"
    return str(title), str(summary)


def _item_metadata(relative: Path, source_label: str, base: Path) -> tuple[str, list[str], str]:
    """区分技能入口、嵌套子模块和配套文件，避免所有入口同名。"""
    package = relative.parts[0]
    package_title, package_summary = SKILL_DESCRIPTIONS.get(package, _skill_metadata(base / package / "SKILL.md"))
    if relative.name == "SKILL.md":
        title, summary = SKILL_DESCRIPTIONS.get(relative.parent.name, _skill_metadata(base / relative))
        kind = "主入口" if len(relative.parts) == 2 else "子模块"
        return title, [source_label, kind, package_title], summary
    if package == "公司资料":
        title = "公司技能整合说明" if relative.name == "README.md" else relative.stem
        return title, [source_label, "附带资料"], package_summary
    return relative.stem, [source_label, "配套资料", package_title], f"{package_title}的配套文件：{relative.as_posix()}"


def import_skill_library(
    project_root: Path | None = None,
    *,
    restore_deleted: bool = False,
) -> dict[str, int]:
    """补充导入资料，保留原文件、既有内容及用户编辑的元数据。

    隐藏清单记录已导入路径。后续启动只引入新增来源文件，不复原用户删除的
    文件或文件夹；显式传入 restore_deleted 才补回缺失资料，仍不覆盖已有文件。
    列表和刷新接口不触发本函数，也不会执行任何导入包中的脚本。
    """
    project_root = project_root or Path(__file__).resolve().parents[3]
    base = knowledge._category_dir("skill", "docs")
    state_path = base / ".skill-import.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    imported_paths = set(state.get("paths", []))
    existing = knowledge._read_raw_index("skill", "docs")
    existing_item_keys = {(item.get("folder", ""), item.get("stored_name", "")) for item in existing["items"]}
    existing_folder_paths = {folder["path"] for folder in existing["folders"]}
    file_sources: dict[str, str] = {}
    copied = 0
    entries = _source_entries(project_root)

    # 保留源包布局，逐文件补缺；复制后才记入清单，便于失败后重试。
    for source, relative, source_label in entries:
        paths = [source, *sorted(source.rglob("*"))] if source.is_dir() else [source]
        for path in paths:
            if path.is_symlink() or "__pycache__" in path.parts or ".git" in path.parts:
                continue
            target_relative = relative / path.relative_to(source) if source.is_dir() else relative
            key = target_relative.as_posix()
            target = base / target_relative
            if path.is_file():
                file_sources[key] = source_label
            if key in imported_paths and not restore_deleted:
                continue
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif path.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied += 1
            imported_paths.add(key)

    # 磁盘同步会保留既有元数据；仅首次发现的记录补上中文展示文案。
    knowledge._sync_cache.pop(("skill", "docs"), None)
    items = knowledge._read_index("skill", "docs")
    folders = knowledge._read_folders("skill", "docs")
    for item in items:
        key = (item.folder, item.stored_name)
        relative = Path(item.folder) / item.stored_name
        source_label = file_sources.get(relative.as_posix())
        if key not in existing_item_keys and source_label:
            item.title, item.tags, item.summary = _item_metadata(relative, source_label, base)
    for folder in folders:
        if folder.path in existing_folder_paths:
            continue
        leaf = Path(folder.path).name
        if leaf in SKILL_DESCRIPTIONS:
            title, summary = SKILL_DESCRIPTIONS[leaf]
            folder.desc = f"{title}：{summary}"
        elif leaf == "公司资料":
            folder.desc = "公司技能整合说明与 BlockBlast 专项脚本、文档压缩包。"
        elif (base / folder.path / "SKILL.md").is_file():
            title, summary = _skill_metadata(base / folder.path / "SKILL.md")
            folder.desc = f"{title}：{summary}"
        else:
            folder.desc = FOLDER_DESCRIPTIONS.get(leaf, "技能包配套资料目录")
    knowledge._write_index("skill", "docs", items, folders)
    state_path.write_text(json.dumps({"paths": sorted(imported_paths)}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "packages": sum(source.is_dir() for source, _, _ in entries),
        "skill_entries": sum(item.filename == "SKILL.md" for item in items),
        "files": len(items),
        "copied_files": copied,
    }
    if copied:
        logger.info("技能知识库导入完成：%d 个包，%d 份技能说明，本次新增 %d 个文件", result["packages"], result["skill_entries"], copied)
    return result


def sync_skill_revision(relative_path: str, reason: str, run_id: str, project_root: Path | None = None) -> dict:
    """显式发布本次指定源文件；保留用户索引元数据，并存档前后版本与运行关联。

    普通启动仍只补缺。只有调用此函数才覆盖明确指定的知识库副本，避免把
    工程原始包的变化隐式覆盖到用户编辑后的整个知识库。
    """
    project_root = project_root or Path(__file__).resolve().parents[3]
    source_root = (project_root / "skills").resolve()
    source = (source_root / relative_path).resolve()
    if not source.is_relative_to(source_root) or not source.is_file() or source.is_symlink():
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
    base = knowledge._category_dir("skill", "docs")
    target = (base / relative_path).resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError("知识库目标路径无效")
    previous = target.read_text(encoding="utf-8") if target.is_file() else None
    revision = {"path": relative_path, "run_id": run_id, "reason": reason,
                "time": datetime.now(timezone.utc).isoformat(), "previous": previous, "content": content,
                "sha256": hashlib.sha256(content.encode()).hexdigest(), "validation": "源路径、UTF-8 与 Skill 元数据检查通过"}
    archive = base / ".skill-revisions"
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
