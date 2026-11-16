# Game Agent Backend

游戏 AI Agent 系统后端，FastAPI + Python 3.13。

## 启动

全流程模板接口已接入现有 DeepAgents 工作流：`GET /api/workflow/templates` 获取内置配置，
`POST /api/workflow/templates/validate` 校验导入；创建项目可传 `production_plan`。
网页确认创建时传 `start_immediately=true`，同一请求保存并启动，关闭页面不影响执行；
已有草稿可调用 `POST /api/workflow/projects/{id}/pipeline/start` 连续执行四阶段。
暂停提问通过 `POST /api/workflow/runs/{id}/answers` 提交 `{answers: {问题ID: 回答}}`，
调度恢复与取消分别使用同项目的 `/pipeline/resume`、`/pipeline/cancel`。
详情见 [网页模板与全流程说明](../docs/agent-production/deepagents-api-workflow.md)。

```bash
# 切换到 conda base 环境（Python 3.13）
conda activate base

# 安装依赖（首次）
cd backend
pip install -r requirements.txt

# 启动开发服务器（默认 8003 端口）
uvicorn app.main:app --reload --port 8003
```

启动后访问：
- `http://localhost:8003/` — 根路径，返回服务信息
- `http://localhost:8003/api/health` — 健康检查
- `http://localhost:8003/docs` — Swagger 自动文档

## 远程 MCP 接入

已提供 FastMCP 工具接口，复用四阶段工作流的启动、状态、取消恢复和产物校验。
按 [MCP 接入说明](MCP.md) 生成客户端凭据，并设置 `GAME_MCP_CONFIG` 后启用 `/mcp/`。
默认不开启。MCP 使用独立 Bearer 凭据，网站业务 REST 接口和 API 文档使用登录会话保护。
创建和启动接口还可传入 `request_id`，相同请求重试返回原项目／运行。

## 目录结构

```
backend/
├── app/
│   ├── main.py              FastAPI 入口
│   ├── config.py            配置（路径、CORS、API key）
│   ├── api/routes/          各模块 HTTP 路由
│   ├── models/              Pydantic schemas
│   ├── services/            业务逻辑
│   └── providers/           外部服务适配（LLM 等）
├── data/                    运行时本地状态（gitignore）
└── tests/
```

## 路由约定

所有业务路由都挂在 `/api` 前缀下：

- `/api/health`                 健康检查
- `/api/auth/*`                 登录、会话检查与退出
- `/api/workflow/*`             项目、四阶段任务、模型配置、模板与 Skill
- `/api/workflow/reference-games/*` 公司游戏参考
- `/api/knowledge/*`            知识库
- `/api/produced-games/*`       产出游戏目录、试玩与删除

网站写请求携带 `X-Requested-With: GameAgent`，登录成功后由浏览器自动携带 HttpOnly 会话 Cookie。
账号与会话存放在 `data/auth/users.sqlite`，不进入版本控制。旧版独立 Agent 路由及 Demo
生成接口已删除，全流程直接使用共享模型和生图服务，不经过旧接口转发。

## Skill 知识资料

知识库的 `skill/docs` 与美术、策划等模块同级。正常启动时会导入工程 `skills/`
中的技能包和 `ref/公司skill整合/` 中的公司包，动态发现新增入口，保留原始目录、逆向子模块、
参考文档、工具源码、样例和配置；公司说明与独立 ZIP 放在「公司资料」文件夹。
这些内容作为资料浏览和下载，导入过程不会执行技能或脚本，也不会调用外部模型。

导入文件存放在 `backend/data/knowledge/skill/docs/`，原始来源保持不变。隐藏清单
`.skill-import.json` 记录已导入路径：重复启动仅补充来源新增的文件，保留既有文件、
标题、摘要、标签和文件夹说明，并尊重用户在知识库中的删除。刷新列表不会重新导入。

