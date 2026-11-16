"""真实 MCP、DeepAgents 中断与四阶段发布闭环；模型推理使用本地脚本替身。"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI

from app.services.workflow import engine, model_runtime, pipeline
from tests import test_mcp, test_workflow_pipeline


class MCPPipelineTests(unittest.IsolatedAsyncioTestCase):
    # 复用真实 HTTP 和小型构建夹具，不继承测试类，避免重复发现其他测试。
    asyncSetUp = test_mcp.MCPTests.asyncSetUp
    asyncTearDown = test_mcp.MCPTests.asyncTearDown
    hold_execution = test_mcp.MCPTests.hold_execution
    client = test_mcp.MCPTests.client
    call = test_mcp.MCPTests.call
    prepare_fixture = test_workflow_pipeline.PipelineTests.prepare_fixture
    scripted_model = test_workflow_pipeline.PipelineTests.scripted_model

    async def wait_pipeline(self):
        task = pipeline.PIPELINES.get(self.project["id"])
        if task:
            await asyncio.wait_for(asyncio.shield(task), 30)

    def scripted_api_model(self):
        """模型先真实读取所选框架和品类资料，再复用阶段工具调用脚本。"""
        normal = self.scripted_model()

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            knowledge = context["project"].get("knowledge_paths", [])
            completed = {item.tool_call_id for item in messages
                         if isinstance(item, ToolMessage) and item.name == "read_game_knowledge"}
            calls = [{"name": "read_game_knowledge", "id": f"knowledge-{index}", "args": {"path": path}}
                     for index, path in enumerate(knowledge) if f"knowledge-{index}" not in completed]
            if calls:
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=calls))])
            # 阶段夹具只根据自己的工具结果推进，知识工具结果仍保留在真实图检查点中。
            production_messages = [item for item in messages
                                   if not isinstance(item, ToolMessage) or item.name != "read_game_knowledge"]
            return await normal(model, production_messages, **kwargs)

        return infer

    async def test_default_api_pipeline_interrupt_reconnect_answer_retry_and_publication(self):
        """省略模型参数仍以 API 完成四阶段、中断问答、重连和发布，不调用 Codex。"""
        # 使用不可联网的占位身份，保留 API 模型工厂、回调、图与文件工具真实行为。
        local_model = ChatOpenAI(model=model_runtime.DEFAULT_MODEL, api_key="local-test-placeholder",
                                 base_url="http://127.0.0.1:1", use_responses_api=False)
        with patch.object(engine, "execute_run", self.real_execute), \
             patch.object(engine, "CodexChatModel", side_effect=AssertionError("API 项目不得使用 Codex 登录")), \
             patch.object(model_runtime, "inspect_runtime", AsyncMock(return_value={"available": True})), \
             patch.object(model_runtime, "get_chat_model", return_value=local_model), \
             patch.object(ChatOpenAI, "_agenerate", self.scripted_api_model()):
            async with self.client() as client:
                tools = {tool.name: tool for tool in await client.list_tools()}
                self.assertTrue(tools["answer_questions"].annotations.idempotent_hint)
                self.assertTrue(tools["get_pending_questions"].annotations.read_only_hint)
                arguments = {"request_id": "mcp-pipeline-project", "name": "MCP API 全流程",
                             "brief": {"idea": "蓝色棋盘", "art": "沿用棋子贴图"},
                             "genre_id": "board-games", "framework_id": "native-web",
                             "production_plan": test_workflow_pipeline.simple_plan(
                                 autonomous=False, auto_publish=True, publish_slug="mcp-pipeline-demo")}
                created = await self.call(client, "create_project", **arguments)
                duplicate = await self.call(client, "create_project", **arguments)
                self.assertEqual(created["id"], duplicate["id"])
                self.assertEqual(created["model_provider"], "api-key")
                self.assertFalse(created["production_plan"]["autonomous"])
                self.assertTrue(created["production_plan"]["auto_publish"])
                self.assertEqual(created["pipeline"]["status"], "draft")
                self.project = engine.load("projects", created["id"])
                self.prepare_fixture()
                start = {"project_id": created["id"], "request_id": "mcp-pipeline-start"}
                await self.call(client, "start_pipeline", **start)
                await self.call(client, "start_pipeline", **start)
                await self.wait_pipeline()
                paused = await self.call(client, "get_project", project_id=created["id"])
                self.assertEqual(paused["pipeline"]["status"], "awaiting_input", paused["pipeline"])
                run_id = paused["pipeline"]["run_id"]
                run = await self.call(client, "get_run", run_id=run_id)
                self.assertTrue(run["requires_input"])
                self.assertEqual(run["interrupt_count"], 2)
                self.assertFalse(run["autonomous"])
                self.assertEqual(run["model_provider"], "api-key")
                first = await self.call(client, "get_pending_questions", run_id=run_id, limit=1)
                self.assertTrue(first["has_more"])
                first_question = first["interrupts"][0]

            # 断线不丢问题；新的 MCP 会话使用问题 ID 恢复同一 SQLite 检查点。
            async with self.client() as client:
                second = await self.call(client, "get_pending_questions", run_id=run_id,
                                         offset=first["next_offset"], limit=1)
                self.assertFalse(second["has_more"])
                questions = [first_question, *second["interrupts"]]
                answers = {item["id"]: item["value"]["options"][-1] for item in questions}
                arguments = {"run_id": run_id, "request_id": "mcp-pipeline-answer", "answers": answers}
                response = await self.call(client, "answer_questions", **arguments)
                duplicate = await self.call(client, "answer_questions", **arguments)
                self.assertEqual(response["id"], duplicate["id"])
                self.assertEqual((await self.call(client, "get_pending_questions", run_id=run_id))["total"], 0)
                await self.wait_pipeline()
                finished = await self.call(client, "get_project", project_id=created["id"])
                self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
                self.assertTrue(all(item["confirmed_by"] == "pipeline" for item in finished["stages"]))
                self.assertTrue(finished["publication"]["url"].endswith("/games/mcp-pipeline-demo/index.html"))
                self.assertTrue((self.root / "frontend/public/games/mcp-pipeline-demo/index.html").is_file())
                # 完成后再次重试同一答复也只读取原运行，不重新提问或产生新阶段。
                completed_retry = await self.call(client, "answer_questions", **arguments)
                self.assertEqual(completed_retry["status"], "completed")
                self.assertEqual(completed_retry["interrupts"], [])
                records = engine.project_runs(created["id"])
                self.assertEqual(len(records), 4)
                self.assertTrue(all(record["status"] == "completed" and record["provider"] == "api-key" for record in records))
                self.assertTrue(all(record["artifacts"] for record in records))
                self.assertEqual(len(engine.load("projects", created["id"])["human_answers"]), 2)
                self.assertEqual(len(engine.load("runs", run_id)["answer_submissions"]), 1)
                # API 模型回调应继续记录身份，不能把测试替身当作 Codex 调用。
                self.assertTrue(all(any(event["type"] == "model_completed"
                                        and event["data"].get("provider") == "api-key"
                                        for event in record["events"]) for record in records))

    async def test_cancel_pending_run_stops_pipeline_and_resume_preserves_questions(self):
        """旧 cancel_run 入口也须同步流水线；继续计划不能替用户回答原有问题。"""
        with patch.object(engine, "execute_run", self.real_execute), \
             patch.object(engine, "inspect_runtime", AsyncMock(return_value={"available": True})), \
             patch.object(engine.CodexChatModel, "_agenerate", self.scripted_api_model()):
            async with self.client() as client:
                created = await self.call(client, "create_project", request_id="cancel-project",
                    name="人工问题取消测试", genre_id="board-games", framework_id="native-web", model_provider="codex-login",
                    production_plan=test_workflow_pipeline.simple_plan(autonomous=False))
                self.assertEqual(created["model_provider"], "codex-login")
                self.project = engine.load("projects", created["id"])
                self.prepare_fixture()
                await self.call(client, "start_pipeline", project_id=created["id"], request_id="cancel-start")
                await self.wait_pipeline()
                paused = await self.call(client, "get_project", project_id=created["id"])
                self.assertEqual(paused["pipeline"]["status"], "awaiting_input", paused["pipeline"])
                run_id = paused["pipeline"]["run_id"]
                original = await self.call(client, "get_pending_questions", run_id=run_id)
                self.assertEqual(original["total"], 2)
                cancelled = await self.call(client, "cancel_run", run_id=run_id)
                self.assertEqual(cancelled["status"], "cancelled")
                self.assertFalse(cancelled["requires_input"])
                self.assertEqual(cancelled["interrupts"], [])
                project = await self.call(client, "get_project", project_id=created["id"])
                self.assertEqual(project["pipeline"]["status"], "cancelled")
                self.assertEqual((await self.call(client, "get_pending_questions", run_id=run_id))["total"], 0)
                answers = {item["id"]: item["value"]["options"][0] for item in original["interrupts"]}
                rejected = await client.call_tool("answer_questions", {
                    "run_id": run_id, "request_id": "cancelled-answer", "answers": answers}, raise_on_error=False)
                self.assertTrue(rejected.is_error)
                self.assertIn("没有待回答", rejected.content[0].text)
                await self.call(client, "resume_pipeline", project_id=created["id"], request_id="cancel-resume")
                await self.wait_pipeline()
                resumed = await self.call(client, "get_project", project_id=created["id"])
                self.assertEqual(resumed["pipeline"]["status"], "awaiting_input", resumed["pipeline"])
                self.assertEqual(resumed["pipeline"]["run_id"], run_id)
                self.assertEqual(engine.load("runs", run_id)["provider"], "codex-login")
                pending = await self.call(client, "get_pending_questions", run_id=run_id)
                self.assertEqual(pending["interrupts"], original["interrupts"])
                self.assertFalse(engine.load("projects", created["id"]).get("human_answers"))
                self.assertEqual(len(engine.project_runs(created["id"])), 1)
                # 确认仍暂停后显式结束测试任务，不依赖用例清理伪装业务取消成功。
                await self.call(client, "cancel_pipeline", project_id=created["id"], request_id="final-cancel")


if __name__ == "__main__":
    unittest.main()
