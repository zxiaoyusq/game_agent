# Carrom 场馆启动异常退款审查

## 1. 范围、结论与证据等级

- 项目：7c640f0233424ee5b867187cc4b3bdad；当前仅 prototype 原型定义/静态审查阶段，attempt=1。
- 用户目标：比较两份 JS，拆分入场同步启动失败、退款、部分匹配清理、广告暂停、存档及重入边界。不是新建游戏，也不授权改玩法、换引擎或推进美术/代码/测试阶段。
- 本轮产物：`/workflow/prototype.md`。未修改参考源码，未创建游戏、试玩包或修复补丁。
- **核心结论：guard 增加了窄范围同步补偿，但不是完整事故处理。** 对广告调用或 `_0x3153fe()` 向调用栈传播的同步异常，尝试清理当前已登记匹配、将本次 fee 加回内存、保存并恢复场馆。before 在这个位置只有 finally 释放 pending，不进行上述补偿。
- **静态已确认缺口：** 构造器返回前有循环 Tween 和匹配 timer 副作用；构造失败时无法通过 activeMatch 找回半成品。已登记对象的 rollback 未清 Tween、未注销监听器、未 destroy。保存接口吞掉单键错误且不返回确认。恢复失败仅 warn。异步启动异常不在本次 catch 内。广告生命周期独立，rollback 不取消广告 token。
- **重复退款：未发现当前单次正常同步 catch 会执行两次 fee 加回的直接证据。** pending 覆盖本次同步补偿；缺少持久交易 ID 不等于已证明重复退款。异步重试、跨重启补偿的幂等安全尚未建立。

状态词口径：PASS/FAIL 用于注明的静态结构检查，不代表浏览器测试；BLOCKED 表示运行验收缺证据；NEEDS_CONTEXT 表示外部契约未定。

| 检查项 | 状态 | 含义 |
|---|---|---|
| 新增同步补偿分支存在、fee 使用本次局部值、finally 放锁 | PASS（静态） | 已读两版入口正文 |
| 构造失败资源可找回、所有动画/监听器完整清理 | FAIL（静态完整性） | 当前分支与构造副作用不匹配；实际泄漏量未测 |
| 退款持久成功可确认 | FAIL（静态完整性） | 单键失败被内部吞掉，无提交结果 |
| UI 恢复失败后有可靠兜底与可见反馈 | FAIL（静态完整性） | 仅 warn，可能留下部分 UI 状态 |
| 广告失败是否应退款、异步启动是否也应补偿 | NEEDS_CONTEXT | 当前代码行为可描述，但产品/SDK契约未确认 |
| 实际退款次数、节点/内存泄漏、暂停恢复及冷启动读回 | BLOCKED | 本轮没有故障注入或运行环境验证 |

## 2. 输入与方法依据

### 2.1 真实参考路径（相对 ref/）

- A / before：`mcp-inputs/mac-codex/2745eef73e67f3982139f1497456e7b4f85d45c03e148127675ce8bb0e96090e/arena-before-refund.js`
- B / guard：`mcp-inputs/mac-codex/309e9b1c0a3e10a44c4cc600897e02f203c40abf8a556fa059b9104b286c2dce/arena-refund-guard.js`

通过 read_reference 读取，不执行混淆代码。路径内摘要样式字符串只作为定位信息，不当作本轮计算的文件哈希。采用函数标识和片段作为检索锚点，不编造源码行号。局部对照不等于完整文件 diff，也未做完整字符串表运行解码。

主要证据索引：

