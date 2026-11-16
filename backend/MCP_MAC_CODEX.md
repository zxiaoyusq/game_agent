# 游戏研发 MCP 通用接入与使用说明

本文适用于 **Windows、macOS、Linux** 上支持远程 MCP 的 Agent 客户端，包括 Codex、Claude Code、
Cursor、VS Code 的相应 Agent 模式，以及使用 MCP SDK 开发的自建 Agent。
文件名 `MCP_MAC_CODEX.md` 为兼容旧链接保留，内容已不限定 Mac 或 Codex；可以整份转交给其他 Agent。

**选择 `model_provider:"api-key"` 就直接使用服务器已配置的模型 API Key。
调用方无需提供自己的模型 Key，也不需要在本机配置模型密钥。不要向用户索要模型 API Key。**
连接服务所需的 **MCP Token** 由管理员提供，与模型 API Key 是两种不同凭据。

## 给接收本说明的 Agent

用户要求接入时，请识别当前操作系统、客户端、版本和实际执行主机，完成配置及只读验证。
保留已有模型、项目与其他 MCP 配置，仅添加或更新 `game_agent`；不修改全局审批策略。
不要为了验证连接自动创建项目、启动研发任务或调用付费模型。

统一连接参数如下，**配置文件格式按客户端选择，不能直接跨客户端复制**：

| 参数 | 值 |
| --- | --- |
| 服务名称 | `game_agent` |
| 服务地址 | `https://pagent.ahagamecenter.com/mcp/` |
| 传输协议 | Streamable HTTP |
| HTTP 认证头 | `Authorization: Bearer <管理员提供的MCP Token>` |
| 服务端模型来源 | `model_provider: "api-key"` |
| 服务端模型示例 | `model_id: "gpt-6.1-sol"`；其他可用值查询 `get_capabilities` |
| 本地运行环境 | 原生支持远程 MCP 的客户端不需要安装本服务的 Python、DeepAgents、Multica 或游戏工程 |

接入要求是客户端能发起 Streamable HTTP MCP 请求，并携带上述认证头。
仅支持本地 STDIO、旧版 SSE 或仅支持 OAuth 登录且不能设置 Bearer 的客户端，不能仅填写 URL 就直连；
应使用其正式支持的 HTTP 适配器或支持该协议的版本。当前服务不提供 OAuth 登录，也没有单独的 `/sse` 入口。
云端 Agent 的连接和密钥需配置在实际云端执行环境；SSH、WSL、容器中的配置也应放在实际运行客户端的一端。

## 凭据与跨平台路径

管理员提供的凭据文件只有连接令牌和地址，例如：

```dotenv
GAME_AGENT_MCP_TOKEN=管理员提供的真实MCP令牌
GAME_AGENT_MCP_URL=https://pagent.ahagamecenter.com/mcp/
```

示例中文不是可用令牌。已有 `mac-codex.env` 也可继续使用，文件名不限制客户端或操作系统；
更换客户端不会要求更换模型 API Key。不同使用者由管理员分配各自 MCP 身份及项目权限。

以下是本文建议的凭据位置，**不是客户端自动读取的标准目录**：

| 环境 | 建议位置 |
| --- | --- |
| macOS / Linux | `~/.config/game-agent/client.env`；也可使用用户指定的现有路径 |
| Windows 原生 | `%APPDATA%\game-agent\client.env`；PowerShell 中使用 `$env:APPDATA` |
| WSL / SSH / 容器 | 实际运行 Agent 的 Linux 环境内的路径，不能假定宿主机文件可见 |
| 云端 Agent | 平台私有密钥配置或该执行环境内可读取的凭据文件 |

接收本文的 Agent 应通过本机文件 API 读取赋值，或使用用户提供的 `GAME_AGENT_MCP_TOKEN` 环境变量。
文件读取时使用 UTF-8（兼容 BOM），按赋值解析，不执行 `.env` 里的 shell 内容。
macOS/Linux 可用 `0600` 文件权限；Windows 使用文件 ACL 控制访问，不照搬 `chmod`。
不要回显 Token、写入 URL 或项目仓库，也不要把服务器模型 Key 复制到调用方。

将凭据转换为下文对应客户端的认证设置，或者注入**该客户端进程**的 `GAME_AGENT_MCP_TOKEN` 环境变量。
保存 `.env` 文件本身不会让客户端自动加载；已打开的桌面程序也不会自动获得终端中新设的变量。
只缺 MCP 凭据时，请用户提供凭据文件位置或由管理员配置连接身份，不请求模型 API Key。

