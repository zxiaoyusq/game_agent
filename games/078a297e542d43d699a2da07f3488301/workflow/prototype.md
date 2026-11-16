# Carrom 启动资源依赖与延迟加载可行性只读复核

## 1. 结论与范围

**结论：PASS（旧包静态依赖复核）；NEEDS_CONTEXT（迁移到当前 f996）；BLOCKED（动态、离线宿主及目标设备性能验收未执行）。**

选定的最小非首屏候选族是 **Royal Arena 匹配/对局背景对**：`bg_4` 与 `matchmaking_bg_royalarena_slices`。选择依据是注册表、桌台配置、隐藏界面初始化、匹配构造器和同步缓存消费者的交叉证据，不是名字含 Royal Arena。

这两项目前属于全量启动加载屏障，但静态查到的首次业务消费在选择该桌台后的**匹配构造器内部**，不是开局后。因而可以研究拆出首屏加载集合，**不能批准“从 bitmaps 循环排除后照常执行”**。必须在首次匹配构造前完成可用性检查，并处理旧逻辑先扣费保存、后构造界面的事务风险。

本轮只执行原型阶段的只读审查与验证方案设计：不修改游戏源码、HTML、资源、SDK、构建脚本或发布物；不执行旧包脚本；不安装依赖、不构建、不发布、不推进后续阶段。仅增加本报告及逐字节研究文本副本。没有独立读取当前 f996 完整源码。用户给出的日期和版本角色照录，不从文件名推定最新版。

棋盘/回合制指南用于证据与状态边界方法，不把 Ludo 路径、安全格、精确终点规则套到 Carrom；本轮不重新设计玩法。Canvas Web 是项目流程配置，**旧参考实际是 PIXI + Planck + Howler**，本轮不迁移引擎。报告中文；后续验证界面维持默认英文，建议失败/等待提示使用 `Loading arena…`、`Arena unavailable. Retry or go back.`、`Retry`、`Back`，不改本次旧界面。

## 2. 输入身份与可复查路径

参考路径（相对 `ref/`）：

`mcp-inputs/mac-codex/736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99/Carrom_current_development.zip`

- 用户指定角色：2026-11-12 旧开发包，不代表目前 f996。
- ZIP 实际 SHA256：`736fd619432f30a9c444492c68809cb8876d7162c777ba883f1b8b857f677b99`。
- 工具清单：335 个条目；总展开量 5,099,606 bytes。不是 HTTP 传输量，不是当前项目包体，也未取得 ZIP 文件字节大小。候选延迟加载不会自动减少离线 ZIP 下载/解包总量。
- 当前工作区初始目录清单为空，没有可独立核验的 f996、Git HEAD、当前 dist 或当前构建配置。

证据文件身份：

| 编号 | ZIP 内原始路径 | SHA256 | 研究副本 |
|---|---|---|---|
| E01 | `development/index.html` | `3fb70363f17dc63925ffa5b60b2bb2a3a335183f525876594abe62e7d6ed6bf4` | `/reference-inputs/old-development/index.html` |
| E02 | `development/game.html` | `59227ad5cf749e3776388bf01385d5b1ee66e64cebd480850996b92314022235` | `/reference-inputs/old-development/game.html` |
| E03 | `development/js/game.js` | `3140ae1bd16fd91b6c025fc3641f2ff41e9f26e2b7200c94810199ada22a1573` | `/reference-inputs/old-development/js/game.js` |
| E04 | `development/developer_v2.js` | `ecaccd063d47e7a8e002f2e697282e9a3ba93c1aa3cbfd24d3b6c3cf26ef3c47` | `/reference-inputs/old-development/developer_v2.js` |
| E05 | `development/js/libs/pixi.min.js` | `e6c608465f403d0201603f31b369cfecea242eaff4b905b6fbaa6efc42c8e57e` | ZIP 直接读取字符 0–999，头部为 pixi.js v4.8.9；未提取/执行 |
| E06 | `development/js/disc-rules.js` | `95cb52107dc0d6ca62d915478169443e725234c240bd2c0da3a6401e44b4e008` | ZIP 直接读取全文；未提取/执行 |
| E07 | 本次用户请求内 f996 启动循环及生命周期片段 | 无独立源码哈希 | 调用方提供文本，不赋予 E03 的版本/行号 |
| E08 | 本次用户提供的桌面慢资源实验摘要 | 无原始日志/样本 | Royal Arena 背景人工延迟 3 秒可延后 ready；仅历史线索 |

