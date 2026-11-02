# 端到端总流程（速查）

> **何时读我**：任务刚起步要判断该走哪条链路，或一次命中多个环节、不确定先后顺序。
> **读完能做到**：用指纹表定出引擎与对应模块，并按依赖顺序排出从识别、提取、修复到构建 QA 与真机验收的完整路线，知道每步细节去哪查。
> **范围**：`GENERAL_DEFAULT`

本文件从根 `SKILL.md` 拆出，是"识别 → 提取 → 修复 → 换皮 → 烘焙 → 构建 QA → SDK 替换 → 真机验收"全链路的速查。各阶段细节以对应模块 `SKILL.md` 为准；任务入口路由见根 `SKILL.md` 的「任务意图快速分发」。

多任务同时命中时按依赖顺序组合：`引擎识别 -> 提取/解密 -> 玩法/资源恢复 -> 工程修复 -> 换皮 -> prefab 烘焙 -> 构建与 QA -> 真机视觉验收 ->（重建场景）Godot 迁移 -> 真机验收`。

## 0. 识别引擎

| 引擎 | 决定性指纹 | 路由 |
|---|---|---|
| Cocos 2.3.x | `src/settings.js` + `src/project.js` + `res/` | cocos-reverse-engineering |
| Cocos 2.4.x | `main.js` + `settings.js` + `assets/` + `subpackages/` | cocos-reverse-engineering |
| Cocos 3.x | `index.html` + `data/` + `assets/main/config.json` + `cocos-js/` | cocos-reverse-engineering |
| Cocos 加密 | `.jsc` + XXTEA 标记 | cocos-reverse-engineering（自动提取 key） |
| Unity IL2CPP | `lib/<abi>/libil2cpp.so` + `libunity.so`；`assets/bin/Data/global-metadata.dat`（magic `0xFAB11BAF`，先查是否加密）；`data.unity3d`（UnityFS 头 + 版本串） | unity-extract |
| 引擎未知 | 指纹全空 | engine-identification（先跑检测器再判定） |

外层 Java/Kotlin 壳（广告 SDK/内购）≠ 游戏本体：Cocos 本体在 `assets/`，Unity 本体在 `assets/bin/Data/`，不要被壳误导。

## 1. 提取/解密

- Cocos：Node.js（版本以 `check-deps.sh` 实测为准）装 `cc-reverse`，`bash scripts/detect-project.sh <build>` 检测，加密构建自动找 XXTEA key 解密 `.jsc`，再恢复 meta/场景/精灵帧/音频/动画/Spine/DragonBones。详见 `modules/cocos-reverse-engineering/SKILL.md`。
- Unity：AssetRipper GUI Open Folder → Settings（换皮选 `No Scripts`）→ Export；IL2CPP 代码用 Il2CppInspectorRedux，脚本式提取用 UnityPy。详见 `modules/unity-extract/SKILL.md`。

## 2. 修复/还原

`.fire` 场景自引用/悬空引用导致栈溢出、脚本组件压缩 UUID（`cc._RF.push` 第二参数）、类级 `data:` 属性报错、Play 黑屏（cc.Label 缺 `_materials`、`_spriteFrame` 必须填子资源 subMetas uuid）等见 `modules/cocos-creator-repair/SKILL.md`。批量素材导入用手写 meta + `sprite→spriteFrame 子资源 uuid` 映射表。

## 3. 换皮（skinpipe）

统一 CLI：`python modules/skinning-pipeline/scripts/skinpipe.py`，子命令 `manifest / atlas-extract / map / apply / rollback / atlas-rebuild / diff / verify`。默认 dry-run；`apply --execute` 先备份再原子替换；Cocos 图集原位重建只自动处理 `rotated=false && trimmed=false && 尺寸一致` 子图，rotated/trimmed 进人工清单。详见 `modules/skinning-pipeline/SKILL.md`。

## 3b. UI 烘焙（WYSIWYG 固化）

当换肤/新 UI 是运行时代码（编辑器里 prefab 仍是旧版、美术无法编辑）时，把运行时换肤函数逐值回写进 `.prefab` JSON：备份 → dump 节点树 → 按序列化字段表换算（contain 缩放需原图 PNG 尺寸）→ 补节点（必须带 UITransform + fileId 去重）→ 重解析校验 → 重建冒烟 → 编辑器目检。CLI 无 prefab 编辑能力，脚本化必走 JSON；幂等 guard 防双跑。详见 `modules/prefab-bake/SKILL.md`。

## 4. 构建与 QA

Cocos Creator CLI 构建 web-mobile/android → headless Chrome CDP 验收 + 真实拖拽 → MuMu adb 安装/启动/截图 → 视觉验收与交付同步。注意 Gradle `mergeAssets` 陈旧缓存清理、CDP 视口强制 reload、`CocosCreator.log` EPERM 为良性报错。详见 `modules/cocos-qa/SKILL.md`。

## 5. Android 真机视觉验收

当任务要求可重复的真机截图回归时，使用 ADB 操作、逐步截图、OCR、UI XML、设备元数据与 Logcat 形成证据包；基线必须来自已人工确认的已知良好构建，且视觉/OCR/崩溃任一确定性检查失败都不能被模型判断覆盖。详见 `modules/vision-device-testing/SKILL.md`。

## 6. 完全替换 SDK（联网隔离 / 离线内置 / 全新 SDK）

按结果档位交付：**A** = 供应商切换（切断原厂联网 + 保留/接入新 SDK 联网）；**B** = 断网离线内置（所有联网内容下载内置到本地，Seed 门禁 `missing=0 unmapped=0 hash_conflict=0`）；**C**（可选）= 二进制级彻底消失（DEX/资源/Manifest 移除）。先取基线（APK 哈希/证书/版本）与表面清单，再写隔离配置与验收契约；实现遵循"隔离原厂实际连接与数据交付，而非无差别删除旧类/字符串"；最终判定必须用真机 DNS/TLS/HOST 三层抓包 + 业务回归，模拟器通过不算。详见 `modules/sdk-replacement/SKILL.md`。
