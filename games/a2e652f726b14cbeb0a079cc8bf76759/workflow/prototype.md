# 原型阶段报告 · Carrom 离线对手头像集成风险审查

- 项目：`a2e652f726b14cbeb0a079cc8bf76759`（Carrom 对手头像集成风险审查）
- 阶段：prototype（原型定义）｜ 品类：board-games ｜ 框架：canvas-web
- 技能：`game-reverse-engineering/SKILL.md`（总集 v10.5.0，manual 选择）
- 提交：`carrom-profile-review-project-20261113-01`
- 本阶段性质：**只读审查**。未修改任何参考源码，未执行浏览器/真机，未验证网络真实性。

## 1. 审查输入与读取范围

| 输入 | 实际路径 | 角色 |
|---|---|---|
| 游戏源码（审查主体） | `ref/mcp-inputs/mac-codex/09cc050bc26a3f81480b1818fe28df6068ace2cae7e59721832500cc845430c9/carrom-09cc-game.js` | 源码可证证据 |
| 人工说明 | `ref/mcp-inputs/mac-codex/da5dcc5947f178f7121b2e6563da5fc090c2086034088c996b7ef8409923486e/carrom-profile-notes.md` | 人工说明（效果稿/测试件记录），非源码证据 |
| 品类资料 | `genre/docs/general.md`、`genre/docs/board-games.md` | 冻结资料，已完整读取 |
| 框架资料 | `framework/docs/web-common.md`、`framework/docs/canvas-web.md` | 冻结资料，已完整读取 |

源码目录同时被 `ref/mcp-inputs/mac-codex/09cc050bc26a3f81480b1818fe28df6068ace2cae7e59721832500cc845430c9/` 作为 SHA-256 标识（正式源码 SHA-256 `09cc050bc26a3f81480b1818fe28df6068ace2cae7e59721832500cc845430c9`，与 notes 一致）。

运行环境事实（源码可证）：实际为 **PIXI.js + planck(box2d) + Howler + GameSnacks** 组合，字符串经 `_0x3797` 解码器还原（文件头 `var _0x4a128a = _0x3797;`），**并非裸 Canvas 2D**。本阶段沿用项目既有运行时，不重写引擎。

## 2. 本阶段交付定位（与冻结资料的关系）

- `framework/docs/web-common.md` 规定 prototype 阶段报告为 `workflow/prototype.md`（本文件）。
- `framework/docs/canvas-web.md` 要求「玩法状态与渲染、输入分离，提供真实浏览器输入验证」。本阶段**不生产新玩法代码**：现有产物是既有 H5 离线棋盘游戏的**只读审查结论 + 头像资源交接清单 + 后续阶段的验收条件**。
- 因此本报告按「来源规则 / 新增设计 / 复用资源 / 未验证项」四分类交付，满足 `genre/docs/board-games.md` 的「说明哪些是来源、哪些是新设计、哪些被复用或重新生成」。
- **语言默认值**：本阶段不产出任何玩家可见文案或文字素材，故不涉及界面语言实现。下游美术/代码/测试阶段须按默认英文交付（英文界面文案、`html lang="en"`），不得因宿主或浏览器为中文而切换语言；本次审查中出现的 `text_you` / `text_opponent` / `results_win_title` 等均为图片纹理，非可本地化文本。

## 3. 源码可证结论（逐项）

### 3.1 资源注册（`src.bitmaps` 加载表）

- 新增键：`avatar_opponent_local: "assets/avatars/opponent_local.png"`。
  同一调色板中既有玩家剪影 `avatar_silhouette_cha01`（值走解码器 `_0x4a128a(0x26f)`），以及 `avatar_silhouette_cha02`(0x439) / `cha03` / `cha04` / `cha05`。
- 结算/匹配相关键（`src.bitmaps`）：
  - `results_opponent_profile` → 解码索引 `_0x4a128a(0x1d9)`。字符串表中**同时**存在 `"results_opponent_profile"`（键名）与 `"assets/result/results_opponent_profile.png"`（路径）两个字面量；按「键名明文写在左侧、值走解码器取路径」的规律，`0x1d9` 应解析为该路径，但**索引→字符串的具体对应关系未逐条解出**，标为「推断」而非确证；
  - `results_opponent_profile_win: "assets/result/results_opponent_profile_win.png"`（**明文**）；
  - `results_you_profile`、`results_you_profile_lose`（解码字符串，字符串表含 `assets/result/results_you_profile_lose.png`）。
- 字符串表中确实存在 `"assets/result/results_opponent_profile.png"` 与 `"results_opponent_profile"`、`"results_opponent_profile_win"` 条目，说明注册键与路径字面量均被引用。

