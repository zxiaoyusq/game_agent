# 两个 Ludo 原始包研究记录

记录日期：2026-11-03。范围：用户指定的本地两个原始 H5 ZIP。依据工程 `casual-game-production` 与 `game-reverse-engineering` 的执行协议、引擎识别和玩法执行路径方法开展；没有将未测试的平台能力写成已验证事实。

## 输入与指纹

| 输入 | ZIP 字节 | 展开字节 | 文件数 | 引擎证据 |
|---|---:|---:|---:|---|
| `ref/公司skill整合/AHAgames/82251_Just_Ludo/Just_Ludo.zip` | 3,327,654 | 5,525,803 | 195 | `www.volcanoh5game.com/Just_Ludo/cocos2d-js-min.js` 中 `cc.ENGINE_VERSION="2.4.3"`；`main.js` 加载 Cocos 资源与场景；运行时输出 `Cocos Creator v2.4.3` |
| `ref/公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip` | 5,213,177 | 6,773,526 | 651 | `www.hnyigegame.com/Ludo_Superstar/game/scripts/cocos2d-js-min.ec322.js` 同样声明 2.4.3；`main.184ad.js`、`settings.f4dd5.js` 和运行时相互印证 |

ZIP SHA256：

- Just Ludo：`190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`
- Ludo Superstar：`9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`

完整逐文件路径、字节、SHA256、分类以及可读取图片的尺寸见 `reference-inventory.json`。Just Ludo 有 37 个图像文件、16 个音频、1 个字体；Superstar 有 504 个图像文件、18 个音频、1 个字体。图像文件数不等于 Sprite 数量：Just 使用合并图集；Superstar 含独立图与分层加载内容。所有原包素材标注 `reference_only`，用于研究，不表示已经换皮或被新游戏引用。

## 玩法执行路径证据

以下 `J` 指原 ZIP 内 `www.volcanoh5game.com/Just_Ludo/assets/main/index.js`；`S` 指 `www.hnyigegame.com/Ludo_Superstar/game/scripts/assets/main/index.a298e.js`。S 是单行压缩代码，因此用模块名与方法名作为稳定检索锚点；J 的行号来自原 ZIP 未改动正文。

