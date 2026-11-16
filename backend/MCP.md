# 游戏研发 MCP 接入

使用 FastMCP 4.1.4，通过 Streamable HTTP 将四阶段工作流开放给可信内部客户端。
MCP 与 REST 同进程运行，共用 `workflow.engine`、JSON 运行记录、SQLite 检查点和产物快照。
没有配置 `GAME_MCP_CONFIG` 时不挂载 MCP；已有工作台保持原有访问方式。

Windows、macOS、Linux 上各类 Agent 客户端的配置和使用步骤见 [可直接转交的通用接入说明](MCP_MAC_CODEX.md)。
该文件保留历史名称，已包含 Codex、Claude Code、Cursor、VS Code 与自建 MCP 客户端示例。
本工程对外目标地址为 `https://pagent.ahagamecenter.com/mcp/`；下文的回环地址
仅用于服务器本机检查或同机代理转发。

## 本机启动与连接验证

在 `backend/` 目录操作：

```bash
conda activate base
python -m pip install -r requirements.txt

# 初次生成客户端。'*' 表示所有项目，--allow-create 另行授予创建权限。
python -m app.mcp.configure --client-id local-harness --project-id '*' --allow-create

# 单后端进程启动；不要同时启动另一个共享同一数据目录的执行器。
GAME_MCP_CONFIG=data/mcp/server.json uvicorn app.main:app --host 127.0.0.1 --port 8003
```

生成命令将服务端摘要配置写入 `data/mcp/server.json`，将客户端明文令牌写入
`data/mcp/local-harness.env`。两个文件权限均为 `0600`，目录已加入 `.gitignore`。
终端仅输出文件位置，不输出令牌。重复客户端标识或已有凭据文件会报错，不覆盖旧凭据。

在另一终端运行只读连接检查：

```bash
conda activate base
cd /root/dev/game-agent/game_agent/backend
set -a
source data/mcp/local-harness.env
set +a
python -m app.mcp.check
```

检查会完成真实 HTTP 握手、工具发现和 `get_capabilities`，不会启动模型或创建项目。
其他 Harness 填写 URL `http://127.0.0.1:8003/mcp/`，并通过它支持的密钥配置方式发送
`Authorization: Bearer <客户端令牌>`。环境变量是否自动展开取决于客户端，不能把
`${GAME_AGENT_MCP_TOKEN}` 当作所有客户端都支持的配置语法。

MCP 能连通不代表模型已就绪。实际执行依赖所选来源下的服务器 API Key 或 Codex 登录、
指定模型可用，以及项目工具环境；模型不可用时运行如实进入 `failed`，不切换身份。

`api-key` 直接使用服务器 `backend/.env` 已配置的模型凭据，所有获准调用任务的客户端共用这份配置。
调用方无需拥有、提供或在本机配置自己的模型 API Key；外部 Agent 不应向用户索要模型密钥。
MCP Bearer Token 只用于连接本服务，与模型 API Key 分开。

MCP 和网页新项目默认使用服务器 API Key：`create_project` 省略模型参数等同于
`model_provider="api-key"`、`model_id="gpt-6.1-sol"`；选择其他模型时再显式传入参数。
`start_stage` 省略模型参数会继承项目设置，也可显式指定本次运行。
新项目只有显式选择 `model_provider="codex-login"` 才使用服务器 Codex 登录。
已有项目和恢复旧运行保留原来源；重试升级前的项目创建请求时，应显式传入原模型来源，
否则同一 `request_id` 会因参数不同被拒绝，不会重复创建项目或切换原任务身份。
`get_capabilities` 默认只检查 API 配置，不发计费推理、不修改项目设置。
服务器配置与完整操作见 [API Key 全流程说明](../docs/agent-production/deepagents-api-workflow.md)。

## 远程部署

生成配置时指定实际 HTTPS 入口，例如：

```bash
python -m app.mcp.configure --client-id team-planner \
  --project-id '<已有项目ID>' --public-url https://pagent.ahagamecenter.com/mcp
```

