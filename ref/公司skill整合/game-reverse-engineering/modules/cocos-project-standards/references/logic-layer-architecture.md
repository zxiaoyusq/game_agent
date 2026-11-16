# 整体架构设计（逻辑层）

> **何时读我**：开始任何工程规范工作之前（第 1 节体检表是**强制第一步**）；以及要判断"某段代码该放哪一层""启动顺序为什么是这样"时。
> **读完能做到**：判定目标工程能套用本模块的哪些层，画出启动链路，说清六个角色的契约与依赖方向。
> **范围**：`[COCOS]` 架构模式 + `[CFW]` 具体钩子名 + `[DADA]` 证据出处。

## 1. 工程体检表（强制第一步）

**在做任何规范工作前，先确认这三件事。**结果直接决定哪些条目可用。

| # | 要确认 | 怎么查 | 影响 |
|---|---|---|---|
| 1 | **Creator 版本** | 工程 `package.json` 的 `creator.version` | 版本决定 prefab 序列化字段与资源导入行为；也决定能否用编辑器通道 |
| 2 | **是否有自研框架层，是哪一个** | 看 `extensions/` 下有无线程框架扩展；看业务 import 是否指向统一别名 | **决定全部 `[CFW]` 条目是否可用**。框架不匹配时必须走降级方案（见 `framework-boundary.md` 第 7 节） |
| 3 | **逻辑层骨架是否已存在** | 看 `assets/scripts/` 下的目录划分 | 已有工程 → 做**对照差异清单**；新工程 → 套用第 4 节骨架 |

**判定表**：

| 情况 | 处理 |
|---|---|
| 用同一框架（本总集已验证：`driftsand-framework` / `framework_cfw_cocos`） | 全量采用；`[CFW]` 条目直接可用 |
| 有别的自研框架 | 采用 `[COCOS]` 条目；`[CFW]` 条目**只借鉴分层意图**，API 全部按目标框架重写 |
| 纯 Creator 原生、无框架 | 走降级方案（`framework-boundary.md` 第 7 节）；**契约照抄、实现自建** |
| 情况不明 | **`NEEDS_CONTEXT`** — 先取证，不要凭猜往下做 |

**体检结论必须落盘成表**（版本 / 框架身份与版本 / 现有骨架 / 新老工程），它是后续一切判定的前提。

## 2. 双层架构与唯一的强制边界 `[CFW]` 结构，`[COCOS]` 原则

```text
框架层  extensions/<framework>/        ← 独立仓库（子模块），零业务耦合
   ↑ 业务单向依赖
逻辑层  assets/scripts/                ← 本工程的全部业务代码
```

**唯一的强制边界（已实测验证，可依赖）**：

- 逻辑层一律经**框架统一别名**导入（`db://driftsand-framework/index`）。
- **框架层 0 处 import 业务代码**（来源项目全量检索确认）。
- 框架层若需要业务数据，走**接口注入 / 回调配置**（例：把"取配置"的函数作为初始化参数传入），而不是反向 import。

**这条边界是架构的地基**：它保证框架可独立升级、可复用到下一个项目。破坏它的代价是框架再也无法同步。

## 3. 启动链路（从进程启动到进入第一个 Stage）`[CFW]`

顺序结论（每一条都影响"我该在哪里做初始化"）：

