# Carrom 插屏结束与暂停恢复：原型审查报告

## 1. 范围、证据与结论口径

阶段：prototype；本次 attempt=1，恢复续接。只审查引用代码与定义验收，不修改游戏、不推进美术/代码/测试阶段。无上游已确认设计；下述建议不是已集成补丁。

参考文件（相对 ref/）：
- B：`mcp-inputs/mac-codex/309e9b1c0a3e10a44c4cc600897e02f203c40abf8a556fa059b9104b286c2dce/ad-before.js`
- A：`mcp-inputs/mac-codex/de2cfc7eac9d748af09307b139885429df5f0007286a30f655f4c76ae00da228/ad-after-end.js`

实际分段读取：两版初始段、90,000–114,000 字符附近的 `_0x248455`、`_0x2e33a4`、`_0x4d02b5`；A 继续读取 114,000–294,000 范围的消费者、输入、物理循环及 helpers；B 读取 249,000–265,000 附近核对主循环入口和相同 pause/timer helpers。初始大段输出有截断，不声称全文读取、全文件差分或全部调用者穷尽。使用函数名定位证据，不把字符位置当精确源码行号。不把路径中的字符串充当本次计算的文件 SHA256。

已读取选定技能 `game-reverse-engineering/SKILL.md` v10.5.0，以及 execution-protocol、global-rules、unknowns-ledger-template、ad-fallback-and-reward-lifecycle 配套正文。另读取全部四份冻结资料：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md。采用“实际 owner、请求去重与领奖去重分离、暂停归属、静态与动态分层证据”的方法，不套用其他项目测试结果。SDK 模块入口读取被平台拒绝（未选中），未绕过限制。

### 用户真实补充与官方语义

用户通过 request_user_input 回答：按官方契约及条件化审查，不假定 AHA 必然遵循。用户提供：
- https://developers.google.com/gamesnacks/developer/sdk/ad/break ：GameSnacks `ad.break` 包装 Ad Placement API，接受同样参数。
- https://developers.google.com/ad-placement/apis/adbreak ：`afterAd` 在广告结束后触发。
- 用户称本地 developer_v2.js 也有 beforeAd 暂停、afterAd 解除暂停；本次未提供该文件可读参考，未实际核查。

本平台无网页获取工具；以上是用户提供的官方文档说明和 URL，不声称本次联网读取，也未核对 AHA 实际 SDK 版本。引用代码使用混淆表达式 `GameSnacks.ad[_0x157421(0x49d)]`，本次未执行解码；与官方 ad.break 的映射须后续核查。

**总判定：正常顺序的插屏结束双回调去重为静态 PASS；完整异常/重入/暂停副作用幂等为 FAIL；真实宿主播放安全为 NEEDS_CONTEXT。没有动态验收 PASS。**

## 2. 核心差异

B 的 `afterAd` 是空函数，只在 `adBreakDone` 中释放 token、同步静音、启动 ticker、continue。
A 新增 `_carromFinishInterstitial()`，`adBreakDone` 直接调用，`afterAd` 仅在本请求 `_carromAdPaused` 为真时调用。finish 顺序：

```text
if done return
AdResume(token)
paused = false
SyncMute()
ticker.start()
Continue(): done = true; callback()
```

`done` 在恢复副作用之后才置位。因此“业务 callback 至多调用一次”和“恢复副作用至多执行一次”不是同一个保证。

按照用户提供的官方 afterAd 结束语义，A 在 afterAd 时释放本请求是合理的：它不是按任意延迟强行恢复仍播放中的本广告。若 AHA 错发提前结束事件、SDK 在仍展示时抛错、或实际方法并非该接口，本代码没有独立播放状态确认；最后一个 token 被释放且 host 未暂停时，游戏会恢复。官方说明不能代替这部分宿主验收。

## 3. 正常回调矩阵（无副作用异常、无同步重入）

记 P=beforeAd，E=afterAd，D=adBreakDone，C=可选业务继续；无其他暂停原因。

