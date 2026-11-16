# Carrom 滑条多指取消与隔离审查

## 范围与结果

当前阶段：prototype；恢复轮次：attempt 2。仅交付审查文档，不实施补丁、不创建测试工程、不迁移引擎、不推进下一阶段。用户要求“禁止自行修改工程”；本轮仅写本工作流要求的报告，不改任何游戏源码、配置、资源或参考文件。

- **PASS（静态审查产出）**：完成摘要模型、d201 滑条静态核对、条件反例、最小修复建议、验证矩阵。
- **NEEDS_CONTEXT（当前版缺陷判定）**：未读取或运行当前开发版，也未读取最新 2cdbc90b；摘要不能证明完整事件绑定、身份适配或运行路由。
- **NEEDS_CONTEXT（运行验收）**：本轮没有执行函数注入、浏览器、真机或宿主测试。以下反例是可供重放的推导，不是实测结果。

上一轮 Connection error 后，本轮成功重新读取旧参考的目标片段；不将旧轮验证作为本轮成功。原型审查未进入代码/测试阶段，未运行 npm run build、npm test、npm run check，未生成 dist、ZIP 或截图。

## 1. 输入与来源

当前版唯一信息来源：用户摘要——startSlide 检查 _enable 与 _sliding，锁定布尔状态并保存坐标；moveSlide/stopSlide 按 _sliding 判断，摘要未见 pointer 标识匹配。摘要没写出的检查不等于源码不存在。

旧参考路径（相对 ref/）：
`mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js`

版本角色：d201 仅为旧版静态对照，不是当前开发版或最新 2cdbc90b。工具返回正文为部分字符窗口，不声称完整读取全文件。定位锚点比近似偏移更可靠：

| 证据 | 实际读取定位 | 可得结论 |
|---|---|---|
| 滑条类 _0x570109 / 内部 _0x1bb809 | offset 474000, limit 24000 | 完整构造、enable/start/stop/move/value 片段；没有在这些方法中保存或比较身份 |
| 宿主 pause/resume | offset 16000, limit 8000 | pause 清 aim、调用有条件的 _0x41684e、直接置 slider._sliding=false，并关闭 canvas pointerEvents；resume 恢复 pointerEvents |
| 滑条实例 _0x147a99 及消费者 | 先前已读约 40000–65000 | value 更新击球器位置；结束调用 _0x41684e；有业务、host/ad、教程条件 |
| aim cancel / 原生输入桥 | 先前已读约 60000–70000 | 独立 aim 身份与原生 pointercancel/touchcancel 路由；这些已读回调不调用 slide cancel |
| 游戏自身暂停 _0x5e0129 / 教程 | 先前已读约 88000–95000 | 已读暂停函数显式取消 aim，未见显式取消 slider；不等于其他路径不存在取消 |
| 广告调用点 | offset 95000/16000、111000/16000 | beforeAd 调 _carromAdPause(token)，结束路径调 Resume；未定位其定义，不能断言取消细节 |

已读冻结资料：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md。已读技能：game-reverse-engineering/SKILL.md，以及同包 references/execution-protocol.md、global-rules.md、unknowns-ledger-template.md。采用证据分层、唯一 owner、幂等提交和未知清单方法。专项 modules/gameplay-logic-reverse/SKILL.md 未被本轮选中，读取被拒；不声称采用其正文。

d201 可见 PIXI、box2d=planck 和 GameSnacks。Canvas Web 是本工作流资料选型，不是旧游戏使用原生 Canvas 2D 的证明；本审查不改框架。

## 2. 旧版静态核对与参考取舍

### 滑条本体

d201 的局部范围是 30..430，value=(striker.x-30)/400。start 保存 `event.data.global.x - _0x24b13c/2` 与初始 striker.x；move 用新 global.x 减起始坐标形成位移并 clamp，随后 emit 混淆键 0x3c8；stop 清布尔并 emit 0x421。0x3c8 在其他原型更新函数、0x421 在显式 stop 等上下文对应 update/stop；未执行混淆解码器，本报告保留原键作为定位依据。

