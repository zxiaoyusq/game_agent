---
name: cocos-mcp-channel
description: Use when 用户要通过 MCP 驱动 Cocos Creator 3.8.x 编辑器、配置或启动 Funplay MCP 或 harady cocos-creator-mcp、在线拼 UI、烘焙 prefab、检查引用或进行无人值守编辑器操作；也用于 harness 需自己拉起编辑器（编辑器起不来/进程秒退）、绕过人工点扩展面板自动启动 MCP 服务、编辑器频繁崩溃需自愈续跑、或要批量截运行态画面与设计稿比对；2.4.x 使用文件级与 CLI 通道。

---

# Cocos MCP 实时通道 (cocos-mcp-channel)

## 执行卡（先用这张卡，再读正文）

**我管什么**：Creator 3.8.x 编辑器 MCP 实时操作与中间检查；正式构建/设备验收交给 QA 模块。

**第一步做什么**：确认工程/Creator 版本与当前已开工程，按第 2.1 节选通道。Funplay 脚本仅初步探测，随后用 get_editor_state 验证身份；harady 用 /health、MCP 握手/只读调用及 cocos://project/info Resource 核对工程。TCP 可连和 server_status 单独返回均不能证明工程归属。

**要 harness 自己拉起编辑器 / 无人值守批处理**：直接读**第 9 节 + `modules/cocos-mcp-channel/references/autonomous-startup.md`**，跑 `modules/cocos-mcp-channel/scripts/ensure_cocos_mcp.py`。三个必知点：
① 编辑器进程秒退且退出码 0 → 先查 `ELECTRON_RUN_AS_NODE`（环境变量污染，不是工程坏了）；
② 不用人点面板也能起服务——`--remote-debugging-port` + CDP 调 `Editor.Message.request(pkg,'start-server')`；
③ DADAPET 曾发生导航期间断线，恢复链是「目标编辑器 → MCP新会话 → **重开游戏预览** → 桥接就绪 → 重试失败项」。该案例只证明一次恢复后续跑，崩溃根因、普遍阈值和长期稳定性未证明。脚本仅支持 harady；工程身份不符或活实例无CDP时失败退出，不全局杀进程。

**做完怎么算完成**：服务和工程归属有工具返回证据（并记录本任务用的是 Funplay 还是 harady 通道）；修改已保存、引用已检查；正式构建/设备门禁另按 QA 执行。

**红线**：2.4.x 不走 MCP；操作前保留工程/配置备份；预览不能替代正式 QA。端口/版本/工具数量按当前扩展发现。自定义游戏侧命令**不得在没做事时返回 success**（9.6 有两次踩坑记录）。

**按需读**：本文件通道选型与启动章节、`modules/ui-feature-pipeline/SKILL.md`、`modules/prefab-bake/SKILL.md`；**美术差异报告复核（运行态复测+报告回写）→ [art-diff-reaudit.md](references/art-diff-reaudit.md) + `scripts/artdiff_*.py`**；规则见 `references/execution-protocol.md`。

本模块是 harness 驱动 Cocos 的**第二通道**：编辑器内实时 MCP。它与既有模块的
"文件级 + CLI"离线通道并列，不是替代——按工程版本选通道：

| 工程版本 | 通道 | 说明 |
| --- | --- | --- |
| Cocos Creator **3.8.x** | **MCP 实时（本模块）** + 文件级 | harness 通过 MCP 直接建节点/改组件/烘焙/校验，编辑器所见即所得 |
| Cocos Creator **2.4.x**（如 Marble Shooter 2.4.13） | 仅文件级 + CLI（既有模块） | MCP 扩展要求 3.5+/3.8+，2.4 工程不可用，不折腾 |

范围标签：本模块全部为 `GENERAL_DEFAULT`（MIT 开源扩展，跨项目通用）；
本机安装路径与端口是**2026-09-14 历史实测值**，每次任务先按第 2 节重新发现。

## 1. 通道选型（先读这张表再动手）

