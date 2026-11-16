# Carrom 广告生命周期只读审查

## 范围与结论

本轮为 prototype 阶段的只读业务审查，只新增本报告，不修改源码、不构建、不执行模拟或真实 SDK 测试。结论来自用户提交的最新函数摘录的 JavaScript 控制流静态推导，不是线上故障复现。整体运行验收状态：NEEDS_CONTEXT。以下 FAIL 均指指定输入序列下的局部控制流不满足目标，不表示已证明 SDK 会产生该序列。

优先目标：普通玩法不依赖广告可用；没有本次有效观看完成证据不发激励；广告结束只释放自身暂停；一次请求只结算一次且不污染下一次请求。本轮不重新设计物理、碰撞、计分、胜负、输入窗口或美术，这些不属于广告摘录可证明的范围。

主要结论：

1. 插屏仅 adBreakDone 或同步 catch 调用继续函数；prepare 正常返回且无回调，或只有 afterAd，均无本地继续路径。beforeAd 后失联还会留下本函数造成的暂停。摘录内没有看门狗。
2. 激励的 generation 与 resolved 能限制单个请求的结果重复投递，但未统一保护 beforeReward、展示闭包及 afterAd，也没有绑定对局或业务领取单位。
3. 激励 prepare 外层 catch 清准备态并使当前 generation 失效，却不调用失败消费者、不清全局业务 callback；已发生 beforeAd 时尝试恢复，但恢复异常被吞掉。
4. afterAd 先恢复 ticker，再重新 prepare，最后无条件清全局 callback；同步回调、重入或缺结果事件可导致 callback 丢失、重复恢复或新请求受污染。
5. 两种广告直接 start ticker，摘录没有暂停原因集合；它们不能单独保证后台、用户暂停和并发广告的恢复正确。
6. 激励 true 只由 adViewed 进入 resolver，摘录没有以超时、关闭或异常冒充成功的路径；这不等于奖励经济、回调真实性或业务消费者已经验收。

## 证据与参考取舍

- E-01：本次用户消息内 _0x248455、_0x2e33a4、_0x4d02b5 的最新摘录；_0x21acae 只有函数开头，不能分析其函数体。当前行为结论只引用 E-01。
- E-02：历史 ZIP：ref/mcp-inputs/mac-codex/736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99/Carrom_current_development.zip，清单返回 SHA256 为 736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99，335 项，展开 5099606 字节。这些是历史包清单信息，不是本轮构建测量。
- E-03：历史成员 development/js/game.js，SHA256 3140ae1bd16fd91b6c025fc3641f2ff41e9f26e2b7200c94810199ada22a1573；实际仅读字符 [0,18000)。可见历史 Planck/Pixi/Howler 相关结构，未读到广告函数或解码表，不能用来证明最新别名和调用者。
- E-04：已完整读取所选 aha-game-integration/SKILL.md、game-reverse-engineering/SKILL.md，以及本轮四份冻结品类/框架正文。已读 AHA api-contract、workflow，总集 execution-protocol、global-rules、ad-fallback-and-reward-lifecycle、unknowns-ledger-template。它们用于证据与状态审查方法，AHA 整数事件码、上传 h5sdk 壳及示例时限均不移植为 GameSnacks 合同。
- E-05：读取 game-reverse-engineering/modules/sdk-replacement/SKILL.md 被工具拒绝：该入口未被本轮选中。没有声称读取成功，也未扩充选中入口。

未取得 GameSnacks 官方合同、实际加载 SDK 版本/实现、当前完整源码、调用者、初始化和运行日志。因此不能宣称 adBreakDone 是真实支持的必达回调，不能宣称 afterAd 与 adViewed 的顺序，不确认 Promise 返回约定，也不确认 SDK 是否捕获用户回调异常。

摘录中 _0x157421(0x49d)、(0x187)、(0x215)、(0x431)、(0x114) 的解码未被本轮实际验证。下文将相应操作依业务上下文称为 prepare、mute、ticker、start、reward；关于具体方法身份的结论以当前解码一致为前提。显式 Howler.mute 与 ticker.start 的 catch 路径不需要该别名假设。

## 状态定义与所有者

插屏：每次调用闭包持有 P=_carromAdPaused、D=_carromInterstitialDone；继续消费者为传入参数 _0x2132c0。D 在调用消费者之前置 true，防同一闭包再次投递，但不保护恢复副作用，也没有跨请求去重。

