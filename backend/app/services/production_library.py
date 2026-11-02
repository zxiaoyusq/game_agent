"""品类与技术方案目录，以及只读知识快照；沿用现有文件知识库。

目录描述可执行契约，Markdown 保存可编辑的业务知识。运行时冻结两者，
避免用户更新知识库后，恢复中的任务悄悄改变输入或验收标准。
"""

import copy
import hashlib
import json
import logging
from pathlib import Path

from app.services import knowledge

logger = logging.getLogger(__name__)
SOURCE = Path(__file__).resolve().parents[3] / "resources" / "game-production"
VERSION = "1.0.0"
MODULES = ("genre", "framework")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}

# 品类只决定需要研究和验证的问题，不复制四阶段状态机或实现专属 Agent。
GENRES = [
    {"id": "general", "label": "通用 / 自定义休闲玩法", "description": "先定义核心循环和规则，再选择适用的验收方法。",
     "stage_guidance": {"prototype": "定义核心循环、状态转移、成功失败条件与首版范围，不预设排序或消除。", "test": "按原型中的规则不变量、完整循环和平台要求验证，不强制套用关卡求解。"}},
    {"id": "sorting", "label": "分类整理", "description": "球、水、货物等整理玩法；先明确容器、移动和完成规则。",
     "stage_guidance": {"prototype": "明确容器容量、单次移动、隐藏信息和完成规则，验证选定关卡。", "test": "核对数量守恒、合法移动、关卡可解性及本项目实际提供的辅助操作。"}},
    {"id": "block-placement", "label": "方块摆放与消行", "description": "离散网格、形状摆放、消行与无处可放的结算。",
     "stage_guidance": {"prototype": "明确棋盘、形状坐标、供块规则、同时消行和终局，不默认所有随机局面都可解。", "test": "验证越界重叠、同时消行计分、供块和无合法位置的终局；测试拖放与取消。"}},
    {"id": "match3", "label": "三消与连锁消除", "description": "交换、匹配、消除、下落补齐和连锁的状态顺序。",
     "stage_guidance": {"prototype": "定义有效交换、匹配优先级、特殊块、连锁、目标与无步处理。", "test": "用固定随机种子验证交换回退、连锁终止、步数与目标计数一致。"}},
    {"id": "merge", "label": "合成与升级", "description": "合并条件、产物、空间和经济消耗的事务一致性。",
     "stage_guidance": {"prototype": "明确合成输入、产物、消耗、空间与等级边界，区分拖拽和自动合成。", "test": "验证一次性扣除与生成、满盘、顶级物品、取消拖拽和存档恢复。"}},
    {"id": "idle", "label": "放置与轻经营", "description": "产出、成本、升级、离线收益与时间边界。",
     "stage_guidance": {"prototype": "定义资源流、升级成本、收益上限和离线时间策略。", "test": "验证经济不变量、幂等结算、时钟回拨、离线收益上限与数值精度。"}},
    {"id": "physics", "label": "物理与时机玩法", "description": "碰撞、运动、输入时机和可重现的模拟条件。",
     "stage_guidance": {"prototype": "定义物理步长、碰撞与计分、成功失败、输入窗口和可接受误差。", "test": "按固定输入与时间步验证碰撞、重开、快慢帧和误差范围，不要求棋盘求解。"}},
]
for _genre in GENRES:
    _genre["knowledge_paths"] = list(dict.fromkeys(["genre/docs/general.md", f"genre/docs/{_genre['id']}.md"]))

# 本轮仅注册已实现的 Web 命令/预览协议；其它引擎先作为选型资料保留。
FRAMEWORKS = [
    {"id": "cocos-web", "label": "Cocos · Web / H5", "description": "官方 Cocos 引擎的独立 Web 工程。",
     "status": "已有完整项目验收", "instructions": "使用真实官方 Cocos 引擎，固定实际版本、构建来源和运行时证据。新任务重新核实版本。此配置是独立 Web 工程，不代表 Creator 编辑器或原生包适配。",
     "knowledge_paths": ["framework/docs/web-common.md", "framework/docs/cocos-web.md"],
     "recommended_skills": ["casual-game-production/SKILL.md", "cocos-game-production/SKILL.md"]},
    {"id": "canvas-web", "label": "Canvas 2D · Web / H5", "description": "轻量二维规则验证，使用浏览器 Canvas 和独立玩法逻辑。",
     "status": "执行协议已适配，待完整项目验收", "instructions": "使用浏览器原生 Canvas 2D 实现轻量游戏，不加载 Cocos 或伪造引擎版本。玩法状态与渲染、输入分离，提供真实浏览器输入验证；复杂物理或编辑器需求应重新选型。",
     "knowledge_paths": ["framework/docs/web-common.md", "framework/docs/canvas-web.md"],
     "recommended_skills": ["casual-game-production/SKILL.md"]},
]
for _framework in FRAMEWORKS:
    _framework.update(required_validations=["npm run build", "npm test", "npm run check"], preview_entry="dist/index.html")