| 任务 | 首选工具面 | 落点模块 |
| --- | --- | --- |
| 无人值守搭 UI / 建节点 / 拼界面（3.8.x） | MCP `execute_javascript`(scene) / Prefab 组 | 本模块 + `ui-feature-pipeline` 阶段 4 |
| 烘焙固化 prefab（3.8.x 实时） | MCP `create_prefab_from_node` / `edit_prefab_json` / `apply_prefab_instance` | 本模块 + `prefab-bake` 门禁 |
| 烘焙固化 prefab（2.4.x 或无 MCP） | JSON 手工七步（不变） | `prefab-bake` |
| 快速视觉循环（预览截图） | MCP `run_project_preview` / `capture_preview_screenshot` | 本模块；**正式验收仍走 `cocos-qa`** |
| 引用/场景校验（编辑器在线） | MCP `validate_prefab_references` / `validate_scene` / `validate_asset_dependencies` | 与 `cocos-creator-repair`（离线 `check_fire_refs.py`）互补 |
| TS 编译报错分诊 | MCP `run_script_diagnostics` / `get_script_diagnostic_context` | 本模块 |
| 最终构建出包 + 真机验收 | CLI 构建（不变） | `cocos-qa` + `vision-device-testing` |
| 新工程结构/命名/接口规范对照评审 | 不改工程，只出对照清单（体检查版本与框架层） | `cocos-project-standards` |

**分工铁律**：MCP 通道负责"编辑器内的实时操作与中间验证"；正式构建、模拟器/真机、
截图验收证据包仍按 `cocos-qa` / `vision-device-testing` 的门禁执行，两者证据等级不同，
不得互相替代（全局证据规则第 2 条）。

## 2. 本机安装与发现（每次任务先核对）

- 扩展：**Funplay MCP for Cocos**（MIT，v0.6.3 实测），仓库
  `https://github.com/FunplayAI/funplay-cocos-mcp`。
- 全局安装位置（按 Creator 版本隔离，历史安装记录，当前任务须重查）：
  `%USERPROFILE%\.CocosCreator\builtin-extensions\3.8.7\funplay-cocos-mcp`
  （3.8.2 等其他版本需各自安装一次；项目级副本在 `<project>/extensions/`，优先级更高，
  二者并存会冲突提示，留一份即可）。
- 更新：`git -C <上述目录> pull`，或扩展面板 `Funplay > MCP Server` 的 Release 安装。
- 编辑器本机路径（2026-09-14 实测）：`C:\ProgramData\cocos\editors\Creator\3.8.7\CocosCreator.exe`
  （`E:\Gameprogram\CocosCreator_*` 旧路径已失效）。

### 2.1 通道实现选型：Funplay（默认）与 harady（备选）

本模块支持两个 3.8.x MCP 扩展实现，**默认 Funplay**（SOP、启动脚本与坑表都按它沉淀）；harady 是 2026-10-12 接入的备选（工具面粒度更粗但带只读 Resources 与 stdio bridge，见第 8 节）。

| 维度 | Funplay MCP（默认） | harady/cocos-creator-mcp（备选） |
| --- | --- | --- |
| 来源 | FunplayAI/funplay-cocos-mcp v0.6.3（第 2 节） | harady/cocos-creator-mcp v2.0.2（第 8 节） |
| 工具面 | core 39 / full 105，主工具 `execute_javascript` | 64 个 category_action 工具 + 12 只读 Resources |
| 传输 | HTTP（面板写 URL；8765 / 20000+） | HTTP `http://127.0.0.1:3000/mcp`（项目配置可改）+ stdio bridge |
| 连通验证 | `get_editor_state` 核对工程 | `/health` → 握手/当前只读工具 → `cocos://project/info` 核对工程 |
| 何时选它 | 默认；无人值守 SOP 全按它 | 需要只读 Resources 巡检、客户端有 OAuth 问题走 stdio bridge、或 Funplay 不可用时 |

**单写入者纪律**：同一工程同一时间只启用/接入一个实现；换实现先断开另一条的客户端配置，避免两条通道同时写编辑器状态。

## 3. 启动与端口（无人值守入口）

**一键脚本**：`modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1`

```powershell
powershell -ExecutionPolicy Bypass -File <skill>/modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1 `
  -ProjectPath "D:\path\to\cocos-project"          # 可加 -Port 8765 / -NoLaunch / -WaitSeconds 120
