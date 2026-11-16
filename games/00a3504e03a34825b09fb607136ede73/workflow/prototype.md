# Carrom 最新规则模块与结算一致性：只读审计

本轮阶段：prototype；attempt=1。仅写本报告，不改游戏源码、资源，不创建新游戏。结论等级为静态源码分析与人工路径推演，未执行 JS、浏览器、构建、单测或真机复现；下文触发顺序是复现用例，不能视为已运行的测试。

## 输入与引用约定

E1：ref/mcp-inputs/mac-codex/1ebfc85e4d69a64bbe67b3e0e7877dbfb0f04c6466493bc0b033b3249c514a93/Carrom_current_1ebfc85e.js。已从字符偏移0开始，以24000字符连续分页读到552000之后的文件结束。

E2：ref/mcp-inputs/mac-codex/080bc7b20fc83732926bfce6785481287f93b63ac97735df9f8eaef7a0a6fb71/Carrom_disc_rules_current.js，已全文读取。

E3：ref/mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip；工具返回归档SHA256为ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1，35条目。实际读取report/竞品_ARM64代码定位.md、analysis/native_击球消息线格式候选.json、disassembly/09_queenCovered_1aa3458.txt，未解压整个工程。

read_reference返回正文不带源码行号，故引用以真实分页字符区间、唯一函数名和原文锚点联合定位；不编造行号。以下字符区间为检索范围而非精确语句起止。E1/E2路径中的哈希段只作输入身份标识，本轮未另行计算文件哈希。

读取了选定Skill入口、execution-protocol、global-rules、unknowns-ledger-template及全部4份冻结品类/框架资料。Skill的modules/gameplay-logic-reverse/SKILL.md被工具拒绝，未声称读取成功。

## 模式、状态与完整规则消费链

大厅_0x28bd7a的按钮事件明确映射Disc Pool=0、Carrom=1、Freestyle=2（E1[408000,456000)）。_0x48e98f写入模式_0x5d148e；选桌_0x4d0a10写入_0x408018，扣入场费后进入_0x3153fe；匹配结束调用_0x1260d2，再调用_0x5480e3初始化。

关键owner：_carromRoundId为局代次，_carromTurnId为回合代次；_carromSettledTurn防重复结算；_carromResultCommitted防重复结果奖励；_0x209883=true为玩家行动；_0x55e693为玩家可操作；_0x530863为本杆犯规；_0x5ebd99控制续杆；_0x4268e2为普通模式皇后待覆盖标志；_carromQueenClearedThisShot记录本杆清除该标志；_carromFreestyleQueenState另存board/pending/covered与owner。

盘面数组：_0x3e4566玩家白子、_0x2a9c75对方黑子、_0x3231b3皇后、_0x31089b待结算入袋队列；_0x4d3bf1和_0x41f634分别为双方计数/积分。E1[120000,168000)、[456000,480000)。

### E2逐函数核验

|函数|真实语义与输入|E1消费者|
|---|---|---|
|私有isSixDiscDelhi|严格mode===0且table===0|target、layout、turnTicks内部调用，不导出|
|target(mode,table)|仅Disc Pool Delhi返回6，其他均9|_0xd3d8fe初始化双方棋子数量|
|layout(mode,table)|仅上述组合返回双方各6个点；其他null|_0xd3d8fe选择新布局或原9子布局|
|turnTicks(mode,table,originalTicks,timeBonus)|上述组合1200，否则原桌时长；再加timeBonus*2|_0x5480e3写_0x1f57de；双方回合起始均复制此值|
|hasWon(mode,table,count)|count===target，严格等于|_0xbdafb3普通分支终局条件及行动方胜负分支，多次调用|
|freestyleQueen(previous,shot)|pending要求同owner、非犯规、ordinary>0；否则回盘撤分；board且queen且非犯规按ordinary决定同杆covered或pending；covered不撤销|_0xbdafb3 Freestyle延迟提交分支，先提交计分回调，再消费决定、回皇后、更新状态、判胜|