def _knowledge_file(relative: str) -> Path:
    """只接受两类知识正文；拒绝索引、隐藏文件、链接及任意路径跳转。"""
    parts = relative.split("/")
    if (len(parts) < 3 or parts[0] not in MODULES or parts[1] != "docs"
            or any(not part or part.startswith(".") or "\\" in part for part in parts)
            or Path(relative).suffix.lower() not in TEXT_SUFFIXES or parts[-1] == "index.json"):
        raise ValueError("知识路径必须是游戏品类或技术框架库中的正文文件")
    base = knowledge.KNOWLEDGE_DIR.resolve()
    current = knowledge.KNOWLEDGE_DIR
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("知识资料不能使用符号链接")
    if not current.resolve().is_relative_to(base) or not current.is_file():
        raise ValueError(f"知识资料不存在：{relative}")
    if current.stat().st_size > 256 * 1024:
        raise ValueError("单份运行知识不能超过 256KB，请先拆成可按需引用的文档")
    return current


def get_catalog() -> dict:
    """返回可执行方案与当前可读资料；刷新目录不会恢复用户删除的文件。"""
    documents = []
    for module in MODULES:
        for item in knowledge.list_items(module, "docs"):
            relative = "/".join(part for part in [module, "docs", item.folder, item.stored_name] if part)
            try:
                _knowledge_file(relative)
            except ValueError:
                continue
            documents.append({"path": relative, "title": item.title, "module": module, "summary": item.summary,
                              "url": f"/api/knowledge/{module}/docs/items/{item.id}/raw"})
    return {"version": VERSION, "genres": copy.deepcopy(GENRES), "frameworks": copy.deepcopy(FRAMEWORKS),
            "documents": sorted(documents, key=lambda item: item["path"])}


def resolve_profile(genre_id: str = "general", framework_id: str = "cocos-web") -> dict:
    """仅采用服务端注册的执行契约，调用方不能上传任意命令覆盖门禁。"""
    genre = next((item for item in GENRES if item["id"] == genre_id), None)
    framework = next((item for item in FRAMEWORKS if item["id"] == framework_id), None)
    if not genre or not framework:
        raise ValueError("未知游戏品类或技术框架，请从当前目录选择")
    profile = copy.deepcopy({"version": VERSION, "genre": genre, "framework": framework,
                             "knowledge_paths": list(dict.fromkeys(genre["knowledge_paths"] + framework["knowledge_paths"]))})
    profile["sha256"] = hashlib.sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return profile


def snapshot_knowledge(paths: list[str]) -> list[dict]:
    """运行开始时冻结实际正文与哈希；恢复任务通过快照读取，不追随资料变动。"""
    unique = list(dict.fromkeys(paths))
    if len(unique) > 20:
        raise ValueError("单次最多引用 20 份知识资料，请优先选择与本项目相关的内容")
    result = []
    for relative in unique:
        path = _knowledge_file(relative)
        raw = path.read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"知识资料必须是 UTF-8 文本：{relative}") from error
        title = next((line.lstrip("# ") for line in content.splitlines() if line.startswith("# ")), path.stem)
        result.append({"path": relative, "title": title, "sha256": hashlib.sha256(raw).hexdigest(), "content": content})
    if sum(len(item["content"].encode()) for item in result) > 1024 * 1024:
        raise ValueError("所选知识超过 1MB，请减少引用或拆分资料")
    return result


def import_production_library(source: Path | None = None) -> dict:
    """首次补导种子文档，保持用户编辑与删除；原始内容留在 resources 供审阅。"""
    source = source or SOURCE
    copied = 0
    for module in MODULES:
        base = knowledge._category_dir(module, "docs")
        state_path = base / ".production-import.json"
        imported = set(json.loads(state_path.read_text()).get("paths", [])) if state_path.exists() else set()
        existing = {(item.folder, item.stored_name) for item in knowledge._read_index(module, "docs")}
        for path in sorted((source / module).glob("*.md")):
            if path.is_symlink() or path.name in imported:
                continue
            target = base / path.name
            if not target.exists():
                target.write_bytes(path.read_bytes())
                copied += 1
            imported.add(path.name)
        knowledge._sync_cache.pop((module, "docs"), None)
        items = knowledge._read_index(module, "docs")
        for item in items:
            if (item.folder, item.stored_name) not in existing and not item.folder and item.stored_name in imported:
                content = (base / item.stored_name).read_text(encoding="utf-8")
                item.title = next((line.lstrip("# ") for line in content.splitlines() if line.startswith("# ")), item.title)
                item.tags = ["游戏品类" if module == "genre" else "技术框架", "初始指南"]
                item.summary = next((line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")), "")
        knowledge._write_index(module, "docs", items, knowledge._read_folders(module, "docs"))
        state_path.write_text(json.dumps({"paths": sorted(imported)}, ensure_ascii=False, indent=2), encoding="utf-8")
    if copied:
        logger.info("品类与技术知识导入完成，本次新增 %d 个文件", copied)
    return {"copied_files": copied}