| 规则/能力 | Just Ludo 证据 | Ludo Superstar 证据 | 结论及证据等级 |
|---|---|---|---|
| 出营 | J 1717–1748 `Chess.canWalk`：在基地只允许 `DICE_MAX_POINTS`；J 3327 常量为 6 | S `Chess.canChessWalk` 与 `GameConst.DICE_MAX=6` | 静态确认，六点出子；出子落自家起点，不走六格 |
| 精确归家 | J `Chess.canArriveTerminal`、`canWalk` 比较剩余长度 | S `canChessArriveTerminal`、`canChessWalk` 相同分支 | 静态确认，超出终点不可走 |
| 环与归家道 | J 主包配置 `assets/main/import/0b/0b5e1c6b1.json` 的 `MapInfo.paths` | S `game/loading/assets/main/import/0b/0be10531e.a5010.json` 的 `MapInfo.paths` | 两者相同：外圈 52 格；玩家0解锁归家路径为 `[0..50,52..57]`，跳过外圈最后一格51。相对路径最终索引56，不要混淆绝对棋盘编号57与相对进度 |
| 安全格 | 同配置 `safeGrids=[0,13,26,39,8,21,34,47]`；J 2258 `canEateOther` | S 同配置及 `Chess.walk` | 静态确认，起点与星标格免吃 |
| 吃子与叠子 | J 10168 `MapGrid.getBeEatenChess` 仅当前格总棋子数1且为敌人才返回目标；J `canWalk` 不检查道路堵塞 | S `MapGrid.getBeEatenChess` 同条件；`Chess.walk` 先判断安全再判吃子 | 静态确认，单枚敌子可吃；叠子免吃、无阻路规则。可共存，不应凭常见 Ludo 规则擅自恢复成不可跨越的路障 |
| 加掷 | J 5119 `onPlayerOptCompleted` 吃子/归家保留当前玩家；J 5146 `setTurnPlayerIndex` 六点保留当前玩家 | S `GameScene.onPlayerOptCompleted`、`setTurnPlayerIndex` | 静态确认，六点、吃子、归家奖励继续掷骰 |
| 快局初始状态 | J 4835–4860 `loadOnlineComputer` 设置双方预出子数2；J 1242 `setPlayerChessToStartPosition`、2130 `setStartPosition` | S `GameScene.loadComputer` 设置2，`TokenManager.setPlayerChessToStartPosition` | 静态确认，两枚都在自己起点，相对进度均0；另两枚仍在基地 |
| 快局回家门槛 | J 4743 将 Quick 的 barrier 设为 true；`Chess.walk` 吃子回调将其解除 | S `GameScene.onLoad` + `Chess.walk` 吃子回调 `setBarrier(owner,false)` | 静态确认，至少吃子一次才能进入回家道；未解除时沿52格外环循环 |
| 胜利条件 | J 5199 `checkGameOver`，Quick 第一枚归家；Classic 四枚归家；四人局原作继续排名 | S `GameScene.checkGameOver` 对应 Quick/Classic/Local 分支 | 静态确认；新作可选择首位冠军后结束，但应在设计报告声明其对原四人排名收尾的调整 |
| 本地同屏与 AI 配置 | J `LocalRoomView.onBtnSelectPlayer`、`onBtnPlayerClick` 可在 Human/Computer/Nobody 间切换、2/3/4P | S `GameScene.loadLocal` 使用每席 `isComputer`；本地大厅入口 | 静态确认；本轮 Just 的两人本地局通过实际点击进入，Superstar 的人机局通过实际点击进入 |
| 续局 | J 包含保存相关流程，未逐个验证所有模式 | S `GameScene.loadLocal` 读取 `Save_Game_Data` 并每秒 `saveGame` | S 静态确认本地续局，是可借鉴的实用能力；没有声称原版跨设备云存档 |
| 策略 AI | J 14800 `doChessWalkStrategy`：归家→吃子→安全→特殊格→危险区规避→默认推进 | S `ComputerManager.doChessWalkStrategy` 对应顺序 | 静态确认，不只是随机挑可走棋子；应在新引擎做独立纯函数与规则测试 |
| 连续六点 | J 12920–12935 `PlayerInfo.getDicePoints`；S 同方法 | 两者 `_sixPointsCount>3` 后把第四个6重抽为1..5 | 原包不是“第三个六点罚停”。新作若采用三6罚停，应显式写为公开规则调整 |
| 隐性概率 | J `LuckManager.getDefaultDicePoints`、`getDicePoints`、首局机器人6点改1..5；S `LuckManager` 参与掷骰 | 有 luck、难度或皮肤相关分支 | 静态确认存在非单纯均匀骰子分支；不推断实际运营权重。新作适合统一公平随机，不复制暗调概率 |
| Just 扩展玩法 | J `GameMode` 有 BombItem/Roadblock，`Chess.walk` 有火箭+3与炸弹路径；本轮实际菜单显示 Bomb Cup/Roadblock Cup | S `GameEnum` 与棋子也有道具分支，但入口与配置不同 | 菜单可见与静态代码可证；未运行完成这些活动，不把枚举存在当成全部功能已验收 |

关键 owner：`GameScene` 负责回合结束与胜利提交，`Chess` 负责移动/落格/吃子事务，`MapGrid` 负责同格棋子集合，`ComputerManager`/`RobotManager` 负责落子优先级，`PlayerInfo`/`LuckManager` 负责掷骰入口。新引擎可保持这些职责边界，同时避免移植原包的场景单例依赖和广告回调。

## 两款可融合的优势与改进方向