来源内容有修订时，在 Skill 页检查并显式同步，或调用 `GET /api/workflow/skills/source-sync`
取得计划，再向同一路径 POST `{reason, expected_digest}`。范围为工程 `skills/` 与公司技能包及
附带文件；AHAgames 等无 Skill 入口的目录独立处理。计划列出新增、更新、一致、保持删除及冲突，
摘要绑定正文、索引和导入状态；过期或路径/同名来源冲突会拒绝整批写入。更新前在
`.skill-source-sync/{operation_id}/` 保存旧字节和元数据，操作清单记录前后哈希与理由。
本地维护用独立操作编号，不伪造游戏生产运行；运行中的技能发布仍沿用真实 `run_id`。

公司游戏资料由 `/api/workflow/reference-games` 原位只读索引 `ref/公司skill整合/AHAgames/`。
列表按实际 `gameInfo.json` 生成，包体按当前同目录 ZIP 检测，忽略历史 Windows `localFile`
和 CSV 成功字段；UTF-8 BOM 与历史清单数量差异均单独处理。详情 `/{id}` 提供来源路径和本地
素材清单，`/{id}/assets/{name}` 只服务列出的商店图片，不提供 HTML、脚本、ZIP 执行或下载接口。
新建项目使用已有 `references` 字段保存所选游戏信息与实际 ZIP 路径，不改变历史项目或运行快照。

需要手动补导时，在 `backend/` 目录运行：

```bash
python -m app.services.skill_library
# 明确恢复已删除资料时使用；仍不会覆盖现有文件或元数据
python -m app.services.skill_library --restore-deleted
```

浏览接口复用 `/api/knowledge/skill/docs/items`、`/folders`、条目详情和 `/raw`。
Skill 目录支持最多 8 层，其他模块继续最多 4 层。相关回归测试使用临时知识库：

```bash
python -m unittest tests.test_skill_library -v
```

## 四阶段真实研发工作流

`/api/workflow` 串联「原型定义 → 美术资源 → 代码与集成 → 测试验收」。运行成功先进入
`awaiting_confirmation`，用户核对真实产物后确认，下一阶段才能开始。重跑上游会使全部
下游确认失效，历史运行和产物快照保留；同一真实工作区及其父子目录同一时间只能运行一个任务。
下游启动和恢复都会比对上游已确认的报告、资源清单及明确引用资源的当前哈希与
归档快照；代码交接还会核对构建测试指纹。交接输入被外部修改后必须重跑并确认对应
上游，其他仅作为工作区观测归档的文件不会因此阻断下游。

安装及启动仍使用 conda base 的 Python 3.13：

```bash
conda activate base
cd backend
pip install -r requirements.txt
# API模式先在 backend/.env 配置 LLM_API_KEY 和 LLM_GATEWAY_URL_OPENAI。
uvicorn app.main:app --host 127.0.0.1 --port 8003
```

工作流使用官方 `deepagents.create_deep_agent`、工作区 `FilesystemBackend` 和 SQLite
检查点。网页和 MCP 新项目默认 `model_provider=api-key`，通过工程已有 LangChain provider 工厂
直接调用用户网关的 `gpt-6.1-sol`。`GET /runtime` 只检查API配置是否存在，不产生计费请求；
真实模型响应与用量保存在 `model_completed` 事件，不允许失败时切换到 Codex 身份。
OpenAI 默认使用 Responses API（`LLM_OPENAI_API=responses`），通过完整历史与加密推理内容继续执行，避免跨上游资源引用 item ID；只支持旧协议的网关可显式选择 `chat-completions`。图片服务选择 `IMAGE_PROVIDER=openai` 时可复用工程网关及 Key，默认图片模型为 `gpt-image-2`；原 Azure 配置仍保留。
配置、网页步骤和能力边界见 [API Key 全流程说明](../docs/agent-production/deepagents-api-workflow.md)。

历史项目或显式选择 `codex-login` 时，`CodexChatModel` 是 LangChain `BaseChatModel` 适配器，通过官方
`codex exec --output-schema` 使用已有 ChatGPT 登录调用 **gpt-6.1-sol**。
每次运行先通过官方 App Server `model/list` 核验模型；模型不可用会失败，不会换成其他
模型或返回模拟内容。适配器不读取登录令牌、不调用私有接口、不修改全局 Codex 配置。

