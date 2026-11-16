# Carrom 外层广告 SDK 离线降级静态复核

## 范围与结论

本次为原型阶段的只读源码审查，仅以用户在任务中提供的当前外层 HTML 文本判断当前行为。仅新增本报告，不修改 HTML、SDK、游戏代码或资源，不推进美术、代码或测试阶段。

结论：部分缺失守卫有效，但完整广告失败降级为 FAIL（静态反例成立）；正常 SDK 调用分支仍保留，但正常运行是否成功为 NEEDS_CONTEXT。没有执行浏览器、设备、远端 SDK、构建或自动测试，不作运行验收结论。

## 证据与参考取舍

- E-01：用户本次提交的当前外层 HTML 原文。当前源码的唯一直接证据；未取得当前 game.html、游戏业务消费者或完整工程。以下使用唯一代码片段定位，不编造文件行号或源码哈希。
- E-02：旧参考包 ref/mcp-inputs/mac-codex/2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2/Carrom_Clash_Master.zip。工具返回 SHA256：2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2。
- E-03：实际读取的旧包成员 www.excellenth5game.com/Carrom_Clash_Master/index.html，SHA256：3fb70363f17dc63925ffa5b60b2bb2a3a335183f525876594abe62e7d6ed6bf4。旧入口直接调用 init，没有当前文本的初始化 try/catch、布尔标志及消息守卫。只证明历史差异，不证明当前工程其他文件。
- 方法参考：已读取三份所选技能入口、执行协议、全局规则、未知清单、广告失败与奖励生命周期，以及 AHA 接口契约和标准流程。相关 SDK 模板只是上传样例，不证明远端 adsdk_1.8.0.0.js 的真实实现。
- 已读取四份冻结品类/框架资料。本次不设计或修改玩法；物理步长、碰撞、计分、胜负、操作窗口、误差、游戏界面和存档均不在外层文本的证据范围内，不能从 Carrom 名称或旧包推断。
- 一次 read_reference 尝试读取 ZIP 被工具明确拒绝；随后通过 list_reference_archive 定位并由 read_reference_archive 成功读取 E-03。未解压、执行或复制旧工程。

## 现行路径与局部有效性

1. iframe 直接使用相对地址 game.html，写在远程 SDK 脚本之前；未见由 SDK 初始化成功决定是否创建 iframe 的代码。这支持“外层未显式以广告成功作为创建游戏的前置条件”，不能证明内层离线可玩。
2. window.h5sdk 或 init 不存在时，carromSdkInitialized 保持 false；init 同步抛错且未被 SDK 内部吞掉时，外层 catch 输出警告，随后仍可注册 message 监听器。
3. 守卫命中时，next 与 gameLoadingCompleted 静默返回；reward 尝试向当前 iframe 发送 rewardFailed，targetOrigin 为 '*'。没有在缺 SDK 分支直接发送 rewardSuccess，这一局部性质为 PASS。是否恢复按钮、暂停或等待状态取决于未提供的内层消费者。
4. 方法检查按消息类型区分：加载完成检查 gameLoadingCompleted，插屏和激励检查 adBreak。未知消息无对应 SDK 调用分支，但所有消息都会先被记录到控制台。
5. init 正常返回后标志置 true。原有配置、广告请求和回调路径保留：配置 callback 调用 athenaSend('game_start')、adConfig；onReady 请求 preroll；next 请求插屏；reward 的 beforeReward 调用 showAdFn，adBreakDone 根据 breakStatus 返回结果。保留结构不等于验证 SDK 接受参数或广告成功。

## 缺陷与边界

### 高优先级：消息来源未认证

E-01 的 window.addEventListener('message', ...) 只比较 evt.data，没有校验 evt.source 是否为指定 iframe.contentWindow，也没有校验 evt.origin。能取得此窗口引用并发送消息的其他窗口，可尝试触发插屏、激励或加载上报；这不等于任意网站无需窗口引用即可发送。未见请求 ID、广告位白名单或玩家主动动作的业务校验。

建议后续由双方约定固定消息结构，检查 source、精确预期 origin 和允许类型。响应也应携带请求 ID，并由内层同样验证来源。此为建议，未实施。

### 高优先级：初始化标志不是 SDK 就绪证据

carromSdkInitialized = true 仅说明 init 调用同步返回，init 返回 false、Promise 拒绝、稍后初始化失败或广告尚未 ready 都不会使标志正确表达就绪。未 await 或观察返回值，也没有 readiness 状态机。若 init 内部同步调用配置 callback，该 callback 位于外层 try 的动态调用栈中，逃逸的异常可能被捕获并令标志保持 false；异步调用同一 callback 时，异常不在该 try/catch 的保护范围内。不能将所有 callback 一概认定为被捕获或不被捕获。