- setEnable(false) **确实清 _sliding**，这是已闭合的旧版事实。
- start 检查 host/ad、_enable、_sliding；第二个 start 因布尔锁被拒绝。
- move 检查 host/ad、_enable、_sliding；没有身份比较。
- stop **同时检查 _enable 与 _sliding**，不使用事件参数，也未在方法体检查 host/ad。这与当前摘要只描述 _sliding 并不等同。
- 构造器将混淆事件键 0x43e 绑定 start，0x39c/0x2ea 绑定 stop，0x109 绑定 move；没有在该构造器片段绑定 cancel。0x43e 在其他对象显式 pointerdown 对照可支持其含义；其余事件仍应核对完整映射和 PIXI 版本，不能以猜测替代运行分发。

### 业务后果边界

滑条 update 消费者检查 host/ad 和业务门禁，再映射 value 到击球器 worldX，并更新位置/碰撞提示。stop 消费者检查类似门禁后调用 _0x41684e，并在相应教程步骤恢复瞄准教学。因而“滑条内部状态变化”与“击球器业务接受变化”是两个断言：消费者拒绝不保证内部 dragging 未被提前清掉。

本次没有证明 slider stop 会击球、计分或提交结果，不使用“第二指释放必然误击球”的说法。_0x41684e 的完整合法落点处理需要进一步核对。

点击轨道是当前版后续新增功能：不从旧版的容器命中区/相对位移公式推断新功能行为，不把建议改成新的轨道玩法。

## 3. 核心循环与规则状态

保留玩法链：合法放置窗口内拖滑条调整击球器 → 结束放置并核对落点 → 瞄准/力度输入 → 发射 → 物理运动、碰撞和进袋 → 结算回合 → 下一次合法放置。后半段仅为审查边界，不重新定义 Carrom 计分算法。

摘要模型：I=idle，D=dragging（只有布尔，无 owner 信息），X=业务不可交互。X 是分析抽象，不声称当前源码有此状态。

| 当前状态/事件 | 布尔摘要可推导行为 | 建议行为 |
|---|---|---|
| I + 合法 A.down | 保存 A 坐标，转 D | 记录 owner(A)、dragEpoch、起始值；转 D(A) |
| D + B.down | 被 _sliding 拒绝 | 拒绝；不改 A 身份、起始坐标或值 |
| D + B.move 已进入 handler | 只要门禁通过，可能按 B 坐标更新 | 非 owner 无副作用 |
| D + B.up 已进入 handler | 只要门禁通过，可能结束 A | 非 owner 无副作用 |
| D + A.move | 更新并限幅 | 保持既有坐标映射与限幅 |
| D + A.up | 正常结束 | 清 owner 后仅一次正常结束通知 |
| D + A.cancel 或全局阻断 | 摘要不足 | 独立 cancel，清状态，不发正常 stop |
| D(A) + B.cancel | 摘要不足 | 忽略 B；全局 pause 才无条件取消 A |
| X + 任意 down/move/up | 摘要不足 | 不接管、不提交；恢复后须新的合法 down |

输入窗口：只有已有合法放置业务门禁允许、enable=true、所有暂停 owner 均释放且教程允许滑条时，才能接收新 down。取消和清理不应被 enable=false/paused 提前 return 阻挡。身份匹配不可用坐标距离或 isPrimary 替代。

成功标准：整个拖动仅 owner 能改变值；正常结束至多一次；阻断后无残留 owner，正常 stop 次数为零；恢复可新开拖动。失败标准：非 owner 改值/结束、取消被当正常提交、重复通知、残留锁、恢复污染新拖动。

## 4. 条件反例：可供人工/函数级重放，未执行

前提：enable=true，业务/host/ad 门禁通过，A 与 B 为不同身份，事件坐标已转换至同一游戏坐标空间。下列 down/move/up 表示实际调用对应 handler，不保证任何浏览器天然如此分发。

### R1：第二指移动污染

