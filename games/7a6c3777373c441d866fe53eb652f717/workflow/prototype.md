# Carrom 当前触控函数只读复核

## 范围与证据

本轮为 prototype 阶段的专项源码审查，不制作新游戏、不修改源码、不构建、不发布。用户的专项范围优先于通用原型模板。

当前证据为任务正文粘贴的函数原文。用户声明完整 game.js SHA256 为 `8d8364b690ad035a713944e3445def683271915398509e74380063224f07e6c0`；本轮未取得该完整文件，未独立计算此哈希，不能证明摘录以外代码、调用方、初始化、字符串映射、PIXI 版本及生命周期清理与当前完整文件一致。当前定位使用函数名和精确语句，不虚构当前文件行号。

旧参考 ZIP：`ref/mcp-inputs/mac-codex/736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99/Carrom_current_development.zip`，工具返回包 SHA256 `736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99`。

已实际读取的旧上下文：

- 包内 `development/js/game.js`，SHA256 `3140ae1bd16fd91b6c025fc3641f2ff41e9f26e2b7200c94810199ada22a1573`；研究副本 `/reference-inputs/old-game.js`。
- 包内 `development/js/libs/pixi.min.js`，SHA256 `e6c608465f403d0201603f31b369cfecea242eaff4b905b6fbaa6efc42c8e57e`；研究副本 `/reference-inputs/old-pixi.min.js`。头部标明 PIXI 4.8.9，已读取 InteractionData/InteractionManager 相关正文。

旧 ZIP 仅是上下文，明确不是最新完整源码。没有整包导入、执行参考代码或将其作为新游戏交付。

已读取冻结技能 `casual-game-production/SKILL.md` v1.3.0，以及 `genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/native-web.md`。本次应用其证据分层、输入归属和生命周期审查方法，不扩大到美术、代码或测试阶段。

## 结论

当前摘录对正常 down/move/up 的 identifier 归属检查基本连贯，不能认定正常鼠标或触屏被新增检查普遍阻断。可见薄弱点集中在取消路径只保存编号而未保存来源、暂停分支先于归属检查、以及瞄准会话未在这些函数内绑定局/回合。是否已由当前完整文件其他位置消除，需要补充证据。下列均为静态推导，未声称浏览器复现通过。

## 1. 正常输入与两个触点：已有保护

旧 game.js 第1574行为 `_0x27e1b4["on"]("pointerdown", _0x36ab44)`，直接传 PIXI InteractionEvent；并非无参包装调用。当前 down 中 `if (!_carromEvent || !_carromEvent.data || _carromEvent.data.identifier == null) return;` 允许编号0，随后保存标量 `_carromEvent.data.identifier`，不会因 PIXI 复用事件对象而自行改变保存值。当前调用方是否仍相同未证。

旧 PIXI 的 `getInteractionDataForPointerId` 对鼠标使用 `this.mouse`，其 identifier 固定为1；TouchEvent 规范化使用 `pointerId = identifier || 0`；非鼠标通常使用规范化 pointerId。支持 TouchEvent 时，PIXI 忽略 pointerType=touch 的 PointerEvent，转而处理 TouchEvent。因此 Touch.identifier 与原生 touch PointerEvent.pointerId 不是可任意互换的编号。编号1也可能对应 Touch，本身不代表鼠标。

当前 `_0x536112` 和 `_0x1e39ba` 在 owner 非空时拒绝不同编号或缺 data 的事件。A开始瞄准后，B按下被 `_0xf86500` 阻止，B移动或抬起被 identifier 比较阻止；A移动更新力度，A抬起才提交。Touch identifier=0 可正常通过。该结论以事件确实到达相应处理器为前提。

力度为距离/`_0x647bf3`，距离上限被截断；release 的 `strength >= 0.25` 才发射，强度恰为0.25属于发射侧，初始强度0的点击不发射。发射参数为 `strength * _0x301cde * 1.25` 与 `2*Math.PI-angle`。release不重算最终坐标，使用最后一次move的力度；这属于当前行为，是否需以抬起坐标为准取决于产品约定，不直接判缺陷。

最小回归：分别用鼠标、Touch 0、Touch非零编号完成down→move→up；力度0、0.249999、0.25、1分别断言发射次数0、0、1、1；重复up不追加发射。A=0、B=2及A=1、B=2各执行B move/up，断言A归属与力度不变，再由A完成一次发射。全部待执行。

## 2. touchcancel 的无剩余触点兜底会跨来源取消

精确代码：`if (!_carromEvent.touches || !_carromEvent.touches.length) _carromCancelAim();`。此分支不要求 changedTouches 命中owner，也不检查正在瞄准的是Touch、鼠标还是笔。