| 时序 | B | A | 判定 |
|---|---|---|---|
| P→E→D | E 不恢复；D 恢复及 C 一次 | E 恢复及 C 一次；D 忽略 | A 静态 PASS |
| P→D→E | D 恢复及 C 一次 | D 恢复及 C 一次；E 因 paused=false 忽略 | 静态 PASS |
| P→E，D 永不到 | token/ticker 仍暂停，C=0 | E 恢复，C=1 | A 补齐核心遗漏 |
| P→D，无 E | D 恢复，C=1 | 同左 | 静态 PASS |
| 仅 E（未 P） | 无动作 | paused=false，无动作，不启动 ticker，不 C | 不把未开始的 E 当完成；若再无 D，请求悬而未决 |
| 仅 D（未 P） | resume 无 token，但仍同步静音/启动 ticker/C | 同左 | C 一次；ticker 仍可能被不当启动 |
| D→迟到 P→E | done 阻止迟到 P | 同左 | 不重新获得 token |
| P 重复，随后任一有效结束 | token helper 用对象身份去重；mute/stop 可重复 | 同左；E 或 D 完成 | token 去重不等于所有副作用去重 |
| 结束完成后重复 E/D | D 被 done 拦截；E 空 | D 被 done 拦截，E 通常被 paused=false 拦截 | C 不重复 |
| P 后无 E/D 且无抛错 | 没有结束兜底 | 同左 | 无限期暂停风险；不能靠任意播放超时声称解决 |

A 未增加跨请求/跨局 generation。每次调用创建独立 token 和 done；已完成请求的迟到回调通常无动作。尚未完成旧请求跨局到达仍能启动当前 ticker、执行旧 callback；是否适合继续新业务须由调用者 owner 决定，不能宣称跨局安全。

已读实际非奖励入口 `_0x4d0a10`：扣费并保存后调用 `_0x248455(type)`，紧接着 `_0x3153fe(...)`，**没有传 callback，不等待广告结束才建立匹配**。因此不能声称此处 afterAd 新增的 C 直接重复创建比赛；这一路比赛对象和计时器由独立暂停守卫约束。其他插屏消费者没有穷尽检索。

## 4. 暂停所有权：不能把 ticker.start 等同于物理恢复

两版相同 helpers：
- `_carromMatchBlocked()` = host paused 或 token 数量 > 0。
- `_carromAdPause(token)`：身份去重、push、清零步长累积、暂停匹配 timers、同步静音。
- `_carromAdResume(token)`：仅移除自己的 token；同步静音；只有不 blocked 才恢复匹配 timers。
- timer schedule/arm/resume 都检查 blocked，resume 还检查 activeMatch 和 stage parent；版本号阻止过时 timeout。
- `_0x4bf21a` 主循环入口 blocked 时 return；每次逻辑步后再检查。A 的 `_0x49d791` 入口检查用户暂停、host、token，在 Tween 更新后再次检查 host/token。
- `_carromSyncMute` 保留宿主音频禁用、页面不可用、host pause、其他 token 的静音原因。

**P(A)→P(B)→E(A)**：A 只释放 A；B token 仍在，匹配 timers 不恢复，主循环入口不走，静音维持。finish 却仍执行 ticker.start。因此“错误启动 ticker”为静态事实；“一定恢复 B 播放期间的物理模拟”为错误结论。共享 ticker 的渲染、交互插件或其他监听器是否继续属于未验边界。

**host pause→广告结束**：host 标志不被结束回调清除，主循环和 timers 继续阻塞，静音维持，host 设置的 pointerEvents=none 不被 finish 改写。**host resume→广告未结束**：timer resume 自身核对 token，不放行物理；但 host 恢复 pointerEvents，没有独立广告 pointer owner。

广告 pause helper 没有取消瞄准或禁用 pointerEvents；已读 `_0x36ab44`、`_0x1e39ba` 的开始/松手守卫检查用户暂停与 host，**不检查 token**；松手路径可直接施加冲量。即使主循环 blocked，也不能凭 stop ticker 保证所有真实/合成输入都被拒绝。应补统一输入守卫并测广告中拖拽及松手，不宣称已观察到真实误射。

