# LUDO · 原版美术资源交接

## 阶段与结论
仅美术阶段。恢复执行 attempt=2 已重新运行美术静态核验，不引用旧运行当作本轮成功。交付61个真实文件，总计931475字节（约0.89MiB），无AI整屏重绘，无新游戏引擎/玩法实现。资源文件与静态装配可供集成；**不是运行校准通过或最终游戏验收通过**。本轮用户真实答复：**“首版只使用已确认的两张原版形象，取消16头像随机化”**。因此首版交付原版真人、电脑两张形象，不随机选择16头像；未修改已确认上游文件，该范围调整明确交给下游执行。不自动确认本阶段或推进代码阶段。

## 已读输入与参考取舍
四个所选Skill及四份冻结品类/框架正文已在恢复前实际读取；使用原冻结输入。上游 `/workflow/prototype.md`、`reference-evidence.md`、`board-contract.json` 已读取，未修改已确认规则与坐标。

参考路径（相对ref）：
- `公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip`，SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7`。
- `公司skill整合/AHAgames/82251_Just_Ludo/Just_Ludo.zip`，SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55`。
- 两包各自 `gameInfo.json`；详细定位见 `workflow/reference-evidence.md`。

主来源为Superstar原版original皮肤的实际运行部件，Just仅作布局/规则研究补充，不混用其风格。保留紫色菱纹、奶油白十字、四色营地、亮面滴形棋子、白灰立体骰子。背景没有需要改动之处，未调用生图API。另提取skin2图集，未完成其帧索引分类：仅保存在 `reference-assets/superstar-ui.png`，**未当运行棋盘集成**。未整包解压或执行参考代码。

## 交付
- `public/assets/`：61份真实图像与音频。
- `workflow/art-manifest.json`：非空清单，path、sha256、usage、source均为非空字符串；复杂来源写source_details。
- `workflow/art-integration.json`：Canvas绘制、旋转、骰帧UUID时间序列、动画与声音映射。
- `evidence/art-preview.html`：静态装配入口。
- `evidence/board-assembly.svg`：嵌入真实素材的720×1280棋盘装配。
- `evidence/board-coordinate-overlay.svg`：76格中心标记与16营地槽装配。
- `evidence/dice-timeline.svg`：按clip真实引用顺序的25帧时间轴。
- `evidence/alpha-scale-samples.svg`：白底/深底棋子、骰面、门、星、头像代表样。
- `evidence/art-source-index.json`：逐帧来源native与原始rect/offset索引；其中路径为研究定位索引，实际提取以工具日志包内清单为准。
- `evidence/art-validation.json`：本轮实际静态核验。
- `scripts/art-index.mjs`、`scripts/art-delivery.mjs`：可复核的研究索引与SVG静态装配脚本，不是游戏源码。

## 尺寸、编码、透明与图集契约
|资源|实际尺寸/处理|用途与注意|
|---|---|---|
|board.png|586×585，精确裁切|营地区域透明，必须与四营地装配|
|background.png|719×1600，不缩放裁出|等比cover；不得拉伸纹样|
|camp-{color}.png|233×233，四份|蓝左下、红左上、绿右上、黄右下|
|token-blue/green/yellow|32×53 / 33×53 / 33×53|保留软透明边，中心锚点静态装配|
|token-red-packed|52×32，图集rotated=1|静态拟定Canvas顺时针90°恢复32×52；尖端朝向待真实显示复核；不要拉伸|
|safe-star|27×26|max alpha253，无完全不透明像素并非空图，禁止阈值抠底|
|gate-packed|33×15|恢复竖门为15×33，再按席位旋转；是门状态视觉，不封阻外环|
|dice-face-1…6|104×106|原画布220×220，trim绘制位置[62,54]；统一pivot[110,110]|
|dice-roll-00…24|220×220|原始native逐字节复制，实际编码WEBP，保留.png原后缀；浏览器依magic解码，不要当裁片再放大|
|dice-roll-sample.webp|220×220真实WEBP|process_art_image无缩放转换代表样，非额外动画帧|
|avatar-human / avatar-ai|96×121 / 121×128|原版同屏形象，不是自创头像；预览等比显示|
|info四色|146×146|保留四边软alpha，作为原手游玩家底件|
|back / button-ok / disabled|71×78 / 195×78 / 193×75|使用原手游按钮语言，文字由程序绘制|
|声音|8份mp3/ogg|摇骰、走子、吃子、归家、胜利、轮转、按钮、背景音乐|

