"""全流程与 HITL 回归：模型推理使用测试替身，图、工具、检查点和校验真实执行。"""

import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ValidationError
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.services.workflow import engine, pipeline
from app.services import knowledge, production_library
from app.services.skill_library import import_skill_library
from app.services.workflow.templates import ProductionPlan, WorkflowTemplate, list_templates
from app.api.routes.workflow import router


def simple_plan(**values):
    return {"art_requirements": "保留用户选择的主题", "auto_publish": False,
            "stages": {name: {"prompt": "完成真实阶段", "skill_mode": "manual", "skill_paths": []}
                       for name, _ in engine.STAGES}, **values}


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(engine, "ROOT", self.root), patch.object(engine, "STORE", self.root / "state"),
                        patch.object(engine, "KNOWLEDGE_DIR", self.root / "knowledge"),
                        patch.object(engine, "inspect_runtime", AsyncMock(return_value={"available": True}))]
        for item in self.patches:
            item.start()
        self.project = engine.create_project("全流程测试", {"idea": "测试夹具"}, None, [], production_plan=simple_plan())

    async def asyncTearDown(self):
        await engine.shutdown_workers()
        engine.WORKERS.clear(); pipeline.PIPELINES.clear()
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    async def wait_pipeline(self):
        task = pipeline.PIPELINES.get(self.project["id"])
        if task:
            await asyncio.wait_for(asyncio.shield(task), 20)
        return engine.get_project(self.project["id"])

    def prepare_fixture(self):
        """测试夹具只放临时目录，构建和规则检查由正式 run_validation 工具执行。"""
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "scripts").mkdir()
        (workspace / "package.json").write_text(json.dumps({"scripts": {
            "build": "node scripts/build.mjs", "test": "node scripts/test.mjs", "check": "node scripts/check.mjs"}}))
        (workspace / "rules.mjs").write_text("export const move = (position, dice) => Math.min(10, position + dice);\n")
        (workspace / "scripts/build.mjs").write_text(
            "import{mkdirSync,writeFileSync}from'node:fs';mkdirSync('dist',{recursive:true});"
            "writeFileSync('dist/index.html','<!doctype html><title>测试</title><p>真实构建</p>');")
        (workspace / "scripts/test.mjs").write_text(
            "import assert from'node:assert/strict';import{move}from'../rules.mjs';"
            "assert.equal(move(2,3),5);assert.equal(move(9,6),10);")
        (workspace / "scripts/check.mjs").write_text(
            "import assert from'node:assert/strict';import{readFileSync}from'node:fs';"
            "assert.match(readFileSync('dist/index.html','utf8'),/<!doctype html>/);")

    def scripted_model(self, ask=True, audit=False):
        """只替代模型推理，返回工具请求，其他生产路径完全沿用正式实现。"""
        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            stage = context["stage"]
            results = [item for item in messages if isinstance(item, ToolMessage)]
            names = [item.name for item in results]
            calls = []

            def call(name, **args):
                calls.append({"name": name, "args": args, "id": f"{stage}-{len(results)}-{len(calls)}"})

            if ask and stage == "prototype" and "request_user_input" not in names:
                call("request_user_input", question="选择棋盘配色", options=["紫色", "蓝色"])
                call("request_user_input", question="选择对手", options=["AI", "同屏玩家"])
            elif stage == "art" and "inspect_assets" not in names:
                if not results:
                    call("write_file", file_path="/piece.svg", content='<svg xmlns="http://www.w3.org/2000/svg"><circle r="4"/></svg>')
                else:
                    call("inspect_assets", paths=["piece.svg"])
            elif stage == "art" and not any(item.tool_call_id.endswith("-manifest") for item in results):
                inventory = json.loads(next(item.content for item in results if item.name == "inspect_assets"))
                asset = {**inventory[0], "usage": "棋子", "source": "测试夹具绘制"}
                calls.append({"name": "write_file", "id": "art-manifest", "args": {
                    "file_path": "/workflow/art-manifest.json", "content": json.dumps({"assets": [asset]})}})
            elif audit and stage == "test" and not any(item.tool_call_id == "test-audit-write" for item in results):
                calls.append({"name": "write_file", "id": "test-audit-write", "args": {
                    "file_path": "/scripts/test-audit.mjs", "content":
                    "import assert from 'node:assert/strict';import{readFileSync}from'node:fs';"
                    "assert.match(readFileSync('dist/index.html','utf8'),/<!doctype html>/);console.log('补充验收通过');"}})
            elif audit and stage == "test" and not any(item.tool_call_id == "test-audit-check" for item in results):
                calls.append({"name": "run_validation", "id": "test-audit-check", "args": {"command": "node scripts/test-audit.mjs"}})
            elif stage in {"code", "test"}:
                checked = {json.loads(item.content)["command"] for item in results if item.name == "run_validation"}
                pending = [command for command in ["npm run build", "npm test", "npm run check"] if command not in checked]
                if pending:
                    call("run_validation", command=pending[0])
            if not calls and not any(item.tool_call_id == f"{stage}-report" for item in results):
                path = f"/workflow/{stage}.md"
                local = engine.resolve_workspace(self.project["workspace"]) / path.lstrip("/")
                content = f"# {stage} 真实测试报告\n修复轮次：{context['project'].get('pipeline', {}).get('repair_cycles', 0)}"
                args = {"file_path": path, "old_string": local.read_text(), "new_string": content} if local.exists() else {"file_path": path, "content": content}
                calls.append({"name": "edit_file" if local.exists() else "write_file", "id": f"{stage}-report", "args": args})
            message = AIMessage(content="" if calls else "已执行本阶段", tool_calls=calls)
            return ChatResult(generations=[ChatGeneration(message=message)])
        return infer

    def scripted_autonomous_model(self):
        """每阶段先提出问题，再由模型补全第二个选项和理由，其他图与工具仍真实执行。"""
        normal = self.scripted_model(ask=False)

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            stage = context["stage"]
            answers = [item for item in messages if isinstance(item, ToolMessage) and item.name == "request_user_input"]
            if len(answers) < 2:
                arguments = {"question": f"{stage} 阶段采用哪种呈现？", "context": "项目要求蓝色主题", "options": ["紫色主题", "蓝色主题"]}
                if answers:
                    arguments.update(decision="蓝色主题", reason="依据项目明确的蓝色主题要求选择第二项，保持各阶段一致。")
                call = {"name": "request_user_input", "id": f"{stage}-decision-{len(answers)}", "args": arguments}
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[call]))])
            # 原有阶段夹具仅根据生产工具结果推进；讨论结果保留在真实图中，不改变其素材准备步骤。
            production_messages = [item for item in messages if not isinstance(item, ToolMessage) or item.name != "request_user_input"]
            return await normal(model, production_messages, **kwargs)
        return infer

    async def test_updated_h5_skills_run_through_four_stage_graph_and_frozen_reads(self):
        """真实公司包与 DeepAgents 图联通；仅模型决策使用确定性替身，不调用外部服务。"""
        source_root = Path(__file__).resolve().parents[2]
        override = patch.object(knowledge, "KNOWLEDGE_DIR", engine.KNOWLEDGE_DIR)
        override.start()
        self.patches.append(override)
        import_skill_library(source_root)
        production_library.import_production_library()
        plan = simple_plan(autonomous=True)
        for stage in plan["stages"].values():
            stage["skill_mode"] = "auto"
        self.project = engine.create_project("H5 技能图验证", {"idea": "已有 H5 原版还原并换皮，进行包体优化"},
                                             None, [], "general", "native-web", production_plan=plan)
        self.prepare_fixture()
        normal = self.scripted_model(ask=False)
        read_names = {"read_skill", "read_skill_resource", "read_game_knowledge"}

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            calls = []
            # 入口、起读参考与品类知识均经真实工具读取，不能把索引当作已读证据。
            for name, paths in [
                ("read_skill", context["selected_skills"]),
                ("read_skill_resource", [path for item in context["skill_selection"]["items"] for path in item["resource_paths"]]),
                ("read_game_knowledge", context["project"]["knowledge_paths"]),
            ]:
                for index, path in enumerate(paths):
                    identifier = f"{name}-{index}"
                    if not any(isinstance(item, ToolMessage) and item.tool_call_id == identifier for item in messages):
                        calls.append({"name": name, "id": identifier, "args": {"path": path}})
            if calls:
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=calls))])
            filtered = [item for item in messages if not isinstance(item, ToolMessage) or item.name not in read_names]
            return await normal(model, filtered, **kwargs)

        with patch.object(engine.CodexChatModel, "_agenerate", infer):
            pipeline.start_pipeline(self.project["id"])
            finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        records = engine.project_runs(self.project["id"])
        self.assertEqual(len(records), 4)
        for run in records:
            self.assertEqual(run["skill_selection"]["version"], "1.1.0")
            self.assertTrue(any(path.endswith("h5-canvas-reskin/SKILL.md") for path in run["skill_paths"]))
            engine.verify_skill_reads(run, engine.STORE / "inputs" / run["id"] / "skills")
            self.assertTrue(any(item["type"] == "skill_resource_read" for item in run["events"]))

    async def test_autonomous_four_stages_decide_without_interrupting_or_faking_human_answers(self):
        self.project = engine.create_project("自主全流程", {"idea": "蓝色主题游戏"}, None, [], production_plan=simple_plan(autonomous=True))
        self.prepare_fixture()
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_autonomous_model()):
            pipeline.start_pipeline(self.project["id"])
            finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertFalse(finished.get("human_answers"), "模型自主选择不能写成用户确认")
        records = engine.project_runs(self.project["id"])
        self.assertEqual(len(records), 4)
        for run in records:
            self.assertIs(run["autonomous"], True)
            self.assertEqual(run["status"], "completed")
            self.assertFalse(run.get("interrupts"))
            self.assertNotIn("human_input_requested", [event["type"] for event in run["events"]])
            decisions = [event["data"] for event in run["events"] if event["type"] == "autonomous_decision"]
            self.assertEqual(len(decisions), 1, "缺少决策参数的首次提问不能产生伪决策")
            self.assertEqual(decisions[0]["decision"], "蓝色主题", "不应固定选第一个候选项")
            self.assertIn("第二项", decisions[0]["reason"])
            self.assertIn(run["stage"], decisions[0]["question"])
            stages = [stage for stage, _ in engine.STAGES]
            upstream_stages = stages[:stages.index(run["stage"])]
            self.assertEqual([item["stage"] for item in run["upstream_decisions"]], upstream_stages)
            self.assertTrue(all(item["decision"] == "蓝色主题" and item["source"] == "ai" for item in run["upstream_decisions"]))

    async def test_autonomous_pipeline_can_be_manually_stopped_and_resumed(self):
        self.project = engine.create_project("可停止的自主流程", {"idea": "蓝色主题游戏"}, None, [], production_plan=simple_plan(autonomous=True))
        self.prepare_fixture()
        normal = self.scripted_autonomous_model()
        paused = asyncio.Event()

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            if context["stage"] == "art" and not paused.is_set():
                paused.set()
                await asyncio.Event().wait()
            return await normal(model, messages, **kwargs)

        with patch.object(engine.CodexChatModel, "_agenerate", infer):
            pipeline.start_pipeline(self.project["id"])
            await asyncio.wait_for(paused.wait(), 15)
            before = engine.get_project(self.project["id"])
            run_id = before["pipeline"]["run_id"]
            stopped = await pipeline.cancel_pipeline(self.project["id"])
            self.assertEqual(stopped["pipeline"]["status"], "cancelled")
            self.assertIs(engine.load("runs", run_id)["autonomous"], True)
            pipeline.resume_pipeline(self.project["id"])
            finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertEqual(finished["stages"][0], before["stages"][0], "停止恢复不能重跑已完成阶段")
        self.assertEqual(finished["stages"][1]["run_id"], run_id)
        self.assertEqual(engine.load("runs", run_id)["attempt"], 2)
        self.assertTrue(all(run["autonomous"] for run in engine.project_runs(self.project["id"])))
        self.assertFalse(finished.get("human_answers"))

    async def test_autonomous_mode_is_frozen_and_old_runs_remain_interactive(self):
        self.project = engine.create_project("自主配置冻结", {"idea": "蓝色主题游戏"}, None, [], production_plan=simple_plan(autonomous=True))
        self.prepare_fixture()
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_autonomous_model()):
            run = engine.start_run(self.project["id"], "prototype", "制作蓝色主题游戏")
            # 协程开始前修改项目设置，当前运行仍须采用创建时冻结的自主模式。
            project = engine.load("projects", self.project["id"])
            project["production_plan"]["autonomous"] = False
            engine.save("projects", project)
            await asyncio.wait_for(engine.WORKERS[run["id"]], 15)
        self.assertEqual(engine.load("runs", run["id"])["status"], "awaiting_confirmation")
        self.assertIs(engine.load("runs", run["id"])["autonomous"], True)
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model()):
            old = engine.start_run(self.project["id"], "prototype", "兼容旧运行")
            old.pop("autonomous", None)
            engine.save("runs", old)
            project = engine.load("projects", self.project["id"])
            project["production_plan"]["autonomous"] = True
            engine.save("projects", project)
            await asyncio.wait_for(engine.WORKERS[old["id"]], 15)
        restored = engine.load("runs", old["id"])
        self.assertEqual(restored["status"], "awaiting_input", "旧运行不能因为项目字段变化而绕过人工确认")
        self.assertEqual(len(restored["interrupts"]), 2)

    async def test_native_interrupt_resume_and_four_stage_delivery(self):
        """真实 DeepAgents 暂停两个问题，重启恢复后衔接四阶段并验证发布文件。"""
        self.prepare_fixture()
        project = engine.load("projects", self.project["id"])
        project["production_plan"]["auto_publish"] = True
        engine.save("projects", project)
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model()):
            pipeline.start_pipeline(project["id"])
            # 重复开始必须指向同一计划，不产生第二次模型运行。
            pipeline.start_pipeline(project["id"])
            paused = await self.wait_pipeline()
            self.assertEqual(paused["pipeline"]["status"], "awaiting_input", paused["pipeline"])
            run_id = paused["pipeline"]["run_id"]
            run = engine.load("runs", run_id)
            self.assertEqual(len(run["interrupts"]), 2)
            self.assertEqual(len(engine.project_runs(project["id"])), 1)
            engine.recover_interrupted_runs()
            self.assertEqual(engine.get_project(project["id"])["pipeline"]["status"], "awaiting_input")
            with self.assertRaisesRegex(ValueError, "全部问题"):
                pipeline.answer_run(run_id, {"过期问题": "紫色"})
            with self.assertRaisesRegex(ValueError, "不能为空"):
                pipeline.answer_run(run_id, {item["id"]: " " for item in run["interrupts"]})
            with self.assertRaisesRegex(ValueError, "全流程"):
                engine.start_run(project["id"], "prototype")
            pipeline.answer_run(run_id, {item["id"]: item["value"]["options"][0] for item in run["interrupts"]})
            with self.assertRaisesRegex(ValueError, "没有待回答"):
                pipeline.answer_run(run_id, {item["id"]: "重复" for item in run["interrupts"]})
            finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertTrue(all(item["confirmed_by"] == "pipeline" for item in finished["stages"]))
        self.assertEqual(len(engine.project_runs(project["id"])), 4)
        self.assertEqual(len(finished["human_answers"]), 2)
        self.assertTrue(finished["publication"]["url"].endswith(f"/{project['id']}/index.html"))
        self.assertTrue((self.root / "frontend/public/games" / project["id"] / "index.html").is_file())
        for record in engine.project_runs(project["id"]):
            self.assertEqual(record["status"], "completed")
            self.assertTrue(record["artifacts"])

    async def test_failures_are_bounded_and_never_auto_confirmed(self):
        async def fail(run_id, resume=False):
            engine.set_status(run_id, "failed", error="真实校验失败")
            engine.WORKERS.pop(run_id, None)
        with patch.object(engine, "execute_run", fail):
            pipeline.start_pipeline(self.project["id"])
            result = await self.wait_pipeline()
        self.assertEqual(result["pipeline"]["status"], "failed")
        runs = engine.project_runs(self.project["id"])
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["attempt"], 2)
        self.assertTrue(all(not item["confirmed_at"] for item in result["stages"]))
        self.assertNotIn("publication", result)

    async def test_supplemental_audit_and_publication_retry_preserve_completed_stages(self):
        """重现新增补测脚本后的发布重试；四阶段工具真实执行，恢复时不重跑模型。"""
        self.prepare_fixture()
        project = engine.load("projects", self.project["id"])
        project["production_plan"]["auto_publish"] = True
        engine.save("projects", project)
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model(ask=False, audit=True)):
            with patch.object(engine, "publish_project", side_effect=ValueError("模拟发布步骤失败")):
                pipeline.start_pipeline(project["id"])
                failed = await self.wait_pipeline()
        self.assertEqual(failed["pipeline"]["status"], "failed")
        self.assertTrue(all(stage["status"] == "completed" for stage in failed["stages"]))
        records = engine.project_runs(project["id"])
        code = next(run for run in records if run["stage"] == "code")
        self.assertIn("confirmed_source_snapshot", code)
        self.assertNotIn("scripts/test-audit.mjs", code["confirmed_source_snapshot"])
        before = {run["id"]: run["attempt"] for run in records}
        with patch.object(engine, "execute_run", new_callable=AsyncMock) as execute:
            pipeline.resume_pipeline(project["id"])
            finished = await self.wait_pipeline()
            execute.assert_not_called()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertIsNone(finished["pipeline"]["error"])
        self.assertEqual(before, {run["id"]: run["attempt"] for run in engine.project_runs(project["id"])})
        self.assertTrue((self.root / "frontend/public/games" / project["id"] / "index.html").is_file())

    async def test_test_stage_cannot_confirm_modified_upstream_files(self):
        self.prepare_fixture()
        normal = self.scripted_model(ask=False)

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            if context["stage"] == "test" and not any(isinstance(item, ToolMessage) for item in messages):
                workspace = engine.resolve_workspace(self.project["workspace"])
                original = (workspace / "scripts/check.mjs").read_text()
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[{
                    "id": "change-existing-check", "name": "edit_file", "args": {
                        "file_path": "/scripts/check.mjs", "old_string": original, "new_string": original + "\n// 改动旧测试\n"}}]))])
            return await normal(model, messages, **kwargs)

        # 独立运行至测试阶段，检查完成验证也不能直接确认被改写的上游文件。
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model(ask=False)):
            pipeline.start_pipeline(self.project["id"])
            await self.wait_pipeline()
        with patch.object(engine.CodexChatModel, "_agenerate", infer):
            run = engine.start_run(self.project["id"], "test")
            await engine.WORKERS[run["id"]]
        current = engine.load("runs", run["id"])
        self.assertEqual(current["status"], "failed")
        self.assertIn("scripts/check.mjs", current["error"])

    async def test_cancel_and_restart_do_not_advance_or_lose_input(self):
        async def hold(run_id, resume=False):
            await asyncio.Event().wait()
        with patch.object(engine, "execute_run", hold):
            pipeline.start_pipeline(self.project["id"])
            await asyncio.sleep(0.02)
            await pipeline.cancel_pipeline(self.project["id"])
            self.assertEqual(engine.get_project(self.project["id"])["pipeline"]["status"], "cancelled")
            pipeline.resume_pipeline(self.project["id"])
            await asyncio.sleep(0.02)
            await engine.shutdown_workers()
        result = engine.get_project(self.project["id"])
        self.assertEqual(result["pipeline"]["status"], "interrupted")
        self.assertEqual(result["production_plan"], self.project["production_plan"])

    async def test_http_stop_and_resume_preserve_real_graph_checkpoint_and_outputs(self):
        """经真实 HTTP 路由取消正在推理的图，再从 SQLite 检查点完成剩余阶段。"""
        self.prepare_fixture()
        paused = asyncio.Event()
        cancelled = asyncio.Event()
        normal = self.scripted_model(ask=False)

        async def infer(model, messages, **kwargs):
            # 美术报告和素材已由真实工具落盘后，在下一次模型推理中等待用户停止。
            if not paused.is_set() and any(isinstance(item, ToolMessage) and item.tool_call_id == "art-report" for item in messages):
                paused.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()
            return await normal(model, messages, **kwargs)

        app = FastAPI()
        app.include_router(router, prefix="/api")
        base = f"/api/workflow/projects/{self.project['id']}"
        with patch.object(engine.CodexChatModel, "_agenerate", infer):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                self.assertEqual((await client.post(base + "/pipeline/start")).status_code, 202)
                await asyncio.wait_for(paused.wait(), 15)
                before = engine.get_project(self.project["id"])
                run_id = before["pipeline"]["run_id"]
                worker = engine.WORKERS[run_id]
                workspace = engine.resolve_workspace(before["workspace"])
                files = {path: (workspace / path).read_bytes() for path in (
                    "piece.svg", "workflow/prototype.md", "workflow/art.md", "workflow/art-manifest.json")}
                response = await client.post(base + "/pipeline/cancel")
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["pipeline"]["status"], "cancelled")
                self.assertTrue(cancelled.is_set(), "取消必须传递到正在执行的模型协程")
                self.assertTrue(worker.done(), "停止接口返回前必须结束实际任务")
                self.assertNotIn(run_id, engine.WORKERS)
                self.assertNotIn(self.project["id"], pipeline.PIPELINES)
                with closing(sqlite3.connect(engine.STORE / "checkpoints.sqlite")) as connection:
                    count = connection.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (run_id,)).fetchone()[0]
                self.assertGreater(count, 0, "停止后必须保留持久检查点")
                for path, content in files.items():
                    self.assertEqual((workspace / path).read_bytes(), content)
                activity = (await client.get(base + "/activity")).json()
                self.assertEqual(activity["project"]["pipeline"]["status"], "cancelled")
                response = await client.post(base + "/pipeline/resume")
                self.assertEqual(response.status_code, 202, response.text)
                finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertEqual(finished["stages"][0], before["stages"][0], "已完成的策划阶段不能重跑")
        self.assertEqual(finished["stages"][1]["run_id"], run_id, "继续必须复用原运行及检查点")
        self.assertEqual(len(engine.project_runs(self.project["id"])), 4)
        resumed = engine.load("runs", run_id)
        self.assertEqual(resumed["attempt"], 2)
        reports = [item for item in resumed["events"] if item["type"] == "graph_update"
                   and item["data"].get("message", {}).get("tool_call_id") == "art-report"]
        self.assertEqual(len(reports), 1, "检查点内已完成的工具结果不能重复执行")

    async def test_http_stop_and_resume_preserve_unanswered_questions(self):
        """取消待补充任务后继续，原问题仍等待回答，不替用户自动作答。"""
        self.prepare_fixture()
        app = FastAPI()
        app.include_router(router, prefix="/api")
        base = f"/api/workflow/projects/{self.project['id']}"
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model()):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post(base + "/pipeline/start")
                paused = await self.wait_pipeline()
                run_id = paused["pipeline"]["run_id"]
                questions = engine.load("runs", run_id)["interrupts"]
                # 单阶段取消入口也必须同步停止所属全流程。
                response = await client.post(f"/api/workflow/runs/{run_id}/cancel")
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(engine.get_project(self.project["id"])["pipeline"]["status"], "cancelled")
                response = await client.post(base + "/pipeline/resume")
                self.assertEqual(response.status_code, 202, response.text)
                restored = await self.wait_pipeline()
                self.assertEqual(restored["pipeline"]["status"], "awaiting_input")
                self.assertEqual(engine.load("runs", run_id)["interrupts"], questions)
                self.assertFalse(restored.get("human_answers"))
                answers = {item["id"]: item["value"]["options"][0] for item in questions}
                response = await client.post(f"/api/workflow/runs/{run_id}/answers", json={"answers": answers})
                self.assertEqual(response.status_code, 202, response.text)
                finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertEqual(len(finished["human_answers"]), len(questions))

    def test_templates_are_versioned_complete_and_have_no_secret_fields(self):
        templates = list_templates()
        ludo = next(item for item in templates if item["id"] == "ludo-classic")
        self.assertEqual(ludo["model_provider"], "api-key")
        self.assertIn("azure-image2-generation/SKILL.md", ludo["production_plan"]["stages"]["art"]["skill_paths"])
        with self.assertRaises(ValidationError):
            WorkflowTemplate.model_validate({**ludo, "api_key": "禁止凭据"})
        with self.assertRaises(ValidationError):
            ProductionPlan.model_validate(simple_plan(stages={}))
        with self.assertRaises(ValidationError):
            ProductionPlan.model_validate(simple_plan(publish_slug="../old-game"))

    async def test_missing_skill_is_rejected_before_project_creation(self):
        value = simple_plan()
        value["stages"]["art"]["skill_paths"] = ["missing/SKILL.md"]
        with self.assertRaisesRegex(ValueError, "Skill 不存在"):
            engine.create_project("无效模板", "", None, [], production_plan=value)
        self.assertEqual(len(engine.list_projects()), 1)

    async def test_independent_test_failure_returns_to_code_once(self):
        self.prepare_fixture()
        normal = self.scripted_model(ask=False)

        async def infer(model, messages, **kwargs):
            context = next(json.loads(item.content) for item in messages if item.type == "human")
            project = engine.get_project(self.project["id"])
            if context["stage"] == "test" and not project["pipeline"].get("repair_cycles"):
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="测试阶段未交付有效证据"))])
            return await normal(model, messages, **kwargs)

        with patch.object(engine.CodexChatModel, "_agenerate", infer):
            pipeline.start_pipeline(self.project["id"])
            finished = await self.wait_pipeline()
        self.assertEqual(finished["pipeline"]["status"], "completed", finished["pipeline"])
        self.assertEqual(finished["pipeline"]["repair_cycles"], 1)
        records = engine.project_runs(self.project["id"])
        self.assertEqual([item["stage"] for item in reversed(records)], ["prototype", "art", "code", "test", "code", "test"])
        self.assertNotIn("publication", finished)

    async def test_template_http_validation_and_project_idempotency(self):
        app = FastAPI(); app.include_router(router, prefix="/api")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            templates = (await client.get("/api/workflow/templates")).json()
            value = next(item for item in templates if item["id"] == "web-game")
            self.assertEqual((await client.post("/api/workflow/templates/validate", json=value)).status_code, 200)
            self.assertEqual((await client.post("/api/workflow/templates/validate", json={**value, "api_key": "不允许"})).status_code, 422)
            invalid = {**value, "references": ["../../backend/.env"]}
            self.assertEqual((await client.post("/api/workflow/templates/validate", json=invalid)).status_code, 409)
        first = engine.create_project("幂等计划", "", None, [], production_plan=simple_plan(), request_id="same-plan")
        again = engine.create_project("幂等计划", "", None, [], production_plan=simple_plan(), request_id="same-plan")
        self.assertEqual(first["pipeline"], again["pipeline"])
        explicit_manual = engine.create_project("幂等计划", "", None, [], production_plan=simple_plan(autonomous=False), request_id="same-plan")
        self.assertEqual(first["id"], explicit_manual["id"], "旧请求未携带开关与显式关闭应视为相同提交")
        with self.assertRaisesRegex(ValueError, "不同参数"):
            engine.create_project("幂等计划", "", None, [], production_plan=simple_plan(autonomous=True), request_id="same-plan")
        with self.assertRaisesRegex(ValueError, "不同参数"):
            engine.create_project("幂等计划", "", None, [], production_plan=simple_plan(auto_publish=True), request_id="same-plan")

    async def test_waiting_input_reserves_overlapping_workspace_and_can_cancel(self):
        self.prepare_fixture()
        with patch.object(engine.CodexChatModel, "_agenerate", self.scripted_model()):
            pipeline.start_pipeline(self.project["id"])
            paused = await self.wait_pipeline()
            other = engine.create_project("重叠工作区", "", self.project["workspace"] + "/child", [])
            with self.assertRaisesRegex(ValueError, "工作区"):
                engine.start_run(other["id"], "prototype")
            run_id = paused["pipeline"]["run_id"]
            await engine.cancel_run(run_id)
            self.assertEqual(engine.get_project(self.project["id"])["pipeline"]["status"], "cancelled")
            pipeline.resume_pipeline(self.project["id"])
            paused_again = await self.wait_pipeline()
            self.assertEqual(paused_again["pipeline"]["status"], "awaiting_input")
            self.assertEqual(len(engine.project_runs(self.project["id"])), 1)

    async def test_create_request_can_start_without_a_second_browser_request(self):
        app = FastAPI(); app.include_router(router, prefix="/api")

        async def hold(run_id, resume=False):
            await asyncio.Event().wait()

        # 项目初始化已有独立用例；这里核验 HTTP 入口的明确启动标志与旧默认兼容。
        with patch.object(engine, "create_project", return_value=self.project), patch.object(engine, "execute_run", hold):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                payload = {"name": "测试", "production_plan": simple_plan(), "start_immediately": True}
                response = await client.post("/api/workflow/projects", json=payload)
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["pipeline"]["status"], "running")
                again = await client.post("/api/workflow/projects", json=payload)
                self.assertEqual(again.json()["pipeline"]["id"], response.json()["pipeline"]["id"])
                self.assertEqual((await client.post("/api/workflow/projects", json={"name": "缺计划", "start_immediately": True})).status_code, 409)
                await asyncio.sleep(0.02)
                self.assertEqual(len(engine.project_runs(self.project["id"])), 1)
