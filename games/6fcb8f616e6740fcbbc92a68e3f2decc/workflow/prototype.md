# Carrom 广告与宿主暂停交错审查

## 范围与结论

本轮为原型定义阶段的只读代码审查及人工设计分析，不制作新游戏、不修改旧脚本、不进入美术、代码或测试阶段。新版源码未提供，以下明确区分旧源码事实、人工方案和有条件推演；不认定新版已实现或已通过验收。

独立 hostPaused 加每次广告调用的独立 token，在 token 获取/释放幂等、清理不受业务代次阻断、全部匹配任务采用同一有效时间门控的条件下，可以解决宿主与广告互相覆盖匹配暂停的问题。它不能证明保留的 ticker.stop/start、Howler.mute 或旧奖励 callback 安全。建议暂不判定整体通过。

## 参考与方法

唯一旧源码参考：ref/mcp-inputs/mac-codex/dd8b79747ae3b111ad0a83ec8088b69b7632ec9f122e685b76601e731d52ffe8/Carrom_current_dd8b7974.js。通过 read_reference 按字符区间连续读取 0 至文件末尾，关键定位采用函数名，未编造行号。文件名中的哈希仅作输入标识，本轮没有独立计算源文件 SHA256。

已实际读取 casual-game-production/SKILL.md v1.3.0，以及冻结的 genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/native-web.md。采用其生命周期、旧异步回调隔离、一次提交一次结果的方法；本次明确的审查范围优先于新游戏生产模板。

人工设计输入：独立 hostPaused；每次广告调用独立 token；beforeAd 增加 token 并冻结匹配计时；interstitial 的 adBreakDone/异常，以及 rewarded 的 afterAd/异常释放所属 token；仅 hostPaused=false 且 token 集合为空时恢复匹配计时；新任务继承冻结；旧 ticker 与 Howler 逻辑和奖励路径保留。以上均为用户描述，未读取对应新版实现。

## 已确认的旧源码证据

1. `_0x248455` 为 interstitial 封装：beforeAd 设置调用局部 `_carromAdPaused`，全局静音并 stop ticker；afterAd 为空；adBreakDone 在 `_carromInterstitialDone` 检查后恢复声音并 start ticker，再调用 `_carromInterstitialContinue`。continue 在调用外部 continuation 前置 done=true，因此 continuation 的重复进入已有一定保护。异常分支在曾暂停时恢复 ticker/声音，再继续；恢复过程的异常被吞掉。广告结束常规恢复没有聚合其他广告或宿主暂停原因。
2. `_0x2e33a4` 为 rewarded 准备封装：用全局 `_carromAdGeneration` 和调用局部 `_carromThisAd` 检查代次，局部 `_carromAdResolved` 对奖励结果去重。`_carromResolveAd` 在调用业务 callback 前先标记 resolved，并取出、清空全局 `_0x38b273`。这是单次结果重入保护，但回调归属仍使用全局槽位。
3. rewarded 的 beforeReward 保存 show 包装到全局 `_0x420004`；`_0x4d02b5` 消费 show 槽、写入全局 callback 后同步调用 show。无 show 时直接返回，不通知传入 callback。
4. rewarded 的 beforeAd、afterAd 入口先检查广告代次。afterAd 恢复全局声音与 ticker、清空 `_0x38b273` 并重新调用 `_0x2e33a4`。它没有独立的 afterAd 完成标记；是否马上产生新代次还受 `_0xcd5b2f` 影响，不能把它当作必然去重。
5. show 异常：若结果已 resolved 则重新抛出；否则尝试恢复、清空可用广告、resolve(false)，finally 中仅当代次仍相同才递增代次。准备调用异常则会递增当前代次、清空全局可用广告及 show 槽，但未调用 `_carromResolveAd(false)`。外部业务 callback 抛错可能沿 SDK 同步栈进入这些 catch，不能等同于 SDK 展示失败。
6. `_0x522c35` 使用 `Howler.mute(_0x7fd997 || !_0x270daf)`；GameSnacks audio 订阅及可见性路径都会调用它。该公式未包含广告或人工描述中的 hostPaused。音乐/SFX 用户设置通过分组 mute 实现，不能简单说全局 unmute 必然覆盖分组偏好。
7. `_0x104b9b` 匹配界面的 startRoll 使用原生 setTimeout 3000ms；停止滚动事件中另有 ready 的 setTimeout 3050ms（有费用）或 1000ms（无费用）。这些原生计时器不因 ticker.stop 自动暂停，片段未保存可取消的任务句柄。`_0x4d0a10` 先调用 interstitial，随后直接创建匹配界面，并非等待其 continuation。
8. `_0x49d791` 更新 Tweener、动画、回合计数和物理；物理步长为 1/60 秒、迭代参数 10/10。`_0x4bf21a` 累积 ticker delta 并按单位补步，所读循环未见显式补步上限。`_0x338c29` 是依赖 Tweener 的延迟，并检查 roundId 与在局状态，与原生匹配 timeout 是不同计时体系。
9. 旧对局结算 `_0x47e567` 有 `_carromResultCommitted` 防重复基本结算；但翻倍奖励 callback 读取执行时全局桌号/模式，未见该 callback 捕获并检查原结算身份。另有转盘奖励 callback 的读写与界面切换路径。
10. 该单文件公开 game.pause/resume/mute/unmute 为空函数；可见性处理不能直接认定为人工方案的宿主事件实现。已读文件中未见 hostPaused/token 方案；其他宿主脚本未提供，不能推断整个产品无宿主适配。

