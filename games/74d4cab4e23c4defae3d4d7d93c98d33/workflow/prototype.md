# Carrom 匹配半构造资源清理审查

## 1. 范围、结论与证据等级

- 项目：74d4cab4e23c4defae3d4d7d93c98d33；阶段：prototype；attempt=1。用户要求静态审查，不是新建游戏、玩法改造或直接修补源码。
- **结论：补丁改善了父类初始化成功后、匹配构造中途失败时的定位与已挂载子树 Tween 清理，但不能证明完整回滚或无泄漏。退款路径的异常隔离不满足要求（FAIL，静态反例）；运行验收为 NEEDS_CONTEXT，未执行。**
- 最优先问题：清理循环没有异常边界和 visited，可能跳过退款，甚至无限循环；后续匹配动画的异常不属于入口同步 catch；单个全局 constructing 槽不是资源所有权账本。
- 证据分为：源码直接证明、带明确前提的静态反例、缺依赖/动态证据的未知项。本文 FAIL 表示静态设计条件不成立，不代表已运行故障注入。
- 不修改参考 JS，不制作 dist、试玩包、美术或新的游戏界面，不自动推进后续阶段。报告中文；现有玩家内容保持原状。若后续新增玩家提示，默认英文，例如 “Match setup failed. Your entry fee was refunded.”，只有退款确实提交后才能显示；保存失败用 “Progress could not be saved.”，不虚报持久化成功。

## 2. 参考与方法

以下路径均相对工程 `ref/`，均通过 read_reference 实际读取：

- **A（对照）**：`mcp-inputs/mac-codex/de2cfc7eac9d748af09307b139885429df5f0007286a30f655f4c76ae00da228/ad-after-end.js`
- **B（候选）**：`mcp-inputs/mac-codex/5124e5e25fac79542fdd2e91eb28300bd872df6531337a1d658e7a4e13f490f1/arena-partial-cleanup.js`

定位索引（offset 为工具字符偏移，区间不是行号；函数名是精确搜索锚点）：

|证据|已读范围/锚点|用途|
|---|---|---|
|E1|A、B `[0,64000)`；`_carromActiveMatch`、`_0x3a0318`、`_0x9b0cd`、pause/resume|全局槽、保存、宿主暂停与页面退出|
|E2|A `[88500,106500)`；B `[94800,103300)`；`_0x3153fe`、`_0x4d0a10`|正常安装与扣费/退款分支的局部差异|
|E3|B `[64000,184000)`；A `[88500,106500)`；`_0x248455`|插屏发起、暂停、结束与异常路径|
|E4|B `[244000,304000)`；`_carromMatchSchedule`、Arm、Cancel、Pause、Resume、AdPause、AdResume|定时器真实 owner、版本和暂停归属|
|E5|B `[364000,424000)`；A `[384000,410000)`；`_0x104b9b`/`_0x3875cf`、`_0x5e1e47`/`_0x26cb35`|匹配构造、roll/stop、奖池数据 Tween、粒子与 shuffle 链|
|E6|B `[502000,528000)`；`Tweener.extract`、addTween、Tween.stop/update|提取不是递归、不是 finish；同步回调语义|
|E7|B `[528000,540000)`；`ParticleManager`|全局粒子列表和 `_velocity` 非树目标|
|E8|B `[184000,274000)`；`_0x49d791`、`_0x4bf21a`|固定物理步与 tick 累积、暂停门控|

只对与本次请求有关的路径做人工静态对照，**没有执行全文自动 diff，没有证明其他位置完全相同**。目录名中的长字符串不当作本次重新计算的文件 SHA256，也不据文件名断言正式版本谱系。

实际读取所选 `game-reverse-engineering/SKILL.md` 及 `references/execution-protocol.md`、`global-rules.md`、`unknowns-ledger-template.md`：采用真实 owner、稳定提交边界、证据分级、最小变更和未知清单方法。专项模块入口未被本轮选中，读取被工具拒绝，未声称采用其正文。

