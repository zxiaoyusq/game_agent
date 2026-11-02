# 实战案例：Block Blast（com.block.juggle）算法与 Trait 系统逆向

> **何时读我**：哥哥要拆 Block Blast / BlockMaster 的出块算法、OFFER_TYPE 枚举或 Trait 机制，问"这个游戏的关卡算法怎么逆向出来的、取证走了哪几步、AFFA 内层怎么绕过"，或要在同款 Cocos JSB 游戏上复刻这套静态+动态取证流程时。
> **读完能做到**：按本文五个阶段的顺序（静态堆窗口 → 远程包 HEK 解密 → Frida attach 抓运行时明文 → 代码级还原策略管线 → 三份交付文档）独立走完一遍同规模逆向，并知道哪些数值和 hook 偏移必须重新采集、哪些是历史快照。
> **范围**：`CASE_ONLY_BLOCKMASTER`

范围：`CASE_ONLY_BLOCKMASTER` · `DO_NOT_COPY_LITERAL_VALUES`。其他项目只参考取证方法，不复制数量、类名、地址、服务器或路径。

2026-08-12 · 版本 1.2.83.0.0 · 环境 MuMu 12（adb 127.0.0.1:16384）· 证据目录 `E:\codex_apk_work\`

**证据边界（2026-08-26 补充）**：本文的枚举数量、远程包数量、hook 地址和目录数量属于该次历史采集快照，不是跨版本常量。BlockMaster 当前直接重打包基底是 Block Blast 10.4.7；原版 9.5.0 与历史运行采集只用于对照。重做任务时必须重新确认当前 APK、运行时模块和地址，禁止照抄数值或 hook 偏移。

## 目标

破解主游戏算法体系（OFFER_TYPE 1,024 项 + 策略管线）与 262 个 Trait 目录（机制开关系统），并产出策划/程序双视角文档。

## 关键指纹

| 项 | 值 |
|---|---|
| 引擎 | Cocos Creator 2.4.x JS（`libcocos2djs.so` + `patch/main.js`） |
| 外层加密 | HEK:XOR v03（config/皮肤）、v01（代码包，XXTEA(KEY_B)） |
| 内层加密 | AFFA 容器（hdr4+meta8+载荷），静态未解 |
| 热更服务器 | `https://bband1.afafb.com/update/block_android_online/remoteRes/0/` |
| 远程包全量 | 4,882（3,823 Trait + 125 皮肤 + 语言/主题/功能） |
| 实机缓存 | 121 个 Trait 目录（gamecaches/），cacheList.json 2,768 条 |

## 各阶段要点与实测数据

### Phase 1 静态

- 堆转储代码窗口：`code_windows.json`（13 个核心键：`AlgoFillSortEdge`、`EntropyIncreaseBeforeFill`、`RandomNoDeath`、`UCBBlockPoolStrategy`、`LightGBMAlgorithmStrategy`、`AlgorithmStrategyLogic`、`applyReplaceAlgorithmV3`、`findPileUpPos`、`canPutBlock`、`BinarySupport` 等）；

- 枚举：`AlgorithmType_module.txt`（OFFER_TYPE 1,024 项，含 60+ 个 `OFFER_TYPE -> algo_*` C++ 映射）；

- 装饰器注册表：`AlgoFillSortEdgeTrait.isCanReplace -> AlgoFillSortEdgeNoUseTrait`、`AlgoSymmetryBlockTrait.replaceSymmetryAlgorithm -> ZX209_ReplaceQuestionAddComboTrait`、`Advertisement_Reward_Proxy.advertisementCallBack -> 4 个广告 Trait` 等 36 组。

### Phase 2 远程清单与验收

- 3,790 个包 config+index 下载并 HEK 解密；1,240 个 config 含资产路径（26,823 条）；781 个关键包资产 4,023 个文件全部解密；

- 262 Trait 目录验收：254 唯一目录（全部有本地资产文件）、241 有远程包、214 config 解密成功、27 个 CDN 403、253 有堆证据、11 个 classId 注册确认；

- 口径：121（实机拉取）⊆ 262（本地目录）⊆ 3,823（远程 Trait 包全量）。

### Phase 3 动态捕获（突破 AFFA）

- Frida attach 进程 `Block Blast!`（PID 8296），hook `libcocos2djs.so`：

