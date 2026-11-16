# One Connect 重置迭代分析报告

> 版本 v1.0 · 2026-10-29  
> 分析范围：项目代码（只读）+ AHA SDK 模板（CombiMons）+ Google Play 竞品抓取 + 后台用户国家分布数据  
> 作者：AI 分析，项目负责人审核

---

## 1. 执行摘要

| 结论 | 说明 |
|---|---|
| 现包可用但不可持续 | Construct 2 无源工程，关键 bug 影响留存，Famobi 壳需全部替换 |
| SDK 接入可行 | CombiMons 模板结构清晰：插屏/激励/Banner 均已封装，适配代价低 |
| 用户画像高度一致 | 巴基斯坦+印度+尼日利亚 = 37%，全部为中低端传音设备+流量贵+弱网 |
| 品类窗口期存在 | 该地区连连看头部 Boombox 5M+，但竖屏+本地化+激励体系的产品空缺 |
| 重置策略 | 在现有 H5 包上直接改造，不重建引擎；重点改广告体系、竖屏适配、本地化、关卡曲线 |

---

## 2. 项目现状诊断

### 2.1 技术债清单（基于代码逆向）

| 问题 | 文件定位 | 严重度 |
|---|---|---|
| 无 `.capx` 源工程，`data.js` 是生成物 | `baseline/data.js` 129KB | 🔴 高 |
| 横屏 1280×720，手机竖屏下画面极小 | `game/game.html` viewport + `data.js` 末尾 `1280,720` | 🔴 高 |
| Famobi 包 ID / analytics / `v1.js` 残留 | `game.html`、`custom.js`、`html5games/` | 🔴 高（版权+品牌） |
| `showGameLoadingCompleted` 未定义时白屏/报错 | `custom.js` → `top.h5_sdk` | 🔴 高 |
| `showAd` 缺失时结算页无主页按钮，无法重开 | `阶段说明.md` 验证记录 | 🔴 高（留存伤害） |
| 胜/败均调插屏，无激励广告，无频控，不 await | `custom.js` EVENT_LEVELSUCCESS/FAIL | 🔴 高（收益低+体验差）|
| 随机棋盘无可解性保证 | `board-hooks.js`、`开发说明.md` | 🟡 中 |
| 埋点仅内存缓存，无上报 | `host-adapter.js`、`event-hooks.js` | 🟡 中 |
| Famobi CSS `play.css`（107KB）、Famobi JS 无用依赖 | `html5games/gameapi/` | 🟡 中 |
| 真机性能空白（仅桌面 Chrome 验证） | `开发说明.md` BLOCKED | 🟡 中 |

### 2.2 包体现状（baseline 84 文件，3.0MB）

| 类型 | 文件数 | 大小 |
|---|---|---|
| PNG 图集 | 55 | 1.83 MB |
| JS（含 c2runtime/jQuery/Famobi）| 9 | 0.79 MB |
| OGG 音频 | 12 | 0.31 MB |
| CSS（Famobi play.css）| 1 | 0.11 MB |
| 其他 | 7 | 0.04 MB |

**结论**：原包 3MB 远低于 20MB 上限，改造后目标 ≤4MB（含新美术）。

---

## 3. AHA SDK 接入分析（CombiMons 模板）

### 3.1 架构模式

```
宿主 AHA App
  └── 外层 index.html（SDK host）
        ├── adsdk_1.8.0.0.js（hippoobox.com）→ window.h5sdk
        ├── Banner（底部 50px，320×50 AdSense）
        └── <iframe> game/index.html  ← 游戏放这里
```

### 3.2 SDK API 契约

| API | 调用时机 | 回调 |
|---|---|---|
| `h5sdk.gameLoadingCompleted()` | 游戏资源加载完成时 | 无 |
| `h5sdk.adBreak({ type:"preroll" })` | 游戏启动时自动播放开屏广告 | `adBreakDone` |
| `postMessage("next")` + `MIAD_NEXT._callback/_failback` | 插屏（关卡间）| `_callback`=看完，`_failback`=失败/跳过 |
| `postMessage("reward")` + `MIAD._callback/_failback` | 激励视频 | `_callback`=看完发奖，`_failback`=不发奖 |

