# Carrom 红球在途恢复独立审查

请求：queen-pending-sprite-recovery-dd-review-20261113。阶段：prototype；attempt=1。仅进行参考源码静态审查，本轮仅写本报告，不修改游戏源码，不推进后续阶段。

## 结论与证据等级

dd 新增接管可修复普通模式结算时 HUD 引用尚未建立、但 pending 精灵仍存在的窄场景。真实 Tweener 实现支持正常 addTween 路径下取消当前入袋 Tween；没有证据证明接管后会自然残留旧入袋回调。不能因 extract 只处理首个匹配目标就认定漏洞：addTween 本身先 extract，在空队列且全部通过该入口创建的前提下，每目标最多存在一个队列 Tween。

本次不能给出“全面通过”结论：没有执行游戏、浏览器、构建或反例；没有完成机械全文 diff，也未建立准确源码行号。以下以真实函数名、原文及 read_reference 字符区间定位，不把相同字符偏移视为两版对齐行号。不宣称新增分支是全文唯一差异。开发者所述暂停动画、超时构造实验属于外部陈述，本轮未复验，不能替代自然对局证据。

## 参考及方法

当前 dd：`mcp-inputs/mac-codex/dd8b79747ae3b111ad0a83ec8088b69b7632ec9f122e685b76601e731d52ffe8/Carrom_current_dd8b7974.js`。

之前 bf：`mcp-inputs/mac-codex/bf0c02532d135d6ad96666c840a8da05e684fc6b795bf62a8f28075b478b6a36/Carrom_current_bf0c0253.js`。

版本名称按输入路径识别，不将目录名冒充本轮计算的文件哈希。已读取冻结 casual-game-production/SKILL.md v1.3.0、genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/native-web.md。采用一次提交、局生命周期隔离、规则与表现分离的审查原则；本任务为只读审查，不制作新玩法、资源或构建。参考目录未提供可直接启动的完整游戏依赖，CarromDiscRules 的实现未获取。

## 已确认的版本差异

两版 `_0xbdafb3` 的普通结算等待回调可在字符 144000 起附近定位。dd 在等待返场分支前增加以下原文，bf 对应位置没有该分支：

```js
if (_0x5d148e === 1 && _0x4268e2 && !_0x5ebd99 && !_0x404020 && _carromPendingQueenPocket) {
  Tweener.extract(_carromPendingQueenPocket);
  _0x404020 = _carromPendingQueenPocket;
  _carromPendingQueenPocket = null;
}
```

它要求普通模式、待覆盖、无续杆、HUD 为空且 pending 存在。先取消旧动画，再将同一个显示容器移交 HUD/返场引用，最后清 pending。其后两版均调用 `_0x52e61d(callback)` 并 return，成功 callback 清待覆盖、隐藏勾、推进回合。已有 HUD 时不会执行新增接管；成功覆盖使待覆盖为 false 时也不会执行。

## 实际引用链与状态

1. `_0x49d791` 更新中四袋距离检测均为 `<= 0x14`（20）。红球入袋同步设置 `_0x5ebd99=true`、`_0x4268e2=true`，调用 removeFromWorld，从 `_0x3231b3` 移除且保留显示对象，然后 `_carromPendingQueenPocket=sprite`。dd 四袋原文位于字符 203000 起的读取区间。
2. removeFromWorld 两版实现相同：destroyBody、body=null，移除发光子节点并清其引用；保留棋子容器。定义位于 `_0x54e9a5` 类，可在两版字符 437000 起的读取区间定位。故接管目标已无物理刚体，并非直接把旧刚体放回棋盘。
3. 入袋第一段为15 tick，移动到袋口并向 alpha=.7、scale=.9 插值；完成检查 active 与 round，随后普通模式创建20 tick HUD 移动。双方分别使用各自 HUD 坐标。
4. 第二段完成检查 active 与 round；仅 pending 等于自身时清 pending，但随后无条件写 `_0x404020=sprite` 并显示勾。四袋、双方共八条完成路径采用相同所有权模式。没有 turn 校验，也没有所有权不符即拒绝提交的判断。
5. 发射后约2300ms的等待触发 `_0xbdafb3(expectedTurn)`；结算还等待物理静止。该函数拒绝旧 turn 或重复结算，设置 settled 与计时=-1，提交普通棋得分/返场，随后经 `_0x338c29` 等待500ms或1000ms进入最终处理。
6. `_0x338c29` 用空目标 Tween 将毫秒换算为 `ms/1000*60` tick，完成检查 active、round；它不是独立 setTimeout。最终结算闭包另检查 round 与 turn。
7. 最终回调先强制提交普通棋结果，再调用 CarromDiscRules.hasWon 判胜负，之后才执行 dd 的 pending 接管。判胜负早退不会走接管，属于两版共有顺序；缺规则依赖，不能断言该顺序造成错误胜负。
8. `_0x52e61d` 捕获 round 与 HUD 精灵身份，调用 `_0x1f3ae5` 找返场位置，仅 HUD truthy 时创建15 tick x/y Tween。完成检查 active、round、当前 HUD 是否仍为捕获对象；成功新建物理红球、设置 world 坐标和 queen 类型、加入场景及红球数组、移除旧精灵、HUD=null，再调用结算 callback。dd 原文位于字符110000起的读取区间；两版返场函数已对照，逻辑一致。
9. 结算 callback 再检查 active/round/turn，清待覆盖、隐藏勾，调用 advance。玩家 `_0x5e7a5f` 或 AI `_0x50a0ff` 入口递增 turn。返场完成前不正常推进该回合。

