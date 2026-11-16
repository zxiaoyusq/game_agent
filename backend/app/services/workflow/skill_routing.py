"""按品类配置、技术框架和阶段选择 Skill；仅规划资料，不执行来源工具。

规则只覆盖已有的真实复用关系。品类细节由项目知识资料承接，专项外部能力
单独说明限制，不把已收录文档解释为已经接入新的引擎、模型或采集器。
"""

from __future__ import annotations

import re

VERSION = "1.1.0"
STAGES = {"prototype": "原型定义", "art": "美术资源", "code": "代码与集成", "test": "测试验收"}
REVERSE = "game-reverse-engineering/modules/"
GENERAL = "casual-game-production/SKILL.md"
COCOS = "cocos-game-production/SKILL.md"
ART = "ai-art-automation/SKILL.md"
ART_STYLE = "azure-image2-generation/modules/casual-game-art-style/SKILL.md"
IMAGE = "azure-image2-generation/SKILL.md"
COMPETITOR = "game-competitor-analysis/SKILL.md"
H5_RESKIN = REVERSE + "h5-canvas-reskin/SKILL.md"
SKINNING = REVERSE + "skinning-pipeline/SKILL.md"
CREATOR = REVERSE + "cocos-project-standards/SKILL.md"
HARVEST = REVERSE + "hosted-minigame-harvest/SKILL.md"

# 每阶段只加入必需的流程方法；特定任务在后面的条件规则中补充。
STAGE_SKILLS = {
    "prototype": [(GENERAL, "用当前品类的规则与技术配置定义原型和验收条件")],
    "art": [(GENERAL, "沿用当前品类的资源交接和阶段边界"),
            (ART, "组织资源轻量索引、代表样、批量生产计划和累计回填"),
            (ART_STYLE, "确定当前休闲玩法的形式语言、功能色和视觉层级")],
    "code": [(GENERAL, "按当前品类实现核心循环，并遵守框架构建与交接契约")],
    "test": [(GENERAL, "按当前品类的规则不变量与真实运行证据进行验收")],
}

# 仅识别任务中的明确意图；不读取来源文档、引用路径或框架说明做关键词匹配。
INTENTS = {
    "reskin": r"换皮|换肤|美术替换|替换美术|\breskin(?:ning)?\b",
    "image": r"生图|生成(?:AI)?(?:图片|图像|美术|素材)|AI(?:图片|图像|美术)生成|(?:制作|生成)(?:真)?透明(?:素材|图片|贴图)|参考图编辑|编辑参考图|结构锁定换皮|\bimage\s+generat(?:ion|e)\b|\bgenerate\s+(?:images?|art)\b",
    "competitor": r"竞品(?:研究|分析|拆解|调研)|(?:研究|分析|拆解|调研)竞品|\bcompetitor\s+(?:research|analysis)\b",
    "harvest": r"(?:采集|抓取|拉取|下载|收集).{0,16}(?:宿主|托管|小游戏|AHA\s*Games)|(?:宿主|托管|小游戏|AHA\s*Games).{0,16}(?:采集|抓取|拉取|下载)|\b(?:harvest|download)\s+(?:hosted\s+)?minigames?\b",
    "restore": r"(?:原版|原码|原包|已有\s*H5|现有\s*H5).{0,12}(?:还原|恢复|复现|迭代|二开|二次开发)|(?:还原|恢复|复现|迭代|二开).{0,12}(?:原版|原码|原包|H5|托管小游戏)|\b(?:restore|iterate)\s+(?:existing\s+)?h5\b",
    "optimize": r"(?:包体|加载|首屏|内存|低\s*RAM).{0,8}(?:优化|压缩|裁剪|瘦身|降低)|(?:优化|压缩|裁剪|缩小|降低).{0,8}(?:包体|加载|首屏|内存)|\b(?:package|loading|memory)\s+optimization\b",
    "creator": r"(?<![A-Za-z0-9_])(?:cocos\s+)?creator(?![A-Za-z0-9_])",
    "standards": r"规范|体检|审查|审计|架构检查|\b(?:standards?|audit|review)\b",
}
NEGATION = re.compile(r"(?:不需要|无需|不用|不要|不必|不做|不想|不使用|不涉及|不进行|不执行|不是|并非|暂不|禁止|不再|仅参考|只参考).{0,12}$|不$|(?:\bno\b|\bnot\b|\bdon't\b|\bwithout\b|\bskip\b).{0,20}$", re.I)
NEGATION_AFTER = re.compile(r"^\s*(?:不需要|无需|不用|不要|不必|暂不|不做|不执行|不适用)")


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _brief_text(brief) -> str:
    """只取用户简报中的文本值，避免键名或配置字段意外触发任务。"""
    if isinstance(brief, str):
        return brief
    if isinstance(brief, dict):
        return "\n".join(_brief_text(value) for value in brief.values())
    if isinstance(brief, list):
        return "\n".join(_brief_text(value) for value in brief)
    return ""


