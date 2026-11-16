# Carrom 机器人候选、力度与中断生命周期只读审计

阶段：prototype；attempt=1；非自主推进。游戏源码及资源未修改。本报告不构成上线、引擎迁移或下游阶段确认。

## 1. 结论与证据等级

**未证明自然对局中必然停局、不发杆，或瞄准显示与最终施力大小矛盾。** 不把“候选不理想”当成“卡死”。

确认的条件性问题：
1. **候选失效重试换候选但保留旧力度**：与初次fallback固定100的策略不一致。摘录原函数在合成输入下实际验证；自然触发频率和进球影响未验证。
2. **路径采样可漏掉圆形扫掠碰撞**：原路径函数能对合法坐标的几何反例返回无遮挡；尚未证明完整候选生成器会自然产生并选中该杆。

确认的策略事实，**不认定为功能缺陷**：只按hDot排序；请求力度0.165×dist；125上限施加后不重排；speed字段不进入生产发射链。无法凭此证明自然射不进或停局。

反证：正常主链先截力再显示，提交使用同一力度；角误差方向一致；有效AI提交幂等；无候选/无空位/重试耗尽有交接或queen结算；暂停阻止游戏Tween与物理步进，并非消耗掉延迟。

真实诊断：`node scripts/check-carrom-audit.cjs` exit=0，共15项断言通过，其中13项涉及摘录函数执行，2项为明确标注的数学推导。**PASS表示断言证实当前行为，不表示缺陷已修复或游戏验收通过。**

## 2. 输入、方法与行号口径

当前JS：`ref/mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js`。

竞品摘录：`ref/mcp-inputs/mac-codex/6bb4656c18abf6f8a51e1fe87e8d64d58af6cb9432b46c2934a43c33b34d4ae5/carrom_comparator_original_bytes.json`。

JS通过read_reference按字符offset 0、24000……552000连续读到文件结束。选定四份品类/技术资料及冻结技能入口已实际读取。原源码指纹未能独立计算；路径中的哈希只视为提交标识。实际源码为PIXI+planck，不是原生Canvas 2D工程；本轮只读，不迁移。

下面“JS重建L”由参考工具分页在会话文件中的换行数重建，不是执行器直接扫描原文件的结果。并列的“H L”是会话证据文件 `/conversation_history/fbb8d45128cf4ea1bb45dc41a58476cf.md` 的真实行号。映射及页边界见 `evidence/source-line-map.json`；发生排版差异时以函数、原文表达式、参考字符页和H行号定位，**不得把字符offset当行号**。末端物理类不在旧会话记录中，用参考页+函数体相对行锚点。

原文件诊断脚本exit=1、ENOENT：工具可读参考并未挂载到执行工作区。未绕过工程边界。替代诊断逐行摘录4个函数到 `evidence/carrom-fragments.js`，在Node vm中仅执行该摘录，外围状态、发射器和调度均为stub。片段SHA256：`f3554b6c5000f8bcaed35359833bf79930a4ecca0a3b8ef2d0d866715aaf264d`。没有执行完整游戏、PIXI、planck或真实Tween。

## 3. 候选生成与力度完整主链

