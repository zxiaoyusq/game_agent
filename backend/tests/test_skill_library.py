"""技能资料导入与知识库 API 回归测试，所有写入均限定在临时目录。"""

from __future__ import annotations

import tempfile
import unittest
import json
import hashlib
import shutil
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.knowledge import router
from app.services import knowledge
from app.services.skill_library import (import_skill_library, sync_skill_revision,
    plan_company_skill_sync, apply_company_skill_sync, LEGACY_REVERSE_SUMMARY,
    LEGACY_SKILL_DESCRIPTIONS, SKILL_DESCRIPTIONS)


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
                if source.is_symlink() or source.name.startswith("."):
                    continue
                if source.is_dir() and (source / "SKILL.md").is_file():
                    for path in source.rglob("*"):
                        if path.is_file() and not path.is_symlink() and not any(part.startswith(".") or part in {"__pycache__", "node_modules"} for part in path.relative_to(source).parts):
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

    def _company_fixture(self):
        """两个普通文件即可验证真实复制、覆盖及二进制备份，不执行源脚本。"""
        root = self.root / "project"
        package = root / "ref" / "公司skill整合" / "sample-skill"
        (package / "references").mkdir(parents=True)
        (package / "SKILL.md").write_text("---\nname: sample-skill\ndescription: 示例能力\n---\n# 第一版\n", encoding="utf-8")
        (package / "references" / "image.bin").write_bytes(b"\x00\xff\x01")
        return root, package

    def test_source_sync_plan_is_read_only_and_apply_is_idempotent(self):
        root, package = self._company_fixture()
        (package.parent / ".gitignore").write_text("机密配置文件名")
        (package / ".cache").mkdir()
        (package / ".cache" / "ignored.txt").write_text("缓存")
        (package.parent / "AHAgames").mkdir()
        (package.parent / "AHAgames" / "gameInfo.json").write_text("{}")
        plan = plan_company_skill_sync(root)
        self.assertFalse(self.knowledge_root.exists())
        self.assertEqual(plan["counts"]["added"], 2)
        self.assertFalse(any("AHAgames" in item["path"] or ".cache" in item["path"] or ".gitignore" in item["path"] for item in plan["files"]))
        result = apply_company_skill_sync("明确同步示例来源", plan["digest"], root)
        self.assertEqual(result["summary"]["files"], 2)
        archive = self.knowledge_root / "skill/docs" / result["backup_path"]
        self.assertEqual(json.loads((archive / "manifest.json").read_text())["status"], "completed")
        repeated = plan_company_skill_sync(root)
        self.assertEqual(repeated["counts"]["unchanged"], 2)
        self.assertIsNone(apply_company_skill_sync("重复核对", repeated["digest"], root)["operation_id"])
        self.assertEqual(len(list(archive.parent.iterdir())), 1)

    def test_source_sync_updates_binary_and_preserves_user_metadata(self):
        root, package = self._company_fixture()
        import_skill_library(root)
        items = knowledge.list_items("skill", "docs")
        main = next(item for item in items if item.filename == "SKILL.md")
        main.title, main.summary, main.tags = "我的名称", "我的摘要", ["自定义"]
        folders = knowledge.list_folders("skill", "docs")
        folder = next(item for item in folders if item.path == "sample-skill")
        folder.desc = "用户目录描述"
        knowledge._write_index("skill", "docs", items, folders)
        target = knowledge.get_raw_path("skill", "docs", main.id)
        previous = "用户编辑后的正文\r\n".encode()
        target.write_bytes(previous)
        (package / "SKILL.md").write_text("# 来源第二版\n", encoding="utf-8")
        (package / "references/image.bin").write_bytes(b"\x00\xfe\x02")
        (package / "references/new.md").write_text("新参考", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        self.assertEqual((plan["counts"]["added"], plan["counts"]["updated"]), (1, 2))
        result = apply_company_skill_sync("用户明确要求按新来源同步", plan["digest"], root)
        archive = self.knowledge_root / "skill/docs" / result["backup_path"]
        self.assertEqual((archive / "previous/sample-skill/SKILL.md").read_bytes(), previous)
        self.assertEqual((archive / "previous/sample-skill/references/image.bin").read_bytes(), b"\x00\xff\x01")
        self.assertEqual(target.read_bytes(), (package / "SKILL.md").read_bytes())
        refreshed = knowledge.get_item("skill", "docs", main.id)
        self.assertEqual((refreshed.id, refreshed.title, refreshed.summary, refreshed.tags), (main.id, main.title, main.summary, main.tags))
        self.assertEqual(knowledge.get_folder("skill", "docs", "sample-skill").desc, "用户目录描述")
        record = json.loads((archive / "manifest.json").read_text())
        entry = next(item for item in record["files"] if item["path"] == "sample-skill/SKILL.md")
        self.assertEqual(entry["target_sha256"], hashlib.sha256(previous).hexdigest())
        self.assertFalse(any(item.folder.startswith(".skill-source-sync") for item in knowledge.list_items("skill", "docs")))

    def test_new_capability_labels_replace_only_known_generated_metadata(self):
        """旧采集标签升级为全生命周期说明，但手动编辑过的字段必须保留。"""
        root, package = self._company_fixture()
        for name in LEGACY_SKILL_DESCRIPTIONS:
            path = package / "modules" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"---\nname: {name}\ndescription: 示例\n---\n初版")
        import_skill_library(root)
        items = knowledge.list_items("skill", "docs")
        folders = knowledge.list_folders("skill", "docs")
        for item in items:
            name = Path(item.folder).name
            if item.filename == "SKILL.md" and name in LEGACY_SKILL_DESCRIPTIONS:
                item.title, item.summary = LEGACY_SKILL_DESCRIPTIONS[name]
                if name == "h5-canvas-reskin":
                    item.title = "用户自定换皮名称"
                (package / "modules" / name / "SKILL.md").write_text("# 新版规范")
        for folder in folders:
            name = Path(folder.path).name
            if name in LEGACY_SKILL_DESCRIPTIONS:
                title, summary = LEGACY_SKILL_DESCRIPTIONS[name]
                folder.desc = f"{title}：{summary}" if name == "hosted-minigame-harvest" else "用户的说明"
        knowledge._write_index("skill", "docs", items, folders)
        plan = plan_company_skill_sync(root)
        apply_company_skill_sync("按公司新能力同步", plan["digest"], root)
        items = knowledge.list_items("skill", "docs")
        harvest = next(item for item in items if item.folder.endswith("hosted-minigame-harvest"))
        reskin = next(item for item in items if item.folder.endswith("h5-canvas-reskin"))
        self.assertEqual((harvest.title, harvest.summary), SKILL_DESCRIPTIONS["hosted-minigame-harvest"])
        self.assertEqual(reskin.title, "用户自定换皮名称")
        self.assertEqual(knowledge.get_folder("skill", "docs", reskin.folder).desc, "用户的说明")

    def test_source_sync_rejects_stale_source_target_and_index(self):
        root, package = self._company_fixture()
        import_skill_library(root)
        for changed in [package / "SKILL.md", self.knowledge_root / "skill/docs/sample-skill/SKILL.md", self.knowledge_root / "skill/docs/index.json"]:
            plan = plan_company_skill_sync(root)
            changed.write_bytes(changed.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "计划已过期"):
                apply_company_skill_sync("过期计划不能覆盖", plan["digest"], root)
        self.assertFalse((self.knowledge_root / "skill/docs/.skill-source-sync").exists())

    def test_source_sync_preserves_deleted_files_and_folders(self):
        root, package = self._company_fixture()
        import_skill_library(root)
        base = self.knowledge_root / "skill/docs/sample-skill"
        (base / "SKILL.md").unlink()
        shutil.rmtree(base / "references")
        (package / "references/new.md").write_text("删除目录中的新增来源", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        self.assertEqual(plan["counts"]["deleted_skipped"], 3)
        apply_company_skill_sync("尊重删除", plan["digest"], root)
        self.assertFalse((base / "SKILL.md").exists())
        self.assertFalse((base / "references").exists())
        import_skill_library(root)
        self.assertFalse((base / "references").exists())

    def test_source_sync_reports_links_and_source_collisions_without_writing(self):
        root, package = self._company_fixture()
        local = root / "skills/sample-skill"
        local.mkdir(parents=True)
        (local / "SKILL.md").write_text("# 工程维护版", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        self.assertEqual(plan["counts"]["conflicts"], 2)
        with self.assertRaisesRegex(ValueError, "来源或路径冲突"):
            apply_company_skill_sync("同名来源禁止混写", plan["digest"], root)
        self.assertFalse(self.knowledge_root.exists())
        import_skill_library(root)
        self.assertEqual((self.knowledge_root / "skill/docs/sample-skill/SKILL.md").read_text(), "# 工程维护版")
        self.assertFalse((self.knowledge_root / "skill/docs/sample-skill/references").exists())
        shutil.rmtree(local)
        (package / "references/linked.md").symlink_to(package / "SKILL.md")
        (package / "linked-dir").symlink_to(package / "references", target_is_directory=True)
        plan = plan_company_skill_sync(root)
        linked = [item for item in plan["files"] if "linked" in item["path"]]
        self.assertEqual(len(linked), 2)
        self.assertTrue(all(item["status"] == "conflicts" and item["source_sha256"] is None for item in linked))
        target = self.knowledge_root / "skill/docs/sample-skill/SKILL.md"
        target.unlink()
        target.symlink_to(package / "SKILL.md")
        self.assertTrue(any(item["path"] == "sample-skill/SKILL.md" and item["status"] == "conflicts" for item in plan_company_skill_sync(root)["files"]))

    def test_explicit_source_sync_also_updates_project_skills(self):
        root, _ = self._company_fixture()
        package = root / "skills/local-production"
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text("# 本地旧版", encoding="utf-8")
        import_skill_library(root)
        (package / "SKILL.md").write_text("# 本地新版", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        entry = next(item for item in plan["files"] if item["path"] == "local-production/SKILL.md")
        self.assertEqual((entry["origin"], entry["status"]), ("工程已有", "updated"))
        result = apply_company_skill_sync("当前任务维护工程技能", plan["digest"], root)
        self.assertEqual((self.knowledge_root / "skill/docs/local-production/SKILL.md").read_text(), "# 本地新版")
        self.assertEqual((self.knowledge_root / "skill/docs" / result["backup_path"] / "previous/local-production/SKILL.md").read_text(), "# 本地旧版")

    def test_sync_rejects_symlinks_above_source_and_knowledge_roots(self):
        """根目录外层的链接不能通过 resolve 被静默当作可信来源或写入位置。"""
        root, _ = self._company_fixture()
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "父级不能使用符号链接"):
            plan_company_skill_sync(alias / "project")
        with self.assertRaisesRegex(ValueError, "父级不能使用符号链接"):
            import_skill_library(alias / "project")
        with patch.object(knowledge, "KNOWLEDGE_DIR", alias / "knowledge"):
            with self.assertRaisesRegex(ValueError, "父级不能使用符号链接"):
                plan_company_skill_sync(root)
            with self.assertRaisesRegex(ValueError, "父级不能使用符号链接"):
                import_skill_library(root)
        self.assertFalse((self.knowledge_root / "skill/docs/sample-skill").exists())

    def test_source_sync_does_not_read_linked_display_configuration(self):
        """用户副本中的可选展示配置链接不能把外部内容带入新增条目的标签。"""
        root, package = self._company_fixture()
        import_skill_library(root)
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "openai.yaml").write_text("interface:\n  display_name: 外部哨兵名称\n", encoding="utf-8")
        (self.knowledge_root / "skill/docs/sample-skill/agents").symlink_to(outside, target_is_directory=True)
        (package / "new.md").write_text("新增文档", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        apply_company_skill_sync("同步新增文档", plan["digest"], root)
        new_item = next(item for item in knowledge.list_items("skill", "docs") if item.filename == "new.md")
        self.assertNotIn("外部哨兵名称", new_item.tags)
        self.assertIn("sample-skill", new_item.tags)

    def test_source_sync_refreshes_only_known_generated_descriptions(self):
        root, package = self._company_fixture()
        original = package.parent / "game-reverse-engineering"
        package.rename(original)
        import_skill_library(root)
        items = knowledge.list_items("skill", "docs")
        main = next(item for item in items if item.filename == "SKILL.md")
        main.summary = LEGACY_REVERSE_SUMMARY
        main.title = "用户保留的主入口名称"
        folders = knowledge.list_folders("skill", "docs")
        next(item for item in folders if item.path == "game-reverse-engineering").desc = "用户自定义目录描述"
        knowledge._write_index("skill", "docs", items, folders)
        (original / "SKILL.md").write_text("# 新公司规范", encoding="utf-8")
        plan = plan_company_skill_sync(root)
        apply_company_skill_sync("更新旧自动模块说明", plan["digest"], root)
        self.assertNotIn("16 个", knowledge.get_item("skill", "docs", main.id).summary)
        self.assertEqual(knowledge.get_item("skill", "docs", main.id).title, "用户保留的主入口名称")
        self.assertEqual(knowledge.get_folder("skill", "docs", "game-reverse-engineering").desc, "用户自定义目录描述")

    def test_source_sync_api_returns_preview_and_conflict_for_stale_digest(self):
        from app.api.routes.workflow import router as workflow_router
        root, package = self._company_fixture()
        app = FastAPI()
        app.include_router(workflow_router, prefix="/api")
        with TestClient(app) as client, \
             patch("app.services.skill_library.plan_company_skill_sync", side_effect=lambda project_root=None: plan_company_skill_sync(root)), \
             patch("app.services.skill_library.apply_company_skill_sync", side_effect=lambda reason, expected_digest: apply_company_skill_sync(reason, expected_digest, root)):
            preview = client.get("/api/workflow/skills/source-sync")
            self.assertEqual(preview.status_code, 200)
            self.assertFalse(self.knowledge_root.exists())
            digest = preview.json()["digest"]
            (package / "SKILL.md").write_text("# 查看后发生变化", encoding="utf-8")
            response = client.post("/api/workflow/skills/source-sync", json={"reason": "同步变动", "expected_digest": digest})
            self.assertEqual(response.status_code, 409)
            digest = client.get("/api/workflow/skills/source-sync").json()["digest"]
            response = client.post("/api/workflow/skills/source-sync", json={"reason": "同步当前变动", "expected_digest": digest})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["operation_id"])


if __name__ == "__main__":
    unittest.main()