| 步 | 发生什么 | 关键点 |
|---|---|---|
| 1 | 引擎加载常驻节点，`GameEntry.onLoad` 装全局错误捕获 | 框架基类先于业务 |
| 2 | 业务入口 `extends GameEntry`，**覆写 `start()`** | 业务在 `super.start()` **之前**插入自己的准备 |
| 3 | 加载 **`global_config`**（层级配置、公共 UI 路径、环境配置） | ⚠️ **早于 `CFW.init`**；失败按重试策略递归重试 |
| 4 | **`await super.start()`** → `CFW.init(...)` | 传入：`baseUrl`、`uiRoot`、UI 配置与层级配置、表类与表组加载器 |
| 5 | `CFW.init` 内部：资源器初始化 → 预载全部 bundle → **配置表就绪** → 注册管理器（音频/定时/ SDK /加载器/ UI）→ 层级初始化 → 特效初始化 | ⚠️ **Luban 配置表在这一步就绪**（由表组加载器驱动） |
| 6 | `onGameStart()`：装配初始化加载器（步骤表 + 必需资源清单 + 资源检查器）、SDK 适配器注入、注册业务管理器与全局系统 | 业务管理器/全局系统在此注册 |
| 7 | **`await initLoader.load()`**（带最短展示时长） | 加载器的 `DEFAULT_STEPS` 被拼到步骤头部 |
| 8 | 加载器步骤内：① 多语言装配 ② **用户数据初始化**（`DataMgr.init()` + 默认装扮保底） ③ 必需资源 `ensureReady` ④ **`retainResident` 保底驻留** | ⚠️ **用户数据在 loader 内就绪**，不在 `CFW.init` |
| 9 | 按存档分流进入 **GuideStage / LobbyStage** | 带 `skipEnterLoader` / `deferBackground` |
| 10 | 进入 Stage 后：**等一帧**（`EVENT_AFTER_DRAW`）→ 关加载器（不启后台）→ 启动后台资源 | 等一帧是为了避免在同帧内切换造成的闪烁 |
| 11 | Stage 就绪 → `onLoad` 里打开常驻系统 → 常驻 UI 挂载后通知 SDK 加载完成 | 关原生 loading 的时机在此 |

**四条最容易踩的顺序结论**：

1. **`global_config` 早于 `CFW.init`**，所以它不能依赖框架能力；用引擎原生资源加载。
2. **配置表在 `CFW.init` 内就绪**，因此 `CFW.init` 之后即可读表。
3. **用户数据在加载器步骤内就绪**，因此 `CFW.init` 之后、`initLoader.load()` 之前**不能**访问 `DataMgr`。
4. **必需资源要 `retainResident` 保底驻留**，否则可能被释放导致后续再次加载（或黑图）。

## 4. 逻辑层四块职责与依赖方向

| 目录 | 职责 |
|---|---|
| `common/` | 通用库：`debug` / `fsm` / `sdk` / `time` / `uilib`，跨业务复用 |
| `config/` | 配置：`data`（配置数据）+ `schema`（**导表生成物，禁手改**） |
| `logic/` | 游戏逻辑主目录：`core/`（领域核心组件）、`global/`（全局能力与全局系统）、`Stage/`（场景）、`Systems/`（按域分包的业务系统） |
| `userData/` | 本地用户数据：门面 + `data/`（数据类）+ Helper（派生逻辑） |

### ⚠️ 实测：逻辑层内部**不是**严格单向分层

必须如实说明，否则会写出误导新人的"理想架构图"。来源项目实测：

| 方向 | 实测情况 |
|---|---|
| `logic` → `userData` / `config` | ✅ 存在（业务读数据、读表） |
| `userData` → `logic` | ⚠️ **存在**。`userData/` 下的 **Helper** 会 import `logic/core` 的领域组件与 logic 的事件类 |
| `common/uilib` → `logic` + `userData` | ⚠️ **存在**（上滑 UI 基类直接引用业务 Stage 与数据） |
| `config` → 其它 | ✅ 无反向 import（仅表加载器被框架消费） |
| 框架层 → 业务 | ✅ **无**（唯一被真正守住的边界） |

**结论与用法**：

- **只有"框架层不依赖业务"这一条是被实测守住的**，务必守住。
- 逻辑层内部的反向引用**客观存在**，且**未取证到任何静态检查/编译规则在强制它**。
- 因此**不要把"逻辑层严格分层"写进规范当作已实施的事实**。正确写法：把它列为**目标**与**评审项**，并说明当前代码存在例外，收敛需要单独排期。
- **`userData/` 里的 Helper 可以引用 logic**（真实存在且承担跨层派生），但**实现 `IUserData` 的纯数据类不得引用 logic**（见 `data-modules.md` 第 5 节）——这两件事必须分开说，否则规范自相矛盾。