**关键约束**：
- 插屏有 45 秒频控（`data-ad-frequency-hint: "45s"`），调用失败时 `_failback` 必须也能让游戏继续
- 激励视频 `_failback` 不发奖励，但不能卡住游戏
- Banner 占底部 50px，竖屏 UI 设计需为 Banner 预留空间，游戏有效区域 = `calc(100% - 50px)`
- 宿主存在时（`window.a_bridge`）游戏才加载到 iframe，否则直接加载 `game/index.html`（本地调试路径）

### 3.3 现有代码改造点

| 现状 | 需改为 |
|---|---|
| `window.oneConnectHost.showAd("Interstitial")` | `window.parent.postMessage("next", "*")` + `MIAD_NEXT` 回调 |
| `window.top.h5_sdk.showGameLoadingCompleted()` | `window.parent.postMessage("gameLoadingCompleted","*")` |
| 广告调用不 await | 每次调用前先注册 `MIAD_NEXT` / `MIAD`，在回调里继续游戏 |
| 无激励广告 | 失败时增加 `postMessage("reward")` 入口，发复活/加时奖励 |

---

## 4. 用户国家分布分析

### 4.1 后台数据（Top 10，总 DAU 约 2170 万）

| # | 国家 | DAU | DAU 占比 | H5play 用户 | 设备特征 | 语言优先级 |
|---|---|---|---|---|---|---|
| 1 | Pakistan | 3,014,850 | 13.88% | 2,360,978 | TECNO/Infinix/itel，2-4GB RAM | **Urdu** + English |
| 2 | India | 2,869,854 | 13.21% | 2,137,461 | itel/TECNO，低端 Android | **Hindi** + English |
| 3 | Nigeria | 2,141,211 | 9.86% | 1,394,097 | TECNO/Infinix，主流 4G | **English** |
| 4 | (null) | 1,161,644 | 5.35% | 920,797 | 无 country 的廉价机 | English 兜底 |
| 5 | Philippines | 1,050,449 | 4.83% | 771,435 | Infinix，竞争激烈 | **Filipino** + English |
| 6 | Indonesia | 948,714 | 4.37% | 621,830 | TECNO/itel | **Bahasa Indonesia** |
| 7 | Bangladesh | 884,312 | 4.07% | 648,347 | itel/TECNO | **Bengali** |
| 8 | Côte d'Ivoire | 497,106 | 2.29% | 304,706 | itel，流量极贵 | **French** |
| 9 | Venezuela | 453,073 | 2.09% | 321,406 | Infinix，近年扩张 | **Spanish** |
| 10 | Kenya | 449,094 | 2.07% | 303,365 | TECNO，English 强 | English + Swahili |

### 4.2 关键洞察

1. **南亚双头（巴+印，27%）是第一优先级**：两国合计接近 600 万 DAU，均为低端设备，流量敏感，网络不稳定。巴基斯坦 H5play 转化率（78%）高于印度（74%），说明 H5 场景适配已经较好。
2. **尼日利亚（10%）是非洲头号市场**，H5play 转化率（65%）偏低，可能因为 2G/3G 比例更高，说明首屏速度是关键。
3. **"null" 国家 5.35%**：廉价设备无 SIM 或未授权 location，英语 + 简化 UI 是唯一选择。
4. **性别数据存疑**：用户自己指出数据可能不准（一家共用一台手机），不应基于性别做内容区分。
5. **菲律宾、印尼、孟加拉合计 13%**：东南亚扩张明显，这三个国家年轻用户比例高、社交分享动力强。

### 4.3 语言优先级（建议分阶段）

**Phase 1 必须**：English、Urdu、Hindi、Bahasa Indonesia  
**Phase 2 按 DAU 排序**：Bengali、Filipino、French  
**Phase 3 补全**：Spanish、Swahili  

对于 H5 游戏，文字量极少（按钮、倒计时、结算分数），每语言翻译量 < 50 词，实现代价极低。

---

## 5. 目标用户画像

