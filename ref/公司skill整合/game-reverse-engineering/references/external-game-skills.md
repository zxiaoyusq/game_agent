# 外部游戏技能注册表 (external-game-skills)

> **何时读我**：需要 Godot 研发、工作流或美术类能力，要确认该技能由哪个外部仓库维护、本机装在哪、怎么更新。
> **读完能做到**：按名加载正确的外部技能而不在本 hub 内复制正文，并对有 git 仓库的目录跑通 fetch/差异判断/同步，避免盲 pull 覆盖本地改动。
> **范围**：`GENERAL_DEFAULT`

用途：`game-reverse-engineering` 是游戏域唯一入口，但 Godot 研发/工作流/美术/工作室内容由各自独立技能维护（避免重复、避免更新冲突）。本表 = **路由 + 来源 + 更新方法**。

加载规则：

- 命中即用 skill("name") **按名加载**；禁止在本 hub 内复制这些技能正文。
- 外部技能内容与版本以各自仓库为准；其自身范围标签同样适用。
- 外部技能的"项目专属证据"永不写入通用技能；需要案例值时记入项目 landing-log 或 `CASE_ONLY_*` 文件。

## A. Godot 研发（GodotPrompter）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/jame581/GodotPrompter |
| 本机克隆 | `${GODOT}/GodotPrompter`（git 仓库，当前 master @ eae755a，2026-08-12，v1.13.0） |
| 引导 | using-godot-prompter（先读） |
| 技能全集 | 2d-essentials 3d-essentials ability-system addon-development ai-navigation animation-system assets-pipeline audio-system beehave camera-system component-system csharp-godot csharp-signals dedicated-server dependency-injection dialogue-manager dialogue-system event-bus export-pipeline gdextension gdscript-advanced gdscript-patterns godot-brainstorming godot-code-review godot-debugging godot-mentor godot-optimization godot-project-setup godot-testing godot-ui hud-system input-handling inventory-system limboai localization math-essentials mobile-development multiplayer-basics multiplayer-sync multithreading particles-vfx phantom-camera physics-system player-controller popochiu procedural-generation resource-pattern responsive-ui save-load scene-organization shader-basics state-machine tween-animation xr-development |
| 更新命令 | `git -C ${GODOT}/GodotPrompter fetch` 先看 ahead/behind；工作树干净时 `git -C ${GODOT}/GodotPrompter pull --ff-only origin master` |
| 同步命令 | 将仓库 `skills/*` 中变更文件复制到 `${HARNESS_WORKBUDDY}`、`.agents/skills`、`.dsh/skills`（只覆盖同名文件，用哈希比对） |
| 注意 | 技能副本是拷贝（非 git），不要手工改 `${GODOT}/GodotPrompter` 之外的副本后反向覆盖；2026-09-04 已拉取 8 提交并同步 |

## B. 游戏工作室 / 流程

| 技能 | 来源 | 本机位置 | 更新 | 本地改动提醒 |
|---|---|---|---|---|
| gstack-game | https://github.com/fagemx/gstack-game | `.dsh/skills/gstack-game`、`.agents/skills/gstack-game` | git fetch → 0 behind 才 pull | .agents 副本有本地改动（skills/*.md 修改），先 `git diff` 再决定 |
| claude-code-game-studios | https://github.com/Donchitos/Claude-Code-Game-Studios | `.dsh/skills/claude-code-game-studios`、`.agents/skills/Claude-Code-Game-Studios` | 同上（上游 2026-05-13 v1.0.0） | .agents 副本大量本地改动（.claude/skills/*），**禁止盲 pull**；.dsh 一个未跟踪 SKILL.md 勿删 |
| superpowers 方法系 | https://github.com/obra/superpowers | 无 git 仓库（仅 using-superpowers 入口 + 各方法技能） | 本机无 git 克隆；更新走官方插件市场/重新 clone（先备份本地改动） | brainstorming / executing-plans / test-driven-development / systematic-debugging / writing-plans / verification-before-completion / requesting-code-review / receiving-code-review / subagent-driven-development / dispatching-parallel-agents / using-superpowers |

## C. 美术/视觉/生图

| 技能 | 来源 | 备注 |
|---|---|---|
| ai-game-art-pipeline-skill | https://github.com/ybuild-ai/ai-game-art-pipeline-skill | `.dsh` 副本 up-to-date；`.agents` 副本领先 1 个本地提交（保留） |
| vision-skills / vision-analysis | 本机 | 截图→UI 还原/OCR/UI 检测 |
| imagegen-frontend-mobile / imagegen-frontend-web / gpt-image-2 / gpt-image-gen | 本机 | 生图/概念图/效果图 |
| writing-skills | 本机 | 技能撰写/验证（本 hub 维护时使用） |

## D. 逆向/QA 姐妹技能（旧目录兼容，内容与本 hub 模块同步）

assetripper-unity-extract → unity-extract；cocos-reverse-engineering；cocos-creator-project-repair；blockudoku-cocos-qa → cocos-qa；db2spine-spine38-qa → dragonbones-spine-convert；vision-device-testing；game-build-engine-identification → engine-identification；huaijiushiguang-pintu（项目专属）。

## E. Phaser（HTML5 web 引擎：官方仓库 / 技能包 / Game Agent MCP）

