# 数据模块规范（本地用户数据）

> **何时读我**：要新增一个用户数据模块、排查"数据没存上""改了字段没生效""老玩家存档读不出来"时。
> **读完能做到**：正确注册一个数据模块，避开嵌套对象不置脏的坑，知道何时需要手动刷盘。
> **范围**：`[COCOS]` 原则 + `[CFW]` 具体 API（`FRAMEWORK_BOUND_CFW`）。

## 1. 定位

本地用户数据统一由一个**数据门面**管理（例：`DataMgr`），底层用**响应式存储**：`Proxy` 自动置脏 + 防抖刷盘 + 生命周期绑盘。

- **数据模块：静态属性即注册**，一行一处，属性即数据。
- **存储 key = 数据类名**（`ctor.name`），JSON 序列化落盘。

## 2. 数据类契约

```ts
import { IUserData } from "./IUserData";

export class PlayerData implements IUserData {
    /** 旧存档 key（历史兼容，可选） */
    public static KEY: string = "GUIDE_USER_DATA";

    public gold: number = 0;
    public guideCompleted: boolean = false;

    load(): void { /* no-op */ }
    save(): void  { /* no-op */ }
    reset(): void { this.gold = 0; this.guideCompleted = false; }
}
```

约定 `[COCOS]` 原则 + `[CFW]` API：

- 字段用 **`camelCase`**，且必须是 **`public`**——`Proxy` 依赖属性可写性，`private`/只读会破坏置脏。
- `load` / `save` 是 **no-op**：置脏由 `Proxy` 自动完成，**不需要手动调 `save()`**。
- `reset` 恢复**所有**字段默认值（清档用）。漏字段 = 清档不干净。
- `static KEY` 记录**旧存储 key**，供 key 重构时兼容老玩家存档。

## 3. 注册

```ts
function regX<T extends object>(ctor: new () => T, legacyKeys: string[] = []): T {
    const mgr = ReactiveStorageManager.instance;
    const mk = <U extends object>(key: string, factory: () => U): U =>
        mgr.createModule(key, factory, { mode: StorageMode.JSON, legacyKeys }).data;
    return mk(ctor.name, () => new ctor());
}

export class DataMgr {
    static playerData   = regX(PlayerData, [PlayerData.KEY]);   // 有旧 key
    static foodMgrData  = regX(FoodMgrData);                    // 无旧 key
}
```

- 第一个参数为数据类，第二个为**旧 key 列表**（可省略）。
- **注册顺序即加载顺序**；无强依赖时可任意，有依赖必须显式排序。

## 4. 嵌套对象陷阱（最高发的坑）

嵌套数据对象**不实现 `IUserData`**，也不单独注册，作为数据类的字段随 JSON 一起序列化：

```ts
export class PetInfo {
    public petId: number = 0;
    public level: number = 1;
    public intimacy: number = 0;
}
```

**陷阱**：`Proxy` 只代理数据类的**顶层属性**；**嵌套对象内部属性变更不会触发置脏**。

```ts
DataMgr.petMgrData.pets[0].level = 5;   // ✗ 不置脏，可能不落盘
DataMgr.petMgrData.pets = [...next];    // ✓ 整体替换 → 置脏
DataMgr.flushAll();                     // ✓ 或显式强制刷盘
```

**判定口径**：凡是要改嵌套层级的字段，二选一——**整体替换顶层引用**，或**显式调 `flushAll()`**。不允许"改了嵌套字段然后指望自动落盘"。

## 5. 派生逻辑不进 Data 类

**原则 `[COCOS]`**：Data 类保持**纯数据**。派生计算（等级换算、亲密度、可否喂食、装扮组合等）集中到 `XxxHelper`；跨模块的派生集中到一个业务 Helper（例：`PetHelper`）。

理由：Data 类被任意 System/UI 引用，一旦掺入业务规则就会出现"同一算法多处实现"与循环依赖；Helper 是唯一可测试、可替换的派生入口。

## 6. 生命周期与刷盘

| 方法 | 作用 |
|---|---|
| `DataMgr.init(config)` | 注册配置（含 schema 版本迁移器）+ 加载全部 + 绑定生命周期 |
| `DataMgr.flushAll()` | 强制全量刷盘 |
| `DataMgr.flushIfDirtyAll()` | 仅刷脏模块 |
| `DataMgr.resetAll()` | 清档（重置所有模块） |

- **绑盘**：`init` 时订阅"切后台 / 关页面"（`onBeforeUnload` / `onPageHide`）→ 自动 `flushAll()`。**这是移动端的必要保护**：被系统回收前不给落盘机会就丢档。
- 初始化参数通常含：默认存储模式、`schemaVersion`、防抖毫秒、自动刷盘间隔、`bindLifecycle`、`migrator`。

## 7. 旧档迁移

两个机制配合使用，**都要有**：

1. **`legacyKeys`**：解决"存储 key 改名"（旧 KEY 系统级别的键名变化）。
2. **迁移器 `migrator` + 字段补齐**：解决"字段结构变化"。

```ts
private static migrateFoodMgrData(): void {
    const data = DataMgr.foodMgrData;
    if (!data.foods || typeof data.foods !== 'object') data.foods = {};
    if (typeof data.adFoodDateKey !== 'string') data.adFoodDateKey = '';
    if (!Number.isFinite(data.adFoodResetBoundary)) data.adFoodResetBoundary = 0;
}
```

**迁移三条纪律 `[COCOS]`**：

- **补齐而非覆盖**：只在字段缺失/类型不符时写默认值，**不要**用旧版结构覆盖玩家已有数据。
- **迁移代码与被迁移的数据同名同版本**：删字段前先确认线上不再有该形态存档；删的时候用 `if ('oldField' in data) delete data.oldField;` 而非直接不读（否则 JSON 里会永久残留）。
- **迁移必须幂等**：重复进游戏不应产生不同结果。

## 8. 访问示例

```ts
import { DataMgr } from "./userData/DataMgr";

DataMgr.playerData.gold += 100;
DataMgr.petMgrData.petName = "小白";
```

**注意**：数据**变化后**需要通知界面的，走事件（见 `code-and-naming.md` 的事件约定），不要靠 UI 轮询 Data。

## 9. 未取证项

- 响应式存储 v2 的**框架侧实现细节**（`common/storage/reactive/`）与完整 `StorageConfig` 字段语义**未逐项取证**；需要时读框架仓库文档 `userdata.md`。
- 来源项目 README 引用的 `docs/data-storage.md` 与 `docs/数据存储模块-方案.md` **在仓库中不存在** → 上述 v2 设计说明缺失，本文件内容主要由 `DataMgr` 代码与既有 `数据规范.md` 重建。
