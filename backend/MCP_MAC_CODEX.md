# 发给 Mac 上 Codex 的游戏研发 MCP 接入与使用说明

本文可以整份交给另一台 Mac 上的 Codex 执行。它包含本地配置要求、验证标准、工具说明和调用流程。
本文不包含访问令牌；服务器管理员需另行提供 Mac 专用的客户端凭据文件。

## 给接收本说明的 Codex

请在当前 Mac 上配置并验证下述 MCP，然后按本文的工作流使用服务器上的游戏研发 Agent。
用户已授权你完成本机 MCP 配置和只读连接测试。保留已有模型、项目及其他 MCP 配置；
只增改名为 `game_agent` 的服务，不修改全局审批策略。接入验证阶段只查询能力、项目和技能，
不要为测试自动创建项目、启动阶段或调用付费模型。

固定连接参数：

| 参数 | 值 |
| --- | --- |
| MCP 配置名称 | `game_agent` |
| 对外地址 | `https://pagent.ahagamecenter.com/mcp/` |
| 传输方式 | Streamable HTTP |
| 认证 | `Authorization: Bearer <客户端令牌>` |
| 推荐凭据位置 | `~/.config/game-agent/mac-codex.env` |
| 默认 Codex 配置 | `~/.codex/config.toml`；如配置了自定义 Codex home，则使用实际配置目录 |

这是一项已经实现的远程 MCP 服务。Mac 使用自己的 Codex 登录；MCP 令牌独立签发，
不是 OpenAI API Key、ChatGPT 登录令牌或 Multica 令牌。Mac 无需安装 Multica、DeepAgents，
也无需复制服务器游戏工程。

最新部署记录（2026-10-29）：服务器已启用 MCP，并生成 `mac-codex` 专用凭据。
后端 `127.0.0.1:8003/mcp/` 与入口 `127.0.0.1:24681/mcp/` 已通过真实认证、初始化、
12 个工具发现和 `get_capabilities` 验证。公网地址修正为上表的 `pagent` 域名；从服务器
请求该域名时发生连接超时，尚未完成公网验收。请在 Mac 上重新测试，不能直接声称公网已就绪。
之前说明中的其他域名已经作废，不要继续使用旧地址。

## 自动配置步骤

按顺序执行，只有确实缺失的信息才请用户补充。

1. 确认当前是用户要配置的 Mac 和 Codex 本地主机。检查可用的 Codex 版本及 MCP 配置能力；
   若存在 `codex` 命令，可用 `codex --version`、`codex mcp add --help` 检查。桌面端没有独立 CLI
   不妨碍配置共享的 `config.toml`，不要因此安装 Multica。
2. 查找用户提供的客户端凭据文件。优先使用用户指定路径，其次使用上表的推荐路径。
   如果只有用户明确提供的 `GAME_AGENT_MCP_TOKEN` 环境变量，也可以从该变量读取。
   不搜索浏览器、钥匙串或其他应用的登录凭据；缺少 MCP 凭据时，只请求该文件的本机路径，
   不要求用户把明文令牌贴到聊天里。
3. 凭据文件来自下文的服务端配置命令，格式为两行 shell 变量赋值：

   ```dotenv
   GAME_AGENT_MCP_TOKEN=服务端生成的真实令牌
   GAME_AGENT_MCP_URL=https://pagent.ahagamecenter.com/mcp/
   ```

   示例中的中文不是可用凭据。由本地程序读取文件，按变量赋值解析，必要时使用 `shlex`
   处理引号；不要把文件当作脚本执行。检查令牌非空、URL 与固定 HTTPS 地址一致。
   文件应只有当前用户可读写，例如权限 `0600`。操作和日志都不要回显令牌。
4. 读取实际生效的 Codex 配置，修改前在同一用户私有目录保存一份权限为 `0600` 的备份。
   使用可用的 TOML 解析工具确认现有结构，仅新增或更新 `mcp_servers.game_agent`。
   不用整文件模板覆盖现有设置；重复执行应更新同一服务，不产生第二个同名 TOML 表。
5. 对本机桌面端和 CLI，优先采用下面的固定请求头配置。由本地程序把令牌填入，
   用正确的 TOML 字符串编码写入；不要把真实令牌经过聊天或命令行参数再传回文件：

   ```toml
   [mcp_servers.game_agent]
   url = "https://pagent.ahagamecenter.com/mcp/"
   enabled = true
   startup_timeout_sec = 30
   tool_timeout_sec = 60
   http_headers = { Authorization = "Bearer <由本地程序读取并填入的真实令牌>" }
   ```

   `http_headers` 的值是字面量，不会展开 `${变量名}`。配置文件也须设为 `0600`。
   更新本服务时移除其旧的 STDIO 启动参数和重复的认证来源；不要同时配置两个 Authorization。
   不要将令牌配置写入项目仓库的 `.codex/config.toml`。
6. 若用户明确只使用从同一终端启动的 Codex CLI，也可以改用环境变量：

   ```bash
   codex mcp add game_agent \
     --url https://pagent.ahagamecenter.com/mcp/ \
     --bearer-token-env-var GAME_AGENT_MCP_TOKEN
   ```

   确保该变量在 Codex 进程启动前已导出。终端中的 `export` 不会自动进入已打开的桌面进程，
   因此不要把这条 CLI 路径误当成桌面端认证已经配置成功。
