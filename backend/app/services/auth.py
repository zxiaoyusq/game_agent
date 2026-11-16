"""网站账号与持久会话，密码及会话令牌仅保存不可逆摘要。"""

import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

PASSWORD_ITERATIONS = 600_000
SESSION_SECONDS = 7 * 24 * 60 * 60
COOKIE_NAME = "game_agent_session"


class InvalidCredentials(ValueError):
    """账号或密码校验未通过。"""


class LoginThrottled(ValueError):
    """同一来源短时间内多次输错密码。"""


def hash_password(password: str) -> str:
    """每个密码使用独立随机盐，迭代参数随摘要保存，便于后续升级。"""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """固定时间比较摘要，损坏或未知格式的密码记录按校验失败处理。"""
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthStore:
    """账号与会话共用 SQLite，重启后登录状态仍可验证，退出可立即撤销会话。"""

    def __init__(self, database: Path):
        self.database = database
        database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        database.parent.chmod(0o700)
        with closing(self._connect()) as connection, connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin'
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS login_attempts (
                    source_hash TEXT PRIMARY KEY,
                    failures INTEGER NOT NULL,
                    window_start INTEGER NOT NULL
                );
            """)
        database.chmod(0o600)

    def _connect(self):
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_user(self, username: str, password: str) -> None:
        """账号由服务端显式创建，网站启动不会重设已有密码。"""
        if not username or len(username) > 64 or not password or len(password) > 512:
            raise ValueError("用户名或密码长度无效")
        with closing(self._connect()) as connection, connection:
            connection.execute("INSERT INTO users(username, password_hash) VALUES (?, ?)",
                               (username, hash_password(password)))

    def login(self, username: str, password: str, source: str, previous_token: str = "") -> tuple[dict, str]:
        """在同一事务内限速并创建新会话，重复登录替换当前浏览器的旧令牌。"""
        timestamp = int(time.time())
        source_hash = token_digest(source)
        invalid = False
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (timestamp,))
            connection.execute("DELETE FROM login_attempts WHERE window_start <= ?", (timestamp - 60,))
            attempt = connection.execute("SELECT failures FROM login_attempts WHERE source_hash = ?", (source_hash,)).fetchone()
            if attempt and attempt["failures"] >= 10:
                raise LoginThrottled("登录尝试过于频繁，请稍后重试")
            user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            # 未知账号也执行同样的密码派生，避免通过响应耗时枚举账号。
            encoded = user["password_hash"] if user else f"pbkdf2_sha256${PASSWORD_ITERATIONS}${'00' * 16}${'00' * 32}"
            if not verify_password(password, encoded) or user is None:
                connection.execute("""INSERT INTO login_attempts VALUES (?, 1, ?)
                    ON CONFLICT(source_hash) DO UPDATE SET failures = failures + 1""", (source_hash, timestamp))
                invalid = True
            else:
                connection.execute("DELETE FROM login_attempts WHERE source_hash = ?", (source_hash,))
                if previous_token:
                    connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_digest(previous_token),))
                token = secrets.token_urlsafe(32)
                connection.execute("INSERT INTO sessions VALUES (?, ?, ?)",
                                   (token_digest(token), username, timestamp + SESSION_SECONDS))
                result = {"username": user["username"], "role": user["role"]}
        # 在事务提交后抛出错误，保留失败次数；回滚不能绕过登录限速。
        if invalid:
            raise InvalidCredentials("用户名或密码错误")
        return result, token

    def session_user(self, token: str) -> dict | None:
        if not token or len(token) > 128:
            return None
        with closing(self._connect()) as connection:
            user = connection.execute("""SELECT users.username, users.role FROM sessions
                JOIN users ON users.username = sessions.username
                WHERE token_hash = ? AND expires_at > ?""", (token_digest(token), int(time.time()))).fetchone()
        return dict(user) if user else None

    def logout(self, token: str) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_digest(token),))