`0xB8E8C0` = core eval → 抓运行时 eval 的明文 JS；

- `0xB8F3E0` = run → 抓模块执行轨迹。

- 关键捕获：`core_00024.js`（1,541,139 B，章节主包，358 模块、78 个 `*Trait` 类、359 次 `cc._RF.push`）；

- 运行时调用：42 条事件 = 5 次 core eval（3 次 `window.adCallback` 广告回调 + 2 次代码包）+ 34 次 run（32 次 `./GameLogic`，每步落子一次）+ 远程包加载；

- `TRAIT("XxxTrait")` 运行时用法 27 处（`active` 开关判断、`dynamicActive=false` 降级、`getSafePropValueByKey` 安全读参）。

### Phase 4 代码级恢复（来自运行时明文）

- **算法策略模块** `ChapterAlgorithmStrategy_Module.registerProxys`：Reset → BlocksPos → Run → Init → Replace → Deal → Priority；

- **10 阶段执行** `ChapterAlgorithmStrategy_Run_Proxy.onTriggerStrategy`：ChapterDeal → ChapterPriority → ChapterReplace → Deal → ChapterCondition → AlgoExe → ChapterBlockOut → BlockPos → Collect → Color（每阶段 `execute` 派发事件 + `condition` 由 `ChapterAlgorithmStrategyGameInfo.shouldExecute*` 决定，复活局跳过 Deal）；

- **方块生产** `ChapterBlocksProducer_Module`：9 个 Proxy（Proxy → Revive → RoundDot → Validate → TouchDot → Round → Render → Run → ChangeBlockPos），Run 派发 `E_ChapterAlgorithmStrategy_Run` 触发整条算法管线；

- **性能**：`algorithmPerformanceIsOpen` 开关切换帧拆分（AlgoExe/BlockPos/Collect/Color 每步 `nextFrame()`）与串行执行；

- **兜底**：算法失败 → `chapterBlockLists=[]` + 重置；章节触发游戏结束 → `getRandomFloatedArray([10,20,30])`（±4 随机）；

- **棋盘**：`BinarySupport` 位棋盘（每行一个整数，bit=1 有方块），`canPutBlock` 单块枚举→优先消除→两两组合验证→禁放区/方差排序；

- **Trait 机制**：基类 `active = dynamicActive && staticActive`、`classId` 注册 `__traitsClassMap__/traitRegisterEvents`、`TRAIT()` 单例查找、`traitConfigSafePropsInfo.getSafePropValueByKey` 安全读参、`traitConfigInfo` 配置管线（预编译→服务端→黑/白名单→CTRefactor 映射→热替换→类型校验）；

- **示例 Trait**：`LevelRandomReplaceTrait`（参数 algoId1=SUI_JI_WU_SI、algoId2=SHANG_ZENG_3、rate1/rate2=0.5，`@Algorithm()` onActive 按权重二选一替换本关算法）；`ChapterAlgoStrategyTrait`（按简单/中等/困难 + 旅行阶段整套切换算法列表，含 IOS 变体与 `chapterFirstHardState_base` 首次困难标记）。

### Phase 5 交付

- `主算法体系与Trait系统解密报告.md`（技术全量，含 8.x 续攻与 9.x 动态验证章节）；

- `主算法体系与Trait目录验收报告.md`（262 目录逐项验收）；

- `主算法体系与Trait机制-策划与程序手册.md`（最终交付：策划视角 + 程序视角 + 验证方法/词汇表/局限）；

- 全部代码片段标注来源（运行时包 `core_00024.js` / 堆窗口），未解处列入局限（AFFA 内层、基础包启动链、`algo_*` 原生实现、27 个 403 包）。

## 可复用资产（源路径）

```text
E:\codex_apk_work\main_algo_extract\        全部静态产物与报告/手册
E:\codex_apk_work\frida_capture\            捕获脚本与运行时明文 JS（attach_capture4.py、core_00024.js）
E:\codex_apk_work\gamecaches_live\          实机远程资源快照
E:\codex_apk_work\remote_traits\dec\        3,790 个远程包解密产物
E:\codex_apk_work\scripts\                  下载/解密/验收/文档生成脚本
```

运行时离线恢复的最新 owner/稳定边界规则见 `blockmaster-v123-v124-lifecycle-regression.md`。
