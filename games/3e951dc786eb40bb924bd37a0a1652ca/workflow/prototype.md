# Carrom Freestyle 无操作换手证据与实现边界

## 0. 交付范围与结论

- 项目：`3e951dc786eb40bb924bd37a0a1652ca`；工程工作区 `games/3e951dc786eb40bb924bd37a0a1652ca`。文件工具以该工程为根，本报告交付为 `/workflow/prototype.md`。
- 阶段：prototype / 原型定义；attempt=1，恢复续接。`autonomous:false`。本轮仅文字证据分析与历史源码静态追踪，不实现，不推进 art/code/test，不代表设计已获用户批准。
- **未收到视频附件，没有观看或独立复核录像。当前开发版未知；文件名包含 current 的 JS 仍仅为用户提供的历史快照 d201。**
- 60 秒样本的完整相邻高亮换侧间隔为 **15.6、15.2、15.6 秒**，支持“该样本存在约 15 秒量级的可见无操作换侧节奏”的假设；不证明精确内部超时值、倒计时起点、输入是否重置或竞品全模式规则。开头 9 秒是截断段，不参与完整窗口估计。
- 历史 d201 有两套不同计时：回合计数和延迟结算随逻辑 ticks/Tweener 推进；匹配界面使用保留剩余时间的原生 setTimeout 任务。**不能将匹配准备定时器误认作回合无输入超时。**
- 建议离线双人传玩使用独立模式配置、唯一回合 owner、有效前台单调计时、暂停原因集合和带 round/turn token 的一次提交。超时只结束当前输入机会，不凭证据不足添加罚分，不进入 AI 发射路径。
- 本轮实际验证只有附件文字读取、历史源码函数交叉核对、手算间隔及报告回读；没有构建、单测、浏览器输入或竞品实测。本报告不是成品验收 PASS。

## 1. 证据来源、方法及引用约定

### 1.1 实际读取来源

以下路径相对工程 `ref/`，通过 read_reference 读取：

|编号|来源|身份与边界|
|---|---|---|
|R1|`mcp-inputs/mac-codex/d8e1a0b421927f19767297d450a93cd464bb49b6e9a14e3de5635afd05a3a196/freestyle-local-evidence.md`|累积文字证据，读取全文；内含录像、截图、日志路径及他人观察，不等于本轮收到或查看这些媒体。|
|R2|`mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js`|用户提供历史 JS d201，多字符区间静态读取；未取得当前开发版、依赖包及该文件实际 SHA-256。|
|O1|本任务提交的 60 秒观察摘要|操作者按 0.2 秒步长采样上/下侧高亮，比分 20:0；仅转述，没有视频。|

R1 中录像的 SHA-256 是文档记载值，本轮未对录像重新计算。R2 目录中的 d201 标识是附件路径身份，不冒充文件哈希。R1 提到的 `development/js/game.js` 配置属于文档记载，不能当作本轮现版源码取证。

实际读过冻结知识正文：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。实际读过技能 `game-reverse-engineering/SKILL.md` v10.5.0 及 `references/execution-protocol.md`、`references/global-rules.md`、`references/unknowns-ledger-template.md`。采用证据分层、版本隔离、定位真正 owner 与稳定提交边界、一次事件一次提交及未知登记的方法；不复制案例阈值。玩法逻辑子模块入口读取被本轮选择权限拒绝，未采用其未读正文，不宣称完成模块方法验收。

### 1.2 行号缺口与执行选择

附件接口返回字符切片，不返回 JS 原文件绝对行号。本轮已就引用格式调用暂停询问工具；返回内容明确为**执行者引用格式选择**：接受函数锚点、摘录行号和字符区间，原文件绝对行号标记为未闭合。**这不是用户确认，也不是设计批准。**

下文引用格式：`R2 历史d201 / 函数名 / 读取区间 / 摘录编号:相对行号`。附录中每行有局部 L 编号，只针对该摘录，从 L01 重新计数；**不是 JS 原文件绝对行号，更不是报告所在行号**。字符区间是实际请求的 offset 与 limit 窗口，不是精确函数偏移，也不声称返回的每个窗口均无截断。绝对行号仍为 U05 未闭合。

## 2. 观察、推断与未证实项

### 2.1 本次无操作样本

|采样时刻|操作者所述高亮|与前次换侧间隔|使用范围|
|---|---|---|---|
|9.0 s|上侧首次亮|起录至此 9.0 s|起录已在回合中，截断段；不得据此设为 9 秒超时。|
|24.6 s|下侧|24.6−9.0 = 15.6 s|完整相邻可见换侧间隔。|
|39.8 s|上侧|39.8−24.6 = 15.2 s|完整相邻可见换侧间隔。|
|55.4 s|下侧|55.4−39.8 = 15.6 s|完整相邻可见换侧间隔。|
|60.0 s|摘要未给新的换侧点|尾段 4.6 s|截断尾段，不用于完整窗口估计。|

