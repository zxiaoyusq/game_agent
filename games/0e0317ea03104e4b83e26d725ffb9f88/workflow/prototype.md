# Carrom 广告期间玩家输入保护：独立原型审查

## 1. 结论与范围

当前阶段：prototype；本次仅只读审查及验收设计，不修改参考源码、不迁移引擎、不推进美术/代码/测试阶段。

**结论：B 相比 A 有有效的玩家出杆保护，但不足以认定“广告期间所有玩家输入冻结、恢复状态完整”。**

- 静态成立：B 的瞄准开始/移动/释放以及滑条业务回调检查广告 token；广告开始先登记 token 再取消正在进行的瞄准；token 集合按对象身份幂等，剩余 token 或 host pause 可继续阻止主逻辑推进。
- 静态缺陷：滑条控件内部没有广告/host guard 和指针 owner；广告期间仍可重新进入拖动并改变 value。教程中断后无显式终态恢复入口。restart 不清滑条拖动状态。
- 静态风险：pause/其他业务入口缺少统一广告门禁；rewarded 的请求代际与 ticker 启停所有权可能脱节；缺终态可能一直锁住；暂停收尾异常可能留下部分清理状态。
- **真实浏览器与真实 GameSnacks 宿主验收：BLOCKED（未执行），不是 PASS。** 本次没有局部可执行夹具、构建、试玩包或运行截图。

报告内 PASS/FAIL 只针对明确注明的静态断言。NEEDS_CONTEXT 表示需要 SDK 合同或业务政策；BLOCKED 表示未具备/未执行运行验证。

## 2. 参考身份、读取证据与方法

两份源码仅按用户提供的参考版本对照；不能据文件名推断 A 是线上基线或 B 已部署。目录中的长标识不能直接作为文件内容 SHA256。本次没有取得两份文件的独立全文哈希，也没有做全文机器 diff。

- A：`ref/mcp-inputs/mac-codex/31fbe829f0056d30c46a725ac47b64ee98146b0df711a11d00ca623f345b67c2/interstitial-reentrancy-fixed.js`
- B：`ref/mcp-inputs/mac-codex/9c61aa2e8412c33c3665d7a504f530ec7286c41dbe0ac42150f92191d33e7be5/ad-player-guard.js`

实际通过 read_reference 读取。下表范围为读取工具的 offset 区间（字符片段定位），不是源码行号；函数名是主要定位锚点。

|证据|版本及片段|定位内容|
|---|---|---|
|E1|A/B 0–84000；B 再读 61000–73000|host API、初始化、slider 业务监听、`_carromCancelAim`、原生取消事件、`_0x5480e3` restart、教程入口|
|E2|B 84000–114000；A 100000–113000|`_0x5e0129` pause、arena 入口、interstitial/rewarded wrapper|
|E3|B 114000–174000；A 157000–173000|回合、baseline 校正、玩家 down/release/move、延迟结算；B 局部再次读取|
|E4|B 216000–264000；A 254000–262000|主 tick、物理步进、键盘/stage 入口、token 与原生 timer 管理|
|E5|B 468000–492000|`_0x570109` slider 控件完整定义、striker impulse|
|E6|B 492000–516000|按钮控件、Tweener 更新与 extract/addTween 策略|

B 174000–204000、420000–468000 等片段亦读过，仅用于定位，不据此宣称完整 UI 或所有调用点穷尽审查。A 未读全文，因此比较只覆盖已核对的对应函数。

