# LUDO · 原版贴图与动画版：代码与集成

## 本轮有限收尾（以本节为当前结果，以下首版记录保留为历史）

当前仅code阶段，attempt=1、resume=false；未确认、未部署、未发布、未推进test。执行通道按项目输入为工程API Key / gpt-6.1-sol；未调用Codex登录或其他Key，也未在本轮重新生成美术。

### 实际读取与保留

本轮完整读取3个选定Skill入口及4份冻结知识（general、board-games、web-common、canvas-web），按需读取换皮Skill的`references/runtime-diagnosis.md`；读取本报告、reuse-baseline、main/timeline/render/assets/map、core.test、build/zip/verify/check/browser-lifecycle，以及最新summary、animation-pixels、rules/lifecycle/visibility/package证据和实际手机/吃子中间帧。参考证据通过read_reference读取两款`gameInfo.json`，路径为`ref/公司skill整合/AHAgames/94034_Ludo_Superstar/gameInfo.json`和`82251_Just_Ludo/gameInfo.json`；遵照本次要求不重新研究ZIP、不重做美术。原路径→运行路径、imported/API编辑、尺寸/alpha/帧序仍由已确认的`public/assets/visual-manifest.json`和`workflow/art-manifest.json`完整交接。

58件资源经build/test/check逐件白名单哈希核验，保持已确认内容；prototype/art、manifest、已确认美术脚本/报告均未修改。收尾inspect_assets核验art-manifest、visual-manifest、audit-art、art-integration哈希仍与首版记录一致。五个复用纯核心本轮未编辑或格式化；rules/storage仍仅含首版授权命名差异，rng/ai/lifecycle保持来源SHA。

### 有限修改与验收条件

1. **归档目录**：一次性`node scripts/migrate-packages.mjs`真实退出0，将delivery内仅本项目两个ZIP迁至`releases/initial-code/`，未知内容会拒绝迁移、既有目标会拒绝覆盖；迁移完成后delivery已不存在，再开始build。正式build/packageCheck均写读`releases/`，未修改平台指纹门禁。迁移自身改变源码指纹是预期的准备动作，不作为最终构建通过证据。
2. **吃子缓出**：只改最后100ms为`1-(1-u)^3`，之前逆路30ms/格不变。新增端点/中点测试：逆路15ms x=45、30ms x=30；末段60ms起点(0,0)，110ms中点(87.5,70)，160ms终点(100,80)，超时仍停终点，后半段位移递减。规则/RNG不受表现采样影响。
3. **输入与ready门禁**：保留骰子owner校验与aria-disabled焦点行为；新增鼠标、Enter、Space、真实触摸点非当前席位，整份state（包括revision/RNG）不变；减少动态下owner2轮转owner0后旧按钮仍不能代掷。菜单开始/继续初始原生disabled，处理器再次校验ready；图片加载成功才启用，失败显示“刷新重试”按钮。真实延迟board-cross.png请求期间两按钮禁用，即使发click事件也不创建局面，释放真实图片后恢复存档完全一致。
4. **生命周期精度**：保留3×3用例及Canvas/CDP多指取消；连点改为真实骰子/编号按钮boundingBox中心交替10次。每次中断前断言busy且kind准确，错过窗口则从菜单自然重新准备，不能注入局面。本轮9例全部naturalRetries=0；dice约95ms、walk约94—111ms、capture约117ms时执行中断。真实两标签切后台继续覆盖dice/walk/capture，hidden前busy/kind明确；AI改正常动画quick2 seed1，明确owner2为AI，隐藏前revision0，后台2.2秒不变，恢复后AI实际ROLL推进至revision1。
5. **同seed重放**：原18局矩阵完整保留，逐条复用相同合法动作重放并每步deepEqual，最终state/RNG/胜者一致。实际18/18局、累计6,405条动作重放一致；见rules-summary。
6. **可读性与依赖**：prepare_web_runtime真实安装/核验Playwright1.63.0，移除未使用@playwright/test；官方npm固定Prettier3.6.2，由`node scripts/format.mjs`调用官方API限定格式化15个表现层/HTML/CSS/新增工程测试文件，未自写格式化器。补时间轴、输入提交/取消、叠子、白名单和自然轨迹中文注释。新增README，源码ZIP含README、依赖声明/锁和format脚本；排除美术生产脚本、一次性迁移/补丁/安装器和凭据。