## 5. 同步抛错、异常及重入反例

### SDK 同步抛错

| 抛错位置 | 静态结果与风险 |
|---|---|
| P 前 | catch resume 无 token；paused=false，不启动 ticker；C 一次，迟到 P 被 done 忽略 |
| P 后 | catch 释放 token，尝试 mute/start，C 一次；若 SDK 此时仍展示，可能误恢复本广告，抛错不是可靠展示结束证明 |
| A 的 E 完整成功后 | done 已置位、paused=false；catch 不再 C，也不额外 start |
| B 的 D 完整成功后 | done 已置位，但 paused 未清 false；catch 仍可能额外 mute/start，C 不重复 |
| callback 抛错 | done 在调用前已置位，不重复 callback；同步 SDK 调用栈内会被外层 catch 当“interstitial unavailable”记录，混淆业务异常和 SDK 异常；异步回调则不被该外层 catch 捕获 |

### finish / beforeAd 副作用异常

- `_carromAdResume` 先 splice token，再调用 `_carromSyncMute`。mute 抛错会使 timer resume 未执行；catch 再 resume 因 token 已不存在直接 return，不能补偿漏掉的 timers。
- A finish 外层 SyncMute 或 ticker.start 抛错时，paused 已 false，done 仍 false。若为异步 E，错误向 SDK/事件宿主传播，E 不再触发重试；后续 D 可以重试，但 D 缺失则业务继续丢失且 ticker 可能仍停。
- 同步 E 的该异常被 SDK 外层 catch 捕获时，paused=false 导致 catch 跳过 start，却仍 C 并置 done；逻辑已完成，ticker 未恢复。不能判整体恢复成功。
- catch 的 AdResume 不在保护性 inner try 内；它抛错可直接阻断 warn 和 C。
- beforeAd 的 token 获取、mute、stop 任一步异常可能部分完成。stop 抛错可能留下游戏仍 tick 的状态（主循环 token 守卫通常仍挡住），也可能导致 SDK 中止展示；需实际异常策略。

### 重入

1. finish 的 AdResume 内部 mute 引发 D 重入：外层尚未置 done，内层仍可完成恢复。C 通常仍至多一次，但 start/mute 可重复。
2. AdResume 移除 token 后、finish 置 done 前重入 P：P 重新添加同一 token。外层随后 paused=false 并 C，done=true；后续 D 被忽略且 E 因 paused=false 忽略，**token 泄漏、永久 blocked**。这是明确静态反例。
3. ticker.start 内重入 D：done 尚 false，可重复 start；持续重入甚至递归耗尽。正常 PIXI 是否这样回调未实测，但故障注入应覆盖。
4. callback 内重入 E/D：此时 done 已 true，不重复 C。callback 新开请求 B 后抛错，B token 仍在；B 不应被旧请求清除，但旧 catch 仍可能重复 start。

结论：**当前 Continue 对单请求 callback 是 at-most-once，不是保证必定一次；finish 的恢复副作用不是强幂等或异常安全。**

## 6. 用户激励广告与插屏必须分离

两版插屏 beforeReward/adViewed/adDismissed 都是 no-op；结束回调不发奖励。

两版激励逻辑在已读范围相同，A 的插屏改动未覆盖它：
- `_0x2e33a4` 准备请求，beforeReward 保存 show 函数；`_0x4d02b5(callback)` 在有 show 时先消费 show 入口并保存 callback，然后调用展示。
- `_carromResolveAd(success)` 校验 generation，先置 resolved，取出并清空 callback，再调用。adViewed=true，adDismissed=false；关闭不是 earned。
- afterAd 独立释放 token、启动 ticker、清空 callback并再准备下一请求；未添加 adBreakDone fallback。不能把激励 adBreakDone 到达视为当前代码已处理。
- 展示同步失败的未 resolved 分支尝试 resolve(false)；准备失败 catch 不 resolve 当前业务 callback。没有 show 时 `_0x4d02b5` 直接 return，没有失败反馈。
- generation 防部分迟到奖励进入新请求，但不是跨所有入口的统一事务。afterAd 先于 adViewed 时可能清空 callback/更新 generation，丢失成功结果；实际契约顺序待核查。仅有结果而无 afterAd 时可已领奖但 token/ticker 仍暂停。

