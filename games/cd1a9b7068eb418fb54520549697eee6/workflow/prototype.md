# Carrom七项体验拆解核查：原型阶段证据报告

## 0. 范围、版本与执行结果

项目：cd1a9b7068eb418fb54520549697eee6。阶段：prototype。恢复轮次：attempt=2。
本报告仅做附件静态核查、原型建议与未来验收设计；不修改玩法源码、配置或资源，不执行附件代码，不推进美术、代码或测试阶段。唯一新增产物为工作流要求的本报告 `/workflow/prototype.md`，不是可玩原型。没有生成图片、截图、试玩包或构建。

### 参考路径

- **R-N（原生分析附件）**：`ref/mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip`。工具确认ZIP SHA256：`ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1`。清单35项、展开2411908字节，均为分析文本/反汇编；没有截图、真实图像、动画文件、原始SO/APK或实际配置plist。该字节数是证据附件大小，不是游戏包体。
- **R-H（历史d201）**：`ref/mcp-inputs/mac-codex/d20134541539737f425912e559c21b4c383c94b7df59de5962598b516b884198/carrom-current-d201.js`。按用户说明作为历史脚本，不因文件名含current就称现版。路径中的d201哈希未由本轮独立文件哈希工具确认。
- **R-C（当前现版）**：不在附件中。不能核对当前功能是否存在、当前补丁是否生效、当前资源是否缺失。

### 方法与地址约定

已实际读取所选 `game-reverse-engineering/SKILL.md` 及执行协议、全局证据规则、原生地址模型和未知清单模板；读取冻结资料 `genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/native-web.md`。专项 gameplay-logic-reverse 入口读取被权限拒绝，未采用其未读正文。