三段平均约 15.47 s，范围 15.2–15.6 s，仅作样本描述，不提高为配置精度。0.2 s 是采样步长而非内部计时精度；若确为首个采样检测且相邻样本均可靠，每个边界可落在此前一个采样间隔内，间隔量化偏差可达约 ±0.2 s。缺少原始采样表和视频，不能保证这些条件，也不能为内部倒计时建立此误差界限。高亮出现可能晚于回合提交，准备动画、恢复/失焦、漏记事件和网络/版本差异均可能影响间隔。

比分保持 20:0 的摘要支持“该样本未见积分变化”；不证明所有超时永远不罚分、是否返棋或高亮等于输入权。必须另用实际另一侧输入验证换手。不能从 20:0 倒推这一分钟中的进袋过程或女王状态。

### 2.2 累积证据与模式隔离

|层级|能说什么|不能说什么|
|---|---|---|
|R1 的竞品记载|19.6.0 /1491、MuMu 单账号；离线传玩 Freestyle Disc Pool 与联网 Delhi Freestyle 来自不同入口、场景和网络状态。|不是仅改变网络条件的控制变量试验，不证明联网/离线导致规则差异。|
|R1 初盘记载|离线某局 12 黑+12 白、未见红、目标180；联网某局 9 黑+9 白+红、目标160。|未独立看图；不能推广到所有对局，顶部红图标不证明盘面有红。|
|R1 黑棋样本|同杆黑棋进袋及 +10 的文字记载，四袋抽样加强归因。|抽样不等于完整事件追踪，不证明所有模式黑棋10。|
|R1 后续白棋样本|该局单白棋入袋后玩家1为20/180、下侧仍亮的记载，强支持该局白棋20。|本轮未查看视频；不能把曾有冲突的图例配对当定论，不能称新断网实测。|
|R1 后续另录一杆|另段开头已上侧亮，等待后下侧操作、再换侧。|录像不连续，不能证明白棋得分后原回合直接连续续杆。|
|R1 摆位红圈|文字支持母球重叠附近有红色反馈。|不能证明距离阈值、禁止发射、精确碰撞几何。|
|历史 d201 静态代码|存在 mode/arena/equipmentTime 配置调用、AI回合与玩家回合、超时分支。|不是竞品运行证据，不是当前工程状态，不证明本地双人模式已经存在。|
|项目建议|可以采用可配置15秒输入预算及无输入不改棋盘比分的设计。|这些是建议，不是复刻已证实规则或已完成实现。|

R1 的“白10/黑20”排列推断有撤回和后续冲突，应优先保留真实单棋事件归因但仍标样本边界。360/2=180、320/2=160 只是特定配置的算术关系，不证明通用目标公式。旧影像复核 run `a121f5acbe1e444d8ad1229ad3e43f3d` 在 R1 记载为 awaiting_input，JPEG读取通道无法查看，未完成独立影像复核；本轮未重做或声称完成。

## 3. 历史 d201 的真实计时与生命周期

### 3.1 逻辑计时：回合计数不是原生定时器

1. `_0xa07a9b` 初始化 PIXI sharedTicker 并注册 `_0x4bf21a`（读取窗口 offset=12000, limit=36000）。历史代码 `box2d=planck`，不代表本项目改选 PIXI/Planck 框架。
2. `_0x4bf21a(delta)` 累加 delta，**while(accumulator > 1)** 执行 `_0x49d791(1)`，循环内重新检查 host/ad blocked。不是 `>=1`；本地循环没有明确的每帧追赶次数上限，PIXI ticker 是否裁剪 delta 未知。附录 E1:L01–L08。
3. `_0x49d791` 开头核游戏内暂停 `_0x3e61d0`、host pause、广告 token，之后才推进 Tweener、对象和粒子；因此这些暂停阻止回合 tick 和 Tween 延迟。回合倒计时门控为 `_0x3a1262 && (arena !==0 || (mode===0 && !tutorial))`，不可简化成“所有模式都开超时”。每次合格逻辑更新将 remaining 减1、改当前方头像进度条。附录 E2。
4. `_0x5480e3` 重开时由缺失外部 `window.CarromDiscRules.turnTicks(mode,arena,fallback,equipmentTime)` 取得 turnTicks。fallback 数组为 `[100*60,25*60,20*60,15*60,10*60]`（读取窗口12000/36000）；不能把 fallback 当实际有效配置或全模式15秒。重开配置赋值原文见 E6:L04。
5. `_0x50a0ff` 是 **AI 回合**，`_0x5e7a5f` 是玩家回合；两者 turn++、enable timer、remaining=turnTicks，随后再加 striker 准备动画 `time:0xf`（读取窗口138000/60000）。所以所见历史路径计时重置早于准备完成，准备可消耗计时，不宜照搬为双人输入窗口。
6. 到零先 `_0x24bb4a` 关闭计时/输入；普通路径玩家→AI、AI→玩家。mode1待覆盖或mode2女王pending时建立 round/turn timeout ticket，50式延迟作 armed 标记，由进袋扫描后 flush，稳定后交 `_0xbdafb3(turn)`。附录 E2/E4/E7；**普通超时不能直接调用AI回合来实现第二位人类。**

### 3.2 `_0x338c29` 是 Tween tick 延迟

