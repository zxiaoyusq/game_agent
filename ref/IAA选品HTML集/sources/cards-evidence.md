# 纸牌扩展核查：七国 Android IAA 机会

访问：2026-09-21 16:56—17:01（UTC+08）。排名统一为 `snapshotDate=2026-09-18T00:00:00`。本次只做公开研究，没有开发产品、登录、绕过鉴权或实机测试。

## 结论先行

**应提升纸牌优先级，但不是把所有传统牌都提成同一优先级。** 上轮用29/Callbreak的规则门槛概括纸牌，漏掉了可离线、无需对手AI的 Klondike 单人接龙，以及尼日利亚 Whot、巴基斯坦/孟加拉国 Spades 的独立证据。

- **P0验证：Klondike 单人接龙**，重点南非、肯尼亚、巴基斯坦，兼测埃及。这里P0指值得进入首轮小规模验证，并非已证明它的DAU、LTV或盈利胜过解谜。一个相同包名在七国Cards都有排名，胜过仅凭全球累计安装推市场。
- **区域高优先：尼日利亚 Whot、印度 Callbreak**，有Games总榜补强。Whot用数字/图形匹配的入门层可降低新手门槛；Callbreak仍优先面向已经懂叫墩的用户。
- **P1定向：巴基斯坦/孟加拉国 Spades；印度/孟加拉国29；埃及Basra。** Basra由全榜发现，不是预设名单；先验证规则偏好、教程、AI与局长。
- **扩展而非首发大合集：Spider 1花色，再看FreeCell。** 复用牌面不等于零成本；规则、可解性、撤回和布局必须分别验证。

## 1. 数据口径和七国来源

S = Similarweb公开HTML `layout.data.apps[].storeRank`，所选国家 **Cards分类 Top Free** 的商店排名。U = `usageRank`，官方解释为当前安装与28天活跃用户的混合排名，**非DAU排名，更非DAU人数**。字段0转换为缺失。只采用snapshotDate，不采用dateModified。

七国Cards公开样本分别为：印度51、巴基斯坦51、孟加拉国51、尼日利亚44、肯尼亚51、南非51、埃及51条。名单并非完整商店排名；未出现不能推断精确名次或无需求。IN/ZA/EG含U，PK/BD/NG/KE这批U不可得；榜面默认排序不能直接当S。

|国家|日期|Cards 来源URL|
|---|---|---|
|印度 IN|2026-09-18|https://www.similarweb.com/top-apps/google/india/games/cards/top-free/|
|巴基斯坦 PK|2026-09-18|https://www.similarweb.com/top-apps/google/pakistan/games/cards/top-free/|
|孟加拉国 BD|2026-09-18|https://www.similarweb.com/top-apps/google/bangladesh/games/cards/top-free/|
|尼日利亚 NG|2026-09-18|https://www.similarweb.com/top-apps/google/nigeria/games/cards/top-free/|
|肯尼亚 KE|2026-09-18|https://www.similarweb.com/top-apps/google/kenya/games/cards/top-free/|
|南非 ZA|2026-09-18|https://www.similarweb.com/top-apps/google/south-africa/games/cards/top-free/|
|埃及 EG|2026-09-18|https://www.similarweb.com/top-apps/google/egypt/games/cards/top-free/|

## 2. 六个有价值的产品参考

前三项中文标题来自此次GP `hl=zh_CN` 官方商店页；后三项使用**说明性译名，不冒充官方中文名**。精确链接固定包名，避免同名误认。

|中文名及类型|当前英文原名 / 开发者|精确 Google Play|
|---|---|---|
|经典纸牌接龙游戏 - Solitaire（官方中文标题；玩法为Klondike）|Solitaire - Classic Card Games / Guru Puzzle Game|https://play.google.com/store/apps/details?id=solitaire.patience.card.games.klondike.free|
|Callbreak.com - 纸牌游戏（官方中文标题）|Callbreak.com - Tash Game / Teslatech|https://play.google.com/store/apps/details?id=io.teslatech.callbreak|
|黑桃王 - 接龙纸牌游戏（官方中文标题，**不是Klondike接龙**）|Spades Solitaire - Card Games / Topy Games|https://play.google.com/store/apps/details?id=com.spades.solitaire.online.plus.offline.free.card.games|
|尼日利亚 Whot 出牌游戏（说明性译名）|Naija Whot / Tonielrosoft|https://play.google.com/store/apps/details?id=com.tonielro.naijawhotfree|
|29点搭档纸牌（说明性译名）|Card Game 29 / Z Level Labs|https://play.google.com/store/apps/details?id=com.zlevelapps.cardgame29|
|埃及巴斯拉吃牌（阿语版）（说明性译名）|Egyptian Basra Arabic / TheDarkSeraph|https://play.google.com/store/apps/details?id=com.abyadtherock.egybasraarab|

