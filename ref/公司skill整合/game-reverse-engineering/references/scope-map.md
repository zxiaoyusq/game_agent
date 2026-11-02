# 游戏逆向技能适用范围地图

本文件帮助 Agent 判断哪些内容可以直接用于新项目，哪些只能作为案例。范围标签是使用约束，不代表案例内容"价值较低"。

**路径基准约定**：本总集所有正文中的反引号路径一律相对总集根目录（如 `modules/skinning-pipeline/SKILL.md`、`references/global-rules.md`）；markdown 链接 `[]()` 相对所在文件。引用新文件时遵守此约定，`scripts/validate_skill.ps1` 会校验。

## 标签定义

### GENERAL_DEFAULT

跨项目通用的流程、证据规则和工具。可以默认采用，但仍需针对当前构建验证输入格式、工具版本和输出。

### GENERALIZED_PATTERN

从真实项目提炼出的判断方法。可以迁移"如何找 owner、如何取证、如何设置门禁"，但必须在当前项目重新确认具体实现。

### CASE_ONLY_BLOCKMASTER / CASE_ONLY_BLOCKUDOKU / CASE_ONLY_SUDOKU / CASE_ONLY_JIGSAWCARD

项目专属证据。仅在包身份匹配、直接基底匹配，或用户明确要求用该案例作对照时加载。

### DO_NOT_COPY_LITERAL_VALUES

以下字面值永远不得从案例直接复制到其他项目：

- 包名、Activity、域名、URL、appId、证书和签名；

- APK 版本、SHA-256、设备序列号、模拟器端口和本机绝对路径；

- Trait/Proxy/事件/类名、资源目录、bundle id 和配置 key；

- hook 地址、so 偏移、加密 key、远程包数量和实验组数量；

- Loading/重试/动画时间、低端机阈值和"前 N 次"计数。

应迁移的是证明方法，例如"先定位真实请求 owner"，不是案例结论，例如"这个项目 appId 是 5943"。

## Agent 加载规则

1. 先读根 `SKILL.md` 和与任务匹配的模块 `SKILL.md`。

2. 新项目默认只加载 `GENERAL_DEFAULT`。

3. 遇到相似症状时加载对应 `GENERALIZED_PATTERN`，把案例名词替换为当前项目中重新定位的对象。

4. 只有包身份/直接基底匹配，或用户明确要求对照时，才加载 `CASE_ONLY_*`。

5. 引用案例后，交付报告必须注明"迁移的方法"和"当前项目重新取得的证据"，不能只写"参考 BlockMaster 已处理"。

## 模块范围

**模块执行卡索引**：每个模块 `SKILL.md` 顶部都有一张「执行卡」，固定四块（我管什么 / 第一步做什么 / 做完怎么算完成 / 红线）。下表「执行卡的唯一入口」列即卡内第一步；执行者读完该卡即可开工，不必预读模块正文。