激励：G=_carromAdGeneration 为全局代次，g 为闭包捕获代次，R=_carromAdResolved、P 为闭包状态；A=_0xcd5b2f 是共享准备标记，S=_0x420004 是共享展示函数，C=_0x38b273 是共享消费者。_0x3e43c0 的真实业务含义未知。_0x1f977d 被写为 1200，单位和外部更新方式未知，不能称其为已实现的超时。

业务链已知部分：_0x2e33a4 准备 → beforeReward 写 S/A → _0x4d02b5 消费 S、先登记 C 再展示 → adViewed/adDismissed 经 resolver 调 C → afterAd 恢复并尝试再次准备。真实按钮、奖励写入、存档和取消 owner 均未给出。

## 插屏转移与具体反例

| 输入/事件 | 摘录内变化 | 静态结论 |
|---|---|---|
| prepare 正常返回，无任何回调 | P=false，D=false | 无继续、无超时；若调用者等待继续则业务等待。此时不能说 ticker 已停 |
| beforeAd | P=true，先 mute(true)，后 stop | mute 抛错则 stop 不执行；P 已置 true |
| adViewed / adDismissed / afterAd | 空函数 | 单独收到任一事件不恢复、不继续 |
| adBreakDone | 先恢复音频、再 start、再 continue | 任一恢复操作抛错则该次回调到不了 continue；若仍在 prepare 同步调用栈且异常传播，外层 catch 可继续；异步则外层 catch 不覆盖 |
| prepare 同步抛错 | P=true 时尝试恢复；警告；continue | 恢复失败被吞，但通常仍继续；console.warn 或消费者自身抛错另论 |
| 重复 adBreakDone | 每次都先恢复；D 只拦消费者 | 消费者至多一次，恢复可多次 |
| 完成后迟到 beforeAd | 不检查 D，重新停 ticker | 已继续的业务可被再次暂停；其后无结束事件则本函数无恢复 |

最小反例 I-01：调用插屏，SDK stub 只记录参数并返回 undefined；不触发回调。继续次数为 0，不能证明正常离线继续。I-02：beforeAd → afterAd，无 adBreakDone；观察 stop 一次、start 零次、继续零次。I-03：adBreakDone → beforeAd；消费者一次，末态仍被暂停。上述序列是否为真实 SDK 可达，须查合同。

消费者抛错：continue 先置 D=true 再调用消费者，所以不会因重复完成重调消费者。若异常同步穿透 prepare，外层 catch 可能把业务异常误记为广告 unavailable，并再次尝试恢复；D 仍拦住继续消费者。异步消费者异常不被外层 try 捕获。

## 激励准备、展示、结果和关闭

| 输入/事件 | 摘录内状态 | 静态结论 |
|---|---|---|
| A=true 时调用 prepare 包装函数 | 立即 return | A 是准备门禁，不是覆盖完整广告播放的互斥锁 |
| A=false 开始准备 | ++G，g=G，R=false，计数=1200，A=false | 未先清旧 S/C；外部是否保证其为空未知 |
| prepare 正常返回，无回调 | 不创建新展示函数，也不自动结算 | 干净初态下点击 show 因无 S 直接返回，不调用传入 callback；若 UI 已等待则可悬空 |
| beforeReward | 只核 g=G；写 S，A=true | 不核 R；同代重复 beforeReward 可重新暴露展示函数 |
| show(S存在) | S=null，C=传入消费者，A=false，然后调用保存的 S | 同步展示结果到来前 C 已登记，这是正确的初始化顺序；但允许此时重新准备另一代 |
| show(S不存在) | 直接 return | 不保证调用方收到 false，也没有摘录内玩家反馈 |
| beforeAd | 核 g=G；P=true；mute/stop | 不核 R；结果已结算但代次未失效时仍可再次暂停 |
| adViewed | resolver(true) | 只核代次与 R；不核本次 show 是否已触发 |
| adDismissed | resolver(false) | 与 viewed 共用首结果胜出机制 |
| resolver | 核 g=G 且 !R；R=true；读取 C，清 C；再调消费者 | 同代结果至多投递一次；消费者抛错后不重试。结果到来时 C为空仍会 R=true，稍后 show 的 callback 就无法被该代结果结算 |
| afterAd | 核 g=G；恢复；调用 prepare 包装函数；置 _0x3e43c0=false；C=null | 不调用 resolver、不清 P、不先设关闭幂等标记；重入后尾部清理可能清掉新请求 callback |

同代 viewed → dismissed：只投递 true；dismissed → viewed：只投递 false。重复 viewed 不重复投递，但这只是结果回调幂等，不证明业务领取或持久化幂等。若 SDK 合同保证结果互斥，可按合同接受；若允许先 dismissed 后有效 viewed，首结果胜出会丢掉有效完成，当前未知。

