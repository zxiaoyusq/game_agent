"""策划 Agent 的业务核心。

每个子模块（玩法 / 数值 / 活动 / ...）后面都会有自己的提示词，
本期先以「玩法策划案」为例落地一条端到端的流式生成链路。

知识库读取 + vision 注入 + 流式拆包统一走 services/kb_context，
本文件只关心 prompt 文本与流式入口；不感知 HTTP/SSE。
"""

from __future__ import annotations

from typing import AsyncIterator, List, Optional

from app.providers import get_chat_model
from app.services.kb_context import build_messages, extract_text, resolve_kb


# ---- 提示词 -----------------------------------------------------------------

# 「玩法策划案」节点 system prompt：把用户需求 + 项目设定 + 已选知识库
# 转化为结构化的策划文档草稿。后续其它节点会有自己的 prompt，可放到下面继续扩展。
GAMEPLAY_SYSTEM_PROMPT = (
    "你是一名资深游戏策划，擅长把模糊的玩法想法拆解为可落地的策划案。\n"
    "请基于用户输入和提供的项目设定 / 知识库参考，输出一份 Markdown 策划草稿，结构包含：\n"
    "1. 玩法目标\n2. 核心机制\n3. 玩家行为路径\n4. 反馈与奖励\n5. 风险与边界\n"
    "要求：条目清晰、避免空话；输出全部使用中文。\n"
    "若知识库中包含图片，请结合图像内容做出针对性建议。"
)


# ---- 公共流式入口 -----------------------------------------------------------

async def stream_planning(
    *,
    user_input: str,
    model_id: str,
    project_brief: str = "",
    kb_refs: Optional[List[str]] = None,
    sub_module: str = "gameplay",
) -> AsyncIterator[str]:
    """对策划 Agent 的某个子模块做一次流式生成。

    Args:
        user_input:     用户在聊天框里的最新请求
        model_id:       前端选择的模型，必须在后端白名单内
        project_brief:  项目背景 / Setup 文本，对应 InputPanel 中的设置区
        kb_refs:        前端选中的知识库三段式 key 列表（module:category:item_id）
        sub_module:     子模块 id（gameplay / activity / numeric / ...），
                        当前阶段只实现 gameplay，其它先回退到 gameplay 的 prompt

    Yields:
        每个 token 的 delta 文本（已剥离 langchain 的 chunk 包裹）。
    """
    # 当前只接了「玩法策划案」一个节点，其余子模块先复用同一个 prompt 兜底。
    # 真要扩展时，把 sub_module 映射到不同 system prompt 即可。
    system_prompt = GAMEPLAY_SYSTEM_PROMPT

    # 1) 解析知识库（公共方法已统一文本读取 + 图片 base64 抽取）
    kb = resolve_kb(kb_refs)

    # 2) 拼 human 文本：仍按原有结构「项目设定 / 相关知识库摘要 / 本次需求」
    user_text = (
        f"【项目设定】\n{project_brief or '（未提供项目设定）'}\n\n"
        f"【相关知识库参考】\n{kb.text or '（本次未引用知识库）'}\n\n"
        f"【本次需求】\n{user_input}"
    )

    # 3) 构造 messages：vision provider 自动注入 base64 图片，其它 provider 走纯文本
    messages = build_messages(
        system=system_prompt,
        user_text=user_text,
        kb=kb,
        model_id=model_id,
    )

    # 4) temperature 给一个偏低值让结构稳定；复杂创意场景由调用方覆盖
    model = get_chat_model(model_id, temperature=0.4)

    # 5) langchain 0.3 的统一异步流：每个 chunk 是 AIMessageChunk
    async for chunk in model.astream(messages):
        text = extract_text(chunk)
        if text:
            yield text