函数实际创建空对象 Tween，`time=(delay/1000)*60`，onComplete 只核 active 与 captured round。E3:L01–L14。它**不加入 `_carromMatchTimers`，也不自己核 turn**；部分调用者捕获 turn 并在后续函数校验。换算示例：50→3 ticks；500→30 ticks；1000→60 ticks；2300→138 ticks；`time:15` 为15 ticks，名义60Hz约0.25秒，不是15秒。实际墙钟时间依赖未提供的 Tweener/PIXI 实现。

玩家 `_0x1e39ba` 松手在 strength>=0.25 时真正击出，调用 `_0x24bb4a`，再通过 `_0x338c29(...,0x8fc)` 请求 capturedTurn 的结算。AI `_0x4b3cc6` 也在有效发射后关闭倒计时并延迟结算；存在候选校验、有限重试及 AI shot turn 幂等。`_0xd6b627` 中 return 后的旧5000延迟代码不可达，不计入执行路径。

`_0xbdafb3(expectedTurn)` 核 turn、settledTurn、timeout ticket及active；运动未停则50式延迟再试，稳定后提交 settledTurn、remaining=-1并让刚体睡眠。mode2普通子飞分回调仍承担部分积分提交，但最终决定回合前会 flush 回调；queen积分部分先credited、表现回调不重复加分。历史代码不能称为完全规则/渲染分离。延迟500或进袋1000式后决定续杆、换方或结果，女王策略注释明确 provisional；外部 rules 未提供，不作为竞品定论。

### 3.3 匹配UI的原生 setTimeout 任务

`_carromMatchSchedule` 注册 owner、callback、remaining、handle、due、version；`_carromMatchNow` 优先 performance.now、fallback Date.now。arm 记due并设置原生 setTimeout；回调核version、blocked、列表身份，移除任务后只有owner仍为activeMatch且parent为stage才调用。暂停clearTimeout并保留 `max(0,due-now)`；恢复只给有效owner重arm。E5。

匹配UI `_0x104b9b` 构造中 `_carromMatchSchedule(matchUI,... emit('ready'),0xbea)` 的 3050ms 是匹配准备延迟（实际读取窗口348000/60000）；并非玩家无输入窗口。另UI分支也调schedule，早先切片末尾未完整取得该delay，不泛化成全部3050ms。匹配`startRoll`会先cancel该owner任务（本轮窗口408000/12000）。

`_carromMatchBlocked()` **只含hostPaused或广告tokens，不含游戏内暂停，也没有直接visibility条件**。所以内暂停冻结逻辑ticks/Tweener，却未在此任务集合统一冻结原生匹配timer。原生转盘中奖音效 `_0x5b20b9` 的200ms setTimeout又是另一用途（窗口78000/30000），不能混入回合计时。日期型奖励冷却也不是回合无输入timer。本轮不宣称全文件所有异步已穷举。

### 3.4 事件边界清单

|事件/锚点（均为历史d201）|静态事实|移植风险/边界|实际读取窗口 offset/limit|
|---|---|---|---|
|game.pause/resume；`_carromConnectLifecycle`|host暂停幂等、清accumulator、暂停match timers、静音、cancelAim、结束滑条、禁view.pointerEvents；resume恢复但timer仍核广告；GameSnacks注册一次。|host路径不等于内暂停/后台路径。恢复输入样式本身不证明所有交叉暂停安全。|12000/36000|
|`_0x4ad106`|失焦/隐藏改前台标志与静音；回前台若原在对局则打开内暂停。|所见update门控不直接核visibility，不能宣称后台立即冻结；浏览器节流行为未知。|12000/36000|
|`_0x5e0129`|内暂停清当前aim表现与pointer身份、设pause flag、显示面板；close清flag，home走退局。|所见不调用pauseMatchTimers；不声称所有原生timer被冻结。|78000/30000|
|`_carromAdPause/Resume`；插屏/奖励函数|token去重、pauseMatchTimers、清aim/滑条、静音，token全清且非host暂停才恢复timer；SDK回调另有完成去重/generation和ticker.stop/start。|插屏finish所见无条件尝试ticker.start，但update仍有host/ad门控；不能仅看start就判交叉恢复正确或故障已复现。|252000/12000；78000/30000；108000/30000|
|`_0x36ab44`/`_0x536112`|start核pause/host/ad/tutorial/允许输入/actor及pointer；move核aim及pointer身份；所见不重置remaining。|没有证明竞品输入重置政策；应测试摆位滑条、按压、长拖和无效输入。|138000/60000|
|`_0x1e39ba`|release核aim与pointer id/type，清身份，pause/ad时取消；strength>=0.25才击出并关闭计时。|到零与松手竞争需唯一提交owner；不能只靠UI开关。|138000/60000；168000/60000|
|`_0x24bb4a`|关闭aim标志、隐藏瞄准、关闭timer、清头像进度、disable滑条/输入。`_0x1a373b - 0x1` 是无赋值表达式，**不会修改remaining**；本函数没有显式清pointer IDs。|不能误读为remaining=-1，也不能当作完整cancelAim。|108000/30000；E4|
|`_0x5480e3`重开|清aim/pointer、discard待罚/女王、round++、清ticket/result/history、extract striker/aim Tween、清分重建盘面、配置turnTicks，再启动玩家或AI。|不证明现版具备这些保护。|69000/9000；E6|
|`_0x3771eb`退局；`_0x3153fe`建匹配|cancel旧activeMatch timer、activeMatch=null；退局active=false，旧Tween回调靠active/round失效；match事件核owner/parent。|退局再进可能重新active，必须结合新round和每个回调token；不能笼统认为clearTimeout覆盖Tween。|78000/30000|
|准备Tween回调|所见玩家准备回调未捕获round/turn；重开提取striker Tween能覆盖部分路径。|旧回合准备回调干扰新回合是静态风险候选，未运行复现。|138000/60000|
|`_carromFlushTimeoutAfterScan`/`_0xbdafb3`|ticket核round/turn，armWait/wait逐tick推进，awake时延迟；扫描后flush再world.step(1/60,10,10)、clearForces。|必须防同tick袋口/女王事件漏提交；物理顺序不能擅称为标准引擎惯例。|108000/30000；252000/12000|
|`_0x47e567`结果|resultCommitted幂等、捕获round；奖励还有bonus一次发放。|不是离线双人胜负契约；终态必须另断开输入/超时与旧callbacks。|108000/30000|

