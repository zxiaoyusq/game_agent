# 非洲 Android IAA 游戏公开证据核查

访问时间：2026-09-21（系统时区 +08:00）。覆盖尼日利亚、肯尼亚、南非、埃及。独立使用 web_search/web_fetch 发现及核对公开网址；因工具正文截断，以 Node fetch 读取相同公开 HTML，无登录、无付费接口。此前未创建文件，本文件按父代理后续明确要求保存。

## 1. 必须保留的数据口径

- 下表 S = Similarweb 公开 HTML `layout.data.apps[].storeRank`，页面选择 Google Play / Android / Top Free；U = `usageRank`，是 Similarweb 使用排名，**不是 DAU 人数**。
- NG/KE 页面 `orderBy=store-rank`、可见表头 Store Rank；ZA/EG 即使 URL 也是 `/top-free/`，实际默认 `orderBy=app-index`、可见表头 Usage Rank。不能把数组顺序或 JSON-LD `position` 当 S。
- 所有已读国家 Games/Board 页 `snapshotDate=2026-09-18T00:00:00`，标题 September 18；但 JSON-LD `dateModified=2026-10-18T00:00:00.000Z` 与快照有一月矛盾。采用 snapshotDate 和访问时间，不采用异常 dateModified。
- `0` 不算名次；NG/KE U 未形成可用数据，标“—”。不存在于这次截取列表，不等于不在完整榜或没需求。
- 累计下载、评论数、排名不代表 DAU；使用排名也不是公开 DAU 人数。没有核实 DAU、收入、eCPM、留存或广告填充率。
- Google Play 的 Offline 是开发者声明/商店标签，不是低端机实测；Contains ads + IAP 不意味着纯 IAA。

## 2. 国家 Games 总榜证据

全部为 2026-09-18 快照，2026-09-21 访问。S、U 均按公开字段原样记录。

### 尼日利亚
来源：https://www.similarweb.com/top-apps/google/nigeria/games/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Vita Mahjong | 9 | — | com.vitastudio.mahjong |
| Arrow Puzzle: Tap Puzzle Games | 11 | — | com.easybrain.arrow.puzzle.game |
| Naija Ludo | 15 | — | com.tonielrosoft.classicludofree |
| Naija Whot | 36 | — | com.tonielro.naijawhotfree |
| Water Sort: Color Match | 39 | — | com.water.sort.puzzle.game.color.magic.free |
| Dream League Soccer 2026 | 1 | — | com.firsttouchgames.dls7 |
| Football League 2026 | 4 | — | com.football.soccer.league |
| eFootball | 5 | — | jp.konami.pesam |

完整足球模拟产品仅证明题材需求，不能直接证明轻足球需求。

### 肯尼亚
来源：https://www.similarweb.com/top-apps/google/kenya/games/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Vita Mahjong | 12 | — | com.vitastudio.mahjong |
| Tile Club - Match Puzzle Games | 22 | — | com.gamovation.tileclub |
| Water Sort: Color Match | 29 | — | com.water.sort.puzzle.game.color.magic.free |
| Arrow Puzzle: Tap Puzzle Games | 42 | — | com.easybrain.arrow.puzzle.game |
| Ball Sort Puzzle - Color Game | 45 | — | ball.sort.puzzle.color.sorting.bubble.games |
| Ludo Classic | 53 | — | com.whiture.apps.ludoorg |
| eFootball | 4 | — | jp.konami.pesam |
| Football League 2026 | 5 | — | com.football.soccer.league |
| Dream League Soccer 2026 | 6 | — | com.firsttouchgames.dls7 |

公开数组含部分缺号，不能以数组下标重建名次。Ball Sort 虽包名含 bubble，是否排除应看玩法：容器排序不是 Bubble Shooter；但与 Water Sort 应合并为同类，不算独立创新赛道。

