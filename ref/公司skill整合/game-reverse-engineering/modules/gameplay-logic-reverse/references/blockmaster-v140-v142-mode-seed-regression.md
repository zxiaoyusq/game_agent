# BlockMaster V140-V142 模式回调与 Seed 就绪竞态复盘

> 范围：具体版本、日志 marker、皮肤 ID 和事件名属于 `CASE_ONLY_BLOCKMASTER`；“保留原条件范围、区分逻辑回归与资源未就绪、晚到结果只在稳定边界提交”属于 `GENERALIZED_PATTERN`。

更新日期：2026-09-01。用于诊断 Cocos JSB 游戏中“修复跨模式表现后，经典模式不再切特殊材质”以及“同一 APK 前后两次验收结论相反”的问题。

## 1. 两个症状必须分开归因

### 1.1 真实代码回归：条件外追加 hook

原代码只在目标 UI 打开时调用：

```js
"ChapterGame" === event.name && owner.onOpenChapterGame();
```

V141 在分号后直接追加运行时通知：

```js
"ChapterGame" === event.name && owner.onOpenChapterGame();
runtime.handleModeOpen("ChapterGame");
```

第二句不再受原条件约束，任何 UI open 都被误报为进入闯关。真机经典模式日志同时出现 `mode=class` 和连续 `chapter_open`，计数短时间达到 154；每次误报都会释放待提交的经典材质状态，再把普通皮肤重新绑定，因此特殊材质无法出现。

最小修复是让新增调用与原 owner 共用同一条件块，不改材质池、清屏或选材逻辑：

```js
if ("ChapterGame" === event.name) {
  owner.onOpenChapterGame();
  runtime.handleModeOpen("ChapterGame");
}
```

### 1.2 表面回归：冷启动 Seed 尚未完成

V142 修正 UI 条件后，首次验收仍看到清屏没有特殊材质。完整时间线证明这不是同一个错误：

- 引导清屏按规则保持当前材质；
- 后续清屏时选择器记录 `preferred=special`，但特殊材质 ready 数仍为 0，于是降级为普通配色；
- `MATERIAL_SEED_WAIT` 结束后，6 套特殊材质陆续 ready；
- 不改代码、不换 APK，用户在下一次清屏确认特殊材质切换成功。

因此只能证明“失败与清屏时资源未就绪强相关”，不能把“稍后成功”写成已经修复冷启动体验。若产品要求首个有效清屏就能进入特殊材质，仍需单独处理预热时序或未就绪策略。

## 2. 通用诊断方法（GENERALIZED_PATTERN）

### 2.1 先建立单调时间线

至少记录：

1. 进程启动、真实模式进入和目标 UI open；
2. Seed/资源等待开始与结束；
3. 每套候选资源 ready；
4. 业务边界触发，例如新局或清屏；
5. selector 的偏好、resolver 的实际结果和降级原因；
6. 最终 commit、owner 回调与首帧渲染。

只有“同一边界、同一就绪状态”的旧包/新包才能直接比较。热启动成功不能代替冷启动验收，等待完成后的第二次清屏也不能证明首次清屏通过。

### 2.2 用互斥证据区分根因

| 证据 | 优先结论 |
|---|---|
| 非目标 UI 也触发模式通知；当前模式与通知矛盾 | 条件范围或 hook 位置错误 |
| selector 偏好特殊，但 resolver 因 ready=0 选择普通 | 资源就绪竞态或降级策略 |
| 特殊资源已完整 ready，selector/commit 仍无特殊 | 选择、提交或 owner 链回归 |
| commit 成功但棋盘混入旧节点 | 跨模式重绘/对象复用边界问题 |

不要只凭画面把四类问题都归为“材质切换失败”。

### 2.3 晚到结果不得热提交

资源准备完成时只更新 ready/pending 状态。禁止在 bundle 回调里立即切材质，因为完成点可能位于拖拽、预消除或清屏动画中间，会重新制造双重变色、半生命周期或混合棋盘。

可选产品策略必须显式决定并测试：

- 保持当前完整表现组，把特殊材质延期到下一稳定边界；
- 调整 Seed/预热优先级，使至少一个完整特殊组更早 ready；
- 若允许普通降级，明确是否消耗本轮特殊材质轮换名额。

无论选择哪种，材质资源和配套 effect handler/pool 必须双就绪，并由单一 owner 在一个 epoch 内提交一次。

## 3. 代码生成与测试门禁

### 3.1 行为测试优先于字符串存在

必须验证：

1. Settings、广告、弹窗等非目标 UI 打开时，模式通知为 0；
2. 目标 UI 打开时，原 owner 与新增通知各执行一次；
3. 生成器对已打补丁输入再次运行，行为和 hook 数量不变；
4. 两份可能执行的 JS 副本都满足目标 gate=1、无条件 hook=0；
5. 经典模式普通 UI 刷新不会释放 pending 材质。

只断言源码“包含 `handleModeOpen`”抓不到条件外追加错误。

### 3.2 冷启动资源矩阵

至少覆盖：

- 清装/覆盖安装后立即清屏，资源尚未 ready；
- 部分特殊资源 ready；
- 全部目标资源 ready；
- 热启动；
- 经典 -> 闯关 -> 经典；
- 低端机慢复制与慢 bundle 初始化。

自动测试应能人为延迟资源 ready，并断言未就绪结果不会在动画中途补提交。

## 4. 禁止做法

- 在短路条件语句的分号后追加本应受条件控制的 hook；
- 只测目标 UI，不测任意非目标 UI；
- 重新生成时重复叠加旧 hook；
- 看到画面没变化就立刻改 selector，而不核对 ready 时间线；
- 把“多等几十秒”当成产品修复；
- 资源 ready 回调一到就自动切材质；
- 用热启动或第二次清屏替代冷启动首次边界验收；
- 把版本号或新 APK 当成修复证据。

## 5. BlockMaster 专属验收清单（CASE_ONLY_BLOCKMASTER）

1. 日志中经典模式不得出现无对应 ChapterGame open 的 `BM_V140_CLASS_VISUAL_SCOPE reason=chapter_open`；
2. `BM_V141_CLASS_SKIN_REBIND` 只允许真实经历闯关后返回经典时出现一次；
3. 清屏时对齐 `BM_V81_APPEARANCE_PICK`、ready 数、`BM_V64_MATERIAL_ARM`、`BM_V80_MATERIAL_SINGLE_COMMIT` 和最终皮肤；
4. 引导清屏和产品规定的首次清屏保持原规则；
5. 特殊材质 ready 后，在下一清屏稳定边界原子切换；
6. 返回经典后不得混入普通方块，闯关仍由原版材质 owner 管理；
7. 任何修复不得重新引入 Replay 等待、双重变色、每步换材质或特殊预消除消失。

