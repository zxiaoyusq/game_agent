# Carrom 场馆入场扣费与离线异常审查

## 1. 范围、结论与证据等级

- 项目：ce8b6b311f5241e8946d186312bc41c1；阶段：prototype；attempt=1。
- 本次任务是两份参考 JS 的独立静态审查，不是新游戏设计、经济规则还原、引擎迁移或补丁实施。未修改参考源码，未推进美术、代码或测试阶段，未取得或编造用户确认。
- 结论：新入口显著改善参数校验、余额不足、同步重入和匹配对象存活期间的重复调用，但**不是扣费—存档—匹配启动的完整事务，也不是整个对局生命周期的一次性入场凭证**。
- 高优先级剩余风险：扣费后匹配构造/启动失败；匹配开始后的延迟旧选择再次扣费；存储部分写入与冷启动余额不一致；广告缺终态导致暂停无法释放。
- 所有下述发现均为“静态事实 + 条件路径推断”。真实运行复现：无；隔离故障注入复现：无；浏览器、真机、真实广告和离线存储验收：均未执行。运行安全结论为 **BLOCKED（缺运行上下文）**，不能把静态审查完成写成验收 PASS。
- 没有全文件机器 diff 或源码 SHA256 计算。因此“新增内容”仅指已对照入口和声明中的观察，不宣称两文件只有这些差异。参考路径中的长字符串不作为本次计算出的文件哈希。

## 2. 来源与定位索引

参考路径相对 ref/：

- R1：`mcp-inputs/mac-codex/b09fd8306a1ed77ffb6c57d93a4f6704e5f387a5c363a2cb17c94a66aaa68de5/arena-before.js`
- R2：`mcp-inputs/mac-codex/c617ab2f8c5077a7ff7128808cf06becab2d2fd1902507a1921f76191de501d6/arena-entry-guard.js`

下表范围是 read_reference 的读取窗口，不是精确函数起止行；函数名为稳定定位锚点，混淆字符串尚未全表解码。

| 证据 | 参考与读取窗口（offset/limit） | 锚点与用途 |
|---|---|---|
| E1 | R1、R2：0/24000及R2早期连续片段 | 配置、状态、初始化与存储字段 |
| E2 | R1、R2：90000/24000 | `_0x4d0a10` 前后入口、`_0x3153fe`、插屏及激励广告 |
| E3 | R2：68000/22000 | `_0x5480e3`、`_0x1260d2`、`_0x3846bf`、`_0x3771eb`、`_0x48e98f` |
| E4 | R2：113000/8000 | `_0x47e567` 基础奖励、广告奖励及结果返回 |
| E5 | R2：248000/15000 | 物理步进、输入拦截、广告 token、匹配 timers helpers |
| E6 | R2：383000/24000、397000/10000、407000/24000 | `_0x104b9b` 匹配构造、滚动、ready/start 动画链 |
| E7 | R2：407000/24000、431000/24000 | `_0x40d778` 选择卡片、`_0x22a07c` 选场事件转发与 setCoins/setEnable |
| E8 | R2早期读取及119000之后的已读玩法片段 | `_0x3a0318`、`_0x5ecd40`、game.resume/restart、player/AI turn 与结算保护 |

