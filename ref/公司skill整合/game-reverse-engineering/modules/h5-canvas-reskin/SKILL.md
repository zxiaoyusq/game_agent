---
name: game-h5-canvas-reskin
description: Use when 用户要给成品 AHA / H5 / canvas 游戏换皮，包括尚无效果图、目标市场或风格未定，需要 HTML 选择引导、GPT 生图、素材合入与运行 QA；或需要保持尺寸、命名与图集契约，处理平铺接缝、功能辨识及输入停摆。
version: 2.0.0
created: "2026-10-23"
author: bai-lian
tags: [reskin, skinning, h5, html5, canvas, phaser, webview, apk, atlas, tiling, alpha, luminance, visual-hierarchy, runtime-diagnosis, cdp, freeze]
triggers: [AHA换皮, 换皮方向未定, 没有效果图, HTML设计评审, 目标市场, H5换皮, canvas游戏换皮, Phaser换皮, webview换皮, 平铺背景重绘, 拼图没拼上, 接缝, 底板发暗, 深色块, 背景太花, 四级配色, 特效看不清, 卡死无法拖动, 拖不动, 输入锁死, 色相回锁, 图集契约, h5 reskin]
---

# H5 / Canvas 游戏换皮流水线 (game-h5-canvas-reskin)

## 执行卡（先用这张卡，再读正文）

**我管什么**：通过 HTML 引导成品 **AHA / H5 / canvas 游戏**从市场与产品方向、概念图选定、GPT 素材生产走到实际合入和 QA。保持原尺寸、命名、实际 alpha 语义和图集契约，并按用户指定平台逐屏对照。不处理引擎解密或 Cocos/Unity 预制体；引擎未知先做必要识别后路由。

**第一步做什么**：先检查已有 `reskin-state.json`、用户已给信息和明确授权。有有效设计就沿用、跳过重复问卷；无方向/无效果图时，先读 [方向预输入](references/intake-and-direction.md)，用 [HTML 工作台](references/html-workbench.md) 主动给出目标市场、用户和产品方向选择题，不要求用户先准备完整效果图。此时只核对原游戏入口与少量代表画面，不展开全库制作准备。选定方向后调用 GPT 生图形成项目概念候选；具体设计与计划明确后，按 [全程编排](references/end-to-end-orchestration.md) 连续推进：**代表屏落地 → 同族批量生产 → 累计回填 → 集中 QA → HTML 交付**。技术细节仍走 [散件定位](references/component-restoration.md) 和 [背景参考](references/background-reference-workflow.md)。

**做完怎么算完成**：
- [ ] 无方向时通过 HTML 明确市场/产品简报与风格组合；已有有效目标不重复索要选择
- [ ] GPT 生图现行风格/地区配色按需读取；具体设计图、版本及用户选择可追溯，旧 M 编号没有静默改义
- [ ] 实施前已主动展示逐项步骤、范围和验收平台；HTML 选择有真实回传与导入回显，未采用选择不冒充已确认
- [ ] 工作台持续显示有效素材、合入和 QA 各自进度；状态可续接，设计变更使受影响证据失效
- [ ] 全量资源有轻索引和分类；已替换资源有足够用途/装配证据，未覆盖项写明原因，不强制全库精确定位
- [ ] 实际替换件关联对应目标局部或标明母版推导/缺参考，记录生产版本与技术、视觉状态；失败按授权集中处理或明确未通过
- [ ] 定位不明或高风险散件按需用原版复原验证；替换后按原版/目标/用户指定的 H5 或设备实际画面三列复验
- [ ] 尺寸 / 文件名 / 图集页尺寸 / 帧完整性 / **非美术文件逐字节**全部一致（仅换美术时不允许游戏代码补丁；壳必要差异单列）
- [ ] 按逐项技术契约检查；仅实际遮罩/轮廓约束或用户要求的条目锁原 alpha
- [ ] 拼接类检查真实相接顺序和完整画面，不靠像素差单独判无缝；量化阈值按项目与用户要求确定
- [ ] 玩法对象保持可辨识的功能色；色相变更按项目要求验证，不把旧值作为所有目标的强制阈值
- [ ] 按目标和实际可读性检查前景、交互区与背景层级
- [ ] 背景保留要求的空间结构和目标装饰；不要用单一边缘密度阈值删除用户指定主景
- [ ] 按用户指定的 H5、模拟器或真机来源执行自然交互；记录真实来源与覆盖范围，不把调试调起冒充自然解锁
- [ ] 稳定性：**确定性枚举入口**跑过一遍，画面/逻辑停摆检测无告警
- [ ] 交付报告附**未解决项清单**；失败就写失败，不写"应该没问题"