原生材料声明模块为 `libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so`，SHA256 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`，AArch64、ELF64 ET_DYN。由于原SO未提供，无法独立复核该原件身份。下文原生数值都是该材料中的 **ELF link VA**；不是运行时地址，也不是文件偏移，更不能迁移到另一版。

证据强度：源代码静态分支 > 字符串/重定位命名线索；二者都不等于实际运行。FDE只表示栈展开范围，不保证业务函数边界。重定位槽地址不是函数地址。报告原目录 `../02_静态分析/` 与真实ZIP目录不同，下文只引用清单中的 `analysis/`、`disassembly/`、`report/`。

JS位置使用工具的**零基字符读取范围**加唯一函数名定位，不冒充行号。未完整解混淆，不把未解码表达式猜成具体英文文案。R-H读取范围包括 [0,270000)、[300000,348000)、[400000,424000)、[470000,494000)、[530000,554000)；不是全文件穷尽检索。原生关键词文件只抽读部分区段，不以“未找到”证明“不存在”。

## 1. 证据索引

所有N项路径均为R-N内完整member。

| 编号 | 文件/位置 | 实际支持的证据 |
|---|---|---|
| E-N1 | `report/竞品_ARM64代码定位.md`；`analysis/native_elf_符号.json`头部[0,3000) | 模块身份声明、扫描方法和地址约定；未完整检索全部业务符号 |
| E-N2 | `analysis/native_关键词字符串.txt`，[0,48000)、[600000,700000) | 源路径、类型、selector、配置键的文字线索；不是对应源文件或素材实物 |
| E-N3 | `analysis/native_队友代打字符串交叉引用候选.json` | take-over文案键、selector；扫描结果xrefs为空，不证明不存在调用 |
| E-N4 | `analysis/native_队友代打relocation候选.json`；`analysis/native_队友代打相邻重定位.json` | selector/type/code-pointer相邻关系候选 |
| E-N5 | `analysis/native_字符串交叉引用候选.json` | shotPowerLimits、queenCovered、physicsStopped等候选位置，不是完整玩法恢复 |
| E-N6 | `disassembly/02_MatchShotSolver_18bc618.txt`；`disassembly/07_physicsStopped_1a855b8.txt` | 本轮实际读取的28字节短范围，仅类型名比较/访问代码，不是求解或停球算法 |
| E-H1 | R-H，[0,30000)及`src.bitmaps`、`_0x1ac80c`、`_0x2dad3f` | 五场馆、三模式命名、费用/奖励、纹理引用 |
| E-H2 | R-H，[30000,54000)、[246000,270000)：`_0xa07a9b`、`_0x358d16`、`_0x18076e`、`_0x16b945`、`_0x4bf21a` | PIXI加载、进度条、完成回调、逻辑tick累积 |
| E-H3 | R-H，[54000,102000)：`_0x1260d2`、`_0x5480e3`、`_0x4d0a10`、`_0x3153fe` | 场馆切换、入场、首手决定与新局初始化 |
| E-H4 | R-H，[102000,174000)：`_0x47e567`、`_0xbdafb3`、`_carromFlushTimeoutAfterScan` | 结果去重、奖金、停球后规则结算、超时延后处理 |
| E-H5 | R-H，[150000,222000)：`_0x50a0ff`、`_0x24bb4a`、`_0x49d791` | 本地机器人与无输入超时交接 |
| E-H6 | R-H，[246000,270000)：`_carromMatchSchedule`、`_carromMatchArm`、`_carromPauseMatchTimers`、`_carromResumeMatchTimers` | 匹配页计时的owner/version保护、剩余时长暂停恢复 |
| E-H7 | R-H，[300000,348000)：`_0x15504e`、`goRight`、`_0x51b412` | 教学翻页、结果按钮事件与显示配置 |
| E-H8 | R-H，[400000,424000)：`_0x104b9b`、`startRoll`、`loadTable`、`showStartingShuffle` | 头像轮转、准备事件、首手箭头位置及动画配置 |
| E-H9 | R-H，[530000,554000)：`_0x3797`、`_0x3f3a` | 字符串查表结构及大量资源命名；未运行开头旋转逻辑解表 |

## 2. 七项证据核查

### 2.1 场馆/模式背景与色彩

**原生竞品候选**：E-N2中出现 `TierNodeBack1On1Carrom`、`TierNodeBack1On1DiscPool`、`TierNodeBack1On1PointCarrom`、`POINT_CARROM`、`_boardType`、`filterTierListByGameMode:`、`reloadTiersWithList:tierIdToSnap:gameMode:` 等。证明材料包含按模式组织场馆/UI的命名，不证明具体场馆数、配色、解锁配置或最终贴图。原生业务入口地址未知。

**历史d201可证**（E-H1/E-H3）：`_0x1ac80c`有五场馆 Delhi Lounge、Golden City、Mahal Palace、Mumbai Plaza、Royal Arena；prize/fee依次为50/0、125/50、400/200、1500/750、10000/5000。这是历史配置，不是竞品当前经济系统。`_0x2dad3f`有table/logo/bg/corners/bar/bar_2/cover组；`_0x1260d2`按场馆ID更换相关纹理，mode=2切点数HUD。

实际JS引用例：`assets/tables/0/delhi_lounge_table_01_background.png`、`assets/tables/1/golden_city_table_01_background.png`、`assets/tables/2/mahal_palace_table.png`、`assets/tables/3/Carrom_table_01_background.png`、`assets/tables/4/royal_arena_table_01_background.png`。**这些是路径文字，图片不在附件。** 文件名中的golden、red、purple不能替代像素取色。没有可报告的竞品背景主色、色值或截图内容。

**历史状态流**：菜单选模式 → `_0x48e98f`场馆选择 → `_0x4d0a10`校验余额并扣费 → 本地匹配页 → `_0x1260d2`换纹理 → `_0x5480e3`新局。

**未知**：U-01/U-02。**可执行验证**：未来在同版完整构建逐一进入15个模式×场馆组合，记录资源实际请求/纹理绑定及截图；从真实图片取样色值，检查遮挡、可读性和是否仅换背景不改碰撞。当前不执行。

### 2.2 无操作超时与接管

**原生竞品候选**（E-N3/E-N4）：存在 `effect_turn_take_over_title`、`effect_turn_take_over_description`、`turn_take_over_toast`、`playTurnTakeOverAnimation`。
- 槽`0x291b610` → selector字符串`0x128f46c`；前槽`0x291b608` → code-pointer候选`0x1a11a74`；后槽`0x291b618` → `v16@0:8`编码。
- 第二selector槽`0x29293a0` → `0x130d840`。
- title槽`0x291b370`、description槽`0x291b388`、toast槽`0x2928d00`。
只能标注“接管动画方法实现指针候选”，不能证明触发条件、秒数、谁替谁、是否自动击球；没有该候选函数体或运行记录。词义“队友代打”不能自动套成单人机器人代玩家击球。

**历史d201可证**（E-H5/E-H6/E-H2）：`_0x49d791`每逻辑update递减`_0x1a373b`；计时条件为`_0x3a1262 && (arena !== 0 || (mode === 0 && !tutorial))`。基础数组为[6000,1500,1200,900,600] ticks，最终由缺失的`CarromDiscRules.turnTicks(...)`确定，不能当作固定秒数。

本轮进一步核对`_0x4bf21a`：累加PIXI ticker传入delta，`while (accumulator > 1)`执行`_0x49d791(1)`；其末尾物理调用参数为`1/60,10,10`。因此物理步长静态可证为1/60，计时以逻辑tick为单位；依赖版本、ticker速度/限幅配置未齐，实际墙钟秒数仍未知。严格`>1`而非`>=1`及无明显追帧上限是需要测量的边界，不能据此声称真机卡顿。

超时`_0x24bb4a`取消瞄准、关闭输入；普通分支玩家→`_0x50a0ff`机器人，机器人→`_0x5e7a5f`玩家。**这是弃回合交接，不是替玩家完成击球。** Queen pending分支用turn/round ticket、50ms arm及scan后停球结算防漏进袋。host/ad暂停使逻辑不更新；匹配页计时器按remaining保存并带version保护。仅这些保护有静态依据，不代表全部浏览器后台场景已通过。

**状态流**：可输入回合 → tick耗尽 → 取消手势 →（Queen待处理则scan/停球/结算）→下一回合。原生接管完整流未知。

**未知**：U-03/U-04。**可执行验证**：同版运行无操作、最后1tick放球、Queen刚进袋、暂停/恢复和旧timer到期；记录owner、turn、round、剩余时间、是否实际shot提交，证明超时究竟是skip还是take-over，检查每回合只交接一次。

### 2.3 局内表情与短句交互

**原生竞品候选**（E-N2）：字符串包含构建源路径尾名 `GameplayHudBubbleLayer.mm`、`GameplayHudChatButton.mm`、`ChatBubble.mm`、`ChatMenu.mm`、`ChatMenuFreeTab.mm`。说明包内分析材料涉及HUD聊天/气泡组件；这些源码文件未提供，函数地址、具体短句、表情列表、发送/接收路径、限流和封禁规则均未知。`resetChatReceivers`位于接管邻近重定位材料的`0x29293c0`命名线索，不能据此补出聊天业务入口。材料混有club chat、ludo，不能全部归属于Carrom局内。

**历史d201**：已读区段未定位可证的局内表情/短句发送与显示完整链路。不能报告其“已实现”，也不能穷尽断言“没有”。头像轮转、教程提示、OPPONENT字样不算聊天证据。

**状态流**：原生与历史完整流未知。待验证链为入口点击→选择→发送→气泡显示→消失/限流/静音；不是已证竞品状态流。

**未知**：U-05。**可执行验证**：实际构建打开局内聊天入口，逐项记录菜单、发送者ID、接收者ID、显示时长、重复发送、静音、遮挡；网络协议或本地队列必须与实际气泡对应。当前没有真人会话、消息发送或截图证据。

### 2.4 结算与再赛

**原生竞品候选**（E-N2）：`MatchResultsRewardsList.mm`、`MenuMatchResults showRewardList`、`MatchmakingManager leaveMatchResults`、`rewardsAnimationEnded`等命名。只能证明结算/奖励组件线索，不能证明再赛按钮、与同一对手再匹配、等待超时或原生奖励幂等。

**历史d201可证**（E-H4/E-H7）：`_0x47e567(win)`以`_carromResultCommitted`去重，胜利加prize并保存，创建`_0x51b412(win,prize-or-zero,stone,playerScore,opponentScore)`。外部SDK通知try/catch；广告额外奖励另有一次grant/round guard，外部成功与离线回退未知。

`_0x51b412`构造结果标题、双方分数和奖励；主要按钮pointerdown发close，外围close处理回`_0x48e98f`场馆选择。另一按钮发ad。**已核对按钮类，不能把close描述成直接rematch。** 再开局必须再选场馆并重新进入扣费流程。静态Tween的缩放/位移/奖励数字变化可列为配置，不能声称看到了对应动画。

**状态流**：停球→`_0xbdafb3`回合规则结算→胜负判定→`_0x47e567`一次提交→结果弹窗→close→场馆选择→新入场流程。

**未知**：U-06/U-04。**可执行验证**：胜负分别完成一局；连续点击close/ad；结果阶段重启/切后台；旧广告回调落到新局；对照余额每场只扣费一次、基本奖励一次；确认“再赛”是否重新选场馆。

### 2.5 匹配与加载

**原生竞品候选**（E-N2）：`MenuConnecting.mm`、`MenuMatchmaking setup/leave/rouletteStoppedCallback/updateCoinsToPot`、`matchmaking_enter`、`matchmaking_found`、`matchmakingAnimationsEnded`、`lobby_start_matchmaking_request/response`等。证明命名上区分匹配事件/动画；不证明真实耗时、联网服务状态或进度百分比。

**历史d201可证**：应区分两条流。
1. 资源加载（E-H2）：`_0xa07a9b`建640×1137、resolution=1、sharedTicker、antialias=false的PIXI Application和加载条；`_0x358d16`将src.bitmaps加入loader；`_0x18076e`用loader进度字段/100乘430设置条宽；`_0x16b945`调用`_0x3690db`构造界面。Howl音频另行创建，因此不能保证这个条覆盖音频/所有解码。宿主ready与`postMessage('gameLoadingCompleted','*')`仅是代码上报，不是完整加载验收。
2. 本地对局准备（E-H3/E-H8/E-H6）：`_0x104b9b.startRoll`启动头像轮转，owner计时3000ms后让轮转停止；stop后根据fee分支再安排ready：fee非零3050ms，零1000ms。ready→showStartingShuffle→start。总耗时还包含轮转停止/Tween与调度，不能机械相加宣称总加载时间。`_0x50a0ff`是本地机器人击球链，不是服务器匹配算法。

`_carromMatchArm`只有owner等于activeMatch且挂在当前stage才回调；pause保存remaining，cancel增加version。静态可见防过期机制，未做运行竞态验证。

**未知**：U-07/U-04。**可执行验证**：分开测resourceReady和matchReady；阻断外网、失败一张图、暂停匹配、快速退进场馆、降低帧率；日志比对loader完成、关键纹理解码、按钮可用与首个可操作帧。不能用假轮转时长当加载进度。

### 2.6 开局首手提示

**原生竞品候选**（E-N2）：`OpeningShot`、`OnPlayerTurn`、`ResumeTurn`、`break_player`、`break_opponent`、`gameStartingWithOpponent:localPlayerOrder:tierId:eligibleForLeaderboards:`。这些只是开局/回合命名，不证明抽签动画、首手概率或文字。

**历史d201可证**（E-H3/E-H8）：`_0x4d0a10`先决定`_isPlayerStart = Math.random() > 0.5 || tutorial`；教程强制玩家先手，非教程是代码上的约一半概率。ready后传0/1给`showStartingShuffle`，不是箭头动画随机决定结果。

该方法创建starting_arrow，配置水平数组循环time=40、loop=3，结束后向玩家侧x=210或对手侧x=430补间time=30，然后发start；Tween time单位是该历史更新体系，不直接冒充秒。场景坐标是设计坐标，不是实拍屏幕坐标。新局`_0x5480e3`按已选首手进入玩家/机器人回合。原`assets/starting/1.png`、`starting_player_base.png`等图片内容未知。

**状态流**：入场时决定首手→头像轮转→ready→展示既定首手→start→对应owner回合。关键信息应由状态先确定，表现只消费它。

**未知**：U-08。**可执行验证**：固定随机种子/注入双方首手各跑一局，断言箭头最终侧、HUD owner和首个输入窗口一致；跳过动画/减少动画后也一致；教程始终玩家先手。

### 2.7 规则教学

**原生竞品候选**（E-N2）：`TutorialWelcomePopup.mm`、`TutorialCongratulationsPopup.mm`、`MatchFlowTutorial enterFirstStepTry/enterFirstStepTryMoving/leaveWelcomePopup`、`MatchControllerTutorial setupAimControls/onFinishStateEnter`；还有`rules_carrom`、`rules_point_carrom`、`rules_match_point_carrom`及Queen提示键。`Tutorial_Arrow.png`、`Tutorial_Finger.png`只是字符串，不是附件图片。不能恢复页面原文或Queen规则细节。

**历史d201可证**（E-H3/E-H7）：
- `_0x15504e`默认6页；指定mode=0/1/2时各4页，PAGES/TITLES/PAGE_COUNTER更换，左右pointerdown翻页，close按钮发close；菜单和暂停面板可创建此页。
- `goRight`指定mode时page>=3返回，但隐藏right仅在page==5执行：四页模式末页右箭头可能仍显示但不前进，这是静态风险，未运行判定实际视觉缺陷。
- `_0x25e9ed`与滑杆回调提供定位击球器→瞄准/拉动→合法放球的操作教学；`_carromFinishTutorialAfterShot`只在合法strength>=0.25放球后结束，弱力度重新显示提示。文本表达式未全解码，图片化规则内容未提供。
- 核心计分/Queen/Freestyle分支依赖未附`CarromDiscRules`；历史补丁注释明确部分Freestyle规则为provisional。不能标成已还原竞品规则。

**状态流**：规则手册打开→翻页→关闭回原菜单/暂停面板；首次操作引导→位置输入→瞄准→有效击球→记录完成。不能混同“看完图片页”和“掌握合法击球”。

**未知**：U-09/U-04。**可执行验证**：全部模式逐页翻阅、末页边界、退出重看、跳过、弱力/非法输入、存档失败/清档；对照实际规则文本与规则单测，保证Queen/犯规说明不与代码冲突。

## 3. 参考取舍与离线原型建议（非竞品事实、非用户新增确认）

保留可证明的流程组织：模式/场馆分离、回合owner、一次结算、首手状态先决定、首次操作与规则手册分开。不要复制缺失图片、未确认配色、原厂经济值、原生偏移、联网匹配文案、SDK或广告依赖。

### 3.1 核心循环与规则契约

建议默认英文界面，页面`lang=en`，不因中文系统自动切语言。标题`Carrom — Offline`；对手所有主要页面明确`Local Bot`。循环：选择规则/场馆→准备本地局→展示首手→定位/瞄准/释放→物理运动→静止后结算→续手/换手→胜负→再赛或回菜单。

为避免把未知竞品边界硬编码为“官方规则”，原型建议以独立命名的`Quick Match`作为可验证基础：双方各9枚目标盘，无Queen；己方进袋每枚1分，9分胜；对方目标进袋计给对方；击球器进袋为犯规，不续手；合法进己方至少一枚且未犯规可续手，否则换手。整杆收集事件后统一判断胜负，双方同杆达9分以Draw结束，不按动画顺序决定胜者。犯规不倒扣已提交分、不返盘。这是建议的简化离线规则，不是竞品Carrom完整规则。Queen/Point/Freestyle作为后续规则规格选项，本轮不实施、不声称用户选择此范围。

状态：menu、preparing、opening、playerAim、botThink、simulating、settling、result；暂停保存原状态与有效时间。所有异步任务带matchEpoch/turnId，旧epoch回调无副作用；计分和存档先一次提交，动画被取消不丢分。退出未结局不发胜利奖励。再赛新epoch、重置输入/timer/事件队列，保留同规则/场馆，首手重新决定。

### 3.2 物理步长、碰撞、误差与输入窗口

建议规范逻辑棋盘边长600单位，显示缩放不改物理。原型参数起点：目标盘半径14、击球器18、目标质量1/击球器1.5、恢复系数0.85、无旋转球体、线性阻尼2.8/s、击球最大速度900单位/s。这些待调值不来自原生算法恢复。

- 固定物理h=1/120s，requestAnimationFrame仅显示；累加有效前台时间，每渲染帧最多12步。单帧间隔>100ms走显式暂停/恢复，不悄悄丢模拟时间或一次补完巨量步数。计时使用独立前台有效墙钟，不按渲染帧扣时间。
- 圆-圆与圆-边界碰撞、稳定ID排序；高速用扫掠碰撞/TOI或经过验证的子步，不能只看终点重叠。四角袋口使用明确洞口几何及中心穿过捕获线事件，capture后退出碰撞世界；每盘每杆只capture一次。袋口与墙相交区域优先按TOI处理，不能靠扫描顺序判分。
- 全盘速度<2单位/s连续0.25秒后置零并进入settling；有效模拟15秒仍不静止则暂停为可见恢复提示，不强判胜负。
- 同一seed/同一逻辑tick输入，在30/60/120fps呈现下得分、捕获盘ID、犯规和owner完全一致；最终位置差<=0.5逻辑单位、停球时间差<=1个物理tick；同设备重复试验目标为更严格一致。残留穿透<=0.1单位，无NaN/无穿墙/无双入袋。
- 输入仅playerAim开放，单pointerId+pointer capture；底边合法位置拖动、拉动瞄准、pointerup释放。力度归一化0.05..1有效，低于0.05取消不消耗回合；角度与力度在释放时锁定，屏幕坐标经统一逆变换，映射误差<=1逻辑单位。暂停、pointercancel、多指、非owner输入不得触发shot。
- 建议20秒前台有效瞄准窗口，剩5秒提示；截止判断为eventTime<deadline有效，否则超时胜出，双方竞争同一原子shot-or-timeout提交；每回合至多1次。超时文案`Time's up. Turn skipped.`，不默认代玩家击球。若未来设计可选Auto Shot必须显式开关、`Auto Shot by Local Bot`说明，与正常Bot回合分owner；本轮不确认此扩展。

