# Carrom 宝箱与装备成长代码对照

阶段：prototype；attempt=1。范围：只读分析输入 H5 ZIP，交付设计与代码证据报告，不修改游戏源码、不进入美术、代码或测试阶段。

## 结论

现有游戏具备金币购买装备、金币直接升级、装备属性汇总、比赛奖励与四小时转盘奖励，可复用这些入口和界面资源。已检查的完整主脚本未发现与用户样本对应的宝箱倒计时、装备碎片库存、碎片升级门槛或 Blaze 名称；这不是对竞品实现的判断。复现样本需要新增宝箱与碎片成长状态机，不能仅修改升级价格。最优先处理独立部署存储边界和金币调试入口。

## 输入、方法与证据边界

参考路径（相对 ref/）：`mcp-inputs/mac-codex/2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2/Carrom_Clash_Master.zip`。ZIP SHA256：`2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2`。329项，展开总计5,074,490字节；未取得ZIP整体压缩字节数，不能把展开量当作下载量。submission.sha256属于不同字段，不替代ZIP哈希。

包内公共前缀 R=`www.excellenth5game.com/Carrom_Clash_Master/`。下文字符区间均为 read_reference_archive 返回文本的零起始定位范围，不是源码行号。

已读取完整成员清单；完整读取 R/index.html、R/game.html、R/developer_v2.js，以及 R/js/game.js 的全部513,531字符。主脚本文件513,553字节，SHA256=`2a036140fcf41e307b604373d307ff4014d061eef4bee5fb9504b90424b3460e`。developer_v2.js SHA256=`ecaccd063d47e7a8e002f2e697282e9a3ba93c1aa3cbfd24d3b6c3cf26ef3c47`。保留混淆符号定位，没有运行未知脚本或生成反混淆结果。主脚本末尾字符串表与明文调用支持必要的属性名称对应；没有生成全量机器检索索引。

已按所选 game-competitor-analysis、apk-engineering-analysis 技能读取入口及相关证据规范，借用证据分层方法；本次没有联网检索或APK分析工具，未完成联网竞品研究、APK拆包或实机操作。已读冻结资料：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/native-web.md。保留输入既有 Pixi/Planck 架构，不因原生Web资料而擅自改写工程。

证据分层：A=输入ZIP静态源码/清单；B=用户转述单账号样本；C=本报告建议。静态代码不等于实际执行结果。未查看图像，未验证视觉质量或授权状态，未执行构建、单测、浏览器、离线重启、性能或广告测试。

## 用户样本逐项对照

| 用户转述（B） | 当前源码证据（A） | 差异、未知与最小新增（C） |
| --- | --- | --- |
| 青铜箱一免费等待10秒 | `_0x66b857`为四小时；`_0x4c7a25`按Date与lastRewardTime更新转盘入口 | 四小时转盘不是10秒宝箱；新增独立chestId、readyAt与领取状态 |
| 箱一35金币、Blaze×5；2/10→7/10 | 转盘按颜色发金币，装备upgrade直接由金币升级 | 未发现对应碎片库存或Blaze名称；新增稳定equipmentId与fragment库存，禁止凭外观强行映射 |
| 箱二免费等待30秒，联网重启后可开 | 当前适配层存储依赖宿主；没有证实独立页持久化 | 样本无法证明服务器计时、必须联网或后台持续运行；新增持久化readyAt，重启按时间戳恢复 |
| 箱二42金币、Blaze×5 | 现有转盘金币为50、100、200、500等配置；现有奖励没有这条碎片路径 | 将35/42金币与每次5碎片仅作为样本重放配置，不推导掉率 |
| 达标花50金币升2级，最后2/12 | `_0x5a5b07`检查金币与升级上限，扣upgradeCost并upgrade++ | 样本算术为7+5=12，消耗10剩2，下门槛12；新增碎片与金币联合校验及一次性提交 |

所有竞品数字来自用户转述，未核对截图、视频、APK、网络请求或多账号样本；不能据此推导通用等级公式、宝箱序列、概率、联网依赖或防作弊能力。

