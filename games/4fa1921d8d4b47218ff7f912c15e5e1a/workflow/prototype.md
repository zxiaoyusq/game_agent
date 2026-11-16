# Freestyle 同色多棋犯规补丁：只读静态复核

## 1. 范围、结论与真实执行记录

- 项目：`4fa1921d8d4b47218ff7f912c15e5e1a`；阶段：prototype；运行：`8c379ee0521e4c3696c2d704fd558d92`，attempt=1（恢复续接）。
- 用户要求：只读比较两份完整 JS，检查同色、多条、score 恰等于历史和的扩展，双方/两色、旧局、异步返棋、清历史、混色/queen、错误数据与重复执行。不得把旧竞品文字视为完整原版政策确认。
- 本轮实际工作：读取冻结方法资料；分页读取两份 JS 至末尾字符串表闭合，核对核心函数及调用链；读取旧观察文字；在用户真实补充后读取完整 diff 文本和实际规则依赖；进行人工静态状态与调度推演；仅写本报告。
- **没有执行 JS、启动游戏、浏览器、Creator、MCP 客户端或 ADB；没有构建、单元测试、动态测试、截图或真机验证。** 旧文档中的测试次数、录像、设备和日志不是本轮结果。`npm run build`、`npm test`、`npm run check` 未执行：当前是用户限定的只读原型审查，而非代码或测试阶段。
- 未修改游戏源码、资源、规则、测试、构建脚本或发布包；不推进美术/代码/测试阶段。产物：工作区 `/workflow/prototype.md`。

### 摘要结论

1. **目标扩展静态成立**：从仅一条匹配历史，扩展为一条或多条；匹配范围仍是当前 actor、当前 round。要求全体 type 相同且为普通棋 1/2，points 相同且为有限正数，score 严格等于 `points * 条数`。在实际普通棋分值 20/10 的有效数据下，这等于历史分值和。
2. **一次成功调用仍只返一枚、删一条、扣一枚分值**，不是清空所有同色历史，不是返全部，也不是固定扣 20。分数/HUD/历史同步提交；棋子物理返场异步提交。
3. **正常结算调用链具有回合去重和返棋完成屏障**：不能仅凭返棋 Tween 通常比 500ms 短就判安全。屏障等待 pending，累计等待达到阈值后主动 finish，再进入 queen、胜负与换手。
4. **新增函数级重复调用窗口可静态复现**：两条同色历史第一次成功后，剩一条仍满足条件，第二次直接调用会再次罚棋并覆盖 global pending。正常结算的 settledTurn 去重保护该入口；尚无正常游戏自然双罚的动态证据。
5. 混色、queen 历史及不满足总分的匹配集仍被拒绝；所提供完整 diff 只包含目标条件修改块。queen 依赖的源码现已读取，政策接口与两版调用方一致，**但运行时加载绑定和 diff 的独立全量重算仍未闭合**。
6. 有限分值乘法溢出接受 Infinity 是新增错误数据边界；null 历史、错误 type/points 配对、同局强推旧回合回调、找不到空位等为既有或条件风险，不应全部归罪于本补丁。

本报告 PASS/FAIL 均指**静态条件或防护性质**，不是测试通过/失败。BLOCKED 表示证据不足；NEEDS_CONTEXT 表示依赖产品假设或自然可达性。

## 2. 输入与证据索引

以下路径相对工程 `ref/`，均通过 `read_reference` 实际读取。目录名和文件名中的哈希样式字符串仅用于定位，未被当作本轮独立计算的文件 SHA256。

| 编号 | 角色 | 参考路径 |
|---|---|---|
| E1 | 后版 | `mcp-inputs/mac-codex/49f30646fca7e94b0525ab33789858d81f31be44960f0c8f3ed25486585ff707/Carrom_same_color_49f30646.js` |
| E2 | 前版 | `mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js` |
| E3 | 旧竞品观察文字 | `mcp-inputs/mac-codex/2b4680b7135bd8bfbfa79c1b63e0ed71f21fc81c6b2403cf7f1f3190b776a279/freestyle_foul_observation.md` |
| E4 | 用户补充的完整 diff | `mcp-inputs/mac-codex/acfe600b37eac8f3e25c9c670ecdd57d528f43499d851ebbeda4006a28e8692d/freestyle-full.diff.txt` |
| E5 | 用户补充的实际规则依赖 | `mcp-inputs/mac-codex/080bc7b20fc83732926bfce6785481287f93b63ac97735df9f8eaef7a0a6fb71/disc-rules.js` |

