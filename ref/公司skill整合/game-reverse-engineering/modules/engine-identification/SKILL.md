---
name: game-build-engine-identification
description: Use when 用户要逆向、解包或检查未知游戏构建，需要先识别 Cocos Creator、Unity IL2CPP 或其他引擎；也适用于 Cocos 检测返回 unknown，或发现 libil2cpp.so、global-metadata.dat、data.unity3d 等 Unity 指纹时。
version: 1.0.0
created: "2026-08-01"
author: bai-lian
tags: [reverse-engineering, engine-detection, cocos, unity, il2cpp, game-build]
triggers: [识别引擎, 什么引擎, 游戏逆向, 逆向工具链, unity il2cpp, libil2cpp, global-metadata, 解包游戏, 不是 cocos, engine detection]
---

# 游戏构建引擎识别

## 执行卡（先用这张卡，再读正文）

**我管什么**：判断一个游戏构建是哪个引擎做的（Cocos 2.3.x / 2.4.x / 3.x、Cocos 加密、Unity IL2CPP），并据此指定下一条工具链。不管解包、解密和资源提取本身。

**第一步做什么**：宿主内嵌功能先按「宿主 App 内嵌功能」章节确认前台归属；独立构建则打开目标构建目录，对照本文件「指纹对照表」逐行实测——先查 Cocos 四类指纹（`src/settings.js` + `src/project.js` + `res/`、`main.js` + `settings.js` + `assets/`、`index.html` + `data/` + `assets/main/config.json` + `cocos-js/`、`.jsc` + XXTEA 标记），再查 Unity 指纹（`lib/arm64-v8a/libil2cpp.so` + `libunity.so`、`assets/bin/Data/global-metadata.dat`、`assets/bin/Data/data.unity3d`）。

**做完怎么算完成**：
- [ ] 给出受证据支持的引擎/渲染层结论（Cocos / Unity / 宿主自研渲染层等）；宿主页面技术与渲染引擎分开记录，不能确定时明确 unknown 与缺失证据
- [ ] 结论可追溯到目标构建决定性指纹，或宿主目标 Activity/组件与 loader 证据；后台其他应用的视图不算目标证据
- [ ] Unity 命中时已记录 metadata 是否加密，以及 `data.unity3d` 的版本串（如 `6000.3.16f1`）
- [ ] Cocos 三项指纹全空时如实记 `unknown`，不硬凑成 Cocos
- [ ] 已写明下一步交给哪个技能 / 哪条工具链

**红线（不可违反）**
- 先识别引擎、再选工具链：Unity 构建不许跑 cc-reverse。
- `HEK:` 或 `.jsc` 只是加密族线索，不能用来判定引擎。
- 未加密的 IL2CPP metadata ≠ 源码和业务语义全部恢复，不许承诺「能拿到源码」。
- Java/Kotlin 外壳（广告 SDK / 内购）不决定本体引擎，别被外层壳误导。
- 静态字符串不足时不许仅凭字符串判引擎，必须用原生 loader / 组件证据补证。
- 三项指纹全空是正确结果，不许为了「有个结论」而猜。

**卡住时按顺序读**：
- 指纹对不上 / 不知道查哪些文件 → 本文件「指纹对照表」
- 疑似 Unity 但证据不足 → 本文件「路由规则」+ `references/native-code-evidence.md`
- 出现 `HEK:` / `.jsc` 需进一步定性 → `modules/cocos-reverse-engineering/SKILL.md` 的 Phase 2
- Unity 工具链命令与产物 → `modules/cocos-reverse-engineering/references/unity-il2cpp.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERAL_DEFAULT`。文中的 Sudoku.com 路径、版本和资产数量属于 `CASE_ONLY_SUDOKU`。

**先识别引擎，再选工具链。** 逆向一个游戏构建的第一步永远是判断它是什么引擎做的——选错工具链等于白干。已证实案例：Sudoku.com 7.8.0（Easybrain）表面像 Cocos 目标，实际是 **Unity 6000.3.16f1 IL2CPP**，cocos-reverse-engineering 的检测器三项指纹全空、正确返回 unknown，随后改用 Unity 工具链完成同等深度拆解。

## 宿主 App 内嵌功能（非独立 APK）识别

范围：`GENERALIZED_PATTERN`（方法）+ `CASE_ONLY_QQPET`（字面值）。QQ 宠物(Adelie/Ergo)全案见
`references/host-app-embedded-qqpet-case.md`。

目标可能是"宿主 App 里内嵌的小游戏/3D 功能"(如社交 App 内置宠物)，不是独立游戏 APK。此时：

1. **先确认前台窗口归属，再判引擎。** 桌面/后台还开着别的游戏时，`dumpsys activity top` 会把其它窗口的渲染视图混进来（案例：把后台某 Cocos 游戏的 `Cocos2dxGLSurfaceView` 误判为目标引擎）。
   判据链：`topResumedActivity` → `dumpsys window | grep mCurrentFocus` → 目标 Activity 段内(不是整份 dump)的 View Hierarchy。
