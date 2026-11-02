"""MCP 客户端身份与项目授权配置，不保存或输出明文令牌。"""

import hashlib
import hmac
import re
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

from fastmcp.server.auth import AccessToken, TokenVerifier
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9_-]{1,128}$")]


class MCPClient(BaseModel):
    """一份令牌对应一个稳定调用方；项目白名单用于接口授权，不是执行沙箱。"""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    client_id: Identifier
    token_sha256: str = Field(pattern=r"^[a-f0-9]{64}$", repr=False)
    project_ids: list[str] = Field(min_length=1)
    can_create_projects: bool = False

    @model_validator(mode="after")
    def validate_projects(self):
        """只允许明确的项目标识或单独的通配符；创建项目必须拥有全项目权限。"""
        valid_ids = all(re.fullmatch(r"[a-z0-9_-]{1,128}", value) for value in self.project_ids)
        if self.project_ids != ["*"] and not valid_ids:
            raise ValueError("project_ids 须为项目标识列表，或单独的 ['*']")
        if self.can_create_projects and self.project_ids != ["*"]:
            raise ValueError("创建新项目需要 project_ids=['*']")
        return self


class MCPSettings(BaseModel):
    """显式配置后才挂载服务；public_url 是含 /mcp 的外部入口，不从请求 Host 推导。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clients: list[MCPClient] = Field(min_length=1)
    public_url: str = "http://127.0.0.1:8003/mcp"

    @model_validator(mode="after")
    def validate_settings(self):
        """拒绝重复身份与不安全的外部地址，配置错误时启动失败。"""
        for field in ("client_id", "token_sha256"):
            values = [getattr(client, field) for client in self.clients]
            if len(values) != len(set(values)):
                raise ValueError("客户端标识和令牌摘要不能重复")
        url = urlsplit(self.public_url)
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        if (url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password
                or any(character.isspace() or ord(character) < 32 for character in self.public_url)
                or url.query or url.fragment or url.path.rstrip("/") != "/mcp"
                or (url.scheme == "http" and not local)):
            raise ValueError("public_url 须为以 /mcp 结尾的 HTTPS 地址；仅本机允许 HTTP")
        # 显式访问 port，让 URL 解析器同时校验端口格式和范围。
        _ = url.port
        return self


def load_settings(path: Path) -> MCPSettings:
    """读取专用配置；不把配置内容放进异常，避免日志包含凭据摘要。"""
    try:
        return MCPSettings.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("MCP 配置无法读取或格式错误，请检查客户端、项目权限和 public_url") from None


class ClientTokenVerifier(TokenVerifier):
    """使用 FastMCP 的认证扩展点，复用其 HTTP 认证和请求上下文。"""

    def __init__(self, clients: list[MCPClient]):
        super().__init__()
        self.clients = {client.client_id: client for client in clients}

    async def verify_token(self, token: str) -> AccessToken | None:
        """仅比较高熵令牌的 SHA256；HTTP 端和产物下载端使用同一校验器。"""
        digest = hashlib.sha256(token.encode()).hexdigest()
        for client in self.clients.values():
            if hmac.compare_digest(digest, client.token_sha256):
                return AccessToken(token=token, client_id=client.client_id, scopes=["workflow"])
        return None
