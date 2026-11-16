# 落地记录（cocos-project-standards）

> 迭代协议见根 `SKILL.md`「落地迭代协议」。每次项目里程碑**立即追加**一行，不凭记忆补写。
> 单个文件超过 20KB 时把较早条目整体移入同目录 `landing-log-archive-<YYYYQn>.md`。

## 记录格式

| 日期 | 阶段 | 实际结果 | 与预期偏差 | 回填动作 | 验证 |

---

## 2026-10-26 · 模块创建（首轮沉淀）

| 项 | 内容 |
|---|---|
| **阶段** | 模块建立与首轮内容下沉 |
| **来源** | Cocos Creator 3.8.7 项目 DADAPET（`cocos_dadapet`），规范文档位于该项目 `docs/程序/` 与 `docs/推进/00_通用开发规范.md` |
| **实际结果** | 新建模块 `cocos-project-standards`：`SKILL.md`（执行卡 + 迁移等级标记 + 五类规范路由 + 边界表）+ 10 份 reference + 1 个门禁脚本 + 本文件 |
| **与预期偏差** | 见下方「来源文档缺陷」——**来源项目 README 引用的 5 份架构文档全部不存在**，故「整体架构设计」一册为**从代码与碎片重建**，非转录 |
| **回填动作** | 新增总集范围标签 `FRAMEWORK_BOUND_CFW`；根 `SKILL.md` 增任务分发表行、路由表行、标签定义；`scope-map.md` 登记模块与参考文件；`validate_skill.ps1` 登记模块并补两处漏登记；`CHANGELOG.md` 记 10.0.0 |
| **验证** | `scripts/validate_skill.ps1` 全绿；模块 `SKILL.md` 四块执行卡标记齐备；`description` 以 `Use when` 开头 |

### 未闭合项（如实登记）

- **工程运行态未验证**：本模块产出的是**约定与对照方法**，**未宣称**任何工程"已符合规范"或"已通过验收"。构建与真机验收走 `cocos-qa` + `vision-device-testing`。
- `getRequiredResources` / `getBackgroundResources` 的精确消费时机未逐行取证。
- 响应式存储 v2（`common/storage/reactive/`）设计说明缺失（来源 `docs/data-storage.md` 不存在），当前内容由 `DataMgr` 代码反推。
- 热更 / 远程配置 / ABTest 的业务侧使用规范未取证。
- 代码风格层面（缩进/引号/lint）来源项目无成文规范。

### 来源文档缺陷（重要，供后续对照时避坑）

下沉过程中实测到来源项目文档存在**自相矛盾与过时**。本模块已按"与代码/meta 实测一致的一侧"裁决，列表如下：

| # | 缺陷 | 本模块裁决 |
|---|---|---|
| 1 | `.clinerules` 称"单一 bundle 按域拆子目录"，`目录结构规范.md` 把各域称作"bundle" | 实测 `assets/bundle.meta` 的 `userData.isBundle=true`，各域 meta 的 `userData={}` → **单一 bundle + 资源域**；已在 `resource-contract.md` 第 1 节写明并提示不要沿用"多 bundle"措辞 |
| 2 | 图片落地路径一处写 `lobby/images/{asset}.png`，另一处写 `images/icons|ui` 拆分 | 采用**按用途二分**（实测目录为 `images/{common,icons,ui}`），见 `resource-contract.md` 第 2 节 |
| 3 | 图标子目录文档写 `{food,dress,avatar,misc}`，实测另有 `back/`，且 `dress/` 下有 `collar/face/head`、`food/` 下有 `big/` | **类别表按项目重新派生**，不复制来源清单 |
| 4 | 生成器输入路径一处写 `art/v1`，另一处写优先 `art/美术设计/data/` 回退 `art/v2/` | 记录为冲突，以实际脚本为准；已在 `ui-prefab-pipeline.md` 第 9 节登记 |
| 5 | 旧全局事件 `LANGUAGE_CHANGED` 仍被列在全局事件表，同文另一节又禁止监听旧 `LanguageChanged` | 采用**禁止监听旧事件**一侧，见 `i18n-and-text.md` 第 1、4 节 |
| 6 | 导表命令不一致（`gen_excels.py` + `merge_config_data.js` vs `merge-json.js`，且前者本应默认拒绝执行） | 采用**真源准则 + `merge-json.js`** 一侧，见 `config-pipeline.md` 第 1、2 节 |
| 7 | UI 继承描述覆盖范围不一致（`BaseUI` vs `cc.Component` vs `SlideUpUI`） | 按**场景选基类**三者并存，见 `framework-boundary.md` 第 5 节 |
| 8 | `00_通用开发规范.md` 第 7 节存在**未闭合的 Markdown 代码块**，正文结构损坏 | 仅提炼其规则语义，未复制其排版 |

