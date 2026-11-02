---
name: cocos-reverse-engineering
description: Use when 用户要反编译、解包、恢复或检查 Cocos Creator 2.x/3.x 构建，包括 Android APK/split、JSC/XXTEA、HEK 多版本资源、PKM、Spine/DragonBones、JSB 运行时补丁、广告/埋点隔离和真机回归。非 Cocos 构建先做引擎识别再移交。
version: 2.4.0
created: "2026-08-01"
updated: 2026-09-06
author: bai-lian
tags: [cocos, cocos-creator, reverse-engineering, decompile, jsc, xxtea, hek, xor, pkm, etc1, apk, spine, dragonbones, game-engine, unity, il2cpp, athena, hisavana, aidl, analytics]
triggers: [反编译 cocos, cocos 逆向, cocos creator 逆向, 解包 cocos, 提取 cocos 资源, 解密 jsc, xxtea jsc, cc-reverse, 重建 cocos 工程, cocos 游戏逆向, 提取 cocos 精灵, decompile cocos, unpack cocos, extract cocos assets, rebuild cocos project, 不是 cocos, unity il2cpp, 雷电模拟器, split 包, HEK, XOR, v03 加密, PKM, ETC1, pkm 转 png, 资源解密, 合并损坏, spine 完整性]
---

# Cocos Creator Reverse Engineering

## 执行卡（先用这张卡，再读正文）

**我管什么**：把已编译的 Cocos Creator 构建（2.3.x / 2.4.x / 3.x）还原成可编辑工程——脚本、场景、资源、meta，含 XXTEA `.jsc`、HEK 资源解密、PKM 转换和完整性验收。不管非 Cocos 构建（先做引擎识别）。

**第一步做什么**：跑 `bash scripts/check-deps.sh`，补齐其中 `INSTALL_REQUIRED:` 列出的依赖（`bash scripts/install-dep.sh <依赖>`），再跑 `bash scripts/detect-project.sh <构建目录>` 拿到 `ENGINE=` 那一行。

**做完怎么算完成**：
- [ ] `ENGINE=` 有明确值（`2.3.x` / `2.4.x` / `3.x`），不是 `unknown`
- [ ] `ENCRYPTED=yes` 时已有 `KEY=`（来自 `bash scripts/find-jsc-key.sh`）或用户提供的 key，二者都没有则已停下询问用户
- [ ] `bash scripts/unpack-cocos.sh` 已产出 `RECOVERY_REPORT.md`，其中失败解码的资源逐条列出
- [ ] `python scripts/verify_assets.py --project <目录> --out report.json --extract-skeletons` 通过：PNG 0 damaged、每个 `.atlas` 有配对且类型正确的 `.json`
- [ ] 输出五件套齐全：还原工程、引擎摘要、资源清册、脚本清单、完整性报告 `report.json`

**红线（不可违反）**
- 先读 `HEK:` 后面的头/版本字节再解密，不许把所有 `HEK:` 一律当 v03；v01、AFFA 包装等其他变体走各自已验证的项目路径。
- `modules/cocos-reverse-engineering/scripts/decrypt_v03_resources.py` 只对确认是 HEK:XOR v03 的文件使用。
- 原始密文必须保留，解密产物写到独立目录，不许原地覆盖。
- 找不到 key 就停下问用户，不许猜 key、不许暴力尝试。
- 未确认真是 Cocos（`ENGINE=unknown`）时，禁止对目标跑 `cc-reverse`。
- 完整性验收以 `verify_assets.py` 的逐项证据为准，不许用文件数量代替验收。

