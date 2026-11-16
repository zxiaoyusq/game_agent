# 接口规范（框架边界与六件套契约）

> **何时读我**：要确定"代码该经什么方式调用框架能力""各角色继承什么基类、覆写什么方法""System 与 UI 之间怎么互相访问"时。
> **读完能做到**：写出依赖方向正确、不散落单例 import、生命周期钩子齐全的系统与界面骨架。
> **范围**：`[COCOS]` 原则 + `[CFW]` 具体 API（`FRAMEWORK_BOUND_CFW`）。

## 1. 门面纪律（最重要的一条）

**原则 `[COCOS]`**：运行时能力（日志 / 事件 / 资源 / 层级 / 配置 / 音频 / 存储）统一经**一个门面对象**访问，禁止在业务代码里散落 `import { 某个内部单例 }`。理由：内部模块的导出名与层级会随框架重构漂移，门面是唯一稳定面；散落 import 会让重构成本按调用点数爆炸。

**具体 API `[CFW]`**（仅当体检确认使用 `driftsand-framework` 时）：

```ts
import { CFW } from "db://driftsand-framework/index";
```

| ~~不推荐~~ | ✅ 推荐 |
|---|---|
| `import { message } from "db://.../MessageManager"` | `CFW.event.dispatchEvent(...)` |
| `import { logger } from "db://.../Logger"` | `CFW.log.info(...)` |
| `import { resLoader } from "db://.../ResLoader"` | `CFW.res.load(...)` |
| `import { LayerManager } from "db://.../LayerManager"` | `CFW.layer.open(...)` / `CFW.gui.open(...)` |
| `import { global_config } from "db://.../Config"` | `CFW.config` |

常用门面能力：`CFW.event` / `CFW.log` / `CFW.res` / `CFW.layer` / `CFW.gui` / `CFW.config` / `CFW.stage` / `CFW.gsys` / `CFW.mgr` / `CFW.audio` / `CFW.uiMgr`。

**例外 `[CFW]`**：**类型与基类**（用于继承、类型声明，无法经 `CFW.*` 表达）仍需直接 `import`，但同样统一走框架入口，不要深入内部路径：

```ts
import { BaseStage, BaseSystem, BaseUI, LayerType, UIController } from "db://driftsand-framework/index";
```

落地做法：把框架 import 尽量收敛到**一行**，其余能力一律 `CFW.*`。

## 2. 基类职责与继承场景 `[CFW]`

| 基类 | 继承场景 | 关键约定 |
|---|---|---|
| `BaseStage` | 场景 Stage（每个大流程一个） | **必须**覆写 `onRegSystem`；可选 `onLoad` / `onLoaded` / `onBeforeUnload` / `onExit` / `getRequiredResources` / `getBackgroundResources` / `getBundleList` / `isPersistentStage`。⚠️ `onEnter` 已废弃，用 `onLoad` |
| `BaseSystem` | 业务系统 | `init()` 里 `regUI(...)` 注册 UI；经宿主 Stage 的 `getSystem(Cls)` 访问 |
| `BaseUI` | UI 控制器 | 只承载框架层 UI 生命周期与通用节点/资源封装，**不承载具体游戏表现逻辑** |

## 3. Stage ↔ System 访问

- **原则 `[COCOS]`**：跨系统调用必须经**宿主 Stage 的类型化查询**，不要用字符串按名开界面。
- **API `[CFW]`**：

```ts
// 取系统
CFW.stage.get(LobbyStage)?.getSystem(GlobalTipSystem)?.showGlobalTip(content);
// 取系统（System 内部）
this.stage?.getSystem(TaskSystem)?.openDailyTask();
```

- **Stage 生命周期顺序 `[CFW]`**：注册 `onRegSystem` → 进入 `onLoad` → 关闭加载器后 `onLoaded` → 退出 `onBeforeUnload` → 逆序退出各 System → 释放（非常驻时）→ `onExit`。⚠️ `onEnter` 已废弃，不要用。
- **常驻纪律**：`isPersistentStage` 默认 `false` → **退出即真释放**。要求"退回大厅不重建"必须显式声明常驻，并承担状态残留风险。
- **禁止** `CFW.layer.open('字符串路径')` 直接从业务层开界面——界面由归属 System 注册与打开，调用方只调 System 的 `openXxx()`。这样界面归属与缓存策略集中在一处。

## 4. UI 注册与打开

```ts
// System.init()
this._feedUI = this.regUI(FeedUI, {
    layer: LayerType.PopUp,                    // 弹窗用 PopUp；常驻用 UI
    prefab: "lobby/ui_prefabs/Feed",           // 预制体路径（相对 bundle）
    destroy: false,                             // false = 缓存复用，保证 open 幂等
});

// 打开 / 关闭
await this._feedUI.open();
this._feedUI.close();
```

约定：

- **`destroy: false` 保证幂等**：重复 `open()` 复显同一缓存实例，不会叠加多个弹窗。
- **`LayerType` 选择**：`PopUp`（弹窗，通常伴随镜头拉远）vs `UI`（常驻，如顶栏/功能入口）。
- **摄像机效果的弹窗不设 `mask: true`**：去掉遮罩后打开弹窗仍可操作身后的角色/宠物——这是产品需求（可边看宠物边操作），照默认加遮罩会挡掉交互。