## 4. 建议的离线同机传玩原型契约（未实现、未确认）

### 4.1 核心循环与配置隔离

入口明确为 `local-pass-and-play/freestyle-disc-pool`：两位真人在同一设备轮流摆位、瞄准、松手击出 → 物理运动 → 进袋事件汇总 → 一次结算 → 续杆/另一人准备 → 下一输入窗口，直到目标胜负或主动退出。

禁止把现有AI actor=false直接当Player2；抽象 `actorId=player1|player2` 与 `controlType=human|ai`，输入权由activeActor决定。联网模式的计时权威需按其实际协议另行核验；若由服务器授权，应保留该权威，不套用本地暂停契约。AI、普通Disc Pool、Carrom女王覆盖模式各自配置和验收。不给现有单人模式静默修改默认计时、棋数或计分。

模式配置至少包含 `modeId, entryId, rulesVersion, discLayout, pointsByType, queenPolicy, goal, inputBudgetMs, prepareMs, timeoutPolicy`。为后续可复现实验可建**暂定夹具**：12黑12白、无女王、黑10白20、目标180、输入预算15000ms、准备250ms；它是根据有限样本构造的项目假设，不是竞品完整规则。命中目标条件建议 `score>=goal`，不要求精确等于；若有规则pending，先稳定结算再宣布胜方。合法进普通子且无犯规建议续杆、空杆建议换方；这些仍待连续录像与产品决定，不能从本次无操作样本证明。

### 4.2 状态与输入窗口

|状态|输入|输入预算|离开条件|
|---|---|---|---|
|MATCH_READY / TURN_PREPARING|禁止发射，不保留上一人pointer|不消耗|稳定盘面、母球合法摆放及准备完成后由逻辑owner开窗。|
|TURN_INPUT（摆位/瞄准/拖动）|仅当前真人；一个有效pointer捕获|消费有效前台时间；任何移动/按压都不重置|合法松手且未到期→SHOT_IN_FLIGHT；到期→TIMEOUT_RESOLVING。|
|SHOT_IN_FLIGHT|关闭所有发射/摆位|停止，无输入超时不打断已击出的物理|盘面稳定并完整扫描进袋后→SETTLING。|
|SETTLING / TIMEOUT_RESOLVING|禁止输入|停止|同turn仅一次提交；续杆或换方后开新turn。|
|PAUSED|取消当前拖动，不在恢复时自动发射|冻结并保存remaining|所有pause原因清空且用户恢复后回到暂停前的合法状态。|
|RESULT / EXITED|禁止发射|关闭|只允许Restart/Home；旧回调不改分、不换方。|

建议窗口从**逻辑TURN_INPUT开放**而不是视觉高亮首次出现计时，准备时间单独计；这与历史d201准备可能计入预算的路径不同。暂定15000ms只为本项目可配置评审值，不要求为了贴合15.6秒高亮间隔增加600ms。配置必须显式记载起点政策，HUD显示同一逻辑remaining。

### 4.3 时钟、暂停与原子提交