| 维度 | 特征 |
|---|---|
| 设备 | 2–4GB RAM，Mediatek Helio G36–G85，720×1560~720×1640 屏，Android 10–13 |
| 网络 | 流量按 MB 计费，2G/3G 并存，断网随时发生 |
| 游戏习惯 | 单手竖屏，碎片化（单次 3–8 分钟），无付费意愿 |
| 偏好 | 强颜色反馈、消除爽感、本地元素（动物/食物/节日）|
| 痛点 | 加载慢、没网玩不了、广告卡死游戏流程、文字看不懂 |

---

## 6. 竞品分析

### 6.1 连连看赛道（直接竞品）

| 产品 | 开发商 | Google Play 下载 | 评分 | 核心差异 |
|---|---|---|---|---|
| Onet - Connect & Match Puzzle | Boombox Games | **5M+** | 4.5 ⭐ | 竖屏、多主题、关卡地图、干净 UI |
| Onet Connect - Tile Match | TerranDroid | 1M+ | 4.0 ⭐ | 功能完整但 UI 陈旧 |
| ONET Mahjong Connect Game | **Famobi**（原游戏！）| 100K+ | 4.3 ⭐ | 原版，横屏，已更新至 2026.6 |
| Tile Connect | Higgs Studio | **50M+** | 4.3 ⭐ | 竖屏变体玩法，关卡制 |
| Tile Connect | Azur Games | 5M+ | 4.5 ⭐ | 横竖屏适配，简洁风 |

**重要风险**：Famobi 的 `com.famobi.onetconnectclassic` 就是本游戏原版，2026 年 6 月还在更新。重置版美术、名称、音频必须完全原创，否则存在版权纠纷风险。建议与版权方确认授权状态。

### 6.2 三消槽位（同区域强势品类，间接参考）

| 产品 | 下载 | 核心机制 |
|---|---|---|
| Tile Explorer - Triple Match | 100M+ | 槽位消三，关卡地图，装修元系统 |
| Tile Club - Match Puzzle | 100M+ | 同类，每日挑战，强留存钩子 |
| Triple Tile: Match Puzzle | 50M+ | 三消变体，Tripledot 出品，高品质 |
| Tile Match: Triple Puzzle | 50M+ | 情感叙事驱动，收集元素 |

**启示**：这些产品在巴基斯坦/印度/尼日利亚均排名高于经典连连看。它们成功的共同点：**关卡地图进度感 + 激励复活 + 轻元系统**。连连看的迭代应借鉴这些留存机制，而不是停留在"计时消除"的功能集。

### 6.3 该地区视觉风格趋势

基于头部产品研究，总结如下规律：

| 维度 | 趋势 |
|---|---|
| 配色 | 高饱和暖色主调（橙、黄、绿）；背景深色或渐变；牌面亮色重描边 |
| 牌面 | 大尺寸、粗黑描边、填充色与轮廓色对比强（适配低分辨率屏 + 户外强光）|
| UI 风格 | 圆角厚按钮，图标先于文字，数字大而清晰 |
| 反馈 | 消除时粒子喷射 + 音效 + Combo 数字弹出；结算时金币/星级动画 |
| 主题 | 动物（非洲/亚洲本地物种）> 水果 > 食物；斋月/圣诞限时主题是常见做法 |
| 排行榜 | 假玩家榜单（伪社交）已是行业惯例，增加竞争感 |

---

## 7. 优化重构方向

### 7.1 广告体系重构（优先级最高，直接影响 ARPDAU）

**现状问题**：胜利失败都弹插屏，无激励，结算卡死。

**目标架构**：

```
开屏 → preroll（SDK 已配，维持）
局内 → 不插广告
关卡失败 → 弹"激励视频 → 复活/加时"选项（主收入来源）
            用户拒绝 → 结算页（不强插插屏）
关卡胜利 → 结算页 + "激励视频 → 金币×2"（可选，不强制）
每 N 关  → 插屏（N≥3，且距上次 >45 秒）
菜单页   → Banner 常驻（SDK 已配）
```

**接入方式（对接 CombiMons SDK）**：
```js
// 失败时调激励（复活）
function offerRevive() {
    window.parent.MIAD = {};
    window.parent.MIAD._callback = () => { revivePlayer(); };   // 看完 → 复活
    window.parent.MIAD._failback = () => { showGameOver(); };   // 跳过 → 直接结算
    window.parent.postMessage("reward", "*");
}

// 关卡间插屏（非必须等待结果）
function showInterstitial(onDone) {
    window.parent.MIAD_NEXT = {};
    window.parent.MIAD_NEXT._callback = onDone;
    window.parent.MIAD_NEXT._failback = onDone;   // 失败也继续流程
    window.parent.postMessage("next", "*");
}
```