## 5. 六件套契约 `[CFW]`

### 5.1 Stage

| 项 | 内容 |
|---|---|
| 基类 | `BaseStage`（抽象） |
| **必须覆写** | `onRegSystem()` |
| 可选覆写 | `onLoad`（进入后）、`onLoaded`（加载器关闭后）、`onBeforeUnload`（退出前）、`onExit`、`getRequiredResources`、`getBackgroundResources`、`getBundleList`、`isPersistentStage` |
| ⚠️ 已废弃 | `onEnter` — **不要用**，用 `onLoad` |
| 创建 | 由 StageManager 首次进入时 `new stageClass()` 并注册 |
| 访问 | `CFW.stage.get(Cls)` / `has` / `exitStage` / `returnStage` / `switchStage` |
| 生命周期时序 | 注册：建 UIManager → `onRegSystem()`；进入：开进入加载器 → 预载必需资源 → 逐 System 进入 → `onLoad` → 关加载器 → `onLoaded` → 启动后台资源；退出：`onBeforeUnload` → 逆序退出各 System → 释放（非常驻）→ `onExit` |

**常驻纪律**：`isPersistentStage` 默认为 `false`，来源项目两个 Stage **都未覆写** → **退出即真释放**。若你的工程要求"退回大厅不重建"，必须显式声明常驻，并承担它带来的状态残留风险。

### 5.2 System

| 项 | 内容 |
|---|---|
| 基类 | `BaseSystem`（抽象） |
| **必须覆写** | 实际上无强制项（`onReg` 默认转发 `init`） |
| 常见覆写 | **`init()`**（绝大多数系统只覆写它，在其中 `regUI(...)`）；少数覆写 `onEnter` / `onExit` / `update` / `onRelease` |
| 创建 | 宿主 Stage 的 `regSystem(cls, data?, priority?)` → `new` + 绑定宿主 + 按优先级排序 + 进入注册态 |
| 访问 | 同宿主 `getSystem(Cls)`；跨宿主/全局走 `CFW.gsys.getGSystem(Cls)` |
| 生命周期 | 注册（Registered）→ 每次进入 `onEnter`（Running）→ 退出 `onExit` → 释放 `onRelease`（仅销毁/整包） |
| `update` | **仅就绪态被驱动**；未就绪时不会被调 |

**实践建议**：默认只用 `init()`；需要"每次进入都刷新"时才用 `onEnter`。

### 5.3 UI 控制器

| 项 | 内容 |
|---|---|
| 基类 | `BaseUI`；项目可再包一层中间基类（来源项目：`LogicBaseUI`，再加 `SlideUpUI`） |
| **声明在 `BaseUI` 的钩子** | `onPrefabLoaded` / `onOpen` / `onClose` / `onShow` / `onHide`；以及就绪机制 `waitReady` / `ready` / `markReady` |
| ⚠️ **框架还会调、但未声明在 `BaseUI` 的钩子** | `onInit` / `onCreate` / `onAdded` / `onRemoved` / `onBeforeRemove` |
| 创建 | System 的 `this.regUI(Cls, {layer, prefab, destroy})` → 得到 `UIController` |
| 访问 | `UIController.open() / close() / get() / isOpen()` |
| 打开时序 | 有实例则复显；否则按层级加载 prefab → 取组件 → 注入 uiManager → `onCreate` → `onPrefabLoaded` → （若 `waitReady`）await `ready` → `onInit(data)` → `onOpen(data)` → `onShow(data)` |
| 关闭时序 | `onClose`（缺省回落 `onRemoved`）→ 层级移除 → `onBeforeRemove` → 按 `destroy` 真销毁或仅 `active=false` → `onRemoved` → `onHide` |

**两个必须记住的坑**：

