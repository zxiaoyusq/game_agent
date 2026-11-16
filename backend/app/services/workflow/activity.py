"""把持久运行日志投影为网页活动记录，不重放模型或复制图片/推理负载。"""

RUN_FIELDS = ("id", "stage", "status", "created_at", "updated_at", "summary", "error", "model",
              "provider", "attempt", "interrupts", "artifacts", "skill_paths", "autonomous")
TOOL_ARGUMENT_FIELDS = ("file_path", "path", "member", "destination", "command", "pattern", "query", "directory", "output_path", "todos")
EVENT_DATA_FIELDS = ("path", "member", "command", "exit_code", "error", "count", "url", "model", "provider", "call_id", "tool", "arguments")


def public_text(content) -> str:
    """仅取面向用户的正文，忽略多模态字节与供应商推理块。"""
    if isinstance(content, str):
        return content[:16000]
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict)
                         and block.get("type") in {"text", "output_text"} and isinstance(block.get("text"), str))[:16000]
    return ""


def activity_run(run: dict) -> dict:
    """保留工具调用 ID 配对及中断问题；冻结输入、原始大结果仍在详情接口。"""
    result = {key: run[key] for key in RUN_FIELDS if key in run}
    result["events"] = []
    for event in run.get("events", []):
        kind = event["type"]
        data = event.get("data") or {}
        visible = {key: data[key] for key in EVENT_DATA_FIELDS if key in data}
        if kind == "graph_update":
            message = data.get("message", {})
            if not isinstance(message, dict) or message.get("type") not in {"ai", "tool"}:
                continue
            visible = {"message": {key: message[key] for key in ("id", "type", "name", "status", "tool_call_id") if key in message}}
            text = public_text(message.get("content"))
            # 工具正文常含整份源文件，活动台保留摘要，完整结果仍可在详情查看。
            limit = 1800 if message.get("type") == "tool" else 16000
            visible["message"]["content"] = text[:limit] + ("\n…完整结果请在项目详情查看。" if len(text) > limit else "")
            calls = []
            for call in message.get("tool_calls", []):
                arguments = call.get("args") or {}
                calls.append({"id": call.get("id"), "name": call.get("name"), "args": {
                    key: (value[:1000] if isinstance(value, str) else value)
                    for key, value in arguments.items() if key in TOOL_ARGUMENT_FIELDS}})
            visible["message"]["tool_calls"] = calls
        elif kind == "autonomous_decision":
            # 独立展示 AI 的取舍及依据，不把它渲染成用户补充或阶段通过。
            visible = {key: data[key] for key in ("question", "context", "options", "decision", "reason", "source") if key in data}
        elif kind == "model_completed":
            # 正文由 graph_update 展示一次；此事件只用于结束“正在分析”状态。
            visible = {key: data[key] for key in ("model", "provider", "call_id") if key in data}
        elif kind in {"validation_completed", "tool_error"}:
            visible["output"] = public_text(data.get("output") or data.get("stdout") or "")[-4000:]
        result["events"].append({**{key: event[key] for key in ("seq", "time", "type", "message")}, "data": visible})
    return result
