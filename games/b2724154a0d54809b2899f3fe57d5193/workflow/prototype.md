# Carrom 红棋入袋动画身份保护只读复核

## 结论与范围

现版验收状态：NEEDS_CONTEXT。操作者描述的新增身份检查，在 pending 被清空或替换后、active 与 round 仍合法的情况下，可以阻止旧红棋完成回调继续接管 HUD。它不检查 turn，因此 pending 仍为同一 sprite 时，单纯跨 turn 不会被该新增条件误阻。此结论是对所述条件的静态推理，不是现版代码或运行验收结论。

附件是旧 dd8b7974，不是当前 game.js。本次仅读取参考文本并写此报告；没有修改游戏源码、资源、构建或发布文件，没有执行构建、单测、浏览器或受控样本。没有独立核算现版 SHA256。当前阶段按用户要求收敛为只读审查，不设计新玩法、不迁移 Canvas 框架、不推进美术、代码或测试阶段。

## 证据与定位

E-01：实际读取旧源码 ref/mcp-inputs/mac-codex/dd8b79747ae3b111ad0a83ec8088b69b7632ec9f122e685b76601e731d52ffe8/Carrom_current_dd8b7974.js，字符范围 [0,288000)，以下定位使用函数名与字面片段，不编造行号或声称全文搜索完成。路径中的旧版标识不作为本次独立哈希计算结果。

E-02：操作者陈述现版 game.js SHA256 为 1ebfc85e4d69a64bbe67b3e0e7877dbfb0f04c6466493bc0b033b3249c514a93；四袋第一段及第二段回调在既有 active/round 检查之后新增 `if (_carromPendingQueenPocket !== _0x91f24c) return;`。这些内容未由现版正文或差异文件核对。

E-03：操作者称四袋×双方×两个阶段，以及正常覆盖、返场等受控样本通过。未提供本次可读取的脚本、断言、调度轨迹或结果文件，故仅登记为操作者陈述，不能写成独立测试 PASS。

E-04：已读取四份冻结资料 genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md；已读取所选 game-reverse-engineering/SKILL.md 及 execution-protocol、global-rules、unknowns-ledger-template。玩法模块 modules/gameplay-logic-reverse/SKILL.md 被工具以未选入口拒绝，未读取成功，也未绕过限制。使用的技能方法为版本分离、真实 owner/提交边界取证及未知清单。

## 旧源码中的引用与所有权

| 位置 | 已见事实 | 含义 |
|---|---|---|
| 状态声明 | `_carromPendingQueenPocket = null`，另有 `_0x404020`、round、turn | pending 与 HUD/返场引用不是同一职责 |
| `_0x49d791` 四袋红棋分支 | 红棋离开物理世界，从 `_0x3231b3` 移除，pending 赋为该 sprite；Freestyle 还将同一对象推入 `_0x31089b` | pending 与结算队列可以同时持有同一对象，并非复制件 |
| 第一段完成 | 仅 active/round 检查；Freestyle 分支为空，其他模式启动飞往当前双方 HUD 的第二段 | Freestyle 没有该红棋的第二段 HUD 飞行动画 |
| 第二段完成 | 仅条件清空 pending，但无条件 `_0x404020 = sprite` 并更新勾选 HUD | 旧版 pending 已变更仍可能被旧回调重新接管 |
| Carrom `_0xbdafb3` 延迟决策 | 满足 mode=1、待覆盖且不续杆、无 `_0x404020` 而有 pending 时，extract pending，赋给 `_0x404020`，清空 pending | 明确、合法的动画到返场 owner 转移 |
| `_0x52e61d` | 捕获 `_0x404020`，返场完成创建新的物理红棋，加入 `_0x3231b3`，移除旧表现 sprite，清空 `_0x404020`，再通知推进 turn | 返回棋盘的是新对象；旧入袋回调不应重新占用旧表现对象 |
| `_carromDiscardPendingQueenPocket` | 先置 pending=null，再 extract，再移除父节点 | 是取消与清理，不是正常完成；主菜单、选桌、商店、匹配、重开等已见入口调用它 |
| `_0x5480e3` | 丢弃 pending，增加 round，并清理 `_0x404020` 与棋盘队列 | 新局边界有独立生命周期隔离 |

上述是已读取范围内的赋值与清除位置，不声称覆盖附件未读取尾部或现版所有写入。

## 两种模式的合法时序

### Carrom

正常链为棋盘红棋 → pending 入袋第一段 → pending 飞往 HUD 第二段 → pending=null、`_0x404020=sprite` → 覆盖状态展示或返场。普通棋入袋会清除 `_0x4268e2`，并用 `_carromQueenClearedThisShot` 保留同杆覆盖痕迹；犯规结算可重新标记需返场。第二段 HUD 纹理还会读取 mode=1 且 `_0x4268e2` 已清除的状态，以显示 filled。普通覆盖只改变覆盖标志，本次已见分支并不清空 pending，因此新增身份条件本身不应拦截该正常路径。