**卡住时按顺序读**：
- 依赖装不上 / 环境不通 → `modules/cocos-reverse-engineering/references/setup-guide.md`、`modules/cocos-reverse-engineering/references/local-environment.md`
- 布局识别不出 / 到底是 2.x 还是 3.x → `modules/cocos-reverse-engineering/references/cocos2x-format.md`、`modules/cocos-reverse-engineering/references/cocos3x-format.md`
- 解密失败 / key 找不到 → `modules/cocos-reverse-engineering/references/jsc-decryption.md`、`modules/cocos-reverse-engineering/references/cocos-formats.md`
- 验收不过 / 合并 JSON 损坏 / PKM → `modules/cocos-reverse-engineering/references/completeness-checklist.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

Scope: `GENERAL_DEFAULT` plus selected `GENERALIZED_PATTERN` references. Files whose names contain `blockmaster` and the 10.4.7 SDK-injection case are `CASE_ONLY_BLOCKMASTER`; consult the root `references/scope-map.md` before loading them.

Recover the editable project (scripts + scenes + assets + meta) from a compiled Cocos Creator build. Supports **Cocos Creator 2.3.x / 2.4.x** (the `src/project.js` + `res/` layout and the `main.js` + `assets/` layout) and **Cocos Creator 3.x** (the `assets/main/` bundle layout with `config.json` + `import/` + `native/` + `cocos-js/`). Handles XXTEA-encrypted `.jsc` scripts via auto key extraction.

The workflow is driven by [cc-reverse](https://github.com/Crain99/cc-reverse), a Node.js CLI that this skill wraps and extends with engine detection and decryption helpers.

## Prerequisites

This skill requires a Node.js version compatible with the installed `cc-reverse` CLI. Do not rely on a historical minimum alone; run the dependency checker and inspect the installed tool version:

```bash
bash scripts/check-deps.sh
```

If anything is missing, follow `modules/cocos-reverse-engineering/references/setup-guide.md`, or let the install helper handle it:

```bash
bash scripts/install-dep.sh cc-reverse
```

**Windows note**: the helper scripts are bash. On a PowerShell host run them through Git Bash or WSL, and see `modules/cocos-reverse-engineering/references/local-environment.md` for machine-specific paths (installed editors 2.4.13 / 3.8.7) and shell workarounds.

## Workflow

### Phase 0: Acquire the Android build (APK / split packages)

When the target is an Android APK (e.g., exported from an LDPlayer/雷电模拟器  
installation or `adb shell pm path `):

1. Export `base.apk` and **all** `split_config.*.apk` (x86_64 carries the  
native `so`; zh/xhdpi carries region resources — do not miss them).

1. Unzip each into an `extracted/` directory (unzip/7z).

2. Recognize the engine and encryption variant before the main reverse pass:  
Cocos Creator layouts use `assets/assets/` + `config.json`/`settings.json`  
with the `_packed/` bundle layout. A `HEK:` header identifies only the HEK  
family, not automatically v03; inspect its version bytes and the native  
loader before selecting a decoder. Script encryption may instead show  
`.jsc` (XXTEA, no HEK header).

Reference: `modules/cocos-reverse-engineering/references/cocos-formats.md`.

### Phase 1: Verify and install dependencies

```bash
bash scripts/check-deps.sh
```

The output contains machine-readable lines:

- `INSTALL_REQUIRED:` — must be installed before proceeding (`node`, `cc-reverse`).

- `INSTALL_OPTIONAL:` — nice-to-have (`7z`, `unzip`, `ffmpeg` for audio format conversion).

If required dependencies are missing (exit code 1), install them:

```bash
bash scripts/install-dep.sh <dependency>
```

Re-run the check until everything passes. Do not proceed to Phase 2 until all required dependencies are OK.

### Phase 2: Detect the project layout

Cocos Creator ships three distinct build layouts. Before anything else, identify which one you're looking at — the rest of the workflow branches on this.

**Action**: Run the detector script.

```bash
bash scripts/detect-project.sh 
```

It prints `ENGINE=` (`2.3.x`, `2.4.x`, or `3.x`), followed by key paths (settings, bundles, script entry, asset roots, native dirs) and a list of encryption markers. Machine-readable keys:

- `ENGINE=` — detected engine series.

- `ENCRYPTED=yes|no` — are `.jsc` files present?

- `BUNDLES=` — detected bundle names (3.x only; `main,internal,resources,`).

- `WEB_MOBILE=yes|no` — is this the web-mobile build (has `index.html`)?

The detector looks at:

- `src/settings.js` + `src/project.js` + `res/` → **2.3.x**

- `main.js` + `settings.js` + `assets/` + optional `subpackages/` → **2.4.x**

- `index.html` + `data/` + `assets/main/config.json` + `cocos-js/` + `application.js` + `src/settings.json` → **3.x**

- Web-mobile games packed inside an `index.html` at the root also work — treat the build dir as the root.

- HTML5 builds from a ZIP/WAR need to be extracted first (use `unzip`/`7z`).

**Not Cocos? Stop and identify the engine.** If the detector prints no Cocos  
fingerprints (`ENGINE=unknown`) — no `settings.js`/`project.js`/`main.js`/  
`assets/main/config.json`, no `.jsc` — do NOT run `cc-reverse`. Check for  
Unity IL2CPP fingerprints instead:

- `lib//libil2cpp.so` + `libunity.so` (+ optional `lib_burst_generated.so`)

