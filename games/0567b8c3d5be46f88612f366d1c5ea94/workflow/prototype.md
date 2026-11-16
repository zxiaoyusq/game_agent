# Carrom 自由模式待覆盖出口审查

## 范围与结论

本报告为 attempt=2 恢复交付的原型阶段只读审查产物。用户补充授权写入本报告。阶段确认仍待工作流处理。

方案具备补齐旧版出口遗漏的条件依据，当前版本安全性为 NEEDS_CONTEXT，真实运行验收为 BLOCKED。扩大条件后可以将自由模式 pending 的无出杆或超时导入既有结算入口，但返棋、撤分与换手结果仍依赖当前规则函数、队列归属和异步生命周期。

## 输入与证据边界

- E-01，实际读取的旧版参考路径为 ref/mcp-inputs/mac-codex/dd8b79747ae3b111ad0a83ec8088b69b7632ec9f122e685b76601e731d52ffe8/Carrom_current_dd8b7974.js。相关正文已通过 read_reference 分段读取，范围覆盖字符偏移 0 至 264000。路径中 dd8b7974 的版本角色依据用户说明。未独立计算该文件哈希。
- E-02，操作方陈述当前 game.js SHA256 为 66196b30aaf18038204294b0f8238f89b667237cb68d288bed73b7b71851e290。当前文件正文和实际加载入口均未提供，本报告未读取或审计当前源码，也未校验该哈希。
- E-03，操作方陈述四个 AI 无出杆出口及 timeout 出口的条件由 mode===1 && _0x4268e2 扩展为 (mode===1 && _0x4268e2)||(mode===2 && _carromFreestyleQueenState.phase==='pending')。命中后停表、置续杆 false、调用 _0xbdafb3(_carromTurnId)，AI 还锁定旧出杆。该陈述用于条件推演。
- 已读取本轮冻结的 genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md。
- 已读取 game-reverse-engineering/SKILL.md 及同包 execution-protocol.md、global-rules.md、unknowns-ledger-template.md。gameplay-logic-reverse 子模块入口读取被工具拒绝，未作为证据。

旧源码中的自由模式策略带 provisional 注释，其边界规则属于项目暂定实现。竞品规则与竞品运行行为均缺直接证据。项目选择的 Canvas Web 配置属于工作流配置，旧参考直接出现 PIXI 和 planck，审查沿用旧参考的真实调用链。

## 旧源码调用链

四个 AI 无出杆出口分别位于 _0x50a0ff 的 fallback 为空、_0xd6b627 参数无效、_0x4b3cc6 参数无效、_0x4b3cc6 盘面失效且重试耗尽。旧版均仅在普通模式待覆盖时进入 _0xbdafb3，否则直接进入玩家回合。_0x49d791 内 timeout 具有相同条件。

_0x24bb4a 将 _0x3a1262 置 false，关闭输入及瞄准。其中 `_0x1a373b - 1` 为无赋值表达式，计时停止依赖布尔门禁。_0xbdafb3 等待物理静止，校验 turn 与已结算标记，然后提交当前回合。自由模式结算先清 _0x4268e2，从 _0x31089b 快照构造 actor、foul、queen、ordinary，再调用 window.CarromDiscRules.freestyleQueen。该外部函数正文尚缺。

自由模式通过 _carromReturnFreestyleQueen 创建返还红棋、撤销历史积分，再替换 queen state。回合最终根据续杆标记选择玩家或 AI 入口。

## 规则与时序核查基线

核心循环为回合输入或 AI 规划 → 出杆及物理演化 → 入袋排队 → 静止结算 → 红棋覆盖决策、计分或返棋 → 续杆或换手。无出杆和超时应在待覆盖状态下结束该次覆盖机会，具体返棋规则须由当前 freestyleQueen 正文和项目规则补证。

旧版物理调用为 step(1/60,10,10)，ticker 累积后逐步更新。补步循环未见本次范围内的长帧上限。入袋扫描采用距离 ≤20，扫描位于该 tick 的物理 step 之前。timeout 位于入袋扫描之前，须检查同 tick 超时与入袋的交错。