```

- 幂等：先探测已监听端口，`READY_ALREADY_RUNNING` 直接返回，不重复拉起编辑器。
- 探测顺序：`-Port` 指定值 → `8765`（旧固定端口）→ `20000-20012`（新项目独立端口带前段）。
- 输出单行 JSON：`status / project / mcp_port / mcp_url / editor_running`，harness 直接解析。
- 现有 Funplay 探测脚本按任意编辑器/TCP判断，project为传入值，不能证明服务归属；其他工程已开时须另核对实际身份。没有崩溃恢复功能，20000-20012也没有覆盖完整端口带。
- `TIMEOUT_OPEN_FUNPLAY_PANEL_TO_CHECK_PORT`：编辑器已起但 MCP 未监听——人工开一次
  `Funplay > MCP Server` 面板看实际端口（临时回退端口必须先点"固定当前端口"再配客户端），
  之后用 `-Port <实际端口>` 重跑。

**端口机制**（来自扩展 README）：新项目获得 `20000-29999` 稳定项目独立端口；
已有配置保留原固定端口（含 8765）。端口被占时同项目 listener 安全复用，无关 listener
自动回退下一可用端口。**以面板显示的实际 URL 为准**。

## 4. harness 接入（先备份客户端配置再改）

MCP 服务为 HTTP 传输。在 harness 的 MCP 配置中加（server 名习惯
`cocos-<project>-<hash>`，一键配置由扩展面板写入）：

```json
{ "mcpServers": { "cocos-<project>": { "type": "http", "url": "http://127.0.0.1:<port>/" } } }
```

- OpenCode：工程 `opencode.json` 的 `mcp` 段（`"type": "remote"`）；Codex / WorkBuddy /
  Claude Code / Cursor / Trae / Qoder 均在各自 mcp 配置写同一 URL。扩展面板自带
  各客户端一键配置。
- 改配置前备份原文件；改完用一次 `get_editor_state` 调用做连通性验证（端到端确认，
  不靠"理论上能连"）。
- 工具面：默认 `core` 39 个；`full` 105 个（含删除/写文件等破坏性工具），在
  `Funplay > Tool Exposure` 按需开启。无人值守流建议保持 core + 按需加 Prefab/Build 组。

## 5. 工具面精要（core 39 / full 105）

- **主工具**：`execute_javascript` —— `context:"scene"` 在当前场景/运行态执行 JS
  （建 UI 层级、挂组件、读节点值）；`context:"editor"` 在编辑器上下文执行（Editor API、
  asset-db、文件系统、MCP 编排）。窄工具不够用时优先回它，避免多窄工具噪声。
- **Prefab 组（full）**：`create_prefab_from_node`（节点→prefab，UI_2D 归一化，
  3.8.x 上替代裸 scene:create-prefab）、`edit_prefab_json`（JSON path 赋值/字面替换 + 引用校验）、
  `apply_prefab_instance` / `revert_prefab_instance` / `instantiate_prefab` / `duplicate_prefab`
  （不复制 meta UUID）。
- **校验组**：`validate_prefab_references`（序列化 UUID 对 asset-db）、`validate_scene`
  （场景+runtime+TS 诊断+日志一次性体检）、`validate_asset_dependencies`、
  `run_script_diagnostics`（TS no-emit）。
- **构建/预览组**：`get_build_status`、`run_project_preview`（browser / Game View /
  simulator）、`get_preview_mode` / `set_preview_mode`、`open_build_panel`。
- **截图组**：`capture_editor_screenshot` / `capture_scene_screenshot` /
  `capture_preview_screenshot` / `capture_game_screenshot` / `capture_desktop_screenshot`。
- **输入模拟（full）**：`simulate_mouse_click/drag`、`simulate_key_press/combo`、
  `simulate_preview_input`——对编辑器/预览/模拟器窗口发低级输入（Game View 冒烟用）。
- **文件组（full）**：`read_file` / `write_file` / `replace_in_file` / `refresh_assets`——
  限定在 Cocos 项目内（path-safety），脚本自动修复循环用。
- 完整清单：扩展目录 `docs/TOOLS.md`（由 tool-registry 生成，勿手编）。

## 6. 无人值守 SOP（harness 主视角，哥哥只审成品）

1. **拉起**：跑 `start_cocos_mcp.ps1` 拿 `mcp_url`（幂等，编辑器已起则秒回）。
2. **接入**：把 URL 写进 harness MCP 配置（先备份），`get_editor_state` 验证连通。
3. **读知识**：按任务加载 `ui-feature-pipeline`（六阶段）与 `prefab-bake`（门禁/字段表）——
   知识层不变，只是执行工具从"改 JSON + CLI"换成 MCP 工具。
4. **开发**：阶段 1-3 照旧（需求表/效果图 QA/控件切分，生图走既有生图 skill）；
   阶段 4 重组用 `execute_javascript`(scene) 实时建层级挂组件；阶段间用
   `capture_scene_screenshot` 做中间视觉自检（非正式验收证据）。
5. **固化**：`create_prefab_from_node` 落 prefab → `prefab-bake` 的验收门禁
   （fileId 唯一 / 多分辨率 / 适配函数保留 / 双真值）逐条过；JSON 级微调用
   `edit_prefab_json` + `validate_prefab_references`。
6. **验收**：最终构建出包与真机证据仍走 `cocos-qa` / `vision-device-testing`；
   MCP 预览截图只算中间验证。
7. **收尾**：`save_current_scene`（full）保存编辑器状态；无需关闭编辑器（幂等脚本
   下次复用）。

## 7. 坑与安全（实测/上游文档提炼）

- **`execute_javascript` 是任意代码执行**：只对自有工程启用；不把端口暴露到局域网外。
- **编辑器单实例纪律**：同工程编辑器与离线CLI build分开调度，不并发互写build；按目标root/PID/启动时间核对实例，不全局清理其他工程。旧脚本“任意已有进程不拉起”不足以证明目标实例正确。
- **临时回退端口**：面板显示 fallback 端口时先"固定当前端口"再配客户端，否则重启后漂移。
- **全局 vs 项目副本冲突**：同名扩展两处并存会有冲突提示，留一份（建议全局，工程零侵入）。
- **3.8.x 专用**：`create_prefab_from_node` 等消息在 3.8.x 验证；2.4 工程调用会静默无效果
  → 版本不符直接走文件级通道，不要试。
- **EPERM 日志报错为良性**（同 `cocos-qa`），别当成 MCP 失败。
- **MCP 截图 ≠ 验收证据**：等级低于正式构建截图（全局证据规则第 2 条）。
- **更新**：`git pull` 后重启编辑器生效；面板会提示落后于 GitHub Release。

## 8. 备选通道 harady/cocos-creator-mcp（v2.0.2，2026-10-12 接入）

- **来源与更新**：https://github.com/harady/cocos-creator-mcp（MIT）。本机克隆
  `D:\skills\cocos-creator-mcp`（浅克隆 @ a25ebd9，2026-09-21）；github 直连被重置时用
  `https://ghfast.top/https://github.com/harady/cocos-creator-mcp` 镜像。更新：
  `git -C D:\skills\cocos-creator-mcp fetch` → ahead/behind 判断，工作树干净才 pull
  （`node_modules` 是本地生成的，pull 后重跑 `npm install`）。