实际读取本轮冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。采用状态、时间、输入、异常验收约定；不套用新游戏制作流程。参考源码明确使用 PIXI、planck、Howler 与 GameSnacks；项目配置 Canvas 2D 不构成迁移授权，也不能把参考称作原生 Canvas 实现。PIXI 外部 Container 实现与版本未提供决定性证据。

## 3. 局部差异与生命周期

B 相对 A 在已核对的匹配路径中新增：

1. 全局 `_carromConstructingMatch = null`。
2. `_0x3875cf` 中先 `PIXI.Container.call(this)`，**然后** `_carromConstructingMatch = this`。
3. `_0x3153fe` 在 `new _0x104b9b(...)` 返回后先保存 active，随后清空 constructing，再设坐标、挂 stage、注册 ready/start 监听。
4. `_0x4d0a10` 的同步失败 catch 从只取 active，改为 `active || constructing`；清空两槽；取消 failed owner timers；用栈遍历 failed 的当前 children，并逐目标 `Tweener.extract`；最后移除根节点。退款、保存、选择页恢复仍位于清理之后。

**正常完成清空指的是调用方 `new` 返回后的 constructing 清空，不在构造函数末尾，也不等于匹配动画已经完成。** `_0x104b9b` 是 IIFE 返回的普通函数 `_0x3875cf`，不是 ES 派生 class；父类是外部 `PIXI.Container.call(this)`，不是另一个混淆业务父类。

### 核心循环与规则状态（审查模型，不新增玩法）

`Selection → EntryPending/扣费 → 广告发起 → Constructing → Active/挂载 → Roll → Stop → Ready → StartingShuffle → Start/移除匹配 UI → 实际对局 → 结算 → Selection`。

- 入口仅允许选择页可见、无 pending/active、合法整数 arena、有限非负 fee、有限足额余额。pending 在同步 try/finally 内保护重复扣费。
- 构造先搭建头像和滚动子容器，再 `loadTable` 和 `startRoll`；**startRoll 在奖池图标、BitmapText 和最后亮光节点创建之前调用**。因此这些后置资源抛错时，滚动 Tween 与 3000ms owner timer 已可能注册。
- 滚动子容器 roll 对自身注册无限 Tween；stop 用 addTween 替换同目标滚动 Tween，40 tick 后 emit stop。stop 监听建立奖池动画、粒子和 ready timer；有 fee 时 ready 延迟 `0xbea=3050ms`，否则 `1000ms`。这些是 setTimeout 的 ms，与 Tween 的 tick 不能混用。
- ready 开始箭头 shuffle，最后 Tween onComplete emit start；入口 start 监听要求 active 身份、stage 父节点匹配，先清 active 再移除匹配 UI、调用 `_0x1260d2`。实际对局初始化异常发生在后续回调，不能被早已结束的扣费 try/catch 回滚。
- 成功条件：一次入口扣费、一次合法进入实际对局、constructing 不残留。失败条件：本次同步设置异常；当前实现只在清理正常终止后尝试内存退款及 UI 恢复。广告不可用在包装器正常降级时并不等于匹配失败。
- 匹配 UI 布局：背景、两侧头像/名称/棋子、奖池图标与金额、先手箭头；选择页/商店/大厅在安装时隐藏，失败调用选择页恢复。未实际渲染验证布局。

### 物理、计分、输入与可接受误差

- 参考 `_0x49d791` 用 `world.step(1/60,10,10)`、clearForces；`_0x4bf21a` 累积 ticker delta，`while (accumulator > 1)` 消耗整数 tick。门控暂停时不执行模拟，广告暂停将 accumulator 清零；不改为可变物理步长，不新增 catch-up 上限作为本次补丁。
- 可见入袋距离条件为到袋心 `<=20`，本次不改变碰撞半径、Planck 配置、皇后/罚分规则或胜负计分。匹配奖池数字 Tween **仅改 BitmapText，不应被当作发奖提交**；实际结算奖励和广告奖励是另外的业务路径。
- 输入窗口：只有 Selection 合法入口接受选择；pending/active 时重复选择不得再次扣费；匹配阶段不允许射击；正常对局输入保留原 host pause 与对局状态门控。
- 验收建议：钱款与入口/开始计数要求精确相等，不能用浮点容差掩盖重复退款；以整数安全币值测试。固定 tick 输入下，物理参数和逻辑计分与 A 对照零差异，允许渲染比较初设 0.5 逻辑像素容差（建议值，非已测结果）。Tween 时间比较容许 1 tick；owner timer 在可控时钟下按剩余 ms 精确验证，真实浏览器只检验不早于应有期限和至多一次，不承诺后台 timer 的最大迟到值。慢帧按现有累积规则对照，`>1` 不擅自改为 `>=1`。