若结算赶在第二段结束前要求返场，结算把 pending 转交 `_0x404020` 并清空 pending。此后旧入袋回调退出是正确行为，不应为完成旧 HUD 动画而恢复 pending。返场完成再推进 turn 的路径也是有意安排。

### Freestyle

红棋同时由 pending 与 `_0x31089b` 引用。物理停止后，`_0xbdafb3` 拷贝并消费队列：无犯规时红棋分数在结算同步预记，飞分文字仅表现；犯规时对队列中的原 sprite 启动返场，完成后新建物理对象。随后强制完成器会在决策前补交尚未完成的返场或普通计分，`freestyleQueen` 的实际政策来自未提供的外部 CarromDiscRules。`_carromReturnFreestyleQueen` 则直接创建新的棋盘红棋并撤销对应分数。

关键边界：已见 Freestyle 消费队列、移除原 sprite、返场及重新建棋代码都没有同步清空 `_carromPendingQueenPocket`。第一段 Freestyle 回调也是空分支。因此该指针可能继续指向已离开父节点的旧对象；身份仍相等并不证明入袋动画还拥有它。不能将 Carrom 的 pending→HUD 转移语义直接套给 Freestyle。

## 回调先后、重入与队列

1. 每个 `_0x49d791` 逻辑步先执行 Tweener 更新，再处理活动棋盘与入袋检测，最后调用物理 step(1/60,10,10)。入袋动画目标通常在该步 Tween 更新之后才创建。定时 `_0x338c29` 也使用 Tweener，毫秒换算为 60Hz tick，且只自带 active/round 检查。不能由登记顺序自行推定同 tick 中完成回调的实际遍历顺序。
2. `_0xbdafb3` 用 expectedTurn 与 settledTurn 防止同 turn 重复进入结算；多个计分/返场完成器有局部 finished 标志，并支持延迟决策强制调用。但旧四袋第一段、第二段没有相同的局部幂等标志。
3. 新条件可使首次正常第二段完成清空 pending 后的重复第二段调用退出；第一段重复调用时若 pending 仍相等，仍可能登记多个第二段。该风险是需注入重复回调验证的反例，不是已证实自然运行必发。
4. `_0x253500(array,sprite,true)` 在数组中找到对象时只 splice 并立即返回，不取消 Tween、不销毁；所以队列取出不等于动画交权。若对象不在数组中，即便传 true，仍会落入 kill/extract/destroy 路径。需要区分正常一次消费与重复消费反例。
5. Tween 实现不在本次已读证据内。addTween 是否覆盖同目标旧任务、extract 是否移除正在遍历的完成项、回调是否可重入，均不能假定。新增 onComplete 条件也不会自动阻止 Tween 在回调前对坐标、缩放、alpha 的写入。

## 新增检查的收益与可接受边界

在 active=true、round 不变、pending 已为空或另一个对象时，条件直接 return，既不写 HUD，也不在这个新增分支移除对象；这符合已由返场或其他 owner 接管时保留其对象的目标。第一段检查可避免新建错误第二段；第二段检查可避免过期 HUD 提交。

但条件位于既有 active/round 检查之后，因此 inactive 或 round 不符时，既有分支仍可能移除捕获对象。不能把“身份不符不移除”扩大为所有旧回调分支都不移除。

也不能把“允许跨 turn”扩大为目的 HUD 必然正确：第一段完成读取实时 `_0x209883` 选择双方 HUD；若 turn 在第一段完成前改变，pending 仍相同，新条件放行，旧动画可能飞向新 actor 的 HUD。若第二段已经创建，目标坐标已选定，跨 turn 则不等同于前述风险。正常流程是否能自然产生第一段跨 turn，尚无运行证据。

## 可能误阻与反例矩阵（均未执行）