使用的冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`，均实际读取。选定 Skill `game-reverse-engineering/SKILL.md` 已读；采用证据协议、global-rules、unknowns-ledger-template 及广告 fallback/lifecycle 配套参考的通用方法。sdk-replacement 模块入口读取被本轮选择权限拒绝，未声称采用该模块全文。

实际参考依赖 **PIXI、planck（box2d 别名）、Howler、GameSnacks**，不是已实现的原生 Canvas 2D 工程。配置的 canvas-web 仅为工作流技术标签。本次不进行有范围影响的引擎迁移，因此无须为只读审查暂停选型；若下一阶段要求迁移，应先确认范围。

## 3. 保留的玩法与输入契约

不新增玩法。现有核心循环为：玩家回合定位 striker → pointerdown 建立瞄准所有权 → move 写方向/力度 → owner release 达阈值施加冲量 → 固定步长运动及进袋检测 → 静止后结算/犯规返子 → 下一回合或胜负结果。广告为跨状态阻塞原因，而不是回合/胜利状态。

- 物理：`_0x1392b5.step(1/60,10,10)`，每逻辑 tick 一步；ticker delta 累加于 `_0x990fb7`，循环条件为 `>1`（不是 >=1）。广告/host pause 清 accumulator，阻塞时不累加。未见主 accumulator 的最大追帧步数限制；超长非广告帧应另测，不在此改物理参数。
- 碰撞：圆盘物理碰撞与静态边界；进袋扫描以盘中心距袋中心 <=20 判断。baseline 校正以 `_0x133600+16` 检查占位，左右按2单位搜索，再尝试开放 baseline。全堵时没有保证找到位置的结果通道。
- 出杆：力度归一化并截上限1；release 力度 >=0.25 才施加 `strength * _0x301cde *1.25` 的冲量。settlement 先延后2300ms（Tweener 游戏时间）再检查运动，仍运动则重试。
- 计分/胜负：结算按模式及 `window.CarromDiscRules` 决定；现有 round/turn guards 与结果幂等标志保留。外部 DiscRules 实现未提供，本次不编造各模式目标分/queen政策。广告期间不得因玩家输入改变分数、回合或产生冲量；奖励广告业务结算属于另一 owner，不应混作玩家出杆。
- 成功验收：阻塞期零新增玩家冲量；解除全部阻塞后必须建立新输入序列；暂停原因彼此不覆盖；教程未完成且仍属当前玩家回合时能恢复适当步骤。
- 失败验收：旧指针松手出杆、滑条旧拖动继续、提前释放其他 token、host pause 被 afterAd 解开、广告结束教程消失、旧局任务修改新局，任一项出现即 FAIL。
- 输入窗口：锁从 beforeAd 调用 `_carromAdPause(token)` 登记 token 的同步时刻开始，到对应终态释放最后 token 且无 host/game pause 才允许新玩家操作。广告请求/准备到 beforeAd 之间不视作已有 token；如产品要求请求即锁，属于政策改变而非本补丁已实现行为。
- 可接受误差（验收建议，不是已测结果）：token/owner/shot count/score/turn 断言严格零误差；锁后的同一 JS 任务内取消输入。暂停前后物理状态浮点差 <=1e-6 世界单位（只比较未发生授权 baseline 校正/重开时）；baseline 与 slider 换算差 <=1e-6，画面投影差 <=1 CSS px；恢复提示最迟下一可渲染帧出现且循环 tween 不重复。原生 timer 剩余时间以受控钟严格断言，真实浏览器仅允许调度晚到、不允许广告时间被扣除。

界面审查布局：棋盘/striker 与瞄准层、底部定位滑条、教程遮罩/手势/文字、pause modal、结果页与广告按钮。没有新增画面或美术资源。默认玩家语言 English；后续若添加提示可用 `Ad in progress`、`Drag to aim`、`Release to shoot`、`Move the striker`、`Paused`、`Resume`、`Restart`。本轮未交付 HTML，故不宣称 lang=en 或中文浏览器默认语言已验收。

## 4. 静态对照与保护边界

### 4.1 A → B 的已核实有效改动

E1/E3/E4：

1. 玩家 `_0x36ab44` down 增加 token guard；`_0x536112` move 增加 token guard；`_0x1e39ba` release 增加 token guard，阻塞分支清 aim/三类 pointer owner/表现/strength，不施加冲量。
2. slider change/stop **业务监听器**增加 token guard，阻止更新棋盘 worldX/教程推进和 stop 业务校正。
3. `_carromCancelAim` 的教程恢复条件增加“无广告 token”。
4. A 的 `_carromAdPause` 仅入集合、清 accumulator、暂停 timer 与同步 mute；B 在入集合后增加 CancelAim、滑条占位校正与 `_sliding=false`。

这些改动不等于 slider 内部、按钮与业务 API 全被冻结。

### 4.2 广告开始顺序与瞄准

**PASS（静态、正常路径）**：`push(token)` 先于 CancelAim，避免取消时错误重开教程；有效 aim 被清且力度归零。锁内 release 即使非 owner 也进行统一清理，不会出杆；这属于阻塞期取消语义，不应误报为多指偷出杆。

**风险 R4 / P2**：CancelAim 在 `!aim` 时早退，不清残留 pointer 或教程/AI aim 表现。不能据此断言所有状态下 aim 图像必隐藏、strength 必为0；AI/教程也使用同一表现对象。需将玩家输入状态与演示视觉分开定义。

**风险 R5 / P1**：CancelAim 不在 `_carromAdPause` 的保护性 try/finally 中；异常会中止后续滑条和原生 timer 收尾。slider 校正异常被吞掉后仍清 `_sliding`，无可用位置也无显式失败反馈。应集中取消输入，确保 timer/mute 收尾并记录错误，不能只 rely on ticker.stop。

### 4.3 滑条：明确遗漏 F1 / P1

**FAIL（静态）**，E5：slider.startSlide 只检查 `_enable` 和 `_sliding`；move 只检查同二者，直接改内部 striker.x/value 后 emit；stop 只清 bool 后 emit；`setEnable(false)` 只改 `_enable`/alpha，既不改 interactive，也不清 `_sliding`。

可构造路径：beforeAd 清 `_sliding` → 广告期间新 pointerdown 再令 `_sliding=true` → move 改 slider.value，但业务 listener 因 token return，棋盘位置不变 → 最后 afterAd 释放 token → 无新 down 的 move 继续旧拖动，业务 listener 已可更新棋盘。若广告期间 down 后没有 move，恢复后同样可直接接续。是否真实事件能穿透宿主遮罩待浏览器/宿主测，但源码保护边界已不满足全输入冻结。

slider 不记录 identifier/native pointerId/type：第二指可 move/stop 第一指的拖动。广告未保存 view.pointerEvents，也没禁用 slider；仅 host pause 禁用 view DOM pointerEvents，不能代替 slider 方法门禁。

建议：控件 start/move 增加统一 canPlayerInput；取消时清 bool、owner、拖动基准，并同步 value 到实际合法棋盘位置；停止事件核 owner。不得将控件 value 修改留到业务 listener 拒绝之后。

### 4.4 “归位”不等于中点

E3：`_0x41684e()` 仅当 striker 发生占位冲突才向左右/开放 baseline 搜索，找到后同步 slider.value、alpha、overlay。无碰撞则保留位置；全堵可能找不到。**不能写成广告开始必将滑条设为0.5。**

正常正在拖动的输入终止是明确意图；占位校正可能在 token 已有效时改变 striker 位置，因此物理冻结断言应在授权收尾后取快照。F1 导致恢复后的 slider/棋盘不同步，即使收尾时无碰撞也不能靠 `_0x41684e` 自动修复。

### 4.5 教程：明确遗漏 F2 / P2

**FAIL（静态恢复路径）**，E1/E3/E4：step1 pointerdown 调 `_0x279414(2)` 隐藏提示但不完成教程；beforeAd CancelAim 因已存在 token 不恢复提示；`_carromAdResume` 仅 splice、mute、resume timers，没有 `_0x25e9ed`。host.resume 同样没有提示恢复。

另一路径：step0 slider change 已隐藏提示并推进 step1，广告在 stop 前到来；beforeAd 清 `_sliding` 且未执行 stop 的教程恢复，afterAd 仍无恢复。玩家仍可能凭经验操作，但“中断恢复教程”不成立。

未进行操作的可见 step0/step1，ticker 恢复后原 tween 可继续，不能说所有教程都丢失。E6 addTween 会 extract 同 target 旧 tween，故不能仅因多次 show 断言必重复循环。

建议：在综合 blocked → unblocked 边沿、当前 round/turn/玩家可操作且教程未完成时恢复当前步骤；不要每个 token 完成就恢复。仅补 afterAd 不够，host.resume 也需同一恢复 owner。新提示演示可有非零视觉力度，但玩家 aim/owner 必须为空，不能把演示力度当已武装出杆。

### 4.6 瞄准指针所有权

**PASS（静态有限边界）**，E1/E3：normal move/release 核 PIXI identifier 和可获得的 pointerType；outside/cancel 用 native pointerId 优先及类型核对；touchcancel 核 changedTouches.identifier，仅无剩余 touches 时作兜底。down 要求有效 identifier。

**风险 / P2**：PIXI move/release 不再次核 native pointerId，pointerType 缺失时放行；真实 PIXI identifier 与原生 ID 的映射、触摸兼容分支要实际测。release 正常分支不再次核玩家可操作/玩家回合，依赖所有回合转换已取消 aim。失效状态注入及 timer 到期转回合需复测，不将其直接定性为正常用户必能越权。slider 的 owner 缺失见 F1。

### 4.7 多 token、host pause、ticker

**PASS（静态 token 集合）**，E4：重复 pause 同 token 不重复插入；resume 未知 token 不改变集合；仅移除指定对象；还剩 token 或 host paused 时 timers 不 arm。mute 综合 host/audio/焦点/token。主 `_0x4bf21a`、`_0x49d791` 亦检查阻塞，所以先结束一广告无条件 ticker.start **不等于物理必然推进**。

host.pause 独立 bool、清 accumulator/取消 aim/结束滑条、保存并禁用 pointerEvents；host.resume 只解除 host 原因，resumeTimers 内仍核 token；不应把恢复 DOM pointerEvents 当成所有广告锁失效（瞄准 guard 仍生效，但 slider 内部有 F1）。

**风险 R1 / P1**，E2：interstitial finish、rewarded 常规 afterAd/异常分支直接 ticker.start，未统一 owner。旧 rewarded afterAd 会先释放其 token，再因 generation 已变 return，可能不 start ticker。若旧广告是最后停 ticker 的请求，而新代际仅 prepared 尚未 beforeAd，token 已空但 ticker 可能仍停。具体重入路径需受控 SDK 回调验证。推荐一个综合运行状态协调器决定 ticker、timer、mute、输入与教程；不能让旧代际碰新请求业务回调，也不能因代际过期放弃自身暂停资源收尾。

游戏内 `_0x3e61d0` 由 tick 与玩家 down/release 拦截，但不包含于 MatchBlocked。原生 match timers 只冻结 host/token，不冻结游戏内 pause；所读 timer 管理带 intro match owner，不宜笼统称为“所有游戏 timeout”。Tweener 延迟受主 tick 冻结。用户暂停期间原生 timer 是否应冻结标 NEEDS_CONTEXT，宿主 pause 与用户 pause 不应互相覆盖。

### 4.8 pause/restart 与其他入口

**明确遗漏 F3 / P2**，E1/E5：restart 清 aim/owner/力度并 round++，可防旧 aim release 打入新局；但未显式清 slider._sliding，而 disable 不清该状态。无广告时的持拖重开亦可能在下一回合 enable 后接续旧 move。广告内 restart 还会重建回合/调用 rewarded prepare，但保留 host/token；保留暂停原因本身正确，是否允许重开需业务定义，不应强制把 token 清空。

**FAIL（静态全入口门禁断言）**，E2/E4/E6：`_0x5e0129` 仅检查游戏内 pause，没有 token/host；瞄准手动取消分支缺统一 strength 清理，并可在设置 pause 前展示教程。modal close/home 直接改交互状态；arena `_0x4d0a10` 有费用/重复进入检查但无综合 pause guard，广告请求后直接创建 match。按钮控件 down/up 无 token guard；舞台 `_0x152e94/_0x12774a` 可在 token 时改辅助坐标；keydown 可写 `_0xb768e8`，左右 switch 当前为空，**未发现当前键盘直接出杆，不据缺 guard 编造键盘出杆漏洞**。keyup 清键是可保留的取消语义。

建议：玩家动作与允许的 host/SDK 管理动作分门禁。玩家 pause/home/arena/重开明确拒绝或排队；host.restart 若授权可执行，必须取消旧输入、更新 round、保留外部暂停原因。visibility 返回调用游戏内 pause 亦需明确政策，避免 afterAd 后无故留在 pause modal。真实宿主遮罩是否拦截按钮不能当源码门禁证据。

### 4.9 广告业务终态与异常

E2：interstitial done 防重入，beforeAd 后 afterAd 或 adBreakDone/异常可释放自己的 token；continuation 受 try/catch。rewarded 每请求 token 独立，pending callback 先登记再 show，viewed/dismissed 用 resolved+generation 去重，这是有效的同步回调保护。

**风险 R2 / P1，NEEDS_CONTEXT**：rewarded 无 adBreakDone 兜底，beforeAd 后缺 afterAd 可能永久持 token；afterAd 若先于 viewed，会清全局 callback 并启动新 generation，随后 viewed 被代际拒绝，业务可能无结果。不能不查真实 GameSnacks 合同就断言这种顺序合法。无 show 函数 `_0x4d02b5` 直接 return、不通知失败；prepare catch 也未明确通知 pending false，UI若先移除会失去恢复回调。

viewed/dismissed 的业务 callback 在释放 token 前运行，允许切 UI/重开/创建新请求；需核新 owner、旧 terminal、token 与 ticker 的交叉次序。旧胜局奖励回调先幂等授予捕获 prize 后才核 round/UI owner；属于持久奖励政策，不是本轮证明的输入漏洞，不擅自改变奖励归属。

## 5. 广告恢复必须满足的不变式

1. token 集合仅删对应 token；重复/未知终态不再触发提交；还有任一外部阻塞时不恢复物理与原生 match timers。
2. 当前玩家 aim=false，三类 pointer owner=null；旧 release 不施加冲量；新 pointerdown 后才可能出杆。演示/AI视觉另行判定。
3. slider._sliding=false、无旧 owner/拖动基准；value 与合法 baseline 位置一致；不得用旧 move 开启恢复操作。
4. host pause、用户 pause 各有 owner，afterAd 不擅自清；综合解除后 ticker/timers/mute 的状态一致，不“token空但ticker死停”。
5. 当前 round/turn 仍有效；旧 owner callback 不改新局；计分提交只一次。
6. 教程恢复由综合解除边沿与当前局状态决定；不完成/跳过未完成教程，不重复循环 tween；被 modal 遮挡时不抢显示。
7. 非广告原有 audioDisabled/失焦/用户静音不被广告终态覆盖。
8. 正常终态与异常终态都收尾，未知 SDK 生命周期保留日志与请求 ID；不得超时自动授奖。

当前 B 对1和2的正常路径有静态支持；3存在 F1/F3；4有R1及用户暂停政策待定；6有F2；5/7/8仅部分静态覆盖，尚无运行 PASS。

## 6. 可复现测试矩阵（全部待执行）

测试前固定 A/B 文件实际哈希、完整依赖与资源、相同初始局面/模式/随机种子；记录事件时序、request/token ID、round/turn、aim/owners、strength、slider state/value、棋盘位置/速度、shot count、timers、ticker、mute、教程可见性与 tween 数。受控 SDK 夹具持有每请求回调，不能把直接函数调用视为浏览器输入；混淆闭包需只读测试 hook 或专用测试构建，不假设这些内部函数在 window 上公开。

|ID/层级|前置与步骤|严格断言/预期|
|---|---|---|
|T01 局部+浏览器|玩家回合 down(P1)，move 到力度0.8；执行 beforeAd(A)；token期间 move/up；afterAd 后再发旧up；最后新down/move/up|锁开始清aim/owner/力度；锁内和旧up shot=0；新序列shot=1。A作为对照可能失败，B正常路径应通过|
|T02 局部+浏览器|先无拖动；beforeAd；slider down→move；afterAd 后不发down只move/up|阻塞时 value/棋盘不变，恢复后旧move不改棋盘。B源码预测 FAIL（F1）|
|T03 局部+浏览器|拖slider到合法非中点与冲突位置，各执行beforeAd；含全baseline堵塞布局|清_sliding；合法点保留而非强制0.5；冲突点校正并同步value；全堵明确不允许非法出杆且有失败策略（当前策略不足）|
|T04 浏览器|教程step1 down隐藏提示→beforeAd→afterAd，不做额外点击；host-only pause/resume同测|当前教程步骤不跳过，综合解除后提示恢复一次。B预测F2|
|T05 浏览器|教程step0 slider move推进step1，未stop即beforeAd，广告内/后释放|step1能恢复；旧drag不能继续；未完成教程不能误保存完成|
|T06 浏览器+触摸设备|P1 aim，P2 move/up/cancel；同identifier但不同type；PIXI ID与native ID不同；touchcancel另一指、owner指|非owner不改aim/不出杆；owner取消清理；广告期任何release只取消。记录原生到PIXI映射|
|T07 浏览器|aim/slider分别拖出canvas，upoutside、pointercancel、touchcancel；仅owner松手；含触摸兼容分支|不残留aim/drag；返回画布无需遗留up；slider owner/outside路径需重点查|
|T08 局部|pause(A)、重复pause(A)、pause(B)、resume(A)、重复resume(A)、resume(unknown)、resume(B)；倒序结束再测|集合数量1/1/2/1/1/1/0；B仍有效时logic/timers不推进；每终态仅收自身资源|
|T09 局部+浏览器|host.pause→beforeAd→host.resume→afterAd；beforeAd→host.pause→afterAd→host.resume；原pointerEvents值非空|任一原因存在时不推进；原DOM样式精确恢复；slider内不能靠host解除而绕广告锁；教程只综合解除后恢复|
|T10 浏览器|用户pause在先再广告；广告中尝试pause/home/modal close；切hidden/visible后终态|afterAd不清原用户pause；不错误创建/关闭modal；原生timer是否冻结按明确政策验收|
|T11 局部+浏览器|持aim和持slider分别restart，广告内/外各测；新回合enable后只旧move/up|round变化、旧aim无shot、旧slider不继续；token/host原因保留。slider预测F3|
|T12 浏览器|token中真实点击pause/arena/奖励按钮，键盘左右重复down/up；受控直接调用业务入口单独测|玩家状态/费用/回合不因未授权入口改动；清键允许；当前键盘无shot，不把空switch当射击测试|
|T13 SDK夹具|同步beforeReward→show→beforeAd→viewed→afterAd；dismissed；show抛错、prepare抛错、continuation抛错；重复终态|pending先登记；callback最多一次；自身token清理；UI失败可恢复；其他token不受影响|
|T14 SDK夹具+合同核对|beforeAd无afterAd；afterAd先于viewed；adBreakDone only；beforeAd晚于finish；旧generation终态|分合法/非法SDK序列记录；不重复奖、不删新token；异常请求有可诊断收尾政策；不超时授奖|
|T15 SDK夹具|reward viewed业务回调内restart或prepare新reward；旧afterAd在最后；新请求仅prepared未beforeAd；再混interstitial|锁空且无其他pause时ticker正常运行；新请求callback不被旧终态清；复现R1候选|
|T16 受控钟+浏览器|射出后运动中beforeAd，等待5s以上并结束；timer到期边界同任务前后插beforeAd；同固定输入模拟30/60/120fps及长帧|收尾后物理/score/turn冻结；remaining不扣广告时间；恢复不补广告期间步；正常游戏延时/碰撞按相同输入时间重现|
|T17 浏览器+宿主|原audioDisabled/失焦/手动静音分别开启→广告开始结束；两个广告交叉|mute由所有原因合成，广告结束不越权取消静音；实际声音以宿主证据核验|
|T18 最终dist浏览器|桌面及手机视口真实点击核心序列，中文浏览器locale重复；记录console/pageerror与截图|默认英文与lang=en（若交付网页）；无错误；最终dist相对资源可用，不引用源码试玩|

真实浏览器至少桌面1280×720、手机390×844；真实触摸与宿主不能用桌面模拟替代。浏览器脚本需启动本地静态服务访问最终dist、自动停止服务，截图/事件日志写evidence。真实宿主还需广告请求/终态日志、暂停回调与遮罩输入证据；不承诺当前没有的ADB/编辑器/外部服务操作。

## 7. 验证记录、未知与下一步条件

### 本次真实执行

- 完成：两份真实参考的关键片段静态读取与对应函数比较；控件/回调/主循环分层审查；可复现测试设计；写入本报告。
- 未执行：局部脚本测试、npm run build、npm test、npm run check、Chromium、手机触摸、真实GameSnacks宿主、广告声音/遮罩测试、包体/加载/内存测量。
- 原因：本次为原型只读审查，工作区起始目录清单为空，没有完整运行HTML、依赖/资源/DiscRules、package.json或宿主测试入口。不能用新造页面或模型脚本冒充原游戏构建。
- 未生成AI图像、资源清单或试玩ZIP；当前阶段无美术需求。无源码变更、无修补发布。

### 未知清单

|未知|影响|解除条件|
|---|---|---|
|A/B实际部署身份及全文hash|不能下线上已修复结论|提供完整版本/部署映射并独立计算内容hash|
|GameSnacks版本/合法回调顺序/失败终态合同|R2是否正常宿主必遇、恢复责任不明|提供本项目SDK合同及回调日志|
|完整HTML、PIXI版本与资源、DiscRules|不能真实输入/碰撞/胜负验收|完整可构建包与固定局面|
|广告遮罩是否截断/透传pointer、host回调次序|F1/F3运行触发频率未知|真实宿主及手机证据|
|用户pause、host.restart、请求期锁与持久奖励政策|是否拒绝/排队/保留回调未定|修复阶段确认具体政策；本报告不自行改政策|
|所有独立setTimeout/业务入口调用点|不能声称穷尽全入口、全timer|完整入口索引及补充代码搜索/运行覆盖|

建议代码阶段优先：F1控件门禁/owner/取消 → F2综合恢复教程 → F3重开清slider → R1统一运行状态协调 → 合同驱动R2终态异常收尾。这只是修复建议，不是用户确认或已完成修改。若授权修复，先取得完整工程及上述政策，再在最后源码/资源修改后真实执行 build/test/check；check验收最终dist，验证后不重建dist。只读审查到此收口。

产物：`/workflow/prototype.md`（本报告；工具根目录为本项目工作区，不重复嵌套 games/项目ID）。
