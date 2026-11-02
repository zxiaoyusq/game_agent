# 非洲与南亚 Android IAA 音游扩品研究

- **实际调研日期：2026-09-21**（运行时系统日期，Asia/Shanghai）。七国 Similarweb 榜单 **snapshotDate 均为 2026-09-18**。未使用异常 dateModified。
- 研究边界：印度、巴基斯坦、孟加拉国、尼日利亚、肯尼亚、南非、埃及；不讨论版权，不开发产品。
- 结论：**轻音游应正式进入首轮候选，而不是只研究箭头/消除。首选短段钢琴块与单指节奏跳球两条并行路线；节奏射击作为巴/孟区域化备选；配色音乐跑道作为次优玩法探索。**“规则直观”不等于动作门槛低：音游有实时反应、连续追踪、音画同步与失败重开成本。

## 1. 证据口径

所有排名直接来自公开 HTML 的 `window.__APP_DATA__.layout.data.apps`，不是列表序号：

- **S = storeRank**，该国家该分类的商店排名。
- **U = usageRank**，Similarweb 的当前安装量与过去 28 天活跃用户混合使用排名，**不是 DAU，不是具体活跃人数**。
- `0` 记为“—”（来源缺失），不记为第 0 名。
- “未见”是本次公开数组没有该包名，不等于无用户、无排名或跌出某一确定名次。印度、巴、孟、尼、肯、埃及 Music 各暴露 51 项，南非 34 项。部分页面按 U 排列，因此数组第一个不是 S1。
- 巴基斯坦、孟加拉国、尼日利亚、肯尼亚本次 U 均为缺失。不能在这四国声称高日活。
- 本次是单日横截面，不能推出持续增长、收入、买量成本或 ROAS。

## 2. 七国 Music 可核查对比

单元格为 **S / U**；分类均为 **Google Play > Games > Music > Top Free**，榜单日期均 **2026-09-18**。

|产品（按准确包名识别）|印度|巴基斯坦|孟加拉国|尼日利亚|肯尼亚|南非|埃及|
|---|---:|---:|---:|---:|---:|---:|---:|
|Magic Tiles 3|6 / 8|5 / —|10 / —|3 / —|5 / —|3 / 1|1 / 1|
|Piano Beat: Music Game|1 / 2|3 / —|6 / —|1 / —|1 / —|2 / 13|2 / 2|
|Tiles Hop|7 / 7|13 / —|12 / —|14 / —|18 / —|9 / 5|4 / 3|
|Beat Fire|13 / 27|10 / —|7 / —|44 / —|28 / —|未见|未见|
|Piano Tiles 2（现 Kooapps 包）|未见|未见|未见|38 / —|未见|未见|37 / 14|
|Dancing Road|未见|未见|未见|未见|未见|未见|未见|

Music 来源：