**判定（源码可证）**：`avatar_opponent_local` 是**新增独立键**，未覆盖 `avatar_silhouette_cha01`。玩家剪影纹理键仍保留且其路径未被改动。

### 3.2 头像控件类 `_0x3020e6` 与两侧构造分支

- 构造函数 `_0x5f1a21(_0x48c159)` 内：
  - 第一张纹理仍走解码器：`PIXI["Sprite"]["fromFrame"](_0x48c159 ? _0xef337d(0x2d5) : _0xef337d(0x466))`（底层框/底色图，未改动）；
  - 第二张（人像）**显式分支**：
    `var _0x1aeedb = PIXI["Sprite"]["fromFrame"]( _0x48c159 ? "avatar_opponent_local" : "avatar_silhouette_cha01" );`
    并 `this[_0xef337d(0x362)] = _0x1aeedb;`——该混淆键对应 `avatar` 属性，由后文明文 `_0x44d1ad["avatar"]["texture"] = ...` 与 `this[_0x1eb22a(0x130)]["x"]` 系列访问交叉确认（属性名明文可读，索引键仅为等价混淆写法）。
- 实例化（对局场景构造段）：
  - `(_0x2cf38a = new _0x3020e6(0x0))` → falsy → **玩家侧取 `avatar_silhouette_cha01`**，`x = 0x50`（左侧），`scale 0.85`；
  - `(_0x44d1ad = new _0x3020e6(0x1))` → truthy → **对手侧取 `avatar_opponent_local`**，`x = 0x230`（右侧），`scale 0.85`。
  - 两者均再有 `_0x483e8b` 头像框实例（`_0x2cf38a["frame"] = _0x44982f`、`_0x44d1ad["frame"] = _0xa32e35`）。

**判定（源码可证）**：玩家侧与对手侧由**构造参数分支**，改造后已各自持有独立纹理键，不再是「两侧共用同一张剪影」。人工说明中「源码显示局内左右两侧均通过 `_0x3020e6` 创建并共用 `avatar_silhouette_cha01`」描述的是**改造前**状态。

### 3.3 对局开始的纹理覆盖（`_0x1260d2`）

- 函数 `_0x1260d2(_0x259626)`（对局入口/重置）尾部存在：
  ```
  (_0x44d1ad["avatar"][_0x3dd3e7(0x335)] =
     PIXI[_0x3dd3e7(0x304)]["TextureCache"]["avatar_opponent_local"]),
  ```
  该语句**只针对对手变量 `_0x44d1ad`**；同函数内**未见**对 `_0x2cf38a`（玩家）的同类覆盖。
- 该覆盖点在同一源码文本中出现在多处重复切片（读取到的行号约 2417/2418、4761/4762、16583），是混淆打包文件的重复段，语义同一处。

**判定（源码可证）**：进入对局时对手侧纹理被**再次显式赋为** `avatar_opponent_local`。因为构造函数已按分支选中同一纹理，这是**冗余赋值（no-op 级别的重复设置）**，不是第二次资源加载（`TextureCache` 为共享缓存）。其净效果是：即使其它路径曾改写过对手侧纹理，进入对局时仍会被强制回到新头像。风险见 §4.2 / §4.3。

### 3.4 匹配与胜负结算的头像引用

- 匹配/结算容器类 `_0x104b9b`（构造函数内 `_carromConstructingMatch = this;`）持有 **对手专属字段**：
  - `this["oponnentAvatar"]`（拼写如此，两处定位 `x = 0x18e + 0x1e`, `y = 0x2d0 - 0x50`）；
  - `this["oponnentNameLabel"]`（同 `x`，`y = 0x35c - 0x50`）；
  - 相关字段还有 `0x146`/`0x21b`/`0x26c`（玩家侧标签/图标）与 `0x130`（即 `oponnentAvatar` 的混淆等价访问，如 `this[_0x1eb22a(0x130)]["x"]`、`this[_0x5c86fd(0x130)]["y"]`）。
- `oponnentAvatar` 也被粒子奖励函数引用：`_0x4c745a["x"] = this["oponnentAvatar"]["x"] + 0x14`（偶数粒子从对手头像右侧喷出）。
- 结算使用的是一组**独立纹理键**：`results_opponent_profile`、`results_opponent_profile_win`、`results_you_profile`、`results_you_profile_lose`，以及 `winner_background`、`winner_outer_glow`、`winner_glow`、`loser_01..05`、`results_win_title`、`results_title`、`results_title_stones`、`results_claim*` 等。**结算不复用局内 `avatar_opponent_local`，也不复用 `avatar_silhouette_cha01`。**

