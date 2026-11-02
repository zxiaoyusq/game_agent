---
name: gameplay-logic-reverse
description: Use when 用户要逆向或离线恢复游戏算法、出块策略、玩家泳道、Trait/机制开关、难度系统、远程 bundle、本地快照，或需要诊断材质/特效在新局、清屏、引导和预消除生命周期中的冲突。适用于 Cocos Creator JS/JSB，也覆盖静态证据、运行时捕获、本地替代和真机验收边界。
---

# 玩法逻辑 / 算法体系与 Trait 系统逆向

## 执行卡（先用这张卡，再读正文）

**我管什么**：逆向和离线恢复玩法算法（出块策略、玩家泳道、难度系统）、Trait / 机制开关与远程 bundle、本地快照，以及诊断材质/特效在新局、清屏、引导、预消除生命周期里的冲突。只管 Cocos Creator JS/JSB；美术资源提取不归这里，Unity IL2CPP 玩法也不归这里。

**第一步做什么**：先读根 `references/scope-map.md` 分清 `GENERALIZED_PATTERN` 与 `CASE_ONLY_BLOCKMASTER`，再定位该项行为的原版真实执行路径与唯一 owner（谁负责 show/hide/restore/commit）。定位不到 owner 之前，不动任何条件、配置或调用入口。

**做完怎么算完成**
- [ ] 能一句话说出「任务是 X，走本模块，第一步是 Z」
- [ ] 已写出原版唯一 owner 及其负责的生命周期阶段
- [ ] 已确认改动点落在哪个稳定边界（拖拽/预消除/动画/广告回调进行中只允许记录 pending）
- [ ] 版本边界已钉死，没把两个版本的 owner、事件顺序或资源格式混成一套「原版代码」
- [ ] 每条结论都标了来源（运行时包 / 堆窗口），未解处如实写进已知局限

**红线（不可违反）**
- 严禁用全局扫节点、遍历 proxy、对象池清空或延迟清理替代 owner；严禁靠加延迟掩盖时序问题。
- 后台只 prepare，只在原代码证实的稳定边界 commit；同一 epoch 只能由一个 owner 提交一次 PresentationBundle。
- tray 已展示、已消耗一块或进入拖拽后不可再改；同一出块 epoch 只允许提交一次。
- 案例字面值不可复制：枚举、Trait 名、事件名、hook 偏移、包名、服务器、数量、V123/V124 结论均属 `CASE_ONLY_BLOCKMASTER`，默认 hook 地址与包名必须重新定位。
- 正确不等于分布正确：候选搜索顺序不能暗中变成选择概率，不得意外推进正式 RNG；1x1、万能牌等退化候选只能作最后应急。
- 快照只能证明服务器曾返回过什么；没有数据源时不得宣称活动、赛季、热修或未来资源已恢复。