下文 `game.js:L…` 均指 E03 原文件一基行号，研究副本保持原字节，不是另行格式化的源码；HTML 行号同理。ZIP 清单搜索了 `.js`、`.html`、`assets/tables/4/`；没有全包解压或完整素材提取。

### 混淆字符串的静态交叉核对

E03:L12212–12220 的解码器减去 `0xcf`，E03:L12559–13583 为 1025 项字符串表；L2–23 轮转表并以 `0x283e4` 校验。静态核对左旋 481 项的对应位置：

- `0x487 → init`（L12967），调用 L11419，与 L375–378 的 init 实现一致。
- `0x314 → register`（L12596）；`0x27d → loader`（L13470）；`0x3d7 → add`（L12791）；`0x1e0 → load`（L13313）。
- `0x2f7 → progress`（L12567）；`0x348 → fromFrame`（L12648）；`0x335 → texture`（L12629）；`0x304 → utils`（L12580）；`0x299 → TextureCache`（L13498）。
- `0x41b → bg_4`（L12859）；`0x4b6 → matchmaking_bg_royalarena_slices`（L13014）；`0x34b → assets/matchmaking/matchmaking_bg_royalarena_slices.png`（L12651）；`0x118 → cover`（L13113）；`0x3ad → loadTable`（L12749）。

校验式对应数值为 `-245144 + 369086/2 + (3/3)*(1199816/4) - 737660/5 + 1065888/6 + (553861/7)*(24/8) - 3078018/9 = 164836 = 0x283e4`。这是人工静态表索引与算术复核，不是执行解混淆或证明浏览器启动成功。函数路径的认定同时使用明文属性/字段交叉验证，不把旧混淆编号直接移植到 f996。

## 3. 入口、注册与启动屏障

### 入口依赖

1. E01 `index.html:L51` iframe 指向 `game.html`；L65、L76 另有外部广告 SDK 与 `h5sdk.init`。外壳离线失败与图像加载失败应分层诊断，不能据此认定当前离线项目也依赖这些远程服务。
2. E02 `game.html:L30` 尝试查询 `../..` 的 Service Worker 注册并注销；这不是离线预缓存策略，也没有证明其他 scope/缓存均清除。
3. E02:L33–35：`local-save.js → developer_v2.js → CarromLocalSave.install()`；L62 的 CSS 首屏底图为 `assets/preloader/bg.png`；L76–84 定义 Simonetta TTF 并以隐藏字符触发字体使用。
4. E02:L99–103：Howler → PIXI → Planck → disc-rules → game.js，普通脚本按页面顺序加载。E03:L368 以 `box2d = planck` 使用物理库。E05 头部直接证实 PIXI v4.8.9，未核实其所有 Loader/Sprite 细节。

### 从入口到 ready 的静态调用链