- `assets/bin/Data/global-metadata.dat` (magic `0xFAB11BAF` — check whether encrypted)

- `assets/bin/Data/data.unity3d` (UnityFS header + version string)

If those hit, follow `modules/cocos-reverse-engineering/references/unity-il2cpp.md` (Il2CppInspectorRedux +  
UnityPy + manifest AXML + signature-level analysis). Mind the shell trap: the  
DEX layers are usually just ads/IAP/Firebase wrappers — the game core is in the  
Unity data. Sibling skill `game-build-engine-identification` covers  
engine-level routing for Cocos/Unity/other engines.

See `modules/cocos-reverse-engineering/references/cocos2x-format.md` and `modules/cocos-reverse-engineering/references/cocos3x-format.md` for detailed layout maps.

### Phase 3: Decrypt resources and JSC (if encrypted)

If Phase 2 reported `ENCRYPTED=yes`, recover the XXTEA key and decrypt before the main reverse pass.

**Action**: Try auto-extraction first; fall back to manual key if the user has one.

```bash
bash scripts/find-jsc-key.sh 
```

This greps `main.js`, `src/main.js`, `application.js`, and `cocos-js/` for known key patterns:

- `xxteaKey = "…"` / `encryptKey = "…"` / `XXTEA_KEY = "…"`

- `key: ""` (Cocos 2.x default is a UUID-shaped string)

- In 3.x, search `src/settings.json` → `assets.encrypted` and `application.js` for the `xxteaKey` variable

- Keys embedded as arrays of bytes (`[0x61, 0x62, ...]`) — the script normalises these back to a string

Expected output: one or more `KEY=` lines. If the key is obvious, `cc-reverse` will find it automatically too; the script is for confirmation and for the cases where cocos-engine ships it as a byte array.

**Resource encryption (HEK variants)** — first classify the header/version  
against known-good samples and the native loader. Only files positively  
identified as HEK:XOR v03 may use the helper below; v01, AFFA-wrapped or other  
variants need their verified project-specific path. Keep the original  
ciphertext and write decrypted output to a separate directory.

For confirmed v03 files:

```bash
python scripts/decrypt_v03_resources.py --src  --dst  --key 
```

It writes `_manifest.json` with per-file SHA1, which later completeness checks  
reuse. For `.jsc` (XXTEA), use the key above with the Python bulk decryptor  
(multi-member gzip handled):

```bash
python scripts/decrypt_jsc.py --src  --dst  --key 
```

If no key is found, ask the user — **don't guess**. Unauthorized decryption of encrypted game assets may be restricted by the software's licence.

Reference: `modules/cocos-reverse-engineering/references/jsc-decryption.md`.

### Phase 4: Run the reverse pass

Drive `cc-reverse` to rebuild the project.

**Action**: Run the unpack wrapper, passing the key if one was found.

```bash
bash scripts/unpack-cocos.sh [OPTIONS] 
```

Options:

- `-o ` — output directory (default: `-extracted`).

- `-k ` — XXTEA key (if Phase 3 produced one).

