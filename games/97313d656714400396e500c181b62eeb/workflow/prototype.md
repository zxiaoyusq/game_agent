# Carrom 最新 JS 与竞品红棋结算证据复核

本轮：attempt=1；阶段：prototype；日期：2026-11-13。范围为只读源码审查及报告，不修改游戏源码、资源、构建与测试脚本，不推进美术、代码或测试阶段。

## 结论与证据等级

1. 静态已证实：Freestyle（模式 2）红棋 pocket 后，`_carromPendingQueenPocket` 指向原棋子；pocket 动画完成的 Freestyle 分支为空。`_0xbdafb3` 消费队列后移除该棋子且未清除此引用。因此它可以指向 body=null、parent=null 的旧对象。这是生命周期清理遗漏；JavaScript 对象仍被强引用，不是原生悬空指针。
2. 静态已证实的后果：旧对象及其仍可达的子对象被保留，直到下一次 pocket 覆盖引用或显式 discard。不能据此宣称无限内存增长：该全局槽位一次仅保留一个引用，实际内存字节数未测量。
3. 未证明：残留引用造成重复计分、错误返场、HUD 错位、跨模式污染或崩溃。当前读取者具有模式或身份条件；返场新建棋子，并无已发现的棋子对象池复用。不能把清理遗漏升级为上述玩家可见缺陷。
4. 竞品证据只支持匹配原生库中的静态指令、分支与直接调用边。不能证明竞品 Freestyle 红棋需要何种覆盖、何时返场、犯规扣分、同杆红白黑次序或胜负门槛。
5. H5 的 Freestyle 覆盖决策交给外部 `window.CarromDiscRules.freestyleQueen`；提供的 JS 不包含其实现，不能独立确认完整规则。源码自身将相关策略标为 provisional。

## 输入与引用口径

E-01 最新 JS：`ref/mcp-inputs/mac-codex/1ebfc85e4d69a64bbe67b3e0e7877dbfb0f04c6466493bc0b033b3249c514a93/Carrom_current_1ebfc85e.js`。通过 read_reference 从字符 offset=0 连续读取至末尾，窗口依次为 0、24000、48000、108000、168000、228000、288000、348000、408000、468000、528000。引用以下使用函数名与唯一语句定位；工具返回未附源码行号，故不编造行号。路径中的摘要为输入标识，本轮未另行计算该 JS 的字节哈希。

E-02 原生 ZIP：`ref/mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip`。清单工具返回 SHA256=`ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1`，35 个条目，展开 2411908 字节。未全量解包。

实际读取的成员：

|编号|ZIP 内完整路径|工具返回 SHA256|
|---|---|---|
|E-03|report/竞品_ARM64代码定位.md|c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f|
|E-04|disassembly/09_queenCovered_1aa3458.txt|0d5ea8f1c3ec5bbded18719168b4f163c258aac3a4f748e8c37a33a0aae1bf09|
|E-05|disassembly/caller_1aa2eb0.txt|af2612149a270ceb4d9121d011dfe2efee0ab0e697f0215c5b5f958dece9cf0a|

其他 ZIP 成员仅清点，没有将其内容作为已读证据。所选总集技能及执行协议、全局规则、原生取证、未知清单均实际读取。玩法专项模块入口两次被工具拒绝，不计为读取成功，不扩充未选技能。四份冻结品类和框架资料均已读取。

## 状态与所有权：三个 pending 不可混同

|状态|含义与 owner|赋值、读取、清理|
|---|---|---|
|`_carromPendingQueenPocket`|动画对象引用；pocket 扫描与普通模式 HUD 转移共享|声明 null；`_0x49d791` 四袋赋值；各 pocket/HUD 回调身份校验；普通模式结算接管；discard 清空|
|`_carromFreestyleQueenState`|Freestyle 规则状态；结算 owner 为 `_0xbdafb3`，决策依赖外部规则模块|初始化/reset 为 `{phase:'board',owner:null}`；结算调用 freestyleQueen 并接收 state；pending 时阻止达标结束；timeout/AI 无有效击球分支读取 phase|
|`_carromPendingPenalty`|普通棋罚返动画任务；owner 为 `_carromFreestylePenalty`|登记 cancel/finish；restore 身份匹配后清空；discard 取消；不负责红棋 pocket 引用|

