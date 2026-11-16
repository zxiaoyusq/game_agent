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
from app.services.workflow import engine, model_runtime
from app.services.workflow.codex_model import CodexChatModel
from app.services.workflow.tools import create_workflow_tools


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

    def skill_fixture(self):
        """只创建两个小型入口，验证真实目录发现与冻结，不依赖公司资料或模型。"""
        paths = ["casual-game-production/SKILL.md", "cocos-game-production/SKILL.md"]
        for path in paths:
            target = self.root / "knowledge" / "skill" / "docs" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"---\nname: {target.parent.name}\ndescription: 测试阶段所需的真实技能正文\n"
                'metadata:\n  version: "1.0.0"\n---\n\n# 阶段规范\n\n实际读取本次冻结输入，并记录产物与验证结果。',
                encoding="utf-8",
            )
        return paths

    def routing_project(self, workspace="games/routing", framework="cocos-web"):
        return engine.create_project("技能路由项目", "按选定框架制作分类整理游戏", workspace, [],
                                     genre_id="sorting", framework_id=framework)

    async def test_tool_discovery_submission_retry_and_reconnection(self):
        async with self.client() as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            self.assertIn("start_stage", tools)
            self.assertIn("preview_skill_selection", tools)
            self.assertIn("confirm_stage", tools)
            self.assertIn("run_id", tools["confirm_stage"].input_schema["required"])
            for name in ("list_templates", "get_template", "list_references", "get_reference_upload_info",
                         "start_pipeline", "resume_pipeline", "cancel_pipeline", "get_pending_questions",
                         "answer_questions", "publish_project"):
                self.assertIn(name, tools)
            self.assertTrue(tools["get_run"].annotations.read_only_hint)
            self.assertTrue(tools["preview_skill_selection"].annotations.read_only_hint)
            project_schema = tools["create_project"].input_schema["properties"]
            self.assertEqual(project_schema["model_provider"]["default"], "api-key")
            self.assertEqual(project_schema["model_id"]["default"], "gpt-6.1-sol")
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
            self.assertEqual(first["model_provider"], "api-key")
            self.assertEqual(first["model_id"], "gpt-6.1-sol")
            self.assertNotIn("workspace", first)
            # 不填写模型参数时，项目持久化与后续阶段必须都使用服务器 API 来源。
            self.assertEqual(engine.load("projects", first["id"])["model_provider"], "api-key")
            run = await self.call(client, "start_stage", project_id=first["id"], stage="prototype", request_id="default-api-stage")
            self.assertEqual(run["model_provider"], "api-key")
            self.assertEqual(engine.load("runs", run["id"])["provider"], "api-key")
        async with self.client(self.restricted_token) as client:
            result = await client.call_tool("create_project", {"request_id": "project-1", "name": "越权项目"}, raise_on_error=False)
            self.assertTrue(result.is_error)
            projects = await self.call(client, "list_projects")
            self.assertEqual([item["id"] for item in projects["items"]], [self.other_project["id"]])

    async def test_template_and_reference_inputs_preserve_full_plan_and_reject_invalid_paths(self):
        """模板配置通过真实协议创建项目，不因默认参数覆盖美术、Skill 或模型选择。"""
        async with self.client() as client:
            page = await self.call(client, "list_templates", limit=1)
            self.assertTrue(page["items"])
            template = await self.call(client, "get_template", template_id=page["items"][0]["id"])
            self.assertEqual(set(template["production_plan"]["stages"]), {name for name, _ in engine.STAGES})
            # 此夹具只导入小型 Skill；正式模板仍保留原内容，调用者可按需求修改后提交。
            self.skill_fixture()
            template["production_plan"]["autonomous"] = True
            for stage in template["production_plan"]["stages"].values():
                stage.update(skill_mode="manual", skill_paths=["casual-game-production/SKILL.md"])
            reference = self.root / "ref" / "设计说明.md"
            reference.parent.mkdir()
            reference.write_text("# 设计输入\n保留原有棋盘布局", encoding="utf-8")
            arguments = {key: template[key] for key in ("name", "brief", "genre_id", "framework_id",
                                                       "model_provider", "model_id", "knowledge_paths", "production_plan")}
            arguments.update(request_id="template-project", references=["ref/设计说明.md"])
            project = await self.call(client, "create_project", **arguments)
            self.assertEqual(project["pipeline"]["status"], "draft")
            self.assertTrue(project["production_plan"]["autonomous"])
            stored = engine.load("projects", project["id"])
            self.assertEqual(stored["brief"], arguments["brief"])
            self.assertEqual(stored["production_plan"], arguments["production_plan"])
            self.assertEqual(stored["references"], ["设计说明.md"])
            self.assertEqual(stored["model_provider"], "api-key")
            self.assertFalse(engine.project_runs(project["id"]))
            self.assertEqual((await self.call(client, "create_project", **arguments))["id"], project["id"])
            references = await self.call(client, "list_references", query="设计说明")
            self.assertEqual(references["items"][0]["reference_path"], "设计说明.md")
            for index, value in enumerate(("/Users/mac/design.png", "../backend/.env", "不存在.zip")):
                invalid = await client.call_tool("create_project", {**arguments, "request_id": f"bad-ref-{index}",
                                                                    "references": [value]}, raise_on_error=False)
                self.assertTrue(invalid.is_error)

    async def test_authenticated_reference_upload_and_client_scoping(self):
        """二进制上传走同一 Bearer 和项目创建权限；超过普通 MCP 消息大小的文件也能提交。"""
        url = "/mcp/references/upload"
        parameters = {"filename": "美术需求.md", "request_id": "reference-1"}
        content = ("真实设计输入\n" * 30000).encode()
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/octet-stream"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver") as http:
            self.assertEqual((await http.post(url, params=parameters, content=content)).status_code, 401)
            limited = await http.post(url, params=parameters, content=content,
                                      headers={"Authorization": f"Bearer {self.restricted_token}"})
            self.assertEqual(limited.status_code, 403)
            first = await http.post(url, params=parameters, content=content, headers=headers)
            self.assertEqual(first.status_code, 200, first.text)
            repeated = await http.post(url, params=parameters, content=content, headers=headers)
            self.assertEqual(repeated.json(), first.json())
            conflict = await http.post(url, params=parameters, content=b"changed", headers=headers)
            self.assertEqual(conflict.status_code, 409)
            oversized = await http.post(url, params=parameters, content=b"test",
                                        headers={**headers, "Content-Length": str(65 * 1024 * 1024)})
            self.assertEqual(oversized.status_code, 413)
        uploaded = first.json()
        async with self.client() as client:
            info = await self.call(client, "get_reference_upload_info")
            self.assertEqual(info["url"], "http://127.0.0.1:8003/mcp/references/upload")
            references = await self.call(client, "list_references", query="美术需求")
            self.assertEqual(references["items"][0]["reference_path"], uploaded["reference_path"])
            created = await self.call(client, "create_project", request_id="uploaded-project", name="附件项目",
                                      references=[uploaded["reference_path"]], framework_id="canvas-web")
            self.assertEqual(created["references"], [uploaded["reference_path"]])
        async with self.client(self.restricted_token) as client:
            references = await self.call(client, "list_references", query="美术需求")
            self.assertEqual(references["items"], [])
            self.assertTrue((await client.call_tool("get_reference_upload_info", {}, raise_on_error=False)).is_error)

    async def test_pipeline_controls_retry_without_cancelling_a_later_resume(self):
        """成功操作的标识持久保存；晚到的取消重试不能取消用户随后恢复的任务。"""
        plan = {"auto_publish": False, "stages": {name: {"prompt": "真实阶段", "skill_mode": "manual", "skill_paths": []}
                                                  for name, _ in engine.STAGES}}
        async with self.client() as client:
            project = await self.call(client, "create_project", request_id="control-project", name="控制测试",
                                      framework_id="canvas-web", production_plan=plan)
            project_id = project["id"]
            await self.call(client, "start_pipeline", project_id=project_id, request_id="pipeline-start")
            for _ in range(100):
                if engine.project_runs(project_id):
                    break
                await asyncio.sleep(0.01)
            runs = engine.project_runs(project_id)
            self.assertEqual(len(runs), 1)
            duplicate = await self.call(client, "start_pipeline", project_id=project_id, request_id="pipeline-start")
            self.assertEqual(duplicate["pipeline"]["status"], "running")
            conflict = await client.call_tool("cancel_pipeline", {"project_id": project_id, "request_id": "pipeline-start"},
                                               raise_on_error=False)
            self.assertTrue(conflict.is_error)
            cancelled = await self.call(client, "cancel_pipeline", project_id=project_id, request_id="pipeline-cancel")
            self.assertEqual(cancelled["pipeline"]["status"], "cancelled")
            resumed = await self.call(client, "resume_pipeline", project_id=project_id, request_id="pipeline-resume")
            self.assertEqual(resumed["pipeline"]["status"], "running")
            replay = await self.call(client, "cancel_pipeline", project_id=project_id, request_id="pipeline-cancel")
            self.assertEqual(replay["pipeline"]["status"], "running")
            self.assertEqual(len(engine.project_runs(project_id)), 1)
            self.assertEqual(engine.load("runs", runs[0]["id"])["attempt"], 2)
        # 重新连接后仍保留同一去重结果；每次调用都重新校验目标项目权限。
        async with self.client(self.restricted_token) as client:
            for name in ("start_pipeline", "resume_pipeline", "cancel_pipeline"):
                denied = await client.call_tool(name, {"project_id": project_id, "request_id": "pipeline-start"}, raise_on_error=False)
                self.assertTrue(denied.is_error)
                self.assertIn("无权", denied.content[0].text)
            for name in ("get_pending_questions", "answer_questions"):
                arguments = {"run_id": runs[0]["id"]}
                if name == "answer_questions":
                    arguments.update(request_id="answer-1", answers={"question": "用户输入"})
                denied = await client.call_tool(name, arguments, raise_on_error=False)
                self.assertTrue(denied.is_error)
                self.assertIn("无权", denied.content[0].text)
        async with self.client() as client:
            await self.call(client, "cancel_pipeline", project_id=project_id, request_id="pipeline-cancel-final")

    async def test_manual_stage_confirmation_binds_run_and_preserves_checks(self):
        """远程确认不能跨项目、跳过产物验收，或把旧确认误施加到新运行。"""
        async with self.client() as client:
            run = await self.start(client)
            await self.call(client, "cancel_run", run_id=run["id"])
            arguments = {"project_id": self.project["id"], "stage": "prototype", "run_id": run["id"],
                         "request_id": "confirm-prototype"}
            engine.set_status(run["id"], "awaiting_confirmation", artifacts=[])
            missing = await client.call_tool("confirm_stage", arguments, raise_on_error=False)
            self.assertTrue(missing.is_error)
            workspace = engine.resolve_workspace(self.project["workspace"])
            report = workspace / "workflow" / "prototype.md"
            report.parent.mkdir(parents=True)
            report.write_text("# 原型设计\n\n真实测试产物。", encoding="utf-8")
            artifacts = engine.collect_artifacts(run["id"], workspace, {})
            engine.set_status(run["id"], "awaiting_confirmation", artifacts=artifacts)
            wrong = await client.call_tool("confirm_stage", {**arguments, "run_id": "wrong-run"}, raise_on_error=False)
            self.assertTrue(wrong.is_error)
            confirmed = await self.call(client, "confirm_stage", **arguments)
            self.assertEqual(confirmed["stages"][0]["status"], "completed")
            new_run = await self.start(client, request_id="prototype-again")
            replay = await self.call(client, "confirm_stage", **arguments)
            self.assertEqual(replay["stages"][0]["run_id"], new_run["id"])
            self.assertNotEqual(replay["stages"][0]["status"], "completed")
            premature = await client.call_tool("publish_project", {"project_id": self.project["id"],
                                                                     "slug": "not-ready", "request_id": "publish-early"}, raise_on_error=False)
            self.assertTrue(premature.is_error)
        async with self.client(self.restricted_token) as client:
            denied = await client.call_tool("confirm_stage", arguments, raise_on_error=False)
            self.assertTrue(denied.is_error)
            self.assertIn("无权", denied.content[0].text)

    async def test_explicit_api_project_selection_is_persisted_and_inherited(self):
        """MCP 参数进入真实项目与运行记录；未传运行覆盖值时继承项目的 API 身份。"""
        async with self.client() as client:
            arguments = {"request_id": "api-project", "name": "API 棋盘项目", "genre_id": "board-games",
                         "framework_id": "native-web", "model_provider": "api-key", "model_id": "gpt-6.1-sol"}
            project = await self.call(client, "create_project", **arguments)
            duplicate = await self.call(client, "create_project", **arguments)
            self.assertEqual(project["id"], duplicate["id"])
            self.assertEqual(project["model_provider"], "api-key")
            stored = engine.load("projects", project["id"])
            self.assertEqual(stored["model_provider"], "api-key")
            self.assertEqual(stored["model_id"], "gpt-6.1-sol")
            run = await self.call(client, "start_stage", project_id=project["id"], stage="prototype", request_id="api-stage")
            self.assertEqual(run["model_provider"], "api-key")
            self.assertEqual(run["model_id"], "gpt-6.1-sol")
            self.assertEqual(engine.load("runs", run["id"])["provider"], "api-key")
            self.assertEqual((await self.call(client, "get_run", run_id=run["id"]))["model_provider"], "api-key")

    async def test_explicit_run_selection_preserves_project_default_retry_and_resume(self):
        """单次覆盖不会改写项目默认；重试不能换身份，恢复使用已冻结的 API 来源。"""
        async with self.client() as client:
            arguments = {"project_id": self.project["id"], "stage": "prototype", "request_id": "api-override",
                         "model_provider": "api-key", "model_id": "gpt-6.1-sol"}
            run = await self.call(client, "start_stage", **arguments)
            duplicate = await self.call(client, "start_stage", **arguments)
            self.assertEqual(run["id"], duplicate["id"])
            self.assertEqual(run["model_provider"], "api-key")
            self.assertEqual(engine.load("runs", run["id"])["model"], "gpt-6.1-sol")
            self.assertEqual((await self.call(client, "get_project", project_id=self.project["id"]))["model_provider"], "codex-login")
            conflict = await client.call_tool("start_stage", {**arguments, "model_provider": "codex-login"}, raise_on_error=False)
            self.assertTrue(conflict.is_error)
            await self.call(client, "cancel_run", run_id=run["id"])
            resumed = await self.call(client, "resume_run", run_id=run["id"], request_id="resume-api")
            self.assertEqual(resumed["model_provider"], "api-key")
            self.assertEqual(resumed["model_id"], "gpt-6.1-sol")
            self.assertEqual(resumed["attempt"], 2)

    async def test_legacy_project_without_model_fields_keeps_original_login_source(self):
        """旧项目的只读展示不能补写或悄悄迁移模型来源，启动仍使用历史默认。"""
        legacy = engine.load("projects", self.project["id"])
        legacy.pop("model_provider")
        legacy.pop("model_id")
        engine.save("projects", legacy)
        record = engine.STORE / "projects" / f"{legacy['id']}.json"
        original = record.read_bytes()
        async with self.client() as client:
            project = await self.call(client, "get_project", project_id=legacy["id"])
            self.assertEqual(project["model_provider"], "codex-login")
            self.assertEqual(project["model_id"], "gpt-6.1-sol")
            self.assertEqual(record.read_bytes(), original)
            run = await self.start(client)
            self.assertEqual(run["model_provider"], "codex-login")
            self.assertEqual(engine.load("runs", run["id"])["provider"], "codex-login")

    async def test_preupgrade_project_request_requires_original_source_after_default_change(self):
        """新默认不能改写历史请求；显式传回旧来源才能幂等读取旧项目。"""
        arguments = {"request_id": "before-upgrade-project", "name": "升级前项目", "brief": "保留历史模型来源",
                     "genre_id": "general", "framework_id": "canvas-web"}
        project = engine.create_project(arguments["name"], arguments["brief"], None, [], "general", "canvas-web", [])
        project.pop("model_provider")
        project.pop("model_id")
        # 固定升级前协议字段，不能调用现在的 describe_submission 随实现一起变化。
        old_payload = {"name": arguments["name"], "brief": arguments["brief"], "workspace": None,
                       "references": [], "genre_id": "general", "framework_id": "canvas-web", "knowledge_paths": []}
        encoded = json.dumps(old_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        project["submission"] = {"request_id": arguments["request_id"], "scope": "mcp:admin",
                                 "sha256": hashlib.sha256(encoded.encode()).hexdigest()}
        engine.save("projects", project)
        record = engine.STORE / "projects" / f"{project['id']}.json"
        original = record.read_bytes()
        project_count = len(engine.list_projects())
        async with self.client() as client:
            omitted = await client.call_tool("create_project", arguments, raise_on_error=False)
            self.assertTrue(omitted.is_error)
            self.assertIn("不同参数", omitted.content[0].text)
            replay = await self.call(client, "create_project", **arguments, model_provider="codex-login")
            self.assertEqual(replay["id"], project["id"])
            self.assertEqual(replay["model_provider"], "codex-login")
            switched = await client.call_tool("create_project", {**arguments, "model_provider": "api-key",
                                                                  "model_id": "gpt-6.1-sol"}, raise_on_error=False)
            self.assertTrue(switched.is_error)
            self.assertIn("不同参数", switched.content[0].text)
        self.assertEqual(record.read_bytes(), original)
        self.assertEqual(len(engine.list_projects()), project_count)

    async def test_preupgrade_stage_request_digest_replays_original_worker_and_rejects_api_switch(self):
        """旧阶段请求仍幂等；显式切换 API 必须使用新 request_id，不能复用历史运行。"""
        arguments = {"project_id": self.project["id"], "stage": "prototype", "request_id": "before-upgrade-stage"}
        run = engine.start_run(self.project["id"], "prototype")
        old_payload = {"project_id": self.project["id"], "stage": "prototype", "prompt": "", "skill_paths": [],
                       "skill_mode": "auto", "excluded_skill_paths": []}
        encoded = json.dumps(old_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        run["submission"] = {"request_id": arguments["request_id"], "scope": "mcp:admin",
                             "sha256": hashlib.sha256(encoded.encode()).hexdigest()}
        engine.save("runs", run)
        record = engine.STORE / "runs" / f"{run['id']}.json"
        original = record.read_bytes()
        worker = engine.WORKERS[run["id"]]
        async with self.client() as client:
            replay = await self.call(client, "start_stage", **arguments)
            self.assertEqual(replay["id"], run["id"])
            self.assertEqual(replay["model_provider"], "codex-login")
            switched = await client.call_tool("start_stage", {**arguments, "model_provider": "api-key",
                                                               "model_id": "gpt-6.1-sol"}, raise_on_error=False)
            self.assertTrue(switched.is_error)
            self.assertIn("不同参数", switched.content[0].text)
        self.assertEqual(record.read_bytes(), original)
        self.assertEqual(len(engine.project_runs(self.project["id"])), 1)
        self.assertIs(engine.WORKERS[run["id"]], worker)

    async def test_capabilities_check_api_configuration_without_leaking_credentials_or_calling_login(self):
        """真实 API 配置检查只返回是否已配置，不暴露令牌、私有网关或产生模型推理。"""
        secret = "仅测试的模型令牌"
        gateway = "https://private-gateway.example/v1"
        with patch.object(model_runtime.config, "LLM_API_KEY", secret), \
             patch.object(model_runtime.config, "get_llm_base_url", return_value=gateway), \
             patch.object(model_runtime, "inspect_codex_runtime", AsyncMock()) as login:
            async with self.client() as client:
                capabilities = await self.call(client, "get_capabilities")
                runtime = capabilities["model_runtime"]
                self.assertEqual(runtime["provider"], "api-key")
                self.assertEqual(runtime["model"], "gpt-6.1-sol")
                self.assertTrue(runtime["configured"])
                self.assertFalse(runtime["connection_checked"])
                self.assertTrue(runtime["capabilities"]["reference_archives"])
                self.assertIn("gpt-6.1-sol", {item["id"] for item in runtime["models"]})
                self.assertEqual(capabilities["default_model_selection"], {
                    "model_provider": "api-key", "model_id": "gpt-6.1-sol",
                })
                serialized = json.dumps(capabilities, ensure_ascii=False)
                self.assertNotIn(secret, serialized)
                self.assertNotIn(gateway, serialized)
                invalid = await client.call_tool("get_capabilities", {"model_id": "unknown-model"}, raise_on_error=False)
                self.assertTrue(invalid.is_error)
            login.assert_not_awaited()

    async def test_project_permissions_cover_every_run_and_artifact_operation(self):
        async with self.client() as client:
            run = await self.start(client)
        async with self.client(self.restricted_token) as client:
            operations = {
                "get_project": {"project_id": self.project["id"]},
                "preview_skill_selection": {"project_id": self.project["id"], "stage": "prototype"},
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
            cursor, events = 0, []
            while True:
                page = await self.call(client, "get_run_events", run_id=run["id"], after=cursor, limit=2)
                self.assertLessEqual(len(page["events"]), 2)
                self.assertGreater(page["next_cursor"], cursor)
                cursor = page["next_cursor"]
                events.extend(page["events"])
                if not page["has_more"]:
                    break
            expected = engine.load("runs", run["id"])["events"]
            self.assertEqual([item["seq"] for item in events], [item["seq"] for item in expected])
            self.assertTrue(all(len(item["message"]) <= 1000 and "data" not in item for item in events))
            for arguments in ({"run_id": run["id"], "limit": 51}, {"run_id": "../../private"}):
                result = await client.call_tool("get_run_events", arguments, raise_on_error=False)
                self.assertTrue(result.is_error)

    async def test_skill_preview_is_read_only_and_checks_project_permissions(self):
        """真实 MCP 预览显示框架候选；既不创建输入快照，也不更改阶段与历史运行。"""
        paths = self.skill_fixture()
        project = self.routing_project()
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        async with self.client() as client:
            plan = await self.call(client, "preview_skill_selection", project_id=project["id"], stage="prototype")
            self.assertEqual(plan["mode"], "auto")
            self.assertEqual(plan["selected_paths"], paths)
            self.assertEqual(plan["context"]["genre_id"], "sorting")
            self.assertEqual(plan["context"]["framework_id"], "cocos-web")
            self.assertTrue(all(item["reason"] for item in plan["items"]))
            manual = await self.call(client, "preview_skill_selection", project_id=project["id"],
                                     stage="prototype", skill_mode="manual", skill_paths=[])
            self.assertEqual(manual["selected_paths"], [])
            self.assertEqual(manual["recommended_paths"], paths)
        async with self.client(self.restricted_token) as client:
            forbidden = await client.call_tool("preview_skill_selection", {
                "project_id": project["id"], "stage": "prototype",
            }, raise_on_error=False)
            self.assertTrue(forbidden.is_error)
            self.assertIn("无权", forbidden.content[0].text)
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((engine.STORE / "inputs").exists())
        self.assertEqual(engine.project_runs(project["id"]), [])

    async def test_mcp_auto_selection_freezes_versions_and_exposes_actual_read_evidence(self):
        """启动和读取均走实际服务；来源编辑后真实工具仍读旧快照，MCP 不泄漏正文。"""
        paths = self.skill_fixture()
        project = self.routing_project()
        async with self.client() as client:
            request = {"project_id": project["id"], "stage": "prototype", "request_id": "auto-skills"}
            started = await self.call(client, "start_stage", **request)
            self.assertEqual(started["skill_paths"], paths)
            self.assertEqual(started["skill_selection"]["mode"], "auto")
            self.assertEqual([item["path"] for item in started["skill_snapshot"]], paths)
            self.assertEqual(started["skill_reads"], [])
            self.assertTrue(all("content" not in item for item in started["skill_snapshot"]))

            # 文件工具采用冻结运行输入。模拟知识库后续修订，不能改变正在运行的版本。
            stored = engine.load("runs", started["id"])
            source = self.root / "knowledge" / "skill" / "docs" / paths[0]
            previous = source.read_text(encoding="utf-8")
            source.write_text(previous + "\n后续来源修改\n", encoding="utf-8")
            tools = create_workflow_tools(
                root=self.root, knowledge_dir=self.root / "knowledge", workspace=engine.resolve_workspace(project["workspace"]),
                run=stored, emit=lambda kind, message, data: engine.event(stored["id"], kind, message, data),
                load_run=lambda: engine.load("runs", stored["id"]),
                skill_input_dir=engine.STORE / "inputs" / stored["id"] / "skills",
            )
            reader = next(tool for tool in tools if tool.name == "read_skill")
            self.assertEqual(reader.invoke({"path": paths[0]}), previous)
            result = await self.call(client, "get_run", run_id=started["id"])
            self.assertEqual(result["skill_snapshot"], started["skill_snapshot"])
            self.assertEqual(result["skill_reads"], [{"path": paths[0], "sha256": hashlib.sha256(previous.encode()).hexdigest(),
                                                    "version": "1.0.0", "frozen": True}])
            self.assertNotIn("skill_resources", result)
            duplicate = await self.call(client, "start_stage", **request)
            self.assertEqual(duplicate["id"], started["id"])
            self.assertEqual(duplicate["skill_snapshot"], started["skill_snapshot"])
            for changed in ({"skill_mode": "manual"}, {"excluded_skill_paths": [paths[1]]}):
                conflict = await client.call_tool("start_stage", {**request, **changed}, raise_on_error=False)
                self.assertTrue(conflict.is_error)
                self.assertIn("不同参数", conflict.content[0].text)
            self.assertEqual(len(engine.project_runs(project["id"])), 1)

    async def test_mcp_manual_empty_and_auto_exclusions_preserve_user_choices(self):
        paths = self.skill_fixture()
        manual_project = self.routing_project()
        excluded_project = self.routing_project("games/excluded")
        supplemented_project = self.routing_project("games/supplemented", framework="canvas-web")
        async with self.client() as client:
            manual = await self.call(client, "start_stage", project_id=manual_project["id"], stage="prototype",
                                     request_id="manual-empty", skill_mode="manual", skill_paths=[])
            self.assertEqual(manual["skill_paths"], [])
            self.assertEqual(manual["skill_snapshot"], [])
            self.assertEqual(manual["skill_selection"]["mode"], "manual")
            excluded = await self.call(client, "start_stage", project_id=excluded_project["id"], stage="prototype",
                                       request_id="exclude-cocos", excluded_skill_paths=[paths[1]])
            self.assertEqual(excluded["skill_paths"], [paths[0]])
            self.assertEqual(excluded["skill_selection"]["recommended_paths"], paths)
            self.assertEqual([item["path"] for item in excluded["skill_snapshot"]], [paths[0]])
            supplemented = await self.call(client, "start_stage", project_id=supplemented_project["id"], stage="prototype",
                                           request_id="supplement-cocos", skill_paths=[paths[1]])
            self.assertEqual(supplemented["skill_paths"], paths)
            manual_item = next(item for item in supplemented["skill_selection"]["items"] if item["path"] == paths[1])
            self.assertEqual((manual_item["source"], manual_item["usage"]), ("manual", "reference"))

    async def test_legacy_run_view_and_new_preview_do_not_rewrite_history(self):
        """旧运行没有选择计划或快照；读取及预览不能为它补写新的必读条件。"""
        paths = self.skill_fixture()
        legacy = {"id": "legacy-run", "project_id": self.project["id"], "stage": "prototype", "status": "completed",
                  "progress": 100, "attempt": 1, "created_at": "2026-10-01", "updated_at": "2026-10-01",
                  "summary": "旧任务", "error": None, "events": [], "artifacts": [], "skill_paths": [paths[0]]}
        engine.save("runs", legacy)
        stored_path = engine.STORE / "runs" / "legacy-run.json"
        before = stored_path.read_bytes()
        async with self.client() as client:
            old = await self.call(client, "get_run", run_id=legacy["id"])
            self.assertIsNone(old["skill_selection"])
            self.assertEqual(old["skill_snapshot"], [])
            self.assertEqual(old["skill_paths"], [paths[0]])
            await self.call(client, "preview_skill_selection", project_id=self.project["id"], stage="prototype")
            self.assertEqual((await self.call(client, "get_run", run_id=legacy["id"]))["status"], "completed")
        self.assertEqual(stored_path.read_bytes(), before)

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