- `TurnController` 为唯一回合/超时owner。使用注入的单调时钟，生产默认 performance.now；remaining=T−当前输入窗口未暂停累计时长，不按渲染帧数减，不因动画时长或FPS改变预算。
- `pauseReasons` 集合至少区分 `menu, host, hidden, blur, ad:<token>`。暂停前先消费到暂停事件时刻再冻结；移除一个原因不移除其他原因；最后原因清空才恢复。后台立即加入原因，回前台默认要求Resume，避免直接把设备交给另一人或补扣后台时间。所有相关逻辑scheduler采用统一政策，音效/奖励冷却另声明用途。
- 到期的准确判定是 `activeElapsed>=inputBudgetMs`。松手命令进入逻辑层时先更新计时；`activeElapsed<T` 且合法才接受击出；等于或超过T时超时优先。记录命令处理时刻和输入原始timestamp，主线程阻塞后不回溯补发已过期的松手。
- timeout与shot通过同一个 `finishInput(roundId,turnId,reason)` 一次提交；同turn不能既击出又换手。接受任一后立即取消pointer捕获、清ID/力度/aim，关闭滑条，invalidate旧turn延迟；迟到pointerup无效。
- 无效低力度松手/取消/多指不发射、不换方、不重置预算；只有活跃pointer可以瞄准。摆位几何非法时明确英文反馈并拒绝发射，仍消耗预算。不采用截图红圈推断的精确阈值。
- **无输入超时**只提交一次`timeout`并换给另一真人；该空窗口没有击出/入袋事件时棋子与比分保持，重新摆放母球属于下一回合准备，不扣分、不返已得分棋子、不自动发射。已有规则pending不得被当作纯空窗口：交由该模式规则显式处理，不移植历史女王罚分猜测。
- round/turn/phase token随每个准备、结算、音画回调携带；回调核active+token，动画完成不是积分/换手唯一提交点。重开、退出、结果统一撤销旧任务并清pointer/timeout候选；重开生成新round，即使旧native timer已入队也不得提交。

### 4.4 物理、碰撞、计分与成功失败

本项目继续原生 Canvas2D Web/H5，玩法状态、输入和渲染分离；不加载 Cocos、不伪造引擎版本。本轮无引擎迁移或代码集成。

建议物理固定 `dt=1/60 s`，圆盘与圆盘/边界接触解算，袋口检测只对未pocketed的discID产生一次事件；高速路径用连续扫掠或有界子步防穿袋/穿子。历史读取明确 `world.step(1/60,10,10)`，但不据此假定新Canvas解算器与Planck轨迹完全一致。碰撞摩擦、阻尼、质量、恢复系数和盘面尺寸需随冻结物理配置交接，当前未定，不编造已还原参数。

长帧建议每render最多8个物理步；超额物理积压保留并逐帧追赶，积压存在时不开放下一输入窗口、不认定settled。极端积压需显示恢复状态并记录日志，禁止以一次超大dt快进。输入计时独立于物理catch-up；回前台清暂停期间物理差值，禁止补跑后台运动。稳定判据建议所有盘面对象线速度低于棋盘有效宽度的0.001/秒、角速度低于0.01rad/秒持续12个物理tick，且无待进袋/返棋事件；该阈值是暂定工程误差政策而非竞品测量。

碰撞不直接提交积分。`RulesReducer`在稳定边界消费唯一shotID+discID队列，按模式配置一次计分、一次判续杆/换方/目标胜负；`Renderer`只读状态画飞分。目标临界、同杆多子、母球入袋、女王pending需单独规则夹具；本轮不确定竞品罚分政策，不能默默启用。成功是冻结配置下先达目标且结算有效；对另一玩家为失败；输入超时仅丢失本回合机会，不等于整局失败。棋子耗尽但双方未达目标的处理需配置（建议比较分数、相同则Draw），不得把未定规则误报为竞品行为。

### 4.5 界面布局与英文文案

默认游戏语言 English，后续页面 `html lang=en`，中文浏览器仍默认英文；报告中文不等于游戏改用中文。

竖屏：上部Player2与比分，中央棋盘与四袋，下部Player1与比分及当前方定位条，角落Pause；双方高亮同时配 `Your turn`/`Waiting` 和倒计时数值，不能仅靠颜色传达。桌面居中等比缩放，输入坐标映射至固定棋盘逻辑坐标，面板不遮住有效定位区。准备态与可输入态视觉区分，暂停面板覆盖输入，结果面板提供Restart/Home。

主要文案：`Carrom Freestyle`、`Pass & Play`、`Player 1`、`Player 2`、`Ready`、`Your turn`、`Drag to aim. Release to shoot.`、`Time is up — pass to Player 2.`（动态玩家名）、`Invalid position`、`Paused`、`Resume`、`Restart`、`Home`、`Player 1 wins!`、`Draw`。规则提示：`Reach 180 points to win. Your turn timer does not reset while aiming.`（目标动态读取配置）。无障碍标签如 `Pause game`、`Striker position`、`Time remaining`。

## 5. 可复现验收计划（本轮全部未执行）

### 5.1 夹具与日志

固定模式/规则/物理配置版本、种子、初始棋盘、actor与remaining。注入时钟测试逻辑边界，真实浏览器测试Canvas坐标、pointer捕获、UI与生命周期；二者不能互相冒充。日志每事件至少包含 `sequence, monotonicMs, inputTimestamp, roundId, turnId, modeId, actorId, phase, pauseReasons, remainingMs, shotId, timeoutCommitted, settledTurn, physicsStep, pocketedDiscIds, scoreBefore, scoreAfter, callbackToken, rejectReason`。必须能够说明谁开窗、谁消耗时长、谁提交及旧回调为何被拒绝。

参考采样核验另需连续录制从开窗前至换侧后，同步输入时间与四袋、HUD、网络/版本，不能只依赖高亮首帧。

### 5.2 误差边界（建议验收标准，不是实测）

