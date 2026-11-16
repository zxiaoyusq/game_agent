# Carrom Freestyle 红棋与罚则依赖复核

项目：531d306b87bc430487cc27cdbf2af234。阶段：prototype，只读静态审查。人工确认模式：autonomous=false。本轮没有修改游戏实现、依赖或资源，没有创建新游戏，没有推进美术、代码或测试阶段。

## 1. 结论与边界

1. 当前完整 JS 真实调用上传依赖 `window.CarromDiscRules.freestyleQueen`，实现 `board → pending → covered`。单独红棋先入账50分，下一杆同一方非犯规进任意普通棋才完成覆盖；否则撤销红分并返红。单杆红+普通直接覆盖是源码明确标注的**项目假设**，不是已证实的竞品事实。
2. 犯规优先于本杆计分：本杆队列非空时全部返场、不给本杆分；只有队列为空才尝试历史罚棋。该罚棋仅接受“本轮本方全部历史为同一种普通棋、同一正有限分值、分数精确匹配历史构成”。多颗历史也只扣/返一颗，不支持混色、含红或欠罚。
3. 高关注规则缺口：covered 红历史会挡住一般罚棋，而 covered 状态不会撤红。因此已覆盖红棋后空杆母球犯规，按当前正常账本条件可能分数完全不变。另一个待确认策略是“本杆进子+母球犯规只返本杆子，不额外罚历史子”。这里没有将规则偏好判作已复现程序故障。
4. 延迟边界先等罚棋、强制完成返场/积分，再做红覆盖或撤分，最后判160分终局。pending 状态阻挡任何一方终局；双方同时达标时当前出杆方胜。这些均是当前项目策略。
5. 真正的 Tweener 是逻辑tick调度而非简单定时器，同target替换取消旧 completion，live数组移除可能令后续tween本tick跳过。当前积分/返场一次完成标志及边界finish兜底有意义，但不能仅靠替身测试证明真实时序可靠。
6. 上传的 `freestyle-full.diff.txt` 实际只有母球罚则一个hunk，不能证明包含红棋状态机、回滚和迟到积分的全部改动。历史“红50后空杆仍50”是旧开发版受控浏览器记录，不能用来反驳当前pending实现。

**验证状态：完成参考正文静态阅读及调用链复核；动态结论全部未验证。没有执行 npm run build、npm test、npm run check、VM、浏览器、真机、宿主或竞品对局。以下测试是可执行复现规格/待执行代码，不是测试结果。**

## 2. 输入与证据索引

所有路径相对工程 `ref/`；不将目录名中的哈希当作上传文件正文哈希。

|编号|真实输入路径|本轮采用范围与限制|
|---|---|---|
|E1|`mcp-inputs/mac-codex/31000435a09f059b10e61a82cd31930e4255c7658fbd6c75bb9d1c487e78178f/Carrom_fallback_current.js`|完整读取到EOF，主调用链、物理扫描、棋子/母球类、HUD、完整Tweener及字符串表。没有计算正文SHA256，不提供臆造行号。|
|E2|`mcp-inputs/mac-codex/080bc7b20fc83732926bfce6785481287f93b63ac97735df9f8eaef7a0a6fb71/disc-rules.js`|全文，UMD导出及真实freestyleQueen依赖。|
|E3|`mcp-inputs/mac-codex/acfe600b37eac8f3e25c9c670ecdd57d528f43499d851ebbeda4006a28e8692d/freestyle-full.diff.txt`|全文仅一个hunk，标头before-98cdce5f.js / after-49f30646.js，hunk原文为@@ -3325,10 +3325,12 @@。这里的行号属于diff基线，不冒充当前E1行号。|
|E4|`mcp-inputs/mac-codex/b6eaf03a683f18bb120a4ccf37ff801d0b4f583d7fb5462d2b667d1c2e4f6bca/freestyle-evidence.md`|全文历史证据摘要。其底层脚本、输出JSON、视频本体没有作为本轮输入得到核验。|

E1按字符连续读取区间：0–24000、24000–84000、84000–144000、144000–204000、204000–264000、264000–324000、324000–384000、384000–444000、444000–504000、504000–564000；564000起读返回空。区间是工具请求范围，末段可能不足请求长度，并非精确文件长度。复核追加84000–126000、126000–160000，后一区含罚则、返红和结算完整核心。本文用函数名和短表达式定位，未声称对正文计算哈希或生成准确行号。

### 2.1 方法资料

已读本轮冻结总入口 `game-reverse-engineering/SKILL.md`，采用真实符号、owner、回合隔离与提交边界的取证方法；配套已读 `references/execution-protocol.md`、`references/global-rules.md`、`references/unknowns-ledger-template.md`。尝试读取 `game-reverse-engineering/modules/gameplay-logic-reverse/SKILL.md` 被工具拒绝（入口未选中），不声称使用其正文；本轮没有因此扩大技能范围。