已实际读取本轮冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`；技能入口 `game-reverse-engineering/SKILL.md`（10.5.0），及 execution-protocol、global-rules、unknowns-ledger-template 配套文本。采用 owner 定位、事件提交边界、证据分级和未知清单的方法。专项 gameplay-logic-reverse 模块读取被权限拒绝，未声称采用其正文；下轮如需专项工具应补选该入口。

技术取舍：输入源码实际引用 PIXI、planck、GameSnacks、Howler、Tweener，以及 CarromDiscRules/CarromLocalSave 等外部全局。不能据本轮 Canvas 2D 资料宣称参考已是原生 Canvas、Cocos 或可独立构建工程。保留既有实现，不为静态审查强造运行壳。

## 3. 已改善的入口校验

变量：`_0xa07851` 为运行时金币；`_0x408018` 为场馆索引；`_0x1ac80c` 为费用/奖金配置；`_0x2e2e88` 为场馆状态；`_carromActiveMatch` 为匹配 UI owner，并非整局 owner。

旧入口只拦 `index >= states.length`，然后更新索引、决定先手、扣费、存储、申请广告、启动匹配。负索引、小数、字符串、余额不足、重复请求没有入口级完整校验；存储同步抛错会在扣费之后直接中断后续流程。

新入口按以下顺序执行（E2）：

1. pending 或 ActiveMatch 非空则直接返回。
2. 索引必须为整数、非负、低于状态数组长度，并有费用配置。
3. fee 必须为有限 number 且非负；coins 必须为有限 number 且 coins >= fee。
4. 设置 pending；更新场馆与先手；执行 `coins -= fee`。
5. 保存同步异常只 warning；继续申请插屏并调用 `_0x3153fe`。
6. finally 清 pending。

改善判定（静态，不是测试 PASS）：非法索引与非数值费用不会进入普通扣费路径；余额不足不扣费；等额余额允许入场；存储/SDK 内的同步递归入口受到 pending 拦截；ActiveMatch 存活时的第二次入口受到 owner 拦截。保存抛错不会像旧版那样必然阻止匹配，但此取舍没有解决持久化一致性。

局限：fee/coins 未要求整数或安全整数；`-0` 被当作0接受。是否必须整币是项目契约待确认，不当作已证实缺陷。入口不检查当前场景、是否对局中、选择请求代际、unlocked 状态或对应 `_0x2dad3f` 视觉配置。已读选场 `updateStates` 为空，卡片 setEnable 主要由显示余额决定，不能擅自设定场馆解锁政策。

## 4. 资金与流程风险表

优先级用于安排验证，非真实事故等级；示例统一 fee=50、初始 coins=100、无其他奖励写入。

| 编号 / 优先级 | 条件路径与静态依据 | 余额、流程后果及证据边界 |
|---|---|---|
| F1 / 高 | 扣到50并成功保存后，`_0x3153fe` 的构造器抛错（E2/E6）；例如缺视觉配置导致 loadTable 访问失败，或装备/资源调用失败 | 未成功启动却已扣50；主要旧场景已隐藏，ActiveMatch仍null，pending在finally释放。再次尝试可能再扣50。无自动退款或场景回滚。缺配置是否会在真实启动前先暴露，需运行验证 |
| F2 / 高 | ActiveMatch赋值后，stage.addChild、监听注册或动画链抛错（E2/E6） | coins仍50；owner可能非空而无有效start路径，此时后续入口一直返回。finally只清pending，不清owner；需有外部返回/清理才能恢复，不能假设玩家一定能触达 |
| F3 / 高 | start回调先清ActiveMatch，再removeChild或`_0x1260d2`抛错（E2/E3） | coins仍50；owner已空，局可能只部分初始化，重试可继续扣费。异步start失败不处在最初入口调用栈，入口finally不是它的恢复机制 |
| F4 / 高 | 匹配start成功后，延迟旧select或其他直接调用再次进入口（E2/E7） | pending=false、ActiveMatch=null，即使`_0x3fddb3=true`仍可再次扣到0并覆盖场馆、切回匹配。免费场馆不会丢金币，但仍可能替换当前局。普通隐藏界面的自然点击是否能产生此路径未复现；不要把事件重放推断成已观察到双击漏洞 |
| F5 / 高 | `_0x3a0318`先复制快照，再逐键storage.setItem；某键同步throw（E8） | 内存扣费、快照更新，磁盘可能全未写、coins已写或多字段部分写。入口继续匹配且无回滚。coins已写+启动失败形成持久扣费未开局；coins未写+冷启动可能恢复旧余额（不一定是资金丢失）；奖励写失败则可能冷启动丢奖励。实际重试/缓冲行为由缺失CarromLocalSave决定 |
| F6 / 高 | 插屏beforeAd已暂停，但只afterAd/viewed/dismissed或永无adBreakDone（E2/E5） | coins已扣；token仍在、匹配timers和物理推进被blocked，ticker可能保持stop。没有已读到的超时终态兜底。真实SDK是否保证done、断网时是否发生此序列未知 |
| F7 / 中高 | 插屏catch内`_carromAdResume`自身抛错；或后到done中resume/mute/ticker.start抛错（E2/E5） | 外围catch并非完整隔离；catch内resume无单独保护，异常仍能阻止随后的匹配调用。异步回调错不由原调用栈的try/catch自动捕获。resume先移token再syncMute，若后者抛错，timers恢复可能未执行；token清空也不代表已经恢复 |
| F8 / 中 | 进入匹配期间外部调用`_0x48e98f`（E3），没有取消/清空ActiveMatch | 选场显示但入口仍拒绝；原owner仍在stage时其timers/start可能继续导航。正常结果返回前匹配owner本已清空，因此不能把此条件风险说成每次结算返回都卡住 |
| F9 / 中 | `_0x3771eb`取消匹配timers并清owner，但没有显式移除匹配节点（E3/E6） | 旧start被identity拦截，改善跨场景误启动；旧节点/动画是否遮挡或残留取决于显示层清理，需截图/节点清点。取消timer不等于销毁整个匹配UI |
| F10 / 中 | 结果win加基础prize后，保存同步throw（E4） | 奖励已在内存，后续广告按钮及庆祝配置被中断。close监听已注册，不能断言结果必卡死；持久化奖励是否丢失待冷启动验证。resultCommitted阻止同局再次基础结算，但不是持久账本 |
| F11 / 中 | 激励广告show handle不存在时`_0x4d02b5`直接return；或afterAd没有viewed/dismissed即清callback（E2/E4） | 请求消费者得不到false终态；结果广告按钮隐藏后自动返回不发生。结果普通close仍可能可用，故更准确是广告流程无反馈/无法自动完成，不是整个游戏必然不可退出 |

补充：GameSnacks.storage.setItem若返回Promise拒绝或失败值，入口同步catch没有await也没有返回值判断，不能声称覆盖这些失败；该SDK实际返回契约未知。console.warn也不应被视为玩家可见恢复提示或可靠账本。

## 5. 广告与暂停归属

插屏入口没有传continuation，也没有await广告：广告请求返回后立即创建匹配。同步SDK throw在通常resume/mute均正常时，会warning并继续匹配，这是有益兜底；不等于“断网时广告一定安全”。

广告token去重、hostPaused以及timer版本控制是既有保护（E5）：

- `_carromMatchBlocked()` = hostPaused 或任一广告token存在。
- adPause加入token、清物理累积、暂停匹配timers并同步静音。
- adResume只移自己的token，全部阻塞解除后恢复timers。
- timer保存remaining；暂停/取消递增version；执行时校验ActiveMatch与parent===stage。
- 匹配startRoll约3000ms后stop；stop动画之后ready延迟免费1000ms、收费3050ms。收费/免费随后都依赖Tween发出start。这些是源码展示时序，不是经济规则证据。

因此旧timer跨owner执行受到保护；但晚到token不释放、timer恢复过程中抛错仍能阻断流程。插屏/激励终态有直接ticker.start调用，不能只凭timer被blocked就宣称host暂停或多广告重叠时所有渲染/动画也保持停止；应注入“一个广告结束、另一token或host仍暂停”，检查物理、timer、Tween、声音和输入分别是否推进。

## 6. 正常循环、规则状态与返回/重开

审查用状态链，不把它误称现有源码具有独立显式状态机：

`LOBBY → ARENA_SELECT → ENTRY_PENDING（扣费/保存）→ MATCH_UI → PLAYING（player/AI turns）→ RESULT → ARENA_SELECT`

- 入场成功判定：对应匹配完成一次start且棋盘可用；不是pending解除或存储调用没有throw。
- 入场失败判定：校验拒绝、启动链抛错或匹配未完成；后两者现有代码缺稳定失败状态。失败是否应退款、能否离线继续，以项目政策为准，本次只指出未成功开局而扣费的条件路径。
- `_0x5e7a5f`与`_0x50a0ff`开启player/AI turn、递增turnId；`_0xbdafb3`校验turn与settledTurn，等待运动结束并做单次结算；延迟回调带round/turn校验。正常换人、进球续回合或犯规处理不调用场馆入口，不应每回合重复扣费。
- 结果函数win加入该场馆prize；loss不加入基础prize。基础resultCommitted和广告bonusGranted分别去重。晚到旧广告成功会先加缓存prize，再检查round/UI来阻止旧导航；能加旧奖励是静态事实，是否应该禁止须确认，不猜竞品政策。
- 结果close回到选场，不直接重新走入场。随后合法新select会按当前fee再扣一次。
- `game.restart()`、`_0x3846bf()`直接调用`_0x5480e3()`，不走入场扣费。重开清瞄准/指针、pending处理、布局、计分等并roundId++。仅描述当前行为，不认定重开免扣费的经济设计正确。
- 直接restart在匹配中或结果UI尚存在时是否允许、是否清理所有UI，需要宿主契约和运行边界测试。

### 物理、碰撞、输入窗口与误差边界

本次不更改玩法；按品类要求保留审查基线（E3/E5）：

- 物理world.step每次传`1/60`秒及`10,10`求解参数，随后clearForces。ticker增量累计后在`while(accumulator > 1)`里逐步推进；不假设其等同严格墙钟60Hz。暂停条件阻止推进，快慢帧/大delta应回归验证，不新增求解算法。
- 已读入袋扫描对棋子中心到袋口距离采用`<=20`源码显示坐标单位；这是入袋判定，不是全部刚体碰撞半径。棋子碰撞细节由planck与缺失规则模块组合，未独立验收。
- 计分与局胜负由既有模式/规则模块、queen/犯规及结果调用决定；本次重点是不把同回合结算或UI动画误当新入场。完整各模式胜负公式未穷尽，不能用推测补齐。
- 输入在hostPaused、非运行局、非玩家阶段或其他已读阻塞flag下返回；重开会清旧瞄准pointer，防止持有指针射入新局。场馆入口没有同等的PLAYING/请求代际检查。
- 金额、扣费次数、奖励次数、round/turn身份的可接受误差为**0**；timer不可消耗暂停时长；跨代际不允许提交旧启动/旧回合结算。物理位置/碰撞数值容差未获得现有项目验收契约，不编造阈值。建议同版本、同输入和固定步数先确定基线，再量化容差；袋口20附近测试19.99/20/20.01（只作测试点，不把0.01定义为许可误差）。

## 7. 界面布局与英文文案约定

保留既有界面，不生成新图片或新UI。选场为教程卡+五个场馆卡的横向排列，顶部余额和Back，下方商店/教程入口；场馆卡显示fee/prize与Select；匹配包含双方头像、奖池与先手动画；棋盘显示双方分数/奖池；结算有普通关闭/领取与可选Claim x2。

当前仅从源码布局读取，未读取所有文字贴图、未看到实际页面，不宣称截图一致或默认语言验收通过。若后续授权增加玩家可见兜底，本轮默认英文候选文案为：`Select Arena`、`Entry Fee`、`Prize`、`Not enough coins.`、`Unable to start the match. Please try again.`、`Progress could not be saved.`、`Ad unavailable. Continue without bonus.`、`Back`、`Retry`。这些只是建议，未集成；后续独立英文Web页面需lang=en，中文浏览器不切换默认语言。

## 8. 边界测试矩阵（待执行，不是测试结果）

统一观测：每次记录运行coins、snapshot.coins、真实storage.coins、写键顺序/错误、入口调用计数、匹配构造与start计数、ActiveMatch/parent、round/turn、token/timer列表、ticker、可见UI和控制台。固定随机输入或种子；故障注入stub只能证明隔离路径，真实SDK、浏览器自然输入和冷启动另测。

### A. 配置和资金

| 场馆索引 / 源码配置名称 | fee | prize | 余额测试点 |
|---|---:|---:|---|
| 0 / Delhi Lounge | 0 | 50 | -1、0、1 |
| 1 / Golden City | 50 | 125 | 49、50、51 |
| 2 / Mahal Palace | 200 | 400 | 199、200、201 |
| 3 / Mumbai Plaza | 750 | 1500 | 749、750、751 |
| 4 / Royal Arena | 5000 | 10000 | 4999、5000、5001 |

- 所有行先确保其他入口条件有效：不足拒绝、等额扣至0、充足扣一次fee。免费且coins=0接受；负余额及NaN/Infinity即使免费也拒绝；fee=0仍会保存/广告/匹配，不是跳过异常路径。
- 索引：-1、0、4、5、大整数、0.5、字符串`"1"`、null、undefined、NaN、±Infinity、对象、-0；拒绝时所有余额、场馆、先手、存储和SDK调用应不变。
- fee：负数、NaN、±Infinity、字符串、undefined、0、50、小数、MAX_SAFE_INTEGER以上；coins同类。有限小数按现代码接受，安全整数溢界也未拦，期望应分“现实现行为”和“待确认整币契约”。
- 缺费用配置、缺视觉配置、数组长度不一致、locked/unlocked：记录拒绝/构造异常与余额；解锁期望待确认。

### B. 重复、重入、owner与场景

1. 同一调用栈内，让save和SDK同步再次调用实际入口：只允许外层一次扣费/一次构造。
2. 首次返回后、匹配start前重复select：ActiveMatch正常时拒绝。免费也只允许一个匹配。
3. 匹配start之后重放旧select；对局中直接调用入口；不同场馆的旧select；结果未关闭时旧select：重点核对F4。用隔离事件重放和真实鼠标双击/手机多指各做一份，不混证据。
4. 重复ready/start、被取消旧owner的start、旧timer到期、owner不在stage：不得重复启动新局或再次扣费。
5. 匹配时返回选场/大厅、再进入；检查owner/timer/旧节点和Tween清理。构造前、赋owner后、addChild后、on注册时、start的removeChild和局初始化分别throw：余额与失败恢复须逐点记录。

### C. 存储与冷启动

1. 对实际存储写入第一个键、coins键、coins后键、最后键分别throw；记录快照已改变到哪个阶段，匹配是否继续。
2. 测 quota/访问禁用/getItem throw/损坏JSON/recover失败；启动余额以真实恢复实现为准。
3. 若SDK支持，注入静默失败、失败返回值和异步reject，监测未处理拒绝；不预设同步catch能捕获。
4. 每个点在扣费后、匹配失败后、奖励后立即关闭/冷启动；对比磁盘余额。resume.flush失败/重试成功、下次save成功、断网恢复分别测。
5. 完整保存成功后制造匹配失败，是验证“已持久扣费未开局”的优先案例。未写coins恢复旧余额应报一致性问题而不是错称丢金币。

### D. 广告与暂停

1. 插屏申请同步throw（beforeAd前/后）、无广告正常done、beforeAd→done、done重复、done→迟到beforeAd。
2. beforeAd→afterAd但无done、beforeAd→viewed/dismissed但无done、无任何终态；观察匹配和可返回能力。
3. 广告回调中的syncMute/resume/ticker.start分别throw；含异步回调和SDK吞异常，验证外围catch边界。
4. 两广告token重叠、一广告结束host仍paused、host恢复另一广告未结束：分别核验声音、输入、物理、timer和动画。
5. 激励未ready/handle已消费、show throw、viewed/dismissed重复与乱序、afterAd缺奖励终态、旧generation晚到、结果close/重开后成功晚到；奖励最多一次，不能旧导航。旧奖励是否应入账按确认政策验收。

### E. 正常局与回归

- 三模式×免费/收费场馆：正常入场、player/AI轮换、进球续回合、无进球换人、犯规、胜/负、结果close→再选；每次正常回合金币不因入场逻辑变化。
- 基础结算重复与加倍结果重复分别仅加一次；奖励保存throw之后普通close仍可用性需真实点击确认。
- game.restart与UI restart前后余额按现实现不变，roundId递增；持有pointer重开、匹配中restart、结果中restart单测并记录契约缺口。
- 固定步数下30/60/120Hz、大delta、暂停/恢复、袋口阈值、同回合timeout/入袋同帧：确认没有额外入场、跨代际结算或暂停时间消耗。物理容差待基线确定。

## 9. 建议方案与验收条件（未授权实施）

优先建议，而不是本次已经修改：

1. 为合法选场请求建立requestId/scene generation，与整个入场/局生命周期的owner绑定；只有可接受选择的场景能提交。pending用于同步重入，不能替代请求幂等。
2. 区分余额预留、持久提交、匹配构建成功和对局启动；全链配置预检与统一失败处理。不得简单catch后重复扣费，也不得无账本地“退款一次”而产生重复退款。
3. 明确本项目保存失败政策：禁止开局、离线待同步继续，或其他策略。异步/静默失败须按SDK契约处理；逐键存储需恢复/事务记录，否则内存回滚也不能保证磁盘回滚。
4. 统一导航时清理owner、timer、Tween和节点；start成功提交后再释放哪些锁要有明确状态。取消后旧请求、旧start与旧结算无权操作新局。
5. 广告失败与缺终态应有一次性消费者、可见兜底与暂停归属恢复；超时阈值依SDK契约确认，不照抄案例值。不允许fail silently吞掉领取请求。
6. 保存入口与奖励有不同异常处理，建议按同一持久化策略收口并保留诊断信息。

后续通过条件：拒绝请求不产生副作用；一个合法入场最多扣一次；任何失败不会永久卡owner/token且有玩家可触达退出/重试；持久余额与已确认提交策略一致；自然输入与故障注入分层覆盖；正常回合不重扣；旧owner不能启动/导航新局；经济与退款规则只按本项目确认契约验收。

## 10. 真实验证结果、未知项与交接

真实执行：只读参考与冻结资料、静态调用链对照、写入本报告并回读。没有执行脚本、npm构建/测试/check、浏览器或真机，没有发布dist/试玩ZIP。当前是审查原型阶段、无可运行工程及完整SDK/资源，不为满足后续代码阶段门禁创建虚假构建。上述所有边界测试均未执行。

未知清单：

- CarromLocalSave的recover/flush/缓冲与实际存储接口契约；CarromDiscRules等外部规则实现。
- 原始HTML、完整依赖/资源、真实GameSnacks广告宿主及断网回调序列。
- 场馆状态政策、整数金额/上限、未成功开局/主动退出/重开的扣费与退款契约。
- 自然双击/多指是否能触达匹配后旧select；旧节点实际遮挡、完整碰撞容差及各模式胜负规则。
- 全文件精确diff与哈希、运行脚本、浏览器/真机/evidence尚缺；本报告不替代其验收。

这些缺口不阻止提出静态审查结果，但阻止运行安全判PASS。若后续要实施事务/退款或修改广告策略，应先通过request_user_input确认重大取舍及补齐运行材料；本轮不自行选择或推进。

交付产物：`/workflow/prototype.md`。无源码改动、无新增资源、无Skill更新。