```text
game.html 加载 game.js
  → game.init()                           game.js:L11419，L375–378
  → _0xc37276()                          L906–910
      → _0xa07a9b()                      L941–990
          PIXI Application、ticker、首屏进度对象
          Sprite.fromImage 预加载 UI      L964–989
      → _0x358d16()                      L992–1124
          new Howl 注册音频                L994–1115
          for (key in src.bitmaps)
            PIXI.loader.add(key, url)     L1116–1121
          loader.on('progress', …)
          loader.load(_0x16b945)          L1122–1123
  → _0x16b945(loader, resources)          L5585–5587
      → _0x3690db()                      L1125–1168
          → _0x5ecd40() 读取/恢复存档      L1170–1185
          → _0xf8ddc7() 构造界面与世界     L1373–1743
              游戏场景/默认纹理             L1462–1475
              隐藏 lobby、wheel、select、shop L1689–1737
              → _0x3771eb() 显示 lobby    L1738，L2044–2073
              注册输入、render、game.ready L1739–1742
          → _0x1d7cac() 启动 ticker      L2031–2035
```

因此旧包的 `ready` 位于整批 bitmaps 的 load 回调之后，而且在界面构造之后。`_0x16b945` 不检查传入的 resources/error（L5585–5587），所读启动段只注册 progress，未见资源失败终态 UI。**load 回调到达、progress=100 或发送 ready 均不足以证明所有 texture 可用**；失败时库是否继续完成、具体异常表现仍需复测。

音频通过 Howl 独立注册，未在此段找到与图片队列共用的 ready 检查；不要把全部启动时间归因于候选图片。E07 提供的循环与此旧包在结构上相似，但它未附全量字符串表、bitmaps、消费链或 build 身份；E07 多了 `_carromConnectLifecycle()` 调用，不能据旧包证明当前全部同步消费者不变。旧包 `pause/resume` 自身还是空函数（E03:L410–411），不能拿它验收当前宿主暂停实现。

## 4. 候选族边界：Royal Arena 匹配/对局背景对

| key / 真实包内文件 | 注册证据 | 配置证据 | bytes / SHA256 |
|---|---|---|---|
| `bg_4` / `development/assets/tables/4/royal_arena_table_01_background.png` | E03:L309 为明文 URL | `_0x2dad3f[4].bg`，L727–736、L12859 | 9,160 / `404b47c743ecb9de90f409266a5542032a5cb84253bf686d858fc9383a5cf6c7` |
| `matchmaking_bg_royalarena_slices` / `development/assets/matchmaking/matchmaking_bg_royalarena_slices.png` | E03:L170、L12651 | `_0x2dad3f[4].cover`，L735、L13014 | 15,472 / `a7e7035a508c9f900ead45d605c10b9f55cf8e8dd7828866700f40acaa647dbb` |

文件存在及散列来自 ZIP 真实条目清单。两项合计原文件 **24,632 bytes**，不是可承诺的 HTTP 减量或内存收益；未读取图片像素尺寸/视觉内容，不估算 GPU 内存。

### 为什么是非首屏候选，而非已批准的安全延迟项

- 默认游戏场景的背景在 L1466 同步 `Sprite.fromFrame(bg_1)`；匹配构造器先用 `bg_3`（L8994）及 Mumbai 的 cover（L9129–9136），然后在 L9154 调用 `loadTable`。Royal 背景对不是这些默认构造的明文/已核对 token 输入。
- 搜索 `bg_4`/对应 token、`_0x2dad3f`、bg/cover 属性消费者后，所读路径显示该对在桌台 4 被选中时进入匹配构造器；这只是已识别的静态路径，没有声称覆盖所有运行中反射、SDK 或当前 f996 分支。
- 保留 `logo_4`、桌面、角框、击球条、棋子、教程、字体及首屏素材的原加载策略。本轮不将整个 `assets/tables/4/`、`assets/select/`、`assets/matchmaking/` 目录当一个可延迟批次。
- **特别排除 Royal 选桌卡资源**：L678–684 定义选桌 base/logo；L1716 在启动时构造隐藏 `_0x22a07c`；L9571–9605 遍历所有桌台构造 `_0x40d778`；L9419–9426 在卡片构造中同步 `fromFrame(base/logo)`。即使 Royal 卡片在远端滚动页、未解锁或未显示，这些卡片素材也已被首屏前代码读取。名称/可见性不能支持安全延迟。

