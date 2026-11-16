# Carrom 原生证据与历史 d201 离线对手审查

## 0. 范围与结论

项目记录：02115684f720474c95eed31936ec131c；本轮仅原型阶段的附件静态审查与测试建议。本文不是新游戏原型实现、竞品算法还原、性能验收或阶段确认。没有修改游戏、UI、资源、构建或测试脚本；不推进其他阶段。

**d201 仅是用户指定的历史 H5 对照版本。其文件名中的 current 不具有现行项目身份效力。全文对 H5 的描述均只针对该附件已读路径，不能外推现行项目存在或缺失任何逻辑。**

主要结论：
1. 两附件可读，但证据不对称：ZIP 是原生分析派生文本，JS 是可审查的历史混淆源码；双方均没有本轮运行证据。
2. `MatchShotSolver`/`simulateShot` 可作后续定位线索，所给短反汇编却是类型名比较辅助片段，不能恢复真实搜索或模拟算法。
3. 历史 d201 已含直击、单库反射和有限组合击，以及合法位置过滤、异步票据与提交前局面重验。把“增加库球/组合击/重验”写成补足历史缺失不成立。
4. 可优先研究：全段碰撞几何与实际刚体一致性；有预算的 top-K 试算和规则风险评分；queen/犯规/同 tick 入袋/超时的结算契约；固定步长与暂停、随机性的可复现性。
5. 上述是**独立离线设计候选**，不是已经证明竞品采用的参数或算法，也没有证据证明一定优于历史 d201。

## 1. 附件身份、SHA 与可读性

参考路径均相对工程 `ref/`，不是工作区游戏代码。