若 SDK 晚到或 init 后续可恢复，当前代码没有重试初始化和补发机制；早期 next/加载消息直接丢弃，reward 直接失败。

### 高优先级：消息处理与回调异常没有终态兜底

message 处理器没有 try/catch。adBreak 或 gameLoadingCompleted 即使是函数也可能同步抛错；若返回被拒绝的 Promise，代码没有处理拒绝。方法存在不等于可用。此类错误会中断当前处理流程，不代表永久移除监听器，也不必然使整个游戏崩溃；是否卡住由内层等待策略决定。

配置 callback 对 athenaSend、adConfig、onReady 内的 adBreak 没有独立能力检查或错误隔离。统计调用失败可能阻断同次 callback 中后续广告配置。初始化 catch 不保护后来触发的异步异常。

beforeReward 未验证 showAdFn 为函数、未防重复、未捕获调用异常；adBreakDone 未验证 info 非空就访问 info.breakStatus。iframe 元素不存在时读取 contentWindow 会抛错，contentWindow 不可用也无法发送结果。缺 SDK 的 rewardFailed 分支本身同样没有这些保护。

### 高优先级：无回调、并发、重复及迟到结果未收口

没有请求前登记的 pending 状态、请求 ID、并发锁、超时或终态去重。adBreak 不回调时，外层不会自行返回 rewardFailed。重复回调可能发送多次成功；并发请求的结果都是无身份字符串，无法由外层准确关联。不能据此声称游戏已经重复发奖，因为发奖消费者未提供。

adBreakDone 每次重新查询当前 iframe，而非校验请求时的文档 generation；iframe 导航或重开后，旧请求结果可能发给新文档。需要对请求、对局/页面生命周期和业务领取单位分别核验，旧请求不得支付新上下文。

### 跨窗口：两种 postMessage 写法语义不同

缺 SDK 分支使用 postMessage('rewardFailed', '*')，允许向目标窗口当前任意 origin 投递；若 iframe 已导航，仍可能向新页面发送。

正常分支使用单参数 postMessage('rewardSuccess') 等写法。在支持现代可选 targetOrigin 重载的浏览器中，省略 targetOrigin 默认限制为发送方自身 origin，并非默认 '*'；同源 iframe 可以接收，跨源或导航后的目标可能不接收。旧实现可能要求第二参数并抛出 TypeError，具体支持须按目标浏览器实测。不能直接断言所有浏览器单参数都会抛错，也不能宣称当前壳已支持跨域。相对 src 通常初始同源，但重定向、导航和不透明 origin 环境未核验。

### 奖励判定与正常 SDK 路径

现行代码只在 adBreakDone(info).breakStatus === 'viewed' 时发送 rewardSuccess；dismissed 发 rewardDismissed，其他状态发 rewardFailed。adViewed/adDismissed 仅打印日志，不直接发奖。缺失 SDK 不会在此代码中自动模拟观看成功。

此行为依赖 SDK 对 breakStatus 的真实合同。若只有 adViewed 而没有 adBreakDone，当前代码没有成功或失败响应；若 info 缺失则抛错。不能未经合同确认把 adViewed、关闭、超时与成功任意互换。即使发送 success，也仅证明外层意图通知，不证明消息送达、领取资格、奖励入账或持久化。

### 加载顺序和正常路径的竞态

远程 SDK 是无 async/defer 的经典外链脚本，位于 message 监听注册之前。网络迟缓可延迟后续监听注册；失败后通常继续后续脚本，但不能承诺业务级等待上限。iframe 已先创建，可能在监听注册前发送消息；postMessage 不为尚未注册的业务监听器保存历史消息。init 同步期间产生的消息或回调也需核验顺序。早到加载完成没有握手重传，重复加载完成没有去重。

### Banner 与其他安全性

