# 美术差异报告复核（runtime re-audit）—— 2026-10-19 实测沉淀

范围标签：`GENERALIZED_PATTERN`（方法可迁移；工程路径、界面清单、桥命令、API 名必须在当前项目重新发现）。
案例锚点：DADAPET 2026-10-19（工程版本 `9de45be`，22 屏重采 21 屏、10 屏逐项目检、报告 9 个状态标签回写）。

## 我管什么

对一份**已存在的美术差异评审报告**（HTML/MD，逐屏问题清单 + 截图）做运行态复测：
重新实拍当前构建的每一屏 → 逐项判定原问题「已修复 / 仍存在 / 随重构作废 / 需确认」→
**非破坏地回写报告**。适用于"程序合入了一批修复，重新确认差异报告哪些条目已解决"的场景。
首次采集（建立基线）与 prefab 静态截图见本模块 9.7；设备验收见 cocos-qa。

## 架构与前提

```
编辑器进程(:3000) ── /mcp        编辑器工具（scene/prefab/asset/…+ debug_preview/debug_game_command）
                 └── /game/*     游戏桥队列（游戏内 McpDebugClient 以 500ms 轮询取命令、回结果）
浏览器/编辑器预览中的游戏 ── 轮询 ──┘
```

- **游戏内桥必须存在**。若主线没有桥（如美术分支被要求 TS 对齐主线后），从 git 历史恢复桥文件到
  **工作区且不提交**（`git show <历史提交>:assets/scripts/common/debug/DebugBridge.ts > …`），
  `GameApp` 只接 `initDebugBridge()` 一行（uncommitted），审计完
  `git checkout -- <GameApp> && rm -rf <debug目录>` 丢弃。恢复前确认目录里是否有**原有**脚本，
  目录 meta 可能是共享的，勿整目录删除（DADAPET 曾误删 `common/debug.meta`，目录里另有 DebugSettings.ts）。
- **桥会随主线重构漂移**：桥代码调用已删除/改签名的 API 时，navigate 返回
  `(intermediate value)...` 类 JS 错误（案例：主线删了 `LanguageManager.t()`，桥还在调）。
  直接修改**未提交的桥代码**对齐当前签名（如改传普通字符串、适配新数据结构），这也是发现
  「重构后接口对 undefined 入参容错不足」的探测器（DADAPET：LevelUp 弹 `Lv.undefined`）。
- 桥命令集参考（按项目自定）：`pages`（在线凭证）`closeAll`（返回 before/after 计量）
  `navigate {page}` `screenshot {maxWidth,imageFormat}` `enterLobby`/`enterGuide`（Stage 门禁）
  `killnodes {names}`（清 closeAll 管不到的残留）。红线见 9.6：**没做事不得返回 success**。

## 执行步骤

0. **确认报告与清单**：读报告的 MD 源（若有）拿到逐屏问题项；记录采集时的构建版本与 **UI 语言**。
1. **probe**：`debug_preview {action:start}` 拉起预览 → `pages` → `closeAll` → `enterLobby`
   三连通过才算桥就绪（脚本 `artdiff_probe.py`）。
2. **逐屏实拍**：`artdiff_runtime_shots.py`（泛化自 DSH `runtime_shots.py`，保留全部自愈逻辑）。
   逐屏序列：健康检查 → `closeAll`（校验 after=0，残留则回大厅再关）→ `killnodes` 除目标外全部页根
   + toast 层 → `navigate` → 等动画 → `screenshot` → 落盘 → 裁黑边。
3. **新鲜度验证**：`ls --time-style` 看截图时间戳是否全为本次运行——**skip 逻辑按文件存在判断，
   会把旧构建的旧图当"已截过"**（DADAPET 实测 22 屏里 19 张是昨晚旧图却全部 SKIP）。用
   `--only ... --redo` 分批强制重截，每批 ≤6 屏。
4. **目检判定**：逐屏读图，对照原清单逐项打分类标签（见下）。只对受本次变更影响的屏做逐项判定，
   其余屏标注"已重截未逐项复核"。
5. **回写报告**：`artdiff_reaudit_html.py` 非破坏注入（见下）。

## 本次新沉淀的坑（9.6–9.8 之外）