- **本机安装**：junction `%USERPROFILE%\.CocosCreator\builtin-extensions\3.8.7\cocos-creator-mcp`
  → `D:\skills\cocos-creator-mcp`（2026-10-12 建，与 funplay-cocos-mcp 同目录并存不冲突，
  名字不同）；其他 Creator 版本（本机另装有 3.8.8）按需各自 junction。
  **编辑器内激活与基本端到端已在2026-10-14 DADAPET验证**：CDP调用start-server不依赖打开面板；当前工程重新查扩展/身份，完整回归与长期稳定性另验收。
- **构建**：仓库自带预构建 dist（BUILD_ID 20260327035439）；2026-10-12 本机 `npm install`
  （19 包）+ `npm run build`（tsc，BUILD_HASH 36e0a3582d7e）成功且复跑兼容测试 PASS，
  Node 24 工具链可复现。仅源码改动才需重建；重建后在 Creator 重载扩展，
  场景脚本改动需重启编辑器。
- **项目配置**：`<project>/settings/cocos-creator-mcp.json`：
  `{ "port": 3000, "autoStart": true }`。3000 是常见开发端口，冲突就改这里并以
  `/health` 实测为准。
- **客户端接入**（先备份客户端配置再改）：HTTP 直连
  `{ "mcpServers": { "cocos-creator-mcp": { "type": "http", "url": "http://127.0.0.1:3000/mcp" } } }`；
  或 stdio bridge
  `{ "mcpServers": { "cocos-creator-mcp": { "command": "node", "args": ["D:\\skills\\cocos-creator-mcp\\client\\stdio-bridge.js"] } } }`
  （Claude Code VSCode 扩展等 OAuth 兼容问题场景走 bridge；环境变量 `COCOS_MCP_URL`
  覆盖目标 URL，2026-10-12 实测 bridge 内置默认 `http://127.0.0.1:3000/mcp`）。