| 编号 | 调度或反例 | 应有结果与判定 |
|---|---|---|
| C1 | pending=S，round/active 合法，仅 turn 改变，然后调用任一完成回调 | 新身份条件应放行；第一段须另查 actor 归属，不能只断言回调完成 |
| C2 | Carrom 在第一段结束前或第二段中由结算接管 S：extract、HUD=S、pending=null，再送达旧完成回调 | 旧完成回调应退出，HUD/返场对象保留；这是有意阻止，不是误阻 |
| C3 | 正常同杆覆盖先发生，pending 仍 S，再完成第二段 | 应显示 covered，不应丢失 HUD；覆盖标志清除不等于 pending 身份失效 |
| C4 | 其他现版路径为正常计分/覆盖提前清空 pending，却没有接管或补交 HUD | 新条件会使合法第二段静默退出，造成误阻；旧已读代码未证明存在该写入，需现版所有写入核对 |
| C5 | 已返场新红棋再次入袋，pending=T，旧 S 的第一段/第二段晚到 | 应退出且不改 T 的 HUD、不移除 T 或返场 S；四袋及双方均需验证 |
| C6 | 同一 sprite S 被复用并再次赋 pending=S，旧 S 的回调晚到（ABA） | 对象身份检查会放行，不能区分两次入袋；已见返场通常新建对象，未证明正常路径存在同对象复用 |
| C7 | Freestyle 结算无犯规移除 S 或犯规返场接管 S，但 pending 仍 S，之后旧第一段晚到 | 新条件仍放行；Freestyle 空分支暂不写 HUD，但不能据此证明 Tween 坐标写入及生命周期安全 |
| C8 | 第一段回调重复调用，pending=S；第二段回调重复调用 | 前者可能重复登记第二段，后者首次清空 pending 后应退出；检验是否存在重复提交/悬挂 Tween |
| C9 | extract 发生在 Tweener 同一轮更新中，旧任务已进入完成队列 | 身份失效回调不应提交；还须证明取消后没有旧插值覆盖返场坐标 |
| C10 | active=false 或 round 改变，pending 指向被其他 owner 复用的同一 S | 既有 cleanup 先执行，新增条件不能保护该场景；需约束跨局复用或核对现版生命周期 |
| C11 | 两个异常红棋或重复入袋让 S 被 T 覆盖，但 S 没有接管者/清理者 | S 的正常回调被阻止后可能悬挂；应验证唯一棋盘红棋不变量及替换 owner 的清理责任 |
| C12 | 队列重复消费或回调强制完成与自然完成交错 | 每颗计分、返场最多一次，旧对象从队列/父节点/Tween 的清理应一致；不能只看 HUD 最终值 |

建议证据矩阵保留四袋×双方，但必须按模式与实际存在阶段区分：Carrom 两段；Freestyle 第一段与结算/返场，不能将不存在的 Freestyle 红棋第二段计为覆盖。每例记录 round、turn、actor、sprite ID、pending ID、HUD ID、队列成员、父节点、Tween 事件及创建/移除次数。

## 物理、输入、计分与界面审查边界

本报告不改变既有规则。旧代码可见固定物理步长 1/60 秒，速度与碰撞由 planck/box2d 负责；ticker 累加器 `while(accumulator > 1)` 执行逻辑步，已见实现无显式补步上限。入袋为中心距离袋点 <=20 的几何触发，不能与刚体接触事件混称。输入在玩家合法回合且可操作时开始，力度 >=0.25 才发射；动画结果跨 turn 的合法性与玩家输入窗口应分开判断。

Freestyle 可见红棋/两色分值数组 [50,20,10]，目标分数变量为160；红棋是否可结束由外部 freestyleQueen 决策配合状态决定。Carrom 胜负依赖外部 hasWon 和棋盘红棋数量，不能据本附件补造完整胜负规则。既有布局为棋盘、双方 HUD 与覆盖勾选标志，本次只审核旧动画是否错误占用这些表现位置，不制作界面或语言资源。

身份、计分、重复返场与对象数量的可接受误差为零次错误提交；物理轨迹和视觉坐标容差未被本次任务定义或实测，不虚设像素阈值。此次成功条件是报告可追溯、版本分离、明确合法交权及反例；现版安全验收需要正文/差异与独立运行证据，当前未满足。

## 未知清单

| 编号 | 未知项 | 还缺什么 | 当前证据 | 状态 |
|---|---|---|---|---|
| U-01 | 现版确实仅作所述回调修改且覆盖全部分支 | 对应哈希的 game.js 或完整差异及所有 pending 写入 | E-02 | 未闭合 |
| U-02 | 所称受控样本断言与调度覆盖 | 原脚本、逐例结果和事件轨迹 | E-03 | 未闭合 |
| U-03 | Tween 对覆盖、取消、遍历与重入的具体契约 | 实际加载的 Tweener 实现及目标版本运行轨迹 | E-01 调用点 | 未闭合 |
| U-04 | Freestyle 红棋完整政策与队列交权 | 实际 CarromDiscRules 实现，尤其 freestyleQueen | E-01 外部调用 | 未闭合 |
| U-05 | 附件尾部及现版是否存在其他 pending 写入/对象复用 | 针对实际完整版本的引用索引 | E-01 已读字符范围 | 未闭合 |
| U-06 | 第一段自然跨 turn 是否可达及 actor 是否正确 | 固定输入和长短帧调度下的运行事件轨迹 | E-01 实时 actor 读取；E-03 概括陈述 | 未闭合 |

## 实际验证与产物

已完成：参考文本静态读取与人工控制流推理。未执行：npm run build、npm test、npm run check、运行时注入、截图或真机测试。以上矩阵为待验证条件，不是执行结果。产物仅 /workflow/prototype.md。结论保持 NEEDS_CONTEXT：新增检查有针对性的防护价值，但旧证据与操作者摘要不足以宣称现版所有正常路径不受影响或同 sprite 所有权问题全部解决。