**判定（源码可证）**：匹配与结算走独立素材路径；局内、匹配、结算三处要「同一角色」必须**分别**提供对应资源，不能只替换其中一个声称同局一致（与人工说明一致）。

## 4. 逐项风险清单

证据等级：**[可证]** = 源码直接可读；**[人工]** = notes 记录，非源码；**[未验证]** = 无运行/设备证据。

### 4.1 玩家头像被误改
- **[可证] 倾向未受影响**：玩家侧由 `_0x2cf38a = new _0x3020e6(0x0)` 构造，falsy 分支走 `avatar_silhouette_cha01`；`_0x1260d2` 的覆盖只写 `_0x44d1ad`；全文件未见对 `_0x2cf38a` 写入 `avatar_opponent_local` 或其它结算纹理。
- **[未验证]** 未运行浏览器确认玩家侧实际渲染像素；若后续有人在加载表层把 `avatar_silhouette_cha01` 的**文件本身**替换掉，则会同时改变玩家与任何仍引用该键的界面（这是最大的误改入口）。当前改造方式是**新增键**，避开了该入口。

### 4.2 丢失纹理（键名/路径一致性）
- **[可证] 注册与引用键名一致**：`src.bitmaps` 有 `avatar_opponent_local`；`_0x3020e6` 与 `_0x1260d2` 均以**字符串键** `"avatar_opponent_local"` 从 `PIXI.utils.TextureCache` 取值，两边拼写一致。
- **[未验证] 运行期键名可解析性未测**：`_0x1260d2` 直接用 `PIXI[...]["TextureCache"]["avatar_opponent_local"]` 取纹理。若加载表键与 `TextureCache` 实际注册名因打包/命名策略不同（例如前缀化、hash 化）而不符，该表达式会得到 `undefined` 并让对手头像空掉。本次为只读审查，无运行证据，**标为未验证**。
- **[未验证] 图集/单图加载方式未核对**：`avatar_opponent_local` 指向独立文件 `assets/avatars/opponent_local.png`，而 `avatar_silhouette_cha01` 走解码字符串。两者是否走同一 loader 分支（单图 vs 图集帧）未在源码读取范围内确证，**标为未验证**。

### 4.3 重复加载 / 冗余赋值
- **[可证] 不是重复加载**：`PIXI.utils.TextureCache` 是共享缓存，`_0x1260d2` 只是再次赋值同一个纹理对象，不产生第二次网络请求或第二份显存纹理。
- **[可证] 确实存在冗余赋值**：构造函数已按 `0x1` 分支选中 `avatar_opponent_local`，开局又从 `TextureCache` 取同一键覆盖一次。冗余本身无害，但**掩盖问题**：若将来把构造函数分支改回剪影，开局覆盖仍会「纠正」为对手头像，导致阅读者误判真实生效点。建议在代码阶段**只保留一个真实 owner**（构造分支或开局覆盖二者取一），或加注释说明保留意图。

### 4.4 异步 / 兼容性
- **[人工] 扩展名与内容不一致**：notes 记载合入的 `development/assets/avatars/opponent_local.png`、`results_opponent_profile.png`、`results_opponent_profile_win.png` **实际为 WebP 内容配 `.png` 扩展名**。
  - **[未验证]** 目标宿主（AHA/GameSnacks WebView）按扩展名/MIME 处理时的兼容性未实测；
  - **[未验证]** 部分宿主会走图片代理/CDN，`Content-Type` 若按后缀推断为 `image/png` 而实际为 WebP，可能解码失败。notes 声称「沿用项目已有同扩展名资源的浏览器加载方式」，但那是**推断**而非设备证据。
- **[可证] 纹理可用时机的编码风险**：`_0x1260d2` 在函数尾部同步取 `TextureCache`。构造侧同理。若纹理尚未加载完成，取到的是空/占位纹理；本次未读到等待加载的守卫代码，**[未验证]** 是否存在加载完成回调。
- **[人工] 包体影响**：notes 记录开发目录 ZIP 4,031,003 → 4,043,912 字节（+12,909）；旧 `results_opponent_profile.png` 仅 954 字节，新素材显著变大。**[未验证]** 正式分发 ZIP、加载耗时、设备帧耗时、低内存设备表现。
- **[人工] tint/颜色状态**：匹配/结算存在按胜负切换的独立图（`results_opponent_profile_win`、`results_you_profile_lose`）。新素材在这些状态下的实际配色/叠加未验证。

