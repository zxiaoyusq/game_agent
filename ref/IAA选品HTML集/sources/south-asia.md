# 南亚 Android IAA 休闲玩法公开证据核查

调研访问：2026-09-21，约16:34—16:56（UTC+08）。最初遵循不建文件；本文件按委派方后续明确更新要求生成。没有开始开发。

## 1. 结论及证据边界

- **低门槛、低联网成本的首轮验证优先：Arrow/Tap Away、Ball Sort；Tile Match可作主线程已有证据的对照。** 本分报告独立核实三国 Arrow 总游戏免费商店排名均第3；Ball Sort 巴基斯坦第12、孟加拉国第7。它们不是 Bubble Shooter，也不是俄罗斯方块/Block Blast 式落块或摆块消行。
- **区域差异化：Carrom 优于再做一款泛 Ludo。** Carrom Pool 在印度 Games 免费商店榜第6、孟加拉国第10；巴基斯坦 Sports 免费榜第6。Ludo 的跨国需求证据非常强，但头部品牌、好友关系和在线大厅形成竞争壁垒。
- **轻板球降为第二阶段。** Cricket League 的 Sports 免费榜印度第3、巴基斯坦第5、孟加拉国第22，有现实需求，但不能从“南亚喜欢板球”直接推导小游戏易成功；击球/投球、3D反馈、在线同步比抽象单人解谜复杂。
- **传统牌/棋须分国家、分受众。** 孟加拉国 Bead 16 棋盘免费榜第3值得单独小测；29/Callbreak有现成用户证据，却有叫分、将牌、搭档与计分门槛，不宜当做完全新手产品的第一优先。
- 本次**没有可核实 DAU 数值、广告收入、eCPM、留存、买量成本或付费转化率**。高DAU仅为待验证潜力判断。榜单高位、累计下载大、Contains ads，均不能单独证明IAA盈利。

## 2. 数据获取及最关键的口径陷阱

按要求使用 web_search/web_fetch。Similarweb 与 Google Play 的 web_fetch 返回HTTP200，但正文被截断；AppBrain请求失败，SensorTower报告PDF链接能发现但web_fetch不支持PDF正文，因此没有引用它们的未读数字。随后以Node原生fetch只读获取同一公开URL完整HTML，提取公开页面文本与页面自带 `layout.data.apps`，并逐项检查字段；没有登录或绕过付费墙。

**全部下列 Similarweb 榜单日期：2026-09-18。**

- `S` = 页面公开数据字段 `storeRank`，所选 Google Play / 国家 / 类别 / Top Free Apps 的商店排名。它是免费商店榜，不是收入榜，也不是明确下载量。
- `U` = `usageRank`。印度页面可见列表主要按U排序，**即使URL以 `top-free/` 结尾也不能把可见序号当S**。
- HTML中对应tooltip原文：`The usage rank is based on a mixture of current installs and active users over a 28-day period. Results are shown for the selected country and category`。因此U是当前安装与28天活跃用户混合形成的使用排名，**不是DAU排名，也不是DAU数值**。
- Store tooltip：`App's store ranking in the chosen store, country, category and leader board, updated daily`。
- 巴基斯坦/孟加拉国可见表为Store Rank，公开JSON的U为0，本报告记作“—/不可得”，**不能称第0名**。部分印度产品S也是0，亦记缺失。
- SEO meta-description含DAU、MAU等词，不构成该指标已公开的证据。
- 例证：印度Games中 Candy Crush Saga 的 U=3而S=22；Tile Explorer U=9而S=44；Cricket League U=48而S=85。直接抄可见列表会严重混淆。
- 以下S值包含从公开HTML自带数据读取的字段，并不声称所有S值都在当前表格默认可见列中展示。

## 3. 国家及榜单证据

### 3.1 Games：总游戏类 Top Free Apps

