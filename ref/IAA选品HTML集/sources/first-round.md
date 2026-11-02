# 非洲、南亚 Android IAA 游戏选品报告（第一轮）

**调研日：2026-09-21｜公开榜单快照：2026-09-18｜状态：第一轮候选研究，尚非正式规模化立项。**

> 范围补充：本轮较偏重视觉解谜，对音游、纸牌及其他轻玩法展开不足。新的完整范围见 `IAA宽口径候选池_2026-09-21.md`（14组方向、32款参考）；音游与纸牌另有专项讨论。下面的“首选”仅代表第一轮子集比较，不应视作已经排除其他品类。文末已补核心竞品中文说明名与 Google Play 链接。

## 一、结论先行

建议建立两条产品线，但首批只验证两个原型，不同时开多个正式项目：

1. **跨地区主线：首选 Arrow Puzzle（箭头解阻），第二原型选 Triple Tile Match（槽位图块三消）。** 前者当前跨国榜单信号强、规则可一句话解释；后者有多个产品与市场交叉支持，清屏反馈接近已验证玩法，但核心机制不同。
2. **稳健替补：Mahjong Solitaire（两张配对清屏）与 Ball/Water Sort（球／水分类）。** 配对在本轮非洲总榜的覆盖很好；分类在巴基斯坦、孟加拉国尤其值得留意。与三消、箭头分别验证，不把它们当作同一玩法。
3. **地区产品线：本地规则 Ludo → 南亚 Carrom → 埃及 Domino。** 有地区榜单与文化适配理由，但对局时长、AI、规则本地化或联网竞争使其不宜成为当前最低成本的第一项目。
4. **暂缓：螺丝／毛线分类、轻足球／板球、Ayo/Bao、Callbreak/29 牌类。** 并非没有市场，而是当前证据、规则门槛或研发成本不如前述方向匹配。

**如果本轮只能选一个：先做“离线优先、大点击区域、无强制计时”的 2D 箭头解阻。**

注意：这里的“高潜”是**值得投入验证预算**，不是已经证明高 DAU、高增长或 IAA 盈利。没有竞品真实 DAU、收入结构、留存与买量成本，不能直接承诺规模。

## 二、数据可信度与口径

### 2.1 已核查的数据