辅助状态：`_0x3231b3` 为场上红棋数组，`_0x31089b` 为待结算 pocket 队列；`_0x404020` 为普通模式已到 HUD 或被结算接管的红棋表现对象；`_0x4268e2` 为旧覆盖标志；`_carromQueenClearedThisShot` 为模式 1 本杆普通棋清除覆盖标志的记录。`_carromFreestyleHistory` 保存类型、积分、actor、round、turn、queueIndex。

## 最新 JS 调用链与条件

下表所有函数均引用 E-01；四袋分支结构重复，不能只修其中一袋。

|函数/位置|调用与条件|状态、对象和回调效果|
|---|---|---|
|`_0x49d791` 红棋循环|对 `_0x3231b3.slice(0)` 中棋子，距任一 `_0x2fc10d[0..3]` <=20|置续杆与覆盖标志；removeFromWorld；从红棋数组移除但保留表现对象；pending=原棋子；模式 2 将其 push 到结算队列；启动 15 tick pocket tween|
|四袋 pocket onComplete|要求对局有效、round 相同、pending===捕获棋子|模式 2 空分支；其他模式启动飞向 player/opponent HUD 的 20 tick tween|
|四袋双边 HUD onComplete|再次要求对局、round、pending 身份相同|pending===回调对象时清 null；`_0x404020=回调对象`；设置勾选图标位置、可见性、纹理。actor 与 mode 在回调执行时读取，未捕获 turn；这属于潜在时序风险，当前未给出可达失败轨迹|
|`_0xbdafb3` 入口|expectedTurn 必须等于当前且未结算；timeout ticket 未占用；对局有效；所有棋子停稳|标记该 turn 已结算，冻结棋子；模式 2 与普通模式分流，异步结算再次检查 round/turn|
|`_0xbdafb3` 模式 2 非犯规|遍历队列快照|红棋同步加 50 分并写 history/HUD/reportScore；飞字回调仅移除文字，不再加红棋分。普通棋 20/10 分由幂等完成回调提交；定时结算强制补齐延迟回调。消费时从场景移除原棋子，再从队列移除，未清动画 pending|
|`_0xbdafb3` 模式 2 犯规|`_0x530863` 为真|为本杆队列棋子启动返场 tween；幂等回调检查 round/turn，再 new 棋子、避让、入对应场上数组并移除旧对象；未清红棋动画 pending。结算边界可强制 finish，避免仅靠动画时长决定回合|
|`_0xbdafb3` Freestyle 决策|提交飞字积分与本杆返场后|调用 `CarromDiscRules.freestyleQueen(state,shot)`，shot 含 actor/foul/queen/ordinary；returnQueen 时调用 `_carromReturnFreestyleQueen(revokeOwner)`；接收新 state。仅 phase 非 pending 且任一分数>=160 才调用结果函数|
|`_carromReturnFreestyleQueen`|未 returnCommitted，按 round/owner/type=0 查 history|new 红棋并入场；删除对应 history，标记 returnCommitted，按 entry.points 撤回得分并更新 HUD。缺 history 时使用 state.points；不复用旧 sprite，不读取 pocket pending。外部决策何时重置 returnCommitted 未知|
|`_0xbdafb3` 普通模式接管|mode===1、覆盖标志真、无续杆、没有 `_0x404020` 且 pending 存在|extract pending tween；把 pending 交给 `_0x404020`，清 pending；调用 `_0x52e61d`，完成后清标志/图标再换回合|
|`_0x52e61d`|存在 `_0x404020` 才启动返场|捕获 round 与 sprite，回调要求对局/round/sprite 身份一致；new 红棋入场，移除旧表现对象，`_0x404020=null`，再通知完成。不接管 Freestyle pending|
|`_carromDiscardPendingQueenPocket`|重开或页面切换调用|先取旧引用并清 null，再 extract tween，parent 存在则移除；不负责规则状态判定、不销毁共享纹理|
|discard 调用者|`_0x5480e3`、`_0x3771eb`、`_0x48e98f`、`_0x10184d`、`_0x411a1e`、`_0x3153fe`|分别覆盖重开、主页、模式/桌台选择、转盘、商店及匹配入口；模式选择先 discard 再改 mode。重开同时递增 round 并重置 Freestyle state/history|
|`_0x50a0ff` / `_0x5e7a5f`|下一回合|递增 turn，清本杆标志；不清 pocket pending|

### 动画、容器与复用语义

