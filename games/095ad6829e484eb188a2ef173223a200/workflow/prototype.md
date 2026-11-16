# Carrom 插屏恢复重入与异常审查

## 1. 阶段、范围和总评

- 项目：095ad6829e484eb188a2ef173223a200；当前 attempt=1，仅 prototype 原型定义/静态审查阶段。
- 用户目标：逐项审查插屏结束先锁终态、释放 token 的异常回退、声音与 ticker 独立恢复、继续回调异常隔离；覆盖重入、重复/迟到回调、多 token、宿主暂停、无 beforeAd、同步 SDK 抛错、动画、业务流程及激励广告边界。
- 本次产物：`/workflow/prototype.md`。没有修改参考源码，没有生成新游戏、资源、构建包或测试脚本；没有进入美术、代码与测试阶段，也没有记录虚构的用户确认。
- **结论：修订版改善了单次插屏请求的终态锁和异常隔离，但不能认定“恢复所有权正确、所有广告链已修复或真实 AHA 验收通过”。**
- 总体发布判定：**NEEDS_CONTEXT**。静态局部性质可以确认；动态恢复、完整调用覆盖和真实宿主事件契约尚未闭合。

证据标签：本文“PASS（静态）”只表示在给定代码与明确假设下成立，不是运行测试通过；“FAIL（静态）”指代码不满足所列保障；“NEEDS_CONTEXT”需依赖或宿主信息；运行验收均为“未执行”，当前运行验收状态为 BLOCKED。

## 2. 参考证据与方法

### 2.1 输入

以下路径相对工程 `ref/`，实际通过 `read_reference` 分段读取：

- **A / 对照**：`mcp-inputs/mac-codex/5124e5e25fac79542fdd2e91eb28300bd872df6531337a1d658e7a4e13f490f1/arena-partial-cleanup.js`
- **B / 待审修订版**：`mcp-inputs/mac-codex/31fbe829f0056d30c46a725ac47b64ee98146b0df711a11d00ca623f345b67c2/interstitial-reentrancy-fixed.js`

“对照/修订版”是本次比较角色，不证明 Git 谱系、部署版本或历史版本先后；路径中的十六进制字符串未作为本次重新计算的文件哈希。未执行完整机械 diff，也未对全部混淆字典、依赖和全量广告调用点完成解析。

定位锚点（offset 是读取工具偏移，不是源码行号）：

| 证据 | 文件/读取窗口 | 函数或内容 |
|---|---|---|
| E1 | A，offset=104000，limit=4400 | `_0x248455` 的旧插屏闭包、finish/continue、SDK catch |
| E2 | B，offset=105000，limit=7400 | `_0x248455` 完整插屏收口、`_0x2e33a4` 激励、`_0x4d02b5` 展示入口 |
| E3 | B，offset=216000，limit=4000 | `_0x49d791` 函数开头、暂停检查、ParticleManager/Tweener 更新、回合时限 |
| E4 | B，先前连续分段读取 | `_carromAdPause/Resume`、`_carromMatchBlocked`、`_carromSyncMute`、match timer、`game.pause/resume`、`_0x4bf21a` |
| E5 | B，先前分段读取 | `_0x4d0a10` 选场付费/入场、`_0x47e567` 结果、`_0x5b20b9` 转盘、`_0x338c29` tween 延时 |

B 的已读窗口为 0–192000、216000–228000、228000–300000（部分窗口重叠）；A 已读 0–48000 及核心 104000–118500 等局部窗口。读取覆盖不等于全文件审查，未命中窗口不补造结论。

### 2.2 实际采用的方法资料

已读取选定 `game-reverse-engineering/SKILL.md` v10.5.0；采用执行协议、全局证据规则、未知清单模板，以及 `modules/sdk-replacement/references/ad-fallback-and-reward-lifecycle.md` 的请求/领取幂等、失败消费者、场景 owner 和暂停归属分析方法。配套路径前缀均为 `game-reverse-engineering/`。

`game-reverse-engineering/modules/sdk-replacement/SKILL.md` 的读取被工具拒绝（该入口未选中），不记作成功读取或完整模块执行；没有启用完整 SDK 替换流程。

开始审查前已实际读取本轮冻结资料：