来源：[印度](https://www.similarweb.com/top-apps/google/india/games/top-free/)；[巴基斯坦](https://www.similarweb.com/top-apps/google/pakistan/games/top-free/)；[孟加拉国](https://www.similarweb.com/top-apps/google/bangladesh/games/top-free/)。日期均2026-09-18。

|国家|产品|免费商店S|使用U|
|---|---|---:|---:|
|印度|Ludo King|2|2|
|印度|Arrow Puzzle: Tap Puzzle Games|3|5|
|印度|Carrom Pool: Disc Game|6|6|
|印度|Tile Explorer - Triple Match|44|9|
|印度|Vita Mahjong|198|14|
|印度|Callbreak.com - Card game|182|18|
|印度|Card Game 29|—|22|
|印度|Tile Club - Match Puzzle Games|151|26|
|印度|Cricket League|85|48|
|巴基斯坦|Yalla Ludo - Ludo&Jackaroo|2|—|
|巴基斯坦|Arrow Puzzle: Tap Puzzle Games|3|—|
|巴基斯坦|Ludo King|4|—|
|巴基斯坦|Subway Surfers|7|—|
|巴基斯坦|Ludo STAR: Online Dice Game|10|—|
|巴基斯坦|Ball Sort Puzzle - Color Game|12|—|
|巴基斯坦|Tile Club - Match Puzzle Games|39|—|
|孟加拉国|Ludo King|2|—|
|孟加拉国|Arrow Puzzle: Tap Puzzle Games|3|—|
|孟加拉国|Snake Lite - Snake Game|6|—|
|孟加拉国|Ball Sort Puzzle - Color Game|7|—|
|孟加拉国|Carrom Pool: Disc Game|10|—|
|孟加拉国|Tile Club - Match Puzzle Games|18|—|
|孟加拉国|Yalla Ludo - Ludo&Jackaroo|20|—|

未出现在上述摘录中不等于没有排名；本表是候选相关摘录，不是完整榜单。某产品未进入读取范围也不能推定其精确名次。

### 3.2 Board：棋盘类 Top Free Apps

来源：[印度Board](https://www.similarweb.com/top-apps/google/india/games/board/top-free/)；[巴基斯坦Board](https://www.similarweb.com/top-apps/google/pakistan/games/board/top-free/)；[孟加拉国Board](https://www.similarweb.com/top-apps/google/bangladesh/games/board/top-free/)。日期均2026-09-18。

|国家|产品|免费商店S|使用U|
|---|---|---:|---:|
|印度|Ludo King|1|1|
|印度|Vita Mahjong|8|2|
|印度|Ludo（Yarsa）|9|4|
|印度|Bead 16 - 16 Guti Board Game|15|10|
|印度|Carrom Lite-Board Offline Game|27|22|
|巴基斯坦|Yalla Ludo|1|—|
|巴基斯坦|Ludo King|2|—|
|巴基斯坦|Ludo STAR|3|—|
|巴基斯坦|Carrom - A Disc Board Game（Brainit）|20|—|
|巴基斯坦|Carrom Lite-Board Offline Game|36|—|
|孟加拉国|Ludo King|1|—|
|孟加拉国|Yalla Ludo|2|—|
|孟加拉国|Bead 16 - 16 Guti Board Game|3|—|
|孟加拉国|Carrom Go-Disc Board Game|6|—|
|孟加拉国|Vita Mahjong|7|—|
|孟加拉国|Carrom Lite-Board Offline Game|9|—|
|孟加拉国|Carrom Pro: Bangladesh|18|—|
|孟加拉国|Sholo Guti: Bead 16 Char Goti|35|—|

重要：**Carrom Pool在Google Play归Sports而非Board**，不能只看Board就判断它缺乏市场需求。Bead16在孟加拉国第3是Board子榜，不是Games总榜第3。

### 3.3 Sports：体育类 Top Free Apps

来源：[印度Sports](https://www.similarweb.com/top-apps/google/india/games/sports/top-free/)；[巴基斯坦Sports](https://www.similarweb.com/top-apps/google/pakistan/games/sports/top-free/)；[孟加拉国Sports](https://www.similarweb.com/top-apps/google/bangladesh/games/sports/top-free/)。日期均2026-09-18。

|国家|产品|免费商店S|使用U|
|---|---|---:|---:|
|印度|Carrom Pool|1|1|
|印度|Cricket League|3|2|
|印度|Real Cricket GO|24|13|
|印度|Stick Cricket Super League|90|36|
|印度|World Cricket Championship 1|73|43|
|巴基斯坦|Real Cricket|3|—|
|巴基斯坦|Cricket League|5|—|
|巴基斯坦|Carrom Pool|6|—|
|巴基斯坦|Real Cricket GO|11|—|
|孟加拉国|Carrom Pool|3|—|
|孟加拉国|Cricket League|22|—|
|孟加拉国|World Cricket Championship 2|23|—|
|孟加拉国|Real Cricket GO|44|—|

### 3.4 Cards：纸牌类 Top Free Apps

来源：[印度Cards](https://www.similarweb.com/top-apps/google/india/games/cards/top-free/)；[巴基斯坦Cards](https://www.similarweb.com/top-apps/google/pakistan/games/cards/top-free/)；[孟加拉国Cards](https://www.similarweb.com/top-apps/google/bangladesh/games/cards/top-free/)。日期均2026-09-18。

|国家|产品|免费商店S|使用U|
|---|---|---:|---:|
|印度|Callbreak.com|1|1|
|印度|Card Game 29|10|2|
|印度|Callbreak Master|3|3|
|巴基斯坦|Callbreak.com|19|—|
|孟加拉国|Card Adda Spades Callbreak 29|6|—|
|孟加拉国|Callbreak - Card Game Offline|7|—|
|孟加拉国|Card Game 29|8|—|
|孟加拉国|Callbreak.com|17|—|

## 4. Google Play产品核查

访问同为2026-09-21；以下URL明确 `hl=en&gl=IN`。**下载徽章是应用全球累计下载档位，不是印度下载量、不是当月下载、更不是DAU。** 星级/评论数随时间和商店展示口径变化，仅作当次观测。下列产品均显示 `Contains ads` 和 `In-app purchases`，这证明广告与内购同时存在，不证明广告收入占比或纯IAA可行。

|产品及来源|累计下载徽章|评分/评论|页面更新日期|已读机制与成本相关事实|
|---|---|---|---|---|
|[Carrom Pool](https://play.google.com/store/apps/details?id=com.miniclip.carrom&hl=en&gl=IN)|500M+|4.6 / 7.95M|2026-08-31|物理弹射入袋；支持离线、同设备、在线；3种模式、2v2；语音/视频仅Carrom Pass；每周限时活动|
|[Ludo King](https://play.google.com/store/apps/details?id=com.ludo.king&hl=en&gl=IN)|1B+|4.0 / 10.3M|2026-09-08|离线电脑/本地轮流操作、在线多人、Quick mode、低端机支持；月度赛季、社交聊天|
|[Cricket League](https://play.google.com/store/apps/details?id=com.miniclip.cricketleague&hl=en&gl=IN)|100M+|4.5 / 3.77M|2026-09-07|在线3D多人；2 overs、宣称3—5分钟；25+角色、投球变种；列出Mumbai/Karachi/Dhaka球场；宣称2G/3G顺畅但未独立实测|
|[Bead 16](https://play.google.com/store/apps/details?id=com.alignit.sixteenbead&hl=en&gl=IN)|10M+|4.2 / 87.1K|2026-08-25|跳吃对方全部16子；也有12子变体；离线CPU、三个难度、双人、在线与聊天|
|[Card Game 29](https://play.google.com/store/apps/details?id=com.zlevelapps.cardgame29&hl=en&gl=IN)|10M+|4.2 / 107K|2026-09-16|32张牌、四人两队、叫分/将牌/墩；离线AI、好友邀请和补机器人；支持英/印地/孟加拉语；多种规则开关|
|[Callbreak.com](https://play.google.com/store/apps/details?id=io.teslatech.callbreak&hl=en&gl=IN)|100M+|4.3 / 546K|2026-09-17|52牌四人叫墩、黑桃将牌；离线AI、在线/好友房、速度与自动出牌|
|[Arrow Puzzle](https://play.google.com/store/apps/details?id=com.easybrain.arrow.puzzle.game&hl=en&gl=IN)|50M+|4.5 / 1.39M|2026-09-04|单人/离线；沿箭头方向无阻挡才能移除；生命与提示；宣称数百手工关、每日挑战|
|[Ball Sort](https://play.google.com/store/apps/details?id=ball.sort.puzzle.color.sorting.bubble.games&hl=en&gl=IN)|50M+|4.7 / 949K|2026-09-16|离线；把顶层球移到同色且有空间的瓶；undo、加瓶、重开；宣称数千关|

Ludo King下载注意：Google Play结构化徽章是**1B+**，厂商描述另写 **2 Billion Downloads**。后者没有在已读正文中清晰拆出平台/地区/统计口径，不应拿它替代Android徽章。

GP当次卡片另显示Callbreak“#1 top free card”、29“#9 top free card”、Carrom“#1 top free sports”、Cricket“#3 top free sports”、Ludo“#1 top free board”、Arrow“#1 top free puzzle”。这些是访问时gl=IN页面展示，与Similarweb 09-18快照不必相同；本报告主体表采用日期更明确的Similarweb，不把29的9与10混为同一时点矛盾。

## 5. 六个候选的取舍（下述成本和IAA设计均为分析判断）

|候选|优点、需求证据|主要缺点|IAA设计适配|联网及内容成本|建议|
|---|---|---|---|---|---|
|1. Arrow / Tap Away|三国Games免费S均3；一句话可解释规则，少文字，适合低本地化门槛|近期高榜不保证长期留存；关卡同质化；难度、可解性与广告密度需平衡|关后插屏；自愿看广告获提示/续命；不要连续打断思考|单机可玩，业务服务器低；中等关卡生成、求解验证与难度标定成本|优先MVP假设，不抄品牌/关卡|
|2. Ball Sort|PK Games S12、BD S7；明确离线，顶球移瓶易懂；不同于bubble shooter|同质产品多；深关搜索负担；色弱可读性，随机局面可解性|额外空瓶、撤回等自愿激励；关后频控插屏|低联网；中低关卡资产量，但求解器、反死局验证是实成本|适合作为低成本对照；不称南亚传统文化|
|3. Carrom（优先Disc Pool简化变体）|IN Games S6/U6、BD S10；PK Sports S6；瞄准蓄力到入袋视觉反馈直观|物理手感与AI难度有门槛；传统queen/cover规则比简化入袋更难；头部竞技生态成熟|单人挑战后插屏、外观/挑战门票激励；公平PvP中不卖广告换瞄准优势|离线AI/本地双人中等；实时匹配、断线重连、防作弊变高；关卡少但物理测试多|区域差异化首选，先离线挑战验证|
|4. Ludo快速局|三国S分别2/4/2，跨国需求证据最直接；离线/本地/Quick mode已有标杆|头部品牌与社交网络强，普通克隆难获客；随机等待、长局降低广告节奏|整局结算插屏、外观奖励；避免每次掷骰广告和看广告改点数|离线低，好友房/匹配中，语音与大社群审核运维高；关卡内容成本低|需求强但进入壁垒高，不建议泛克隆|
|5. 传统棋/牌：Bead16为孟加拉首测，29/Callbreak为熟客备选|BD Board Bead16 S3；BD Cards29 S8；IN Cards Callbreak S1/U1；可离线复玩|不是一个可全区通用的玩法：Bead16战略学习中等；29/Callbreak叫分计分门槛明显更高，规则方言差异|单人局后插屏、训练提示激励；竞技局内避免打断与破坏公平|棋类AI中等，合作纸牌AI与规则组合更复杂；无实时内容也可复玩，在线房间成本可控|需先做当地用户规则访谈，不能宣传“所有南亚用户天然会玩”|
|6. 轻板球：单击击球/短over挑战|Cricket League Sports S：IN3/PK5/BD22；标杆已把比赛缩为3—5分钟|完整板球术语规则不如抽象谜题低；打击判定、镜头、3D动画/素材更贵，赛事/球星授权风险|每局结束插屏、单人重试激励；不是每球广告|单机击球中等；还原在线投打与角色成长较高；内容量/设备优化高于2D谜题|第二阶段实验；不从Sports子榜推断Games前五|

**Tile Match补充：**本次独立证据有IN Tile Explorer Games S44/U9、Tile Club S151/U26，PK Tile Club S39、BD S18。这支持长期使用与跨国需求线索，但本分报告没有读取它们GP完整机制与下载徽章，因此不补写未读数据。主线程若另有完整核查，可用Tile Match替换六候选中的较低优先级项。Tile Match是取相同图块消除，不等同摆方块消行；仍须核实玩法避免只是Block Puzzle换皮。

## 6. 文化判断：只说来源支持的范围

1. Ludo/Carrom跨国需求用**实际国家榜单**支持，不以“南亚人都喜欢社交/都爱棋盘”替代证据。GP的“family/childhood”是厂商定位文案，不是人口调查。
2. Bead16的孟加拉国Board第3比泛泛文化断言更扎实。其GP厂商称12子变体在Bangladesh叫Baro Guti；不要误说16子本体只有这一名称，也不要把厂商“South-East Asia”营销地理表述当权威区域分类。
3. 29已有孟加拉语支持和BD Cards第8，是当地适配线索；来源不证明全民熟悉。规则较复杂已从GP具体规则核实。
4. Callbreak GP厂商称在India/Nepal流行，不能外推PK/BD同等强度。三国Cards榜实际差异为IN1、PK19、BD17。
5. Cricket League列Mumbai、Karachi、Dhaka场景是产品的本地化事实，不等于证明某国所有用户热爱板球；三国Sports排名差异足以支持分国测试。
6. 不把宗教、民族、收入、识字水平或“低端用户”当无来源人群标签。低文字、离线和低端机优化是产品兼容策略，而不是人口特征断言。

## 7. IAA与上线验证底线

- 离线可玩不等于离线能加载广告。应在无广告库存/无网络时保持核心可玩；广告缓存、奖励一致性、隐私同意必须按SDK规则实现。
- 广告位选择以上均为设计建议，**不是声称竞品已使用该精确广告位或频率**。
- 不建议从Ludo现金奖励产品、Teen Patti/rummy现金玩法抄经济系统；真人货币、抽奖与未成年人合规需单独法务审查。传统免费牌棋不应自动等同赌博，但也不能忽视经营方式带来的风险。
- 国家分别测试D1/D7/D30留存、DAU/MAU、时长与自然日启动次数、每DAU可展示广告量、广告完成率、无网占比、设备帧率、崩溃率、IAA ARPDAU、CPI和LTV；现有公开榜单不能替代这些。
- 顺序建议：Arrow与Ball Sort/Tile Match做低成本主线对照；Carrom离线挑战做区域差异化对照；Ludo/传统牌棋/轻板球仅在对应受众验证后加大投入。