- `--version-hint 2.3.x|2.4.x|3.x` — force engine version when auto-detection fails.

- `--bundle ` — 3.x only; unpack a specific bundle (`main`, `internal`, `resources`, subpackage name). Default: all bundles.

- `--assets-only` — skip the script pass, only recover assets.

- `--scripts-only` — skip the asset pass, only recover scripts.

- `--verbose` — show per-file progress.

The wrapper runs `cc-reverse` under the hood and then:

1. Copies the recovered `assets/` tree into the output directory.

2. Generates a minimal editor-compatible `project.json` / `package.json` at the root so the result opens in Cocos Creator.

3. Writes a `RECOVERY_REPORT.md` listing engine version, bundle count, script count, and any assets that failed to decode.

For 3.x projects, each bundle is unpacked into its own subdir (`assets/main/`, `assets/resources/`, …) — matching the editor's folder layout when a project is re-imported.

See `modules/cocos-reverse-engineering/references/cc-reverse-usage.md` for the full CLI reference and troubleshooting matrix.

### Phase 5: Inspect and catalogue assets

With the project recovered, navigate and document what's inside.

**Actions**:

1. **Read the entry point(s)**:

- 2.x → `assets/Scripts/.ts` (game bootstrap) and the first entry under `scenes` in `settings`.

- 3.x → `assets/main/` scripts (bundled application) plus `scene/` for `.scene` files. Look at `application.js` / `settings.json` for the launch scene UUID.

1. **Survey the asset tree**:

```bash
bash scripts/find-assets.sh /assets
```

Prints counts of each asset kind (Scene, Prefab, SpriteFrame, AudioClip, AnimationClip, Spine, DragonBones, Material, Mesh, EffectAsset, …) plus total size and any unrecognised file types.

1. **Map scene → prefab → component dependencies**. The `.fire`/`.scene` files reference prefabs and components by UUID; the recovered meta files list each asset's UUID. Trace from the scene root down.

2. **Identify third-party SDKs**. Cocos games commonly bundle analytics/ads SDKs (AppLovin, Unity Ads, Bugly, GameAnalytics). These usually sit in `assets/Scripts/` as large `.ts` files with recognisable API names.

- `modules/cocos-reverse-engineering/references/asset-recovery-patterns.md` — grep patterns for scenes, prefabs, sprite frames, Spine, DragonBones, and the per-asset documentation template.

### Phase 6: Rebuild and verify recovered 2.x projects

After Phase 5, re-import the recovered project and verify it end-to-end:

1. **Re-import assets** — every recovered PNG needs a standard 2.4.x texture  
meta (see `modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md` §1). A running editor  
re-imports changed PNGs and normalizes the metas automatically; keep the  
texture UUIDs stable so scene references survive.

1. **Runtime-built UIs** — a "single scene + one boot component" build keeps  
the real scene graph in the boot script, not in the `.fire`/prefab JSON.  
Catalogue the nodes from the script and the `cc.resources.load` paths it  
uses (§6 of the reference).

1. **Rebuild via CLI** — `CocosCreator.exe --path  --build
``"platform=web-mobile;debug=true"` works while the editor is open; trust the  
`Built ... successfully` log line, not the exit code (§4).

1. **Headless QA** — drive the built page over Chrome CDP  
(`Runtime.evaluate` with `returnByValue`, `node.emit('click')`), and verify  
visuals with screenshots + pixel analysis. Mind UTF-8 Chinese node names in  
`cc.find` paths (§5).

The 2.4.x engine quirks that most often break recovered/runtime-built UIs —  
`Sprite`+`Label` node conflict, `label.color` vs `node.color`, Label  
auto-size overriding node size, trimmed-frame offsets — are documented in  
`modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md` §3.

### Phase 7: Repair, convert and verify completeness (merged from cocos-reverse)

After the reverse pass, run the Python helpers in `scripts/` (validated on  
real projects, e.g. com.block.juggle: 9948+ files, 82 Spine atlases):

