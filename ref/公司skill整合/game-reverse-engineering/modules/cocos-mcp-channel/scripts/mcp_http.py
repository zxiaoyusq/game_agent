# -*- coding: utf-8 -*-
"""通用 MCP-over-HTTP 客户端（Cocos Creator 编辑器 MCP 扩展，如 harady cocos-creator-mcp）。

用法（作为库）:
    from mcp_http import McpHttp
    m = McpHttp("http://127.0.0.1:3000/mcp")
    sid = m.session()
    r = m.call("server_status", {"action": "port"}, sid)

协议要点（实测）:
  - POST /mcp，JSON-RPC；initialize 后服务端返回 Mcp-Session-Id，后续调用必须带
  - 响应可能是 SSE（data: 行流）或纯 JSON，两种都要能解
  - 单次调用超时按工具估：编辑器批处理建议 45s，游戏桥命令 15~30s，启动预览 90s
"""
import json
import urllib.request


class McpHttp:
    def __init__(self, url="http://127.0.0.1:3000/mcp", call_timeout=300):
        self.url = url
        self.call_timeout = call_timeout

    def _post(self, body, sid=None, timeout=None):
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if sid:
            headers["Mcp-Session-Id"] = sid
        req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout or self.call_timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            return raw, r.headers.get("Mcp-Session-Id")

    @staticmethod
    def _parse(raw):
        chunks = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunks.append(line[5:].strip())
        txt = "".join(chunks) if chunks else raw
        return json.loads(txt) if txt.strip() else None

    def session(self, timeout=30):
        raw, sid = self._post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "artdiff", "version": "1.0"}},
        }, timeout=timeout)
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid=sid, timeout=timeout)
        return sid

    def call(self, tool, args=None, sid=None, timeout=None):
        sid = sid or self.session()
        raw, _ = self._post({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool, "arguments": args or {}},
        }, sid=sid, timeout=timeout or self.call_timeout)
        return self._parse(raw)

    def text(self, r):
        """取 tools/call 结果里的首个 text 内容（失败返回原文切片）。"""
        try:
            return r["result"]["content"][0]["text"]
        except Exception:
            return json.dumps(r, ensure_ascii=False)[:300]