Callbreak的Similarweb快照标题为“Callbreak.com - Card game”，当前IN英文GP标题为“Tash Game”，同一包名，不是两款产品。Basra的zh_CN页面仍显示阿文“عشرة كوتشينة 3”，无已核实中文官方标题。

### 六产品国家 S/U 矩阵：全部为Cards分类，2026-09-18

`—`表示该字段缺失；`未见`表示未出现在此次公开样本，绝不等同于零排名或无用户。

|产品|IN S/U|PK S/U|BD S/U|NG S/U|KE S/U|ZA S/U|EG S/U|
|---|---:|---:|---:|---:|---:|---:|---:|
|Guru Klondike|22/11|4/—|16/—|11/—|2/—|2/2|9/10|
|Callbreak.com|1/1|19/—|17/—|未见|3/—|未见|未见|
|Topy Spades|5/6|1/—|2/—|未见|5/—|104/25|未见|
|Naija Whot|未见|未见|未见|2/—|未见|未见|未见|
|Card Game 29|10/2|未见|8/—|未见|18/—|未见|未见|
|Egyptian Basra Arabic|未见|未见|未见|未见|未见|未见|3/7|

### Games总榜：重新抓取七国，而非把上表当总榜

本次六主产品加四个比较品的总榜交叉检查只命中以下三项；日期仍为2026-09-18。

|国家/产品|Games S/U|来源|
|---|---:|---|
|印度 Callbreak.com|182/18|https://www.similarweb.com/top-apps/google/india/games/top-free/|
|印度 Card Game 29|—/22|https://www.similarweb.com/top-apps/google/india/games/top-free/|
|尼日利亚 Naija Whot|36/—|https://www.similarweb.com/top-apps/google/nigeria/games/top-free/|

**Guru Klondike在七国Games公开样本均未见**。不能写“南非/肯尼亚游戏总榜第二”，也不能用Cards第二证明全国大DAU。其他总榜来源见 `games-crosscheck.json`（同一URL规则，去掉 `/cards`）。

## 3. 规则、离线/AI、广告与本地化判断

以下规则/标签来自上述GP页面；门槛、成本与广告位为本研究的设计判断，并非竞品广告位实测。

|产品|核实的真实玩法与规则门槛|AI、联网与规则本地化|自然广告位与公平底线|
|---|---|---|---|
|Klondike|52牌；列内红黑交替递减，基座按花色A→K，空列仅K。不熟悉扑克牌的人仍需学花色、A/J/Q/K顺序、两种相反堆叠方向；比叫墩/搭档牌容易教，不等于零门槛|GP有Offline标签、单人、提示/撤回、每日挑战、抽3张模式、Joker；没有对手AI/实时大厅成本。建议先做抽1张、合法落点高亮、短教程、免费重发/基本撤回。原厂承认部分牌局无解；不能为了广告故意强制死局|完成/主动结束一局后频控插屏，额外提示可选激励；不要每次移动/撤回打断。原厂GP回复明确依赖广告并售去广告，但没有收入占比证据；可做广告优先机会，不称竞品纯IAA|
|Callbreak|52牌4人、每人13牌、各自叫1—13墩，黑桃恒将牌，未完成叫数罚分。**个人叫墩，不是29的两队合作**；需理解跟花、将牌、叫数风险|明确完全离线AI、在线多人、私人房、速度/自动出牌。开发者2026-08-31回复还明确同花可压必须压；不要仅凭营销把Call Bridge、Spades、Callbreak混成一套规则。地区规则应访谈/开关确认|整副13墩结算或离桌后插屏，不是每一墩/每次出牌；训练提示可激励，真人局不能广告换牌、看暗牌或加叫分优势。低文字界面不能代替规则教育|
|Spades|GP明确叫墩、黑桃将牌、Standard/NYC、单人/合作/竞争模式，**虽英文Solitaire、中文接龙，仍是吃墩对战**。nil/袋分/搭档配合使新手门槛高于Klondike|明确离线AI；正文泛称online，但未充分核实真人匹配/好友房具体能力，不能把“多人/竞争模式”必然写成实时联网。合作AI应会保护nil、避无意义抢墩，不能依靠全知暗牌。先单机训练再考虑联网|每副结算/退出后频控；无广告插入轮到用户或搭档等牌时。顶部只见Contains ads，评级处见In-Game Purchases，不能因缺少顶部IAP字样判纯IAA。公开评论质疑机器人/搭档AI，仅作质量风险线索，不是作弊事实|
|Whot|同图形或同数字出牌，先出完获胜；入门匹配较直观。该产品默认1=再出、2=下家取2、5=取3、14=General Market、8=跳过、20=指定图形；锦标赛星形计分翻倍。特殊牌增加中等门槛|QuickPlay对1个AI、锦标赛3个AI；好友在线或离线两人，勿承诺四人真人房。支持动作牌开关、数字配置和防守规则，正说明不能把一个“标准UNO换皮”通用于尼日利亚。两人离线具体连接方式未实测|QuickPlay整局结算较自然；锦标赛轮间适度，不在Pick2防守/连出时插屏。广告给外观或单人练习入口，不给真人额外特权。广告+IAP，已读描述未见充值赌注/提现声明，但不构成完整经营合规审计|
|29|32牌、四人两队、8张/人；J与9高价值，牌点J3/9=2/A1/10=1；叫16—29、设将、末墩可选额外1点。不是“普通扑克一眼懂”，新手需同时理解牌序、牌点、叫分与搭档|明确离线AI/在线邀请链接、满足条件可补机器人；英/印地/孟加拉语；Double、Re-double、Pair、7th Card Trump等开关。规则组合与搭档AI比单人接龙贵，适合熟客和当地合作验证|完整8墩后/局组结算；不可每一墩广告；不以广告改变真人叫分、牌序或暗牌信息。广告+IAP，无已读现金提现声明；不要把双倍叫分术语误判现金赌博|
|Basra|两人轮流出牌，吃相同牌或点数和；J/方块7清桌，Basra清台奖励及特殊计分。少叫分但有心算、抓牌组合与特例牌，陌生牌类用户门槛中等以上|商店Offline/Single player标签，正文明确服务器公房/私房、英阿语界面；**AI算法/难度未明确核实**。标题“阿语版”与埃及S3/U7支持定向试验，不支持“埃及人人熟悉”。阿语RTL/数字/例题应实测|整副牌结束、换桌或单机练习结束；不在计算抓牌时打断。只见Contains ads，未见IAP标签，不把缺失标签当纯IAA收入证明。16+ Strong Language/Users Interact与描述“all ages”相冲突，儿童定位要以商店评级/实际功能审慎评估|