以上是完整E1中CarromDiscRules显式调用集合：初始化调用turnTicks一次、layout一次、target一次；普通终局表达式调用hasWon四处；Freestyle调用freestyleQueen一处。AI不直接调用E2，以初始化后的数组和模式分支消费其结果。

E2的UMD先factory，再在CommonJS环境设置module.exports，否则设置root.CarromDiscRules；非浏览器root为globalThis，浏览器为window。E1全部按window.CarromDiscRules同步读取，无缺模块回退。提供的材料没有HTML和加载器，无法证明实际加载顺序、script类型或混合CommonJS环境是否使window缺失。导出函数本身未见命名不匹配。

合法输入契约由调用方保证：mode/table为数字，count为数字整数；E2不校验。字符串'0'不会命中六子规则；turnTicks缺参会产生NaN或字符串拼接；freestyleQueen缺shot会抛错。这些是接口边界，不据此指称真实玩家可触发漏洞。E1正常消费者传内部数值和构造shot。

### 回合、入袋、提交与AI

玩家：_0x5e7a5f递增turn、清foul/续杆标志、设置sensor并动画摆杆；_0x36ab44接收指针身份→_0x536112计算力度角度→_0x1e39ba松手以strength>=0.25发射→_0x24bb4a关闭操作/计时→_0x338c29约2300ms后调用_0xbdafb3(原turn)。

AI：_0x50a0ff递增turn并重置杆状态→约500ms后从四角_0x52106f/_0x25af2a/_0x521eef/_0x30849b生成候选→校验finite、基线、阻挡→按hDot排序→_0xd6b627→_0x4662ac移动→_0x223471瞄准→_0x4b3cc6二次检查盘面和位置并出杆→同样延迟结算。无候选走_0x3d12d7；基线不可用或重试耗尽，待覆盖时走空杆结算，否则直接交给玩家。_carromAiShotTurn防重复发射，_carromAiRetryCount限制重规划两次；快照按对象/分组及每轴>1画面单位判断变化。AI的普通模式目标为黑子；剩1黑且皇后仍在盘则优先皇后；Freestyle两色和皇后都作为目标，没有按pending覆盖状态重新评分候选。

帧循环：_0x4bf21a累加ticker增量，while(accumulator>1)调用_0x49d791(1)。每tick先更新动画/回调，再计时、扫描striker→皇后→白子→黑子，flush超时票据，最后world.step(1/60,10,10)与clearForces。入袋阈值为中心距离<=20画面单位；_0x54e9a5子半径16，striker实际半径34*0.8*0.8=21.76。物理比例100画面单位/世界单位；trimVelocity以|vx|+|vy|<0.2进入睡眠。没有显式补步上限。

_0xbdafb3先检查期望turn/已结算turn/超时票据及active，运动未停每50ms重试；停球后标记settledTurn并睡眠全部对象。普通模式按颜色计数；本方及皇后犯规回盘、对方子仍可记给对方；按hasWon判终局后才处理失败覆盖回盘与换手。Freestyle非犯规按type0/1/2分别50/20/10分记给行动者，犯规本杆入袋全部回盘；历史扣分只在本杆队列为空时尝试。普通动画计数与Freestyle飞分都有一次性finish，并在判胜前补交延迟回调。

Freestyle shot由结算时队列构造：actor=当前行动方，foul=本杆striker入袋标志，queen=队列是否有_type0，ordinary=队列_type1/2数量。它没有物理碰撞顺序、首碰对象等输入。终局为非pending且任一分数>=160，双达标时当前行动方优先。普通终局为任一count恰等target，若行动者自己恰达标且皇后数组空则行动者赢，否则对手赢。

## 可构造错误与设计差异

### F1：Carrom同杆覆盖取决于入袋先后，存在同一shot内容的不同结算（FAIL，静态逻辑反例）