已实际读取四份冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。以动作/结算一致性、固定步长、状态与表现分离、跨局回调隔离组织审查。配置框架为Canvas 2D，但E1真实实现为PIXI + Planck（box2d=planck）；本轮只记录该差异，没有迁移引擎或伪造Canvas重建。

### 2.2 历史版本对账

|历史版本/来源|E4记录的证据|可以说明|不能说明|
|---|---|---|---|
|基底SHA `2a036140fcf41e307b604373d307ff4014d061eef4bee5fb9504b90424b3460e`|人工VM提取callback，强制旧红flag=true且续杆=false；英文globals缺失时ReferenceError，提供globals则改英文变量而非真实混淆分数。完整空队列结算会先清红flag，未进入该异常。|旧局部callback缺陷及正常入口的分支限制。|正常完整对局必卡；当前源码仍引用未定义英文分数；分支永不可达。|
|旧开发SHA `91c409291936181b3706ed6623cf0cfd986c0b9c3ce3dac657b5af6c6f8efc3d`|受控无头桌面Chrome人工布盘：红50，随后空杆仍50无红且换手；另一组下一杆白得70。|旧版受控样本未实施跨杆撤红；覆盖对照样本存在。|当前pending策略失效；竞品自然局；手机/真机表现。该版game.test曾驱动物理，当前E1不能如此使用。|
|开发SHA `327072b6ab032acb75d80eca4df131e4820850c1e2f4dad8978d3b72e8629999`|文档称五个queen测试脚本正常退出。|历史作者报告隔离规则/积分/幂等/犯规/迟到积分检查。|脚本内容及日志已核验；E1和该SHA字节相同；本轮已跑；真实Tweener/完整浏览器通过。|
|竞品规则页|文档转述“红需要覆盖”。|存在该一般规则的历史转述。|同杆顺序、犯规叠罚、覆盖失败回滚时刻、终局优先级已录得实战。|
|两段“零分欠罚”材料|`传玩新局_零分欠罚.mp4`未明确母球犯规；第二段位置识别不足且没出杆。|取证不足。|竞品存在或不存在欠罚。|

历史五脚本名：`freestyle-queen-policy.test.cjs`、`freestyle-queen-score.test.cjs`、`freestyle-queen-return-idempotent.test.cjs`、`freestyle-pending-queen-foul.test.cjs`、`freestyle-late-score-terminal.test.cjs`。本轮没有这些脚本实体，不能调用它们或赋予本轮PASS。

历史MCP run `72819927833f441e87b606e86e524b34`是静态报告而非设备验收；`cb7b6645d97341c394c2e19adae8dae5`在文档时仍运行，不改写成完成。

## 3. 状态、分值与owner

|含义|E1真实符号/字段|
|---|---|
|模式/桌型|`_0x5d148e`：2 Freestyle、1 Carrom、0 Disc Pool；`_0x408018`桌型。|
|出杆方|`_0x209883`：true player、false opponent。账本actor用`opponent`，棋子type用拼写`oponent`，两者不应混淆。|
|分数与HUD|player `_0x4d3bf1` / `_0x27ee82`；opponent `_0x41f634` / `_0x458adc`。|
|棋型/分值|`_type` 0红/1白/2黑；`_0x1c2aac=[50,20,10]`，Freestyle目标`_0x153877=160`。普通任色给出杆方计分，不按初始棋子归属计分。|
|棋盘与队列|红`_0x3231b3`、白`_0x3e4566`、黑`_0x2a9c75`；本杆入袋队列`_0x31089b`。|
|杆级旗标|母球`_0x27e1b4`；犯规`_0x530863`；进袋/续杆`_0x5ebd99`；旧红flag`_0x4268e2`，不等于新覆盖phase。|
|隔离与提交|active `_0x3fddb3`；`_carromRoundId`、递增`_carromTurnId`、`_carromSettledTurn`；结果一次提交`_carromResultCommitted`。|
|新红状态|`_carromFreestyleQueenState`：初始`{phase:'board',owner:null}`；pending主调用附`points:50`。|
|积分账本|`_carromFreestyleHistory`项`{type,points,actor,round,turn,queueIndex}`。普通棋写入顺序取决于completion顺序，不保证按queueIndex排序。|
|表现/异步|`_carromPendingPenalty`；`_carromPendingQueenPocket`旧入袋sprite；非Freestyle红HUD sprite `_0x404020`。|

### 3.1 E2依赖状态图（不是竞品规范）