### 3.3 七项轻量UI方案

| 项目 | 建议实现与英文文案 | 低包体/安全边界 |
|---|---|---|
| 场馆/模式 | DOM卡片、Canvas共享棋盘，主题tokens换背景/边框；色彩使用新设计而非“还原竞品” | 不做15套整屏贴图；主题不改变物理；颜色不是唯一状态信号 |
| 超时 | HUD数字/细环，`Your turn`/`Local Bot's turn`；暂停不耗时 | CSS变化只在显示值变化时更新；不以环动画决定超时 |
| 表情/短句 | 本地4个反应+`Nice shot!`/`Good game!`/`Oops!`，气泡2秒，冷却3秒，Mute reactions | 不接网络、不暗示真人回复；机器人反应注明Bot或关闭；最多2气泡，DOM SVG图标避免平台emoji尺寸差异 |
| 结算/再赛 | `You win`/`Local Bot wins`/`Draw`、分数、`Play Again`、`Back to Menu` | 无广告解锁、无远端奖励；Play Again只创建一局，禁连点 |
| 匹配/加载 | `Loading local assets…`与`Preparing local match…`分开 | 真实资源就绪决定可玩；不制造Searching for players；无必要的固定3秒等待 |
| 首手 | `You break first`或`Local Bot breaks first`；约0.6秒可跳过 | 先定状态，动画只显示；prefers-reduced-motion直接静态提示 |
| 教学 | `Move the striker`→`Drag to aim`→`Release to shoot`；`Skip`/`Rules`/`Replay Tutorial` | DOM文字与简单矢量示意替代文字整页图；教程完成按合法输入，不按计时 |