旧版玩家出杆要求有效回合、对应指针及 strength≥0.25。AI 在移位、瞄准、延迟执行后施加冲量，旧盘面快照每轴位移大于 1 个坐标单位即判变化。计时外层受桌号、模式和教程约束，旧版自由模式桌号 0 未进入该 timeout 分支。以上为实现值，位置单位映射与可接受物理误差仍待当前工程补证。计分次数、返棋数量和回合推进次数要求精确一致。

旧版自由模式分值配置为红棋 50、两类普通棋 20/10，目标分变量初始值为 160。红棋先记分，pending 时暂缓达标胜负判断。当前分值、胜负和覆盖成功失败条件须读取当前依赖核实。界面核查范围为棋盘、回合计时框、击球器、瞄准线、积分 HUD 与结果层，本次沿用已有布局。

## 验证矩阵

下表运行要求均为待执行的验收条件。

| 项目 | 旧源码证据与条件风险 | 当前源码补证 | 真实运行验收条件 | 当前状态 |
|---|---|---|---|---|
| 五处条件 | 扩展保留普通模式分支并新增自由模式 pending。phase 本身未证明 owner 与 actor 一致 | 五处完整上下文、状态初始化、owner 约束、其他直接换手出口 | 四个 AI 出口分别触发，玩家与 AI timeout 分别触发，普通模式及非 pending 回归 | NEEDS_CONTEXT |
| timeout 可达性 | 自由模式桌号 0 被旧版外层门禁排除 | 当前外层条件及 turnTicks 正文 | 分桌号验证超时路径与防卡死条件 | NEEDS_CONTEXT |
| 停表及续杆 | _0x24bb4a 停止计时门禁，未重置 foul；其中计数减法未赋值 | 五处停表、续杆 false、return 顺序 | 结算等待期间不再倒计时，无额外换手与冲量 | NEEDS_CONTEXT |
| 入袋队列 | _0xbdafb3 复制 _0x31089b，逐项 splice 移出；未按 round/turn 过滤 | 所有入队、清空、异常中断及归属路径 | 空杆队列为空，残留项不得重复计分或误判覆盖 | NEEDS_CONTEXT |
| 犯规标志 | _0x530863 在回合入口清零，空队列且 foul 时调用普通棋罚还函数 | 五处是否保留正确 foul，是否有遗留或新增赋值 | foul=false 不误罚普通棋，foul=true 不漏罚，返红棋及罚棋分别计数 | NEEDS_CONTEXT |
| 重复结算 | 静止前可排多个重试，静止后由 _carromSettledTurn 去重 | 门禁顺序、回调捕获原 turn、round 校验 | 同 tick 失败出口、timeout、延迟结算交错，计分返棋换手各一次 | NEEDS_CONTEXT |
| AI 旧出杆 | _carromAiShotTurn 阻止最终发杆，移位瞄准回调另有 round/turn 检查 | 锁设置时机及规划、移位、瞄准、重试全链 | 等待结算及换手后旧回调无冲量，不移动玩家击球器或重显旧瞄准线 | NEEDS_CONTEXT |
| 调度队列清理 | _0x338c29 为匿名 tween，统一检查活动局和 round，未统一检查 turn；未见全局清空调度队列 | 各回调 turn 检查和任务取消归属 | 暂停恢复、重开、菜单往返及延迟交错无旧局副作用 | NEEDS_CONTEXT |
| 返红棋 | _carromReturnFreestyleQueen 生成红棋并使用 returnCommitted 局部去重 | freestyleQueen 正文、owner、历史和 state 替换语义 | pending 失败后仅返一枚，历史、场上棋、刚体、HUD 一致 | NEEDS_CONTEXT |
| 得分撤销 | 返红棋撤销对应历史积分，缺历史时回退 state.points | points 有限性、归属、缺失及重复历史处理 | 撤销原 owner 的正确积分，无重复加减及异常负值 | NEEDS_CONTEXT |
| 胜负边界 | pending 时暂缓目标分判断，之后再判断胜负 | 当前阈值、同分规则及结果去重 | pending 达标不提前结束，失败覆盖撤分后正确判断，结果只提交一次 | NEEDS_CONTEXT |
| 状态重置 | 重开清 history/queen state 并递增 round，回合入口清 foul/续杆并递增 turn | 菜单、模式切换、结果页、返棋锁生命周期 | 返棋和计分中重开或切换，旧回调不污染新局，再次 pending 正常结算 | NEEDS_CONTEXT |
| 拥堵返棋 | _0x1f3ae5 有有限位置搜索，未见失败返回 | 当前搜索结果及无合法点处理 | 中心和候选点拥堵时无重复刚体、异常重叠或不可继续操作 | NEEDS_CONTEXT |
| 帧率和物理等待 | _0xbdafb3 以 _0x56abf7 等待静止并延迟重试 | trimVelocity、长帧策略、等待上限 | 正常帧、长帧、暂停恢复及长期微动均核对状态收敛和回合数 | NEEDS_CONTEXT |