**卡住时按顺序读**
- 静态卡在自定义加密（AFFA 内层）→ 本文件 Phase 3 的 Frida 运行时捕获
- 材质/特效局内生命周期冲突 → `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md`、`modules/gameplay-logic-reverse/references/blockmaster-v128-tray-guard-regression.md`
- 本地重放 / 跨版本迁移 / native 执行层 → `modules/gameplay-logic-reverse/references/observed-runtime-replay.md`、`references/binary-version-diff.md`、`references/native-code-evidence.md`
- 需要完整端到端样例 → `modules/gameplay-logic-reverse/references/block-blast-case.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：逆向和离线恢复方法属于 `GENERALIZED_PATTERN`；Block Blast 的枚举、Trait 名、事件、偏移、服务器、数量和 V123/V124 结论属于 `CASE_ONLY_BLOCKMASTER`。先读根 `references/scope-map.md`。

脚本说明：本模块全部脚本随本仓库分发（`modules/gameplay-logic-reverse/scripts/`），文中 `python scripts/…` 均指该目录；每个脚本文件头有 docstring（用途/用法/参数）。引用任一脚本前先在最小夹具上跑通，再用于真实项目。

在美术资源逆向完成后，进一步破解**游戏玩法逻辑**：主游戏算法体系（每回合怎么出题、怎么验证、怎么兜底）与 Trait 特性系统（远程开关/调参/实验）。本模块以 Block Blast（`com.block.juggle`，Cocos Creator 2.4.x + 远程 bundle）为实战案例，沉淀可复用的五阶段流程。

版本边界：BlockMaster 当前工程的直接重打包基底是 Block Blast 10.4.7；9.5.0 运行采集、六套 AB 快照和旧版本报告只用于历史对照。不要把两个版本的 owner、事件顺序或资源格式混成一套“原版代码”。

## 适用判定

- 目标是"算法/玩法/Trait/机制开关"而非美术资源 → 本模块；

- 构建是 Cocos Creator 2.x/3.x JS 游戏（`libcocos2djs.so` + `main.js` + `assets/` + `gamecaches/` 远程缓存）→ 本模块；

- 静态解密卡在自定义加密（HEK:XOR v03 外层已解、AFFA 内层未解）→ 用 **Phase 3 动态运行时捕获**绕过；

- Unity IL2CPP 的玩法逻辑 → 不属于本模块（走 unity-extract + Il2CppInspectorRedux）。

## 核心思路

静态只能拿到"壳"（HEK 外层解密后的 AFFA 容器、堆转储碎片），**运行时才是真代码**：游戏进程内存里必然存在解密后的明文 JS。两条证据链合流：

```text
静态链：APK/内存 -> HEK 解密 -> 枚举/代码窗口/装饰器注册表（覆盖面广、有碎片）
动态链：Frida hook eval/run -> 运行时明文 JS 包（完整、真实执行、无碎片）
验收链：远程清单 -> 下载/解密 -> 逐目录状态验收 -> 文档
```

离线恢复多一条约束：快照只能证明“服务器曾返回过什么”，不能精确复制服务器对当前玩家的实时决策。应明确区分：

- 已证实的本地规则：可按代码、配置和运行证据恢复；

- 缺少实时模型输出的部分：用透明、确定、可测试的本地替代；

- 活动、赛季、热修和未来资源：没有数据源时不得宣称已恢复。

## 运行时恢复的最高优先级规则

1. **原版生命周期优先。** 先定位负责 show/hide/restore/commit 的单一 owner，再修条件、配置或调用入口。不得用全局扫节点、遍历 proxy、对象池清空或延迟清理替代 owner。

2. **加载和启用分离。** bundle/Trait 可后台加载，但只在原代码证实的稳定边界启用。拖拽、预消除、动画和广告回调进行中只允许记录 pending。

3. **一个事件一次提交。** 材质、普通配色、消行、清屏、连击、分数、棋盘和警告效果组成同一个 PresentationBundle；同一 epoch 只能由一个 owner 提交一次。

4. **Replay 不等待异步。** 第一条新局事件立即放行，后台准备不得成为 awaited gate；Replay 不等于连续清屏，不能触发 SSS。

5. **引导以持久化状态为准。** 手指等待阶段的预消除高亮可能是原版设计；仅在触摸和动画都已结束后仍保留才判残留。

6. **特殊材质双就绪。** 材质资源与匹配效果配置/handler/pool 都 ready 才能进入本轮；晚到结果延期到下一稳定边界。

7. **低端机只降成本，不改语义。** 预热离开热路径，降低粒子/并发/时长/分辨率，不关闭整组 Trait。

8. **安全保护器只做后验最小修复。** 先证明原版 producer 与 solver 的真实成功语义；若 solver 已枚举顺序，禁止再叠加“每种首选都必须成功”等更严格条件。原始输出只要满足原版语义就原样保留；确实无解时按“最少槽位、非退化候选优先、扩大修复范围必须有证据”的顺序处理。tray 已展示、已消耗一块或进入拖拽后不可再改，同一出块 epoch 只允许提交一次。

9. **正确不等于分布正确。** 除“是否仍会刷死”外，必须统计保护器触发率、被替换槽位数、各形状频率、连续极小块长度以及与未加保护版本的分布差异。候选搜索顺序不能暗中变成选择概率：优先复用原 producer 的权重，或在同级有效候选中按 tray epoch 做可复现选择，且不得意外推进正式 RNG。1x1、万能牌或其他退化候选只能作为最后应急。

BlockMaster V118-V124 的失败链、V123 回退和 V124 稳定边界见 `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md`。

出块保护器的通用测试矩阵，以及 BlockMaster V128 的 `BaubleTopic` 语义、1x1 洪水根因和最小修复证据，见 `modules/gameplay-logic-reverse/references/blockmaster-v128-tray-guard-regression.md`。该文件中的类名、块 ID、候选池和版本号均为 `CASE_ONLY_BLOCKMASTER`；只迁移判断方法。

## Phase 0：环境与指纹识别

1. **引擎/加密指纹**（可复用 `modules/engine-identification/SKILL.md`）：

- `libcocos2djs.so` + `patch/main.js`（HEK 加密 boot）→ Cocos 2.4.x JS；

- `HEK:` 头 + 版本字节只说明进入 HEK 家族。先比对原生加载器和已验证样本再选择 v01/v03 或其他变体；不得把所有 HEK 文件交给 v03 XOR 工具；

- `.jsc` → XXTEA（走 `modules/cocos-reverse-engineering/SKILL.md` Phase 3）。

1. **运行时环境**：模拟器或真机；先用 `adb devices` 发现当前序列号，不假设固定端口。游戏启动到目标阶段后用 `adb shell pm path ` 定位设备实际 APK，并按授权范围提取 `files/patch/` 与 `files/gamecaches/`。

2. **依赖**：可用的项目兼容 Python、frida/frida-tools、adb。先实时发现可执行文件并校验版本，不依赖系统 `python` 别名一定可用：

```powershell
python -c "import frida; print(frida.__version__)"
adb devices
```

## Phase 1：静态提取（先于动态，覆盖面广）

### 1.1 堆转储与代码窗口

进程内存中搜索 `window.__require` / `"use strict"` / `cc._RF` 等标记，导出 JS 代码窗口：

```bash
python scripts/extract_js_from_heap.py     # 按标记切窗
```

产出 `code_windows.json`（{ 函数/类名 -> \[\[源文件, 代码\], ...\] }），后续枚举/装饰器恢复都从这里来。

### 1.2 算法枚举恢复

在代码窗口中定位 `AlgorithmType` 模块（`(function(e) { e[e.NONE = -1] = "NONE"; ... })`），提取：

- `OFFER_TYPE`：1,024 项算法注册表（随机/清屏/困难/上增/免死家族）；

- 家族枚举：`OFFER_TYPE_BASE / OFFER_TYPE_SHANG / OFFER_TYPE_BLANK / OFFER_TYPE_DIFFICULTY / OFFER_TYPE_DIE`；

- 映射表：`OFFER_TYPE.X -> AlgoClassTypeConst.algo_*`（JS 名 → C++ 实现类）。

脚本：`python scripts/extract_algo_traits.py --code-windows code_windows.json --out algo_traits.json`；产出 `algo_traits.json`（算法线索计数与 Trait 引用统计；可 `--trait-patterns` 追加本项目正则）。

### 1.3 装饰器注册表（Trait → 算法方法挂载）

堆窗口里常含整张装饰器表：`类名: { 方法名: { decorators: [{ traitClassName }] } }`。这是"哪个 Trait 改哪个算法方法"的直接依据。

```bash
python scripts/extract_decorator_registry.py  
```

产出 `trait_decorator_registry.json`（如 `AlgoFillSortEdgeTrait.isCanReplace -> AlgoFillSortEdgeNoUseTrait`）。

## Phase 2：远程 Trait 目录清单与验收

### 2.1 恢复远程清单

从堆/`settings` 恢复热更服务器（`server`、`jsList`、`bundleVers`）：

```bash
python scripts/gen_remote_manifest.py --settings assets/main/index.*.js --url-template "https://<你的CDN>/{bundle}/{version}/config.json" --out remote_manifest_full.json
```

产出 `remote_manifest_full.json`（Block Blast：4,882 个远程包，其中 3,823 个 Trait 包 + 125 皮肤包；`cacheList.json` 2,768 条实机缓存索引）。

### 2.2 批量下载与解密

```bash
python scripts/download_remote_trait_bundles.py --manifest remote_manifest_full.json --out remote_traits/raw
python scripts/decrypt_v03_resources.py --input remote_traits/raw --output remote_traits/dec
```

规则：config 为 v03（纯 XOR(KEY_B) → 明文 Cocos JSON）；index 为 v01（XXTEA(KEY_B) → 明文 JS 或 AFFA 容器）。Block Blast 实测 3,790 个包 config+index 解密成功（195 个 CDN 403/下架）。

### 2.3 逐目录验收

把"本地目录（262）/远程包/堆证据"三套口径对齐：

```bash
python scripts/associate_trait_dirs.py --local <解包assets> --remote remote_manifest_full.json --out local_dir_to_remote_bundle.json
python scripts/trait_dir_evidence.py --heap code_windows.json --catalog trait_catalog.txt --json-out trait_dir_evidence.json
python scripts/build_trait_acceptance.py --local-dir <解包assets> --catalog trait_catalog.txt --manifest remote_manifest_full.json --evidence trait_dir_evidence.json --remote-dec remote_traits/dec --out trait_dir_acceptance.json
python scripts/gen_acceptance_report.py --manifest remote_manifest_full.json --mapping local_dir_to_remote_bundle.json --evidence trait_dir_evidence.json --build trait_dir_acceptance.json --out 验收报告.md
```

验收字段（每目录）：`remote_bundle / remote_config / remote_403 / remote_asset_count / local_file_count / heap_occurrences / heap_classIdRegistered / status`。Block Blast 实测：262 行 = 254 唯一目录 + 8 同名重复；254 全部有本地资产、241 有远程包、214 config 解密成功、27 个 403。

## Phase 3：Frida 动态运行时捕获（关键突破）

静态卡在 AFFA 内层时，动态捕获是绕过关卡的正解：**hook 运行时 eval/run，直接拿解密后的明文 JS**。

### 3.1 定位 hook 地址

先枚举 `libcocos2djs.so` 导出/符号，再在内存里定位核心 JS 入口（Block Blast 实例：`0xB8E8C0` = core eval、`0xB8F3E0` = run 模块）。定位法：下断点观察哪个地址收到 `window.__require` / 模块路径字符串。

### 3.2 附加并挂钩

```powershell
python scripts/frida_capture_eval.py --device 127.0.0.1:16384 --package <当前项目包名> --out eval_capture --spawn