## 4. 逐路径覆盖与发现

### F1 — 高：遍历失败可阻断退款（源码 + 条件静态反例，FAIL）

E2 中 `if (node.children) stack.push.apply(stack,node.children)` 在任何逐节点 try/catch 之外，且没有 visited/节点合法性判断：

- children 中有 null：pop 后读 null.children 抛 TypeError。
- destroyed 节点 children getter 抛错、非预期 array-like、两次 getter 返回不一致：遍历直接中断。
- children 含自身/祖先：重复入栈，循环不结束。有效 PIXI 树通常不应循环，但候选没有在审查要求的损坏树边界自保。
- 超宽 children 的 apply 参数数量超限：可抛 RangeError（阈值依 JS 引擎，不虚填数字）。

抛错后外层 finally 只解除 pending，**退款、退款保存、根节点移除、UI 恢复以及最后警告可能全部跳过**；循环不退出时 finally 也到不了。相比 A 的简单异常清理，B 在失败分支引入了新的退款中断点。

### F2 — 中：父类失败仍不可定位，不能当作 ES super 语义（E5，NEEDS_CONTEXT）

Container.call 抛错时尚未写 constructing，new 不返回，active 已先清空，catch 常拿不到本次对象。父类若在抛错前注册外部资源，补丁无法释放；父类若没有外部副作用，则不因此自动产生持久泄漏，普通不可达对象可被 GC。

本参考是普通构造函数，this 在 `.call` 前已存在；理论上可以提前注册根对象，但其 children 尚未初始化，不能直接依赖树遍历。若换成 ES 派生 class，才有 super 返回前不能访问 this 的限制。可靠办法是在父类可产生副作用前建立 attempt context，父类通过资源注册协议交接，而不是只移动一行就宣称安全。

### F3 — 中：未挂载对象不在树中；真实构造风险要区分（E5/E6）

B 可清理 startRoll 后、后置奖池资源抛错时已经挂载的滚动容器 Tween 和 root owner timer，这是真正改善。

`new _0x5e1e47()` 失败或它返回后设坐标/addChild 失败时，该子容器还不在 root.children；但已读其构造仅建节点、没有注册 Tween/timer，不能断言这个具体断点一定产生外部泄漏。其它 Sprite/BitmapText 的底层资源创建若有副作用或外部缓存，需依赖实现证明。通用静态反例“局部未挂节点先注册 Tween 再抛错”不被当前算法覆盖，资源账本才能覆盖。

### F4 — 高：异步动画异常不在同步回滚边界（E2/E5/E6，FAIL：完整生命周期覆盖）

`_carromMatchArm` 的 task.callback、滚动 stop 监听、shuffle 完成回调、奖池 onUpdate 均在入口返回后执行；这些路径没有统一 owner abort。比如 stop 监听创建部分动画后 ParticleManager.emit 或 BitmapText 更新抛错，不会自动退款或清子树。

Tweener.update 的回调执行没有逐 Tween 异常隔离。onUpdate 在 stop 前抛错时该 Tween 仍留在全局 tweens，可后续再抛错；这可能妨碍其他动画推进。不能把“构造 catch 加清理”推广成所有匹配失败都有清理。

### F5 — 中：非树目标和其他管理器不覆盖（E5/E6/E7）

真实匹配代码存在：

- stop 监听 `addTween({value: prize-fee*2}, {value:prize}, {onUpdate:...})`：目标是匿名数据对象，闭包保留 `_cc826c` 金额节点。
- 匹配粒子把 Tween 注册在粒子 `_velocity` 对象；该对象不是 children。ParticleManager.emit 另将粒子放入全局列表。
- 没有统一注销粒子列表、事件监听、第三方创建资源；extract 只处理指定 identity 的 Tween。