2. **宿主内嵌 ≠ 独立小游戏。** 资源与代码放在宿主 data 目录(`files/` `cache/` `app_lib/`)，而非自有 APK；页面可能是"动态包 + dex"(案例：Kuikly `kuikly_dynamic.zip` → `*.apk` → `classes.dex`，是 Kotlin 不是 JS)；3D 缓存可能是自研引擎私有格式(案例：Ergo + Filament 的 `.filamat`/`.ktx2`/`zplanlite://`)。
3. **别被单屏视图误导**：同一 Activity 可能混 TextureView/WebView/GL，用 Fragment/反编译类确认真实页面栈。
4. 判断"本地 vs 远程"用三重证据：APK entries 扫描、客户端下载痕迹(etag/manifest)、远程配置中心内嵌模块 JSON(downloadUrl/isLoadFromPresetAssets/diffInfoList)。
5. 拉取清单：宿主远程配置(如 unitedconfig MMKV)里已含每个模块的版本与 CDN 目录模板，比抓包更直接。

典型指纹追加：

| 场景 | 决定性指纹 |
| --- | --- |
| 宿主 App 内嵌 3D 功能(自研引擎) | 前台 Activity = 宿主包内 `…FragmentActivity`；页面 = Kuikly 动态包(apk 内 classes.dex)；渲染 = 自研(案例 Ergo+Filament)；资源 = 宿主 `cache/zplan`+`files/ZRes` |
| 引擎误判陷阱 | 后台独立游戏窗口(Cocos/Unity so/view)混入 activity top，须按窗口/focus 归属过滤 |

## 指纹对照表

| 引擎 | 决定性指纹 |
|---|---|
| Cocos 2.3.x | `src/settings.js` + `src/project.js` + `res/` |
| Cocos 2.4.x | `main.js` + `settings.js` + `assets/` + `subpackages/` |
| Cocos 3.x | `index.html` + `data/` + `assets/main/config.json` + `cocos-js/` + `application.js` |
| Cocos 加密 | `.jsc` 文件 + XXTEA 标记 |
| **Unity IL2CPP** | `lib/arm64-v8a/libil2cpp.so` + `libunity.so` + `lib_burst_generated.so`；`assets/bin/Data/global-metadata.dat`（magic `0xFAB11BAF`，**先查是否加密**）；`assets/bin/Data/data.unity3d`（UnityFS 头 + 版本串，如 `6000.3.16f1`） |

## 路由规则

- Cocos 指纹命中 → `cocos-reverse-engineering` skill（按实际格式选择 cc-reverse、XXTEA 或 HEK 变体处理）。

- Unity 指纹命中 → 不要对 Unity 构建跑 cc-reverse。改用 Unity 工具链：

**Il2CppInspectorRedux**（历史路径 `${IL2CPP_INSPECTOR}\`）→ 导出 dummy DLL、C# 桩代码、il2cpp.json；先验证当前 .NET 与目标 Unity/metadata 版本兼容。

**UnityPy**（历史路径 `${PYLIBS}\`）→ 解 data.unity3d：Sprite/Texture2D、AudioClip、Font、TextAsset；每次记录实际安装版本。

完整案例与产物：`E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md`（Sudoku.com 7.8.0：58k 对象 / 51 类型 / 663 资产 / 12.5MB，导出在 `E:\download\sudoku-re\assets-export\`）。

- 本机已落地的逆向资产目录（E:\\download\\sudoku-re\\）可作为同类手游逆向的素材源：319 Sprite PNG + 156 贴图 + 17 音效 + 7 字体 + 164 文本。

## 关键判断

- **未加密的 IL2CPP metadata 通常可恢复大量类名/方法名/字段名，但不等于源码和业务语义全部恢复。** 优先检查 `global-metadata.dat` 是否加密，再结合对应 `libil2cpp.so`、Unity 版本和工具兼容性判断工作量。

- 游戏外层是 Java/Kotlin 壳（广告 SDK/内购），游戏本体在 Unity 数据里——解包时别被外层壳误导。

- 逆向产物 ≠ 可编辑工程：素材提取后仍需按目标引擎（如 Cocos 2.4.13 复刻）组装场景、挂脚本、连引用，见 Sudux 项目的 sudux-ui-rebuild-plan。

## References

- `E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md` — Unity IL2CPP 全流程逆向报告（引擎指纹、工具链命令、资产导出、变现 SDK 版图）。

- `E:\download\sudoku-re\assets-export\` — 已导出的 663 个官方资产（可直接复用为 UI 素材）。

## 代码执行层与保护层分流

引擎识别与代码/壳身份分别记录：Unity 可能是 Mono 或 IL2CPP；Java/Kotlin 壳、动态 DEX 与原生 loader 不决定本体引擎。metadata 路径还应检查 `Data/Managed/Metadata/`。静态指纹不足时读 [原生代码取证](../../references/native-code-evidence.md)，以真实组件/loader/consumer 补证，不能仅凭字符串判引擎。