| 环节 | 函数与锚点 | 当前行为 |
|---|---|---|
| AI开始 | `_0x50a0ff` JS重建L3962–4058 / H4838–4934 | turn++；actor=false；sensor=true；默认装备外观；500ms后生成候选，检查active/turn |
| 四洞生成 | `_0x52106f` L4458起 / H5335；`_0x25af2a` L4671起 / H5548；`_0x521eef` L4881起 / H5759；`_0x30849b` L5077起 / H5955 | 每目标hDot门槛0.5；精确共线点及6个baseline点；差候选尝试4点反弹、单层组合 |
| 筛选/排序/请求力 | JS重建L4034–4055 / H4910–4931 | pos/dir/hDot/dist有限、dist≥0、baseline与空位有效；仅hDot降序；dist×0.165；空集合fallback100 |
| 表现入口 | `_0xd6b627` L4248起 / H5124 | 有限性校验、抓棋盘快照、表现链；return后旧直接shoot代码不可达 |
| 摇摆 | `_0x4662ac` L4271–4307 / H5148–5184 | 最多4段移动，每段20–30ticks，round/turn防旧回调 |
| 截力/显示 | `_0x223471` L4308–4344 / H5185–5221；关键L4312、4319、4322–4331 | `min(F,100×1.25)`；strength=F/125；按桌概率产生±0.05–0.1rad误差 |
| 提交/重试 | `_0x4b3cc6` L4345–4372 / H5222–5249 | 快照/位置再验；每turn最多2次fallback重试；有效杆记shotTurn、shoot、2300ms后结算 |
| 玩家对照 | `_0x1e39ba` L4177–4199 / H5053–5075 | strength≥0.25才发射，力=strength×100×1.25；同pointer校验 |
| 最终施力 | 参考字符页456000；`_0x13fb80`内`_0x4e67e7.prototype[_0x1c0283(0x1cd)]`函数体相对L1–16 | 关闭sensor，构造力向量，setAwake(true)，调用body[0x311]，字符串表核对为applyForceToCenter；没有末端再次截力 |

目标集合：Freestyle为双方普通子+queen；非Freestyle为对手子，若对手剩1且queen在板则先瞄queen。无fallback目标时还尝试玩家子+queen，仍无则null。模型用绝对点积；组合乘上游绝对点积；没有分数、犯规、实际碰撞后进洞或耗力可达性的完整模拟。

`speed=10+(1-hDot)×100`确有写入，但主链读取的是dist，不读取speed。它不是实际球速、不是竞品power字段的同义词。

AI力请求与装备无直接挂钩；玩家force装备改变达到满力需要的拖距 `75+25×force`，而满力提交仍125。表现外观差异不足以推导“机器人超玩家最大力”。

### 显示与物理量

AI显示角a=π+dir−error；提交角b=π−dir+error；末端力向量方向−b+π=dir−error。瞄准箭头朝向−(cos a,sin a)，与力向量同向。显示strength=clampedF/125，提交同一clampedF。因此没有把正常角误差反向或先显示满力却提交未截力的证据。

F是applyForceToCenter的输入，不是setLinearVelocity的速度。物理质量、1/60步长、阻尼、碰撞会改变实际速度/行程；未用完整planck做验证，不把F=125解读成125px/s，也不承诺某dist一定入洞。

## 4. 确认问题A：重选候选却沿用旧力度

**级别：条件性候选/力度策略不一致；停局结论NEEDS_CONTEXT。**

锚点：`_0x4b3cc6` JS重建L4352–4356 / H5229–5233，特别是 `_0xd6b627(_carromRetryShot, _0x3e3780)`；对照 `_0x50a0ff` L4053–4055 / H4929–4931 的初次fallback100。

输入：mode=0/1/2；active=true；turn=7；shotTurn=-1；旧candidate `{pos:{x:320,y:421},dir:0.8,dist:200}`，已计算并截后的F=33。快照中opponent棋子位置(298,500)，提交时同对象(300,500)，触发每轴移动>1。stub固定fallback `{pos:{x:320,y:421},dir:1,dist:900}`。

已执行断言：只调用一次retry，候选对象为新fallback，但F仍33，不是初次fallback约定的100；旧杆不提交，shotTurn未标记。三个模式均证实。输入包含合成旧候选和指定fallback，**未证明完整生成器自然选中dist=200或现场会在表现期间移动2px**。

影响：新fallback的瞄准与最终提交仍会一起显示/使用33，因此不是“显示33实际100”的矛盾；是候选换了但力度与新策略失配，可能过弱/过强，尚无进球和自然概率证据。

现有恢复：最多2次重试；耗尽或无fallback时普通状态转玩家，queen pending则停止续杆并走该turn结算。对应断言已执行。table0也有此路径，不依赖倒计时。