```
board + 本杆非犯规红入袋 + ordinary=0 -> pending(actor)
board + 本杆非犯规红入袋 + ordinary>0 -> covered(actor) [项目假设]
pending(owner) + 同owner + 非犯规 + ordinary>0 -> covered(owner)
pending(owner) + 其他任何本杆 -> board/null + returnQueen + revokeOwner
covered + 任意本杆 -> 保持covered
board + 无有效红入袋 -> 保持board
```

`shot={actor,foul,queen,ordinary}`。ordinary是白黑合计，不关心颜色、入袋先后或“红之后”事件；pending分支优先，本杆queen=true不会再作为新红处理。owner错位、重复红、损坏账本等须用异常夹具区分，不声称自然可达。

## 4. 一杆结算调用链与优先级

入口 `_0xbdafb3(expectedTurn)`：错turn、重复settled或同轮同杆尚待postscan flush的timeout ticket直接返回；active=false返回；棋子/母球仍醒则通过 `_0x338c29(...,50)`重试。静止检查含trimVelocity，不等于数学速度精确为零。

|顺序|当前行为|提交边界/风险|
|---|---|---|
|1|标记settled，计时置-1、sleep全部；Freestyle先清旧红flag；`snapshot=queue.slice(0)`；冻结actor/foul/queen/ordinary。|后续新扫描事件不自动进入snapshot。|
|2a 犯规|snapshot所有棋子返场；不给本杆分。返场finish先一次完成保护，再active/round/turn校验。|表现棋子已有body移除，返场必须新建物理实例。|
|2b 非犯规|红分50及history/HUD/玩家SDK同步预入账；飞分仅表现。普通分在飞分completion入账，并写history。|普通finish同样一次保护、active/round/turn校验。|
|3|逐项从队列移除，`_0x253500(...,true)`保留表现对象；有入袋则延迟参数1000，否则500。|不是队列整体锁，晚入袋候选需测试。|
|4|仅`foul && snapshot.length===0`调用历史罚棋；犯规强制续杆=false。|进子犯规不叠加历史罚棋。|
|5|延迟边界先`_carromAwaitPenalty`等罚棋，每50参数重试，第20次可finish兜底；之后active/round/turn guard。|round失效/退出应阻止旧杆后续动作。|
|6|强制所有本杆返场finish和积分finish。|迟到或被同target替换取消的completion不能决定漏分；重复finish不重复账本。|
|7|真实调用E2；需返红则`_carromReturnFreestyleQueen(revokeOwner)`；pending红附points50，更新state。|覆盖失败撤红及撤分早于终局。|
|8|phase非pending才允许任一分数≥160判终局；双方达标取当前actor胜；`_0x47e567`一次提交。|pending甚至阻止非owner已达标方获胜；这是策略而非竞品依据。|
|9|终局return之后才有旧flag分支：`_0x4268e2 && !_0x5ebd99`调用旧返红、扣真实分数50、更新HUD。|旧分支与新状态机并存，未证实自然可达；若强制进入，它不更新新history/state。|
|10|关输入、按续杆保持出杆方或换手；两方回合入口turn++、清foul/续杆，保留新queen state。|这是跨杆pending得以延续的路径。|

### 4.1 历史罚棋并不是“任意正分扣最低棋”

`_carromFreestylePenalty`筛选actor且round相同的**全部历史**，不限最近一杆。要求非空、首项type1/2、首项points有限且>0、全部type和points相等、`score===entry.points*matches.length`。选`matches[0]`，是账本首项，不是最近一颗。由于同类同分，数值上扣一颗，但账本turn/queueIndex选择仍有意义。

同步删除一条历史、扣其points、更新HUD及玩家SDK；动画结束或state.finish才创建新物理棋并入白/黑数组。restore一次保护及active/roundguard；cancel extract表现tween/移除sprite；finish置中心并restore。调用方以pending保证先返完再换手。纯白20/40/60扣20返一白；纯黑10/20/30扣10返一黑；混色、含红、无历史、历史与分数不一致都不罚。没有debt字段，零分不记欠罚。

### 4.2 新返红与旧返红不能混用

`_carromReturnFreestyleQueen(owner)`找本round旧owner首条type0历史，没有则用当前state.points||0；同步创建红棋、避障、push红数组、删历史、标当前旧state.returnCommitted、扣owner分/HUD/玩家SDK。主调用随后换成board对象，所以该标志是当前状态对象级幂等，不是永久跨杆锁。

该函数自身不检active/round/turn，依赖调用边界；不查棋盘是否已有红、不检查fallback points有限性、不夹分数下界。属于异常状态防御风险，不把缺字段、重复红假定成正常局必现。旧`_0x52e61d`依赖`_0x404020`动画sprite，不等于新同步返红机制。

## 5. 物理、输入窗口与可接受误差