| 编号 | 函数/片段 | 本轮定位 |
|---|---|---|
| E1 | `_0x4d0a10`、`_0x3153fe` | A 的读取窗口 offset=84000, limit=18000；B offset=94000, limit=9000，均为字符窗口 |
| E2 | `_0x104b9b` 实际构造函数 `_0x3875cf`、`_0x5e1e47`、startRoll | A offset=393000, limit=24000；B offset=351000, limit=60000 与 offset=411000, limit=30000 |
| E3 | `_carromMatchSchedule/Arm/CancelMatchTimers/PauseMatchTimers/ResumeMatchTimers`、`_carromAdPause/Resume` | B offset=243000, limit=24000；A offset=251000, limit=7000 可见前半 helper |
| E4 | `_0x3a0318`、`_0x9b0cd` | 两版前部读取窗口中的存档实现；函数锚点优先 |
| E5 | `_0x248455`、pause/resume、更新函数 | B 前部广告与宿主函数窗口；更新/helper 见 E3 |
| E6 | `_0x48e98f`、场馆 UI `_0x22a07c`、卡片 `_0x40d778` | 恢复函数在前部窗口；UI 类 B offset=411000, limit=30000 |

已读取手选技能 `game-reverse-engineering/SKILL.md` 及其 execution-protocol、全局规则和未知清单配套正文；采用证据分级、owner/提交边界、未知清单方法。额外模块 `game-reverse-engineering/modules/gameplay-logic-reverse/SKILL.md` 的入口调用被工具拒绝（本轮未选中），未声称采用其正文，不绕过限制。本轮不更新 Skill。

已实际读取全部冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。框架配置是工作流背景，不改变参考源码身份：参考中实际可见 PIXI、planck、Howler、GameSnacks；未核验版本，不称原生 Canvas 2D 实现或 Cocos 工程。

### 2.2 参考取舍与设计决策

以 A 为局部控制流基线，以 B 为被审查变更；保留现有业务流程，审查财政补偿和资源所有权，而非重设计物理玩法。把同步 setup、异步匹配演出、实际对局初始化、存档写入、广告暂停划为不同提交边界。下面状态模型和修复方向是建议，不是已实现/已确认方案。

## 3. 入场循环、状态与界面契约

### 3.1 当前可见流程

场馆选择界面 `on("select", _0x4d0a10)` → 参数/余额校验 → pending=true → 写场馆与随机先手 → 扣费并尝试保存 → 请求广告（不等待终态）→ 隐藏选择/商店/大厅 → 构造匹配演出 → activeMatch=对象 → 坐标/挂载/两个事件注册 → 同步函数返回、pending=false → 后续 timer/Tween 触发 ready 与先手演出 → 启动事件清 active、移除匹配 → `_0x1260d2()` 初始化真实对局。

B 在“请求广告 → 同步匹配 setup”之间新增内层 catch；命中后清 active、尝试取消其匹配 timer、尝试 detach、内存加回 fee、尝试保存、尝试恢复场馆，最后外层 finally 释放 pending。

建议显式状态：`arenaReady → entryPending → matchSetup → matching → gameInitializing → playing`；失败补偿应区分 `rollbackPending → refundPersistPending → arenaReady/recoveryRequired`，不能只用 activeMatch=null 表达所有失败终态。广告状态是独立 `requested/paused/finished`，不可与财政交易状态合并。

### 3.2 费用、成功失败与输入窗口

- 源码 fee（id 0–4）：0、50、200、750、5000；当前入口要求 id 为合法整数、配置存在，fee/余额有限、fee 非负且余额足够。费用不是任意按品类模板设定。
- 本次同步失败的财政不变量：无其他收支时，余额 B → B−F → B；存在其他合法收支 Δ 时应回到 B+Δ，而非覆写钱包快照。加回局部 fee 有利于保留 Δ，但不足以证明持久一致。
- 同步 setup 返回不等于对局成功启动。建议成功提交点放在真实对局完成初始化、可输入且资源归属明确之后；当前 patch 没有这样的交易提交标志。
- 输入窗口：当前 pending/activeMatch/选择界面 visible 三种检查共同限制入场；pending 只覆盖一个同步调用栈，finally 后释放。active 为空但 UI 未恢复时不能判定可重试。
- 当前入口不直接检查 hostPaused/adTokens 或 UI 总体 enable 状态。UI 正常点击是否可达与直接事件/程序调用必须分开验证。
- 已读场馆 UI：`setCoins()` 按余额与 fee 重设各付费选择按钮 enable；`updateStates()` 为空。场馆总体 `setEnable()` 管返回/商店/教程/左右箭头，恢复函数没有显式调用它。因此不能声称“没 setEnable(true) 所以所有按钮必卡死”，也不能声称所有控件已恢复。
- 未发现本场馆另有已证实的独立 unlocked 契约；商店装备 locked/unlocked 不应误套到场馆。

