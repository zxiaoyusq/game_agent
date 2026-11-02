# cocos-reverse-engineering 版本记录

> **何时读我**：哥哥要追溯本模块某能力是哪一版加进来、或想知道当前流程对应哪个版本时。
> **读完能做到**：按版本号查每轮新增能力与出处，判断当前做法是否过期。
> **范围**：`GENERAL_DEFAULT`

- **2.4.0 (2026-09-06)** — Restored the referenced `modules/cocos-reverse-engineering/scripts/install-dep.sh` from the older Claude harness and fixed the dependency-install command placeholder. The script is syntax-checked before multi-harness release.

- **2.2.0 (2026-08-26)** — Corrected HEK routing so `HEK:` is not treated as v03 by default; linked the V123/V124 owner-lifecycle and stable-boundary regression reference.

- **2.1.0 (2026-08-25)** — Added `modules/cocos-reverse-engineering/references/android-blockmaster-runtime-effects-ads-regression.md`: evidence hierarchy, guide-state source of truth, non-blocking Replay, atomic PresentationBundle ownership, material readiness, ad/Banner recovery, low-end degradation, solvability guard, and strict regression matrix.

- **2.0.0 (2026-08-24)** — Added `modules/cocos-reverse-engineering/references/android-cocos-lifecycle-trait-and-release-qa.md`: lifecycle trait ownership/event-order rules, migration-safe dual-JS updates, ad settlement verification, DEX-slot isolation, signature-safe device installation, and delivery evidence.

- **1.9.0 (2026-08-20)** — 新增 `modules/cocos-reverse-engineering/references/android-blockmaster-v35-vendor-isolation-and-real-device-qa.md`：沉淀 V35 原厂联网隔离和真机验收经验，包括动态 trait URL 绕过、兼容成功响应、隐藏 SDK 初始化、Bugsnag 兼容骨架与交付层隔离、Athena 诊断字段净化、Seed 门禁及 PCAP 验收。

- **1.8.0 (2026-08-19)** - Added `modules/cocos-reverse-engineering/references/android-athena-aidl-loop-and-upload-verification.md` for Athena AIDL loops, four-level upload proof, environment separation, safe startup correction, and runtime ad ownership checks.

- **1.7.0 (2026-08-20)** — 新增 `modules/cocos-reverse-engineering/references/android-blockmaster-v31-ad-resource-and-ui-removal.md`：Hisavana 广告资源缺失导致全屏广告透明卡死、R 类资源 ID 重映射、Windows N0/n0 大小写碰撞规避、HEK:XOR v03 保头修改、No Space/More Games/评分移除、启动期 patch sanitizer、V30/V31 构建链与静态门禁。

- **1.6.0 (2026-08-18)** — 新增 `modules/cocos-reverse-engineering/references/android-blockmaster-moregames-settings.md`：BlockMaster full/lite 双包实战（More Games 主界面+设置弹窗彻底清除且双 JS 同步、小游戏资源双目录删除、MoreSettings 原生弹窗类缺失自定义 dex 恢复、热更缓存 install -r 覆盖坑与 main.js 禁用 patch 搜索路径、Play Store versionCode>1015+正式签名覆盖约束）。

- **1.5.0 (2026-08-14)** — 新增 `modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md`：BlockMasterPro 10.4.7 换皮+hisavana/athena 注入实战踩坑（真机 ART vs 模拟器 IllegalAccessError/VerifyError、JS↔Java 桥接改道与回调契约、重启模式热更/RN 崩溃、SDK shim、hisavana 接入规范）。

- **1.4.0 (2026-08-13)** — 新增 Android 启动卡 loading 排查手册（BlockMasterPro/Block Blast 案例：settings 哈希错配静默中断、文件标记插桩、GLThread 假死锁误判、frida-on-houdini）与 Android 换皮/重基打包手册（版本重基、split ABI 匹配、SeedCopier 离线内容内置、extractNativeLibs=false 构建链）。

- **1.3.0 (2026-08-10)** — 并入旧 `cocos-reverse` 独立 skill：新增 APK（含 split 包/雷电模拟器）提取、HEK:XOR v03 资源解密（decrypt_v03_resources.py）、.jsc 批量解密（decrypt_jsc.py）、ETC1 PKM→PNG（pkm_to_png.py）、重建合并损坏修复（restore_skeleton_data.py）与 Spine/DragonBones 附件完整性验证（verify_assets.py）；新增 `modules/cocos-reverse-engineering/references/cocos-formats.md` 与 `modules/cocos-reverse-engineering/references/completeness-checklist.md`。

- **1.2.0 (2026-08-04)** — Phase 2 now routes non-Cocos targets: added  
`modules/cocos-reverse-engineering/references/unity-il2cpp.md` (Unity IL2CPP detection, toolchain, and the  
Easybrain Sudoku peripheral-system extract: LiveOps events / recurring  
modes / push / remote config) from the Sudux APK peripheral-extract project;  
added `unity`/`il2cpp` tags and a `不是 cocos` trigger.

- **1.1.0 (2026-08-04)** — added Phase 6 (rebuild \& verify) and  
`modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md` from the Sudux 2.4.13 rebuild  
project; bumped version and added `updated` frontmatter field.