| 模块 | 范围 | 使用说明 | 执行卡第一步 |
|---|---|---|---|
| `engine-identification` | `GENERAL_DEFAULT` | 引擎指纹与工具路由通用；Sudoku.com 的路径、版本和产物是 `CASE_ONLY_SUDOKU` | 跑引擎指纹检测，写出引擎 + 版本 + 是否加密 |
| `cocos-reverse-engineering` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | 格式识别、解密分流、资产完整性通用；Android BlockMaster 参考按下表单独分类 | 先读文件头/版本字节确认真实加载器，再决定解密链 |
| `cocos-creator-repair` | `GENERAL_DEFAULT` + 案例片段 | `.fire`、引用、黑屏诊断通用；Sudux 文件路径、坐标和窗口状态不可照搬 | 跑 `check_fire_refs.py` 查引用悬空 |
| `unity-extract` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | AssetRipper/UnityPy 思路通用；TextAsset/Spine/远程 manifest/配置挖掘方法可迁移（见 jigsawcard 全案）；本机工具路径和 Sudoku/jigsawcard 产物是案例值 | 用 AssetRipper/UnityPy 提取并核对产物可反查回原文件 |
| `gameplay-logic-reverse` | `GENERALIZED_PATTERN` | 算法/Trait/运行时捕获方法可迁移；Block Blast 枚举数、类名、偏移和远程清单是专属值 | 定位真实执行路径与唯一 owner |
| `sdk-replacement` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | 三档结果定义（A 供应商切换 / B 断网离线内置 / C 二进制级消失）、P0-P8 八阶段、证据分级与误判表、静态/网络/Seed 三层门禁、真机 DNS/TLS/HOST 验收与报告生成通用；具体域名、appId、证书、SDK 类名和数量是案例值（`DO_NOT_COPY_LITERAL_VALUES`） | 先钉死 A/B/C 档位，再读 P0–P2（基线 + 联网面 + 隔离配置） |
| `skinning-pipeline` | `GENERAL_DEFAULT` | manifest/map/apply/rollback/diff/verify 通用，调用者传入当前工具和项目路径 | 先出 `skinpipe manifest`（默认 dry-run） |
| `prefab-bake` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | Cocos 3.x prefab JSON 序列化字段表、七步烘焙流程、幂等/校验门禁通用；案例里的坐标、uuid、设计基准尺寸和 codex_* 命名是怀旧时光拼图专属值（`DO_NOT_COPY_LITERAL_VALUES`） | 先读运行时换肤函数，再备份 prefab |
| `ui-feature-pipeline` | `GENERALIZED_PATTERN` | 六阶段 UI 开发链路（效果图分层/控件切分复用/等比 contain/动态文字安全框/多语言多分辨率安全区 QA/固化）与生图工具无关接入通用；项目路径、母版、processed 清单内容是怀旧时光拼图专属值（见其项目级 skill cocos-ui-reskin-qa） | 从功能需求表开始走六阶段链路 |
| `cocos-mcp-channel` | `GENERAL_DEFAULT` + 历史环境记录 | 3.8.x MCP；2.4.x 用文件/CLI，预览和正式 QA 分开 | 确认版本并探测/启动，get_editor_state 核对服务和工程 |
| `cocos-qa` | `CASE_ONLY_BLOCKUDOKU` + `GENERALIZED_PATTERN` | 主脚本硬编码 Blockudoku 工程、包名和工具路径；`spine-fx-repair-qa.md` 与 `content-image-mapping-qa.md` 的分层审计、证据边界和门禁可迁移，字段与路径必须重新发现 | 分开结构审计与语义审计，再生成可回写三联表 |
| `dragonbones-spine-convert` | `GENERAL_DEFAULT` | DB 5.0/5.5 → Spine 3.8 转换与三级 QA 流程通用；具体项目骨骼命名、分组和路径是案例值 | 跑 `db2spine.py` 转换，随后过三级 QA |
| `vision-device-testing` | `GENERAL_DEFAULT` | ADB/截图/OCR/UI dump/Logcat 验收合同通用；具体设备序列号、包名和基线是案例值 | 构建 → 安装 → 逐步截图证据包 |
| `godot-migration-port` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | 十二类迁移映射、S0–S7 端到端生产流程、证据状态、阶段门禁、当前版本快照/provider、后期系统、分层 QA、最终 APK 与交接方法通用；jigsawcard 的资源数量、门槛、坐标、哈希和评估结论是 `CASE_ONLY_JIGSAWCARD`；整页截图路线仅在用户明确接受时读取 `art-remake-playbook.md` | 先做 S0 资产盘点清单与覆盖矩阵 |
| `3d-asset-extraction` | `GENERAL_DEFAULT` | PC 3A 游戏 3D 资产提取的引擎→工具链路由（NeoX/Messiah、RE Engine、FromSoftware、REDengine 4、MT Framework）、加密容器解法与渲染/交付规范通用；本机工具绝对路径、具体游戏实测坐标与密钥是案例值，密钥只随该游戏项目使用 | 按引擎指纹查模块路由表选工具链；未知格式走四步法 |
| `deliverable-book-template` | `GENERALIZED_PATTERN` | 逆向拆解交付的目录规范、md 文档分类法、证据标注体系与单文件 HTML 全书模板通用；案例的章节编号、数量与主题按目标游戏实际系统增删 | 用 `md2book_template.py` 生成骨架，再按目录规范填充 |

## 外部技能与总集的关系

- 总集持有：意图路由、迁移映射、迭代协议、多端同步结构与验证脚本。
- 外部技能持有：各自正文与版本（`references/external-game-skills.md` 只做路由与来源登记，hub 不复制正文）。
- 项目专属证据永远不进入外部通用技能；若某外部技能需要案例值，只写"方法"，字面值留在项目 landing-log 或 `CASE_ONLY_*` 文件。
- 外部技能更新：按注册表更新命令处理；本地有改动的副本先 diff 再决定，禁止盲 pull。