可由摘录直接推导的条件：鼠标或笔正在瞄准，另一只手的最后一个触点发生touchcancel，事件冒泡到document，`touches.length===0`，即使其identifier与owner不同也取消当前鼠标/笔瞄准。混合输入设备可产生此类序列；具体浏览器实际派发情况未测。不能把它描述成同一文档内两个正常Touch中“B取消、A仍在touches里”也必定误取消：在该正常序列中touches非空，兜底不会执行。

最小测试：mouse owner=1、strength=0.5，调用取消处理器，事件为 `changedTouches:[{identifier:8}], touches:[]`；静态预期当前实现取消鼠标瞄准，目标应保持。对照Touch A=0、B=8，B cancel且touches保留A，预期保持；A cancel且touches保留B，预期清除owner、归零且不发射。直接调用属于处理器级测试，不能替代真实混合设备事件验收。

建议的最小修复方向仅供后续代码阶段：保存输入来源与对应原生编号域，仅取消实际owner；是否保留全触点消失兜底应限定于Touch会话。本轮未实施。

## 3. pointercancel 比较存在编号域与来源风险

精确代码：`if (_carromEvent.pointerType === "touch" && "ontouchstart" in window) return;`，随后 `if (_carromAimPointerId != null && _carromEvent.pointerId === _carromAimPointerId) _carromCancelAim();`。

若当前仍使用所读旧PIXI，忽略touch PointerEvent的分支与该PIXI策略一致，不能简单认定它漏掉正常Touch取消；后续应由touchcancel处理。普通Touch的identifier与原生pointerId不同，也不能因此误报正常move/up失配。

但鼠标PIXI identifier固定为1，原生鼠标pointerId若不是1，owner鼠标pointercancel将不能命中；反之，不同来源事件编号恰与当前owner相同，则可能误取消。例如Touch identifier=某个笔pointerId，笔发生pointercancel时通过比较。编号相同不能证明是同一输入会话。此为结合旧PIXI的条件性风险，当前运行库版本、平台pointerId及混合设备实际序列缺证，不能宣称所有浏览器必现。

最小测试：在真实PIXI链路记录 `event.data.identifier`、`data.pointerType`、`data.originalEvent.pointerId`。鼠标原生ID非1时开始瞄准并派发对应cancel，确认是否仍保持active；另以Touch owner=7、无关pen cancel pointerId=7验证误取消。pointer-only触屏环境（无ontouchstart）应验证其owner pointercancel正常清理。真实事件目标需位于canvas并冒泡至document。document的监听器不是window捕获监听器，对仅派发在window上的合成事件不保证收到，不把这种合成失败作为真机缺陷。

## 4. 暂停release绕过owner检查，清理不完整

精确代码：`if (_0x3e61d0) { _0xf86500 = false; _0xc5bee4.visible = false; return; }` 位于 `_0x1e39ba` 的active和identifier检查之前。它不清 `_carromAimPointerId` 和strength，任意编号release都可进入该暂停分支。

可确定的局部行为：若active瞄准期间暂停标志变true，非owner B的release也会清掉A的active；返回后owner仍旧、strength仍旧。再调用 `_carromCancelAim` 会被 `if (!_0xf86500) return;` 挡住，无法清掉该残留。不能把这直接说成恢复后必然误发射：active已false，普通release会返回，下一次合法down会覆盖owner和strength。实际危害取决于其他代码是否读取这些残留或如何恢复教程。

旧快照第2300–2351行菜单暂停会提前清active并隐藏，但未归零strength；旧第2036–2039行宿主暂停仅设暂停标志并停ticker，未显示瞄准清理。它们说明需要检查哪些入口，不能证明最新版本入口未修复。

最小测试：A开始并拉至0.5→宿主暂停→B release→记录active=false、owner仍A、strength仍0.5；断言不发射；恢复后合法down/move/up仍可完成。菜单暂停、宿主暂停分别测试；取消后教程是否恢复应单独观察。

## 5. 切局/切回合的旧手势没有在摘录内绑定生命周期

down只保存identifier，move未检查暂停、玩家输入许可、round或turn，release除暂停外也不复核 `_0x55e693`、`_0x209883` 或down时round/turn。`var _carromPlayerShotTurn = _carromTurnId` 在release时采集，不是开始瞄准时采集。

条件性复现：A瞄准→回合超时或切局→若外部未清active/owner且事件仍可到达→A move更新新状态、A release可能对新局/新回合发射；release时采集的新turn不能阻止这次旧手势提交。旧快照 `_0x50a0ff` 第3549行及 `_0x5e7a5f` 第3633行增加turn，已读函数内未见清active；旧 `_0x5480e3` 第1768行增加round，但这不等于当前版本缺少统一清理。需当前这些完整函数、超时调用链及所有owner/active写入才能定案。

最小测试：A down→move 0.5→真实超时切AI→A up，发射计数不得增长；新局/返回大厅再开局重复同序列；不同round但复用同identifier也不得提交。不能仅修改计数器就称已覆盖真实切局链路。验收要求旧手势失效，新会话需新down。