### 首次使用、同步依赖与不可延后的边界

```text
lobby 真实 play 输入
  → _0x48e98f(mode)                 L1701–1704，L2074–2087
      显示选桌页、设置 mode / coins / states
  → select 事件 _0x4d0a10(tableId)   L1724，L2455–2463
      _0x408018 = tableId
      随机先手
      扣除桌台 fee → _0x3a0318 保存
      其他原调用 → _0x3153fe()
  → new _0x104b9b(tableConfig, …)    L2431–2442
      → 构造器 _0x3875cf             L8990…
      → this.loadTable(tableConfig) L9154
          this.bg.texture = TextureCache[config.bg]       L9364–9365
          this.logo.texture = TextureCache[config.logo]   L9366–9367
          this.cover.texture = TextureCache[config.cover] L9368–9369
      → startRoll                   L9155，L9371–9394
  → 加入 stage / 注册动画事件        L2443–2453
  → start 事件移除匹配对象
      → _0x1260d2()                 L2451–2452
          再读 TextureCache[config.bg]                   L1847–1848
          同步换 logo/table/corners/bar/bar_2 等          L1849–1871
          显示游戏场景 → _0x5480e3() 开新局              L1904–1905
```

**第一读取点是 L9364–9369，在匹配对象加入 stage 前，早于 `start`/`_0x1260d2`。**只在开局函数里等待，或等匹配动画结束才加载，已经太晚。当前 code 没有“texture 缺失则 await”契约，改循环不会自动把缓存读取变成异步加载。

守住同步 `TextureCache` 契约最保守的研究路线：先准备背景对，检查二者及既有 logo 均可用，再由原匹配 owner 一次进入构造；随后保持原开局同步消费不变。需要等待状态时停留在可返回的选桌状态，不在正在运行的匹配动画/物理 tick 中晚到替换主题。更改扣费/保存顺序、失败退款或引入回退主题均是后续明确授权的实施事项，本轮不改、不假定批准。

## 5. 必须解决的风险与实施门槛

