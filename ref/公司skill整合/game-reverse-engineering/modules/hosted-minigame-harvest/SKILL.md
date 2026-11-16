---
name: hosted-minigame-harvest
description: Use when 用户要从宿主商店/分发 App（AHA Games 类）采集内嵌小游戏原包体、美术素材和文案，或要从已有宿主 H5 包贯通采集、拆解、自然运行、原版还原与关卡/美术/埋点/广告持续迭代；也适用于现有 H5 游戏的包体、加载与低内存优化，以及小游戏目录化、包体直链发现及按 gameId 或名称批量出库。
metadata:
  version: "1.4.0"
  updated: "2026-11-10"
  created: "2026-10-20"
  author: bai-lian
  tags: [reverse-engineering, host-app-embedded, minigame, h5game, zipgame, storefront, api-contract, bulk-harvest, asset-catalog, adb, root, md5-verify, index-page, h5-restoration, lifecycle, live-ops, package-optimization, loading, low-memory]
  triggers: [小游戏包体, 拉取包体, 即点即玩, 内嵌小游戏, 宿主小游戏, 游戏商店拉取, 批量拉游戏, 小游戏素材, icon hotgame banner, 游戏介绍页, 索引页, 宿主H5还原, 小游戏全流程, 自然截图, 持续迭代, aha games, net.bat.store, watertube, zip game, 重置立项, 竞品调研, 优化方向报告, 关卡参考竞品, 传音用户画像, H5包体优化, 加载优化, 低内存手机]
---

# 宿主小游戏采集与全生命周期

## 执行卡（先用这张卡，再读正文）

**我管什么**：宿主小游戏从**采集、拆解、原版运行到后续迭代的路由与交付闭环**。批量采集仍是本模块的专门执行流程；引擎识别、各引擎解包、玩法和 H5 美术由对应模块负责，不把采集产物当成玩法分析。完整任务读 [端到端生命周期](references/hosted-game-lifecycle.md)；已有包的 H5 原码路线读 [原版还原与持续迭代](references/hosted-h5-restoration.md)。

包体、加载或低内存优化读 [H5 包体与运行优化](references/h5-package-runtime-optimization.md)：先保护当前有效修改并区分成本，再按引用证据裁剪、按目标平台复测；无需重复采集或套用 Cocos 构建。

**范围边界**：Cocos/Unity/Construct/Phaser 等依实际指纹路由；`gameplay-logic-reverse` 的 Cocos 专属方法不能原样套到其他引擎。

**第一步做什么**：先确认用户目标、交付路径、已有输入及授权。**已取得包体**或已有解包时先核验身份、版本、哈希、只读基线与引擎，不重复采集；从 [端到端生命周期](references/hosted-game-lifecycle.md) 的阶段 0/2 进入。缺包且需要采集时才执行采集 S0：确认宿主归属、下载解压/流式形态和包体落点，再按现有采集链路操作。

**做完怎么算完成**：完整任务按 [端到端生命周期](references/hosted-game-lifecycle.md) 各阶段和用户要求收口，区分静态、浏览器、模拟宿主及真实设备/SDK 证据。以下六条是**仅对采集阶段**的门禁（缺任一条按 `BLOCKED` / `NEEDS_CONTEXT` 报），不能反向套给用户已提供包体的任务：

- [ ] 按任务范围确认可用来源、目标身份/版本与形态；只有需要设备缓存或宿主验收时才要求对应设备证据
- [ ] 每个请求的包体已落盘、格式/完整性核查；来源提供官方散列时逐个比对，未提供时记录本地 SHA-256 并标明无法证明与上游一致
- [ ] 对本任务请求的素材按 magic bytes 核验真实格式及后缀；未请求的素材记 N/A
- [ ] 若请求索引页，引用的本地资源均存在且页面无乱码；未请求记 N/A
- [ ] 按目标范围记录清单，含可获得的身份、来源、散列和状态；仅在要求素材编目时提供对应清单，缺失字段如实标注
- [ ] 交付附未知清单（见 `references/unknowns-ledger-template.md`），写明未打通的接口与未覆盖的目标

**红线（不可违反）**