- **工具面（v2.0 category_action 64 个）**：scene×12（scene_manage / scene_query /
  scene_execute_script / scene_execute_component_method…）、view×3、node×10（node_manage /
  node_create_tree / node_set_property / node_get_info…）、component×3（component_auto_bind
  批量绑引用）、prefab×7（prefab_edit / prefab_create / prefab_validate…）、asset×2、
  project×6、debug×15（read_console / debug_screenshot / debug_preview /
  debug_wait_compile…）、preferences / builder / server_status、refimage×3；另有 12 个
  只读 Resources（`cocos://scene/current`、`cocos://project/info`、`cocos://asset/{uuid}` 等，
  供支持 Resources 的客户端做只读巡检）。v1→v2 工具名映射见仓库 `MIGRATION.md`。
- **验证与测试**：服务起后先 `curl http://127.0.0.1:<port>/health` 再调 `server_status`；
  该tool的get/port查询Creator预览服务器，不是MCP transport。MCP URL取扩展get-server-status的port；通过resources/list/read的cocos://project/info核对工程，按tools/list查实际名称/参数。
  无需编辑器的静态回归 `npm run test:compat`（2026-10-12 本机 2/2 PASS：无全局 crypto 的
  scene 创建、URI 参数单次解码）；需编辑器在跑的完整回归 `node test/regression.mjs [port]`
  （357+ 断言，首次激活后跑一遍并回填本模块 landing-log）。
- **坑**：① 服务跑在编辑器进程内——编辑器没起或扩展未启用时端口必然不通，先查壳再查服务
  （**要 harness 自己把壳拉起来，走第 9 节**）；② 扩展附带 dummy OAuth 端点（`/oauth/*`、`/.well-known/oauth-*`，上游兼容临时方案），
  端口**勿暴露局域网外**（同 Funplay 任意代码执行红线）；③ 与 Funplay 二选一启用
  （2.1 节单写入者纪律）；④ `debug_clear_code_cache`、`builder_manage` 等属破坏面，
  无人值守保持最小启用；⑤ 2.4.x 工程不可用（本模块红线不变）；⑥ **本项目内还并存一个
  `cocos-mcp` v2.8.0（`<project>/extensions/cocos-mcp-server`），方法未注册、调用即报
  `methods is undefined`——在用的是 `cocos-creator-mcp`，调之前先用 `Editor.Package.getPackages()`
  核实包名（见 9.4）**。

## 9. 无人值守启动与自愈（2026-10-14 实测沉淀）

> 长文与完整取证过程见 `modules/cocos-mcp-channel/references/autonomous-startup.md`；一键脚本
> `modules/cocos-mcp-channel/scripts/ensure_cocos_mcp.py`。**要自己拉起编辑器并跑无人值守批处理，先读这一节。**

### 9.1 能自动到什么程度

