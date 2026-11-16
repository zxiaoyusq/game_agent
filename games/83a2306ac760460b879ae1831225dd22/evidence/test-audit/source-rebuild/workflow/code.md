# LUDO · 原版美术复现——代码与集成

## 阶段及交付结论
本轮仅执行代码与集成（attempt=1，非恢复）。实现浏览器原生Canvas 2D版本，保留既有上游规则、交接素材及研究文件；未加载Cocos、广告或联网SDK，未自行推进/确认测试阶段。最后一次源码修改后，已在本attempt依次真实执行并通过 `npm run build`、`npm test`、`npm run check`。最终dist验收后保持不变，后续仅写报告、证据和发布包。

入口 `dist/index.html`。构建展开 **1064192字节（约1.015MiB）**，小于10MB。源码包 `releases/ludo-source.zip`，试玩包 `releases/ludo-play.zip`；实际字节/哈希和条目数以运行打包脚本后生成的 `releases/manifest.json` 为准。试玩ZIP根目录为index.html及包内相对资源，HTTP静态托管支持独立子路径。本轮未取得外部发布URL，不把本地产物称为已经上线。

## 已读输入与真实参考
完整读取本轮冻结入口：`casual-game-production/SKILL.md`、`ai-art-automation/SKILL.md`、`game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md`；按需读取后者 `references/component-restoration.md`。已读冻结资料四份：`genre/docs/general.md`、`genre/docs/board-games.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。

上游实际读取：`workflow/prototype.md`、`workflow/board-contract.json`、`workflow/reference-evidence.md`、`workflow/art.md`、`workflow/art-manifest.json`、`workflow/art-integration.json`。取消16头像随机化，采用用户明确确认的真人/电脑两张原版形象。

参考路径相对ref：
- `公司skill整合/AHAgames/94034_Ludo_Superstar/gameInfo.json`及`Ludo_Superstar.zip`；包SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`。
- `公司skill整合/AHAgames/82251_Just_Ludo/gameInfo.json`及`Just_Ludo.zip`；包SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`。

本轮按ZIP真实清单定位并读取：
- `www.hnyigegame.com/Ludo_Superstar/game/loading/assets/main/import/0b/0be10531e.a5010.json`，SHA256 `939a9d1fda59358fd9c388cd19e6e13bb0febd3eebdcc75b0f4e74ecf77a7393`，字符0–15500。实际MapInfo四条路径、八安全格、门前和归家格与上游契约一致；Difficulty/Luck机制不引入。
- `www.volcanoh5game.com/Just_Ludo/assets/main/index.js`，SHA256 `3334a9a60e060753ae65d2c89ab51376d5cfcd72f614efbe2c9ab9d3dd7d4c0f`，字符57500–64500及68500–78500。核对走子、落点安全分支、吃子回程和开门回调；不执行/导入参考源码。

主美术仅来自Superstar真实original运行部件，Just仅补充规则依据。不使用商店缩略图、AI整屏图或网页卡片式布局。既有61资源未改动：构建脚本逐份校验上游清单SHA256；代表棋盘、红子、骰帧、头像、BGM亦通过本轮inspect_assets核验。向inspect_assets传目录返回空结果的第一次调用不当作资源核验成功，随后显式文件路径调用才作为证据。

## 玩法设计及规则取舍
循环：菜单/模式/席位→随机首席→预存骰子结果→摇骰→合法棋子选择→逐格移动→吃子/归家→胜利或一次奖励/换席→结算→再来或存档继续。
- 2～4有效席，每席真人/电脑/空席，至少一真人；同屏和人机均可。
- 经典四子全营地，掷6出营到起点，四子精确归家即胜。
- 快速两子在起点、两子在营地，首次成功吃子永久打开本席所有棋子归家权限，首子精确归家即胜。四人经典也统一首名结束，均依真实用户答复。
- 52外环、四条各六格私有归家道，共76坐标；八安全格。安全免吃；非安全落点进入前恰好一敌子才吃；多子混叠免吃、不封路，不沿途吃。
- 6/吃子/归家奖励采用OR，仅一次额外摇骰，胜利优先。无动作非6换席、6保留；独立骰子，无连续六罚停、AI改点数或皮肤buff。
- 快速开门保持棋子绝对位置。normal最后格下一步正常回起点，下一次门前才进道；不套terminal.indexOf(-1)，不瞬移。
- xorshift32可复现规则随机流与AI流分离；按非零周期的2^32−1样本范围拒绝采样后映射点数。动画不消耗规则随机。固定种子URL仅复现，不注入点数、棋子或赢家；不是加速/强制胜利入口。

## 模块与状态职责
- `src/rules.js`：纯规则、路径、合法动作、不可变移动计划、一次提交、胜利、AI评分及状态不变量。
- `src/random.js`：独立持久化随机流、拒绝采样、浏览器crypto初始种子。
- `src/animation.js`：110ms逐格弧线、120ms落点强调、逆环30ms/格+180ms回槽、400ms归家；冻结分段采样，不提前改棋子。
- `src/storage.js`：schema/版本/席位/位置/骰子/赢家/随机状态和运动事务验证，错误向上传递。
- `src/renderer.js`：真实素材、骰子trim/旋转、局部→Canvas坐标、叠子/编号/合法高亮、运动pose及程序彩屑。
- `src/main.js`：ready/rolling/choosing/moving/skip/celebrating/result阶段、覆盖层、唯一输入路由、AI450ms等待、存档、Pointer与DOM操作。
- `src/assets.js`：全部核心图像decode完成后进入菜单，失败明确重试；原音频手势播放、音乐/音效分开开关。
- `scripts/build.mjs`、`scripts/check.mjs`、`scripts/release.mjs`及`tests/*.test.mjs`：真实构建、测试、最终dist浏览器验收及ZIP交付。

存档保留局ID、当前席/点数、规则与AI随机状态、turn/action、模式/席位/棋子/开门、待提交计划及完整分段、elapsed、AI wait、赢家和上次奖励。动作计划在移动前保存；运动完成才提交，事务ID防重复。写失败持续提示，仅后续写成功清除。刷新摇骰不重新取点，刷新走子续原计划；result存档恢复也打开结算界面。

后台visibilitychange与真实freeze/resume共用暂停时钟与保存路径，前台不按墙钟跳完；pagehide保存。设置和确认框暂停；重开替换session并清空事件，运行循环没有旧局异步定时器可提交。图像重试采用generation过滤迟到结果。

## 界面与原美术集成
720×1280设计画布等比contain，桌面竖版居中外围延展原紫纹。十字棋盘、四营地和76格采用上游变换 `X=360+1.15x, Y=640−1.15y`，棋盘与营地坐标未重排。实际Canvas截图确认四色、营地槽、路线格、亮面棋子和中央停泊区匹配静态装配，不声称与原游戏运行截图像素级对齐。

红棋子packed帧Canvas顺时针90°恢复，实际参考图观察的大头朝上、小尾朝下。门packed也旋转恢复；骰子25滚动帧使用完整220画布，六面在原画布[62,54,104,106]绘制，不把裁片放大成220。原真人/电脑形象、四色信息底件、绿按钮/禁用按钮、背景和音效实际接入。

手机布局修正仅限底部玩家信息向上55设计像素，防大操作按钮遮挡；棋盘比例/路径保持不变，骰子绘制与命中共用infoPoint。原返回图与骰代表转换样图保留在交接包，但返回操作采用带文字的大语义按钮，代表样图不作为额外帧。菜单/设置/结果为原背景上的全屏手游遮罩，无侧栏/仪表盘。按钮44CSS像素起，叠子以四枚编号按钮消除命中歧义；Canvas真实Pointer坐标转换与鼠标/触摸均验证。

## 验收条件与本轮最终真实结果
最终源码指纹（工程构建清单）：`59ba3aaecc16752aeafbe25dc56ba2eda4f4704a703bd3f6382a9a5353a1e4d9`。
工具记录最终源码指纹：`ca22a392bfddd239e0155033c1097edf9c3f99f868803baa334c49f318dc255e`。两者范围不同，前者为发布源码清单，后者由工具运行框架计算，不混同。
工具最终build_sha256：`66c6b9b2ca35116bf985eb8f02bd241ccc026de90522478d1e82c8e5b64b9b77`。

|实际命令|退出码|结果|
|---|---:|---|
|npm run build|0|61资源逐哈希验证，dist展开1064192字节，无研究源码|
|npm test|0|11测试组全部通过；两模式×2/3/4席×20种子，共120场从初始规则局到真实终局|
|npm run check|0|真实Chromium 153.0.8010.12，最终dist与源码哈希不变，控制台/pageerror/必需请求错误为空|

浏览器覆盖：320×568手机触摸、390×844手机触摸、1100×900桌面鼠标及780×720缩放；本地服务器根路径及 `/independent/ludo/index.html`。脚本结束自动关闭服务器与浏览器。真实DOM按钮/Pointer点击，不写棋子状态或调用游戏规则代替输入。
- 快速seed14，从新局到首子归家赢家绿；最终turn=29、总action=30，刷新后事件文件记录29次提交、133落地。
- 经典seed5，从新局到蓝方第四子归家；最终turn=122、总action=106，刷新后事件文件记录105次提交、435落地。
- 事件数量比总action少一次是刷新前记录存在旧页面内存，不是丢失规则动作。两个完整对局均与纯规则种子结果一致，均有自然吃子/回营、归家及胜利，不强制赢家。
- 每模式真实再来一局；3席同屏和4席混合AI真实合法移动另测；全人数/模式120场完局矩阵属纯规则，不能称全部UI矩阵已完局。
- 摇骰833.333ms、25原帧；每逻辑格110ms弧线；吃子可见逆程；归家400ms；胜利1500ms。连续WebM录像覆盖正常速度完整对局，截图及sequence JSON补充时点，动作/分段/落地日志绑定ID。
- 真实触摸连点锁定，设置暂停；摇骰刷新同点数；两模式移动中刷新同冻结计划；运动中确认重开无旧局提交；吃子回程/归家/胜利阶段取消重开确认继续，均记录capturePaused/homePaused/winPaused=true。
- 后台使用真实导航BFCache：visibilitychange(hidden)→freeze→resume→visibilitychange(visible)，elapsed冻结且原骰保留。探测证明无头Page.setWebLifecycleState单独调用并未发生事件，因此不把命令响应成功当生命周期通过。
- 慢图像加载期间无开始入口；损坏核心图片重试成功；损坏存档提示，存储拒写持续可见。八份原音频均经真实AudioContext解码，记录时长和声道。

## 本轮失败与修复记录
前序check真实失败，没有引用失败日志为成功：
1. 慢加载用goto默认load等待导致断言时已进菜单；改为DOM ready验证loading。
2. 无头冻结/窗口最小化不触发真实可见性，另写探测验证BFCache真实事件；更换实际浏览器入口及允许缓存的测试服务器响应。
3. 事件details.kind覆盖“落地/动画段”标签，造成日志断言失败；修正为segmentKind，保持主事件标签。
4. 纯规则最快经典种子无吃子，候选筛选增加captures>0；摄像采样可能越过短回程，最终事件与连续录像共同核验，不捏造截图。
5. 参考原型随机拒绝采样范围修正到xorshift非零周期，重新统计所有完整对局并选新种子。
6. 导航可能中止尚未播放的音频预加载，脚本单列ERR_ABORTED音频取消，不屏蔽图片/代码/其他网络错误；最后成功check没有该取消记录，errors为空。
7. 实际手机截图发现底部信息与操作遮挡、菜单重复标题；最小布局修复及去重后重建重测。

## 证据与包路径
- `evidence/build.json`：构建字节、源码文件逐项哈希。
- `evidence/rule-games.json`：120场规则统计与可复现种子。
- `evidence/browser/report.json`：最后成功check、视口、按项结果、最终dist哈希、实际请求、控制台及结束时间。
- `evidence/browser/*-sequence.json`及`*-events.json`：真实时点/姿态局面、动画阶段、落地/提交。
- `evidence/browser/quick-320-touch-start.png`、`classic-desktop-home-0.png`、`classic-desktop-result.png`等已实际多模态读取复核。
- 最终快速录像 `evidence/browser/video/page@30087e633fad680678d6558c61735158.webm`，2622840字节，SHA256 `a2d6b2d1b382bd3c8fb25ac02dc0707b13593da521ae88b82fd2afc4ee7af89f`。
- 最终经典录像 `evidence/browser/video/page@311bde440ea0d8b76c0bbb227d2d7c73.webm`，7197649字节，SHA256 `29478c68057bfb539a66ad6447acb3839e3ed772e24b6c9e205a269bc77d1216`。
- 早期失败录像/截图仍保留供溯源；仅最后成功report列出的证据属于最终验收，不以旧文件名推断通过。
- `releases/ludo-source.zip`：源码/锁文件/测试构建发布脚本/上游契约与报告/实际素材，不含node_modules、参考源码、原包广告和研究图集。
- `releases/ludo-play.zip`：最终dist；`releases/manifest.json`：ZIP与最终资源哈希。

## 限制及测试阶段交接
- 当前为代码阶段自验，不是独立测试阶段确认；测试阶段需按当次attempt重新build/test/check，不修改上游代码和资源。源码ZIP独立清洁安装重建及包内重建一致性尚未在本轮另建环境执行，留作独立测试复核，不伪称已验证。
- Chromium视口模拟不是实体手机。未做iOS Safari、Firefox、低端真机、ADB、Creator或联网采集；短横屏可contain但大按钮可能占比较高，推荐竖屏，未做完整短横屏交互矩阵。
- 实际运行资源来自用户研究包，商业/再发布许可未核验；交付不代表获得授权。无原游戏真实运行截图，不能声称像素级原版复现或已独立视觉服务验收。
- 五类动画有正常速度录像及事件证据，但本轮未对每种动画逐一执行“刷新×后台×确认重开”全组合；已测摇骰刷新、走子刷新、真实摇骰后台、运动中确认重开、吃子/归家/胜利确认取消暂停。需测试阶段扩展中断组合。
- 原音频解码与播放接口已接入，未做人耳试听/音乐无缝循环、真实声卡输出测量；自动播放拒绝不阻断玩法。
- AI为公开合法动作启发式，不承诺竞技强度；局时/胜率不从设计值推定。随机源可复现而非密码学对抗随机。
- 未新增/修改Skill，未生成AI图片，未执行其他项目代码。没有外部托管发布工具，本地独立路径已验证，线上发布由工作流后续处理。