Codex 在独立只读临时目录中只产生结构化推理结果；实际文件操作、参考读取、Skill
读取和验证命令由 DeepAgents 工具执行。工具参数错误作为错误消息交回模型纠正，
模型调用失败则如实记录失败。取消会结束实际进程组；恢复继续使用原运行检查点。
每次创建图都把当前 attempt 和恢复标记写进系统提示；挂起工具继续使用原消息顺序，
代码及测试恢复后仍须在新 attempt 重做构建、测试和任务明确要求的其他验证。
单次图执行保留 150 步上限，超过后记录失败并允许基于检查点恢复。
每次运行的文件读写、目录检索和验证共用异步锁，避免模型并发编辑同一文件导致内容
覆盖或读取半写入文件；同一文件的连续编辑仍要求模型按最新内容串行安排。

主要接口如下，完整结构见 FastAPI `/docs`：

| 接口 | 用途 |
| --- | --- |
| `GET /api/workflow/runtime` | 按 provider/model_id 检查配置；API模式不发计费请求 |
| `GET /api/workflow/skills` | 动态读取技能知识库入口及哈希 |
| `GET/POST /api/workflow/skills/source-sync` | 检查来源变化；携带计划摘要显式同步并备份 |
| `GET /api/workflow/reference-games` | 本地公司游戏参考目录及实际资源统计 |
| `GET /api/workflow/reference-games/{id}` | 单个游戏的说明、路径与资源状态 |
| `GET /api/workflow/reference-games/{id}/assets/{name}` | 白名单商店图片 |
| `GET /api/workflow/catalog` | 游戏品类、技术框架及可选知识资料索引 |
| `GET/POST /api/workflow/projects` | 列出或创建项目；brief 支持字符串及对象 |
| `GET /api/workflow/projects/{id}` | 四阶段状态和已存在构建的预览地址 |
| `POST /api/workflow/projects/{id}/runs` | `{stage,prompt,skill_paths}` 启动指定阶段 |
| `POST /api/workflow/projects/{id}/skill-selection` | 只读预览阶段技能选择、理由与能力限制 |
| `GET /api/workflow/projects/{id}/runs` | 项目运行历史 |
| `GET /api/workflow/runs/{id}` | 持久运行状态、事件、产物及错误 |
| `GET /api/workflow/runs/{id}/events?after=0` | 按序号增量读取事件 |
| `POST /api/workflow/runs/{id}/cancel` | 终止当前运行及其子进程 |
| `POST /api/workflow/runs/{id}/resume` | 恢复失败、取消或服务中断的原运行 |
| `POST /api/workflow/projects/{id}/stages/{stage}/confirm` | `{note}` 确认真实产物 |
| `POST /api/workflow/projects/{id}/publish` | `{slug}` 发布已确认且与浏览器验收字节一致的构建 |
| `GET /api/workflow/artifacts/{run_id}/{artifact_id}` | 校验快照哈希后读取产物 |
| `POST /api/workflow/skills/publish` | `{path,reason,run_id}` 显式发布指定源文件修订 |

阶段 key 为 `prototype`、`art`、`code`、`test`。不指定 workspace 时自动分配
`games/{project_id}`。新项目不自动携带任何参考工程；参考路径既可写 `examples/guide.md`，
也可写 `ref/examples/guide.md`，保存时统一为相对 `ref/` 的路径。
路径必须位于工程 `games/` 的独立目录；参考工具只能读取 `ref/`，Skill 工具只能
读取已归档包的入口和配套文本。美术阶段必须提交真实文件哈希、用途及来源清单，
代码和测试阶段必须有本次框架配置要求的全部验证成功事件，不能靠模型自述通过。
验证事件绑定源码、资源、引擎和测试脚本指纹，阶段结束和人工确认都会再次核对最终
文件；验证后再改代码必须重验，恢复尝试也必须重新执行构建和测试。