最小建议（未实施）：该重试分支采用与初次fallback一致的100，再走统一截力/显示；或统一函数原子返回candidate+requestedForce。前者单行级修改、无新增素材或搜索；不应在本次只读阶段擅改。后者需要确定fallback策略，不应凭dist900自动改成148.5。

## 5. 确认问题B：路径采样漏检

**级别：可证明的几何检查假阴性；自然入选/体验后果NEEDS_CONTEXT。**

锚点：`_0x3ea989` JS重建L5274–5289 / H6152–6167；`_0x247dad` L5291–5300 / H6169–6178。按width推进，采样次数floor(dist/width)，检查半径0.9×width，不做精确线段距离。

具体输入：起点S=(320,421)，方向0，长度200，width=2×21.76=43.52，唯一阻挡子B=(385.28,456)。初始距离约74.07>37.76，没有baseline重叠。采样x=363.52、407.04、450.56、494.08；最近两样点与B的距离 `sqrt(21.76²+35²)≈41.21`，大于采样检查半径39.168，原函数返回false。可是B到线段的垂距35，小于真实striker半径21.76+普通子半径16=37.76，圆形扫掠相交。

已执行：原摘录路径函数返回false；几何断言相交，PASS。这是合法坐标下的原辅助函数反例，不是完整生成器、实际施力后轨迹或真实planck接触测试。较低力度也可能根本没行进到阻挡位置。

受影响模式：三个模式共用该辅助函数；直接/反弹/组合路径均可能调用。无法给出现实掉杆频率。

现有恢复：它不阻断shoot；碰撞由planck处理，静止后正常计分/交接。不会仅因该false永久等待；最坏“选错无遮挡杆”的结果需自然复测。

最小建议（未实施）：将每片棋子的点到有限线段距离与相应两圆半径和比较，并明确排除当前目标/组合接触子，不盲目过滤合法接触。O(棋子数)，可少于现有多次采样；无新资源。不直接扩大0.9系数宣称修复全部端点、短段和采样空隙。

## 6. 不升级为缺陷的观察

### C. hDot排序与力上限后不重排

锚点：H4919–4926 / JS重建L4043–4050；H5189 / L4312。合成A(hDot=.99,dist=800)、B(.98,400)，A被选，请求132截为125，B请求66。临界dist=125/.165≈757.575758。数学断言已执行，但未执行原生成器产出A/B，不证明A会失败或B能成功。把“截力后缺少完成性模拟”记录为策略限制，不建议引入竞品式重型搜索。若后续有自然失败反例，可先统一力计算并以现有hDot为主键添加廉价次级键；是否削弱长距离策略须另评估。

### D. 快照容忍每轴1px

锚点：`_carromAiBoardChanged` H5115–5117 / JS重建L4239–4241。同一棋子从(300,500)到(301,501)仍false；x=301.001则true。已执行边界断言。最多√2像素位移不是“1像素欧氏误差”；这是既定容忍口径，不是脱离碰撞边界的安全保证。没有临界进球/漏碰撞自然反例，故不认定停局缺陷；不能仅将>改成≥就宣称修复。

### E. TR生成器左侧baseline限制不是镜像错误的充分证据

H5600–5608 / JS重建L4723–4731：目标向右上洞时，理想striker位于目标左下（baselineX小于targetX）。因此与TL某处相同不等于写错。生成器仍有采样与绝对点积的启发式局限，但本轮无证明TR必须改成右侧限制的几何反例；不做镜像补丁。

### F. 有限但负力度与死代码

表现入口只校验有限数、clamp仅上限，人工调用F<0会产生负strength及反向施力；生产候选dist≥0、fallback100、重试沿用其非负值，未证实自然负力可达。负力注入不列正式体验缺陷。`game.test`早return后的试射和`_0xd6b627`return后旧代码不作为生产发射入口。

## 7. 中断、计分与不发杆审查

