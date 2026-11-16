# LUDO · 原版贴图与动画版 — 美术交付

## 当前运行：清单接口有限补正

项目：3663442e040f42b2b73291ef2094884b；工作区：games/ludo-classic-reskin；阶段：art；attempt=1，resume=false；请求：ludo-original-art-20261106。

**58件运行资源全部沿用上一API美术run `0c71c52dcca24ebab342debc11aad7da`，本次未生成、编辑、裁切或替换任何图像/音频。** 参考路径、视觉设计和尺寸/alpha/帧序契约沿用下面的历史交付及`design/art-integration.md`，没有重新研究ZIP或把历史生产计为本轮新生成。当前仍为工程API Key / gpt-6.1-sol任务，不使用Codex登录或其他Key。

### 补正内容与实际读取

本次全文读取4个冻结Skill入口（casual-game-production、ai-art-automation、h5-canvas-reskin、azure-image2-generation）及四份冻结知识（general、board-games、web-common、canvas-web）；读取既有art报告、art-manifest、art-integration、审计脚本、审计证据和运行清单相关字段。下面历史记录中的ZIP/配套文档/图像阅读及API生产均属于上一run，不表示本轮重新执行。

仅修正`scripts/audit-art.mjs`写入简表的映射：
- `path`、`sha256`、`usage`、`source`全部为非空字符串，并在写入前逐项断言。
- `source`采用人可读中文来源，包含具体源ZIP、成员、原帧/处理方式；API编辑件另标真实参考路径及原provider/model。完整原来源对象保存在`source_details`，分类不变。
- 增加58件路径、顺序、SHA与既有简表一致的断言，防止接口补正改变正式资源。
- `visual-manifest.assets.source`仍是原对象；运行配置重新序列化后**内容与SHA256均不变**。不修改平台服务器门禁。

本次内容变更仅：`scripts/audit-art.mjs`、`workflow/art-manifest.json`、`evidence/art-audit.json`和本报告。未改任何运行资源、规则模块、原型、acceptance、spec或integration内容。

### 当前attempt真实验证与最终指纹

开始实际调用`inspect_assets`；修改脚本后实际执行`run_validation("node scripts/audit-art.mjs")`，**exit_code=0，attempt=1**。输出：`美术对账通过：58件，PNG 54件，音频4件，资产1107204字节；不代表游戏或音频播放验收。` 工具记录脚本执行产生内容变化的路径仅为`evidence/art-audit.json`、`workflow/art-manifest.json`。

随后实际对58件正式资源及清单/脚本/证据/规格调用`inspect_assets`：全部资源SHA与补正前及上一run清单一致，54张PNG+4段MP3仍为1,107,204字节。最终简表58件字段断言通过；没有把上一run的审计结果当作本次执行。

| 文件 | 本次最终SHA256 | 变化 |
|---|---|---|
| `workflow/art-manifest.json` | `7955424cd32138f68ebbb4356b51ed808af1f52a194260f2ce8647f8a3f4c4fe` | 来源字符串兼容及source_details |
| `scripts/audit-art.mjs` | `2f9b97a398ae0406c0843281b5a573f9aefde276b1ee34f0526a0e1dc3f392bf` | 映射与断言 |
| `evidence/art-audit.json` | `c5e8e38a168350e58d548beba6bde0ce4777a8090c2c419f8d61764be57c077d` | 本次真实审计输出 |
| `public/assets/visual-manifest.json` | `896bcf843a797a6dbcfa1f2edd46bf261d7e074d4369ae92235553e5b6b26c95` | 不变，131,682字节 |
| `design/art-resource-spec.json` | `673d2652214bda63d02091823fc7f015f61031ae2449be8fe030a29d4cce246b` | 不变 |
| `design/art-integration.md` | `b4c54d6a1baa0466c68747155f69c2d64222ff7f526a3f1add1458bf7ec75052` | 不变 |

### 当前限制与结论

历史无参考背景候选仍拒绝，不入allowlist、不作新参考。本次未调用图片API、未重新提取ZIP、未执行npm构建/测试/浏览器check，未编写游戏、确认、部署或推进下一阶段。未实际调用服务端`verify_art_manifest`，因此只报告本地字段断言、资源对账与哈希复核通过，不宣称服务器门禁已复验成功。后续游戏/动画/音频播放与最终dist验收仍按原integration及acceptance执行；授权未独立核实。

结论：有限接口补正完成，58件正式资源及运行配置不变，等待工作流审阅。

---

## 上一API美术run历史交付（以下“本轮”均指上一run）