### 待回填触发器

- 若后续第二个工程落地本模块，需回填：**框架层版本耦合矩阵**（框架版本 ↔ 引擎版本 ↔ 破坏性变更）。
- 若出现"同一规范在两个项目行为不同"的案例，需在对应 reference 增加**项目差异节**，而不是改写成更模糊的表述。

---

## 2026-10-26 · 接线与验证（第二轮）

| 项 | 内容 |
|---|---|
| **阶段** | 全量接线 + 验证器跑绿 |
| **实际结果** | ① 根 `SKILL.md`：适用标签表加 `FRAMEWORK_BOUND_CFW` 行、任务分发表加"新建 Cocos 工程 / 工程规范"行、路由表加一行、description 与 tags/triggers 补关键词、`metadata.version` 9.1.0→**10.0.0**；② `references/scope-map.md`：新增 `FRAMEWORK_BOUND_CFW` 标签定义节、模块行、参考文件行、通用默认内容行；③ `references/CHANGELOG.md`：新增 **10.0.0** 条目；④ `scripts/validate_skill.ps1`：`$modules` 登记新模块并补两处历史漏登记，scope-map 标记断言加 `FRAMEWORK_BOUND_CFW` / `cocos-project-standards`；⑤ 邻居模块交叉引用 4 处：`cocos-reverse-engineering`（新增「逆向之后的工程化」衔接节）、`ui-feature-pipeline`（新增「工程规范（本模块的前置约定）」节）、`prefab-bake`（派生文件禁手改回指）、`cocos-mcp-channel`（分流表加一行） |
| **与预期偏差** | 见下方两条 |
| **验证** | `validate_skill.ps1` 输出 `PASS: game-reverse-engineering skill structure and rules` |

### 偏差一：验证器的路径基准约定（踩到并已修正）

验证器强制「**反引号路径一律相对总集根**，markdown 链接相对所在文件」（正则只匹配以 `modules/` `references/` `scripts/` 开头的反引号路径）。首次运行报了 **26 条** `backtick path not root-resolvable` —— 因为模块 `SKILL.md` 内我按**文件相对**写了 `references/&lt;name&gt;.md`。

**修法**：模块内所有反引号路径改为根相对（`modules/cocos-project-standards/references/&lt;name&gt;.md`）。**这是一条硬约束，写新模块时必须先遵守**，否则验证器必红。

### 偏差二：修掉 3 条**与本模块无关的既有失败**（如实登记）

首次运行除我的 26 条外，另有 3 条**在我改动范围之外**的失败（涉及文件我全程未改）：

| 失败项 | 位置 | 处置 |
|---|---|---|
| `skill tree must not contain generated .pyc files` | `modules/cocos-mcp-channel/scripts/__pycache__/mcp_http.cpython-312.pyc` | 删除该生成目录（验证器明令禁止生成物入库） |
| `backtick path not root-resolvable -> scripts/check_icon_meta.py` | `modules/cocos-creator-repair/SKILL.md` | 改为 `cocos-asset-config-pitfalls/scripts/check_icon_meta.py`（该脚本属**另一个 skill**，原文已在正文点名归属，此处只把路径补全） |
| 同上 | `modules/cocos-mcp-channel/references/landing-log.md` | 同上 |

**说明**：这三条**非本次引入**，但不修则验证器无法全绿，故一并处置；改动均为最小且语义更正确（点名归属而非留悬空根相对路径）。**未改动任何业务结论或证据内容。**

### 门禁脚本实跑结果（对来源工程）

`check_program_standards.ps1 -ProjectRoot <来源工程>` 命中真实缺陷，证明检查有效而非空跑：

- B 段：扫描 **183** 个图标 meta（递归定位到 1 个 `icons/` 目录）→ **4** 个 `trimType=auto`、**3** 个已裁边（如 440×347 vs raw 442×442）、**6** 个非方形（含 200×427 的背景图）
- D 段：**1** 个文件 `on > off`（静态 `DataMgr`，属**已知误报**——常驻单例全局监听按约定无需 off，已在脚本内写明该边界）
- E 段：**22 种、41 处**无语义节点名（`img000`…`img039`，分布在 5 个 prefab）
- C/F/G 段：无 `.webp`、无 `.bak`、`data.json` 可解析、无废弃路径命中