### 3.3 布局、文案与物理验收边界

参考场馆布局有顶部余额/返回、横向规则页与场馆卡片、左右箭头、底部商店与教程；匹配演出呈现场馆背景、玩家/对手、奖池与先手演出。本轮不生成视觉资源或调整布局。

玩家语言默认 English；如后续实现错误反馈，可用 `Unable to start match. Please try again.`、`Refund pending. Please do not retry yet.`、`Return to arenas`。这些是建议文案，当前源码只新增中文报告所引用的英文 console.warn，不是玩家可见提示。当前没有可核验 HTML 页，不声称 lang=en 或中文浏览器语言验收通过。

物理品类契约按本任务收敛：已读更新代码有 planck step `1/60` 秒、迭代参数 `10,10` 及 clearForces，累积器按逻辑步更新，host/ad blocked 时跳过更新。保留既有碰撞、进袋、回合与计分，不对其完整正确性作本轮结论。入场失败不应创建有效对局、记分或结算奖池；奖池演出数值不等于钱包入账。财政验收容许误差为 **0 coins、0 次额外扣/退费**；节点、timer、Tween、listener 验收以 owner 残留数为 0，不拿 heap 抖动等同泄漏。暂停期间匹配 timer 的 remaining 不应消耗；真实浏览器调度允许延迟但不允许暂停期启动，时间容差须由目标环境实测约定，不伪造物理轨迹或帧率误差指标。

## 4. 按异常点审查

以下全部为静态事实或条件推断，未注入执行。

