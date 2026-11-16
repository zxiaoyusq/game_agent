# Carrom 多触点瞄准与引导中断只读评审

## 结论与边界

本轮为原型阶段只读评审，仅写报告，不修改游戏源码、不构建、不发布。已读取旧归档部分源码与随包 PIXI 输入实现；未取得、未读取最新版 game.js，也未独立计算其 SHA。不能认定最新改动已经兼容真实设备。

用户提供的新版过滤方向合理：在 drag 活跃、owner 非 null 且事件 data 存在时，非 owner 的移动与释放被拒绝；合法释放前清 owner 有助于避免重复提交。但摘录尚不足以闭合真实取消、缺失身份和生命周期安全。优先验证 owner 单独取消且另一触点仍存在的情况，以及 PIXI identifier 与 DOM pointerId 不同的情况。

证据等级：A=本轮实际读取的归档静态事实；B=用户陈述，未独立验证；C=条件推导或待验证风险；D=建议与验收约定。A 不等于运行复现，B 不升级为本轮实测。

## 输入与参考指纹

- 旧 H5 归档：ref/mcp-inputs/mac-codex/736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99/Carrom_current_development.zip；工具返回归档 SHA256：736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99。
- 旧条目 development/js/game.js：SHA256 3140ae1bd16fd91b6c025fc3641f2ff41e9f26e2b7200c94810199ada22a1573；逐字节研究副本 /reference-inputs/carrom-old-game.js。读取了入口及本文引用片段，并非完整解混淆审计。
- 旧条目 development/js/libs/pixi.min.js：SHA256 e6c608465f403d0201603f31b369cfecea242eaff4b905b6fbaa6efc42c8e57e；研究副本 /reference-inputs/carrom-old-pixi.min.js；文件头为 PIXI 4.8.9。该版本及内容不代表最新版依赖。
- 用户称当前 game.js SHA256 为 a991a3e0117fbe04c70a103b443a0f8439a869c6514d62194d1f704b2179c032；仅作为 B 级版本标签。
- 精简证据归档：ref/mcp-inputs/mac-codex/bd0dd6921ea55d90e5aee904144559e59e5106b2691ab3ebf820f05c2c545bfd/精简证据_v2.zip；归档 SHA256 bd0dd6921ea55d90e5aee904144559e59e5106b2691ab3ebf820f05c2c545bfd。实际读取 mcp_first/01-版本与来源.md（09ba9eca507c2daafdc33e2976844bd2f9e8112ca6094051903a4928f092c83d）、03-模式规则与输入.md（f34a2bd2895a37ab4ffedc163eaaacbeb9f8aedcb7105eb04cfdb4df185f1b36）、unknowns.md（d376e362f4fc1f030f9adf9dc0578cdf2c24c2e9601fc338888eb1c016a8dddf）。这些主要为 Android 原生竞品静态研究，不作为当前 H5 规则或输入证明。

已读取本轮冻结 casual-game-production/SKILL.md 1.3.0，以及 general、physics、web-common、native-web 四份资料。采用其证据分层、一次提交和生命周期约束；本任务保留既有 PIXI/Planck 工程，不借技术配置要求重写原生 Web。

## 已证实的旧快照事实（A）

1. game.js:3720–3762：开始处理函数没有事件参数，仅设置全局 drag；移动无触点身份过滤，直接读取 data.global；释放不使用传入事件身份，力度达到 0.25 即出杆。静态路径允许另一触点改变方向或结束拖拽；未在本轮浏览器复现。
2. game.js:3727、2010–2025：旧版引导第二步按下即调用完成分支，设步骤为 2、关闭 tutorial 并保存，发生于有效出杆之前。弱拖也可能已保存完成，这是旧源码可直接推导的时序问题，不代表新版仍存在。
3. game.js:2300–2306：旧暂停入口清 drag、隐藏瞄准；没有新版 owner 变量可核对。3072–3083 统一清理同样清 drag、隐藏瞄准并关闭输入。
4. game.js:4797–4808：计时到期调用统一清理并切换回合。1766 起重开递增 roundId；3548、3632 起回合入口递增 turnId。5662–5673 通用延迟回调检查局活跃和 roundId，未统一检查 turnId。不能据此认定所有回调都安全或都存在缺陷。
5. PIXI 4.8.9 InteractionManager：supportsTouchEvents 来自 ontouchstart 检测，supportsPointerEvents 来自 window.PointerEvent；两者都支持时仍安装 Touch 监听，并在 down/move/up/cancel 路径忽略 pointerType=touch 的原生 PointerEvent，使用 TouchEvent 路径。Touch 归一化以 changedTouches 枚举，pointerId 由 Touch.identifier 提供（含 identifier=0）；InteractionData.identifier 使用归一化身份，mouse 使用内部身份 1。
6. PIXI 取消分发为 pointercancel，并对触控分发 touchcancel；正常释放可分发 pointerupoutside。未解出旧 game.js:1744–1764 所有混淆事件名，因此不声称游戏已绑定取消或 outside 处理。

