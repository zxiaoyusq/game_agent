# 彩球融境 · 美术资源阶段

日期：2026-10-18。当前交付为现有资源接入核验与追溯报告，等待阶段确认，不推进代码或测试阶段。

## 范围与归属

依据已确认的 /workflow/prototype.md，复用 Guru、HM、Infinite Joy 三款参考真实素材。现有源码、资源导入、引擎构建、截图与浏览器验证由其他工程制作 Agent 完成；本轮仅读取并核对，新增 /workflow/art-manifest.json 与本报告。未修改源码、资源、prototype 或 Skill，未生成 AI 位图。UI、背景、文字及星屑由现有 Cocos Graphics/Label/Tween 原创实现，不计作位图资产。

采用 cocos-game-production/SKILL.md 与 ai-art-automation/SKILL.md 的来源、用途、目标路径、渲染契约和分层验收要求，并读取各自 references/ball-sort-fusion.md、references/ui-runtime-delivery.md。按用户指定的现有资源模式执行，不启用历史 Windows 路径、GameArtAgent、ASSET_SPEC v2 生产工具或生图服务；契约集中在本报告及资源清单，不伪造生产规格校验。

## 已读证据

- /workflow/prototype.md：已确认范围、主题、布局和迷雾设计。
- /evidence/source-manifest.json：已读全部268行；逐项原始路径、目标与来源SHA256。
- /public/assets/asset-map.json：Guru 12、HM 1、Infinite Joy 12张PNG的加载路径。
- /src/main.mjs：已读全部269行，核对预加载、主题、布局、透明度、音效与使用条件。
- inspect_assets：本轮实际枚举文件及真实SHA256，确认25张PNG、3个WAV；28项均与source-manifest对应哈希一致。这是目标文件指纹与已读来源记录的比对，未重新计算参考原文件哈希。
- ref/BallSort工程拆解_2026-10-01/交付说明.txt：经read_reference读取，确认exports为规范导出、原包来自APKPure；不证明商业使用授权。
- ref/BallSort竞品拆解_2026-10-01/彩球分类头部产品拆解与融合设计报告.md：经read_reference读取开头至第8节片段，用于清晰棋盘、主题复用、底部工具和主动选择迷雾的取舍；未亲看竞品图片。
- /evidence/browser-validation.json、/evidence/engine-build.json：已有制作Agent的运行与引擎记录，非本轮重跑结果。

读取 guru/browser/art_summary.json 与 hm/browser/art_summary.json 均返回不存在；这两份材料未被核验，不用于尺寸或透明像素结论。

## 资源与来源映射

完整逐项表见 /workflow/art-manifest.json，格式为assets数组，各项包含path、sha256、usage、source；path为public/assets/...，source保留ref原始路径。

| 来源 | 目标 | 实际用途与引用 | 处理与边界 |
| --- | --- | --- | --- |
| Guru exports/Sprite 下ball01至ball12 | public/assets/guru-0.png至guru-11.png | 暮色海湾、极光花园球体；main.mjs:14–18、126–133、194–198 | 保留目标文件字节；颜色ID减1索引，Sprite CUSTOM正方形显示；不是新绘图片 |
| Infinite Joy exports/Sprite 下Ui_Game_1Ball_01至12 | public/assets/infinite-0.png至infinite-11.png | 清晨雾岛球体；同一球体函数与移动节点使用 | 同上；12张均预加载，不代表每一关都出现全部颜色 |
| HM tube_2 | public/assets/hm-0.png | main.mjs:147–149，所有模式试管玻璃高光，非仅高管 | CUSTOM宽高分别设置为管宽+3、管高+5；白色alpha70；来源清单“仅等比缩放”与代码不符，以实际代码为准 |
| HM BSP_touch-sound | public/assets/tap.wav | main.mjs:54–60、173–175，按钮及试管点击 | 保留WAV，音量0.35，声音设置控制 |
| HM tick1 | public/assets/move.wav | main.mjs:199，每球落位播放 | 保留WAV，音量0.35；本轮未试听叠音效果 |
| HM BSP_Full-tube | public/assets/complete.wav | main.mjs:229–230，整关完成播放 | 保留WAV，音量0.45；原名不代表本项目按满单管播放 |

加载依据：main.mjs:7–10读取asset-map，65–69遍历全部25个图片路径，经HTML Image、ImageAsset、Texture2D转SpriteFrame；三个WAV用assetManager.loadRemote加载并创建AudioSource。77行等待资源加载后继续场景。图片错误会拒绝加载；音频错误仅跳过该clip并resolve，因此无失败请求记录不能替代实际试听。此处是源码引用核验，不是本轮浏览器加载实测。

## 视觉契约