- 真实物理步长 `Planck.step(1/60,10,10)`，随后clearForces。每逻辑tick先更新动画/粒子/Tweener，再检查active、计时、扫描母球→红→白→黑、timeout postscan flush，最后物理step。同tick扫描顺序不是实际入袋时间顺序；同杆覆盖规则也不读该顺序。
- 棋子动态body：allowSleep=true、初始awake=false、bullet=true；半径16，angularDamping0.2、linearDamping1.8、density0.45、friction0、restitution1。`trimVelocity`在awake且`abs(vx)+abs(vy)<0.2`时sleep，这是代码阈值，不能解释成竞品物理或实测误差。
- 入袋判断距离≤20；母球设foul并sensor防重复。复现边界用19.99/20/20.01世界单位，不用肉眼截图判断。返场避障阈值32，轴向/对角/有界网格搜索；满堵搜索未找到并未返回失败信号，必须检实际返回位置与重叠。
- `_0x338c29`使用Tweener空对象、time=(delay/1000)*60并捕获round；completion只在active且round相同调用，内层常另检turn。500/1000参数分别对应30/60名义逻辑tick，50参数对应3tick，出杆后2300参数对应138tick；不是保证500/1000毫秒壁钟。飞分15–25tick，返棋20–30tick，真实数组调度可产生偏移。
- 输入口应只在真实turn与界面启用阶段接收pointer，出杆/结算过程不得再次开启出杆。测试桌面mouse及移动touch；暂停、游戏暂停、广告token会在更新入口阻塞逻辑推进，不应凭壁钟等待作失败判断。重开取消瞄准pointer；不是本轮已验证输入可靠。
- Freestyle table0计时不会递减（条件是table非0或mode0非教程），因此table0不能通过“等倒计时”复现覆盖超时。非table0才可测真实timeout；人工调用结算必须标为夹具。AI无合法候选且无fallback时，pending分支会主动走结算。
- 数值验收：分值、history计数、phase、owner、turn/round/一次提交要求严格相等，**容差0**；入袋边界按实现≤20精确断言；物理轨迹重复比较建议暂定位置0.5世界单位/角度0.01rad，只用于同环境可重复性而非竞品对齐，须后续实测确认。避障应不重叠，无“误差内重复红”。tick日志严格记录实际发生顺序，不预先承诺completion都在名义时长tick发生。
- HUD `_0x1eceb4`内部value同步，增分文本要5tick放大completion才写label、再5tick缩回，扣分直接改文本；瞬时label旧值不能单独认定漏分。需同采score/HUD.value/label，并在表现稳定后校验最终一致。

## 6. 场景矩阵：输入、预测、证据、风险、复现

记号：P/O为player/opponent，Q/W/B为红/白/黑；S为出杆方初分；正常场景要求active=true、同round/turn、history与score一致且无旧回调。A为直接运行E2依赖，B为原函数隔离夹具，C为测试副本真实浏览器物理（准备方法见第8节）。所有条目本轮状态均为**未执行**。E1/E2表示当前静态依据；E4旧样本只能辅助，不等同当前验证。C参数化P/O、四袋、mouse/touch、同tick/异tick。

