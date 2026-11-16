"""远程人工补充的持久幂等、问题分页和安全结果投影回归。"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app import config
from app.services.workflow import engine, pipeline, remote


class HumanAnswerSubmissionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(engine, "ROOT", self.root), patch.object(engine, "STORE", self.root / "state"),
                        patch.object(engine, "KNOWLEDGE_DIR", self.root / "knowledge")]
        for item in self.patches:
            item.start()
        self.project = engine.create_project("远程补充测试", "蓝色棋盘", "games/demo", [])
        self.run = self.create_waiting_run(self.project, "waiting-run")

        async def hold_execution(*args, **kwargs):
            # 只隔离模型推理；排队、持久记录与调度仍使用生产函数。
            await asyncio.Event().wait()

        self.execute = AsyncMock(side_effect=hold_execution)
        self.worker_patch = patch.object(engine, "execute_run", self.execute)
        self.worker_patch.start()

    async def asyncTearDown(self):
        await engine.shutdown_workers()
        engine.WORKERS.clear()
        pipeline.PIPELINES.clear()
        self.worker_patch.stop()
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    def create_waiting_run(self, project, identifier, count=1):
        run = {"id": identifier, "project_id": project["id"], "stage": "prototype", "status": "awaiting_input",
               "progress": 20, "attempt": 1, "events": [], "artifacts": [], "summary": "", "error": None,
               "created_at": engine.now(), "updated_at": engine.now(), "autonomous": False,
               "interrupts": [{"id": f"question-{index}", "value": {
                   "kind": "clarification", "question": f"问题 {index}：选择配色", "context": "用于棋盘主题", "options": ["蓝色", "紫色"]}}
                   for index in range(count)]}
        engine.save("runs", run)
        project["stages"][0].update(status="awaiting_input", run_id=identifier)
        engine.save("projects", project)
        return run

    def answer(self, run_id=None, answers=None, request_id="answer-001", scope="mcp:mac-one"):
        return pipeline.answer_run(run_id or self.run["id"], {"question-0": "蓝色"} if answers is None else answers,
                                   request_id=request_id, request_scope=scope)

    async def test_duplicate_answer_returns_current_run_without_second_worker_or_answer(self):
        first = self.answer()
        worker = engine.WORKERS[self.run["id"]]
        second = self.answer()
        self.assertEqual(first["id"], second["id"])
        self.assertIs(worker, engine.WORKERS[self.run["id"]])
        await asyncio.sleep(0)
        self.execute.assert_awaited_once_with(self.run["id"], resume=True)
        saved = engine.load("runs", self.run["id"])
        self.assertEqual(saved["pending_answers"], {"question-0": "蓝色"})
        self.assertEqual(len(saved["answer_submissions"]), 1)
        self.assertEqual(sum(event["type"] == "human_input_answered" for event in saved["events"]), 1)
        project = engine.load("projects", self.project["id"])
        self.assertEqual(len(project["human_answers"]), 1)
        self.assertEqual(project["human_answers"][0]["answer"], "蓝色")

    async def test_changed_answers_and_reused_request_id_for_another_run_are_rejected(self):
        self.answer()
        with self.assertRaisesRegex(ValueError, "不同参数"):
            self.answer(answers={"question-0": "紫色"})
        other = engine.create_project("另一项目", "", "games/other", [])
        other_run = self.create_waiting_run(other, "other-run")
        with self.assertRaisesRegex(ValueError, "不同参数"):
            self.answer(run_id=other_run["id"])
        # 请求身份按认证调用方隔离，另一个客户端的同名标识不冲突。
        accepted = self.answer(run_id=other_run["id"], scope="mcp:mac-two")
        self.assertEqual(accepted["id"], other_run["id"])

    async def test_retry_after_shutdown_reads_persistent_receipt_without_resuming_again(self):
        self.answer()
        await asyncio.sleep(0)
        await engine.shutdown_workers()
        engine.WORKERS.clear()
        self.execute.reset_mock()
        result = self.answer()
        self.assertEqual(result["status"], "interrupted")
        self.assertEqual(engine.WORKERS, {})
        self.execute.assert_not_called()

    async def test_old_request_does_not_answer_a_new_interrupt_batch(self):
        self.answer()
        worker = engine.WORKERS.pop(self.run["id"])
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
        engine.set_status(self.run["id"], "awaiting_input", interrupts=[{
            "id": "new-question", "value": {"question": "选择对手", "options": ["AI", "同屏"]}}])
        result = self.answer()
        self.assertEqual(result["status"], "awaiting_input")
        self.assertEqual(result["interrupts"][0]["id"], "new-question")
        self.assertNotIn(self.run["id"], engine.WORKERS)
        with self.assertRaisesRegex(ValueError, "全部问题"):
            self.answer(request_id="new-operation")

    async def test_stale_wrong_partial_and_empty_answers_are_rejected_before_scheduling(self):
        for answers in ({"question-0": " "}, {"question-0": "x" * 12001}, {"question-0": 3}, {}):
            with self.subTest(answers=str(answers)[:60]), self.assertRaises(ValueError):
                self.answer(answers=answers)
        with self.assertRaisesRegex(ValueError, "全部问题"):
            self.answer(answers={"other-run-question": "蓝色"})
        engine.set_status(self.run["id"], "awaiting_input", interrupts=[*self.run["interrupts"], {
            "id": "second-question", "value": {"question": "选择对手"}}])
        with self.assertRaisesRegex(ValueError, "全部问题"):
            self.answer()
        project = engine.load("projects", self.project["id"])
        project["stages"][0]["run_id"] = "newer-run"
        engine.save("projects", project)
        with self.assertRaisesRegex(ValueError, "新运行取代"):
            self.answer()
        self.execute.assert_not_called()
        self.assertNotIn("human_answers", engine.load("projects", self.project["id"]))

    async def test_all_paginated_questions_can_be_answered_together(self):
        run = self.create_waiting_run(self.project, self.run["id"], count=60)
        questions = []
        offset = 0
        while True:
            page = remote.interrupt_page(run, offset, 20)
            questions.extend(page["interrupts"])
            if not page["has_more"]:
                break
            offset = page["next_offset"]
        result = self.answer(run_id=run["id"], answers={item["id"]: "蓝色" for item in questions})
        self.assertEqual(len(result["pending_answers"]), 60)
        self.assertEqual(result["status"], "queued")
        self.assertFalse(remote.run_view(result)["interrupts"])


class RemoteWorkflowProjectionTests(unittest.TestCase):
    def run_fixture(self, count=1):
        return {"id": "remote-run", "project_id": "project", "stage": "prototype", "status": "awaiting_input",
                "progress": 20, "attempt": 1, "events": [], "artifacts": [], "summary": "已读取需求", "error": None,
                "pipeline_id": "production-pipeline", "autonomous": False, "pending_answers": {"private": "旧答案"},
                "initial_snapshot": {"private": "源码内容"}, "model_context": "不应返回的模型上下文",
                "interrupts": [{"id": f"question-{index}", "private": "内部字段", "value": {
                    "kind": "clarification", "question": "选择配色", "context": "背景说明", "options": ["蓝色", "紫色"],
                    "api_key": "不应暴露", "encrypted_content": "不可返回的推理块"}} for index in range(count)]}

    def test_run_view_exposes_pending_questions_and_no_private_context(self):
        run = self.run_fixture(25)
        result = remote.run_view(run)
        self.assertTrue(result["requires_input"])
        self.assertFalse(result["requires_confirmation"])
        self.assertEqual(result["pipeline_id"], "production-pipeline")
        self.assertFalse(result["autonomous"])
        self.assertEqual(result["interrupt_count"], 25)
        self.assertEqual(len(result["interrupts"]), 20)
        self.assertTrue(result["has_more_interrupts"])
        second = remote.interrupt_page(run, offset=20)
        self.assertEqual(len(second["interrupts"]), 5)
        self.assertFalse(second["has_more"])
        self.assertEqual(second["next_offset"], 25)
        self.assertEqual(result["interrupts"][0], {"id": "question-0", "value": {
            "kind": "clarification", "question": "选择配色", "context": "背景说明", "options": ["蓝色", "紫色"]}})
        encoded = json.dumps(result, ensure_ascii=False)
        for forbidden in ("model_context", "initial_snapshot", "pending_answers", "api_key", "encrypted_content", "内部字段"):
            self.assertNotIn(forbidden, encoded)

    def test_answered_or_completed_runs_do_not_expose_historical_interrupts(self):
        for status in ("queued", "running", "completed", "failed", "cancelled", "interrupted"):
            with self.subTest(status=status):
                run = self.run_fixture()
                run["status"] = status
                result = remote.run_view(run)
                self.assertFalse(result["requires_input"])
                self.assertEqual(result["interrupts"], [])
                self.assertEqual(remote.interrupt_page(run)["total"], 0)

    def test_question_payload_is_bounded_and_pagination_is_explicit(self):
        run = self.run_fixture()
        run["interrupts"][0]["value"].update(question="问" * 3000, context="说" * 5000, options=["选" * 900] * 12)
        value = remote.interrupt_page(run)["interrupts"][0]["value"]
        self.assertEqual(len(value["question"]), 2000)
        self.assertEqual(len(value["context"]), 4000)
        self.assertEqual(len(value["options"]), 8)
        self.assertEqual(len(value["options"][0]), 500)
        self.assertEqual(remote.interrupt_page(run, offset=50)["interrupts"], [])
        for offset, limit in ((-1, 20), (0, 0), (0, 51)):
            with self.assertRaises(ValueError):
                remote.interrupt_page(run, offset, limit)

    def test_project_view_preserves_execution_and_publication_summary_only(self):
        project = {"id": "project", "name": "远程项目", "workspace": "/private/workspace",
                   "stages": [{"id": "art", "status": "completed", "internal_model_payload": "内部阶段上下文"}],
                   "references": ["uploads/reference.zip"], "knowledge_paths": ["genre/docs/board-games.md"],
                   "production_plan": {"template_id": "ludo-classic", "art_requirements": "沿用原版贴图",
                       "autonomous": True, "auto_publish": True, "publish_slug": "ludo-demo", "api_key": "内部凭据",
                       "stages": {"art": {"prompt": "不应返回的完整阶段提示词", "skill_mode": "manual",
                                           "skill_paths": ["art/SKILL.md"]}}},
                   "pipeline": {"id": "pipeline", "status": "completed", "run_id": "run", "current_stage": "test",
                                "error": None, "internal_model_payload": "不可返回"},
                   "publication": {"url": "https://example.com/games/ludo/index.html", "slug": "ludo-demo",
                                   "bytes": 1024, "file_count": 5, "files": [{"path": "内部文件列表"}], "token": "内部凭据"}}
        result = remote.project_view(project)
        self.assertEqual(result["pipeline"]["status"], "completed")
        self.assertTrue(result["production_plan"]["autonomous"])
        self.assertEqual(result["production_plan"]["stages"]["art"]["skill_paths"], ["art/SKILL.md"])
        self.assertEqual(result["references"], project["references"])
        self.assertEqual(result["publication"]["file_count"], 5)
        self.assertEqual(result["publication"]["url"], project["publication"]["url"])
        encoded = json.dumps(result, ensure_ascii=False)
        for forbidden in ("workspace", "api_key", "internal_model_payload", "token", "内部凭据", "完整阶段提示词", "内部文件列表"):
            self.assertNotIn(forbidden, encoded)

    def test_run_and_pipeline_errors_redact_configured_credentials(self):
        run = self.run_fixture()
        run["error"] = "上游拒绝：演示密钥"
        project = {"pipeline": {"status": "failed", "error": "上游拒绝：演示密钥"}}
        with patch.object(config, "LLM_API_KEY", "演示密钥"):
            self.assertNotIn("演示密钥", remote.run_view(run)["error"])
            self.assertNotIn("演示密钥", remote.project_view(project)["pipeline"]["error"])


if __name__ == "__main__":
    unittest.main()