`Tweener.addTween(target,...)` 先 `extract(target)`；extract 找到同目标 tween 后 stop，stop 从 tween 数组删除，未调用 onComplete。因此犯规返场 tween 会替换同棋子 pocket tween，不能假定两个回调都会执行。

`_0x253500(array,disc,true)` 在数组包含该对象时 splice 后立即 return，跳过函数后部的 kill、extract、destroy。这解释了为何入袋时保留表现对象，也解释了结算消费不会自动清全局 pending。若对象不在数组则不走该 early return，不能把 true 参数等同所有情况下都不销毁。

棋子 `_0x54e9a5` 构造函数创建新 Container、Sprite、动画和刚体。removeFromWorld 销毁 body 并设 null，移除 light；返场均调用 new `_0x54e9a5`。未发现将旧红棋重新注入棋子对象池的路径。pending 引用复用有两种：下一次 pocket 覆盖该槽位；普通模式结算把同对象移交 `_0x404020`。这不等于对象池复用。

### HUD 所有权

Freestyle 红棋积分 owner 是结算同步提交段；飞字是表现。普通棋积分暂由幂等飞字完成函数承担，并在规则决策前强制补齐。`_carromScoreFinished` 与 round/turn 检查抑制重复和旧回合提交。

Freestyle 数字 HUD 为 `_0x27ee82` / `_0x458adc`（`_0x1eceb4`）；value setter 更新 `_value` 并 redraw，增分时标签动画回调读取当前 `_value`，不是捕获的历史分数。普通模式计数 HUD 为 `_0x539ff8` / `_0x25b85f`（`_0x133fee`）。`_0x337f1a` 是普通模式覆盖图标；普通棋 pocket 在 `_0x4268e2` 真时可修改其纹理，模式 2 下通常隐藏，不能只凭写纹理断言可见错误。

## 最小反例与风险分级

### A：动画 pending 残留的静态最小反例

前置：mode=2，对局有效，round=R，turn=T，场上仅一枚目标红棋 Q，分数远离胜负门槛；其余普通棋可留场但本杆不进袋，无犯规。

1. Q 距一袋中心<=20，运行 pocket 扫描：Q.body=null，Q 从红棋数组移出，pending=Q，Q 加入 `_0x31089b`。
2. 允许 15 tick pocket tween 完成：mode=2 的空分支使 pending 仍等于 Q。
3. 棋子停稳后结算：红棋加 50 分一次，Q 从场景和结算队列移除。
4. 在外部规则返回之前即可检查：pending===Q 且 Q.parent==null、Q.body==null。

该步骤链由源码分支直接推出，本轮没有执行脚本或浏览器复现。它是对“Freestyle 消费后一定清 null”的反例，不是对“红棋重复计分”的反例。

### B：犯规返场后的旧引用

同杆红棋 Q 入袋并发生 striker foul。结算替换 Q 的 pocket tween，返场完成创建 Q2 并移除 Q，pending 仍可为 Q；Q2!==Q。再次入袋 Q2 时 pending 覆盖为 Q2。可预测的是引用残留及覆盖，不是已证明的红棋复制：返场回调有幂等保护；外部规则对 foul+queen 的决策未提供。

### C：目前不能成立的缺陷断言

- “残留 pending 会重复给 50 分”：积分从队列与结算边界产生，不从 pending 产生；无证据。
- “旧对象会返场并复制红棋”：Freestyle 返场 new 对象，普通模式 pending 接管限定 mode===1，正常切模式有 discard；无已证可达轨迹。
- “退出后旧回调必定污染新局”：有对局/round/身份门禁；未证明绕过。
- “竞品不需要覆盖，所以 H5 规则错误”：原生材料不能证明该规则。

## 竞品原生证据：可证与未知

