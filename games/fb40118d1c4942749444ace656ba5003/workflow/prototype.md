# 原型阶段记录：Carrom 当前机器人力度与候选一致性排查

项目ID：fb40118d1c4942749444ace656ba5003。当前阶段prototype；attempt=1；autonomous=false。范围为只读源码审计，不修改游戏，不推进美术、代码、测试阶段。

## 参考与方法

实际读取：
- `ref/mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js`，按字符分页连续读取至末尾。
- `ref/mcp-inputs/mac-codex/6bb4656c18abf6f8a51e1fe87e8d64d58af6cb9432b46c2934a43c33b34d4ae5/carrom_comparator_original_bytes.json`。
- 冻结资料 `genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。
- 冻结技能 `game-reverse-engineering/SKILL.md`，以及execution-protocol/global-rules/unknowns-ledger-template配套正文。未选专项入口被工具拒绝，不声称使用其正文。

参考JS实际使用PIXI+planck；Canvas 2D索引不代表原工程实现。本轮保留已有方案，不借审计迁移框架。竞品局部指令不证明字段单位、调用优先级或完整AI策略，不复制其算法。

## 核心循环与规则状态

保持原版：当前玩家或AI准备→baseline选位置/瞄准蓄力→单次施力→物理运动及进洞扫描→等待静止→犯规/queen/计分结算→续杆、交接或结束。

模式0 Disc Pool，模式1 Carrom，模式2 Freestyle。AI targets在Freestyle为双方子+queen；其他模式主要为对手子，对手剩1且queen在板时先queen。无合法候选尝试fallback；没有fallback则交接，queen pending走本回合结算。胜负与queen的完整外部模块尚缺，不重写规则。

物理固定step=1/60秒，10/10迭代并clearForces；striker实际半径21.76px，普通子16px，启发式普通子参数15px。F是applyForceToCenter的输入而非速度。玩家释放strength≥.25才提交，最大125；AI请求F=.165×dist，表现入口截到125后显示strength=F/125，提交同一F。已推导箭头与最终施力角度一致。

输入窗口：当前actor、当前turn、同pointer手势；暂停取消瞄准，旧释放不应提交；AI准备延迟500ms、最多4段20–30tick摇摆、10–20tick蓄力、500ms后提交，2300ms后尝试静止结算；暂停不推进游戏Tween。静止仍awake则每50ms重试。table0 Carrom/Freestyle没有倒计时兜底，但现有候选错误出口不依赖它。

## 界面与语言

不新增界面或资源。维持原棋盘、四角洞、上下HUD、baseline、底部位置slider、瞄准箭头、暂停/教程/结算界面。玩家文案默认英文；如后续需要新增，可用“Your turn”“Opponent's turn”“Paused”“Resume”“Play again”。本轮无HTML构建，未验证lang=en或中文浏览器默认语言，不修改原素材。

## 发现与取舍

1. **条件性候选/力度失配**：候选在提交前失效后，fallback沿用旧F，初次fallback却用100。原函数摘录合成断言证实，未证明自然移动触发或进球后果。最小建议：重试与初次fallback统一100，仍经统一截力/显示；未实施。
2. **路径检查几何假阴性**：S=(320,421)、width=43.52、dir=0、dist=200、阻挡子=(385.28,456)时，原采样函数false，但两圆扫掠相交。未证明完整候选生成器自然入选。最小建议：有限线段距离检查并正确排除目标，O(棋子数)，不加素材；未实施。
3. hDot排序、dist力度与125截断没有重排序是确切策略事实，不足以证明卡死或自然射不进；speed非生产力字段。不因竞品名称改变优先级。
4. 重复提交有shotTurn guard；重试耗尽/queen pending有恢复；暂停冻结Tween；重开round/turn防旧回调。没有证明自然停局、不发杆或显示与施力大小矛盾。

## 验收条件与真实结果

原型审计条件：每项发现区分静态推导/摘录合成/自然运行；附函数、行级锚点、输入、断言、模式、恢复、最小建议。详见 `workflow/carrom-ai-audit.md`。

实际执行：
- `node scripts/audit-carrom.cjs` exit=1，ENOENT；参考文件未挂载到执行工作区。未对原文件独立哈希；行号从已读分页会话换行重建，并保留真实会话行号和函数锚点。
- `node scripts/check-carrom-audit.cjs` exit=0，15项断言通过，13项涉及摘录函数隔离执行、2项数学推导。结果 `evidence/audit-checks.json`。摘录SHA256 `f3554b6c5000f8bcaed35359833bf79930a4ecca0a3b8ef2d0d866715aaf264d`。
- 断言覆盖三个模式的旧力度重试、两次重试恢复、有效提交幂等，两个queen pending出口、快照1/1.001px边界、路径漏检、排序与截力、角度一致性。

数学可接受误差：力度1e−9、角向量1e−12，仅用于本轮算术断言；快照实际容忍为每轴≤1px。真实物理/视觉误差须后续同构建测量，不能用算术误差宣称浏览器验收。

自然复测准入（未执行）：完整离线工程和依赖/规则/资源到位，固定seed由真实生成器选杆，不注入候选，记录candidate/requested/clamped/实际施力；覆盖固定步、慢帧、暂停/恢复、广告token交叠、重开、重复回调、queen pending；每turn至多一杆且settle/advance一次。取得自然案例后再评估是否实施最小补丁。

## 产物与限制

- 详细报告：`workflow/carrom-ai-audit.md`。
- 可复现摘录与结果：`evidence/carrom-fragments.js`、`evidence/audit-checks.json`。
- 锚点口径/失败记录：`evidence/source-line-map.json`、`evidence/reference-access-failure.json`。
- 只读诊断：`scripts/audit-carrom.cjs`（原文件访问BLOCKED）、`scripts/check-carrom-audit.cjs`（隔离断言已通过）。

没有完整HTML工程、资源、PIXI/planck运行依赖或CarromDiscRules/LocalSave正文，未执行完整游戏、浏览器、真机、SDK或自然对局。Tweener正文已读取，不代表其完整链已执行。无联网采集或依赖安装。npm build/test/check、dist、试玩与源码ZIP不属于本轮只读prototype产出，未执行/未创建；不制造假构建。审计文件不进入游戏包，原游戏资源与计算量均未改变。

本阶段仅交付审计结论和复测契约；没有用户对修复或下游阶段的确认，不自行推进。