### 南非
来源：https://www.similarweb.com/top-apps/google/south-africa/games/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Ludo King | 8 | 14 | com.ludo.king |
| Vita Mahjong | 30 | 19 | com.vitastudio.mahjong |
| Soccer Superstar | 108 | 32 | com.soccer.score.star |
| Ludo（Yarsa） | 95 | 44 | io.yarsa.games.ludo |
| Tile Explorer - Triple Match | 120 | 45 | com.oakever.tiletrip |
| eFootball | 18 | 3 | jp.konami.pesam |
| Dream League Soccer 2026 | 3 | 7 | com.firsttouchgames.dls7 |
| Football League 2026 | 4 | 23 | com.football.soccer.league |

### 埃及
来源：https://www.similarweb.com/top-apps/google/egypt/games/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Vita Mahjong | 35 | 12 | com.vitastudio.mahjong |
| Tile Explorer - Triple Match | 64 | 18 | com.oakever.tiletrip |
| Yalla Ludo - Ludo&Jackaroo | 12 | 21 | com.yalla.yallagames |
| Ludo Club - Fun Dice Game | 28 | 24 | com.moonfrog.ludo.club |
| Arrow Puzzle: Tap Puzzle Games | 5 | 26 | com.easybrain.arrow.puzzle.game |
| Soccer Superstar | 44 | 32 | com.soccer.score.star |
| Ludo King | 40 | 33 | com.ludo.king |
| Arrows – Puzzle Escape | 137 | 42 | com.ecffri.arrows |
| eFootball | 14 | 1 | jp.konami.pesam |
| Dream League Soccer 2026 | 19 | 14 | com.firsttouchgames.dls7 |
| Football League 2026 | 6 | 20 | com.football.soccer.league |

## 3. Board 分榜证据

### 尼日利亚
https://www.similarweb.com/top-apps/google/nigeria/games/board/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Ludo Naira | 1 | — | com.ludonairapro |
| Vita Mahjong | 2 | — | com.vitastudio.mahjong |
| Naija Ludo | 3 | — | com.tonielrosoft.classicludofree |
| Whot! Ludo Party | 4 | — | ludo.whot.online.board.game |
| Ludo Master | 5 | — | com.ludo.master.hippo |
| Ludo Offline - Board Game | 6 | — | com.zariba.ludo.offline |
| Ludo King | 13 | — | com.ludo.king |
| Mancala Online - Congklak | 33 | — | com.donkeycat.mancala |
| Opon Ayo | 47 | — | com.ayoolopon.app |

Ludo Naira、Ludo Cash、Win Airtime 等奖励取向名称不能当作纯 IAA 需求证据；应另核业务性质，避免引入提现/赌注激励。

### 肯尼亚
https://www.similarweb.com/top-apps/google/kenya/games/board/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Vita Mahjong | 1 | — | com.vitastudio.mahjong |
| Mahjong Blast | 2 | — | com.nebula.mahjongtile |
| Ludo Classic | 3 | — | com.whiture.apps.ludoorg |
| Ludo（Yarsa） | 5 | — | io.yarsa.games.ludo |
| Ludo King | 7 | — | com.ludo.king |
| Ludo STAR | 9 | — | com.superking.ludo.star |
| Ludo Offline - Board Game | 12 | — | com.zariba.ludo.offline |

### 南非
https://www.similarweb.com/top-apps/google/south-africa/games/board/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Ludo King | 1 | 2 | com.ludo.king |
| Vita Mahjong | 3 | 3 | com.vitastudio.mahjong |
| Ludo（Yarsa） | 4 | 6 | io.yarsa.games.ludo |
| Align It / Nine Men's Morris | 6 | 9 | com.millgame.alignit |
| Mahjong Blast | 2 | 10 | com.nebula.mahjongtile |
| Ludo Offline | 11 | 15 | com.alignit.ludo |
| Mahjong Voyage: Tile Matching | 15 | 17 | com.playvalve.mahjong |
| Ludo Buzz | 5 | 23 | com.popupgames.ludo.king.club.dice.board.game |
| Domino Legends: Classic Game | 40 | 33 | com.playvalve.dominoes |

Nine Men's Morris 不可未经规则比较当成南非 Morabaraba（十二子棋）的完全等价产品。

### 埃及
https://www.similarweb.com/top-apps/google/egypt/games/board/top-free/