### 最终真实验证（最后一次源码/脚本/依赖修改及官方格式化之后，依次执行）

| 命令 | 退出码 | 当前结果 |
|---|---:|---|
| npm run build | 0 | 71文件，展开1,287,748字节，小于10MB；58件白名单资源 |
| npm test | 0 | 11项通过；18局规则全对局/6,405步确定性重放；cubic端点/中点通过 |
| npm run check | 0 | 最终dist真实Chromium153.0.8010.12；77.807秒（含包CRC/重建和浏览器，低于300秒）；服务自动停止 |

三条命令的source_before/source_after**全部相等且同为**`4828bf4a10aeb38458d75618a027c3b6490c9154e691553e8393390465dd56d2`。build_sha256全部同为`5128f172f4b90c6e7151712878e9bc95969bad5f2a2bc2388dcab11e1191fa79`。最终check之后只读核验并更新本报告/evidence，没有重建或修改dist。

真实UI快速4人142次真人输入到蓝队胜；经典2席人机140次真人输入、合计282次提交到绿AI四枚归家胜。桌面1280×800和手机390×844/320×568/360×640继续自然点击/触摸，手机不滚动、棋盘骰子可见、辅助区≥44CSSpx。五类正常动画dice/walk/capture/home/victory保留真实rAF起止/中间帧/ROI像素变化断言，375ms到家与1000ms胜利均通过；读取实际手机图和吃子中间图确认原十字/四圆营地/亮面棋子和紧凑场景仍在使用，非整屏AI或HTML HUD替代。正常动态暂停/刷新/重开及真实隐藏不重复提交，存档失败持续提示、键盘焦点、观测副本隔离及无控制台/请求错误继续通过。

独立ZIP逐件CRC真实检查，源码88条目解包后在独立目录实际运行Node build和11项单测，与最终dist逐文件SHA一致；试玩ZIP71条目逐文件一致。未在最终check之后重建原dist。最后读取`dist/index.html`确认包内相对入口。

### 当前正式产物

- 试玩入口：`dist/index.html`，计划独立挂载`ludo-classic-reskin/`，尚未部署。
- 源码：`releases/ludo-classic-reskin-source.zip`，1,476,747字节，SHA256 `361b85036001d7f6c9ab3a63258abc426692fa702ba1506ca1f9e12cb78e8883`。
- 试玩：`releases/ludo-classic-reskin-dist.zip`，1,295,894字节，SHA256 `eb9df8117bbe1958135ec9b84e319e7eb699ff26e6ddee9d3b0c6ed1b1530caa`。
- 旧版两ZIP：`releases/initial-code/`，哈希记录`evidence/package-migration.json`。
- 说明：`README.md`、本报告；验证：`evidence/{build,rules-summary,browser-summary,input-regression,lifecycle,visibility,animation-pixels,animation-events,packages}.json`；截图`evidence/mobile.png`、`evidence/screenshots/`、`evidence/frames/`；当前录像`evidence/video/page@42207700926e0a24a95901dd42674414.webm`。

### 失败历史与限制

首版e684ed947ef943f38e7a0f6b49cb8667三命令实际退出0，但build前194ff44e…/后48e8d1dc…不同，阶段归档失败，**未确认**；下面首版“最终验证”是旧命令结果，不是本轮/平台验收成功。其原因与本次迁移已明确记录，不删除历史。当前收尾首次check曾因测试固定dice-2而点到seed1真实当前席位导致退出1；改为按观测找非当前席位，随后完整重跑build/test/check均通过。详情`evidence/finite-fix-history.md`和保留的browser-failure.json。

