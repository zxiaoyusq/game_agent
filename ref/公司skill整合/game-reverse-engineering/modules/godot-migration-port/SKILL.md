---
name: godot-migration-port
description: Use when 用户要把 Unity/Cocos 逆向提取出的工程包与美术资源迁移或重建为 Godot 可编译、可运行、可二开的同款游戏，或继续修复已有 Godot 重制工程的玩法、原切图 UI、Spine、粒子、音频、后期系统、配置、SDK 接口与 Android 验收。提供 S0–S7 端到端生产流程、证据状态、阶段门禁和专项参考路由；不用于没有原版证据的自由改版。
version: 1.10.0
updated: 2026-10-12
author: bai-lian
tags: [godot, godot-migration, unity-to-godot, migration, rebuild, asset-import, spine, tween, ui, shader, localization, export, landing-log]
triggers: [godot 重建, 还原 godot 工程, unity 转 godot, 迁移到 godot, godot 迁移, godot 二开, 用 godot 重新实现, godot 版本, godot 4.6, godot 工程]
---

# Godot 迁移/重建桥 (godot-migration-port)

## 执行卡（先用这张卡，再读正文）

**我管什么**：把 Unity/Cocos 逆向提取出的工程包与原美术资源迁移、重建为 Godot 4.6.2 可编译、可运行、可二开的同款游戏（含 S0–S7 阶段流程与专项参考路由）；不管没有原版证据的自由改版，也不复制任何外部 godot-* 技能正文。

**第一步做什么**：读 `modules/godot-migration-port/references/end-to-end-restoration-workflow.md`，用 `inventory_only/static_confirmed/runtime_observed/controlled_runtime_confirmed/implemented/verified/fitted/unknown` 建覆盖矩阵，把每个资产/系统的当前状态逐项标出来。

**做完怎么算完成**：
- S0–S7 覆盖矩阵已落盘，每项资产/系统都取 8 个证据状态之一，未知项显式标 `unknown`。
- 原始字节备份存在，原版与重制版本谱系已记录。
- 每个里程碑都在 `modules/godot-migration-port/references/landing-log.md` 留下一行（实际结果/偏差/回填动作）。
- 进入下一阶段所需的"核心证据"逐条可指认，不是"看起来好了"。
- 每个缺口都走完"基线→差距→owner→单变量实验→最小修复→分层回归"闭环。

**红线（不可违反）**
- 不许跳阶段：严格按 S0–S7 顺序推进，前一阶段的进入证据没齐不得开工下一阶段。
- 证据状态只能从那 8 个值里选，不许自造词，更不许把"导入成功"当 `verified`。
- GDExtension 二进制跨版本不兼容：Spine 等插件必须用 4.6 构建版，否则用同版本源码自编（godot-cpp 同版本），禁止只改版本字符串。
- IL2CPP 下 `.cs` 不可还原：逻辑代码只能重写，不许声称还原了源码逻辑。
- 案例数字（jigsawcard 的图集/纹理/精灵/材质/关卡数量）属案例证据，不得复制到其他项目。

**卡住时按顺序读**：
- 不知道当前在哪个阶段、下一阶段要什么证据 → `modules/godot-migration-port/references/end-to-end-restoration-workflow.md`。
- 原切图、Sprite 几何、Prefab 固化、包体问题 → `modules/godot-migration-port/references/native-restoration-gates.md`。
- 引擎行为异常（粒子、命中树序、导航演出、字体行框、导出互斥）→ `modules/godot-migration-port/references/godot-engine-pitfalls.md`。
- Spine 导入/播放/ABI 异常 → `modules/godot-migration-port/references/godot-spine-integration.md`。

全局五步循环与六条铁律见 `references/execution-protocol.md`。

## 适用范围

- `GENERAL_DEFAULT`：资产盘点方法、迁移清单映射、S0–S7 端到端生产流程、证据状态、阶段门禁和工具矩阵。
- `GENERALIZED_PATTERN`：从 jigsawcard（Unity 6000.3.16f1 IL2CPP）重建评估提炼的迁移点分类与优先级方法。**该案例的资源数量、材质/Shader 清单、关卡数与评估结论属于 `CASE_ONLY_JIGSAWCARD`**，其他项目必须重新统计自己的清单。
- 不复制 GodotPrompter / gstack-game / claude-code-game-studios 任何技能正文；本模块只定义"迁移映射"与"何时加载哪个技能"（见 `references/external-game-skills.md`）。

## 目标与基线

- 目标：用解析出的工程包（AssetRipper/UnityPy 输出）+ 原美术资源，在 **Godot 4.6.2 stable**（本机 `${GODOT}`）重建"可编译、可运行、可 AI 二开"的同款游戏。
- 技能基线：全部 godot-* 技能声明 `4.3+`，与 4.6.2 兼容。**GDExtension 二进制跨版本不兼容**：godot-spine 等插件必须使用为 4.6 构建的版本，否则一律源码自编（godot-cpp 同版本）。
- 代码基线：IL2CPP 下 `.cs` 不可还原 → 逻辑代码重写；序列化资产（prefab/场景/材质/动画/图集）可还原 → 优先保住"资产 1:1 + 逻辑重写"。

