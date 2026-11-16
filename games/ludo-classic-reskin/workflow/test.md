# LUDO · 原版贴图与动画版：独立测试验收

## 1. 结论与执行边界

**结论：本轮既定门禁通过，等待用户确认；未发布、未部署。** 未发现需要退回代码或美术阶段的已确认缺陷。此结论针对本报告记录的规则、Chromium 页面输入、正常动画、生命周期及离线构建范围，不代表所有设备或商业授权均已通过。

- 项目：`3663442e040f42b2b73291ef2094884b`；工作区：`games/ludo-classic-reskin`。
- 阶段：test；run：`e1c11cf67503417789e4ff685e4560db`；attempt=1，resume=false。
- 项目输入声明执行通道为工程 API Key / `gpt-6.1-sol`。本轮使用工作区文件与验证工具，未调用 Codex 登录、其他 Key、外部模型客户端或图片生成；工具日志本身不能独立证明服务端文本模型身份。上游图片编辑模型另为 `gpt-image-2`，不得混称。
- 只读审计已确认上游。未修改 src、scripts、tests、package、图片、音频或 prototype/art/code 报告，未安装依赖、格式化或放宽脚本断言。构建正常生成 dist/releases，check 正常更新 evidence。
- 三条验证均为本 attempt 实际执行，非引用代码阶段通过。最后 check 后未重建或修改 dist，仅复核证据并新增本报告。

## 2. 实际读取资料与参考取舍