|ID / 输入|当前代码预测|已有依据|未覆盖风险|可执行复现与断言|
|---|---|---|---|---|
|Q01 board、S=0、仅Q、非犯规|S=50，history红1，pending(P/O)，红数组0，续杆，无终局。|E1结算+E2；E4旧版首杆50仅佐证旧样本。|入袋表现/预入账/文本不同步。|A传queen=true ordinary=0；B/C单红入袋，采预入账及最终state，断言仅+50一次。|
|Q02 Q01后同owner空杆、非犯规|撤50删红history、返红1、board/null、换手。|E1新返红+E2。E4旧空杆仍50属不同版本。|返红位置堵塞、重复finish。|A pending+ordinary0；B/C连续两杆，断言S回0、红恰1、一次撤分。|
|Q03 Q01后同owner W或B非犯规|covered同owner，S=70或60，红不返，普通历史新增1，续杆。|E1/E2；E4旧W对照70有限参考。|白黑同等覆盖未获竞品对局证据。|A ordinary1；B/C分别W、B，并多普通，检查covered与总分。|
|Q04 board同杆Q+W/B或多个普通、非犯规|直接covered，+50+20*w+10*b，续杆；不读先后。|E2注释明确项目假设；E1snapshot计数。|竞品是否要求红之后进普通未知。|B队列[Q,W]/[W,Q]、[Q,B]/[B,Q]；C先后不同帧和同帧；最终分/phase严格相同。|
|Q05 pending旧owner=P，本杆actor=O且普通>0|返旧P红/扣P50，新state board；O本杆普通仍计给O。|E2 pending分支优先+E1计分先于撤红。|正常路径是否会跳过owner覆盖杆未知。|A/B异常owner错位夹具，断言扣旧owner而非当前actor；C仅自然发生才归实局证据。|
|Q06 pending，非table0超时空杆；AI无候选无fallback|同空杆撤红，再换手。|E1timeout postscan flush、AI fallback分支+E2。|table0不倒计时；真实AI候选条件难控制。|B设ticket等scan后flush；C非table0等待真实超时。AI在测试副本受控禁候选/fallback并标人工条件。|
|Q07 pending返红幂等与损坏账本夹具|同一旧state重复调用返红只提交一次；缺红history且points50仍撤50；points也缺则撤0；不检查已有红或异常points。|E1returnCommitted、history.findIndex及points fallback。|新state替换后标志不再存在；重复红/坏分数是否自然可达未知。|B直接调用原返红两次，断言红+1且只扣一次；另设缺history/缺points/已有红/NaN或字符串points，记录真实结果，缺history正常fallback与损坏输入分别标注，不把异常输出当竞品事实。|
|F01 board，同杆Q/W/B任意多子+母球犯规|本杆所有子返、无本杆积分、board、换手；不额外罚历史棋。|E1foul全返及snapshot.length门槛+E2。|叠罚策略未证实；返场避障互相影响。|B/C分别[Q]、[W,B]、[Q,W,B]加母球，历史已有40也保留40；所有入袋子各返1，无新增history。|
|F02 空队列犯规，纯白历史n=1/2/3，S=20*n|扣20返一白，删首匹配历史；其余保留，换手。|E1罚棋+E3唯一diff。|旧历史顺序与queueIndex顺序可能不同。|B/C给20/40/60，断言新分0/20/40、白+1、删除最先账本项；再犯规可再罚1。|
|F03 空队列犯规，纯黑n=1/2/3，S=10*n|扣10返一黑，非扣20，其他同F02。|E1/E3。|不能从只有白测试泛化黑。|B/C给10/20/30，断言0/10/20及黑+1。|
|F04 空队列犯规，history白+黑，S=30|一般罚棋false，分/棋盘不变，换手。|E1matches.every条件。|混色真实规则未闭合。|B/C先累计W+B再只进母球；断言不删历史、不返普通；不得改期待为竞品最低棋罚则。|
|F05 空队列犯规，零分/空历史|不扣不返、不记录欠罚，换手；随后进W正常+20。|E1无debt写入；E4欠罚材料不足。|竞品欠罚未知。|B/C零分犯规后下一可得分杆，断言没有延迟抵扣、history仅新W。|
|F06 空队列犯规，score不匹配history/异round/异actor/points坏值|不符合组成条件则不罚；只看当前actor当前round。|E1罚棋过滤及有限值条件。|损坏状态不是已证自然故障。|B异常参数表：score39配两W、负/NaN points、type0、另round/actor；断言false且无副作用。|
|F07 pending红+同owner空队列母球犯规|含红历史阻一般罚；覆盖规则撤50返红，换手。|E1/E2；E4称历史pending-foul隔离测试但脚本缺失。|可能错误双扣/错owner。|B/C由Q01接只进母球，断言只撤50、红1、无普通罚棋。|
|F08 pending红+本杆普通入袋且母球犯规|本杆普通返/不加分，旧红也返/扣50，board，换手。|E1全返→E2撤红。|返场时序及位置重叠。|B/C pending后[W,B]+母球，断言各普通+1、红+1、score仅-50。|
|F09 covered红+普通history，空队列母球犯规|含红挡一般罚棋；covered保持；可能分数完全不变。|E1/E2直接组合。|高关注规则缺口，未获产品/竞品确认。|B/C先Q+W=70 covered，再只进母球；断言当前策略70不变、无返棋、换手。把结果交产品决定，不冒充正常竞品规则。|
|T01 S=110，board仅Q非犯规|S到160但pending，不提交胜利。|E1phase门槛；E4迟到积分历史摘要有限参考。|HUD先显示160易误判“未胜bug”。|B/C初始合法110账本+Q，断言resultCommitted=false，再W覆盖才胜。|
|T02 pending S=160，下一空杆非犯规|撤50至110后再判，未终局、换手。|E1撤红先于终局。|旧flag分支可能额外扣分的异常夹具。|B/C承接T01空杆，断言110、红1、无结果提交。|
|T03 pending覆盖普通迟到completion；S=140后W|强制积分到160，再covered，再提交一次。|E1scoreCallbacks强制finish。|真实tween取消、倒序及HUD滞后。|B延后/取消普通completion使边界先到，断言+20一次、history1、结果一次；C用真实Tweener受控替换与正常对照。|
|T04 pending撤红后任一方仍≥160；双方均≥160|先撤红再看分；非pending达标则终局；双方达标取当前actor胜。|E1playerQualified/opponentQualified表达式。|双达标/非owner先达标的可达性及竞品策略未知。|B夹具设置两方分与owner，分别只有P/只有O/双方/撤后皆不足；断言结果通知参数，不称自然局样本。|
|A01 同杆多个普通completion倒序/延迟/重复/同target取消|最终总分/历史各一次；已完成项重复finish无效，取消completion项边界finish兜底。|E1一次标志与强制finish；真实Tweener.extract不调completion。|history append可能倒序，表现对象移除后的tween仍更新。|B/C记录每项queueIndex与commit顺序，断言总数而非history天然排序；重复调用completion+边界finish后计分不变。|
|A02 历史罚棋completion永不到/重复到|第20次await可finish，pending清，返一颗；重复restore不再返。|E1AwaitPenalty与returned保护。|不可用真实壁钟1秒替代tick等待；cancel路径。|B捕获state禁止原completion，连续await推进到20；断言一返一扣、只advance一次，后再触发completion无重复。|
|A03 积分/返场/罚棋途中重开或退出|新局round++清分/账本/新红state，旧积分/返场guard拒绝；退出active=false且discard表现。|E1重开与discard、各finish guards。|并非所有UI/母球入场completion都有guard。|B/C在预入红分、普通飞分、返棋各窗口触发重开/退出；强行释放旧callback，断言新局无旧分/旧棋/旧turn推进。|
|A04 暂停/游戏暂停/广告阻塞后恢复|阻塞时逻辑更新停；恢复继续，不能多次计分/返棋/结果。|E1更新入口及广告token。|真实宿主回调顺序未知；fallback不代表实宿主。|C在上述三个表现窗口暂停，采tick不推进；恢复后最终账本一致；宿主广告需另取真实证据。|
|A05 结算snapshot前后同tick晚入袋/晚母球|snapshot已冻结；其后入袋可能没进入本杆结算，foul与续杆可能不同步。这里只是时序风险候选。|E1Tweener先于扫描、正常结算无统一postscan屏障。|自然可达尚未证明，不能宣布已漏分。|B强制boundary在scan前运行；C低速棋放距20附近、速度阈值0.2上下，记录settled/snapshot/scan/tween顺序；成功复现才判实际缺陷。|
|A06 终局提交后继续更新|result函数防重复通知但不设active=false；后续scan/物理可能继续。|E1_0x47e567及更新入口。|结果后是否仍入袋/改账本未观测。|C提交胜利后持续推进至少120tick，断言分/history/board/result通知不再变化；失败需返回代码阶段，不在此修。|
|A07 旧红flag强制true且续杆false|若非终局并进入旧分支，扣真实owner分50，依赖旧sprite返红；不更新新history/state。|E1旧分支已修真实混淆分数；E4旧局部VM。|自然可达未知；仅延迟红入袋通常使true/true，不能据此断言进入。|B分别完整入口初flagtrue（会先清false）、callback前强制true/false、true/true对照；单列夹具结果与自然扫描结果。|
|A08 红入袋sprite/棋body生命周期|mode2入袋表现completion空分支，pendingQueenPocket未显式清零；removeFromWorld不幂等且body=null不可再world访问。|E1红扫描、棋子类、discard函数。|悬挂sprite引用、重复移body风险，正常外围保护可能防住。|B/C四袋红入袋→返红→重开，检查sprite.parent/tween/body及旧引用；测试重复remove仅作异常防御，不冒充正常故障。|
|A09 真实Tweener live数组调度与HUD文本|splice会改变遍历后继；completion可追加任务；同target替换取消旧completion；HUD逻辑先于label。|E1完整Tweener及HUD类。|简单fake调度器不等价。|真实Tweener隔离：两个同tick到期任务观察是否次tick才跑第二；completion追加任务观测当前tick是否执行；同target替换查旧completion=0；HUD稳定后label=score。|