- 注入时钟：T−1ms不超时，T及T+1ms超时；pause剩余误差≤1ms；每turn至多一次shot/timeout/settlement，分数和棋子事件无“差不多”容差。
- 真实前台无阻塞：逻辑提交不得早于deadline，正常60Hz下日志检测延迟建议≤50ms，视觉反馈≤100ms；必须记录实际FPS/长任务。长阻塞不要求浏览器准点执行，但下一次处理不得补发过期击球或一次跳过多个新回合。
- 同一实现/配置/种子/固定输入，以30/60/120Hz render测试：最终计分、进袋ID、actor完全一致；对应固定物理step中心坐标偏差建议≤有效棋盘宽度0.001。与竞品轨迹不作等价要求。
- 摆位用可缩放逻辑几何：中心距小于半径和时非法；允许数值epsilon建议为棋盘宽度1e−5，不把屏幕红光圈像素当物理半径。高亮采样的0.2秒误差不可用来放宽项目内部计时验收。

|ID|步骤|预期及可观测断言|
|---|---|---|
|A01 无输入|静止盘面，完成准备后连续6个15000ms窗口不操作。|每窗口一次timeout，P1/P2交替且两侧均可真正输入；比分/棋子不变，准备250ms单列。|
|A02 部分回合|开窗已过6000ms开始采样。|剩9000ms到期，不以录制起点另给15秒；能解释样本首段为何不能估值。|
|A03 准备|将prepareMs改为0/250/1000，分别记录ready及高亮。|输入窗口均独立15秒；比较可见换侧周期时包含准备，不误读为改变timeout配置。|
|A04 输入不续时|在第1、7、14秒摆位/瞄准；长拖跨过deadline。|remaining只递减，到期cancel捕获；迟到release不击出，另一真人获得输入。|
|A05 临界竞争|注入松手于T−1、T、T+1；重复pointerup与timeout回调、不同调用顺序。|前者合法才shot，后两者timeout；每turn唯一提交，不同顺序遵守同一边界政策。|
|A06 取消与多指|低力度、pointercancel、touchcancel、outsideRelease、第二指移动/松手、非法摆位。|不误发射/不重置预算；有效pointer身份正确，英文反馈；失效旧ID不影响下一回合。|
|A07 已击出与运动|第14.9秒合法击出，运动延续超过15秒；四袋有同杆多子。|倒计时停止，不因15秒打断运动；完整pocket队列一次结算；续杆开新turn预算。|
|A08 暂停菜单|剩5秒开Pause等30秒，Resume；分别在准备、拖动、运动、结算暂停。|预算/逻辑scheduler冻结；拖动取消不自动击出；运动继续来自暂停点，结果不重复。|
|A09 交叉生命周期|host pause→ad pause→host resume→ad resume；双ad token、重复pause/resume、hidden+menu。|任一原因残留都不恢复输入/计时；最后原因按Resume策略恢复；匹配与回合timer分别核。|
|A10 后台/失焦|真实page隐藏/失焦再返回，另用注入生命周期做边界确定测试。|后台不扣预算不补物理，返回需Resume；模拟事件与真实浏览器行为分别记录，不声称真机。|
|A11 慢帧/长帧|30/60/120Hz render，注入500ms和20s主线程间隔，物理积压单列。|输入deadline取单调时钟；下一次处理最多结束当前窗口，新turn不被旧delta连跳；未追赶完不结算。|
|A12 重开/退局|准备/拖动/运动/飞分/pending处罚时Restart/Home；随后触发旧native/Tween回调及旧pointerup。|新round分数/棋盘只来自新局；退出不变分不换方；旧owner/token被拒绝。|
|A13 终态|冻结配置下179→199、同杆多人可归属事件、结果后timeout及回调、重复结果按钮。|>=目标只提交一个胜方/结果；不精确等于才胜；RESULT不再发射/换方/加分。女王pending另夹具。|
|A14 模式隔离|同配置索引进入local、AI、network、mode1女王路径，测计时门控和actor输入。|local Player2是人而非AI；network不套本地暂停权威；旧单人分值/目标不被静默替换。|
|A15 浏览器交付|桌面与手机viewport、中文locale，从最终dist真实点击Play/Pause/Resume/Restart/Home并完成shot及timeout。|默认英文/`lang=en`、坐标正确、控制台无错误、截图与事件日志保存evidence；不是只测源文件。|

后续代码/测试阶段需真实执行 `npm run build`、`npm test`、`npm run check`；check启动本地静态server访问最终dist，覆盖桌面/手机真实输入与截图并自动停止server。构建小于10MB、入口`dist/index.html`、资源包内相对路径，验证后不改dist；源码/试玩ZIP进releases、验收证据进evidence。**这里仅交接计划，本轮未创建测试脚本、dist、ZIP或evidence，不填写通过结果。**

## 6. 风险与未知台账

