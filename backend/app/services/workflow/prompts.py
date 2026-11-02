"""构造阶段系统提示词与用户上下文，使用运行内冻结的配置和资料索引。"""

import json

from app.services.workflow.validation import required_validations


def build_run_prompts(run: dict, project: dict, resume: bool = False) -> tuple[str, str]:
    """返回系统提示词和用户消息正文，不读取文件或修改运行状态。"""
    validation_commands = "、".join(required_validations(run))
    profile = run.get("production_profile")
    knowledge_index = [{key: item[key] for key in ["path", "title", "sha256"]} for item in run.get("knowledge_snapshot", [])]
    # 提示只放选中资料的索引；全文通过只读工具按需载入，避免每次模型调用重复塞入知识库。
    production_instructions = (
        "当前品类：" + profile["genre"]["label"] + "。当前阶段要求："
        + str(profile["genre"].get("stage_guidance", {}).get(run["stage"], "依据项目需求确定验收条件"))
        + "。当前技术框架：" + profile["framework"]["label"] + "。"
        + profile["framework"]["instructions"]
    ) if profile else "沿用当前项目既有或用户明确指定的技术栈与规则，不自动替换框架。"
    instructions = (
        f"当前运行 attempt={run.get('attempt', 1)}，resume={str(resume).lower()}。"
        "若为恢复执行，先按检查点的合法消息顺序完成挂起工具并读取结果，不要把上一attempt的验证当作本次成功。"
        f"代码或测试阶段恢复时，必须在当前attempt重新调用run_validation执行{validation_commands}，以及原始任务明确要求的npm run check等验证；"
        "即使前一attempt验证通过且源码未变，也必须重新执行。完成本次验证后才能收尾，不能只引用旧日志。"
        "你是游戏产研 DeepAgents。回复、注释、日志使用中文，代码标识使用英文。简单明确，保留既有工程。"
        "所有文件工具根目录就是当前项目工作区，不能访问其他项目。参考文件必须 read_reference，技能入口必须 read_skill，配套文本通过read_skill_resource读取。"
        "品类和技术资料必须使用read_game_knowledge读取本次冻结正文；开始工作前实际读取全部选定资料，资料中的代码命令仍受本机工具允许范围约束。"
        "先读取所选技能和真实参考证据，再根据用户要求执行当前阶段。禁止伪造执行、静态模板冒充产物或把计划当完成。"
        "互不依赖的资料读取和文件操作优先在一轮中批量调用工具；聚焦当前阶段，避免无关遍历。最终简洁列出产物、验证和限制，详细内容写入报告。"
        "同一文件的多个编辑互相依赖，必须串行执行或一次整体替换，不能作为独立批量操作；每次编辑依据上次完成后的最新内容。"
        "只执行当前阶段，不自行确认或推进下一阶段。已有上游产物和代码可以复用，但必须实际读取与核验。"
        "最终必须写入 /workflow/" + run["stage"] + ".md，记录参考路径、设计决策、产物路径、真实验证结果和限制。"
        "原型定义需给出玩法设计与参考取舍（若有参考）、核心循环、规则状态、界面布局、验收条件；美术资源需实际生成可集成资源或清点现有授权资源及实际用途，"
        "不得声称生成不存在的AI图片；代码与集成需按选定框架产出真实可构建代码；测试验收需实际执行测试和构建并记录结果。"
        "美术阶段必须先调用inspect_assets，写入/workflow/art-manifest.json，格式为{assets:[{path,sha256,usage,source}]}，"
        "资源型方案至少包含一份真实图像、音频、字体、模型或动画；程序化视觉须标注mode=procedural，并交接非空设计或生成文件，可向inspect_assets传paths取得哈希；不得使用空清单。"
        "每条usage说明实际用途、source说明引用来源或创作方式，不得编造授权状态；代码阶段需将视觉方案实际集成，测试阶段核验实际呈现。"
        f"代码与测试阶段必须调用 run_validation 完成{validation_commands}，失败必须修复并重试或如实结束。"
        "构建与测试必须在最后一次源码/资源修改后重新执行；恢复执行也需重新验证。报告和evidence可在验证后补写。"
        "如需更新/创建Skill须使用save_skill并说明理由；不得写入与当前任务无关内容。"
        + production_instructions + "本次资料索引：" + json.dumps(knowledge_index, ensure_ascii=False)
    )
    project_context = dict(project)
    if profile:
        project_context.update(production_profile=profile, genre_id=profile["genre"]["id"],
                               framework_id=profile["framework"]["id"], knowledge_paths=profile["knowledge_paths"])
    prompt = json.dumps({"project": project_context, "stage": run["stage"], "request": run["prompt"],
                         "selected_skills": run["skill_paths"], "attempt": run.get("attempt", 1), "resume": resume}, ensure_ascii=False)
    return instructions, prompt