### 4.5 状态覆盖范围不全（最需在代码阶段收口）
- **[可证]** 已改的是「局内对手侧（构造 + 开局覆盖）」+「匹配/普通结算图」+「对手胜利图」（notes）。
- **[人工] 未闭环项**：败局（对手胜利即玩家败）路径下 `results_you_profile_lose` 与 `results_opponent_profile_win` 的组合仅在 notes 中记为「败局为临时注入、胜局为受控布棋且引导层残留」，**不是自然完整胜负复验**。
- **[未验证]** 引导/教程（`tut_01_screen_design` 等）是否另有头像引用；本次读取范围内未发现，但未做穷尽搜索。

## 5. 玩法与原型定义（沿用来源，不做新设计）

按 `genre/docs/board-games.md`，本阶段需明确来源棋类的规则要点。本游戏为 **Carrom（印度撞球）**，不是 Ludo 路径/骰子游戏，因此品类指南中「环路长度/安全格/精确终点」等 Ludo 条目**不适用**，应替换为 Carrom 对应项；本阶段仅登记，不在本轮发明规则：

| 品类要求项 | Carrom 对应（来源证据） | 状态 |
|---|---|---|
| 棋子/资源数 | 源码含 `stone_00..stone_08`、`puck_sprite`、`stone_pot_sprite` | [可证] 资源键存在；具体每方几枚未在本轮确证 |
| 随机公平性 | 有 `_0x3797` 解码后的 `Math.random` 调用点 | [未验证] 分布/AI 合法性未测 |
| 回合制提交点 | 存在 `_carromTurnId`、`_carromAiTurn`、`_carromRoundId`、`_carromMatchSchedule` 等回合/局标识 | [可证] 存在；唯一提交点未在本轮穷尽 |
| 模式差异 | 存在 `_0x5d148e == 0x2` 等分支（不同 HUD/布局路径） | [可证] 存在分支；模式语义未确证 |
| 胜利条件 | 结算类 `_0x104b9b` + 胜/负独立纹理 | [可证] 存在；具体判定未在本轮确证 |

**结论**：本阶段**不新增玩法设计**，只做现有游戏的资源引用审查。若后续要产出自制原型，需先补齐上表「未确证/未验证」项，并按 `board-games.md` 的验收条目做纯规则覆盖。

## 6. 美术资源交接（本阶段实际产出）

本阶段为**只读审查阶段**，未生成新的图像/音频/字体/模型。现有可交接资源为**他人前置产出**（notes 记录），本会话**未创建、未修改、未取得其哈希**，因此不写入 `workflow/art-manifest.json`，也**不声称**已生成 AI 图片。

| 资源路径（notes 记录） | 用途 | 来源 | 本次会话是否核验 |
|---|---|---|---|
| `development/assets/avatars/opponent_local.png`（实为 WebP） | 局内对手头像 | 前置阶段生成并合入加载表 | 否（不可见/无哈希） |
| `development/assets/result/results_opponent_profile.png`（实为 WebP） | 匹配/普通结算对手头像 | 同上，替换旧 954 字节素材 | 否 |
| `development/assets/result/results_opponent_profile_win.png`（实为 WebP） | 对手胜利态头像 | 同上 | 否 |
| `evidence/backups/20261113_opponent_profile/` | 原代码与两张旧结算图备份 | 前置阶段 | 否 |

**[未验证]** 上表全部路径在本会话工作区**不可见**（`ls` 返回空），无法调用 `inspect_assets` 获取真实 SHA-256，故不能声明哈希与用途已完成交接。**美术阶段必须先 `inspect_assets` 取真实哈希后再写 `art-manifest.json`。**

## 7. 后续阶段验收条件（承接本报告）

**美术阶段**
1. `inspect_assets` 对 `public/assets/` 与 `assets/` 下实际文件取 SHA-256，写 `workflow/art-manifest.json`（`{assets:[{path,sha256,usage,source}]}`，四项均非空字符串）。
2. 至少一份真实图像资源；补齐「局内 / 匹配 / 普通结算 / 对手胜利 / 玩家失败」五态的同一角色一致性。
3. 明确 `.png` 扩展名 + WebP 内容的处理决策（转换或在清单中标注），不得留模糊。

**代码阶段**
1. `avatar_opponent_local` 在 `TextureCache` 中的**运行期键名**必须实证存在（可加断言或加载日志），否则 4.2 风险落空。
2. 收敛 §4.3 的冗余赋值：保留唯一 owner。
3. 补全 §4.5 未闭环的败局/对手胜利路径引用。
4. 真实执行 `npm run build`、`npm test`、`npm run check`，入口 `dist/index.html`。