布局建议：竖屏上部为模式/暂停和双方身份/分数，中部600单位棋盘，下部位置滑杆与操作提示，反应菜单放棋盘外；横屏棋盘居中、HUD/操作分列。DOM弹窗阻断底层输入并管理焦点。点击区域至少44CSS px，校验360×800和1280×800等视口；低DPR/高DPR都用相同规则坐标。

### 3.4 架构与机器人

原生HTML/CSS/ES modules，Canvas棋盘+DOM UI；rules、physics、input、presentation、bot、storage、assetLoader边界分离。相对资源路径、无CDN、无必需联网或SDK。HTML/CSS/JS及资源全部本地打包。首次下载也必须有分发载体；网页第二次离线冷启动需要安装包或经验证缓存策略，不能把“断网后原标签继续运行”当离线冷启动。

本地机器人在同一规则/物理接口提交合法shot；候选目标/袋口最多64，稳定seed用于复现，每批主线程预算<=4ms，整次思考计算墙钟p95<=100ms，超预算用合法fallback，不能卡住输入/动画。不复制MatchShotSolver候选28字节当AI算法。难度通过可记录的角度/力度扰动控制，不凭空改变碰撞或分数。

## 4. 可执行验收与测量方案（全部待测）

本轮只读原型定义，未建立package.json/scripts/dist，因此没有执行npm构建/测试/check；这是阶段不适用，不是PASS。原始输入不能完整运行，其资源和依赖缺失。上一attempt的日志也不作本轮运行成功证据。未来代码阶段最后一次源码/资源修改后必须真实执行`npm run build`、`npm test`、`npm run check`；check启动本地静态服务器访问最终dist，结束自动关服，验收后不再改/重建dist。