注意：hook 的默认 eval/run 偏移、包名与壳层符号是 `CASE_ONLY_BLOCKMASTER` 案例值（见根 `references/scope-map.md`）；其他项目必须重新定位自己的 hook 地址，`--hook-eval/--hook-require/--hook-function` 可按需关掉默认打点。
```

脚本行为（`modules/gameplay-logic-reverse/scripts/frida_capture_eval.py`）：

- `Interceptor.attach` 到 core eval 与 run；

- 读取 arg1 字符串（eval 源码 / 模块路径），>100 字节写入设备文件（`core_.js`）；

- 逐条打印 `{tag, seq, arg1str}` 到 stdout（供本地落盘）；

- 设备端目录用 `adb pull` 增量同步（或本地 watch 每 15s 拉取）。

### 3.3 关键产出与解读

- `core_.js`：运行时 eval 的明文 JS 包（Block Blast：`core_00024.js` 1.5 MB = 章节主包，358 模块、78 个 `*Trait` 类、`ChapterAlgorithm*` 全套管线）；

- `run` 事件：模块执行轨迹（Block Blast：每步落子一次 `./GameLogic`，32 次证明管线真实运行）；

- 同时 `adb pull /data/user/0//files/gamecaches/` 拉实机 Trait 目录快照（Block Blast：121 个目录，含 cacheList.json）；