1. **Fix mangled merged JSON** — cc-reverse may merge several same-path assets  
(SkeletonData + atlas native cc.Asset + SpriteFrame) into one corrupt json  
(`json.loads` fails with `Extra data`). Rewrite them from the decrypted  
source by uuid:

```bash
python scripts/restore_skeleton_data.py --project  --decrypted 
```

1. **Convert ETC1 PKM to PNG** — Creator 2.x textures may ship as `.pkm`  
(ETC1). Convert in place:

```bash
python scripts/pkm_to_png.py --root 
```

1. **Completeness verification (mandatory, not just file counts)**:

```bash
python scripts/verify_assets.py --project  --out report.json --extract-skeletons
```

Checks: every `.png` decodes with Pillow (0 damaged); every `.atlas` has a  
companion `.json` that is `sp.SkeletonData` (Spine) or `cc.SpriteFrame`  
(plain atlas); SkeletonData attachment names resolve in the atlas text or a  
project-wide atlas index (`--write-combined-atlas` merges multi-atlas  
skeletons); unused-skin "dead references" are reported, not counted as  
missing.

1. **Font completion** — SHA1-compare the native dir with the project tree and  
copy missing `.ttf` into `_packed//`.

The full acceptance checklist is in `modules/cocos-reverse-engineering/references/completeness-checklist.md`.

## Output

At the end of the workflow, deliver:

1. **Recovered project** in the output directory, structured as a regular Cocos Creator project (`assets/`, `project.json`, per-asset `.meta`).

2. **Engine summary** — detected version, bundle count, encryption status, key (if any).

3. **Asset catalogue** — counts by type, total size, list of any assets that couldn't be decoded.

4. **Script inventory** — recovered `.ts`/`.js` files grouped by package prefix, with SDK dependencies called out.

5. **Completeness report** — PNG decode / Spine-DragonBones attachment coverage / PKM conversion results (`report.json`).

## References

- `modules/cocos-reverse-engineering/references/setup-guide.md` — installing Node, `cc-reverse`, and optional tools.

- `modules/cocos-reverse-engineering/references/cc-reverse-usage.md` — `cc-reverse` CLI reference and `cc-reverse.config.js` options.

- `modules/cocos-reverse-engineering/references/cocos2x-format.md` — 2.3.x and 2.4.x build layout, `CCSettings`, compressed-type array format, `res/` tree.

- `modules/cocos-reverse-engineering/references/cocos3x-format.md` — 3.x build layout, bundle `config.json` schema, `import/`/`native/` paths, CCON and packed formats.

- `modules/cocos-reverse-engineering/references/jsc-decryption.md` — XXTEA key locations, byte-array keys, gzip post-processing, why decryption sometimes fails.

- `modules/cocos-reverse-engineering/references/asset-recovery-patterns.md` — grep patterns for scenes, prefabs, sprite frames, Spine, DragonBones, and the per-asset documentation template.

- `modules/cocos-reverse-engineering/references/local-environment.md` — machine-specific facts: installed editor paths (2.4.13 / 3.8.7), Windows/PowerShell execution notes, per-agent skill locations.

- `modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md` — 2.4.x texture meta format, runtime `resources.load`, engine quirks (Sprite/Label conflicts, tint, auto-size, trim offsets), CLI build automation, headless CDP QA, and the "single scene + runtime-built UI" architecture.

- `modules/cocos-reverse-engineering/references/unity-il2cpp.md` — non-Cocos (Unity IL2CPP) handoff: detection fingerprints, Il2CppInspectorRedux/UnityPy workflow, and the Easybrain Sudoku peripheral-system case study (LiveOps events / recurring modes / push / remote config).

- `modules/cocos-reverse-engineering/references/cocos-formats.md` — HEK:XOR v03 资源加密、JSC XXTEA 多成员 gzip、ETC1 PKM、Cocos 序列化数组、Spine/DragonBones 内嵌格式。

- `modules/cocos-reverse-engineering/references/completeness-checklist.md` — 完整性验收清单与常见坑（解密/重建/美术/报告逐项证据）。

