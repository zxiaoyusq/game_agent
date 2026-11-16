# 用工程 API Key 完成游戏生产与发布

## 当前边界与结论

沿用现有 `deepagents.create_deep_agent`、四阶段状态机、工作区文件工具和 SQLite 检查点，无须另建一套 DeepAgent。新增的 API 模式由工程 `LLM_API_KEY` 通过 LangChain 原生模型客户端发出请求，不调用 Codex CLI、不读取 Codex 登录凭据，也不会在失败时回退到 Codex。

复用 `casual-game-production` Skill，补充 ZIP 研究工具用法；棋盘规则放在新 `board-games` 品类知识中，DOM/SVG/Canvas 的交付约定放在 `native-web` 技术知识中。没有为单个游戏新建 Skill。

2026-11-04 已用用户在 `backend/.env` 配置的 API Key 完成《琥珀商路》的原型、美术、代码、独立测试四阶段，并完成评审和发布。四阶段服务端实际记录的来源均为 `api-key`，请求模型和网关返回模型均为 `gpt-6.1-sol`；游戏背景由同一工程配置的 `gpt-image-2` 图片 API 生成。本项目没有使用 Codex 登录推理，没有在 API 出错时切换来源。原有公开游戏不作为本轮 API 成功证据。

**本轮试玩链接：[《琥珀商路》API 版本](https://pagent.ahagamecenter.com/games/amber-caravan-api/index.html)。** 支持经典/快速模式、2—4 席同屏或人机对局、中文规则与刷新继续。首次试玩可选「快速」→「人机对局」→「掷骰启程」；掷骰后点击可走的编号棋子。

工作台中的项目为 **「琥珀商路 · API 全流程验证」**，ID 为 `4a33b4b07d1f4fcc874ad80aa1b6a876`，工作区为 `games/amber-caravan-api`。项目已选择 API Key / `gpt-6.1-sol`、两款参考游戏的资料及 ZIP、棋盘品类和原生 Web 方案；打开即可查看 **4 / 4 已确认**、完整运行记录、产物及已发布地址，无须重新执行。若要制作另一款游戏，请创建新的项目和工作目录。

## 服务器一次性配置

编辑工程的 `backend/.env`，保留已有 MCP 配置。只在服务器文件中填写真实值，不粘贴到游戏需求、运行提示或网页聊天：

```dotenv
LLM_API_KEY=你的网关密钥
LLM_GATEWAY_URL_OPENAI=https://你的网关域名/v1
GAME_PUBLIC_BASE_URL=https://pagent.ahagamecenter.com
```

网关地址应为该供应商文档中的 OpenAI 兼容 API 基址，不是管理后台地址，也不是 `/chat/completions` 完整路径。`LLM_GATEWAY_URL_OPENAI` 优先于通用的 `LLM_GATEWAY_URL`。本次网关要求 `gpt-6.1-sol` 的推理和工具调用使用 Responses API，工程默认 `LLM_OPENAI_API=responses`；只兼容旧协议的网关可设为 `chat-completions`。Responses请求使用完整历史和加密推理内容重放，不引用不同上游资源的 item ID。页面显示“已配置”只证明字段存在，真实成功以运行事件为准。

`gemini-3.8-flash` 使用同一网关的 OpenAI 兼容 Chat Completions 接口，模型配置会单独覆盖协议，
不影响 GPT 的 Responses 设置。网页和 MCP 中的 `claude-opus-5-5` 对应网关实际注册的
`claude-opus-5-5-20260820`；配置状态的 `upstream_model` 会返回实际请求名称。

本次网关已列出 `gpt-image-2`，通过以下设置可复用同一工程Key与OpenAI API基址，让美术阶段生成真实位图：

```dotenv
IMAGE_PROVIDER=openai
IMAGE_MODEL=gpt-image-2
```

图片服务需要单独地址或密钥时可设置 `IMAGE_API_BASE_URL` / `IMAGE_API_KEY`。也保留原 Azure 服务配置：

```dotenv
AZURE_IMAGE_ENDPOINT=https://你的资源域名.openai.azure.com
AZURE_IMAGE_API_KEY=图片服务密钥
AZURE_IMAGE_DEPLOYMENT=你的图片模型部署名称
AZURE_IMAGE_API_VERSION=该部署支持的版本
```

Azure 服务的密钥与 LLM 网关独立；OpenAI图片服务仅在显式选择 `IMAGE_PROVIDER=openai` 时复用工程Key。`generate_art_image` 只在美术阶段调用工程图片服务，返回真实图片、尺寸和 SHA256；没配置时页面明确显示“未配置”，不能声称完成 AI 生图。

修改 `.env` 后，等当前工作流任务结束，再重启本工程后端进程使配置生效。使用项目启动脚本时应重启本项目的 `domain` 进程组；不要停止同机其他应用或用 80 端口服务替代本项目。常规启动入口为工程根目录的 `bash start.sh domain`。Python 依赖使用 Conda `base`，浏览器测试依赖为 Playwright 1.63.0；服务器需有对应 Chromium。

## 网页操作

1. 打开 <https://pagent.ahagamecenter.com/>，进入首页的「全流程工作台」。该工程目前通过页面内导航切换，不能把 `/workflow` 当作独立路由。
2. 创建新项目，模型来源可选择「Codex CLI（服务器登录）」或「API Key 网关」。API 模型下拉提供 `gpt-6.1-sol`、`claude-opus-5-5`、`deepseek-v4-pro`、`deepseek-v4.1-flash`、`gemini-3.8-flash`；默认选择 `gpt-6.1-sol`。Codex CLI 目前适配 `gpt-6.1-sol`，来源互不回退。
3. 品类选「棋盘与回合制」，技术方案选「原生 Web · DOM / SVG / Canvas」。工作区留空由后端创建独立目录；继续现有验证时直接打开已准备的项目，不要另建同工作区项目，也不要指向原来的 `games/amber-caravan`。
4. 在公司游戏参考里搜索并加入 **Just Ludo** 和 **Ludo Superstar**。选择器会同时加入 `gameInfo.json` 与实际 ZIP 路径；选中资料不表示 Agent 已经读过包内代码。
5. 填写需求并保存。保持 Skill「自动推荐」，查看选中知识与原因。代码和测试阶段必须保留构建、规则测试和浏览器验收要求。
6. 依次运行「原型定义 → 美术资源 → 代码与集成 → 测试验收」。每阶段结束查看报告、真实资源与事件，再点击确认，才会开放下一阶段。失败时先看错误；同一模型继续执行用「从上次记录继续」，更换模型或输入则重新执行本阶段。
7. 测试确认后，在发布面板填独立名称，例如 `amber-caravan-api`，点击发布。成功后页面返回 `https://pagent.ahagamecenter.com/games/amber-caravan-api/index.html`。只有实际发布成功才可分享该链接；创建项目不会自动部署。

已有项目的模型选择位于「阶段执行」面板顶部；选择只应用于下一次执行。运行期间不能切换，同一运行的「继续 / 重试」保持原模型身份。要换模型，应选择新的来源和模型后点击「重新执行本阶段」，这会重新评审该阶段及下游。Codex CLI 指服务器上的 CLI 登录环境，不使用访问网页的 Mac 上的 Codex 登录；API 模式只使用服务器配置的密钥。

模型下拉当前是工程允许的列表，不是网关所有模型的自动发现。本次真正完成游戏推理的是 `gpt-6.1-sol`；Claude、DeepSeek 的下拉选择和配置读取已验证，尚未用它们重复这套游戏生产任务。配置就绪也不等于模型请求已成功，须查看本次运行事件。

可复制的项目需求：

```text
研究所选 Just Ludo 与 Ludo Superstar 两个真实 ZIP 的关键规则代码，记录路径、哈希及各自取舍，制作原创《琥珀商路》棋盘游戏。
主题为摩洛哥/北非商路，手机和电脑直接在浏览器操作。保留清晰的掷骰、合法棋子选择、出发、移动、吃子、安全格、入终点、轮流行动和胜负反馈；支持人机对局及同屏多人，先在原型明确经典/快速模式和差异。
资源和代码模块化，规则引擎与界面分离，代码注释使用中文，面向玩家的界面和提示默认使用英文；其他语言须在需求中明确指定。不得直接复制旧的 amber-caravan 成品、整体照搬参考工程或伪造模型/测试记录。
使用所选 native-web 框架，运行时不依赖远程CDN，最终 dist 展开小于10MB，所有资源使用包内相对路径。
有图片服务时生成原创美术；未配置时使用明确标注的原创SVG/程序化视觉，不声称AI图片生成。
代码阶段实现 npm run build、npm test、npm run check；浏览器测试启动最终dist，覆盖桌面和手机触摸、完整核心循环、刷新恢复、错误日志和截图；真实通过后再提交验收。
测试阶段只复核最终代码并写 evidence/workflow 报告；若需改代码，返回代码阶段修复、重验和确认。通过后发布到独立 amber-caravan-api 路径，不覆盖已有公开游戏。
```

## 如何辨别实际执行

- 模型事件 `model_completed` 必须有 `provider: api-key`、请求模型、网关返回的 `response_model`、响应 ID 和实际用量（以网关返回为准）。这些字段证明调用路径；网关内部究竟如何映射模型仍由供应商决定。
- 原型阶段应出现两个 ZIP 的 `reference_archive_read`，包含真实包/条目哈希；只有列表或 `gameInfo.json` 读取不能证明源码分析。
- 文件产物区区分工具写入、图片 API 生成、引用快照和验证输出。所选 Skill/知识与实际读取记录分开展示，并固定本次正文哈希。
- 代码和测试的 `validation_completed` 应对应当前 attempt、成功退出码、最终源码指纹。`npm run check` 另外记录构建 SHA256；发布时再比较相同文件字节。
- 测试过程中修改源码、资源或脚本会使旧代码确认失效。必须返回代码阶段重验，再重新测试；不能改旧记录使发布通过。
- 发布保护已有手工部署和其他项目的路径，生成包不得超过 10MB，也不得引用缺失资源、远程 CDN 或域名根路径资源。

## 模块与接口

| 模块 | 职责 |
| --- | --- |
| `workflow/model_runtime.py` | API/Codex 显式模型来源、配置检查、真实调用事件与错误脱敏 |
| `workflow/model_messages.py` | 将工具返回图片适配为 OpenAI 合法视觉消息，保留原始检查点 |
| `workflow/reference_tools.py` | ZIP 分页索引、关键文本研究、按件提取及来源哈希 |
| `workflow/production_tools.py` | 浏览器依赖准备、工程图片生成/参考编辑、图片处理工具及来源事件 |
| `workflow/art_processing.py` | 按图片实际编码验证、精确裁切与等比透明画布装配，保留 RGBA 和输入输出哈希 |
| `workflow/publishing.py` | 已确认构建的字节验证、路径归属、发布与失败回滚 |
| 既有 `workflow/engine.py` | 四阶段状态、执行、恢复、确认和证据归档 |

`POST /api/workflow/projects` 接受 `model_provider`、`model_id`，网页新项目默认 `api-key` / `gpt-6.1-sol`。`POST /projects/{id}/runs` 可显式选择下一次执行的模型；恢复旧运行保持原来源和模型。`GET /api/workflow/runtime?provider=api-key&model_id=gpt-6.1-sol` 只检查配置，不发计费请求。`POST /api/workflow/projects/{id}/publish` 接收 `{"slug":"amber-caravan-api"}`，返回真实发布地址和哈希。

执行环境仍是可信服务器、单后端进程。文件工具有工作区边界、验证命令有固定入口，子进程不继承服务密钥变量；这些约束不等同于操作系统级沙箱。

## 本次联调修复

- 用户网关的工具调用使用 Responses API；跨上游资源重放时移除资源专属的消息块 ID，保留标准工具调用关联及加密推理内容，使用完整历史重放。
- 补齐 SOCKS 代理依赖与 OpenAI 兼容图片接口，游戏使用真实图片 API 产物；没有把 SVG 占位称作 AI 生图。
- 长代码任务实际触及原 150 步图执行上限，调整为 300 并加入回归验证。该上限计数图执行步骤，不等于 300 次模型请求；原失败运行仍留在历史中。
- 游戏复核修复观察事件泄漏状态引用、跨标签删除存档、键盘焦点和图标 ID 冲突；完成真实后台事件验收及源码 ZIP 解包重建。代码使用官方 Prettier 整理，保留规则、随机数、AI、存档、生命周期、坐标与界面的模块边界。

## 本轮验证记录

四阶段的最终确认运行如下。调用次数只统计服务端记录到的成功模型响应，不代表付费请求总数；失败、取消的代码迭代及恢复历史仍完整保留。

| 阶段 | 最终运行 ID | 成功模型响应 | 状态 |
| --- | --- | ---: | --- |
| 原型 | `a64ac4eb74664e678836b663a8059dec` | 43 | 已确认；attempt 2 |
| 美术 | `aa260a4336e14d10b9c50a9f42ae096b` | 20 | 已确认；真实图片 API 产物 |
| 代码 | `f4dcc9b6e1de48c4a30af42ff1d2be24` | 43 | 已确认；包含复核修复 |
| 测试 | `4c9cc34de72b46bdb99a3a2543e87805` | 20 | 独立重验后确认并发布 |

最终测试运行实际重新执行 `npm run build`、`npm test`、`npm run check`，全部退出 0；前后源码指纹相同，最终构建 SHA256 为 `c62159148ff53cc702d4df992ca1130e92d430c4bbdac0f59c53ae9619afd341`。核心结果：

- 25 项游戏单测；30 局规则对局及 30 局逐动作复现。
- 6 组完整 Chromium 页面对局覆盖经典/快速、2/3/4 席、鼠标/键盘/手机触摸模拟，共 905 次真人席位输入。验收实际操作菜单和棋子，没有向界面注入终局。
- 真实 `isTrusted=true` 的 hidden→visible 事件；两轮后台等待超过 2 秒，存档、随机数状态及 AI 提交不变，恢复后正常继续。
- 事件观察副本、刷新恢复、跨标签更新/删除/clear、存储 I/O 异常、键盘焦点、320px 和文字放大检查通过。
- 最终 `dist` 为 15 文件、345738 字节；源码 ZIP 实际 CRC 校验、隔离解包、重建及单测通过，重建结果与已验收构建逐字节一致。

发布使用真实网页操作完成「确认本阶段」和「发布试玩版本」，并回读发布地址及哈希。随后经本机实际网站入口取回 15 个文件，逐个 SHA256 与发布清单一致；1440px 桌面、390px 和 320px 手机模拟均完成普通掷骰/选子及刷新继续，无资源失败、控制台异常或横向溢出。原公开游戏 10 个文件、383340 字节保持与原构建一致。网页模型来源切换和 API 三种模型选择已验证；最终项目页面显示 4 个阶段完成，390px 无横向溢出或浏览器异常。

平台后端 `python -m pytest tests -q`：158 项通过、291 个子用例通过。前端构建、差异格式检查通过。平台协议回归使用内存 HTTP 替身，另有本项目的真实网关响应、工具事件和完整游戏产物证明实际 API 执行；两种证据分开记录。详见 [本轮机器记录](api-workflow-validation.json)、游戏工作区的 `workflow/test.md` 与 `evidence/test-summary.json`。

完整源码包位于服务器的 `games/amber-caravan-api/releases/amber-caravan-api-source.zip`，试玩包位于同目录的 `amber-caravan-api-dist.zip`。当前工作台可查看报告、截图和游戏预览，ZIP 保存在服务器工作目录中，尚未纳入网页产物下载列表。包内 README 是代码确认时的交接快照，最新发布状态以工作台和本说明为准。

验证边界：手机覆盖为 Chromium 触摸模拟，未验实体 iOS/Android 或 Safari，也未进行真人音频试听、主观局时/美术评价。服务器访问公网域名仍超时，外部抓取工具也无法打开；因此只将本机实际网站入口的文件与浏览器检查记为部署验证，不声称已经在外部手机网络复验。首次原型网关错误、代码图执行上限和一次慢模型响应均有历史记录；最终成功不意味着过程中没有调试或重试。

## 模板导入与一次确认全流程（2026-11-09）

新项目默认采用连续执行：在首页进入「全流程工作台」，点击「创建新项目」，选择「LUDO · 原版贴图与动画」后点击「一键填入模板」。模板会填入简报、两款原游戏参考路径、API Key / `gpt-6.1-sol`、Canvas 2D 方案、统一美术与动画要求，以及四阶段提示词和 Skill。无需到各阶段重复输入。也可选择通用 H5 模板，或导入此前导出的 JSON 模板。

创建时检查以下内容：

1. 修改项目名称、核心想法与首版范围；美术要求统一写在「美术需求与修改范围」，美术输入通过参考资料路径或公司游戏选择器添加。
2. 在高级配置中可调整各阶段预置提示词与 Skill。LUDO 模板已配置原版换皮和美术技能，无需额外逐阶段选择。
3. 检查模型来源、技术方案和「测试通过后自动发布独立试玩链接」。发布路径留空会生成独立地址；工作目录留空也会分配独立目录，模板不会复制或覆盖现有 LUDO 项目。
4. 勾选统一确认项，点击「确认需求并开始全流程」。四阶段成为进度与产物查看入口；真实文件、Skill/知识读取、构建与测试证据通过后自动衔接。自动通过事件明确标记 `confirmed_by=pipeline`，不冒称用户逐阶段人工评审。
5. 若 DeepAgents 发现关键信息缺失或需求冲突，会调用 `request_user_input`。页面出现问题、背景与候选项；可以自由回答，点击「提交回答并继续」。问题及回答保存在服务端，刷新后仍可恢复。没有用户回答不会继续。
6. 完成后在全流程面板点击「打开试玩游戏」。取消自动发布的项目仍可在测试页手动发布。

调度复用既有 `create_deep_agent` 与 SQLite 检查点。提问工具使用 LangGraph `interrupt()`，回答使用同一 `thread_id` 的 `Command(resume={问题ID: 回答})`。多个问题必须完整回答，过期或重复回答被拒绝。实现参考 [DeepAgents HITL](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop) 和 [LangGraph 中断](https://docs.langchain.com/oss/python/langgraph/interrupts)。常规阶段不设人工审批中断；初次确认授权的是模板中明确保存的执行与发布计划。

单阶段失败最多自动恢复一次；独立测试仍失败时最多自动退回代码修复一次，并重新执行测试。持续失败会保留真实错误并暂停，用户可查看事件、继续或取消。服务重启保留检查点和待答问题，其他未完成任务显示「已中断」，点击「继续全流程」恢复，避免重启后悄悄重复计费。关闭浏览器不终止已启动任务。

内置模板位于 `resources/workflow-templates/`，交换格式为 `schema_version=1`。只允许需求、模型选择、参考路径与阶段配置，不含 API Key、执行状态和工作目录；导出时也清空固定发布路径。后端校验四阶段完整性、Skill 是否存在与参考路径边界。导入模板本身不会执行模型。

旧项目仍保留原有手动分阶段操作与历史记录。此前 LUDO 使用的预置规则模块和素材校准文件不会被新模板自动复制，新运行从真实参考资料分析制作。

本次已用服务器 API Key 的 `gpt-6.1-sol` 从空工作区完成「星点采集」验证项目，包含网页提问、刷新后回答、四阶段自动通过及自动发布，共 54 次真实模型响应。可[打开验证游戏](https://pagent.ahagamecenter.com/games/pipeline-star-check-20261109/index.html)。发布的 6 个文件与验收构建逐项哈希一致，桌面及 390/320px Chromium 触摸模拟下的五次点击胜利、刷新恢复、重开均通过。平台后端 193 项测试通过，网页模板导入/导出、需求修改撤销确认和取消/继续回归通过。详细记录见 [全流程验收记录](template-pipeline-validation.json)。本次没有重新制作第二份 LUDO；LUDO 模板已核验填入、导入与导出，真实完整新运行采用上述小型游戏。

## LUDO 原版贴图与动画版（2026-11-06）

[直接试玩新版 LUDO](https://pagent.ahagamecenter.com/games/ludo-classic-reskin/index.html)。项目为「LUDO · 原版贴图与动画版」，ID `3663442e040f42b2b73291ef2094884b`，工作区 `games/ludo-classic-reskin`；原有《琥珀商路》继续保留。

本轮沿用现有四阶段 DeepAgents，实际模型事件均为 `api-key` / `gpt-6.1-sol`，没有切换 Codex 登录模型。使用现有 `casual-game-production`、`ai-art-automation`、`h5-canvas-reskin`，美术阶段另选 `azure-image2-generation`；实际读取事件与冻结正文哈希均已归档，无须新建另一套 Agent 或游戏专用 Skill。

视觉以 Ludo Superstar 的真实运行棋盘、营地、亮面棋子、头像和骰子为主，Just Ludo 提供表现参考。54 张图片和 4 段音效按明确清单集成；唯一新贴图是带原图参考的 `gpt-image-2` 紫色背景编辑。摇骰使用原版 25 槽、约 833ms 的序列，另有逐格弧跳、吃子逆路回营、归家闪光和胜利彩纸。完整原图集、旧候选和参考商业脚本不进入发布包。

### 在网页查看、试玩与继续制作

1. 打开网站首页，进入「产出游戏」，搜索 LUDO，选择「LUDO · 原版贴图与动画版」，点击「开始游戏」或「新窗口打开」。直接试玩链接无需经过工作台。
2. 查看生产过程时，进入「全流程工作台」并打开同名项目，四阶段均已确认；报告、真实截图、动画证据和发布地址可在项目中查看。
3. 若继续修改，在「阶段执行」选择模型来源「API Key 网关」、模型 `gpt-6.1-sol`。另一选项「Codex CLI（服务器登录）」仍可选，属于不同执行来源；本轮验收只证明 API 路径。
4. 本项目品类为「棋盘与回合制」，技术方案为「Canvas 2D · Web / H5」。Skill 使用手动选择；保留上述美术/换皮技能，不添加 `azure-image2-generation/modules/casual-game-art-style/SKILL.md` 的泛化风格，以免重新偏离原版。
5. 修改需求应明确“保持原版十字棋盘、四色功能色与部件布局，只做小幅纹理调整；摇骰、逐格走子、吃子、归家和胜利必须有真实动画”。改动上游阶段后，重新验证、确认下游再发布，不能只替换公开文件。

本项目明确复用了上一 API 项目的五个纯规则模块，来源见 `design/reuse-baseline.json`。这些是已准备的项目输入；新建其他工作区不会自动复制本项目代码，也不能把跨工作区复用当作默认能力。

### 实际验收与交付

最终确认运行：原型 `90af2a79322d4bfcaf6a9399d1448984`，美术清单补正 `fb3483a972b1439b9e15e809ec42f320`，代码 `19ff0734d6d0453184d640161de59a1f`，独立测试 `e1c11cf67503417789e4ff685e4560db`。美术实际参考编辑与裁切来自此前运行 `0c71c52dcca24ebab342debc11aad7da`；补正运行沿用这些真实素材，不冒称重新生图。

- 独立测试重新执行 build/test/check，三项退出 0；11 组测试、18 局完整规则对局和 6,405 步逐条重放一致。
- 经典两席人机、快速四人同屏均由真实输入完成；三席轮转、桌面及 390/360/320px 手机触摸布局通过。
- 五类正常速度动画有真实时间、连续 PNG、录像及 Canvas 像素变化证据；9 组动画暂停/刷新/重开、真实后台切换与 AI 恢复、无效席位输入、慢加载门禁通过。
- 最终构建 71 文件、1,287,748 字节，构建指纹 `5128f172f4b90c6e7151712878e9bc95969bad5f2a2bc2388dcab11e1191fa79`；发布入口取回的 71 个文件逐项 SHA256 相同。独立链接与游戏库内嵌均通过实际开局和输入检查，独立链接还验证了刷新恢复。
- 源码包 `games/ludo-classic-reskin/releases/ludo-classic-reskin-source.zip`、试玩包同目录 `ludo-classic-reskin-dist.zip`；源码包实际解包、重建及单测通过，重建字节与最终 dist 一致。包内 README 是代码交接快照，最新发布状态以工作台为准。

本轮补齐可复用的 `process_art_image`：按真实编码识别 PNG/JPEG/WebP，处理 Cocos 中扩展名为 PNG、内容实际为 WebP 的素材，支持精确裁切和等比透明画布装配。清单字段错误改为指出具体文件和字段；复杂来源保存在 `source_details`。交付 ZIP 统一使用 `releases/`，防止构建输出混入源码指纹。被拒绝的无参考生图、清单格式失败和首版输出目录失败仍保留在运行历史中，未通过的候选没有发布。

手机验收仍是 Chromium 触摸模拟，未验实体手机或 Safari。服务器回访公网域名仍超时；部署证明来自本机实际网站入口的文件校验和浏览器操作，不声称已从外部手机网络复验。