|ID|缺什么/当前证据|影响与闭合动作|状态|
|---|---|---|---|
|U01|O1视频与逐点采样表缺失，只转述。|补连续可视媒体与采样方法，才可独立复核边界、比分、输入、四袋及过渡。|NEEDS_CONTEXT，未闭合|
|U02|当前开发版身份、commit、源码/依赖包、R2实际文件哈希未知。|先冻结现版并diff历史；不按历史保护判现版安全。|NEEDS_CONTEXT，未闭合|
|U03|CarromDiscRules/Tweener/PIXI实际版本和正文未提供。|有效turnTicks、布局、分值、女王规则、delta裁剪与墙钟换算未知；取得依赖配置并测试。|NEEDS_CONTEXT，未闭合|
|U04|竞品输入重置、暂停、后台、超时罚分、网络权威未形成控制变量证据。|按同入口/场景/版本做连续实验；约15秒只保留假设。|NEEDS_CONTEXT，未闭合|
|U05|R2源文件绝对行号缺失。|本轮使用执行者选择的函数/局部摘录/字符窗口；取得完整带行号原文后再补绝对引用，不冒充用户确认。|NEEDS_CONTEXT，未闭合|
|U06|玩法逻辑专项Skill读取受限。|未采用该未读模块；下一轮若需要补选入口，本轮按已读总入口/全局证据方法分析。|BLOCKED，模块层未闭合|
|U07|准备回调未见完整turn保护；长帧catch-up上限本地未见；广告ticker交叉start。|静态风险，不是已复现bug；现版核owner/token并做A09/A11/A12。|NEEDS_CONTEXT，未闭合|
|U08|离线续杆、母球犯规、女王/耗尽平局规则、特殊计分不足。|项目夹具不能宣传为竞品真规则；模式内补样本并显式决定产品政策。|NEEDS_CONTEXT，未闭合|
|U09|15秒预算、准备不计时、pause原因集合、超时不罚分为项目建议。|实施前由产品选择并冻结rulesVersion；本轮未编造确认。|NEEDS_CONTEXT，待设计决定|
|U10|无当前可运行构建及目标设备性能证据。|不能报告加载、内存、包体、FPS/真机PASS；后续最终dist验收及设备采样。|NEEDS_CONTEXT，未闭合|

不因未知取消已可完成的报告分析，也不把引用格式缺口升级为无法交付；但不能将未闭合项隐去。

## 7. 本轮交付核对与限制

|项|本轮真实操作与结果|
|---|---|
|证据读取|R1完整文字读取；R2多窗口定位了回合计数、Tween延迟、原生match任务、输入与pause/restart/home/settlement锚点；没有把未见定义判为不存在。|
|间隔计算|15.6/15.2/15.6秒手算与首尾截断区分，非程序测速。|
|引用|附录局部L编号与原文摘录及实际读取窗口；源绝对行号U05未闭合。|
|设计|状态、输入边界、60Hz物理、碰撞/进袋一次事件、计分与胜负、UI英文和容差均为建议定义，不是实现结果。|
|文档产物|`/workflow/prototype.md`，写入后回读核对；保留既有工程，无源码或资源修改。|
|运行验证|未运行npm build/test/check、浏览器、竞品、ADB、Creator、Python采样或联网采集；本轮不适用成品验收。|
|阶段边界|仅prototype报告交付；不生成AI美术，不实现，不自行确认或推进下一阶段。|

## 附录：历史d201关键原文摘录（局部编号）

以下摘录保留原代码语义与混淆标识；为引用而添加的Lxx标签不是代码文件内容。跨摘录从L01重计。未显示的函数部分不以省略片段推断其不存在。

### E1 `_0x4bf21a`，R2 offset=252000, limit=12000

```text
L01 function _0x4bf21a(_0x55838a) {
L02   if (_carromMatchBlocked()) return;
L03   _0x990fb7 += _0x55838a;
L04   while (_0x990fb7 > 0x1) {
L05     (_0x990fb7--, _0x49d791(0x1));
L06     if (_carromMatchBlocked()) break;
L07   }
L08 }
```

### E2 `_0x49d791`内倒计时分支，R2 offset=216000, limit=24000

```text
L01 if (_0x3a1262 && (_0x408018 !== 0x0 || (_0x5d148e === 0 && !_0x183856))) {
L02   if (_0x1a373b > 0x0) {
L03     _0x1a373b--;
L04     _0x209883
L05       ? (_0x2cf38a["frame"][_0xcaac96(0x4b7)] =
L06           (_0x1a373b / _0x1f57de) * 0x64)
L07       : (_0x44d1ad[_0xcaac96(0x39a)]["value"] =
L08           (_0x1a373b / _0x1f57de) * 0x64);
L09     if (_0x1a373b <= 0x0) {
L10       _0x24bb4a();
L11       if (((_0x5d148e === 1 && _0x4268e2) || (_0x5d148e === 2 && _carromFreestyleQueenState.phase === "pending"))) {
L12         if (!_0x209883) _carromAiShotTurn = _carromTurnId;
L13         _0x5ebd99 = false;
L14         // Queue settlement for after pocket detection, including retry ticks.
L15         let _carromTimeoutTicket = {turn: _carromTurnId, round: _carromRoundId, armed: false, armWait: 4};
L16         _carromTimeoutReady = _carromTimeoutTicket;
L17         _0x338c29(function () { if (_carromTimeoutReady === _carromTimeoutTicket) _carromTimeoutTicket.armed = true; }, 0x32);
L18       } else if (_0x209883) _0x50a0ff();
L19       else _0x5e7a5f();
L20     }
L21   }
L22 }
```