| 路径 | 冻结 SHA256 |
|---|---|
| `genre/docs/general.md` | `8d5058f8368fece60ae844b0d40217481746a7d8f0697b8f95cda9d78de64047` |
| `genre/docs/physics.md` | `1aa7a11ef4bee1cb3bbd8acdf8c29cfed381e6450c5d0f77655c91dd5b1bd606` |
| `framework/docs/web-common.md` | `5631072d40b38dfcb641838ceb1836e65d2a9ed07347215f8eb90819e25ceb08` |
| `framework/docs/canvas-web.md` | `ef6ec5c4232be8c692c2ddb567d8353f82266baa5502f96a846ce999d994aad5` |

选定技能冻结 SHA256：`c6d78ae0d45e47349957791798560a5b9f3c6846317c035a05ad6631d66b4d05`。以上是冻结资料标识，不是对游戏源码重新计算的哈希。

### 2.3 框架取舍

项目配置为 Canvas Web，但参考实际调用 PIXI、planck（box2d=planck）、Howler/Howl、Tweener、ParticleManager 和 GameSnacks，且出现 sharedTicker:true。依赖版本和完整包装实现未核验。本轮沿用“已有 H5 代码静态审查”，不假称原码是原生 Canvas 2D、Cocos 或已完成框架迁移。若后续要实际实现或迁移，须先解决框架范围取舍，不能自动改写。

SDK 入口仍有 `GameSnacks.ad[_0x3a5106(0x49d)]` 混淆属性；本文按代码中的回调字段分析，不将其直接认作真实 AHA API，也不凭通用广告文档推定此宿主契约。

## 3. 原型定义：保留游戏，冻结广告行为边界

这不是新增 Carrom 玩法立项；定义的是“不改变既有玩法”的广告恢复审查原型。

### 核心循环与状态

现有业务片段：选场/资格检查 → 扣入场费与保存 → 调用插屏入口 → 创建比赛 → 瞄准与击球 → 固定步物理、碰撞/落袋扫描与回合流转 → 结算基础奖励 → 可选激励加成 → 返回/下一局。完整模式胜负规则未全部解混淆，不臆造目标分数或国际 Carrom 全规则。

单次插屏闭包状态：OPEN（done=false，可能尚未 beforeAd）→ PAUSED（注册本请求 token）→ FINISHING/TERMINAL（done=true，在释放/恢复/继续前锁定）。TERMINAL 是“收口已被占用”，并非每项恢复成功。独立请求有独立闭包和 token，不能把局部 done 当全局广告互斥锁。

暂停维度分开记录：宿主 `_carromHostPaused`、广告 token 数组、用户/菜单 `_0x3e61d0`、页面可见/聚焦、ticker 实际 started 状态。游戏成功/失败由原规则判断；广告失败不得伪造胜利或额外奖励。广告流程成功条件是本请求最多继续一次、只释放本 token、不能解除别的暂停理由；失败也须有可观测终态或宿主明确保证的回调，而不是无限等待。

### 物理、碰撞、计分和可接受误差

- 已见物理调用 `world.step(1/60, 10, 10)`，固定步长为 1/60 秒；`_0x4bf21a(delta)` 累加 ticker delta，使用 `while (accumulator > 1)` 调用 `_0x49d791(1)`，没有在该循环内看到步数上限。严格 `>1` 不等于 `>=1`；恢复首帧 delta 截断取决真实 ticker 版本，未量测。
- 已见落袋距离判定 `<=0x14`（20 个渲染坐标单位）、sensor 与落袋 tween；物理空间换算、碰撞 fixture、全模式计分未全量核验，不将 20 宣称为物理世界袋口半径或改动规则。
- 验收拟定：广告/宿主阻塞期间物理 step 次数、回合扣时、落袋提交、owner timer 与该路径 tween 推进应为 0；解除最后一个阻塞后继续剩余时长，不补算广告经过的墙钟时间。
- 离散计分、费用、基础奖、激励 claim 和继续调用次数要求完全一致（误差 0）；同依赖、固定输入、固定物理步的前后位置/速度比较建议数值容差 1e-6 世界单位。跨设备依赖差异需先量测并另行确认，不声称此阈值已达成。
- timer 验收以虚拟时钟精确比较 remaining；浏览器端只要求不早于剩余时长，前台空载测试可先用 1 个固定步约 16.67ms 作为调度误差目标。后台节流不设无证据的固定上限。上述均为验收目标，非真实测试结果。