主要状态：active=`_0x3fddb3`，菜单暂停=`_0x3e61d0`，局=`_carromRoundId`，回合=`_carromTurnId`，待覆盖=`_0x4268e2`，有效入袋/续杆=`_0x5ebd99`，HUD/返场精灵=`_0x404020`，在途精灵=`_carromPendingQueenPocket`。

## Tween 取消与异步幂等

真实 Tweener 位于两版字符475000..501000附近的读取区间。extract 严格比较 `_target`，找到后 stop 并 break；stop 设置 running=false 并从实时数组 splice，不调用 onComplete。addTween 总先 extract，再构造、入队和 start。update 正向遍历实时数组，同步调用 running Tween 的 update；普通到时先 stop，再同步 onComplete，没有已观察到的独立异步完成回调队列。因此接管、清 pending、发起返场之间不存在浏览器事件回调插入的异步窗口。

实时数组 splice 会让下一个元素本帧跳过；回调新增的项可能本帧更新。这是既有调度行为，可改变一帧时序，但不足以推出永久卡死。

返场成功先将 HUD 清空再执行外层 callback，同一完成回调再次被手动调用时会因身份不符退出，不能仅因没有 finished 变量就宣称重复创建。该结论针对串行重复回调；不覆盖外部改写引用或异常重入。

Tween.finish 先写终值、调用完成回调，再 stop，未见 running/finished 防护；stop 未保护 indexOf==-1。对已停止对象手动 finish、重复 stop 或在完成回调中异常重入可能破坏队列。未证明普通红球链实际会如此调用，列为条件性底层风险，不归为 dd 自然回归。

## 场景矩阵

| 场景 | 静态结论 | 归属与限制 |
| --- | --- | --- |
| 四袋 × 双方 | pending 设置、15+20 tick动画及八条 HUD 完成路径一致；新增接管双方共用 | 已读原文；未跑八组对局 |
| pending 存在、HUD 为空、覆盖失败 | dd 取消当前动画并等待返场；bf 可能走无HUD fallback后推进 | 新增分支覆盖的目标状态；自然触发频率未测 |
| 正常成功覆盖 | 普通棋清待覆盖，新增分支不进入；延迟 HUD 回调按待覆盖状态选择 filled/unfilled | 未发现新增直接副作用；未验证全部规则组合 |
| 犯规且本杆曾覆盖 | 普通结算可恢复待覆盖并清续杆，之后进入恢复判断 | 原有规则链；需实际组合测试 |
| 菜单暂停 | 更新函数在 Tween 更新前 return，结算等待和入袋动画一起冻结 | 暂停本身不等于只冻动画而结算继续 |
| 公开 pause/resume | 所读公开接口为空函数 | 不可与菜单暂停或广告 ticker 停启混称 |
| 重开 | 先丢弃 pending，再 round++；旧返场回调受round与身份保护 | 未证明旧回调能提交新局；HUD Tween未见显式extract，可能继续驱动已移除旧对象 |
| 退出 | discard pending 后 active=false，可拦旧提交 | 退出入口未都递增round；全部再进入路径未完成闭环核查 |
| 无HUD且无pending | fallback调用返场但不创建红球，仍清待覆盖并advance | 两版共有；需预先损坏状态，自然可达性未证 |
| 返场Tween被另行取消 | stop不调用callback，外层等待分支无完成兜底 | 两版共有；需取消前提，未证自然发生 |
| 重复返场完成 | 成功后HUD=null，后续串行调用被身份校验挡住 | 静态支持幂等；未执行 |
| 返场中操作 | `_0x24bb4a`关闭瞄准、输入与slider，计时=-1；输入入口与滑条事件有门禁 | 未发现正常链提前开放输入；未做浏览器事件测试 |
| Freestyle | 新分支限定mode=1，不直接介入 | 不借Freestyle的returned/finish兜底证明普通模式有同样保护 |

## 保留风险与反例前提

A. 两种精灵均缺失：构造棋盘无红球、pending=null、HUD=null、普通模式待覆盖=true且续杆=false。最终结算会跳过等待返场分支；返场函数不创建对象、不调用callback；fallback仍清规则并换回合。它证明无精灵恢复不完备，不证明正常游戏会自然到达该损坏状态。