adViewed 在 beforeReward/show 之前到达：若 C 为空则静默标 R=true；稍后注册 C 的真实展示不再结算。若 C 是共享槽残留值，则会投递给残留消费者。两者都是对指定序列的静态反例，非断言 SDK 会如此调用。

afterAd 不等于观看完成。它直接清 C：show → beforeAd → afterAd → adViewed，在 prepare 包装函数确实建立新代的条件下，旧 viewed 被 generation 拦截；若 A=true 导致重准备 return，C也已被清空。无论哪种分支，原消费者都可能未收到任何结果。若合同保证结果总在 afterAd 之前，该序列才可排除。

## 异常边界

1. prepare 同步抛错且 g=G：catch 先 G++，清 A/S；P=true 时尝试恢复，最后警告。它不执行 resolver(false)、不清 C、不重置 _0x3e43c0。若本来已有等待中的消费者，失败无投递；后续该代结果因代次失效被忽略。是否存在等待消费者须看调用者和同步重入。
2. 旧 prepare 的同步调用栈在重入创建新代后才抛错：catch 的 G++ 有代次条件，但清 A/S 与暂停恢复没有。因此旧 catch 可清掉新代准备状态或解除新代广告暂停。
3. show 函数同步抛错且 R=false：若 P=true，尝试恢复并清 P；清 A/S；resolver(false)；finally 在仍为当前代时 G++。正常条件下消费者得到 false，不会伪造 true。消费者抛错时 finally 仍执行，警告语句可能不执行。
4. 保存的展示闭包自身没有 g=G 守卫；陈旧闭包仍会调用 SDK show。其 catch 也不先核 g=G 就清全局 A/S、恢复 ticker；resolver 会拒绝旧结果，但副作用不能因此被挡住。
5. show 先同步触发 adViewed，让 R=true，再抛错：show catch 直接重抛，不做恢复/清理。若调用仍嵌套在 prepare 同步回调栈内，可能继续被 prepare 外层 catch 捕获；通常独立用户点击栈则向外传播。不能把所有 show 异常都描述为已降级 false。
6. Promise rejection：如果 prepare 或 show 返回 Promise，代码没有 await/then/catch；异步 rejection 不被这些同步 try 捕获。SDK 是否返回 Promise、是否内部消化 rejection 未知。
7. SDK 延后调用 beforeAd、afterAd 或消费者时抛出的异常，不属于已返回的 prepare try 动态范围；只有 SDK 自己捕获/转发才可能改变传播结果。
8. afterAd 的 mute/start/prepare 任一操作抛错，会跳过后续尾部赋值。恢复使用顺序语句，一处失败不保证另一处仍执行；catch 中合并 try 也有这个问题。

## 重入、重复回调与并发

R-01：show → adViewed，业务消费者同步调用 prepare，为新代触发 beforeReward。此后旧 afterAd 因 g!=G 直接 return，旧 P 对应的暂停可能从未释放。generation 能隔离旧结果，同时也会跳过旧代资源清理；不能用新代广告未来结束来保证恢复。

R-02：show → afterAd；其内部 prepare 同步触发新 beforeReward，并在返回前重入 show(newCallback)。旧 afterAd 返回时的 C=null 清掉 newCallback；新代随后 viewed 只会置 R、不投递该 callback。该反例依赖同步重入，但 JavaScript 语义允许，不要求多线程。

R-03：beforeReward → show → 重复 beforeReward → 第二次 show；同代第二次调用可覆盖全局 C，第一次消费者失联。S=null 只能阻止未重新准备时的直接连点，不能证明整个广告期间互斥。

R-04：afterAd 在 A=false 时通常令 prepare 创建新代，重复旧 afterAd 随后被代次拦截；因此不能笼统说它必然重复 prepare。若 A=true 让内部 prepare 立即 return，代次不变，则重复 afterAd 仍能反复恢复与清 C。

R-05：播放期间 A=false，任何外部 prepare 可建立新代，让旧 beforeAd/结果/afterAd 全部失效；是否真实可达取决于 _0x21acae 等未提供调用者。

R-06：插屏与激励未展示共享的广告互斥 owner；二者可独立 stop/start。一个结束可 start 另一个仍需要暂停的 ticker。当前摘录不能证明 SDK 本身允许并发，也不能证明业务已串行化。

## 暂停与离线边界