### 输入窗口与界面

保留现有选场、棋盘/HUD、瞄准/力度控件、暂停层、结算及可选激励控件位置，不新增广告美术，也不提供伪造界面截图。宿主 pause 的已读路径会取消瞄准、结束拖拽并禁用 canvas pointerEvents；插屏 beforeAd 不可据此认定也关闭了所有 DOM/PIXI 输入。广告期间输入监听器是否统一检查 token 尚未证明，需验收。

输入窗口要求：有效当前回合且没有阻塞时才提交击球；广告结束不能把暂停前的拖拽末事件变成自动发射。广告未 ready、失败或等待应有可理解反馈，不能把永久 disabled 当恢复完成。

玩家默认语言为 English；本轮无界面改动。后续新增文案可用 `Ad unavailable. Try again later.`、`Continue`、`Resume`、`Claim bonus`，默认英文构建设置 html lang=en；宿主日志不作为玩家错误反馈。中文浏览器不得自动切换默认语言；本轮未执行文字/页面语言验收。

## 4. 四项补丁逐项比较

### 4.1 结束前先锁终态 — PASS（静态，单请求范围）

A：`finish → resume(token) → paused=false → syncMute → ticker.start → continue`，done 在 continue 中才置 true。因此 resume/mute/start 同步调用 finish 时，外层仍未锁终态，可能重复恢复、重复递归；后面的 continue 去重不足以防止前面的恢复重入。恢复抛错也可能导致终态未锁。

B：先 `done=true; paused=false`，再执行上述外部操作。恢复期间同一请求的 afterAd/adBreakDone 重入会返回，迟到 beforeAd 也会返回。结束完成后重复通知不重做恢复/继续。

限制：锁住的是闭包，不拦截新请求。done 已置真后，恢复失败也不通过迟到终态重试。“最多一次尝试继续”不是“业务必然成功完成一次”。

### 4.2 token 释放的异常退路 — PASS（静态，正常原生数组假设）

B 在 `_carromAdResume(token)` 抛错后，只从数组移除当前 token；若此时 `_carromMatchBlocked()` 为 false，尽力恢复 match timers。

已读正常 resume 顺序是：找到 token → splice → syncMute → 未 blocked 才 resume timers。因此：

1. 释放前抛错：fallback 可以移除本 token。
2. 已 splice 后 mute 抛错：fallback 找不到 token 属于预期，仍会检查是否允许恢复 timers，避免仅因声音失败卡住计时。
3. 另一个 token/host pause 尚在：不恢复 match timers，不清空他人 token。
4. timer 恢复自己抛错：吞掉后继续 mute/ticker/业务尝试，但 timer 是否恢复成功不保证。

退路并非绝对不抛错：`Array.isArray` 后的 indexOf/splice 没有再套 try；若数组方法被替换、数组被冻结等，可能再次抛错并跳过后续步骤。正常可变原生数组足以支持局部结论；任意篡改环境不在保障内。正常 resume 找不到 token 会直接 return，no-beforeAd 的结束不主动重试既有 timers；不能拿此路径修复其他历史坏状态。

### 4.3 声音和 ticker 分别恢复 — PASS（静态隔离）；所有权保障 FAIL（静态）

B 的 syncMute 和 ticker.start 分别放在 try 中：声音抛错不会阻止 ticker.start；ticker.start 抛错不会阻止继续回调。A 的串行 finish 及 catch 内同一 try 不具备这种隔离。

syncMute 基于宿主暂停、剩余广告 token、可见/聚焦及 SDK audio 禁音标记计算全局 mute，不是盲目 mute(false)。用户音乐/SFX 组级设置另有接口；真实音频上下文解锁、组级互操作、实听结果未验证。

**B 仍无条件 ticker.start。** 不保存本请求开始前 ticker 是否 stopped，也不检查自己是否有恢复 ticker 的所有权。无 beforeAd、有另一个广告、宿主尚暂停或旧请求在新场景结束，都可能调用 start。不能由 token 计数推导 ticker 的 start 调用归属正确。

