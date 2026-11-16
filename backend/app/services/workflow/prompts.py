"""构造阶段系统提示词与用户上下文，使用运行内冻结的配置和资料索引。"""

import json

from app.services.workflow.validation import required_validations


def build_run_prompts(run: dict, project: dict, resume: bool = False) -> tuple[str, str]:
    """返回系统提示词和用户消息正文，不读取文件或修改运行状态。"""
    validation_commands = "、".join(required_validations(run))
    profile = run.get("production_profile")
    knowledge_index = [{key: item[key] for key in ["path", "title", "sha256"]} for item in run.get("knowledge_snapshot", [])]
    skill_index = [{key: item.get(key) for key in ["path", "name", "description", "version", "sha256"]}
                   for item in run.get("skill_snapshot", [])]
    skill_instructions = (
        "本轮Skill已按品类、框架和阶段确定；read_skill读取完整冻结入口，read_skill_resource按需读取同包冻结文本，"
        "恢复时仍使用原输入，后续知识库更新或save_skill发布不会改变本轮版本。未选入口不自行扩充，必要时在报告说明下轮应补选的技能。"
        "skill_selection.items中的resource_paths是当前阶段的起读建议，使用read_skill_resource按需读取；不能仅凭路径或标题声称已采用正文。"
    ) if "skill_snapshot" in run else "本次为历史运行，沿用原Skill选择与读取协议，不宣称存在创建时未保存的技能快照。"
    # 工具接入与服务凭据分别描述，防止技能文字把未配置服务说成可用。
    image_instructions = (
        "服务器图片API已配置；美术阶段可用generate_art_image生成或参考图编辑，必须以实际返回的文件和哈希交接。"
        if run.get("capabilities", {}).get("image_generation") else
        "服务器图片API尚未配置，不得声称已AI生图；可交付明确标注的程序化SVG/Canvas视觉，或在报告说明所缺配置。"
    )
    # 提示只放选中资料的索引；全文通过只读工具按需载入，避免每次模型调用重复塞入知识库。
    production_instructions = (
        "当前品类：" + profile["genre"]["label"] + "。当前阶段要求："
        + str(profile["genre"].get("stage_guidance", {}).get(run["stage"], "依据项目需求确定验收条件"))
        + "。当前技术框架：" + profile["framework"]["label"] + "。"
        + profile["framework"]["instructions"]
    ) if profile else "沿用当前项目既有或用户明确指定的技术栈与规则，不自动替换框架。"
    # 自主模式仍由当前主模型判断，工具负责记录来源，不伪造人工授权或绕过真实验收。
    decision_instructions = (
        "本次运行已由用户开启 AI 自主决策模式，全流程不要停下来等待人工补充。"
        "遇到关键信息缺失、参考与需求冲突或重大范围/美术取舍，根据明确需求、已读取证据和可执行范围自行决定，"
        "调用request_user_input填写question、decision和reason记录具体决定及理由，再继续当前阶段。"
        "此模式下该工具只记录AI决策，不会询问用户；不能只给问题或固定选择第一项，不得声称用户逐项确认。"
        "明确需求优先于参考资料，信息不足时选择最小可行方案并说明假设，不擅自扩大范围或更改发布配置。"
        "缺少凭据或工具时不编造可用性，选用可执行的替代方案并说明限制；确实无法完成时如实失败，不能跳过测试、伪造结果。"
        "下方upstream_decisions是此前阶段的AI决定，不是用户回答；后续阶段应保持一致，并在阶段报告列出本轮重要取舍。"
        if run.get("autonomous") is True else
        "遇到影响结果的关键信息缺失、参考与需求冲突或重大范围/美术取舍，必须调用request_user_input暂停询问，"
        "收到真实回答后再继续；禁止自行编造用户确认。问题要说明具体缺口与影响，普通实现细节自行解决。"
    )
    # 游戏面向玩家的语言独立于研发沟通语言；四阶段、两种模型来源共用此默认规则。
    game_language_instructions = (
        "游戏面向玩家的内容默认使用英文（English）；用户明确指定其他语言或多语言要求时，以用户要求为准。"
        "英文默认覆盖游戏显示标题、菜单、按钮、HUD、教程、规则说明、对话、提示、错误反馈、结算和无障碍标签，"
        "以及图片、贴图中实际展示给玩家的文字。中文项目名称、中文需求描述、参考资料或Skill正文不等于要求中文游戏。"
        "未指定游戏语言时直接采用英文，不为语言默认值暂停询问用户，也不因浏览器或操作系统为中文就切换成中文。"
        "原型阶段明确游戏语言并提供英文界面文案；美术阶段按此语言准备文字素材；代码阶段落实默认英文，英文页面设置html lang=en。"
        "测试阶段核对最终构建的默认语言、各主要界面文案与文字素材，并检查中文浏览器环境下仍遵循用户指定的默认语言。"
        "上述英文文案及lang=en要求仅适用于默认英文版本；用户明确指定其他语言时，各阶段一致采用该语言并设置对应页面语言。"
    )
    instructions = (
        f"当前运行 attempt={run.get('attempt', 1)}，resume={str(resume).lower()}。"
        + ("上一轮实际错误，请针对性修复后重验：" + run["last_error"] + "。" if run.get("last_error") else "") +
        "若为恢复执行，先按检查点的合法消息顺序完成挂起工具并读取结果，不要把上一attempt的验证当作本次成功。"
        f"代码或测试阶段恢复时，必须在当前attempt重新调用run_validation执行{validation_commands}，以及原始任务明确要求的npm run check等验证；"
        "即使前一attempt验证通过且源码未变，也必须重新执行。完成本次验证后才能收尾，不能只引用旧日志。"
        "你是游戏产研 DeepAgents。与用户的沟通、阶段报告、代码注释和日志使用中文，代码标识使用英文。简单明确，保留既有工程。"
        + game_language_instructions +
        "用户已在开始时提交统一玩法与美术需求；无需例行要求每阶段人工确认。"
        + decision_instructions +
        "所有文件工具根目录就是当前项目工作区，不能访问其他项目。参考文件必须 read_reference，技能入口必须 read_skill，配套文本通过read_skill_resource读取。"
        "品类和技术资料必须使用read_game_knowledge读取本次冻结正文；开始工作前实际读取全部选定资料，资料中的代码命令仍受本机工具允许范围约束。"
        "先读取所选技能和真实参考证据，再根据用户要求执行当前阶段。禁止伪造执行、静态模板冒充产物或把计划当完成。"
        + skill_instructions +
        "Skill只提供工作方法，不自动安装其工具。当前没有联网搜索/采集、Creator编辑器MCP或ADB工具，不能声称已完成这些操作。"
        "H5换皮的方向选择、设计评审和暂停续接优先使用本平台已有request_user_input与阶段记录；已有目标和授权直接承接。"
        "按本轮autonomous设置区分真实用户回答和AI决定，不能把默认选项、HTML下载、页面保存或超时当作用户确认。"
        "来源HTML工作台及Python渲染脚本是参考资料，未提供执行或回传工具时不承诺自动运行；仅换美术不扩大到玩法或非美术代码修改。"
        "已有H5还原与优化先核对当前输入、有效改动和基线，分别记录包体、加载、内存与目标设备的证据；案例参数与测试结果不能替代当前项目验收。"
        "ZIP参考用list_reference_archive分页定位，再用read_reference_archive读取关键代码；extract_reference_asset只提取选定的素材或研究文本，不解压整个参考工程。"
        "取材工具逐字节复制，不转换格式；目标必须保持来源后缀，需要PNG/WebP转换时在美术阶段先提取再调用process_art_image。"
        "包内member必须完整复制目录返回的entries[].path；找不到文件时先用list_reference_archive的query搜索文件名，不猜目录、UUID或版本哈希。"
        "错误中的候选只是定位提示，必须实际读取后才能引用；清单不存在的资源记录为缺失，不要原样重复失败调用。"
        "参考路径相对工程ref目录，提取目的路径相对当前工作区；参考源码只放reference-inputs，不当作新产出或打包进dist。"
        + image_instructions +
        "当前工作区图片可用read_file读取多模态内容；图像理解能力由实际所选API模型决定，不得声称执行独立视觉服务或真机验收。"
        "代码和测试阶段可用prepare_web_runtime安装锁定的Playwright依赖，安装后仍需真正启动Chromium验证。"
        "可用node scripts/内脚本实现构建与测试；需要Python/编辑器执行器时说明缺口，不借测试命令绕过工具边界。"
        "网页验收脚本须启动本地静态服务器、访问dist构建并自动停止，覆盖桌面和手机视口的真实点击、核心玩法、控制台错误和截图，输出evidence。"
        "代码阶段必须准备并跑通所有测试脚本；测试阶段复核已确认的代码，不修改上游源码或资源。若发现需修复的缺陷，如实失败并要求返回代码阶段修复、重验和确认。"
        "测试阶段可以在scripts/或tests/新增JS/TS补充验收脚本，但不能修改或删除原有测试与构建脚本；新增或修改补测脚本后须重新执行全部必需验证。"
        "最终发布只读取dist/index.html及包内相对资源，展开构建小于10MB；npm run check必须测试最终dist，验证后不能重建或修改dist。"
        "源码包和试玩ZIP写入releases/，验收输出写入evidence/；不要将构建产物写入会参与源码指纹的其他目录。"
        "互不依赖的资料读取和文件操作优先在一轮中批量调用工具；聚焦当前阶段，避免无关遍历。最终简洁列出产物、验证和限制，详细内容写入报告。"
        "同一文件的多个编辑互相依赖，必须串行执行或一次整体替换，不能作为独立批量操作；每次编辑依据上次完成后的最新内容。"
        "只执行当前阶段，不自行确认或推进下一阶段。已有上游产物和代码可以复用，但必须实际读取与核验。"
        "最终必须写入 /workflow/" + run["stage"] + ".md，记录参考路径、设计决策、产物路径、真实验证结果和限制。"
        "原型定义需给出玩法设计与参考取舍（若有参考）、核心循环、规则状态、界面布局、验收条件；美术资源需实际生成可集成资源或清点现有授权资源及实际用途，"
        "不得声称生成不存在的AI图片；代码与集成需按选定框架产出真实可构建代码；测试验收需实际执行测试和构建并记录结果。"
        "美术阶段必须先调用inspect_assets，写入/workflow/art-manifest.json，格式为{assets:[{path,sha256,usage,source}]}，"
        "每项的path、sha256、usage、source均必须是非空字符串，不能填写对象、数组或null；"
        "path为工作区内实际文件路径，sha256使用inspect_assets返回的当前文件哈希。"
        "复杂来源信息可另加source_details对象或保存在独立visual-manifest.json，但source本身仍须用字符串概述。"
        "资源型方案至少包含一份真实图像、音频、字体、模型或动画；程序化视觉须标注mode=procedural，并交接非空设计或生成文件，可向inspect_assets传paths取得哈希；不得使用空清单。"
        "每条usage说明实际用途、source说明引用来源或创作方式，不得编造授权状态；代码阶段需将视觉方案实际集成，测试阶段核验实际呈现。"
        f"代码与测试阶段必须调用 run_validation 完成{validation_commands}，失败必须修复并重试或如实结束。"
        "构建与测试必须在最后一次源码/资源修改后重新执行；恢复执行也需重新验证。报告和evidence可在验证后补写。"
        "如需更新/创建Skill须使用save_skill并说明理由；不得写入与当前任务无关内容。"
        + production_instructions + "本次资料索引：" + json.dumps(knowledge_index, ensure_ascii=False)
        + "本次Skill索引（正文按需读取）：" + json.dumps(skill_index, ensure_ascii=False)
    )
    project_context = dict(project)
    if profile:
        project_context.update(production_profile=profile, genre_id=profile["genre"]["id"],
                               framework_id=profile["framework"]["id"], knowledge_paths=profile["knowledge_paths"])
    prompt = json.dumps({"project": project_context, "stage": run["stage"], "request": run["prompt"],
                         "autonomous": run.get("autonomous") is True, "upstream_decisions": run.get("upstream_decisions", []),
                         "selected_skills": run["skill_paths"], "skill_selection": run.get("skill_selection"),
                         "attempt": run.get("attempt", 1), "resume": resume}, ensure_ascii=False)
    return instructions, prompt