**红线（不可违反）**
- **缺方向先引导，缺效果图先设计**：不能直接批量生图，或只登记缺参考后等待用户自行提供方案。方向确认前可做少量原版核对，不能用全量拆解替代产品讨论。
- **HTML 是主要沟通面**：问卷、设计评审、实施计划、进度、三列对照和验收均在同一工作台呈现。短消息只引导打开/提交。离线选择单须由 AI 实际导入；宿主回传只在真实支持时启用。默认勾选、页面保存、下载或等待超时都不是确认。
- **选型与生成分工明确**：先读 GPT 生图的美术指导与现行风格库；形式、配色、当地题材和玩法功能色分列。概念探索与正式素材生产分别调用生图技能，不把概念图当运行素材。已有授权范围连续推进，不逐件重复批准；暂停必须显式恢复。
- **按真实契约分流**：用户要求 UI 轮廓不变时，以原资源作几何母版，只重绘轮廓内部；禁止先生成新造型，再缩放、裁切或强贴原 alpha 补救。独立图标能否缩放或重绘须按实际占位、状态和用户要求判断。
- **技术约束与目标样式分列**；普通底板/按钮不因九宫格或家族名一律锁旧alpha/只换色。仅契约要求时回写原alpha，先配准RGB主体再查透明边缘；明暗以批准目标为准，不能强行回原亮度破坏新画法。柔光/加色特效保原配色与alpha，纯旋转资源按转轴和占位决定可重绘范围。
- **玩法对象的功能辨识优先**：色相变化按用户目标和玩法契约验证；只有用户要求或运行证据表明必须保留原色时才回锁，不以来源案例阈值作为通用规则
- **原版证明定位与技术契约，批准效果图证明美术目标**；指标用于定位问题，不代替逐件视觉与运行验收。
- **用户选定的候选是工作基准**：技术缺陷如接缝或裁切单独标记、局部修复，不因未通过技术检查擅自替换或丢弃已认可的视觉方案。正式采用仍须通过相关检查；必要时可明确标注原版临时占位，不能冒充选定方案。
- **仅换美术时不改游戏JS/HTML/CSS/布局/图集坐标**。代码修复提交最小提案，获额外授权才实施；显式声明补丁不等于已获授权。
- **修复必须用原始触发路径反证**；只跑一遍新路径不算数
- 覆盖前必须备份；禁止只信复制动作或沿用旧清单

