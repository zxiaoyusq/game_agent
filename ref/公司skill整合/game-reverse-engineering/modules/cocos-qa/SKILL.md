---
name: blockudoku-cocos-qa
description: Use when 用户要对 Cocos Creator 项目执行构建、打包、模拟器/真机安装、拖拽实测、截图、日志、网络或交付验收，修复/验收 Spine 特效错色、错图、不播放、完成点崩溃与层级遮挡，或审计每关图片与配文/出处的结构和语义映射并制作可回写配置表或本地关卡编辑器。本模块保留 Blockudoku 2.4.13 案例，但所有路径、设备、检查数量和工具版本必须在当前会话重新发现。
---

# Blockudoku Cocos QA

## 执行卡（先用这张卡，再读正文）

**我管什么**：Cocos Creator 项目的构建 → 打包 → 模拟器/真机安装 → 拖拽实测 → 截图/日志/网络 → 交付验收全流程，外加 Spine 特效错色/错图/不播/遮挡修复验收、关卡图片与配文/出处的结构与语义双层审计；引擎识别、通用逆向解包、换皮走 engine-identification / cocos-reverse-engineering / skinning-pipeline，不在本模块。

**第一步做什么**：按 `modules/cocos-qa/references/build-cocos.md` 与 `modules/cocos-qa/references/web-qa.md` 建 `web-mobile`，用 `modules/cocos-qa/scripts/start_qa.ps1` 起静态服务器 + CDP 无头 Chrome，再跑当前测试清单对应的 `modules/cocos-qa/scripts/qa_driver.js` 与 `modules/cocos-qa/scripts/qa_drag_v2.js`。

**做完怎么算完成**：
- [ ] 起服务前已确认固定 HTTP/CDP 端口不在 Windows/Hyper-V excluded range
- [ ] 服务器进程存活，首页 HTTP 200，运行态 `System`/`cc` 已初始化
- [ ] CDP 视口强制 720x1280 且已 reload，画布没有黑边
- [ ] 驱动脚本跑完，产出的截图不是浏览器错误页
- [ ] 没有把"脚本退出 0 / 生成了 PNG"当成 PASS

**红线（不可违反）**
- `CASE_ONLY_BLOCKUDOKU`：本模块脚本、工程路径、包名、MuMu 端口与工具版本都是 Blockudoku 夹具；新项目必须先在当前会话重新发现全部路径/设备/参数，只借鉴验收结构。
- 结构 PASS 不能代替语义 PASS：关卡图片、显示顺序、标题/配文、出处、多语言键必须过语义层，缺一即不通过。
- 服务启动后任一断言（进程存活 / 首页 200 / `System`+`cc` 初始化）不成立时，整轮截图证据作废。
- Gradle 前设好 `NDK_ROOT`/`ANDROID_SDK_ROOT`/`JAVA_HOME`，并先删 `app\build\intermediates\assets\release`，否则 APK 打包进陈旧 `index.js`。
- 开头的 `EPERM ... CocosCreator.log` 是良性报错，不要当成失败。
- 不向技能内分发原始解包 APK 资产，只保留路径与尺寸比例。

