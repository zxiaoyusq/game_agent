# 游戏研发 MCP 接入

使用 FastMCP 4.1.4，通过 Streamable HTTP 将四阶段工作流开放给可信内部客户端。
MCP 与 REST 同进程运行，共用 `workflow.engine`、JSON 运行记录、SQLite 检查点和产物快照。
没有配置 `GAME_MCP_CONFIG` 时不挂载 MCP；已有工作台保持原有访问方式。

另一台 Mac 上 Codex 的配置和使用步骤见 [可直接转交的 Mac 接入说明](MCP_MAC_CODEX.md)。
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

MCP 能连通不代表模型已就绪。实际执行仍依赖服务器已有 Codex 登录、指定模型可用，
以及项目选定的工具和运行环境；模型不可用时运行如实进入 `failed`。

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

**MCP 鉴权只保护 `/mcp/` 及其产物下载路由，不会给旧 `/api/` 增加登录功能。**
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
所有已认证客户端可查看共同的品类、框架与 Skill 索引；这些索引不是按项目隔离的知识库。
没有 `confirm_stage` 或发布 Skill 的 MCP 工具，阶段确认继续由用户在工作台完成。

## 工具与调用流程

| 工具 | 用途 |
| --- | --- |
| `get_capabilities` | 阶段、品类、框架及当前令牌权限 |
| `list_skills` | 分页获取 Skill 路径、摘要和哈希 |
| `list_projects` / `get_project` | 授权项目和阶段状态 |
| `create_project` | 自动分配独立工作区，要求创建权限与 `request_id` |
| `start_stage` | 提交阶段并返回 `run_id`，要求 `request_id` |
| `get_run` | 有限长度的状态、摘要、错误及产物数量 |
| `get_run_events` | 用 `after` / `next_cursor` 增量读取事件摘要 |
| `list_artifacts` | 分页读取产物索引、来源、哈希和认证下载链接 |
| `read_artifact` | 校验产物并按字符读取文本；二进制文件返回下载链接 |
| `cancel_run` | 取消实际任务；重复调用返回当前状态 |
| `resume_run` | 从原检查点恢复失败、取消或中断任务，要求新的 `request_id` |

示例工具参数：

```json
{
  "project_id": "已有项目ID",
  "stage": "prototype",
  "request_id": "prototype-request-001",
  "prompt": "定义首版玩法、规则状态和验收条件",
  "skill_paths": []
}
```

1. 用 `get_capabilities`、`get_project` 和 `list_skills` 确认上下文。
2. 调用 `start_stage`，记录返回的 `id`，后续作为 `run_id`。
3. 按 `poll_after_seconds` 建议间隔调用 `get_run`；事件列表最多每页 50 项。
4. 用 `list_artifacts` 和 `read_artifact` 取回实际产物。文本 `offset`、`next_offset`
   均按字符计数，一次最多 16000 字符；图片、构建包等通过下载地址获取。
5. `awaiting_confirmation` 表示执行产物就绪、等待人工确认；`completed` 才代表确认完成。
   用户在工作台确认后，再提交下一阶段。失败或取消不代表产物通过验收。

文件下载须携带相同 Bearer 令牌，不能只把链接交给不带凭据的读取器。
下载会重新核对文件哈希，始终使用附件响应；HTML／SVG 等不会在服务自身源下直接执行。
外层客户端或 Multica 任务被关闭不会自动取消内部运行，取消须调用 `cancel_run`。

## 重试、恢复与单进程边界

- 创建与启动：请求标识按调用方和操作类型去重；同一标识、相同参数返回原记录，
  不同参数返回工具错误。标识随项目／运行原子写入，普通重启后仍有效。
- 恢复：同一 `run_id` 下的同一恢复标识只增加一次 `attempt`。再次失败或重启后需要
  真正发起新恢复时，应使用新标识；复用旧标识只查询那次操作的当前结果。
- HTTP 请求超时或客户端重连不终止后台执行。不要通过换一个请求标识来“重试”提交。
- 服务关闭会停止实际任务，启动后将遗留活动运行标为 `interrupted`，需要显式恢复。
  不会自动重试模型调用，也不会回滚已经写入的文件或已执行命令。
- 当前为单进程 JSON 状态与 SQLite 检查点。提交去重不是多副本分布式事务，
  也不保证模型工具副作用在崩溃恢复时恰好执行一次。不要设置多个 Uvicorn worker，
  或让多个后端实例共享同一数据／工作区目录。

## 代码边界与验证

| 模块 | 职责 |
| --- | --- |
| `app/mcp/auth.py` | 配置校验、令牌验证和客户端身份 |
| `app/mcp/server.py` | 工具 Schema、协议错误与受保护下载路由 |
| `app/mcp/configure.py` / `check.py` | 凭据生成与真实 HTTP 只读检查 |
| `app/services/workflow/remote.py` | 项目授权、有限结果视图与文本分页，不依赖 MCP |
| `app/services/workflow/submissions.py` | 请求指纹和持久记录查重，不执行任务 |
| `app/services/workflow/engine.py` | 唯一执行器及任务状态；REST／MCP 共用提交去重 |
| `app/main.py` | 合并 MCP 生命周期与原有初始化、任务清理 |

```bash
conda activate base
python -m unittest tests.test_mcp tests.test_workflow tests.test_workflow_tools \
  tests.test_production_library tests.test_skill_library -q
```

测试使用临时目录和真实 MCP HTTP 协议，覆盖 TCP 连接、身份与项目授权、提交重试、
断线重连、取消恢复、分页、快照篡改和文件下载。闭环测试实际执行 DeepAgents 建图、
文件工具、SQLite 检查点与归档，仅替换模型答复及登录检查，不产生真实模型费用。
这些测试不等于某个实际 Harness／Multica 部署环境已经通过验收。

实现参考：[FastMCP FastAPI 集成](https://gofastmcp.com/integrations/fastapi)、
[令牌验证](https://gofastmcp.com/servers/auth/token-verification)、
[工具定义](https://gofastmcp.com/servers/tools)。