P 只是“本闭包执行过暂停尝试”的标记，不是暂停所有权或原状态快照。成功结束路径没有将其清 false；没有 visibility、用户暂停、系统 activity、其他广告的集合。原本停着的 ticker 在 adBreakDone/afterAd 中也会被 start。音频恢复表达式采用当前 _0x7fd997 || !_0x270daf，但两个变量的实际含义未证，不能称为完整后台或用户设置恢复策略。

只见 ticker.stop 不代表 DOM输入、其他 requestAnimationFrame、setTimeout、物理步进、AI或系统音频全部暂停；恢复后是否补入大 dt 也未知。不能从这里填写物理步长或允许误差。

SDK 缺失/方法非函数时，在 try 内访问会同步抛错：插屏通常进入继续路径；激励 prepare 通常清 A/S并警告，不发奖励，但不会通知失败消费者。广告脚本加载失败是否阻塞游戏启动、离线资源是否完整、按钮能否恢复，需要入口及消费者证据。

prepare 无回调和 beforeAd 后无回调是不同状态：前者可能只是广告不可用而 ticker 仍正常；后者已尝试暂停，缺终态会保留暂停。未展示阶段的有限等待可设计为离线降级；展示后失联不能简单套加载时限，以免在真实广告仍覆盖时提前恢复输入。任何超时均不是奖励证据。

## 最小测试方案（仅提供，未编写执行脚本、未运行）

夹具应在隔离函数作用域放入 E-01 的原始函数和当前真实解码器；GameSnacks 方法替身记录每次 options，支持立即调用、microtask和手工延迟；Howler/ticker 记录事件并可按次抛错。观察 G、A、S、C、R可观察结果、消费者调用序列、mute/stop/start 次数以及独立奖励账本。不能凭历史 ZIP 的解码猜测建立“原样当前代码”测试。

最小替身接口示意（不是已执行代码，也不是 SDK 合同）：

```js
const requests = [];
const events = [];
const prepare = options => { requests.push(options); };
const emit = (index, name, ...args) => requests[index][name]?.(...args);
const consumer = success => events.push(['result', success]);
```

在当前真实 method 名处注入 prepare，保存各代 options 后逐步 emit。下表“当前推导”是 E-01 条件下的预计观察；“验收目标”是未来修复要求，两者不能混称测试通过。

| ID | 最小输入序列/故障 | 当前推导 | 验收目标 |
|---|---|---|---|
| T01 | 插屏 prepare 无回调 | continue=0，未必暂停 | 未展示失败有限收口，主流程继续一次 |
| T02 | 插屏 beforeAd→afterAd，无 done | stop后无恢复/继续 | 按真实终态合同释放自身暂停 |
| T03 | 插屏 done×2；再 beforeAd | continue一次，恢复两次，末态又暂停 | 终态后迟到事件不再改变状态 |
| T04 | SDK缺失；插屏/激励各请求 | 插屏继续；激励无成功但无失败投递 | 离线可玩，激励等待者可恢复且奖励不变 |
| T05 | 激励 beforeReward→show；show同步 throw | R=false时 false一次，清准备态 | 失败一次，入口恢复，奖励不变 |
| T06 | 激励 beforeReward→show→beforeAd；无后续 | C悬空，暂停未释放 | 独立展示失联策略，不能伪奖 |
| T07 | viewed×2→dismissed；反向另跑 | 分别只 true一次、false一次 | 用合同确认顺序；业务奖励账本至多一次 |
| T08 | show→afterAd→viewed | C被清或旧代失效，消费者可失联 | 支持合同允许的尾部结果或明确拒绝该序列 |
| T09 | show后、结果前 prepare同步 throw | 当前代失效，C保留且不投 false | 对应等待者失败收口、旧结果隔离 |
| T10 | show返回 rejected Promise；另测prepare | 同步catch不捕获 rejection | 依真实返回合同处理异步错误，无未处理拒绝 |
| T11 | viewed消费者内 prepare→beforeReward；再旧afterAd | 旧afterAd跳过，原暂停可残留 | 旧资源清理与新代结果隔离分离 |
| T12 | afterAd内部新prepare同步重入show(C2) | 尾部 C=null，C2丢失 | 旧清理不接触新请求 |
| T13 | 同代beforeReward→show(C1)→beforeReward→show(C2) | C1可被覆盖 | 在途请求串行，重复准备不重开入口 |
| T14 | 保存旧S→新代准备→执行旧S且抛错 | 旧catch可清新S/A | 陈旧展示与陈旧清理均无效 |
| T15 | user暂停或hidden，再广告结束 | 本函数直接start | 其他暂停原因仍有效 |
| T16 | 激励与插屏各beforeAd，只结束一个 | 结束方直接start | 还有广告暂停原因时不恢复 |
| T17 | 异步done/afterAd中mute或start抛错 | 后续步骤跳过，外层try不接住 | 各项清理独立保证，业务失败有明确定义 |
| T18 | viewed先于show；随后beforeReward/show | R先占终态，新C不能结算 | 结果必须绑定已发起展示的当前请求 |
| T19 | show同步viewed后throw；消费者本身throw | R已置位；show异常重抛 | 不重复发奖，区分业务与SDK异常，暂停可释放 |
| T20 | 换局/离场→旧viewed | 只有广告generation守卫，业务归属未知 | 校验match/claim，旧结果不发到新局 |