Phaser 是 HTML5 web 游戏引擎（npm `phaser`，2026-10 实测最新 4.2.1）。指纹识别与下游分流在 `modules/engine-identification/SKILL.md` 的 Phaser 指纹行/路由规则；本节只登记三个外部资源的来源与更新方法，命中即按需加载，不在本 hub 复制正文。

### E-1 phaser4-gamedev（Claude Code 插件 + 可移植技能包）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/Yakoub-ai/phaser4-gamedev（MIT；上游标 Phaser 4.2.1） |
| 本机克隆 | `D:\skills\phaser4-gamedev`（git 浅克隆，2026-10-12 @ 1c1bf45，2026-08-27）。github 直连被重置时用镜像：`git clone --depth 1 https://ghfast.top/https://github.com/Yakoub-ai/phaser4-gamedev` |
| 技能全集 | 26 个 `phaser-*`（各带 SKILL.md）：analyze / animation / architect / asset-advisor / audio / brainstorm / build / coder / debugger / feedback / fx / gameobj / gdd / init / input / matter / migrate / mobile / particles / physics / playtest / release / saveload / scene / tilemap / ui |
| 附属资产 | 5 个 agent 定义（architect/coder/debugger/playtester/asset-advisor）+ 10 个斜杠命令 + 2 个 hooks（PreToolUse 拦截废弃 v3 API、SessionStart 检测 Phaser 工程）+ 无头 Playwright 测试 `skills/phaser-playtest/scripts/playtest.mjs`（黑屏 / 资源 404 / 未捕获异常 / FPS 崩溃） |
| 加载规则 | 本 hub 模式 = 路由 + 本地克隆；按名 skill("phaser-xxx") 加载对应技能，读其 SKILL.md 执行。也可 `npx skills add Yakoub-ai/phaser4-gamedev` 装入当前 harness 技能目录 |
| 更新命令 | `git -C D:\skills\phaser4-gamedev fetch`（origin 指向实际可用的克隆源）→ 看 ahead/behind；工作树干净才 pull |
| 注意 | 技能按 Phaser 4 口径编写（hook 会拦 v3 废弃 API）；v3→v4 迁移用 `phaser-migrate`，官方迁移指南见 E-2，两者冲突以官方仓库为准 |

### E-2 phaserjs/phaser 官方仓库（API 与迁移版本源）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/phaserjs/phaser（v4.2.1；npm `phaser`；仓库自带 `skills/` 目录） |
| 权威入口 | API 文档 docs.phaser.io；示例 phaser.io/examples（2000+）；教程 phaser.io/learn；v3→v4 迁移指南在仓库 `changelog/v4/4.0/MIGRATION-GUIDE.md` |
| 官方 skills | 仓库 `skills/` 目录覆盖场景/物理/输入/动画等子系统 + v3→v4 迁移 skill；按需读原文，不复制进本 hub |
| 用途 | 引擎 API 事实源与迁移依据；与 E-1 `phaser-migrate` 互相印证，冲突时以官方仓库/文档为准。指纹实测基准：3.90.0 与 4.2.1 dist 均含 `VERSION:"x.y.z"` |

### E-3 Phaser Game Agent MCP（云端 Agent 构建通道，付费）

| 项 | 值 |
|---|---|
| 文档 | https://phaser.io/agent/mcp/codex（其他 agent 同构，换 `--tool` 参数） |
| 安装 | `npx @phaserjs/game-agent setup --tool codex`（Node 20+，建议 `npm i -g @phaserjs/game-agent` 保 bridge.mjs 路径有效）；`npx @phaserjs/game-agent manual` 打印填好真实路径的配置（2026-10-12 实测 @phaserjs/game-agent@1.0.0 可运行：未 login 时先提示 "Sign in first: phaser-game-agent login"，打印完整配置需先登录；**npmmirror 镜像尚未同步其 tarball，须加 `--registry=https://registry.npmjs.org`**） |
| 手动配置 | 编辑 `%USERPROFILE%\.codex\config.toml`（**TOML 不是 JSON**）：`[mcp_servers.phaser-game-agent]` 设 command=node 绝对路径、args=bridge.mjs 绝对路径、startup_timeout_sec=120；`[mcp_servers.phaser-game-agent.env]` 设 `PHASER_AGENT_MCP_URL=https://mcp.phaser.io/agent/mcp`、`PHASER_GAME_AGENT_TOKEN=pga_...`（token 在 phaser.io/agent 页生成） |
| 验证 | 配置后完全重启 agent（MCP 只在启动时读取），问 "Check my Phaser Game Agent account"，返回名字与余额即通 |
| 能力/计费 | 云沙箱按分钟计费，图像/音频消耗 credits（官方口径一个完整游戏约 500 credits）；成品可出 Web/Windows/macOS/Linux 包、公开链接与 iframe 嵌入 |
| 红线 | 付费外部服务：接入、生成或调用前必须向用户确认 token 与预算；本 hub 只登记路由与配置方法，不复制其工具面，也不把云端产出当作本地构建验收证据 |

## 每次游戏项目开始前的更新检查

1. 对 A/B/E 中标注 git 仓库的目录执行 `git fetch` + 看 ahead/behind；**有更新且工作树干净 → pull → 同名字典文件同步到各 skill 副本端**。
2. 本地有改动时：先 `git diff` 判断是否保留；保留则记入 landing-log，再决定是否合并上游。
3. 只改路由/注册表时不 bump 外部技能版本；影响 skill 行为的内容变更须记入对应总集"版本说明"。