示例沿用旧版公式，临时令横向偏移为零，初始 striker.x=230：
1. A.down(x=230)：_sliding=true，dragPosition=230，tempPosition=230。
2. B.down(x=350)：start 被拒，起始字段不变。
3. B.move(x=370) **确实送入 moveSlide**：x=230+(370-230)=370，value=0.85；A 尚未移动，正确隔离期望仍为 x=230、value=0.5。
4. A.move(x=240)：x=240，value=0.525，可能出现回跳。

只要 B.move 到达并且门禁通过，d201 方法体对此序列没有 owner 隔离；当前摘要支持同类风险，但当前坐标算法未知，不把这些数值复制成当前版结果。

### R2：第二指释放提前结束

A.down → B.down 被拒 → B.up **送入 stopSlide** → _sliding=false，结束通知一次 → A.move 被忽略 → A.up 不再正常结束。消费者可能因门禁拒绝该结束通知，但 A 的锁仍可能已清。

### R3：迟到事件污染新拖动

A.down → pause/cancel 清状态 → resume → C.down → 迟到 A.up 进入 stop。只有布尔时可误结束 C；owner 不同可挡住。若运行系统复用同一个数字 ID，单加数字匹配仍不充分：需要会话有效性与真实路由顺序证据。

### 不构成当前漏洞实证的流

- B.down 在滑条上，随后 B.move/up 未被框架送到滑条：上述反例不发生；锁拒绝 start 也不必然阻止框架记录 B 的按下目标。
- B.down 在滑条外、始终未命中且 move 没有全局转发：可能无干扰。
- B.down 在外，B.move 后进入滑条：是否分发 move 取决于命中/捕获策略；即使 B 从未成功 start，只要 move 被送入仍有条件风险。
- A 先释放而 B 留下：B 不能自动继承拖动；新策略需要新的 down。
- 系统仅路由 primary pointer，或适配层已过滤 owner：可能隔离；必须读适配层/运行日志，不能仅凭缺字段排除或确认。
- 合成 dispatchEvent 与直接函数调用只能分别证明 DOM监听或局部状态规则，不能证明真实多点命中、捕获和 PIXI 分发。

## 5. 最小修复设计（建议，未实现）

### 5.1 保留一个输入 owner

优先保留现有 PIXI 输入通道，在边界统一读取其 interaction event 的稳定身份；如需接原生取消，仅增加对应桥，不再添加一套并行 move/up 处理玩法。

owner 建议记录 `{source, type, id, nativeId, dragEpoch}`。source 区分 PIXI/DOM pointer/legacy touch/mouse；PIXI ID、DOM pointerId、Touch.identifier 不可假定数值等价。nativeId 只有在同一个 down 的 originalEvent 能建立关系时保存。合法 ID=0 不能用 `id || fallback` 丢弃；身份缺失时采用经确认的单 mouse 通道或拒绝歧义 touch，不让“未知身份”匹配任何 owner。

仅合法 down 可占有 owner，所有 move/end/cancel 都比较 owner；mouse 接受既有主键策略，普通 hover 无 owner 不更新，buttons 丢失且未收到 up 时可按匹配鼠标会话取消。不要用 isPrimary 排斥真实可接受的第二个独立新会话。

### 5.2 正常结束与取消分离

- `finishSlide(event)`：仅匹配 owner 且会话有效，先使状态/owner 失效，再走原来的唯一 stop 消费者，避免重入和重复释放。
- `cancelSlide(reason, event?)`：系统取消若带身份，仅取消匹配 owner；pause/ad/reset/disable 等明确全局阻断可无身份取消。先清状态、身份、坐标缓存/会话，再释放捕获或清监听；重复调用无副作用。不能依赖 enable=true，也不能调用正常 stop 冒充取消。
- 最小位置策略建议保留最后已接受值，不因 cancel 额外移位或回滚；若原业务要求在停止时校正非法落点，应复用既有落点校正函数并独立于 stop/教程推进，而非复制第二套算法。该校正是否必须在暂停前同步完成仍需 _0x41684e 与当前源码确认；不直接删除旧宿主 pause 中的调用。
- pointercancel/touchcancel、匹配的 lostpointercapture、canvas外释放、blur/hidden 与销毁的兜底均进入取消/既定外释放路径。lostpointercapture 因主动正常结束而触发时应无操作。touchcancel 用 changedTouches 找匹配 identifier，不能任取 touches[0]；无身份的 fallback 只有确证 owner 已不在 active touches 时才取消。
- DOM setPointerCapture 若采用，要确认与现有 PIXI 路由兼容，并成对释放；捕获不等于 owner 隔离，单独加捕获不足以修复多指。

