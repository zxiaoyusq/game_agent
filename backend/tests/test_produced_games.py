"""验证自产游戏目录、构建优先级和运行资源边界，夹具均位于临时目录。"""

import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.produced_games import router
from app.services import produced_games as games
from app.services import produced_game_deletion as deletion


class ProducedGamesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.projects = self.root / "projects"
        self.projects.mkdir()
        for name, value in (("ROOT", self.root), ("PROJECTS_DIR", self.projects)):
            override = patch.object(games, name, value)
            override.start()
            self.addCleanup(override.stop)
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)

    def make_game(self, name="sample", published=False):
        """模拟独立构建，刻意保留一份不同的工作区源码供越界测试。"""
        workspace = self.root / "games" / name
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "index.html").write_text("不能直接暴露工作区源码")
        base = self.root / "frontend/public/games" / name if published else workspace / "dist"
        base.mkdir(parents=True, exist_ok=True)
        (base / "index.html").write_text('<title>测试游戏</title><meta name="description" content="游戏介绍"><script type="module" src="./src/main.mjs"></script>')
        (base / "src").mkdir(exist_ok=True)
        (base / "src/main.mjs").write_text("document.body.textContent = '游戏已运行';")
        return workspace, base

    def test_discovers_all_builds_and_public_only_games_without_duplicates(self):
        self.make_game("first")
        self.make_game("first", published=True)
        self.make_game("second")
        public = self.root / "frontend/public/games/archive"
        public.mkdir(parents=True)
        (public / "index.html").write_text("<title>存档游戏</title>")
        prototype = self.root / "games/prototype"
        prototype.mkdir()
        (prototype / "index.html").write_text("只有源码，尚未构建")
        # 公司参考内容不能混入产出游戏。
        reference = self.root / "ref/example/dist"
        reference.mkdir(parents=True)
        (reference / "index.html").write_text("参考游戏")
        result = games.list_games()
        self.assertEqual(result["total"], 3)
        self.assertEqual({item["id"] for item in result["items"]}, {"first", "second", "archive"})
        self.make_game("new-game")
        self.assertEqual(games.list_games()["total"], 4)

    def test_project_metadata_and_fallback_work_even_with_a_broken_record(self):
        self.make_game()
        (self.projects / "broken.json").write_text("{")
        (self.projects / "valid.json").write_text(json.dumps({"name": "正式名称", "workspace": "games/sample",
            "production_profile": {"genre": {"label": "分类整理"}}}))
        item = games.list_games()["items"][0]
        self.assertEqual((item["name"], item["description"], item["category"]), ("正式名称", "游戏介绍", "分类整理"))
        self.assertIsNone(item["cover_url"])
        (self.projects / "valid.json").write_text(json.dumps({"workspace": "games/sample", "production_profile": []}))
        self.assertEqual(games.list_games()["items"][0]["name"], "测试游戏")

    def test_explicit_sort_order_pins_imported_game_and_keeps_legacy_order(self):
        self.make_game("alpha")
        self.make_game("beta", published=True)
        workspace, _ = self.make_game("zuma")
        manifest = workspace / "game.json"
        manifest.write_text(json.dumps({"name": "祖玛", "sort_order": -100}))
        # 从正常目录接口读取，置顶信息在重新加载后仍然生效。
        for _ in range(2):
            items = self.client.get("/api/produced-games").json()["items"]
            self.assertEqual([item["id"] for item in items], ["zuma", "alpha", "beta"])
        for invalid in (True, "-100", None, []):
            with self.subTest(sort_order=invalid):
                manifest.write_text(json.dumps({"name": "祖玛", "sort_order": invalid}))
                items = games.list_games()["items"]
                self.assertEqual([item["id"] for item in items], ["alpha", "beta", "zuma"])

    def test_imported_incomplete_package_is_listed_but_never_playable(self):
        directory = self.root / "games/checkers-pocket"
        directory.mkdir(parents=True)
        (directory / "game.json").write_text(json.dumps({"name": "口袋西洋跳棋", "category": "棋盘游戏",
            "unavailable_reason": "上传包只有广告测试页", "play_url": "https://example.com/pretend-game"}))
        (directory / "index.html").write_text("只有广告按钮")
        item = games.list_games()["items"][0]
        self.assertFalse(item["available"])
        self.assertIsNone(item["play_url"])
        self.assertEqual(item["unavailable_reason"], "上传包只有广告测试页")
        self.assertEqual(games.list_games()["playable"], 0)
        self.assertEqual(self.client.head("/api/produced-games/checkers-pocket/play/index.html").status_code, 404)
        self.make_game("checkers-pocket")
        item = games.list_games()["items"][0]
        self.assertTrue(item["available"])
        self.assertIsNone(item["unavailable_reason"])
        self.assertEqual(item["name"], "口袋西洋跳棋")
        self.assertEqual(games.list_games()["playable"], 1)

    def test_imported_engine_resources_preserve_binary_bytes(self):
        _, base = self.make_game()
        for name in ("level.ccm", "atlas.plist", "physics.wasm", "project.manifest"):
            content = b"\x00\x01\x02\xff"
            (base / name).write_bytes(content)
            response = self.client.get(f"/api/produced-games/sample/play/{name}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, content)

    def test_published_resources_take_priority_and_missing_assets_do_not_fall_back(self):
        _, build = self.make_game()
        _, public = self.make_game(published=True)
        (public / "index.html").write_text("已分发版本")
        (build / "only-local.json").write_text("{}")
        self.assertEqual(games.game_file("sample", "index.html").read_text(), "已分发版本")
        with self.assertRaises(FileNotFoundError):
            games.game_file("sample", "only-local.json")

    def test_http_list_head_and_relative_module_are_playable(self):
        self.make_game()
        response = self.client.get("/api/produced-games")
        self.assertEqual(response.status_code, 200)
        url = response.json()["items"][0]["play_url"]
        self.assertEqual(self.client.head(url).status_code, 200)
        self.assertEqual(self.client.head(url).content, b"")
        response = self.client.get(url.replace("index.html", "src/main.mjs"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.headers["content-type"])
        self.assertEqual(self.client.get(url.replace("index.html", "missing.png")).status_code, 404)
        self.assertEqual(self.client.head(url.replace("sample", "missing")).status_code, 404)

    def test_rejects_traversal_hidden_files_and_private_build_files(self):
        _, base = self.make_game()
        for name in ("package.json", "credentials.json", "source.zip", ".env"):
            (base / name).write_text("不能公开")
            with self.assertRaises((ValueError, FileNotFoundError)):
                games.game_file("sample", name)
        for path in ("../index.html", "src/../../index.html", "/index.html", "src\\main.mjs", "src/./main.mjs"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                games.game_file("sample", path)
        with self.assertRaises(ValueError):
            games.game_file("../sample", "index.html")
        self.assertEqual(self.client.get("/api/produced-games/sample/play/%2Eenv").status_code, 400)

    def test_covers_are_limited_to_game_screenshots_and_symlinks_are_rejected(self):
        workspace, base = self.make_game()
        evidence = workspace / "evidence"
        evidence.mkdir()
        image = evidence / "desktop-lobby.jpg"
        image.write_bytes(b"test image")
        self.assertIsNotNone(games.list_games()["items"][0]["cover_url"])
        self.assertEqual(self.client.get("/api/produced-games/sample/cover").content, b"test image")
        outside = self.root / "outside.js"
        outside.write_text("不能读取外部脚本")
        (base / "linked.js").symlink_to(outside)
        with self.assertRaises(ValueError):
            games.game_file("sample", "linked.js")
        image.unlink()
        image.symlink_to(outside)
        self.assertIsNone(games.list_games()["items"][0]["cover_url"])
        (self.root / "games/alias").symlink_to(workspace, target_is_directory=True)
        self.assertEqual(games.list_games()["total"], 1)
        with self.assertRaises(ValueError):
            games.game_file("alias", "index.html")

    def make_workflow(self, name="source", status="completed"):
        """构造有独立发布别名、阶段快照及检查点的工程，删除测试始终使用临时文件。"""
        workspace, _ = self.make_game(name, published=True)
        alias = self.root / "frontend/public/games/release"
        alias.mkdir(parents=True)
        (alias / "index.html").write_text("发布别名")
        project = {"id": "owner", "name": "待删除工程", "workspace": f"games/{name}",
                   "created_at": "2026-11-09", "stages": []}
        (self.projects / "owner.json").write_text(json.dumps(project))
        for kind, record in (("runs", {"id": "run-one", "project_id": "owner", "status": status}),
                             ("publications", {"slug": "release", "project_id": "owner"})):
            directory = self.root / kind
            directory.mkdir(exist_ok=True)
            key = record.get("id", record.get("slug"))
            (directory / f"{key}.json").write_text(json.dumps(record))
        for relative in ("workflow/plan.md", "assets/art.png", "evidence/screen.jpg"):
            path = workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("游戏产出")
        for kind in ("artifacts", "inputs"):
            directory = self.root / kind / "run-one"
            directory.mkdir(parents=True)
            (directory / "saved.txt").write_text("生成快照")
        with closing(sqlite3.connect(self.root / "checkpoints.sqlite")) as connection:
            connection.execute("CREATE TABLE checkpoints(thread_id TEXT)")
            connection.execute("CREATE TABLE writes(thread_id TEXT)")
            for table in ("checkpoints", "writes"):
                connection.executemany(f"INSERT INTO {table} VALUES (?)", [("run-one",), ("unrelated-run",)])
            connection.commit()
        return workspace, alias

    def test_deletes_workspace_all_builds_history_and_only_its_checkpoints(self):
        workspace, alias = self.make_workflow()
        other, _ = self.make_game("unrelated")
        backup = self.root / "publications/backups" / ("release-" + "a" * 32)
        backup.mkdir(parents=True)
        (backup / "index.html").write_text("历史发布包")
        unrelated_backup = backup.parent / ("release-other-" + "b" * 32)
        unrelated_backup.mkdir()
        response = self.client.delete("/api/produced-games/release")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()["deleted_ids"]), {"source", "release"})
        for path in (workspace, alias, self.root / "frontend/public/games/source", backup,
                     self.projects / "owner.json", self.root / "runs/run-one.json",
                     self.root / "publications/release.json", self.root / "artifacts/run-one", self.root / "inputs/run-one"):
            self.assertFalse(path.exists(), path)
        self.assertTrue(other.exists())
        self.assertTrue(unrelated_backup.exists())
        with closing(sqlite3.connect(self.root / "checkpoints.sqlite")) as connection:
            for table in ("checkpoints", "writes"):
                self.assertEqual(connection.execute(f"SELECT thread_id FROM {table}").fetchall(), [("unrelated-run",)])
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 200)

    def test_incomplete_import_can_be_deleted(self):
        directory = self.root / "games/incomplete"
        directory.mkdir(parents=True)
        (directory / "game.json").write_text(json.dumps({"name": "未完成的导入游戏"}))
        self.assertEqual(games.list_games()["total"], 1)
        self.assertEqual(self.client.delete("/api/produced-games/incomplete").status_code, 200)
        self.assertFalse(directory.exists())
        self.assertEqual(games.list_games()["total"], 0)

    def test_running_worker_or_pipeline_prevents_any_deletion(self):
        workspace, alias = self.make_workflow(status="running")
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 409)
        self.assertTrue(workspace.exists())
        self.assertTrue(alias.exists())
        self.assertFalse((self.root / "deletions/release.json").exists())
        (self.root / "runs/run-one.json").write_text(json.dumps({"id": "run-one", "project_id": "owner", "status": "completed"}))
        with patch("app.services.workflow.engine.WORKERS", {"run-one": Mock(done=Mock(return_value=False))}):
            self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 409)
        with patch("app.services.workflow.pipeline.PIPELINES", {"owner": Mock(done=Mock(return_value=False))}):
            self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 409)
        self.assertTrue(workspace.exists())

    def test_deletion_failure_retains_scope_for_retry_after_records_disappear(self):
        workspace, alias = self.make_workflow()
        project_file = self.projects / "owner.json"
        original_unlink = Path.unlink

        def fail_last_record(path, *args, **kwargs):
            if path == project_file:
                raise PermissionError("模拟记录删除失败")
            return original_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", fail_last_record), self.assertLogs("app.api.routes.produced_games", level="ERROR"):
            self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 503)
        self.assertFalse(workspace.exists())
        self.assertFalse(alias.exists())
        self.assertFalse((self.root / "publications/release.json").exists())
        pending = games.list_games()["items"][0]
        self.assertEqual(pending["id"], "release")
        self.assertTrue(pending["deletion_pending"])
        self.assertFalse(pending["available"])
        with self.assertRaises(deletion.GameDeletionConflict):
            deletion.ensure_workspace_not_deleting(self.root, self.root, workspace)
        from app.services.workflow import engine
        with patch.object(engine, "ROOT", self.root), patch.object(engine, "STORE", self.root):
            with self.assertRaises(deletion.GameDeletionConflict):
                engine.ensure_workspace_available({"workspace": "games/source"})
            with patch.object(engine.model_runtime, "validate_selection", return_value={}), self.assertRaises(deletion.GameDeletionConflict):
                engine.create_project("不能重建清理中的工程", "需求", "games/source", [])
        deletion.ensure_workspace_not_deleting(self.root, self.root, self.root / "games/other")
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 200)
        self.assertFalse(project_file.exists())
        self.assertFalse((self.root / "deletions/release.json").exists())
        self.assertEqual(games.list_games()["total"], 0)

    def test_deletion_rejects_unsafe_paths_before_touching_any_output(self):
        workspace, alias = self.make_workflow()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("保留其他内容")
        alias.rename(self.root / "original-alias")
        alias.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 400)
        self.assertTrue(workspace.exists())
        self.assertTrue((outside / "keep.txt").exists())
        self.assertEqual(self.client.delete("/api/produced-games/%2E%2E").status_code, 400)
        self.assertFalse((self.root / "deletions/release.json").exists())

    def test_deletion_refuses_overlapping_project_and_unowned_publication(self):
        workspace, _ = self.make_workflow()
        (self.projects / "nested.json").write_text(json.dumps({"id": "nested", "workspace": "games/source/subgame"}))
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 409)
        (self.projects / "nested.json").unlink()
        (self.projects / "owner.json").unlink()
        self.assertEqual(self.client.delete("/api/produced-games/release").status_code, 409)
        self.assertTrue(workspace.exists())

    def test_concurrent_delete_requests_are_idempotent(self):
        self.make_game()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(deletion.delete_game, ["sample", "sample"]))
        self.assertTrue(all(result["deleted"] for result in results))
        self.assertEqual(games.list_games()["total"], 0)
