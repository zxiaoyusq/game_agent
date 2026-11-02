# 非洲／南亚 Android IAA 选品：行业证据补充

- **实际核查日期：2026-09-21**（运行环境实际日期；不是报告出版日期）。
- **核实4条指标：3条官方原始网页、1条公开二手行业报道。** 两条GSMA指标来自同一份官方新闻稿，并非两项独立研究。
- 本文仅为交互HTML汇总的内容源，不修改既有14类32产品候选池，不新增Bubble／Tetris重复候选，不制作HTML。
- 每条先经 `web_search` 发现，再以 `web_fetch` 阅读。Mobilegamer正文被截断后以Node fetch**同一公开URL**抽取正文核查；未引用未读PDF或搜索摘要中的数字。
- **完整性说明：** 未得到同时具备清晰口径、期间与可读正文的南亚移动互联网使用率／地区每GB连接价格，因此不硬凑。设备价格不冒充流量价格。下述历史数据和预测保留原时间，不包装为2026现状。

## 快速索引

| ID | 核心指标 | 指标时期 | 地域／平台 | 来源性质 |
|---|---|---|---|---|
| industry-gsma-ssa-usage-2023 | 移动互联网使用人口27% | 2023基期、2024版报告 | 撒哈拉以南非洲／不限Android | GSMA官方新闻稿 |
| industry-gsma-ssa-device-affordability-2024 | 入门联网设备价格为最贫20%人口平均月收入的99% | 2024报告披露，价格独立采样期未标明 | 撒哈拉以南非洲最贫20%人口 | GSMA官方新闻稿 |
| industry-sensortower-india-downloads-fy2024-25 | 手游下载84.5亿次 | FY2024–25 | 印度／App Store+Google Play | Sensor Tower官方文章 |
| industry-newzoo-mobile-revenue-2025-forecast | 全球移动游戏收入预测1030亿美元，同比+2.9% | 2025年预测、2025-09报道版本 | 全球／mobile，非Android独占 | Mobilegamer转述Newzoo |

## 1. GSMA：撒哈拉以南非洲移动互联网使用率27%

- **报告／文章：**《State of Mobile Internet Connectivity 2024》发布新闻稿，GSMA，**2024-10-23**。
- **统计时期：**2023年基期；2024版新闻稿以“last year”说明新增用户。属于历史基线，不是2026现状。
- **地域／平台：**撒哈拉以南非洲人口；在自有设备上使用移动互联网，不限Android。
- **精确数值：**27%人口使用移动互联网。同一新闻稿列出13%覆盖缺口、60%使用缺口。
- **定义：**使用率不是覆盖率；使用缺口指有覆盖却未使用移动互联网的人口。该指标也不是游戏玩家、Android装机或广告可触达人群占比。
- **原文短摘录：**
  > The least connected region globally is Sub-Saharan Africa, where only 27% of the population are using mobile internet services