def _intent_in_text(text: str, pattern: str) -> bool | None:
    """处理常见明确否定；同一请求最后一次明确提及优先，不推断复杂自然语言。"""
    state = None
    for clause in re.split(r"[，,。；;！!？?\n]", text):
        for match in re.finditer(pattern, clause, re.I):
            before, after = clause[:match.start()], clause[match.end():]
            state = not (NEGATION.search(before) or NEGATION_AFTER.search(after))
    return state


def _intent(prompt: str, brief: str, key: str) -> bool:
    """当前阶段请求可撤销简报中的旧意图；未提及该意图时沿用项目简报。"""
    current = _intent_in_text(prompt, INTENTS[key])
    return current if current is not None else bool(_intent_in_text(brief, INTENTS[key]))


def _context(project: dict, stage: str) -> dict:
    """冻结配置优先；没有配置的历史项目不从名字猜测引擎或品类。"""
    profile = _as_dict(project.get("production_profile"))
    genre, framework = _as_dict(profile.get("genre")), _as_dict(profile.get("framework"))
    return {
        "stage": stage, "stage_label": STAGES[stage],
        "genre_id": genre.get("id") or project.get("genre_id") or "",
        "genre_label": genre.get("label") or project.get("genre_id") or "未指定品类",
        "framework_id": framework.get("id") or project.get("framework_id") or "",
        "framework_label": framework.get("label") or project.get("framework_id") or "未指定技术框架",
        "knowledge_paths": list(profile.get("knowledge_paths") or project.get("knowledge_paths") or []),
        "genre_guidance": _as_dict(genre.get("stage_guidance")).get(stage)
            or "品类规则从项目已选知识和原型读取；当前目录没有独立的逐品类 Skill，不复制其他游戏的专属机制。",
    }