## 通用默认内容

以下内容可优先用于其他项目：

- **`references/execution-protocol.md` 的五步循环、六条铁律、卡住时的排查顺序和状态四词表**：这是所有模块共用的执行骨架，任何任务动手前先读；案例与模块只提供"做什么"，本文件提供"怎么推进、什么时候算过"。

- 根 `SKILL.md` 的路由、证据等级、版本谱系、最小补丁、交付门禁与落地迭代协议；

- `modules/engine-identification/` 的引擎指纹；

- `modules/cocos-reverse-engineering/` 的格式文档与通用工具，但 `decrypt_v03_resources.py` 仅用于已确认的 v03；

- `modules/cocos-creator-repair/scripts/check_fire_refs.py` 与 `.fire` 引用检查方法；

- `modules/unity-extract/` 的资产提取和验证流程；

- `modules/skinning-pipeline/` 的 manifest、映射、备份、回滚、diff 和 verify；

- `modules/godot-migration-port/` 的十二类迁移映射与 S0–S7 主流程；端到端细节在 `modules/godot-migration-port/references/end-to-end-restoration-workflow.md`，真实回填在 `modules/godot-migration-port/references/landing-log.md`；

- `scripts/validate_skill.ps1` 的结构与多端一致性验证。

## 可迁移的案例提炼模式