新增刷新重试按钮为失败恢复路径，本轮自动化实际覆盖延迟图片与恢复，未主动制造解码失败点击重试；此分支不扩大为真实故障全覆盖。浏览器模拟不代表Android/iOS真机、多浏览器或人工外放听音；无ADB/Creator MCP，未验证商业授权或全部资源审美。未修改规则、美术、旧游戏或平台门禁；未新增登录/广告/通用框架；等待本阶段确认，不发布。

---

## 首版历史记录（目录已迁移，历史结果不作本轮成功证据）

项目3663442e040f42b2b73291ef2094884b；阶段code；attempt=1，resume=false。仅完成当前代码集成与本阶段验证，未确认、部署、发布或推进test阶段。

## 1. 输入、来源与保留范围

本次实际读取3份冻结Skill完整入口：`casual-game-production/SKILL.md`、`ai-art-automation/SKILL.md`、`game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md`；配套读取`ui-runtime-delivery.md`与`component-restoration.md`。实际读取全部4份冻结知识general/board-games/web-common/canvas-web，以及确认的prototype/art、visual-baseline/acceptance/art-integration、reuse-baseline、全部visual-manifest、全部5个纯逻辑模块、研究棋盘JSON、camp-calibration与原版装配/两款预览图。

参考路径：`ref/公司skill整合/AHAgames/94034_Ludo_Superstar/{gameInfo.json,Ludo_Superstar.zip}`和`82251_Just_Ludo/{gameInfo.json,Just_Ludo.zip}`。本次通过read_reference读取两份gameInfo；不重新全库研究/解压ZIP，实际集成使用已确认美术真实文件。Superstar ZIP SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`，Just ZIP SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`为上游溯源记录，不冒充本轮再次审计。

开始与收尾实际inspect_assets核验。正式58件（54 PNG、4 MP3）全部与已确认art-manifest一致；背景是上游真实工程图片API参考编辑件，其余为原版imported音频/processed PNG。**本轮未生成或改动任何图像、音频、上游元数据/报告/美术审计脚本；没有使用Codex登录、其他Key、外部图片工具或新题材。** 项目输入声明作者通道为工程API Key/gpt-6.1-sol；本轮未另行调用模型客户端，不能把上游图片模型gpt-image-2改称文本作者模型。

原路径→运行路径、来源分类、保留/局部编辑、rect/rotated/originalSize/offset/尺寸/alpha/帧序完整沿用：`public/assets/visual-manifest.json`与`workflow/art-manifest.json`。运行引用集中在`src/assets.js`和`src/render.js`；禁止自动全目录打包。

## 2. 实现与视觉决策

- `src/map.js`：15×15十字P拓扑、私道/终点及原版16圆孔底座定位。颜色严格蓝0、红1、绿2、黄3。主板按586×585有效层等比缩放到336宽，不把628外框算入网格；营地不使用机械半格中心。
- `src/assets.js`：只加载清单54张规范PNG；trim面按原220画布在(62,54)绘104×106，摇骰原220整画布不二次裁切/偏移。25个时间槽对应20件唯一图片，重复槽保留时长。
- `src/render.js`：原版十字、四圆营地、透明外框、亮面棋子、星/箭头、四色座框、人/机器人头像、骰子与克制局部特效实际呈现。背景采用确认的低对比紫色参考编辑贴图；桌面同一竖屏场景居中，手机一屏，无网页侧栏/游戏HUD大卡片/圆形地图/景观。
- `src/timeline.js`：rAF采样的小型时间轴，无通用引擎/继承层。骰833.333ms；走子110ms/格、0.30格弧线和1.15缩放；落点圈、100ms碰撞、30ms/格逆路+末100ms回营；375ms归家闪光、1000ms24片胜利彩纸。视觉确定性不消费规则RNG。
- `src/main.js`：真实指针→统一合法动作，DOM语义按钮/≥44CSSpx编号辅助、Tab/Enter/Space、中文状态；同步提交并存档一次后演出，busy期间骰子/棋子/AI均锁定。暂停/隐藏/设置/重开取消旧演出和TaskGate，刷新只恢复已提交状态，不重播/补落子。
- `index.html/style.css`：准确meta description、系统中文字体、无CDN；菜单与设置为简洁语义表单，主游戏全部Canvas纹理。默认正常动态；减少动态与静音为可持久化选项。
- 音效实际引用4段原版MP3；首交互允许播放、静音/取消停止；play失败被安全捕获不阻断玩法。没有虚构胜利音效。
- 观测接口仅`window.ludo.observe()`，返回structuredClone副本；没有setDice/forceWin/loadFixture或状态注入入口。测试修改副本不能污染真实state。