1. **`onAdded` / `onRemoved` 不在 `BaseUI` 声明里，但框架会调** —— 想做常驻节点行为就用它们；成员名写错不会有编译错误，只会静默不执行。
2. **`destroy` 的文档默认值与代码实际相反**（文档写默认 `true`，代码实际 `?? false`）。**业务应一律显式传 `destroy`**，不要依赖默认值。来源项目统一显式 `false` 以获得幂等 open。

### 5.4 Event

| 项 | 内容 |
|---|---|
| 基类 | **无基类**。纯类 + `static` 字符串常量 |
| 通道 | `CFW.event`（即框架的消息管理器）的 `on / once / off / dispatchEvent` |
| 监听签名 | `(event, ...args)` |
| 优先级 | `-1` 为 FIFO；`>= 0` 数值越大越先执行 |

约定见 `code-and-naming.md` 第 4 节（成对 / 同一引用）。

### 5.5 Data

| 项 | 内容 |
|---|---|
| 契约 | 接口只有 `load()` / `save()` / `reset()`，**无基类、无脏标记** |
| 注册 | 数据门面的注册宏，一行一个；**注册发生在门面被 import 时**，早于 `init()` |
| 初始化 | `init()` = 框架存储初始化（schema 版本 / 防抖 / 自动刷盘 / 绑生命周期 / 迁移器）+ 加载全部 + 字段迁移 + 绑前后台刷盘 |
| 访问 | 静态属性即数据（`Proxy` 自动置脏）+ `flushAll / flushIfDirtyAll / resetAll` |

⚠️ **注意框架层可能存在另一套同名/近名的用户数据机制**，而本工程用的是**响应式存储**那一套。两套并存时不要混用——来源项目实测框架层的另一套在本工程**零引用**。落地时先确认用哪一套，再写代码。

详见 `data-modules.md`。

### 5.6 Config

| 项 | 内容 |
|---|---|
| 生成物 | `config/schema/schema.ts`（含 `Tables` 类 + 每表 getter + `InitAsync()`） |
| 接入 | 业务入口提供 `{ tablesClass, tableGroups: [{ name, loader }] }`，由框架的表管理器按组驱动加载 |
| 就绪时机 | **`CFW.init` 内**（见表组加载器） |
| 访问 | `CFW.tables.TbXxx`；类型与枚举直接 import schema |

详见 `config-pipeline.md`。

## 6. 跨系统交互

| 场景 | 做法 |
|---|---|
| 同宿主 System 互调 | `getSystem(Cls)` |
| 跨宿主 / 全局系统 | `CFW.gsys.getGSystem(Cls)` |
| **UI 拿 System** | `CFW.stage.get(StageCls)?.getSystem(XxxSystem)?.openXxx()` — **不缓存 System 实例** |
| 数据变化通知视图 | 走事件总线：**消费/结算方派发，视图监听刷新** |
| **不要** | 散落 `CFW.layer.open('字符串路径')` 直接开界面（界面归属与缓存策略会散掉） |

**关于"UI 不得直接 import 另一个 System"的如实说明**：

- 文档侧只找到**相邻条文**：跨宿主走事件或 `CFW.gsys`、"严禁直接 import 其他系统的 Manager"、"不散落字符串开界面"。
- **代码侧存在反例**：来源项目的常驻顶栏 UI 直接 import 并使用兄弟 System 类。
- **未取证到**任何专门禁止该写法或强制分层的 lint / 编译规则。

**因此**：把"UI 经 System 公开方法访问"作为**推荐约定与评审项**，**不要**宣称它是已被强制执行的规则。

## 7. 资源加载时机 `[CFW]`

| 钩子 | 何时被消费 | 失败行为 |
|---|---|---|
| `getRequiredResources()` | 进入 Stage 第 2 步，逐路径预载（目录优先，回退单文件） | **仅告警，不阻断进入** |
| `getBackgroundResources()` | 进入末尾；若 `deferBackground:true` 则延后到加载器关闭后由业务显式触发 | 仅告警 |
| `getBundleList()` | 仅在释放时用于移除 bundle | — |