- Similarweb：七国 Puzzle 分榜，以及地区研究中的 Games 总榜、Board、Sports、Cards 分榜。
- Google Play：核心竞品商店介绍、全球累计下载档位、广告／内购标签、离线声明和部分公开评论。
- 文化资料：只用于解释本地玩法与规则差异，不用于推导当前市场规模。
- [Apollo 公司平台](https://apollo.shalltry.com/big-data-web/#/applicationAnalysis/leaderboard/active)：本次仅取得平台入口，未取得榜单内容或已登录数据；**未引用任何 Apollo DAU 数值**。

web_fetch 起初对部分公开网页仅返回标题；后通过 Node 获取同一公开页面 HTML，读取其可见文本与公开结构化数据。未使用登录凭据、付费接口或绕过访问权限。

### 2.2 一个必须注意的榜单陷阱

同样是 `/top-free/` 页面，默认排序不一定相同：

|标记|实际含义|本次处理|
|---|---|---|
|S：Store Rank|指定国家、商店、分类、榜单的商店排名；平台称每日更新|作为商店榜信号，不称下载量或 DAU|
|U：Usage Rank|Similarweb 综合当前安装与近 28 天活跃用户因素的使用排名|作为存量使用信号，不是 DAU 人数或单纯活跃用户排名|
|全球累计下载档位|Google Play 对单款应用显示的累计 Downloads 档位|不等于目标国下载、近期新增、独立用户或 DAU|

七国 Puzzle 页中：印度、南非、埃及默认按 U 排；巴基斯坦、孟加拉国、尼日利亚、肯尼亚按 S 排。后四国 U 字段为 0，本报告按缺失显示，不写“第 0 名”。**不能拿页面行号当 S。**

日期采用页面标题与 `snapshotDate=2026-09-18`。部分结构化元数据的 `dateModified` 显示不同月份，未采用该字段。所有证据均记录实际访问日 2026-09-21。

本轮是单日横截面，没有 28/90 天序列，**不能用单日高位证明自然增长、长期稳定性或投放效率**。榜单可能受买量、预装、交叉推广、促销等影响。

本轮未进行竞品真机试玩、广告 SDK 抓包或低端机性能测试；玩法描述来自已读取的商店材料，手感、包体、帧率、实际广告频次和用户留存均留待下一阶段验证。

## 三、跨国榜单证据

### 3.1 同一产品在七国 Puzzle 分榜的排名

每格为 **S / U**，破折号表示该字段缺失。均为 Similarweb 的 Google Play、Puzzle 分类、2026-09-18 快照，不能与 Games 总榜数字混用。

|产品|印度|巴基斯坦|孟加拉国|尼日利亚|肯尼亚|南非|埃及|
|---|---:|---:|---:|---:|---:|---:|---:|
|Arrow Puzzle · Easybrain|1 / 2|1 / —|1 / —|2 / —|6 / —|24 / 13|1 / 6|
|Amaze GO! · Oakever|2 / 3|6 / —|12 / —|31 / —|45 / —|37 / 3|9 / 5|
|Tile Explorer · Oakever|6 / 4|10 / —|17 / —|9 / —|11 / —|23 / 9|7 / 3|
|Tile Club · GamoVation|18 / 8|4 / —|5 / —|8 / —|4 / —|13 / 30|25 / 40|
|Ball Sort · Guru|30 / 24|3 / —|2 / —|25 / —|7 / —|10 / 44|21 / 26|

来源：[印度](https://www.similarweb.com/top-apps/google/india/games/puzzle/top-free/) · [巴基斯坦](https://www.similarweb.com/top-apps/google/pakistan/games/puzzle/top-free/) · [孟加拉国](https://www.similarweb.com/top-apps/google/bangladesh/games/puzzle/top-free/) · [尼日利亚](https://www.similarweb.com/top-apps/google/nigeria/games/puzzle/top-free/) · [肯尼亚](https://www.similarweb.com/top-apps/google/kenya/games/puzzle/top-free/) · [南非](https://www.similarweb.com/top-apps/google/south-africa/games/puzzle/top-free/) · [埃及](https://www.similarweb.com/top-apps/google/egypt/games/puzzle/top-free/)。

**解读：**
- 箭头解阻不只有一个头部产品：Arrow Puzzle 与 Amaze GO! 同时出现，是优先拆解该机制的理由；但这也意味着竞争已经形成，不是无人进入的蓝海。
- 三张配对并非只能服务单一国家：Tile Explorer、Tile Club 的交叉表现降低了“只命中某国某款产品”的担忧。
- 分类并非处处同强：Ball Sort 在巴／孟明显更靠前。不能把这个结果直接外推整个南亚或非洲。
- 不计算“七国平均名次”：国家大小、分类容量、渠道与排序口径不同，简单平均容易误导。

### 3.2 用 Games 总榜补证，避免只看小分类

|方向／竞品|可核查的总榜证据|含义与限制|
|---|---|---|
|Arrow Puzzle|印度 S3/U5；巴基斯坦 S3；孟加拉国 S3；尼日利亚 S11；肯尼亚 S42；埃及 S5/U26|具有总榜支撑，不只是 Puzzle 分类头部|
|两张配对：Vita Mahjong|尼日利亚 S9；肯尼亚 S12；南非 S30/U19；埃及 S35/U12|非洲四国均有总榜信号；这里是图案配对，不是四人传统麻将|
|Ludo King|印度 S2/U2；巴基斯坦 S4；孟加拉国 S2；南非 S8/U14|大盘需求明确，但经典市场竞争强|
|Naija Ludo|尼日利亚 S15，另 Board S3|本地规则可能比泛化 Ludo 更重要|
|Carrom Pool|印度 S6/U6；孟加拉国 S10|注意该产品在 Sports 分类，不是 Board|
|Water Sort: Color Match · FunForge|尼日利亚 S39；肯尼亚 S29|分类玩法另有非洲总榜交叉证据，勿与其他同名产品混淆|

总榜来源：[印度](https://www.similarweb.com/top-apps/google/india/games/top-free/) · [巴基斯坦](https://www.similarweb.com/top-apps/google/pakistan/games/top-free/) · [孟加拉国](https://www.similarweb.com/top-apps/google/bangladesh/games/top-free/) · [尼日利亚](https://www.similarweb.com/top-apps/google/nigeria/games/top-free/) · [肯尼亚](https://www.similarweb.com/top-apps/google/kenya/games/top-free/) · [南非](https://www.similarweb.com/top-apps/google/south-africa/games/top-free/) · [埃及](https://www.similarweb.com/top-apps/google/egypt/games/top-free/)。

## 四、候选排序与开发取舍

排序综合：跨国／总榜证据、规则与操作门槛、IAA 自然触点、离线可达性、研发及内容成本、地区适配和差异化空间。**不是统计模型得分，也不是 DAU 预测。**

|优先级|候选|一句话规则|建议市场／定位|主要风险|
|---|---|---|---|---|
|P0-1|箭头解阻 Arrow Puzzle|点击前方无阻挡的箭头，按顺序清空棋盘|跨地区首个原型；先选公司可稳定获量的两个国家|密集图案难辨认、关卡同质化、过难依赖提示|
|P0-2|槽位图块三消 Triple Tile|点选露出的图块，凑三张相同消掉，避免槽位占满|跨地区第二原型；与箭头对照|伪随机死局、槽位挫败、关卡生产及广告打断|
|P1-1|两张配对清屏 Mahjong Solitaire|选两张相同且可操作的牌消除，清空布局|非洲优先替补；追求更低初始认知门槛|竞争成熟、遮挡／可选规则仍需教学、过度依赖洗牌|
|P1-2|Ball / Water Sort|把容器顶端同色物移到一起，最终各容器颜色统一|巴基斯坦／孟加拉国优先；成熟对照|色彩辨识、状态空间难度、广告加瓶破坏体验|
|P2-1|本地规则 Ludo Lite|掷骰移动棋子并先完成赛道|尼日利亚本地版、南亚版分别验证|长局、多人广告节奏、AI公平、本地规则差异|
|P2-2|Carrom Lite|瞄准弹击，把己方棋子打入袋|印度／孟加拉国优先，巴基斯坦另验|瞄准精度、物理手感、设备触控、AI与头部竞争|
|P2-3|Domino Lite|把相同点数的牌端连接，先出完或按规则计分|埃及单市场小试|规则／计分本地化；不能只凭咖啡馆文化推算全体需求|

### 4.1 为什么首推箭头解阻

**与已验证玩法共性：** 少文字、一指操作、清晰局面、从复杂变整洁的清屏反馈、关卡可重复组织。**不重复：** 没有发射泡泡、颜色碰撞消除、下落方块或填满行列；核心是方向、遮挡与移除顺序。

[Arrow Puzzle 商店页](https://play.google.com/store/apps/details?id=com.easybrain.arrow.puzzle.game&hl=en&gl=IN) 已核查：50M+ 全球累计下载档位、Contains ads + IAP、单人离线标签；规则为路径畅通才能移除箭头，并有提示与每日挑战。商店介绍不构成低端机性能实测。

**建议 MVP：**
- 2D、大点击区、可放大但避免默认依赖缩放；首 10 关无时间限制，用演示取代文字教程。
- 约 60–100 个经过解算器验证可解的关卡作为初测范围；建立逆向生成／可解性校验，再谈无限关卡。
- 短关主线与每日关卡；离线本地存档、回前台不丢进度。
- 激励广告：自愿提示／失误恢复。插屏仅关后自然断点，不在找路径过程中出现。
- 第一版不做实时多人、公会、大地图装修、复杂付费经济；内容和商业化均原创，不能直接复制竞品关卡、美术或品牌。

**差异化假设：** 不是“换皮箭头”，而是“大尺寸可辨认＋更短的首局＋无网不卡关＋可靠存档”。这些优势必须通过真实设备和玩家测试证实。

### 4.2 第二原型：槽位三消，而不是重型装修三消

[Tile Club](https://play.google.com/store/apps/details?id=com.gamovation.tileclub&hl=en&gl=IN) 与 [Tile Explorer](https://play.google.com/store/apps/details?id=com.oakever.tiletrip&hl=en&gl=IN) 均显示 100M+ 全球累计下载档位、广告＋内购和离线标签。它们的成功不证明我们需要复制社交、公会、活动和全部关卡量。

- 用水果、器物等高区分度图案；颜色与轮廓双重识别，不要求用户会麻将术语。
- 先验证固定容量槽位、三张同图案消除、可见／遮挡关系；以可解关卡替代“随机凑满”。
- 约 60–100 个验证关；暂不做重 3D 寻物、大量货架物体或装修经济。
- 可选撤销、提示、洗牌是广告触点；必须保留免费重试与无广告时的可继续路径。
- 公开商店评论中可见对局中插屏、广告冻结／缓冲的投诉，只作为体验问题线索，**不是统计意义上的投诉率**。

**两张配对单独管理：** [Vita Mahjong](https://play.google.com/store/apps/details?id=com.vitastudio.mahjong&hl=en) 的核心是两张可用牌配对，不是槽位三消，也不是传统麻将。若非洲首轮测试显示槽位规则理解慢，优先用其机制做下一轮替补，而非在同一原型堆上两个模式。

### 4.3 分类作为稳健候补，球／水不要重复算赛道

[Guru Ball Sort](https://play.google.com/store/apps/details?id=ball.sort.puzzle.color.sorting.bubble.games&hl=en&gl=IN) 显示 50M+；[IEC Water Sort](https://play.google.com/store/apps/details?id=com.gma.water.sort.puzzle&hl=en&gl=IN) 显示 100M+，均为全球累计下载档位。前者规则为同色顶球入瓶，后者为同色倒水，核心均涉及容量与顺序规划。

虽然画面可能有“球”，**但不是 Bubble Shooter**：没有发射、瞄准、碰撞消泡。建议两者作为同一分类赛道的表现方案，不占用两个选品名额。

可测试高对比颜色＋形状／纹理、大容器、无计时和免费撤销。不要默认“必须看广告加一瓶才能解”；易变成强制广告，且离线时直接破坏体验。

## 五、地区文化：用本地规则，而不只是贴地方皮肤

### 尼日利亚：Ludo 本地规则有明确产品信号

[Naija Ludo](https://play.google.com/store/apps/details?id=com.tonielrosoft.classicludofree&hl=en) 商店介绍含离线／蓝牙、不同骰子与安全区选项，且描述为两人各八棋等规则，**不能机械套用经典四人各四棋版本**。先做本地规则访谈，再做短局 AI／同机体验；不做“看广告改骰子”。现金、提现、赢话费类同榜产品不纳入纯 IAA 需求证据，也不照搬其获客承诺。

### 印度／孟加拉国：Carrom 有榜单基础，但操作不如点按解谜简单

[Carrom Pool](https://play.google.com/store/apps/details?id=com.miniclip.carrom&hl=en&gl=IN) 显示 500M+ 全球累计下载档位；印度 Sports S1/U1，孟加拉国 Sports S3。可以研究离线 AI、同机双人、短局残局，但物理稳定性与触控体验是关键成本。不能看到 Carrom 的头部成绩就推断任何弹珠玩法都能复现。

[Ludo King](https://play.google.com/store/apps/details?id=com.ludo.king&hl=en&gl=IN) 显示 1B+ 全球累计下载徽章，支持离线等模式。厂商正文更大的、统计范围未澄清的宣传数字未替代该徽章，也未用于推算地区 DAU。

### 埃及：Domino 有文化与多产品证据，但只做定向试验

[埃及 Board 榜](https://www.similarweb.com/top-apps/google/egypt/games/board/top-free/)：Domino Cafe S5/U10、ZiMAD Domino S6/U13、Loop Dominoes S13/U16。它们是 **Board 分榜**，不是总榜头部。

[National Geographic 的埃及咖啡馆报道](https://www.nationalgeographic.com/travel/article/egypts-coffeehouses)（2011-06-09）提到多米诺／双陆棋，且场景主要男性；这是历史文化线索，不代表当前全年龄、性别普及率。[Loop Dominoes](https://play.google.com/store/apps/details?id=com.LoopGames.Domino&hl=en) 提供 Draw／Block／All Five，哪个本地规则更合适仍需访谈。

### 跨地区落地原则

- 不做统一“非洲风”或默认所有南亚市场规则相同。埃及阿语、巴基斯坦乌尔都语涉及 RTL；语言选择还需结合公司实际受众。
- 传统棋类依赖本地规则；抽象解谜更适合以低文字、大图案覆盖多地区。
- 宗教、神像、国旗、球队、人物肖像等敏感或授权元素不作为默认皮肤。不要从某款宗教题材进入印度榜就外推整个南亚。
- “离线”不等于“低端机流畅”：需要实测 2GB RAM 级设备、弱网、恢复前台、广告 SDK 内存峰值及发热。
- 文化皮肤必须通过本地审查与素材 A/B 验证；熟悉感是否降低 CPI、提高留存目前未知。

## 六、为什么暂不选其他方向

|方向|暂缓原因|
|---|---|
|Bubble Shooter、Tetris、Block Blast、Block Puzzle、填格消行|按本轮去重边界排除；不借方块皮肤重新选择已验证方向|
|螺丝／毛线排序|本轮多国 Puzzle 样本中可见，但整体证据不优于箭头／图块；若涉及物理、3D 与复杂遮挡，内容和性能成本更高；全球趋势不等于目标国高 DAU|
|完整足球／板球模拟|榜单热度不等于轻玩法热度；实时网络、操作、授权与资源消耗增加；可保留轻射门／短击球作为第二波|
|轻足球 Soccer Superstar|南非总榜 S108/U32、埃及 S44/U32，有直接证据，但非洲其他国家的完整足球头部成绩不能直接替它证明需求|
|Ayo／Mancala／Bao|尼日利亚 Board 有 Mancala S33、Opon Ayo S47，但不够支持首个大盘项目；东非 Bao 四排规则较复杂，不等于简单两排 Ayo|
|Callbreak／29|印度 Cards 有强使用信号，但叫分、将牌、四人对局（29还涉及搭档协作）的入门门槛高于本任务；有本地棋牌能力时再做|
|Sudoku／文字问答|可能有存量用户，但数字／文字学习成本或本地化内容成本更高，不优先于当前视觉解谜路线|
|现金奖励／提现型产品|其榜单流量可能来自奖励诉求；不据此推断纯玩法需求，不作为 IAA 原型模式|

Bao 规则差异参考：[Ludii 学术游戏库](https://ludii.games/details.php?keyword=Bao+Kiswahili+(East+Africa))。Carrom／板球分榜参考：[印度 Sports](https://www.similarweb.com/top-apps/google/india/games/sports/top-free/) · [孟加拉国 Sports](https://www.similarweb.com/top-apps/google/bangladesh/games/sports/top-free/)；牌类参考：[印度 Cards](https://www.similarweb.com/top-apps/google/india/games/cards/top-free/)。

## 七、IAA 成立条件：可玩的大盘，不等于可变现的大盘

核查的核心竞品普遍同时包含广告和内购，**不能称为已证实的纯 IAA 成功案例**。我们的目标是广告主导，需要单独验证广告收入占比与用户体验。

建议以实际曝光衡量：

`广告 ARPDAU = Σ（各广告形式有效展示数 / 总 DAU × 对应实现 eCPM / 1000）`

`广告 LTV_H = Σ t=0…H（该安装 cohort 第 t 日活跃率 × 第 t 日广告 ARPDAU）`

- 使用同一国家／渠道／cohort 的口径；总 DAU 包括离线活跃，缺失离线事件回传必须单独标识。
- 有效展示数已体现联网比例、请求率、填充率和展示成功率；不要在公式中重复乘这些折损。
- 若用“广告机会数”预测，则必须逐项考虑联网、填充、实际播放成功及激励完成率。
- 买量决策比较 **净 LTV 与有效 CPI**，并计入归因延迟、无效流量、退款／扣量、运营及服务成本，不能只看广告毛收入。
- 本轮没有实测 eCPM、CPI、填充率或付费转化率，不填写假定“非洲均价”“南亚均价”。

广告体验建议：首轮教学不强插；插屏只放自然关后断点并限制频率；不在用户点按或思考中途触发。激励广告明确自愿、承诺必兑现；无网／无填充时给重试或可玩替代，不强迫联网。任何频控参数都应作为实验变量，不是预设收益保证。

## 八、从选品到开发的低成本验证方案

### 阶段 A：补齐商业数据，收窄到两个市场

优先选择公司渠道可触达的“一非洲＋一南亚”市场，而非首轮投七国。**在渠道条件未知时，暂用尼日利亚＋印度作跨地区对照；若巴基斯坦／孟加拉国获量更好，则替换，不硬套。**

每条候选按包名收集最近 28／90 天：DAU/MAU、新增、国家占比、排名趋势、使用时长、会话、可用留存、增长是否来自投放／预装。验证榜单爬升是否转化为存量使用，不能只看当日名次。

### 阶段 B：先理解与性能，再广告

- 首批只做 Arrow 和槽位三消两个原型，复用基础存档、埋点、广告、关卡校验能力。
- 每个市场先访谈／观察 10–15 位目标用户：看能否不用解释理解规则、是否误触、读图是否困难；该规模只用于可用性问题，不用于推断市场留存。
- 先无广告测试规则与关卡，再对胜出者随机分配低频广告组。样本充足才测多档频控，避免小样本切太多组。
- 记录安装渠道、国家、设备档位、在线状态、规则首次理解、关卡尝试／失败、退出点、提示／撤销、广告请求／填充／展示／奖励、崩溃／ANR和存档恢复。

### 阶段 C：软启动与停止条件

以下是**内部建议筛选门槛，不是行业事实或收益承诺**，应优先校准到公司已验证产品的同国、同渠道基线：

|维度|建议初始门槛／判定|
|---|---|
|上手|目标用户无需口头解释完成前 3 关比例 ≥80%；同时核查误触和真正理解，不能仅以通关数判断|
|小规模留存筛选|D1 ≥30%、D7 ≥10% 可作为初筛目标；连续优化后 D1 <20% 或 D7 <5% 且无明确技术／归因原因，优先停止；中间区间只给一次明确改版机会|
|可用性与稳定性|目标低端机可完成连续关卡；无广告返回丢档／卡死；crash-free users ≥99.5% 作为初始技术目标，短期小样本不够则不宣称已达标|
|广告损伤|与无广告或低频随机对照比较留存、退出、会话与净收入；不因曝光增加就判成功|
|商业化|取得分国实际 eCPM、填充、有效曝光/DAU 与 CPI；在预定回收周期内有可信的净 LTV>CPI 才扩大投放|

每个“玩法×国家”可先准备约 500–1,000 个有效安装作为方向筛查，等 cohort 满 7 天再看 D7；这不保证能检出小差异。需报告置信区间，根据预计差异计算后续样本。若预算达不到，不硬切多国家、多变体；**减少实验数量比制造不可靠结论更重要**。

D1/D7 采用固定的安装 cohort 日留存定义，统一时区与反作弊口径；不要混用滚动留存。七天数据也不能完整证明长期 LTV，应继续观察 D14/D30，再决定扩大投入。

### 建议执行顺序

1. 补公司真实国家权重与渠道数据。
2. 两个原型并行或顺序完成，具体取决于团队人力；只进行小规模理解／性能测试。
3. 留下一强一对照进行留存试验；如果三消规则门槛不合适，使用两张配对替换，不持续加模式。
4. 胜出玩法接广告试验与净收益验证，再形成正式 PRD、排期和投放预算。

## 九、下一轮最需要的公司输入

1. **市场与渠道：** 实际发布国家及 DAU／新增占比；自然量、买量、预装或交叉推广分别占多少。
2. **历史基线：** 已验证 Bubble Shooter／俄罗斯方块在各国的 D1/D7/D30、时长、广告 ARPDAU、填充率、CPI及低端机性能；本轮不重复选它们，但要用它们做比较基线。
3. **研发约束：** 团队人数、引擎／原生技术、是否有现成广告与关卡框架、单项目预算和验证周期。
4. **Apollo 导出：** 按国家、包名、日期提供最近 28／90 天榜单、DAU/MAU及可用的新增／留存／时长；若只能截图，请包含国家、时间范围、指标名、单位和前后排名。无需提供账号密码。

## 十、交付与证据文件说明

- 本报告：`IAA选品报告_非洲南亚_2026-09-21.md`。
- `research/puzzle-rankings-2026-09-18.csv`：七国 Puzzle 公开页面共 357 条样本，分列 S/U、包名和来源。每国页面返回 51 条；**不是每国完整榜单，也不一定是 Store Top 51**，因为部分页面按 U 排序。空排名表示数据缺失，不是零。
- `research/public/rank-summary.md`：核心竞品双口径摘录。
- `research/public/puzzle-rankings.json` 及同目录 HTML/TXT：本轮采集原始结构与可读文本。动态网页未来可能变化，应以留存快照和访问日复核。
- 地区补充记录：`research/africa-evidence.md`、`research/south-asia-evidence.md`。

**第一轮建议：先用箭头解阻争取新的产品机会，用槽位三消做第二原型；以两张配对／分类作为替补，以本地 Ludo／Carrom／Domino 保留地区化产品线。该排序需与后续音游、纸牌专项候选共同评审，并非最终立项决定。**

## 十一、核心参考产品：中文名称与商店地址

以下中文均为便于讨论的**中文说明名／常用译名，未确认是发行商官方中文名**；以原名、开发商及包名区分同名产品。商店可能根据访问地区显示其他语言或不同副标题。

|中文说明名|商店原名|开发商|Google Play|
|---|---|---|---|
|箭头解谜：点击解阻|Arrow Puzzle: Tap Puzzle Games|Easybrain|[打开商店](https://play.google.com/store/apps/details?id=com.easybrain.arrow.puzzle.game)|
|箭头迷阵 GO|Amaze GO!|Oakever Games|[打开商店](https://play.google.com/store/apps/details?id=com.oakever.arrows)|
|图块探索：三张配对|Tile Explorer - Triple Match|Oakever Games|[打开商店](https://play.google.com/store/apps/details?id=com.oakever.tiletrip)|
|图块俱乐部|Tile Club - Match Puzzle Games|GamoVation|[打开商店](https://play.google.com/store/apps/details?id=com.gamovation.tileclub)|
|维塔麻将：单人配对|Vita Mahjong|Vita Studio|[打开商店](https://play.google.com/store/apps/details?id=com.vitastudio.mahjong)|
|彩球分类谜题|Ball Sort Puzzle - Color Game|Guru Puzzle Game|[打开商店](https://play.google.com/store/apps/details?id=ball.sort.puzzle.color.sorting.bubble.games)|
|倒水分类：颜色谜题|Water Sort: Color Puzzle Game|IEC Global|[打开商店](https://play.google.com/store/apps/details?id=com.gma.water.sort.puzzle)|
|颜色水分类|Water Sort: Color Match|FunForge Studios|[打开商店](https://play.google.com/store/apps/details?id=com.water.sort.puzzle.game.color.magic.free)|
|鲁多之王|Ludo King|Gametion|[打开商店](https://play.google.com/store/apps/details?id=com.ludo.king)|
|尼日利亚鲁多|Naija Ludo|Tonielrosoft|[打开商店](https://play.google.com/store/apps/details?id=com.tonielrosoft.classicludofree)|
|卡罗姆弹盘|Carrom Pool: Disc Game|Miniclip|[打开商店](https://play.google.com/store/apps/details?id=com.miniclip.carrom)|
|多米诺骨牌|Dominoes|Loop Games|[打开商店](https://play.google.com/store/apps/details?id=com.LoopGames.Domino)|