## 5. UI 基类选用 `[CFW]` + `[COCOS]`

| 场景 | 基类 | 说明 |
|---|---|---|
| 底部上滑弹窗 | `SlideUpUI`（项目 `common/uilib/`）`[DADA]` 位置 | 封装上滑入场、角色舞台移动与归位 |
| 全屏 / 普通弹窗 | `BaseUI`（框架） | 框架基类，生命周期由框架驱动。⚠️ 框架还会调 `onInit` / `onCreate` / `onAdded` / `onRemoved` / `onBeforeRemove`，这五个**未声明在 `BaseUI` 上**——成员名写错不会有编译错误，只会**静默不执行** |
| 常驻顶栏 / 功能入口 | `Component`（`cc`） | 挂场景节点，用 `onAdded` / `onRemoved` |

上滑弹窗的**成对约定**（这是最容易漏的返工点）：

```ts
public onOpen(_data?: any): void {
    this.movePetStageUp();    // 上移角色舞台；若配置了固定功能背景，同时开始切换
    this.slideUp();           // 底部上滑入场
    this.bindEvents();
    this.setEntryButtonsVisible(false);   // 隐藏大厅底部功能入口
    this.refresh();
}
public onClose(): void {
    this.resetPanelPos();     // 归位（兜底防界面残留屏幕外）
    this.unbindEvents();
    this.restorePetStage();   // 恢复角色舞台，并切回最新主背景
    this.setEntryButtonsVisible(true);
}
```

`onOpen` 与 `onClose` 必须**对称**：凡是 `onOpen` 改动的全局可见性（舞台位置、入口按钮、背景、监听），`onClose` 必须全部还原。不对称 = 关闭后大厅残留错位，且往往要等下一次打开才暴露。

## 6. 依赖方向（不许反向、不许横穿）

- **逻辑层可以依赖框架层；框架层绝不依赖逻辑层。** `[COCOS]` 框架层若需要业务数据，走**接口注入/回调配置**（如把取配置的函数作为初始化参数传入），不要在框架里 `import` 业务模块。
- **UI 不要直接 `import` 另一个 System 的 UI 类**。要跳转就调对方 System 的公开方法，由对方决定开哪个界面。 `[COCOS]` 原则
- **实现数据接口（`IUserData`）的纯数据类不引用 System / UI**。派生计算放 Helper，Data 只存字段（见 `data-modules.md`）。 `[COCOS]` 原则
  ⚠️ **不要把这条错误扩大**成"`userData/` 整个目录不引用 logic"：实测 `userData/` 下的 **Helper 会引用 `logic/`** 的领域组件与事件类，且这承担着跨层派生的实际职责。
- **⚠️ 逻辑层内部不是严格单向分层（实测结论）**：`userData/` 与 `common/uilib/` 反向引用 `logic/` 是**客观存在**的，且**未取证到任何静态检查或编译规则在强制它**。因此"逻辑层严格分层"只能写成**设计目标与评审项**，**不能**写成"已实施的事实"——否则规范本身就与现实矛盾。唯一被实测守住的边界是上面第 1 条（框架层不依赖业务）。
- 注册顺序即加载顺序：`DataMgr` 的注册顺序 = 数据加载顺序；无强依赖时顺序无关紧要，但**有依赖就必须显式排**。

## 7. 无框架层时的降级方案 `[COCOS]`

若体检发现目标工程**没有**自研框架层（纯 Creator 原生工程），不要把 `[CFW]` 条目硬套上去。按以下降级：

| `[CFW]` 契约 | 降级做法（原生 Cocos） |
|---|---|
| `CFW.log` | 自建 `Logger` 单例（或直接 `console` + 统一前缀），仍是**一个**入口 |
| `CFW.event` | `EventTarget` 或自建事件总线单例 |
| `CFW.res` | `resources.load` / `assetManager` + `assetManager.bundles` 封装成一个 `ResLoader` |
| `CFW.layer` / `LayerType` | 自建 UIManager：按 Layer 分层挂 Canvas 子节点 |
| `BaseSystem` / `BaseStage` | 自建等价基类，**保留同样的 `init` / `update` / `onRelease` + `getSystem` 契约** |
| `CFW.tables` | 自行加载 `data.json` 并构表；Luban 链路本身不变（见 `config-pipeline.md`） |

**关键**：降级的是**实现**，不是**契约**。六件套的职责划分、生命周期钩子、依赖方向、幂等 open、事件成对——这些是 `[COCOS]` 层面的收益，与是否使用某个框架无关。反过来，若只有框架没有纪律，工程一样会烂。

## 8. 未取证项（如实登记）

- 框架层 `module.md` / `gui.md` / `facade.md` / `userdata.md` 描述了比本文更细的契约（如 `MgrModule` / `GSystemModule` 的区别、`UIController` 的完整方法面）。按红线**不复制**，需要时读框架仓库自身文档。
- `getRequiredResources` / `getBackgroundResources` 的**消费时机已取证**（进入 Stage 第 2 步逐路径预载，失败仅告警不阻断进入），见 `modules/cocos-project-standards/references/logic-layer-architecture.md` 第 7 节。本条原登记为"未取证"，第二轮重建已补齐。