- [印度](https://www.similarweb.com/top-apps/google/india/games/music/top-free/)
- [巴基斯坦](https://www.similarweb.com/top-apps/google/pakistan/games/music/top-free/)
- [孟加拉国](https://www.similarweb.com/top-apps/google/bangladesh/games/music/top-free/)
- [尼日利亚](https://www.similarweb.com/top-apps/google/nigeria/games/music/top-free/)
- [肯尼亚](https://www.similarweb.com/top-apps/google/kenya/games/music/top-free/)
- [南非](https://www.similarweb.com/top-apps/google/south-africa/games/music/top-free/)
- [埃及](https://www.similarweb.com/top-apps/google/egypt/games/music/top-free/)

### 不能只看老产品：榜单浮现品

- **Piano Beat: Music Game**（`piano.game.music.beat.tiles`）在印/尼/肯 Music S1；南非、埃及 S2，是本轮必须纳入的高潜参考。印度 U2、埃及 U2 比单看下载商店排名多一层使用信号；南非 S2/U13 也提醒下载与使用并不一致。
- **Piano Music Heart: Pop Tiles**（`piano.music.pop.tiles.game.beat`）巴/孟 Music S1/U缺失；印 S8/U12、尼 S6、肯 S3、南非 S4/U9。尚未补 Play 玩法详情，不把中文名伪称官方；可称“钢琴音乐之心”（说明性译名）。
- **Piano Fire: Edm Music & Piano**（`beatmaker.edm.musicgames.PianoGames`）：印度 S4/U4、巴 S4、孟 S3、尼 S2、肯 S8、埃及 S10/U9。
- **Piano Fire 2: Slide Challenge**：巴 S6、孟 S5、尼 S9；**Rhythm Fire-EDM Shooting Game**：巴 S7、孟 S4；**Rhythm Shooter: Phonk Rush**：巴/孟 S8。这些只是已核榜名与排名，尚未核 GP 玩法，不能凭标题宣称功能，但支持下一步对滑动/射击细分做定向验证。
- Music 分类还包含儿童琴、真实乐器模拟，如印度 Piano Kids S2/U1、Harmonium S10/U3；尼 Real Guitar S5、肯 S2。**不能把整个 Music 榜等同于成人节奏音游市场。**本轮不将儿童产品当作一般 IAA 强广告模板。

## 3. Games 总榜交叉核查

七国 Games Top Free 均抓取公开数组（各 51 项），日期同为 **2026-09-18**。

|国家|产品|分类|S|U|公开来源|
|---|---|---|---:|---:|---|
|肯尼亚|Piano Beat: Music Game|Games 总榜|16|缺失|[Games](https://www.similarweb.com/top-apps/google/kenya/games/top-free/)|
|巴基斯坦|Piano Music Heart: Pop Tiles|Games 总榜|24|缺失|[Games](https://www.similarweb.com/top-apps/google/pakistan/games/top-free/)|
|孟加拉国|Piano Music Heart: Pop Tiles|Games 总榜|13|缺失|[Games](https://www.similarweb.com/top-apps/google/bangladesh/games/top-free/)|

这比只在狭窄 Music 分类占头部更能支持轻音游进入首轮测试，但仍不是收益证明。

[印度 Games](https://www.similarweb.com/top-apps/google/india/games/top-free/)、[尼日利亚 Games](https://www.similarweb.com/top-apps/google/nigeria/games/top-free/)、[南非 Games](https://www.similarweb.com/top-apps/google/south-africa/games/top-free/)、[埃及 Games](https://www.similarweb.com/top-apps/google/egypt/games/top-free/)本次公开数组未见 Music 产品。印度/南非/埃及默认 `orderBy=app-index`，公开集合不是完整 S 前 51，因此**不能写“Music 进不了 Games 前 50”**。尝试 `?orderBy=storeRank` 未改变排序，不将其当作成功获取商店前 50。

## 4. 四条细分机会与取舍

下述 IAA 位置是产品设计推断，**不是已实测竞品广告位**；所有六个 GP 参考均明确 Contains ads 与 In-app purchases，属于混合变现先例，不能称纯 IAA。

|优先级 / 细分|主证据与机会|动作门槛|声音、弱网、低端机|IAA 自然位|短局复玩风险|
|---|---|---|---|---|---|
|**P1A：短段钢琴块 / 点按连击**|Piano Beat + Magic Tiles 3；7国重复出现，Piano Beat 肯 Games S16。先验证宽容判定、低密度短乐段，而非直接复制高速谱面|入门规则简单，但多轨识别、左右手协调、连续点击、加速和漏键惩罚使上限高；不应泛称低操作|2D可控，但卡顿和输入延迟直接影响公平；本地预置少量曲段、可选缓存、离线可重玩。静音可按视觉操作，但音乐反馈与满足感会下降|失败后可选复活；曲段结算奖励加倍；明确自愿解锁曲段/外观。开曲与演奏中不插广告|短段可降低重开成本；过短而每局强制广告会令广告时长超过游玩。重复前奏、失败首段循环、以复活填容错都伤留存|
|**P1B：单指节奏跳球 / 路线追踪**|Tiles Hop 埃 S4/U3、南非 S9/U5、印 S7/U7；比只做琴键更宽玩法。可用可视路线、宽平台、缓节奏差异化|手指数少，不代表负荷低：持续横向追踪、落点预判、平台间距和突然变向构成门槛；需避免窄跳台与早期高速|声音增强沉浸，视觉落点可保留部分静音可玩性。低特效简背景、稳定帧时比炫光优先；基础曲段离线，音乐包预缓存|掉落后一次自愿续跑；结算；球皮肤与主题试用。不可在连续跳跃中切断声音|曲段可复玩，但坠落几秒即广告、拖动灵敏度不稳定、从头重复长曲会强挫败；需复活频控与短段检查点|
|**P2A：节奏射击 / 按住拖动瞄准**|Beat Fire 巴 S10、孟 S7；同时有 Rhythm Fire 与 Rhythm Shooter 榜单信号，南亚值得独立创意测试|真实动作是 hold & drag 瞄准，不是单次点击。追踪下落目标、节拍与屏幕遮挡叠加，中等或更高反应压力|枪声和节拍是差异点，静音价值损失较大；闪光/粒子控制，避免枪声延迟。单人预置曲段可离线，广告收益仍需联网|失败续局、武器皮肤试用、结算翻倍；不在连射中强插|单一节拍易疲劳，过强音效/失败即重播影响耐受；区域榜信号较集中，不应直接七国同配置铺开|
|**P2B：配色音乐跑道 / 滚球收集**|Dancing Road 的“节奏+颜色识别”是扩玩法参照；但本次七国数组未见，不当当前头部证明|滑动方向+颜色选择双任务；变色节点、拥挤色球提高认知与反应门槛；需形状冗余避免单靠颜色|视觉跑道使静音仍可能可玩，但届时更接近跑酷而非纯音游；简化材质和远景，稳定帧时；离线基础路线|撞错色后的自愿续跑；终点奖励；外观解锁|失败多来自看不清或镜头遮挡会显得不公平；颜色换皮内容深度有限，不能只靠新歌解决跑道单调|

### 国家测试重点（假设，不是市场收益排序）

- **印度 / 埃及 / 南非**：能同时观察 S、U，适合验证“下载吸引力与重复使用”差异；埃及 Magic Tiles 3 S1/U1、Piano Beat S2/U2、Tiles Hop S4/U3，为点按与跳球双线提供直接信号。
- **肯尼亚 / 尼日利亚**：优先把 Piano Beat 式短段点按列首轮；肯 Games S16 是跨分类证据。U缺失，必须依赖自己的留存/会话数据，而非假设活跃高。
- **巴基斯坦 / 孟加拉国**：点按仍为主线，音乐射击为创意对照。Piano Music Heart Games S24/S13 是跨分类支持；非“用户只接受超低操作”。
- 网络和低端设备是需测的产品条件，不把七国所有用户概括为同质低端机。离线可玩能降低中断风险，但**离线期间无法等同获得 IAA 收益**；不能用离线标签推导广告填充或 eCPM。

## 5. 与箭头 / 消除的差异

- **箭头**（以空间方向/顺序解谜为例）：可停下来想，静音基本不损失核心体验；音游是持续实时反馈。箭头更适合不确定打断场景，音游以节奏快感、技巧成长与曲段收藏形成不同复玩动机。
- **消除**：主要是盘面规划、目标和连锁反馈，可容纳较长关卡内节奏起伏；音游依赖时间轴连续性，不能借用“任何时刻都能插广告”的思路。
- 音游的广告自然位是失败/曲段结算/自愿内容或外观奖励；箭头可用提示、撤回，消除可用步数、道具。**不能把失败强迫复活当作音游自然高变现的保证。**
- 音游比箭头/消除多了音频与触控时延、曲段内容、帧时一致性的工程成本，但2D点按和简化跳球不是天然重度产品。应把 P1A/P1B 与箭头/消除并行做小规模验证，而非因这些成本直接降为不做。
- 首轮看首段完成率、连续失败后的退出、短段复玩、D1/D7与会话、低端设备帧时和时延、静音占比、联网覆盖、广告展示/留存损失；排名只能指导选品，不能代替这些指标。

## 6. 六个参考产品：中文名、准确 Play 链接、玩法和声明

商店核查时间2026-09-21；语言页 `en_US` 与 `zh_CN`，地区 `gl=US`。包名确认不代表已逐一核验七国所有设备可安装或广告配置。**offline 均为商店声明，未实测；下载若引用均为当前包全球累计徽章。**

|中文名（身份说明）|英文标题（本次实际页面）|核心玩法|广告 / IAP|offline 证据|全球累计徽章|
|---|---|---|---|---|---|
|魔法方块3（官方中文介绍正文用名；标题仍为英文）|[Magic Tiles 3™ - Piano Game](https://play.google.com/store/apps/details?id=com.youmusic.magictiles)|下落黑键点按，失误中断，多难度|均有|介绍明确 Game Offline Mode + Offline 标签|500M+|
|钢琴块2™ - 钢琴游戏（官方中文页标题）|[Piano Tiles 2™ - Piano Game](https://play.google.com/store/apps/details?id=com.kooapps.pianotiles2gp)|黑键点按、避白键，滑块/双块/加速|均有|介绍明确 Play offline, no WIFI + 标签|10M+|
|节奏跳球（说明名；官方中文页标题为“钢琴节奏大师: 音乐单机游戏”，AMANOTES 产品，非腾讯）|[Tiles Hop Music & Ball Game](https://play.google.com/store/apps/details?id=com.amanotes.beathopper)|控球沿音乐砖块跳跃与落点跟踪|均有|Offline 标签；不能推断全部曲目无需首次下载|500M+|
|跳舞的路：彩球配色（说明性译名，中文页无中文标题）|[Dancing Road Color Balls Match](https://play.google.com/store/apps/details?id=com.amanotes.pamadancingroad)|音乐跑道滚球、同色收集/配色，错色失败|均有|Offline 标签|100M+|
|节拍射击（说明性译名，中文页无中文标题）|[Beat Fire - Edm Gun Music Game](https://play.google.com/store/apps/details?id=beatmaker.edm.musicgames.gunsounds)|按住拖动瞄准，击碎随 EDM 下落的块|均有|Offline 标签|50M+|
|钢琴节拍（说明性译名，中文页无中文标题）|[Piano Beat: Music Game](https://play.google.com/store/apps/details?id=piano.game.music.beat.tiles)|随拍点键、连击金币解锁歌曲、加速/无尽|均有|介绍明确 Offline Mode，中文介绍“无需网络”+ 标签|10M+|

中文核对页：在以上准确链接后加 `&hl=zh_CN&gl=US`；已在 compact 产品 JSON 保存完整URL。

额外注意：Piano Tiles 2 现包名是 `com.kooapps.pianotiles2gp`，不能用旧猎豹版本包名替代；其介绍“全球11亿玩家”不是本包下载徽章。Dancing Road 此次标题已经不是历史常见的 Dancing Road: Color Ball Run!，用包名保持可追踪性。

## 7. 保存的内部证据

- `music-rankings-compact-2026-09-21.json`：七国 Music 原始 S/U 精简数据。
- `games-rankings-compact-2026-09-21.json`：七国 Games 总榜公开数组及 Music 命中。
- `music-product-evidence-compact-2026-09-21.json`：六品核实字段、命名级别、声明与 caveat。
- `fetch-music-research.mjs` / `fetch-games-evidence.mjs` / `fetch-play-evidence.mjs`：公开 URL 抓取脚本，由 write 创建；无登录、无产品开发。
- `*.raw.html` / `play-*.txt`：核对来源留档。GP原始自动抽取的 offlineSnippets 可能含用户评论，本结论只采商店介绍和标签，不把评论当离线保证。
