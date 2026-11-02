# Local environment (this machine)
> **何时读我**：要装或查本机逆向工具环境、要确认本机装了哪些 Cocos 编辑器、要弄清 `scripts/` 下的 bash 脚本在 Git Bash / PowerShell 下该怎么跑，或要定位各 coding agent 的技能安装目录时。
> **读完能做到**：知道本机 2.4.13 / 3.8.7 编辑器各自该开哪个版本的还原工程，按本机 shell 规则正确执行脚本，并在各 agent 的技能根目录之间做路径替换。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_LOCAL_MACHINE`

Machine-specific facts for the Cocos Creator reverse engineering workflow on this  
Windows workstation. Verified 2026-07-30.

## Installed Cocos Creator editors

| Version | Install path | Executable |
|---|---|---|
| Cocos Creator 2.4.13 | `${COCOS_2X}` | `${COCOS_2X}\CocosCreator.exe` |
| Cocos Creator 3.8.7 | `${COCOS_3X}` | `${COCOS_3X}\CocosCreator.exe` |

Use these to open a recovered project after Phase 4:

- Recovered **2.x** projects → open with **2.4.13**. `cc-reverse` writes asset metas  
with `ver: "1.2.7"` (2.4.5-era), so the 2.4.x editor imports them cleanly.

- Recovered **3.x** projects → open with **3.8.7**.

The `version` file inside each install dir shows the Electron runtime version  
(`13.1.4` / `31.3.1`), not the editor version — trust the directory name.

## Shell environment

The host shell is **Windows PowerShell 5.1** — the scripts under `scripts/` are  
bash and will NOT run in PowerShell directly. Execute them via Git Bash or WSL:

```powershell
# Git Bash example
& "C:\Program Files\Git\bin\bash.exe" scripts/check-deps.sh

# or, if WSL is installed
wsl bash scripts/check-deps.sh
```

PowerShell pitfalls already hit on this machine:

- `&&` / `||` are NOT valid statement separators in PowerShell 5.1 — use `;`.

- Inline `powershell -Command "..."` strings containing `$variables` get mangled  
when invoked through an outer bash layer. Write a `.ps1` file and run it with  
`powershell -NoProfile -ExecutionPolicy Bypass -File <script.ps1>` instead.

- `find -printf` (used in `find-assets.sh`) requires GNU findutils — available in  
Git Bash, not in PowerShell's `find`.

## Path variables across coding agents

`SKILL.md` references scripts as relative paths (`scripts/...`, `references/...`)  
— that works everywhere (skills live under the agent's own skills root).  
The old Claude Code style `${CLAUDE_PLUGIN_ROOT}/skills/cocos-reverse-engineering/...`  
only exists in Claude Code plugin contexts. On this machine the skill is installed  
at these locations (one per agent); substitute accordingly:

| Agent | Skill root |
|---|---|
| WorkBuddy（本机维护源） | `${HARNESS_WORKBUDDY}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| 共享 Agent Skills | `${HARNESS_AGENTS}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| Codex | `${HARNESS_CODEX}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| OpenCode | `${HARNESS_OPENCODE}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| DSH | `${HARNESS_DSH}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| Trae | `${HARNESS_TRAE}\game-reverse-engineering\modules\cocos-reverse-engineering` |
| Hermes（旧独立副本，已被总集取代） | `E:\hermes\skills\game-dev\cocos-reverse-engineering` |
| Claude Code（旧独立副本，已被总集取代） | `${HARNESS_CLAUDE}\cocos-reverse-engineering` |

Canonical (source-of-truth) copy on the current user profile:  
`${HARNESS_WORKBUDDY}\game-reverse-engineering`.  
五端同步与哈希校验由根目录 `scripts/validate_skill.ps1 -CompareRoots` 完成，见根 `SKILL.md` §技能发布与同步。

## Related local projects

`E:\Gameprogram` also contains Cocos game projects that may be analysis targets:  
`blockcocos`, `MarbleShooter`, `water_game`, `Yahagames`, plus build output in  
`release_folder20260430152353`.

`E:\Gameprogram\Sudux` is a 2.4.13 web-mobile project with a fully  
runtime-built UI (tiny `Main.fire` + `BootGame` script). Its  
`build/web-mobile` is a clean 2.4.x analysis target, and it is the source of  
the runtime/build/QA knowledge in `modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md`.

## Unity IL2CPP sibling toolchain

When Phase 2 returns `ENGINE=unknown`, the target may be Unity IL2CPP. Installed  
tools (full workflow in `modules/cocos-reverse-engineering/references/unity-il2cpp.md`):

| Tool | Location |
|---|---|
| Il2CppInspectorRedux | `${IL2CPP_INSPECTOR}\` (CLI needs .NET: `E:\Gameprogram\dotnet`) |
| UnityPy 1.25.2 | `${PYLIBS}\` |

`E:\download\sudoku-re\` is the completed Unity IL2CPP analysis workspace for  
Sudoku.com 7.8.0 (stub dump, asset export, peripheral-system extracts, full  
report `REVERSE_ANALYSIS_REPORT.md`) — reuse its artifacts for sibling-game  
work. It is the source of the knowledge in `modules/cocos-reverse-engineering/references/unity-il2cpp.md`.