- 游玩期间配合 `screencap` + `uiautomator dump` 留游戏画面证据。

注意：hook 要在目标 bundle eval 之前挂上才能抓到全部包；游戏已启动时只抓后续加载的 bundle（Block Blast 的章节主包是进关卡才 eval）。需要启动链完整包时，用 `frida -f ` spawn 模式重抓。

## Phase 4：代码级恢复（从运行时明文 JS）

### 4.1 模块清单与类注册

```python
cc._RF.push(t, "", "")  # 每个模块注册一次
模块表 = re.findall(r'([A-Za-z0-9_$./-]+):\s*\[ *function', js)
```

产出 `chapter_bundle_modules.json`（358 模块）+ `chapter_bundle_traits.txt`（78 Trait 类）。

### 4.2 管线恢复（策划/程序都要的骨架）

每个 Module 的 `registerProxys()` 声明执行顺序；主执行 Proxy 的 `onTrigger*` 声明阶段列表（Block Blast：`ChapterAlgorithmStrategy_Run_Proxy.onTriggerStrategy` 的 10 阶段：ChapterDeal → ChapterPriority → ChapterReplace → Deal → ChapterCondition → AlgoExe → ChapterBlockOut → BlockPos → Collect → Color），每阶段有 `execute`（派发事件）与 `condition`（GameInfo 开关）。

### 4.3 Trait 机制恢复

- 基类字段：`_state/_props/_cachedStaticActive/_dynamicActive`；`active = dynamicActive && staticActive`；

- `classId(name)` 注册：写入 `window.__traitsClassMap__` + `window.traitRegisterEvents`（事件拦截点）；

- `TRAIT(name)`：查 `traitConfigInfo.traitsClassNameMap` → `__traitsClassMap__` → 单例实例（注入 id/props/state，onCreate）；

- 参数安全读取：`traitConfigSafePropsInfo.getSafePropValueByKey(traitName, key, props, default)`；

- 配置管线：preInit(本地预编译) → initializeCfg(服务端) → 黑名单/白名单/CTRefactor 映射/热替换 → 类型校验。

### 4.4 棋盘/底层算法