> 首次运行时 B 段因**路径假设错误**（假设 icons 在 bundle 根下）而被跳过 → 已改为递归查找任意 `icons/` 目录。`resources/icons/` 实际位于资源域之下（`<域>/images/icons`），此为该轮修正的实际教训。

### 结构性验证（全绿清单）

- [x] 模块 `SKILL.md` 四块执行卡标记齐备（我管什么 / 第一步做什么 / 做完怎么算完成 / 红线）
- [x] 模块 `description` 以 `Use when` 开头
- [x] 根 `SKILL.md` 路由表含本模块路径（验证器强制）
- [x] `scope-map.md` 索引本模块（验证器强制：每个 modules/ 目录都必须在 scope-map 中登记）
- [x] 全部反引号路径根可解析
- [x] 树内无 `.pyc`
- [x] `validate_skill.ps1` 全绿

### 本轮**未**做的事（避免夸大）

- **未**在真实新工程上演练本模块（第二个工程落地时才回填框架版本耦合矩阵）。

---

## 2026-10-26 · 与既有沉淀对账（第三轮）

| 项 | 内容 |
|---|---|
| **触发** | 用户指出开发过程会话 `session-dc5591f4-0e78-4fe4-983a-9bc0a281c8f7`（标题「查看DADApet项目会话」，**103 轮 / 944 步**）的经验此前已沉淀到其他模块，要求核对本模块是否有重复、错位或需转移的内容 |
| **实际结果** | 查明该会话第 **100** 轮做过查重，当时结论是「`trimType` / `Luban` / `data.json` 这类关键词在 RE skill 的所有 md 里**几乎零命中**」→ 因此当年把经验沉到**项目级 skill** `cocos-asset-config-pitfalls`，hub 侧只留 `cocos-creator-repair` 的两个诊断节与 `cocos-mcp-channel` 的一行 landing-log。**本模块新建后，同一根因变成三处表述** |
| **回填动作** | ① 本模块 `SKILL.md` 新增「同一根因散在多处时的归属划分（防漂移）」表，明确三方职责：**诊断入口** = `cocos-creator-repair`；**项目操作 SOP** = `cocos-asset-config-pitfalls`（项目级，不在本总集）；**通用规范** = 本模块。② `cocos-creator-repair` 与 `resource-contract.md` §4 / `config-pipeline.md` §8 **双向补交叉引用**（诊断 ↔ 规范），并写明"规范条文只在本模块维护一份" |
| **验证** | `validate_skill.ps1` 全绿；改动文件行尾与编码未被污染（均与各自原约定一致） |

### 修复本模块自身遗留的矛盾

`framework-boundary.md` §8 原登记「`getRequiredResources` / `getBackgroundResources` 的精确消费时机**未逐行取证**」，但 `logic-layer-architecture.md` §7 在同一次重建中**已取证**（进入 Stage 第 2 步逐路径预载、失败仅告警不阻断）。两处矛盾 → 已改为指向 §7 并注明"本条原登记为未取证，第二轮已补齐"。**这是模块内自相矛盾，属必须修的类型。**

### 本轮识别出但**未**处置的缺口（需用户决定归属）

对账时发现下列经验**在会话中有、在 hub 全部 md 里零命中或无对应操作规程**。未擅自写入，因为写准确需要回读对应轮次的完整响应或工程产物：

| # | 缺口 | 会话出处 | 建议归属 |
|---|---|---|---|
| 1 | **跨工程 prefab + 依赖整体移植**（把某 prefab 及其图片/动画/脚本从 A 工程迁到 B 工程） | 第 50–52、82 轮 | `cocos-project-standards` 新参考 或 `prefab-bake` |
| 2 | **承原 meta/uuid 替换 prefab 内容**（复制 A 改名替换 B，保留 B 的原 uuid 以免引用断裂） | 第 56 轮 | 同上；属高价值反直觉技巧 |
| 3 | **prefab 文字节点全量规范化**（取消自动换行 + 溢出改 SHRINK；实测 43 prefab / 299 节点） | 第 101 轮 | `prefab-bake`（已有字段表 `_enableWrapText` / overflow 2=SHRINK）或本模块 |
| 4 | **专项校验脚本体系**（每系统一个 `verify_*` 静态门禁；`ROOT=parents[N]` + `fail()` 统一约定 + `utf-8-sig` 读生成物） | 本模块第二轮自查（非会话） | 本模块新参考 |