| 想做的事 | 能否自动化 | 怎么做 |
| --- | --- | --- |
| 启动 Cocos 编辑器 | ✅ | `Start-Process` + **剔除 `ELECTRON_RUN_AS_NODE`**（9.2） |
| 拿到编辑器 JS API | ✅ | `--remote-debugging-port=9222` + CDP（9.3） |
| 启动 MCP 服务（不用人点面板） | ✅ | CDP 里 `Editor.Message.request(pkg,'start-server')` |
| 让扩展面板自动打开 | ❌ | UI Automation 与改 `window.json` 布局都试过，不行 → **走 CDP 而非开面板** |
| 编辑器崩溃后接着跑 | ✅ | 崩溃 → 重启编辑器 → 起 MCP → **重开游戏预览** → 重试本项（9.4） |

### 9.2 坑一：`ELECTRON_RUN_AS_NODE` 污染（先查它，别查工程）

**症状**：从 harness 启动编辑器后进程 **900ms 内自己退出**、**退出码 0**、无窗口、
无日志、事件日志无崩溃记录。四个现象凑一起极易误判成"工程坏了/许可失效/杀软拦截"。

**根因**：harness 自身若是 Electron 应用（DSH / VS Code / Cursor…），环境里带
`ELECTRON_RUN_AS_NODE=1`；子进程继承后 Electron 以 **Node 模式**运行，拒绝 `--project` 这类 GUI 开关。

**一步取证**：`-RedirectStandardError` 抓 stderr，看到这句即可定性：

```
CocosCreator.exe: bad option: --project
```

**修法**：启动前 `Remove-Item Env:ELECTRON_RUN_AS_NODE`（及 `NODE_OPTIONS`），
或用剔除后的 env 启动子进程。**鉴别口诀：秒退 + 退出码 0 + 无崩溃事件 → 先查这个变量。**

### 9.3 坑二：扩展面板必须人工点（自举死锁）→ CDP 逃生舱

MCP 服务跑在编辑器进程内，常规要人点面板才 start-server。绕过方式：

```
1) CocosCreator.exe --project <proj> --remote-debugging-port=9222
2) GET http://127.0.0.1:9222/json          → 取 main.html 那个 target 的 webSocketDebuggerUrl
3) WS 发 Runtime.evaluate {expression, returnByValue:true, awaitPromise:true}
4) JS: typeof Editor !== 'undefined' ? 'HAS_EDITOR' : 'NO_EDITOR'   （实测 main.html 有 Editor）
5) JS: Editor.Message.request('<pkg>','start-server')  → {"running":true,"port":3000}
```

依赖仅 `requests` + `websockets`。

**两条走不通的路（别再试）**：① UI Automation 点菜单——编辑器是 Chromium 渲染
（`Chrome_WidgetWin_1`），无原生 MenuBar，UIA 够不到；② 改
`%USERPROFILE%\.CocosCreator\editor\window.json` 把面板塞进布局——补丁会被读取但
面板不打开，`cocos-mcp` 与 `cocos-mcp.default` 两种 id 写法都无效。

### 9.4 坑三：包名要对，否则 `methods is undefined`

同机可能并存多个同类扩展。**先查真实注册名再调，不要猜**：

```js
(await Editor.Package.getPackages())
  .filter(p => /mcp/i.test(p.name)).map(p => p.name + ' v' + p.version + ' enable=' + p.enable)
```

实测本机并存两个（`enable`/`invalid` 都正常）：**`cocos-creator-mcp` v2.0.2 才是在用的**
（`toolCount: 64`）；项目内那个 `cocos-mcp` v2.8.0 方法未注册，调用即报
`Method does not exist(...), The 'methods' of the module is undefined`。
看到这个报错先核对包加载/方法注册和实现身份，有证据证明用了错误实现才换包名。harady服务管理消息面：
`get-server-status` / `start-server` / `stop-server`；此前open-panel失败属于项目级cocos-mcp，不能推断harady面板必失败。

### 9.5 自愈式批处理：编辑器崩溃不再中断任务

**案例现象**：DADAPET批处理导航期间出现连接重置，恢复后继续任务；次数来自该项目会话报告，不能定义为Creator的“10次硬限制”。退出根因仍需退出码/崩溃日志配对。

**恢复链（缺一环就恢复不了）**：