## 7. 风险分级与未知项台账

等级反映复核优先级，不是本轮动态FAIL，也不是授权改动范围。

|ID|级别/问题|当前证据|缺少的闭合证据/下一步|
|---|---|---|---|
|U01|高：上传版本与历史SHA不可等同|E1真实正文；E4开发SHA；E3缩写标头。|对真实文件计算SHA256、拿对应before/after完整文件对账。本轮未计算。|
|U02|高：covered红后的空杆母球犯规可能免罚|E1历史含红限制+E2covered保持。|F09真实复现，产品罚则确认及竞品完整录像；目前规则缺口未闭合。|
|U03|高：进子犯规不叠历史罚棋、混色免罚、无欠罚|E1分支条件；E4欠罚材料不足。|F01/F04/F05复现及产品决策；不可套通用carrom规则当竞品事实。|
|U04|高：同杆红+普通覆盖、pending阻挡双方终局、双方达标当前actor胜|E1/E2，明确项目策略。|竞品对应完整对局与产品确认；本文只审当前预测。|
|U05|高：正常结算scan前snapshot/晚事件竞态|E1更新次序及sleep阈值，timeout另有postscan屏障。|A05真实物理事件日志；未证明自然可达。|
|U06|高：终局后active仍可能true|E1结果一次提交但不停止active。|A06结果后持续扫描/计分实测。|
|U07|中：真实Tweener时序及finish兜底有效性|完整Tweener、结算finish已读。|A01/A02/A09真实调度器与浏览器对照；旧隔离脚本原文/日志未上传。|
|U08|中：返红损坏账本、points异常、重复红及旧分支并存|E1新返红缺自身guard及旧分支不同账本。|正常/异常分别复现、追自然可达路径；不能仅强制flag就宣告自然故障。|
|U09|中：返场全堵搜索未报告失败、sprite/body生命周期|E1避障、pendingQueenPocket、removeFromWorld。|密集盘面A08和满堵返场，世界位置/数组/body/tween日志。|
|U10|中：部分UI/母球入场回调隔离未统一|E1存在无同级round/turnguard的表现回调。|A03按回调类型分组实测，不把有guard的积分路径一概判泄漏。|
|U11|证据缺口：竞品及历史底层材料|只有E4摘要；两视频结论不足；一run当时未结束。|原脚本、原日志、可辨认犯规和覆盖顺序的录像、真实设备/宿主记录。|
|U12|方法权限/框架差异|只选总Skill，子入口读取拒绝；真实PIXI/Planck而配置Canvas。|后续若需深模块可另轮选入；若要重建须另授权选型，不在本轮迁移。|

