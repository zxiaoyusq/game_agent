# game-reverse-engineering 部署说明（可移植版）

本 skill 包已做**路径可移植化**处理。原技能里的所有环境/工具/8端同步的绝对路径，
已替换为 `${VAR}` 占位符；案例历史路径保留原文（它们是历史证据，不是运行时依赖）。

## 一、部署到哪里

把 `game-reverse-engineering/` 整个目录放到你的任一 harness 技能目录：

| 工具 | 放置路径（Windows） |
|---|---|
| Claude Code | `C:\Users\<you>\.claude\skills\game-reverse-engineering` |
| Codex | `C:\Users\<you>\.codex\skills\game-reverse-engineering` |
| OpenCode | `C:\Users\<you>\.config\opencode\skills\game-reverse-engineering` |
| DSH | `C:\Users\<you>\.dsh\skills\game-reverse-engineering` |
| GW / ZCode | `C:\Users\<you>\.zcode\skills\game-reverse-engineering` |
| 共享技能池 | `<你的技能池>\skills\game-reverse-engineering` |

放置后用你 harness 的技能列表确认能加载（每个工具有自己的技能加载验证方式）。

## 二、必须配置的环境占位符

以下占位符出现在`${VAR}`位置，**部署后必须把它们替换成你第二台电脑上的真实绝对路径**，
否则对应脚本/工具无法找到可执行文件。

**推荐做法**：把本目录下的 `env.example` 复制为环境的真实配置，
或在当前 PowerShell 使用 `$env:变量名 = "真实路径"`，也可通过 Windows 环境变量设置。`.env` 不会自动加载。

| 占位符 | 本机路径 | 指向 |
|---|---|---|
| `${COCOS_2X}` | `E:\Gameprogram\CocosCreator_2.4.13` | Cocos Creator 2.x 安装目录 |
| `${COCOS_3X}` | `E:\Gameprogram\CocosCreator_3.8.7` | Cocos Creator 3.x 安装目录 |
| `${COCOS_DASHBOARD}` | `D:\CocosDashboard` | Cocos Dashboard 安装目录 |
| `${ANDROID_SDK}` | `E:\AndroidSdk` | Android SDK 根目录 |
| `${ANDROID_NDK}` | `E:\AndroidSdk\ndk\23.2.8568313` | Android NDK（用于构建 APK） |
| `${ANDROID_PLATFORM_TOOLS}` | `E:\AndroidSdk\platform-tools` | adb 等（真机调试） |
| `${ANDROID_BUILD_TOOLS}` | `E:\AndroidSdk\build-tools\34.0.0` | aapt（APK 校验） |
| `${GODOT}` | `E:\Godot\Godot_v4.6.2-stable_win64.exe` | Godot 可执行文件 |
| `${ASSETRIPPER}` | `E:\Gameprogram\tools\AssetRipper\AssetRipper.GUI.Free.exe` | Unity 资产提取 |
| `${IL2CPP_INSPECTOR}` | `E:\Gameprogram\tools\Il2CppInspectorRedux` | IL2CPP 反编译 |
| `${PYLIBS}` | `E:\Gameprogram\tools\pylibs` | Python 第三方库（UnityPy 等） |
| `${SPINE_VIEWER}` | `E:\program\Spine\SkeletonViewer\skeletonViewer-3.8.99.jar` | Spine 完整验证 |

**⚠️ 注意**：path 分隔符建议全部用正斜杠 `/`，可移植性更好。

## 三、案例历史路径（不需配置，但要知道）

skill 里有大量**旧项目/历史证据路径**，例如：

- `E:\download\sudoku-re`、`E:\codex_apk_work`、`E:\gameprogram\Blockudoku`
- `E:\program\...`、`E:\hermes\...`、`E:\Gameprogram\...` 下的游戏工程

这些是运行过案例留下的**取证记录**，不是运行时依赖。在**新项目上使用时必须重取证，
不得照抄这些路径**（skill 里 `DO_NOT_COPY_LITERAL_VALUES` 规则也这么要求）。

## 四、多端入口（按实际发现）

当前电脑使用 `D:\skills\game-reverse-engineering` 单一维护源，11 个已发现入口通过 Junction 共用，不需要复制。入口与路径以根 `SKILL.md` 的发布表为准；新机器只有存在独立副本时才先合并再同步，并对照全树哈希。

可移植部署保留环境变量约定。PowerShell 构建/QA/Spine 工具脚本调用 `scripts/resolve_environment.ps1` 读取进程环境并验证路径，也接受显式工具参数；目录型变量自动追加工具名，完整文件路径不会重复追加。文档示例 `${VAR}` 不等于 shell 自动展开。旧机器路径仅供历史对照，须检查真实存在性。

## 五、验证部署是否成功

1. 你的 harness 列表里能看到 `game-reverse-engineering`
2. 打开 `SKILL.md` 确认路由表可读
3. 临时把 `engine-identification` 模块的执行流程跑一遍（任意引擎识别），确认不报「找不到 ${VAR}」