| 场景 | 证据与结论 |
|---|---|
| 正常AI输入 | 玩家交互禁用；候选后表现→提交；有效提交先记shotTurn，重复回调只shoot一次（已隔离验证） |
| 没候选/没target/没空位 | `_0x50a0ff`、`_0x3d12d7`、`_carromFindOpenBaseline`都有null出口；普通状态交给玩家，queen pending结算。没有“null一路不处理”的静态证据 |
| host/menu/ad暂停 | `_0x49d791` H6191（JS重建L5313）在Tweener.update前返回；host/ad二次防护；暂停清accumulator与瞄准pointer；ad token去重且全部退出才续计时。未真实按暂停按钮 |
| 恢复 | host resume恢复pointerEvents、计时器和静音状态；match timers保存remaining/version且校验owner；游戏Tween未被暂停期推进 |
| 重开/旧回调 | `_0x5480e3` H2738起（L1867起）round++、清striker/aim Tween与旧棋子；`_0x338c29` H7182–7195（L6301–6314）捕获round；AI回调额外turn校验 |
| 结算等待静止 | `_0xbdafb3` H4368–4379（L3494–3505）：旧turn/重复settle/timeout ticket过滤；awake则50ms再查。trimVelocity在L1范数速度<0.2时sleep，双方子+queen+striker都检查；未证明自然永远awake |
| table0计时例外 | `_0x49d791` H6218–6236（L5340–5358）：table0 Carrom/Freestyle不扣回合时间；Disc Pool非教程扣。失去所有回调时它缺少倒计时兜底，但没有自然丢回调可达证据，不能单独认定卡死 |
| queen超时 | ticket含round/turn，pocket扫描后等待静止再结算；不是超时立刻跳过queen待cover状态 |
| `_0x24bb4a`表达式 | H4120–4136 / L3246–3262：有 `_0x1a373b - 1`未赋值，但turn timer flag已关闭；不据此造致命计时缺陷 |
| 慢帧 | `_0x4bf21a` H7025–7032 / L6144–6151：累加delta，while(accumulator>1)固定tick；未见补步上限。大delta可能长任务，但没有设备输入/耗时证据，不报告自然停局 |

计分/规则边界：先扫描进洞、记录子/犯规，再等静止结算；Disc Pool按归属和剩余子推进，Carrom queen待cover约束续杆与胜负，Freestyle含queen phase及分数目标。计分动画有幂等完成标记与round/turn防旧回调，部分外部规则为window.CarromDiscRules。缺该模块正文，不能声称完整胜负/queen规则已动态验收；本轮只证明机器人异常出口仍进入现有计分/回合接口，不改变规则。

未覆盖的异常：body/fixture API抛异常、外部规则模块抛异常、Tweener transition丢失、ticker被宿主永久停止、非有限物理状态。没有自然日志，不编造这些原因已经发生。

## 8. 竞品证据边界与取舍

JSON声明原ELF源SHA256=`4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`，scope为本地字节与重定位摘录、无独立解码或运行。当前没有原始ELF；下面只在信任所提供指令与符号配对的条件下成立：

- UnfouledStrikerComparator：0x18cb8b4–0x18cb8d8，读取offset0x48 byte并比较。
- HigherScoredPucksComparator：0x18cbbe4–0x18cbbfc，读取offset0x4c uint32，所给cmp/unsigned LS摘录较高返回−1、相等0。
- LeastFouledPucksComparator：0x18cbefc–0x18cbf14，读取offset0x50 uint32，较低返回−1、相等0。
- ShortestShotComparator：0x18ccb5c–0x18ccb74，读取offset0x28 double；LeastPoweredShotComparator：0x18cce74–0x18cce8c，offset0x30 double；所给普通有限值比较较低返回−1、相等0，NaN不能按普通全序说明。

未知：字段构造/写入、单位、调用者、复合优先级、稳定排序契约、搜索范围、物理预测以及名字与方法体的独立匹配。不能从名字恢复“先避免犯规→得分→距离→力度”的完整算法，也不能把它们的double同本项目dist/F等同。本轮拒绝据此更换算法或加算力。

