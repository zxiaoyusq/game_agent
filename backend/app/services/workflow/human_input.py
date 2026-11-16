"""按冻结的执行模式提供人工提问或 AI 自主决策，不混淆两种回答来源。"""

import json

from langchain_core.tools import tool
from langgraph.types import interrupt


def _validate_question(question: str, context: str, options: list[str] | None) -> None:
    """两种执行模式使用相同输入边界，防止无意义问题或过长内容进入记录。"""
    if not question.strip() or len(question) > 2000 or len(context) > 4000:
        raise ValueError("问题不能为空，问题及说明分别最多 2000、4000 字")
    if options and (len(options) > 8 or any(len(item) > 500 for item in options)):
        raise ValueError("候选项最多 8 项，每项最多 500 字")


@tool
def request_user_input(question: str, context: str = "", options: list[str] | None = None) -> str:
    """关键信息缺失、需求冲突或重大取舍时暂停并询问用户。question 为完整中文问题，context 解释影响，options 可提供候选项；用户可自由回答。不要询问可自行决定的常规实现细节。"""
    _validate_question(question, context, options)
    # LangGraph 恢复时会重进工具；interrupt 之前必须保持纯计算，避免重复执行。
    answer = interrupt({"kind": "clarification", "question": question, "context": context, "options": options or []})
    return json.dumps({"用户补充": answer}, ensure_ascii=False)


def create_user_input_tool(run: dict, emit):
    """工具随运行冻结，恢复旧运行时不因项目设置变化而跳过原有人工问题。"""
    if run.get("autonomous") is not True:
        return request_user_input

    @tool("request_user_input")
    def decide_autonomously(question: str, context: str = "", options: list[str] | None = None,
                            decision: str = "", reason: str = "") -> str:
        """自主模式下记录 AI 对需求缺口或重大取舍的决定，不询问用户、不暂停流程。question 描述问题，context/options 描述背景和候选；decision 必须是你结合项目需求自行选定的方案，reason 说明依据。不得编造用户确认，也不得总选第一项；记录后继续执行。"""
        _validate_question(question, context, options)
        if len(decision) > 4000 or len(reason) > 4000:
            raise ValueError("自主决定及理由分别最多 4000 字")
        if not decision.strip() or not reason.strip():
            # 兼容模型先发出普通提问的情况，将决策交回同一主模型，不能硬编码默认答案。
            return json.dumps({"status": "decision_required", "source": "ai", "message":
                "用户已开启 AI 自主决策。此问题不会发给用户；请结合已确认需求、参考资料和当前工具结果，"
                "自行选择合理方案，再调用本工具填写 decision 和 reason。当前尚未记录决定，不得视为用户已回答。"}, ensure_ascii=False)
        record = {"question": question.strip(), "context": context, "options": options or [],
                  "decision": decision.strip(), "reason": reason.strip(), "source": "ai"}
        emit("autonomous_decision", "AI 已自主决策", record)
        return json.dumps({"status": "decided", **record}, ensure_ascii=False)

    return decide_autonomously


def pending_interrupts(state) -> list[dict]:
    """从持久检查点读取问题，而非解析模型自然语言来猜测是否需要用户输入。"""
    return [{"id": item.id, "value": item.value}
            for task in getattr(state, "tasks", ()) for item in task.interrupts]