## 代码索引与调用关系

### 初始化与存储

R/js/game.js [20000,60000)：`game.init → _0xc37276 → _0xa07a9b / _0x358d16 → PIXI.loader.load(_0x16b945) → _0x3690db → _0x5ecd40 → _0x13b722`；随后`_0xf8ddc7`构造世界和界面，`_0x1d7cac`启动ticker。

`_0x23207e`存档包含tables、upgrades、strikers、stones、coins、tutorial、lastRewardTime。`_0x5ecd40`逐键读取GameSnacks.storage，truthy值直接JSON.parse覆盖；`_0x13b722`同步金币、升级和装备状态。`_0x3a0318 → _0x9b0cd → 逐键JSON.stringify/setItem`保存。默认存档coins=0会覆盖运行变量早先声明的1000，不能把1000当最终初始金币。未见版本迁移、坏档恢复、数组长度和数值范围验证、跨键原子事务或写入确认。

R/developer_v2.js全文：存储对象先使用内存this.g，可由URL gameData初始化；有channel时才向宿主发送持久化消息。R/game.html没有data-target-origin，适配脚本在此条件下关闭跨帧通道。故当前调用路径的setItem停留在内存是静态推断，未实测重启丢档。适配脚本还将window.localStorage访问替换为抛错，后续方案不能直接照搬localStorage调用而不处理适配边界。

R/index.html依赖远程广告SDK，iframe加载game.html；接收next、reward、gameLoadingCompleted等消息。接收端未校验origin/source。R/game.html尝试注销既有Service Worker，不构成离线缓存实现。离线“页面可启动”和“存档可恢复”须分别验收。

### 商店、购买、装备与升级

R/js/game.js [60000,120000)：商店`_0x429f89`注册select→`_0x16f9d2`，buy→`_0x900aee`，select_stone→`_0x937251`，buy_stone→`_0x3f64a2`。

- striker购买：`_0x900aee → _0x230373`检查value≤coins，扣value、解锁；成功后切换当前装备，更新商店并`_0x3a0318`。
- striker升级：`_0x900aee → _0x5a5b07`检查upgradeCost≤coins且upgrade小于配置上限，扣upgradeCost、upgrade++，返回后刷新并保存。该链没有碎片检查。
- striker装备：`_0x16f9d2`把原equiped改unlocked，选中项置equiped，更新`_0x4b3012`并保存。
- stone购买/装备：`_0x3f64a2 → _0x1e3129`扣购买value，更新`_0x3e9ee1`和状态并保存。虽然stone数据有upgrade字段，已读链未实现对应升级消耗或属性成长；存档也仅保存stone状态。
- `_0x937251`开头已对equiped提前return，后面再次判断equiped的卸下分支因此不可达；这是静态控制流问题，未动态复现。

配置位于[20000,60000)：9个striker购买价为0/50/100/200/400/600/2000/5000/10000；各自upgradeCost为20/25/50/100/200/300/1000/2500/5000。当前升级链未递增upgradeCost，故在本链按装备固定价扣费；这些价格不等于碎片门槛。upgrade上限3/3/3/4/4/4/5/5/3，表示内部升级次数，不宜直接当作用户可见等级。

商店显示位于[240000,360000)：`_0x350929`装备卡、updateStats显示三种属性和下一次升级预览；`_0x886cb6`构建3列9件装备并转发事件，updateStates按金币/状态/上限调整按钮。显示层与业务扣费均需在新增碎片规则后采用同一个判定函数，防止按钮亮起但交易失败。

### 属性实际生效

[60000,120000)的`_0x1260d2`在开局读取当前striker的aim、force、time，再遍历已完成升级序列：0增加aim，1增加force，2增加time。升级不只是卡片显示，开局确有属性汇总路径。