## 有条件交错反例

下表是事件序列推演，未经运行复现；对新版只在所列条件成立时适用。A、B 表示独立广告调用，M 表示匹配任务。

| 风险 | 条件与具体顺序 | 后果及最低风险处理 |
| --- | --- | --- |
| 宿主与广告交错 | A.beforeAd → hostPaused=true → A.done，旧 start/mute 逻辑仍直接执行 | 匹配 token 门控可仍正确冻结，但 ticker 已被启动；声音公式若不包含宿主状态也可能解除静音。所有启动/声音写点应通过统一状态计算，包含既有暂停菜单、宿主、可见性及广告原因。不能仅尾部再次 stop：同步 start 的副作用需先核实。 |
| 并发广告 | A.beforeAd → B.beforeAd → A.done | 若按所属 token 删除，集合仍含 B，匹配应继续冻结；旧 A 的 start/unmute 仍可让 B 期间物理、动画或声音运行。禁止直接恢复，按聚合原因决定；若 SDK 不保证可并发，适配层串行展示，仍保留所属清理。 |
| 重复 beforeAd | 同一调用 beforeAd 连续两次，若每次新建 token、局部仅保存最后一个 | done 仅释放最后 token，永久冻结。每调用预先创建唯一 token；beforeAd 仅将同一个身份加入 Set，且开始状态只转换一次。若方案实际使用同一 token 的 Set.add，则此反例不成立。 |
| 终止后晚到 beforeAd | A 异常或 done 已处理 → A.beforeAd 晚到 | 若没有 terminal 检查，又加入 token，后续无清理事件。终止先置 terminal，之后所有 start/beforeReward/beforeAd 不再激活；无 beforeAd 的结束不得扣减其他广告。 |
| 重复终止 | A.done → B.beforeAd → A.done 再到 | 精确 Set.delete(A) 对 B 安全；普通计数减一、清空全集或释放共享 currentToken 则可能误恢复。所有终止路径调用同一幂等 finalize(A)，副作用也必须受保护。 |
| 代次变化后晚到清理 | A.beforeAd 获 token → 其他准备调用使 generation 改变 → A.afterAd | 若 token 删除放在旧代次 return 后，A token 泄漏。资源清理按所属调用身份执行，不因业务代次过期跳过；奖励/UI 更新再单独检查代次和业务身份。 |
| 旧异常破坏新广告 | A 内同步业务 callback 准备 B，之后 A 的外层 SDK 调用抛错 | 旧准备 catch 对 `_0xcd5b2f` 与 `_0x420004` 无条件清理，可擦掉 B。catch 仅修改仍归属于 A 的槽位；不能只给 generation++ 加条件而保留无条件全局清空。 |
| 同步回调重入 | show 同步发 adViewed → 旧业务 callback 进入 `_0x1260d2`/重开等并准备 B → A.afterAd 返回 | 代次检查可避免部分旧业务写入，却也可能跳过 A 清理；若不检查，A 清空全局 callback 又可能抹掉 B。清理、奖励、可用性状态分开，以调用对象归属；内部状态先提交再调用外部 callback，返回后重新核对归属。 |
| 结束回调内部抛错 | A.done 中先 Howler.mute 再 ticker.start，其中一个抛错，token 删除在其后 | 异步回调异常一般不受外层 try 捕获，token 未释放；也可能声音恢复了但 ticker 未恢复。先提交 terminal/所属资源释放，独立尝试表现同步并记录错误，使用 finally 保证清理；不要把业务异常当广告失败再次发奖或继续。 |
| 缺少 afterAd | rewarded.beforeAd → adViewed 或 adDismissed → 无 afterAd、也无异常 | 奖励结果可已回传，token/ticker/声音仍未清理，新匹配任务继承永久冻结。奖励结果不是关闭证明，不能在 adViewed 即恢复。需 SDK 确认关闭/取消或宿主权威状态；超时只进入恢复流程并记录，不凭时间或普通 host resume 清除仍可能显示的广告。 |
| 缺少 interstitial done | beforeAd → afterAd（旧路径为空）→ 无 adBreakDone | 相同泄漏；是否可把 afterAd 作为终止要依据实际 SDK 合同，当前未提供，不能假定。 |
| 延迟 beforeAd | 发起 A → 创建并启动 M → 一段时间后 A.beforeAd | beforeAd 才获暂停权意味着请求等待时间仍计入 M。如果需求仅暂停实际展示，这是合理边界；如果要求请求即冻结，则需独立 pending 请求租约及无填充/取消清理，不能把两种语义混同。 |
| 已排队 timeout | M 的 timeout 已进入队列 → beforeAd/宿主暂停先被处理 → 旧 timeout 仍执行 | 仅 clearTimeout 不足以证明取消已排队执行。任务执行入口核对 active、任务身份、调度版本及全局 blocked；被阻塞则保留剩余时间，不能先执行事件再检查。 |
| 重复暂停扣时 | M 剩余 2000ms → A.beforeAd 冻结并扣已耗时 → 再 host pause 又从同一起点扣时 | 剩余时间重复减少。仅 running→blocked 边沿结算一次有效运行时间，多原因重叠不重复扣。 |
| 重复恢复与旧任务 | host resume 重复，或旧 M timeout 晚到且新匹配已建立 | 若每次恢复都重新调度会重复 ready/开局；旧任务可切换新局。每任务最多一个有效调度，实例销毁取消全部匹配任务；每次调度有版本号，回调提交前检查实例与版本。 |