- **已核查原始URL：**[GSMA官方新闻稿](https://www.gsma.com/newsroom/press-release/new-gsma-report-shows-mobile-internet-connectivity-continues-to-grow-globally-but-barriers-for-3-45-billion-unconnected-people-remain/)
- **谨慎启示：**已有覆盖不等于所有人都是联网玩家；应验证离线核心循环、弱网可玩、免首启强制登录／大包下载、广告断网或缺货不阻断游戏。
- **限制：**区域平均不能替代国家、城乡、年龄与设备分层，不能据此算Android市场规模。后续ITWeb对2025版报道为25%，但本次未核查两版方法或历史重估，**禁止从27%到25%推断市场萎缩**。本条读取的是官方新闻稿，不声称读过PDF。

## 2. GSMA：SSA最贫20%人口的设备接入负担为月收入99%

- **报告／文章：**同上，GSMA，**2024-10-23**。
- **统计时期：**2024报告发布时披露；**新闻稿未单列设备价格／收入采样起止时间**，不擅自补成某月或明确2023价格。
- **地域／平台：**撒哈拉以南非洲最贫20%人口；入门级可联网设备，不限Android。
- **精确数值：**设备购买价格相当于该群体平均月收入的**99%**。
- **定义：**一次性设备价格÷该收入群体平均月收入；不是99%的用户买不起手机，**不是每GB流量价格、月套餐费或IAA成本**。
- **原文短摘录：**
  > In Sub-Saharan Africa, which accounts for a quarter of the global unconnected population, this rises to 99% of average monthly income for the region’s poorest 20%.
- **已核查原始URL：**[GSMA官方新闻稿](https://www.gsma.com/newsroom/press-release/new-gsma-report-shows-mobile-internet-connectivity-continues-to-grow-globally-but-barriers-for-3-45-billion-unconnected-people-remain/)
- **谨慎启示：**支持把低端设备适配和低进入成本列为测试重点：小体积、低内存、少常驻SDK、短首启。但不能由价格指标推出RAM占比；机型门槛应来自当地真实设备测试。
- **限制：**采样期、国家权重与设备规格未在新闻稿单独披露；该群体不是全体非洲玩家，更不是南亚用户。不能当当前报价，也不能冒充地区流量连接成本。

## 3. Sensor Tower：印度FY2024–25手游下载84.5亿次

- **文章：**《India Mobile Game Insights 2025 — Homegrown Hits Drive 8.45B Downloads》，Sensor Tower，作者Donny Kristianto。
- **文章日期：****2025-06**，网页仅标月份，未标具体日。
- **统计时期：****FY2024–25财政年度**；已读正文未列起止日，不改写成2024或2025自然年。
- **地域／平台：**印度；合并Apple App Store与Google Play。
- **精确数值：****8.45 billion installs＝84.5亿次**；原文称印度按手游下载量为全球最大市场。
- **定义：**App Performance Insights估计下载；**排除预装、重复下载及第三方Android应用市场**。这是下载／安装次数，**不等于独立玩家、活跃玩家、留存用户或付费人数**；也不是Android独立数据。
- **原文短摘录：**
  > India continues to hold its position as the world’s largest mobile gaming market by downloads, with an impressive 8.45 billion installs in FY 2024-25.
- **方法原文短摘录：**
  > excluding pre-installs, re-downloads, and downloads from third-party Android marketplaces.
- **已核查原始URL：**[Sensor Tower官方文章](https://sensortower.com/blog/india-mobile-game-insights-2025)
- **谨慎启示：**支持在印度做分国、小预算获量测试。原文定性提到模拟、街机、益智与本地桌游下载强，可为既有候选池设计测试组，但不是任何具体产品获量便宜或IAA回收高的证明。
- **限制：**缺Android独立拆分、候选产品本地广告收入。原文另提IAP超过4亿美元，**不将其当IAA收入，也不以IAP除下载量计算ARPU**。不把印度下载大盘外推到整个南亚或非洲。

## 4. Newzoo／Mobilegamer：2025年全球移动游戏收入预测1030亿美元

- **来源性质：****公开二手行业报道**；Mobilegamer.biz作者Tom Ivan转述Newzoo《Global Games Market Report》。
- **文章日期：****2025-09-10**；文章未给底层报告精确发布日期。
- **统计时期：****2025自然年预测，2025-09-10报道所述版本**；不是2025最终实绩，也不声称为最新预测。
- **地域／平台：**全球mobile；未分别给Android与iOS。
- **精确数值：****USD 103 billion＝1030亿美元**；该版本同时给出同比**+2.9%**、占全平台游戏收入**55%**。
- **定义：**报道明确在游戏软件及订阅服务（game software and subscription services）收入框架下叙述；**不等于IAA广告收入、广告市场规模或开发商广告净收入**。
- **原文短摘录：**
  > Mobile games revenues are forecast to reach $103bn in 2025 (+2.9% YoY), according to research firm Newzoo.
- **口径原文短摘录：**
  > it estimates mobile will account for 55% of total game software and subscription services revenues this year.
- **已核查二手URL：**[Mobilegamer公开行业报道](https://mobilegamer.biz/data-digest-newzoos-latest-report-aonics-150m-buy-eu-market-analysis-game-milestones-and-more/)
- **谨慎启示：**只能作移动游戏仍为全球重要平台的宏观背景；不能给非洲／南亚IAA项目回收背书。决策仍需当地Android实测留存、展示次数、填充率、eCPM、CPI和净回收。
- **限制／核查方法：**Newzoo官网相关页面此次web_fetch为403；本条采用已读二手报道。Mobilegamer先web_search发现，再web_fetch核查；因正文截断，用Node fetch同一公开URL抽取并读取正文。未读底层PDF与完整方法，因此不扩大收入口径。版本可能已更新；**不能从全球收入推导任何本地eCPM**。

## HTML汇总建议：将边界与数字同屏展示

1. 每张数据卡同时显示“统计时期／发布日期／抓取日期”，不要只显示2025或2026。
2. GSMA设备99%卡标“设备成本，不是流量费；采样期未单独披露”。
3. Sensor Tower卡标“iOS+Google Play；下载≠独立玩家”。
4. Newzoo卡标“二手来源／历史预测／全球／非IAA”。
5. 上述数据仅补行业背景，不替代既有32产品的实证评分，更不构成未验证的本地广告收益承诺。

## 未纳入项目与证据边界

- GSMA SOMIC主入口此次web_fetch返回403；两个2025 PDF链接返回不支持的application/pdf。本次**没有引用PDF数字**。
- GSMA 2024官方新闻稿正文可读，因而使用其明确披露的27%与99%，但不隐藏其历史基期及采样时间缺失。
- 南亚区域使用率和地区每GB连接成本未得到足够完整正文与口径，因此留空，不由全球／LMIC平均数代替。
- Unity 2025趋势文章可读，但多为预测性定性判断，不作为新增量化数据凑数。