- **采集阶段区分 UI 运行与实际包体获取**：AHA 来源案例中点搜索结果只进流式 WebView、不落缓存；当前宿主先核验是否实际下载。接口或缓存可取时核验来源与散列；自然 UI 操作仍用于后续玩法取证。
- **不许用文件名当 MD5**：仅在可信来源明确提供对应版本的校验值时比对；没有来源校验值时只报告本地身份哈希，不声称与上游一致。
- **不许按 URL 后缀判图片格式**：必须读 magic bytes 定真实格式再决定后缀。
- **采集请求要节流**：按当前服务限制控制速率、观察并退避；AHA 来源案例用间隔 ≥1.2s，非其他接口通用阈值。
- **核对批量端点实际返回条数**：AHA 来源案例 `offline-home` 单次最多返回 20 条，曾采用 6 条/批；当前端点的上限与批量大小须重新验证，避免静默漏项。
- **不碰账号态与支付**：只用匿名可见的目录/详情接口；不提交登录态、不触发下单/支付路径。
- **不把案例字面值当通用**：域名、路径、字段名、gameId、磁贴尺寸一律重新取证（`DO_NOT_COPY_LITERAL_VALUES`）。

**卡住时按顺序读**：

- 全链路如何从现有包进入、按引擎衔接 → [hosted-game-lifecycle.md](references/hosted-game-lifecycle.md)
- H5 原码自然运行、路线验证、关卡/广告/埋点/美术迭代与交接 → [hosted-h5-restoration.md](references/hosted-h5-restoration.md)
- 迭代中建立关卡可视化编辑器、按用户授权委派 DSH 解码、阶段性将可复用经验写回技能 → [iteration-editor-and-delegation.md](references/iteration-editor-and-delegation.md)
- 重置立项要做平台/用户画像/竞品调研与分析报告（md + 带竞品图 HTML），或找可参考关卡的同玩法竞品 → [reboot-market-analysis.md](references/reboot-market-analysis.md)