原三张图集及新增头像/按钮native后缀.png但真实编码WEBP。裁件与头像/按钮通过process_art_image输出真实PNG，crop精确且target_size=null，无放大、无自动抠底。骰帧保留来源后缀是逐字节提取契约，不是伪造PNG编码；清单标明实际WEBP。代表摇骰帧透明38871、全不透明9142、半透明387像素，完整220画布仅有中间骰子与阴影，不能二次trim。board透明226480、全不透明113246、半透明3084像素；棋子、头像均含透明及软alpha。颜色未回锁重染，因为直接保留原像素。

## 坐标与界面设计
以 `board-contract.json` 为唯一76格/营地/停泊坐标来源，保留0.5px及1–2px偏差。静态设计转换 `X=360+1.15*x，Y=640-1.15*y`。场景mapNode父链、scale1.15与组层级已读取；Widget和默认锚点的实际运行效果仍待代码阶段核验，**不能将该转换称为已运行冻结**。

布局保留手游纵向棋盘与四角玩家信息。顶部返回/设置、底部状态与操作；预览展示返回和掷骰按钮，设置/菜单/结果属于下游Canvas交互集成，不另画网页卡片或侧栏。手机320/390及桌面contain，同一坐标变换用于绘制与输入；触摸热区至少44CSS像素但不得改动逻辑中心。静态预览未浏览器渲染，因此组合层次、门朝向与棋子pivot须在代码阶段真实页面对照后确认。

## 五类动画交接与验收条件
默认开启；最终画面由animation pose而非提前提交的规则位置驱动。
1. 摇骰833.333ms、30fps，正常25帧，clip负133.333ms为预滚不增加时长。时间轴由clip引用UUID→resources pack条目解析，而非文件名排序。相同图像连续重复属于原clip，不能删帧。开始即保存均匀独立结果，结束切原版结果面。
2. 出营单段；走子110ms/逻辑格，每格弧线升起与落地，不飞最终格，不多走6步。
3. 吃子120ms落点强调，受害者沿外环逆程约30ms/格，最后180ms回原槽；持续可见，无一帧消失假回程。
4. 精确归家最后110ms弧线，再400ms光圈/缩放入本席分槽；停泊不额外耗步，完成子不可选。
5. 胜利1500ms赢家光圈/彩屑/原头像，再结算；首名结束优先于回合奖励。

走子光圈、弧线影子、胜利彩屑可由Canvas程序表现，不声称已有AI动画图。动画中锁棋盘输入，设置/重开可取消；后台/设置暂停单调elapsed，刷新继续已保存阶段；重开generation令旧任务失效，不能延迟改变新局。声音对应art-integration.json，首次用户手势解锁音频，BGM与音效分开开关。真实验收须保留正常速度连续截图/录像与时间记录，证明多帧、N格N次落地、回营可见、精确终点、赢家庆祝及输入锁定。

## 本轮真实验证
- attempt=2 `node scripts/art-delivery.mjs` 最后执行exit_code=0：61个非空资源、76格、16营地槽、25帧引用解析及全部native220×220、清单字符串格式通过。
- 最后调用inspect_assets，显式传入61个public/assets文件路径，返回真实字节数与SHA256；资源未发生改动，与脚本生成清单使用的当前文件一致。来源研究文件/预览不进入public资源清单。
- attempt=2重新执行 `node scripts/art-index.mjs` 和 `node scripts/art-delivery.mjs`，均exit_code=0。补充六结果面精确crop、原始副本哈希和音频来源，修正BGM实际位于loading路径；清单来源追溯没有冒充授权证明。
- 前序read_file图像调用未返回可据此确认的视觉内容，因此不宣称逐件视觉复核通过。真实process_art_image返回编码、尺寸、alpha数据；本轮修正头像预览为等比显示，降级红子/门朝向为待确认。SVG/HTML实际存在，但不是浏览器截图。
- 美术阶段prepare_web_runtime被工具拒绝，因此未执行Chromium、鼠标/触摸、手机适配或真机验收。没有package.json/dist游戏，未运行npm build/test/check；这些是代码/测试阶段必须重新执行的验证，当前不越阶段制作游戏或绕过依赖门禁。

## 未完成项与限制
1. 未定位完整16头像；用户已明确取消首版16头像随机化，使用两张已确认的原版形象。此项不再阻碍首版资源交接；若以后恢复16头像需求，须另行定位来源。
2. 装配目前静态，待真实Canvas复核Widget、父链/锚点、棋子与门朝向、信息底与骰节点的精确相对位置；不能以静态预览替代动态验收。
3. 音频已按真实来源提取并核验哈希/非空，未解码试听、未验证循环衔接/并发播放。
4. 未有最终dist、源码包或试玩ZIP；不发布美术预览为可玩游戏。最终展开<10MB及相对子路径只能在代码/测试阶段验证。
5. 素材来自用户研究包，商业使用/再发布权利未核验；不编造授权。无联网采集、Creator编辑器MCP、ADB、独立视觉服务或真机操作。