**卡住时按顺序读**：
- 构建或引擎内验收卡住 → `modules/cocos-qa/references/build-cocos.md`
- Web/CDP 或拖拽卡住 → `modules/cocos-qa/references/web-qa.md`
- Android 打包、MuMu 安装/截图卡住 → `modules/cocos-qa/references/android-mumu-qa.md`
- 截图与交付卡住 → `modules/cocos-qa/references/vision-check.md`；Spine 特效 → `modules/cocos-qa/references/spine-fx-repair-qa.md`；图片↔配文映射 → `modules/cocos-qa/references/content-image-mapping-qa.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

> **CASE_ONLY_BLOCKUDOKU 警告**：本模块的脚本与环境值是 Blockudoku 项目验收夹具，硬编码工程路径、包名、MuMu 端口和工具版本。新项目**不要**直接执行本模块脚本：先走 engine-identification / cocos-reverse-engineering / skinning-pipeline 等通用模块，再回来借鉴本模块的验收结构，并在当前会话重新发现全部路径、设备与参数。

范围：主构建脚本为 `CASE_ONLY_BLOCKUDOKU`；`modules/cocos-qa/references/spine-fx-repair-qa.md` 与
`modules/cocos-qa/references/content-image-mapping-qa.md` 为 `GENERALIZED_PATTERN`。其他项目只能借鉴
验收结构，必须重新发现路径、资源版本、字段和参数。

Run the full acceptance pipeline for the Cocos Creator 2.4.13 Blockudoku project:  
source project `E:\gameprogram\Blockudoku`, deliverables copied to the session  
`outputs` folder. Follow the pipeline in order and read the matching reference  
before each stage.

## Pipeline

1. **Web build + headless QA** (fast loop): build `web-mobile`, then run the  
headless Chrome CDP driver（以当前测试清单为准）+ real drag, then screenshot  
acceptance. See `modules/cocos-qa/references/web-qa.md` and `modules/cocos-qa/references/build-cocos.md`.

1. **Android build + MuMu acceptance**: build `android` (jsb-link), package the  
APK with Gradle, install to MuMu via adb, launch, and screencap. See  
`modules/cocos-qa/references/android-mumu-qa.md`.

1. **Vision acceptance + delivery**: verify screenshots (native vision, or the  
vision-analysis skill when the model cannot see images), then sync  
deliverables. See `modules/cocos-qa/references/vision-check.md`.

## Reference navigation

- `modules/cocos-qa/references/build-cocos.md` - launch Cocos Creator in GUI, in-engine  
acceptance steps, CLI builds for `web-mobile` and `android`.

- `modules/cocos-qa/references/web-qa.md` - start_qa.ps1, the current `qa_driver.js`, the real  
drag probe `qa_drag_v2.js`, expected outputs, screenshot naming.

- `modules/cocos-qa/references/android-mumu-qa.md` - Gradle env, the stale `mergeAssets` cache  
fix, APK content verification, MuMu install/launch/screencap, error table.

- `modules/cocos-qa/references/vision-check.md` - screenshot acceptance prompts, vision skill  
fallback, `sync_delivery.ps1` and the outputs layout.

- `modules/cocos-qa/references/spine-fx-repair-qa.md` - Spine 错色/错图/不播/遮挡的资产、运行时、Web、
  MuMu/真机与 APK 包内数据验收闭环。

- `modules/cocos-qa/references/content-image-mapping-qa.md` - 关卡图片、显示顺序、标题/配文、出处和多语言键的
  结构/语义双层审计，以及可回写配置表或本地编辑器的安全实现与产物复验。

- `assets/content-mapping-editor/` - 可复制到项目 `working` 目录的无依赖 HTML 编辑器模板。动态发现新增关卡，用自然语言引导美术逐关审核，草稿与正式写回分离。

## Historical Blockudoku environment (discover and verify each session)

- Cocos Creator: `${COCOS_2X}\CocosCreator.exe` (2.4.13)

- Project: `E:\gameprogram\Blockudoku` (engine `cocos-creator-js` 2.4.13)

- Work dir: use the current task workspace; do not reuse the historical `C:\Users\Administrator\...` session path.

- Android SDK / NDK: `${ANDROID_SDK}` / `${ANDROID_NDK}`; JDK 17  
at `E:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot`

- MuMu 12: `F:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe`;  
adb endpoint `127.0.0.1:16384`

- Chrome (headless): `C:\Program Files\Google\Chrome\Application\chrome.exe`

- APK identity: package `org.cocos2d.blockudoku`, launchable activity  
`org.cocos2dx.javascript.AppActivity`

The entries above are case defaults, not universal requirements. Before acting, verify executable existence, connected `adb devices`, package/activity, APK SHA-256, ABI, version, signature and the current test count.

## Non-negotiable gotchas

- CocosCreator logs start with a benign `EPERM ... CocosCreator.log` error  
(locked log file). Ignore it; build continues.

- In the historical Blockudoku CDP QA, force the viewport to 720x1280 **and reload** or the SHOW_ALL  
canvas renders with black letterbox bars.

- Android: set `NDK_ROOT`/`ANDROID_SDK_ROOT`/`JAVA_HOME` before Gradle, and  
delete `app\build\intermediates\assets\release` before `assembleRelease` -  
otherwise the incremental cache packages a stale `index.js` and the APK ships  
old code.

- PowerShell console default encoding is GBK: read UTF-8 text with  
`.read_text('utf-8')` (Python) or `Get-Content -Encoding UTF8`; write long  
scripts to `.ps1`/`.py` files instead of inlining Unicode.

- Keep original unpacked APK assets out of this skill: reference paths and  
size ratios only, never redistribute the original game assets.

- Headless QA 启动前先检查固定 HTTP/CDP 端口是否落入 Windows/Hyper-V excluded range
  （`netsh interface ipv4 show excludedportrange protocol=tcp`）。服务启动后必须断言进程仍存活、
  首页 HTTP 200、运行态 `System`/`cc` 已初始化；任一不成立时截图是浏览器错误页，整轮证据作废，
  不能因脚本退出 0 或生成了 PNG 就判 PASS。

## Scripts

- `modules/cocos-qa/scripts/start_qa.ps1` - start the static server + headless Chrome (CDP).

- `modules/cocos-qa/scripts/qa_driver.js` / `modules/cocos-qa/scripts/qa_drag_v2.js` - the acceptance drivers.

- `modules/cocos-qa/scripts/build_web.ps1` / `modules/cocos-qa/scripts/build_android.ps1` - CLI builds.

- `modules/cocos-qa/scripts/gradle_apk.ps1` - Gradle APK with the cache fix + content check.

- `modules/cocos-qa/scripts/mumu_shot.ps1` - MuMu install, launch, binary-safe screencaps.

## Cocos 编辑器实时通道

Creator 3.8.x 的编辑器操作与中间自检可按 `modules/cocos-mcp-channel/SKILL.md` 执行；2.4.x 或无 MCP 时走本模块文件级/CLI 路径。预览、编辑器引用检查和正式构建/设备验收分别记录证据。