L14是来源原有英文注释，不是本轮新增代码注释；本轮未修改代码。该函数开头原文门控（同一窗口、单独摘录）：

```text
L01 function _0x49d791(_0x2d8e89) {
L02   var _0xcaac96 = _0x157421;
L03   if (_0x3e61d0 || _carromHostPaused || _carromAdTokens.length) return;
```

### E3 `_0x338c29`，R2 offset=252000, limit=12000

```text
L01 function _0x338c29(_0x49a911, _0x3fc90b) {
L02   var _0x10b8c3 = _0x157421;
L03   var _carromScheduledRound = _carromRoundId;
L04   Tweener[_0x10b8c3(0x3a0)](
L05     {},
L06     {},
L07     {
L08       time: (_0x3fc90b / 0x3e8) * 0x3c,
L09       onComplete: function () {
L10         if (_0x3fddb3 && _carromScheduledRound === _carromRoundId) _0x49a911();
L11       },
L12     },
L13   );
L14 }
```

### E4 `_0x24bb4a`，R2 offset=108000, limit=30000

```text
L01 function _0x24bb4a() {
L02   var _0x53fb9f = _0x157421;
L03   ((_0xf86500 = ![]),
L04     (_0xc5bee4["visible"] = ![]),
L05     (_0x3a1262 = ![]),
L06     _0x1a373b - 0x1,
L07     (_0x44d1ad[_0x53fb9f(0x39a)][_0x53fb9f(0x4b7)] = 0x0),
L08     (_0x2cf38a["frame"][_0x53fb9f(0x4b7)] = 0x0),
L09     (_0x55e693 = ![]),
L10     _0x147a99[_0x53fb9f(0x12d)](![]),
L11     (_0x27e1b4["alpha"] = 0x1),
L12     (_0x27e1b4[_0x53fb9f(0x3f1)][_0x53fb9f(0x197)] = ![]));
L13 }
```

### E5a blocked/arm，R2 offset=252000, limit=12000（两个完整函数摘录）

```text
L01 function _carromMatchBlocked() {
L02   return _carromHostPaused || _carromAdTokens.length > 0;
L03 }
```

```text
L01 function _carromMatchArm(task) {
L02   var armVersion = ++task.version;
L03   task.due = _carromMatchNow() + task.remaining;
L04   task.handle = setTimeout(function () {
L05     if (task.version !== armVersion || _carromMatchBlocked()) return;
L06     task.handle = null;
L07     var index = _carromMatchTimers.indexOf(task);
L08     if (index < 0) return;
L09     _carromMatchTimers.splice(index, 1);
L10     if (task.owner === _carromActiveMatch && _0x423f7f && task.owner.parent === _0x423f7f.stage) task.callback();
L11   }, task.remaining);
L12 }
```

### E5b pause/resume，R2 offset=252000, limit=12000

```text
L01 function _carromPauseMatchTimers() {
L02   var now = _carromMatchNow();
L03   _carromMatchTimers.forEach(function (task) {
L04     if (task.handle === null) return;
L05     task.version++;
L06     clearTimeout(task.handle);
L07     task.handle = null;
L08     task.remaining = Math.max(0, task.due - now);
L09   });
L10 }
L11 function _carromResumeMatchTimers() {
L12   if (_carromMatchBlocked()) return;
L13   _carromMatchTimers.slice().forEach(function (task) {
L14     if (!task.owner || task.owner !== _carromActiveMatch || !_0x423f7f || task.owner.parent !== _0x423f7f.stage) {
L15       var index = _carromMatchTimers.indexOf(task);
L16       if (index >= 0) _carromMatchTimers.splice(index, 1);
L17     } else if (task.handle === null) _carromMatchArm(task);
L18   });
L19 }
```

### E6 `_0x5480e3`配置赋值片段，R2 offset=69000, limit=9000

```text
L01 ((_0x3a1262 = ![]),
L02   (_0x647bf3 = 0x4b + 0x19 * _0x2799f0),
L03   (_0x1a373b = 0x0),
L04   (_0x1f57de = window.CarromDiscRules.turnTicks(_0x5d148e, _0x408018, _0x3cbd63[_0x408018], _0x4bee00)),
```

### E7 `_carromFlushTimeoutAfterScan`，R2 offset=108000, limit=30000

```text
L01 function _carromFlushTimeoutAfterScan() {
L02   if (!_carromTimeoutReady) return;
L03   if (!_0x3fddb3 || _carromTimeoutReady.round !== _carromRoundId || _carromTimeoutReady.turn !== _carromTurnId) { _carromTimeoutReady = null; return; }
L04   if (_carromTimeoutReady.armed === false) {
L05     if (_carromTimeoutReady.armWait > 0) { _carromTimeoutReady.armWait--; return; }
L06     _carromTimeoutReady.armed = true;
L07   }
L08   if (_carromTimeoutReady.wait > 0) { _carromTimeoutReady.wait--; return; }
L09   if (_0x56abf7()) { _carromTimeoutReady.wait = 2; return; }
L10   var turn = _carromTimeoutReady.turn;
L11   _carromTimeoutReady = null;
L12   _0xbdafb3(turn);
L13 }
```