| 产品 | S | U | 包名 |
|---|---:|---:|---|
| Vita Mahjong | 3 | 2 | com.vitastudio.mahjong |
| Yalla Ludo - Ludo&Jackaroo | 1 | 3 | com.yalla.yallagames |
| Ludo Club | 2 | 4 | com.moonfrog.ludo.club |
| Ludo King | 4 | 5 | com.ludo.king |
| Domino Cafe: Classic Games | 5 | 10 | com.big.ludocafe |
| Mahjong Blast | 7 | 12 | com.nebula.mahjongtile |
| Domino - Dominos online game | 6 | 13 | ru.skillcap.dominoes |
| Dominoes（Loop Games） | 13 | 16 | com.LoopGames.Domino |
| Dominoes: Classic Dominos Game | 22 | 31 | loppipoppi.dominoes |
| Dominoes - Offline Domino Game | 32 | 38 | com.sngict.dominoes |
| Domono - Egyptian Dominoes | 21 | 51 | com.gaitco.domono |

辅助备选：南非 Cards 分榜 https://www.similarweb.com/top-apps/google/south-africa/games/cards/top-free/ ，Solitaire - Classic Card Games（`solitaire.patience.card.games.klondike.free`）S2/U2。同日快照；这是纸牌分榜，不是游戏总榜。

## 4. 六候选评估与 Google Play 核查

### A. Mahjong Solitaire / Tile 配对：跨四国第一梯队

- **证据强**：Vita Mahjong 四国均有 Games 总榜记录，优于只有小分类或全球安装量的论证。
- 官方页：https://play.google.com/store/apps/details?id=com.vitastudio.mahjong&hl=en
- 公开正文：点击/滑动两张相同、未遮挡或锁住的牌；清完牌过关；full offline；提示/撤销/洗牌；每日挑战；大牌面。特别声明不是传统麻将规则，Mahjong 仅指牌面视觉。
- 文化：不要推论当地熟悉中国麻将；图案识别可跨语言，宜测试通用生活物件和清晰符号，不把四国做一个笼统“非洲主题”。大牌设计可能适合小屏/视力弱者，但商店“面向老人”不能证明四国实际用户年龄。
- IAA：局间广告与可选提示自然；强制洗牌、连串插屏会损伤留存，离线玩家不等于广告可触达玩家。
- 与 Bubble/Tetris 共同点：低文字、识别/规划、清屏反馈。**非重复**：遮挡可达性配对，无泡泡发射、下落方块、拼满行/格。

### B. Water/Color Sort：NG/KE 优先

- **证据中强**：同一产品 NG Games S39、KE Games S29。
- 官方页：https://play.google.com/store/apps/details?id=com.water.sort.puzzle.game.color.magic.free&hl=en
- FunForge Studios 产品正文：点瓶倒水、每瓶归为同色、无时限、Undo/额外瓶、offline。
- 文化和操作门槛低；颜色需辅以形状/纹理，避免色弱问题。Water/Ball Sort 同类应合并，不应重复计候选。
- IAA：额外容器/撤销可做自愿激励广告，但不要制造广告必解死局；离线需有不依赖广告的基本恢复路径。
- 共同点：颜色识别、规则少、逐步难度。**非重复**：容器容量与倒序规划，不是射击邻接消除或落块填行。

### C. 本地规则 Ludo：区域路线最稳

- **证据强**：NG Naija Ludo Games S15；ZA King Games S8/U14；KE/EG 也有明确分类或总榜。
- 官方页：https://play.google.com/store/apps/details?id=com.tonielrosoft.classicludofree&hl=en
- 页面有 Offline 标签；正文有 Bluetooth、AI 难度、移动速度、1/2 骰、安全屋/障碍开关。
- **规则陷阱**：Naija 当前正文为两名玩家、各控制八枚棋子，并有吃子出局等规则，不能当通用四人各四棋模板。
- 操作简单不等于短局。适合短局 AI/同机/蓝牙作为离线核心；EG 的 Yalla 语聊/联网成功不代表可直接照搬离线产品。
- IAA：中途插屏破坏轮流体验；看广告改骰或获得竞技优势损害公平。现金/提现类流量与纯娱乐 IAA 必须分开。
- 共同点：清晰目标、重复对局、低操作门槛。**非重复**：掷骰赛跑、吃子、对手决策，无消除/填块。

