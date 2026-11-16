"""代码交接与补测脚本的边界回归；全部夹具写在临时目录。"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app.services.workflow.validation import verify_code_handoff, verify_validation_evidence
from app.services.workflow.workspace import fingerprint_snapshot, snapshot, source_snapshot


class CodeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        for name in ("src/game.js", "scripts/check.mjs", "tests/rules.test.mjs", "public/assets/piece.png"):
            self.write(name, f"夹具内容：{name}")
        baseline = source_snapshot(self.workspace)
        self.code = {"stage": "code", "attempt": 1, "confirmed_source_snapshot": baseline,
                     "initial_snapshot": snapshot(self.workspace), "artifacts": [], "events": self.validations(baseline)}
        self.test = {"stage": "test", "attempt": 1, "initial_snapshot": snapshot(self.workspace), "events": []}

    def write(self, name, content):
        file = self.workspace / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return file

    def validations(self, files):
        """夹具只构造验证记录，真实命令和自动发布另由全流程测试覆盖。"""
        fingerprint = fingerprint_snapshot(files)
        return [{"type": "validation_completed", "data": {
            "command": command, "exit_code": 0, "attempt": 1,
            "source_before": fingerprint, "source_after": fingerprint,
        }} for command in ("npm run build", "npm test")]

    def record_write(self, name, content):
        """模拟真实写入的完整请求、落盘哈希与成功响应，不能只伪造一个成功标志。"""
        file = self.write(name, content)
        call_id = f"write-{len(self.test['events'])}"
        self.test["events"].extend([
            {"type": "model_completed", "data": {"tool_calls": [{
                "id": call_id, "name": "write_file", "args": {"file_path": "/" + name, "content": content}}]}},
            {"type": "file_written", "data": {"path": name, "call_id": call_id,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}},
            {"type": "graph_update", "data": {"message": {
                "type": "tool", "tool_call_id": call_id, "status": "success", "content": "Updated file /" + name}}},
        ])

    def test_supplemental_script_keeps_code_valid_but_requires_fresh_final_tests(self):
        self.test["events"].extend(self.validations(source_snapshot(self.workspace)))
        self.record_write("scripts/test-audit.mjs", "console.log('补充验收');")
        verify_code_handoff(self.code, self.workspace, self.test)
        with self.assertRaisesRegex(ValueError, "重新验证"):
            verify_validation_evidence(self.test, self.workspace)
        self.test["events"].extend(self.validations(source_snapshot(self.workspace)))
        verify_validation_evidence(self.test, self.workspace)
        self.write("scripts/test-audit.mjs", "console.log('外部修改');")
        with self.assertRaisesRegex(ValueError, "未核验的新增文件"):
            verify_code_handoff(self.code, self.workspace, self.test)
        with self.assertRaisesRegex(ValueError, "重新验证"):
            verify_validation_evidence(self.test, self.workspace)

    def test_existing_game_assets_and_tests_cannot_change_even_after_new_success(self):
        for name, original in self.code["confirmed_source_snapshot"].items():
            with self.subTest(path=name):
                file = self.workspace / name
                content = file.read_text()
                self.record_write(name, "未经上游确认的修改")
                self.test["events"].extend(self.validations(source_snapshot(self.workspace)))
                with self.assertRaisesRegex(ValueError, "修改或删除"):
                    verify_code_handoff(self.code, self.workspace, self.test)
                file.unlink()
                with self.assertRaisesRegex(ValueError, "修改或删除"):
                    verify_code_handoff(self.code, self.workspace, self.test)
                self.write(name, content)
                self.assertEqual(source_snapshot(self.workspace)[name], original)

    def test_unrecorded_scripts_and_new_game_files_cannot_use_the_exception(self):
        for name in ("scripts/unknown.mjs", "src/extra.js", "public/assets/extra.png", "package.json"):
            with self.subTest(path=name):
                if name.startswith("scripts/"):
                    self.write(name, "外部新增，不具备工具记录")
                else:
                    self.record_write(name, "测试工具也不能添加游戏运行输入")
                with self.assertRaisesRegex(ValueError, "未核验的新增文件"):
                    verify_code_handoff(self.code, self.workspace, self.test)
                (self.workspace / name).unlink()

    def test_only_failed_or_missing_tool_results_do_not_count_as_new_script_evidence(self):
        self.record_write("tests/new.test.mjs", "console.log('测试');")
        self.test["events"][-1]["data"]["message"]["status"] = "error"
        with self.assertRaisesRegex(ValueError, "未核验的新增文件"):
            verify_code_handoff(self.code, self.workspace, self.test)

    def test_graph_request_needs_successful_matching_result_without_model_callback(self):
        self.record_write("tests/new.test.mjs", "console.log('图消息验收');")
        request = self.test["events"][0]
        self.test["events"][0] = {"type": "graph_update", "data": {"message": {"type": "ai", **request["data"]}}}
        verify_code_handoff(self.code, self.workspace, self.test)
        self.test["events"].pop()
        with self.assertRaisesRegex(ValueError, "未核验的新增文件"):
            verify_code_handoff(self.code, self.workspace, self.test)

    def test_legacy_code_manifest_must_reproduce_the_original_validation_hash(self):
        self.code.pop("confirmed_source_snapshot")
        digest = self.code["initial_snapshot"].pop("src/game.js")
        self.code["artifacts"] = [{"path": "src/game.js", "sha256": digest}]
        self.record_write("scripts/test-audit.mjs", "console.log('补测');")
        verify_code_handoff(self.code, self.workspace, self.test)
        self.code["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "重新验证"):
            verify_code_handoff(self.code, self.workspace, self.test)

    def test_test_restart_can_inherit_previously_checked_supplemental_scripts(self):
        self.record_write("scripts/test-audit.mjs", "console.log('补测');")
        verify_code_handoff(self.code, self.workspace, self.test)
        restarted = {"initial_snapshot": snapshot(self.workspace), "events": []}
        verify_code_handoff(self.code, self.workspace, restarted)
        with self.assertRaisesRegex(ValueError, "重新验证"):
            verify_code_handoff(self.code, self.workspace)

    def test_original_validation_attempt_and_failures_are_still_enforced(self):
        self.record_write("scripts/test-audit.mjs", "console.log('补测');")
        self.code["attempt"] = 2
        with self.assertRaisesRegex(ValueError, "当前恢复尝试"):
            verify_code_handoff(self.code, self.workspace, self.test)
        self.code["attempt"] = 1
        self.code["events"][-1]["data"]["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "当前恢复尝试"):
            verify_code_handoff(self.code, self.workspace, self.test)

    def test_source_manifest_includes_large_files_and_preserves_legacy_hash_format(self):
        self.write("src/大型资源.bin", "x" * 5_000_001)
        self.write("workflow/test.md", "报告不进入运行指纹")
        files = source_snapshot(self.workspace)
        self.assertIn("src/大型资源.bin", files)
        self.assertNotIn("workflow/test.md", files)
        expected = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(fingerprint_snapshot(files), expected)


if __name__ == "__main__":
    unittest.main()