有限位置差异：箭头服从已确认原型，放P0/P13/P26/P39；原版放归家道外缘P50/P11/P24/P37。没有宣称逐像素不变。星仍P8/P21/P34/P47。棋子底座UV(0.5,0.82)为接入设计锚点而非原metadata；以实际纹理圆孔和运行截图核验。走子幅度/时长采用确认的克制版本，不声称原Cocos动作逐帧移植。

## 3. 规则复用与授权差异

`design/reuse-baseline.json`保持原字节，记录上一API规则作者run `f4dcc9b6e1de48c4a30af42ff1d2be24`。rng/ai/lifecycle三个文件完全不变；rules/storage仅执行授权标识与旧提示替换：

- rulesVersion：`ludo-classic-reskin-1`；存档校验同步。
- 专用键：`ludo-classic-reskin:match:v1` / `ludo-classic-reskin:settings:v1`。
- 中文旧“商队”提示改为“玩家”。

规则及API未改；经典4枚全归家、快速首枚到家、2/3/4席、安全格/敌叠子全吃、奖励/第三连六均原样复用。单测将以上授权字符串逆向归一后与原SHA比较，仅用于核验改动范围，不改来源清单掩盖差异。不读取、写入或清理旧amber键。

当前rules SHA `c8067c018c739cf14fededd1d274615df6128a38fd6ace92bf69f424a642c441`；storage SHA `867660a934e080620c36116c8d88a0b757511133e2b77cd9d8ee786b2d01ab14`。rng/ai/lifecycle SHA与reuse-baseline一致。

## 4. 最终真实验证

最后一次源码/测试修改后，本attempt依次实际调用run_validation：

| 命令 | 退出码 | 结果 |
|---|---:|---|
| npm run build | 0 | dist/index.html，71文件，展开1,283,838字节，严格小于10,000,000 |
| npm test | 0 | 10组全部通过；18组经典/快速×2/3/4席×种子完整规则对局；坐标/圆孔、RNG拒绝采样、奖励/终点、安全/叠子、存档和取消 |
| npm run check | 0 | Chromium153.0.8010.12实际启动；最终dist服务器try/finally关停；自然输入、正常rAF动画及包重建通过 |

验证绑定源码指纹（工具source_before/source_after）`48e8d1dc437225ec0aa333a49faf6d7b701b85d55e8af0dca7966096e5d5ae10`；最终构建SHA（工具build_sha256）`9f73d6c9f420dda5ad35eafbbb0e45595c8124886393b47a43f063c1a17d03e5`。验证后只补报告/evidence，不重建、不修改dist。

真实UI结果（seed=1）：
- 快速4人同屏：142个UI动作，73次ROLL/69次MOVE、4枚被吃，蓝队先归家胜；真实Canvas点子与编号入口均走通。
- 经典2席人机：282次规则提交（其中140次真人UI动作，其余AI），146次ROLL/136次MOVE；绿AI4枚归家胜，没有强胜局注入。
- 三席配置进入并真实轮转3个owner；桌面1280×800、手机390×844/320×568/360×640触控操作，DPR1/2，无滚动，核心辅助按钮均≥44CSSpx。
- 正常动态下dice/walk/capture/home/victory全部采集真实rAF时间、Canvas getImageData ROI像素差、不同帧/不同中间位置与连续PNG；走子至少3段中间位置，吃子逆路被吃棋子可见；每类有实际绘制start/end与时长互证。截图时刻记录于animation-pixels，非仅静态终点或CSS类名。
- dice/walk/capture各覆盖≥10次点击、原生CDP触控多指取消、暂停至少2.1秒、刷新、重开；状态/revision/rng不重复提交，旧局不污染新局。
- 原生Chromium进程+connectOverCDP noDefaults默认上下文，两标签bringToFront产生isTrusted visibilitychange。dice/walk/capture和AI后台均真实等待2.2秒，隐藏期间状态不变且动画取消；没有改document.hidden或派发假事件。
- 键盘Tab/Shift+Tab、Enter掷骰、Space打开设置与返回焦点；存档写失败持续提示；finished刷新保留胜者；观测副本修改隔离。
- 源码ZIP真实解包并在独立目录执行Node构建及10组单测；与原最终dist逐文件SHA相同；distZIP解包逐文件相同。