E1/E2 分页阅读至 `528000` 起的尾段，结尾为字符串表及函数闭合；`588000` 起读取均为空。没有取得工具直接返回的精确字符/字节总长或源码行号。大 limit 请求曾被截断，因此未以请求 limit 当作实际覆盖量。全文范围结论以后续分段阅读和 E4 补充交叉支持，不伪称本轮生成了全文 diff。

可复查核心定位：

- E1/E2 `120000` 起：`_carromFreestylePenalty`、清盘/棋盘重建；`128500` 附近：罚棋尾、queen 撤回、cancel/await、结算入口；`138000` 附近：飞分回调、罚棋调用、queen/胜负/换手屏障。
- E1/E2 `228000` 起后续更新段：入袋扫描、物理步进和延迟调度；`408000` 起后续段：棋子构造/物理注册/销毁；`468000` 起后续段：Tweener manager/Tween 实现。
- 这些 offset 是参考工具的文本定位参数，**不是源码行号**。E4 自带 `@@ -3325,10 +3325,12 @@` 行定位，属于上传 diff 的定位，不是本轮自行计数结果。

### 方法资料与采用边界

实际已读：冻结 `game-reverse-engineering/SKILL.md`（10.5.0）、同包 `references/execution-protocol.md`、`global-rules.md`、`unknowns-ledger-template.md`；四份冻结资料 `genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。

采用 owner/调用链、稳定提交边界、最小差异、证据分级和未知清单方法。专项 `modules/gameplay-logic-reverse/SKILL.md` 入口因未选中而读取失败，没有声称采用其正文；下轮如需专项模块应另行选入。本任务不新建 Canvas 游戏：真实源码使用 PIXI、planck/Box2D 接口、Tweener 和 GameSnacks，不套用 Cocos API，不声称原工程是纯原生 Canvas 2D。

## 3. 修改范围与版本适用性

### 3.1 已确认的差异

E4 标头 `before-98cdce5f.js` / `after-49f30646.js` 与 E2/E1 文件名标识相符。完整读取的 E4 **只有一个 hunk**，其上下文和增删行与 E1/E2 实读的 `_carromFreestylePenalty` 一致：

```diff
- if ((actor !== 'player' && actor !== 'opponent') || matches.length !== 1) return false;
+ if ((actor !== 'player' && actor !== 'opponent') || !matches.length) return false;
...
- if ((entry.type !== 1 && entry.type !== 2) || !Number.isFinite(entry.points) || entry.points <= 0 || score !== entry.points) return false;
+ if ((entry.type !== 1 && entry.type !== 2) || !Number.isFinite(entry.points) || entry.points <= 0 ||
+     !matches.every(function (item) { return item.type === entry.type && item.points === entry.points; }) ||
+     score !== entry.points * matches.length) return false;
```

据**提供的完整 diff 与核心源码交叉核对**，修改范围限于此条件扩展；已查的计分、历史写删、异步返棋、scheduler、Tweener、queen 调用、离场与重开逻辑未见此次改动。不能把人工分段阅读说成本轮独立逐字节全量比对。E4 无输入总长、完整输入哈希和生成命令，故“E4 是这两份上传文件的无遗漏全量差分”仍缺独立机械校验；这里不据此编造其他修改，也不宣称独立证明了唯一 hunk。

### 3.2 规则依赖适用性

E5 可完整读取，UMD 导出同一 rules 对象：浏览器挂 `root.CarromDiscRules`，CommonJS 用 `module.exports`。提供 `target/hasWon/layout/turnTicks/freestyleQueen`，与 E1/E2 的 `window.CarromDiscRules.*` 调用名字及参数形式兼容。

- `freestyleQueen(previous, shot)` 接受 `phase/owner` 和 `actor/foul/queen/ordinary`，恰与结算构造的数据一致；返回 `state/returnQueen/revokeOwner`，恰与调用方读取的数据一致。
- `target/layout` 的六棋 Delhi 特例为 `mode===0 && table===0`；mode=2 Freestyle 不落入此特例，target 返回 9、layout 返回 null，使用原布局。此 target 是摆棋数量，不是 Freestyle 胜利分数 `_0x153877`。
- E5 无版本号/构建标识；未提供 HTML script 加载顺序、发布 manifest 或运行时对象证据。用户说明它是实际依赖，且接口兼容，可据此审查**该配对源码**；仍不能独立确认两版已部署时都加载这一字节版本。不可用接口兼容替代运行时版本确认。

## 4. 核心规则、状态与提交边界

### 4.1 选择条件

先 `history.filter(entry.actor===actor && entry.round===currentRound)`，再验证 actor。因此：

- 包含同一局内该 actor 的各个旧 turn 记录，这是预期的累积得分历史；没有按当前 turn 限制。
- 对方和旧 round 的**结构有效**记录不参与 all/equality，不阻塞当前 actor 的正常同色罚棋，也不被删除。
- 历史顺序使用数组首匹配 `matches[0]`；不依据 `turn/queueIndex` 排序，不取最后入袋棋。
- 后版要求所有匹配记录 type 和 points 都严格相等；不接受“当前历史里存在同色子集”而其余为混色/queen。
- 用乘法而不是 reduce 求和。在正常整数分值 20/10 下完全等价，计分比较容差为 **0**。浮点舍入、非标准分值及 Infinity 不能按正常等价扩展解释。

### 4.2 分值与双方/颜色独立

Freestyle mode=2，分值表 `[50,20,10]`：queen=type0/50，普通 type1/20、type2/10。

| 属性 | player | opponent |
|---|---|---|
| 得分 | `_0x4d3bf1` | `_0x41f634` |
| HUD | `_0x27ee82` | `_0x458adc` |
| SDK 通知 | `_carromReportScore`，内部 try/catch | 此处不发送玩家 score SDK 通知 |

颜色并不由 actor 决定：type1 返回 `_0x3e4566`、棋子 type 字符串 `'player'`；type2 返回 `_0x2a9c75`、棋子 type 字符串 `'oponent'`。actor 的 `'opponent'` 与棋子类型的 `'oponent'` 是源码中的不同字符串，不能“纠正拼写”后推演。

### 4.3 一次成功调用的时序

1. 检查条件，捕获 entry/current round，设置闭包 `returned=false`。
2. 构造同 type 临时动画棋；构造器已经创建物理 body，立即 `removeFromWorld()` 销毁 body，仅保留动画节点。
3. 若提供 state：覆盖 global `_carromPendingPenalty`，挂 `cancel/finish`；没有已有 pending 拒绝。
4. 注册 Tween（20–30 逻辑刻度，不是 20–30ms）。`addTween/start` 不会同步完成回调。
5. **同步 splice 首记录，score 减 entry.points，更新 actor HUD；player 通知 SDK；返回 true。** 正常 caller 将 true 赋给 state.pending。
6. 自然完成或 state.finish 调用 restore：returned 防重，检查 active/current round；新建同 type 物理棋、设位置/type、加入容器、找落点、push 对应颜色组；移临时节点；global 仍指向 state 时清 global；通知 onReturned 令 caller pending=false。
7. restore 不再扣分，不重新写历史。returned 是闭包一次性防护，不是整个函数的幂等键。

有效 restore 的物理棋不是纯图像：`_0x54e9a5` 构造器直接 world.createBody/createFixture；`removeFromWorld` 是 destroyBody 并 body=null。设置 worldX/Y 会转换尺度并同步 body 位置。`_0x1f3ae5` 只负责选落点，不负责注册物理。

### 4.4 计分历史来源与先后顺序

普通入袋扫描仅移除物理棋/颜色组、保动画节点、加入 `_0x31089b`；入袋 Tween 的空 onComplete 不提交得分。结算非犯规飞分 callback 才同次提交 score 与 `{type,points,actor,round,turn,queueIndex}`，受 finished+active+round+turn 防护。结算 done 显式调用未及时完成的 score finish，晚动画回调不重复提交。

queen 的 50 分/type0 历史在结算循环预提交一次；飞字仅表现，不再次计分。数组首条不保证真实最早/最晚入袋：先扫描 type1 组再 type2 组，组内顺序及飞分结束顺序影响历史排列；queueIndex 不是精确物理时间，也不是唯一棋子 ID。同色有效数据下首尾返棋颜色/分值相同，但不能据此宣称“返最后一枚”。

## 5. 正常调用链与异步完成屏障

### 5.1 入口和输入窗口

`_0xbdafb3(expectedTurn)` 默认 current turn；旧 expectedTurn、已 settledTurn、matching timeoutReady、inactive 都阻止提交。棋子仍运动时用 50ms 逻辑 scheduler 重试；确认静止后标 settledTurn 并冻结刚体。

Freestyle 对当前入袋队列做 snapshot。**只有母球犯规且 snapshot 长度为 0，才调用历史罚棋。** 本杆普通棋或 queen 同时入袋时，走本杆返棋路径，不调用该历史罚棋函数；本杆返棋不新增得分历史。母球犯规令续杆标记为 false。

结算可提交窗口为 active、当前 round/turn、未结算且棋子静止；移动/超时扫描边界在上述 guards 下等待。玩家输入/AI 输入需服从原工程状态，本报告未动态验证全部指针手势与设备输入延迟，不另造新操作窗口。AI 开回合与瞄准/击球已见 round/turn 保护。

### 5.2 屏障流程

- 空队列基础等待 500ms，有队列 1000ms。
- `_carromAwaitPenalty(state, done)`：pending 时累加 waits；达到 20 次检查且存在 finish 就强制 finish；仍 pending 再排 50ms 检查；不 pending 才 done。
- done 再查 active+captured round+expected turn，补齐本杆返棋和飞分后调用 queen 政策、判胜负、决定续杆/换手。
- 因此在正常有效 state、无异常且更新继续的前提下，历史返棋提交先于最终换手。该性质来自**屏障**，不是 Tween 时长估算。
- finish 是 `Tweener.extract(disc)` 后强制目标中心坐标并 restore 的自定义 state.finish，**不是** manager 的 `Tweener.finish`。

`_0x338c29` 用空对象 Tween 模拟延迟：`time=(delayMs/1000)*60`，捕获 round，回调检查 active+round；500/1000/50ms 对应 30/60/3 刻度。并非 setTimeout，也无通用 turn guard，关键调用方再查 turn。

广告/宿主暂停通过 matchBlocked 阻止逻辑更新、清 accumulator，并暂停匹配 timer；期间不承诺墙钟兜底时间。`_carromMatchSchedule` 是另一套真正 setTimeout 的大厅/匹配 UI timer，有 owner/version/remaining 等检查，不能与罚棋 scheduler 混为一谈。

### 5.3 Tweener 的调度推演（未执行）

manager.update 正向遍历**实时 tweens 数组**。自然 Tween 结束先 stop/splice 再 onComplete；extract 找首同 target 调 stop，不触发完成回调。因此静态可确定：本轮删除当前项会让相邻下一项跳过本次 update；回调新增项也可能在同次遍历后续被访问。

可复现手工调度：令数组 `[X, P, W]`，X 当前 tick 结束并删 index0；数组变 `[P,W]`，manager 的 i 随后变1，因此访问 W、P 跳过一 tick。若此时 W 是 await、P 是罚棋动画，W 看到 pending=true 应继续等待，不换手；达到等待阈值通过 state.finish 取出 P 并 restore，再 done。**晚一 tick 不等于双罚，也不能以相邻数组删除推断屏障失效。** 是否存在极端持续饥饿/实际耗时需动态验证。

manager/Tween 自带 finish 的先 onComplete 后 stop，与自然更新顺序不同；stop 的 indexOf 无非负保护是既有通用重入风险候选。本次历史罚棋兜底不调用该 finish，未确认关联自然触发路径，不将其列作本补丁已复现缺陷。

### 5.4 取消、旧局与迟到回调

重开 `_0x5480e3`：discard pending penalty/queen、round++、清结果/queen 状态/history，双方 score/HUD 归零并重建棋盘。离场相关路径先 discard，匹配/大厅还停止 timer 并令 inactive。

cancel 设置 returned=true、extract 动画、移节点、pending=false；晚 restore 立即返回。discard 先置 global=null 再 cancel。即使旧 closure 在重开后到达，active/round guard 也阻止旧棋返到新局。

restore 没有 turn guard、没有 global pending 身份作为“允许提交”的 gate、没有独立结果提交检查。正常屏障与离场取消负责外围保护；仅同局人为强推 turn 或覆盖 pending 时，函数本身不足以拒绝旧操作。

## 6. Queen 与混色边界：补充依赖后的核对

E5 的真实状态表如下；函数内注释明确指出 same-shot coverage 仍是 product assumption。

| 初态 | shot 条件 | 输出 |
|---|---|---|
| board | queen && !foul && ordinary>0 | covered，owner=shot.actor |
| board | queen && !foul && ordinary=0 | pending，owner=shot.actor |
| board | 无 queen 或 foul | 保原 state，不要求撤回旧 queen |
| pending | shot.actor===owner && !foul && ordinary>0 | covered，保 owner |
| pending | 其余条件 | board；returnQueen=true；revokeOwner=旧 owner |
| covered | 任意正常 shot | 保 covered；该函数不因随后犯规重新撤回 covered queen |

- pending 状态来源的 points=50 由 caller 补存；covered/board 的新 state 不保留该 points 字段是当前实现事实。
- `_carromReturnFreestyleQueen` 找 current round/owner/type0 首历史，缺失时取 pending state.points||0；同步新建 queen 物理棋、找落点/加 queen 组、删记录、扣 owner 分/HUD；returnCommitted 防重复。它与普通历史罚棋是不同函数，不受新 every 条件改动。
- 当前 actor 的匹配 history 含 type0 时，普通罚棋拒绝，不会从中挑白/黑子集；混色匹配集同样拒绝。对方或旧 round 的 type0 不参与过滤结果，不阻塞当前 actor。
- 本杆 queen/普通/母球同入袋：snapshot 非空，只返本杆入袋棋，不另罚历史；后续 queenDecision 处理既有 pending queen。不能仅凭此政策确认竞品是否还要求额外历史罚棋。

**与新扩展可相邻发生、但不是 queen 政策改动的推演**：pending owner 的 history 为 `[Q50,W20,W20]`、score90；下一杆空袋母球犯规，普通罚棋因 type0 拒绝，queenDecision 撤 Q50，留下 score40/history `[W20,W20]`。后续该 actor 再次空袋母球犯规，后版可扣20返白1，前版因两条拒绝。这是删除 queen 历史后新条件的预期生效范围，不能说 queen 撤回函数被补丁改写。

E5 没有 schema/状态合法性校验。对损坏 owner/points 的 queen 错误数据处理不充分为既有条件风险，未把“正常 pending 状态记有50”延伸为所有损坏数据均安全。

## 7. 静态验收矩阵

记 W=type1/20，B=type2/10，Q=type0/50。除另注明外，历史属于当前 round/指定 actor，score 是该 actor 分数；函数成功时以动画有效完成后最终棋组数量计。以下全为**未运行的人工推演**。

| ID | 初态/调用条件 | 前版 | 后版最终结果 | 静态判断 |
|---|---|---|---|---|
| M01 | player，[W]，score20 | 成功 | score0，删1，白组+1 | PASS，保留单条 |
| M02 | player，[B]，score10 | 成功 | score0，删1，黑组+1 | PASS，非固定20 |
| M03 | opponent，[W]，score20 | 成功 | 对手score0/对手HUD，白组+1 | PASS，actor/色独立 |
| M04 | opponent，[B]，score10 | 成功 | 对手score0/对手HUD，黑组+1 | PASS |
| M05 | player，[W,W]，score40 | 拒绝 | score20，余W1，白组+1 | PASS，新扩展 |
| M06 | player，[B,B,B]，score30 | 拒绝 | score20，余B2，黑组+1 | PASS，新扩展 |
| M07 | opponent，[W,W,W]，score60 | 拒绝 | 对手score40，余W2，白组+1 | PASS，新扩展 |
| M08 | opponent，[B,B]，score20 | 拒绝 | 对手score10，余B1，黑组+1 | PASS，新扩展 |
| M09 | [W,W]，score39/41/0 | 拒绝 | false，无分/历史/棋组改动 | PASS，严格等值 |
| M10 | []，score0 或非0 | 拒绝 | false | PASS，无欠罚逻辑 |
| M11 | 当前player W2/score40，另有对手Q、旧round B | 拒绝当前两条 | 仅当前player删W1扣20；其余保留 | PASS，结构有效数据隔离 |
| M12 | 当前 actor [W,B]，score30 | 拒绝 | false | PASS，混色不扩展 |
| M13 | 当前 actor [Q] 或 [Q,W,W]，总分吻合 | 拒绝 | false | PASS，queen/含queen不扩展 |
| M14 | type相同而points不同 | 拒绝多条 | false | PASS，同色仍需同points |
| M15 | 非player/opponent，历史结构正常 | 拒绝 | false | PASS；不是防null验证 |
| M16 | 同一局旧turn的W2，score40 | 拒绝 | 可成功 | PASS，累计历史；不是旧round |
| M17 | 空袋母球犯规，正常结算 | 一条才罚 | 同色有效多条罚一枚，不续杆 | PASS，条件路径 |
| M18 | 母球+本杆普通或queen入袋 | 不调用历史罚棋 | 同样不调用；返本杆棋/queen政策处理 | PASS，路径未扩展 |
| M19 | 同expectedTurn重复结算入口 | settledTurn拒绝后续 | 相同 | PASS，正常入口去重 |
| M20 | 同一restore自然回调+强制finish重复到达 | returned防重 | 一次物理返棋，不二次扣分 | PASS，闭包级防重 |
| M21 | Tween延迟，await仍pending | 等待/兜底 | 完成后才能done | PASS，有效更新/无异常条件下 |
| M22 | 返棋中重开/离场再迟到回调 | cancel/round保护 | 新局无旧棋污染 | PASS，已读正常退出路径 |
| M23 | pending时同局直接清history且保score | 条件风险 | 旧closure仍可返棋 | NEEDS_CONTEXT，见R05 |
| M24 | 直接重复调用penalty两次，W2/40 | 初次即拒绝 | 两次同步扣删，两个动画 | FAIL，函数幂等性质 |
| M25 | null/非数组history、非法points/溢出 | 见反例 | 见反例 | FAIL/拒绝，区别有效数据 |

## 8. 可复现问题与精确状态推演

所有 R 项均为静态推演，不提供虚构执行日志。为手工复查，可把下述初态替换进 E1/E2 同名函数并逐条检查；若后续授权动态验证，应在隔离 harness 中执行，不在真实发布游戏中故意注入损坏数据。

### R01 新扩展的函数级双罚与 pending 覆盖（中风险，正常自然触发未证）

初态：active=true、round=7、player score40，history 两个不同对象 W1/W2（同type1/20，actor player，round7），白组数量c；global pending=null；两个不同 state A/B 都 `{pending:false}`。

1. 按正常 caller 赋值形式 `A.pending=penalty('player', ()=>A.pending=false, A)`：返回true；score20，history `[W2]`，白组仍c，global=A，Tween A 未完成。
2. 不等动画，再 `B.pending=penalty('player', ()=>B.pending=false, B)`：一条W2和score20仍匹配；score0，history空，白组仍c，global=B，Tween A/B 均存在。
3. 若保持同round active并自然完成二者：A 虽不是 global owner 仍可 restore，白组c+1，A.pending=false；B完成后白组c+2，B.pending=false，global清空。**同一次外部事件若错误重复调用，实际扣两次、删两条、返两棋。**
4. 前版相同原始两条初态第一次就false。后版并未新增 operationId/pending 拒绝；单closure returned不能防另一次函数调用。
5. 若此时只调用 discard，取消的是 global=B；A 不被该 global取消。如果不离场、不递增round，A仍能返棋。正常重开round++可额外阻止A返入新局。

范围：此反例证明公共 helper 非幂等及 pending 覆盖风险，不证明 `_0xbdafb3` 正常重复提交；同turn settledTurn guard在首次进入循环前已写入，拒绝正常第二次入口。修复建议仅供下轮：加入由round/turn/operation形成的幂等事务键或已有pending拒绝/一致取消，不在本轮修改。

### R02 null 历史在 actor 验证之前抛错（既有）

初态：history=`[null]`，其他状态任意，actor 即使非法或null条目意图属于旧局也无区别。filter 首次读 `entry.actor` 即 TypeError；未到actor合法性检查。history=null、undefined或无filter对象同样会失败。两版都如此，不是新 every 导致。

结构有效但 points 为字符串`'20'`、NaN、0、负数或Infinity的首匹配会正常false；不可把这些拒绝当作null安全证明。

### R03 type/分值表未校验（既有缺口，被新多条路径承接）

初态：两条 `{type:1,points:10,actor:'player',round:7}`，score20。后版 all/equality成立，删1、扣10，最终返type1白棋；白棋实际正常应值20。前版两条拒绝，但前版单条 type1/points10/score10 已接受并错配，因此根因是两版都不验证 `points===分值表[type]`，不应说本补丁首次创造该类错误数据问题。正常历史写入从分值表取值，注入此初态的自然来源未证。

### R04 乘法溢出接受 Infinity（新增，正常20/10不可达）

初态：history两条同type1、points=`Number.MAX_VALUE`，player score=`Infinity`。每条points本身有限且正，同值检查成立；`points*2===Infinity`，与score严格相等，所以后版接受。同步删1后 `Infinity-Number.MAX_VALUE` 仍Infinity，最终返1棋而score无法反映扣分。前版多条拒绝；前版即使单条同有限points，Infinity score也不等points而拒绝。

这是没有 `Number.isFinite(score/total)` 的新增边界，不是常规整数分值计算误差；不得宣称正常玩法会生成Infinity。

### R05 清空历史不取消在途返棋（既有、条件风险）

初态：用有效W1/score20成功罚棋，故同步score0/history空，动画pending。动画未完成时，在同round active直接做 `history=[]`（多条例可在第一次后将剩余history清空），不取消、不递增round。restore使用已捕获entry，仍返1棋，不再扣分、不重新写history。多条例若原score40，首次后score20、剩1历史；直接清空保score20，返棋后score20/history空的不一致**首先来自外部清空破坏不变量**，不是restore偷偷重添历史。

正常重开同时cancel、round++、score归零，不能用上述人为操作证明正常重开漏保护。本轮未证明正常代码存在“仅清history且保score/同round继续”的调用路径。

### R06 同局强推turn仍允许旧返棋（既有、条件风险）

初态：active、round7、turn10，有效罚棋pending；绕过await强制turn11而round不变。旧restore只查active+round，会返棋；onReturned仍可调用原state。最终done的turn guard不能撤销已经发生的物理返场。正常屏障本来阻止turn先于返棋推进，因此是函数级防御不足，不是正常必现旧回合污染。

### R07 落点全堵仍无失败提交协议（既有、条件风险）

`_0x1f3ae5` 作有限轴/对角/环网格搜索，无全部失败的明确返回信号；候选全部堵住时仍保留原/当前位置，调用方照样push棋组并完成pending。不能据静态空位搜索确认无重叠/无物理异常；需要固定堵塞场景和实际planck验证。新条件不改该搜索。

## 9. 物理、界面和验收约束（不扩展为新游戏设计）

本轮设计决策是保留原工程玩法与表现，仅复核罚棋补丁；不存在新美术/换皮授权需求。

- 核心循环：摆/瞄母球→击球→物理运动/入袋扫描→静止或超时结算→本杆飞分/返棋、必要历史罚棋→queen政策→胜负→续杆/换手。
- 状态：round/turn/settledTurn、active、score、当前入袋队列、累积history、queen board/pending/covered、penalty pending/returned、广告/宿主 blocked。
- 物理步长：逻辑accumulator循环每次update(1)，扫描后planck step `1/60`；不是本轮新增自适应物理。棋子圆半径16/尺度换算，入袋中心距离阈值 `<=20`；构造动态body含sleep/bullet与阻尼设置。碰撞/反弹实际稳定性未执行验证，不重新标定参数。
- 时序单位：Tween和scheduler按60逻辑刻度折算；快慢帧及暂停下墙钟耗时不能由该折算直接保证。成功分数/历史容差0，返棋计数容差0；物理位置容差尚未做动态标定，本轮不编造设备可接受误差。
- 成功/失败：有效普通罚棋一次删1/扣p/最终物理返1；无匹配/不满足全体同色同points和总分则false且不更改此事务数据。正常犯规不续杆。Freestyle胜利分数用当前配置 `_0x153877`，queen非pending才允许判达标；双方同时达标优先当前行动方。target9摆棋数不是胜利分数。
- 界面布局：沿用中心棋盘/母球与瞄准控制、player/opponent各自score HUD、飞分/返棋动画及结算/大厅界面；罚棋从得分方HUD飞回棋盘，不按actor强制某颜色。未出新界面，未修改玩家文案或lang；本轮无构建语言验收，默认英文的新开发要求不被用来擅改上传游戏。

### 后续如授权动态验收的必要条件（本轮未执行）

1. 以本报告M01–M25建立隔离且固定round/turn/分值的状态测试；双方×两色×1/2/3条覆盖；断言同步score/history与延迟棋组/body计数分开。
2. 核验自然完成、晚完成、重复restore、await阈值finish、广告暂停/恢复、重开/离场和多个相邻Tween删除；实际固定输入与固定步长记录顺序。
3. 验证正常结算入口重复触发不双罚；单独复现R01 helper重复调用，不能混为正常用户操作。
4. queen各状态与母球/普通同杆组合按E5真值表核对；覆盖撤queen后同色多条历史的后续犯规。
5. 数据损坏/null/非法points/Infinity/同round强推turn/全部落点堵塞标为健壮性验收，不冒充正常可达玩法。
6. 提供实际HTML/依赖加载清单与全输入哈希，重算全文差异。若进入代码/测试阶段，按该阶段重建并运行全部必要命令和真实dist浏览器输入检查；不沿用旧报告作为本轮动态通过证据。

## 10. 竞品文字的取舍与证据限制

E3 是旧转述，不是本轮直接观察。

- Delhi 联网：旧文字标识2026-11-12、Miniclip `com.miniclip.carrom`19.6.0/1491，目标160、每色9，queen/白/黑50/20/10；白入袋20、白9→8，再母球犯规20→0、8→9并换手，与返白1扣20相容。返场瞬间被遮挡；不能由此确认多条同色、混色选择顺序、固定20、queen或零分欠罚。
- 离线传玩 Freestyle Disc Pool：目标180、每色12，与Delhi不是同配置；黑入袋10、12→11；母球犯规10→0、11→12；其他40→30/30→20伴新增黑。缺完整历史颜色/顺序，不能证明本补丁的“全体同色且score=历史和”就是原版完整条件。零分保持0未见新棋，不等于已排除所有欠罚机制。
- “黑棋20分”“9→10超初始盘”已在旧文字勘误，不复用错误值。官方一般Carrom帮助不等于当前Freestyle规则确认。
- E5 本身承认同杆cover为product assumption；E1 queen撤回注释也是provisional policy。补充源码闭合的是**本项目实现**，不是竞品产品规则。
- 旧MCP/本机若干测试通过、截图/录像路径仅为历史陈述，本轮未访问其真实文件，不作为运行证据。

## 11. 未知清单与闭合状态

| 编号 | 状态 | 证据/缺口 | 本轮处置 |
|---|---|---|---|
| U01 | 部分闭合 | E4可读、仅1hunk、标识/核心内容配对；无全输入哈希/总长/重算日志 | 使用“所提供完整diff仅1hunk”；独立无遗漏全文校验仍BLOCKED |
| U02 | 源码闭合，绑定未闭合 | E5可读、API/结构与双方调用兼容；无HTML/发布manifest/版本号 | 完成queen政策静态表；运行时版本适用性保留限制 |
| U03 | 未闭合，NEEDS_CONTEXT | E3配置不同且缺完整入袋史/返场直接观察 | 不宣称竞品原版确认；需新增直接证据 |
| U04 | 未闭合，NEEDS_CONTEXT | R01直接helper重复调用成立，正常入口settledTurn去重 | 不称正常自然双罚；需动态入口追踪/复现 |
| U05 | 已闭合（静态） | `_0x338c29`、Tweener更新/取消、await和棋构造实际读取 | 调度单位/跳项/物理注册不再列作未知 |
| U06 | 未闭合，BLOCKED动态 | 无本轮执行、设备、帧耗时/位置误差数据 | 所有矩阵/反例均标未运行推演；不借旧测试补齐 |
| U07 | 未闭合，NEEDS_CONTEXT | R02–R07错误数据/绕过状态/堵塞场景的自然来源未证 | 分类既有/新增，不推断正常可达 |
| U08 | 工具限制 | 专项未选入口读取失败 | 已读总入口/协议方法；必要时下轮补选，不伪称已采用 |

## 12. 收口判定

**静态目标条件复核：PASS（有效20/10历史、正常caller、无运行异常的限定下）。**

**函数级幂等性质：FAIL（R01）。** 新增Infinity错误数据边界：FAIL（R04）。既有健壮性缺口与外围状态绕过风险另列，不以此制造补丁无关改动。

**修改范围：所提供完整diff仅目标条件hunk，核心实读匹配；独立全量字节校验尚未闭合。Queen政策：配对源码可核对且未见此补丁改变，运行时依赖版本绑定仍未闭合。**

本报告不作动态验收通过或上线安全承诺；未确认下一阶段，没有修改游戏。用户在本轮真实补充并要求继续完整复核，补充参考已读取；剩余缺口明确保留，不推断补齐。