### 7.2 竖屏适配

原版 1280×720 横屏，目标 720×1280（16:9竖屏基准）或 720×1560（20:9长屏）。

改法：
- 棋盘从 12×6 → 10×8 或 8×10（竖向更多行），保持牌面尺寸不缩小
- Banner 区 50px 从棋盘可用区剪掉，棋盘向上偏移
- 顶部状态栏（分数/时间/关卡）横向收窄布局
- `data.js` 中 `1280,720` → 通过 `canvas` 动态设置 scale + viewport，或直接改 Construct 2 数据参数

### 7.3 关卡设计优化

| 问题 | 建议 |
|---|---|
| 全部关卡 300 秒，无难度区分 | 前 5 关 240 秒宽松入门，之后每章缩短 15 秒，后期关卡 120 秒 |
| 随机棋盘无可解性保证 | 生成算法改为：先随机成对放置 → BFS 验证连通性 → 不可解时重新洗牌，最多 3 次 |
| 单主题一次解锁 | 前 3 关引导 → 第 4 关解锁甜点主题 → 第 8 关解锁水果主题，增加探索感 |
| 无关卡地图 | 做 3×10 = 30 关地图，按章节分 3 章（动物/甜点/水果）；30 关后循环+加难度 |
| 无每日挑战 | 日期哈希生成固定棋盘，所有玩家同一天同一关，天然伪社交 |

### 7.4 美术重置方向

**风格目标**：竖屏 × 厚描边扁平卡通 × 高饱和暖色 × 本地动物主题

**牌面设计规范**：
- 尺寸：64×64px 有效内容，描边 3px 黑，背景圆角矩形
- 每主题 20 张，同主题内色相间隔 ≥30°（避免色弱混淆）
- 主题一（**非洲/亚洲动物**）：狮子、大象、猴子、孔雀、犀牛、火烈鸟、老虎、鳄鱼、蝴蝶、斑马……优先选择用户国家本地物种
- 主题二（甜点）：保持，颜色比现版更鲜艳
- 主题三（水果）：保持，增加芒果/番木瓜等南亚/非洲本地水果

**背景/UI 色方案**：
- 深色背景：`#1A1A2E`（深藏蓝）或 `#0D1117`，避免强光反射
- 主色调：`#FF8C00`（橙）+ `#FFD700`（金）→ 按钮、星级、奖励
- 功能色：`#4CAF50`（成功绿）、`#F44336`（失败红）、`#2196F3`（提示蓝）
- Banner 安全区底部背景颜色与 SDK 外层页面一致（白色）

**生图工单（AI 负责生产）**：
1. 牌面图集：20 张动物 × 3 尺寸变体 → 合成 512×512 图集 × 1 张
2. UI 按钮组：开始、暂停、重玩、主页、提示、洗牌 × 正常+按下 2 态
3. 背景：3 种章节背景（草原/糖果城/果园），1024×2048 竖屏
4. 特效帧：消除粒子、连线光带（序列帧，≤8帧）
5. 结算弹窗：胜利/失败各 1 张底板，星级 3 档

**版权隔离**：现有 `autoshuffle-sheet0.png`、`bonus*.png`、`credits-sheet0.png` 等 Famobi 原图全部替换，不保留任何原版图集帧。音频全部替换为免版权素材或 AI 生成。

### 7.5 性能优化（低端机）

**目标**：冷启动 ≤3 秒（3G），对局 ≥50 FPS，JS 堆 ≤50MB，包体 ≤4MB。

| 优化项 | 具体做法 |
|---|---|
| 删除无用依赖 | 删除 `html5games/`（Famobi 壳 ~140KB），删除 jQuery（88KB），c2runtime 保留但精简 |
| 图片压缩 | PNG → pngquant/TinyPNG（无损压缩约 40%），考虑 WebP（Android WebView 5+ 支持） |
| 音频 | 保留 OGG，删除重复的 M4A；BGM 延迟加载 |
| 棋盘内存 | 牌对象池化，避免频繁 GC |
| 首屏 | 只加载菜单+默认主题资源，其余主题图集异步预加载并 localStorage 缓存 |
| 断网 | Service Worker 缓存全部静态资源（本地 AHA 环境需确认支持） |