**卡住时按顺序读**
- 没有方向/效果图、目标市场或风格未定 → [方向预输入](references/intake-and-direction.md)（先读）
- HTML 如何选择、回传、确认、展示进度或恢复 → [HTML 工作台](references/html-workbench.md)
- 设计已定，下一步怎么生成、合入、QA → [全程编排](references/end-to-end-orchestration.md)
- AHA换皮/散件认不出/效果图还原不准 → [散件定位到运行还原](references/component-restoration.md)（必读）
- 不知道怎么分类 → [四类分流与按类执行](references/pipeline.md)
- 用户说了一句主观的话（太花 / 不明显 / 看不清 / 拖不动）→ [主观抱怨 → 可测指标](references/complaint-to-metric.md)
- 游戏"能跑但操作无反应" → [运行时诊断](references/runtime-diagnosis.md)
- 用户授权同时做关卡/UI 二开或需要区分高 DPI 画布与页面坐标 → [关卡工具与迭代交接](../hosted-minigame-harvest/references/iteration-editor-and-delegation.md)；仅美术任务仍遵守本模块的非美术变更限制。
- 打了补丁却没用 → [上游缺陷模式](references/upstream-defect-patterns.md)
- 想确认自己没在重复错误做法 → [错误流程汇总](references/wrong-approaches.md)
- 要动手写/改工具 → [工具接口说明](references/tooling.md)

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERALIZED_PATTERN`。本模块的**方法与判据**可迁移到其他 H5/canvas 游戏；文中所有实测数值、包名、端口、路径均来自来源案例，**必须按当前项目重新获取**，不得照抄。
详见 [适用范围地图](../../references/scope-map.md)。

## 与相邻模块的边界

| 情形 | 去哪 |
|---|---|
| Cocos 2.x/3.x、Unity、JSC/HEK 解密、图集重建（Godot/Spine） | `modules/cocos-reverse-engineering`、`modules/unity-extract`、`modules/skinning-pipeline` |
| 只做结构/动作/轮廓锁定的通用换皮 | `modules/skinning-pipeline`（本文档的中立原理与之相通，但工具与判据不同） |
| 引擎未知、要先识别是不是 Phaser 2/3/4 | `modules/engine-identification` |
| 真机截图/OCR/Logcat 验收的通用手段 | `modules/vision-device-testing` |

**不要把 Godot/Spine 那边的命令照搬到 canvas 游戏**，反之亦然。

## 与 Godot/Spine 那边的相通之处与不同之处

**相通的方法**（可互相印证）：按契约配准主体 / 必要时锁alpha / 按批准目标重画 / 原版定位复原 / 先备份后覆盖 / 失败就是失败。

**不同的手段**：那边靠 `.tres` 的 `Rect2` 与 `--headless --import` 重导；
这边靠 **WebView 调试协议（CDP）** 取运行时证据，且要面对
**实机证据截图须走对应设备通道；浏览器 H5 截图标明浏览器来源**、**图片后缀可能是伪装的 WebP**、**没有文件级"重新导入"这一步**。

## 快速索引

| 文件 | 内容 |
|---|---|
| [intake-and-direction.md](references/intake-and-direction.md) | 先问市场与产品，接入现行 GPT 生图风格，概念比较与设计锁定 |
| [html-workbench.md](references/html-workbench.md) | 初始化、回传导入、项目状态、图片与完成度、恢复执行 |
| [end-to-end-orchestration.md](references/end-to-end-orchestration.md) | 各阶段用户交互、执行动作、证据与完成条件 |
| [render_workbench.py](scripts/render_workbench.py) | 标准库 CLI：init / render / import / validate；读取当前风格来源 |
| [workbench.html](assets/workbench.html) | 渲染器使用的自包含页面模板；不直接打开未渲染模板 |
| [component-restoration.md](references/component-restoration.md) | 轻索引、按风险定位、目标样式提取与新资源装配回归 |
| [pipeline.md](references/pipeline.md) | 四类分流判据、按类执行、按类门禁、容器契约、打包与真机 QA |
| [complaint-to-metric.md](references/complaint-to-metric.md) | 把"太花 / 不明显 / 看不清 / 拖不动"翻译成可测量 |
| [runtime-diagnosis.md](references/runtime-diagnosis.md) | 「能跑但拖不动」、逻辑停摆 vs 画面停摆、取证纪律 |
| [upstream-defect-patterns.md](references/upstream-defect-patterns.md) | 上游缺陷模式 + 一行修法 + 补丁纪律 |
| [wrong-approaches.md](references/wrong-approaches.md) | **错误流程汇总**：做过的错做法，逐条对照 |
| [tooling.md](references/tooling.md) | 每个工具的职责/输入输出/关键算法（按需重实现或参数化） |
