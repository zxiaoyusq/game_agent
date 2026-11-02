"""研发状态机与真实证据门禁回归；单元测试替身绝不进入生产路径。"""

import asyncio
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from app.services.workflow import engine
from app.services import knowledge, production_library
from app.api.routes.workflow import ProjectRequest


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    """验证项目隔离、依赖、恢复、取消、下游失效与产物完整性。"""

    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(engine, "ROOT", self.root), patch.object(engine, "STORE", self.root / "state"),
                        patch.object(knowledge, "KNOWLEDGE_DIR", self.root / "knowledge")]
        for item in self.patches:
            item.start()
        self.project = engine.create_project("测试项目", {"idea": "规则验证"}, "games/demo", [])

    async def asyncTearDown(self):
        for task in list(engine.WORKERS.values()):
            task.cancel()
        await asyncio.gather(*engine.WORKERS.values(), return_exceptions=True)
        engine.WORKERS.clear()
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    async def hold_execution(self, *args, **kwargs):
        """仅隔离状态机测试，不会返回虚假的模型或阶段成功。"""
        await asyncio.Event().wait()

    async def start(self, stage="prototype"):
        with patch.object(engine, "execute_run", self.hold_execution):
            return engine.start_run(self.project["id"], stage)

    def create_profile_project(self, genre_id="merge", framework_id="canvas-web", extra_paths=None):
        """在临时知识库准备真实正文，生产配置和快照读取仍使用正式实现。"""
        profile = production_library.resolve_profile(genre_id, framework_id)
        for relative in [*profile["knowledge_paths"], *(extra_paths or [])]:
            target = knowledge.KNOWLEDGE_DIR / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# 测试知识\n\n冻结正文标识：{relative}\n", encoding="utf-8")
        return engine.create_project("合成项目", "拖拽合成与满盘规则", "games/merge", [],
                                     genre_id, framework_id, extra_paths or [])

    def finish_with_artifact(self, run):
        """写入真实临时文件与快照，供确认和哈希测试。"""
        workspace = engine.resolve_workspace(self.project["workspace"])
        report = workspace / "workflow" / f"{run['stage']}.md"
        report.parent.mkdir(exist_ok=True)
        report.write_text("# 实际测试产物\n\n由单元测试写入临时工作区。", encoding="utf-8")
        if run["stage"] == "art":
            resource = workspace / "public" / "assets" / "palette.svg"
            resource.parent.mkdir(parents=True, exist_ok=True)
            resource.write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="8"/></svg>', encoding="utf-8")
            (workspace / "workflow" / "art-manifest.json").write_text(json.dumps({"assets": [{
                "path": "public/assets/palette.svg", "sha256": hashlib.sha256(resource.read_bytes()).hexdigest(),
                "usage": "测试配色资源", "source": "单元测试临时创建",
            }]}), encoding="utf-8")
        artifacts = engine.collect_artifacts(run["id"], workspace, {})
        engine.set_status(run["id"], "awaiting_confirmation", artifacts=artifacts)
        task = engine.WORKERS.pop(run["id"])
        task.cancel()
        return artifacts

    async def test_dependencies_concurrency_and_upstream_invalidation(self):
        with self.assertRaisesRegex(ValueError, "前置"):
            await self.start("art")
        first = await self.start()
        with self.assertRaisesRegex(ValueError, "运行中"):
            await self.start()
        self.finish_with_artifact(first)
        engine.confirm_stage(self.project["id"], "prototype", "审核通过")
        second = await self.start("art")
        self.finish_with_artifact(second)
        engine.confirm_stage(self.project["id"], "art")
        await self.start("prototype")
        project = engine.get_project(self.project["id"])
        self.assertEqual(project["stages"][1]["status"], "pending")
        self.assertIsNone(project["stages"][1]["confirmed_at"])
        with self.assertRaisesRegex(ValueError, "取代"):
            engine.set_status(first["id"], "failed")
            engine.resume_run(first["id"])

    async def test_cancellation_and_restart_recovery(self):
        first = await self.start()
        await engine.cancel_run(first["id"])
        self.assertEqual(engine.load("runs", first["id"])["status"], "cancelled")
        with patch.object(engine, "execute_run", self.hold_execution):
            engine.resume_run(first["id"])
        engine.recover_interrupted_runs()
        current = engine.load("runs", first["id"])
        self.assertEqual(current["status"], "interrupted")
        self.assertEqual(current["events"][-1]["type"], "interrupted")

    async def test_artifact_snapshot_integrity_and_path_boundary(self):
        first = await self.start()
        artifacts = self.finish_with_artifact(first)
        artifact = artifacts[0]
        snapshot = engine.artifact_file(first["id"], artifact["id"])
        snapshot.write_text("被篡改的内容", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "哈希"):
            engine.confirm_stage(self.project["id"], "prototype")
        for value in ["../private", "/tmp/game", "games/../../private", "games"]:
            with self.assertRaises(ValueError):
                engine.resolve_workspace(value)
        with self.assertRaises(ValueError):
            engine.checked_child(self.root, "../../private")

    async def test_default_workspace_is_unique(self):
        first = engine.create_project("独立甲", "", None, [])
        second = engine.create_project("独立乙", "", None, [])
        self.assertNotEqual(first["workspace"], second["workspace"])

    async def test_resume_cannot_bypass_shared_workspace_lock(self):
        first = await self.start()
        await engine.cancel_run(first["id"])
        other = engine.create_project("同工作区项目", "", "games/demo", [])
        with patch.object(engine, "execute_run", self.hold_execution):
            engine.start_run(other["id"], "prototype")
        with self.assertRaisesRegex(ValueError, "工作区"):
            engine.resume_run(first["id"])

    async def test_canonical_and_nested_workspaces_share_lock(self):
        alias = engine.create_project("同目录别名", "", "games//demo", [])
        nested = engine.create_project("嵌套目录", "", "games/demo/child", [])
        self.assertEqual(alias["workspace"], "games/demo")
        first = await self.start()
        with patch.object(engine, "execute_run", self.hold_execution):
            for project in [alias, nested]:
                with self.assertRaisesRegex(ValueError, "父子目录"):
                    engine.start_run(project["id"], "prototype")
        await engine.cancel_run(first["id"])
        with patch.object(engine, "execute_run", self.hold_execution):
            engine.start_run(nested["id"], "prototype")
        with self.assertRaisesRegex(ValueError, "父子目录"):
            engine.resume_run(first["id"])

    async def test_confirmed_report_change_blocks_downstream_start(self):
        """确认快照后的上游正文变化，不能被下游当作已确认输入继续使用。"""
        prototype = await self.start()
        self.finish_with_artifact(prototype)
        engine.confirm_stage(self.project["id"], "prototype")
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "workflow" / "prototype.md").write_text("# 未经确认的新规格", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "原型定义.*重跑"):
            await self.start("art")

    async def test_confirmed_report_change_blocks_resume(self):
        prototype = await self.start()
        self.finish_with_artifact(prototype)
        engine.confirm_stage(self.project["id"], "prototype")
        art = await self.start("art")
        await engine.cancel_run(art["id"])
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "workflow" / "prototype.md").write_text("# 外部修改的规格", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "原型定义.*重跑"):
            engine.resume_run(art["id"])

    async def test_confirmed_art_inputs_are_checked_without_locking_unrelated_files(self):
        prototype = await self.start()
        self.finish_with_artifact(prototype)
        engine.confirm_stage(self.project["id"], "prototype")
        art = await self.start("art")
        self.finish_with_artifact(art)
        engine.confirm_stage(self.project["id"], "art")
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "unrelated.txt").write_text("不属于阶段交接输入", encoding="utf-8")
        code = await self.start("code")
        await engine.cancel_run(code["id"])
        resource = workspace / "public" / "assets" / "palette.svg"
        resource.write_text("<svg>外部更改</svg>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "美术资源.*重跑"):
            engine.resume_run(code["id"])
        with self.assertRaisesRegex(ValueError, "美术资源.*重跑"):
            await self.start("code")

    async def test_confirmed_art_manifest_change_blocks_downstream(self):
        prototype = await self.start()
        self.finish_with_artifact(prototype)
        engine.confirm_stage(self.project["id"], "prototype")
        art = await self.start("art")
        self.finish_with_artifact(art)
        engine.confirm_stage(self.project["id"], "art")
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "workflow" / "art-manifest.json").write_text('{"assets":[]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "美术资源.*重跑"):
            await self.start("code")

    async def test_confirmed_code_fingerprint_change_blocks_test_stage(self):
        prototype = await self.start()
        self.finish_with_artifact(prototype)
        engine.confirm_stage(self.project["id"], "prototype")
        art = await self.start("art")
        self.finish_with_artifact(art)
        engine.confirm_stage(self.project["id"], "art")
        workspace = engine.resolve_workspace(self.project["workspace"])
        source = workspace / "src" / "game.js"
        source.parent.mkdir()
        source.write_text("const state = 1;", encoding="utf-8")
        code = await self.start("code")
        fingerprint = engine.source_fingerprint(workspace)
        for command in ["npm run build", "npm test"]:
            engine.event(code["id"], "validation_completed", "单元测试的验证事件结构", {
                "command": command, "exit_code": 0, "attempt": 1,
                "source_before": fingerprint, "source_after": fingerprint,
            })
        self.finish_with_artifact(code)
        engine.confirm_stage(self.project["id"], "code")
        source.write_text("const state = ;", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "代码与集成.*重跑"):
            await self.start("test")

    async def test_validation_fingerprint_and_resume_attempt(self):
        workspace = engine.resolve_workspace(self.project["workspace"])
        source = workspace / "src" / "game.js"
        source.parent.mkdir()
        source.write_text("const state = 1;", encoding="utf-8")
        fingerprint = engine.source_fingerprint(workspace)
        run = {"attempt": 1, "events": [{"type": "validation_completed", "data": {
            "command": command, "exit_code": 0, "attempt": 1,
            "source_before": fingerprint, "source_after": fingerprint,
        }} for command in ["npm run build", "npm test"]]}
        engine.verify_validation_evidence(run, workspace)
        report = workspace / "evidence" / "report.json"
        report.parent.mkdir()
        report.write_text('{"result":"真实报告"}', encoding="utf-8")
        engine.verify_validation_evidence(run, workspace)
        source.write_text("const state = ;", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "源码/资源已变更"):
            engine.verify_validation_evidence(run, workspace)
        source.write_text("const state = 1;", encoding="utf-8")
        run["attempt"] = 2
        with self.assertRaisesRegex(ValueError, "不能沿用旧成功"):
            engine.verify_validation_evidence(run, workspace)

    async def test_malformed_skill_metadata_does_not_break_registry(self):
        knowledge_root = self.root / "knowledge"
        path = knowledge_root / "skill" / "docs" / "bad" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\n- bad\n---\n正文", encoding="utf-8")
        with patch.object(engine, "KNOWLEDGE_DIR", knowledge_root):
            skills = engine.list_skills()
            self.assertEqual(skills[0]["name"], "bad")
            await self.start()

    async def test_non_sorting_project_uses_selected_profile_and_reads_frozen_knowledge(self):
        """替代推理图以检查真实建图输入和只读工具，不调用外部模型。"""
        self.project = self.create_profile_project()
        run = await self.start()
        task = engine.WORKERS.pop(run["id"])
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        captured = {}
        workspace = engine.resolve_workspace(self.project["workspace"])

        class KnowledgeGraph:
            async def astream(self, inputs, config, stream_mode):
                captured["input"] = json.loads(inputs["messages"][0]["content"])
                reader = next(item for item in captured["tools"] if item.name == "read_game_knowledge")
                for document in run["knowledge_snapshot"]:
                    content = await reader.ainvoke({"path": document["path"]})
                    self_test.assertEqual(content, document["content"])
                report = workspace / "workflow" / "prototype.md"
                report.parent.mkdir()
                report.write_text("# 临时测试的合成规则报告", encoding="utf-8")
                yield {"tools": {"messages": []}}

            async def aget_state(self, config):
                return SimpleNamespace(next=(), values={"messages": [AIMessage(content="测试图完成")]})

        self_test = self

        def build_graph(**kwargs):
            captured.update(kwargs)
            return KnowledgeGraph()

        with patch.object(engine, "inspect_runtime", AsyncMock(return_value={"available": True})), \
             patch.object(engine, "create_deep_agent", side_effect=build_graph):
            await engine.execute_run(run["id"])
        current = engine.load("runs", run["id"])
        self.assertEqual(current["status"], "awaiting_confirmation")
        self.assertEqual(ProjectRequest(name="新项目").references, [])
        self.assertEqual(self.project["references"], [])
        self.assertIn("合成与升级", captured["system_prompt"])
        self.assertIn("Canvas 2D", captured["system_prompt"])
        self.assertNotIn("BallSort", captured["system_prompt"])
        self.assertNotIn("可构建Cocos代码", captured["system_prompt"])
        self.assertNotIn("冻结正文标识", captured["system_prompt"])
        self.assertIn("npm run check", captured["system_prompt"])
        self.assertEqual(len([item for item in current["events"] if item["type"] == "knowledge_read"]), len(run["knowledge_snapshot"]))
        engine.confirm_stage(self.project["id"], "prototype")

    async def test_profile_and_knowledge_are_frozen_during_resume(self):
        self.project = self.create_profile_project(extra_paths=["genre/docs/custom.md"])
        run = await self.start()
        await engine.cancel_run(run["id"])
        document = run["knowledge_snapshot"][0]
        (knowledge.KNOWLEDGE_DIR / document["path"]).write_text("# 之后修改的知识", encoding="utf-8")
        with patch.object(production_library, "resolve_profile", side_effect=AssertionError("恢复不能重新选型")), \
             patch.object(production_library, "snapshot_knowledge", side_effect=AssertionError("恢复不能重新读取知识库")), \
             patch.object(engine, "execute_run", self.hold_execution):
            engine.resume_run(run["id"])
        resumed = engine.load("runs", run["id"])
        self.assertEqual(resumed["production_profile"], run["production_profile"])
        self.assertEqual(resumed["knowledge_snapshot"], run["knowledge_snapshot"])
        self.assertEqual(engine.read_frozen_knowledge(resumed, document["path"])[0], document["content"])
        with self.assertRaisesRegex(ValueError, "未实际读取"):
            engine.verify_knowledge_reads(resumed)
        for item in resumed["knowledge_snapshot"]:
            _, evidence = engine.read_frozen_knowledge(resumed, item["path"])
            engine.event(run["id"], "knowledge_read", "单元测试核对的读取事件", evidence)
        engine.verify_knowledge_reads(engine.load("runs", run["id"]))
        with self.assertRaisesRegex(ValueError, "知识快照"):
            engine.read_frozen_knowledge(resumed, "genre/docs/unselected.md")
        resumed["knowledge_snapshot"][0]["content"] = "篡改后的正文"
        with self.assertRaisesRegex(ValueError, "哈希"):
            engine.read_frozen_knowledge(resumed, document["path"])

    async def test_selected_framework_requires_browser_validation_and_current_attempt(self):
        self.project = self.create_profile_project()
        workspace = engine.resolve_workspace(self.project["workspace"])
        fingerprint = engine.source_fingerprint(workspace)
        run = {"attempt": 1, "production_profile": self.project["production_profile"], "events": []}
        for command in ["npm run build", "npm test"]:
            run["events"].append({"type": "validation_completed", "data": {
                "command": command, "exit_code": 0, "attempt": 1,
                "source_before": fingerprint, "source_after": fingerprint}})
        with self.assertRaisesRegex(ValueError, "重新完成"):
            engine.verify_validation_evidence(run, workspace)
        run["events"].append({"type": "validation_completed", "data": {
            "command": "npm run check", "exit_code": 0, "attempt": 1,
            "source_before": fingerprint, "source_after": fingerprint}})
        engine.verify_validation_evidence(run, workspace)
        run["attempt"] = 2
        with self.assertRaisesRegex(ValueError, "不能沿用旧成功"):
            engine.verify_validation_evidence(run, workspace)
        # 同样的历史两命令记录仍符合旧运行契约，不追加强制浏览器验证。
        legacy = {"attempt": 1, "events": run["events"][:2]}
        engine.verify_validation_evidence(legacy, workspace)

    async def test_knowledge_read_gate_requires_full_coverage_of_frozen_text(self):
        """验证首字符绕过、分页间隙和伪造范围，完整重叠或连续分页可以累计。"""
        content = "甲乙丙丁戊己庚辛壬癸"
        document = {"path": "genre/docs/example.md", "sha256": hashlib.sha256(content.encode()).hexdigest(), "content": content}
        run = {"attempt": 2, "knowledge_snapshot": [document], "events": []}

        def reading(start, end, **overrides):
            return {"type": "knowledge_read", "data": {"path": document["path"], "sha256": document["sha256"],
                    "offset": start, "end": end, "total_chars": len(content), **overrides}}

        invalid = [reading(0, 1), reading(-1, 10), reading(0, 11), reading(0, 0), reading(10, 10),
                   reading(0, 10, path="genre/docs/other.md"), reading(0, 10, sha256="其他正文的哈希"),
                   reading(False, 10), reading(0.0, 10), reading("0", 10), reading(0, "10")]
        for record in invalid:
            run["events"] = [record]
            with self.subTest(evidence=record["data"]), self.assertRaisesRegex(ValueError, "未实际读取"):
                engine.verify_knowledge_reads(run)
        # 事件谎报长度也不能缩短冻结正文；两段之间存在一个字符间隙仍不完整。
        for records in [[reading(0, 1, total_chars=1)], [reading(0, 4), reading(5, 10)]]:
            run["events"] = records
            with self.assertRaisesRegex(ValueError, "未实际读取"):
                engine.verify_knowledge_reads(run)
        # 区间可以乱序、重叠；同一冻结正文跨恢复尝试的读取仍然有效。
        for records in [[reading(4, 10, attempt=2), reading(0, 4, attempt=1)],
                        [reading(3, 10), reading(0, 6)], [reading(0, 10)]]:
            run["events"] = records
            engine.verify_knowledge_reads(run)
        document["content"] = "甲乙丙丁戊己庚辛壬子"
        with self.assertRaisesRegex(ValueError, "未实际读取"):
            engine.verify_knowledge_reads(run)

    async def test_invalid_selected_knowledge_is_rejected_before_project_creation(self):
        self.create_profile_project()
        for path in ["genre/docs/../../secret.md", "/genre/docs/general.md", "skill/docs/test/SKILL.md", "genre/docs/missing.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                engine.create_project("非法资料", "", "games/invalid", [], "merge", "canvas-web", [path])
        link = knowledge.KNOWLEDGE_DIR / "genre" / "docs" / "linked.md"
        link.symlink_to(knowledge.KNOWLEDGE_DIR / "genre" / "docs" / "general.md")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            engine.create_project("链接资料", "", "games/invalid", [], "merge", "canvas-web", ["genre/docs/linked.md"])
        self.assertFalse((self.root / "games" / "invalid").exists())

    async def test_reference_prefix_and_framework_preview_preserve_legacy_behavior(self):
        project = engine.create_project("参考规范化", "", "games/reference", ["ref/examples/guide.md", "examples/guide.md"])
        self.assertEqual(project["references"], ["examples/guide.md"])
        with self.assertRaises(ValueError):
            engine.normalize_reference("ref/../../secret")
        legacy_workspace = engine.resolve_workspace(project["workspace"])
        (legacy_workspace / "index.html").write_text("<!doctype html>", encoding="utf-8")
        self.assertEqual(engine.preview_location(project), (legacy_workspace, "index.html"))
        profiled = self.create_profile_project()
        profiled["production_profile"]["framework"]["preview_entry"] = "export/web/game.html"
        workspace = engine.resolve_workspace(profiled["workspace"])
        self.assertEqual(engine.preview_location(profiled), (workspace / "export" / "web", "game.html"))
        for entry in ["../secret.html", "/tmp/secret.html"]:
            profiled["production_profile"]["framework"]["preview_entry"] = entry
            with self.assertRaises(ValueError):
                engine.preview_location(profiled)

    async def test_asset_manifest_accepts_jpeg_and_procedural_files_but_rejects_empty_or_stale(self):
        workspace = engine.resolve_workspace(self.project["workspace"])
        for filename, content, mode in [("texture.jpeg", b"temporary image fixture", "assets"),
                                        ("model.glb", b"temporary model fixture", "assets"),
                                        ("visual-design.md", "# 以程序绘制角色与背景".encode(), "procedural")]:
            (workspace / filename).write_bytes(content)
            asset = {"path": filename, "sha256": hashlib.sha256(content).hexdigest(), "usage": "临时测试交接", "source": "测试创建"}
            manifest = {"mode": mode, "assets": [asset]}
            engine.verify_art_manifest(workspace, manifest)
            asset["sha256"] = "错误哈希"
            with self.assertRaisesRegex(ValueError, "哈希"):
                engine.verify_art_manifest(workspace, manifest)
        with self.assertRaisesRegex(ValueError, "空清单"):
            engine.verify_art_manifest(workspace, {"mode": "procedural", "assets": []})

    async def test_artifact_provenance_requires_successful_tool_evidence(self):
        run = await self.start()
        workspace = engine.resolve_workspace(self.project["workspace"])
        report = workspace / "workflow" / "prototype.md"
        report.parent.mkdir()
        report.write_text("# 实际模型产物", encoding="utf-8")
        (workspace / "external.js").write_text("const external = true;", encoding="utf-8")
        baseline = engine.snapshot(workspace)
        engine.event(run["id"], "model_completed", "测试中的工具请求", {"tool_calls": [
            {"id": "call-write", "name": "write_file", "args": {"file_path": "/workflow/prototype.md", "content": "# 实际模型产物"}},
        ]})
        engine.event(run["id"], "graph_update", "测试中的真实成功结果结构", {"message": {
            "type": "tool", "status": "success", "tool_call_id": "call-write", "content": "Updated file /workflow/prototype.md",
        }})
        # 即使正文与基线相同，存在成功写入证据仍可归档；外部变化不冒充Agent编辑。
        (workspace / "external.js").write_text("const external = false;", encoding="utf-8")
        artifacts = engine.collect_artifacts(run["id"], workspace, baseline)
        origins = {item["path"]: item["provenance"] for item in artifacts}
        self.assertEqual(origins["workflow/prototype.md"], "agent_edit")
        self.assertEqual(origins["external.js"], "workspace_observation")

    async def test_empty_initial_snapshot_survives_resume(self):
        """空工程首轮生成的文件，恢复成功后仍属于同一运行的产物。"""
        run = await self.start()
        pending = engine.WORKERS.pop(run["id"])
        pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)
        run = engine.load("runs", run["id"])
        run["initial_snapshot"] = {}
        engine.save("runs", run)
        workspace = engine.resolve_workspace(self.project["workspace"])
        (workspace / "game.js").write_text("const state = 1;", encoding="utf-8")
        first_artifacts = engine.collect_artifacts(run["id"], workspace, {})
        engine.set_status(run["id"], "failed", artifacts=first_artifacts, error="测试中的首轮中断")
        seen = {}

        class ResumeGraph:
            """只替代本测试模型图；持久状态、工作区和产物归档均用真实实现。"""

            def __init__(self):
                self.state_calls = 0

            async def aget_state(self, config):
                self.state_calls += 1
                return SimpleNamespace(next=("tools",) if self.state_calls == 1 else (),
                                       values={"messages": [AIMessage(content="测试恢复节点完成")]})

            async def astream(self, inputs, config, stream_mode):
                seen.update(inputs=inputs, config=config)
                report = workspace / "workflow" / "prototype.md"
                report.parent.mkdir()
                report.write_text("# 恢复后的实际临时文件", encoding="utf-8")
                yield {"tools": {"messages": []}}

        with patch.object(engine, "inspect_runtime", AsyncMock(return_value={"available": True})), \
             patch.object(engine, "create_deep_agent", return_value=ResumeGraph()) as graph_factory:
            engine.resume_run(run["id"])
            await engine.WORKERS[run["id"]]
        completed = engine.load("runs", run["id"])
        self.assertEqual(completed["status"], "awaiting_confirmation")
        self.assertEqual(completed["initial_snapshot"], {})
        self.assertEqual({item["path"] for item in completed["artifacts"]}, {"game.js", "workflow/prototype.md"})
        # 挂起工具继续用None输入，当前恢复轮次通过system提供，不插入Human破坏顺序。
        self.assertIsNone(seen["inputs"])
        self.assertEqual(seen["config"]["recursion_limit"], 150)
        self.assertEqual(completed["attempt"], 2)
        system_prompt = graph_factory.call_args.kwargs["system_prompt"]
        self.assertIn("attempt=2", system_prompt)
        self.assertIn("resume=true", system_prompt)
        self.assertIn("当前attempt重新调用run_validation执行npm run build、npm test", system_prompt)
        self.assertIn("npm run check", system_prompt)
        self.assertIn("即使前一attempt验证通过且源码未变，也必须重新执行", system_prompt)

    async def test_concurrent_filesystem_edits_do_not_lose_other_sections(self):
        """真实 FilesystemBackend 并发修改同文件，守卫确保整次编辑及读取串行。"""
        workspace = engine.resolve_workspace(self.project["workspace"])
        document = workspace / "prototype.md"
        document.write_text("\n".join(f"章节{index}：初始内容" for index in range(16)) + "\n", encoding="utf-8")
        backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)
        records = []
        guard = engine.create_tool_guard(workspace, lambda *args: records.append(args))
        active = 0
        peak_active = 0

        async def handler(request):
            nonlocal active, peak_active
            active += 1
            peak_active = max(peak_active, active)
            try:
                args = request.tool_call["args"]
                if request.tool_call["name"] == "read_file":
                    result = await backend.aread(args["file_path"])
                    self.assertIsNone(result.error)
                    content = result.file_data["content"]
                else:
                    result = await backend.aedit(args["file_path"], args["old_string"], args["new_string"])
                    self.assertIsNone(result.error)
                    content = f"Successfully replaced {result.occurrences} instance(s) of the string in '{result.path}'"
                # 明确保留一次调度机会，断言不能有其他工具越过完整文件操作边界。
                await asyncio.sleep(0)
                return ToolMessage(content=content, tool_call_id=request.tool_call["id"], status="success")
            finally:
                active -= 1

        requests = [SimpleNamespace(tool_call={"id": f"edit-{index}", "name": "edit_file", "args": {
            "file_path": "/prototype.md", "old_string": f"章节{index}：初始内容", "new_string": f"章节{index}：更新后的中文内容",
        }}) for index in range(16)]
        requests.append(SimpleNamespace(tool_call={"id": "read-final", "name": "read_file", "args": {"file_path": "/prototype.md"}}))
        results = await asyncio.gather(*(guard.awrap_tool_call(request, handler) for request in requests))
        self.assertTrue(all(result.status == "success" for result in results))
        self.assertEqual(peak_active, 1)
        final_content = document.read_text(encoding="utf-8")
        for index in range(16):
            self.assertIn(f"章节{index}：更新后的中文内容", final_content)
        self.assertNotIn("初始内容", final_content)
        self.assertEqual(sum(record[0] == "file_written" for record in records), 16)

    async def test_real_builtin_failed_edits_are_not_recorded_as_writes(self):
        """只替代测试中的模型推理；真实内置工具失败不能生成写入证据。"""
        workspace = engine.resolve_workspace(self.project["workspace"])
        report = workspace / "workflow" / "prototype.md"
        report.parent.mkdir()
        original = "# 已有报告\n\n保持原文。"
        report.write_text(original, encoding="utf-8")
        calls = [
            {"id": "write-existing", "name": "write_file", "args": {"file_path": "/workflow/prototype.md", "content": original}},
            {"id": "edit-missing", "name": "edit_file", "args": {"file_path": "/workflow/prototype.md", "old_string": "不存在的片段", "new_string": "不应写入"}},
        ]

        async def scripted_inference(model, messages, **kwargs):
            message = AIMessage(content="测试结束") if any(isinstance(item, ToolMessage) for item in messages) else AIMessage(content="", tool_calls=calls)
            return ChatResult(generations=[ChatGeneration(message=message)])

        records = []
        with patch.object(engine.CodexChatModel, "_agenerate", scripted_inference):
            graph = create_deep_agent(model=engine.CodexChatModel(), backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
                                      middleware=[engine.create_tool_guard(workspace, lambda *args: records.append(args))])
            result = await graph.ainvoke({"messages": [{"role": "user", "content": "测试失败路径"}]}, {"recursion_limit": 8})
        tool_results = [item for item in result["messages"] if isinstance(item, ToolMessage)]
        self.assertEqual([item.status for item in tool_results], ["error", "error"])
        self.assertIn("already exists", str(tool_results[0].content))
        self.assertIn("String not found", str(tool_results[1].content))
        self.assertFalse(any(record[0] == "file_written" for record in records))
        self.assertEqual(report.read_text(encoding="utf-8"), original)

    async def test_error_text_with_default_success_cannot_reuse_old_report(self):
        """即使工具包装错误地保留默认success，实际失败正文也不能通过产物门禁。"""
        run = await self.start()
        workspace = engine.resolve_workspace(self.project["workspace"])
        report = workspace / "workflow" / "prototype.md"
        report.parent.mkdir()
        original = "# 既有正文"
        report.write_text(original, encoding="utf-8")
        before = engine.snapshot(workspace)
        backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)
        guard = engine.create_tool_guard(workspace, lambda kind, message, data: engine.event(run["id"], kind, message, data))
        calls = [
            {"id": "write-existing", "name": "write_file", "args": {"file_path": "/workflow/prototype.md", "content": original}},
            {"id": "edit-missing", "name": "edit_file", "args": {"file_path": "/workflow/prototype.md", "old_string": "不存在", "new_string": "替换"}},
        ]

        async def handler(request):
            call = request.tool_call
            if call["name"] == "write_file":
                result = await backend.awrite(call["args"]["file_path"], call["args"]["content"])
            else:
                result = await backend.aedit(call["args"]["file_path"], call["args"]["old_string"], call["args"]["new_string"])
            self.assertTrue(result.error)
            return ToolMessage(content=result.error, tool_call_id=call["id"])

        engine.event(run["id"], "model_completed", "测试中的工具请求", {"tool_calls": calls})
        for call in calls:
            result = await guard.awrap_tool_call(SimpleNamespace(tool_call=call), handler)
            engine.event(run["id"], "graph_update", "测试中的默认状态错误结果", {"message": result.model_dump(mode="json")})
        current = engine.load("runs", run["id"])
        self.assertFalse(any(item["type"] == "file_written" for item in current["events"]))
        self.assertEqual(engine.written_file_evidence(current), {})
        self.assertEqual(engine.collect_artifacts(run["id"], workspace, before), [])
        self.assertEqual(report.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