def _usage(path: str, framework: str, *, local_h5: bool = False) -> tuple[str, str]:
    """资料可读与专项执行分开描述；手动选择同样不能绕过实际工具边界。"""
    if path in {GENERAL, ART_STYLE}:
        return "workflow", ""
    if path == COCOS:
        return ("workflow", "") if framework == "cocos-web" else (
            "reference", "当前项目未配置 Cocos Web；Cocos 生产 Skill 仅作参考，不替换已选技术方案。")
    if path == ART:
        return "workflow", "美术流程用于任务拆分与资源回填；AI 图片须通过已配置的 generate_art_image 实际生产，并交接文件与哈希。"
    if path == H5_RESKIN:
        if framework in {"canvas-web", "native-web"}:
            return "workflow", "H5 换皮通过平台提问或自主决策记录确定方向，沿用已有设计与授权；知识库 HTML 仅供阅读，未接入的工作台回传、Python 脚本和设备工具不能视为可用。"
        return "reference", "H5 Canvas 换皮面向纯 H5/Canvas 资源，不应用到 Cocos/Unity 预制体；当前选择仅供参考。"
    if path == CREATOR:
        return "reference", "Creator 工程规范仅作审查参考：先体检工程身份和版本；当前没有 Creator 执行器或编辑器 MCP，不能推断使用 CFW，也不能照搬 DADA 案例。"
    if path == IMAGE:
        return "workflow", "读取生图规范后核实服务器图片API配置；只能用 generate_art_image 返回的真实文件证明图片生产，未配置时说明缺口。"
    if path == COMPETITOR:
        return "reference", "当前四阶段没有联网检索工具；竞品 Skill 仅用于已提供本地证据的分析，不宣称完成最新在线调研。"
    if path == HARVEST:
        if local_h5:
            return "workflow", "先核验已有 H5 输入与基线，按当前阶段完成还原或优化；包体、加载和内存分别取证，不重复采集。浏览器结果不代表真实宿主、广告或低内存设备验收。"
        return "reference", "当前四阶段没有托管小游戏下载、联网采集或 ADB 工具；采集 Skill 仅用于制定输入与校验要求，不会执行采集。"
    if path == "gpt52-vision-router/SKILL.md":
        return "reference", "此 Skill 面向特定 GPT-5.2 外部视觉配置；当前运行不会切换模型或启用独立视觉服务。"
    if path in {"spine-animation-pipeline/SKILL.md", "spine-imagegen-animation/SKILL.md",
                REVERSE + "dragonbones-spine-convert/SKILL.md"}:
        return "reference", "当前四阶段未接 Spine 编辑器或转换器；普通图片生成不代表已经完成动画制作与导出。"
    if path == "apk-engineering-analysis/SKILL.md" or path in {
            REVERSE + "unity-extract/SKILL.md", REVERSE + "3d-asset-extraction/SKILL.md",
            REVERSE + "cocos-reverse-engineering/SKILL.md"}:
        return "reference", "当前四阶段未接安装包解包、反编译或资源提取工具；只能分析已提供的可读证据，不能声称已执行拆包。"
    if path in {REVERSE + name + "/SKILL.md" for name in (
            "cocos-mcp-channel", "cocos-creator-repair", "prefab-bake", "ui-feature-pipeline", "cocos-qa")}:
        return "reference", "当前四阶段未接 Creator 编辑器、Prefab 烘焙或设备通道；仅借鉴适用方法，独立 Web 验证不代表编辑器或真机通过。"
    if path == REVERSE + "vision-device-testing/SKILL.md":
        return "reference", "当前四阶段没有真机、ADB 或独立 OCR 工具；浏览器可产出截图，但设备验收须由实际目标环境提供证据。"
    if path == REVERSE + "godot-migration-port/SKILL.md":
        return "reference", "当前可执行框架未包含 Godot；迁移文档只作方案参考，不能沿用 Web 命令宣称 Godot 已验收。"
    if path == SKINNING:
        return "reference", "仅借鉴资源映射、替换与回归方法；图集、Spine、Godot 或外部脚本按实际工具确认，不将来源工具当成本工程能力。"
    return "reference", "该专项 Skill 可按需阅读；工具、平台和命令仍以当前工作流为准，不会自动执行包内脚本或启用外部服务。"


def _resource_paths(path: str, stage: str, *, restore: bool, optimize: bool) -> list[str]:
    """只提示当前任务的起读资料；正文仍由冻结读取工具按需提供。"""
    names = []
    if path == H5_RESKIN:
        names = {
            "prototype": ["intake-and-direction.md", "html-workbench.md"],
            "art": ["end-to-end-orchestration.md", "component-restoration.md"],
            "code": ["end-to-end-orchestration.md", "pipeline.md"],
            "test": ["pipeline.md", "runtime-diagnosis.md"],
        }[stage]
    elif path == HARVEST:
        if optimize:
            names.append("h5-package-runtime-optimization.md")
        if restore:
            names.append("hosted-game-lifecycle.md" if stage == "prototype" else "hosted-h5-restoration.md")
        if not names:
            names.append("harvest-pipeline-and-gates.md")
    return [path.removesuffix("SKILL.md") + "references/" + name for name in names]