这些资源通常在正常构造之后的 stop 事件才生成，**不是证据证明当前原始同步构造失败必然已经拥有它们**。它们证明子树算法无法覆盖完整匹配生命周期；扩展失败处理时必须注册 owner。有限 Tween/粒子可在正常 update 后自然结束，是暂时保留而不必然永久泄漏；若后续回调持续抛错、无限目标失去正常 stop、或系统长期暂停，则保留时间/泄漏风险增加。

scaleX/scaleY 在 E7 是对节点 scale 的代理属性：Tween target 仍是节点，因此节点 extract 可以清掉这些动画。不能仅因动画写 scale 就说本例遗漏；直接对 scale/anchor 对象注册的 Tween 才另算非树目标，本次构造未证明存在此模式。

### F6 — 中：单全局槽、多次匹配和重入（E1/E2/E4/E5）

- 常规 `_0x4d0a10` 同步重复入口有 pending 防护，正常单实例成功后 constructing 被清空；这两点有效。
- `_0x3153fe` 自身没有 pending/constructing guard，旧 active 只 cancel timers，不移除旧根、不提取旧 Tween；直接再次调用可留下 stage 旧 UI/动画。常规按钮入口是否能触发该内部调用需另证，不把条件风险写作必现。
- 构造函数直接使用时没有 caller finally 清槽，成功返回也会保留 constructing。构造/SDK/容器事件等同步重入若绕过入口，可覆盖或清除外层槽；`active || constructing` 只选一个，可能清错新实例而遗漏失败旧实例。
- pending 只保护同步扣费入口，不是跨异步匹配完成的 transaction id；roundId 也不是本次匹配 attempt id。

### F7 — 定时器覆盖有实效，但不是全资源取消（E4）

Cancel 使用 owner 严格 identity，task.version++、clearTimeout、从列表 splice；已排队旧 arm callback 先检查 version，再检查列表成员，正常环境下可屏蔽迟到调用。最终 task.callback 还必须 owner===active 且 parent===stage。这比仅 clearTimeout 强。

不覆盖正在执行的 callback、其它原生 timers、其它 owner 或 Tween 模拟延时 `_0x338c29({},...)`。cancel 若异常被吞，清理结果不透明；从 registry 删除不等于已执行 callback 的副作用回滚。

Resume 会删除不再 active/挂 stage 的 task。若构造期间发生直接 resume 重入，尚未挂载的合法 constructing task也可被丢弃，正常匹配无法继续。它是条件重入风险，非正常事件循环同步打断构造。正常 start 清 active 时通常 ready task已先从列表移除；不能说此处一定泄漏一个 ready timer。

### F8 — 广告异常和退款互相独立（E3/E4）

arena 调 `_0x248455(type)` 不传 continuation：发起后立即构造，不等待广告结束。beforeAd token暂停 timers/Tween模拟；退款不撤销 SDK 请求或 ad token。晚到 before/afterAd仍可能暂停/恢复选择页或新匹配。

- SDK 同步 throw 在包装器通常被降级捕获、continue 后仍构造；若 catch 内 `_carromAdResume` 再抛错，会传到入口 setup catch。
- 异步 afterAd/adBreakDone 内 resume/syncMute/ticker.start 抛错不被入口 catch 处理；done 标记发生在这些调用之后，失败可使 finish 重复进入。
- token 列表使 MatchBlocked 和 owner timer resume尊重其他广告及 host pause；但 finish 仍直接 ticker.start。宿主暂停/其他 token 时模拟门控尚在，不能直接断言物理已恢复；ticker/渲染启动则可能与暂停预期不一致。
- 不可为退款强行清空所有 ad tokens 或全局 start ticker，避免解开另一个暂停 owner。需要每请求 token 的异常安全释放与回调归属，而不承诺宿主 SDK支持取消广告。

### F9 — 保存不是原子扣费/退款（E1/E2）

入口 save 的异常被记录后继续构造；退款 save 异常也不撤回内存退款。`_0x3a0318` 先 `_0x9b0cd` 同步业务数据，再逐 key storage 写入，各 key 自己 catch/warn，所以外层 save catch通常感知不到单 key 写失败。它没有事务、整体成功返回或重试提交协议。

