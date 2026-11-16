# LUDO · 原版美术复现——独立测试验收

## 结论与阶段边界

本轮为测试阶段，attempt=1、resume=false。**已执行的验收范围通过**：本attempt独立重跑构建、规则测试及最终dist真实Chromium验收；两模式由菜单真实输入完成到结算，120场规则对局通过；补充五类动画中断恢复及源码包重建一致性通过。无已复现的游戏阻断缺陷。仅新增测试脚本 `scripts/test-audit.mjs` 和验收证据/本文，未修改已确认游戏源码、HTML/CSS、玩法契约或美术。阶段确认与上线由工作流管理，本报告不自行推进阶段。

最终 `npm run check` 完成于 **2026-11-09T11:52:55.546Z**。其后未重建或修改dist。展开 **1064192字节**、73个文件、61份资源，小于10MB。

## 已读资料、参考与设计基线

实际读取三个冻结Skill入口：`casual-game-production/SKILL.md`、`ai-art-automation/SKILL.md`、`game-reverse-engineering/modules/h5-canvas-reskin/SKILL.md`；按需读取后者 `references/component-restoration.md`。实际读取全部四份冻结知识：`genre/docs/general.md`、`genre/docs/board-games.md`、`framework/docs/web-common.md`、`framework/docs/canvas-web.md`。

已读上游 `workflow/prototype.md`、`workflow/art.md`、`workflow/code.md`、`workflow/reference-evidence.md`、资源清单与集成配置；核对规则、随机、存档、动画、渲染、输入及构建/单测/check/打包脚本。构建逐份校验61资源的清单SHA256；另以inspect_assets复核棋盘、红子、骰帧、真人形象代表件。

真实参考（路径相对ref）：
- `公司skill整合/AHAgames/94034_Ludo_Superstar/gameInfo.json` 与 `Ludo_Superstar.zip`；包SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`。
- `公司skill整合/AHAgames/82251_Just_Ludo/gameInfo.json` 与 `Just_Ludo.zip`；包SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`。
- 本轮先用ZIP工具真实定位，再读取Superstar member `www.hnyigegame.com/Ludo_Superstar/game/loading/assets/main/import/0b/0be10531e.a5010.json`，字符0–7000、7500–15500；SHA256 `939a9d1fda59358fd9c388cd19e6e13bb0febd3eebdcc75b0f4e74ecf77a7393`。0–7000含MapInfo四队路线、八安全格、门与终点；后一范围主要是其他配置，不充当地图证据。
- 读取Just member `www.volcanoh5game.com/Just_Ludo/assets/main/index.js`，字符68500–78500；SHA256 `3334a9a60e060753ae65d2c89ab51376d5cfcd72f614efbe2c9ab9d3dd7d4c0f`。核对安全分支、吃子回程完成后开门及移动回调；未执行参考源码、未解压参考整包。

保留已确认取舍：经典2～4席首位四子精确归家即结束；快速两子预置、吃子永久解锁全队归家道、首子精确归家胜，扩展所有席位配置；仅两张已确认原版真人/电脑形象，取消16头像随机化。不复现参考Luck或暗改骰子。52外环+24私有归家格，八安全格；非安全落点进入前恰好一敌子才吃，多子免吃且不封路；6/吃子/归家仅一次奖励OR。快速开门保留绝对位置，normal末格下一步回起点，不瞬移入家。

界面基线为720×1280等比contain、原紫纹/十字棋盘/四色营地/亮面棋子/骰帧与形象，Canvas绘制与DOM大按钮互补，叠子用编号明确选择。浏览器截图复核320px快速起局、390px经典、桌面归家与结算，布局未裁切关键按钮、四色与棋盘格可辨；没有参考游戏运行截图，不能宣称像素级原版复现。

## 本attempt真实命令

补充脚本最后修改后，重新依次执行以下三项；不沿用代码阶段或早期测试结果：

|命令|退出码|结果|
|---|---:|---|
|`npm run build`|0|61素材哈希一致，展开1064192字节|
|`npm test`|0|11组全部通过，120场完整规则对局|
|`npm run check`|0|最终dist真实Chromium、两模式自然完局、触摸/鼠标与恢复通过|
|`node scripts/test-audit.mjs`（本轮补充）|0|交付包校验、源码包重建/单测、390触摸完整快局、五类动画刷新及真实后台恢复通过|