引用：E1 _0x49d791皇后与两色扫描，范围[192000,264000)，锚点皇后入袋`(_0x4268e2 = !![])`；任一普通子入袋`(_0x4268e2 = ![])`。_0xbdafb3普通分支[144000,168000)以`_0x4268e2 && !_0x5ebd99`决定回皇后。

最小顺序A：mode=1、双方均有多子、皇后在盘、非犯规。玩家本杆先入1白；在后续tick再入皇后；不再入其他子。白入袋时标志false，皇后稍后设true；两次均设续杆true，结算不回皇后，进入下一杆时仍pending。下一杆空杆会回皇后。

对照顺序B：相同起始计数、同杆先皇后后1白。皇后设true，白子清false；下一杆空杆不会回皇后。二者同杆都入皇后+本方普通子、同样无犯规，却产生不同后续状态。若同一tick同时跨入袋阈值，固定先皇后后普通子的扫描顺序又将结果归到B。

影响：玩家无法只凭本杆入袋内容预测是否需再覆盖；后续末子胜负可受影响。产品是否允许同杆覆盖需确认，但当前实现无显式时间顺序规则且两种效果不统一。不能依据native键名决定A/B哪种才符合竞品。

### F2：Carrom对方颜色能清除皇后待覆盖，皇后可无本方覆盖而保留（FAIL状态归属不完整；正确产品罚则NEEDS_CONTEXT）

引用同F1，两色的`_carromQueenClearedThisShot = ... (_0x5d148e === 1 && _0x4268e2)`均不检查行动者和颜色；续杆的设置却检查颜色归属。

触发：玩家合法只入皇后→结算续杆且pending→下一杆仅入1黑、不犯规。黑子清pending，但不为玩家设续杆，停球后皇后不回盘、黑子计给对手并换手。皇后数组空，后续玩家清完白子可满足终局皇后条件。对称情形AI仅入白也成立。

与空杆对照：pending后下一杆无子入袋会回皇后；仅入对方子反而免回盘。UI check_filled也由任意颜色触发。代码没有皇后owner可再核对。能证明实现差异和状态缺口，不能在缺产品规则时冒称已违反竞品正式规则。

### F3：Carrom同tick清空双方末子，后扫描黑子不入队，黑子永久少计（FAIL，影响胜负）

引用E1 _0x49d791白/黑扫描[216000,264000)：白子先从_0x3e4566移除，随后`if (_0x5d148e == 0x1 && !_0x2a9c75.length) {} else _0x31089b.push(...)`；黑子对称检查白数组。removeFromWorld实际destroyBody且body=null（_0x54e9a5，[456000,480000)）。

最小局面：mode=1、双方各剩1普通子，计数8:8，皇后已合法覆盖并离盘；同一个扫描tick白黑末子均在任意袋中心20单位内，无striker犯规。

执行：先扫描白，黑数组非空，白移除并入队；再扫描黑，白数组已空，黑移除但不入队；结算只增加白方至9，黑方仍8。双方盘面都已无普通子，计分只承认白。若当前是AI回合，普通终局分支仍判玩家赢。

这是确定的扫描顺序偏置：黑子已从物理世界和盘面数组删除，空分支没有恢复、计分或直接结束逻辑。产品对双方同杆清台如何裁决未知，但漏掉已入袋对象的事实无需依赖竞品。

### F4：Freestyle历史罚则只允许一条记录，多得一次分即可免除这项扣回（NEEDS_CONTEXT设计政策，差异可静态确定）

引用E1 _carromFreestylePenalty[120000,144000)：`matches.length !== 1`立即false，且score必须严格等于该条points，类型只能1/2；_0xbdafb3仅在`_0x530863 && _0x3daed1.length === 0`调用。

顺序A：本局玩家只成功入1白得20分→续杆仅striker入袋、无其他子→history恰1条且score20，扣20并回1白。顺序B：成功入2白累计40（可两杆各1白）→相同仅striker犯规→history为2条，直接不罚、不回历史子。另一个开关：在犯规杆同时入任意普通子时，队列非空，只回本杆子而不调用历史罚则。