精确影响：B 的 `_0x4bf21a` 先检查 `_carromMatchBlocked()`；`_0x49d791` 在 ParticleManager/Tweener 前检查用户暂停、host pause、tokens，更新后又检查 host/tokens。因此剩余 host/token 阻塞时，**该路径的物理、ParticleManager 和 Tweener不会因 start 就推进**。不能误报“所有动画恢复”。但是 PIXI 渲染、shared ticker 的其他监听器、自带动画等是否推进需完整依赖证明；存在恢复原先停止的 ticker/额外耗电或画面变化风险。

若 Tweener 更新内部回调同步开启另一广告，更新后的检查可挡住后续物理；该次 Tweener.update 内剩余 tween 是否仍跑依赖库实现，尚不能保证立即中止。

### 4.4 业务继续回调异常隔离 — PASS（静态调用隔离）

B 在所有恢复尝试之后才调用 continuation，并捕获其异常。这避免把普通业务异常抛给异步 SDK 回调，也避免同步 SDK 分支误把业务异常当 unavailable。继续回调开始新广告时，旧 finish 后面没有常规恢复操作，可减少“新请求 pause 后又被旧请求 start”的覆盖。

但回调失败不回滚已经提交的费用/场景/奖励，且没有重试或失败通知。日志只有固定字符串，缺请求、场景与原异常详情；console.warn 本身也未保护。SDK 外层 catch 先 warn 后 finish，若日志接口抛错，仍可能不收口；这不属于正常 console 环境下的主要风险，但不能称为绝对 never-throw。

## 5. 时序与风险矩阵

优先级表示后续修复/验收顺序，不代表用户已批准改动。

| 情形 | B 的静态行为与边界 | 判定/优先级 |
|---|---|---|
| 同一请求恢复期间再次 finish | done 已真，直接返回；A 没有前置锁 | PASS（静态） |
| 重复 afterAd/adBreakDone、完成后 late beforeAd | finish 去重；late beforeAd 被 done 挡住 | PASS（静态） |
| 完成前重复 beforeAd | pause(token) 去重，但 mute/stop 副作用仍重复执行 | NEEDS_CONTEXT / P1 |
| 同步 SDK 调用抛错（未暂停/已暂停） | 外层统一 finish；本 token 尽力清理，继续最多尝试一次 | PASS（静态，正常日志/数组） |
| 同步终态完成后 SDK 又抛错 | warn unavailable，第二次 finish 返回；可能误导诊断，但不二次继续 | P2 |
| 异步 beforeAd 内 pause/mute/stop 抛错 | 外层调用 SDK 的 try 不捕获后来独立异步栈；可能部分暂停 | FAIL（全面异常隔离）/ P1 |
| 无 beforeAd 但有 adBreakDone | finish 继续；也会 syncMute/start，即使从未拥有 ticker 暂停 | P1 |
| 无 beforeAd，仅 afterAd | paused=false，不 finish；无其他终态会等待 | NEEDS_CONTEXT / P1 |
| 无任何终态回调 | 无 watchdog；有 continuation 消费者时不会得到继续通知；已注册 token 时可能永久阻塞 | NEEDS_CONTEXT / P1 |
| 两请求 A/B token 乱序释放 | 仅释放各自 token；remaining token 保持 timers/mute/main tick 阻塞，但 finish 都可 start ticker 和调用各自业务 | 部分 PASS；P1 |
| 恢复函数本身开启另一个广告 | 新 token 可阻塞主更新，旧 finish 后续仍无条件 start；不能宣称跨请求串行化 | P1 |
| host pause → ad end → host resume | ad end 不清 host flag；timers/main tick 仍阻塞，但会 start ticker；host resume 后才能允许 timers | 部分 PASS；P1 |
| host resume 时广告 token 仍在 | resume timers 内部 blocked 检查保留暂停；指针权限、音频及其他 UI 须实测 | NEEDS_CONTEXT / P1 |
| 原先 ticker stopped / 用户暂停 / 隐藏页 | done 不保存原状态；用户暂停主更新 guard 存在，但 match timer blocked 条件仅 host/tokens，不能推定用户暂停也暂停该 timer 系统 | P1 |
| 恢复失败后迟到结束回调 | done 已真，不重试；异常隔离不是恢复成功证明 | P1 |
| 跨场景旧插屏结束 | 无 round/scene owner 检查；可恢复全局 ticker、调用旧 continuation。token 所有权正确不等于业务 owner 正确 | P1 |
| continuation 抛错 | 已锁 done，不传播普通回调异常；副作用与业务失败无人回滚 | PASS（隔离）；P1（业务保障） |