## 使用顺序

先读 [端到端生产流程](references/end-to-end-restoration-workflow.md)，用统一的 `inventory_only/static_confirmed/runtime_observed/controlled_runtime_confirmed/implemented/verified/fitted/unknown` 状态建立覆盖矩阵，再按问题加载专项参考：

- 原切图、Sprite 几何、Prefab 固化与包体：`native-restoration-gates.md`。
- Godot 引擎行为坑（gl_compatibility 粒子、命中树序、导航演出、生成器排版、字体行框、翻译启动、内存口径、导出互斥、看门狗）：`godot-engine-pitfalls.md`。
- Spine 插件、版本、资源链、轨道与 ABI：`godot-spine-integration.md`。
- 广告未接入反馈、奖励回调、重复领取与后台弹窗：读 SDK 模块的 [广告生命周期](../sdk-replacement/references/ad-fallback-and-reward-lifecycle.md)，通用契约只维护这一份。
- 已发现差距的 owner 定位、最小修复和四层回归：`restoration-gap-to-qa.md`。
- 只有用户明确接受整页截图底图时：`art-remake-playbook.md`。
- 项目专属数字和结果：`jigsawcard-restoration-lessons.md` 或相应案例文件。
- 完成定义与交付收口：[义务清单模板](references/obligation-ledger-template.md)，S5/S7 收口前逐条关闭，关闭条件与反例见文内。

入口流程负责阶段和交付边界，专项参考负责具体技术，案例文档只保存字面证据。不要把三者复制成多套互相冲突的工作流。

## 迁移清单（十二类，按优先级）

| # | Unity 资产/系统 | Godot 对应 | 难度 | 要点/插件 |
|---|---|---|---|---|
| 1 | 2D 纹理/精灵/图集 | Texture2D / AtlasTexture / SpriteFrames | A | 保留原始 PNG；图集用 AtlasTexture 子区域引用（案例 jigsawcard：762 图集纹理 + 1081 纹理、959 精灵；其他项目重新统计） |
| 2 | SpriteAtlas | AtlasTexture + SpriteFrames | B | Unidot Importer（AnEntrypoint/Godot-Unidot-Importer）或自写导入器；先导入再人工复核引用 |
| 3 | DOTween 动画序列 | Tween / create_tween / AutoFree | B | 复用 tween-animation / animation-system 技能；注意缓动曲线与原版逐帧差异 |
| 4 | Spine（案例 46 套） | godot-spine（GDExtension） | B+ | **必须 4.6 构建版**；3.8 JSON+Atlas；db2spine-spine38-qa 可先校验骨骼文件 |
| 5 | Coffee.UIEffect | CanvasItem shader 改写 | B+ | 无现成 GitHub 技能；按源码/文档自写 UIGradient/UIShadow/UIRipple 等，落地后回填经验 |
| 6 | UIParticle | GPUParticles2D | B | particles-vfx 技能；粒子挂 UI 图层需注意 CanvasLayer 与 z 序 |
| 7 | AnimationClip（案例 815 个） | AnimationPlayer | B+ | prefab-animation-converter（surendra019）或自写转换；**先迁移关键路径动画**（开局/消除/结算），其余按频率 |
| 8 | RTLTMPro（阿拉伯语等） | TextServer Advanced + TranslationServer | B | localization 技能；Godot 4.6 RTL/文字塑形更成熟，但文字安全框/缩放需实测 |
| 9 | i2 Localization | TranslationServer + CSV/PO | A | localization 技能；key 命名与语言列表需从原项目导出再映射 |
| 10 | ParticleSystem（案例 1508 个） | GPUParticles2D | C | 只迁移"看得见、有功能属性"的关键特效；其余降级/省略并在交付说明标注 |
| 11 | Shader/材质（案例 76 材质 382） | CanvasItem/StandardMaterial + 自写 shader | C | 80/20：先 UI 与最高频材质；每个还原项记 landing-log（还原度、偏差） |
| 12 | SDK（Pangle/Firebase/Facebook/MCPForUnity） | Godot 插件或占位接口 | C | 只做接口桩 + 真机降级；广告/埋点留到发布日期前，按"原 owner 调用点"接入 |

## Godot 接入 Spine 的通用方法

Spine 迁移不能停在“文件已导入”或“编辑器能显示”。先选与当前 Godot 小版本和 Android ABI 匹配的 GDExtension，核对源 Spine minor、目标 runtime、骨骼数据、atlas 页面、PNG、材质和 SkeletonData 的完整引用链；版本不匹配时完整转换或同版本源码编译，禁止只改版本字符串。然后将骨骼数据、atlas 和材质保存为可复用 `.tres`，在 `.tscn` 中预置固定 `SpineSprite`（或插件等价节点）宿主，运行时通过小型适配层查找并复用节点，负责 setup pose、clear tracks、主轨道/overlay 轨道、loop、后续动画、停止和生命周期取消。编辑器预览只显示固定宿主，不保存运行状态；业务播放必须由原版 owner 和稳定事件触发。完整资源链、适配器伪代码、失败模式和桌面/Android 验收矩阵见 [godot-spine-integration.md](references/godot-spine-integration.md)。