- aim：`_0xc5bee4.aimFactor = 0.5 + 0.1 × effectiveAim`；[360000,420000)的`_0x902691.redraw`将辅助线Y缩放设为strength×aimFactor。因此证据支持辅助线更长，不支持命中吸附或改变物理精度。
- force：`_0x647bf3 = 75 + 25 × effectiveForce`；[120000,180000)移动计算strength=min(拖动距离/该值,1)，释放达到0.25才击球。击球参数为strength×100×1.25，最大125不随force增加。相同拖动距离下更高force反而可能降低strength；不能宣传为已证实“最大击球力量增加”，须实测确认设计意图。
- time：回合窗口`_0x1f57de = tableBaseTicks + 2 × effectiveTime`，tableBaseTicks为6000/1500/1200/900/600。非第0桌每逻辑步减1；按60步/秒目标，每属性点只增加约33.3ms，不是2秒。第0桌显式不执行超时扣减，6000不能直接称其有效限时100秒。

### 金币来源与奖励

[60000,120000)：选桌`_0x4d0a10`扣fee并保存；UI通过余额禁用不足的桌，但业务入口仅见上界检查，没有再次检查余额、负索引或整数性，建议收口到领域校验。胜负结算`_0x47e567(true)`增加桌prize并保存，激励成功再加同额；失败不发胜利金币。fee为0/50/200/750/5000，prize为50/125/400/1500/10000。

转盘`_0x50f739`按purple:3、blue:15、green:6、red:15、yellow:1进行权重选择，`_0x5b20b9 → _0xffce48`增加对应金币200/50/100/50/500，记录Date.getTime为lastRewardTime并保存；激励成功可再加同额。该权重仅是本H5转盘静态配置，不是竞品宝箱掉率。`_0x4c7a25`以当前时间减lastRewardTime，严格大于四小时判可用，整点相等的边界须测。奖励链未见持久化唯一领奖ID或跨重启幂等记录，UI禁用不能替代交易幂等。

[360000,420000)大厅金币区域pointerdown发出hackcoins；[60000,120000)监听该事件每次coins+=500并刷新大厅，没有立即保存，后续其他保存可能把增加值写入。不能将其作为正常产出来源，应优先移除或限制到明确开发环境。未动态点击验证。

## 物理、规则与时机定义

以下先记录现有代码，后列未来验收口径，不混淆为本次实现。

- 世界：Planck零重力，100设计像素/物理单位，640×1137设计画布。`_0x49d791`末尾world.step(1/60,10,10)、clearForces；`_0x4bf21a`累积ticker delta，while accumulator>1执行固定逻辑步，未见补步上限。后台恢复须测是否突发补步；>而非>=也有整步边界差异。
- 碰撞：[360000,420000)棋子动态圆半径16px，linearDamping=1.8、angularDamping=0.2、friction=0、restitution=1、density=0.45、bullet=true。[420000,480000)striker圆半径21.76px，linearDamping=2.8、angularDamping=5、friction=0、restitution=1、density=0.5、bullet=true。放置时striker为sensor，发射时关闭sensor。用于摆放避让的棋子半径常量15px与实体16px不同，需核验边缘重叠。
- 球桌由静态Edge围成；begin-contact负责音效/特效并改变阻尼，不直接按每次接触发分。存在两处puck接触阻尼分支都写向fixtureB对应body的情况，可能依赖接触顺序，应回归验证。
- 进袋：每逻辑步按球心距四袋中心≤20设计像素判入袋，移出物理世界，随后回合结算处理分数。它是距离检测，不是袋sensor接触回调。
- 输入窗口：仅玩家有效回合允许开始拖动；强度不足0.25释放不击球；达到阈值调用发射、关闭本次输入，再通过约2300ms逻辑延迟后轮询是否仍有运动，轮询间隔50ms。低速|vx|+|vy|<0.2时休眠。暂停标记使逻辑更新提前返回；可见性隐藏分支主要静音，恢复时可能弹暂停，不能据此保证完整后台冻结。
- 常规模式：玩家和对手各9子，回合结算对9分和queen是否仍在场分支判胜负；入己方子通常续回合，未有效进袋换手，striker入袋有犯规处理。保留现有不同模式，不将其简化为所有模式统一9分。
- freestyle：按棋子类型对应50/20/10累计，达到`_0x153877`触发结算；本次报告不补猜目标常量值。犯规分支出现`playerScore -= 50`和`oponentScore -= 50`，但周围实际HUD与结算使用`_0x4d3bf1/_0x41f634`，应查证是否引用未定义变量或漏改名，不能声称已复现错误。