**启动必需资源清单**由业务提供（例：遮罩、主界面、引导首屏、全局提示），经初始化加载器的 `resourceConfig.init` 消费，`ensureReady` 之后 **`retainResident` 保底驻留**。

**要点**：

- 两个钩子**失败都不阻断进入** → 缺失资源不会崩，但会表现为"界面缺图/空面板"。所以**必须有空数据兜底与告警**（见 `code-and-naming.md` 第 5 节）。
- **`retainResident` 是防黑图的关键**：启动必需资源若不保底驻留，可能在后续资源压力下被释放。

## 8. 预制体路径写在哪（三处，容易漏）

**prefab 路径不在配置表里**，来源项目实测写在**三处**：

1. **System 的 `regUI` 选项**（绝大多数界面在此）——部分系统用类常量集中声明。
2. **Stage 的资源清单钩子**（`getRequiredResources` / `getBackgroundResources` 里的路径数组）——用于预载。
3. **直接加载**（启动加载界面、遮罩、场景切换加载界面等框架级 UI）。

**纪律**：新增界面时**三处都要考虑**——`regUI` 注册是一处，**预载清单必须同步追加**，否则首次打开会有可感知的加载延迟。UIManager 有"按类名推导路径"的缺省逻辑，但**来源项目一律显式传路径**，不依赖推导（显式更可读、可检索）。

## 9. 框架文档与代码不一致（避坑表）

来源项目实测到框架文档与代码有 **9 处不一致**。**落地时以代码为准**，并在本模块登记，避免再被文档误导：

| # | 文档说法 | 代码事实 |
|---|---|---|
| 1 | Stage 状态 3 个 | 实际 **4 个**（多 `Registered`） |
| 2 | System 状态含 `Initializing` | 实际**无** `Initializing`，有 `Registered` |
| 3 | 主钩子为 `onRegSystem → onEnter` | `onEnter` 已 **@deprecated**；主链是 `onLoad / onLoaded` |
| 4 | 存在 `_useSwitchLoader` 三选一策略 | **不存在**；实际是每 Stage 一个 StageLoader + `skipEnterLoader` 选项 + 直接预载 |
| 5 | `enterStage` 无 options | 实际有 `{skipEnterLoader, deferBackground}`；另有 `return/returnStage/onYield/onResume` 未见于文档 |
| 6 | BaseUI 只有 5 个钩子 | 实际还调 `onInit/onCreate/onAdded/onRemoved/onBeforeRemove` |
| 7 | `UIConfig.destroy` 默认 `true` | 实际 **`?? false`** |
| 8 | 新数据模块一律用框架的 `register`/`reg()` | 实际用响应式存储的 `createModule`；框架另一套在本工程零引用 |
| 9 | 启动链路 = `start → CFW.init → onGameStart` | 实际业务**覆写 `start()`**，把 `global_config` 插在 **`CFW.init` 之前** |

**用法**：把这张表当作"读框架文档时的对照表"。**任何来自框架文档的结论，进规范前都要用代码复核一遍**。

## 10. 未取证项（如实登记）

- **强制分层的 lint / 编译规则**：未取证到任何规则。逻辑层反向依赖**客观存在**。
- **Event 基类**：确认**不存在**基类（这本身是结论）。
- **"UI import System"的显式禁令条文**：未找到；代码存在反例。
- **后台预热（BackgroundLoader）**：本工程用 `close(0)` 明确**不启动后台**，故其实际行为未取证。
- **来源项目 README 引用的 5 份架构文档全部不存在**（`新逻辑层框架定义.md` / `architecture.md` / `加载器与Stage架构.md` / `data-storage.md` / `数据存储模块-方案.md`）→ 本文件为**从代码重建**，所有结论均带代码出处；缺文档导致的空白已在各处标注。