因此：内存减 fee 后加 fee，在没有其它变动及数值问题时恢复余额；不能保证落盘余额、跨 key 一致或关闭后不丢币。构造清理与保存失败都须单独报告。保留原始错误阶段而不是所有异常只用同一个 setup failed。当前只保护 save，不保护扣费前随机数等全部语句；这些语句异常是否扣费取决于执行断点，不应无条件退款。

## 5. 正常匹配副作用与最小设计建议

已核对的正常安装路径新增的只是暂存/清空引用，没有主动 extract 成功匹配树；无重入条件下不会直接改变 fee、奖池、roll/shuffle 参数。**未实际回归，不能宣称零副作用。**

风险防线：

1. extract 真实实现按严格 target identity 停止找到的第一个 Tween后 break；addTween 正常先 extract同目标，通常维持单目标单 Tween。外部直接操作公开 tweens/手工 Tween时可产生多个，此时一次提取不够。不能假设 extract 递归或一口气清所有同目标。
2. Tween.stop 只停止并 splice，不执行 onComplete；finish 则会写终值并调用完成。失败清理应 stop，不应 finish，否则可能触发 ready/start。若提前对成功树清理，同样会切断 shuffle进入对局的唯一完成链。
3. 正常 start 后根移除没有统一 dispose；有限动画/粒子可能自然结束，未 destroy本身不等于泄漏。共享 TextureCache资源不能随匹配销毁，更不能全局 Tweener.clear/ParticleManager.clear来“兜底”。
4. 在 Tweener.update中途删全局列表可能跳过本帧下一个 Tween；失败路径当前多为同步入口，但新增异步 abort时需安全迭代/延迟清理，不能误伤其他界面动画。

建议最小架构（仅设计，未实施）：

- 每次入口在任何副作用前创建局部 `attempt`，含 id、phase、root、feeCharged、refundCommitted、ownedTimers、ownedTweenTargets/handles、ownedParticles、listener disposers。资源创建即登记，不以挂载作为 ownership来源。
- `constructing → mounted → matching → started` 显式提交；所有异步回调核验 attempt id和phase。abort先使本 attempt失效，重复 abort无副作用；不得清空不属于自己的 active槽。
- 构造 factory/context接收父类/子工厂注册的 disposer；区分父类是否初始化，禁止对半初始化节点调用要求完整字段的 destroy。销毁选项按真实 PIXI 版本确认，不销毁共享纹理。
- 扣费记账与清理结果隔离：任何清理失败不跳过一次性退款提交及UI恢复尝试；把 error、cleanup errors、refund/save/UI结果分别记录。有限预算、安全快照、visited的树遍历仅为辅助，逐步异常隔离，去掉 push.apply；不能用树遍历代替资源账本。
- 对完整生命周期统一 owner dispose，在正常 start明确提交后取消不再需要的资源；不要在 shuffle完成前 stop；已合法产生的实际结算/广告奖励与入口退款分开记账。
- 保存增加可观测成功/失败与重试状态，若要持久化原子性需额外存储协议；本轮不擅自把存档改成事务或改广告顺序。

## 6. 验收条件（全部待执行，不是测试结果）