宿主 pause/resume 自身还有范围外但相邻的风险：先改 host flag，再串行执行 timer/mute/取消瞄准/pointer 等；某步抛错会留下部分完成状态，重复事件因 flag 幂等可能直接返回而不能修复。插屏 finish 的新 try 不保护这些宿主函数。host boolean 是否足够表示宿主多暂停理由也取决真实 onPause/onResume 语义。

## 6. 动画、计时与业务流程影响

### 6.1 两类延迟，不混为一谈

- `_carromMatchSchedule` 是带 owner、remaining、version 的 setTimeout 任务系统：pause 保存剩余时间、清 handle 并使旧版本失效；resume 检查 blocked，删除无效 owner，仅重 arm 合法当前比赛任务。需要当前 activeMatch 且 parent 为 stage 才执行回调，减小跨场景误提交风险。
- `_0x338c29` 使用 Tweener 空对象延迟（time=毫秒/1000*60），不是上述 timer 系统；其暂停取决 guarded Tweener 更新路径。恢复、删除旧节点、动画 onComplete 的安全性还要检查各自 owner/round guard。
- 不建议以“清空全局 tween/移除所有节点”修复广告恢复；这会破坏落袋、queen cover、结果动画与下一局流程。先以暂停理由与任务 owner 管理，保持当前比赛状态。

### 6.2 已见入场消费者

`_0x4d0a10` 完成资格检查，设 entry pending、扣费并保存，调用 `_0x248455(type)` **未传 continuation**，之后立即 `_0x3153fe()` 创建比赛。因此不能写成“入场等插屏 continuation 才创建比赛”，也不能用该路径证明 continuation 业务必然可恢复。

已见比赛构造异常清理针对 constructing/active match、该 owner timers 和子节点 tween，并退款/回选场；它与广告 token 的全局暂停控制不同。实际广告结束是否正好触发入场、构造期间暂停是否完整、下一局动画是否恢复须运行验证。其他插屏消费者未全量定位，不宣称本项目调用覆盖 100%。

## 7. 插屏与激励广告必须分开

插屏 `adViewed/adDismissed/beforeReward` 为无业务空回调；补丁不增加发奖，也没有把插屏 done 与 rewarded generation 合并。**插屏修复不能替代激励链验收。**

激励 `_0x2e33a4` / `_0x4d02b5` 已读风险：

1. resolve 检查 generation/resolved，先锁 resolved、清全局业务 callback，再调用 callback，但没有 try；属于尝试去重，不是经济 claim 持久幂等。
2. afterAd 先锁 finished 再 resume token，resume 无保护；随后 syncMute/start 也不独立隔离，异常可阻止清理和下次 prepare。show/prepare catch 中 resume 也可能抛错，不能视为受插屏 fallback 保护。
3. 没有缓存 show fn 时展示入口直接 return，不通知业务 callback；prepare 抛错也未明确 resolve(false)，消费者可能一直等待。
4. afterAd 清全局 callback 并重新 prepare；若有效 earned 迟到，是否被丢弃取决真实事件顺序及 generation 契约。不能未经宿主证据认定“关闭即未赚取”，也不能保证任何乱序均安全。
5. 结果 `_0x47e567` 有 resultCommitted 与闭包 bonusGranted：基础胜利奖励先提交；激励成功会先加奖/保存，再做 round/parent 的 UI 检查。旧场景是否仍应交付已赚奖励须明确经济策略，不能一律因场景已换就废弃合法奖励，也不能把 UI guard 当经济 guard。
6. 转盘 `_0x5b20b9` 的额外奖金消费者未见同等闭包 claim guard；必须分别验证展示尝试去重和领取单位幂等，不把一次 resolved 等同于完整经济安全。

验收应记录 requestId、generation、claimId、round/scene owner、基础奖励和额外奖励前后值。claim 身份与持久去重策略目前未提供；本轮不新增字段或奖励补丁。

## 8. 未执行验收清单

下列全为计划，**本次每一项均未执行**。模拟回调脚本只可证明被模拟条件下的代码行为；浏览器回归不能证明 AHA 契约；真实 AHA 必须另附 SDK/bridge 版本、设备、事件序列与日志。