项目：3663442e040f42b2b73291ef2094884b；工作区：games/ludo-classic-reskin；阶段：art；run：0c71c52dcca24ebab342debc11aad7da；attempt=1。

上一run修复/提取/生产与交接美术资源并确定接入验收条件。以下生产和验证为历史证据；清单、审计脚本和证据的当前最终指纹以本报告顶部补正表为准。未确认、未发布、未部署、未推进代码或测试。未修改src、已确认原型及上游设计/验收文档。

## 1. 采用方案与真实参考

Superstar为主：标准15×15十字棋盘、四角圆营地、红绿蓝黄功能色、亮面立体棋子、上下小头像/骰子座、深紫低对比菱格。Just Ludo只补充材质/动画研究，不混入该套资源或大品牌/金边布局。无北非题材、圆形棋盘、HTML仪表盘大卡片、整屏AI棋盘或风景背景。

已读取上游`workflow/prototype.md`、`design/visual-baseline.md`、`design/acceptance.md`、`design/reuse-baseline.json`；研究索引和原版两预览/棋盘装配图已实际读取。辅助JSON仅作定位，通过选定ZIP metadata读取、native逐件提取/哈希复用与工程图片处理核验，不执行参考源码或整包解压。

| 参考 | 实际路径/哈希 | 用途 |
|---|---|---|
| Superstar | `ref/公司skill整合/AHAgames/94034_Ludo_Superstar/Ludo_Superstar.zip`；SHA256 `9ec528932dff7b8ee0dff125aa57cc4663e1419435c7143dcef4533d3d3646b7` | 正式原版素材来源 |
| Just Ludo | `ref/公司skill整合/AHAgames/82251_Just_Ludo/Just_Ludo.zip`；SHA256 `190f2525f6b18b7104b5ee5fe28eb91d52996b2d73c9a4b2e8f73311be72de55` | 补充研究，不进入运行allowlist |
| 预览 | `reference-assets/original-super-preview.png`、`original-just-preview.png` | 已查看，非本轮游戏截图 |
| 分层证据 | `reference-assets/research-board-runtime.json`、`original-board-assembly.png` | 原运行十字/营地/透明外框与标记，不采用商店缩略板 |
| 帧证据 | `reference-assets/research-index.json`、`research-dice-frames.json` | 逐帧来源、HUD规格、原clip时序，已分段读取 |

已全文读取本轮4个冻结Skill入口：casual-game-production、ai-art-automation、game-reverse-engineering/modules/h5-canvas-reskin、azure-image2-generation。已读规定配套：ui-runtime-delivery、reskin-pipeline、structure-locked-reskin、component-restoration、pipeline。已读取四份冻结知识：general、board-games、web-common、canvas-web。方法用于结构锁定、分层资源、真实API与清单交接；未调用外部CLI、Python、GameArtAgent、Codex登录或其他Key，未更新Skill。

关键原metadata均由`read_reference_archive`读取，源前缀`www.hnyigegame.com/Ludo_Superstar/game/`：skin3-0 `loading/assets/resources/import/0f/0f000441e.f6f55.json`；背景/蓝绿营地skin3-1 `.../04/04afb2abe.9a5b4.json`；skin1 `.../0b/0b0754561.b16fd.json`；红棋子独立非旋转帧 `.../12/1289e33a-9cbc-4f3b-9d95-b399c7ed7970.f99c5.json`；骰clip `.../0c/0c67ce8ea.b217e.json`；PlayerInfo `.../05/05a1c9723.58580.json`；MapGrid `.../0d/0d4dc8f4b.c2128.json`；场景 `assets/main/import/09/09d798ff2.89558.json`；四色座框补充 `assets/resources/import/0f/0fd4eb583.d1ec9.json`。完整逐件源ZIP成员/metadata/帧/裁切映射见运行manifest，不重复抄长研究正文。

## 2. 实际资源交付

最终allowlist为**58件：54张PNG + 4段MP3**，素材实际总量**1,107,204字节**，运行JSON131,682字节。素材+配置约1.24MB，**不是最终dist包体通过**。