7. 校验 TOML 能解析且只有一份 `game_agent` 服务。只汇报服务名称、URL、配置路径、
   是否存在认证值，不打印整个配置文件。配置管理命令成功只代表“已登记”。
8. 通过当前客户端支持的 MCP 重新连接或重启入口加载配置。若当前会话无法热加载新工具，
   明确提示用户重启 MCP 连接或客户端并开启新会话；不要强制终止用户正在进行的其他工作。
   当前服务使用固定 Bearer 令牌，不需要运行 `codex mcp login game_agent`。

上述字段以 [OpenAI 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
和 [配置字段参考](https://learn.chatgpt.com/docs/config-file/config-reference) 为依据。
若旧版客户端不认识这些设置，先确认版本支持，再使用官方支持的配置方式。

## 验证接入成功

使用 Codex 已加载的 MCP 工具或可用的 MCP 客户端，完成下列只读验证：

1. 完成 MCP 初始化并调用 `tools/list`。当前实现有 12 个工具，至少应发现
   `get_capabilities`、`list_projects`、`start_stage`、`get_run`、`read_artifact`。
2. 调用 `get_capabilities`，确认返回四个研发阶段、品类、框架、项目权限和
   `can_create_projects`。实际运行时以服务返回的能力和 Schema 为准。
3. 调用 `list_projects`，确认返回 JSON 结构的项目列表。列表为空也可以连接成功，
   不要为了证明连接正常自动创建项目。
4. 按需调用 `list_skills` 查看远程 Skill 索引；它们由服务器读取，无需在 Mac 再安装一套。

工具在客户端中的完整名称可能带服务名前缀，以实际发现的名称为准。
认证响应、HTML 页面、首页能打开、配置列表出现该服务，均不等于上述验证已经通过。

| 现象 | 处理方式 |
| --- | --- |
| `200 text/html`，返回网页或登录页 | 域名入口尚未把 `/mcp/` 送到 MCP，或被网页鉴权拦截；交由服务器管理员处理 |
| `404` | 后端未启用 MCP、运行的是旧进程，或转发路径错误 |
| `401` | 令牌缺失或无效，也可能代理未转发 Authorization；核对配置，不把它当作连通验收成功 |
| 工具报告“无权访问该项目” | 已认证，但客户端没有该项目权限；使用允许的项目或申请授权 |
| `502` / `503` | 入口无法连接后端，或后端不可用 |
| TLS / DNS / 连接超时 | 检查域名、证书和 Mac 网络；不要关闭证书验证绕过问题 |
| 配置存在但本会话无工具 | 重新加载连接或开启新会话；核对配置所在 Codex 主机及目录 |

最终向用户区分报告：“本地配置已完成”“MCP 协议验证通过”“当前会话已加载工具”。
缺少令牌或服务器尚未就绪时，报告具体缺项，不能伪造成功或自行改连 Mac 的 `127.0.0.1`。

## 工具清单

下表参数来自当前实现。调用时仍以服务器实际返回的工具 Schema 为准。

| 工具 | 必填参数 | 常用可选参数 | 用途 |
| --- | --- | --- | --- |
| `get_capabilities` | 无 | 无 | 阶段、品类、框架及当前身份权限 |
| `list_skills` | 无 | `offset=0`、`limit=20` | Skill 路径、摘要、版本哈希 |
| `list_projects` | 无 | `offset=0`、`limit=20` | 授权项目列表 |
| `create_project` | `request_id`、`name` | `brief`、`genre_id`、`framework_id`、`knowledge_paths` | 创建独立项目，需要创建权限 |
| `get_project` | `project_id` | 无 | 项目四阶段状态及当前运行标识 |
| `start_stage` | `project_id`、`stage`、`request_id` | `prompt`、`skill_paths` | 提交阶段并立即返回运行记录 |
| `get_run` | `run_id` | 无 | 状态、摘要、错误、产物数量 |
| `get_run_events` | `run_id` | `after=0`、`limit=20` | 增量事件摘要 |
| `list_artifacts` | `run_id` | `offset=0`、`limit=20` | 产物索引、哈希和下载地址 |
| `read_artifact` | `run_id`、`artifact_id` | `offset=0`、`limit=8000` | 文本正文或二进制文件下载信息 |
| `cancel_run` | `run_id` | 无 | 取消实际任务 |
| `resume_run` | `run_id`、`request_id` | 无 | 从原检查点恢复失败、取消或中断任务 |

阶段固定为 `prototype`（原型定义）、`art`（美术资源）、`code`（代码与集成）、
`test`（测试验收）。当前框架配置为 `cocos-web` 和 `canvas-web`，默认 `cocos-web`。
品类和框架是服务器的能力配置，并不代表所有玩法或平台已经过实际成品验收。

项目、Skill 和产物列表每页最多 50 项。事件使用 `next_cursor` 作为下一次 `after`；
其他列表使用 `next_offset`，依据 `has_more` 判断是否继续。文本正文按字符分页，
使用 `next_offset` 继续，每次最多 16000 字符。

## 接入后怎样执行真实任务

只有用户提出实际研发任务后再提交。先确认目标项目、阶段和需求，检查当前能力、项目状态
和所需 Skill。用户指定了已有项目就使用该项目；不要每次对话都重新创建。

需要新项目且拥有创建权限时，可调用 `create_project`，例如：

```json
{
  "request_id": "create-demo-001",
  "name": "合成玩法原型",
  "brief": "拖拽两个同级物品进行合成，先定义最小可玩范围与验收条件",
  "genre_id": "merge",
  "framework_id": "canvas-web"
}
```

从结果的 `id` 取得真实 `project_id`。实际新操作请生成新 UUID 等合法标识，不反复使用
示例的 `request_id`；允许字母、数字和 `_ . : -`，最长 128 位。

再调用 `start_stage`：

```json
{
  "project_id": "替换为真实项目ID",
  "stage": "prototype",
  "request_id": "prototype-demo-001",
  "prompt": "只完成原型定义，写明核心循环、合法合成、满盘处理、界面布局和验收条件",
  "skill_paths": []
}
```

使用 Skill 时，路径必须来自实际的 `list_skills`，不能把 Mac 本地路径传给服务器。
任务输入通过 `brief`、`prompt` 传递；当前工具没有上传 Mac 本地文件的接口，不能只在
提示中写一个本机文件路径，就假定服务器已经获得文件。

从提交结果的 `id` 取得 `run_id`，按 `poll_after_seconds` 建议间隔查询 `get_run`，
需要细节时增量读取事件。保存本次 `request_id`、`project_id`、`run_id` 和事件游标，
以便断线或新会话继续。

| 运行状态 | 含义与后续操作 |
| --- | --- |
| `queued` / `running` | 后台任务仍在执行，继续查询 |
| `awaiting_confirmation` | 真实阶段产物就绪，读取产物后请用户到工作台评审确认 |
| `completed` | 用户已确认该阶段，可按用户任务继续下一阶段 |
| `failed` | 查看错误与事件，解决原因后再明确发起恢复 |
| `cancelled` | 执行已取消，不能作为通过验收的结果 |
| `interrupted` | 服务中断留下的运行，需要显式恢复 |

当前 MCP 没有 `confirm_stage`。不要从其他接口自动绕过评审；`resume_run` 只恢复执行，
不会替代阶段确认。下游启动前，所有上游须已确认；重跑上游会使下游确认失效。

网络超时不等于远程任务失败。创建、启动操作重试时复用原 `request_id` 和参数；
真正的新操作才使用新标识。恢复操作也遵循此规则：同一次恢复的重试复用标识，
之后再次失败或中断、需要新一次恢复时换新标识。客户端关闭或断线不会自动取消远程任务，
用户要求停止时调用 `cancel_run`。

## 产物交付到 Mac

用 `list_artifacts` 找到报告，再通过 `read_artifact` 分页阅读全文。二进制文件使用
返回的 `download_url` 下载，下载时附带同一 Bearer 令牌。下载程序直接从本机凭据文件
读取令牌，不把令牌放入 URL、命令参数或聊天内容。

将下载文件存入用户指定的项目目录，使用产物 ID 或经过校验的文件名，避免把服务器返回的
路径直接当作任意本机写入路径。按返回的 `sha256` 核对下载内容，向用户说明本机文件位置。
服务器绝对路径或服务器工作区不会自动同步到 Mac。

## 附录：服务器管理员需要先完成的准备

这部分在服务器执行；没有服务器管理权限的 Mac Codex 只需向管理员报告缺项。
本次服务器本机启用和 `mac-codex` 凭据生成已完成，以下也用于后续维护或新客户端接入；
使用本次接入包时不要重复签发令牌。公网是否可达仍以实际协议测试为准。

1. 在 `/root/dev/game-agent/game_agent/backend` 的 Conda base 环境生成 Mac 专用客户端：

   ```bash
   conda activate base
   cd /root/dev/game-agent/game_agent/backend
   python -m app.mcp.configure --client-id mac-codex \
     --project-id '*' --allow-create \
     --public-url https://pagent.ahagamecenter.com/mcp
   ```

   此例授权可信个人客户端访问全部项目并创建项目；仅授权指定已有项目时，改用其真实
   `--project-id`，移除 `--allow-create`。不要给所有使用者复用同一身份。
2. 生成 `data/mcp/server.json` 和 `data/mcp/mac-codex.env`。若已存在同名客户端，
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
5. 通过实际 HTTPS 域名完成 MCP 初始化、工具发现和 `get_capabilities` 验证。
   在服务器本地测试成功，不等于从 Mac 已经可达。
6. 安全传送 `mac-codex.env` 到 Mac 的推荐位置，将本文一起交给 Mac Codex。
   不要发送 `server.json` 替代客户端凭据，也不要传送服务器 Codex 的登录文件。

服务器通用部署细节见同目录 `MCP.md`；本文的 Mac 接入步骤可独立阅读，无需访问服务器源码。