原生库身份来自归档文本声明：`libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so`，SHA256 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`，AArch64。ZIP 内没有该库原件，本轮不能独立核对原始机器码与库哈希。以下均为 ELF link VA，不能直接用于运行时 hook。

|证据|实际指令及条件|允许结论|禁止提升的结论|
|---|---|---|---|
|E-05 caller|0x1aa30ac 将 x19 传 x0；0x1aa30b0 BL 0x1aa3458。前面 0x1aa3028/3034 可跳到 30ac|提供窗口存在该直接调用；所见可选分支在该点汇合|不是已识别停球/结算 owner，也不是实际触发证明；前置未知调用可能异常或不返回|
|E-04 循环|0x1aa349c 读取 begin/end；每项步进0x60；w26 非零时须与另一字段相同；随后长度/字节比较过滤；匹配时 w24++|存在计数及筛选控制流|不能把未命名字段直接称为 pocket、actor 或红棋类型|
|E-04 标志计算|w26==0 且 [x20+0x18]==2 可置 w23=1；否则模式候选字段==4 且当前条目首32位==0 可置1；空集合为0|可记录准确比较条件与布尔候选的来源|常量2/4不可未经映射称为 Freestyle/Carrom；条目0不可直接称为红棋|
|E-04 queenCovered 构造段|0x1aa36fc `and x9,x23,#1`，3704 写栈；3708/370c 构造已标注 queenCovered 字符串地址0x1232240；3738 调用0x1aa763c，3744 调用0x2706868|布尔候选与键名相关的临时值构造/写入调用序列；与报告/字典组装解释相容|缺被调函数语义，不认定为权威覆盖状态写入、规则 owner、联网发送或服务端认可|

E-03 明示 FDE 是展开范围、字符串扫描与 BL 扫描有覆盖限制。MatchShotSolver/physicsStopped 短范围命名不能作为玩法算法。H5 与 native 未建立字段、模式枚举、版本语义对应，不做字面映射。

## 无新增资源的最小修复建议（未实施）

建议优先只修清理所有权，不改未知规则：在 `_0xbdafb3` 的 Freestyle 队列消费边界，确认当前 disc 为红棋且 pending===disc 时，同步清 pending；如仍有同对象 pocket tween，extract 取消后由该消费分支继续安排自己的表现。不要在 pocket onComplete 简单调用 discard：它可能过早移除还待结算或待犯规返场的对象。

非犯规消费：取消该棋子剩余 pocket tween、身份匹配清槽位，再移除场景对象；不改变同步50分、history、规则决策。犯规消费：身份匹配清槽位，返场动画仍由已有幂等完成函数负责；不调用会移除返场目标的通用 discard。不要在回合开始无条件清全局引用，以免破坏模式1合法 HUD 转移。

可将“释放动画所有权”和“销毁表现对象”拆成小函数，保持一个对象一次交接；不要引入第二套红棋规则、额外资源、网络库或对象池。若强化普通模式 HUD 回调，捕获 actor/mode/turn 或显式所有权令牌，并先验证现有正常跨回合动画是否允许持续，避免盲加 turn 门禁丢失合法 HUD 提交。

## 建议测试与验收条件（本轮未执行）

|测试|输入/时序|断言|
|---|---|---|
|T01|四袋×双方，Freestyle 单红无犯规，pocket 完成后消费|修复后 pending=null；红棋只加50一次；队列空；旧对象无parent/body|
|T02|结算先于 pocket 完成、以及 pocket 先完成|规则分数一致；无迟到 HUD 接管；无重复回调提交|
|T03|红棋+striker 同杆犯规，动画自然结束与强制 finish|只恢复一枚新红棋；pending=null；新旧对象不相等；不重复扣分|
|T04|待覆盖红棋后空杆、普通棋覆盖、超时、AI无合法击球|使用真实 CarromDiscRules 实现断言状态与返场，不用推测竞品规则|
|T05|红棋单独/同杆普通棋，改变飞字完成顺序、重复调用finish|积分/history各一次；规则决策前积分齐备；pending不控制加分|
|T06|pocket/HUD/返场动画中重开、主页、选模式、商店、转盘、匹配|旧round回调不改新局；pending清空；模式1接管仍可正常完成|
|T07|mode1红棋HUD未到达即需返场；双方四袋|pending移交404020后清空；返场完成再推进回合；图标状态正确|
|T08|返场再入袋多轮，覆盖旧pending槽位|棋子总数按规则守恒；无旧sprite复用；对象引用不持续积累|

测试分层：先对原始函数受控调度作规则/生命周期测试，再以完整离线 H5 和真实浏览器验证点击、HUD与截图；桩对象测试仅证明受控路径，不等同 PIXI/Planck 整体行为。数值断言：计分、状态、回调次数和棋子数量必须精确相等；物理轨迹容差另行校准。

## 物理、输入、界面及范围取舍

当前是证据复核，不新设计玩法。保留观察→瞄准/拖拽→释放→模拟→pocket→停稳结算→续杆/换手/结束循环。E-01 实际使用 PIXI 和 `box2d=planck`，与工作流 Canvas 2D 配置并非同一渲染实现；本轮不迁移、不伪称原生 Canvas 2D 工程。