| ID | 操作/样本 | 必须断言、测量或保存 | 本轮状态 |
|---|---|---|---|
| V-01 | 同输入seed，30/60/120fps和单帧100ms边界 | 物理误差阈值、同capture/分数/owner；高速盘-盘/角袋/边界 | 待测 |
| V-02 | deadline前/等于/后释放，pointercancel、2指、拖出画布 | shot或timeout唯一提交；无跨owner输入，坐标误差<=1单位 | 待测 |
| V-03 | aim/botThink/preparing/simulating中暂停10秒后恢复 | 剩余有效时间不减，旧epoch task不触发，模拟不追后台时间 | 待测 |
| V-04 | 完整胜/负/Draw；结果连点20次；连续再赛30次 | 每局一次结算、无状态残留/奖励重复，旧动画回调无效 | 待测 |
| V-05 | 首手双方、教程完成/跳过/重看、规则末页 | 首手提示=owner；弱力不完成；末页导航可见性正确 | 待测 |
| V-06 | 反应快点、Mute、弹窗开闭 | 3秒限流、2秒消失、无遮挡/焦点泄漏/假真人信息 | 待测 |
| V-07 | 无缓存、禁止外网、断网冷启动、缺失关键资源 | 所有请求本地；真实加载完成才可输入；错误有Retry且无永久假100% | 待测 |
| V-08 | 桌面1280×800/手机360×800真实点击和触摸 | 主要流程、控制台零未处理错误、截图、英文文案/lang=en；zh-CN浏览器仍英文 | 待测 |
| V-09 | 至少30次Bot决策/档位，多局长时间 | 计算p50/p95/最大值、每批耗时、fallback频率/合法性 | 待测 |
| V-10 | 每视口至少10次冷启；运行5分钟并连续30局 | 启动、帧耗时、输入延迟、长任务、内存与资源释放 | 待测 |

