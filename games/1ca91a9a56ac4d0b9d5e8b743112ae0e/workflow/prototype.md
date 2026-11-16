# Carrom 超时结算归属与生命周期只读审查

## 范围与结论

本轮仅作原型阶段的静态审查，唯一产物为 /workflow/prototype.md；不修改游戏、资源、测试或构建文件，不推进后续阶段。

结论：ticket 作为超时结算的唯一入口具有合理的归属隔离设计，但所述方案不能证明活性闭合。尤其是 armed 仍由可取消、可被活跃状态过滤的 Tweener 完成回调驱动：存在明确的条件反例，导致 ticket 永远未激活、普通结算入口持续返回、计时与 AI 已锁住。该反例是基于旧代码与文本设计的条件推论，并非现版运行缺陷的复现。现版总体状态为 NEEDS_CONTEXT，不作验收 PASS。

## 证据与版本边界

E-01：实际通过 read_reference 分段读取的旧附件：ref/mcp-inputs/mac-codex/dd8b79747ae3b111ad0a83ec8088b69b7632ec9f122e685b76601e731d52ffe8/Carrom_current_dd8b7974.js。读取字符范围为 [0,249000)，以下按函数名定位；没有运行解混淆器，不虚构源码行号。目录及用户将其标识为旧版本 dd8b7974，本轮没有独立计算附件哈希。

E-02：操作方文本描述的新 game.js，声称 SHA256 为 d2d0ce7fb795a4342e6a288ec1ec75c16dc798d5167d23d13040020980362840。本轮未取得该文件，未核对哈希，也未读取新实现。描述包括：红棋 pending timeout 停表锁 AI；立即创建 {turn,round,armed:false} ticket；_0x338c29 50ms 后仅同一对象置 armed；每 tick 入袋扫描后 flush 校验活跃状态、round/turn、armed，每三 tick 调 _0x56abf7；静止后清 ticket 再 _0xbdafb3(turn)；结算入口遇同 round/turn ticket 返回；重开清 ticket。

E-03：操作方声称构造测试通过；未提供本轮可复核的脚本、日志或运行证据，未复验，不计作本轮通过。

E-04：已读取本轮冻结资料 genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md，以及已选 game-reverse-engineering/SKILL.md 和其执行协议、全局证据规则、未知清单模板。玩法模块入口读取被工具拒绝为本轮未选，未将其内容作为已读证据，也未扩充技能选择。

## 旧代码可证明的执行关系

1. _0x49d791 首先在 _0x3e61d0 为真时直接返回；否则递增 _0x3768e7，再更新动画、粒子、Tweener，随后才在 !_0x3fddb3 时返回。因此 UI 暂停会停止此 tick 内 Tweener 推进，而不活跃本身不阻止前面的 Tweener 更新。
2. 活跃 tick 内顺序为倒计时与超时分支 → striker 入袋检测 → 红棋扫描 → 玩家普通棋扫描 → 对手普通棋扫描 → world.step(1/60,10,10) → clearForces。旧超时分支可在本 tick 扫描前直接调用 _0xbdafb3。所述新 flush 是改动描述，旧附件不存在这段可核验实现。
3. _0x338c29 将毫秒换算为 time=(delay/1000)*60，向匿名空对象添加 Tweener；完成时仅当 _0x3fddb3 且排程 round 等于当前 round 才调用业务回调。它不返回 timer handle/target，也没有 turn 校验。50ms 对应三个模拟 tick 单位，不能当作真实墙钟 50ms 保证。
4. _0xbdafb3 检查 expected turn 与 _carromSettledTurn，检查活跃状态；_0x56abf7 返回真时通过 _0x338c29 再等 50ms，否则立即设置 settled turn，再安排后续计分、返棋与换手。后续主要回调有活跃、round、turn 保护。
5. _0x56abf7 对红棋、玩家棋、对手棋以及 striker 逐个 trimVelocity 并检查 isAwake，遇首个 awake 立即返回 true，全部未 awake 才返回 false。因此它具有修改速度的副作用，不是只读几何检测，也不保证一次调用会 trim 全部棋子。其 false 不能证明所有表现动画或返棋事务已经结束。
6. _0x5480e3 重开先丢弃 pending penalty/queen pocket，再递增 round、重置结果和相关状态，提取 striker/aim 的 tween，清理棋子并启动新回合。_0x50a0ff 与 _0x5e7a5f 均递增 turn；所读代码中重开没有把 turn 归零。
7. _0x3771eb、_0x48e98f、_0x10184d、_0x411a1e、_0x3153fe 均置对局不活跃并清理部分 pending 对象；这些入口本身不递增 round。暂停弹窗 _0x5e0129 使用 _0x3e61d0；关闭暂停恢复此标志，回主页另调用 _0x3771eb。页面隐藏路径主要更改音频/可见性标志，恢复前台时可能进入暂停弹窗，不能把它等同于立即停止 ticker。广告路径另外存在 ticker.stop/start。公开 pause/resume 在旧附件中为空函数。