实际消费者：lobby 的广告成功后进入转盘；转盘基础奖先发并保存，激励成功追加同奖；比赛胜利基础奖先发并保存，结果激励有本结算 bonusGranted 防重复和固定 prize。比赛的 round/stage 判断位于奖励增币之后，保护的是旧 UI，不是绝对禁止跨局入账。是否允许已赢得旧结算奖励跨局兑现需业务政策，不能擅自称漏洞或取消奖励。转盘/入口领奖单位的完整跨场景与持久化事务未验。

## 7. 最小修正设计建议（未实施）

- 用请求局部 `requested/showing/terminal` 状态；在任何外部副作用前抢占 terminal 并阻止迟到 P；callback 单独提交标志。不要把 callback 去重代替资源清理状态。
- token acquire/release、timer 恢复、静音、ticker 与输入许可统一由暂停 owner 协调。释放只作用自己的 token；重复 cleanup 可安全重试。terminal 不应因恢复失败自动变回 showing。
- 清理异常与 SDK 异常、业务 callback 异常分别记录；清理失败可重试，不再发 C。清理策略需覆盖“token 已释放但 timers 未恢复”，而非只重复 resume(token)。
- ticker 是否运行应综合 host/token/原 ticker 所有者；需要渲染但冻结模拟时应显式分层，不让广告结束无条件抢占共享 ticker。
- P 前允许未展示请求的超时/取消，必须将请求设终态以挡迟到展示；P 后没有结束证据时，不使用任意播放超时解除暂停。记录故障并等待可信宿主/SDK 结束或显式取消确认；无回调风险保持登记。
- 激励成功证据、结束清理、业务领取 claim 三个状态独立；失败反馈不得发奖励。未经确认不将插屏 finish 复制到激励并自动 success。

## 8. 玩法与界面原型约束（审查适用范围）

保留现有 Carrom，不新造玩法、不迁移引擎。引用证据实际依赖 PIXI、planck、Howler、GameSnacks；Canvas 2D 是项目后续技术配置，不是本次现有代码的实际实现声明。

核心循环：选桌扣费→请求非奖励插屏/建立匹配→轮流瞄准和击球→物理运动及入袋扫描→结算计分/犯规→换手或胜负→可选用户激励追加奖励→返回大厅。引用保留这一业务结构，不把奖励与插屏混为一谈。

- 物理：现有 step 表达式 1/60，迭代参数 10/10；ticker 以单位逻辑步累积，while 条件为 >1，未见该入口的显式最大追赶步数。暂停时不累积；快慢帧与恢复首帧不得补跑广告墙钟时长，这是验收条件，不是已测结论。
- 碰撞/计分：沿用现有 planck 与外部 CarromDiscRules；已读入袋中心距离阈值 <=20，普通入袋及 Freestyle 结算分别处理，结果提交防重复。外部规则文件未提供，不能重新断言所有 queen/犯规胜负规则正确。
- 成功失败：本审查成功指可信结束释放本请求一次、其他暂停原因保留、业务继续不重复、激励凭有效观看最多兑现一次。失败包含误放行仍展示广告、泄漏 token、永久停止 ticker、丢失业务结果或重复领奖。
- 输入窗口：当前回合玩家可瞄准，单指身份匹配，松手 strength>=0.25 才施加冲量；暂停必须拒绝新瞄准和旧松手，不缓存广告期间击球待恢复后发射。
- 可接受误差：token/领奖/continue 次数误差为零；blocked 期间物理步数与匹配计时剩余消耗为零；位置不应被逻辑更新（比较容差建议 1e-6 逻辑单位，非引擎已证精度）；正常计时调度偏差与首帧 delta 须测量，不能拿任意广告秒数当允许误差。
- 界面布局保留大厅/选桌、匹配层、棋盘 HUD/瞄准滑杆、暂停层、结果/转盘与用户广告按钮，不新增美术。未来玩家内容默认英文，页面 lang=en；可选故障文案 `Ad unavailable. Please try again.`、`Game paused`、`Continue`、`Watch Ad`。本次未制作或核验最终页面语言及贴图。