### 7.6 本地化

**实现方式（极简）**：
```js
const i18n = {
  en: { start:"Start", hint:"Hint", shuffle:"Shuffle", win:"Level Complete!", fail:"Time's Up!" },
  ur: { start:"شروع کریں", hint:"اشارہ", shuffle:"ملائیں", win:"!منزل مکمل", fail:"!وقت ختم" },
  hi: { start:"शुरू करें", hint:"संकेत", shuffle:"फेरबदल", win:"स्तर पूरा!", fail:"समय समाप्त!" },
  id: { start:"Mulai", hint:"Petunjuk", shuffle:"Acak", win:"Level Selesai!", fail:"Waktu Habis!" },
  // ...
};
```
检测语言：`navigator.language` 前两位映射，默认 `en`。
阿语/乌尔都语需要 RTL 翻转，按钮从右到左排列；数字显示建议保留阿拉伯-印度数字（٩٨٧٦...）。

### 7.7 伪排行榜

- 本地存储 `localStorage` 保存玩家昵称（首次进入随机生成本地名字）
- 榜单前 10 名：8 个预制"玩家"（从目标国家名字库随机抽取）+ 玩家自己
- 分数：每天更新一次预制分数（从当前玩家分数为基准 ±15% 随机生成）
- 无需网络，完全离线运行

---

## 8. 版权风险提示

`com.famobi.onetconnectclassic`（Famobi 的原游戏）2026 年 6 月仍在 Google Play 更新。本项目 `game/` 目录代码中含有 `window.famobi_gameID = "onet-connect-classic"` 及 Famobi analytics 全套。

**建议在重置前确认**：
1. 是否持有 Famobi 原版的合法授权（重新分发许可）？
2. 如无授权：玩法规则本身不受版权保护，但代码、图集、音频需全部换成原创。
3. 游戏名称建议更换，避免与 "ONET Mahjong Connect" 直接撞名。

---

## 9. 路线图

| 阶段 | 时间 | 工作内容 | 交付物 |
|---|---|---|---|
| P0 确认 | 1–2天 | 版权确认；平台确认 localStorage/SW 支持；获取具体广告位 ID | 需求确认单 |
| P1 止血 | 1周 | 替换 SDK 适配层（host-adapter.js → postMessage）；修复结算 bug；限频插屏；激励复活入口 | 可上线止血版 |
| P2 竖屏 | 1–2周 | 竖屏布局改造；Banner 安全区；棋盘行列调整 | 竖屏版 |
| P3 美术 | 2–3周 | AI 生产全套美术；音频替换；Famobi 元素清零 | 全新皮肤版 |
| P4 关卡 | 1周 | 30 关设计；可解性生成算法；每日挑战 | v1.0 正式版 |
| P5 本地化 | 1周 | 7 语言接入；RTL 处理；本地主题（斋月等）| 多语言版 |
| P6 数据 | 持续 | 埋点上报（若平台支持）；难度曲线调优 | 迭代版本 |

---

## 10. 关键问题（仍需你确认）

1. **版权**：Famobi 原版授权状态？
2. **平台支持**：AHA 宿主 WebView 是否支持 localStorage？是否支持 Service Worker 离线缓存？
3. **广告位 ID**：实际上线时需替换 CombiMons 模板中的 `ca-pub-3214612466403714` 和 `appId: 5026112` 为本项目的真实 ID。
4. **游戏名称**：重置后叫什么？建议换一个，避免 Famobi 纠纷。
5. **图国家数据完整版**：当前只有 Top 10，其余国家是否值得针对性本地化（如图表后续行）？

---

*分析证据：`game/game.html`、`custom.js`、`baseline/data.js`（字符统计）、`迭代接口文档 01–04`、CombiMons SDK 模板（4 文件）、Google Play 搜索结果（NG/PK/BD/KE/EG 五国区）、后台用户国家分布截图。*