## 9. 验收契约与后续最小复测（未执行、未授权推进）

保持现有规则、物理与界面：
- 固定物理step=1/60秒，velocity/position iterations=10/10，step后clearForces；不要用可变dt代替。测试记录ticker delta、累积步与暂停，特别是`>1`边界。
- 实际fixture半径：striker21.76px、普通子16px；启发式普通子参数15px需与真实碰撞区分。洞心距离≤20时有striker犯规扫描；成功击球不等于入洞或胜局。
- 输入仅当前turn/current actor且同pointer释放；玩家strength<.25不发射，≥.25可提交，最大125；暂停/cancel后必须重新开始手势，不应被旧pointerup发射。AI无玩家手势窗口。
- 初次AI准备500ms，摇摆最多4×20–30ticks，蓄力10–20ticks，提交前再等500ms；按60ticks/s，最长约3.33秒加有限步调度误差。重试可再增加表现时间，不承诺壁钟硬截止；暂停时间不计入。
- 力截断误差≤1e−9（算术），角向量误差≤1e−12（本轮数学断言）；真实位置/视觉误差未定，需同构建实测，不照搬这些算术阈值。
- 候选快照每轴≤1容忍已记录；以后碰撞测试必须覆盖切线两侧±0.01px、短于一步的线段、端点、反弹和组合目标排除。
- 状态流：player/AI准备→aim→单次shoot→moving→settling→continue/other actor/finished；无合法杆走交接或queen结算，不能静默挂在aim。
- 界面布局维持原版：棋盘/四角洞、上下玩家HUD与回合时间、baseline与底部slider、棋盘瞄准箭头、pause/tutorial/result；不新增界面或素材。玩家语言维持英文，候选文案可用“Your turn”“Opponent's turn”“Drag to aim and choose power”“Paused”“Resume”“Play again”。本轮无HTML入口，不能声称lang=en或中文浏览器环境已验证。

完整工程到位后才可做自然复测：固定seed和初始盘面，不注入候选，记录每次生成/排序/截力/重试原因和真正applyForceToCenter；固定步重放暂停、广告token交叠、重开与重复回调；验证每turn至多一杆、最终settle/advance exactly once。保留装饰以外的现有流程，不引入联网服务。

## 10. 未知清单与交付限制

| 项目 | 状态 | 原因/影响 |
|---|---|---|
| 原文件独立SHA与直接行号扫描 | BLOCKED | 参考未挂载；保留重建行号+会话行号+函数锚点 |
| 完整生成器自然候选、重试自然触发 | NEEDS_CONTEXT | 只有源码快照，未恢复完整执行环境；合成函数测试不能证明自然可达 |
| PI​XI/planck物理/Tweener全链浏览器 | BLOCKED | 工作区无HTML、完整依赖与资源；Tweener正文已读取，但未完整执行 |
| CarromDiscRules、LocalSave | NEEDS_CONTEXT | 外部模块正文未提交，不能臆测内部或因工作区无它就说线上缺失 |
| 真机与宿主广告 | BLOCKED | 无ADB/MCP/真机入口；未验收加载、内存、掉帧 |
| 竞品独立指令/算法 | NEEDS_CONTEXT | 没有原始ELF/独立解码/运行 |
| 玩法逆向专项入口 | BLOCKED | 未在本轮选中，读取工具拒绝；没有绕过冻结Skill范围 |
| npm build/test/check、dist、发布ZIP | 不适用本阶段/未执行 | 只读prototype审计不是代码或测试阶段，没有可构建工程；不创建假npm脚本/假试玩 |

产物：本报告、`workflow/prototype.md`、`evidence/carrom-fragments.js`、`evidence/source-line-map.json`、`evidence/audit-checks.json`、`evidence/reference-access-failure.json`、两个只读诊断脚本。无美术资源/游戏修改；新增摘录与脚本只用于审计，不打入游戏或dist。未安装依赖、未联网、未发布，未自动确认art/code/test。