## 新版摘录与用户测试（B）

用户描述：owner 初值 null；合法开始赋 e.data.identifier，无 data 则 null；移动/释放仅在 drag、owner 非 null、data 存在且标识不同的条件下拒绝；合法释放前清 owner。document pointercancel 比较 DOM pointerId，touchcancel 仅在 touches 不存在或为空时取消。取消清 drag、owner、力度和可见性，并在合法第二步恢复演示；暂停清 drag、owner 并恢复第二步演示。引导按下只停演示，弱拖恢复，test 返回后保存完成。

用户报告的 CDP 样本：旧版第二指结束提前出杆；修后第二指结束仍 pending，主指结束才出杆；合成 owner pointercancel 在另一触点存在时恢复引导。全部为用户测试陈述，无本轮日志、截图、调用计数或设备复测。尤其合成事件把 pointerId 设成 owner，只证明相等标识的处理分支，不能证明真实 DOM 与 PIXI 标识相等。

## 风险分级与最小改进（C / D）

|优先级|条件与可观察风险|证据边界与最小改进|
|---|---|---|
|P1|混合 Touch/Pointer 模式中，owner 来自 Touch.identifier，document pointercancel 用 DOM pointerId；数值可不同，owner 取消可能未清理。数值偶合也不能证明同一触点。|旧库转换已读，新依赖及设备未核验。优先在同一 PIXI 事件域监听 owner 的 pointercancel；若保留 DOM 桥接，记录输入来源并显式映射，不能跨域裸比较。|
|P1|Touch-only 或混合模式：A 拥有瞄准，B 仍按着，仅 A 被取消；touches 非空使摘录中的 touchcancel 跳过，可能悬挂 drag 或引导。|条件性漏洞路径；若另有有效 PIXI 取消监听可闭合。按 changedTouches 中 owner 判断取消，不要求所有触点消失。另测非 owner 取消不得中断 A。|
|P1|无 data 的 move/up 绕过所述身份过滤；move 若保留旧 data.global 解引用会抛错，up 可能使用旧力度提交。无 data 开始令 owner=null，后续过滤失效。|摘录未说明后续防护，不宣称最新必然出错。缺少可归一化身份或有限坐标时拒绝开始/移动/释放；取消由独立生命周期入口处理。e 本身缺失也须安全。|
|P1|owner=data.identifier 为 undefined，或身份 0 被真值判断丢弃，可能形成错误所有权。|检查最新完整代码；null 专用于无 owner，合法 0 必须保留；验证身份类型，不用 identifier || fallback 判断是否存在。|
|P1|拖拽经过超时、换手、重开、离场后，旧 up/演示回调落入新回合，或同一 ID 被复用。|旧版有局/回合防护但不全面。开始记录 roundId、turnId、gestureId；所有提交及异步恢复检查匹配，在回合失效时统一取消并递增手势代次。|
|P2|双指按同一 striker：第二次 down 覆盖 owner；或者非 owner move/up 在校验前已改变引导、力度或 UI。|摘录未覆盖完整 down 顺序。drag 活跃时拒绝新 down，所有副作用前核验 owner，不能转移所有权。旧快照已有 drag 防重入，应保留。|
|P2|DOM 与 PIXI 重复取消、up/outside、暂停回调重入，重复启动演示、重复出杆或保存。|清 owner 本身不等于完整幂等。提交前原子消费 drag/gesture；取消无活跃会话直接返回；恢复演示先移除旧 tween，确保至多一组。|
|P2|test 返回并不一定表示有效出杆成功：可能提前 return、失败、抛错，或返回异步任务。|旧版 game.test 可提前返回；新版调用关系未读。以明确的 accepted 结果作为引导完成条件，出杆被接受后至多提交一次，不以普通函数返回自动等同成功。存储失败不可报告已持久化。|
|P2|暂停时恢复演示的实现可能重新显示力度，或先清零后 tween 再次覆盖；通用 ticker 暂停、失焦不一定走菜单暂停。|核验全部暂停/visibility/宿主入口；区分用户瞄准值与演示值。恢复需同时满足当前局、当前回合、未暂停、引导第二步 pending。暂停中是否播放演示沿用产品约定，但不得推进规则。|
|P2|拖出 canvas/窗口后没有收到有效 release/cancel，或先在非 owner 控件上点击暂停。|验证 pointerupoutside、窗口外释放、blur/pagehide；必要时统一取消，不依赖 pointerleave 一律取消所有输入。不要仅依赖 isPrimary，鼠标和触控可各有 primary。|