| 异常点 | B 的捕获/补偿 | 副作用及残留风险 | A 对照/证据 |
|---|---|---|---|
| 扣费前场馆赋值/随机先手抛错 | 只 finally 放锁，未进新增 catch | 尚未扣费，不应退费；场馆全局可能已变 | 两版共同 E1 |
| 扣费保存抛错 | 入口保存 catch warn，继续广告/setup | 存档失败不自动触发退款；存档镜像可能已改变 | 两版共同 E1/E4 |
| ad SDK 原始同步异常，被 `_0x248455` 内部处理 | 通常不逃逸，不命中新退款 catch，仍 setup | “广告不可用”不等于“入场失败”；不能称所有 ad throw 都退款 | 两版广告包装 E5 |
| ad 包装内清理再次抛出，逃逸入口 | 内层 catch 可补偿，setup 尚未调用 | 可能已加 pause token 或改变静音/ticker，匹配清理不撤销广告请求 | B E1/E3/E5；A 不退款 |
| setup 前清旧 timer、discard penalty/queen 或隐藏 UI 抛错 | 同步 catch 退款、尝试恢复 | 此时可能没有新对象；旧资源清理可只完成部分，恢复再次 discard 也可能失败 | E1/E6 |
| 构造器分配任何资源前抛错 | 同步 catch，active 通常仍 null | 可恢复钱包/UI；无新对象可清，但需证实具体抛错位置 | E1/E2 |
| 构造器已建子节点/内部 stop listener 后抛错 | 同步 catch，但 active 尚未赋值 | 半成品无法由入口取得；纯内部循环引用不单独证明 GC 泄漏，需看外部引用 | E2 |
| 构造器 startRoll 后、余下 sprite/BitmapText 等创建抛错 | 同步 catch 退款，但 failedMatch=null | startRoll 已启动子对象循环 Tween（loop=-1）并 schedule owner=this 的 3000ms task；入口漏清这些实际登记的副作用 | 两版 E2；B 未补上构造所有权 |
| new 成功后 x/y setter 或挂载前抛错 | active 已登记；尝试 cancel timer+detach | parent 可为空；循环 Tween、子 listener 仍未 extract/off/destroy | B E1/E2/E3；A 保留 active 且不退款 |
| addChild 部分挂载后抛错 | 同上，按实际 parent 尝试移除 | detach 若失败，节点可能遮住恢复场馆；active 已清空，丢失主查找指针 | E1 |
| 第一次 on 注册前/后抛错 | 同步 catch；已知对象清 timer/detach | 已注册回调可能保留；guard 阻止旧对象执行不等于释放回调引用 | E1/E2 |
| 第二次 on 注册前/后抛错 | 同上，第一 listener 已存在，第二可能部分注册 | 不执行 off，不清动画；后续旧演出仍可能有副作用 | E1/E2 |
| cancelMatchTimers 抛错 | 吞错后继续 detach/退款/恢复 | helper 按 owner 循环，部分任务可能未删；无重试/残留报告 | E1/E3 |
| detach 抛错 | 吞错后继续退款/恢复 | stage 残留可遮 UI，active=null 不等于节点已移除 | E1 |
| 退款保存失败 | 内存 fee 已加回；外层保存 catch warn | 单键失败通常由保存函数内部吞掉，入口甚至不会打印 refund save failed；重启可能仍见扣费余额 | E1/E4 |
| 场馆恢复早期 discard 抛错 | catch warn；finally 放锁 | 可能保持多界面 invisible；返回点、补偿状态、用户提示均没有兜底 | E1/E6 |
| 恢复 visibility/setCoins/其他 UI 更新中途抛错 | 同上 | 可出现“场馆可见但余额旧、选择 enable 未更新”或导航未恢复；并非全部界面必然不可用 | E6 |
| 保存/SDK/setup/清理/恢复过程中同步重入同入口 | pending=true 时返回 | 不再次扣费，故同一普通调用栈无直接双退证据；锁不覆盖其他钱包写者 | E1 |
| finally 后再次合法点击，前次已失败并恢复 | 可开始新入场交易 | 再次扣 F/退 F 本身不是重复退款；必须按请求逐次对账 | E1 |
| 免费场馆 F=0 | 仍走保存/广告/setup/清理/恢复 | 余额不变，但泄漏、暂停、卡界面风险同样存在 | E1/E2 |
| 匹配 timer/Tween、ready/先手演出后续抛错 | 通常不在已返回的入场 catch 内 | 已扣费且无该分支退款；无“初始化失败”统一终态 | E2/E3 |
| 启动 listener removeChild 或 `_0x1260d2` 抛错 | 典型延迟事件路径不覆盖 | listener 先清 active，再 remove/init，之后半初始化物理/显示资源不能依赖 active 找回 | E1 |
| 非标准同步重入的启动事件，在 setup 栈内即触发后又抛错 | 若传播到 setup 栈可命中 catch | active 可能已清、甚至游戏已部分启动；财政退款和游戏资源未同步撤销。标准 API 是否允许需核验，不当作自然重现 | E1 + 外部事件语义未知 |

### 4.1 Timer 清理与 Tween 清理不是同一件事

`_carromMatchSchedule` 先把 task 放进全局数组，再 arm；arm 内 setTimeout 若抛错，task 已登记。正常触发时先检查 version/blocked，再移出数组，仅当 owner===active 且 parent===stage 时调用 callback。cancel 按 owner 增 version、clearTimeout、splice。暂停保存 remaining，恢复丢弃不再 active/挂载的 owner。

因此正常 timer guard 可阻止构造失败对象的任务启动真实对局；在未暂停的正常到期情况下还会删掉 task。这**不保证即时释放**，更不清 `_0x5e1e47.roll()` 的循环 Tween。暂停状态的无 handle task 可等到下次 resume 才被移出；clearTimeout/循环清理抛错则另有部分完成风险。B 的 catch 未调用 Tweener.extract，也没有收集子节点动画 owner；即使完全 cancel 了匹配 timer，仍不能判资源清理完整。已读匹配类没有专属 dispose/kill 实现可由此入口调用；不能假定 parent.removeChild 具有递归销毁或清全局 Tween 的语义。

### 4.2 广告暂停与终态窗口