可见实现：每逻辑tick调用 world.step(1/60,10,10)，ticker 累积器 while(accumulator>1) 补步，未见补步次数上限；暂停/广告清累积并阻断推进。pocket 是中心距离<=20的扫描触发，发生在本tick物理step之前；刚体棋子半径16逻辑像素，bullet=true；速度绝对值和<0.2时置sleep。高速穿袋、长帧和不同浏览器物理误差未验收，不能宣称绝不穿透。

输入窗口：仅玩家可操作、未暂停、未已有瞄准时接收指定pointer；释放匹配pointer且strength>=0.25才发射，力度= strength×100×1.25；低于门槛取消。教程门禁、主机暂停、触控取消按现有路径保留。

计分：Freestyle数组[50,20,10]，目标160；规则pending期间不结束；双方同时达标时结算使用当前actor选择结果。普通模式胜利依赖外部hasWon与场上红棋情况，完整成功/失败规则未知。

界面布局保留现状：逻辑尺寸640×1137，双方HUD位于顶部左右，棋盘居中，底部摆放条，覆盖图标与普通模式红棋HUD绑定。无新增玩家文案；未来新增提示默认English，不能凭本轮单JS确认html lang或中文浏览器默认语言。

建议验收误差：规则/状态/积分零误差；pocket判定在20边界两侧使用19.99、20、20.01逻辑像素；输入门槛使用0.249、0.25、0.251；物理跨帧轨迹容差尚未测定，不能把AI快照的1像素容差当作通用物理精度承诺。

## 真实操作与验证结果

- PASS：最新JS连续只读读取至文件末尾；实际读取原生报告、queenCovered和直接调用者反汇编；完成静态调用链与条件核对。
- 本轮源码编辑/覆盖调用：0；未新增资源、依赖、构建产物或网络请求。仅创建本报告。源文件未通过写入工具改动；没有前后独立哈希对账，不宣称已完成字节级不变验证。
- extract_reference_asset 对单JS的调用因缺member失败，没有生成副本；之后未以ZIP工具猜测提取单文件。grep(/ref)返回无匹配，不能作为引用不存在证明；结论依据实际read_reference正文。
- BLOCKED：动态复现与整包运行。工作区初始ls返回空；输入仅单JS与原生证据ZIP，缺HTML入口、PIXI/Planck及资源、外部CarromDiscRules和既有构建配置。
- 未调用run_validation，未执行npm run build/npm test/npm run check；本轮为只读原型分析阶段，未创建虚假构建工程来替代当前游戏。没有测试通过、浏览器截图、真机或网络验收结论。
- 包体与加载：未改游戏文件，未提出新增运行时资源；缺完整包体基线，不能报告最终dist大小、加载时间、离线可玩性或性能提升。

产物路径：`/workflow/prototype.md`。不生成试玩ZIP或源码包，不推进下阶段。

## 未知清单

|编号|未知项|还缺什么|当前证据|状态|
|---|---|---|---|---|
|U-01|外部Freestyle覆盖、犯规与返场决策|匹配最新JS的CarromDiscRules完整实现及测试|E-01只有调用，源码注释标provisional|未闭合|
|U-02|残留引用在完整游戏中的玩家可见后果|完整离线包与受控调度、真实浏览器复现|E-01证明清理遗漏，未证明重复计分/错误返场|未闭合|
|U-03|竞品模式枚举、queenCovered业务语义及权威owner|同哈希原生库、被调函数、匹配符号/结构与运行观测|E-03至E-05仅静态候选|未闭合|
|U-04|竞品红棋覆盖与胜负规则|匹配版本可重复对局观测或完整权威规则执行链|现有材料不能证明|未闭合|
|U-05|输入JS独立SHA256与不变性对账|只读字节哈希工具结果及前后对账|仅输入标识；本轮无源码写入调用|未闭合|
|U-06|完整包离线、体积、加载性能及语言|当前HTML、依赖、资源、构建产物和性能基线|单JS不能覆盖|未闭合|
|U-07|普通模式延迟HUD读取当前actor/mode能否自然错配|完整调度轨迹与边界测试|E-01存在round/身份检查但未捕获turn/actor|未闭合|

本报告的“已证实”限于已读源码/反汇编的静态性质；最小反例是可执行步骤设计，未冒充本轮运行结果。