### 暂定预算与统计口径

这些是本项目建议门槛，未经目标设备实测，不是竞品数据或已批准产品承诺。

- 最终dist展开严格<10000000字节；建议目标<=3MB。分别记录dist展开、试玩ZIP压缩、HTTP transferred/decoded、源码ZIP，源码ZIP不能替代部署包体。只打包实际可达资源，参考分析文本不入dist。
- 本地资源冷启动至首个可操作帧p95<=2秒；同设备/同浏览器/同缓存条件至少10次，记录导航开始、关键资源就绪、UI ready和input ready。远程网络时间另测，不混同本地启动。
- 目标60fps：总帧耗时p95<=16.7ms，输入至视觉响应p95<=50ms；统计5分钟样本、>50ms长任务计数。30fps保底只作另一个档位，不能删除慢帧样本。
- 资源解码图像预算<=16MiB：以宽×高×4估RGBA并另列实际编码字节，PNG/WebP变小不等于解码内存变小。限制Canvas DPR，离屏棋盘只缓存一份。
- 内存必须分别列JS heap、图像/Canvas估算、可用浏览器进程RSS；建议连续30局释放/GC后的稳定JS heap相比第1局增长<=5MiB且无持续单调增长。GC采样方法与工具支持需写明，不能拿heap代表全部内存。目标设备型号/OS/浏览器/WebView/RAM未指定，本轮真机验收BLOCKED，桌面浏览器不能替代。
- 每次測量保存seed、输入时间序列、构建哈希、环境、原始采样与截图，后续输出到evidence/；源码和试玩ZIP到releases/。本轮未生成这些目录内的测试证据。