`_0x248455(type, callback)` 使用 token、adPaused、done；beforeAd 调 pause token、mute、stop ticker；adViewed/adDismissed/afterAd 当前为空；adBreakDone 执行 resume token、syncMute、ticker.start，再 continue() 提交 done。入场没有传 callback，广告请求发出后立即 setup，并不等待播放结束。

- pause 把 token 加入数组后暂停匹配 timers；blocked 判定为 hostPaused 或 adTokens 非空。期间新 schedule 登记但不 arm。因此广告先暂停再构造时，匹配 task 不应消耗 remaining。
- setup 失败后的 rollback 不清 token、不取消请求。后续广告完成可以恢复共享 ticker/静音；不能说退款后广告不会再回调。
- token 非空且永无 adBreakDone 时，更新/匹配 timers 可一直 blocked；无已见 watchdog。退款不自动解决此卡死。
- resume 先 splice token，再 syncMute，再在无其他暂停时恢复 timers；若 syncMute 抛错，token 已删而 task 仍暂停。重试同 token 时 index<0 直接返回，不能保证补做 timer resume。ad 包装的恢复操作发生在 done=true 之前，重复终态还可能重复触发部分共享副作用；continue 的去重不保护所有清理步骤。
- hostPaused 与多个 ad token 的联合判定能防止一个广告结束就恢复匹配 timers，但 ticker.start 不等于物理更新已放行。需同时检查真实输入、剩余 timer、静音、ticker 和所有 token，不能只查一个布尔值。
- pause/resume 与界面总体 disable/overlay 不是同一所有权；入口不直接检查 blocked，程序性入场仍需单独测。

## 5. 持久化、重复退款与信息损失

`_0x3a0318()` 先 `_0x9b0cd()` 把运行时钱包/教程/装备等复制到存档镜像，再逐键 JSON.stringify + GameSnacks 写入；逐键 try 内失败只 warn，无返回结果。镜像更新在逐键 try 外，若这里抛错由入口捕获，但已完成的副作用不撤销。

假设起始内存与持久 coins 都为 B，无其他收支，setup 同步失败；D=扣费 coins 写成功，R=退款 coins 写成功：

| D | R | 当前内存 | 最终持久 coins（条件推断） | 风险 |
|---|---|---|---|---|
| 成功 | 成功 | B | B | 此窄组合可一致，但不是实测 |
| 成功 | 失败 | B | B−F | UI 看似已退，重启仍损失 F |
| 失败 | 成功 | B | B | 失败扣费未持久；退款保存写 B，不等于持久多发 F |
| 失败 | 失败 | B | 原 B | 本例 coins 恰一致，仍无可靠确认，其他键可混合 |

还需覆盖扣费前本就未持久的其他 Δ、延迟 flush 乱序、关闭页发生在 D/R 之间、多键部分写入、JSON.stringify 失败以及 storage API 只是缓存接受的情况。`window.CarromLocalSave.flush()` 在 resume 有调用尝试，但实现未提供，不能假定它可靠持久、顺序正确或会补偿交易。

当前加回 fee 是 delta，不是把 wallet 重置到旧 snapshot；这是局部优点。新增 catch 没有 transactionId、debited/refunded/committed 状态或跨重启 journal，也不保留原始 exception/异常阶段，清理失败多数静默吞掉。仅根据这些缺口不能断言发生了双退；未来若增加异步失败消费者/重试退款/重启恢复，必须证明每个 transaction 的净退款不超过其实际扣费。保存重试应写入已对账状态，不能再执行一次 `wallet += fee`。

## 6. 修复建议（未实施、未确认）

优先顺序：