后续可接受误差提案：固定步长1/60秒；相同初始状态与输入在30/60/120Hz渲染下，得分、回合、奖励次数完全一致，静止终点差≤2设计像素；高速撞边不穿透。输入门槛测试0.249/0.250/0.251，判定不得被显示四舍五入改变；交易金币、碎片、等级均为整数且零误差；宝箱在readyAt之前不可领，达到后前台显示延迟≤1秒；暂停中不消耗回合窗口，恢复无额外发射。上述是待实施验收指标，不是本次通过结果。

## 最小复用方案与核心循环

目标循环：Play → 获得配置指定宝箱 → Start Unlock → 等待 → Open → 领取金币和碎片 → 达标且金币足够时Upgrade → Equip → 下一局体现属性变化。宝箱来源、槽位容量与后续长线数值没有样本证据，最小演示采用固定两箱样本重放，不臆造完整商业化系统。现有比赛和转盘保留为独立机制。

建议新增独立成长领域模块，保留Pixi表现层与Planck规则层。配置包含equipmentId、displayLevel、fragmentRequired、coinCost、attributeEffects；状态包含schemaVersion、revision、coins、equipmentStates、chests、claimedRewardIds。每箱至少有chestId、status、unlockStartedAt、readyAt、rewardPayload或可恢复奖励引用。状态转换为locked→unlocking→ready→claimed；ready可由时间派生，claimed必须持久化。

领取事务：校验箱ID、状态和时间 → 校验未领奖 → 同一快照加入金币/碎片并标记已领 → 持久化成功后展示成功。重复点击/刷新/重复回调返回同一结果且不追加奖励。升级事务：验证装备有效、已解锁、未满级、碎片足够、金币足够 → 同一快照扣两项并加等级 → 持久化成功后刷新属性预览。单快照需配合并发控制，不能只把多键改一键就宣称跨标签页原子性。

样本重放配置：初始Blaze碎片2、等级1；箱一10秒、35金币和5碎片；箱二30秒、42金币和5碎片；1→2级消耗10碎片与50金币，下一门槛12。此时最终碎片2/12；若无其他金币变动，余额相对初始净增27。equipmentId使用独立blaze_demo，不强行认定现有任一striker即Blaze；显示现有图标时标明只是演示复用。后续等级配置缺失时不外推公式。

离线计时用持久化readyAt恢复，前台单调时钟可改善显示连续性，跨重启仍需墙上时钟；纯本地不能可靠防改系统时间。检测回拨时保留箱状态并提示，不自动重复发奖。未要求服务器的最小版本不新增服务器，但报告不把本地时间方案称为可信服务器计时。存储适配区分真实宿主与独立页，独立页考虑IndexedDB，处理当前SDK屏蔽localStorage的边界、写失败与坏档回退。

### 界面与默认英文文案

沿用竖屏大厅、金币HUD、底部入口、商店装备卡和三种属性条。大厅新增Chests入口和两张箱卡；卡片显示状态及剩余时间。领取弹层先显示Coins +35、Blaze Fragments +5及2/10→7/10，随后Continue；升级卡显示Level 1、Fragments 12/10、Upgrade · 50 Coins，升级后Level 2、2/12。按钮文案：Start Unlock、Unlocking、Open、Claimed、Equip、Equipped、Max Level；反馈：Not enough coins、Not enough fragments、Save failed. Please try again.。页面默认英文，未来实现设置html lang=en，中文浏览器环境不切换语言。本次未修改现有页面语言或纹理。

### 资源复用与取舍

真实清单已有assets/shop/strike_01.png至strike_09.png、strike_module_base.png、strike_blue_bit.png、strike_yellow_bit.png、strike_green_stroke.png、shop_button_upgrade.png及hover、购买按钮与金币图；stone编号按真实文件00..06、08、09处理，不补造07。可复用装备卡、按钮、属性条和金币粒子；未确认有宝箱图片，最小新增宝箱可在后续美术阶段选程序化图形方案或生成独立素材。本次未提取、修改、生成或视觉验收这些图片，也没有编造授权。

