"""工具模块拆分回归：独立运行上下文、只读边界与真实验证记录。"""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app import config
from app.services.workflow.publishing import build_manifest
from app.services.workflow.tools import create_tool_guard, create_workflow_tools


class WorkflowToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def create_tools(self, name):
        """每组工具使用独立根目录、知识目录、运行记录和事件接收器。"""
        root = self.root / name
        workspace = root / "games" / "demo"
        workspace.mkdir(parents=True)
        (root / "ref").mkdir()
        (root / "ref" / "guide.md").write_text(name, encoding="utf-8")
        skill = root / "knowledge" / "skill" / "docs" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}技能", encoding="utf-8")
        (skill / "guide.md").write_text(f"{name}配套资料", encoding="utf-8")
        content = f"{name}的冻结知识正文"
        run = {"id": name, "attempt": 1, "knowledge_snapshot": [{
            "path": "genre/docs/guide.md", "content": content,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
        }]}
        events = []
        tools = create_workflow_tools(
            root=root, knowledge_dir=root / "knowledge", workspace=workspace,
            run=run, emit=lambda *args: events.append(args), load_run=lambda: run,
        )
        return {item.name: item for item in tools}, workspace, run, events

    async def test_tool_instances_keep_paths_knowledge_and_events_isolated(self):
        first = self.create_tools("first")
        second = self.create_tools("second")
        for name, (tools, workspace, run, events) in [("first", first), ("second", second)]:
            self.assertEqual(await tools["read_reference"].ainvoke({"path": "ref/guide.md"}), name)
            self.assertEqual(await tools["read_skill"].ainvoke({"path": "demo/SKILL.md"}), f"# {name}技能")
            # 兼容入口转发配套资料，仍绑定本组工具的知识目录。
            self.assertEqual(await tools["read_skill"].ainvoke({"path": "demo/guide.md"}), f"{name}配套资料")
            frozen = await tools["read_game_knowledge"].ainvoke({"path": "genre/docs/guide.md"})
            self.assertEqual(frozen, run["knowledge_snapshot"][0]["content"])
            with self.assertRaises(ValueError):
                await tools["read_reference"].ainvoke({"path": "../outside.md"})
            with self.assertRaises(ValueError):
                await tools["read_game_knowledge"].ainvoke({"path": "unselected.md"})
            self.assertEqual([item[0] for item in events], ["reference_read", "skill_read", "skill_resource_read", "knowledge_read"])
        self.assertNotEqual(first[3][-1][2]["sha256"], second[3][-1][2]["sha256"])

    async def test_invalid_validation_commands_never_start_a_process(self):
        tools, _, _, events = self.create_tools("invalid")
        with patch("app.services.workflow.tools.asyncio.create_subprocess_exec", new_callable=AsyncMock) as spawn:
            for command in ["npm install", "npm test; echo bad", "node scripts/../outside.cjs", "node scripts/check.cjs | cat"]:
                with self.subTest(command=command), self.assertRaises(ValueError):
                    await tools["run_validation"].ainvoke({"command": command})
            spawn.assert_not_called()
        self.assertEqual(events, [])

    async def test_tool_error_keeps_call_identity_and_safe_location_arguments(self):
        """纠错结果继续交给模型，页面按相同调用 ID 展示一次失败。"""
        events = []
        guard = create_tool_guard(self.root, lambda *args: events.append(args))
        call = {"id": "missing-member", "name": "read_reference_archive", "args": {
            "path": "demo.zip", "member": "assets/config.json", "query": "测试令牌",
            "content": "不应复制的正文", "api_key": "测试令牌"}}
        handler = AsyncMock(side_effect=ValueError("包内不存在指定文件；测试令牌"))
        with patch.object(config, "LLM_API_KEY", "测试令牌"):
            result = await guard.awrap_tool_call(SimpleNamespace(tool_call=call), handler)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_call_id, call["id"])
        data = events[0][2]
        self.assertEqual(data["call_id"], call["id"])
        self.assertEqual(data["tool"], call["name"])
        self.assertEqual(data["arguments"]["member"], "assets/config.json")
        self.assertNotIn("content", data["arguments"])
        self.assertNotIn("api_key", data["arguments"])
        self.assertNotIn("测试令牌", json.dumps(data, ensure_ascii=False) + str(result.content))
        self.assertEqual(handler.await_count, 1)

    @unittest.skipUnless(shutil.which("node"), "当前环境未安装 Node，无法运行真实验证脚本")
    async def test_validation_records_current_attempt_and_workspace_evidence(self):
        tools, workspace, run, events = self.create_tools("validation")
        (workspace / "scripts").mkdir()
        (workspace / "scripts" / "check.cjs").write_text(
            'const fs = require("node:fs");\n'
            'fs.mkdirSync("evidence", { recursive: true });\n'
            'fs.writeFileSync("evidence/result.json", JSON.stringify({ passed: true }));\n'
            'console.log("验证成功");\n', encoding="utf-8",
        )
        # 建立工具后更新尝试次数，验证工具必须读取最新记录，不能捕获旧值。
        run["attempt"] = 2
        result = json.loads(await tools["run_validation"].ainvoke({"command": "node scripts/check.cjs"}))
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["attempt"], 2)
        self.assertIn("验证成功", result["output"])
        self.assertEqual(result["source_before"], result["source_after"])
        self.assertEqual(result["changed_paths"], ["evidence/result.json"])
        self.assertTrue(json.loads((workspace / "evidence" / "result.json").read_text())["passed"])
        self.assertEqual([item[0] for item in events], ["validation_started", "validation_completed"])
        self.assertEqual(events[-1][2], result)

    @unittest.skipUnless(shutil.which("node"), "当前环境未安装 Node，无法运行真实验证脚本")
    async def test_validation_binds_actual_dist_bytes_even_when_source_is_unchanged(self):
        """真实 Node 生成构建；仅改 dist 时，发布所用构建指纹也必须随验证更新。"""
        tools, workspace, _, events = self.create_tools("build-fingerprint")
        scripts = workspace / "scripts"
        scripts.mkdir()
        (scripts / "build.cjs").write_text(
            'const fs = require("node:fs");\n'
            'fs.mkdirSync("dist", { recursive: true });\n'
            'fs.writeFileSync("dist/index.html", \'<!doctype html><script src="./game.js"></script>\');\n'
            'fs.writeFileSync("dist/game.js", \'console.log("初始构建");\');\n'
            'console.log("已写入真实构建");\n', encoding="utf-8",
        )
        (scripts / "check.cjs").write_text(
            'const fs = require("node:fs");\n'
            'const assert = require("node:assert/strict");\n'
            'assert.ok(fs.readFileSync("dist/index.html", "utf8").includes("./game.js"));\n'
            'assert.ok(fs.readFileSync("dist/game.js", "utf8").length > 0);\n'
            'console.log("构建文件读取验证通过");\n', encoding="utf-8",
        )
        built = json.loads(await tools["run_validation"].ainvoke({"command": "node scripts/build.cjs"}))
        self.assertEqual(built["exit_code"], 0)
        self.assertTrue((workspace / "dist/index.html").is_file())
        self.assertEqual(built["build_sha256"], build_manifest(workspace)["sha256"])
        first = json.loads(await tools["run_validation"].ainvoke({"command": "node scripts/check.cjs"}))
        self.assertEqual(first["exit_code"], 0)
        self.assertEqual(first["build_sha256"], built["build_sha256"])
        # dist 不参与源码指纹，因此必须另存构建字节证据，不能只认可源码未变。
        (workspace / "dist/game.js").write_text('console.log("修改后的构建");', encoding="utf-8")
        second = json.loads(await tools["run_validation"].ainvoke({"command": "node scripts/check.cjs"}))
        self.assertEqual(second["exit_code"], 0)
        self.assertEqual(second["source_before"], first["source_after"])
        self.assertNotEqual(second["build_sha256"], first["build_sha256"])
        self.assertEqual(second["build_sha256"], build_manifest(workspace)["sha256"])
        self.assertNotIn("build_error", second)
        completed = [item[2] for item in events if item[0] == "validation_completed"]
        self.assertEqual(completed, [built, first, second])
