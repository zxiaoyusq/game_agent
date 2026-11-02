---
name: cocos-mcp-channel
description: Use when 用户要通过 MCP 驱动 Cocos Creator 3.8.x 编辑器、配置或启动 Funplay MCP、在线拼 UI、烘焙 prefab、检查引用或进行无人值守编辑器操作；2.4.x 使用文件级与 CLI 通道。

---

# Cocos MCP 实时通道 (cocos-mcp-channel)

## 执行卡（先用这张卡，再读正文）

**我管什么**：Creator 3.8.x 编辑器 MCP 实时操作与中间检查；正式构建/设备验收交给 QA 模块。

**第一步做什么**：确认工程/Creator 版本，检查 Funplay 扩展，运行 `modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1` 探测或启动，再用 `get_editor_state` 核对服务与工程。端口可连不等于 MCP 已验证。

**做完怎么算完成**：服务和工程归属有工具返回证据；修改已保存、引用已检查；正式构建/设备门禁另按 QA 执行。

**红线**：2.4.x 不走 MCP；操作前保留工程/配置备份；预览不能替代正式 QA。端口/版本/工具数量按当前扩展发现。

**按需读**：本文件通道选型与启动章节、`modules/ui-feature-pipeline/SKILL.md`、`modules/prefab-bake/SKILL.md`；规则见 `references/execution-protocol.md`。

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

## 3. 启动与端口（无人值守入口）

**一键脚本**：`modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1`

```powershell
powershell -ExecutionPolicy Bypass -File <skill>/modules/cocos-mcp-channel/scripts/start_cocos_mcp.ps1 `
  -ProjectPath "D:\path\to\cocos-project"          # 可加 -Port 8765 / -NoLaunch / -WaitSeconds 120
```

- 幂等：先探测已监听端口，`READY_ALREADY_RUNNING` 直接返回，不重复拉起编辑器。
- 探测顺序：`-Port` 指定值 → `8765`（旧固定端口）→ `20000-20012`（新项目独立端口带前段）。
- 输出单行 JSON：`status / project / mcp_port / mcp_url / editor_running`，harness 直接解析。
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
- **编辑器单实例纪律**：并发构建/多实例会互写 build 目录（`prefab-bake` 已知坑）；
  脚本已做"已有进程不再拉起"，构建前仍按 `cocos-qa` 清进程。
- **临时回退端口**：面板显示 fallback 端口时先"固定当前端口"再配客户端，否则重启后漂移。
- **全局 vs 项目副本冲突**：同名扩展两处并存会有冲突提示，留一份（建议全局，工程零侵入）。
- **3.8.x 专用**：`create_prefab_from_node` 等消息在 3.8.x 验证；2.4 工程调用会静默无效果
  → 版本不符直接走文件级通道，不要试。
- **EPERM 日志报错为良性**（同 `cocos-qa`），别当成 MCP 失败。
- **MCP 截图 ≠ 验收证据**：等级低于正式构建截图（全局证据规则第 2 条）。
- **更新**：`git pull` 后重启编辑器生效；面板会提示落后于 GitHub Release。

## 8. 落地记录

落地结果按总集"落地迭代协议"追加到本模块 `modules/cocos-mcp-channel/references/landing-log.md`
（日期/阶段/实际结果/偏差/回填动作/验证）。首次安装记录：2026-09-14，
Funplay MCP v0.6.3 装入 `builtin-extensions\3.8.7`，脚本与模块由本次任务沉淀。