玩家体验：犯规后旧得分是否减少取决于历史条数和本杆是否另有入袋。这里明显不是通用“取最近一子”算法，而是狭窄白名单。缺正式产品罚则，不将其直接定性为需扩展扣分的bug；应让产品明确这是刻意的单记录保护还是遗漏。

### F5：restart未清理正在进行的瞄准，旧指针能在新局提交旧力度（FAIL，输入局生命周期）

引用E1公开restart直接_0x5480e3（[0,24000)）；_0x5480e3[48000,72000)重置round、队列、分数并隐藏_c5bee4，但未写_0xf86500、三个_carromAimPointer字段、strength或调用_carromCancelAim。_0x1e39ba[144000,168000)只校验pause、aim与指针身份，不校验开始瞄准时的round/turn；在松手时才捕获当前turn。

最小条件与顺序：已完成教程、玩家回合；按住striker拖到strength>=0.25且不松手→外部宿主调用公开game.restart()→若新局玩家先手，新局_0x55e693和_0x209883重新true→原指针松手。旧aim标志/identity/strength仍在，松手在新局发射，使用新turn调度结算。若不松手继续按，新pointerdown又因aim仍true被拒。

这一触发依赖宿主在按住期间调用公开restart；材料未给宿主调用点，不能声称普通菜单必然提供该路径。公开API状态转换本身可构造；需用宿主或调试调用动态复核。

### F6：终局只防重复奖励，未关闭对局状态（FAIL终态封锁不完整，后续影响需动态复核）

引用E1 _0x47e567[96000,120000)设置resultCommitted=true并显示遮罩/结果，但不设置_0x3fddb3=false、不清计时/输入、不在_0x49d791扫描入口检查resultCommitted；_0xbdafb3也只查active和turn。

普通正常出杆已通过_0x24bb4a关闭玩家输入/计时，且本杆结算去重，这能避免把该项夸大成正常路径必然重复发奖。较直接的可构造入口是公开game.test()：它无前置判断调用_0x47e567(true)并return；在玩家可瞄准回合调用后，active、玩家许可和计时仍在。若对外暴露该调试API，程序化指针事件/其他既有回调仍可能推进回合，结果面板展示计数与底层后续状态可分离。自然玩家输入能否穿透遮罩未验，不作确定结论。

## 已存在的保护、非缺陷与重要未知

1. reset递增round，清timeout/history/FreestyleQueenState/resultCommitted，丢弃pending罚子和皇后动画，提取striker/aim Tween，重建数组。不能把“没有清turn至0”单独定为错误：turn单调增加，配合round能隔离旧回调。
2. _0x338c29用round与active门禁；计分finish再验round+turn且有finished标志；AI移动/瞄准/出杆及timeout票据也有代次检查；_0x47e567防基础奖励重复。这些是静态保护证据，未执行压力验收。
3. 普通罚子_0x464a16先立即减分，动画完成再建刚体，存在短暂计分/盘面过渡；不要把该动画过渡本身称为守恒漏洞。Freestyle罚子另有pending等待和20次轮询后的finish。
4. E2 hasWon严格等号在正常Disc Pool计数不超过初始目标的前提下合理；没有证明可达超额计数，不能只凭===报告“超过目标不赢”。
5. Freestyle pending会暂缓所有>=160终局，queen覆盖失败先撤50再判胜；同杆覆盖明确是E2注释中的产品假设。covered后普通犯规不撤皇后；这些都需产品政策，不能从通用Carrom惯例判错。
6. turnTicks的timeBonus*2单位是tick，非秒。例如timeBonus=1只加2/60秒；双方共用玩家装备计算出的时长。代码事实明确，但是否应加秒、是否应对AI对称未知。Delhi table0的Carrom/Freestyle计时条件不启用，因此“有turnTicks值”不代表所有桌实际倒计时。
7. 玩家初始摆杆15tick时已经开放_0x55e693，_0x36ab44没有摆杆完成门禁；后续可能与worldX/worldY Tween竞争。需浏览器真实输入验证，不声称已发生轨迹错误。
8. 玩家与AI发射的最低力度政策不同：玩家要求>=31.25；AI只检查finite，候选力量按路径距离计算且瞄准显示将strength上限钳1，实际发射_0x3e3780未随显示钳制。需具体可达候选与力度产品限制再定性，不能将potential大于125视为已复现作弊。