## 8. 可执行但未执行的复现方案

### 8.1 直接验证真实依赖（无生产修改）

使用Node.js 18或更新版本（需要structuredClone及node:assert/strict）。将下列代码保存到独立审查目录的 `queen-policy-review.cjs`，从输入平台导出E2原字节为本地 `disc-rules.js` 后执行 `node queen-policy-review.cjs /absolute/path/disc-rules.js`。不要把虚拟ref路径假定为Node可访问路径；本轮没有导出、保存或运行此脚本。它只断言依赖，**不验证E1积分、返场、物理、UI或竞品**。

```js
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
if (!process.argv[2]) throw new Error('请传入真实依赖的本地绝对路径');
const rules = require(path.resolve(process.argv[2]));
assert.equal(typeof rules.freestyleQueen, 'function');
let count = 0;
function verify(previous, shot, expected) {
  // 检查真实返回结构；每个用例使用独立状态，避免共享对象污染。
  const input = structuredClone(previous);
  const before = structuredClone(input);
  assert.deepEqual(rules.freestyleQueen(input, shot), expected);
  assert.deepEqual(input, before);
  count++;
}
for (const actor of ['player', 'opponent']) {
  const other = actor === 'player' ? 'opponent' : 'player';
  const board = {phase: 'board', owner: null};
  const pending = {phase: 'pending', owner: actor, points: 50};
  const covered = {phase: 'covered', owner: actor};
  const keep = state => ({state, returnQueen: false, revokeOwner: null});
  const revoke = {state: board, returnQueen: true, revokeOwner: actor};
  verify(board, {actor, foul: false, queen: true, ordinary: 0},
    keep({phase: 'pending', owner: actor}));
  for (const ordinary of [1, 2, 3]) {
    verify(board, {actor, foul: false, queen: true, ordinary}, keep(covered));
    verify(pending, {actor, foul: false, queen: false, ordinary}, keep(covered));
    verify(pending, {actor, foul: true, queen: false, ordinary}, revoke);
    verify(pending, {actor: other, foul: false, queen: false, ordinary}, revoke);
  }
  verify(pending, {actor, foul: false, queen: false, ordinary: 0}, revoke);
  verify(pending, {actor, foul: true, queen: false, ordinary: 0}, revoke);
  verify(board, {actor, foul: true, queen: true, ordinary: 2}, keep(board));
  verify(covered, {actor, foul: true, queen: false, ordinary: 0}, keep(covered));
  // 异常重复红：pending分支优先，而非重新开始一轮pending。
  verify(pending, {actor, foul: false, queen: true, ordinary: 0}, revoke);
}
console.log(`真实依赖断言完成：${count}个用例；不代表主游戏验收`);
```

此脚本预计定义36个独立调用断言（每actor18个）；这里只是代码计数，不是执行通过数。先前五个历史脚本不能替代它，更不能替代主程序集成测试。

### 8.2 原函数隔离夹具：实施规格与准备条件