---

## 2026-10-26 · 补齐 4 条缺口（第四轮）

| 项 | 内容 |
|---|---|
| **阶段** | 按上一轮识别的缺口清单逐条补齐 |
| **取证方式** | 会话全文并不在 projcache（那只是**摘要索引**，响应被截断在 ~120 字）。真实转写为 `%USERPROFILE%\.dsh\sessions\--E-codex_apk_work--\session-dc5591f4-…/session.v4.jsonl.zstd`（**zstd 压缩 JSONL，6695 个事件**）。用 `py` + `zstandard` 解压、按 `seq` 区间抽取「用户提问 + 助手最终答复」，落到 `E:\codex_apk_work\out\`（`probe_session.py` / `turn_summary.py` / `t50_52.txt` / `t56.txt` / `t82.txt` / `t101.txt`） |
| **实际结果** | 新增 **3 份 reference（10 → 13）**，覆盖 4 条缺口（其中两条合并进同一份，因同属"prefab/JSON 程序化编辑"）：`prefab-json-batch-editing.md`（缺口 2+3）、`asset-migration-cross-project.md`（缺口 1）、`gates-and-verification-scripts.md`（缺口 4） |
| **回填动作** | 模块 `SKILL.md`：卡住时索引补 3 行 + 五类规范表补 3 行；`scope-map.md`：reference 计数 10→13 并补可迁移内容；`CHANGELOG.md`：新增 **10.1.0**；根 `SKILL.md` metadata version → 10.1.0 |
| **验证** | `validate_skill.ps1` 全绿 |

### 各条的关键结论（均来自会话原文，非推测）

| 缺口 | 会话出处 | 关键结论 |
|---|---|---|
| **2 承 uuid 替换 prefab 内容** | 第 56 轮 | 保留目标 `.meta` 的 uuid（实测 `17a12c4b…`）→ `regUI` 注册与 Stage 预加载列表**零改动**；替换后**目标 prefab 缺框架需要的控制器组件**，需从 `git show HEAD:<prefab>` 取旧组件条目照抄字段集再重绑；`PrefabInfo.asset` 实测用 `__id__` 索引（**不同版本可能是 uuid，必须重查**） |
| **3 prefab 文字节点全量规范化** | 第 101 轮 | 43 prefab / 34 含文字 / 299 个 Label；**枚举值查 `cc.d.ts` 确认**（`Overflow.SHRINK=2`）不得猜；**先证明 JSON 往返字节一致**（9365→9365）再批量写回；改完 `31 files changed, 291 insertions(+), 291 deletions(-)` **正好等于 282+9** → 自证只改字段未重写；显式 `\n` 换行必须保留 |
| **1 跨工程 prefab+依赖移植** | 第 50–52 轮 | 前置四项核对全过（两工程同为 750×1600 / 字体与脚本**已存在且同 uuid** / 零 uuid 冲突 / 源 prefab 无控制器）；依赖**直接 5 个、递归 8 个**文件；**隐性依赖**：用户指出"弹出动画没搬过来"，而源 prefab 里**根本没有 `Animation` 组件** —— 表现来自源工程**共享组件**（`onEnable` scale 0.01→1, 0.3s, backOut）；旧资源去留要查全工程引用（字体被别的 prefab 引用→**保留**；渐变脚本仅被移植件引用→**删**） |
| **4 专项校验脚本体系** | 本模块自查 | 来源工程 `tools/validation/` 12 个 + `tools/prefab/` 6 个；`ROOT=parents[2]` **11/11 齐**，但 `fail()` 统一约定仅 **5/11**、编码 `utf-8-sig` 仅 4 个 → **约定方向已验证有效，落地不彻底**；**未取证到统一运行器与 CI 集成** |

### 本轮**未**做的事

- **未**把会话里其余经验一并下沉：git 协作流水线（占该会话三成以上轮次）、多语言翻译口径、图标交付→min 版（等比缩小+四角切圆角）等，其中多数**已在项目级 skill `cocos-asset-config-pitfalls`**，按归属划分不重复。
- **未**在第二个工程上复跑门禁脚本（跨工程移植与批量编辑的通用性**尚未经第二例验证**）。
- 抽取脚本与中间产物留在 `E:\codex_apk_work\out\`（证据trail），未进本总集。
- **未**修改任何模块的业务结论；`cocos-mcp-channel` 的 `__pycache__` 删除与两处路径补全属仓库卫生，不构成能力变更。
- **未**宣称任何工程"已符合规范"。
