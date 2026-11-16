---
name: cocos-project-standards
description: "Use when 用户要新建或规范一个 Cocos Creator 工程，或需要工程架构设计、代码规范、接口规范、引擎规范、资源规范、目录与命名、Luban 配置链路、用户数据模块、UI 预制体生成、多语言、构建发布等开发约定；也适用于评审既有 Cocos 工程是否符合规范、接手陌生工程的架构交接、把某个项目的工程约定沉淀为可复用规范。典型触发：怎么写新工程 / 工程规范 / 代码规范 / 接口规范 / 分层规范 / 目录规范 / 命名规范 / 配置表规范 / 数据规范 / 资源规范 / 预制体规范 / 工程评审。"
---

# Cocos 工程规范 (cocos-project-standards)

## 执行卡（先用这张卡，再读正文）

**我管什么**：一个 Cocos Creator 工程**从零到可维护**的工程约定——分层架构（Stage/System/UI/Event/Data/Config 六件套）、代码与命名规范、框架接口边界、Luban 配置链路、用户数据模块、UI 预制体生成链路、资源目录契约、多语言、引擎与构建、交付自检。**不管**逆向解包（走 `cocos-reverse-engineering`）、不管具体界面怎么开发（走 `ui-feature-pipeline`）、不管构建验收取证（走 `cocos-qa`）、不管运行时换肤回写（走 `prefab-bake`）。

**第一步做什么**：**先做工程体检，判定"这套规范里的哪些层能用"**——确认目标工程的：① Cocos Creator 版本；② 是否有自研框架层，若有是哪一个（本总集已验证的是 `driftsand-framework` / `framework_cfw_cocos`）；③ 逻辑层目录骨架是否已存在。**没做完体检不许引用任何 [CFW] 标记的条目**——换框架后那些契约全部失效，照抄会直接写出跑不起来的工程。体检查询与判定表见 `modules/cocos-project-standards/references/logic-layer-architecture.md` 第 1 节。

**做完怎么算完成**：
- [ ] 已产出**工程体检表**：Creator 版本 / 框架层身份与版本 / 逻辑层现有骨架 / 是否新工程
- [ ] 已按体检结果**逐条筛选**规范条目：只采用迁移等级匹配当前工程的行，`[DADA]` 行一律不采用
- [ ] 分层与目录骨架已成文（新建工程）或已**逐项对照出差异清单**（既有工程），差异项标注"符合/偏离/不适用"
- [ ] 六件套契约（Stage/System/UI/Event/Data/Config）每件都写清：基类、必须覆写的方法、创建与访问方式、生命周期钩子顺序
- [ ] 配置链路已确认唯一真源（`datas/Excels/*.xlsx`）并写清产物（schema.ts + data.json）与"派生物禁手改"边界
- [ ] 资源目录契约已写清 bundle 分域与 `icons/` `ui/` `modle/` 的判别依据（"配置 icon 字段→UI 图标 / 模型字段→modle"）
- [ ] 交付附**未知清单**（`references/unknowns-ledger-template.md`）：未取证的钩子、未验证的框架版本、缺失文档逐条登记
- [ ] 已跑 `modules/cocos-project-standards/scripts/check_program_standards.ps1`（结构性门禁），结果与偏离清单一致

**红线（不可违反）**
- **框架层契约不复制，只路由**：框架层的 API 契约（门面、基类、生命周期语义）**以框架仓库自身文档为唯一版本源**；本模块只写"逻辑层如何架在框架之上"。复制一份进来 = 框架升级后产生**双份真相**，必然腐烂
- **项目字面值不进本模块**：具体 System/表/资源名、业务路径、uuid、端口、包名、设备号一律留在项目级 skill（参照 `cocos-asset-config-pitfalls` 的分工）或 `CASE_ONLY_*` 文件。本模块只留"怎么判定"，不留"这个项目是什么"
- **规范条目必须可判定**：每条规则要能判出合规/违规。"代码要优雅""结构要清晰"这类不可判定表述禁止写入；写不出判据就登记为未知，不要凑条目
- **派生物禁手改**：生成器输出的 `.prefab` / `.meta` / `schema.ts` / `data.json` 是派生文件，只能改生成器后重跑。手改派生文件 = 下次生成即丢失
- **不与邻居模块抢职责**：逆向走 `cocos-reverse-engineering`、界面开发走 `ui-feature-pipeline`、烘焙走 `prefab-bake`、构建验收走 `cocos-qa`。重叠处**交叉引用，不复制正文**
- **不宣称工程"已验证合规"**：本模块产出的是约定与对照清单，不是运行证据。工程是否真的跑得起来，由构建与真机验收（`cocos-qa` + `vision-device-testing`）判定