- `modules/cocos-reverse-engineering/references/android-boot-stuck-diagnosis.md` — 原生 Android Cocos JSB 游戏启动卡 loading 排查：JS 引导链文件标记插桩（writeStringToFile 参数顺序）、settings 哈希错配、HEK/明文混用、GLThread 假死锁误判、frida-on-houdini 限制、apktool smali_assets 重建坑。

- `modules/cocos-reverse-engineering/references/android-reskin-repack.md` — Android 换皮/重基打包：版本重基工作流、split ABI 版本匹配（RN 模块化 vs 单体崩溃案例）、离线远程内容内置（SeedCopier 模式）、extractNativeLibs=false 构建链（.so STORED + zipalign -p）。


- `modules/cocos-reverse-engineering/references/android-blockmaster-moregames-settings.md` — BlockMaster full/lite 双包实战：More Games 按钮/弹窗彻底清除（主 JS + 远程 patch 双改、GameLobbyAddMoreGame 无条件隐藏、HomePage/Setup 递归按名隐藏、showMiniGameList no-op）、小游戏资源双目录删除、More Settings 弹窗类缺失修复（MoreSettingActivity + MoreSettingsBridge 自定义 dex + NativeBridge 指定目标类）、热更缓存 install -r 覆盖坑与 assets/main.js 禁用 patch 搜索路径、Play Store versionCode>1015+正式签名覆盖约束。

- `modules/cocos-reverse-engineering/references/android-blockmaster-v31-ad-resource-and-ui-removal.md` — BlockMaster V30/V31 实战：Hisavana DEX 合入但资源缺失导致 TAdInterstitialActivity 透明卡死、R 类资源 ID 重映射、Windows N0/n0 大小写碰撞、HEK:XOR v03 保头修改、No Space/More Games/评分移除、启动期 patch sanitizer、V30/V31 构建链与静态门禁。

- `modules/cocos-reverse-engineering/references/android-athena-aidl-loop-and-upload-verification.md` - Athena main/remote-process misclassification, AIDL self-loop diagnosis, test-vs-production endpoints, DB/upload/server proof, Drift_Sand envelope lookup, Frida/Houdini limits, controlled DEX overlays, and mediation-vs-supplier ad attribution.

- `modules/cocos-reverse-engineering/references/android-blockmaster-v35-vendor-isolation-and-real-device-qa.md` — Block Master V35 原厂联网隔离实战：运行参数绕过静态 URL 替换、双 JS/Seed 同步、schema-compatible inert response、SafeDK/APM/Bugsnag 交付层关闭、Hisavana 聚合归属判断、Athena 内容净化、DEX overlay 构建边界、Seed 完整性与真机 DNS/TLS/HTTP 抓包验收。

- `modules/cocos-reverse-engineering/references/android-cocos-lifecycle-trait-and-release-qa.md` — Cocos JSB 本地 trait 生命周期、清屏材质/特效所有权与时序、双 JS 迁移、广告自动结算、DEX 槽位保护、debug/release 签名边界、清装与 Git 交付门禁。

- `modules/cocos-reverse-engineering/references/android-blockmaster-runtime-effects-ads-regression.md` — BlockMaster 离线运行时回归手册：引导完成态、Replay 去重、材质与全组特效原子提交、双重变色、特殊材质就绪、广告/Banner/埋点证据、低端机降级和三块可解保护。

- `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md` — V118-V124 预消除/特殊材质回归复盘：原版 owner、禁止全局清理、异步 prepare 与稳定边界 commit。

## 版本记录

完整版本史见 `references/changelog.md`（模块级）；总集级行为变更见根 `references/CHANGELOG.md`。

## 原生加载器 / JNI / 加壳分流（按需）

Java/JNI 薄壳、加密资源 loader、匿名 native inner 或惰性 DEX 导致静态证据不足时，读 [原生代码取证](../../references/native-code-evidence.md) 与 [运行时恢复门禁](../../references/protected-runtime-recovery.md)。保留本模块 JS/资源恢复链，不把动态 DEX 恢复等同于游戏逻辑还原。