| 风险 | 旧包证据/适用边界 | 保守门槛与应验行为（尚未实施） |
|---|---|---|
| 加载失败、404、解码失败、超时、部分成功 | L9364–9369、L1847–1848 无资源可用检查；L5585–5587 不检查结果 | 两项全部 ready 才提交；失败/超时必须收敛到可重试/可返回 UI，无无限等待、白图或 undefined texture。不能仅检测 cache key 存在，应检查可用尺寸/有效 baseTexture 并真实渲染。具体 PIXI 错误形态未实测。 |
| 扣费与存档 | L2460–2461 先扣 fee 并保存，L2463 才构造匹配 | 加载等待/失败不扣费；取消不扣费；成功只扣一次。优先把资源准备放在原有业务事务之前并重校验余额/模式/桌台；若必须改变保存/退款契约需独立评审，不以视觉 fallback 掩盖失去金币。 |
| 并发、重复点击、竞态 | L2455–2463 仅上界 guard，没有已查到的加载 single-flight；L2437 新建匹配对象 | 同族同版本共用一个 in-flight 请求，但每个进入意图有独立 epoch/token；相同点击至多一次构造、扣费、保存。部分失败后可控重试，失败 Promise 不永久毒化缓存。不能向仍在 load 的全局启动队列任意重复 add。 |
| 重入、模式/桌台改变 | `_0x408018`、`_0x5d148e` 是共享变量；L2078、L2458 设置它们；L2452 回调不捕获桌台快照 | 等待前捕获请求身份，完成时核对当前意图、scene、mode、table、余额；旧结果只可缓存，不可切界面、扣费或开局。避免一轮旧匹配 start 用新的全局桌台开局。 |
| 返回、关闭、重开 | L1723 返回 lobby；L2047–2053 隐藏旧 scene；L2451 removeChild 不是 destroy；L1768 roundId++ | 返回立刻撤销“进入权”，允许资源请求继续填缓存但不得 resurrect 旧界面。取消不依赖定时器；清理监听器、匹配 Tweener/定时回调。roundId 在开局才增，不能直接充当之前的选桌加载 epoch。 |
| 暂停/后台/宿主恢复 | E07 有生命周期注册但未读到实现；E03:L9371–9394 有原生 setTimeout；L2031–2039 ticker 控制 | 加载完成不解除用户/宿主/广告合法暂停；恢复后由原 owner 决定提交。分别测 hidden、宿主 pause、resume、返回后 resume；不能只检查变量或 ready 消息。 |
| 离线首次进入 | 包内有文件不证明 URL 在实际宿主可读取；E02:L30 注销 SW，E01 有远程外壳 | “按需”只允许按需解码/上传或从已随包交付的本地资源取用，不转成首次联网下载。首次离线冷启动且从未进过 Royal，仍应可自然进入；失败必须可返回且不损失金币。 |
| 缓存及版本混用 | 全局 TextureCache 同时被匹配/游戏使用；L1847、L9364；当前 SW/构建未知 | 区分 HTTP、SW、Loader resources、TextureCache、BaseTexture/GPU；按完整版本/URL/key 管理。记录冷/热/清缓存条件；新代码不得用旧图或旧失败状态。asset ready 与场景 commit 分离。 |
| 释放与内存 | L2451 仅移除匹配对象；L2049 仅隐藏游戏 scene，`_0x2b986d` 仍持有最后纹理；L1847 换 texture | 不因返回就全局删除/销毁共享纹理。先列缓存、scene sprite、匹配对象、timer/tween 所有权；有活跃引用则保留。有限保留/淘汰策略须实测首入峰值、重复进入退出回落与重新载入，不能以小 PNG 文件证明低内存。 |

初期建议只分离**首屏加载屏障**，不同时引入激进纹理淘汰、格式重编码、目录裁剪、压缩策略调整或引擎迁移。保留逐字节资源与可回退的 eager 路线；功能门禁失败就不启用延迟路线。这是一项建议，不是用户实施确认。

## 6. 最小验证计划（提供给当前离线项目，未执行）

### P0：必须先配对当前版本

取得真实 f996 的完整运行入口、字符串解码/资源注册、同步 texture 消费者、宿主 lifecycle 实现、存档事务及最终构建；记录 HEAD/有效未提交修改、关键文件和 dist 哈希。对实际默认入口与 iframe/预览入口逐一核实，清点 SW/cache 与离线资源清单。重新定位候选两项、第一次读取 owner 和全部分支，**不要复制 E03 的混淆函数编号**。

输出当前版依赖图及保护项对账：既有离线、ready、暂停/恢复、金币/存档、模式、输入和近期有效修改。若匹配构造已重写、候选已被首屏消费或文件族已改变，停止迁移该候选，重新只读取证。当前 f996 缺失不妨碍本次旧包报告，但阻止实施批准。

### P1：基线与测试观察点

在隔离测试存档下，以**当前最终 dist**自然点击到选桌、Royal 匹配、真实击球、结算、返回与再入。桌面与手机视口各覆盖一次，不能注入棋盘/强制胜利。后期 Royal 若没有合法解锁/余额，登记前提缺口，不绕过锁/补金币后冒充自然通过。

观察点至少包括：启动开始、首帧、lobby 可交互、game.ready、两项请求/加载/解码状态、匹配构造进入、每次 cache 读取、场景提交、扣费/存档、返回/取消和 roundId。记录请求 URL/key/version、时间、结果、requestId/sceneEpoch/mode/table（不采集个人进度或凭据）。等候谓词先自证：持续 false 应超时、延迟 true 不提前通过、reject 必须失败。

