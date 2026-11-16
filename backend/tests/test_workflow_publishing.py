"""独立静态发布的门禁、路径归属和回滚验证；所有写入都在临时目录。"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.workflow.publishing import MAX_BUILD_BYTES, build_manifest, publish_game
from app.services.workflow.workspace import source_fingerprint


class WorkflowPublishingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "games" / "oasis"
        (self.workspace / "src").mkdir(parents=True)
        (self.workspace / "src" / "main.js").write_text("document.body.dataset.ready = 'yes';", encoding="utf-8")
        (self.workspace / "dist" / "assets").mkdir(parents=True)
        (self.workspace / "dist" / "index.html").write_text('<html><script type="module" src="./assets/main.js"></script></html>', encoding="utf-8")
        (self.workspace / "dist" / "assets" / "main.js").write_text("document.body.dataset.ready = 'yes';", encoding="utf-8")
        (self.workspace / "workflow").mkdir()
        (self.workspace / "workflow" / "test.md").write_text("# 测试证据\n本文件由单元测试夹具生成。", encoding="utf-8")
        self.project = {"id": "project-one", "workspace": "games/oasis", "stages": [
            {"id": stage, "status": "completed", "run_id": f"run-{stage}", "confirmed_at": "2026-11-03T10:00:00Z"}
            for stage in ("prototype", "art", "code", "test")
        ]}
        self.verify_dependencies = Mock()
        self.run = {"id": "run-test", "project_id": "project-one", "stage": "test", "status": "completed", "attempt": 1,
                    "production_profile": {"framework": {"required_validations": ["npm run build", "npm test", "npm run check"]}},
                    "events": [], "artifacts": []}
        self.refresh_evidence()
        self.environment = patch.dict("os.environ", {"GAME_PUBLIC_BASE_URL": "https://pagent.ahagamecenter.com"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def refresh_evidence(self):
        """测试夹具提供已执行门禁的输入记录，不把该夹具当成真实模型/浏览器验收。"""
        fingerprint = source_fingerprint(self.workspace)
        manifest = build_manifest(self.workspace)
        self.run["events"] = [{"type": "validation_completed", "data": {
            "command": command, "exit_code": 0, "attempt": self.run["attempt"],
            "source_before": fingerprint, "source_after": fingerprint, "build_sha256": manifest["sha256"],
        }} for command in ("npm run build", "npm test", "npm run check")]
        self.run["artifacts"] = [{"path": "workflow/test.md", "sha256": hashlib.sha256((self.workspace / "workflow/test.md").read_bytes()).hexdigest()}]

    def publish(self, slug="oasis-demo"):
        return publish_game(self.root, self.workspace, self.project, self.run, slug,
                            verify_dependencies=self.verify_dependencies)

    def test_complete_build_is_published_with_private_ownership(self):
        result = self.publish()
        self.verify_dependencies.assert_called_once_with(self.project, "test")
        self.assertEqual(result["url"], "https://pagent.ahagamecenter.com/games/oasis-demo/index.html")
        self.assertEqual(result["file_count"], 2)
        target = self.root / "frontend/public/games/oasis-demo"
        self.assertEqual((target / "assets/main.js").read_bytes(), (self.workspace / "dist/assets/main.js").read_bytes())
        self.assertEqual({item.name for item in target.iterdir()}, {"index.html", "assets"})
        owner = self.root / "backend/data/workflow/publications/oasis-demo.json"
        self.assertEqual(json.loads(owner.read_text())["project_id"], self.project["id"])
        self.assertEqual(result["sha256"], build_manifest(self.workspace)["sha256"])

    def test_all_stages_and_current_test_run_must_be_confirmed(self):
        for stage in self.project["stages"]:
            with self.subTest(stage=stage["id"]):
                stage["confirmed_at"] = None
                with self.assertRaisesRegex(ValueError, "确认全部"):
                    self.publish()
                stage["confirmed_at"] = "2026-11-03T10:00:00Z"
        self.run["id"] = "superseded-test"
        with self.assertRaisesRegex(ValueError, "当前已确认"):
            self.publish()

    def test_upstream_verifier_cannot_be_skipped(self):
        self.verify_dependencies.side_effect = ValueError("已确认的美术资源变更")
        with self.assertRaisesRegex(ValueError, "美术资源变更"):
            self.publish()
        self.assertFalse((self.root / "frontend").exists())

    def test_source_test_report_and_built_bytes_must_remain_current(self):
        source = self.workspace / "src/main.js"
        source.write_text("修改后的源码", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "源码/资源已变更"):
            self.publish()
        self.refresh_evidence()
        (self.workspace / "workflow/test.md").write_text("修改过评审报告", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "测试报告"):
            self.publish()
        self.refresh_evidence()
        (self.workspace / "dist/assets/main.js").write_text("只改构建，源码没变", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "相同字节版本"):
            self.publish()

    def test_browser_check_must_be_current_and_successful(self):
        check = self.run["events"][-1]["data"]
        check.pop("build_sha256")
        with self.assertRaisesRegex(ValueError, "浏览器验收"):
            self.publish()
        self.refresh_evidence()
        self.run["events"][-1]["data"]["attempt"] = 0
        with self.assertRaisesRegex(ValueError, "重新完成"):
            self.publish()
        self.refresh_evidence()
        self.run["events"][-1]["data"]["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "重新完成"):
            self.publish()

    def test_slug_links_and_private_files_are_rejected(self):
        for slug in ("../root", "AA-demo", "ab", "-bad", "bad-", "x" * 65, "one/two", "中文游戏"):
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, "发布路径须"):
                self.publish(slug)
        (self.workspace / "dist/assets/linked.js").symlink_to(self.workspace / "src/main.js")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.publish()
        (self.workspace / "dist/assets/linked.js").unlink()
        for name in (".env", "credentials.json", "private.key", "debug.js.map"):
            with self.subTest(file=name):
                target = self.workspace / "dist" / name
                target.write_text("不应公开", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.publish()
                target.unlink()
        public = self.root / "frontend/public"
        public.mkdir(parents=True)
        (public / "games").symlink_to(self.workspace, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.publish()

    def test_size_limit_and_missing_entry_are_rejected(self):
        large = self.workspace / "dist/assets/large.bin"
        with large.open("wb") as handle:
            handle.truncate(MAX_BUILD_BYTES)
        with self.assertRaisesRegex(ValueError, "超过 10MB"):
            self.publish()
        large.unlink()
        (self.workspace / "dist/index.html").unlink()
        with self.assertRaisesRegex(ValueError, "构建入口"):
            self.publish()

    def test_static_resource_links_must_exist_inside_the_build(self):
        entry = self.workspace / "dist/index.html"
        for reference in ("./missing.js", "../../src/main.js", "/assets/main.js", "https://cdn.example/game.js"):
            with self.subTest(reference=reference):
                entry.write_text(f'<script src="{reference}"></script>', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "资源"):
                    build_manifest(self.workspace)
        entry.write_text('<script type="module" src="./assets/main.js?version=2"></script>', encoding="utf-8")
        module = self.workspace / "dist/assets/main.js"
        module.write_text("import './missing-module.js';", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "资源引用"):
            build_manifest(self.workspace)
        module.write_text("import './helpers.js';", encoding="utf-8")
        (module.parent / "helpers.js").write_text("export const ready = true;", encoding="utf-8")
        self.assertEqual(build_manifest(self.workspace)["file_count"], 3)

    def test_existing_manual_path_and_other_owner_cannot_be_overwritten(self):
        manual = self.root / "frontend/public/games/amber-caravan"
        manual.mkdir(parents=True)
        (manual / "index.html").write_text("现有手工部署的游戏", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不能覆盖"):
            self.publish("amber-caravan")
        self.assertEqual((manual / "index.html").read_text(), "现有手工部署的游戏")
        self.publish()
        self.project["id"] = "project-two"
        self.run["project_id"] = "project-two"
        with self.assertRaisesRegex(ValueError, "其他项目"):
            self.publish()

    def test_same_project_can_update_with_old_version_retained(self):
        first = self.publish()
        target = self.root / "frontend/public/games/oasis-demo/assets/main.js"
        old = target.read_bytes()
        (self.workspace / "src/main.js").write_text("新版源码", encoding="utf-8")
        (self.workspace / "dist/assets/main.js").write_text("新版网页", encoding="utf-8")
        self.refresh_evidence()
        second = self.publish()
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual(target.read_text(), "新版网页")
        backups = list((self.root / "backend/data/workflow/publications/backups").glob("oasis-demo-*/assets/main.js"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), old)

    def test_failed_owner_commit_restores_previous_public_files(self):
        first = self.publish()
        owner = self.root / "backend/data/workflow/publications/oasis-demo.json"
        previous_record = owner.read_bytes()
        previous_html = (self.root / "frontend/public/games/oasis-demo/index.html").read_bytes()
        (self.workspace / "dist/index.html").write_text("<html>新版本</html>", encoding="utf-8")
        self.refresh_evidence()
        replace = Path.replace

        def fail_owner_commit(source, destination):
            if Path(destination) == owner:
                raise OSError("模拟私有记录磁盘写入失败")
            return replace(source, destination)

        with patch.object(Path, "replace", fail_owner_commit), self.assertRaisesRegex(OSError, "模拟"):
            self.publish()
        self.assertEqual(owner.read_bytes(), previous_record)
        self.assertEqual((self.root / "frontend/public/games/oasis-demo/index.html").read_bytes(), previous_html)
        self.assertEqual(json.loads(owner.read_text())["sha256"], first["sha256"])
        self.assertFalse(list((self.root / "frontend/public/games").glob(".oasis-demo-*")))

    def test_domain_must_be_https_except_local_preview(self):
        for value in ("http://example.com", "https://user:pass@example.com", "https://example.com/path", "https://example.com?x=1"):
            with self.subTest(value=value), patch.dict("os.environ", {"GAME_PUBLIC_BASE_URL": value}), self.assertRaisesRegex(ValueError, "HTTPS"):
                self.publish()
        with patch.dict("os.environ", {"GAME_PUBLIC_BASE_URL": "http://127.0.0.1:24681"}):
            self.assertEqual(self.publish()["url"], "http://127.0.0.1:24681/games/oasis-demo/index.html")


if __name__ == "__main__":
    unittest.main()