需要：导出的E1/E2真实字节、可定位的闭包与解码表、Node VM测试工具及PIXI/棋子/SDK/Tweener可控替身；这些完整集成夹具本轮**未编写和运行**。不能用重新实现的“等价规则”代替原结算函数。

1. 在测试副本将真实 `_0xbdafb3`、`_carromFreestylePenalty`、`_carromReturnFreestyleQueen`、`_carromAwaitPenalty` 和被调用guard/工具函数连同原解码表及必要闭包导出至VM上下文；另加载E2原模块对象绑定window.CarromDiscRules。提取范围必须经过语法/依赖检查，不用随意正则截一个callback宣称完整结算。
2. `Disc`替身记录type/bodyAlive/world位置；removeFromWorld后拒绝world访问，new才返场；容器add/remove记录parent；HUD分别记录value和label；SDK计数并记录参数。给定真实符号状态、history、queue，调用原入口expectedTurn。
3. 调度器保留target与completion，支持推进tick、倒序完成、丢弃/替换、重复完成；在边界释放前后采样。替身用来探测规则状态/提交优先级，不用来宣称真实Tweener时长或浏览器通过。
4. 原 `_0x5e7a5f` / `_0x50a0ff` 替身仅记录advance并递增turn、清杆flag，不能默默把phase清掉；结果替身记录win参数与一次提交。静止检查替身可分别设醒/睡，确认settled前重试。
5. 按矩阵B逐一初始化独立上下文，断言分数、各type棋数、history字段、phase/owner、罚棋pending、turn推进次数和结果次数；每个夹具保存事件JSON及原文件SHA。异常输入和正常可达路径分别标注。
6. 另把E1的**真实Tweener**提取为独立上下文重复A09，并在集成夹具替换假调度器作对照。live数组移除可能跳帧、completion追加可能当tick推进，extract不执行completion；必须真实观察日志，不写固定理想事件序。

### 8.3 真实浏览器物理与输入：实施规格与准备条件

需完整可运行测试副本（HTML、PIXI、Planck、纹理/音频/字体和真实SDK配置或明确fallback），E1本身不证明这些资源齐备。当前没有在本轮准备或启动浏览器，也没有生产test接口授权。

- **不得调用当前公共game.test来驱动物理**：E1开头该入口直接 `_0x47e567(true);return;`，会强制胜利。必须在非发布测试副本显式添加受控布盘、只读快照及真实母球 `cast(force,angle)` 注入。真实cast会清sensor、awake=true并向中心施力；这是人工布盘物理证据，不等于自然完整局。
- 静态服务器只供测试副本，桌面mouse和手机视口touch先完成真实菜单点击与拖拽出杆，再做人工布盘精确复现；四袋、P/O、红前后普通、同tick/异tick参数化。桌面手机视口不冒充真机。
- 日志每tick记录：round/turn/settled、actor、queue(type/id)、snapshot、foul/续杆/旧flag、phase/owner/points/returnCommitted、history(含queueIndex)、两方score、HUD.value/label、各色数组与bodyAlive、penalty pending/waits、旧sprite.parent、resultCommitted、SDK次数以及scan/tween/commit/advance事件顺序。
- A05需布置低速临界入袋并用真实update步进，区分“测试钩子强制先snapshot”与“未干预调度自然发生”；A03在各不同completion窗口重开/退出；A06结果后持续推进。异常都保留控制台错误、事件JSON、截图/录像和文件SHA。
- 测试副本不得作为新生产源码或放入发布dist。只有将来获得测试阶段授权与可运行完整输入后再执行构建/浏览器验收；届时必须按阶段要求运行当轮 build/test/check，不引用本文或历史摘要当通过日志。

## 9. 静态交付验收与限制

已覆盖：真实E2依赖、E1红/普通入袋与母球犯规→snapshot→罚棋/返场/积分→覆盖回滚→终局→换手的全路径；同杆多子、跨杆覆盖、actor错位、临界得分、迟到completion、生命周期和物理时序；每矩阵场景给定输入、静态预测、证据边界、未覆盖风险与复现步骤。

未覆盖为动态验收：没有本轮测试PASS/FAIL、构建包、dist、试玩ZIP、浏览器截图或设备/宿主日志；没有确认竞品边缘规则、上传SHA与历史版本关联、自然竞态的实际可达性。没有例行要求阶段确认，也没有编造用户确认；待产品决定的策略仅登记，不擅自选规则或改代码。

产物：`reports/freestyle-static-review.md`（本报告）、`workflow/prototype.md`（阶段记录）。本阶段玩家界面无变更，未新增标题/菜单/提示文案，也未因中文报告切换游戏语言；若后续授权创建新默认英文界面，应采用English并设置lang=en，本轮不改原项目语言或HTML。