## ticket 安全性与归属

条件成立时，立即发布 ticket 可让稍后到达的普通 _0xbdafb3 重试停止抢先结算；同对象判断可使被替换 ticket 的旧 armed 回调失效。flush 校验 round/turn 可防旧局、旧回合提交；静止后先清 ticket 再同步调用入口可避免入口被自身拦截，随后旧 _carromSettledTurn 可防同 turn 重复提交。

这些保护均依赖现版确实按描述实现，且没有其他路径绕过锁直接换手。应核查 guard 的参数匹配、所有 AI fallback/延时击球入口、玩家输入以及所有 turn 修改入口。锁住最终击球函数不自动证明 AI 的中间移动、重试和直接换手分支都被锁住。

归属仍取决于 _0x209883 等实际 actor 状态在提交前不改变。ticket 只保存 round/turn，没有 actor 快照；如果这些状态可在同 turn 内被改写，ID 校验本身不够。反之，若 actor 只在递增 turn 的换手函数中改变，则校验可隔离该类错属。

重复超时事件不应为同 round/turn 无条件重建 ticket，否则旧 armed 回调被对象比较拒绝，新 ticket 又从未激活开始，可能反复延后。重复 armed 回调将同一对象反复置 true 通常无额外效果，但不能替代结算去重。不得假定所有旧延时链都已销毁。

## 关键活性反例

### A. 未 armed 时外部取消 Tweener

序列：创建 ticket 并停表锁 AI → armed 所依赖的 tween 在完成前被外部清除 → 不再有其他 armed 来源 → flush 每次因 armed=false 返回 → 同 round/turn 的 _0xbdafb3 又因 ticket 返回。只要状态不再被其他 owner 改变，该等待没有自愈路径。

这是所述状态机在“外部取消不触发完成回调”前提下的逻辑反例，不证明旧附件中的定向 Tweener.extract(striker/aim) 会取消匿名 timer。匿名 target 与棋子 target 不同；未读到 Tweener 库实现，不能声称 extract 的全部语义或全局清理发生过。

### B. 不活跃期间 timer 到期后恢复原局

序列：未 armed ticket → 对局置不活跃且 round/turn 未变 → tick 继续到 Tweener.update → timer 完成 → _0x338c29 因不活跃不调用 armed 业务回调 → 随后恢复同一局/回合并保留 ticket。若该 tween 为一次性完成且无重新排程，恢复后与 A 同样永久等待。

旧代码能证明 timer wrapper 会过滤业务回调，且不活跃检查位于 Tweener 更新之后；一次性完成后不再重放属于需核对 Tweener 库的前提。不能将恢复活跃等同于被丢弃回调会补发。

不活跃时仅在 flush 中清 ticket 也不一定足够：旧 tick 在不活跃处提前 return，位于扫描后的 flush 根本到不了。不活跃若只发生于两次 tick 之间，恢复时的活跃检查同样看不到这段历史。应由生命周期入口显式失效或记录 session/epoch。

### C. 暂停和 ticker 停止

若仅 UI 暂停且 timer 保留，_0x49d791 顶部返回会一起冻结 armed 计时和扫描；恢复后应继续累计模拟时间，不属于 B 的回调丢弃。若 ticker.stop 则同样需等待 ticker 重新启动。暂停期间若外部取消 timer，仍回到 A；若库由另一个独立 ticker 更新，则需要另外取证，不能套用上述冻结结论。