设计目标为低细节背景、球体优先、稳定颜色ID和可恢复操作。三主题只换表现，沿用同一规则与数字辅助。

| 主题 | 背景 | 卡片 | 边线 | 正文 | 次文 | 强调 | 球组 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 暮色海湾 | #101c31 | #1b2d46 | #35546e | #edf5f9 | #92a8bf | #82dfce | Guru |
| 清晨雾岛 | #e4ecec | #f7fbf8 | #c3d6d5 | #254951 | #688c92 | #2c9c8d | Infinite Joy |
| 极光花园 | #231e3a | #342b4b | #5c4c75 | #fbf0ff | #b5a1c6 | #f0c575 | Guru |

以上为代码色值，未测量实际贴图颜色或对比度。球体贴图颜色不由上述UI色板重染。程序球回退色板为#f45d70、#62c6ff、#ffc75b、#8be29a、#b993ff、#ff9e5c、#65e0d5、#ea95c8、#b3c754、#7b97eb、#f5e9bb、#c5987b。数字辅助使用深蓝底白字；未知球使用#687a91和问号，不绘颜色数字。

逻辑画布540×960，SHOW_ALL随浏览器适配。顶部品牌y434、菜单/标题/设置约y390，关号y320、状态y276，分隔y245；工具y-322，模式入口y-405，页脚y-458。六根及以下单行，其余两行；每行间距min(98,460/行管数)。单行球格43，两行高管球格204/容量，其余43；球显示边长为球格减3。管高为容量×球格+27，管宽min(球格+7,460/每行管数-18)。节点以中心定位，球按管底到管口排列；选中顶球上抬18逻辑单位。弹窗宽484、圆角26，遮罩opacity220/255。以上均为逻辑单位，不等于CSS像素。

透明分层：背景柔光alpha9、微点18；管阴影28、管底色110、高光90、管口140；HM玻璃叠层70。球体Sprite没有额外设置透明度，沿用PNG纹理透明通道。没有图集、trim坐标、九宫格或字体切图接入；Label使用系统字体回退，跨平台字形与符号仍需实测。

尺寸与缩放边界：本轮inspect_assets只返回字节数和哈希，未解码PNG原始宽高、alpha统计或WAV采样信息，不编造这些数值。球体渲染目标为正方形，只有原图也是正方形才能据此判定等比；本轮未证明原始比例。HM玻璃明确按宽高分别适配，应检查高管拉伸的视觉效果。未裁切、压缩、去底或修改资源，不声称完成透明边缘像素QA。

## 实际验证与外部审阅

本轮完成资源实际存在性、28项哈希与来源清单对应关系、25项图片配置覆盖及28项源码用途核对。清单不包含关卡、effects.json或证据截图，因为它们不是本轮运行美术PNG/WAV集合。全部球图是主题可选加载集合，不表示同屏同时展示。

已读browser-validation记录passed=true、浏览器153.0.8010.12、Cocos 3.8.8/WebGL2，errors与failedRequests为空；记录涉及主题切换、数字辅助、390×844移动撤销、高管布局和1440×900宽屏。引擎记录声明源码6340文件比对一致、tarball SHA256为8af14ad3f861b9edd1d90c928a676ccaec4d9ec6d0bce42f56c59c9b3a82afa5，运行时SHA256为c5dbfbd9008357af024539cb96071774d8d9809a5a1d3850b88389f7ac8fa1a0；均为已有证据，不是本阶段重建。

用户提供的外部审阅：编排Agent已看经典截图，并通过实际后端预览在360×640点击移动与撤销。此项按外部审阅记录，不归为本模型亲自操作或看图。本轮未打开截图、试听音频、运行浏览器或执行build/test，不能宣布视觉审美、透明边缘、音效听感、44 CSS像素目标或成品全面验收通过。美术阶段只写文档，不把后续代码/测试阶段结果提前确认。

## 差异与限制

1. main.mjs:152使用hidden && 非顶球 && 管内颜色种类大于1；同色未满管的下层球会显示，与prototype规定仅顶球可见存在差异。这里只登记，交代码阶段按已确认原型处理。
2. HM玻璃原清单描述等比，代码实际非等比适配；本报告已更正实际接入契约，未改上游文件。球体原始比例未解码核实。
3. 三主题源码已建立材质映射，但颜色ID跨两套材质的视觉一致性、亮主题边缘及高管比例未经本轮看图复核。快速动画设置的真实效果不等同于已经验证减少动效要求。
4. 来源可追溯不等于授权。清单记录的是三款提取资源的实际来源，未取得或编造商业使用许可，不称其为已授权原创资产。
5. 本轮仅完成资源追溯与代码契约核验；关键画面、试听及上述差异仍是阶段确认时应知限制。当前停止在美术阶段，等待确认。
