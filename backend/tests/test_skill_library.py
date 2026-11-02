"""技能资料导入与知识库 API 回归测试，所有写入均限定在临时目录。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.knowledge import router
from app.services import knowledge
from app.services.skill_library import import_skill_library, sync_skill_revision


class SkillLibraryTests(unittest.TestCase):
    """验证完整目录、重复导入、用户删除和深层目录访问。"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.knowledge_root = self.root / "knowledge"
        self.patch = patch.object(knowledge, "KNOWLEDGE_DIR", self.knowledge_root)
        self.patch.start()
        knowledge._sync_cache.clear()
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.patch.stop()
        knowledge._sync_cache.clear()
        self.temp.cleanup()

    def _fixture_source(self) -> Path:
        """创建包含主入口、深层子模块和空目录的小型源包。"""
        source_root = self.root / "project"
        package = source_root / "skills" / "apk-engineering-analysis"
        deep = package / "modules" / "cocos-qa" / "assets" / "editor" / "templates"
        deep.mkdir(parents=True)
        (package / "SKILL.md").write_text("# 示例技能\n\n技能正文", encoding="utf-8")
        (deep / "config.json").write_text('{"name":"原始配置"}', encoding="utf-8")
        (package / "references").mkdir()
        company = source_root / "ref" / "公司skill整合"
        company.mkdir(parents=True)
        (company / "README.md").write_text("# 公司说明", encoding="utf-8")
        return source_root

    def test_all_current_packages_and_source_files_are_imported(self) -> None:
        """动态核对当前全部包、入口和配套文件，新增 Skill 无需修改固定数字。"""
        project_root = Path(__file__).resolve().parents[2]
        expected = {}
        for source_root in (project_root / "skills", project_root / "ref" / "公司skill整合"):
            for source in source_root.iterdir():
                if source.is_dir() and (source / "SKILL.md").is_file():
                    for path in source.rglob("*"):
                        if path.is_file():
                            expected[Path(source.name) / path.relative_to(source)] = path
                elif source.is_file() and source_root.name == "公司skill整合":
                    expected[Path("公司资料") / source.name] = source

        result = import_skill_library(project_root)
        package_count = sum(1 for relative in expected if len(relative.parts) == 2 and relative.name == "SKILL.md")
        entry_count = sum(1 for relative in expected if relative.name == "SKILL.md")
        self.assertEqual(result["packages"], package_count)
        self.assertEqual(result["skill_entries"], entry_count)
        self.assertEqual(result["files"], len(expected))
        items = knowledge.list_items("skill", "docs")
        indexed_paths = {Path(item.folder) / item.stored_name for item in items}
        self.assertEqual(indexed_paths, set(expected))
        for relative, source in expected.items():
            self.assertEqual((self.knowledge_root / "skill" / "docs" / relative).read_bytes(), source.read_bytes())

        entries = [item for item in items if item.filename == "SKILL.md"]
        self.assertEqual(len({item.title for item in entries}), entry_count)
        self.assertEqual(sum("主入口" in item.tags for item in entries), package_count)
        self.assertEqual(sum("子模块" in item.tags for item in entries), entry_count - package_count)
        self.assertTrue(all(item.summary for item in entries))
        folders = knowledge.list_folders("skill", "docs")
        self.assertTrue(all(folder.desc for folder in folders))

    def test_explicit_revision_preserves_metadata_and_archives_versions(self) -> None:
        """只有明确发布的文件更新副本，保留用户元数据和前后正文。"""
        source_root = self._fixture_source()
        import_skill_library(source_root)
        items = knowledge.list_items("skill", "docs")
        item = next(item for item in items if item.filename == "SKILL.md")
        item.title, item.tags, item.summary = "保留的标题", ["保留的标签"], "保留的摘要"
        knowledge._write_index("skill", "docs", items, knowledge.list_folders("skill", "docs"))
        path = source_root / "skills" / "apk-engineering-analysis" / "SKILL.md"
        updated = "---\nname: apk-engineering-analysis\ndescription: 修订后的技能规范\n---\n\n# 修订说明\n\n记录真实验收证据。"
        path.write_text(updated, encoding="utf-8")
        revision = sync_skill_revision("apk-engineering-analysis/SKILL.md", "补充真实验收要求", "run-test", source_root)
        self.assertEqual(revision["previous"], "# 示例技能\n\n技能正文")
        self.assertEqual(revision["content"], updated)
        refreshed = knowledge.get_item("skill", "docs", item.id)
        self.assertEqual((refreshed.title, refreshed.tags, refreshed.summary), (item.title, item.tags, item.summary))
        self.assertEqual(knowledge.get_raw_path("skill", "docs", item.id).read_text(encoding="utf-8"), updated)
        archives = list((self.knowledge_root / "skill" / "docs" / ".skill-revisions").glob("*.json"))
        self.assertEqual(len(archives), 1)
        self.assertFalse(any(".skill-revisions" in entry.folder for entry in knowledge.list_items("skill", "docs")))

    def test_repeat_import_preserves_user_files_metadata_and_deletions(self) -> None:
        """重复启动不覆盖内容、用户元数据，也不复原被删除的文件夹。"""
        source_root = self._fixture_source()
        first = import_skill_library(source_root)
        self.assertEqual(first["copied_files"], 3)
        items = knowledge.list_items("skill", "docs")
        main = next(item for item in items if item.filename == "SKILL.md")
        main.title = "用户修改后的标题"
        main.tags = ["用户标签"]
        main.summary = "用户摘要"
        folders = knowledge.list_folders("skill", "docs")
        root_folder = next(folder for folder in folders if folder.path == main.folder)
        root_folder.desc = "用户目录说明"
        knowledge._write_index("skill", "docs", items, folders)
        knowledge.get_raw_path("skill", "docs", main.id).write_text("用户修改后的文件", encoding="utf-8")
        self.assertTrue(knowledge.delete_folder("skill", "docs", path=f"{main.folder}/modules"))
        self.assertTrue(knowledge.delete_folder("skill", "docs", path=f"{main.folder}/references"))

        repeated = import_skill_library(source_root)
        self.assertEqual(repeated["copied_files"], 0)
        preserved = knowledge.get_item("skill", "docs", main.id)
        self.assertEqual((preserved.title, preserved.tags, preserved.summary), (main.title, main.tags, main.summary))
        self.assertEqual(knowledge.get_folder("skill", "docs", main.folder).desc, "用户目录说明")
        self.assertEqual(knowledge.get_raw_path("skill", "docs", main.id).read_text(encoding="utf-8"), "用户修改后的文件")
        self.assertFalse((self.knowledge_root / "skill" / "docs" / main.folder / "modules").exists())
        self.assertFalse((self.knowledge_root / "skill" / "docs" / main.folder / "references").exists())
        self.assertEqual((source_root / "skills" / main.folder / "SKILL.md").read_text(encoding="utf-8"), "# 示例技能\n\n技能正文")

        # 明确要求恢复时只补回缺失文件，不覆盖用户已有内容和元数据。
        restored = import_skill_library(source_root, restore_deleted=True)
        self.assertEqual(restored["copied_files"], 1)
        self.assertEqual(knowledge.get_raw_path("skill", "docs", main.id).read_text(encoding="utf-8"), "用户修改后的文件")

    def test_new_source_files_are_added_without_restoring_deleted_files(self) -> None:
        """源包新增资料可以补导，曾被用户删除的旧文件继续保持删除状态。"""
        source_root = self._fixture_source()
        import_skill_library(source_root)
        main = next(item for item in knowledge.list_items("skill", "docs") if item.filename == "SKILL.md")
        self.assertTrue(knowledge.delete_item("skill", "docs", main.id))
        new_source = source_root / "skills" / main.folder / "references" / "新说明.md"
        new_source.write_text("新增资料", encoding="utf-8")
        result = import_skill_library(source_root)
        self.assertEqual(result["copied_files"], 1)
        self.assertIsNone(knowledge.get_item("skill", "docs", main.id))
        self.assertTrue(any(item.filename == "新说明.md" for item in knowledge.list_items("skill", "docs")))

    def test_skill_api_lists_previews_and_deletes_deep_files(self) -> None:
        """验证界面依赖的模块、文件夹、深层条目、原文和下载接口。"""
        import_skill_library(self._fixture_source())
        modules = self.client.get("/api/knowledge/modules").json()["data"]["modules"]
        self.assertEqual(modules["skill"], ["docs"])
        folders = self.client.get("/api/knowledge/skill/docs/folders").json()["data"]["folders"]
        deep_folder = next(folder["path"] for folder in folders if folder["path"].endswith("templates"))
        response = self.client.get("/api/knowledge/skill/docs/items", params={"folder": deep_folder})
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["total"], 1)
        item = data["items"][0]
        endpoint = f"/api/knowledge/skill/docs/items/{item['id']}"
        self.assertEqual(self.client.get(endpoint).json()["data"]["filename"], "config.json")
        self.assertEqual(self.client.get(f"{endpoint}/raw").json(), {"name": "原始配置"})
        download = self.client.get(f"{endpoint}/raw", params={"download": 1})
        self.assertIn("attachment", download.headers["content-disposition"])
        self.assertEqual(self.client.delete(endpoint).status_code, 200)
        self.assertEqual(self.client.get(f"{endpoint}/raw").status_code, 404)

    def test_skill_eight_level_upload_and_other_modules_keep_four_level_limit(self) -> None:
        """允许 Skill 八层读写，同时守住其他模块原有的四层约束。"""
        eight_levels = "/".join(f"level{number}" for number in range(8))
        response = self.client.post(
            "/api/knowledge/skill/docs/items",
            data={"folder": eight_levels},
            files={"file": ("深层说明.md", "# 深层正文".encode(), "text/markdown")},
        )
        self.assertEqual(response.status_code, 201)
        item = response.json()["data"]
        response = self.client.get("/api/knowledge/skill/docs/items", params={"folder": eight_levels})
        self.assertEqual(response.json()["data"]["items"][0]["id"], item["id"])
        self.assertEqual(len(knowledge.list_items_under_folder("skill", "docs", eight_levels)), 1)
        self.assertIsNotNone(knowledge.get_folder("skill", "docs", eight_levels))
        self.assertEqual(self.client.post("/api/knowledge/skill/docs/folders", json={"path": eight_levels + "/level8"}).status_code, 400)
        self.assertEqual(self.client.get("/api/knowledge/art/docs/items", params={"folder": "a/b/c/d/e"}).status_code, 400)
        self.assertEqual(self.client.delete("/api/knowledge/skill/docs/folders", params={"path": eight_levels}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