def plan_skill_selection(project: dict, stage: str, prompt: str, available_skills: list[dict], *,
                         mode: str = "auto", include_paths: list[str] | None = None,
                         exclude_paths: list[str] | None = None) -> dict:
    """生成可解释的选择计划；自动推荐加人工增减，手动模式采用明确列表。

    缺少自动候选只提示并跳过，尊重知识库删除；手工指定未知文件直接报错。
    返回值不包含正文且不改变输入，正文快照与真正读取由运行层负责。
    """
    if stage not in STAGES:
        raise ValueError("未知研发阶段")
    if mode not in {"auto", "manual"}:
        raise ValueError("Skill 选择模式必须为 auto 或 manual")
    available = {item["path"]: item for item in available_skills}
    includes, excludes = list(dict.fromkeys(include_paths or [])), list(dict.fromkeys(exclude_paths or []))
    if any(path not in available for path in [*includes, *excludes]):
        raise ValueError("人工选择或排除的 Skill 不存在于当前知识库")
    context = _context(project, stage)
    framework = context["framework_id"]
    brief = _brief_text(project.get("brief"))
    web = framework in {"canvas-web", "native-web"}
    reskin = _intent(prompt, brief, "reskin")
    restore = web and _intent(prompt, brief, "restore")
    optimize = web and stage in {"prototype", "code", "test"} and _intent(prompt, brief, "optimize")
    candidates = list(STAGE_SKILLS[stage])
    if framework == "cocos-web":
        candidates.append((COCOS, "当前技术配置为 Cocos Web，使用真实引擎、生命周期与交付规范"))
    if stage == "art" and _intent(prompt, brief, "image"):
        candidates.append((IMAGE, "美术阶段明确要求生成图片，先读取生图规范并核实当前工具能力"))
    if stage == "prototype" and _intent(prompt, brief, "competitor"):
        candidates.append((COMPETITOR, "原型阶段明确要求竞品研究，采用证据与设计取舍方法"))
    if stage == "prototype" and _intent(prompt, brief, "harvest"):
        candidates.append((HARVEST, "原型阶段明确提出托管小游戏采集需求，先说明输入与校验契约"))
    if restore or optimize:
        candidates.append((HARVEST, "已有 H5 还原或持续迭代按当前阶段承接；包体、加载和内存优化按各自证据验收"))
    if reskin:
        if web:
            candidates.append((H5_RESKIN, "当前为 H5 换皮任务，从方向与设计承接到资源生产、合入和运行验收"))
            if stage == "prototype":
                candidates.append((ART_STYLE, "换皮立项先明确目标市场、风格与功能色，已有设计直接沿用"))
        elif framework == "cocos-web" and stage != "prototype":
            candidates.append((SKINNING, "当前为 Cocos Web 换皮任务，采用通用资源映射和替换方法"))
    if _intent(prompt, brief, "creator") and _intent(prompt, brief, "standards"):
        candidates.append((CREATOR, "任务明确要求 Creator 工程规范审查，先确认工程身份与适用边界"))

    warnings, recommended = [], []
    for path, reason in candidates:
        if path not in available:
            warnings.append(f"自动候选未入库或已删除，已跳过：{path}")
            continue
        usage, _ = _usage(path, framework, local_h5=restore or optimize)
        recommended.append({"path": path, "name": available[path].get("name") or path,
                            "reason": f"{context['genre_label']} · {context['stage_label']}：{reason}",
                            "source": "auto", "usage": usage,
                            "resource_paths": _resource_paths(path, stage, restore=restore, optimize=optimize)})
    recommended_by_path = {item["path"]: item for item in recommended}
    selected = list(recommended_by_path) if mode == "auto" else []
    selected = [path for path in dict.fromkeys([*selected, *includes]) if path not in excludes]
    items = []
    for path in selected:
        usage, warning = _usage(path, framework, local_h5=restore or optimize)
        if mode == "auto" and path in recommended_by_path:
            item = dict(recommended_by_path[path])
        else:
            item = {"path": path, "name": available[path].get("name") or path,
                    "reason": "用户为当前阶段明确选择，按实际适用范围使用", "source": "manual", "usage": usage,
                    "resource_paths": _resource_paths(path, stage, restore=restore, optimize=optimize)}
        items.append(item)
        if warning:
            warnings.append(f"{item['name']}：{warning}")
    return {"version": VERSION, "mode": mode, "context": context,
            "recommended_paths": list(recommended_by_path), "selected_paths": selected,
            "items": items, "recommended_items": list(recommended_by_path.values()),
            "warnings": list(dict.fromkeys(warnings))}
