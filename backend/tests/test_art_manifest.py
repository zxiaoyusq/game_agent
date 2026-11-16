"""美术交接清单的严格字段契约与可操作错误诊断。"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.services.workflow.prompts import build_run_prompts
from app.services.workflow.validation import verify_art_manifest


class ArtManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.path = self.workspace / "public/assets/board.png"
        self.path.parent.mkdir(parents=True)
        Image.new("RGBA", (2, 2), (30, 90, 160, 128)).save(self.path)
        self.asset = {"path": "public/assets/board.png", "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
                      "usage": "对局棋盘", "source": "用户提供原包中的棋盘贴图"}

    def assert_diagnostic(self, manifest, *parts):
        """检查诊断实际指向问题资源和字段，不依赖某个固定完整句式。"""
        with self.assertRaises(ValueError) as caught:
            verify_art_manifest(self.workspace, manifest)
        for part in parts:
            self.assertIn(part, str(caught.exception))
        return str(caught.exception)

    def test_string_source_accepts_separate_structured_details_without_mutation(self):
        manifest = {"assets": [{**self.asset, "source_details": {
            "archive": "original.zip", "member": "atlas.png", "crop": [0, 0, 2, 2]}}]}
        before = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        original = self.path.read_bytes()
        verify_art_manifest(self.workspace, manifest)
        self.assertEqual(json.dumps(manifest, ensure_ascii=False, sort_keys=True), before)
        self.assertEqual(self.path.read_bytes(), original)

    def test_object_source_with_correct_file_hash_identifies_exact_later_asset(self):
        """复现真实故障：前一资源正确、后一资源哈希也正确，但source误写成对象。"""
        second = self.path.with_name("piece-red.png")
        second.write_bytes(self.path.read_bytes())
        wrong = {**self.asset, "path": "public/assets/piece-red.png",
                 "source": {"archive": "original.zip", "member": "piece-red.png"}}
        diagnostic = self.assert_diagnostic({"assets": [self.asset, wrong]}, wrong["path"], "source", "非空字符串")
        self.assertNotIn("哈希不匹配", diagnostic)
        self.assertIsInstance(wrong["source"], dict)

    def test_empty_or_non_string_fields_never_coerce_to_strings(self):
        for field in ("sha256", "usage", "source"):
            for value in (None, " \n", {}, ["来源"], 123):
                with self.subTest(field=field, value=value):
                    self.assert_diagnostic({"assets": [{**self.asset, field: value}]}, self.asset["path"], field)
        for value in (None, "", "  ", {}, ["board.png"]):
            with self.subTest(path=value):
                self.assert_diagnostic({"assets": [{**self.asset, "path": value}]}, "第1项", "path")

    def test_missing_empty_and_stale_files_have_distinct_diagnostics(self):
        missing = {**self.asset, "path": "public/assets/missing.png"}
        self.assert_diagnostic({"assets": [missing]}, missing["path"], "path", "不存在")
        empty = self.path.with_name("empty.png")
        empty.touch()
        self.assert_diagnostic({"assets": [{**self.asset, "path": "public/assets/empty.png",
            "sha256": hashlib.sha256(b"").hexdigest()}]}, "public/assets/empty.png", "文件为空")
        self.assert_diagnostic({"assets": [{**self.asset, "sha256": "0" * 64}]}, self.asset["path"], "sha256", "哈希不匹配")
        directory = {**self.asset, "path": "public/assets"}
        self.assert_diagnostic({"assets": [directory]}, directory["path"], "path", "不是普通文件")

    def test_path_escape_and_invalid_container_still_fail_explicitly(self):
        self.assert_diagnostic({"assets": [{**self.asset, "path": "../outside.png"}]}, "../outside.png", "path无效")
        for value in ([], None, "不是对象"):
            with self.subTest(manifest=value):
                self.assert_diagnostic(value, "JSON对象")
        self.assert_diagnostic({"assets": [None]}, "第1项", "资源对象")
        self.assert_diagnostic({"assets": []}, "空清单")

    def test_resource_and_procedural_kind_requirements_remain_distinct(self):
        document = self.workspace / "design.md"
        document.write_text("# 程序化视觉定义", encoding="utf-8")
        asset = {**self.asset, "path": "design.md", "sha256": hashlib.sha256(document.read_bytes()).hexdigest()}
        self.assert_diagnostic({"assets": [asset]}, "真实图像")
        verify_art_manifest(self.workspace, {"mode": "procedural", "assets": [asset]})

    def test_stage_prompt_declares_string_contract_and_optional_structured_details(self):
        instructions, _ = build_run_prompts({"stage": "art", "skill_paths": [], "prompt": "保留原版贴图"}, {})
        self.assertIn("path、sha256、usage、source均必须是非空字符串", instructions)
        self.assertIn("source_details对象", instructions)
        self.assertIn("source本身仍须用字符串概述", instructions)


if __name__ == "__main__":
    unittest.main()