## 竞品native证据边界

E3中report/竞品_ARM64代码定位.md自身标为候选。对应库身份为libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so、AArch64、报告记录ELF SHA256 4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4。本轮没有原库，不能重新验证该哈希或输入与当前H5的版本谱系。

实际读取queenCovered候选：link VA 0x1aa3458–0x1aa38b8，0x1aa3708 ADRP和0x1aa370c ADD定位键字符串，前面有循环/比较，之后有若干BL。可证明这份反汇编包含该键相关地址计算及条件计算；不知道各调用者和被调用函数语义、结构字段含义、枚举值、事件读写方向及运行可达性。不能将w23、某offset或字符串queenCovered直接等同本JS的_0x4268e2、freestyleQueen状态或覆盖算法。

击球线格式候选只列protobuf式tag：1/2、2/1、3/1、4/0、5/2、6/0（field_number/wire_type）。候选文件明确未验证field names或behavioral semantics，不能据此命名为角度、力度、罚则或queenCovered。MatchShotSolver/physicsStopped的短FDE类型名线索也不能当AI或停球规则实现。

缺运行证据时，native材料无法决定：同杆覆盖是否成立、是否要求本方颜色、末子与皇后组合判负、striker罚分/回子顺序、Freestyle目标与pending终局、Delhi六子与20秒时长、AI精度/力度。上述F1–F6是当前JS内部审计，不以竞品候选为规则权威。

## 后续最小验收条件（本轮未执行）

规则回归需直接加载实际E2并从E1真实调用边界记录round/turn/actor、盘面各数组长度、入袋队列、两方score、皇后owner/phase及resultCommitted。依次覆盖F1两种先后及同tick、F2玩家/AI镜像、F3双方末子同tick及异tick、F4一条/两条历史及犯规同时入子、F5按住跨restart。必须区分注入局面测试与真人可操作轨迹。

计数与状态判定零容差；物理到达可用入袋阈值内外小量偏移构造，但不能将20单位判袋半径称为通用可接受误差。帧率比较需固定物理tick与输入序列，并记录实际库版本；长帧补步、暂停/恢复和多次重开需另验。默认界面语言本轮不改，未读取图像文字，不能声称已验证英文界面。

## 未知清单与交付

|编号|未知项|还缺什么|当前证据|状态|
|---|---|---|---|---|
|U01|F1–F6真实运行效果及自然轨迹可达性|当前完整H5依赖、宿主、真实执行环境及复现记录|E1/E2静态路径|未闭合|
|U02|皇后覆盖、罚则与双清台正式设计|产品规则或匹配竞品版本的运行观察|E2产品假设注释；E1差异|未闭合|
|U03|E2实际加载顺序及全局导出环境|HTML/打包入口和加载日志|E2 UMD；E1 window消费者|未闭合|
|U04|native字段业务语义与完整owner|匹配原库、函数体/结构映射、运行观测|E3候选报告/反汇编|未闭合|
|U05|宿主何时调用公开restart/test|宿主源码或调用日志|E1公开API|未闭合|
|U06|玩法Skill子入口|下轮选入该入口或修复归档访问|本轮工具明确拒绝|未闭合|

产物：/workflow/prototype.md。验证：完整静态读取及逐分支人工推演；未调用run_validation，未执行npm run build/npm test/npm run check。当前为只读原型审计，工作区初始ls('/')为空，没有可构建项目；不为审计创建假构建和测试。未生成试玩包、图片、截图或发布包。游戏源码与资源未修改，不推进美术、代码或测试阶段。
