# 原型阶段记录：机器人路径检测与目标接触边界审查

项目ID：128a9f452ad746a59020f5852c1ef6dc。阶段：prototype。attempt=1，resume=false。autonomous=false，无上游确认；本轮没有编造用户确认或推进后续阶段。

## 范围与状态

本轮承接用户明确的**只读审查**授权，检查Carrom AI路径采样、目标合法接触、真实fixture半径、两版重试力度和fallback，不制作新游戏，不修改原JS。

- 已读范围静态审查：完成；两版四个搜索函数各已见16处helper调用，逐处交接。
- 独立合成样本：18项断言PASS，最终辅助脚本真实执行exit_code=0。
- 全文调用完整性、原候选运行、真实进球和性能：NEEDS_CONTEXT/未验证。整体不是游戏或全文件验收PASS。
- 原源码与资源：未编辑；无引擎迁移、无美术生成、无dist/试玩包。

## 参考与实际采用资料

参考路径均相对ref/：
1. mcp-inputs/mac-codex/4d4eab92df392599c54730b6e087a0949d4875f602c010358e18095007e2275d/Carrom_retry_4d4eab92.js
2. mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js

使用read_reference读取相关正文；关键字符定位与摘录在evidence/carrom-static-evidence.md。没有以路径内的哈希冒充本次文件SHA256，也没有执行参考代码。

已读冻结资料：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/canvas-web.md。已读所选game-reverse-engineering/SKILL.md及同包references/execution-protocol.md、references/global-rules.md、references/unknowns-ledger-template.md。未选玩法逆向专项入口读取被拒，未宣称采用其正文；本轮不扩选Skill。

框架标签为Canvas Web，但真实证据为**PIXI + planck**。本轮保留既有实现，仅审查，不伪称原生Canvas 2D或Cocos版本。不因框架元数据擅自迁移游戏。

## 核心循环与规则状态（范围内还原）

现有游戏局部循环：回合准备→合法baseline放置→玩家瞄准/力度释放或AI搜索→动画期间snapshot/turn/round防护→施加冲量→物理与袋口检测→结算/queen处理→同方或另一方回合。完整计分规则不在本轮已证明范围内。

AI搜索：普通子到袋口先检测→最多七个直击baseline候选→best不足尝试四个反弹候选→仍不足时一层普通组合→合并排序/过滤→力度0.165×dist，cap125→失效fallback重试至多两次→无合法起点则交回或走既有queen结算。fallback没有路径保证。

局部状态应区别：普通子移动、striker静态sensor放置、striker关闭sensor出杆、AI候选失效、袋口吸入、queen pending/cover、turn/round变更、host pause/ad pause。不能把候选不可用当成游戏“失败/输了”。

## 物理、碰撞、成功失败与输入窗口

- 物理固定步长已见1/60秒，world.step(1/60,10,10)，pixel/world比例100。ticker累加逐tick；慢帧/暂停恢复与真实步进误差未动态测量。
- 普通子fixture半径16px，striker21.76px；普通间/striker与普通间真实半径和32/37.76px。
- 旧搜索步长30/43.52px，采样阈值27/39.168px，跳过起点并遗漏非整倍数尾段。目标不显式排除；不能全局替换或全段豁免目标。
- 已见入袋条件中心到袋口≤20px，在step前检测；成功路径应无第三子提前接触、按段允许唯一合法终端接触并最终触发现有入袋/结算。合成几何通过只代表边界模型，不代表真实进袋成功。
- 玩家已见strength≥.25才出杆，force=strength×125；完整pointer/时间窗未做浏览器验证。AI动画/500ms回调有turn/round保护；snapshot单轴位移>1px或身份/group变化触发失效重试。
- 离线断言epsilon=1e−7px仅用于数值公式。运行时容差必须按实际planck版本slop、CCD与固定输入补验；不把1px/2px ghost穿透差自动当可接受误差。不得改变袋口20px阈值或计分来让路径样本通过。

## 设计取舍与接触契约

保留原游戏的玩法、资源、状态机和fallback。此次最小建议是**分段契约+影子检测**：
- 普通出袋排除该段移动子，所有第三子仍阻挡。
- 普通组合M→C允许终端撞原T；striker→M只允许终端撞M，原T在该段仍为第三体。
- striker→G不全段排除目标，校核first-contact和有向入射法向。
- 反弹两段检查共同连接点；指定rail可接触，连接点第三子不可豁免。
- 真实ghost37.76/32的调整需要原函数与物理回归，本轮仅给独立保护模型，不直接集成。

详见workflow/carrom-path-review.md的16处调用矩阵、可达样本、成本上界与最小建议。正常组合自选原T通常被区域筛掉，不能仅凭数组含原T宣称必然自撞；abs逆向hDot完整筛选可达性尚未证明。

## 布局与文案

本轮不新增玩家界面。现有局部空间：四袋口(61,362)/(579,362)/(61,886)/(579,886)，AI baseline y=421，x=162…483；table真实资源尺寸未知，不生成臆测效果图。

交接阅读布局：报告顶部为结论/状态；中部为16处调用矩阵、规则与分段几何；下部为18项样本、力度/fallback、成本、未知清单。样本JSON保留原始坐标、采样点、旧判定、连续判定和契约原因，便于后续对照。

默认玩家语言仍为English；本轮中文仅用于审查报告、辅助脚本注释和日志。未制作玩家文字贴图或HTML，不声称验证lang=en。后续若经授权增加开发诊断界面，玩家可见文案应使用英文，例如`Path Check`、`Blocked`、`Target Contact`、`Retry`、`No Valid Position`；这是交接要求，不是已实现UI。

## 验收条件与真实结果

已完成条件：
- 核对两版已见调用的起终点/步长、无身份排除和真实fixture半径。
- 固定袋口/baseline约束下给出普通段、striker段漏检公式可达样本。
- 合法真实切点保护、组合目标/移动体区别、提前目标穿透、反弹连接点第三子、短段/尾段/阈值边界均有独立断言。
- 核对A重试100与B继承cap后force，保留fallback合法起点/null流程；不声称命中率提升。
- 记录理论成本而非未测毫秒，明确完整调用/原运行/性能缺口。

真实执行：最终`node scripts/carrom-geometry-audit.mjs`退出0，18项合成断言PASS。第一次用整倍数L的漏检样本失败，修正辅助样本后重跑，详细见evidence/carrom-validation.md。最终执行后仅补写报告/evidence文档，没有修改研究脚本或原资源。

未执行：npm run build、npm test、npm run check、浏览器/真机测试。当前为只读prototype，没有package.json或可构建原工程；未创建虚假游戏构建/测试以冒充通过。

尚需闭合的升级验收条件：完整文件词法检索/别名与SHA256；执行原候选函数并复现排序选择；原planck固定输入目标接触与真实进袋；rail有效区间/资源尺寸；目标设备调用数、GC、性能及命中率。未经闭合，不推荐全局替换检测函数。

## 产物路径

- /workflow/prototype.md：本阶段记录。
- /workflow/carrom-path-review.md：详细只读审查报告。
- /scripts/carrom-geometry-audit.mjs：独立合成几何与力度断言，可重复运行，非游戏补丁。
- /evidence/carrom-geometry-results.json：18项输入/输出与状态。
- /evidence/carrom-static-evidence.md：参考关键表达式与定位索引。
- /evidence/carrom-validation.md：真实执行、首轮失败与最终通过、限制。

未知清单U01–U08详见审查报告。没有源码包、试玩ZIP、美术manifest或发布产物；这些不属于本轮授权范围。