共同要求：可解释的合法出牌提示；公开且稳定的本地规则；洗牌公平和机器人不读取对手隐藏信息的测试；掉线重连、托管与限时说明；没有广告库存时仍可结束/继续核心对局。**离线可玩不等于离线可以拉取广告**，离线用户不可全算可变现DAU。实时多人增加匹配、断线、反作弊和社交审核成本；不是主菜单加“好友”按钮那么简单。

## 4. 覆盖Spider / FreeCell / UNO / Hearts，为什么未都放进六主参考

### 单人接龙内部不能只看Klondike

- **Spider：蜘蛛纸牌（官方中文）/ Spider Solitaire，Easybrain**，`com.easybrain.spider.solitaire`。Cards IN **S43/U17**、ZA **S8/U21**、EG **S80/U8**。GP：同花K→A序列，1/2/4花色可选、提示/撤回、自动保存、Offline，广告+IAP。EG的U8是使用排名线索，不应因S80误判没有稳定用户。优先试1花色；4花色和长局不宜直接作为完全新手入口。
- **FreeCell：空当接龙 - 经典纸牌接龙游戏（官方中文）/ FreeCell Solitaire - Card Game，Fantasy Games Ltd**，`freecell.solitaire.free.cardgame.king.spades.klondike.no.ads.pro.patience`。ZA **S66/U5**。GP明确52张全明牌、8列、4自由格、红黑交替、按花色A→K、离线/编号牌局/无限撤回提示；广告+IAP。包名含`no.ads`不代表实际无广告。全明牌降低运气不透明感，但空位管理和多步规划更难，适合熟悉接龙的受众。
- 两个比较品都不在本次选中Games公开样本。它们支持做接龙产品家族/进阶选项，不证明七国全都比Klondike优先。

比较品GP证据：
https://play.google.com/store/apps/details?id=com.easybrain.spider.solitaire
https://play.google.com/store/apps/details?id=freecell.solitaire.free.cardgame.king.spades.klondike.no.ads.pro.patience

### UNO类：强参考，但非直接低成本纯IAA模板

UNO!™（中文常用“乌诺牌”，官方当前仍为UNO!™）同一包名`com.matteljv.uno`的Cards **IN2/9、PK2/—、BD4/—、NG21/—、KE1/—、ZA4/3、EG4/6**。这比只凭文化推断匹配出牌跨区需求更有价值。

GP明确实时对局、好友/房规、2v2、俱乐部、月度/赛事、广告+IAP含随机物品；没有核实Offline声明。Go Wild描述最高600倍投入的**游戏币**奖励，不能未经核实写成真实现金提现，也不能当成朴素纯IAA模型。品牌/牌面/素材不可照搬；可以研究“同色/同数字匹配+先出完”的低门槛结构，用原创视觉并核实当地特例牌，不假装正式授权UNO。与Whot也不能混淆牌组、动作牌映射和本地规则。