## 各客户端配置

先备份实际生效的配置，按 JSON/TOML 结构合并 `game_agent`，保留其他服务和用户设置。
下例中的变量引用不能原样作为最终 HTTP 令牌发送；配置完成后必须做后面的协议验证。
如果使用静态认证头，由本地程序读取凭据后用 JSON/TOML 序列化器写入当前用户的私有配置，
不要通过聊天复制真实值。环境变量和静态头选择一种认证来源即可。

### Codex

使用当前 Codex 环境的 `config.toml`，通常位于用户目录的 `.codex/config.toml`；
Windows 用户目录一般为 `%USERPROFILE%`，配置了自定义目录时以实际位置为准。
原生 Windows、WSL 与远程执行环境的配置位置应分别确认。

客户端进程已获得环境变量时：

```toml
[mcp_servers.game_agent]
url = "https://pagent.ahagamecenter.com/mcp/"
bearer_token_env_var = "GAME_AGENT_MCP_TOKEN"
enabled = true
startup_timeout_sec = 30
tool_timeout_sec = 60
```

也可通过 CLI 登记；以下单行命令不含真实令牌，在 bash、zsh、PowerShell 中都不需要改换行符：

```text
codex mcp add game_agent --url https://pagent.ahagamecenter.com/mcp/ --bearer-token-env-var GAME_AGENT_MCP_TOKEN
```

桌面进程不便注入环境变量时，可将 `bearer_token_env_var` 替换为：

```toml
http_headers = { Authorization = "Bearer <本地程序从凭据文件填入的真实MCP Token>" }
```

静态 `http_headers` 不展开 `${变量名}`。固定 Bearer 接入不使用 `codex mcp login`。
配置字段参考 [OpenAI 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp)，并以本机 `codex mcp add --help` 核对版本支持。

### Claude Code

Claude Code 的项目配置文件为项目根目录 `.mcp.json`，合并以下条目：

```json
{
  "mcpServers": {
    "game_agent": {
      "type": "http",
      "url": "https://pagent.ahagamecenter.com/mcp/",
      "headers": {"Authorization": "Bearer ${GAME_AGENT_MCP_TOKEN}"}
    }
  }
}
```