创建项目可提交 `genre_id`、`framework_id` 和 `knowledge_paths`。默认使用 `general`
和 `cocos-web`；可执行框架以 `/catalog` 返回值为准，目前提供 Cocos Web、Canvas 2D
Web 与原生 DOM/SVG/Canvas Web 配置，均要求 `npm run build`、`npm test`、`npm run check`。新增配置表示
执行协议已接入，不等于已有完整项目或其他平台验收；Unity、Godot、原生平台未在此处开放。
品类决定规则与验收重点，框架决定技术约束，两者共用同一四阶段流程。

启动和技能预览均接受 `skill_mode`（默认 `auto`）、`skill_paths`、`excluded_skill_paths`。
自动模式为后端推荐加人工补充、再扣除排除项；`skill_paths: []` 仍保留自动推荐。
需要完全手选时显式传 `skill_mode: "manual"`，此时空列表就是不选择 Skill。
阶段、任务、模式或增减项变化都参与幂等请求摘要；同一请求重试返回原运行和原快照，
不因规则或知识库更新重新执行。预览没有写入，启动时重新计算；前端不是规则真源。

运行保存 `skill_selection` 的理由与限制、`skill_snapshot` 的入口元数据与哈希，
以及 `skill_resources` 的同包文本索引。选择结果中的 `resource_paths` 提示本阶段优先参考：
H5 换皮从原型方向选择进入；已有 H5 的还原与包体、加载优化按适用阶段承接，不重新采集。
正文放在 `data/workflow/inputs/{run_id}/skills/`，
不加入游戏工作区，也不整包注入模型上下文；入口由 `read_skill` 完整读取，支持文本由
`read_skill_resource` 按需读取。单文件上限 2 MB、总文本上限 16 MB；隐藏、链接、图片、
压缩包及大文件不进入文本快照。未选入口不能借资源工具绕过选择。
结束与确认均核对实际 `skill_read` 的冻结哈希、完整范围及归档完整性。
恢复不重选、不重建快照，源文件之后修改或删除不改变本轮输入；没有快照的历史运行
保持旧读取协议，不把历史记录说成已冻结。Skill 发布只影响后续新运行。

当前四阶段工具支持文件操作、本地参考与 ZIP 素材提取、品类/技术/技能读取、资源清点和项目验证。
美术阶段的 `generate_art_image` 已绑定工程图片 API，可生成图片，或传入最多 4 张工作区真实参考图
进行编辑；参考图按真实 PNG/JPEG/WebP 编码校验，并据此设置上传文件名和 MIME，兼容以 `.png`
命名的 WebP 原素材。`process_art_image` 支持明确矩形裁切，以及等比居中到指定尺寸的透明画布，
无损输出 PNG/WebP，记录输入输出 SHA256、实际尺寸和 alpha 统计；不自动抠底、拉伸或覆盖已有候选。
工作区图片可通过 `read_file` 交给所选模型理解，不代表接入了独立视觉服务。联网采集、Creator MCP
和 ADB 仍未接入；Skill 中的外部工具须以当前运行实际暴露的能力为准。

`genre/docs` 和 `framework/docs` 保存可浏览的品类、技术资料；固定资料与手选资料合并后
写入项目。运行开始时将配置、知识正文及 SHA256 冻结到 `production_profile` 与
`knowledge_snapshot`。提示仅注入所选资料索引，Agent 必须通过 `read_game_knowledge`
实际读取正文，事件记录路径、哈希与读取范围，未读取全部选定资料不能进入确认。
恢复使用原快照，不受后续知识库编辑或目录配置更新影响。已有项目和运行缺少这些字段时
维持原契约，不补加知识读取要求；旧代码/测试运行仍要求构建和单测两条验证。

美术清点支持图像、音频、字体、模型和动画。程序化视觉也可以交接：在
`workflow/art-manifest.json` 设置 `mode: "procedural"`，`assets` 列出实际设计或生成文件，
每项仍须包含 `path`、`sha256`、`usage`、`source`；空清单和空文件不能通过。可给
`inspect_assets` 传入这些文件的 `paths` 取得哈希，随后在代码和测试阶段验证实际集成与呈现。
新项目预览入口由框架配置中的受限工作区相对路径确定；旧项目保持 `dist/index.html`
与根目录 `index.html` 的原有回退逻辑。