GP：https://play.google.com/store/apps/details?id=com.matteljv.uno

### Hearts：有样本，不作为本轮首选

Cards NG的Hearts（`com.hyilmaz.hearts`）S14；PK的Hearts: Classic Card Game（`com.hearts.solitaire.plus.offline.free.card.games`）S37；BD的Hearts Single Player - Offline（`com.zariba.viphearts.single`）S50；ZA AI Factory Hearts（`uk.co.aifactory.heartsfree`）S缺失/U43。**不同包名不能拼成同一产品跨国排名。** 本次没有继续GP深核这些Hearts产品，不补写其广告或离线能力。规则通常是避罚分（红心/黑桃Q）、有传牌/全收特殊策略；相较简单数字匹配同样需要教学，当前证据不足以挤掉主六项，不等于没有潜力。

### 不限预设名单带来的反例

EG Bonto S2/U1并非传统埃及扑克牌：GP实际为足球阵容卡牌、1v1、先5球/计时获胜、赛季与卡牌成长。它证明“Cards类别”含足球卡牌对战，**不能把整个Cards榜当传统纸牌规模**。ZA Pokémon、Yu-Gi-Oh等同理。Basra是真实传统吃牌，才纳入区域主参考。PK榜还见Bhabhi S3、Court Piece S18，未完成GP深核，留后续而非凭名称替换主参考。

## 5. 纯IAA机会与现金产品严格分开

- 六主参考中，Klondike/Callbreak/29/Whot都明确广告+IAP；Spades广告+评级内购提示；Basra只见广告标签。**没有任何一项公开收入构成可以证明“纯IAA竞品”。** 所谓纯IAA机会，指可选择无赌注/无提现、广告优先的产品设计路线，而不是已经测得的商业模式结论。
- Guru Klondike描述明确“not a social casino”“without money in and money out”，是最直接的无现金进出声明。其他主参考未读到现金声明不等于完整金融合规核验。
- **尼日利亚Cards S1 Waje Casino**，GP原文明确“real-money gambling app”、充值提现、18+、Real Gambling/Paid Contests；不纳入纯IAA需求证明。来源：https://play.google.com/store/apps/details?id=com.hfhy.waje.special 。其自称牌照不代表本研究核验了监管合法性。
- **尼日利亚Cards S9 Whot Money: Win Cash**，GP明确赢币可换真钱、提现。是现金激励产品，不把它和Naija Whot混作一个需求证据；本研究没验证实际兑现。来源：https://play.google.com/store/apps/details?id=com.nicademia.whotmoney 。更不能仅因为它当前3+评级就推断适合儿童。
- PK等市场的casino/real win名称仅可视作进一步审核信号，未经GP核验不下同类定论。

## 6. 下一步如何判断“应提升多少”

先分国家、分懂牌/不懂牌用户做小测：教程完成、首局独立完成、误触/非法出牌、时长分布、D1/D7、广告后退局、每活跃日局数、真实在线可曝光占比、IAA ARPDAU与CPI/LTV。用Klondike和原来低门槛解谜做同口径对照；NG再测Whot，IN再测Callbreak，PK/BD试Spades，BD/IN的29与EG Basra留给熟客分层。不能从累计安装、子榜名次或孤立评论得到这些指标。

## 7. 保存的可复核材料

- `cards-rankings.json`：七国Cards全部公开样本，保存包名/标题/开发者/S/U、URL、snapshotDate、抓取时间，未存庞大HTML。
- `cards-rankings-summary.txt`：人读排名；已用read检查。
- `games-crosscheck.json`：七国Games交叉检查、样本大小、命中与未观测包名。
- `games-all-public.json` / `games-all-public.txt`：应主线程扩展玩法池要求补存的七国Games全部公开数组（各51条，不是全量商店榜），标题、包名、S/U、URL、snapshotDate俱全；文本已read抽检。
- `play-evidence.json` 与 `play-*.txt`：十个主/比较产品公开GP标题、结构化数据、描述及标签；注意原始`inAppPurchases`只是是否找到字面字符串，不是无内购判断。
- `chinese-title-check.json`：官方中文商店标题查询结果；已read检查。
- `product-facts.json`：将顶部广告/IAP和评级内购提示分开，合并中文名类型、七国S/U及URL；已read抽检。
- `cash-risk-check.json` / `risk-*.txt`：Waje、Whot Money官方现金声明；已read检查。
- `fetch-*.mjs` / `build-facts.mjs`：均以write创建的只读公开页面抓取和证据整理脚本，不是产品开发。