| 编号 | 用例/注入 | 必须观察的结果 |
|---|---|---|
| T01 | 正常 beforeAd → afterAd → adBreakDone | token 净增减为 1，继续次数 1，时长与动画连续 |
| T02 | resume 在删除 token 前抛错 | fallback 只移除本 token，后续步骤独立尝试 |
| T03 | resume 已删除 token 后 mute 抛错 | 不误删他人 token，允许时恢复 timer |
| T04 | resume timer 抛错 | 后续 mute/start/continue 仍尝试，失败有记录，不假报恢复成功 |
| T05 | syncMute 单独抛错 | start 与 continue 的调用次数不受阻 |
| T06 | ticker.start 单独抛错 | continue 仍一次；真实画面失败不能因继续被标 PASS |
| T07 | continuation 部分提交后抛错 | 不二次调用；记录业务失败/余额/场景，不假设自动回滚 |
| T08 | resume/mute/start 内同步重入同请求结束 | 无递归恢复、无重复继续 |
| T09 | continuation 同步发起新广告 | 新 token 不被旧请求删除；旧恢复不覆盖新暂停 |
| T10 | 恢复函数中同步发起另一请求 | 检查旧 start、副作用与新暂停归属；主更新保持 blocked |
| T11 | beforeAd 重复、afterAd/done 重复及乱序 | done 后无副作用；完成前重复暂停行为可观测 |
| T12 | 无 beforeAd，有 done | 继续一次；核对原 ticker stopped 是否被擅自改变 |
| T13 | 无 beforeAd，仅 afterAd；另测无所有终态 | 记录当前等待行为，并与宿主承诺对照，不假报通过 |
| T14 | SDK 同步 throw：before 前、before 后、finish 后 | 各路径有终态、当前 token 不残留、不重复继续 |
| T15 | 独立异步 beforeAd 分别在 pause/mute/stop 抛错 | 浏览器捕获错误和部分状态；核对宿主是否继续回调 |
| T16 | A/B 两 token 以两种次序结束、插屏/激励重叠 | 剩余 token 期间 mute、timer、物理/tween 阻塞；检查 shared ticker |
| T17 | host pause/ad end/host resume 全部交错 | 最后阻塞解除前不推进；pointer/音频按原因恢复 |
| T18 | host pause/resume 各操作抛错及重复事件 | 检测 flag 与 timer/pointer 实态不一致 |
| T19 | 原 ticker stopped、用户暂停层、隐藏/聚焦切换 | 不擅自解除用户暂停；明确 timer 与渲染预期 |
| T20 | 用户音乐/SFX off、SDK audio off、未解锁上下文 | 用户设置保留；按真实可见性/上下文验证实听与静音 |
| T21 | 跨场景旧回调、旧 timer、旧 tween 完成 | 不更改新比赛；合法已赚奖励按明确策略交付 |
| T22 | 真实选场扣费、广告期间构造、构造失败 | 入场/退款一次，owner 清理正确，不孤立比赛或卡动画 |
| T23 | 广告期间拖拽/触摸/键盘，恢复后的末事件 | 不误击球、不叠加输入；桌面及手机真实输入 |
| T24 | 落袋/queen cover/AI 延时/超时扫描中插入广告 | 保持回合与提交次数，暂停时间不参与扣时 |
| T25 | 30/60/120fps、卡帧、长暂停后的首帧 | 记录固定步数、accumulator、ticker delta 截断与误差 |
| T26 | 激励未 ready、prepare/show 同步失败及异步失败 | 消费者得到明确结果或符合宿主承诺的状态，不永久禁用 |
| T27 | 激励 earned/dismissed/afterAd 重复、乱序、晚到 | 有效 earned 不误丢；未赚不加奖；依据真实宿主契约判断 |
| T28 | 重复准备/展示、旧 generation、新场景、重新加载 | attempt 与 claim 分层去重，余额和领取资格一致 |
| T29 | 结果基础奖/bonus 与转盘 double | 分别核对币值与保存，插屏绝不额外发奖 |
| T30 | 下一局、返回菜单、结果按钮及正常动画完整链 | 无卡死、孤立节点、错误 UI、未处理控制台错误 |
| T31 | 默认英文及中文浏览器环境 | 英文主要界面、素材文字及 html lang=en 一致 |