## 优先任务与验收

| 优先级 | 任务 | 后续可执行验收 |
| --- | --- | --- |
| P0 | 处理GameSnacks宿主/独立页存储边界、坏档与写失败 | 断网后关闭重开保持coins、碎片、等级、箱readyAt；损坏JSON/越界等级不阻塞启动，写失败不显示领取成功 |
| P0 | 移除玩家可达hackcoins入口；交易层完整校验 | 点大厅金币区域不增加余额；负索引、NaN、重复输入与不足余额均无扣费/升级；确认实际发布包无调试入口 |
| P0 | 两箱样本重放与事务幂等 | 2/10→7/10→12/10，扣50金币和10碎片后2/12；连点、刷新、重复广告回调不重复获奖 |
| P1 | 明确force/time设计意图并修复需要的实现 | 同力度对比初速度；同拖距比较strength；非零桌计时核对真实秒数，界面描述与行为一致 |
| P1 | 回归疑似计分变量、碰撞阻尼和stone卸下分支 | freestyle犯规不抛异常且扣实际分数；A/B碰撞顺序一致；装备/卸下规则与按钮一致 |
| P1 | 离线启动与远程SDK失败降级 | 无网络仍进入游戏；广告失败不挂死ticker、不发未完成激励奖励；验证消息来源 |
| P1 | 固定步长、暂停与生命周期 | 30/60/120Hz输入重放结果符合前述误差；隐藏/恢复不突发追帧或跳过操作窗口 |
| P2 | 包体去重、纹理优化与场景加载 | 比较真实构建字节、首屏时间和内存；视觉对比后再接受WebP或字体裁剪 |

包体基线：归档展开约4.84MiB，低于10MB，但不代表最终dist或试玩ZIP已验收。主脚本513,553B；Pixi438,158B、Planck193,449B、Howler22,275B。列表未提供package.json或测试构建工程，不应伪造npm成功。

清单已证实同哈希重复：tutorial/ARROW_LEFT.png与select/tableselect_arrow_left.png均1320B、SHA256=`6637401ff4982169f2fb6e149ea3d12b4d9944e05c2a804a06690a31c292e78c`；右箭头对应两文件均1266B、SHA256=`451e41e61e2bdd91a36293f1c58106c73506643b8d5926269108384336d9c3d6`。仅这两对可去重2596展开字节，构建收益未测。较大图片如tutorial/WOODEN_BASE.png132154B、preloader/bg.png116032B、settings/pause_base.png111970B，可作为转换候选，不能预报未经测量的节省率。TTF111152B与bitmap字体同时存在，先核实真实用途。src.bitmaps存在重复键覆盖，不能误写成两份资源必然加载。

性能线索：启动遍历全部bitmaps加入loader；多个Howl启动注册；逻辑循环对多个数组slice、距离扫描和排序；固定步补步无显式上限。先采集首屏、P95帧耗时、内存和长局对象数，再决定分场景加载/复用临时数组/对象释放，不把静态线索当已测瓶颈。

## 本次真实验证与交付

完成：ZIP成员分页清点、入口与适配脚本读取、完整主脚本分段读取、关键业务链和物理公式静态交叉核对。尚未进行：运行、构建、npm测试、Chromium点击、截图、离线重启、广告回调或性能测量。没有本次构建成功、测试通过或真机验收结论；本轮是原型证据分析，未启动代码或测试阶段。

产物：`/workflow/prototype.md`。没有修改游戏源码，没有生成dist、素材、源码包或试玩ZIP。后续代码阶段须在最终源码/资源修改后实际执行npm run build、npm test、npm run check；check应访问最终dist并覆盖桌面/手机真实操作、中文浏览器环境下英文默认文案、错误控制台、离线持久化与上述经济状态边界，输出evidence。发布展开小于10MB须对最终包重新计量。