### 5.3 去重与会话隔离

现代 pointer 与 legacy touch/mouse 选择一条权威路径。触摸产生的兼容 mouse 不得再次提交；优先使用适配器去重、sourceCapabilities（可用时）及已知活跃触摸来源，不能仅靠任意全局时间延迟。不要对整个页面强制 touch-action:none；只在实际游戏输入区域按滚动策略决定。

dragEpoch 用于使延迟回调/注册闭包失效，必须在 down/cancel/finish/reset 维护。但在收到旧原生事件时才读取当前 epoch 没有辨识能力；同 ID 复用需确认事件排序、取消时清监听/框架跟踪与可靠时间或 down token 关联，不声称加 epoch 就能识别所有迟到 DOM 事件。

### 5.4 生命周期与教程

pause/ad/tutorial/disable/reset 调同一个 slide cancel owner，而不是各处直接写 _sliding=false。保留 host pause、自身 pause、ad token 各自的所有权：恢复一个只释放自身阻断，其他 owner 活跃时仍不可交互。不要广告结束就无条件打开输入。

教程正常拖动的既有推进不重做；cancel 只收尾视觉，不额外推进步骤。旧参考在 update 时已经可能推进步骤，所以“取消不推进”指取消路径不再加一步，而非自动回退已经合法发生的步骤。需要转场时恢复对应教程遮罩/zOrder、移除旧动画/监听，不把说明弹窗和实际教学步骤混成一项。

## 6. 布局、语言、物理与误差约定

本审查不制作新界面：保留棋盘、下方滑条、瞄准层、HUD、暂停菜单、广告遮罩和教程层；遮罩视觉出现不能替代输入门禁。建议调试日志在玩家层外，记录 owner 和原因，不改变美术。若将来增加玩家提示，默认英文，例如 “Drag to position”、“Drag cancelled”、“Paused”；本轮未核验既有 UI 语言，也未修改 html lang。

物理步长：当前版实际 dt、子步、碰撞和计分规则未提供，本报告不把品类示例数值声明为现有参数。后续回归建议按真实 dt 固定步输入并比较同一基线；若需独立输入审查模型，可选 1/60s 固定步并明确它只是测试时钟，原生 pointer 事件按顺序即时处理，不等待物理帧。验证 30/60/120Hz 渲染与后台恢复，禁止把长暂停间隔作为一次大物理步。

碰撞/计分：保持当前合法放置检测、射击碰撞、进袋和计分唯一 owner；滑条取消不发射、不加分、不推进回合，正常 slide stop 也不能被假设为计分。确认最后合法位置的策略后才验收物理落点。

可接受误差（建议验收阈值，不是实测）：非 owner 导致的 value、owner、通知次数改变必须为零；坐标映射的数值对照误差 ≤1e-6 normalized value，视觉位置误差 ≤1 个逻辑像素；正常 end 至多一次、cancel 正常 end=0。重开与取消同步清会话，下个事件即能看到清理结果，不用超时自动解锁掩盖残留状态。

## 7. 分层验证矩阵（全部未执行 / NEEDS_CONTEXT）

每项记录：版本/构建哈希、浏览器及 PIXI 版本、输入来源/type/id/nativeId、event target/currentTarget/global/client坐标、命中/捕获、时间序号/dragEpoch、enable/暂停 owners、教程步骤、value前后、owner前后、update/stop/cancel/发射/计分次数。