将项目 ID 替换为实际值。一个服务端配置内所有客户端使用同一 `public_url`；
如已生成本机配置，先显式编辑 `server.json` 的 `public_url`，并同步各客户端地址。
可以重复执行命令添加不同 `client_id`，或编辑配置后重启以撤销令牌和调整项目权限。
令牌属于内部 Bearer 认证，不提供浏览器 OAuth 登录或动态客户端注册。

后端继续绑定 `127.0.0.1`，在已有 TLS 反向代理的专用虚拟主机内仅转发 `/mcp`：

下面的独立入口示例包含根路径拒绝规则。若使用现有工作台的同一个域名，
只合并 `/mcp` 两条规则，保留原站点路由，并单独检查原 `/api/` 的访问控制。
代理不在后端所在主机时，将转发目标改为代理能够访问的后端内网地址。

```nginx
# 放在已经配置证书的 HTTPS server 块内。
location = /mcp {
    return 307 /mcp/;
}

# 文件原始字节上传单独放宽限制；其余 MCP 消息保持小正文上限。
location = /mcp/references/upload {
    proxy_pass http://127.0.0.1:8003;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Authorization $http_authorization;
    proxy_buffering off;
    proxy_request_buffering off;
    proxy_cache off;
    client_max_body_size 64m;
    client_body_timeout 180s;
    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
}

location /mcp/ {
    proxy_pass http://127.0.0.1:8003;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Authorization $http_authorization;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 60s;
    client_max_body_size 256k;
}

# 专用 MCP 域名不转发旧工作台 REST 接口。
location / {
    return 404;
}
```

**MCP 鉴权只保护 `/mcp/`、参考文件上传及产物下载路由，不会给旧 `/api/` 增加登录功能。**
不要通过同一公网入口放开后端整个端口或 `/api/`，否则可以绕过 MCP 的项目限制。
现有工作台应放在可信网络或已有访问控制之后。项目白名单限制的是 MCP 调用权限，
实际执行仍是现有可信服务账户，不能当作不可信多租户进程沙箱使用。

`public_url` 是返回产物下载链接的固定地址，不会修改服务监听地址或申请 TLS 证书。
远程 URL 必须是 HTTPS，只有 localhost／回环地址允许 HTTP。

## 身份配置

`server.json` 的结构如下；摘要必须来自真实高熵随机令牌，建议通过配置命令生成：

```json
{
  "public_url": "https://pagent.ahagamecenter.com/mcp",
  "clients": [
    {
      "client_id": "team-planner",
      "token_sha256": "替换为生成命令产生的64位摘要",
      "project_ids": ["替换为已有项目ID"],
      "can_create_projects": false
    }
  ]
}
```

每次工具调用、事件读取和文件下载都会核对运行所属项目。受限客户端不能创建新项目；
创建权限要求 `project_ids: ["*"]` 且 `can_create_projects: true`。
所有已认证客户端可查看共同的模板、参考游戏、品类、框架与 Skill 索引；这些索引不是按项目隔离的知识库。
客户端上传资料按客户端身份存储，创建项目时会校验引用权限。阶段确认、补充回答、
全流程启停和发布同样受项目白名单约束；没有通过 MCP 修改服务器密钥或发布 Skill 的接口。

## 工具与调用流程

工具 Schema 以连接时的 `tools/list` 为准。下表区分全流程和兼容的手动阶段操作；
远程调用复用网页的执行器、DeepAgents 图和持久检查点，用户可以在网页查看同一个项目。