补充边界：beforeAd中mute抛错与stop抛错分别测；恢复mute抛错与start抛错分别测；旧prepare同步重入新代后才抛错；beforeReward后不show却afterAd；无S的show不能使真实UI永久loading。每例重置全局夹具并检查奖励账本零变化或一次合法提交。以上都需要真实调用者链才能升级为业务测试。

## 建议的最小设计取舍（未实施）

- 一个广告协调 owner，按 request ID保存展示资格、消费者、播放状态、结算状态、清理状态与对局/领取上下文，避免共享单槽跨代覆盖。结果幂等与资源清理幂等分开。
- 在请求前登记身份和消费者；未准备好直接返回明确不可用，消费者不应先进入不可取消等待。beforeReward只准备，主动点击后至多展示一次。
- 依真实 GameSnacks 合同决定结果/关闭顺序及 adBreakDone 支持情况；未知时不给 true。prepare/show 同步异常和合同允许的异步失败均收口为失败，业务消费者异常单独记录。
- 广告恢复只释放本请求暂停原因；音频、物理、AI、输入由统一暂停 owner根据剩余原因决定。即使代次已更替，旧请求仍要安全释放自己的资源，不能动新请求槽。
- 未展示超时与展示失联分开，时限需产品与SDK事实决定，本轮不编造固定秒数。插屏不可用继续原流程；激励不可用留在原业务、反馈可关闭、不改经济。
- 奖励由真实消费者以本次完成证据加业务claim幂等记账，不能用 dismissed、afterAd、done、超时或异常直接当作成功。真实合同若规定另一种可信完成证据，应先取证再采用。

这些是后续最小修复方向，不表示用户已授权源码改动或已推进代码阶段。

## 未知清单

| 编号 | 未知项 | 还缺什么 | 当前证据 | 状态 |
|---|---|---|---|---|
| U-01 | 实际SDK方法、版本、GameSnacks回调顺序/必达性、Promise与异常合同 | 当前加载入口、版本化官方合同与SDK实现/日志 | E-01；E-04只是AHA参考 | 未闭合 |
| U-02 | 当前解码、全局初始化、计数1200的消费者和单位 | 当前解码表及变量读写处 | E-01；E-03是历史局部 | 未闭合 |
| U-03 | 按钮、prepare调用者、_0x21acae与失败UI | 当前完整调用链 | E-01函数体截断 | 未闭合 |
| U-04 | 奖励提交、claim、持久化与换局取消owner | 成功/失败消费者与存档源码、业务回放 | E-01仅投递Boolean | 未闭合 |
| U-05 | 暂停、后台、输入、物理与音频的统一owner | 当前生命周期源码和目标宿主记录 | E-01仅ticker与mute | 未闭合 |
| U-06 | 列举序列在真实SDK中是否可达 | 正式测试配置、各网络/关闭路径回调日志及合同 | 本轮仅条件静态推导 | 未闭合 |
| U-07 | 离线冷启动与无回调是否可玩 | 当前入口和实际离线业务验收 | 无运行证据 | 未闭合 |

## 真实验证、交付与限制

已执行：冻结技能/知识读取、参考目录与ZIP清单查询、历史game.js字符[0,18000)定点读取；工具结果及哈希见E-02/E-03。模块入口读取失败已按E-05记录。

未执行：npm run build、npm test、npm run check、任何Node模拟、浏览器、网络采集、真实广告、目标宿主与奖励经济验证。原因是本轮明确要求只读审查且不声称动态执行；不能将本报告的最小测试方案当测试结果。没有截图、构建、试玩包、美术资源或新模型结果。

产物：/workflow/prototype.md。当前源码完整性、广告真实可达性、离线可玩和奖励发放正确性均未验收；不以旧ZIP补足摘录外的当前事实。报告交付只代表静态审查完成，不推进下一阶段。
