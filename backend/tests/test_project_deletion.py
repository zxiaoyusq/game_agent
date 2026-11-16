"""项目删除接口回归，全部工程与记录均位于临时目录。"""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.workflow import router
from app.services import produced_games
from app.services.workflow import engine


class ProjectDeletionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = self.root / "state"
        for module, name, value in ((engine, "ROOT", self.root), (engine, "STORE", self.store),
                                    (produced_games, "ROOT", self.root),
                                    (produced_games, "PROJECTS_DIR", self.store / "projects")):
            override = patch.object(module, name, value)
            override.start()
            self.addCleanup(override.stop)
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)
        self.project = {"id": "owner", "name": "待删除项目", "created_at": "2026-11-11",
                        "workspace": "games/custom/nested", "stages": []}
        self.write("state/projects/owner.json", self.project)
        self.write("state/runs/own-run.json", {"id": "own-run", "project_id": "owner", "status": "completed"})
        self.write("state/publications/release.json", {"project_id": "owner", "slug": "release"})
        for relative in ("games/custom/nested/workflow/plan.md", "games/custom/nested/dist/index.html",
                         "frontend/public/games/release/index.html", "state/artifacts/own-run/plan.md",
                         "state/inputs/own-run/skill.md"):
            self.write(relative, "测试产出")
        with closing(sqlite3.connect(self.store / "checkpoints.sqlite")) as connection:
            for table in ("checkpoints", "writes"):
                connection.execute(f"CREATE TABLE {table} (thread_id TEXT)")
                connection.executemany(f"INSERT INTO {table} VALUES (?)", [("own-run",), ("other-run",)])
            connection.commit()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value, encoding="utf-8")
        return path

    def delete(self):
        return self.client.delete("/api/workflow/projects/owner")

    def test_custom_workspace_and_owned_outputs_are_removed_by_project_id(self):
        unrelated = self.write("frontend/public/games/owner/index.html", "同名的其他游戏")
        response = self.delete()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["deleted_project_ids"], ["owner"])
        self.assertEqual(response.json()["deleted_ids"], ["release"])
        for relative in ("games/custom/nested", "frontend/public/games/release", "state/projects/owner.json",
                         "state/runs/own-run.json", "state/artifacts/own-run", "state/inputs/own-run",
                         "state/publications/release.json"):
            self.assertFalse((self.root / relative).exists(), relative)
        self.assertTrue(unrelated.exists())
        with closing(sqlite3.connect(self.store / "checkpoints.sqlite")) as connection:
            for table in ("checkpoints", "writes"):
                self.assertEqual(connection.execute(f"SELECT thread_id FROM {table}").fetchall(), [("other-run",)])
        self.assertEqual(self.client.get("/api/workflow/projects").json(), [])
        self.assertEqual(self.delete().status_code, 200)
        self.assertTrue(unrelated.exists())

    def test_empty_draft_can_be_deleted_without_a_game_build(self):
        self.project["workspace"] = "games/empty-draft"
        self.write("state/projects/owner.json", self.project)
        self.assertEqual(self.delete().status_code, 200)
        self.assertFalse((self.store / "projects/owner.json").exists())

    def test_shared_and_nested_workspaces_preserve_other_project_files(self):
        for shared_path in ("games/custom/nested", "games/custom"):
            with self.subTest(workspace=shared_path):
                self.write("state/projects/owner.json", self.project)
                self.write("state/projects/other.json", {**self.project, "id": "other", "workspace": shared_path})
                self.write("state/runs/other-run.json", {"id": "other-run", "project_id": "other", "status": "completed"})
                response = self.delete()
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["workspace_preserved"])
                self.assertTrue((self.root / "games/custom/nested/workflow/plan.md").exists())
                self.assertTrue((self.store / "projects/other.json").exists())
                self.assertTrue((self.store / "runs/other-run.json").exists())

    def test_running_execution_requires_stopping_before_deletion(self):
        self.write("state/runs/own-run.json", {"id": "own-run", "project_id": "owner", "status": "running"})
        self.assertEqual(self.delete().status_code, 409)
        self.write("state/runs/own-run.json", {"id": "own-run", "project_id": "owner", "status": "completed"})
        with patch.object(engine, "WORKERS", {"own-run": Mock(done=Mock(return_value=False))}):
            self.assertEqual(self.delete().status_code, 409)
        self.assertTrue((self.root / "games/custom/nested/workflow/plan.md").exists())
        self.assertTrue((self.store / "projects/owner.json").exists())
        self.assertEqual(self.delete().status_code, 200)

    def test_partial_failure_keeps_a_project_retry_entry_even_after_record_removal(self):
        original_unlink = Path.unlink

        def fail_journal(path, *args, **kwargs):
            if path == self.store / "deletions/project-owner.json":
                raise PermissionError("模拟最后的清理失败")
            return original_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", fail_journal), self.assertLogs("app.api.routes.workflow", level="ERROR"):
            self.assertEqual(self.delete().status_code, 503)
        self.assertFalse((self.store / "projects/owner.json").exists())
        projects = self.client.get("/api/workflow/projects").json()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["id"], "owner")
        self.assertTrue(projects[0]["deletion_pending"])
        self.assertEqual(self.delete().status_code, 200)
        self.assertEqual(self.client.get("/api/workflow/projects").json(), [])
        self.assertFalse((self.store / "deletions/project-owner.json").exists())

    def test_unsafe_workspace_cannot_delete_external_files(self):
        self.project["workspace"] = "games/../../outside"
        self.write("state/projects/owner.json", self.project)
        outside = self.write("outside/keep.txt", "保留")
        self.assertEqual(self.delete().status_code, 400)
        self.assertTrue(outside.exists())
        self.assertTrue((self.store / "projects/owner.json").exists())


if __name__ == "__main__":
    unittest.main()