推荐最小补丁边界：保留现有函数与玩法，抽出同域身份归一化与会话有效性判断；补 owner changedTouches 取消；统一幂等 cancel；补生命周期代次；将教程保存绑定明确接受的出杆。这里只给建议，未实施。

## 玩法、状态与界面评审模型

复核循环：观察棋盘 → 放置 striker → owner 按下开始瞄准 → owner 移动设置方向/力度 → 有效 owner 释放提交一次 → 物理运动/入袋 → 既有规则结算 → 继续、换手或结束。此为评审模型，不是本轮重新定义 Carrom 规则。

建议状态：Idle、Aiming(owner/source/round/turn/gesture)、ShotCommitted、Simulating、Settling、Paused、Ended；引导另有 PendingDemo、PendingDrag、Completed，避免仅靠可见性判定完成。owner 取消或弱拖回到可输入状态并保持 pending；暂停/超时/重开使旧会话失效，不提交出杆或教程完成。

输入窗口：仅当前玩家可操作且未暂停、未结算、未运动、局仍活跃时开始；move/up 还需同一有效会话。成功是一次被接受的有效出杆及一次正确规则结算；失败是非法/取消输入造成提交、旧回调污染新局或引导误完成。本轮不制定未取得证据的比赛胜负、Queen、分值和犯规规则。

布局保留已有棋盘、striker、放置滑条、瞄准层、引导手势/文字、暂停层和计时 HUD；不改变美术与面向玩家文案，不新增界面语言。重叠区域测试第二指点击滑条、暂停与 striker，确认互不越权；视觉隐藏不等于输入禁用。

物理与数值边界：旧代码使用 planck 别名 box2d，已读到 World 与边界 fixture 创建；ticker 将累计 delta 按单位 tick 调用更新（5572–5576），尚未定位并解出实际 world.step 的 dt、补步上限及碰撞参数。不得将单位 tick 直接称为已经核实的 1/60 秒物理步长。旧力度阈值为 0.25，距离上限由 _0x647bf3 配置，出杆调用参数含 strength×100×1.25；最新是否一致未知。碰撞/入袋/计分维持现有规则，不引入竞品原生字符串中的数值。

验收容差：事件数量严格相等，非 owner 及取消的出杆、完成保存增量必须为 0，有效 owner 释放出杆增量必须为 1；输入状态检查在处理回调结束时成立。弱拖测试采用阈值 T−ε、T、T+ε，T 取最新实值，归一化 ε 建议 0.001；精确边界用规则层受控输入，真实触控另记录坐标误差。非 owner 输入前后力度/角度建议差≤1e−6（无演示并发时）。物理回归使用同初局与输入，在 30/60/120Hz 渲染、长帧条件下按相同模拟时刻比较，建议初始容差为棋盘逻辑坐标位置≤1、速度≤基准最大速度1%，计分/胜负/入袋序列完全一致；这些是待校准验收建议，非已测精度。先记录真实 dt、最大补步、截断策略和随机源再执行。

## 可执行验收清单（本轮均未执行）

准备：核算待测 game.js 与 PIXI 的 SHA；记录浏览器/系统/设备、supportsTouchEvents、supportsPointerEvents、实际原始事件族。通过只读 DevTools 日志/断点记录时间戳、DOM type/pointerType/pointerId、Touch changedTouches/touches identifiers、PIXI identifier/originalEvent、round/turn/gesture、drag/owner、strength/angle、引导 pending/completed、出杆计数和存储写入。局部闭包变量通过对应处理函数断点观察，不假定可从 window 读取。保存原始事件顺序，不能仅靠截图判断出杆次数。

每项在普通局和引导第二步分别运行；A/B 表示两个真实触点，A 先按 striker 并拖至有效力度。