## 9. 后续验收条件（全部未执行）

应从真实调用者进入，同时用受控 SDK adapter 故障注入，不能直接 emit 当供应商验收。

1. 完整运行第3节全部顺序，记录 requestId、tokenCount、hostPaused、done、ticker.started、C次数；正常每请求 C<=1，其他请求状态不被改写。
2. A/B token、host pause/resume、用户暂停全部交错；最后一个暂停原因释放前物理 step=0、timer消耗=0、输入冲量=0，静音保留。检查共享 ticker 其他监听器和 pointer owner。
3. 在 SDK 调用前后、P/E/D/业务 callback 内分别同步抛错；mute/start/stop/timer 重臂抛错；模拟 resume 内 P/D 重入。以实际当前函数验证反例，修正后再重验。
4. 请求跨局、callback 开新请求、迟到 P/E/D、激励 generation 变化、缺结果、缺结束、无回调；测试不使用“时间到了就假定广告结束”。
5. 用户点击 Watch Ad，经真实消费者验证成功、dismiss、无 show、重复结果、跨 UI 和存档失败；基础奖与广告追加额分账。
6. 用固定输入与 60Hz/低帧/大 delta 比较暂停前后位置、速度、碰撞、计分、重开，检查恢复首帧是否追赶广告时间；暂停中拖拽及松手不得发射。
7. 宿主真实播放记录广告画面关闭、afterAd、adBreakDone、host事件的相对时间；核对实际 SDK、包装层、方法解码与官方契约一致性。浏览器模拟通过不代替 AHA 真实播放证据。
8. 后续代码/测试阶段应在本阶段修正后的最终源码执行 npm run build、npm test、npm run check；check访问最终 dist/index.html，覆盖桌面/手机点击、控制台、截图和中文浏览器环境默认英文。当前尚无构建工程，不创建假脚本或假试玩包。

## 10. 未知清单与真实执行结果

| ID | 未知/状态 | 当前证据与缺口 | 闭合 |
|---|---|---|---|
| U1 | AHA宿主契约与真实结束时序 NEEDS_CONTEXT | 用户提供官方说明；缺真实版本、包装实现及播放日志 | 否 |
| U2 | SDK方法解码/完整调用者 NEEDS_CONTEXT | 已读混淆调用和选桌入口；未做全文件解码/穷尽差分 | 否 |
| U3 | developer_v2.js NEEDS_CONTEXT | 用户提及；文件未供读取，未作直接证据 | 否 |
| U4 | ticker/Howler/输入实际异常 BLOCKED（动态验收） | 静态反例明确；缺可运行完整工程与受控验证 | 否 |
| U5 | 激励事件顺序、跨场景领取政策 NEEDS_CONTEXT | 局部generation/消费者证据；缺供应商时序及业务政策 | 否 |
| U6 | 外部规则/物理回归 BLOCKED（动态验收） | 现有 step/输入/入袋代码；缺规则依赖与完整运行 | 否 |

本次真实完成：引用文件分段读取、关键函数对照、逐路径静态推演、一次真实用户契约澄清、保存本报告。

明确未执行：源码修改、补丁集成、完整源码差分/解码、JS故障注入运行、npm run build、npm test、npm run check、Chromium桌面/手机测试、最终dist/语言检查、SDK联网请求、官方网页获取、AHA宿主/真机播放验收、资源生成/提取、包体/加载/内存测量、试玩ZIP/源码ZIP发布。没有验证命令日志、浏览器截图或实测数据；静态 PASS 不代表这些事项通过。

产物：`/workflow/prototype.md`。无 dist、evidence 测试输出或 releases 产物。本轮仅完成原型审查交接，不表示用户已确认下一阶段。
