# 代码规范（目录骨架 · 命名 · 代码纪律）

> **何时读我**：要建目录骨架、定命名、写日志/事件/空兜底，或评审一段代码是否符合工程约定时。
> **读完能做到**：新建的文件、节点、属性命名与既有工程一致；事件与监听不成对、空数据无兜底这类返工一眼可判。
> **范围**：`[COCOS]` 为主，个别条目为 `[CFW]` / `[DADA]`，逐条标注。

## 1. 目录骨架 `[COCOS]` 模式

**核心原则**：**一个业务系统 = 一个目录**，目录内按角色固定三件。这样"系统"在文件系统上可见，新人按目录就能找到全部相关文件。

```text
Systems/<域>/XxxSystem/          # 域 = 按大流程分（如 Lobby / Guide）
├── XxxSystem.ts                 # 系统本体（注册 UI + 对外 open 方法）
├── UI/
│   └── XxxUI.ts                 # 该系统的界面（一个系统可有多个）
└── Event/
    └── XxxEvent.ts              # 事件常量
```

逻辑层顶层四块职责 `[COCOS]`（可映射到别的项目，名称是项目值）：

| 目录 | 职责 |
|---|---|
| `common/` | 通用库（`debug` / `fsm` / `sdk` / `time` / `uilib`），跨业务复用 |
| `config/` | 配置（`data` 配置数据、`schema` 表结构）——**派生目录**，见下 |
| `logic/` | 游戏逻辑主目录（`core/` 领域核心、`global/` 全局能力、`Stage/` 场景、`Systems/` 系统） |
| `userData/` | 本地用户数据（门面 + `data/` 数据类） |

**派生目录红线 `[COCOS]`**：`config/schema/` 由导表生成，禁止手改（见 `config-pipeline.md`）。

**System → UI 的归属纪律**：一个 System 目录下的 `UI/` 只放**归属该系统**的界面。跨系统的界面跳转走对方 System 的公开方法（见 `framework-boundary.md` 第 6 节）。

## 2. 命名规则

| 对象 | 规则 | 标记 |
|---|---|---|
| 类名 | `PascalCase` | `[COCOS]` |
| **文件名 = 类名** | 一个文件一个主类，名字必须一致 | `[COCOS]` |
| 角色后缀 | `XxxStage` / `XxxSystem` / `XxxUI`；领域组件不带后缀（如 `PetAvatar`） | `[COCOS]` 模式（后缀词表为项目值 `[DADA]`） |
| 数据类 | `XxxData` | `[COCOS]` |
| 事件类 | `XxxEvent` | `[COCOS]` |
| 派生逻辑 | 放 `XxxHelper`，**不放 Data 类** | `[COCOS]` |
| 资源引用路径 | **全小写 + 斜杠分隔 + 不带扩展名** | `[COCOS]` |
| 数据字段 | `camelCase` 且 `public` | `[COCOS]` |
| 配置表字段 | 源表 `snake_case` → 生成后代码侧 `camelCase` | `[COCOS]` |

### `@property` 前缀按组件类型 `[COCOS]`

这是**最值得跨项目复制**的一条约定——属性名前缀直接编码了组件类型，评审时无需打开 prefab 就能判断类型是否用错：

| 前缀 | 组件 |
|---|---|
| `btn*` | `Button` |
| `pgb*` | `ProgressBar` |
| `img*` | `Sprite` |
| `txt*` | `Label` |

**连带纪律**：**业务节点名必须与其绑定的 `@property` 名一致** `[COCOS]` 模式。收益是"节点 ↔ 代码绑定"可被脚本机械核对；不一致时任何自动化校验都失效。

### 节点命名 `[COCOS]`（防返工重点）

- **节点名必须表达运行时职责**。禁止 `panelB01`、`img001`、`node2` 这类无语义名。
- **设计稿的 ScreenId / 节点 ID 只允许用于生成器映射，不得直接作为业务节点名**。设计稿编号是"给生成器看的临时键"，混进运行时命名后，设计稿一改版全部节点名作废。
- 语义角色前缀约定：

| 场景 | 命名 |
|---|---|
| 互斥页面 | `view*` |
| 分组容器 | `grp*` |
| 页签 | `tab*` |
| 列表 | `scroll*` + `view/content` |

- **关闭按钮必须直属预制体根节点**：直属根部才能在任意子页面状态下被稳定找到并点击。
- **禁止只有一个普通子节点、且无归纳意义的空容器**：空容器会让层级膨胀、引用路径变脆。
- **公共控件放在作用范围最小的共同父节点**：放太高会被不该受影响的页面改到，放太低则重复。
- **重复节点优先用语义角色名**（`partnerCard` 而非 `partnerCard1/2`）；**仅当同父且同职责**时才允许两位数字后缀。
- **按钮结构**：标准文本按钮 = **背景节点挂 `Sprite` + `Button`，文本为全尺寸居中的子节点**。文本不参与点击热区计算。

## 3. 日志 `[COCOS]` + `[CFW]`

