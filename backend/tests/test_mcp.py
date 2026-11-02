"""通过真实 HTTP MCP 协议验证授权、任务交接和产物；模型执行仅在测试中隔离。"""

import asyncio
import hashlib
import json
import os
import shlex
import socket
import tempfile
import unittest
from contextlib import AsyncExitStack
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import httpx2
import uvicorn
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app import main
from app.mcp.auth import MCPSettings, load_settings
from app.mcp.configure import add_client
from app.services import knowledge, production_library
from app.services.workflow import engine
from app.services.workflow.codex_model import CodexChatModel


class MCPTests(unittest.IsolatedAsyncioTestCase):
    """客户端经主应用路由和认证调用工具，不绕过 HTTP 中间件直接调用 Python 函数。"""

    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        for target, name, value in (
            (engine, "ROOT", self.root), (engine, "STORE", self.root / "state"),
            (engine, "KNOWLEDGE_DIR", self.root / "knowledge"),
            (knowledge, "KNOWLEDGE_DIR", self.root / "knowledge"),
        ):
            self.stack.enter_context(patch.object(target, name, value))
        self.stack.enter_context(patch.object(main, "import_skill_library", return_value={}))
        self.stack.enter_context(patch.object(main, "import_production_library", return_value={}))
        # 真实导入小型品类和框架资料；不会导入公司的大型 Skill 附件。
        production_library.import_production_library()
        self.project = engine.create_project("授权项目", "", "games/demo", [])
        self.other_project = engine.create_project("其他项目", "", "games/other", [])
        self.token = "mcp-test-token-only-01234567890123456789"
        self.restricted_token = "restricted-test-token-01234567890123456789"
        self.config = self.root / "clients.json"
        self.config.write_text(json.dumps({
            "public_url": "http://127.0.0.1:8003/mcp",
            "clients": [
                {"client_id": "admin", "token_sha256": hashlib.sha256(self.token.encode()).hexdigest(),
                 "project_ids": ["*"], "can_create_projects": True},
                {"client_id": "limited", "token_sha256": hashlib.sha256(self.restricted_token.encode()).hexdigest(),
                 "project_ids": [self.other_project["id"]]},
            ],
        }), encoding="utf-8")
        self.stack.enter_context(patch.dict(os.environ, {"GAME_MCP_CONFIG": str(self.config)}))
        self.app = main.create_app()
        await self.stack.enter_async_context(run_asgi_lifespan(self.app))
        self.real_execute = engine.execute_run
        self.stack.enter_context(patch.object(engine, "execute_run", self.hold_execution))

    async def asyncTearDown(self):
        # 生命周期先关闭会话和后台任务，再撤销路径替换，避免误触真实工程状态。
        await self.stack.aclose()
        engine.WORKERS.clear()
        self.temporary.cleanup()

    async def hold_execution(self, *args, **kwargs):
        """隔离付费模型调用；任务创建、状态、取消和产物操作均走真实服务代码。"""
        await asyncio.Event().wait()

    def client(self, token=None):
        """使用 FastMCP 提供的流式 ASGI 传输执行完整握手和 HTTP 工具请求。"""
        def http_client_factory(**kwargs):
            return httpx2.AsyncClient(transport=StreamingASGITransport(self.app), **kwargs)

        return Client(StreamableHttpTransport(
            "http://testserver/mcp/", headers={"Authorization": f"Bearer {token or self.token}"},
            httpx_client_factory=http_client_factory,
        ))

    async def call(self, client, tool_name, **arguments):
        result = await client.call_tool(tool_name, arguments)
        return result.data

    async def start(self, client, request_id="run-1"):
        return await self.call(client, "start_stage", project_id=self.project["id"], stage="prototype", request_id=request_id)

    async def test_tool_discovery_submission_retry_and_reconnection(self):
        async with self.client() as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            self.assertIn("start_stage", tools)
            self.assertNotIn("confirm_stage", tools)
            self.assertTrue(tools["get_run"].annotations.read_only_hint)
            schema = tools["start_stage"].input_schema
            self.assertIn("request_id", schema["required"])
            self.assertEqual(schema["properties"]["stage"]["enum"], ["prototype", "art", "code", "test"])
            first, duplicate = await asyncio.gather(self.start(client), self.start(client))
            self.assertEqual(first["id"], duplicate["id"])
            self.assertEqual(len(engine.project_runs(self.project["id"])), 1)
            self.assertEqual(len(engine.WORKERS), 1)
            self.assertNotIn("events", first)
            self.assertNotIn("production_profile", first)
        # 关闭 MCP 客户端不应结束执行器创建的任务。
        self.assertFalse(engine.WORKERS[first["id"]].done())
        async with self.client() as client:
            state = await self.call(client, "get_run", run_id=first["id"])
            self.assertEqual(state["id"], first["id"])
            conflict = await client.call_tool("start_stage", {
                "project_id": self.project["id"], "stage": "prototype", "request_id": "run-1", "prompt": "不同任务",
            }, raise_on_error=False)
            self.assertTrue(conflict.is_error)
            self.assertIn("不同参数", conflict.content[0].text)

    async def test_project_creation_is_idempotent_and_requires_permission(self):
        async with self.client() as client:
            first = await self.call(client, "create_project", request_id="project-1", name="远程项目", framework_id="canvas-web")
            duplicate = await self.call(client, "create_project", request_id="project-1", name="远程项目", framework_id="canvas-web")
            self.assertEqual(first["id"], duplicate["id"])
            self.assertEqual(first["framework_id"], "canvas-web")
            self.assertNotIn("workspace", first)
        async with self.client(self.restricted_token) as client:
            result = await client.call_tool("create_project", {"request_id": "project-1", "name": "越权项目"}, raise_on_error=False)
            self.assertTrue(result.is_error)
            projects = await self.call(client, "list_projects")
            self.assertEqual([item["id"] for item in projects["items"]], [self.other_project["id"]])

    async def test_project_permissions_cover_every_run_and_artifact_operation(self):
        async with self.client() as client:
            run = await self.start(client)
        async with self.client(self.restricted_token) as client:
            operations = {
                "get_project": {"project_id": self.project["id"]},
                "start_stage": {"project_id": self.project["id"], "stage": "prototype", "request_id": "unauthorized"},
                "get_run": {"run_id": run["id"]},
                "get_run_events": {"run_id": run["id"]},
                "cancel_run": {"run_id": run["id"]},
                "resume_run": {"run_id": run["id"], "request_id": "unauthorized"},
                "list_artifacts": {"run_id": run["id"]},
                "read_artifact": {"run_id": run["id"], "artifact_id": "unknown"},
            }
            for name, arguments in operations.items():
                with self.subTest(tool=name):
                    result = await client.call_tool(name, arguments, raise_on_error=False)
                    self.assertTrue(result.is_error)
                    self.assertIn("无权", result.content[0].text)
        self.assertEqual(engine.load("runs", run["id"])["status"], "queued")

    async def test_cancellation_resume_retry_and_durable_submission(self):
        async with self.client() as client:
            run = await self.start(client)
            cancelled = await self.call(client, "cancel_run", run_id=run["id"])
            self.assertEqual(cancelled["status"], "cancelled")
            again = await self.call(client, "cancel_run", run_id=run["id"])
            self.assertEqual(again, cancelled)
            resumed = await self.call(client, "resume_run", run_id=run["id"], request_id="resume-1")
            duplicate = await self.call(client, "resume_run", run_id=run["id"], request_id="resume-1")
            self.assertEqual(resumed["attempt"], 2)
            self.assertEqual(resumed, duplicate)
            await engine.shutdown_workers()
            engine.WORKERS.clear()
            engine.recover_interrupted_runs()
            replay = await self.start(client)
            self.assertEqual(replay["id"], run["id"])
            self.assertEqual(replay["status"], "interrupted")
            self.assertEqual(engine.WORKERS, {})
            # 原恢复请求只返回已中断状态；真正恢复需要新的操作标识。
            same_resume = await self.call(client, "resume_run", run_id=run["id"], request_id="resume-1")
            self.assertEqual(same_resume["status"], "interrupted")
            next_resume = await self.call(client, "resume_run", run_id=run["id"], request_id="resume-2")
            self.assertEqual(next_resume["attempt"], 3)

    async def test_bounded_events_and_input_validation(self):
        async with self.client() as client:
            run = await self.start(client)
            for index in range(3):
                engine.event(run["id"], "test", "进度" * 1000, {"private_context": "不应返回完整上下文"})
            first = await self.call(client, "get_run_events", run_id=run["id"], limit=2)
            second = await self.call(client, "get_run_events", run_id=run["id"], after=first["next_cursor"], limit=2)
            self.assertTrue(first["has_more"])
            self.assertFalse(second["has_more"])
            self.assertEqual([item["seq"] for item in first["events"] + second["events"]], [1, 2, 3, 4])
            self.assertLessEqual(len(second["events"][0]["message"]), 1000)
            self.assertNotIn("data", second["events"][0])
            for arguments in ({"run_id": run["id"], "limit": 51}, {"run_id": "../../private"}):
                result = await client.call_tool("get_run_events", arguments, raise_on_error=False)
                self.assertTrue(result.is_error)

    async def test_artifact_read_download_auth_and_integrity(self):
        async with self.client() as client:
            run = await self.start(client)
            await self.call(client, "cancel_run", run_id=run["id"])
            workspace = engine.resolve_workspace(self.project["workspace"])
            report = workspace / "workflow" / "prototype.md"
            report.parent.mkdir(parents=True)
            report.write_text("# 测试报告\n\n" + "中文产物" * 20, encoding="utf-8")
            artifacts = engine.collect_artifacts(run["id"], workspace, {})
            engine.set_status(run["id"], "awaiting_confirmation", artifacts=artifacts)
            artifact = artifacts[0]
            result = await self.call(client, "read_artifact", run_id=run["id"], artifact_id=artifact["id"], limit=9)
            following = await self.call(client, "read_artifact", run_id=run["id"], artifact_id=artifact["id"], offset=result["next_offset"])
            self.assertEqual(result["text"] + following["text"], report.read_text(encoding="utf-8"))
            self.assertNotIn("/api/", result["download_url"])
            self.assertTrue((await self.call(client, "get_run", run_id=run["id"]))["requires_confirmation"])
            blocked = await client.call_tool("start_stage", {
                "project_id": self.project["id"], "stage": "art", "request_id": "too-early",
            }, raise_on_error=False)
            self.assertTrue(blocked.is_error)
            url = f"/mcp/artifacts/{run['id']}/{artifact['id']}"
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as http:
                self.assertEqual((await http.get(url)).status_code, 401)
                self.assertEqual((await http.get(url, headers={"Authorization": f"Bearer {self.restricted_token}"})).status_code, 403)
                download = await http.get(url, headers={"Authorization": f"Bearer {self.token}"})
                self.assertEqual(download.status_code, 200)
                self.assertEqual(download.content, report.read_bytes())
                self.assertTrue(download.headers["content-disposition"].startswith("attachment"))
                engine.artifact_file(run["id"], artifact["id"]).write_text("篡改", encoding="utf-8")
                self.assertEqual((await http.get(url, headers={"Authorization": f"Bearer {self.token}"})).status_code, 409)
            invalid = await client.call_tool("read_artifact", {"run_id": run["id"], "artifact_id": artifact["id"]}, raise_on_error=False)
            self.assertTrue(invalid.is_error)

    async def test_missing_invalid_tokens_and_disabled_configuration(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as http:
            for headers in ({}, {"Authorization": "Bearer invalid"}):
                response = await http.post("/mcp/", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                self.assertEqual(response.status_code, 401)
        with patch.dict(os.environ, {"GAME_MCP_CONFIG": ""}):
            disabled = main.create_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=disabled), base_url="http://testserver") as http:
            self.assertEqual((await http.post("/mcp/")).status_code, 404)
            self.assertEqual((await http.get("/api/health")).status_code, 200)
        self.config.write_text('{"clients": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "MCP 配置"):
            load_settings(self.config)

    async def test_real_deepagent_writes_report_through_mcp_submission(self):
        """真实建图、文件工具、SQLite 和归档闭环；仅模型答复与登录检查使用测试替身。"""
        async def scripted_inference(model, messages, **kwargs):
            if any(isinstance(message, ToolMessage) and message.name == "write_file" for message in messages):
                response = AIMessage(content="已写入本测试的原型报告，等待人工确认。")
            else:
                response = AIMessage(content="", tool_calls=[{
                    "name": "write_file", "id": "test-report", "args": {
                        "file_path": "/workflow/prototype.md", "content": "# MCP 链路测试\n\n由测试模型驱动真实文件工具写入。",
                    },
                }])
            # 保留正式模型适配器的事件契约，让归档能关联请求、工具结果与文件哈希。
            model.event_callback("model_completed", "测试模型返回结构化结果", {"tool_calls": response.tool_calls})
            return ChatResult(generations=[ChatGeneration(message=response)])

        with patch.object(engine, "execute_run", self.real_execute), \
             patch.object(engine, "inspect_runtime", AsyncMock(return_value={"available": True})), \
             patch.object(CodexChatModel, "_agenerate", scripted_inference):
            async with self.client() as client:
                run = await self.start(client)
                worker = engine.WORKERS.get(run["id"])
                if worker:
                    await asyncio.wait_for(worker, 15)
                result = await self.call(client, "get_run", run_id=run["id"])
                self.assertEqual(result["status"], "awaiting_confirmation", result.get("error"))
                artifacts = await self.call(client, "list_artifacts", run_id=run["id"])
                report = next(item for item in artifacts["items"] if item["path"] == "workflow/prototype.md")
                self.assertEqual(report["provenance"], "agent_edit")
                content = await self.call(client, "read_artifact", run_id=run["id"], artifact_id=report["id"])
                self.assertIn("MCP 链路测试", content["text"])
                self.assertTrue((engine.STORE / "checkpoints.sqlite").is_file())

    async def test_real_tcp_transport(self):
        """再通过本机 TCP 验证一次真实 HTTP 传输，避免测试仅适用于内存 ASGI。"""
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(self.app, lifespan="off", log_level="error", ws="none"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            async with asyncio.timeout(10):
                while not server.started:
                    if task.done():
                        await task
                    await asyncio.sleep(0.01)
                async with Client(StreamableHttpTransport(
                    f"http://127.0.0.1:{port}/mcp/", headers={"Authorization": f"Bearer {self.token}"},
                    httpx_client_factory=lambda **kwargs: httpx2.AsyncClient(trust_env=False, **kwargs),
                )) as client:
                    result = await self.call(client, "get_capabilities")
                    self.assertEqual(result["project_ids"], ["*"])
                    self.assertEqual(result["frameworks"][0]["label"], "Cocos · Web / H5")
        finally:
            server.should_exit = True
            await asyncio.wait_for(task, 10)
            listener.close()


class MCPConfigurationTests(unittest.TestCase):
    """启动时拒绝可疑配置，避免拼错字段后意外放宽访问范围。"""

    def test_rejects_duplicate_credentials_insecure_url_and_invalid_project_scope(self):
        client = {"client_id": "test", "token_sha256": "a" * 64, "project_ids": ["*"]}
        for settings in (
            {"clients": [client, client]},
            {"clients": [client], "public_url": "http://remote.example/mcp"},
            {"clients": [{**client, "project_ids": ["../private"]}]},
            {"clients": [{**client, "project_ids": ["project"], "can_create_projects": True}]},
            {"clients": [{**client, "can_create_projects": "false"}]},
        ):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                MCPSettings.model_validate(settings)

    def test_configuration_command_preserves_clients_and_protects_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config, credential = add_client(directory, "first", ["*"], True, "http://127.0.0.1:8003/mcp")
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(credential.stat().st_mode & 0o777, 0o600)
            token = shlex.split(credential.read_text())[0].partition("=")[2]
            self.assertNotIn(token, config.read_text())
            self.assertEqual(load_settings(config).clients[0].token_sha256, hashlib.sha256(token.encode()).hexdigest())
            add_client(directory, "second", ["project"], False, "http://127.0.0.1:8003/mcp")
            original = config.read_text()
            with self.assertRaises(ValueError):
                add_client(directory, "first", ["*"], True, "http://127.0.0.1:8003/mcp")
            self.assertEqual(config.read_text(), original)
            self.assertEqual(len(load_settings(config).clients), 2)