## S0–S7 阶段摘要

| 阶段 | 目标 | 进入下一阶段的核心证据 |
|---|---|---|
| S0 | 范围、版本、设备、存档和覆盖矩阵 | 原版/重制版本谱系、原始字节备份、未知项已标记 |
| S1 | 资产身份、转换和导入 | 引用链与哈希可追溯，headless 导入无缺失 |
| S2 | 玩法、数据、存档和事务语义 | 真实输入回放、状态快照、幂等和生命周期回归 |
| S3 | 原切图 UI、Spine、音频、粒子和固定 Prefab | 编辑器可编辑，桌面同状态/同阶段视觉与音频验证 |
| S4 | 跨页面演出、后期系统、快照配置和 SDK 契约 | 显式 payload 调用链、快照/provider 消费者测试、取消与重入 |
| S5 | 静态→逻辑→桌面→Android→原版对比的分层 QA | 目标矩阵项达到 `verified`，残差仍标 `fitted/unknown` |
| S6 | 最终 APK、签名、包内资源和设备验收 | 证据绑定最终包哈希，存档/设置测试前后逐字节一致 |
| S7 | 报告、交接、Skill 回填和版本校验 | 新 Agent 可从落盘资料继续，Skill 结构与引用校验通过 |

完整步骤、配置优先级、后期状态矩阵、设备自动化陷阱和最小交付物见 [end-to-end-restoration-workflow.md](references/end-to-end-restoration-workflow.md)。每个缺口内部仍使用 [restoration-gap-to-qa.md](references/restoration-gap-to-qa.md) 的“基线→差距→owner→单变量实验→最小修复→分层回归”闭环。

## 工具与外部技能映射

| 任务 | 加载 |
|---|---|
| 2D 资产/关卡 | 2d-essentials / assets-pipeline |
| 动画与补间 | animation-system / tween-animation |
| UI | godot-ui / responsive-ui |
| 粒子 | particles-vfx |
| 本地化/RTL | localization |
| 求解/玩法算法 | gameplay-logic-reverse（先定位原 owner，再重写语义） |
| 逆向资产提取 | unity-extract（本总集） |
| 骨骼校验 | db2spine-spine38-qa（本总集） |
| 真机验收 | vision-device-testing（本总集） |

## 落地迭代（本模块强制）

- 每个里程碑完成后立即把"实际结果/与预期偏差/回填动作"记入 `modules/godot-migration-port/references/landing-log.md`（模板即该文件表头）。
- 缺失能力（如 shader 还原比例、godot-spine 版本矩阵、导入器成功率）由落地数据驱动回填到本模块与 `references/scope-map.md`，并 bump 版本。
- 不把任何 godot-* 外部技能正文抄进本模块；需要变更外部技能时，记入落地日志并单独维护对应仓库。

## 参考

- `modules/godot-migration-port/references/end-to-end-restoration-workflow.md`（主流程：S0–S7、证据状态、配置优先级、后期系统、分层 QA、最终 APK 与交接）
- `modules/godot-migration-port/references/landing-log.md`（落地记录模板）
- `modules/godot-migration-port/references/art-remake-playbook.md`（美术重制 playbook：单层纪律决策表 / 纹理色值反查 / 烘焙页擦除规则 / 动态组件同位 / Godot GDScript 坑 / 双证据验收清单）
- `modules/godot-migration-port/references/godot-spine-integration.md`（GENERAL_DEFAULT/GENERALIZED_PATTERN：Godot Spine 插件、资源链、固定宿主、播放适配层与跨平台验收）
- `modules/godot-migration-port/references/restoration-gap-to-qa.md`（GENERAL_DEFAULT/GENERALIZED_PATTERN：原版差距发现、对齐定位、最小修复、自行 QA、失败诊断与回归交付闭环）
- `modules/godot-migration-port/references/obligation-ledger-template.md`（完成定义与逐条关闭的义务清单；交付时随未知清单一并交付）
- `references/external-game-skills.md`（外部技能注册表）
- `references/scope-map.md`（范围标签）
- `modules/unity-extract/SKILL.md`（上游提取）

## 原生还原追加门禁

原切图、Spine、功能与场景固化任务必读 [native-restoration-gates.md](references/native-restoration-gates.md)。

已验证的 JigsawCard 案例回填见 [jigsawcard-restoration-lessons.md](references/jigsawcard-restoration-lessons.md)；其中数字、路径、哈希和关卡值均为案例证据，不得复制到其他项目。

## 初始化 Godot 工程

迁移范围已明确且需要新建空工程时，按 `references/external-game-skills.md` 路由到 `godot-project-setup`；初始化不关闭 S0–S7 资源/运行/最终 APK 义务。