## 奖励与声音边界

- `_carromResolveAd` 在同代次内对 viewed/dismissed 采用首个结果胜出，重复 viewed 通常不会再次调用业务 callback；因此不能笼统声称重复 SDK viewed 必然重复发奖。反序 dismissed→viewed 会保持失败，这是否符合 SDK 合同尚待确认。
- afterAd 本身不是成功凭据。旧 afterAd 会清空 callback；若 afterAd 先于 adViewed，结果可能丢失或因重新准备换代而被忽略。当前未提供 SDK 顺序保证，应作为条件反例，不能宣称正常 SDK 必然如此。
- A 已展示但 `_0xcd5b2f=false` 时，其他 `_0x2e33a4` 调用可能递增准备代次；旧 A 的结果随后被忽略。广告准备代次、展示调用身份、奖励业务身份必须分离，不能把准备新广告自动当作已展示广告结束。
- 全局 callback 槽存在归属边界：若允许 B 在 A 未完成时展示并写入槽，而 A 尚能通过其结果检查，A 可能消费 B 的 callback；在旧代码正常递增代次的路径中 A 通常会被拦截，表现为丢结果，不能无条件断言一定串奖。采用调用对象本地 callback，最小化并发入口。
- 结算翻倍应捕获 immutable rewardId、原 round/resultId、原 prize/模式/桌号及必要账户上下文，使用一次提交账本。广告 token 只管理暂停，不能替代奖励去重；基本结算 `_carromResultCommitted` 也不自动保护延迟翻倍。过期 UI 更新与已合法获得奖励的入账应分别定义，避免仅因页面切换吞掉合法奖励。
- `_0x4d02b5` 无 show 时直接返回可能使已隐藏奖励按钮的调用方等待不到结果。入口应明确返回 not-ready 或一次失败结果，并恢复可操作 UI，不伪造成功。
- 全局静音是多个写点的最后写入者竞争：广告 A 静音后，audio.subscribe 或可见性调用 `_0x522c35` 也可能解除静音，即使广告仍显示；恢复端加检查仍不足以封住这些写点。统一计算 effectiveMute，保留用户 Music/SFX 分组设置；全局禁止原因包含宿主、可见性、广告和 SDK audio 禁止，不覆盖用户偏好。

## 最低风险修复契约（建议，未实施）