B. 返场被取消：在等待返场分支已return之后、15 tick完成之前，对当前HUD执行extract。完成callback消失，当前结算不会正常advance，待覆盖保持。它证明缺取消兜底；需要外部取消或可达取消路径，未证明由新增接管自行触发。

C. 旧HUD回调被强制执行：捕获入袋完成闭包，在接管完成、pending已经清空后手动执行旧闭包。该闭包仅校验active/round，仍可能写HUD和勾，说明所有权校验不足；正常stop不会执行该闭包，因此不能把手动调用当自然残留证据。

D. 接管早于HUD完成时，返场仅插值x/y，不恢复alpha/scale；过渡精灵可能保留接管瞬间透明度和缩放。最终是新建物理红球，不能据此声称返场后红球永久半透明。视觉观感未实测。

E. `_0x1f3ae5`按32距离避让，四轴步长2、对角线及8..96的网格搜索均失败时仍使用原位置。此为原有有界搜索限制，本次不归因dd。

## 可执行调试步骤（本轮全部未执行）

需要完整原游戏及浏览器开发者工具；变量位于游戏闭包内，应在源码断点的当前调用帧执行，不能假设变量是window属性。以下只改调试会话内存，不修改磁盘源码；每项使用独立新局。

1. 目标接管对比：在四个袋口红球入袋设置pending后分别断住，捕获该精灵；通过开发者调度使其HUD动画尚未完成，而普通模式最终结算满足待覆盖且无续杆。记录构造方式。dd在新增分支前后核对旧目标Tween移除、HUD等于原pending、pending为空；继续推进Tween至返场完成，断言棋盘红球恰增1、HUD为空、turn只推进1次。bf同前提对照其fallback。双方各做四袋，报告构造实验与自然对局分开。
2. 无精灵反例：在最终结算的待覆盖判断前暂停，确认普通模式、无胜负早退、棋盘红球为空；在该调用帧设 `_0x4268e2=true; _0x5ebd99=false; _0x404020=null; _carromPendingQueenPocket=null;`，记录当前turn后继续。观察规则被清、turn推进而红球仍为0。若未满足其它结算前提，不计为复现。
3. 取消返场反例：在 `_0x52e61d`建立Tween后断住，于相同闭包调用帧执行 `Tweener.extract(_0x404020)`；保持active、round、turn不变并继续正常ticker。观察超过原15 tick后红球是否仍未生成、turn未推进、待覆盖仍真。不得把暂停ticker的时间计为有效推进。
4. 重复完成：在返场Tween完成前捕获其真实onComplete和原调用上下文；正常执行一次后再在调试器调用同一闭包。断言红球不再增加、turn不再推进。不得重设HUD引用，否则改变了幂等前提。
5. 生命周期：分别在第一段、第二段、返场段打开菜单暂停，记录Tween进度与turn，恢复后核对继续；再分别重开，确认round增加并持续推进旧Tween，断言新局红球数与turn不被旧结果改写。退出再进入需记录每条入口，不能仅测重开代替。
6. 输入及覆盖：返场中真实拖动底部滑条、按下/移动/松开瞄准、触发计时边界；断言无新发射或提前turn递增。另做正常覆盖、红球与普通棋同杆、覆盖后犯规，检查得分、勾、红球数量及双方回合归属。

## 验收口径与未完成范围

规则闭环为瞄准输入→发射→物理演化/入袋→覆盖或返场→结算→下一回合；本次沿用既有游戏，不另定计分和胜负数值。入袋阈值20、棋子碰撞半径16及动画15+20/返场15 tick来自源码；动画tick与真实物理步长不得混同。底层物理固定步长、CarromDiscRules计分/胜负及完整再进入链未在本报告中证实，不补造参数。

建议验收不变量：普通模式覆盖失败返场后棋盘有且仅有1枚红球；pending与HUD不继续拥有已返场旧精灵；每次结果/回合最多提交一次；旧局回调不改新局；返场期间不能合法发射；菜单暂停不推进模拟或结算。状态计数允许误差为0；位置误差应基于实际Tween终值与物理单位制定，当前无运行数据，不自称达到像素误差指标。

本轮实际执行：read_reference分段阅读两版、读取已选技能与冻结资料、查看工作区及workflow目录、写本报告。没有执行npm run build、npm test、npm run check、浏览器或调试反例；当前是只读prototype审查，非代码/测试阶段，未为审查创建或修改测试脚本。没有截图、运行日志或测试通过产物。

未完成：机械全文差异清单、精确行号、完整依赖核查、所有退出再进入闭环，以及自然对局与故障注入复验。当前可交付的是有边界的静态审查，不是完整运行验收。

唯一输出：`/workflow/prototype.md`。