首轮check曾在CDP进程退出后的目录清理发生ENOTEMPTY，真实退出1，保留`evidence/browser-failure.json`。修复为等待进程exit并有界重试清理，之后两轮build/test/check全部重新执行成功；不沿用失败或上一版本结果。

## 5. 产物与证据

- 可运行入口：`dist/index.html`（相对资源）；未来独立挂载路径`ludo-classic-reskin/`，本轮未部署。
- 源码ZIP：`delivery/ludo-classic-reskin-source.zip`，1,454,802字节，SHA `327724af26da0d497184715cbadb8ea0a55dfaac31d57452ab7fdf7427c58041`。
- distZIP：`delivery/ludo-classic-reskin-dist.zip`，1,291,984字节，SHA `cf8c9a0127a37188b66897aa8c412fdf62c7e5b0fc7ae7d0fa84466e5590dc58`。
- 必需依赖/锁：package.json、package-lock.json，Playwright1.63.0经prepare_web_runtime真实安装。重建：解包源码，npm ci，npm run build，npm test，npm run check；check需要本机Chromium（可设CHROMIUM_PATH）。构建只用Node内置模块；源码包不含node_modules/凭据/商业参考源码/美术生产脚本。
- 截图：`evidence/screenshots/B01-menu.png`、`evidence/mobile.png`、classic-result/quick-result；关键连续帧`evidence/frames/quick-{0,1,45,141}-*.png`。
- 最终正常速度录像：`evidence/video/page@9b1e7b9a380b0a396394bbc0a579b8df.webm`；此前录像保留为历史验证，不混称最终。
- JSON：build、rules-summary、browser-summary、trajectories、animation-events、animation-pixels、lifecycle、visibility、packages。详见本报告与`evidence/code-validation.md`。

收尾复核上游哈希仍为：art-manifest `7955424cd32138f68ebbb4356b51ed808af1f52a194260f2ce8647f8a3f4c4fe`；visual-manifest `896bcf843a797a6dbcfa1f2edd46bf261d7e074d4369ae92235553e5b6b26c95`；audit-art `2f9b97a398ae0406c0843281b5a573f9aefde276b1ee34f0526a0e1dc3f392bf`；art-integration `b4c54d6a1baa0466c68747155f69c2d64222ff7f526a3f1add1458bf7ec75052`；art-resource-spec `673d2652214bda63d02091823fc7f015f61031ae2449be8fe030a29d4cce246b`。scripts/audit-art.mjs本轮未运行、编辑或格式化。

## 6. 限制

自动化证明的是上述种子/轨迹/Chromium视口，不代表所有随机局、全部浏览器或真机体验。无Creator MCP/ADB，未做Android/iOS真机或人工外放听音验收；未独立核实用户参考库商业授权。未执行逐件白底/深底透明边缘人工对照；已核验资源RGBA/尺寸/哈希与游戏实景关键帧，不能扩大为所有素材审美通过。胜利音效上游未交付，保持无额外音源。源码包含构建校验必需美术清单与选定圆孔JSON，不包含原图集/中间输入/参考引擎。菜单和设置保留少量语义DOM，主HUD与棋盘由Canvas装配。未确认、未发布、未改服务器其他工程；test阶段仍需按工作流重新复核。
