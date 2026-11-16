"""实时工作台的轻量事件、构建版本与静态文件边界回归。"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.workflow import router
from app.services.workflow import engine
from app.services.workflow.activity import activity_run
from app.services.workflow.preview import describe_preview, preview_file


class WorkflowActivityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.base = self.root / "games" / "demo" / "dist"
        self.base.mkdir(parents=True)
        self.write("index.html", '<html><script type="module" src="./game.js?v=1"></script></html>')
        self.write("game.js", 'document.body.textContent = "游戏版本一"')

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, content):
        file = self.base / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        os.utime(file, (time.time() - 5, time.time() - 5))
        return file

    def test_revision_tracks_assets_without_resetting_on_workflow_logs(self):
        initial = describe_preview("demo", self.base, "index.html")
        self.assertEqual(initial["status"], "ready")
        self.write("workflow/log.json", '{"event":"新的执行日志"}')
        unchanged = describe_preview("demo", self.base, "index.html")
        self.assertEqual(initial["revision"], unchanged["revision"])
        self.write("game.js", 'document.body.textContent = "游戏版本二"')
        self.assertNotEqual(initial["revision"], describe_preview("demo", self.base, "index.html")["revision"])
        self.write("texture.png", "贴图测试字节")
        self.assertEqual(describe_preview("demo", self.base, "index.html")["file_count"], 3)

    def test_build_waits_for_entry_dependencies_and_quiet_writes(self):
        (self.base / "game.js").unlink()
        self.assertEqual(describe_preview("demo", self.base, "index.html")["status"], "waiting")
        file = self.write("game.js", "const version = 2")
        os.utime(file, None)
        self.assertEqual(describe_preview("demo", self.base, "index.html")["status"], "waiting")
        self.write("game.js", "const version = 3")
        self.assertEqual(describe_preview("demo", self.base, "index.html")["status"], "ready")
        self.write("index.html", "")
        self.assertEqual(describe_preview("demo", self.base, "index.html")["status"], "waiting")

    def test_preview_blocks_private_files_and_symlinks(self):
        for name in [".env", "auth.json", "package.json", ".cache/test.js", "node_modules/runtime.js", "../private.json"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                preview_file(self.base, name)
        (self.base / "linked.js").symlink_to(self.base / "game.js")
        with self.assertRaises(ValueError):
            preview_file(self.base, "linked.js")
        self.assertEqual(preview_file(self.base, "game.js"), self.base / "game.js")

    def test_activity_keeps_tool_pairing_and_user_questions_without_heavy_payloads(self):
        run = {"id": "run", "stage": "code", "status": "awaiting_input", "initial_snapshot": {"private": "省略"},
               "interrupts": [{"id": "question", "value": {"question": "选哪种颜色？"}}], "events": []}
        content = [{"type": "reasoning", "encrypted_content": "内部负载"},
                   {"type": "image", "data": "x" * 1_000_000}, {"type": "text", "text": "准备实现走子动画。"}]
        payloads = [
            ("model_completed", {"content": content}),
            ("graph_update", {"message": {"type": "ai", "id": "message", "content": content, "tool_calls": [
                {"id": "call", "name": "write_file", "args": {"file_path": "src/game.js", "content": "源代码" * 10000}}]}}),
            ("graph_update", {"message": {"type": "tool", "tool_call_id": "call", "status": "error", "content": "写入失败"}}),
        ]
        for index, (kind, data) in enumerate(payloads):
            run["events"].append({"seq": index + 1, "time": "2026-11-09T00:00:00Z", "type": kind, "message": "事件", "data": data})
        result = activity_run(run)
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertLess(len(encoded), 2000)
        self.assertNotIn("内部负载", encoded)
        self.assertNotIn("initial_snapshot", encoded)
        self.assertEqual(result["events"][1]["data"]["message"]["content"], "准备实现走子动画。")
        self.assertEqual(result["events"][2]["data"]["message"]["tool_call_id"], "call")
        self.assertEqual(result["interrupts"], run["interrupts"])

    def test_rest_activity_and_no_cache_preview(self):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        store = self.root / "state"
        with patch.object(engine, "ROOT", self.root), patch.object(engine, "STORE", store):
            project = engine.create_project("实时预览", {}, "games/demo", [])
            client = TestClient(app)
            result = client.get(f"/api/workflow/projects/{project['id']}/activity")
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["project"]["preview"]["status"], "ready")
            self.assertEqual(result.json()["runs"], [])
            url = result.json()["project"]["preview"]["url"]
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(client.get(url.replace("index.html", "game.js")).status_code, 200)
            self.assertEqual(client.get(url.replace("index.html", "auth.json")).status_code, 409)

    def test_archive_error_keeps_member_and_correlation_for_old_and_new_logs(self):
        events = [
            {"seq": 1, "time": "2026-11-09T00:00:00Z", "type": "graph_update", "message": "工具请求", "data": {
                "message": {"type": "ai", "tool_calls": [{"id": "call", "name": "read_reference_archive", "args": {
                    "path": "demo.zip", "member": "assets/config.json", "content": "不应复制的正文"}}]}}},
            {"seq": 2, "time": "2026-11-09T00:00:01Z", "type": "tool_error", "message": "工具失败", "data": {
                "tool": "read_reference_archive", "error": "包内不存在指定文件"}},
        ]
        result = activity_run({"id": "run", "events": events})
        self.assertEqual(result["events"][0]["data"]["message"]["tool_calls"][0]["args"],
                         {"path": "demo.zip", "member": "assets/config.json"})
        self.assertEqual(result["events"][1]["data"]["tool"], "read_reference_archive")
        events[1]["data"].update(call_id="call", arguments={"member": "assets/config.json"})
        result = activity_run({"id": "run", "events": events})
        self.assertEqual(result["events"][1]["data"]["call_id"], "call")
        self.assertEqual(result["events"][1]["data"]["arguments"]["member"], "assets/config.json")


if __name__ == "__main__":
    unittest.main()