| 组件 | 正式路径（public/assets内） | 数量/处理 |
|---|---|---|
| 背景 | `background-edited.png` | 1张真实api-edited参考背景，719×1600 |
| 棋盘 | `board-cross.png`、`board-frame.png`、`camp-{blue,red,green,yellow}.png` | 6张原版processed分层：586×585十字、628×628低alpha外框、233×233营地 |
| 棋子/标记 | `token-{blue,red,green,yellow}.png`、`arrow-{blue,red,green,yellow}.png`、`marker-star.png` | 9张原版精确crop，全部非旋转采样 |
| 骰子 | `dice-face-1.png`…`dice-face-6.png`；`roll-{00,01,02,04,05,06,08,10,11,12,13,14,15,16,17,18,20,21,23,24}.png` | 六104×106骰面与20份220×220独立像素，共25条真实播放时序 |
| HUD | `hud-human.png`、`hud-bot.png`、`hud-seat-{blue,red,green,yellow}.png` | 两头像+四色座框，不伪称4个独立头像 |
| 圈/按钮 | `effect-landing.png`、`effect-selected.png`、`ui-start.png`、`ui-confirm.png`、`ui-close.png`、`ui-settings.png` | 6张原版native整画布规范，无第二次trim |
| 音效 | `sound-roll.mp3`、`sound-step.mp3`、`sound-capture.mp3`、`sound-home.mp3` | 4段逐件imported，字节未改；未提供胜利音效 |

图片输入实测为WEBP（合法Cocos优化的伪PNG扩展），工程process_art_image输出真正RGBA PNG。原件/图集不覆盖，保留研究用途。53张原版派生图归processed，4段未改音频归imported；背景归api-edited。轻量闪光/彩纸交接非空procedural设计，**未声称已经实现动画**。

产物：
- `public/assets/visual-manifest.json`：58件规格/源路径/SHA/运行相对路径、分层坐标、25条骰时序、trim恢复、HUD与程序化设计参数、构建allowlist。
- `workflow/art-manifest.json`：非空58件，每件path/sha256/usage/source，明确来源类别。
- `design/art-resource-spec.json`：生产映射、唯一背景prompt/参考/候选/最终hash与裁切参数。
- `design/art-integration.md`：可接入坐标/底座锚点、动画设计、规则表现分离、布局和真实验收条件；procedural设计SHA256 `b4c54d6a1baa0466c68747155f69c2d64222ff7f526a3f1add1458bf7ec75052`。
- `scripts/audit-art.mjs`、`evidence/art-audit.json`：美术对账工具与本轮真实结果，非游戏构建或浏览器测试。

## 3. 唯一背景参考编辑记录

真实生成一次：工程`generate_art_image`，provider=`openai-image-api`，实际图片模型=`gpt-image-2`，quality=high，API请求1024×1536；不能把图片模型称为文本作者模型。`reference_paths=["public/assets/background-original.png"]`，没有无参考回退或第二候选。

- 原紫纹理：从原背景图集crop[1,1,719,1600]得真实PNG719×1600，141,756字节，SHA256 `8d53617e1bb1f3c9a2d68195ff34713340a23e4d9d98558403ca00d62a17476f`。上传MIME=image/png，filename=background-original.png。
- API原始候选：`public/assets/background-api-candidate.webp`，10,098字节，SHA256 `84acdfc666a579d2ccbebadd57e098868a0e00bf92949eb9582d6e78ce0d7664`。
- 确定性后处理：中央crop[167,0,690,1536]，裁去左右各167列；target_size=[719,1600]，等比contain实际content_size=[719,1600]、offset=[0,0]，无透明/黑边，不拉伸。由于API画幅与原版比例不同，菱格覆盖范围有中心裁切变化，**不是逐像素锁定原纹理**。
- 正式`background-edited.png`：92,903字节，SHA256 `5c4efaae45391a01d7a701a0f96e5a6d0a2f04c53a7781fa2689bac80c00db3f`，RGBA719×1600，alpha[255,255]、opaque=1,150,400，透明/半透明均0。已实际读取原/候选/最终图片对照：深紫低对比菱格，未增加景物/文字/HUD，色阶更柔和；采用这一张作为本轮交接，不替用户确认。

实际prompt：
> 仅精修输入的原版紫色菱格背景纹理，不重新设计。保持原图竖向构图、菱格方向、大小和分布，以及上下渐变位置；仍为深紫低对比的手游底纹，只小幅改善色阶平滑和柔和丝缎质感，变化克制、接近原图。全画幅不透明，边缘连续，无黑边，无大明暗块。不要风景、建筑、人物、文字、标识、棋盘、骰子、卡片、边框、强光或新增装饰。背景是独立纹理，不包含任何游戏HUD。

旧run `2c30a5ff7d2e41e59899b8ef099359cc`的无参考候选已读`reference-assets/rejected-background.json`：原扩展/真实编码不符导致参考验证失败后旧运行退回无参考生成；该行为不符合要求。拒绝图SHA256 `9d6c4c5b541c96b7d785f0e22e2988961898d681a3fb119864d5bb76009493f6`。本轮不使用该图/不作新参考；未拿到旧工具原始异常文本，不编造错误码。当前修复链路按真实编码成功，无本轮背景API失败。

