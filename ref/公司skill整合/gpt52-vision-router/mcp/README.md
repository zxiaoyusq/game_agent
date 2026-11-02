# gpt52-vision-router MCP Server

把 `gpt52-vision-router` skill 的识图能力封装成 **MCP（Model Context Protocol）stdio
server**，供没有原生视觉的 LLM（如 gpt-5.2 → deepseek-v4-flash-offcial）在遇到图片时调用
外部视觉模型识别。视觉模型优先读取技能目录下的 `vision_config.json`
（当前 MiMo `mimo-v2.5`），其次才是 `~/.gameartagent/user_models.json` 的
`cheap_vision` 实例；改本副本的模型只需编辑 `vision_config.json`。

## 文件

- `server.py` — 纯标准库 MCP stdio server（无第三方依赖，Python 3.10+）
- 复用上层 `scripts/vision_call.py` 的请求逻辑与配置读取

## 工具

| 工具 | 说明 |
| --- | --- |
| `recognize_image` | 传入本地图片路径数组 + 提问，调用外部视觉模型返回文字回答 |
| `check_image` | 只校验图片文件（存在性/格式/大小），不调模型 |
| `vision_config` | 查看当前生效的视觉模型配置（API Key 打码） |

## 注册（Codex）

在 `~/.codex/config.toml` 追加：

```toml
[mcp_servers.gpt52_vision]
command = 'C:\Program Files\Python312\python.exe'
args = ['C:\Users\nenghong.zhao\.codex\skills\gpt52-vision-router\mcp\server.py']
startup_timeout_sec = 60

[mcp_servers.gpt52_vision.env]
PYTHONIOENCODING = 'utf-8'
```

重启 Codex 后即可看到 `gpt52_vision` 前缀的 MCP 工具。

## 手工验证

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"0"}}}' | python server.py
```

## 使用边界（与 SKILL.md 一致）

- 仅当活动模型**没有原生视觉**时使用（典型：gpt-5.2）。
- GPT-5.6 Sol/Terra/Luna 等有原生识图的模型**不要**走本服务，避免覆盖原生能力。
- API Key 存于技能目录 `vision_config.json`（本副本专属），不入库。