| ID | 真实参考路径 | SHA256 与核验等级 |
|---|---|---|
| R-N | `mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip` | `ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1`；ZIP 工具返回 archive_sha256，已核验归档身份 |
| R-H | `mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js` | `d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198`；这是引用目录身份摘要，**未独立重新计算文件字节 SHA**，不能宣称本轮哈希验证通过 |
| R-L | ZIP 派生文本声称来源 `libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so` | 声称 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`；原始 so 不在附件，来源库摘要、构建归属与地址映射未独立核验 |

ZIP 清单：35 个文件，解压总量 2,411,908 字节；17 个 analysis、17 个 disassembly、1 个 report。无原始 APK/so/plist、分析脚本、运行日志、输入回放、轨迹或截图。这个体积只是证据归档展开量，不是任何游戏包体测量。

JS 可读，含 PIXI、planck/box2d、Howler、GameSnacks 和明文 `_carrom*` 补充逻辑；外部规则/存档接口可见调用，但不据此证明依赖完整、离线可启动或库版本。只做定向静态审查，未执行混淆初始化、解码程序或完整依赖装载。字符窗口为定位辅助，**不是字节偏移、行号或精确函数边界**；查找函数名与本文给出的表达式可复核。

工具限制实录：CSV 成员读取被文本类型门禁拒绝，未将其正文作为证据；未选玩法模块 Skill 入口被拒绝，未声称采用其正文。`inspect_assets` 针对 ref JS 返回空；尝试逐字节提取直接 JS 被工具拒绝（该工具要求 ZIP），无文件被成功提取，故 JS SHA 独立复核仍未知。不要把失败/空结果计为验证成功。

## 2. 证据等级与地址口径

- S-N：已读取 ZIP 的派生索引/反汇编；支持其中记录的字面值、指令关系，不能代替对原始库重新反汇编。
- S-H：已读历史 JS 的字面值与控制流；不等于自然游戏路径已运行或结果已观测。
- D：由静态关系提出的解释或风险假设，必须可证伪。
- P：设计/测试建议，不是来源事实。
- R：本轮运行证据。**本轮无 R 级证据。**

原生地址统一记为 ELF link VA，不是文件 offset、runtime VA 或可直接使用的 hook 地址。缺少原始 ELF 的 PT_LOAD 与装载基址，不能换算运行地址。FDE 是 unwind 范围，不自动等于业务函数；ADRP 后有限窗口 ADD 扫描不覆盖所有间接、literal-load 或 relocation 引用；直接 BL 扫描只覆盖其选定目标起点。命中不证明业务可达，扫描空不证明逻辑不存在。

ZIP 报告中的 `../02_静态分析/`、`../00_分析脚本/` 是旧来源描述，不是本附件可访问路径；本文使用实际 `analysis/` 与 `disassembly/` 成员。

## 3. 原生证据账本

以下成员路径均相对 R-N，地址在上述口径下解释。

### N1：求解/模拟命名不等于算法

证据：`analysis/native_字符串交叉引用候选.json`，`disassembly/02_MatchShotSolver_18bc618.txt`，`disassembly/05_MatchShotSolver_18bca50.txt`。

字符串含 constructor(TableLogic, MatchTableState)、startSolving(callback)、simulateShot(ShotAttempt,double) 命名。候选短 FDE：constructor `0x18bc618–0x18bc634`；start `0x18bc818–0x18bc834`、`0x18bc8bc–0x18bc8d8`；simulate `0x18bca50–0x18bca6c`、`0x18bcccc–0x18bcce8`。

已读 constructor 与 simulate 第一片段：加载 `[x1,#8]`，构造 typename 地址，`cmp` 后 `csel x0,x0+8,xzr,eq`，`ret`。这是类型比较/对象获取辅助形态，**不是候选生成、积分、搜索或物理模拟实现**。仅能建立类型关联定位候选，不能断言神经网络、蒙特卡洛、多步规划、搜索深度、耗时、难度或离线机器人已恢复。

### N2：力度配置候选，有槽位无参数语义

证据：`disassembly/01_shotPowerLimits_18b09d4.txt`、`analysis/native_候选函数直接调用.json`、`disassembly/caller_18b31fc.txt`。

长 FDE `0x18b09d4–0x18b15a4`：`0x18b0a64/68` 构造 shotPowerLimits key，`0x18b0a74–80` 调 `0x26c1074` 后读取类型标签并比较 4，随后容器转换候选调 `0x26e630c`、比较 5。`0x18b0f84–0x18b0fa4` 对该 key 派生临时容器中的值调 `0x2706e20`，写双精度槽 `[x19,#0x20]`、`[x19,#0x28]`。x19 来自入口 x8；实际函数签名未证。

可支持“配置查找、容器转换、两个数值输出槽位”的静态候选。不能将其自动命名 min/max，不能给出数值、单位、冲量/速度关系或力度曲线。caller `0x18b31fc–0x18b35e0` 在条件的两个分支分别 `0x18b3374`、`0x18b339c` 直调，不是证明每击必调用两次。其余配置构造不应冒充 AI 评分。

### N3：queenCovered 布尔输出候选，比字符串强，仍不是规则 owner

证据：`disassembly/09_queenCovered_1aa3458.txt`、`disassembly/caller_1aa2eb0.txt`。

`0x1aa3458–0x1aa38b8` 扫描 0x60 步长记录，匹配值并累计 w24、条件置 w23；`0x1aa3544–68` 比较未知模式值 2/4。`0x1aa36f8–0x1aa3744` 以 tag 3、`w23&1` 构造值；`0x1aa3708/0c` 构造 queenCovered key，经 `0x1aa763c`、`0x2706868` 写入样式调用。caller 在 `0x1aa30b0` 直调。

支持“组装 queenCovered 布尔键值候选”，不是只见字符串；但模式枚举、记录字段、queen 捕获/cover 的唯一规则 owner、犯规优先级和触发条件未知。不能将原生 2/4 对应历史 H5 1/2；尾调用未知目标也不证明线上上报成功。

### N4：停球命名没有结算时序证明

证据：`analysis/native_字符串交叉引用候选.json` 中 physicsStopped 候选 `0x1a855b8–0x1a855d4`、`0x1a94c3c–0x1a94c58`。短片段仅提供类型/命名级线索，不证明停球阈值、物理步长、先结算后动画或动画后交接。

### N5：击球记录结构候选，不是字段语义或服务端权威证明

证据：`analysis/native_击球消息线格式候选.json`、`analysis/native_对局消息类型信息候选.json`、`disassembly/proto_wire_candidate_1fa916c.txt`、`disassembly/proto_wire_candidate_1fa9548.txt`、`disassembly/shot_construct_call_1aa3e04.txt`。

RTTI/vtable/relative relocation 与 gameplay_shot_taken/outcome 的关联候选；parser `0x1fa916c`、serializer `0x1fa9548`。字段 tags：1→0x0a/wire2，2→0x11/wire1，3→0x19/wire1，4→0x20/wire0，5→0x2a/wire2，6→0x30/wire0。field2/3 解析 8 字节到对象 +0x28/+0x30，序列化相应 `ldr d0` 后调用 writer。

构造调用片段 `0x1aa3e04` 调 `0x1fa8e80`；保存入口 d0/d1，`0x1aa3e48` 将 d9/d8 写入临时对象 +0x28/+0x30，随后调用其他未知目标。比线格式更支持“两入口浮点寄存器值进入两个槽位”的候选，但**仍不能命名为角度/力度/位置**，上游来源与单位未知。wire1 也可承载 fixed64/sfixed64，不唯一指 double。不能证明消息实际联网发送、服务端模拟或在线权威。离线设计只借鉴 shot record 与 outcome 分离，不导入竞品网络协议。

### N6：接管与配置线索不作机器人证据

接管：`analysis/native_队友代打字符串交叉引用候选.json`、`analysis/native_队友代打relocation候选.json`；playTurnTakeOverAnimation、effect_turn_take_over_title/description、turn_take_over_toast；xref 扫描空而 relocation 有五处（如 `0x291b370`、`0x291b388`、`0x291b610`、`0x2928d00`、`0x29293a0`）。只是接管展示资源关联，不是队友机器人代打。

配置：`analysis/native_配置加载交叉引用候选.json`；GameConfiguration.plist accessor 候选 `0x1e3f710`（12 字节）、decryptAES128 `0x2711cb0`（36 字节）、reload/start `0x1e41898`（628 字节）、downloadClientConfiguration `0x1cbf2fc`（2376 字节）。没有已证调用链，不证明 plist 使用 AES、密钥恢复、线上参数加载或机器人依赖远程配置。

## 4. 历史 d201 证据账本与对比项

所有 H 项仅 R-H；窗口为 read_reference 的字符 offset 范围。混淆属性未全部完成映射，以下优先引用明文函数、控制流与表达式。

| ID/定位 | 已证历史路径（S-H） | 与原生的比较边界 / 可研究候选 |
|---|---|---|
| H1 `_0x50a0ff`、四角生成器 `_0x52106f/_0x25af2a/_0x521eef/_0x30849b`；144000–256000 | ghost 接触点为目标沿入袋方向后退两物体半径之和；解析基线交点加六个等距样本；dot 阈 0.5，保留改善项；较差 dot（<0.7）尝试单库反射；无候选时有限一层中间币组合击 | N1 没有可对照的真实算法。建议保留已有机制，做候选去重、排序敏感性与有预算 top-K rollout；不能称 d201 没有库球/组合击 |
| H2 `_0x50a0ff/_0x223471`；144000–204000；striker 类 `_0x13fb80` 的 0x1cd 方法；470000–494000 | 按 hDot 降序取第一；实际力度 `(dist/100)*60*.2*1.1*1.25`，不是记录的 `candidate.speed=10+(1-hDot)*100`；cap 为 100×1.25。玩家松手 strength≥.25 且同上限；striker 方法将力度和角度组成向量，唤醒后调用混淆刚体 API | N2 只证配置槽位，不可复制力度上下限或宣称公平手感一致。建议同一输入映射、反弹/碰撞损耗敏感性试验，先核清 API 是 force/impulse 及单位 |
| H3 `_0x23a7dc/_0x3ea989/_carromStartPathBlocked`；144000–204000 | 初始位置重叠检查；路径检查有采样及解析投影，非只有点采样；steps=floor(length/diameter)，短段 steps<1 直接 false；默认起始检查只覆盖 min(length,2×strikerRadius)，full fallback 覆盖 length-(strikerRadius+16)，排除 intendedTarget | 原生无碰撞算法证据，不能称原生是精确 CCD。建议分段 capsule/swept-circle 全覆盖与误差测试，明确目标排除和合法预期碰撞 |
| H4 `_0x3d12d7/_carromFindOpenBaseline`；144000–204000 | fallback 随机目标、基线步 2 搜索、阻挡区间 gap；最多七个采样改善，可能仍保留受挡射击；fullFallbackPath 与偏差保护 | 不能说 fallback 必命中、不受挡或不犯规。建议安全动作与受挡降级契约，不保证所有局面有无阻挡 shot |
| H5 `_0xd6b627/_carromCaptureAiBoard/_carromAiBoardChanged`；144000–204000 | 捕获局面、生成、过滤、提交；有限坐标、group/对象身份、位移>1 检查；round/turn 票据、每回合一次提交、无效候选至多两次 fallback 重试 | 已有重验，不建议删除或重复造轮子。快照未见涵盖所有速度、规则 phase 与 RNG；建议扩充规则版本/seed 与取消条件。return 后旧直接 shot、game.test 的提前 return 后段不得当活路径 |
| H6 `_0x18e0e1`、随机偏角；144000–204000 | arena 数组 [.8,.7,.6,.35,.2]，随机角差 ±(.05+random×.05)，伴随假装移动 | 这些是历史字面值，非原生难度参数。建议 RNG 注入/seed 记录，多 seed 分布与消融，不能单 seed 推出胜率/真人感 |
| H7 `_0x49d791/_0x4bf21a`；204000–268000 | 同步显示、入袋中心距离≤20；固定 group 顺序 striker→queen→player→opponent；扫描后 flush 超时，再 `world.step(1/60,10,10)`、clearForces；ticker累加输入 delta，`while(accumulator>1)` 减1逐步执行，遇 matchBlocked 退出 | N4 不证明竞品时序。建议固定 tick 事件账本与长帧/边界测试；不能将 PIXI delta 未核准时解释成毫秒。该循环本身未见步数上限，不等于已测长帧卡顿 |
| H8 `_0x56abf7/_0xbdafb3`；84000–144000；刚体类；450000–494000 | trimVelocity/isAwake 分组停球；L1线速度 `abs(vx)+abs(vy)<.2` 触发睡眠的候选路径；round/turn/settledTurn 防重复结算、动着50ms轮询；动画 finish 后显式提交再胜负，处罚/返queen待完成才交接 | 0.2 是历史物理坐标速度判定字面值，不是原生阈值，也不能换算显示速度而略去 scale；建议低速、高角速度、动画暂停与物理停止分别验证 |
| H9 queen、Freestyle、CarromDiscRules 调用；24000–144000 | mode0 无queen；mode1 cover/罚杆/queenClearedThisShot返queen；mode2积分 [50,20,10] 与 pending queen；ordinary任何组入袋都会清 `_0x4268e2`；pending 未完成前不胜负，双达标按当回合actor | N3 仅组装布尔候选，不能证明规则一致或差异已经发生。外部 target/layout/hasWon/turnTicks/freestyleQueen 在已读调用处未见定义；完整规则未知。Freestyle 明文注明 provisional/竞品边缘需运行证据 |

补充物理证据：两个刚体类的明文 angularDamping/linearDamping：普通币 0.2/1.8，striker 5/2.8，均设置 `bullet:true`、allowSleep。普通币 Circle 使用 `16/_0x541423`，striker Circle 使用 `(34×.8×.8)/_0x541423`。这些仅历史构造值；不要拿显示 sprite 缩放当碰撞半径，也不要自动视为竞品物理。fixture 的混淆系数未全解码，不能断言完整 restitution/friction；bullet 标志也不证明自定义口袋扫描没有穿越遗漏。接触回调中某个 fixtureB 为 puck 的分支仍对 B body 设置 damping，是 A/B 顺序不对称的**风险假设**，不是已运行确认的 bug。

## 5. 改进候选及优先级（P，不实施）

| 优先级 | 候选 | 依据/作用 | 不做的取舍 |
|---|---|---|---|
| P0 | 统一局面、shot、event、outcome 的离线记录契约 | H5/H7/H9 与 N5：稳定提交边界、规则phase、tick、取消、一次结算可复查 | 不复制 wire 协议、网络栈、原库或原生地址 |
| P0 | 全段几何和物理形状一致性测试 | H3 与刚体构造：短段、tail、切线、库球两段、组合目标排除 | 不先认定历史出错，不贸然换整个物理引擎 |
| P0 | queen/犯规/超时事件归约契约 | H7/H9：固定组扫描顺序和跨动画提交带来可测边界 | 不从 queenCovered 字段推导官方全规则 |
| P1 | 两阶段决策：几何候选→有限试算→规则风险排序 | H1/H2 可保留已有低成本候选；N1 只提供命名启发 | 不扩成模型、无限搜索、在线推理；不宣称恢复竞品 solver |
| P1 | 力度响应校准与 RNG 隔离 | H2/H6：距离公式、未使用 candidate.speed、随机偏差 | 不照搬虚构竞品参数，不以一个 seed 或一局胜负验收 |
| P1 | 固定步长、暂停与低速停球的确定性 | H7/H8：1/60 及 >1 累积边界、动画/计时混合 | 不用固定步长自动承诺跨浏览器逐 bit 一致 |

候选设计核心循环：稳定可击局面→建立只读规则/物理快照→几何候选去重→合法性过滤→有预算试算/规则风险评估→提交前重验→一次击球→逐 tick 收集入袋/犯规→停球与返还处理→一次 outcome→续杆/交接/终局。输入只在该 actor 的可击窗口允许；暂停、动画处罚、未稳定、旧回合或已提交票据不能再次提交。无合法候选应取消或按明确降级规则处理，不写“任意局面都必定找到安全射击”。这仅是测试与设计契约，未作为当前工程状态。

规则状态建议记录：actor/turn/round、普通币所有权、score、queenPhase（onBoard/pending/covered/returning）、queenOwner、foul、timeoutPending、shotSubmitted、settledTurn。具体 queen 规则必须先有独立期望表；默认不得以猜测的官方规则填 oracle。

不新增/改动界面布局。测试观测走独立日志/fixture，不插入游戏 HUD。若未来用户另行授权实现，游戏默认语言 English、页面 lang=en，沿用既有布局；本轮中文仅为报告，不生成界面文案或文字素材。

## 6. 可复现/可证伪测试规格（全部未执行）

### 6.1 公共夹具与误差契约

每次试验保存：附件/可运行构建实际字节摘要、依赖与物理版本、规则版本、坐标系/scale、碰撞形状与参数、每枚物体稳定ID/group/pos/vel/angularVelocity/awake/sensor、actor/round/turn/score/queenPhase、RNG算法与seed、合法基线、shot起点/方向/输入力度、tick输入序列、接触/入袋事件、outcome和提交次数。不能只存截图或候选 hDot。

固定物理步长对照用历史可见 `dt=1/60`，velocity/position iterations=10/10；候选实现试算与实际执行必须共享相同参数与停球条件，不用“纯几何命中”替代实际入袋。相同环境相同初态先验证可复现，再跨环境比较；混沌多碰撞不承诺最终位置逐 bit 一致。

误差分层：
- 离散 oracle（提交/结算次数、actor、score、foul、queen phase）必须完全相等，容差为0；规则未知场景标未知而非宽容放行。
- 几何 oracle 用线段最近点/圆扫掠独立解析结果；非切线样例要求分类完全一致；切线用 R±ε 成对测试，并记录ε与坐标单位，不将未指定ε冒称竞品容差。
- 轨迹误差输出 max/RMS位置误差、首碰tick误差、入袋tick误差；可用一个固定tick作为待评估的事件时间误差窗口，但这不是已确认验收阈值。位置、时间预算在实际校准前为未定，不能报告验收通过。
- 计时暂停要求无提交/无结算；计时器允许的调度抖动需单独测量，不能混入物理误差。

### 6.2 测试矩阵

| 测试 | 夹具与步骤 | 可证伪命题 / 期望与输出 |
|---|---|---|
| T1 候选覆盖/排名 | 固定seed与局面，分别仅有直击、仅单库、仅有限组合击可用；收集所有候选type/hDot/dist/实际力度；冻结同一shot执行；分别去掉库球/组合击/rollout做消融 | 反证“历史无库球/组合击”应直接出现对应候选路径；试算改进只有在多局面、多seed的实际成功/犯规统计及预算均达标才支持，不按hDot自证 |
| T2 力度映射 | 同一基线和方向，扫描历史合法输入范围并记录实际刚体调用、质量、速度与距离；加入一库、两币碰撞场景；对candidate.speed与真正提交力度分别取值 | 可反证“记录speed就是执行力度”；检查玩家/AI同输入同响应；撞击/反弹后是否不足、过强仅由轨迹决定，原生曲线仍未知 |
| T3 全段遮挡 | 设置起点(0,0)、终点(L,0)，障碍中心(t,d)，碰撞半径和R按实际形状取；L<D、L=D、L=mD+δ，t分别位于起点、采样间、末尾tail；d取R−ε/R/R+ε；交换己方/对方/queen/目标身份；再测库球两段和组合中间币 | 解析最近点距离<R且投影在段内就是穿过；目标排除只排预期接触对象。输出历史各检查函数与解析oracle差异，区分起始保护范围与全段宣称，不预先判所有false都是bug |
| T4 fallback/失效候选 | 基线全堵/只留窄gap/全部目标不可见；生成后目标移位（含1边界两侧）、移除或换group；随后暂停/换turn/重开；延迟与重复触发callback | 无NaN、越界、初始重叠；已失效票据提交数0、同turn成功提交最多1；重试有界。受挡fallback结果应明确记录，而非声称安全必命中 |
| T5 固定步长与慢帧 | 从同一快照给ticker delta序列 [1,1,…]、[.5,.5,…]、[2,2,…] 和突发大delta；单测累积值恰好1、略大于1；逐步记录物理步数、accumulator、事件/停球tick；比较相同实际执行步数结果 | 证伪“固定step等于所有帧序列相同”或“恰好1立即推进”；不把未知PIXI delta单位当秒。检查是否无限追帧/延迟，不捏造性能结果 |
| T6 低速/刚体对称性 | 接触对交换创建顺序/fixtureA/B，重复puck-puck与puck-striker；另置L1速度阈值.2两侧、对角速度、高角速度；记录damping、awake与outcome触发 | 只有一致物理初态下A/B交换导致非预期差异才能支持不对称缺陷；低线速度睡眠是否改变预期结果需独立oracle，不能只看阈值名称 |
| T7 queen与犯规 | queen单入；同杆己方币、对方币；下杆cover成/败；queen+striker；最后币+queen；最后币+striker；queen+双方币。每项跑两actor、各适用mode、不同score/剩币/pending初态 | 保存每tick事件及score/phase/owner/foul/续杆/返还/终局；先标历史策略实测，再对独立期望表。没有原生运行oracle时“与竞品一致”保持BLOCKED |
| T8 同tick事件/超时 | 用直接规则事件夹具比较事件排列；用物理夹具让queen/双方币/striker在同一tick跨入袋，另造不同tick先后；超时分别在扫描前、扫描后、停球前及结算动画完成边界触发 | 反证“固定group扫描代表真实落袋时间”；同一事件集合顺序是否应影响结果由预先定义规则决定；要求一次shot一次outcome、返还完成前不提前胜负/交接 |
| T9 暂停、广告token与重开 | 在瞄准、AI延迟、运动、50ms轮询、罚杆/返queen动画处暂停；多token交错释放；旧场景callback随后到达；恢复与重开 | 暂停无物理推进或动作提交；剩余计时语义一致；旧owner/ticket无效；不得用模拟广告回调证明真实宿主接入或离线性 |
| T10 随机性与性能 | 多固定seed、多候选密集局面；统计决策、重试、模拟步、胜率/犯规率与随机调用次数；与历史同一环境相同语料比较 | seed复现并不证明难度层单调；需分布/样本量与区间；记录p50/p95/max、峰内存与压缩增量，超预算能取消降级。不臆造topK、耗时或收益 |

T3 的原点是独立几何单元夹具，不是直接宣称游戏基线可在(0,0)；完整游戏回放需映射到实际合法板面坐标。T7/T8 的事件注入验证规则归约，物理场景验证事件生成；两者不能互相冒充。

原生比较后续复核路径仅作建议：对原始库按实际摘要/ABI配对→通过PT_LOAD/基址确定地址口径→沿真实调用关系找到solver/规则owner→同初态shot轨迹与outcome采样→逐项对比。**现有附件无原库和运行环境证据，本轮该链路BLOCKED；不向用户索取材料。** 在本附件条件下能复核的是派生静态关系，不是完整重做反汇编。

## 7. 离线、包体与性能约束

所有P项优先复用已有候选、物理与规则逻辑；快照只含少量标量/数组，不克隆显示树或音频对象；固定候选上限、top-K、模拟步与总时间预算；共享不可变板面数据、复用临时对象；round/turn改变、暂停或超预算立即取消或按既定fallback降级。不引入模型、CDN、在线推理、竞品原库或原始证据归档。

尚无目标设备或基线运行证据，因此不给虚构决策毫秒、内存、候选数或体积收益。未来测量分别记录：展开dist体积（工作流硬门槛<10MB）、压缩试玩包字节、加载请求与冷启动、决策p50/p95/max、峰内存、候选/模拟步/重试、真实目标设备环境。证据归档大小不能替代游戏体积，桌面浏览器也不能替代低端真机验收。本轮没有构建或dist。

## 8. 不成立推断与未知清单

| 项 | 不允许的结论 | 本轮状态 |
|---|---|---|
| 现行项目 | 用d201或空目录认定当前代码有/没有某逻辑 | UNKNOWN；用户明确不授权现行项目判断 |
| 原始库身份/映射 | 原so摘要已实测、link VA就是runtime/文件offset | UNKNOWN；只有派生元数据 |
| 求解器 | 已恢复simulateShot、搜索深度/神经网络/MCTS/离线bot | UNKNOWN；短类型比较片段不支持 |
| 力度 | shotPowerLimits两值已知min/max/单位/曲线 | UNKNOWN |
| 碰撞 | 原生引擎/摩擦/恢复/CCD/步长与H5相同 | UNKNOWN；历史bullet也不代表口袋扫描连续 |
| queen | queenCovered写值证明完整cover/foul/终局规则 | UNKNOWN；原生owner与历史外部规则定义未证 |
| 模式 | 原生枚举2/4直接映射H5模式 | UNKNOWN，禁止按数值凑配 |
| shot消息 | field2/3是角度力度、已实际联网、服务端权威 | UNKNOWN；仅结构与槽位关联 |
| 接管 | toast/relocation证明队友机器人代打 | UNKNOWN |
| 配置 | plist用AES、密钥已恢复、下载配置已装载 | UNKNOWN；缺调用链和原配置 |
| 历史缺失 | d201无库球/组合击/重验/停球提交 | 不成立；已读历史路径含对应逻辑 |
| 已发生缺陷 | tail/fixture顺序/同tick扫描静态风险就是实际失误 | 未成立；仅D级假设，待T3/T6/T8 |
| 离线与表现 | JS依赖名称/模拟SDK证明真实离线可玩或真人感 | UNKNOWN；无完整运行与宿主证据 |
| 性能收益 | 新候选必然更准、更快、更小 | UNKNOWN；未做候选实现与对照测量 |
| JS哈希 | 目录摘要等于本轮独立字节复算成功 | UNKNOWN；身份摘要可记录但实测未完成 |

## 9. 关键成员摘要与方法来源

下表SHA为 ZIP 工具返回的当前成员字节摘要，可用于核验所引用派生文本，不升级原库证据等级。

| 成员 | SHA256 |
|---|---|
| `report/竞品_ARM64代码定位.md` | `c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f` |
| `analysis/native_elf_符号.json`（仅读元数据头部） | `d4d1f06dc49bb5878b8119779ef6a937d8e0e30a795a1b4955712c431f8011cc` |
| `analysis/native_字符串交叉引用候选.json` | `7ee49831a8e4a862af476446d66878c54f68f2b54ea2e57a7d9056921a5f717a` |
| `disassembly/02_MatchShotSolver_18bc618.txt` | `2070412740ad04b7df074f719a60cb9cc4044b75f08f6eefe20cbc8b54a410b8` |
| `disassembly/05_MatchShotSolver_18bca50.txt` | `05f79d1bf970668db9c22a4e63b238c052dfc39186ac639f221906702da241a9` |
| `disassembly/01_shotPowerLimits_18b09d4.txt` | `e001c256d16c9ecfb846e9dbe318d2a8ee8b9fc1531a3b8592856944e51065aa` |
| `disassembly/caller_18b31fc.txt` | `b64aa9d2d4af3a097eb82fd21db048139b9c09be6568f4ec9ccd789fd6b67d12` |
| `disassembly/09_queenCovered_1aa3458.txt` | `0d5ea8f1c3ec5bbded18719168b4f163c258aac3a4f748e8c37a33a0aae1bf09` |
| `disassembly/caller_1aa2eb0.txt` | `af2612149a270ceb4d9121d011dfe2efee0ab0e697f0215c5b5f958dece9cf0a` |
| `analysis/native_击球消息线格式候选.json` | `f20ada502ec9e76a5b8bbb3e66a895ef1d27ae5ac948bb1f603817333b26a9e6` |
| `analysis/native_对局消息类型信息候选.json` | `42cad3218cae2342d1bc3bcdfeebc1ffba7ef13e8abbb5712afbd222efee41df` |
| `disassembly/proto_wire_candidate_1fa916c.txt` | `585f5cf96165cb0a6d2e3b003dacd6b2a06d4478c36336e76647ed18bd844256` |
| `disassembly/proto_wire_candidate_1fa9548.txt` | `92145aa04024bcaf50b576dedd808787ef1a6dabb55b4cba6cea5ec6e420745d` |
| `disassembly/shot_construct_call_1aa3e04.txt` | `efff8351985740a4e1d5ef0ba3b4b556934de6591e874395472a0d05b22cb87a` |
| `analysis/native_候选函数直接调用.json` | `2b224867627e101d78711410798bdb44ce79ac0bc2258d532c794393a3607bfc` |
| `analysis/native_队友代打字符串交叉引用候选.json` | `8ac5924b3ee48db8ca7f93d68b42d39f2b0e32798d90d17a14cc6e78301d0d12` |
| `analysis/native_队友代打relocation候选.json` | `ce6d18a9d86fe4a9fa7844ad7fd3ad10f3730f793cc331ef3ebe33a5edcc6dbd` |
| `analysis/native_配置加载交叉引用候选.json` | `4d984488b0186a91f13cb28b52235513c0794e09b20ca7b2cae583ecf80ac8bd` |

已读取方法资料：选定 `game-reverse-engineering/SKILL.md`（10.5.0）、同包 execution-protocol/global-rules/native-code-evidence/unknowns-ledger-template；冻结 `genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/native-web.md`。仅采用证据分层、真实执行边界、固定步长与误差/离线约束等方法，不采用其他案例参数，也没有安装其工具。未选玩法模块入口被门禁拒绝，没有使用其正文。

## 10. 本轮真实验证与产物

产物：`/workflow/prototype.md`（本报告，含证据账本、原型候选契约、测试矩阵和未知清单）。没有游戏产物、试玩入口、源码包、美术资源、发布ZIP或运行evidence。

真实完成：ZIP真实清单/归档与关键成员SHA读取；原生派生静态关系人工核读；历史JS关键函数与ticker/刚体路径定向阅读；证据强度与不可成立推断交叉审查。

**未执行**：历史或原生游戏启动、浏览器/真机测试、原库反汇编重算、轨迹回放、性能/离线测量、T1–T10、npm run build、npm test、npm run check。本轮是用户要求的只报告原型审查，不是代码/测试阶段，因此未创建空工程或伪测试来冒充验证。原生运行行为比较BLOCKED；候选收益、完整规则一致性和现行项目状态UNKNOWN。

审核完成仅指本附件范围的静态分析报告已交付；不表示机器人恢复成功、测试PASS或用户确认阶段。