定位位棋盘类（`BinarySupport`：`rowBinary` 每行一个整数位棋盘）与放置搜索（`canPutBlock`：单块可放枚举 → 优先消除 → 两两组合验证 → 禁放区/方差排序）。

## Phase 5：验收与文档交付

### 5.1 完整性自验（必做）

- 数字复核：枚举成员数、模块数、Trait 类数、运行时调用次数（从日志逐条数，不凭印象）；

- 三套口径对齐：实机拉取 ⊆ 本地目录 ⊆ 远程全量（Block Blast：121 ⊆ 262 ⊆ 3,823）；

- 每个代码片段标注来源（运行时包 / 堆窗口），未知/未解处如实写入"已知局限"。

### 5.2 双视角文档

```text
策划视角：算法家族与玩法效果、难度组合、Trait 开关方式（firing/黑名单/白名单/CTRefactor/热替换）、
配置 JSON 实例、应用策略速查表、262 目录全景分类
程序视角：Module/Proxy 架构、10 阶段管线源码、阶段开关、算法列表状态机、概率替换算法、
Trait 基类/classId/TRAIT()/参数安全读取、棋盘位运算、装饰器注册表、多模式差异
附：验证方法（storage key / Frida / 日志）、词汇表、已知局限
```

参考完整案例：`modules/gameplay-logic-reverse/references/block-blast-case.md`。

## 产出文件规范

```text
/
|- AlgorithmType_module.txt / OFFER_TYPE_enum.txt / offer_enum_full.json   算法注册表
|- code_windows.json / trait_decorator_registry.json                       静态代码窗口
|- remote_manifest_full.json / remote_traits/dec//                 远程清单与解密产物
|- trait_dir_acceptance.json / 验收报告.md                                  262 目录验收
|- frida_capture/eval_capture_local/core_*.js                              运行时明文 JS
|- chapter_bundle_modules.json / chapter_bundle_traits.txt                 模块清单
|- 主算法体系与Trait机制-策划与程序手册.md                                   最终交付文档
```

## 已知局限（如实报告）

1. AFFA 内层（v01 代码包 XXTEA 后的私有容器）：静态未完全破解 → 动态捕获绕过，未捕获到的包仍缺；

2. 基础包启动链：已启动后才 hook 会漏掉启动瞬间 eval → spawn 模式重抓；

3. 原生边界：`algo_*` C++ 类实现不在 JS 侧（`./GameLogic` 为原生模块），JS 只暴露 OFFER_TYPE 与接口；

4. 远程 403 包：清单有版本号但 CDN 拒绝（下架或需签名），影响全量验收。

## 版本记录

- **2.1.0 (2026-08-28)**：加入“原版 producer、原版 solver、后验 guard”职责分离，明确存在性可解与全称可解不可混用；新增最少槽位修复、partial tray 不可变、退化候选最后使用和分布级回归测试，并记录 V128 的 1x1 洪水案例。

- **2.0.0 (2026-08-26)**：加入离线恢复证据边界、10.4.7/9.5.0 版本分界、原版 owner 优先、稳定激活边界、PresentationBundle 单次提交、引导预消除判定、特殊材质双就绪和 V123/V124 回归复盘。

- **1.0.0 (2026-08-12)**：建立算法枚举、Trait 清单、运行时捕获与双视角文档流程。

## UI 道具与跨关生命周期追加门禁（7.4.0）

游戏重建需按输入→库存→引导/动画→提交→清理追踪完整事务，检查下一关来源、奖励幂等、暂停与拖拽引用；不能用 debug 自动求解代替提示功能。参考 [原生还原门禁](../godot-migration-port/references/native-restoration-gates.md)。原配置、实机 AB 与旧报告冲突时保留版本边界。

## 受控本地复现与版本迁移（按需）

本地重放 JS/JSB 算法时读 [观测驱动重放](references/observed-runtime-replay.md)，先保留配置/RNG/调用状态，以第一处差异驱动补环境。跨版本迁移读 [差分门禁](../../references/binary-version-diff.md)；native 算法转 [执行层取证](../../references/native-code-evidence.md)，不要对 IL2CPP 方法体套 JS heap 流程。

## BlockMaster V140–V142 模式与 Seed 竞态

身份匹配或明确对照案例时读 `modules/gameplay-logic-reverse/references/blockmaster-v140-v142-mode-seed-regression.md`。保留条件外 hook、冷启动 Seed 与模式包竞态、稳定边界提交和行为回归方法；具体名词/版本/路径/时间值属于 `CASE_ONLY_BLOCKMASTER`。