1. **Just Ludo 的快速反馈与引导**：可走棋子的高亮、起点箭头、安全星标、吃子/归家/六点加掷。新作把这些转成明确的中文提示、合法落点预览和点击即可完成的教学，减少初次游玩猜测。
2. **Ludo Superstar 的清楚入口与同屏实用性**：菜单突出 Local 与 Computer；经典/快局选择集中。保留人机、同屏、可续局与两种节奏，让玩家能直接开局。
3. **两者共同的策略快局**：保留“预出两枚 + 吃子解锁归家 + 首枚归家胜利”的短循环，可用主题化的“点亮航标/打开归航线”表达门槛。不要把未达门槛造成的绕圈表现成移动错误。
4. **美术重构**：原 Just 为蓝底、黄色厚描边大卡片；Superstar 为紫底、圆形入口和标准四色棋盘。新作应更换背景、棋盘质感、棋子轮廓、图标、字体层级与反馈粒子，而非只替换标题/背景色。功能色仍需可辨认，并补形状/符号区分。
5. **体积与维护**：只借鉴已证实机制，独立模块实现；原始 ZIP、旧引擎、广告与字体不放进新发布包。所有新资源真实列清单，完整工程与发布 ZIP 分别量尺，避免只报 gzip 数字。

## 浏览器对照与壳适配

原始包未修改。原始解压位于 `/tmp/ludo-reference/{Just_Ludo,Ludo_Superstar}`。另建 `/tmp/ludo-reference-preview/{just,superstar}` 仅用于本地浏览器观察，监听 `127.0.0.1:24732`，没有发布公网。

- Just：保留原 HTML/业务脚本/资源，仅将 HTML 的外部 `adsdk_1.9.2.0.js` 改为本地 no-op SDK；结束回调报告 `noAdPreloaded`，不模拟奖励广告成功。
- Superstar：把原 `game/loading`、`game/assets`、`game/scripts` 的资源按原相对路径合并到观察目录；普通 Cocos HTML 依次加载 settings/main/engine，设置 `proxiesWindow=window`、广告 Promise no-op 以及 `QGUtils.triggerEvent/Ready` 宿主回调。绕过的是宿主 ZIP/VM 壳，不改玩法 JS。
- 浏览器拦截全部非回环 HTTP 请求；因此截图只能证明本地资源与适配后核心页面运行，不证明原发行宿主、在线匹配、广告、支付可用。
- 设备：Linux Chromium / Playwright，420×900 CSS 像素；不是 Android/iPhone 真机。
- 自然入口：Just 主菜单向左滑动到 Local → 2P 默认人类席位 → Play；Superstar Computer → 默认 2P Classic → Play。均通过实际鼠标/触屏事件进入 `Game_grass`，随后点击掷骰控件；没有通过切场景/改棋子进度伪造对局。
- 对照图：`evidence/reference-just-menu.jpg`、`reference-just-game.jpg`、`reference-superstar-menu.jpg`、`reference-superstar-game.jpg`。

## 未知与未覆盖

| 状态 | 范围 | 当前证据与限制 |
|---|---|---|
| PASS | 本地包身份、引擎、资源索引 | SHA256/完整ZIP索引与引擎运行时一致 |
| PASS | 原菜单与对局基线 | 经独立本地壳实际点击进入；四张浏览器截图落盘 |
| NEEDS_CONTEXT | 原宿主线上行为 | 外网被主动阻断；无法证明在线匹配是真实多人，也没有验证广告、登录、付费等运营服务 |
| NEEDS_CONTEXT | 原全部模式终局 | 本轮只作研究对照，没有把两款原游戏所有模式从开局玩到胜利；规则以明确方法/配置静态证据记录 |
| NEEDS_CONTEXT | 原移动真机效果 | 本轮没有 Android/iOS 真机；新游戏需单列浏览器验收覆盖范围 |
| NEEDS_CONTEXT | 原 Just 控制台报错 | 启动时出现 Cocos Error 1510，主菜单、选人、对局仍可进入；这是原包观察环境问题，不能沿用为新游戏的可接受错误 |

本报告的融合建议是新设计输入，不是新工程已完成的证明。新工程的玩法、美术、测试和包体结论须由其最终文件与真实运行结果另行证明。