| 工具 | 用途与关键参数 |
| --- | --- |
| `get_capabilities` | 查询阶段、品类、框架、模型来源及当前令牌权限；可传 `model_provider`、`model_id` 检查选定来源 |
| `list_templates` / `get_template` | 分页列出模板；按 `template_id` 读取完整需求、模型设置和四阶段计划 |
| `list_references` | 按 `query` 检索服务器参考资料，返回可用于项目的引用路径 |
| `get_reference_upload_info` | 取得当前客户端的二进制上传地址、方法和大小等限制 |
| `list_skills` | 分页获取 Skill 路径、摘要和哈希 |
| `preview_skill_selection` | 按项目、阶段、任务及人工增减只读预览 Skill 和能力限制 |
| `list_projects` / `get_project` | 查询授权项目；项目详情包含 `production_plan` 摘要、`pipeline` 与 `publication` |
| `create_project` | 保存需求、`references`、模型设置和可选 `production_plan`，创建独立工作区；要求创建权限和 `request_id` |
| `start_pipeline` | 按已确认的完整计划连续执行四阶段；参数 `project_id`、`request_id` |
| `get_run` / `get_run_events` | 查询阶段状态、待答问题和增量活动记录 |
| `get_pending_questions` | 按 `run_id` 分页读取全部待答问题，参数 `offset`、`limit` |
| `answer_questions` | 用 `run_id`、`answers`、`request_id` 回答当前问题并恢复同一运行 |
| `cancel_pipeline` / `resume_pipeline` | 用 `project_id`、`request_id` 取消或恢复整个流程 |
| `list_artifacts` / `read_artifact` | 查询产物、读取文本或取得需要认证的下载链接 |
| `start_stage` | 手动提交一个阶段，要求 `project_id`、`stage`、`request_id` |
| `confirm_stage` | 手动阶段验收；要求 `project_id`、`stage`、`run_id`、`request_id`，可传 `note` |
| `cancel_run` / `resume_run` | 兼容手动运行的取消与检查点恢复；恢复要求 `request_id` |
| `publish_project` | 发布通过验收的构建；要求 `project_id`、`slug`、`request_id` |

### 1. 准备模板、资料与模型设置

先只读调用 `get_capabilities`、`list_templates`、`list_references`、`list_skills`。
全流程推荐 `get_template({"template_id":"web-game"})`；保留原游戏表现的 LUDO 改造
可选 `ludo-classic`，仍需先用实际模板列表核对 ID，并确认原游戏参考包在服务器存在。

从模板中只取 `name`、`brief`、`genre_id`、`framework_id`、`knowledge_paths`、
`references`、`model_provider`、`model_id`、`production_plan`，补充用户需求和新的
`request_id` 后调用 `create_project`。不要将模板顶层的 `id`、`schema_version`、
`description` 当作创建参数。`production_plan.template_id` 可以保留，顶层没有
“传一个 template_id 自动合并模板”的快捷参数；重试应使用之前保存的完整提交内容。
`get_project.production_plan` 是配置摘要，不回传完整阶段提示词；完整输入应从
`get_template` 或调用方保存的原始创建参数取得。

`brief` 既兼容文本，也接受对象。对象使用 `name`、`genre`、`platform`、`engine`、
`audience`、`cycle`、`idea`、`scope` 字段。统一美术需求写进
`production_plan.art_requirements`，各阶段提示词在 `production_plan.stages` 一次填好。
优先保留模板的交付、构建、测试与美术证据要求，只修改用户需要的范围。

输入的用途不同：

| 输入 | 内容与取得方式 |
| --- | --- |
| `references` | 参考游戏、图片、说明或素材包的服务器引用路径；从 `list_references` 或上传结果取得 |
| `knowledge_paths` | 服务器公开知识库中的有效路径；可保留模板提供的值，不能传 Mac 绝对路径 |
| `production_plan.stages.<阶段>.skill_paths` | `list_skills` 返回的真实 Skill 路径；`auto` 模式为补充，`manual` 模式只采用显式列表 |
| `model_provider` / `model_id` | 本任务模型来源与模型 ID，与 MCP 令牌分开管理 |

创建项目默认使用用户在 `backend/.env` 配置的模型，也可显式传入
`"model_provider":"api-key","model_id":"gpt-6.1-sol"`。不要把 API Key 放进 MCP
参数、需求文本或上传资料；服务器自行读取 Key。实际运行可通过 `get_run.model_provider`
和 `get_run.model_id` 核对；恢复保持原来源，不会降级切换到其他身份。

### 2. 上传调用方本地文件

调用方的 `/Users/...`、`/home/...` 或 `C:\Users\...` 路径对服务器不可见。先调用 `get_reference_upload_info`，然后用
相同 Bearer 令牌向返回的 HTTPS 上传地址发送普通 HTTP POST；这是配套的文件传输接口，
无需把二进制或 Base64 塞进模型上下文。