发布源码清单指纹：`59ba3aaecc16752aeafbe25dc56ba2eda4f4704a703bd3f6382a9a5353a1e4d9`，与代码阶段及源码ZIP一致。最终工具source_before/source_after均为 `cb3e497cfd6f9c7ff718ce9ae048c9ad83fb5b58516eb2448a972006eb7668e4`，包含新增补充测试脚本，范围不同不能混同。最终工具build_sha256：`66c6b9b2ca35116bf985eb8f02bd241ccc026de90522478d1e82c8e5b64b9b77`。补充脚本不在上游sourceFiles打包清单内，留在当前工程供复验，未偷偷变更上游源码包。

## 规则、随机、存档与AI

- 四队出营、门前转私有道、精确终点、超点禁止、完成子不可动；快速锁门循环及normal末格解锁衔接通过。
- 安全格免吃，单敌吃回营、多敌/混叠免吃、途经不吃不封路；吃子只永久打开行动席门，其他棋子不改位置。
- 轮转跳空席、无合法动作跳过、6保留、吃子与6奖励OR、首次胜利优先、重复动作提交幂等通过。
- 60000次点数抽样、相同种子重放及骰子/AI流隔离通过。拒绝采样按xorshift非零周期映射；统计只是辅助，不证明密码学随机或未来不可预测，未统计真人长期胜率。
- 经典/快速×2/3/4席×20种子=120场，从合法初始局运行到真实胜利，AI选择始终在合法集合，不注入终局、不改骰子。
- 各存档阶段结构、版本/骰子/位置/随机状态与冻结事务校验；损坏JSON明确提示，写入拒绝持续可见；运动计划不提前提交，逐段序列化后采样一致。

证据 `evidence/rule-games.json`。候选classic seed5：123次掷骰、106动作、1吃子、6归家、蓝胜；quick seed14：30次掷骰、30动作、1吃子、1归家、绿胜。这是规则对局统计，不是实测真人局时。

## 最终真实页面与动画验收

Chromium **153.0.8010.12**，桌面1100×900鼠标、780×720缩放、320×568及390×844触摸模拟。验收服务器由脚本隔离启动并关闭；只服务最终dist及其相对资源，覆盖根路径、`/independent/ludo/index.html` 和补测 `/audit/ludo/index.html`。无Cocos、广告SDK或必需远程资源。

主check由菜单→模式/席位→开始→真实骰子/棋子点击→自然结算→再来：
- 320快速seed14：绿胜，turn29，刷新后页面事件记录29次动作提交、133次落地；总规则动作30。
- 桌面经典seed5：蓝方第四子归家胜，turn122，刷新后页面事件记录105次提交、435次落地；总规则动作106。
- 事件内存会在刷新时重置，所以上述提交数各少刷新前一次，不能把刷新后事件数当全局总动作。最终结果与同种子规则对局一致。
- 3席同屏配置、4席混合AI合法动作与运动中确认重开通过。完整UI对局并未覆盖全人数×控制器矩阵，矩阵完整对局属纯规则。

正常速度保持默认：摇骰833.333ms/25原帧；每格110ms弧线；吃子120ms强调、逆程30ms/格+180ms回槽；归家400ms；庆祝1500ms后结算。两场均自然产生吃子/回程、归家、胜利。连续WebM录像配合sequence截图时间、动画段、落地与事务事件证明运动，不拿单张截图或静态日志冒充动画。120ms吃子强调容易被截图调用错过，回程录像与事件为主要连续证据；未将旧capture截图文件当成本轮新拍证据。

主check覆盖：真实连点锁定、设置冻结、摇骰刷新同点数、两模式走子刷新同计划、运动确认重开旧局不提交、吃子/归家/庆祝取消重开暂停续播、BFCache导航真实visibilitychange/freeze/resume；慢核心图像加载无开始入口、损坏核心图像重试、八音频AudioContext解码。