E08 的人工延迟 3 秒只用作**因果故障注入**：当前 eager 基线在这两项慢时，ready 与真实可交互是否受阻？拟议 lazy 候选在相同条件下，lobby 是否不等待、但首次匹配不提前读纹理？不得把注入值当真实手机网络或收益样本。

### P2：最小故障/生命周期矩阵

| 场景 | 操作与预期不变量 |
|---|---|
| 正常冷启动、暖启动 | eager/lazy 同入口、同存档、同视口/DPR；首屏和自然 Royal 首次进入均有截图与真实输入证据；key、主题、ready 时机一致可解释。 |
| 两项分别慢、顺序颠倒 | 分别延迟 bg_4 或 cover，另一次颠倒返回顺序；lobby 不被可选资源阻塞，匹配构造前两者均 ready，无半主题。 |
| 单项失败、损坏、永久不返回 | 各项分别 404、损坏图、截止时间超时；显示失败，可 Retry/Back，未进入匹配、不扣费、不存坏状态；第二次恢复请求可成功。 |
| 同族并发、切换意图 | 等待中连点、Royal→其他桌台/模式→Royal；同族不重复加载，旧 intent 不开局、不扣费；提交恰好一次。 |
| 等待中 Back、晚成功、晚失败 | 立即返回 lobby，之后旧响应到达不改变 UI/金币/状态；再入可使用有效缓存或新请求；失败回调不覆盖新界面。 |
| 暂停/恢复/重开 | 加载中、匹配动画中、游戏中分别暂停/恢复；保持合法暂停归属，旧回调不新开一局；结算再来一局纹理完整。 |
| 真正离线未访问 Royal | 全新离线宿主/本地分发缓存上下文，从未在线暖过该桌台；冷启动、首次进入、返回再入可玩；若宿主允许缓存安装，单测首次安装失败与已安装离线重启。 |
| 缓存版本与释放 | HTTP 冷/热、SW 首次/更新、Loader/TextureCache 驻留分别记录；切其他桌台后回 Royal，未误销毁共享纹理；重复进入/退出建议至少 20 次作初筛，观察峰值及回落，次数不是长期无泄漏证明。 |

一项场景失败就保留 eager 默认，不以 fallback 白图、提前 ready、跳过扣费或强制清缓存制造 PASS。补测脚本必须真实起本地静态服务器、访问当前 dist、执行桌面/手机真实点击、收集 console/pageerror/资源失败和截图、结束停止服务，输出 `evidence/`。后续代码阶段获授权后才准备测试脚本，并在最后源码/资源修改后真实执行 `npm run build`、`npm test`、`npm run check`；check 检查最终 dist，验证后不重建/修改 dist。本轮不创建或执行这些脚本。

### P3：收益判断与采用门槛

功能门槛先于收益：P0 当前版配对关闭、两项首次消费前 ready、失败可收敛、取消/重入安全、扣费/保存一次、离线首次 Royal 可达、暖缓存及更新通过、无资源白图/输入回归，才允许候选进入目标设备对照。

性能分别测 ZIP 字节/展开量、实际 HTTP bytes/请求与缓存命中、启动到首帧/可交互/ready、首入 Royal 等待、图像解码/上传可观测段、JS 堆、renderer/宿主进程与可得 GPU 信息、帧耗时尾部和返回回落。不把包体、HTTP、JS 堆或理论 RGBA 当同一个指标。

同一真实目标设备/宿主、系统、视口/DPR、存档、网络条件、缓存状态，对照当前 eager 基线和候选；建议每条件至少 5 次先看原始值与中位数，是否扩样由方差决定。CPU/网络模拟和手机视口是诊断，不是手机性能结论。不得预设收益百分比；当前项目未给定首入允许等待/峰值预算，实施前以基线和目标设备共同确定。不能把启动等待搬到首次进入而仍宣称整体体验改善。

## 7. 本次真实核验结果、产物与限制