### D. Domino：埃及先行

- **证据中强但集中 Board**：EG 多产品 S5/U10、S6/U13、S13/U16；不可说是四国总榜头部。
- 官方页：https://play.google.com/store/apps/details?id=com.LoopGames.Domino&hl=en
- Offline 标签；Draw、Block、All Five 三模式；有去广告订阅。Draw 是端点匹配，Block 无牌可出时跳过，All Five 增加端点计分。
- 文化硬证据：https://www.nationalgeographic.com/travel/article/egypts-coffeehouses ，2011-06-09。正文明确埃及咖啡馆 dominoes/backgammon，主要男性场景。支持文化背景，不代表当下全国用户或女性青年偏好。
- 阿语 RTL、本地数字和规则需另测；不默认埃及用户都接受 All Five。
- IAA：局间自然；联网等待叠加广告会退局；避免赌注/现金桌定位。
- 共同点：符号识别、短动作。**非重复**：端点连接与对手博弈，不是泡泡/方块消除。

### E. 轻足球：滑动传射/定位球

- **直接证据中强**：Soccer Superstar ZA Games S108/U32、EG S44/U32；NG/KE 仅足球题材大作支持，不是轻玩法直接验证。
- 官方页：https://play.google.com/store/apps/details?id=com.soccer.score.star&hl=en
- 正文明确 simple flick controls、滑动传射/弧线球、full offline、关卡挑战。
- 3D 离线不等于低端友好；轻量方案宜短场景、2D/轻3D而非完整模拟。球员肖像/球队标识需授权，不能用地域文化当授权替代。
- IAA：失败重试/回放可选激励；强制广告重试断节奏；材质、阴影和复杂 AI 可能抬高性能成本。
- 共同点：一指、即时反馈、短挑战。**非重复**：轨迹/时机/目标得分，而非同色碰撞或方块布局。

### F. Mancala/Ayo：尼日利亚差异化小试，不作大盘首选

- **证据弱于前五**：NG Board Mancala S33、Opon Ayo S47，无本次总榜或 DAU 证明。
- 官方页：https://play.google.com/store/apps/details?id=com.donkeycat.mancala&hl=en
- 明确离线 AI、同机双人、联网；营销把 Ayo/Congklak 等名称并列，但这不证明各地规则等同。
- Opon Ayo：https://play.google.com/store/apps/details?id=com.ayoolopon.app&hl=en ，正文为播种棋、在线对战和私人房间，**没有核实离线**。
- 文化反证：https://ludii.games/details.php?keyword=Bao+Kiswahili+(East+Africa) 。Digital Ludeme Project 正文：东非 Bao 是四排 4x8 棋盘，复杂且难精通。不能把两排 Ayo 直接改名套入肯尼亚 Bao，也不能把 Bao 归为简单超休闲。
- IAA：思考过程中插屏不合适，规则教育与 AI 公平优先，广告位密度低。
- 共同点：棋盘规划、低资源呈现。**非重复**：播种计数/吃子策略，无发射泡泡、填行/填块。

## 5. 共同变现及技术限制

上述六个主参考产品均看见 Contains ads + In-app purchases，证明可混合商业化，不证明广告收入比例、盈利或纯 IAA。未核包体、RAM、帧率、首启联网、断网广告缓存等。2D/少贴图/无实时联网只是低端友好设计判断。

纯离线提高可达性，却减少常规广告展示机会；不能把离线活跃全部视作可变现 DAU。应分国家观察在线/离线活跃、有效曝光、断网恢复和广告负担，但本调研不声称这些指标已经取得。

排除 Bubble Shooter、Tetris、Block Blast/Block Puzzle。没有把累计安装当 DAU，也没有报告未取得的付费平台数据。Arrow 的国家总榜记录可交由主线程与其已核产品/玩法证据合并；本次未独立完成 Arrow 的 Google Play 深读，故不在六个深评候选中。
