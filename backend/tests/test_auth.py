"""网站登录与接口保护回归，账号及会话数据库均使用临时目录。"""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from app.main import create_app
from app.services import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "auth" / "users.sqlite"
        self.store = auth.AuthStore(self.path)
        self.store.create_user("admin", "test-password-only")
        self.app = create_app(auth_store=self.store)
        self.client = TestClient(self.app, base_url="https://testserver")
        self.headers = {"X-Requested-With": "GameAgent"}

    def login(self, password="test-password-only", username="admin"):
        return self.client.post("/api/auth/login", headers=self.headers,
                                json={"username": username, "password": password})

    def test_anonymous_requests_cannot_read_or_change_workspace(self):
        for path in ("/api/auth/session", "/api/workflow/projects", "/api/knowledge/overview",
                     "/api/produced-games", "/api/reference-games", "/docs", "/openapi.json"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["detail"], "请先登录")
        self.assertEqual(self.client.head("/api/produced-games/example/play/index.html").status_code, 401)
        with patch("app.services.workflow.engine.create_project") as create:
            response = self.client.post("/api/workflow/projects", json={"name": "不应创建"}, headers=self.headers)
        self.assertEqual(response.status_code, 401)
        create.assert_not_called()
        self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_password_hash_and_database_permissions(self):
        with closing(sqlite3.connect(self.path)) as connection:
            encoded = connection.execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertNotIn("test-password-only", encoded)
        self.assertTrue(encoded.startswith("pbkdf2_sha256$600000$"))
        self.assertTrue(auth.verify_password("test-password-only", encoded))
        self.assertFalse(auth.verify_password("wrong", encoded))
        self.assertNotEqual(auth.hash_password("test-password-only"), encoded)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_only_current_business_routes_are_exposed(self):
        """登录后旧接口确实不存在，当前工作流与资料入口仍在路由表中。"""
        self.login()
        paths = self.client.get("/openapi.json").json()["paths"]
        for prefix in ("/api/art", "/api/planning", "/api/dev", "/api/tasks", "/api/chat", "/api/models"):
            with self.subTest(prefix=prefix):
                self.assertFalse(any(path == prefix or path.startswith(prefix + "/") for path in paths))
        for method, path in (("POST", "/api/art/image/generate"), ("POST", "/api/planning/stream"),
                             ("POST", "/api/dev/demo/plan"), ("POST", "/api/dev/demo/generate"),
                             ("GET", "/api/tasks/ping"), ("GET", "/api/chat/ping"), ("GET", "/api/models")):
            with self.subTest(path=path):
                self.assertEqual(self.client.request(method, path, headers=self.headers).status_code, 404)
        for path in ("/api/workflow/projects", "/api/workflow/templates", "/api/workflow/runtime",
                     "/api/workflow/reference-games", "/api/knowledge/modules", "/api/produced-games"):
            self.assertIn(path, paths)

    def test_wrong_password_or_username_return_the_same_error(self):
        wrong_password = self.login("wrong")
        wrong_username = self.login(username="missing")
        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(wrong_username.json(), wrong_password.json())
        self.assertNotIn("set-cookie", wrong_password.headers)
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)

    def test_login_sets_private_cookie_and_session_survives_app_recreation(self):
        response = self.login()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"user": {"username": "admin", "role": "admin"}})
        cookie = response.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=lax", cookie)
        self.assertEqual(response.headers["cache-control"], "no-store")
        token = self.client.cookies.get(auth.COOKIE_NAME)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("SELECT token_hash FROM sessions").fetchone()[0], auth.token_digest(token))
        restarted = TestClient(create_app(auth_store=auth.AuthStore(self.path)), base_url="https://testserver")
        restarted.cookies.set(auth.COOKIE_NAME, token)
        self.assertEqual(restarted.get("/api/auth/session").json()["user"]["username"], "admin")
        self.assertEqual(restarted.get("/docs").status_code, 200)

    def test_logout_revokes_token_and_relogin_rotates_it(self):
        self.login()
        old_token = self.client.cookies.get(auth.COOKIE_NAME)
        self.login()
        token = self.client.cookies.get(auth.COOKIE_NAME)
        self.assertNotEqual(token, old_token)
        self.assertIsNone(self.store.session_user(old_token))
        response = self.client.post("/api/auth/logout", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.store.session_user(token))
        self.client.cookies.set(auth.COOKIE_NAME, token)
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)

    def test_expired_session_is_rejected(self):
        self.login()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("UPDATE sessions SET expires_at = 0")
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)

    def test_write_requests_require_the_browser_header_and_reject_cross_site_preflight(self):
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "admin", "password": "test-password-only"}).status_code, 403)
        self.login()
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)
        self.assertEqual(self.client.get("/api/auth/session").status_code, 200)
        response = self.client.options("/api/workflow/projects", headers={
            "Origin": "https://external.invalid", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-requested-with,content-type"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_failed_attempts_are_committed_and_limited(self):
        with patch.object(auth, "verify_password", return_value=False):
            for _ in range(10):
                self.assertEqual(self.login("wrong").status_code, 401)
            response = self.login("wrong")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "60")

    def test_streaming_responses_still_work_after_login(self):
        @self.app.post("/api/test-stream")
        def stream():
            return StreamingResponse(iter(["data: 开始\n\n", "data: 完成\n\n"]), media_type="text/event-stream")

        self.login()
        response = self.client.post("/api/test-stream", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "data: 开始\n\ndata: 完成\n\n")
        self.assertNotIn("password", json.dumps(self.client.get("/api/auth/session").json()))


if __name__ == "__main__":
    unittest.main()