```
每项前健康检查 → 不通则 ensure_cocos_mcp.py
                 → ⚠️ 必须再 debug_preview start **重开游戏预览**
                    （只重启编辑器+服务，游戏侧客户端不会轮询，命令全部超时）
                 → 轮询到桥接重新连上 → **重试本项**（不是跳到下一项）
```

实测21屏任务在第11项连接断开，恢复编辑器/MCP/预览后继续完成8项，总计18成功、3失败。原日志虽打印“重试本屏”，实际从第12项继续，失败项CrossEnd未重试成功；不得写成全批通过。批处理应保存每项结果并重试原失败项，旧截图须标记旧证据，失败未清零返回非零，不能只按文件存在跳过。恢复器是按需调用，不是常驻watchdog；暂停/正常关闭/构建切换不自动复活。

### 9.6 游戏侧桥接：命令必须真实反映失败

要 MCP 能"打开某界面再截图"，需在游戏代码注册自定义命令：复制扩展的
`client/McpDebugClient.ts` 进工程（只依赖 `cc`），用独立文件包 `initMcpDebugClient({customCommands})`，
**默认关、可整体删除**；服务未启动时客户端内部静默忽略，对游戏零影响。

**两次踩坑都在"没做事却报 success"**：

```typescript
// ❌ 可选链短路 → 什么都没做，却返回 success。后果：19 张截图 16 张同一画面
await CFW.stage.get(LobbyStage)?.getSystem(ShopSystem)?.openShop();
return { success: true };

// ✅ 显式判空 + 返回计量供调用方校验
const stage = CFW.stage.get(LobbyStage);
if (!stage) return "LobbyStage 未激活 —— 先执行 enterLobby";
const sys = stage.getSystem(ShopSystem);
if (!sys) return "系统未注册: ShopSystem";
await sys.openShop();
return null;
```

建议暴露：`pages`（支持清单，用来确认桥接真连上）、`uistate`（当前面板）、`closeAll`
（返回 `{before, after}`）、`enterLobby`（**全新预览默认走引导 Stage，不执行它所有大厅界面都打不开**）。

以上是DADAPET自定义DebugBridge命令，不是其他游戏的默认功能；Wallkickers按自身已实现的心跳/状态入口验证，缺桥接不能据此认定编辑器崩溃。正式玩法验收使用真实输入，不靠enterLobby等状态修改制造通过。

**界面打不开的排查顺序**：`pages` 通不通 → 通则看 `navigate` 报错（提"LobbyStage 未激活"就先
`enterLobby`）→ 成功但截图不对就 `uistate` 看堆叠。

### 9.7 要跟设计稿比对，就用运行态截图

| | 编辑器 prefab 截图 | 运行态截图 |
| --- | --- | --- |
| 内容 | prefab 自身节点，孤立在网格上 | **完整成品画面** |
| 宠物 / 背景 | ❌ 独立 prefab | ✅ |
| 运行时赋值的贴图 | ❌ 品红方块 | ✅ 真实渲染 |
| 与设计稿比例 | ❌ 横向对不上 | ✅ 同比例 |

试过"裁到编辑器场景视图里的 Canvas 白框"来自动对齐比例：**42 张只命中 8 张**，且命中尺寸
互相矛盾（`519x1108` vs `87x194`，后者是误判）——**不可行，别重走**。
运行态截图走游戏侧 `screenshot` 命令（RenderTexture 抓画面）。

### 9.8 坑：`closeAll` 清不掉的界面

不是所有 UI 都归框架 `uiMgr` 管。实测"设置"界面不在 `_openPanels` 里，`closeAll` 报
`{before:0, after:0}` 但它仍显示并压在后续每屏背后。
**兜底：把这类界面排到批处理序列最后**（本次把 `Setting` 移到最后，前面 19 屏全干净）。
不要为了清洁每屏重启预览——每屏多 ~25 秒，且预览重启本身是崩溃诱因。

### 9.9 美术差异报告复核（runtime re-audit，2026-10-19 DADAPET 实测沉淀）