本轮完整读取冻结 Skill 入口：`casual-game-production/SKILL.md`、`ai-art-automation/SKILL.md`、`game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md`；按需读取 `ai-art-automation/references/ui-runtime-delivery.md`、`game-reverse-engineering/modules/h5-canvas-reskin/references/component-restoration.md`。完整读取冻结知识 `genre/docs/general.md`、`genre/docs/board-games.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。

实际读取上游 `workflow/{prototype,art,code}.md`、`design/{acceptance,art-integration}.md`、`design/{reuse-baseline,art-resource-spec}.json`、全部 src 模块与相关构建/规则/浏览器/资源验收脚本。资源大清单为重点分段阅读，运行脚本逐件校验全部正式资源，不把局部人工阅读冒称全文。

真实参考位于 ref：

- `公司skill整合/AHAgames/94034_Ludo_Superstar/gameInfo.json` 与 `Ludo_Superstar.zip`；ZIP SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`。
- `公司skill整合/AHAgames/82251_Just_Ludo/gameInfo.json` 与 `Just_Ludo.zip`；ZIP SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`。

两个 ZIP 各分页定位首100项，未整包解压或执行。实际读取 Superstar 的 `www.hnyigegame.com/Ludo_Superstar/game/loading/assets/resources/import/0c/0c67ce8ea.b217e.json`（全文，SHA256 `759c137bf862a76d6ae487daa0f7817dcd03cda7587d7e10ac7e45713eda9c08`）及 `import/0f/0f000441e.f6f55.json`（同 loading/assets/resources 前缀，全文，SHA256 `578a950e708b5ad497df00e052c340b6f340b73d8d3e6387b2efa1563f0b9d2b`）；Just 的 `www.volcanoh5game.com/Just_Ludo/assets/main/index.js` 读取字符60500—72500区间，未声称全文复原其动画。辅助 `reference-assets/research-index.json`、`research-dice-frames.json` 仅用于定位与核对，不充当本轮新生产。

设计保留 Superstar 15×15十字棋盘、四角圆营地、四功能色、亮面棋子及上下头像/骰座；Just 仅为质感/动作参考，不进入正式素材。没有北非题材、圆棋盘、整屏 AI 场景或 HTML 仪表盘替代玩法。菜单/设置与可访问输入采用少量语义 DOM；棋盘与游戏 HUD 使用 Canvas 2D。箭头位置采用已确认原型的四出营点，而非逐像素复制源位置；背景允许低风险局部编辑，不承诺原纹理完全一致。

## 3. 真实验证记录与构建冻结

依次调用 run_validation：

| 命令 | 工具超时 | 退出码 | 本轮结果 |
|---|---:|---:|---|
| `npm run build` | 180秒 | 0 | 71文件，58白名单素材，展开1,287,748字节 |
| `npm test` | 180秒 | 0 | 11测试通过，0失败/跳过；测试总时长678.504ms |
| `npm run check` | 300秒 | 0 | Chromium 153.0.8010.12真实页面验收、正常动画与生命周期、源码ZIP独立重建通过；记录耗时77,524.719654ms |

三次工具记录的 source_before/source_after 均为 `4828bf4a10aeb38458d75618a027c3b6490c9154e691553e8393390465dd56d2`，构建指纹均为 `5128f172f4b90c6e7151712878e9bc95969bad5f2a2bc2388dcab11e1191fa79`。build/test changed_paths=[]；check 仅更新 evidence。上述是工具聚合指纹，不是单个 HTML 或 ZIP 的哈希。

最终入口实际读取 `dist/index.html`，以相对 `./style.css`、`./src/main.js` 和包内素材运行，无 CDN、无 Cocos；系统中文字体无需外链。展开体积远小于10MB。check 启动本地静态服务器访问最终 dist，并在 finally 停止；源码包解包重建发生于 evidence 隔离子目录，未替换最终 dist。

| 本轮产物 | 字节 | 收尾 inspect_assets SHA256 |
|---|---:|---|
| `releases/ludo-classic-reskin-source.zip` | 1,476,747 | `361b85036001d7f6c9ab3a63258abc426692fa702ba1506ca1f9e12cb78e8883` |
| `releases/ludo-classic-reskin-dist.zip` | 1,295,894 | `eb9df8117bbe1958135ec9b84e319e7eb699ff26e6ddee9d3b0c6ed1b1530caa` |

`evidence/packages.json`：源码包88条目、试玩包71条目；CRC与逐文件SHA校验通过；源码包独立 Node build/test 实际执行，重建相同。ZIP与代码阶段相同是可重复构建结果，不是本轮跳过执行。历史 `releases/initial-code/` 与旧失败证据不作为本轮部署入口或失败结论。

## 4. 规则、状态、存档与 AI

核心循环：当前席掷骰→仅选择合法棋子→同步提交并保存→表现时间轴→奖励掷骰/换席或胜利结算。玩法状态与渲染、输入分离；dispatch 单次提交 revision+1；观察接口返回冻结结构化副本，无改骰、改进度、强胜利命令。

门禁覆盖：四出营点与52格公共环、公共进度0…50、51…55各自私道、56终点；六点仅出营至0；精确到家、超点和已归家非法；安全格 `[0,8,13,21,26,34,39,47]` 不吃；普通最终格敌叠子全吃、经过不吃、同色不阻挡、私道不交叉。六点/吃子/到家奖励不重复叠加，胜利优先、无路换席、第三连六跳过且不撤销此前提交。

- 经典4枚全在营、4枚归家胜；快速2枚初始进度0/-1、1枚归家胜。2席[0,2]、3席[0,1,2]、4席全部。
- 经典/快速×2/3/4席×seed[1,2,42]共18完整合法规则局，6,405动作逐条确定性重放一致，revision唯一递增；详见 `evidence/rules-summary.json`。
- RNG mulberry32+拒绝采样；测试同seed复现、拒绝分支和真实RNG找到第三连六；AI只从合法动作中选择，AI选择/MOVE不消耗未来随机。此为算法与确定性公平性核验，没有进行大样本统计分布检验，也不声称达到密码学随机。
- rng/ai/lifecycle 保持复用字节；rules/storage 仅授权项目标识、键名及提示文案差异，由单测归一比对源SHA。独立版本 `ludo-classic-reskin-1`，存档键 `ludo-classic-reskin:match:v1`、设置键 `ludo-classic-reskin:settings:v1`。
- 损坏存档拒绝、Storage持续失败提示与恢复、刷新恢复提交状态、旧AI令牌失效均通过。规则单测可以构造边界状态；完整浏览器对局未注入骰子/棋子进度/winner。浏览器修改 observe 副本只用于证明隔离，Storage故障与延迟图片属于负面测试，不冒称自然局面。

## 5. 自然页面输入、布局与结算

`evidence/browser-summary.json`、`trajectories.json`、`input-regression.json`：

- 快速4人同屏 seed1：142次真实UI动作，73次ROLL、69次MOVE、吃4枚，蓝owner0自然获胜并结算，使用Canvas棋子点击。
- 经典2人机 seed1：140次真人UI输入；真人+AI共146次ROLL、136次MOVE（282提交），绿AI owner2四枚归家自然胜利并结算，使用Canvas棋子点击。
- 3席 seed5自然12动作覆盖三owner轮转；非当前席鼠标/Enter/Space/触摸不提交，减少动态后旧owner输入不提交。
- 桌面1280×800；手机模拟390×844/DPR2、320×568/DPR1、360×640/DPR2各真实触摸6动作。页面scroll等于视口高度、Canvas完全在屏；骰子触控分别56.328、46.219、52 CSS px，主要辅助控件最小44 CSS px。
- errors=[]。延迟棋盘图片时开始/继续禁用，ready后恢复存档一致。

已读取本轮 `evidence/mobile.png`、`screenshots/{quick-result,classic-result}.png` 与正常关键连续图。画面为紫底紧凑游戏场景、四色十字装配、四圆营地、上下头像骰座，主棋盘与骰子同时可见；不是网页大卡片或AI大风景。终点/营地与脚底设计锚点核对配合坐标单测；抽查连续帧未见错误旋转、裁切或固定纹理跳锚，不把抽查扩大为全部58件人工像素验收。

## 6. 正常真实时间动画与取消

完整UI局多数采用用户可选的减少动态加速；关键掷骰、走子、吃子及胜利动作切回正常，并以真实rAF记录与PNG像素差验收。**不声称整局按默认正常速度打完。**

`evidence/animation-events.json` 与 `animation-pixels.json`有8组正常帧序：骰17帧、普通走10帧、吃子前走9帧/impact3帧/回营14帧、最终走7帧/home8帧/victory21帧。阶段start日志记首个rAF，非时间轴创建瞬间，start/end差存在约一帧偏移，不误当精确阶段时长。

| 动作 | 设计时长与本轮证据 |
|---|---|
| 摇骰 | 原clip 30fps、833.333ms、25非负时槽；本轮事件467.4→1300.7ms，差833.3ms。142.9ms与159.6ms同frame4仍分别有2192/1643像素变化，配合y弹跳证明不只是换帧类名。|
| 逐格弧跳 | 每格110ms、峰缩放1.15。quick-1走4格设计440ms；step事件1700.7/1817.4/1917.4/2034.0ms，间隔116.7/100.0/116.6ms，均在90—130ms；55.999ms处scale1.14994，ROI变化755像素。最终蓝53→56走3格330ms，进入终点而非瞬移。|
| 吃子 | 先走→100ms碰撞反馈→黄3:1从17逐格逆路回营，30ms/格+末100ms cubic缓出=610ms；首帧进度16.4467，后续15.8867等位置连续。事件capture5883.8→6483.9ms（首帧已过16.6ms）。|
| 到家 | 375ms闪光；home16000.1→16366.8ms；150.1ms ROI变化682像素。已读home00/03/07，终点底座光圈放大后收束。|
| 胜利 | 24片彩纸、1000ms；victory16383.4→17383.4ms。已读victory05/13，彩纸由中心向外移动；之后真实结算。|

已抽查骰03/08/13、普通走01/03/05、capture00/05/13、impact01、最终走05、home00/03/07及victory05/13。骰ROI随弹跳移动，其他ROI为棋盘 `[12,126,336,336]`，不是每个精灵独立小框；以连续图与对象轨迹交叉核验，不把任意整屏变化充当动画证据。选中圈在busy期间不画，HUD呼吸位于棋盘ROI之外；减少动态关闭呼吸/演出，不改变状态/RNG/胜者。素材帧可含原始透视形状，位置锚点不随错误二次trim漂移。

生命周期证据：

- `evidence/lifecycle.json`：骰/走/吃×暂停/刷新/重开9例，naturalRetries=0，interrupt.busy=true且kind正确；真实重复点击10次并有CDP双指touchCancel。骰/走约94—111ms中断，吃约133ms中断。暂停/重开后等待2.1秒，提交状态/RNG/stats不重复，刷新不重播旧事件。
- `evidence/visibility.json`：原生Chromium双标签切换、CDP noDefaults与bringToFront，真实isTrusted hidden，不伪造document.hidden或冻结代替隐藏。骰/走/吃分别约9.0/9.8/16.6ms中断，后台2.2秒不变化；AI owner2在后台revision0保持，恢复后真实ROLL至revision1。
- main先提交保存再播，busy锁输入/AI；timeline epoch与TaskGate取消，隐藏/暂停/设置/重开停止音效并对齐已提交状态。

## 7. 资源真实性与最终证据哈希

正式58件，54 RGBA PNG+4原MP3，共1,107,204字节。53 PNG来自原版 imported 后 processed（精确裁切或保留整画布，规范原伪PNG实际WEBP），4音频 imported 字节不改；唯一1张背景为历史真实API参考编辑。正式全部资源通过白名单、尺寸/alpha/帧定义及当前SHA核验，本轮未生成新图。

- 编辑源 `public/assets/background-original.png` SHA `8d53617e1bb1f3c9a2d68195ff34713340a23e4d9d98558403ca00d62a17476f`；历史 `openai-image-api/gpt-image-2` 编辑候选SHA `84acdfc666a579d2ccbebadd57e098868a0e00bf92949eb9582d6e78ce0d7664`，crop[167,0,690,1536]等比至719×1600；正式 `background-edited.png` SHA `5c4efaae45391a01d7a701a0f96e5a6d0a2f04c53a7781fa2689bac80c00db3f`。旧无参考背景明确拒绝、不打包。
- 棋盘586×585+四233×233营地+628透明框统一缩放，不重复源map1.15；底座UV(.5,.82)为已确认设计锚点，不冒称原metadata。
- 骰面104×106、原画布220×220、offset[4,3]只还原一次；20独立摇骰整画布组成25时槽，03/07/09/19/22复用02/06/08/18/21，12/13、23/24不合并；源负帧不播放。
- 2头像（人/机器人）配4色框，不冒称4独立角色；标题中文界面保留通用LUDO、移除旧品牌/商业按钮。原路径→运行路径、用途与来源详见已确认 art-manifest/visual-manifest。

收尾 inspect_assets 确认冻结资料未变：

| 文件 | SHA256 |
|---|---|
| `workflow/art-manifest.json` | `7955424cd32138f68ebbb4356b51ed808af1f52a194260f2ce8647f8a3f4c4fe` |
| `public/assets/visual-manifest.json` | `896bcf843a797a6dbcfa1f2edd46bf261d7e074d4369ae92235553e5b6b26c95` |
| `design/art-integration.md` | `b4c54d6a1baa0466c68747155f69c2d64222ff7f526a3f1add1458bf7ec75052` |
| `evidence/browser-summary.json` | `adbea5087286500dc7b6ec23f0bdd144a03644e77a8e2270152da5fb1defcdcd` |
| `evidence/animation-pixels.json` | `717136aac2ef3a1bf8d6c24aecbb0cbf2cd5f24931d1d250dae78508f35689aa` |
| `evidence/animation-events.json` | `db72491e6abfba06a9cc689969091bdbc9a37d91f22eed8bce946f4d79d8bc87` |
| `evidence/lifecycle.json` | `42cee75c5bd47c1cfe051bf210c180decf7d3d72f7f67d10871dd4570340b4c2` |
| `evidence/visibility.json` | `b15ae209cd7e1e75738f8181d240bed5e939fad7de6c84d68431ea8e2f14cdb2` |
| `evidence/mobile.png` | `362d567436ed25919ac2883b6776962bbf0c1835b6f413f1515e9869e3b5df7a` |
| 本轮录像 `evidence/video/page@8eebc5ceb662638855d52a52146ca493.webm`（3,530,868字节） | `501c6f54cf7b337ce0af074977419b48690283431d62fd220f0325e8ffb39991` |

录像为本轮check产物；本轮读取连续PNG进行视觉复核，没有另用视频播放器逐帧人工看完录像，不把code旧录像混作本轮。其余复现与包体证据见 `evidence/{build,rules-summary,packages,trajectories,input-regression}.json`。

## 8. 限制与交接

1. 真实浏览器为Chromium桌面及手机视口模拟，未验收实体Android/iOS、Safari或其他浏览器，也没有Creator/ADB/外部视觉服务。
2. 已核验引用文件和资源契约，不等于商业授权审查；参考素材授权须由项目方另行确认。
3. 未逐件进行白/深底人工透明边缘与全部素材审美审核；关键帧与尺寸/alpha自动核验不替代全量人工美术质检。
4. 音频文件与异常处理已核验，未真人外放听音；未交付独立胜利音源，胜利使用彩纸/结算。延迟图片已覆盖，未主动制造真实解码失败后点击retry。
5. 完整局可减少动态，正常动态通过的是明确记录的关键动作及生命周期；随机公平性是拒绝采样算法与确定性/不多抽核验，非统计或密码学证明。
6. 报告与证据在最终check之后补充，因此本报告不在此前已验证源码ZIP内；未为把报告打包而重建。交接报告使用工作区 `workflow/test.md`。

下一步仅等待用户确认。若之后发现需改源码/资源的缺陷，返回code/art修复，再重新build/test/check；本轮不自行修改或推进发布。