**测试阶段**
1. 浏览器真实加载 `dist/`，进入对局、完成击球、走到**自然**胜负结算（不得注入棋子状态或强制胜利），覆盖桌面与手机视口。
2. 核对玩家侧仍为原剪影、对手侧与新头像一致，且匹配/局内/结算同角色。
3. 覆盖目标宿主（AHA/GameSnacks）下的图片解码与内存表现；未覆盖设备如实登记。

## 8. 未知清单（必须随交付）

| # | 未知项 | 影响 | 现状 |
|---|---|---|---|
| U1 | `PIXI.utils.TextureCache["avatar_opponent_local"]` 运行期是否真存在 | 若不存在则对手头像空掉 | 未验证（无运行环境） |
| U2 | 素材 `.png` 扩展名 + WebP 内容在目标宿主能否解码 | 白图/报错 | 未验证 |
| U3 | 局内/匹配/结算/胜负四态的实际渲染一致性 | 同角色不一致 | 未验证（notes 亦自认未复验） |
| U4 | 引导/教程层是否存在额外头像引用 | 漏改 | 未穷尽 |
| U5 | 包体增量对加载与低内存设备的影响 | 首屏/内存 | 仅 notes 记 +12,909 字节开发 ZIP |
| U6 | 工作区内 `development/`、`evidence/` 实际文件与哈希 | 无法出 art-manifest | 本会话不可见 |
| U7 | 源码中 `_0x1260d2` 覆盖点是否有加载完成守卫 | 时序竞态 | 未读到守卫 |
| U8 | 是否存在除 `_0x44d1ad` 外其它指向 `avatar_opponent_local` 的写入 | 覆盖冲突 | 仅按当前读取范围判断 |

## 9. 真实验证记录（本阶段实际执行的工具动作）

| 动作 | 结果 | 说明 |
|---|---|---|
| `read_game_knowledge` × 4 | 成功，正文已读 | `general.md`、`board-games.md`、`web-common.md`、`canvas-web.md` |
| `read_skill` `game-reverse-engineering/SKILL.md` | 成功，正文已读 | v10.5.0，路由为「只读取证 + 换皮审查」 |
| `read_reference` 源码（分段） | 输出了 `_0x3020e6` 构造分支（含 `"avatar_opponent_local"` 明文）、`_0x1260d2` 覆盖语句、`_0x104b9b` 的 `oponnentAvatar` 定位、`src.bitmaps` 注册表等原文 | 见 §3 |
| `read_reference` 人工说明 | 成功，全文已读 | 见 §3、§4 的「[人工]」标注 |
| `grep` 于 `ref/` | **未命中**（工具环境异常，`ls` 亦返回空） | 已改由 `read_reference` 分段证据支撑；局限性记入 §11 |
| `inspect_assets` | 返回空数组 | 工作区文件不可见，无法取得哈希 |
| `run_validation`（build/test/check） | **未执行** | 本阶段无自建工程与 `package.json`；执行会被当作伪造构建证据 |

本阶段**没有**可交付的构建产物、截图或测试退出码，故不声明任何界面/行为验收通过。

## 10. 设计决策与取舍汇总

1. **不改源码**：用户明确要求只读。所有结论以「建议」形式给出，不含补丁。
2. **按「新增独立键」而非「覆盖旧剪影」**：这是 notes 记录的前置实现方向，也是唯一能避免玩家头像被连带改动的路径。本报告确认该方向在源码层面成立（§4.1），并列为**必须保留**的约束。
3. **接受冗余赋值，暂不删除**：`_0x1260d2` 的重复赋值在混淆代码中删除风险高于收益（可能触发未读到的时序依赖）。记为代码阶段收口项，而非本阶段改动。
4. **局内 / 匹配 / 结算分开建资源**：源码结构决定了这三处不共享纹理（§3.4），因此「一张图通吃」不可行，必须分别产出，成本已计入美术阶段范围。
5. **不伪造执行**：环境缺少工作区可见性与浏览器工具，明确不写「已跑通」「已验收」。

## 11. 限制声明

- 本报告**未**运行浏览器、模拟器或真机；**未**证明网络真实性；**未**修改任何参考源码或资源。
- 混淆源码存在**重复切片**，报告中的行号仅用于定位同一语义处，不代表文件唯一行。
- 本会话 `grep` 对 `ref/` 下源码返回「未命中」、`ls` 对工作区返回空，故证据来自 `read_reference` 的**分段读取**（命中段含 §3 各引用原文）。这会影响「穷尽性」：U4/U8 的结论只覆盖已读范围。
- 本阶段为 prototype 的只读审查交付，不包含 `npm run build/test/check` 证据（本阶段无自建工程产物），故**不声明**构建与浏览器验收通过。