实际完成：读取全部四份冻结品类/框架资料；读取选定 `game-reverse-engineering/SKILL.md` 及 execution-protocol、global-rules、unknowns 模板和 H5 包体/加载/低内存参考正文；列真实 ZIP 清单并定点读 HTML、PIXI 头部、disc-rules；逐字节提取四份研究文本；按原行号读取注册/入口/构造/缓存/返回路径；静态交叉核对表轮转、校验式和候选文件散列。Skill 模块入口 `modules/hosted-minigame-harvest/SKILL.md` 的资源读取被工具拒绝（未选入口），没有重试、没有宣称采用该入口正文；采用的是已成功读取的同包参考方法，不启用其采集工具。

产物：本报告 `/workflow/prototype.md`；E01–E04 的 `reference-inputs/` 原字节研究副本（仅供阅读，非新游戏产出，不进 dist/release）。不生成试玩、素材清单或发布 ZIP。

| 验证层 | 本轮状态 |
|---|---|
| ZIP 身份、选定文件真实存在/哈希、旧版静态路径 | PASS，证据见 E01–E06 与行号 |
| f996 当前有效源码、真实入口、候选适配 | NEEDS_CONTEXT；仅有 E07 片段 |
| `npm run build` / `npm test` / `npm run check` | 未执行；本轮为只读原型审查，非代码/测试阶段，且无当前工程/最终 dist |
| 旧包浏览器实际启动与纹理缺失行为 | 未执行；静态复核不能替代动态结果 |
| 当前离线首次 Royal、并发/重入/缓存/真实对局 | BLOCKED，需当前构建与授权测试环境 |
| 手机/目标宿主耗时、内存、性能改善 | BLOCKED，无目标设备/宿主测量；没有改善结论 |

### 未知清单

| 编号 | 未知项 | 还缺什么 | 当前证据 | 状态 |
|---|---|---|---|---|
| U01 | f996 完整入口、bitmaps/texture 消费链及受保护修改 | 当前真实源码/有效工作树、运行与构建入口、散列 | E07 仅调用方片段，E03 是旧版 | 未闭合 |
| U02 | 两项在当前默认入口是否仍非首屏及匹配第一次消费 | 当前版全引用复核 + 自然点击观察 | E03 支持旧版静态路径 | 未闭合 |
| U03 | Loader 失败/部分成功、纹理 setter 与 retry 的当前实际行为 | 当前 PIXI/资源管理实现与浏览器故障注入日志 | E03 同步读取；E05 仅版本头部 | 未闭合 |
| U04 | 实际离线宿主本地 URL、安装资源清单、SW 更新与缓存边界 | 当前离线分发物和宿主冷/热/更新测试 | E02 注销 SW；ZIP 内候选文件存在不证明运行可达 | 未闭合 |
| U05 | 当前生命周期、扣费/存档、取消事务 owner | 完整当前实现与真实 pause/resume/返回/失败测试 | E07 生命周期注册片段；E03 先扣费和空 pause/resume | 未闭合 |
| U06 | 图片尺寸、Texture/BaseTexture 所有权、GPU/进程峰值与回落 | 实际图像/当前缓存清单与目标设备生命周期采样 | ZIP 文件字节/散列、E03 隐藏/移除但保留引用路径 | 未闭合 |
| U07 | 目标机型/宿主、性能预算、允许的首次进入等待 | 调用方目标及真实 eager 基线；缺口影响实施不影响本轮只读分析 | E08 桌面人工延迟摘要无原日志 | 未闭合 |
| U08 | Royal 自然可达测试进度/余额和完整对局前提 | 隔离合法测试存档或自然进度测试授权 | E03 fee/coins gating；E06 仅局部规则 | 未闭合 |

所有未闭合项保留。下一步是按 P0 在当前 f996 重新配对，再讨论是否授权小范围实验；本报告不等于阶段人工确认或延迟加载实施批准。