### D. 已 armed 后不活跃

若 ticket 保留、round/turn 不变，再恢复时可能继续 flush。这避免未激活等待，却允许旧请求跨一次退出边界继续生效。是否应继续，取决于这是暂停还是终止对局；二者必须由生命周期 owner 明确区分。若退出时先清 pending queen/penalty，随后恢复旧 ticket，结算可能面对已被清理的中间状态，不能仅凭 round/turn 相同就认为合法。

## 退出、重开与计时器销毁

重开清 ticket 加 round 递增可使旧 armed 回调失效；身份校验和 round 校验是安全性保护，不等于物理销毁计时器。旧 _0x338c29 无返回句柄，重开所读清理主要针对具体对象，不能宣称匿名 timer 已取消。若 ticker 不推进，旧闭包可能继续留存；是否自然移除、占用量和异常行为需库实现及运行证据。

退出到主页或其他页面应在其唯一 owner 处失效 ticket，并让旧回调失效。恢复同局的暂停应保留有意义的规则等待进度。单纯清 ticket 可能让已停表锁 AI 的旧局无结算来源，因此清理必须与“终止旧局”或“恢复受控结算”成套处理，不能只增加一个赋 null。

清 ticket 后 _0xbdafb3 若由于活动状态变化、其他 guard、异常或再次运动而未提交，必须说明后续谁重试。旧入口的运动重试仍依赖相同 Tweener wrapper；本轮方案没有证明提交后阶段中的异步换手/返棋计时被取消时也能恢复。不要将 timeout ticket 修复扩展宣称为整个结算生命周期已闭合。

## 扫描、静止与物理步长

建议将“本次状态同步与所有入袋扫描完成后，才允许超时提交”作为本轮审查契约；不改既有碰撞或计分规则。旧扫描在 world.step 前，因此 flush 若插在扫描后、step 前，看到的是本轮步进前的位置；若插在 step 后，则该步刚产生的入袋位置可能要下一轮才被扫描。应在现版确定准确插入点，防止步进后直接静止结算遗漏待扫描入袋。

每三 tick 检查一次只限制采样频率，不保证连续三 tick 静止。trimVelocity 会改变下一次物理结果；flush 和 _0xbdafb3 同步调用两次 _0x56abf7，也应复核副作用。不得以等待 50ms 或“awake=false”单独证明所有入袋动画/返棋创建刚体已完成。旧正常模式对 pending queen pocket 有提取并转为 _0x404020 的补偿路径，应保留并核对，而非仅等待表现 tween。

旧物理步长为每次逻辑 tick 1/60 秒，求解迭代参数 10、10；外层 _0x4bf21a 累加 delta，while accumulator>1 时逐 tick 执行，没有在所读函数中看到最大补步上限。输入 1 的首次调用可能仅累积而不步进。50ms 换算三个逻辑单位，但精确完成 tick 与插入顺序、Tweener 时间比较有关，未验证。不可把三 tick 当作不同帧率下严格墙钟时间。

碰撞由旧 planck/box2d world 驱动；入袋扫描采用到袋中心距离<=20（源码逻辑坐标），这是几何触发条件，不是碰撞求解阈值。_0x56abf7 所用 trimVelocity 的数值阈值本轮未定位，不新定误差、不修改物理。成功标准是原归属提交一次并合法进入后续回合/结果；失败标准是错属、重结算、旧局污染或等待无恢复。实际胜负依赖未提供的 CarromDiscRules，不补造竞品规则。

## 最小设计收口建议（未实施）

1. 保留唯一结算 owner 与 ticket 对象/round/turn 校验；对同一请求的重复超时做幂等处理。
2. 将 armed 的规则进度放在可恢复的对局状态中，例如活跃且未暂停时累计逻辑 tick；Tweener 只作表现或辅助唤醒。若保留现结构，必须有独立于该 tween 的恢复路径，并保证等待窗口已满足才激活，不可无条件提前结算。
3. 退出/终局 owner 显式失效请求；暂停保持等待状态；恢复 owner 检查未 armed/已 armed 请求及其计时来源，恢复或终止必须一致。
4. 若需要真实取消 timer，应由排程 owner 暴露明确句柄和取消契约，避免全局清空 Tweener；取消、自然完成、重复回调均需幂等。
5. 核对 flush 在所有扫描之后且未遗漏本次物理步的新入袋；原计分、返棋与换手事务仍需独立去重和恢复。