## 重点条件风险

1. 新条件只检验 pending，需确认其 owner 属于当前覆盖回合。异常 owner、跨回合残留或状态尚未提交会影响返棋归属。
2. shot 使用当时队列与 actor/foul。残留普通棋可能被规则函数解释成覆盖成功。仅扩大出口条件无法保证队列归属。
3. 停表与锁出杆分别保护不同路径。锁最终冲量后，旧移位和瞄准 tween 仍可能更改表现，须核查整个等待窗口。
4. _0x338c29 的 round 保护无法统一解决同局旧回合任务。调用者应捕获原 turn，旧任务执行时读取当前 turn 会削弱去重。
5. 无出杆且 foul=false 仍需触发 pending 失败覆盖决策。不得为了返红棋随意置 foul=true，否则可能增加普通棋罚还。
6. 返红棋使用 returnCommitted 后替换 state，幂等保护是否跨重复回调持续有效依赖当前规则状态机。
7. 旧版物理运动期间结算可不断重试，若异常微动不收敛，停表后仍可能卡住。须由真实运行证明可恢复路径。

## 未知清单

| 编号 | 未知项 | 闭合所需证据 | 当前证据 | 状态 |
|---|---|---|---|---|
| U-01 | 当前文件及实际运行加载副本身份 | 当前 game.js 全文、独立 SHA256 与实际加载入口配对 | E-02 操作方陈述 | 未闭合 |
| U-02 | 五处完整变更及旧 AI 锁链 | 当前五处上下文与全部相关异步调用链 | E-01、E-03 | 未闭合 |
| U-03 | 自由模式覆盖和积分规则 | 当前 CarromDiscRules.freestyleQueen、turnTicks、目标分等依赖正文 | E-01 调用点 | 未闭合 |
| U-04 | 方案真实运行效果 | 矩阵逐项运行日志，记录 round、turn、actor、phase、owner、foul、续杆、队列、积分和冲量次数 | 无 | 未闭合 |
| U-05 | 异常队列及拥堵返棋行为 | 对应反例的运行前后快照、坐标及刚体计数 | E-01 有限搜索与队列实现 | 未闭合 |

## 真实执行与产物

当前 attempt 从已返回的合法工具结果继续，检查点中无挂起工具。已通过 request_user_input 获得写报告授权，通过 ls 确认 /workflow 为空后创建本报告。产物路径为 /workflow/prototype.md。

验证方式为已读取旧参考的静态调用链核对和对操作方陈述的条件推演。当前阶段为原型审查，未执行 npm run build、npm test、npm run check，未获得浏览器运行、截图或真机证据。运行验收状态为 BLOCKED，缺当前源码和对应可运行工程及运行记录。

游戏源码、资源与发布产物未改动，未构建、打包或发布。报告落盘不构成用户确认，也不推进后续阶段。