对**已存在的美术差异评审报告**做运行态复测并回写：逐屏实拍当前构建 → 逐项判定
「✔已修复 / ✗仍存在 / 🔄已重构（旧清单作废）/ ⚠需确认」→ 非破坏回写（横幅 + h2 状态标签，
原始条目不动）。与 9.7 的关系：9.7 是首次采集建基线，本节是对既有报告的**复核回写**。

**九条实测坑**（全量见 [art-diff-reaudit.md](references/art-diff-reaudit.md)）：预览游戏循环随编辑器失焦被节流
（命令间歇超时 → 前台化编辑器窗口 + 重启预览）；FAIL ≠ 没截图（先查时间戳）；skip 按"文件存在"
会跳过**旧构建旧图**（必须 --only+--redo 分批 + 时间戳验证）；桥与主线 API 漂移
（`(intermediate value)...` = 调了已删除接口 → 改未提交桥代码）；10054 重试 / 10061 编辑器已挂；
审计前后 UI 语言不同时溢出类结论不可沿用；Stage 门禁页先 enterGuide；残留清理按页根名 +
NEVER_KILL/EXTRA_KILL 按项目枚举；主线无桥时从 git 历史恢复**不提交**、审计完丢弃。

**引擎 API 坑（10）**：3.8.7 的 `cc.Animation` 组件**没有 `getClip`**（只有
`play/getState/createState/clips/defaultClip`）——按 3.2 记忆写 `anim.getClip(name)` 运行时即报
`is not a function`；改用 `anim.clips.some(c => c && c.name === N)` 按名匹配。手写 prefab 的
Animation 组件挂载（cc.Animation + CompPrefabInfo + _clips 引用 .anim uuid）本机实测可被
编辑器/运行时正常加载。

**探针自身会骗人（11）**：桥里写 `node.getComponent(Animation)`，若该文件**没有 import `Animation`**，
等价于 `getComponent(undefined)` —— **静默返回 null**，实测报
`hasAnimation:false, clipNames:[]`，而节点上剪辑其实正在驱动缩放，差点把"已修复"判成"未修复"。
改法：枚举 `node.components` 并用鸭子类型取目标组件
（`(view.components ?? []).find(c => Array.isArray(c.clips) || typeof c.play === 'function')`），
完全不依赖 import。同类风险适用于所有"按类查组件"的探针。

**运行时文案被静态多语言组件覆盖（12）**：代码在 `onOpen` 里写 `label.string` 之后，若该节点同时挂了
项目的 MultiLanguageText（带静态 key），运行时显示的会是 **key 的译文**而不是代码传入值。DADAPET
实例（2026-10-20 实测）：`CommonConfirm` 的 5 个文本节点在美术 prefab 批次里被挂上 LackCoin 专属 key
（`NOT_ENOUGH_GOLD` / `FUNC_EARN` / `FEED_CANCEL` / `COMMONCONFIRM_TXT*`），于是任何非 LackCoin 调用方
（保存装扮确认、退出确认…）都会渲染成「金币不足 / 赚金币」；同批 84 处挂载中 40 处落在疑似代码写值节点。
排查顺序：① 读运行时 `label.string` 拿到实际值；② 静态比对同一节点是否挂了多语言组件及其 key；
③ `git show <ref>:<prefab>` 对比程序分支与当前分支，定责是本次改动引入还是原有；
④ 判据：**凡"运行时由代码按数据写值"的文本节点，prefab 上不得挂静态 key**（静态展示文案节点保留挂载）。

脚本：[mcp_http.py](scripts/mcp_http.py)（客户端）、[artdiff_probe.py](scripts/artdiff_probe.py)（三连探测）、
[artdiff_runtime_shots.py](scripts/artdiff_runtime_shots.py)（逐屏实拍+自愈）、[artdiff_reaudit_html.py](scripts/artdiff_reaudit_html.py)（报告回写）。

## 10. 落地记录

落地结果按总集"落地迭代协议"追加到本模块 `modules/cocos-mcp-channel/references/landing-log.md`
（日期/阶段/实际结果/偏差/回填动作/验证）。首次安装记录：2026-09-14，
Funplay MCP v0.6.3 装入 `builtin-extensions\3.8.7`，脚本与模块由本次任务沉淀。