## 6. 异常无data：通常被挡住，不应虚报可达崩溃

新down拒绝缺event、缺data和null/undefined identifier。在正常down建立的owner非空状态下，move/up的短路条件会安全拒绝缺data；identifier=0同样受保护。因此“正常按下后传无data立即导致move崩溃”与摘录不符。

潜在但未证可达的状态是 `_0xf86500===true && _carromAimPointerId==null`：move绕过owner条件，随后访问event.data.global可能抛错；release绕过owner条件，可能以已有力度无事件提交。摘录正常down不能建立该状态；已读旧源码也不能证明当前文件中有此写入。必须核对最新初始化和所有赋值，不能以手工注入该非法状态证明产品可达缺陷。另有data但缺global、数值非有限等仅属于异常对象边界，正常PIXI提供global；本轮无正常链路产生此异常的证据。

最小测试：从合法down出发调用move/up(undefined)、move/up({})、move/up({data:{}})，断言不抛错、不发射、不改变owner。非法active+null-owner单列防御测试，明确人工构造。

`_carromTouchCancelled(undefined)` 本身会访问事件属性抛错，但DOM addEventListener正常会传事件；没有无参调用方证据，不列正常可达缺陷。

## 7. 教程与异步补充核查

当前down调用 `_0x279414(0x2)`，达到阈值的up才调用 `(0x1)`；对照旧函数，case2只隐藏教程表现，case1才推进教程状态。这比旧down直接case1更符合取消后重试的路径。取消或低力度release会调用 `_0x25e9ed(0x1)`；旧实现该函数会重新显示演示瞄准线并启动教程动画，所以“cancel之后visible一定false”不是教程模式下的正确断言，应断言玩家active=false、owner=null、没有发射，允许教程演示出现。当前教程辅助函数是否与旧版一致未证。暂停release未执行这条教程恢复路径，恢复体验需测试。

当前AI移动及瞄准完成回调包含round/turn保护；延迟发射内部只显式检查turn和active。旧 `_0x338c29` 第5662–5674行捕获round并要求active，若当前仍如此，则外围已补齐round保护，不能仅凭内部未写round就判跨局执行。当前玩家release传turn给 `_0xbdafb3`，但旧第3197行该函数无参数：不能把旧实现用于证明当前参数有效或无效，需当前函数正文及递归调用链。

`_0xd6b627` 新增finite检查可阻止所列AI入参NaN/Infinity；return之后的旧代码不可达，不属于本次触控可达缺陷，也不能由这些检查推断整个物理数值链安全。

## 输入与验收契约

本轮保留既有玩法：观察棋盘→玩家瞄准→合法owner释放→物理运动→结算→下一回合。输入状态为idle/aiming/shot/paused/round-ended；期望一个瞄准会话由输入来源、编号和局/回合共同归属，取消不发射、旧手势不提交、一次up最多发射一次。布局只核验已有striker、瞄准线、暂停入口，不重设计界面。玩家文案保持既有产品，本轮未改动语言或资源。

输入窗口可从摘录确认：未暂停，教程不在第0步，两个许可标志均true，且没有现存active会话。未发现可从摘录确认的毫秒级输入窗口；0x8fc=2300是发射后安排结算检查的参数，不是输入允许时长，也不证明物理已静止。

物理步长、碰撞体/接触规则、进袋计分、胜负与失败、长帧补步、完整结算去重不在当前摘录证据范围，未更改或虚构参数。输入所有权、取消发射数、重复提交采用零容错；力度阈值用0.25两侧及恰好相等验证，几何距离应使用运行时实际坐标换算。跨帧物理位置误差需完整最新物理实现及平台基线后确定，本轮不宣称物理验收。

## 实际验证、交付与限制

本轮已完成：冻结技能/四份资料读取；ZIP真实条目及哈希读取；两份研究文本按字节提取；旧游戏相关函数及PIXI事件处理正文静态阅读；当前用户摘录逐分支比较。以上是静态证据复核，不是动态测试。

本轮未执行 npm run build、npm test、npm run check、浏览器、真机或合成事件测试；本轮为只读原型审查，没有创建测试脚本或可运行最新工程。全部最小测试均为待执行用例，不记为通过。不修改、不发布、不推进后续阶段。

交付：`/workflow/prototype.md`；研究副本 `/reference-inputs/old-game.js`、`/reference-inputs/old-pixi.min.js`，均标记旧参考，不进入发布。

进一步定案需要当前完整game.js（至少全部active/owner写入、事件字符串映射、当前PIXI、暂停/恢复/超时/切局、教程、调度器及结算函数），以及正常鼠标、Touch、Pointer-only和混合输入的真实事件记录。这是结论的证据边界，不妨碍交付本次摘录审查。