1. **构造与激活分离。** 构造阶段只建局部资源；完成后登记 owner、挂载、注册监听器，再显式 startRoll。或由 factory 在内部捕获并对半成品 dispose，资源一创建就登记。仅在 new 返回后登记 active 无法补救构造中途抛错。
2. **统一幂等 dispose。** 按 owner 收集 timer、子节点/匿名目标 Tween、事件、粒子；逐项清理，记录失败并可重试，不销毁共享纹理缓存。清 active 前保留 recovery owner，不能因 detach 失败丢掉追踪对象。identity guard 仍保留，但不代替释放。
3. **财政交易与保存结果显式化。** 每次 entry 独立 ID 与状态；一次 debit、一次 refund、明确 gameInitialized 提交点。保存返回每键结果或原子记录确认，失败进入 refundPersistPending；恢复时只重试落盘、不重复加币。记录原始异常与失败阶段。
4. **恢复 UI 有兜底。** 将余额/按钮/导航/遮罩/输入状态分项检查；恢复失败保留 recoveryRequired，提供可见英文反馈和安全返回入口。不能简单无条件 setEnable(true) 越过合法 modal/host/ad 暂停。
5. **明确广告与异步失败策略。** 广告是否必须完成才进入匹配、不可用是否取消入场、匹配演出/真实对局初始化失败是否退款，应由产品与 SDK 契约决定。本轮不擅自扩大同步 patch 到全异步补偿。广告终态清理设计为可重入且逐项完成，避免 token 已删就跳过未完成恢复；watchdog 不能擅自打断仍播放中的真实广告。

这些是下游改动方向；当前静态审查可在外部契约未齐时完成，不需要为普通审查细节暂停询问。若后续实施第 5 项，存在重大范围取舍，届时须 request_user_input 获取真实选择，不能把本报告当作确认。

## 7. 故障注入与验收矩阵

**本节是验收定义，全部未执行，运行状态均 BLOCKED。不是测试结果，也不是已编写可运行脚本。** 后续应从真实两版源码建立最小 SDK/storage/PIXI/Tweener 可控替身进行单位级故障注入，并用完整真实页面验证自然事件、桌面/手机视口输入与截图；替身结果不能替代真实 SDK/宿主。

每例记录：entryId、初始/扣费/退费内存余额、coins 写调用与结果、冷启动读回、pending/active、stage 节点/遮罩、owner timers/Tweens/listeners/particles、ad token、hostPaused、ticker、mute、输入可用性、原始异常。每次故障只注入一次，失败次数与交易次数分别计数。

| 用例组 | 必测注入/操作 | 验收目标 |
|---|---|---|
| T01 参数与正常入场 | 非整数/越界/余额不足/非法 fee；正常付费与免费 | 无效输入无扣款；合法一次扣 F；免费净额 0 |
| T02 广告同步 | SDK 立即 throw 被内部吞；resume 再 throw 逃逸 | 区分仍匹配与入场补偿，不能统称广告失败都退 |
| T03 构造资源 | 第一个分配前、内部 listener 后、roll/schedule 后、后续 BitmapText/fromFrame 失败 | 前两版对照；回滚应释放每个已分配 owner，不只查 active |
| T04 挂载与注册 | x/y、addChild 前/部分完成后、第一次/第二次 on 前后 | fee 不多退；无残留遮挡；callback/Tween/listener 无旧 owner |
| T05 清理失败 | cancel 第一个/后续 task 失败；removeChild 失败；多次失败循环 | 完整性与重试可观测；不能用 guard 未启动代替无泄漏 |
| T06 保存组合 | D/R 四组合；镜像更新与 stringify 失败；多键部分失败；延迟 flush/冷启动 | 表中结果真实读回；所有余额误差 0；无额外加币 |
| T07 UI 恢复 | 两个 discard、visibility、setCoins、模式/奖励更新分别失败 | 状态明确、余额一致、可安全返回；导航/选择/遮罩分别核验 |
| T08 同步重入 | 在保存、ad、构造、清理、退款保存、恢复中调用 select | pending 期间无第二次扣费/构造/退款；finally 后新请求独立对账 |
| T09 重复/迟到事件 | ready/start 重复、旧 match 事件、active 已清后的迟到回调 | 无旧对局启动/计分，无过期 owner 副作用，无重复退款 |
| T10 异步失败 | timer stop、ready listener、先手 Tween 回调、removeChild、实际对局初始化抛错 | 明确当前 catch 不覆盖；后续是否补偿按确认契约，不能伪报本补丁通过 |
| T11 暂停交错 | beforeAd 同步/异步；构造中广告 pause；setup 失败后广告终态；无终态；两 token；host pause/resume 嵌套 | blocked 期间不消耗匹配时间、不启动物理局；剩余有效暂停未退出不放行 |
| T12 终态清理异常 | token splice 后 syncMute 失败、resume timers 失败、ticker.start 失败、重复 adBreakDone | 未完成恢复可重试；done 与逐项完成一致，不因 token 已删丢恢复 |
| T13 重开与资源量 | 付费/免费各反复失败/成功/回大厅；慢帧/快帧固定输入 | owner 残留应归零；正常玩法 step/碰撞/计分无回归；heap 需实测趋势而非单点推断 |
| T14 浏览器与语言 | 桌面/手机真实点击；中文 locale；页面/console/pageerror/截图 | 若产出英文 Web 版本则 lang=en、主要文案英文，默认不随浏览器切中文 |