```text
POST https://pagent.ahagamecenter.com/mcp/references/upload?filename=<URL编码文件名>&request_id=<本次上传标识>
Authorization: Bearer <与 MCP 相同的客户端令牌>
Content-Type: application/octet-stream

<原始文件字节；不是 multipart 表单，也不是 JSON>
```

上传需创建项目权限（`can_create_projects:true`）。上传成功后，将结果中的 `reference_path` 添加到 `create_project.references`。
保存原文件、上传标识和结果；网络中断重试使用同一个标识、文件名与原始字节。
多个文件分别上传并分别记录引用。文件大小、类型等限制以 `get_reference_upload_info`
返回值为准。目前单文件总上限 64 MiB，UTF-8 文本上限 2 MiB，图片上限 10 MiB，
每客户端已提交文件总额 256 MiB；支持 ZIP、指定文本后缀和 PNG/JPEG/WebP/GIF。
ZIP 会在保存前检查条目、尺寸、压缩比例与可读性；不接受任意二进制后缀。
上传完成不代表其中所有文件都会进入模型上下文。
引用文件不会自动变成 Skill，上传压缩包也不会立即执行其中的程序。

令牌由本地程序从凭据文件读取，不写入 URL、聊天或命令行参数。若客户端有
`curl --data-binary @本机文件` 的能力，认证信息应通过权限受限的配置文件传入，
不要把真实 Bearer 放进 `curl -H` 参数。完整无明文回显示例见
[跨平台文件上传步骤](MCP_MAC_CODEX.md#上传本机参考文件)。

代理需给 `/mcp/references/upload` 单独设置满足上传限制的 `client_max_body_size`
与上传超时；上文普通 MCP 请求的 `256k` 限制不能直接用于游戏参考包。
外层 HTTPS 代理和内层转发都要允许该大小，并保留 Authorization。
`413` 表示上传大小被服务端或某一层代理拒绝，不能靠重复提交解决。

### 3. 创建并开始全流程

创建前整理好完整需求、参考资料、美术要求、模型来源和发布选项。用户已经授权
“按这个需求完成全流程并部署”时，沿用该授权，不因使用 MCP 再增加一次审批弹窗。
只有需求真的缺失或相互冲突时才补充询问。

计划要求同时包含 `prototype`、`art`、`code`、`test` 四个阶段，每阶段有非空 `prompt`。
下列字段决定执行方式，需与用户授权一致：

```json
{
  "autonomous": false,
  "auto_publish": true,
  "publish_slug": ""
}
```

这些字段放在 `production_plan` 内。`autonomous:false` 保留需要补充时暂停提问的行为；
四阶段仍会自动衔接。`autonomous:true` 是用户授权 Agent 对执行中的问题自行决策，
不是“启用自动四阶段”的开关；不要因其他 Agent 正在调用就自动打开。
`auto_publish:true` 在验收通过后发布网页构建；`publish_slug` 留空会用独立项目 ID，
也可指定 3–64 位小写字母、数字、连字符构成的独立路径名，首尾不能是连字符。

`create_project` 返回真实 `id`，记录为 `project_id`。创建只保存项目与草稿计划，
不会立即调用模型。随后调用：

```json
{
  "project_id": "替换为真实项目ID",
  "request_id": "start-project-001"
}
```

以上是 `start_pipeline` 的参数。启动后按 `get_project.pipeline.current_stage` 和
`pipeline.run_id` 定位当前阶段运行，再调用 `get_run`。启动瞬间 `run_id` 可能尚未写入，
稍后重新读取项目即可；不要因为暂时没有 `run_id` 再次创建或手动启动阶段。

### 4. 轮询与 human-in-the-loop

`get_run` 在 `queued` / `running` 时返回 `poll_after_seconds` 建议值；按此间隔查询。
用 `get_run_events` 的 `next_cursor` 作为下一次 `after` 增量取回活动记录。
全流程还需持续读 `get_project`，因为一个阶段结束后会生成下一个阶段的不同 `run_id`。

| 状态 | 外部 Agent 的处理 |
| --- | --- |
| `queued` / `running` | 后台执行中，保存标识并继续轮询 |
| `awaiting_input` | 停止空转轮询，读取待答问题，按已有授权回答或转给用户补充 |
| `awaiting_confirmation` | 阶段产物待验收；全流程由调度器校验衔接，手动阶段调用 `confirm_stage` |
| `completed` | 当前阶段已经确认；全流程是否完成以项目的 `pipeline.status` 为准 |
| `failed` / `interrupted` / `cancelled` | 查询错误、修复原因；需要继续时按归属恢复，不能当作验收通过 |

待答问题位于 `get_run.interrupts`，每项有 `id` 和
`value:{kind,question,context,options}`。`get_run` 最多带前 20 项；
`has_more_interrupts:true` 时调用 `get_pending_questions(run_id,offset,limit)`，
根据 `next_offset`、`has_more` 读取全部问题，不能漏答后续页。

用问题的原始 `id` 作为 `answers` 的键，用用户回答或其已明确授权的答案作为字符串值：

```json
{
  "run_id": "替换为当前等待输入的运行ID",
  "request_id": "answers-project-001",
  "answers": {
    "替换为第一个真实interrupt.id": "保留原棋盘和棋子造型，仅替换指定贴图，保留移动和掷骰子动画。",
    "替换为第二个真实interrupt.id": "手机与电脑都支持，单人对战三名电脑玩家。"
  }
}
```

以上调用 `answer_questions`。必须一次覆盖当前全部待答 ID，不多传、不少传；
每个答案非空且不超过 12000 字。没有第二个问题时不要携带第二项。若网页已回答，
先刷新状态，不要再次用旧 ID 提交新的回答。网络不确定时用原 `request_id` 和完整答案重试。

服务端将答案写入原 DeepAgents 检查点，通过 `Command(resume=...)` 继续同一个运行；
全流程也继续自动衔接，不需要另调 `start_stage`、`resume_run` 或重新创建项目。
浏览器和 MCP 使用同一份待答状态。`awaiting_confirmation` 是验收状态，
不能用 `answer_questions` 当作“同意通过”来替代阶段确认。

### 5. 交付、发布、取消与恢复

全流程 `pipeline.status:completed` 后检查 `get_project.publication`。
`auto_publish:true` 时使用实际返回的 `publication.url` 作为试玩地址；若返回相对路径，
用 `https://pagent.ahagamecenter.com` 补全，并从用户设备验证打开。
发布位置是本服务的 `/games/<slug>/index.html`，不是应用商店、代码仓库或其他平台。
`auto_publish:false` 的流程完成后可在用户授权发布时调用：

```json
{
  "project_id": "替换为真实项目ID",
  "slug": "my-game-demo",
  "request_id": "publish-project-001"
}
```

以上为 `publish_project` 参数。发布仍校验四阶段确认、最终源码、资源、构建与测试证据；
它不会绕过已经失效的验收，也不会覆盖其他项目占用的路径。

通过 `list_artifacts` / `read_artifact` 交付报告、素材、源码包和证据。
文本 `offset`、`next_offset` 按字符计数，一次最多 16000 字；二进制按 `download_url`
下载并核对 `sha256`。下载仍需相同 Bearer 令牌，公开试玩地址与受保护产物链接用途不同。
服务器绝对路径不是可交给 Mac 或手机访问的下载链接。

用户要求停止整个项目时调用 `cancel_pipeline(project_id,request_id)`，包括暂停等回答的流程。
修复失败原因后，使用 `resume_pipeline(project_id,request_id)`；它保留已经完成阶段，
从失败、取消或中断位置继续。等待回答时应调用 `answer_questions`，不要用恢复绕过提问。
外层客户端或 Multica 任务关闭不会自动取消服务器任务。

### 手动阶段兼容流程

未交给全流程管理的项目，仍可 `start_stage` → 轮询／回答问题 → 查看产物 →
`confirm_stage` → 下一阶段。阶段固定为 `prototype`、`art`、`code`、`test`。
`confirm_stage` 必须指向当前真正处于 `awaiting_confirmation` 的 `run_id`，
代表根据用户已有授权对这一份产物确认，不能替代测试证据。
重跑上游会使下游确认失效。

手动运行的取消和恢复用 `cancel_run`、`resume_run`；全流程管理中的阶段应操作整个流程，
不能直接混用 `start_stage` / `resume_run` 来抢占同一工作区。
`start_stage` 省略模型参数会继承项目；显式 `model_provider`、`model_id` 只选择本次运行。
`skill_mode:auto` 下 `skill_paths` 是补充，`excluded_skill_paths` 是排除项；
`manual` 只采用显式列表，空列表保持为空。

两种模式都在启动时冻结 Skill 入口、配套文本和版本。`get_run` 返回 `skill_selection`、
`skill_snapshot`、精简 `skill_reads`，可核对实际读取的哈希，但不包含技能正文。
恢复沿用原输入，不重新路由或升级版本。选中 Skill 不会自动安装其联网、图片生成、
Creator 编辑器或设备工具，需检查能力限制与服务器环境。

## 重试、恢复与单进程边界

- 创建、阶段启动、全流程控制、答复、确认、发布和上传的 `request_id` 标识一次业务操作。
  同一次操作遇到超时，复用原标识和参数；不要生成新标识来“重试”。
  新需求、修改后的回答或修复后再次恢复属于新操作，使用新标识。
- 标识允许字母、数字与 `_ . : -`，最长 128 位。标识按客户端和操作归属隔离，
  同一标识、相同参数返回原操作对应的当前结果，不同参数返回错误；普通重启后仍有效。
- 恢复同一 `run_id` 时，同一次恢复重试只增加一次 `attempt`；复用已处理标识不会发起新恢复。
  HITL 答复也须保存并复用原标识，防止网络重试被错误应用到后续新问题。
- HTTP 超时或客户端断线不终止后台执行。服务关闭会停止实际任务，重启后活动运行标为
  `interrupted`，等待回答的运行保留问题；需要恢复时显式操作，不会替用户回滚已执行命令。
- 当前是单进程 JSON 状态与 SQLite 检查点；提交去重不是多副本分布式事务，
  不保证模型工具副作用在崩溃恢复时恰好执行一次。不要设置多个 Uvicorn worker，
  或让多个后端实例共享同一数据／工作区目录。

## 代码边界与验证

| 模块 | 职责 |
| --- | --- |
| `app/mcp/auth.py` | 配置校验、令牌验证和客户端身份 |
| `app/mcp/server.py` | 工具 Schema、协议错误与受保护下载路由 |
| `app/mcp/configure.py` / `check.py` | 凭据生成与真实 HTTP 只读检查 |
| `app/services/workflow/remote.py` | 项目授权、有限结果视图与文本分页，不依赖 MCP |
| `app/services/workflow/submissions.py` | 请求指纹和持久记录查重，不执行任务 |
| `app/services/workflow/remote_actions.py` | 全流程启停、手动确认及发布的持久操作去重 |
| `app/services/workflow/reference_inputs.py` | 公共参考索引、客户端上传与引用校验 |
| `app/services/workflow/pipeline.py` | 四阶段调度、HITL 答复与原检查点恢复 |
| `app/services/workflow/engine.py` | 唯一执行器及任务状态；REST／MCP 共用提交去重 |
| `app/main.py` | 合并 MCP 生命周期与原有初始化、任务清理 |

```bash
conda activate base
python -m unittest tests.test_mcp tests.test_mcp_pipeline tests.test_mcp_human_input \
  tests.test_reference_inputs tests.test_workflow_pipeline tests.test_workflow tests.test_workflow_tools \
  tests.test_production_library tests.test_skill_library -q
```

测试使用临时目录和真实 MCP HTTP 协议，覆盖 TCP 连接、身份与项目授权、提交重试、
模板与结构化计划、上传隔离与重试、HITL 分页与答复、全流程取消恢复、手动确认与发布门禁，
以及断线重连、分页、快照篡改和文件下载。闭环测试实际执行 DeepAgents 建图、
文件工具、SQLite 检查点与归档，仅替换模型答复及登录检查，不产生真实模型费用。
这些测试不等于某个实际 Harness／Multica 部署环境已经通过验收。

实现参考：[FastMCP FastAPI 集成](https://gofastmcp.com/integrations/fastapi)、
[令牌验证](https://gofastmcp.com/servers/auth/token-verification)、
[工具定义](https://gofastmcp.com/servers/tools)。