## 5. 未知清单

| ID | 缺口 | 影响/如何解除（未来有同版材料或运行条件时） |
|---|---|---|
| U-01 | 附件没有真实图片/截图/动画资源 | 七项视觉均不可验收；同版构建真实显示后取图/取色；本轮不索取资料 |
| U-02 | 当前现版不在参考中 | 历史d201结论不可转写为当前状态；需对当前输入单独建立基线 |
| U-03 | 原生接管仅selector/重定位候选 | 触发条件、时限、代打主体、是否击球未知；需同版函数体与运行轨迹 |
| U-04 | CarromDiscRules、PIXI、Howl、SDK等依赖未附 | 完整规则、tick墙钟、资源成功、离线广告回退/实际执行未知 |
| U-05 | 局内聊天只有原生命名线索，历史完整链路未定位 | 不知道表情/短句、限流/静音/收发规则；不能宣称恢复聊天 |
| U-06 | 原生再赛入口/状态机未提供 | 不知道是否同对手再赛；历史已证为回场馆，不等于原生行为 |
| U-07 | 没有资源/加载运行记录 | loader百分比覆盖范围、实际匹配/启动耗时未知 |
| U-08 | 首手文字贴图和运行未提供 | 历史状态/箭头配置可证，实际文案与原生首手算法未知 |
| U-09 | 教学图片原文、Queen/Freestyle完整规则未知 | 不能复原原生教学内容或宣称规则一致；简化规则只是独立建议 |
| U-10 | 原SO未附、扫描不完整 | 地址来自分析材料声明；不可动态hook、不可跨版本复用；FDE不当函数体 |
| U-11 | 目标设备与完整构建缺失 | 包体、帧率、内存、触摸手感/真机视觉均待测，不填写虚构值 |

## 6. 本轮收口

- 已完成：35项ZIP清单核查；选定方法与冻结资料读取；七项证据分层、历史状态流、地址/函数位置、未知及可执行验证设计。
- 本轮恢复后追加真实静态读取：历史教学/结算按钮类、匹配/首手类、ticker/物理调用/计时owner实现；原生两段短反汇编实际复核。连接恢复后读取成功，但无运行态成功证据。
- 产物：`/workflow/prototype.md`。未改变源码、配置、资源或dist，未建立可玩游戏，未生成美术资源与截图。
- 验证结果：附件静态定位完成；竞品视觉、当前现版一致性与运行/性能验收均未知或待测。npm build/test/check在当前只读原型阶段未执行，不声称通过。不存在以旧日志代替本轮验证的情况。
- 阶段状态：原型证据报告完成，不代表美术、代码或测试阶段完成；不自动推进下一阶段、不编造用户确认。
