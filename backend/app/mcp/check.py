"""使用真实 HTTP MCP 客户端检查接入；仅查询能力，不创建项目或调用模型。"""

import asyncio
import os
from urllib.parse import urlsplit

import httpx2
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def check() -> None:
    """从环境读取凭据，完成握手、工具发现和一次经过认证的工具调用。"""
    url = os.environ.get("GAME_AGENT_MCP_URL", "")
    token = os.environ.get("GAME_AGENT_MCP_TOKEN", "")
    if not url or not token:
        raise SystemExit("请先加载客户端凭据中的 GAME_AGENT_MCP_URL 和 GAME_AGENT_MCP_TOKEN")
    # 本机检查不经过环境里的 SOCKS/HTTP 代理；远程地址仍遵循运维代理设置。
    local = urlsplit(url).hostname in {"localhost", "127.0.0.1", "::1"}
    transport = StreamableHttpTransport(
        url, headers={"Authorization": f"Bearer {token}"},
        httpx_client_factory=lambda **kwargs: httpx2.AsyncClient(trust_env=not local, **kwargs),
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        result = await client.call_tool("get_capabilities", {})
    print(f"MCP 连接正常，可发现 {len(tools)} 个工具。")
    print(f"可访问项目：{result.data['project_ids']}")
    print(f"可创建项目：{'是' if result.data['can_create_projects'] else '否'}")


if __name__ == "__main__":
    asyncio.run(check())