| 参考文件 | 范围 | 可迁移内容 | 不可照搬内容 |
|---|---|---|---|
| `modules/cocos-reverse-engineering/references/android-boot-stuck-diagnosis.md` | `GENERALIZED_PATTERN` | 确认真实 JS 入口、settings/哈希、密文/明文混用、文件标记插桩 | BlockMaster 路径、marker 和构建产物 |
| `modules/cocos-reverse-engineering/references/android-reskin-repack.md` | `GENERALIZED_PATTERN` | 版本重基、split ABI、Seed、原生库压缩与签名门禁 | 原包版本、目录和签名值 |
| `modules/cocos-reverse-engineering/references/android-cocos-lifecycle-trait-and-release-qa.md` | `GENERALIZED_PATTERN` | 单一 owner、异步 prepare/稳定 commit、双执行副本、真机验收 | BlockMaster 事件名和 V123/V124 结论 |
| `modules/cocos-reverse-engineering/references/android-athena-aidl-loop-and-upload-verification.md` | `GENERALIZED_PATTERN` | AIDL 回路、上传四级证据、聚合广告归属判断 | Athena appId、端点、表名和供应商结论 |
| `modules/cocos-reverse-engineering/references/unity-il2cpp.md` | `GENERALIZED_PATTERN` + `CASE_ONLY_SUDOKU` | Unity 外设系统的定位方法 | Sudoku 类名、活动和资源数量 |
| `modules/cocos-reverse-engineering/references/cocos2x-runtime-build-qa.md` | `GENERALIZED_PATTERN` | Cocos 2.x 运行时 UI、meta、构建与截图验证 | Sudux 路径、场景和固定分辨率 |
| `modules/cocos-qa/references/content-image-mapping-qa.md` | `GENERALIZED_PATTERN` | 运行时映射取证、结构/语义双层结论、图片+配文+出处三联审核、可回写工具与 Web/APK 产物复验 | 任一项目的关卡数量、路径、键格式、故事内容和修正文案 |
| `modules/unity-extract/references/jigsawcard-puzzle-case.md` | `GENERALIZED_PATTERN` + `CASE_ONLY_JIGSAWCARD` | TextAsset `m_Script`+latin-1 还原二进制、Spine 六件套识别与缺图补齐、`global-metadata.dat` magic 实测、manifest_ext.bs 分层解析、CDN 403 → 真机 mitmproxy、配置挖掘 + 策划分析四问/图表化交付模板 | jigsawcard 的包名、版本、magic 值、CDN 域名、远程包数、实验/广告/关卡/震动数值 |
| `modules/godot-migration-port/references/art-remake-playbook.md` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` + `CASE_ONLY_MAGICSORT` | 单层纪律决策表（值同→零绘制 / 值异→原始贴图覆盖）、色值反查纹理、几何掩码污染源清单、烘焙页擦除安全区（不穿亮 UI）、9-slice margin 实测、tween bind 参数追加、双证据（拼图+diff blob）验收与检查清单 | magicsort 的包名、版本、所有实测坐标/尺寸和教训清单 |
| `modules/godot-migration-port/references/end-to-end-restoration-workflow.md` | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | S0–S7 阶段、证据状态、资产/玩法/表现/后期系统/快照配置/分层 QA/最终 APK/交接与 Skill 回填；设备页面 ready 多锚点、引导遮罩状态机和 fixture 原字节恢复 | jigsawcard 的资源数量、门槛、坐标、时距、APK 与存档哈希 |
| `modules/godot-migration-port/SKILL.md`（含 landing-log） | `GENERALIZED_PATTERN` | Unity→Godot 迁移分类、专项参考路由与主流程摘要 | jigsawcard 的资源数量、门槛、坐标、材质/Shader 清单与评估结论 |
| `modules/godot-migration-port/references/godot-engine-pitfalls.md` | `GENERALIZED_PATTERN` | gl_compatibility 下粒子不渲染、GUI 命中树序、导航演出解耦、生成器排版守护、字体 fallback 行框、OptimizedTranslation 启动成本、内存台阶口径、导出与 ADB 互斥、接缝/位移看门狗 | 无案例字面值（全泛化）；实证出处 jigsawcard |
| `modules/sdk-replacement/SKILL.md`（含 scripts） | `GENERAL_DEFAULT` + `GENERALIZED_PATTERN` | A/B/C 结果档位、八阶段流程、证据等级与误判表、隔离=切断实际连接非删类、inert-success 与交付层 no-op、URL 参数绕过、Seed 三层门禁、真机三层网络证据链与报告生成 | 具体原厂域名族、appId、证书 SHA、SDK/聚合供应商名、远程包数量和案例结论 |

## BlockMaster / Block Blast 专属内容

根级 BlockMaster 专属规则已集中到 `references/blockmaster-case-rules.md`（`CASE_ONLY_BLOCKMASTER`，8.0.0 起从根 SKILL.md 拆出）；以下案例文件统一标记为 `CASE_ONLY_BLOCKMASTER`：

| 文件 | 专属内容 |
|---|---|
| `modules/gameplay-logic-reverse/references/block-blast-case.md` | OFFER_TYPE 数量、Trait 目录数、运行时模块数、hook 偏移、服务器与缓存快照 |
| `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md` | V118-V124 回归链、10.4.7 owner 名、V124 APK/提交基线 |
| `modules/gameplay-logic-reverse/references/blockmaster-v128-tray-guard-regression.md` | V128 `BaubleTopic` 可解语义、块 ID、候选池、1x1 洪水根因与项目测试证据 |
| `modules/cocos-reverse-engineering/references/android-blockmaster-runtime-effects-ads-regression.md` | 新局/清屏边界、SSS、特殊材质、Banner、Replay 和三块保护的项目规则 |
| `modules/cocos-reverse-engineering/references/android-blockmaster-v35-vendor-isolation-and-real-device-qa.md` | 原厂域名隔离、Athena/Hisavana/Palm/Aha、V35 证据和正式证书 |
| `modules/cocos-reverse-engineering/references/android-blockmaster-v31-ad-resource-and-ui-removal.md` | Hisavana 资源、More Games/No Space/评分与 V30/V31 构建链 |
| `modules/cocos-reverse-engineering/references/android-blockmaster-moregames-settings.md` | BlockMaster full/lite 的 More Games、More Settings、热更缓存和 Play 覆盖规则 |
| `modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md` | BlockMasterPro 10.4.7 的 DEX、JS-Java 桥、Hisavana/Athena 和 SeedCopier 实例 |

`modules/gameplay-logic-reverse/scripts/frida_capture_eval.py` 当前也属于 `CASE_ONLY_BLOCKMASTER`：虽然参数可覆盖，但默认设备、包名示例和两个 native offset 来自 Block Blast。其他项目必须先重新定位地址，最好显式传入全部参数。

### BlockMaster 中已提炼为通用的方法

这些不是只能在 BlockMaster 使用：

- 找到 show/hide/restore 的单一 owner，而不是全局扫节点；

- 把异步加载与稳定边界启用拆开；

- 同一业务 epoch 只允许一次最终表现提交；

- 资源存在性与运行时可达性分开验证；

- 主 APK、Seed/patch、设备缓存分别做哈希和执行路径确认；

- 广告、埋点、原厂隔离分别取得真机网络证据；

- SDK 替换先落地"结果档位 + 验收契约"，再动手：A 只换供应商、B 要离线内置、C 才谈删除旧类，不同档位对应不同证据门禁；

- 维护最后已知良好版本，发生回归先做差异比较，不继续叠补丁。

- 安全保护器沿用原版 solver 的成功语义，只后验修复真实无效输出，并同时验证功能与长期分布。

迁移这些方法时，把 `E_BlocksProducer_AnyTouchEnd`、`Eliminate_Effects_Proxy`、`SkinThreeInfo` 等名字替换为当前项目重新定位的 owner 和事件。

## 其他项目专属案例

### CASE_ONLY_BLOCKUDOKU

`modules/cocos-qa/` 当前整体属于 Blockudoku 验收夹具：脚本默认工程目录、Creator、SDK/JDK、包名、Activity、MuMu 端口和截图流程均为项目值。其他项目只参考"Web 快循环 -> Android 包 -> 真机/模拟器 -> 视觉验收"的结构。

### CASE_ONLY_SUDOKU / CASE_ONLY_SUDUX

- `engine-identification` 和 `unity-extract` 中的 Sudoku.com 版本、对象数、资产数、导出目录是历史案例。

- `cocos-creator-repair` 中的 Sudux 项目路径、Dashboard 坐标、场景 UUID、素材数量和窗口状态是历史案例。

- 可以复用诊断方法，不能复用字面路径、坐标、UUID 或数量。

### CASE_ONLY_JIGSAWCARD

`modules/unity-extract/references/jigsawcard-puzzle-case.md` 中标记为专属的内容包括：包名 `com.oakever.jigsawcard`、版本号、`global-metadata.dat` magic `0x94437212`、CDN 域 `jigsaw-cdn.dailyinnovation.biz`、远程包 54 个、AB 实验数/广告网络数、关卡/震动数值等。可以复用其中的方法链（TextAsset 提取、Spine 识别、配置挖掘、策划分析交付模板），不得复用这些字面值。`modules/godot-migration-port/SKILL.md` 内引用的资源数量/材质清单同样属于本案例值。

### CASE_ONLY_MAGICSORT

`modules/godot-migration-port/references/art-remake-playbook.md` 第 7 章标记为专属的内容包括：包名 `com.grandgames.magicsort`、版本 v0.0.2931、Unity 2021.3.57f2、Godot 路径，以及全部实测几何表与教训清单。可以复用其中的决策表、擦除规则和验证流程，不得复用这些坐标、尺寸或颜色采样值；新项目必须从自己的烘焙页重新实测。

## 快速决策示例

新项目出现"特殊材质预览消失"：

1. 使用 `GENERALIZED_PATTERN`：查谁创建预览、谁在 touch-end 隐藏并恢复节点、是否中途切换 handler。

2. 不直接调用 BlockMaster 的 `hideAllPreEliminateEffects()`，也不复制它的事件名。

3. 只有确认新项目也使用同一 10.4.7 基底和相同类后，才把 BlockMaster 文件作为直接代码证据。

这就是范围划分的核心：**通用层提供问题求解方法，案例层提供已发生过的反例和证据形态，当前项目必须重新取得自己的事实。**

## 7.4.0 追加范围

`modules/godot-migration-port/references/native-restoration-gates.md` 的方法为 GENERALIZED_PATTERN，末节版本、数量、指标为 CASE_ONLY_JIGSAWCARD，不可照搬。

## 7.13 原生与运行观测扩展

| 参考 | 范围与边界 |
|---|---|
| `references/native-code-evidence.md` | `GENERAL_DEFAULT`：执行层/地址基准/只读工具；不包含未知 loader 的恢复保证 |
| `references/protected-runtime-recovery.md` | `GENERALIZED_PATTERN`：JNI、mapping、raw/analysis 分离、反混淆/DEX 门禁；壳家族名与偏移不可照搬 |
| `modules/unity-extract/references/managed-native-code-recovery.md` | `GENERAL_DEFAULT`：构建配对、Mono/IL2CPP 分流与方法体证据等级 |
| `references/binary-version-diff.md` | `GENERALIZED_PATTERN`：版本差分候选/核对/提交/回退 |
| `modules/gameplay-logic-reverse/references/observed-runtime-replay.md` | `GENERALIZED_PATTERN`：真实环境观测、第一差异、RNG/状态门禁 |
| `modules/sdk-replacement/references/custom-protocol-evidence.md` | `GENERALIZED_PATTERN`：帧/状态/schema 取证；不替代真机网络验收 |
| `references/minimaxh3-absorption.md` | 本轮材料来源与审查记录；不是目标游戏成功案例 |

## 8.3.0 证据纪律扩展

| 参考 | 范围与边界 |
|---|---|
| `references/unknowns-ledger-template.md` | `GENERAL_DEFAULT`：未知清单格式与闭合规则；交付必附，沉默即违规 |
| `modules/godot-migration-port/references/obligation-ledger-template.md` | `GENERAL_DEFAULT`：Godot 迁移完成定义模板；义务行按当前项目实例化，禁止套用其他项目证据 |
| `modules/skinning-pipeline/references/obligation-ledger-template.md` | `GENERAL_DEFAULT`：换皮完成定义模板；同上 |
| `modules/sdk-replacement/references/obligation-ledger-template.md` | `GENERAL_DEFAULT`：SDK 替换完成定义模板；义务行按档位实例化，档位降级走豁免 |
| `modules/vision-device-testing/references/collection-boundaries.md` | `GENERAL_DEFAULT`：采集负面清单；适用于全部涉及采集的模块 |

`references/binary-version-diff.md` 同版新增证据等级（显式证据/静态候选/仅推断），范围仍为 `GENERALIZED_PATTERN`。

## 8.4.0 广告生命周期与音频范围扩展

| 参考 | 范围与边界 |
|---|---|
| [广告未接入与奖励生命周期](../modules/sdk-replacement/references/ad-fallback-and-reward-lifecycle.md) | GENERALIZED_PATTERN：同步身份、请求/领取幂等、终态、provider顺序与暂停归属；不是任意厂商的固定closed/earned顺序，也不规定统一奖励与时限 |
| [Godot 引擎行为坑集](../modules/godot-migration-port/references/godot-engine-pitfalls.md) §9～11 | GENERALIZED_PATTERN：reparent与离场区别、单写入者、自愈验收、批量音频与WeakRef；当前引擎与场景生命周期须重新验证 |
| [JigsawCard案例](../modules/godot-migration-port/references/jigsawcard-restoration-lessons.md) 2026-10-12 增量 | CASE_ONLY_JIGSAWCARD：广告位、语言键、音频文件/时长、检查数量与路径仅为此案；桌面与注入回调不能升级为Android/厂商验证 |

## 8.5.1 本地能力合并

| 资源 | 范围与边界 |
|---|---|
| `references/host-app-embedded-qqpet-case.md` | `GENERALIZED_PATTERN` + `CASE_ONLY_QQPET`：前台归属、宿主动态包/MMKV/glTF；开关/地址/路径不可复制 |
| `modules/sdk-replacement/references/android-transsion-sdk-suite.md`、`modules/sdk-replacement/references/transsion-material-pack-index.md` | 供应商参考与 `GENERALIZED_PATTERN`：Transsion 分工/契约/素材；配置版本须确认 |
| `modules/sdk-replacement/assets/transsion/`、`modules/sdk-replacement/scripts/extract_transsion_sdk_pack.py` | 接口范式与脱敏回收；不扩大原资产/凭据分发权限 |
| `modules/gameplay-logic-reverse/references/blockmaster-v140-v142-mode-seed-regression.md` | `CASE_ONLY_BLOCKMASTER`：只迁移条件/边界/行为验证方法 |
| `modules/unity-extract/references/unity-ab-extract-and-html-report.md` | `GENERALIZED_PATTERN` + 案例片段：字节/AB/Spine/全文报告；路径数量版本重查 |
| `modules/sdk-replacement/references/seed-copier-generation.md` | `GENERAL_DEFAULT`：参数/布局/标记；桌面测试不代替 Android 验收 |

`references/local-branch-history.md` 只用于旧分支 provenance；安装路径、版本和端口是历史记录，不能当作当前环境事实。