|编号|注入/回归情形|必须满足的判据|
|---|---|---|
|T1|Container.call 前、内部、返回后分别抛错|精确标明是否已扣费；已扣 fee 仅退一次；父类已注册资源可定位释放，未初始化树不导致二次异常|
|T2|startRoll后奖池 Sprite/BitmapText/最后节点抛错|本 attempt滚动无限 Tween及3000ms timer消失，旧回调不emit stop/ready；恢复选择页；其它 UI动画继续|
|T3|子工厂抛错、返回后addChild抛错，附带先注册非树 Tween|未挂载资源也释放；不把无外部引用的节点误判为永久泄漏|
|T4|奖池数据 Tween、粒子velocity Tween、ParticleManager登记后故障|目标及manager登记均清理；回调不再写旧 BitmapText/创建新Tween；不影响其它owner粒子|
|T5|null child、children getter throw、自环/祖先环、宽树、已destroy节点|有限步数终止；退款和UI恢复不被遍历失败阻断；清理错误可追踪|
|T6|extract/cancel/removeChild/destroy/disposer各自throw|剩余独立disposer仍执行，退款至多一次；pending释放；不能输出虚假的全部清理成功|
|T7|连点入口、重复abort、旧timer已排队、回调正在执行|单次扣费/退款；旧版本及attempt失效门控有效；不承诺取消已发生副作用，提交点单独核验|
|T8|连续正常匹配100次，内部直接调用与同步重入单测|常规流程无旧stage匹配节点/owner登记累积；重入拒绝或正确隔离，不清错其它attempt；强制GC后的保留链解释清楚|
|T9|无广告/有广告；before/after重复、晚到、同步SDK throw、异步resume/mute/ticker throw|正常降级仍构造；释放自己token，不解开host/另一广告暂停；不会重复ready/start或跨attempt触发UI|
|T10|扣费save、退款save、单key storage写入、数据同步各自throw|区分内存与落盘；清理不吞退款；保存失败可观测；刷新/重启后的余额按存储协议检查|
|T11|正常有fee/无fee、玩家/对手先手、教程、暂停/恢复、快慢帧|roll→stop→ready→shuffle→start完整各一次；start前不清完成链；参数、计分、输入窗口与A一致|
|T12|stop/ready/shuffle/onUpdate/实际对局初始化异步抛错|owner统一失败策略或明确提交后故障处理；不能声称入口catch自动覆盖；其它Tween不被长期阻塞|

内存验收要同时看 owner注册计数、stage节点、Tweener/ParticleManager保留链与稳定窗口，不用单次heap数字判定无泄漏。先等有限效果结束再检查；暂停导致的保留应与永久泄漏分列。将“无任何泄漏”作为结论前需要完整依赖与运行证据。

若用户后续授权代码/测试阶段：提供实际依赖/资源/SDK可控适配器，真实运行 build/test/check；最终dist桌面与手机点击、控制台、截图和中文浏览器环境的默认语言验证放 evidence。此处仅验收设计，不声称已启动浏览器、执行这些命令或做设备测量。

## 7. 真实核验记录与未知清单

### 本轮实际完成

- PASS（资料动作）：读取选定Skill入口、允许的配套资料、四份冻结知识及上述两份参考关键函数；人工核对局部变更与同步/异步状态路径。
- FAIL（静态设计判据）：异常遍历可阻断退款；完整匹配生命周期的非树目标与异步失败不能由本补丁统一覆盖。
- NEEDS_CONTEXT：运行泄漏、具体父类副作用、宿主SDK异常行为、正常匹配回归。
- npm build/test/check、Chromium、真机、截图、heap、包体/加载/内存性能：**未执行**；当前只读静态审查不以模板或计划替代执行证据。
- 产物：`/workflow/prototype.md`。只新增报告，未修改A/B、未实施建议、未生成美术、源码包或试玩ZIP。

### 未知清单

|未知项|影响|补充证据|
|---|---|---|
|PIXI Container/Sprite/BitmapText的实际版本、构造及destroy实现|父类失败副作用、底层缓存/字体/纹理释放不能保证|实际依赖源码与版本锁、资源创建保留链|
|全部调用点、SDK是否同步重入/回调次数和契约|直接重复构造与槽覆盖风险的真实可达性|完整调用图、SDK适配实现、重入故障注入|
|异常时heap与外部资源登记|暂时保留或永久泄漏未实测|受控时钟、GC后保留链、逐attempt ledger|
|存储实际后端和flush/失败反馈|原子落盘与刷新恢复不能保证|存储实现、故障注入、刷新验证|
|未执行全文自动diff|不保证无关代码均一致|若授权补测再做全文差分；本次结论限定列出的函数|
|专项Skill入口未选中|没有采用其执行卡|若后续需要专项实现/验收，由下一轮补选，不绕过本轮权限|

本次需求清晰，无需要用户裁定的重大实现取舍；没有编造阶段确认。审查交付后停留prototype，后续修复与验收需单独授权。