| 编号 | 事件与位置 | 函数级预期 | 真实环境补充 |
|---|---|---|---|
| T01 | mouse 主键 down→move→up；hover、右键 | 原行为不退化；仅一次 finish；hover无更新 | 桌面实际点击和拖动、窗口外释放 |
| T02 | A/B 都按滑条；A静止，B移动后先松 | B不改值不结束；A可继续 | 两触点是否被 PIXI 送到同容器必须记录 |
| T03 | 同上，但A先松，B再移动/松 | finish一次；B不继承 | 各命中位置与先后释放均覆盖 |
| T04 | B按滑条外→进入→移动/松 | 无论是否送入，B不干扰 | 区分 move命中和up按下目标路由 |
| T05 | B轨道 / A旋钮与反向顺序 | 新轨道功能不得抢owner | 当前版轨道功能需真实源码与命中证据 |
| T06 | A移出canvas后松；B仍在内 | 按既有外释放策略收尾，无残锁 | pointerupoutside/capture/global兜底及去重 |
| T07 | B.pointercancel / B.touchcancel | A继续；无正常stop | changedTouches顺序与非owner取消 |
| T08 | A.cancel、capture loss、blur/hidden | owner清空；stop=0；可重新down | 真正系统取消与合成cancel区分 |
| T09 | A.up重复、cancel→up、up→capture loss | finish至多一次；取消后finish=0 | 同一结束从DOM/PIXI双到达 |
| T10 | ID=0；touch列表重排；多 changedTouches | ID不丢；不依赖数组索引 | nativeId与PIXI ID不同的设备 |
| T11 | touch→兼容mouse；mouse+touch并存 | 一条权威来源、无重复提交 | 无touch事件浏览器与legacy环境分别验 |
| T12 | A拖动中host pause / 自身pause / ad | 同步取消；不可更新/提交 | 宿主、广告真实回调与异常结束分别测 |
| T13 | host pause+ad→只结束ad→resume | 未释放其他owner前仍阻断 | 重复/乱序回调、双ad tokens |
| T14 | disable(false)→enable；reset/home/销毁 | 清会话、不提交；监听不累积 | 旧d201已清布尔；新字段必须一起清 |
| T15 | 教程step0/1拖动中取消/弹窗/转场 | 不额外推进；遮罩与输入一致 | update已推进的步骤不误回退 |
| T16 | cancel→C.down→迟到A.move/up | C不受污染 | 不同ID与复用同ID分测，epoch不代替路由证据 |
| T17 | 快慢帧、缩放、横竖屏、后台恢复 | 相同合法输入相同value，无越界 | 坐标映射/触点命中、既有物理基线 |

验证层级：L1 直接 handler/状态机注入验证上述断言，不声称验证分发；L2 在最终真实页面、指定 PIXI 版本用真实浏览器输入核对路由；L3 触屏真机/WebView及真实宿主/ad核对系统取消和生命周期。手机视口不是物理触屏多点证据；Playwright合成事件不是宿主或真机验收。各层保留独立状态，不互相代替。

## 8. 未知清单与后续闭合材料

| 缺口 | 状态 | 影响 / 所需材料 |
|---|---|---|
| 当前版start/move/stop、轨道逻辑及完整绑定 | 未闭合 | 决定是否已有隔离；提供当前只读源码与版本哈希 |
| 当前PIXI版本、InteractionManager配置与身份桥 | 未闭合 | 决定B是否能到handler、ID映射；提供依赖/运行入口和路由日志 |
| d201取消与广告pause/resume完整定义 | 未闭合 | 不能推断整文件不存在slide取消；补读定义和调用链 |
| d201 setEnable(false)是否清_sliding | 已闭合 | 已读类中明确置false；不能外推当前版 |
| _0x41684e/current落点校正完整语义 | 未闭合 | 决定取消位置是否需业务校正，避免误删合法化逻辑 |
| 当前物理步长、计分及暂停叠加语义 | 未闭合 | 回归需真实参数，不复制旧值或通用示例 |
| 当前版浏览器/真机/宿主分发 | 未闭合 | 需要授权验收环境；本轮未读取/运行 |
| 用户对补丁与运行验证的授权 | 未闭合 | 本轮仅分析，不执行建议或推进code/test |

产物：`/workflow/prototype.md`。无美术、源码补丁、自动测试、构建和发布包。结论边界：**布尔锁能阻止第二次开始，不等于隔离第二指的后续事件；实际是否触发取决于该事件到达 handler 及当时门禁。**