后续代码/测试阶段若授权实施，必须在最后源码/资源修改后真实执行 `npm run build`、`npm test`、`npm run check`；check 访问最终 dist、自动启停静态服务器并输出 evidence。当前未有可构建页面，不能为完成静态报告伪造三条通过日志或开发新游戏替代参考验收。

## 8. 本轮真实验证与限制、未知清单

### 8.1 已完成的核查

- 本 attempt 通过 read_skill/read_skill_resource/read_game_knowledge 获取方法正文与全部选定冻结资料。
- 通过 read_reference 实际读取两版入口、guard helper 与匹配/UI 类，并局部对照 before 的入口、匹配类及部分 helper。
- 核查 catch 覆盖位置、new 返回前后 active 所有权、fee delta、timer 数组/版本机制、loop Tween 副作用、保存吞错与广告终态顺序。
- 报告文件写入后另行回读核验。没有运行游戏或故障注入。

### 8.2 未执行项目

- 未执行 npm run build、npm test、npm run check；原型静态审查不冒充实现/测试阶段。
- 未启动浏览器、Chromium、真实 SDK/宿主或真机；未产出截图、内存曲线、包体/加载测量。
- 未计算两份参考当前 SHA256、未全文件 diff、未执行完整解混淆；不保证本轮观察到的入口改动是全文件唯一差异。
- 未部署/生成美术/安装引擎/迁移框架/编写修复代码；本轮不发布试玩 ZIP。

### 8.3 未知清单

| 未知项 | 影响 | 下一份必要证据 |
|---|---|---|
| 完整 HTML、依赖与资源/打包壳、PIXI/Tweener 实际版本 | 无法跑自然入场、确认 removeChild/动画替换/GC语义 | 原项目可运行包及依赖锁定/资源 |
| GameSnacks 广告同步/异步回调、终态保障与取消契约 | 决定广告 throw/迟到/无终态的实际可达性 | SDK 文档与真实宿主回调轨迹 |
| GameSnacks storage durable 语义、CarromLocalSave.flush 实现 | 无法保证冷启动退款与写序 | 保存适配实现、故障日志、重启读回 |
| 场馆禁用/模态遮罩上层调用契约 | visible 不等于允许重试 | 真实选择按钮/导航/overlay 的自然输入复测 |
| 全文件有效差异及其他退款消费者 | 不能排除别处业务补偿，也不能断言重复退款 | 全量静态 diff、所有 wallet 加减与调用图 |
| 真实对局半初始化资源与后续失败策略 | 当前同步补偿不覆盖完整事故处理 | `_0x1260d2` 各资源 owner 注入与产品确认 |
| 目标设备快慢帧、timer容差与长期资源趋势 | 只能定义不变量，不能声称物理/性能已验收 | 目标设备固定输入与生命周期测量 |

审查收口：同步补偿有实质局部收益，但资源完整清理、持久退款确认、恢复兜底及异步/广告终态均未达到完整事故处理证明。保持 prototype 阶段，不自行确认或推进下一阶段。