这里的 `${GAME_AGENT_MCP_TOKEN}` 由 Claude Code 从自身进程环境读取。
若需跨项目使用，选择用户作用域，保留用户配置中的其他内容；不要将模型配置写入这个文件。
以上配置针对 Claude Code，不能据此假定 Claude Desktop 或网页连接器使用同一格式。
依据 [Claude Code 官方 MCP 文档](https://code.claude.com/docs/en/mcp)。

### Cursor

在实际用户目录的 `.cursor/mcp.json` 添加全局配置，或在项目的 `.cursor/mcp.json` 添加项目配置：

```json
{
  "mcpServers": {
    "game_agent": {
      "url": "https://pagent.ahagamecenter.com/mcp/",
      "headers": {"Authorization": "Bearer ${env:GAME_AGENT_MCP_TOKEN}"}
    }
  }
}
```

Cursor 这里使用 `${env:变量名}`，与上面的 Claude Code 写法不同。
远程 HTTP 配置不使用 STDIO 专用的 `envFile`；需让实际 Cursor 进程获得变量，
或在用户私有配置里写入静态认证头。依据 [Cursor 官方 MCP 文档](https://cursor.com/docs/mcp)。

### VS Code

使用命令面板打开目标用户或远程环境的 MCP 配置，或者编辑工作区 `.vscode/mcp.json`。
下面是 **VS Code 自身的 `mcp.json` 格式**：

```json
{
  "servers": {
    "game_agent": {
      "type": "http",
      "url": "https://pagent.ahagamecenter.com/mcp/",
      "headers": {"Authorization": "Bearer ${env:GAME_AGENT_MCP_TOKEN}"}
    }
  }
}
```

VS Code 可选择不同 Agent 执行环境。上例使用 `servers`；Copilot 的可移植配置等其他格式
可能使用 `mcpServers` 和 `${变量名}`。应按当前 Agent 实际采用的配置格式设置，不能混用。
在 SSH/容器环境运行时，令牌也须在实际连接 MCP 的环境中可用。
依据 [VS Code 官方 MCP 配置参考](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)。

### 其他 Agent 或可视化配置界面

选择“远程 MCP / Streamable HTTP”，填入统一 URL，并在 Headers 中配置
`Authorization` 为 `Bearer ` 加实际 MCP Token。如果界面有 Bearer Token 专用字段，
按该界面的要求填写，避免重复添加 `Bearer ` 前缀。

不要把 Codex 的 `http_headers`、Claude/Cursor 的 `mcpServers` 或 VS Code 的 `servers`
当成 MCP 协议强制规定的统一配置文件格式。客户端只支持 STDIO 或 OAuth 时，先确认适配能力。

### 自建 Agent：Python SDK 只读连接示例

自建客户端只需实现 MCP 初始化、工具发现和工具调用。下例适用于 Python 3.10+，
使用与本工程相同的 FastMCP 4.1.4；不需要安装整个服务器工程。
已有原生 MCP 客户端时无需安装这个 SDK。

```text
python -m pip install fastmcp==4.1.4
```

把下面保存为 `check_game_agent.py`。凭据路径从命令行传入，参数中不包含真实 Token：

```python
import asyncio
import json
import shlex
import sys
from pathlib import Path
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    values = {}
    credential = Path(sys.argv[1]).expanduser()
    for line in credential.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() in {"GAME_AGENT_MCP_TOKEN", "GAME_AGENT_MCP_URL"}:
            parts = shlex.split(value, comments=True)
            if len(parts) == 1:
                values[key.strip()] = parts[0]
    url = values.get("GAME_AGENT_MCP_URL", "").rstrip("/")
    token = values.get("GAME_AGENT_MCP_TOKEN", "")
    if url != "https://pagent.ahagamecenter.com/mcp" or not token:
        raise ValueError("请检查凭据文件中的 MCP 地址与令牌")
    transport = StreamableHttpTransport(url + "/", headers={"Authorization": "Bearer " + token})
    async with Client(transport) as client:
        tools = await client.list_tools()
        capabilities = await client.call_tool("get_capabilities", {
            "model_provider": "api-key", "model_id": "gpt-6.1-sol"})
        projects = await client.call_tool("list_projects", {})
        print(json.dumps({"工具数": len(tools),
                          "服务器API已配置": capabilities.data["model_runtime"]["configured"],
                          "可见项目数": projects.data["total"]}, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
```

macOS/Linux 示例（按实际 Python 命令调整）：

```bash
python3 check_game_agent.py "$HOME/.config/game-agent/client.env"
```

Windows PowerShell 示例（已安装 Python Launcher 时）：

```powershell
py -3 check_game_agent.py "$env:APPDATA\game-agent\client.env"
```

SDK 客户端成功不代表某个桌面 Agent 已加载该配置；还需回到目标客户端完成下面的验证。

## 验证接入成功

通过目标 Agent 的 MCP 管理界面重新连接或重新加载配置，必要时开启新会话；
不要强制终止用户其他任务。使用其已加载的工具完成以下只读验证：

1. 完成 MCP 初始化及 `tools/list`。检查 `get_capabilities`、`list_templates`、`get_template`、
   `start_pipeline`、`get_run`、`get_pending_questions`、`answer_questions`、`get_reference_upload_info` 等工具。
2. 调用 `get_capabilities`，检查阶段、框架、项目权限和 `can_create_projects`；
   选择 `model_provider:"api-key"`、`model_id:"gpt-6.1-sol"` 只检查服务器配置，不发起付费推理。
3. 调用 `list_projects`，确认得到结构化项目列表。空列表也可以表示接入成功，不要为测试创建项目。
4. 按需 `list_skills`；技能在服务器执行，不需要在调用方再安装一套。

工具名称可能带客户端自己的服务前缀，以实际发现的名称和 Schema 为准；不按固定工具数量判断成功。

| 现象 | 处理方式 |
| --- | --- |
| `200 text/html`，返回网页或登录页 | 检查 `/mcp/` 转发及网页认证层；HTML 不是 MCP 工具响应 |
| `404` | 检查是否启用 MCP、后端是否加载新版、转发路径是否正确 |
| `401` | 核对 MCP Token、环境变量是否进入实际客户端，以及代理是否保留 Authorization |
| 工具报告“无权访问该项目” | 使用当前身份允许的项目，或由管理员调整项目权限 |
| 上传 `413` | 文件超过服务或代理上限；核对上传大小，不能靠重复提交解决 |
| `502` / `503` | 检查入口到后端的连接 |
| TLS / DNS / 连接超时 | 检查实际执行主机的网络与证书；不关闭证书验证 |
| 配置存在但当前会话无工具 | 核对客户端、执行环境和配置作用域，重新加载连接或开启新会话 |

分别报告“配置已保存”“MCP 协议验证通过”“目标 Agent 已加载工具”，三者不能互相替代。
服务器本机通过验证不代表调用方网络已可达；不要改连调用方自己的 `127.0.0.1`。

## 工具清单

调用时以服务器实际返回的 Schema 为准。所有 `request_id` 由调用方生成并保存，
同一请求超时重试时不换标识；真正的新操作才生成新标识。

| 工具 | 必填参数 | 用途 |
| --- | --- | --- |
| `get_capabilities` | 无 | 能力、模型来源、当前身份权限；可选 `model_provider`、`model_id` |
| `list_templates` / `get_template` | 后者 `template_id` | 获取全流程模板列表／完整内容 |
| `list_references` | 无 | 用可选 `query` 查询服务器参考资料，取得引用路径 |
| `get_reference_upload_info` | 无 | 获得本机文件上传地址和限制 |
| `list_skills` | 无 | 获取远程 Skill 路径、摘要、版本哈希 |
| `list_projects` / `get_project` | 后者 `project_id` | 授权项目，计划摘要、全流程状态与发布结果 |
| `create_project` | `request_id`、`name` | 保存需求、引用、模型配置及可选完整 `production_plan` |
| `start_pipeline` | `project_id`、`request_id` | 一次开始原型、美术、代码、测试四阶段 |
| `get_run` | `run_id` | 阶段状态、模型来源、摘要、待答问题 |
| `get_run_events` | `run_id` | 通过 `after`、`limit` 增量查询活动记录 |
| `get_pending_questions` | `run_id` | 用 `offset`、`limit` 分页获取全部待答问题 |
| `answer_questions` | `run_id`、`answers`、`request_id` | 将答案交给原 DeepAgents 继续执行 |
| `cancel_pipeline` / `resume_pipeline` | `project_id`、`request_id` | 取消或恢复整个流程 |
| `list_artifacts` / `read_artifact` | `run_id`；后者还有 `artifact_id` | 读取产物、哈希和认证下载地址 |
| `publish_project` | `project_id`、`slug`、`request_id` | 将验收通过的构建发布到独立网页路径 |
| `preview_skill_selection` | `project_id`、`stage` | 只读预览建议技能和能力限制 |
| `start_stage` | `project_id`、`stage`、`request_id` | 兼容手动单阶段执行 |
| `confirm_stage` | `project_id`、`stage`、`run_id`、`request_id` | 确认当前手动阶段产物；可选 `note` |
| `cancel_run` / `resume_run` | `run_id`；恢复还有 `request_id` | 兼容手动运行的取消／恢复 |

阶段固定为 `prototype`（原型定义）、`art`（美术资源）、`code`（代码与集成）、
`test`（测试验收）。品类、框架、Skill 与模板从服务器查询，不能根据名字猜测可用值。
列表通常使用 `offset`、`limit`，每页最多 50 项；以 `next_offset` 和 `has_more` 翻页。
事件用 `next_cursor` 作为下一次 `after`；文本正文按字符分页，每次最多 16000 字。

## 用 API Key 模型完成一次完整制作

游戏面向玩家的文案默认使用英文，包括菜单、按钮、教程和文字贴图；中文需求描述不会自动将游戏设为中文。
如需中文或其他语言，在项目需求中明确指定即可。Agent 沟通、阶段报告、代码注释和日志仍使用中文。

只在用户提出实际研发任务后执行。用户指定已有项目时，先用 `get_project` 查看状态，
不要每次对话都重新创建。下面是新建项目的完整流程，无需用户分别输入四次提示词。

### 1. 读取模板并整理输入

先调用 `list_templates`，然后按返回的真实 ID 调用 `get_template`。通用 H5 模板为
`web-game`；要保留原游戏表现制作 LUDO 时可选择 `ludo-classic`，并核对其中参考资料真实可用。

```json
{"template_id":"web-game"}
```

从返回模板复制以下字段作为 `create_project` 的参数基础：

```text
name, brief, genre_id, framework_id, knowledge_paths, references,
model_provider, model_id, production_plan
```

再加入新的 `request_id`、修改项目名称和用户需求。不发送模板顶层的 `schema_version`、
`id`、`description`；它们不是创建参数。`production_plan.template_id` 保留即可。
接口没有顶层 `template_id` 自动合并功能，客户端负责把确认的完整模板传入并保存原请求，
避免断线重试时读取了新版模板、改变原先的执行内容。
`get_project` 返回的计划是摘要，不含完整阶段提示词，不能用它代替保存的原始创建配置。

`brief` 支持文字或结构化对象。以下是需要合并到模板的需求示例，**不应替代完整模板**：

```json
{
  "request_id": "create-amber-001",
  "name": "琥珀商路",
  "brief": {
    "name": "琥珀商路",
    "genre": "轻量经营与路线策略",
    "platform": "手机与电脑浏览器，支持触摸和鼠标",
    "engine": "Canvas 2D · Web / H5",
    "audience": "休闲策略玩家",
    "cycle": "可试玩版本并部署到独立路径",
    "idea": "在城镇之间运输商品，根据价格、距离和事件选择商路，赚取金币升级商队。",
    "scope": "完整贸易循环、引导、存档、移动动画、音效开关与响应式布局"
  },
  "model_provider": "api-key",
  "model_id": "gpt-6.1-sol"
}
```

新项目默认使用 `model_provider:"api-key"`、`model_id:"gpt-6.1-sol"`，这两个字段可以省略。
`api-key` 使用服务器 `backend/.env` 配置的 API Key，调用方不需要提供或配置自己的模型密钥。
需要其他模型时显式指定模型参数；新项目显式选择 `codex-login` 才会使用服务器的 Codex 登录。
调用方 Agent 自己使用什么模型与服务端执行模型独立。启动阶段继承项目设置，已有项目及恢复旧任务保留原来源。
重试升级前的项目创建请求时须显式传入原模型来源，否则同一 `request_id` 会返回参数冲突；
需要新建 API 项目时应使用新的 `request_id`。
不要将 OpenAI API Key 填进 MCP Token、需求文本或工具参数。

统一美术要求写在 `production_plan.art_requirements`，例如明确：保留哪些原棋盘、棋子、
布局和动画，只替换哪些贴图，必须使用哪些参考素材。四阶段 `prompt` 沿用模板并按需求调整，
保留构建、测试、交付和美术证据要求。需要额外美术 Skill 时先 `list_skills`，
把真实路径加入 `production_plan.stages.art.skill_paths`；`skill_mode:auto` 表示在自动路由上补充。
`manual` 只使用显式列表，空列表不会自动选技能。可以在启动前 `preview_skill_selection`。

参考文件、知识与 Skill 的路径含义不同：

- `references`：从 `list_references` 或上传结果取得的服务器资料引用。
- `knowledge_paths`：服务器知识库路径；保留模板值或使用实际发现的路径。
- `skill_paths`：`list_skills` 返回的技能入口；不能填调用方本机的 Skill 路径。

若文件仅在调用方电脑上，先上传再填写 `references`；`/Users/...`、`/home/...` 或 `C:\Users\...` 都只是本机路径，无法传递文件内容。

### 上传本机参考文件

上传需 `can_create_projects:true`。先调用 `get_reference_upload_info`，检查地址、最大文件大小和允许类型。
向其返回的 `/mcp/references/upload` 发出携带相同 Bearer 的 HTTP POST：
`filename` 与 `request_id` 放查询参数，正文是原始文件字节，不是 JSON 或 multipart。
当前 ZIP 上限 64 MiB，UTF-8 文本 2 MiB，PNG/JPEG/WebP/GIF 图片 10 MiB，
每客户端已提交文件合计 256 MiB；具体后缀及限制以该工具返回值为准。

下面 Python 示例可在三种操作系统执行，只打印上传结果。保存为 `upload_game_reference.py`，
依次传入本机文件路径和凭据文件路径；修改上传标识为当前任务值，并核对大小限制。重新发送同一文件时保留相同标识；
改变文件内容或文件名时使用新标识。

```python
import http.client
import json
import shlex
import sys
from pathlib import Path
from urllib.parse import urlencode

source = Path(sys.argv[1]).expanduser()
request_id = "upload-board-001"
credential = Path(sys.argv[2]).expanduser()

# 仅解析凭据赋值，不执行文件中的 shell 内容，也不打印原文。
values = {}
for line in credential.read_text(encoding="utf-8-sig").splitlines():
    if line.strip() and not line.lstrip().startswith("#"):
        key, separator, value = line.partition("=")
        if separator and key.strip() in {"GAME_AGENT_MCP_TOKEN", "GAME_AGENT_MCP_URL"}:
            parts = shlex.split(value, comments=True)
            if len(parts) == 1:
                values[key.strip()] = parts[0]
expected = "https://pagent.ahagamecenter.com/mcp"
if values.get("GAME_AGENT_MCP_URL", "").rstrip("/") != expected:
    raise ValueError("请核对凭据文件中的服务地址")
token = values.get("GAME_AGENT_MCP_TOKEN", "")
if not token or not source.is_file():
    raise ValueError("缺少有效令牌或待上传文件")

# HTTPSConnection 不自动跟随重定向，凭据只发送给上面确认的主机。
connection = http.client.HTTPSConnection("pagent.ahagamecenter.com", timeout=180)
query = urlencode({"filename": source.name, "request_id": request_id})
with source.open("rb") as body:
    connection.request("POST", "/mcp/references/upload?" + query, body=body, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/octet-stream",
        "Content-Length": str(source.stat().st_size),
    })
response = connection.getresponse()
content = response.read()
connection.close()
if response.status != 200:
    raise RuntimeError(f"上传失败，HTTP {response.status}；检查服务或代理限制")
print(json.dumps(json.loads(content), ensure_ascii=False, indent=2))
```

macOS/Linux 调用示例：

```bash
python3 upload_game_reference.py "$HOME/Downloads/棋盘参考.png" "$HOME/.config/game-agent/client.env"
```

Windows PowerShell 调用示例：

```powershell
py -3 upload_game_reference.py "$env:USERPROFILE\Downloads\棋盘参考.png" "$env:APPDATA\game-agent\client.env"
```

上传结果中的 `reference_path` 放入 `create_project.references` 数组，多文件分别上传。
此接口与 MCP 共用身份，返回的路径不等于公共下载地址，也不会将上传文件变成可执行 Skill。
若服务仍未提供上传工具，报告服务版本缺项，不能改用无鉴权的旧 REST 接口绕过访问控制。

### 2. 创建并启动

确认完整配置中有 `production_plan.stages` 的四个阶段，并设置：

```json
{
  "autonomous": false,
  "auto_publish": true,
  "publish_slug": ""
}
```

这些字段位于 `production_plan` 内。`autonomous:false` 仍连续执行四阶段；只是遇到
缺失信息时暂停向用户提问。只有用户明确授权问题由 Agent 自行决定时才设 `true`。
自动决策不替代构建、测试与最终产物验证。

`auto_publish:true` 表示验收通过后发布可试玩网页；用户授权“制作并部署”已包含此操作。
`publish_slug` 留空使用独立项目 ID，也可使用确认的 3–64 位小写字母、数字、连字符路径名，
首尾不能是连字符。先把需求、模型、美术与发布配置整理完整；用户已有明确授权时直接执行，
不要因为工具叫 `start_pipeline` 再加一次确认流程。

调用 `create_project` 并从返回 `id` 保存 `project_id`，然后调用 `start_pipeline`：

```json
{
  "project_id": "替换为真实项目ID",
  "request_id": "start-amber-001"
}
```

创建只保存项目，启动才开始调用模型。所有示例标识只供说明，真实新操作生成新 UUID 等标识；
允许字母、数字和 `_ . : -`，最长 128 位。保存完整创建参数、每次操作标识和返回 ID，
让新会话或断线后能继续原任务。

### 3. 查看进度并转交待答问题

这里使用 MCP 工具返回的业务状态和问题 ID，不要求客户端实现专用弹窗或 MCP Elicitation。
调用方 Agent 可以在自身对话中向用户提问，再调用 `answer_questions`；用户也可以在服务网页回答。

定期 `get_project(project_id)`，从 `pipeline.current_stage`、`pipeline.run_id` 找当前阶段。
启动瞬间运行标识可能还没有写入，稍后再查，不要另起一份阶段任务。

调用 `get_run(run_id)`，按 `poll_after_seconds` 建议间隔查询；需要细节时
`get_run_events(run_id,after,limit)` 增量读取。阶段结束会切换到新的 `run_id`，
因此不要只轮询第一次运行直到永远。用运行返回的 `model_provider`、`model_id`
核对这一次确实采用 `api-key` 和 `gpt-6.1-sol`。

| 状态 | 含义与后续操作 |
| --- | --- |
| `queued` / `running` | 后台执行中，继续查询 |
| `awaiting_input` | 查看问题并补充答案，未回答前不反复轮询消耗资源 |
| `awaiting_confirmation` | 真实阶段产物待验收，全流程会自动校验并衔接；手动模式需要 `confirm_stage` |
| `completed` | 当前阶段已确认，全流程结束以 `get_project.pipeline.status` 为准 |
| `failed` | 查看错误与事件，修复原因后恢复 |
| `cancelled` | 已取消，不能当作通过验收 |
| `interrupted` | 服务中断留下的运行，需要显式恢复 |

`awaiting_input` 时 `get_run.requires_input` 为真，`interrupts` 的每项包含：

```text
id                    当前待答问题的原始标识
value.kind            问题类型
value.question        需要补充或确认的具体内容
value.context         提问背景
value.options         可选答案（可能为空）
```

将问题和必要背景交给用户，不展示为“执行失败”。用户此前已经明确的信息可以直接引用；
尚无授权的偏好不能替用户编造。`get_run` 最多返回前 20 项，若
`has_more_interrupts:true`，使用 `get_pending_questions` 的 `offset`、`limit` 取全，
依据 `next_offset` / `has_more` 翻页。收齐当前全部答案后调用 `answer_questions`：

```json
{
  "run_id": "替换为当前等待输入的运行ID",
  "request_id": "answer-amber-001",
  "answers": {
    "替换为真实interrupt.id": "采用已确认的原游戏棋盘布局，仅替换目标贴图，保留棋子移动和掷骰动画。"
  }
}
```

`answers` 的键必须是当前全部待答项的原始 `id`，每个值是非空字符串、最多 12000 字。
有多个问题就全部提交，不能用自编的 `question_1` 或问题标题作键。
先检查用户是否已在网页作答；状态已变化时刷新后继续，不提交旧问题的新答案。

服务端会用 `Command(resume=...)` 恢复原 DeepAgents 检查点，保持同一 `run_id`，
随后继续全流程。无需重新创建项目，也不要再调用 `start_stage` 或 `resume_run`。
答复超时则使用原 `request_id` 和同一份答案重试，不凭超时断言服务器未收到。

### 4. 完成、停止或恢复

`get_project.pipeline.status` 为 `completed` 后检查 `publication`。
自动发布成功时向用户返回实际 `publication.url`；若是相对路径，用
`https://pagent.ahagamecenter.com` 补全，并测试是否能打开。
这是本服务 `/games/<slug>/index.html` 下的试玩网页，不表示发布到应用商店。
`auto_publish:false` 时流程完成不会有自动发布结果；用户授权发布后可调用：

```json
{
  "project_id": "替换为真实项目ID",
  "slug": "amber-caravan-new",
  "request_id": "publish-amber-001"
}
```

以上为 `publish_project`。发布会核对最终源码、资源、测试与构建证据，不绕过验收；
不覆盖其他项目使用的路径。没有发布结果时不能仅根据约定路径猜出一个链接声称成功。

用户要停止时用 `cancel_pipeline(project_id,request_id)`，包括正在等待用户回答的情况。
用户要继续已经失败、取消或中断的流程时用 `resume_pipeline(project_id,request_id)`；
等待回答则用 `answer_questions`。断线、关闭调用方客户端 或关闭外层任务不会自动停止服务端执行。
恢复保留原模型来源和检查点，客户端不要创建替代运行掩盖失败。

### 按需执行：指定阶段与 Skill

用户只需某一阶段时，创建或读取未被全流程占用的项目，再调用 `start_stage`。
必填 `project_id`、`stage`、`request_id`；可传 `prompt`、`skill_mode`、`skill_paths`、
`excluded_skill_paths`，以及显式模型选择。省略模型字段时继承项目设置。

待答问题仍通过 `answer_questions` 处理。到 `awaiting_confirmation` 后读取产物，
按用户已有授权调用 `confirm_stage(project_id,stage,run_id,request_id,note)`；
它确认当前这一次运行并验证证据。下游启动前所有上游须已确认，重跑上游会使下游确认失效。
手动运行用 `cancel_run` / `resume_run` 取消和恢复，不要与全流程启停混用。

先用 `list_skills` 获取真实路径，再用 `preview_skill_selection` 查看适用性。`skill_mode:"manual"`
只使用显式 `skill_paths`；`auto` 表示自动选择并允许补充或排除。当前没有脱离项目阶段的通用
`run_task` / `run_skill` 工具，选择 Skill 不会自动接入其需要的外部执行器。

## 重试规则

每次业务操作保存 `request_id` 与完整参数。网络超时、重连后复用原标识和同一参数，
服务会返回原操作对应的当前结果；相同标识配不同参数会报错。
这同样适用于上传、开始／取消／恢复全流程、回答、手动确认与发布。
真正的新请求、修改后的回答、失败后再次恢复才使用新标识；不要对所有操作复用一个 ID。

服务重启后活动运行会显示 `interrupted`，需要显式恢复；待答问题仍可在网页或 MCP 中处理。
模型工具已写入的文件不会因为失败自动回滚，恢复也不是对全部外部副作用的“恰好一次”保证。

## 产物交付到调用方

用 `list_artifacts` 找到报告，再通过 `read_artifact` 分页阅读全文。二进制文件使用
返回的 `download_url` 下载，下载时附带同一 Bearer 令牌。下载程序直接从本机凭据文件
读取令牌，不把令牌放入 URL、命令参数或聊天内容。

将下载文件存入用户指定的项目目录，使用产物 ID 或经过校验的文件名，避免把服务器返回的
路径直接当作任意本机写入路径。按返回的 `sha256` 核对下载内容，向用户说明本机文件位置。
服务器绝对路径或服务器工作区不会自动同步到调用方；下载目标使用当前操作系统的本机路径。

## 附录：服务器管理员需要先完成的准备

这部分在服务器执行；没有服务器管理权限的调用方 Agent 只需向管理员报告缺项。
已有客户端凭据（包括旧 `mac-codex` 身份）时保留使用，以下用于服务维护或新客户端接入，不要重复签发覆盖。
公网是否可达、是否已经加载全流程工具，以实际协议测试为准。

1. 在 `/root/dev/game-agent/game_agent/backend` 的 Conda base 环境为新增调用方生成独立身份（示例名 `team-agent`，请按实际身份修改）：

   ```bash
   conda activate base
   cd /root/dev/game-agent/game_agent/backend
   python -m app.mcp.configure --client-id team-agent \
     --project-id '*' --allow-create \
     --public-url https://pagent.ahagamecenter.com/mcp
   ```

   此例授权可信个人客户端访问全部项目并创建项目；仅授权指定已有项目时，改用其真实
   `--project-id`，移除 `--allow-create`。不要给所有使用者复用同一身份。
2. 生成 `data/mcp/server.json` 和 `data/mcp/team-agent.env`。若已存在同名客户端，
   保留原凭据或显式管理其更新；命令不会覆盖。若已有配置的 `public_url` 不同，
   先显式更新到实际域名，并同步已有客户端地址。
3. 在现有后端启动环境设置 `GAME_MCP_CONFIG=data/mcp/server.json`，通过现有服务管理方式
   重启加载配置。先检查活动任务并安排重启，保持一个执行进程，不另起第二个共享状态的后端。
   现有入口脚本会读取 `backend/.env`，也可以在启动环境显式传入该变量。
4. 在 `pagent.ahagamecenter.com` 的实际入口确认 `/mcp/` 转发到本游戏服务的 `24681` 端口，
   保留路径和 Authorization，不要回源到其他应用的 `80` 端口。前端入口已将 `/mcp/`
   转发至同机 FastAPI `8003`。外部入口应使用 HTTPS，保留 Authorization
   并关闭响应缓冲。只有代理与后端位于同一台主机时，转发目标才用
   `http://127.0.0.1:8003`；其他机器上的代理需使用其能访问的内网地址。
   保留原站点路由，不用独立 MCP 域名的 `location / { return 404; }` 覆盖现有工作台。
   同域名使用也仍需控制现有 `/api/` 的访问权限。
5. 为 `/mcp/references/upload` 单独配置 `client_max_body_size 64m` 和上传超时，外层与内层代理都要检查；
   普通 MCP 请求的 `256k` 限制不能用于游戏参考包。上传大小以 `get_reference_upload_info`
   为准，上传与下载路由都需要保留 Authorization。
6. 通过实际 HTTPS 域名完成 MCP 初始化、工具发现和 `get_capabilities` 验证。
   在服务器本地测试成功，不等于从调用方环境已经可达。
7. 将新签发的 `team-agent.env` 私下交给对应使用者，保存到调用方的建议位置（可命名为 `client.env`），同时提供本文。
   不要发送 `server.json` 替代客户端凭据，也不要传送服务器 Codex 的登录文件。

服务器通用部署细节见同目录 `MCP.md`；本文的通用接入步骤可独立阅读，无需访问服务器源码。
