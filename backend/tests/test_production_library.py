"""跨品类知识目录测试；用临时知识库验证真实文件导入及引用边界。"""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import knowledge, production_library as library


class ProductionLibraryTests(unittest.TestCase):
    """目录和正文可编辑，但编辑、删除及非法路径不能静默改变运行输入。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.override = patch.object(knowledge, "KNOWLEDGE_DIR", self.root / "kb")
        self.override.start()
        knowledge._sync_cache.clear()

    def tearDown(self):
        self.override.stop()
        knowledge._sync_cache.clear()
        self.temp.cleanup()

    def test_import_preserves_edits_deletion_and_metadata(self):
        source = self.root / "source" / "genre"
        source.mkdir(parents=True)
        (source / "general.md").write_text("# 通用玩法\n\n待验证的指南。", encoding="utf-8")
        library.import_production_library(source.parent)
        target = knowledge.KNOWLEDGE_DIR / "genre/docs/general.md"
        items = knowledge._read_index("genre", "docs")
        self.assertEqual(items[0].title, "通用玩法")
        items[0].title = "我的标题"
        knowledge._write_index("genre", "docs", items, knowledge._read_folders("genre", "docs"))
        target.write_text("用户修改", encoding="utf-8")
        self.assertEqual(library.import_production_library(source.parent)["copied_files"], 0)
        self.assertEqual(target.read_text(), "用户修改")
        self.assertEqual(knowledge.list_items("genre", "docs")[0].title, "我的标题")
        target.unlink()
        library.import_production_library(source.parent)
        self.assertFalse(target.exists())
        self.assertEqual(library.get_catalog()["documents"], [])

    def test_snapshot_preserves_exact_bytes_and_is_detached(self):
        target = knowledge._category_dir("genre", "docs") / "general.md"
        original = "# 规则\r\n旧版\r\n".encode()
        target.write_bytes(original)
        snapshot = library.snapshot_knowledge(["genre/docs/general.md", "genre/docs/general.md"])
        target.write_text("新版")
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["content"].encode(), original)
        self.assertEqual(snapshot[0]["sha256"], hashlib.sha256(original).hexdigest())
        profile = library.resolve_profile("block-placement", "canvas-web")
        profile["framework"]["required_validations"].clear()
        self.assertEqual(len(library.resolve_profile("block-placement", "canvas-web")["framework"]["required_validations"]), 3)

    def test_only_selected_text_libraries_are_readable(self):
        base = knowledge._category_dir("genre", "docs")
        (base / "good.md").write_text("# 合法文件")
        (base / "linked.md").symlink_to(base / "good.md")
        for path in ["../secret.md", "/genre/docs/good.md", "skill/docs/good.md", "genre/docs/index.json",
                     "genre/docs/.hidden.md", "genre/docs/../good.md", "genre/docs/linked.md", "genre/docs/missing.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                library.snapshot_knowledge([path])
        for ids in [("unknown", "canvas-web"), ("general", "unity")]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                library.resolve_profile(*ids)

    def test_seed_guides_are_available_without_sample_project_reference(self):
        library.import_production_library()
        catalog = library.get_catalog()
        self.assertEqual(len(catalog["genres"]), 7)
        self.assertEqual(len(catalog["frameworks"]), 2)
        for genre in catalog["genres"]:
            profile = library.resolve_profile(genre["id"], "canvas-web")
            snapshots = library.snapshot_knowledge(profile["knowledge_paths"])
            self.assertTrue(all(item["content"] for item in snapshots))
            self.assertNotIn("cocos-game-production/SKILL.md", profile["framework"]["recommended_skills"])


if __name__ == "__main__":
    unittest.main()