## 4. 必须保留的渲染取舍

- 外框alpha最高51，十字透明像素保RGBA，查看器黑底/透明RGB不代表画进了黑色底。外框不可当不透明面板。十字、营地、星箭头独立装配，不采商店缩略板。
- 六骰面保trim104×106、originalSize220×220、offset[4,3]，Canvas还原位置而非放大填满220。摇骰native已完整220画布，不再裁source_rect/套source_offset。
- 原25条时序i/30秒，去掉负时间dice0；03/07/09/19/22共享02/06/08/18/21像素，仍保独立原成员与时间。12/13、23/24不同，未合并。
- 原箭头[50,11,24,37]与原型[P0,P13,P26,P39]不同：沿用原贴图，但位置服从已确认原型。这是项目表现取舍，未静默修改原型/规则，未声称原箭头逐像素复刻。
- 棋子源中心与底座锚点分开；baseUV(0.5,0.82)是设计建议而非源元数据，接入需用实际营地孔/路径截图校准。同一棋盘变换、统一翻y，不重复map scale1.15，不改逻辑cellId。
- 默认真实时间骰833ms、逐格110ms弧跳、吃子回营、归家375ms闪光、胜利1000ms彩纸；程序化设计已交接，busy/epoch、先提交存档再只读播放、隐藏/重开/刷新取消等必须下游实现并验收。

## 5. 本轮真实验证与指纹

开始已调用inspect_assets；完成图片后对全部58件正式资源实际inspect_assets取得SHA256。工程process_art_image真实报告输入/输出格式、宽高、crop、alpha及hash；已查看关键原版/派生贴图和背景。没有把图像读取证据称为浏览器截图。

最后一次配置/脚本修改后，当前attempt实际执行：

`run_validation("node scripts/audit-art.mjs")` → **exit_code=0**。

输出：`美术对账通过：58件，PNG 54件，音频4件，资产1107204字节；不代表游戏或音频播放验收。`

范围：PNG签名/尺寸/RGBA color type6、源图集与native哈希、唯一背景参考/候选/最终哈希、25条帧去重合法性/时序、52个公共格唯一性、58件非空清单及路径。5个既有src文件与reuse-baseline哈希一致；上游文档指纹写入evidence。本轮未编辑这些上游文件，不把引用基线的旧测试当本轮通过。

| 文件 | 最终SHA256 |
|---|---|
| visual-manifest.json | `896bcf843a797a6dbcfa1f2edd46bf261d7e074d4369ae92235553e5b6b26c95` |
| art-manifest.json | `94978185ffab6821fab243361787b7ff449219dd7f61286eff896de7e4e075d6` |
| art-resource-spec.json | `673d2652214bda63d02091823fc7f015f61031ae2449be8fe030a29d4cce246b` |
| audit-art.mjs | `c330d3f16b7be4e0bfc1af194248da927898bd8a6f9eb88b5a8147ffb7ed9edd` |
| evidence/art-audit.json | `a051012628ae054595fd0f83d7a1b72d5feb9aae524a651ecce75eba937b062b` |

## 6. 未覆盖与下游门禁

- **未执行**npm run build、npm test、npm run check；本阶段无页面/最终dist交付。不称游戏、动画或包体通过。资源审计不是npm/browser验收的替代。
- 未执行逐件白底/深底/游戏实景透明边缘对照、Chromium自然输入、正常动画中间帧/ROI差异、音效播放/解锁、完整规则对局、存档生命周期或真机；这些均为代码/测试门禁，见`design/art-integration.md`与原`design/acceptance.md`。
- 胜利音效native未定位，不提供、不猜路径、不临时新生资源；胜利用交付程序化彩纸规格。两头像足够区分真人/机器人，四色框区分队伍，不补AI人物。
- 用户参考库外部商业授权未独立核实；来源如实标明，不能据“公司库”推定授权。无Creator MCP/ADB、联网采集或独立视觉服务结果。
- 后续只将确认allowlist和Canvas配置实际集成；资源字节不得擅改。真实npm build/test/check须在最终修改后执行，check访问最终dist并自动启停服务器，保留桌面/手机点击、动画截图与事件/ROI互证；check之后不重建/修改dist。最终独立`ludo-classic-reskin/`、相对资源无CDN、展开严格小于10,000,000字节，保留旧游戏。测试发现缺陷必须返回代码阶段修复重验，不能在测试阶段改上游。

结论：本轮美术资源与接入契约已落盘，58件真实资源对账通过；等待用户审阅，未代替用户确认或推进下一阶段。
