"""通过官方 Codex CLI 复用现有登录，适配 LangChain 工具调用协议。

Codex 只负责推理和产生结构化工具请求；工具由 DeepAgents 执行。
本模块不读取登录令牌、不调用私有接口、不修改全局 Codex 配置。
"""

import asyncio
import json
import os
import signal
import tempfile
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field


async def stop_process(process: asyncio.subprocess.Process) -> None:
    """取消时结束整个进程组，避免遗留 CLI 或其启动的子进程。"""
    group = process.pid
    try:
        os.killpg(group, signal.SIGTERM)
    except ProcessLookupError:
        await process.wait()
        return
    # leader 退出不代表进程组清空；孙进程可以忽略 TERM 或关闭标准流继续运行。
    deadline = asyncio.get_running_loop().time() + 3
    while asyncio.get_running_loop().time() < deadline:
        try:
            os.killpg(group, 0)
        except ProcessLookupError:
            await process.wait()
            return
        await asyncio.sleep(0.1)
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await process.wait()


async def inspect_runtime() -> dict:
    """使用公开的 app-server model/list 查询真实模型列表，绝不猜测别名。"""
    login = await asyncio.create_subprocess_exec(
        "codex", "login", "status", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    try:
        out, err = await asyncio.wait_for(login.communicate(), 15)
    finally:
        await stop_process(login)
    login_text = (out + err).decode(errors="replace").strip()
    process = await asyncio.create_subprocess_exec(
        "codex", "app-server", "--stdio", stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, start_new_session=True,
    )
    async def request(identifier: int, method: str, params: dict) -> dict:
        process.stdin.write((json.dumps({"id": identifier, "method": method, "params": params}) + "\n").encode())
        await process.stdin.drain()
        deadline = asyncio.get_running_loop().time() + 30
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError("Codex 模型列表请求超时")
            line = await asyncio.wait_for(process.stdout.readline(), remaining)
            if not line:
                raise RuntimeError("Codex 模型列表通道提前关闭")
            value = json.loads(line)
            if value.get("id") == identifier:
                if "error" in value:
                    raise RuntimeError(str(value["error"]))
                return value["result"]
    try:
        await request(1, "initialize", {"clientInfo": {"name": "game-agent-workflow", "version": "1.0"}})
        process.stdin.write(b'{"method":"initialized"}\n')
        result = await request(2, "model/list", {"includeHidden": True})
        models = [{"id": item["model"], "name": item["displayName"]} for item in result["data"]]
        return {"provider": "codex-login", "model": "gpt-6.1-sol", "logged_in": login.returncode == 0,
                "login_status": login_text, "available": login.returncode == 0 and any(m["id"] == "gpt-6.1-sol" for m in models),
                "models": models, "framework": "deepagents", "transport": "codex exec --output-schema"}
    finally:
        await stop_process(process)


class CodexChatModel(BaseChatModel):
    """把 Codex 的 JSON 最终答复转为 DeepAgents 原生 AIMessage/tool_calls。"""

    model_name: str = "gpt-6.1-sol"
    tool_definitions: list[dict] = Field(default_factory=list)
    event_callback: Any = Field(default=None, exclude=True)
    timeout_seconds: int = 600

    @property
    def _llm_type(self) -> str:
        return "codex-login"

    @property
    def _identifying_params(self) -> dict:
        return {"model_name": self.model_name, "provider": "codex-login"}

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        """保留框架提供的完整工具参数定义，交由模型决定调用。"""
        return self.model_copy(update={"tool_definitions": [convert_to_openai_tool(tool) for tool in tools]})

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise RuntimeError("Codex 工作流只支持异步调用，请使用 ainvoke/astream")

    async def _agenerate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs):
        names = {item["function"]["name"] for item in self.tool_definitions}
        schema = {
            "type": "object", "additionalProperties": False,
            "properties": {
                "content": {"type": "string"},
                "tool_calls": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"name": {"type": "string", "enum": sorted(names) or ["none"]},
                                   "arguments": {"type": "string"}},
                    "required": ["name", "arguments"],
                }},
            }, "required": ["content", "tool_calls"],
        }
        history = [item.model_dump(include={"type", "content", "tool_calls", "tool_call_id", "name"}, mode="json") for item in messages]
        prompt = (
            "你是 DeepAgents 图内的模型推理层。下面 conversation 是当前完整消息，tools 是图可以执行的工具。"
            "只生成符合 schema 的 JSON；禁止使用 Codex 自带工具、终端、网络和文件操作。"
            "需要操作文件或执行验证时，返回 tool_calls 交给 DeepAgents 执行。"
            "arguments 必须是合法 JSON 对象的字符串，参数严格遵循工具定义。"
            "收到工具结果后继续推理，全部工作完成时 tool_calls 置空，content 给出中文结论。"
            "不得声称执行了未调用的工具，不得伪造文件、测试、图片或模型结果。\n"
            + json.dumps({"tools": self.tool_definitions, "conversation": history}, ensure_ascii=False)
        )
        if self.event_callback:
            self.event_callback("model_started", "开始真实 Codex 模型推理", {"model": self.model_name, "messages": len(history)})
        with tempfile.TemporaryDirectory(prefix="game-agent-model-") as temporary:
            folder = Path(temporary)
            (folder / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
            # 独立只读目录与关闭用户配置避免继承项目工具；身份仍由官方 CLI 自己读取。
            process = await asyncio.create_subprocess_exec(
                "codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "-m", self.model_name, "-s", "read-only", "--json", "--output-schema", str(folder / "schema.json"),
                "-o", str(folder / "response.json"), "-C", temporary, "-",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(prompt.encode()), self.timeout_seconds)
                if process.returncode:
                    raise RuntimeError("Codex 模型调用失败：" + stderr.decode(errors="replace")[-2000:])
                result = json.loads((folder / "response.json").read_text(encoding="utf-8"))
                native_events = [json.loads(line) for line in stdout.decode(errors="replace").splitlines() if line.startswith("{")]
                # 推理桥不能偷偷使用另一套工具绕开 DeepAgents 的工作区边界。
                for event in native_events:
                    item = event.get("item", {})
                    if item.get("type") in {"command_execution", "file_change", "mcp_tool_call", "web_search"}:
                        raise RuntimeError("Codex 推理层越过工具边界，本次结果已拒绝")
            finally:
                await stop_process(process)
        calls = []
        for index, call in enumerate(result["tool_calls"]):
            arguments = json.loads(call["arguments"])
            if call["name"] not in names or not isinstance(arguments, dict):
                raise RuntimeError("模型返回了未知工具或非法参数")
            calls.append({"name": call["name"], "args": arguments, "id": f"call_{os.urandom(6).hex()}_{index}", "type": "tool_call"})
        if self.event_callback:
            self.event_callback("model_completed", "Codex 真实推理完成", {"content": result["content"], "tool_calls": calls,
                                "usage": [event for event in native_events if event.get("type") == "turn.completed"]})
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=result["content"], tool_calls=calls))])