界面与核心循环保留原工程：瞄准/击球→物理演化→入袋→原规则结算→换手或结果→重开。本轮不调整界面布局、不新增标题或文案、不迁移引擎。工作流标注 Canvas 2D，但旧附件实际引用 PIXI 和 planck；仅记录此事实，不为审查而重写工程。默认英文要求不触发本轮游戏文件改动。

## 待执行验收矩阵

以下均未执行。须在匹配现版哈希的完整工程上复验，记录 round、turn、actor、ticket 身份、armed、active、paused、settledTurn、pending queen/penalty、提交次数和 AI 击球次数。

| 场景 | 验收条件 |
|---|---|
| 普通 timeout 与旧结算回调交错 | 扫描完成且静止后仅提交一次，actor 保持一致 |
| 同 tick 红棋/普通棋/striker 入袋 | 入袋和犯规状态先登记，计分/返棋按原规则且无遗漏 |
| armed 前取消该 timer，继续活跃 | 不永久锁局，不能提前越过规定等待窗口 |
| armed 前进入不活跃，timer 在期间到期，再恢复同 round/turn | 有明确恢复或终止结果，无悬空未 armed ticket |
| armed 前后暂停/恢复及 ticker.stop/start | 暂停无提交，恢复继续正确进度，不重复计时或结算 |
| armed 前后退出、重开，多次重复 | 旧回调不污染新局，ticket 正确失效；计时器/闭包不持续累积 |
| 同请求重复超时、重复 armed、重复 flush | 不反复重置等待，不重入或重复换手 |
| 静止后清 ticket 到结算入口，以及结算后返棋延时被取消 | 入口拒绝/异常有可诊断恢复，返棋/换手无永久等待 |
| 快慢帧与补步，逐 tick 袋边状态 | 以逻辑顺序为准，无漏袋，提交次数与归属完全一致 |

规则误差：提交次数、round/turn/actor 和旧局污染容差为零；延时按逻辑 tick 观测，不能未经库实测设定真实毫秒容差；物理位置/速度容差沿用工程阈值，现缺 trimVelocity 与运行轨迹，保留待核对。

## 本轮真实验证结果与限制

PASS：上述旧附件函数及执行关系已通过 read_reference 静态读取，报告区分旧证据和文本方案。
NEEDS_CONTEXT：现版代码、哈希、准确 flush 位置、所有锁入口和恢复实现均未直接核验。
BLOCKED：现版动态复验缺完整现版源码、Tweener 库与可运行工程。未调用 run_validation，未执行 npm run build、npm test、npm run check、浏览器或真机测试；本轮是用户限定的只读原型审查，不以旧附件构建或合成测试冒充现版验证。

未修改游戏文件；未生成图片、截图、源码包或试玩包；操作方构造测试仅为转述。

## 未知清单

| 编号 | 未知项 | 还缺什么 | 当前证据 | 状态 |
|---|---|---|---|---|
| U-01 | 新 game.js 是否与描述及声称哈希一致 | 提供现版文件并核对真实哈希与差异 | E-02 | 未闭合 |
| U-02 | Tweener 完成/取消/清理及暂停时序 | 实际库代码与取消、完成、恢复日志 | E-01 的 wrapper，缺库实现 | 未闭合 |
| U-03 | 不活跃后是否允许原 round/turn 恢复及 ticket 处理 | 当前退出/恢复 owner 与分支代码 | E-01、E-02 | 未闭合 |
| U-04 | flush 与 step 的准确顺序及静止阈值 | 现版 tick、trimVelocity 实现与逐 tick 轨迹 | E-01、E-02 | 未闭合 |
| U-05 | 锁是否覆盖所有 AI/输入/直接换手路径 | 现版所有调用点及交错回归日志 | E-01、E-02 | 未闭合 |
| U-06 | 操作方测试的覆盖和真实结果 | 匹配版本脚本、命令、退出码、事件轨迹 | E-03 | 未闭合 |

本报告完成静态审查交付，不代表现版实现或恢复活性验收通过。