- 自动缺广告时没有释放底部 8%/52px 占位的分支，可能保留空白。bannerTest=yes 只移除 DOM 并调整高度，不能撤销此前执行的 adsbygoogle.push、保证阻止请求，或调用原生 Banner 隐藏接口。
- adsbygoogle.push 位于初始化 try/catch 之外。普通数组队列可先排队，但对象形态异常或 push 抛错不受该 catch 保护。此独立脚本报错不必然阻止后续独立 script 执行。
- 远程脚本以父页面权限执行，当前标签未配置 integrity；页面文本也未给出 CSP，无法由此证明响应头没有 CSP。HTTPS 不证明第三方脚本逻辑可信，亦不构成完全离线或原厂联网隔离。
- iframe 未加 sandbox 不自动等于漏洞；若同源内容可信，它可具有正常同源访问能力。若要隔离不可信内容，应另评估权限及兼容性，不能仅加 sandbox 后假定广告和消息仍正常。
- console.log(evt) 记录所有收到的消息，不宜未经筛选保留潜在业务信息。当前证据不足以断言泄露了特定个人数据。
- getQueryParams 使用普通对象和真值判断重复键，会使空值重复参数、继承属性名和 __proto__ 等出现非预期解析；当前仅将 bannerTest 与 'yes' 比较，未见可据此断言任意代码执行或全局原型污染的路径。

## 审查决策与建议验收条件

保持现行 SDK owner 在父页面；本次不引入原生 Bridge、替换供应商、模拟奖励、改动广告账户或重新设计游戏玩法。以下仅作为将来获授权修复后的验收清单，本次均未执行：

| 场景 | 应验证的结果 |
| --- | --- |
| SDK 缺失、init 缺失、init 同步抛错 | 监听可工作；激励失败一次且不发奖；内层恢复；正常游戏不依赖广告成功 |
| init 返回但未就绪、异步拒绝、SDK 晚到 | 就绪定义准确；失败有终态；补注册/重试遵循明确策略 |
| 统计/配置/加载上报/广告方法抛错 | 各异常隔离，主流程可继续，不留下永久等待 |
| 无填充、无回调、展示后失联 | 按 SDK 合同分别处理加载与展示状态，失败不奖励 |
| 完成、关闭、异常 info、错误 showAdFn | 完成证据正确映射，其余安全失败 |
| 重复、乱序、并发及同步回调 | 调用前登记身份，终态至多一次，同一领取单位至多奖励一次 |
| 外来窗口或错误 origin | 不触发 SDK、不改变奖励状态 |
| iframe 导航、重开、请求取消 | 旧回调不作用于新上下文 |
| 同源、跨源、目标浏览器版本 | 精确 targetOrigin 投递，双向来源检查及兼容性成立 |
| SDK 慢加载与游戏早发消息 | 握手/重发有效，加载上报按实际游戏就绪去重 |
| 广告叠加后台或用户暂停 | 仅释放自身暂停原因；音频和输入正确恢复 |
| Banner 无填充、关闭与测试参数 | 空间按合同释放；不误称 DOM 删除等于禁网 |

## 真实验证记录

本 attempt 实际执行：读取冻结技能与资料、列目录、列 ZIP 匹配项、读取一个历史入口、对用户现行 HTML 作静态控制流审查。目录工具返回根目录为空。

未执行：npm run build、npm test、npm run check、浏览器、设备、网络采集、生产广告、平台后台或奖励落盘验证。当前为限定的只读原型审查，不执行代码/测试阶段命令，不制造测试脚本或发布包。报告路径：/workflow/prototype.md。

## 未知清单

| 编号 | 未知项 | 闭合所需证据 | 当前证据 | 状态 |
| --- | --- | --- | --- | --- |
| U-01 | 当前内层是否消费 rewardFailed/rewardDismissed 并恢复等待状态 | 当前 game.html 及实际业务调用、失败消费者和受控交互 | E-01 仅展示父页发送 | 未闭合 |
| U-02 | SDK 初始化、Promise、ready 和回调顺序的正式合同 | 对应版本 SDK/渠道文档及隔离测试 | E-01、技能上传样例 | 未闭合 |
| U-03 | 奖励是否去重、校验资格及持久化 | 当前奖励 owner、领取单位及业务链验证 | 无当前消费者证据 | 未闭合 |
| U-04 | 部署 origin、重定向、浏览器版本及单参数消息兼容性 | 实际部署与目标浏览器验证 | E-01 相对 iframe 地址 | 未闭合 |
| U-05 | SDK 故障时整款游戏是否离线可玩 | 当前完整工程、资源依赖与受控断网运行 | 旧包不能替代现行工程 | 未闭合 |
| U-06 | 暂停恢复、Banner 展示及埋点到账 | 当前业务生命周期及目标宿主/渠道证据 | 外层未提供完整链路 | 未闭合 |

上述缺口不妨碍完成本次静态审查，但禁止据本报告宣称完整降级、正常 SDK 广告、跨域安全或整款游戏已验收通过。