后续代码/测试阶段还必须在最终源码/资源改动后真实执行 `npm run build`、`npm test`、`npm run check`；check 启动并自动停止本地服务器，访问最终 dist，覆盖桌面/手机真实点击、核心玩法、控制台错误与截图，输出 evidence。最终 dist/index.html 及相对资源展开小于 10MB，验证后不得重建或改 dist。本轮不为完成表格而创建空壳脚本或静态模板。

## 9. 真实 AHA 契约未知清单

所有项目均为未闭合；不以通用 GameSnacks 字段名或其他游戏案例替代。

| 编号 | 未知项 | 当前证据 | 闭合所需 |
|---|---|---|---|
| U01 | 两输入的实际部署关系和完整变更范围 | 文件名/局部对照 | 版本记录、部署文件校验、完整 diff |
| U02 | PIXI/planck/Howler/Tweener 和 SDK bridge 版本 | 明确调用/共享 ticker 配置 | 完整依赖、启动入口与构建包 |
| U03 | 混淆 SDK 属性与 type 对应的真实 API | 0x49d 属性及回调对象 | 字典解码、包装层与宿主 SDK 文档 |
| U04 | 是否允许重叠广告、回调同步重入 | 闭包独立但无全局请求互斥 | SDK 明确限制及真实回调日志 |
| U05 | no-beforeAd 是否仍保证 done，afterAd 是否仅配对 before | paused 条件与 done 回调已见 | 有填充/无填充/拒绝/失败/取消的事件保证 |
| U06 | callback 异常由谁捕获，是否继续终态 | 外层仅包 SDK 调用栈 | 宿主异常契约及注入观察 |
| U07 | earned/closed/after 的合法排序和迟到窗口 | rewarded 全局 callback/generation | 奖励事件定义、取消语义、真实轨迹 |
| U08 | host onPause/onResume 是否表示聚合状态及重复规则 | boolean 幂等注册路径 | 生命周期文档、后台/广告/焦点交错轨迹 |
| U09 | shared ticker 的全部订阅与原停止所有权 | 无条件 start，主更新有 guard | 完整监听器盘点、停止理由、运行截图/计数 |
| U10 | 全部输入门禁、用户暂停与 timer 预期 | host pointer 禁用；timer blocked=host/tokens | 输入入口盘点及业务暂停规格 |
| U11 | continuation 全部消费者与 owner 生命周期 | 入场未传 callback，其他调用未全量定位 | 全量调用者、状态/失败消费者清单 |
| U12 | 跨场景奖励交付、claim 身份和持久幂等 | result 闭包 guard、转盘局部行为 | 明确经济策略及保存/领取边界 |
| U13 | 恢复失败、日志失败、无终态的产品处理策略 | 尽力 try、无 watchdog | 宿主保证与明确超时/补偿策略；不得任意超时解广告暂停 |

本轮没有为需要契约的结论编造答案；当前用户要求的是审查与区分证据，足以交付这一阶段。若下一阶段需要选择超时策略、变更奖励策略或框架迁移，须以 request_user_input 获取真实决定后再改代码。

## 10. 真实验证记录与收口

| 工作 | 本次实际结果 |
|---|---|
| 选定技能/冻结知识/参考读取 | 已实际读取；未选模块入口的拒绝单独记录 |
| A/B 核心插屏对照、B 主更新 guard | 已完成静态代码审查，有函数与读取窗口证据 |
| 完整机械 diff/依赖版本解码/全量调用覆盖 | 未完成，不声称全部覆盖 |
| npm run build | 未执行（本轮为 prototype，无本次可构建工程产物） |
| npm test | 未执行 |
| npm run check / Chromium | 未执行，无浏览器截图或动态 PASS |
| AHA bridge、模拟器、真机、音频实听、后台回执 | 未执行/未提供，真实宿主验收 BLOCKED |
| 参考源码、游戏资源修改 | 无 |
| 原型审查报告 | `/workflow/prototype.md` |

后续建议顺序（不是已授权的实施）：先闭合终态/奖励/暂停契约与 ticker 所有权，再在代码阶段做最小补丁和故障注入测试，最后真实浏览器与 AHA 分层验收。保持 token 仅按请求释放、普通业务异常隔离、动画/计分规则不变；对恢复失败增加可观测证据而不是把吞异常当成功。当前只交付审查报告，不推进下一阶段。