| 坑 | 症状 | 处置 |
|---|---|---|
| **预览游戏循环饿死**（编辑器窗口失焦被节流） | `Game did not respond` 间歇性出现、同一脚本忽好忽坏 | PowerShell `ShowWindow(h,9)+SetForegroundWindow` 把编辑器拉前台；`debug_preview start` 重启预览；重跑失败批 |
| **FAIL ≠ 没截图** | 命令超时报 FAIL，但截图已落盘 | 重试前先查时间戳，别盲目重跑 |
| **skip 旧图陷阱** | "已截过"跳过的是**旧构建**旧图 | `--only+--redo` 分批强制重截；用时间戳验证全部为本次产物 |
| **桥与新 API 漂移** | navigate 返回 `(intermediate value)...` | 改未提交桥代码对齐当前 API；顺带记录组件容错问题 |
| **连接 10054 / 10061** | 瞬时断连 / 拒绝连接 | 10054 等 5s 重试；10061=编辑器挂了，跑自愈/重启编辑器（DSH 实测约 10 屏一崩，脚本内置自愈） |
| **语言环境混淆** | 前后两次采集 UI 语言不同（英→中） | 溢出/截断类结论不可跨语言沿用，报告必须标注采集语言 |
| **Stage 门禁页** | `navigate CreatePet` 报 "GuideStage 未激活" | 先 `enterGuide`（采完 `enterLobby` 回大厅）；由子系统直接打开的界面（Setting 等）排最后（9.8） |
| **跨屏污染** | 上一屏的 toast/界面压在本屏背后 | killnodes 按**页根名**清残留；`ROOT_OF` 映射（子视图归属预制体根）、`NEVER_KILL` 常驻层、`EXTRA_KILL` toast 层按项目重新枚举 |
| **screenshot 返回形状不止一种** | 整批 `screenshot 返回无 path/dataUrl: {}`，但桥其实已落盘 | 有的桥把 `path`（或 `dataUrl`）放在结果**顶层**（如 `{success,path,format:webp,originalSize,savedSize}`），不是嵌在 `data` 里。泛化脚本必须**顶层与 `data` 内两种形状都吃**；落盘文件常为 **webp**（桥按 maxWidth 缩放编码），不能按扩展名当 png，须**按内容解码统一转真 PNG** 再入库（`artdiff_runtime_shots.save_shot()`） |
| **采集语言回退中文** | 换构建后运行态 UI 突然全中文，英文溢出/换行类条目"看起来都好了" | 该构建无持久化语言键（如 `LOCAL_LANGUAGE_TYPE`）时随系统语言。此时**英文文案溢出类结论不可沿用也不可判定**，必须在横幅声明**采集语言=中文**、把这些项标 ⚠「需切英文复采」，只对语言无关项（颜色/缺图/入口/按钮/叠加/占位/数量）给 ✔/✗ |
| **多个预览控制器并发打架** | 两个脚本同时 `debug_preview stop/start`，预览反复重启、桥永远连不上 | 同一编辑器实例**同时只允许一个控制器**（probe/实拍/诊断互斥）。后台重试任务未结束前不要再起第二个；发现"桥连不上"先查有没有残留的旧任务在轮询 |
| **`debug_wait_compile clean:true` 会 wedge 桥** | clean 全量重编译超时后立刻起预览 → 游戏加载到半编译状态，`initDebugBridge` 不执行，桥永不连接，且 `read_console` 还是 0 error | 复核流程**不要用 clean:true**（普通 wait_compile 即可，脚本改动本来就触发增量编译）；必须 clean 时等编译真正结束再 start 预览 |
| **崩溃重启后"navigate 成功但截图落回主界面"** | 恢复后逐屏 OK，但 OnlineGift/CommonConfirm 等弹窗截图其实是主界面 | 自愈恢复后**弹窗类界面要核验打开结果**（navigate success ≠ 弹窗真的开了；游戏状态变化如礼包已领会让 open 无效）。回写前逐张目检，发现落回主界面的标 ⚠ 需复采，别当有效证据 |
| **GameView 桥在编辑器多次崩溃后不再重连** | 编辑器活着、MCP RESULT=OK、preview start 返回 success，但 `pages` 永远超时 | 现阶段无自动修复手段（重开编辑器/重装预览都试过不行）；直接在报告标"该屏本轮无法复采"，别无限重试烧时间。结构性解法是把游戏渲染挪出编辑器进程（browser 预览），harady `debug_preview` 未暴露该开关，需另行验证 |

## 判定分类学（回写用，勿发明新类型）

- **✔ 已修复**：问题在当前构建不复现（注明是哪次变更修复的，若可归因）
- **✗ 仍存在**：复现；若表现形态变了（如 `{0}` 占位符外露 → 昵称为空），写**形态变化**
- **🔄 已重构**：该界面整体重做，旧问题清单作废，按新界面重新评审（旧条目不逐条改状态）
- **⚠ 需确认**：证据不足（截图落在错误界面 / 需真实数据 / 需人工确认配置）

## 报告回写（非破坏模式）

- 在报告 `<h1>` 后注入**复核横幅**：复核日期、方式（MCP 实拍）、工程版本、采集语言、
  结论速览（逐项带 ✔/✗/🔄/⚠ 徽标）、新截图目录。
- 给已复核屏的 `<h2>` 标题追加**状态标签**（inline style 徽标，颜色：绿=修复/红=仍存在/蓝=重构/橙=待确认）。
- **不改动原始问题条目**、不内嵌新截图（避免数 MB 文件膨胀），新截图以目录引用。
- 原始清单条目与回写标签冲突时，以标签为准并在横幅声明"标签优先"。

## 泛化脚本（本模块 scripts/）

| 脚本 | 用途 | 关键参数 |
|---|---|---|
| `mcp_http.py` | MCP-over-HTTP 客户端（握手/会话/SSE 解析） | `--url`（默认 `http://127.0.0.1:3000/mcp`） |
| `artdiff_probe.py` | 预览启动 + 桥三连探测 | `--url` |
| `artdiff_runtime_shots.py` | 逐屏实拍（自愈+残留清理+黑边裁切） | `--url --out --pages-json --only --redo --max-width` |
| `artdiff_reaudit_html.py` | 报告回写（横幅+状态标签） | `--report --banner-html --chips-json` |

界面清单（PAGES/ROOT_OF/NEVER_KILL/EXTRA_KILL）是**项目事实**，放 `--pages-json` 传入，不写死在脚本里。