补充 `evidence/test-audit/report.json`：390触摸从新局到快局自然胜利（action30/turn29/绿胜），分别在rolling/walk/return/home/celebrating中暂停存档、刷新继续、取消重开、实际BFCache后台恢复。各段冻结后刷新前后game/plan相同；本轮前后elapsed示例：rolling50→66.8、walk50→66.6、return433.3→450、home166.7→183.4、celebrating200→216.7ms，前台输入间的正常推进允许保留，后台不按墙钟跳完。结果阶段刷新恢复结算、再来及新局运动确认重开通过。此补测是快局覆盖，不等于两模式全中断排列。

最终主check与补测console/pageerror errors均为空。早期主check曾单列一次导航取消未播放BGM的ERR_ABORTED，非核心加载失败；最后一次主check没有该取消记录。原音频仅解码/接口测试，无人耳试听或真实声卡测量。

## 交付包与重建一致性

保留上游发布包，已实际逐条解析ZIP及CRC32、哈希、路径安全检查：
- `releases/ludo-source.zip`：1171316字节，85条目，SHA256 `f8c3a1c8cb01292060307fc95d561cd58eb7749c66d89c53dacd82eae3cfa5c9`。
- `releases/ludo-play.zip`：1072704字节，73条目，SHA256 `c8c62cca7e3927c5b0af3548637acaa0a4b2424059ff724530d679156eb0589e`。
- `releases/manifest.json`：包与最终dist逐文件哈希。

试玩包每条目与当前dist字节相同。源码包提取到 `evidence/test-audit/source-rebuild/`，没有node_modules，使用包内build脚本真实重建并跑包内单测；73个重建文件与当前dist逐SHA256一致，两个进程退出码0。仅提取本项目交付源码包，不执行参考包代码。未运行清洁npm ci/联网依赖安装或源码包独立Chromium check；构建与规则测试不依赖node_modules，因此上述证据不等于依赖下载路径已验证。重建产物仅在evidence内，不污染源码指纹，也未重建最终dist。

## 证据路径与本轮录像哈希

- `evidence/build.json`、`evidence/rule-games.json`。
- `evidence/browser/report.json`：最后主check、视口、控制台、请求、截图名单和dist哈希；`*-events.json`、`*-sequence.json`及报告列出的PNG。
- 最终320快速录像 `evidence/browser/video/page@607f2181129a529eeef5ef56b0be0aed.webm`：2636021字节，SHA256 `9b95e25b5af14669b00efabf5d674b1a546398aac41fb513ea4db325793cdf42`。
- 最终桌面经典录像 `evidence/browser/video/page@280c2b749ae16cdf59b2e246433d907d.webm`：7192000字节，SHA256 `38705c0e6f220d9794b7cacd5ec977413be01951affa58f0bf6fc88cd30447af`。
- 补测390录像 `evidence/test-audit/video/page@e5e6c4a35c4cf0da4cac1414166b951b.webm`：3778791字节，SHA256 `2f01c40d5bd07ec060cb635dd282b1adc2e8b151f041c8479f1b052da5011515`。
- `evidence/test-audit/report.json`、`quick-*-restored-sequence.json`、连续PNG、`source-build.log`、`source-test.log`、源码包复建目录。

本轮录像文件实际经inspect_assets哈希清点；早期失败与上游录像留存但不算最终验收。多模态读取当前320起局、390经典、桌面归家/结算图作呈现复核；未声称执行独立视觉服务或全视频人审。

## 失败记录与限制

补充脚本首次exit1：110ms单段出营在Playwright逐按钮tap的自动等待间已完成，刷新后断言期望旧game而实际合法提交action1。改用可见按钮真实touchscreen坐标点按，并选择至少三步走子作为walk中断样例后exit0。只改补充测试脚本，游戏与素材未改；这是测试时序竞态，不是通过修补游戏掩盖缺陷。之后再次真实运行build/test/check全部exit0。

未覆盖/不声称：实体320/390手机、iOS Safari/Firefox/低端真机、ADB/Creator、全短横屏交互、全模式×全阶段×刷新/后台/确认重开组合、依赖清洁联网安装、人耳音乐无缝循环/声卡输出、真人局时和主观AI难度。存档校验已覆盖列明样例，不等于穷举所有恶意JSON组合。素材来自用户研究包，商业使用/再发布许可未核验；没有外部上线URL，不把独立子路径本地验收说成公网发布。无新AI生图、无其他项目文件访问、无上游Skill修改。
