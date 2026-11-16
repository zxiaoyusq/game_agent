"""API模型工作流回归：仅替代HTTP响应，真实建图、工具、回调与归档均照常执行。

所有凭据与响应都在测试内构造，既不读取.env，也不连接外部模型服务。
"""

import asyncio
import base64
import hashlib
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app import config
from app.providers import LLMConfigError, llm
from app.services.workflow import engine, model_runtime
from app.services.workflow.model_messages import adapt_response_history, adapt_tool_image_messages
from app.services.workflow.validation import written_file_evidence


MODEL_ID = "gpt-6.1-sol"
TEST_KEY = "workflow-unit-test-placeholder"


def completion(content: str = "", calls: list | None = None, number: int = 1) -> dict:
    """构造OpenAI兼容响应，工具参数仍由正式ChatOpenAI解析。"""
    message = {"role": "assistant", "content": content}
    if calls:
        message["tool_calls"] = calls
    return {
        "id": f"chatcmpl-workflow-test-{number}", "object": "chat.completion", "created": 1,
        "model": MODEL_ID,
        "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls" if calls else "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def tool_call(identifier: str, name: str, arguments: dict) -> dict:
    return {"id": identifier, "type": "function", "function": {
        "name": name, "arguments": json.dumps(arguments, ensure_ascii=False),
    }}


class ApiMessageAdapterTests(unittest.TestCase):
    """消息副本转换不能破坏工具批次配对或检查点中已有的工具证据。"""

    def test_stateless_history_keeps_encrypted_reasoning_and_original_evidence(self):
        message = AIMessage(content=[
            {"type": "reasoning", "id": "rs-external", "summary": [], "encrypted_content": "opaque-fixture"},
            {"type": "reasoning", "id": "rs-only-reference", "summary": []},
            {"type": "text", "text": "已经读到规则", "id": "msg-external"},
            {"type": "function_call", "id": "fc-external", "call_id": "call-local"},
        ], tool_calls=[{"id": "call-local", "name": "read_file", "args": {"file_path": "/rules.md"}}])
        before = message.model_dump()
        adapted = adapt_response_history([message])[0]
        self.assertEqual(message.model_dump(), before)
        self.assertEqual(adapted.content, [
            {"type": "reasoning", "summary": [], "encrypted_content": "opaque-fixture"},
            {"type": "text", "text": "已经读到规则"},
        ])
        self.assertEqual(adapted.tool_calls, message.tool_calls)

    def test_text_messages_are_returned_unchanged(self):
        messages = [HumanMessage(content="读取说明"), AIMessage(content="", tool_calls=[{
            "id": "read-text", "name": "read_file", "args": {"file_path": "/notes.txt"},
        }]), ToolMessage(content="纯文本结果", tool_call_id="read-text")]
        self.assertIs(adapt_tool_image_messages(messages), messages)

    def test_multiple_images_wait_for_all_tool_responses(self):
        images = [{"type": "image", "base64": base64.b64encode(value).decode(), "mime_type": "image/png"}
                  for value in (b"first-test-image", b"second-test-image")]
        messages = [
            AIMessage(content="", tool_calls=[{"id": identifier, "name": "read_file", "args": {}}
                                              for identifier in ("image-a", "image-b", "text-c")]),
            ToolMessage(content=[{"type": "text", "text": "保留原图说明"}, images[0]], tool_call_id="image-a"),
            ToolMessage(content=[images[1]], tool_call_id="image-b"),
            ToolMessage(content="仍然保留文本工具响应", tool_call_id="text-c"),
            AIMessage(content="下一轮历史总结"),
        ]
        original = [item.model_dump() for item in messages]
        adapted = adapt_tool_image_messages(messages)
        self.assertEqual([item.type for item in adapted], ["ai", "tool", "tool", "tool", "human", "ai"])
        self.assertEqual([item.tool_call_id for item in adapted if isinstance(item, ToolMessage)],
                         ["image-a", "image-b", "text-c"])
        self.assertEqual([block for block in adapted[4].content if block["type"] == "image"], images)
        self.assertEqual(adapted[1].content[0], {"type": "text", "text": "保留原图说明"})
        self.assertIs(adapted[3], messages[3])
        self.assertEqual([item.model_dump() for item in messages], original)
        self.assertTrue(all(block["type"] == "text" for item in adapted if isinstance(item, ToolMessage)
                            and isinstance(item.content, list) for block in item.content))

    def test_incomplete_image_batch_is_not_sent(self):
        messages = [AIMessage(content="", tool_calls=[{"id": identifier, "name": "read_file", "args": {}}
                                                      for identifier in ("image-a", "text-b")]),
                    ToolMessage(content=[{"type": "image", "base64": "eA==", "mime_type": "image/png"}],
                                tool_call_id="image-a")]
        with self.assertRaisesRegex(ValueError, "缺少响应"):
            adapt_tool_image_messages(messages)


class ApiModelWorkflowTests(unittest.IsolatedAsyncioTestCase):
    """隔离工作区和HTTP出口，验证新模型来源不会借用Codex登录。"""

    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.requests = []
        self.response_handler = lambda payload: httpx.Response(200, json=completion("测试响应"))
        self.http_client = httpx.Client(transport=httpx.MockTransport(self.dispatch_request))
        self.async_client = httpx.AsyncClient(transport=httpx.MockTransport(self.dispatch_request))
        self.patches = ExitStack()
        for target, name, value in [
            (engine, "ROOT", self.root), (engine, "STORE", self.root / "state"),
            (engine, "KNOWLEDGE_DIR", self.root / "knowledge"),
            (config, "LLM_API_KEY", TEST_KEY), (llm, "LLM_API_KEY", TEST_KEY),
            (config, "LLM_OPENAI_API", "chat-completions"),
            (config, "get_llm_base_url", lambda provider: "https://workflow-test.invalid/v1"),
            (llm, "get_llm_base_url", lambda provider: "https://workflow-test.invalid/v1"),
            (model_runtime, "get_chat_model", self.create_test_model),
        ]:
            self.patches.enter_context(patch.object(target, name, value))
        # API路径不允许调用登录探测或登录模型，即使API缺配置或拒绝请求。
        self.codex_probe = self.patches.enter_context(patch.object(
            engine, "inspect_runtime", AsyncMock(side_effect=AssertionError("API路径不能探测Codex登录")),
        ))
        self.codex_model = self.patches.enter_context(patch.object(
            engine, "CodexChatModel", side_effect=AssertionError("API路径不能创建Codex登录模型"),
        ))
        llm._build_cached.cache_clear()

    async def asyncTearDown(self):
        tasks = list(engine.WORKERS.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        engine.WORKERS.clear()
        llm._build_cached.cache_clear()
        self.patches.close()
        await self.async_client.aclose()
        self.http_client.close()
        self.temporary.cleanup()

    def dispatch_request(self, request: httpx.Request) -> httpx.Response:
        """所有HTTP仅到内存传输层；校验网关身份而不输出凭据。"""
        self.assertEqual(request.url.host, "workflow-test.invalid")
        self.assertEqual(request.headers["authorization"], f"Bearer {TEST_KEY}")
        payload = json.loads(request.content)
        self.assertEqual(payload["model"], MODEL_ID)
        self.assertFalse(payload.get("stream", False))
        self.requests.append(payload)
        return self.response_handler(payload)

    def create_test_model(self, model_id: str, **options):
        """复用生产工厂与缓存，仅显式替换HTTP客户端以封闭网络。"""
        return llm.get_chat_model(model_id, http_client=self.http_client,
                                  http_async_client=self.async_client, http_socket_options=(), **options)

    def create_project(self):
        return engine.create_project("API链路测试", "验证真实工具执行", None, [],
                                     model_provider="api-key", model_id=MODEL_ID)

    async def finish_run(self, project: dict) -> dict:
        run = engine.start_run(project["id"], "prototype", skill_mode="manual")
        worker = engine.WORKERS[run["id"]]
        await worker
        return engine.load("runs", run["id"])

    def assert_no_codex_fallback(self):
        self.codex_probe.assert_not_called()
        self.codex_model.assert_not_called()

    async def test_gemini_uses_chat_completions_even_when_gpt_uses_responses(self):
        """用真实 SDK 验证协议隔离、网关凭据和工具调用解析，避免 Gemini 误发 Responses。"""
        model_id = "gemini-3.8-flash"
        requests = []

        def respond(request):
            self.assertEqual(request.url.host, "workflow-test.invalid")
            self.assertEqual(request.url.path, "/v1/chat/completions")
            self.assertEqual(request.headers["authorization"], f"Bearer {TEST_KEY}")
            payload = json.loads(request.content)
            self.assertEqual(payload["model"], model_id)
            self.assertEqual(payload["tools"][0]["function"]["name"], "report_status")
            requests.append(payload)
            response = completion(calls=[tool_call("status-ok", "report_status", {"status": "ok"})])
            response["model"] = model_id
            return httpx.Response(200, json=response)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as async_client:
            with httpx.Client(transport=httpx.MockTransport(respond)) as client:
                def create_model(identifier, **options):
                    return llm.get_chat_model(identifier, http_client=client, http_async_client=async_client,
                                              http_socket_options=(), **options)

                with patch.object(config, "LLM_OPENAI_API", "responses"), \
                     patch.object(model_runtime, "get_chat_model", create_model):
                    runtime = await model_runtime.inspect_runtime("api-key", model_id)
                    self.assertIn("chat-completions", runtime["transport"])
                    model = model_runtime.create_api_model(model_id, lambda *args: None)
                    tool = {"name": "report_status", "description": "报告状态", "parameters": {
                        "type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"],
                    }}
                    response = await model.bind_tools([tool]).ainvoke("报告检查状态")
        self.assertEqual(len(requests), 1)
        self.assertEqual(response.tool_calls[0]["args"], {"status": "ok"})
        self.assert_no_codex_fallback()

    async def test_responses_replays_tools_without_remote_resource_item_ids(self):
        """跨资源网关拒绝旧item引用；完整参数、call_id和本地文件证据必须仍成立。"""
        def scripted_response(payload):
            self.assertFalse(payload["store"])
            self.assertNotIn("previous_response_id", payload)
            self.assertIn("reasoning.encrypted_content", payload["include"])
            self.assertFalse(any(item.get("id") for item in payload["input"]))
            number = len(self.requests)
            if number == 1:
                output = [{"type": "function_call", "id": "fc-remote-resource", "call_id": "call-write",
                           "name": "write_file", "arguments": json.dumps({
                               "file_path": "/workflow/prototype.md", "content": "# Responses真实文件工具验证",
                           }), "status": "completed"}]
            else:
                calls = [item for item in payload["input"] if item.get("type") == "function_call"]
                results = [item for item in payload["input"] if item.get("type") == "function_call_output"]
                self.assertEqual(calls[0]["call_id"], results[0]["call_id"])
                self.assertEqual(calls[0]["name"], "write_file")
                output = [{"type": "message", "id": "msg-another-resource", "role": "assistant", "status": "completed",
                           "content": [{"type": "output_text", "text": "Responses工具验证完成", "annotations": []}]}]
            return httpx.Response(200, json={
                "id": f"resp-fixture-{number}", "object": "response", "created_at": 1, "status": "completed",
                "model": MODEL_ID, "output": output,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                          "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}},
            })

        self.response_handler = scripted_response
        with patch.object(config, "LLM_OPENAI_API", "responses"):
            project = self.create_project()
            run = await self.finish_run(project)
        self.assertEqual(run["status"], "awaiting_confirmation", run["error"])
        self.assertEqual(run["summary"], "Responses工具验证完成")
        self.assertIn("workflow/prototype.md", written_file_evidence(run))
        original = [event["data"]["message"] for event in run["events"]
                    if event["type"] == "graph_update" and event["data"]["message"].get("type") == "ai"]
        self.assertEqual(original[0]["content"][0]["id"], "fc-remote-resource")
        self.assert_no_codex_fallback()

    async def test_native_api_executes_real_tools_and_collects_evidence(self):
        """从引擎入口启动，真实write/edit工具结果必须与模型回调及最终哈希对应。"""
        def scripted_response(payload):
            count = len(self.requests)
            if count == 1:
                calls = [tool_call("write-report", "write_file", {
                    "file_path": "/workflow/prototype.md", "content": "# 原型报告\n\n初始内容",
                })]
            elif count == 2:
                calls = [tool_call("edit-report", "edit_file", {
                    "file_path": "/workflow/prototype.md", "old_string": "初始内容", "new_string": "已验证的更新内容",
                })]
            else:
                calls = None
            return httpx.Response(200, json=completion("" if calls else "真实工具回归完成", calls, count))

        self.response_handler = scripted_response
        project = self.create_project()
        run = await self.finish_run(project)
        self.assertEqual(run["status"], "awaiting_confirmation", run["error"])
        self.assertEqual((run["provider"], run["model"]), ("api-key", MODEL_ID))
        self.assertEqual(run["summary"], "真实工具回归完成")
        self.assertEqual(len(self.requests), 3)
        tool_names = {item["function"]["name"] for item in self.requests[0]["tools"]}
        self.assertTrue({"write_file", "edit_file"}.issubset(tool_names))
        self.assertNotIn("task", tool_names, "应禁用隐式子Agent以保持主图证据链完整")
        report = engine.resolve_workspace(project["workspace"]) / "workflow/prototype.md"
        self.assertEqual(report.read_text(), "# 原型报告\n\n已验证的更新内容")
        digest = hashlib.sha256(report.read_bytes()).hexdigest()
        self.assertEqual(written_file_evidence(run), {"workflow/prototype.md": digest})
        artifact = next(item for item in run["artifacts"] if item["path"] == "workflow/prototype.md")
        self.assertEqual((artifact["provenance"], artifact["sha256"]), ("agent_edit", digest))
        completed = [item["data"] for item in run["events"] if item["type"] == "model_completed"]
        self.assertEqual(len(completed), 3)
        for item in completed:
            self.assertEqual((item["provider"], item["model"], item["response_model"]), ("api-key", MODEL_ID, MODEL_ID))
            self.assertEqual(item["usage"]["total_tokens"], 15)
            self.assertTrue(item["call_id"])
        self.assertEqual(completed[0]["tool_calls"][0]["id"], "write-report")
        self.assertNotIn(TEST_KEY, json.dumps(run, ensure_ascii=False))
        self.assert_no_codex_fallback()

    async def test_cached_client_does_not_mix_concurrent_run_callbacks(self):
        """多个运行可复用HTTP客户端，回调和回复证据仍严格属于各自运行。"""
        records = {"run-a": [], "run-b": []}

        def callback(identifier):
            return lambda kind, message, data: records[identifier].append((kind, data))

        self.response_handler = lambda payload: httpx.Response(
            200, json=completion(payload["messages"][-1]["content"], number=len(self.requests)),
        )
        models = {identifier: model_runtime.create_api_model(MODEL_ID, callback(identifier)) for identifier in records}
        self.assertIsNot(models["run-a"], models["run-b"])
        self.assertIs(models["run-a"].async_client, models["run-b"].async_client)
        self.assertIsNot(models["run-a"].callbacks, models["run-b"].callbacks)
        await asyncio.gather(*(model.ainvoke(identifier) for identifier, model in models.items()))
        for identifier, events in records.items():
            self.assertEqual([kind for kind, _ in events], ["model_started", "model_completed"])
            self.assertEqual(events[-1][1]["content"], identifier)
            self.assertEqual(events[0][1]["call_id"], events[-1][1]["call_id"])
        self.assertNotEqual(records["run-a"][0][1]["call_id"], records["run-b"][0][1]["call_id"])
        self.assert_no_codex_fallback()

    async def test_read_file_image_reaches_next_api_request_as_visual_input(self):
        """真实读取临时PNG，下一轮必须携带视觉内容且符合Chat Completions角色约束。"""
        from PIL import Image

        project = self.create_project()
        workspace = engine.resolve_workspace(project["workspace"])
        image_path = workspace / "reference.png"
        Image.new("RGB", (2, 2), color=(192, 120, 44)).save(image_path)
        (workspace / "reference-note.txt").write_text("参考图说明：测试用色块。", encoding="utf-8")
        image_bytes = image_path.read_bytes()
        visual_inputs = []

        def scripted_response(payload):
            count = len(self.requests)
            if count == 1:
                calls = [tool_call("read-reference", "read_file", {"file_path": "/reference.png"}),
                         tool_call("read-reference-note", "read_file", {"file_path": "/reference-note.txt"})]
            else:
                pending_tools = set()
                for message in payload["messages"]:
                    if message["role"] == "assistant":
                        pending_tools = {item["id"] for item in message.get("tool_calls", [])}
                    elif message["role"] == "tool":
                        pending_tools.discard(message["tool_call_id"])
                    elif message["role"] == "user" and pending_tools:
                        return httpx.Response(400, json={"error": {
                            "message": "全部工具调用响应完成前不能插入用户图片消息",
                            "type": "invalid_request_error",
                        }})
                    content = message.get("content")
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if block.get("type") != "image_url":
                            continue
                        prefix, encoded = block["image_url"]["url"].split(",", 1)
                        # 只保存判定与角色，失败输出也不打印base64正文。
                        visual_inputs.append({"role": message["role"], "png": prefix == "data:image/png;base64",
                                              "bytes_match": base64.b64decode(encoded) == image_bytes})
                        if message["role"] != "user":
                            return httpx.Response(400, json={"error": {
                                "message": "Chat Completions工具消息只接受文本，图片须作为user视觉内容传递",
                                "type": "invalid_request_error",
                            }})
                calls = [tool_call("write-visual-report", "write_file", {
                    "file_path": "/workflow/prototype.md", "content": "# 图片链路测试\n\n已收到真实PNG视觉输入。",
                })] if count == 2 else None
            return httpx.Response(200, json=completion("" if calls else "图片工具链路验证完成", calls, count))

        self.response_handler = scripted_response
        run = await self.finish_run(project)
        self.assertEqual(run["status"], "awaiting_confirmation", run["error"])
        self.assertTrue(visual_inputs, "图片不能被降为文本说明或从请求中丢失")
        self.assertTrue(all(item == {"role": "user", "png": True, "bytes_match": True} for item in visual_inputs))
        read_messages = [event["data"]["message"] for event in run["events"]
                         if event["type"] == "graph_update"
                         and event["data"].get("message", {}).get("tool_call_id") == "read-reference"]
        self.assertEqual(len(read_messages), 1)
        self.assertEqual(read_messages[0]["status"], "success")
        original_images = [block for block in read_messages[0]["content"] if block.get("type") == "image"]
        self.assertEqual(len(original_images), 1, "图事件必须保留原始图片证据")
        self.assertTrue(base64.b64decode(original_images[0]["base64"]) == image_bytes)
        self.assertEqual(len(self.requests), 3)
        self.assert_no_codex_fallback()

    async def test_runtime_configuration_is_not_a_connection_test(self):
        """有配置只表示允许提交，页面查询不发起计费推理或假报已连通。"""
        runtime = await model_runtime.inspect_runtime("api-key", MODEL_ID)
        self.assertTrue(runtime["configured"])
        self.assertTrue(runtime["available"])
        self.assertFalse(runtime["connection_checked"])
        self.assertEqual((runtime["provider"], runtime["model"]), ("api-key", MODEL_ID))
        self.assertFalse(self.requests)
        self.assertNotIn(TEST_KEY, json.dumps(runtime, ensure_ascii=False))
        self.assert_no_codex_fallback()

    async def test_missing_key_fails_without_login_fallback(self):
        """缺Key的运行保留API来源并明确失败，既不计费也不借用登录身份。"""
        with patch.object(config, "LLM_API_KEY", ""), patch.object(llm, "LLM_API_KEY", ""):
            runtime = await model_runtime.inspect_runtime("api-key", MODEL_ID)
            self.assertFalse(runtime["configured"])
            self.assertFalse(runtime["available"])
            self.assertFalse(runtime["connection_checked"])
            with self.assertRaises(LLMConfigError):
                model_runtime.create_api_model(MODEL_ID, lambda *args: None)
            run = await self.finish_run(self.create_project())
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["provider"], "api-key")
        self.assertIn("LLM_API_KEY", run["error"])
        self.assertFalse(self.requests)
        self.assert_no_codex_fallback()

    async def test_rejected_api_request_redacts_key_and_does_not_fallback(self):
        """上游错误即使回显凭据，运行状态与回调也必须隐藏密钥并保留失败来源。"""
        self.response_handler = lambda payload: httpx.Response(401, json={"error": {
            "message": f"测试拒绝凭据 {TEST_KEY}", "type": "invalid_request_error", "code": "invalid_api_key",
        }})
        run = await self.finish_run(self.create_project())
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["provider"], "api-key")
        self.assertTrue(self.requests)
        self.assertFalse(any(item["type"] == "model_completed" for item in run["events"]))
        model_errors = [item for item in run["events"] if item["type"] == "model_error"]
        self.assertTrue(model_errors)
        self.assertIn("[凭据已隐藏]", run["error"])
        self.assertNotIn(TEST_KEY, json.dumps(run, ensure_ascii=False))
        self.assert_no_codex_fallback()


if __name__ == "__main__":
    unittest.main()