|编号|步骤|严格预期|
|---|---|---|
|T01|A 按下/移动/释放；鼠标左键与触控各跑|正常操作仅提交一次；引导完成仅在出杆接受后；无异常。|
|T02|A 拖拽；B 按相同 striker、移动并先释放；最后 A 释放|owner 不变；B 不改角度/力度、不出杆、不保存完成；A 才提交一次。交换结束顺序重跑。|
|T03|A 拖拽；B 在棋盘外、滑条及其他可交互目标移动/释放|非 owner 不污染 A；若 B 触发暂停，则 A 被取消，恢复后旧 A up 不提交。|
|T04|A+B 按着，仅取消 A，B 保留；再移动/释放 B 与旧 A|A 会话立即失效、无出杆、引导 pending；允许时只恢复一组演示，所有迟到事件无效。|
|T05|A+B 按着，仅取消 B，随后 A 释放|A 继续有效；B 取消不改 A 状态；最终仅 A 出杆一次。|
|T06|取消全部触点；重复 cancel；cancel→up 与 up→cancel 分别重放|取消路径零出杆；已成功 up 不被后续 cancel 重复提交/重启教程。|
|T07|在混合模式记录 A 的真实 Touch.identifier 与 DOM pointerId，再触发实际系统取消|依据实际事件归属清理；不得人为令二者相等后宣布兼容。保留触点仍存在的场景。|
|T08|分别在 Pointer-only、Touch-only、Touch+Pointer、鼠标及 pen 环境运行 T01–T07|记录实际选中的事件路径；每一承诺支持的路径单独通过。模拟配置不替代真机。|
|T09|受控处理器测试：缺 e、缺 data、data={}、缺 identifier、identifier=0、非有限 global 坐标|不抛错、不无身份开始、不使用旧力度提交；合法身份0可正常工作。此为故障注入，不称自然事件复现。|
|T10|弱拖、零移动与 T−ε/T/T+ε 释放|阈值规则一致；弱拖不保存完成并恢复 pending 演示；有效拖提交至多一次。|
|T11|A 拖拽后暂停/恢复、后台/前台、pagehide/blur，再释放旧 A|输入会话失效；无迟到出杆、无引导误完成；新 down 才可开始。|
|T12|倒计时最后 tick，分别先处理 up 再 timeout、先 timeout 再 up|仅一个合法结果；timeout 先发生时旧 up 无效；出杆先被接受时旧 timeout 不切走新状态。|
|T13|拖拽中重开/回大厅/重新开局，复用相同指针 ID，触发旧演示/延迟回调|旧会话不污染新局；新 owner 不被旧取消清除；监听器和演示数量不增长。建议循环20次。|
|T14|拖出 canvas 后释放；窗口外释放；再回到棋盘|不悬挂 drag；outside 路径不遗漏也不双提交。|
|T15|重复调用合法 up、重复绑定监听器场景、暂停与取消同一事件链|同一 gesture 出杆/完成提交各≤1；恢复演示≤1组。|
|T16|出杆入口提前拒绝/抛错/异步拒绝，及存储写入失败|未接受不得完成教程；失败可恢复，不把函数正常返回当接受，不把失败写入称持久化成功。|
|T17|固定初局固定方向力度，30/60/120Hz 与长帧；验证边界碰撞、入袋、结算、重开|核对真实步长与容差；取消和非 owner 路径不产生物理冲量或计分事件。|

真实取消可在目标设备系统手势、应用切后台等场景采样，但不保证每个操作必然产生 cancel；应以记录到的实际事件为准。CDP 多触点可检查浏览器输入链，合成 dispatchEvent 或直接处理器调用仅用于分支和故障注入，不能替代操作系统取消及跨浏览器兼容验收。

## 真实执行结果与交接

本轮完成：读取冻结技能与四份资料；分页/索引定位两份归档；读取相关研究正文、旧版函数片段及 PIXI 输入转换；提取两份逐字节研究源码以供只读定位。未执行归档源码、未独立读取最新版、未运行 CDP/浏览器/真机测试、未生成截图、未安装依赖。没有调用 run_validation；本轮为只读原型评审，不属于代码或测试阶段，npm run build、npm test、npm run check 均未执行，不能报告通过。

唯一交付报告：/workflow/prototype.md。/reference-inputs/carrom-old-game.js 与 /reference-inputs/carrom-old-pixi.min.js 是引用研究副本，不是新游戏源码或发布产物。

后续闭合需匹配所报 SHA 的完整最新版代码、实际加载的 PIXI 指纹与 T01–T17 的对应证据。本轮无需为提交评审暂停索要这些文件；其缺失作为结论限制保留。当前不确认兼容、不推进美术/代码/测试阶段，不修改源码或发布。
