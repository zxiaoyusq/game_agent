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

## 每次游戏项目开始前的更新检查

1. 对 A/B 中标注 git 仓库的目录执行 `git fetch` + 看 ahead/behind；**有更新且工作树干净 → pull → 同名字典文件同步到各 skill 副本端**。
2. 本地有改动时：先 `git diff` 判断是否保留；保留则记入 landing-log，再决定是否合并上游。
3. 只改路由/注册表时不 bump 外部技能版本；影响 skill 行为的内容变更须记入对应总集"版本说明"。
