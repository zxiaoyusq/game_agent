"""运行技能输入快照回归，所有源文件与输出均位于临时目录。"""

import hashlib
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from app.services.workflow import skill_inputs


class SkillInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.knowledge = self.root / "knowledge"
        self.base = self.knowledge / "skill" / "docs"
        self.destination = self.root / "inputs" / "run" / "skills"
        self.entry = "sample/SKILL.md"
        self.nested = "sample/modules/child/SKILL.md"
        self._write(self.entry, "---\nname: sample\ndescription: 示例技能\n---\n完整入口正文")
        self._write(self.nested, "# 子技能\n只按明确选择调用")
        self._write("sample/references/guide.md", "参考正文：按当前项目类型判断。")
        self._write("sample/scripts/check.py", "raise RuntimeError('快照不能执行脚本')\n")
        self._write("other/SKILL.md", "# 另一个未选择的包")
        self.available = [self._metadata(path) for path in [self.entry, self.nested, "other/SKILL.md"]]

    def _write(self, relative, content):
        path = self.base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)
        return path

    def _metadata(self, relative):
        return {"path": relative, "name": "示例技能", "description": "按需调用",
                "version": "1.2.0", "sha256": hashlib.sha256((self.base / relative).read_bytes()).hexdigest()}

    def _freeze(self, paths=None):
        return skill_inputs.freeze_skill_inputs(paths if paths is not None else [self.entry], self.available,
                                                self.knowledge, self.destination)

    def test_frozen_entry_and_resources_survive_source_changes_and_deletion(self):
        """归档与当前知识库完全独立，恢复不追随后来修改或删除的来源。"""
        run = self._freeze()
        original = (self.base / self.entry).read_text()
        self._write(self.entry, "后来修改的入口")
        shutil.rmtree(self.base / "sample")
        text, evidence = skill_inputs.read_frozen_skill(run, self.entry, self.destination, entry=True, offset=7, limit=1)
        self.assertEqual(text, original)
        self.assertEqual((evidence["offset"], evidence["end"], evidence["total_chars"]), (0, len(original), len(original)))
        self.assertTrue(evidence["frozen"])
        self.assertEqual(evidence["version"], "1.2.0")
        self.assertEqual(run["skill_snapshot"][0]["total_chars"], len(original))
        guide, read = skill_inputs.read_frozen_skill(run, "sample/references/guide.md", self.destination, offset=2, limit=6)
        self.assertEqual(guide, "正文：按当前")
        self.assertEqual((read["offset"], read["end"]), (2, 8))
        script, _ = skill_inputs.read_frozen_skill(run, "sample/scripts/check.py", self.destination)
        self.assertIn("快照不能执行脚本", script)
        self.assertFalse((self.destination / "other").exists())

    def test_same_package_and_duplicate_selections_are_read_once(self):
        """同包多入口只扫描一次，入口的预检查字节直接复用于归档。"""
        reads = Counter()
        original = Path.read_bytes

        def track(path):
            reads[path] += 1
            return original(path)

        with patch.object(Path, "read_bytes", track):
            run = self._freeze([self.entry, self.nested, self.entry])
        self.assertEqual(len(run["skill_snapshot"]), 2)
        self.assertEqual(len(run["skill_resources"]), 4)
        self.assertTrue(all(count == 1 for path, count in reads.items() if path.is_relative_to(self.base)))
        child, _ = skill_inputs.read_frozen_skill(run, self.nested, self.destination, entry=True)
        self.assertIn("子技能", child)

    def test_skips_hidden_binary_links_and_large_supporting_files(self):
        """资料脚本只复制文本；图片、大型HTML、隐藏配置及链接不会进入快照。"""
        self._write("sample/.secret", "不应读取")
        self._write("sample/node_modules/dependency.js", "不应读取")
        self._write("sample/assets/image.png", b"looks like text")
        self._write("sample/assets/unknown.bin", b"binary\x00data")
        self._write("sample/assets/legacy.txt", b"\xff\xfe")
        self._write("sample/assets/large.html", b"x" * (skill_inputs.MAX_FILE_BYTES + 1))
        outside = self.root / "outside.txt"
        outside.write_text("外部内容")
        (self.base / "sample" / "linked.txt").symlink_to(outside)
        (self.base / "sample" / "linked-directory").symlink_to(self.root, target_is_directory=True)
        run = self._freeze()
        self.assertEqual(len(run["skill_resources"]), 4)
        listing, evidence = skill_inputs.read_frozen_skill(run, "sample", self.destination)
        self.assertIn("文本快照", listing)
        self.assertNotIn("assets", listing)
        self.assertNotIn("linked", listing)
        self.assertEqual(evidence["kind"], "directory")

    def test_unselected_entry_cannot_be_read_through_resource_tool(self):
        """未选入口即使位于同包，也不能借支持资料读取绕过人工排除。"""
        run = self._freeze()
        for entry in [False, True]:
            with self.subTest(entry=entry), self.assertRaisesRegex(ValueError, "未被本次运行选中"):
                skill_inputs.read_frozen_skill(run, self.nested, self.destination, entry=entry)
        with self.assertRaises(ValueError):
            skill_inputs.read_frozen_skill(run, "sample/modules/child", self.destination)
        with self.assertRaises(ValueError):
            skill_inputs.read_frozen_skill(run, "other/SKILL.md", self.destination)

    def test_resource_and_entry_tampering_are_rejected(self):
        run = self._freeze()
        for relative in [self.entry, "sample/references/guide.md"]:
            target = self.destination / relative
            target.write_text("被修改的快照")
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, "哈希不匹配"):
                skill_inputs.read_frozen_skill(run, relative, self.destination, entry=relative == self.entry)

    def test_selection_hash_change_or_missing_entry_prevents_snapshot(self):
        for change in ["modify", "delete"]:
            with self.subTest(change=change):
                if change == "modify":
                    self._write(self.entry, "发现入口后来源已修改")
                else:
                    (self.base / self.entry).unlink()
                with self.assertRaises(ValueError):
                    self._freeze()
                self.assertFalse(self.destination.exists())

    def test_large_or_binary_selected_entry_is_an_error(self):
        for content in [b"x" * (skill_inputs.MAX_FILE_BYTES + 1), b"x\x00y", b"\xff", b"  "]:
            with self.subTest(length=len(content)):
                self._write(self.entry, content)
                self.available[0] = self._metadata(self.entry)
                with self.assertRaises(ValueError):
                    self._freeze()
                self.assertFalse(self.destination.exists())

    def test_total_size_limit_and_write_failure_remove_partial_destination(self):
        with patch.object(skill_inputs, "MAX_TOTAL_BYTES", 100), self.assertRaisesRegex(ValueError, "16 MB"):
            self._freeze()
        self.assertFalse(self.destination.exists())
        original = Path.write_bytes

        def fail_supporting_file(path, data):
            if path == self.destination / "sample/references/guide.md":
                raise OSError("模拟磁盘写入失败")
            return original(path, data)

        with patch.object(Path, "write_bytes", fail_supporting_file), self.assertRaises(OSError):
            self._freeze()
        self.assertFalse(self.destination.exists())
        self.assertTrue((self.base / self.entry).is_file())

    def test_existing_destination_is_never_overwritten_or_cleaned(self):
        self.destination.mkdir(parents=True)
        old = self.destination / "existing.txt"
        old.write_text("旧运行输入")
        with self.assertRaisesRegex(ValueError, "已存在"):
            self._freeze()
        self.assertEqual(old.read_text(), "旧运行输入")

    def test_manual_empty_selection_is_valid_and_has_no_readable_skill(self):
        run = self._freeze([])
        self.assertEqual(run, {"skill_snapshot": [], "skill_resources": []})
        self.assertEqual(list(self.destination.iterdir()), [])
        with self.assertRaises(ValueError):
            skill_inputs.read_frozen_skill(run, self.entry, self.destination, entry=True)

    def test_paths_and_source_destination_ancestor_links_are_rejected(self):
        for path in ["/sample/SKILL.md", "../sample/SKILL.md", "sample/../SKILL.md", "sample\\SKILL.md", "sample//SKILL.md", "sample/.private/SKILL.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self._freeze([path])
        linked = self.root / "link"
        linked.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            skill_inputs.freeze_skill_inputs([self.entry], self.available, linked / "knowledge", self.destination)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            skill_inputs.freeze_skill_inputs([self.entry], self.available, self.knowledge, linked / "new-output")
        original = self.base / self.entry
        original.unlink()
        original.symlink_to(self.base / self.nested)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self._freeze()

    def test_snapshot_reads_reject_path_traversal_and_archive_links(self):
        run = self._freeze()
        for path in ["../outside.txt", "/sample/SKILL.md", "sample\\SKILL.md", "sample/./SKILL.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                skill_inputs.read_frozen_skill(run, path, self.destination)
        target = self.destination / "sample/references/guide.md"
        target.unlink()
        target.symlink_to(self.base / "sample/references/guide.md")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            skill_inputs.read_frozen_skill(run, "sample/references/guide.md", self.destination)
        linked = self.root / "archive-link"
        linked.symlink_to(self.destination, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            skill_inputs.read_frozen_skill(run, self.entry, linked, entry=True)


if __name__ == "__main__":
    unittest.main()