验证工具只接受固定命令形态：`npm run build`、`npm run test`、`npm run check`、
`npm test`、`node --test ...` 和 `node scripts/...`，不经过 shell 拼接。
它会实际执行当前工作区的项目脚本；**这是可信本机工程的单用户执行环境，并非进程隔离
沙箱或可直接公网开放的多租户服务**。当前没有账号鉴权；不要把接口直接公开给不可信
调用方。文件路径检查不替代操作系统级隔离，npm/Node 项目脚本仍具备服务账户权限。

运行数据目录：

```text
backend/data/workflow/projects/         项目状态
backend/data/workflow/runs/             运行、事件和验证记录
backend/data/workflow/checkpoints.sqlite  LangGraph 持久检查点
backend/data/workflow/artifacts/{run_id}/ 产物不可变快照与哈希
backend/data/workflow/inputs/{run_id}/skills/ 本次入口与配套文本的冻结输入
backend/data/knowledge/skill/docs/.skill-revisions/  指定技能修订的前后版本
backend/data/knowledge/skill/docs/.skill-source-sync/  来源同步操作、旧字节与索引备份
games/{workspace}/workflow/             阶段报告与美术清单
```

当前使用单服务进程和进程内锁，启动时将遗留运行标记为 `interrupted`，由恢复接口
继续执行；不要配置多个 Uvicorn worker。恢复不会回滚已落盘操作，模型会基于检查点
与现有文件继续。普通产物快照忽略依赖目录、构建缓存及大于 5MB 的单文件；美术清单
明确交接的资源始终保留完整快照。游戏完整构建
从项目预览地址提供，不把整个引擎依赖归档为阶段产物。

Skill 的普通导入仍只补缺。明确的技能修订通过 `save_skill` 或发布接口更新工程源及
指定知识库副本，保留知识库标题、标签、摘要；前后正文、理由、验证和关联 run 均保留。
`publish` 支持 `SKILL.md` 及同包 references 文件，不会全量覆盖知识库。

工作流后端按职责组织在 `app/services/workflow/`：

| 文件 | 职责 |
| --- | --- |
| `engine.py` | 项目与运行状态、阶段调度、DeepAgents 执行编排和产物归档 |
| `tools.py` | 每次运行的工具创建、文件操作串行化及工具错误处理 |
| `workspace.py` | 授权路径检查、文件快照和源码指纹 |
| `validation.py` | 阶段验收、资料读取覆盖、资源清单和写入证据校验 |
| `prompts.py` | 系统提示词与当前运行的用户上下文 |
| `codex_model.py` | 登录模型适配与进程管理 |

工具所需的目录、运行记录和事件回调由 `engine.py` 显式传入；辅助模块不反向导入
调度模块。原有 `engine` 调用入口保留，路由无需改动。

已执行的回归命令（临时目录隔离，无测试替身进入生产执行）：

```bash
conda activate base
cd backend
python -m unittest tests.test_workflow tests.test_workflow_tools tests.test_production_library tests.test_skill_library tests.test_reference_games tests.test_skill_routing tests.test_skill_inputs tests.test_skill_execution tests.test_mcp -q
```

已完成真实登录模型和 DeepAgents `write_file → read_file → 最终回复` 冒烟验证。
四阶段实际运行的模型、工具、构建和产物证据写入每个 run 的事件，单元测试结果不作为
游戏生产阶段验收结果。

每项产物带 `provenance`：`agent_edit` 表示本次 DeepAgents 文件工具实际写入，
`generated_asset` 表示工程图片 API 生成或参考图编辑，`processed_asset` 表示图片确定性裁切与等比装配；
生成和处理来源仅在归档字节与对应 `image_generated` / `image_processed` 事件的 SHA256 一致时成立。
`reference_asset` 表示提取的参考素材或美术清单明确引用的资源，`validation_output` 表示验证命令
执行期间观察到的文件变化，`workspace_observation` 表示其他工作区变化。最后两类不是文件作者证明，
已有素材的裁切也不冒充 AI 生图；并行制作工具产生的变化不能归为本次模型生成。