- 统一走门面：`CFW.log.info / warn / error`（`[CFW]`）。禁止散落 `console.log`（`[COCOS]`）。
- **日志前缀带模块**：`[XxxUI]`（UI 层）/ `[XxxSystem]`（系统层）`[COCOS]` 模式。
- **错误日志必须带上下文**：表名、key、节点名、数值。只写 `"error"` 的日志等于没有日志。

## 4. 事件 `[COCOS]`

```ts
export class XxxEvent {
    /** 数据变化（参数说明），常驻 UI 据此刷新 */
    public static XxxChanged: string = "Xxx:XxxChanged";
}
```

- **事件常量是静态字符串，带模块前缀**（`"Xxx:XxxChanged"`）→ 便于全局检索，避免重名。
- **`on` / `off` 必须成对**，且**分布在对称的生命周期里**：

| 角色 | 订阅 | 解除 |
|---|---|---|
| UI（弹窗） | `onOpen` | `onClose` |
| UI（常驻） | `onAdded` | `onRemoved` |
| System | `init` | `destroy` / `onRelease` |

- **闭包必须复用同一函数引用**：列表/卡片的点击回调要存入数组（如 `_cardHandlers[]`），否则 `off` 时传入的新闭包解绑不掉 → 内存泄漏 + 重复响应。这是"点击后触发两次"的典型根因。
- 常驻对象（全局单例、常驻 Stage）的全局监听可不解除，但**必须在注释里写明理由**，否则无法与漏写 `off` 区分。
- **多语言变化也有同一约束**（见 `i18n-and-text.md` 第 4 节）。

## 5. 空数据兜底（必写）`[COCOS]`

**凡是消费配置 / 数据列表的界面，必须在列表为空时同时给出：① 可见的兜底文案 ② 带上下文的错误日志。**

```ts
if (list.length === 0) {
    CFW.log.error('[XxxUI] TbXxx 为空：配置未生成或未加载');
    this.setLabel('txtSubtitle', I18n.t('XXX_EMPTY_TIP', '暂无数据'));
    return;
}
```

理由是排障成本：没有兜底时表现为"界面一片空白"，无法区分是配置没生成、资源没加载，还是布局写错。

## 6. 数据来源纪律 `[COCOS]`

- **界面数据一律取自配置表，不得写死。** 写死的文案与数值无法本地化、无法热更、无法让策划调整。
- **派生逻辑集中到 Helper，Data 类保持纯数据**（见 `data-modules.md` 第 5 节）。
- **少即是多**：不引入非必需的抽象与依赖。抽象成本按"将来可能要改"预支，而大多数"将来"不会来。

## 7. 文本 / 音效 / 提示的统一封装

每个 UI 类内实现**三件套**，不要各写各的：

```ts
/** 全局顶部提示 */
private showTip(content: string): void {
    CFW.stage.get(LobbyStage)?.getSystem(GlobalTipSystem)?.showGlobalTip(content);
}

/** 播放音效（受设置开关控制，资源来自配置表） */
private playSound(name: SoundEffectName): void {
    if (!DataMgr.settingsData.soundOn) return;
    const data = CFW.tables.TbSound.get(name);
    if (!data?.resName) return;
    CFW.audio?.playEffect(`${data.rootPath}/${data.resName}`);
}
// 第三件：多语言取词 → 见 i18n-and-text.md
```

**要点**：音效必须先判设置开关；多语言必须走统一门面（`[DADA]` 具体类名，方法是 `[COCOS]`）。

## 8. 反模式清单（见到就打回）`[COCOS]`

| 反模式 | 为什么 |
|---|---|
| 运行时 `getChildByName()` 后 `addComponent(Button)` 补挂按钮 | 绑定关系逃逸到代码，编辑器里看不到，无法静态校验，改 prefab 即断 |
| 事件 `on` 无 `off`，或 `off` 传新闭包 | 泄漏 + 重复响应 |
| 业务节点名与 `@property` 名不一致 | 自动化校验失效 |
| 设计稿编号直接作节点名 | 改版即全面作废 |
| 配置数据写死在代码里 | 无法本地化 / 热更 / 调整 |
| 空列表无提示无日志 | 排障成本极高 |
| 手改派生文件（`schema.ts` / `data.json` / 生成的 `.prefab` / `.meta`） | 下次生成即丢失 |
| 运行时重设 `Label` 的 `pos` / `fontSize` / `contentSize` | 抹掉美术调整（见 `i18n-and-text.md` 红线） |

## 9. 未取证项

- **`common/` 各子目录（`debug` / `fsm` / `sdk` / `time` / `uilib`）的内部约定**未逐项取证，仅确认其在逻辑层顶层存在的职责划分。
- **代码风格层面（缩进、引号、分号、lint 规则）** 未见成文规范 → 未取证；若目标工程有 lint 配置，以配置为真源。
- 来源项目文档存在**自相矛盾**（详见 `landing-log.md` 的"来源文档缺陷"节），本文件只采用其中与代码/meta 实测一致的一侧。