- 包体减小却加载不快、动态资源能否删、图片/图集取舍、低 RAM 测量、触屏与异步就绪验证 → [h5-package-runtime-optimization.md](references/h5-package-runtime-optimization.md)
- 用户提供匹配 CombiMons SDK 模板或要求参照其 iframe 广告接入 → [combimons-host-sdk-template.md](references/combimons-host-sdk-template.md)；样本 API/参数须重新核验，模拟不等于真实广告
- 不知道接口有哪些端点 → [store-api-contract.md](references/store-api-contract.md) §1「静态挖端点」
- 端点通了但报参数错 → 同文件 §2「错误码驱动的参数爆破」
- 拿到直链但不确定包体/素材对不对 → [harvest-pipeline-and-gates.md](references/harvest-pipeline-and-gates.md)
- 脚本跑不通（中文乱码 / 报 `无法绑定参数"Id"` / 图片打不开）→ [powershell-harvest-pitfalls.md](references/powershell-harvest-pitfalls.md)
- 要判断"本地缓存版 vs 接口最新版" → 本文件「包体版本关系」

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERAL_DEFAULT`（方法） + `CASE_ONLY_AHA`（AHA Games 实测字面值，见 [store-api-contract.md](references/store-api-contract.md) 附录）。

---

## 1. 适用形态判定

宿主 App 内嵌小游戏有三种形态，**先判形态再选路线**：

| 形态 | 判据 | 包体在哪 | 拉取路线 |
|---|---|---|---|
| **A. 下载解压型（zip 包体）** | `files/h5GameCache/`、`files/*Pool/`、MMKV 有 `local_zip_game_manager` / `statistics_zip_game`；缓存目录里每个游戏有 `gameInfo`（含 `pkgs[].uri`） | 宿主 data 目录 + CDN zip | **优先走接口**（见 §2）；接口不通再从 `gameInfo` 收集直链 |
| **B. WebView 流式型** | 当前观察为点播运行，未发现独立下载包 | 已观察到 WebView 资源与入口；是否有其他下发路径未定 | 记录观察范围，继续按可用来源核查；尚未取得独立包时如实记 `NEEDS_CONTEXT` |
| **C. 动态包 + dex 型** | 宿主下发 `*_dynamic.zip` → 内含 `*.apk` → `classes.dex`（Kotlin/Java，非 JS） | 宿主 `files/` + `cache/` | 走 `engine-identification` 的宿主内嵌章节 + jadx；**不是本模块的 zip 包体路线** |

> 形态 A 的关键证据：缓存目录里存在 `gameInfo` 一类的**每游戏元数据文件**，它通常已经写明 `gameId / 包体直链 / md5 / resourceId`。**先读它，再去挖接口** —— 它能直接给出 CDN 直链模板。

## 2. 两条拉取路线

**路线 1（首选）：商店接口直取**
匿名可用的目录/搜索/详情接口通常同时返回**元数据 + 包体直链**。一次请求即可拿到 `bundles[].url/.md5/.size`，不必进游戏、不必点 UI。优点：可枚举"未玩过"的游戏、可批量、与设备状态无关。

**路线 2（兜底）：设备缓存反查**
接口不可用时，遍历宿主 data 目录里的 `gameInfo`（`find <cache> -name gameInfo -exec cat {} \;`）收集 `gameId → 直链` 映射。缺点：只能拿到该设备已缓存的目标，版本代表缓存时取到的包；与当前接口版本的新旧关系需核验。

两条路线的字段含义与契约还原方法见 [store-api-contract.md](references/store-api-contract.md)。

## 3. 端到端阶段（S0–S5）

每一步的通过判据与门禁详见 [harvest-pipeline-and-gates.md](references/harvest-pipeline-and-gates.md)。

| 阶段 | 动作 | 通过判据 |
|---|---|---|
| **S0 目标确认** | 确认目标、请求范围、可用来源和版本；需要设备缓存时再检查设备权限 | 可定位目标和来源，未知形态单列；接口直取不要求设备/root |
| **S1 落点测绘（按需）** | 需要缓存取包或判断已玩状态时查相关落点与账本 | 在权限范围内记录路径与覆盖；接口或用户给定包无需强制设备取证 |
| **S2 契约发现（按需）** | 根据来源和目标查证端点与必要参数 | 已知 ID 仅需足以取目标的接口；需要搜索/枚举才要求发现端点 |
| **S3 发现集** | 关键字搜索 / 推荐流 / 分类 / ID 枚举，汇总目标 gameId 集合 | 目标集合有 ID 或可解析出 ID；"未玩过"有判据 |
| **S4 拉取** | 逐目标取请求范围内的包体、素材和文案；散列可用时比对 | 对适用项执行 G1–G3，来源无散列时保留身份哈希并标明无法上游对比 |
| **S5 编目交付** | 按需求生成清单、索引页、校验报告和未知清单 | 对请求项执行 G4–G6；未请求的素材/索引记 N/A |

**推荐输入优先级**：用户直接给 `gameId` > 给名称（需解析，有同名歧义风险）> 给分类/关键词（需枚举）。**拿到 ID 就不要用名称搜索**。

## 4. 关键判断

**"未玩过"的定义**：`gameId` 既不在宿主的包体缓存里（无对应 `gameInfo` / 缓存目录），也没有游玩账本记录（如 `game_statistics_kv` 的 `game.opened_<id>`、`game.loaded_<resourceId>`）。两个来源都要查，只查一个会漏。

**包体版本关系（容易搞错）**：
- 接口可能返回当前发布包，设备缓存对应设备下载时的包；以版本、元数据和实际哈希取证，不能未经核验断定哪个更新。
- 同一 gameId 在两处的哈希可能不同；差异要登记，不能直接视为损坏或忽略。
- 用户指定的原包/目标版本是基线，不因接口有新版本就替换；需要当前发布版时可与缓存版另作对照。

**素材字段分工**（不同端点给的字段不同，要拼）：

| 素材 | 通常来源 | 字段 |
|---|---|---|
| icon | 详情 / 批量接口 | `iconPictureLink` |
| **hotgame** | **批量接口（offline-home 类）** | `hotGameImageLink` |
| banner | 详情 / 轻量详情 | `banner` |
| theme | 详情 | `themePictureLink` |
| preview（动图） | 详情 | `imageLink` |
| 文案 | 详情 | `description`（一句话）/ `introduction`（详情）/ `tags` / `source`（开发商） |

> AHA 来源案例的 hotgame 在批量接口取得；仅在用户请求该素材且当前接口证据表明需要时查询对应端点。不要把案例端点或字段当成所有宿主的必经条件。

## 5. 交付物形态

```
<Root>\
  index.html              索引页（搜索 + 分类筛选，本地图片，无外链）
  manifest.csv/json        原包体清单（id/名称/直链/md5/大小/状态）
  art_manifest.csv         素材 + 文案清单（含开发商/评分/分类/标签）
  <gameId>_<安全名>\
     <安全名>.zip           原包体（未解压、未修改）
     gameInfo.json          该包元数据
     art\ icon.* hotgame.* banner.* theme.* preview.*
```

索引页每张卡片应含：**文件夹名**（原文要求，便于和磁盘对账）、icon、banner/hotgame/theme/preview、名称 + gameId、分类/评分/包体大小、开发商、`description` + `introduction`、标签、原包体文件名 + MD5 + 在线入口。

## 6. 本模块文件

| 文件 | 内容 |
|---|---|
| [hosted-game-lifecycle.md](references/hosted-game-lifecycle.md) | 采集、拆解、原版自然运行、路线决策、持续迭代到验收的端到端分阶段路由 |
| [hosted-h5-restoration.md](references/hosted-h5-restoration.md) | 现有 H5 包的原码开发、关卡/埋点/宿主接口、美术替换及证据交接；含 Construct 2 案例边界 |
| [h5-package-runtime-optimization.md](references/h5-package-runtime-optimization.md) | 可迁移的当前版本保护、资源可达性、发布裁剪、加载对照、低内存与生命周期证据；项目数值不作通用预算 |
| [reboot-market-analysis.md](references/reboot-market-analysis.md) | 宿主小游戏重置立项：平台/用户画像/竞品调研分析流程、报告输出规范、踩坑纠错与关卡参考竞品筛选法 |
| [combimons-host-sdk-template.md](references/combimons-host-sdk-template.md) | CombiMons 模板父页面/iframe 广告契约、适配、风险与分层验收；仅匹配模板时使用 |
| [store-api-contract.md](references/store-api-contract.md) | 端点静态挖掘法、错误码驱动的参数爆破、AHA 实测完整契约（`CASE_ONLY_AHA`） |
| [harvest-pipeline-and-gates.md](references/harvest-pipeline-and-gates.md) | S0–S5 细则、素材字段分工、六道门禁 G1–G6 与校验脚本行为 |
| [powershell-harvest-pitfalls.md](references/powershell-harvest-pitfalls.md) | 实测六坑：UTF-8 BOM、单字母函数名被别名抢占、Latin-1 乱码、批量上限、混合图片格式、CSV 转义 |
| [harvest_store_pull.ps1](scripts/harvest_store_pull.ps1) | 通用拉取器（按 ID 或名称，含 MD5 校验与分批复用） |
| [harvest_build_catalog.ps1](scripts/harvest_build_catalog.ps1) | 通用索引页生成器（按 `artFiles` 解析真实后缀） |
| [harvest_validate.ps1](scripts/harvest_validate.ps1) | 门禁校验器（G1 包体 magic / G2 MD5 / G3 素材格式 / G4 引用完整 / G5 乱码），非零退即失败 |
| [landing-log.md](references/landing-log.md) | 落地记录（每次里程碑追加一行） |

## 7. 与相邻模块的衔接

- **上游**：`engine-identification` 的「宿主 App 内嵌功能」章节 —— 用来确认前台归属、区分形态 A/B/C。
- **下游（包体到手后）**：
  - 已有 H5 包做原版自然取证、持续迭代与路线评估 → [hosted-h5-restoration.md](references/hosted-h5-restoration.md)；H5 美术换皮 → `h5-canvas-reskin`，按实际授权区分纯美术与代码/UI 修改
  - 解包/解密/资源恢复 → `cocos-reverse-engineering`（`cc.config.json`、`HEK:`、`.jsc`）或 `unity-extract`
  - 玩法/算法/远程开关 → `gameplay-logic-reverse`
  - 美术换皮 → `skinning-pipeline`（本模块的 `<id>_<名>/art/` 是天然输入）
  - 竞品/策划对标 → 交付物可直接作为对标素材库
- **并行**：`vision-device-testing` 的设备采集边界（本模块只拉取公开目录资源，不采集账号态与隐私数据）。