1. 每次调用在进入 SDK 前创建 operation 对象，包含唯一 id/token、started、terminal、resultResolved、本地 callback、业务上下文。分开管理 prepared/showing/closed 和奖励 unknown/viewed/dismissed，奖励已 resolved 仍允许关闭清理。
2. beforeAd 只激活一次；终止先标 terminal，再精确释放所属 token，清理不受旧业务 generation 检查阻断。释放不存在 token 是无副作用操作，终止后的晚到 beforeAd 不再获取。业务回调执行前完成内部状态提交和回调摘除。
3. hostPaused 只由宿主生命周期路径修改，广告结束不替宿主置 false。若宿主可重连或消息可乱序，需宿主会话/序号合同；仅布尔值无法识别旧 resume。当前没有该合同，不编造消息格式。
4. 集中 reconcile：匹配运行条件至少为 !hostPaused && tokens.size===0，并叠加实例有效性等既有必要条件；ticker/输入/音频按各自完整暂停原因计算。保留实际调用 ticker/Howler 的能力，但把旧的无条件恢复写点纳入仲裁。若坚持完全保留无条件 start/unmute，只能声明修复匹配计时，不能声明整体暂停安全。
5. 匹配三个原生 timeout 统一接入可取消任务：保存单调时钟、remaining、runningSince、scheduleVersion、owner；重叠冻结只结算一次；恢复只调度一次；执行前检查 owner/version/blocked；新任务在 blocked 时不启动计时。冻结期间不累计 elapsed，恢复不按墙钟追赶。
6. 广告准备错误、展示错误、业务回调错误分开处理；清理只针对所属 operation，绝不无条件清空新操作全局槽。同步与异步错误分别覆盖，不依赖 SDK 外层 try 捕获未来事件。
7. 缺失终止回调进入可观测恢复状态；记录 operation、阶段、代次、token 集合、匹配任务剩余时间。watchdog 不依赖被停止的 ticker，且超时不是广告关闭证据。仅在 SDK/宿主确认展示结束、取消成功或整个展示会话确已销毁后释放对应暂停原因；不得自动授奖。

## 验收条件与待执行用例

以下仅为建议验收矩阵，尚未执行。成功指全部不变量保持；失败包括提前恢复、永久泄漏、重复开局、丢失或错误归属的奖励以及恢复异常未记录。

- 顺序覆盖：host pause→广告结束→host resume；广告开始→host pause→广告结束；host resume 在广告仍显示时发生；A/B 交叉完成且结束顺序反转。每个事件后断言 token 身份集合与 matchingBlocked，不能只断言最终恢复。
- 回调覆盖：重复 beforeAd、重复 done/afterAd、无 beforeAd 的 done、异常后晚到 beforeAd、结束后晚到 beforeReward、viewed/dismissed 重复与反序、afterAd 先于结果、缺少 afterAd/done。
- 同步覆盖：SDK 在 break/show 内同步调用全部回调；业务 callback 同步创建新匹配或准备 B；业务 callback、Howler、ticker 各自抛错；旧 A 抛错不能擦除 B 状态。
- 代次覆盖：A 获取 token 后准备 B，A 结果不能误改 B，A 结束仍能释放 A；取消旧匹配后旧 timeout 执行不提交事件。
- 时间覆盖：3000ms、3050ms、1000ms 的每段在到期前 1ms、到期时、回调已排队时冻结；冻结中创建下一段；重复宿主通知；长时间后台恢复。注入时钟下冻结扣时误差为 0，恢复不早于剩余有效时长，任务恰好提交一次；真实浏览器允许调度延后，不承诺后台时延上限。
- 声音覆盖：广告中触发 audio.subscribe、页面隐藏/显示、用户 Music/SFX 偏好变更；任何禁止原因仍在时不能解除全局禁止，最后解除后保留分组偏好。
- 奖励覆盖：原结算 prize 与桌号在回调前改变、页面销毁、重开、not-ready、回调抛错、合法成功后缺少关闭回调；分别断言入账最多一次、金额来自原上下文、UI 不跨实例修改、恢复不伪造奖励。
- 浏览器和真实宿主的验收必须后续基于新版源码与真实 SDK 合同执行，模拟序列不能代替真机广告关闭证明。

## 与物理原型模板的对应及范围限制

旧游戏主循环为匹配→开局→瞄准/击球→物理演化/入袋→回合结算→胜负及奖励。旧步长 1/60 秒已见源码；本轮不改变碰撞、计分、胜负、力度门槛、界面布局或英文玩家文案，不编造缺失的完整规则模块。输入窗口的本轮要求是所有暂停原因存在时不得接受会推进匹配/对局的输入，恢复不补执行旧指针；其新版落实待核验。冻结期间物理步进及业务计数应为 0，不应因直接 start 继续推进；非冻结物理轨迹容差不在本次审查变更范围。

## 实际验证与产物

产物：/workflow/prototype.md（本报告）。本轮仅执行参考、技能及冻结资料读取和报告写入；未执行旧参考脚本，未取得新版源码，未调用 run_validation，未运行 npm run build、npm test、npm run check，未进行浏览器、真机、宿主或真实广告验收。当前为只读审查/设计阶段，上述运行验证未作为成功结果引用。未修改游戏源码、资源或技能，未生成图片、构建或发布包。