**卡住时按顺序读**
- 不知道该套用哪些层 / 目标工程没有框架层 → `modules/cocos-project-standards/references/logic-layer-architecture.md` 第 1 节（体检表 + 无框架降级方案）
- 分层怎么切、六件套谁访问谁 → `modules/cocos-project-standards/references/logic-layer-architecture.md`
- 命名/日志/事件/注释/空兜底怎么写 → `modules/cocos-project-standards/references/code-and-naming.md`
- 门面纪律、基类职责、UI 注册与打开 → `modules/cocos-project-standards/references/framework-boundary.md`
- 配置表怎么加、怎么改、主键陷阱 → `modules/cocos-project-standards/references/config-pipeline.md`
- 用户数据怎么注册、嵌套为什么不置脏 → `modules/cocos-project-standards/references/data-modules.md`
- 预制体怎么生成、为什么不能手改 → `modules/cocos-project-standards/references/ui-prefab-pipeline.md`
- 图片该放哪个目录、图标为什么必须方形 → `modules/cocos-project-standards/references/resource-contract.md`
- 文案取词、`*_key` 列、语言切换 → `modules/cocos-project-standards/references/i18n-and-text.md`
- 版本/子模块/构建发布 → `modules/cocos-project-standards/references/engine-and-build.md`
- 交付前自检 → `modules/cocos-project-standards/references/delivery-checklist.md`
- 要用另一个 prefab 的版式**替换**现有 prefab、或**批量改** prefab 字段 → `modules/cocos-project-standards/references/prefab-json-batch-editing.md`
- 要从**另一个工程**搬 prefab 及其资源过来 → `modules/cocos-project-standards/references/asset-migration-cross-project.md`
- 要给某系统建"改完自动能验"的静态门禁 → `modules/cocos-project-standards/references/gates-and-verification-scripts.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

## 迁移等级标记（本模块专用读法）

本模块的规则条目全部带迁移等级标记，**必须按标记筛选后使用**。这是本模块与总集三层标签（`GENERAL_DEFAULT` / `GENERALIZED_PATTERN` / `CASE_ONLY_*`）的对应关系：

| 标记 | 含义 | 对应总集标签 | 使用条件 |
|---|---|---|---|
| `[COCOS]` | 任何 Cocos Creator 工程都成立（引擎行为、通用工程实践、目录契约方法论） | `GENERAL_DEFAULT` | 默认可采用，仍需对当前版本实测 |
| `[CFW]` | 绑定 `driftsand-framework`（`framework_cfw_cocos`）这一套自研框架 | `FRAMEWORK_BOUND_CFW`（本总集新增标签） | **仅当体检确认目标工程使用同一框架时**才可引用；否则只借鉴"分层意图"，不照抄 API |
| `[DADA]` | 来源项目（DADAPET）的业务专有值：具体 System/Data/表/资源名与业务逻辑 | `CASE_ONLY_DADAPET` | **禁止采用**，只作"已发生过的实现样例"阅读 |

关于 `FRAMEWORK_BOUND_CFW` 的定义与使用约束，见 `references/scope-map.md`。

## 五类规范与参考文件

| 规范类别 | 参考文件 | 覆盖内容 |
|---|---|---|
| **整体架构设计** | `modules/cocos-project-standards/references/logic-layer-architecture.md` | 体检表、双层分层（框架层/逻辑层）、启动链路、六件套契约、跨系统交互、依赖方向、无框架降级方案 |
| **代码规范** | `modules/cocos-project-standards/references/code-and-naming.md` | 脚本/节点/属性/资源命名、目录骨架、日志前缀、事件 on/off 成对、注释头、空数据兜底、代码纪律 |
| **接口规范** | `modules/cocos-project-standards/references/framework-boundary.md` | 门面纪律（经门面访问 vs 直接 import）、基类职责与继承场景、Stage↔System 访问、UI 注册与打开、LayerType 选择、UI 基类选用 |
| **配置与数据规范** | `modules/cocos-project-standards/references/config-pipeline.md`、`modules/cocos-project-standards/references/data-modules.md` | Luban 链路与两种表布局、字段命名与主键陷阱、`*_key` 多语言列、真源准则；`IUserData` + 注册宏、嵌套对象置脏陷阱、刷盘生命周期 |
| **资源规范** | `modules/cocos-project-standards/references/ui-prefab-pipeline.md`、`modules/cocos-project-standards/references/resource-contract.md` | 预制体生成链路与 UIBindings、派生物禁手改、语义命名；bundle 分域、`icons/` `ui/` `modle/` 判别依据、图片导入规范、图标方形与 `trimType` |
| **多语言** | `modules/cocos-project-standards/references/i18n-and-text.md` | 统一取词门面、`*_key` 列约定、回退文案保留、语言切换订阅 |
| **引擎与构建** | `modules/cocos-project-standards/references/engine-and-build.md` | Creator 版本锁定、框架子模块/junction 装配、构建发布边界 |
| **交付自检** | `modules/cocos-project-standards/references/delivery-checklist.md` | 交付前逐项自检清单 + 门禁脚本用法 |
| **预制体与 JSON 编辑** | `modules/cocos-project-standards/references/prefab-json-batch-editing.md` | 承原 meta/uuid 替换 prefab 内容、组件注入、`__id__` 索引重映射与 `PrefabInfo` 自引用、批量改字段四步法与 **diff 规模自证**、压缩 uuid 校验、编辑器协同与覆盖风险 |
| **跨工程移植** | `modules/cocos-project-standards/references/asset-migration-cross-project.md` | 前置四项核对（分辨率/共享依赖同 uuid/冲突/源有无控制器）、**递归依赖挖掘**、**隐性依赖**（不在 prefab 里的工程级共享行为组件）、带 `.meta` 保 uuid、旧资源"该删 vs 删了会坏"判据 |
| **校验与门禁** | `modules/cocos-project-standards/references/gates-and-verification-scripts.md` | 专项 `verify_*` 静态门禁的形态与统一约定（`ROOT=parents[N]` / `fail()` / `utf-8-sig`）、三类断言（配置形状 / 代码接线 / prefab 结构）、与总集门禁脚本分工、**静态证据不能替代运行验收** |

## 与其他模块的边界

| 任务 | 走哪个模块 |
|---|---|
| 拿到的包是别人的产品，要识别/解包/解密 | `cocos-reverse-engineering` |
| 要**开发一个新界面**（效果图→控件切分→重组→视觉 QA→烘焙） | `ui-feature-pipeline` |
| 要把运行时换肤结果**固化回 prefab** | `prefab-bake` |
| 要**构建出包 / 模拟器真机验收 / 截图 QA** | `cocos-qa` + `vision-device-testing` |
| 工程打不开、黑屏、`.fire`/prefab 引用悬空 | `cocos-creator-repair` |
| 要 **AI 操作 Cocos 编辑器**做中间自检 | `cocos-mcp-channel` |
| **新建工程、定规范、评审工程结构、写交接文档** | **本模块** |

### 同一根因散在多处时的归属划分（防漂移）

本模块的「图标 `trimType` 拉伸」与「配置与产物不同步导致黑屏」两条经验，来自同一个项目的真实事故，目前**在三个位置都有表述**。必须明确各自职责，否则三处必然漂移：

| 位置 | 承担什么 | 不承担什么 |
|---|---|---|
| `modules/cocos-creator-repair/SKILL.md` | **诊断入口**：症状 → 定位 → 修复结论（「预览黑屏」「图标拉伸」两节） | 不写规范条文与预防流程 |
| `cocos-asset-config-pitfalls`（**项目级 skill，不在本总集内**） | **该项目的操作 SOP**：具体表格、脚本名、命令、git 流程 | 不作为通用规范被其他项目引用 |
| 本模块（`modules/cocos-project-standards/references/resource-contract.md` §4、`modules/cocos-project-standards/references/config-pipeline.md` §8） | **通用规范与预防**：图标导入契约、配置真源准则与安全流程 | 不复制项目路径与脚本名 |

**维护纪律**：该根因一旦有新发现，**先改诊断入口**（`cocos-creator-repair`），再判断是否需要上升为通用规范；**规范条文只在本模块维护一份**，诊断入口用交叉引用、不复制正文。这是本模块「重叠处交叉引用，不复制正文」红线在真实案例上的落地。

## 来源与范围

本模块的规则提炼自一个真实投产的 Cocos Creator 3.8.7 宠物养成项目（DADAPET，`cocos_dadapet`），其规范文档位于该项目 `docs/程序/` 与 `docs/推进/00_通用开发规范.md`。该项目的具体字面值为 `CASE_ONLY_DADAPET`，**不可复制**（`DO_NOT_COPY_LITERAL_VALUES`）。

需要特别说明的**已知缺口**（下沉时如实登记，不臆造）：

- 来源项目的 `README.md` 与框架层文档引用了 5 份架构文档（`docs/新逻辑层框架定义.md`、`docs/architecture.md`、`docs/加载器与Stage架构.md`、`docs/data-storage.md`、`docs/数据存储模块-方案.md`），**实测在仓库中全部不存在**。因此本模块的「整体架构设计」是**从代码与既有碎片重建**的，不是转录现成文档；重建过程与未取证项见 `modules/cocos-project-standards/references/logic-layer-architecture.md` 末节与 `modules/cocos-project-standards/references/landing-log.md`。
- 来源项目框架层自带 20 份框架文档（`extensions/framework_cfw_cocos/doc/`），按红线**不复制**，只在本模块登记路由。

落地记录与迭代见 `modules/cocos-project-standards/references/landing-log.md`。
