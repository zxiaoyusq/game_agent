# Carrom 竞品美术与场景资源拆分核查

项目：3653a39b728d46d8a59a451c44aa688f。阶段：prototype；本轮 attempt=1 恢复后重新执行静态验证。

**状态：原包静态拆分报告已交付，带明确缺口；不是全量视觉验收或实施完成。** 本文替代旧 BLOCKED 检查点。竞品视觉、306项资源的独立清单哈希回填、未抽样图片的尺寸及所有透明边界仍未完成。研究不能直接充当生产切图单或上线许可。

## 1. 范围、安排与取舍

仅分析用户提供的历史快照，输出页面—资源关系、分类、待制作规格、优先级与风险。不执行原游戏、不改线上或本地主工程，不生成替换美术、不做集成、不推进美术/代码/测试阶段。首次工作区为空，本轮只建立隔离研究文件；未访问其他项目、网络、编辑器或设备。原件授权状态未核实，提取仅作研究引用。

平台提问收到的真实执行安排为：**“项目协调者决定：先完成原包页面与资源拆分，竞品视觉部分明确标为证据不足，等待补充截图后再核对；此为执行安排，不代表用户对任何设计的确认。”** 不将此安排记为风格、换皮方案或后续阶段的用户确认。

参考原包实际使用 PIXI、Planck、Howler。虽本项目技术配置为原生 Web，本轮不是重写游戏，不能为满足配置擅自替换历史引擎或执行参考工程。默认玩家语言为 English；本文及日志为中文。只研究原文案，未创建游戏页面或改写历史 HTML；后续如另获授权，英文界面应覆盖 Carrom / Disc Pool / Freestyle、Shop、Settings、Play、Resume、Home、Yes / No、Claim、Free Spin、You / Opponent、Prize / Entry Fee 等菜单/状态语义（这是文案建议，不是逐图OCR结果），新页面设置 lang=en。

已实际读取所选三个技能入口及 H5 intake-and-direction、html-workbench、component-restoration 配套正文，采用证据分级、原路径/状态/锚点契约与散件定位方法；不将技能的完整换皮设计确认、HTML工作台、生图或 Python 渲染流程扩大到本次纯分析。已读取四份冻结正文：genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/native-web.md。技能和品类中的案例不能代替本项目验收。

## 2. 参考来源与证据等级

参考路径相对 ref/；原包 member 前缀统一为 `www.excellenth5game.com/Carrom_Clash_Master/`。下文 assets/ 相对该前缀。

### 2.1 竞品证据

`mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip`

ZIP SHA256：`ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1`。35条，展开2,411,908字节，清单全读。只有 analysis/、disassembly/、report/ 文本、CSV、JSON，没有截图、图像、图集或场景美术。

已完整读 `report/竞品_ARM64代码定位.md`，SHA256：`c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f`。shotPowerLimits、MatchShotSolver、physicsStopped、queenCovered 是历史 ARM64 字符串/调用定位候选，不证明实际规则、求解算法、AES解密或线上行为。报告中的外部目录不是本ZIP内资源，未越界取材。

**竞品画风无法观察**：材质、造型、配色、背景层级、UI构图、光效边界均无图证。不使用原H5素材或技能中其他游戏图替代竞品证据。补证建议：同一版本的大厅、选桌、对局、暂停、商店、胜负、奖励页面截图，以及主要按钮按下/禁用状态和原始分辨率；须带来源与版本信息。这只是待补证清单，不在本轮采集。

### 2.2 原包

`mcp-inputs/mac-codex/2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2/Carrom_Clash_Master.zip`

ZIP SHA256：`2b404cd4b23702153c3279109bcd48bf79ee9e2141fc3334492a100c66036db2`。329条，展开5,074,490字节；0/100/200/300四页全读。321条assets，另8条为README、两个HTML入口、developer_v2.js、game.js与三库。未整包解压或导入。

已完整读：
- index.html：SHA256 `3fb70363f17dc63925ffa5b60b2bb2a3a335183f525876594abe62e7d6ed6bf4`。
- game.html：SHA256 `a16b6c4ac755e776958576708f95b8586eddaa0a918070fff4137dc18dc78d73`。
- developer_v2.js：SHA256 `ecaccd063d47e7a8e002f2e697282e9a3ba93c1aa3cbfd24d3b6c3cf26ef3c47`。
- js/game.js：513,553字节，SHA256 `2a036140fcf41e307b604373d307ff4014d061eef4bee5fb9504b90424b3460e`，提取至 reference-inputs/original-game.js。

原创脚本只解析字符串表，依据9个字面量锚点核对shift=481、1025项字符串、505个别名，不运行混淆初始化。衍生 source-decoded.txt 保留原行数，SHA256 `7d0ef0f78f41ed4a6fd101357ebb7bc3828294aa56324eac818044b17b36330a`；不是可运行替代源码。本报告行号均指该衍生文本，可回溯原JS行。

证据等级：A=真实清单/文件头/哈希；B=已读源码实例/绑定；C=名称与加载声明推断；U=未测/未知。A、B都不等于游戏实际运行通过。逐项 instance_candidate_lines 只是键名引用候选，包含配置和引用，不全是创建实例。

## 3. 主要页面—资源映射与布局

这是历史源码支持的页面/层级关系，不是实际点击路径验收。

| 页面/层 | 资源家族及拆分 | 动态内容/交互 | 证据与置信边界 |
|---|---|---|---|
| 外层入口/加载 | HTML iframe；preloader/bg.png、loading_title、loading_bar_base、loading_bar_purple | 加载条宽度独立变化，不能烘焙到背景；底部广告区不是游戏画面素材 | index/game.html完整读取；JS初始化，A/B；网络行为未运行 |
| 大厅 | lobby_bg整图；lobby_title独立；三模式按钮各有状态图；shop/settings/tutorial/bonus/video入口独立 | 金币与倒计时使用运行值；模式按钮不是背景上的假按钮 | 行9780–10060，B；Disc Pool mode0坐标(305,560)、Carrom mode1(305,727)、Freestyle mode2(305,895) |
| 选桌 | select/五组base+title；返回/左右箭头/select按钮；prize/fee底板 | Prize/Entry Fee为独立BitmapText，43px/33px，不能写死在base；选桌状态独立 | 行9361–9437，B；名称和加载清单为A/C；五套尺寸只抽样Delhi |
| 匹配 | tables配置中的bg/logo；matchmaking_bg_*_slices作为cover单独Sprite；头像、玩家棋色、reward_pot_coins、single_coin | 对手资料、奖励池值、飞金币分离 | 行9048–9079、9289–9296，B；cover anchor0.5、x320、y1137/2；slices文件名不证明多切片或九宫格 |
| 对局 | tables/0–4背景、logo、table、corners、四角与striker条；Carrom黑/白/红/striker；avatar框；aim/line/arrow/overlay | 棋盘/棋子/瞄准层不能并入场景整图；分数、回合时间、身份标签独立 | 初始化与行10423–10632、10917–10950，B；切换主题通过配置取纹理，不能只查直接键字符串 |
| 暂停/设置/退出确认 | pause/settings底板、标题、Home/Resume/教程、声音/音乐开关、close、Yes/No及exit_question | 遮罩、底板、按钮、off/pressed/sfx分离；声音off不是disabled | settings_pause_base行6268及通用按钮行11136–11234，B；所有弹窗拦截/穿透未运行 |
| 教程 | tutorial/WOODEN_BASE、screen_design、title、编号教学图、hand、左右箭头 | 箭头/手势是独立对象；教学图中可能有静态说明，但未目视确认烘焙内容 | 清单与加载声明A/C；图头抽样WOODEN_BASE，A；页数命名不代替页序/可达性验证 |
| 商店 | shop_bg、header、tab、金币底板、stone/strike商品、买/升级/选中/变暗图层 | 商品名、价格、升级指标和持有金币属于动态文字；商品展示图可能也作为对局装饰，不能合图 | 清单/加载声明A/C；棋子构造中商品子图scale0.26，行10436起，B；全部商品状态未逐个实例核验 |
| 胜负/结算 | winner_background、winner_glow、results_title/stones、you/opponent资料、胜负装饰、claim/claimx2/try按钮 | 分数/奖励独立；遮罩不是背景本身；胜负调用外部SDK | 胜负函数行2781起；结果构造行7378–7415，B；background alpha0.9，glow独立子节点y=-320 |
| 转盘/奖励/更新弹窗 | wheel底、指针、背景、shadow、lights、confetti、静态标题；update视频/领取/Spin按钮 | 旋转转轴与奖励值/倒计时保持；不能把指针/按钮烘焙入轮盘 | 清单/加载表A/C；转盘base图头576×576，A；扇区数字是否烘焙/实际内容未知 |

公共头像、金币与数字底板可复用设计母版，但保持每个引用路径/显示状态。清单无直接实例的资源不得自动删为“未使用”。

## 4. 逐文件清单与分类约定

`/workflow/resource-inventory.json` 包含321项，每项有完整member、源ZIP路径、来源说明、加载键、路径行号、实例候选行、类别、优先级、尺寸/格式、哈希/字节数状态、透明边界状态、约束、复用建议及研究交付状态。轻索引为 `/workflow/archive-assets.txt`。

**重要覆盖限制**：321项路径均建立；15项本地实测哈希/尺寸已写入；306项哈希与字节数尚未迁入独立JSON，标UNKNOWN，不是缺文件、也不是已逐项实测。此前ZIP真实清单返回过逐条哈希，但本轮未完整落盘回填。`/evidence/archive-metadata-coverage.json` 如实记录此缺口。所有未提取项尺寸/格式及所有alpha边界未知；不能把同族尺寸外推给未测文件。

四大交付类及附加类：
1. **背景整图/覆盖层**：仅非交互环境与不变装饰；场景bg可整图，cover保留独立层。不能把按钮、计数、棋盘、棋子或遮罩响应合到背景。
2. **独立可点击控件**：完整up/down/over/off/disabled纹理契约；是否可点击以绑定为准，不依赖button/hover文件名。按钮可承载不变英文标签，但可变价格/倒计时不得烘焙。
3. **棋盘与棋子**：board、corners、袋口示意、striker条和各身份棋子分件；商品外观与刚体轮廓区分，留住黑/白/红与striker的功能识别。
4. **动态文字**：PIXI.Text/BitmapText运行生成，交付字体依赖、底板及样式，不另造“固定金币截图”。字体TTF、FNT、页图必须作为关联包核对。
5. **附加独立类**：静态图文/教学图、效果/动画帧表、音频、头像/图标。并非所有独立件都应点击；加载条是动态显示，不是按钮。

分类是名称+加载声明初分，主表中的B级核对结论优先于JSON候选类别；尤其 title_with_glow 是可能含光的静态标题，非已证明可拆独立光层。优先级是工程风险建议，不是用户批准的制作顺序。

## 5. 已测尺寸及制作契约

15件逐字节提取至 `/reference-assets/`；源member、实际bytes及SHA256见 `/evidence/static-audit.json` 的samples，与清单对应。工具图片读取未提供可见图像内容，因此**没有目视画风/裁切/透明像素测量**；下表只是原创Node解析真实文件头的宽高。15个后缀均为.png，实际内容全部是WebP，不能据后缀承诺PNG管线或透明特性，也不能推断全包均是WebP。未转换、裁切或改名。

| assets/内原路径 | 宽×高px | 拆分/保持建议 |
|---|---:|---|
| Carrom_black.png | 34×38 | identity与视觉中心保留；不裁成正方形 |
| Carrom_strike.png | 86×86 | striker独立；不能用图边长当刚体直径 |
| lobby/lobby_bg.png | 854×1390 | 背景母版，不合入口按钮/数值 |
| lobby/lobby_button_carrom.png | 512×180 | 独立主体及不变标签，保持占位 |
| lobby/lobby_button_carrom_hover.png | 512×180 | 源码绑定为down，保持状态尺寸/中心 |
| tables/0/delhi_lounge_table.png | 630×637 | 几何敏感，不改实际纹理宽高/袋口位置 |
| tables/0/delhi_lounge_corners.png | 630×636 | 独立覆盖层；比table矮1px，不能擅改成相同高度 |
| tables/0/delhi_lounge_table_01_background.png | 855×1391 | 场景环境母版；不与board合图 |
| matchmaking/matchmaking_bg_delhilounge_slices.png | 855×1391 | cover单层；不按名字擅拆切片/平铺 |
| select/tableselect_delhilounge_base.png | 502×732 | 选桌卡底；Prize/Fee与选择按钮分离 |
| shop/shop_bg.png | 854×1390 | 商店环境；商品与价格分离 |
| pause/settings_pause_base.png | 556×527 | 弹窗底板，开关/标题按原实例分离 |
| tutorial/WOODEN_BASE.png | 477×707 | 教学底板；箭头与手势独立 |
| result/winner_background.png | 854×1390 | 结果背景；glow/奖励/控件独立 |
| wheel/carrom_spinning_wheel_base.png | 576×576 | 保留中心与轮盘转轴，不能凭尺寸重写旋转 |

帧契约来自源码src.sprites（非实际整张图头）：impact_a=6帧、104×116；impact_b=5帧、104×116；puck=15帧、127×133；stone_pot=8帧、104×116；title=25帧、219×189。保持每帧画布、顺序、转轴、帧间主体位置，未核对sheet布局，不推定总图尺寸或自动重排。

tutorial/ARROW_LEFT.png与select/tableselect_arrow_left.png逐字节相同，RIGHT对应同样重复：可复用母版并分别导出原路径，不能因重复而删除路径。其他五桌场景、模式按钮和弹窗可复用风格模板，但并不因此允许统一尺寸或合并纹理。

## 6. 外扩光效、坐标适配与交互风险

### 6.1 光效和切图
- 用户约束：**可点击控件主体切图不得带外扩光效**；保留原画布/主体占位，不以裁去透明边距缩小图片。已存在的winner_glow、overlay、highlight及sfx等保持独立效果层；名称候选须核对实例和合成方式，不能因叫glow就认定实际带光或不影响点击。
- `tableselect_mumbaiplaza_title_with_glow.png` 等名称提示可能内嵌光，未目视/alpha测量，不能报告“已抠出”。如果原控件状态纹理内嵌外扩光，允许的美术方案是原尺寸重绘无外扩光主体、保留视觉中心；不能擅裁图、改坐标或新增节点。
- 若要求保留原外扩效果而原实现没有独立层，新增effect层/命中区将涉及非美术代码。应在实际制作前提交具体冲突和授权请求；本轮只提出风险，不选择、不改代码。原件不存在的效果层不应在交付表中冒称已生产。

### 6.2 坐标
- 设计坐标640×1137，PIXI resolution1、transparent、无antialias。`_0x4bf9dd`按视口宽高的最小比例缩放，再计算额外逻辑宽高；额外宽度clamp≤213px，容器偏移extra/2。背景854×1390并不是设计分辨率，不应把整个画面强拉成背景图比例。
- 瞄准输入行3682–3695使用event.data.global减额外宽高的一半；滑条行10917–10950同样减半宽偏移、记录拖拽起点并clamp。源码不是直接把CSS client坐标当逻辑坐标；PIXI交互管理器的CSS映射/iframe偏移未实际验证，也未独立完整审计库实现。
- 不自行再除缩放或修改全局坐标；未发现hitArea/getLocalPosition字面量不等于不存在默认命中或坐标转换。桌面、手机、DPR、横竖屏、banner iframe变化可能产生偏移；仅靠图像尺寸不能保证触控准确。

### 6.3 输入状态
- 大厅Carrom普通/_hover两图同为512×180，但实际注册down，不可只制作“悬停”忽略移动端按下。
- 通用button行11136–11234有pointerdown/up/upoutside、up/down/over/disabled状态与按下scale0.9；状态主体中心不一致会跳动，外扩光/透明空白变化可能改变默认bounds和点击反馈。
- 选桌select按钮的hover纹理同时用于down/disabled；必须保留此历史引用关系，不能擅把disabled图当“按钮一定可点”或改绑定。
- off、down、disabled含义不同。弹窗遮罩、退出upoutside、多指、拖出画布、旋转中断、失焦再返回与pointercancel完整恢复均未浏览器验收；本轮不报告这些已通过。

## 7. 物理、输入窗口、计分与胜负保持条件

本任务不重新设计规则，以下只是历史静态事实/候选。核心循环为大厅选模式→选桌→匹配→摆放striker→拖拽瞄准/蓄力→释放→模拟碰撞与入袋→延迟结算/续回合或换手→胜负弹窗/奖励→返回或重开。资源不能改变这些状态判断；所有路径自然可达性未运行证明。

| 项 | 已读历史证据 | 换皮保持条件/未知 |
|---|---|---|
| 时间步 | 行5491 `world.step(1/60,10,10)`；5499–5504 ticker累积while >1补步 | 保持固定1/60秒及迭代参数；未見明显补步上限，不保证长帧/恢复性能 |
| 场景几何 | table中心(320,624)，墙体基于实际纹理尺寸，内缩26px，物理单位=逻辑px/100 | 纹理尺寸参与物理，不是纯视觉；不得改board像素宽高或留白；corners高度差1px保持 |
| 袋口 | `_0x2fc10d`固定计算位置，入袋距离≤20逻辑px | 按常量计算袋口中心(61,362)、(579,362)、(61,886)、(579,886)；图示必须对齐，未做像素量测 |
| 棋子 | 行10423–10483黑/白/红类型，Circle刚体/bullet；基础Sprite anchor(0.5,0.45)、scale0.98；商品子图scale0.26，light独立 | 素材边框/视觉圆心不能替换刚体；类型不能只靠装饰花纹识别；不强裁34×38 |
| striker | 行10573–10632，Circle；贴图scale=0.78×0.55×0.8；overlay scale0.64、alpha0.5；初始fixture isSensor=true | 初始sensor不能解释为整局不碰撞；状态切换需运行核验，保持原美术锚点/中心 |
| 可输入窗口 | 行3655–3680：教程阶段与两个运行标志门控；已在瞄准则拒绝重复start；release隐藏aim并清状态，strength≥0.25才发射 | `_0x647bf3`初始150px，距离clamp并归一化，因此该版本静态阈值对应37.5逻辑px；不是输入毫秒窗口；不足阈值不发射，≥阈值调用test，随后延时2300ms触发后续函数 |
| 滑动 | enable/sliding标志门控，global减extra/2，范围clamp | 输入时机/轨迹由代码控制，不能靠贴图改瞄准范围；标志与移动停止关联需后续运行证明 |
| Freestyle分数 | 类型表[50,20,10]（红/白/黑顺序），目标变量初值160；行3210–3303动态飞字回调更新分数及SDK；达到目标进入胜负判定 | 不将计分动画合到背景或以静态数字替代；阈值与当前回合标志共同分支，不简化为任何先到160都必胜 |
| 常规胜负 | 行3349–3435计数递增，任一计数=9后按当前方与queen数组是否清空分支；有退回/犯规/换手逻辑 | 不套通用Carrom竞赛规则解释所有变体；完整queen cover、罚分及停止条件未动态核验 |
| 结算 | `_0x47e567`行2781起分出win/lose，调用levelComplete/gameOver；test入口直接win后return | test入口不能证明自然成功；奖励/外部广告消息不等于离线奖励兑现 |

可接受误差：本轮可定义的**规格守恒门槛**为实际画布宽高、帧数/帧尺寸、原锚点/scale、棋盘几何常量与输入阈值零变更；袋口视觉中心应以原定位为基准，不批准额外移位。由于未目视和未测轨迹，本轮不声称已达到0px对齐或给出已验证的物理容差。后续授权后建议固定输入与1/60步对比入袋/回合/得分事件一致，再按原版基线制定位置数值误差；未经基线与用户取舍，不使用任意1px/1%充当验收通过。慢帧补步、重开、queen处理、释放阈值两侧、拖出释放和失焦恢复均需真实验证。

## 8. 离线、包体、加载、内存和目标设备

| 维度 | 本包真实证据 | 本轮结论/边界 |
|---|---|---|
| 外部网络 | index.html引用 `https://www.hippoobox.com/static/sdk/adsdk_1.8.0.0.js`、h5sdk广告/统计、next/reward消息 | **原包不能据清单宣称完整离线**；断网/SDK失败运行未测；纯美术不能解决SDK依赖 |
| 容器与存档 | 默认iframe高92%+广告区；bannerTest=yes改100%；GameSnacks跨frame依赖target origin；storage内存对象/可选channel；localStorage getter抛错；game.html有SW注销 | 广告高度影响视口与输入，离线刷新持久化未知；执行入口可能产生网络/SW副作用，故本轮不执行 |
| 包体 | 原包329项展开5,074,490字节 | 历史清单小于10MB，不是新dist验收；未制作/发布ZIP；研究副本/evidence不得进未来dist |
| 加载路径 | bitmaps297条声明→295有效键；两同名键后写覆盖；有效表缺路径0 | 早期缺路径2条不是实际加载失败；不代表HTML/CSS、字体页、音频、间接引用或SDK全加载通过 |
| 图片格式 | 15样本内容为WebP但后缀.png | 新资源不能机械按扩展名压缩/改MIME；保留引用契约；旧解码器兼容、alpha特征未测 |
| 内存 | 多套场景纹理；855×1391按RGBA8基础层理论约4,757,220字节，约4.54MiB/张 | 这是尺寸估算，不是实测峰值；GPU纹理、mipmap、同时驻留和音频另计；压缩包小不代表低内存 |
| 帧性能 | 固定步与while补步、Tween/独立效果 | 首帧、加载时长、帧率、卡顿、热/后台恢复均未知；不改补步代码来做美术任务 |
| 设备 | 未指定/接入目标设备，未运行Chromium或真机 | 桌面/手机触控与性能无证据，不引用技能案例设备结果代替 |

路径重复键说明：Carrom_coins_light早期assets/Carrom_coins_light.png被后续assets/matchmaking/Carrom_coins_light.png覆盖；carrom_spinning_wheel_base_brights早期matchmaking目录被wheel目录覆盖。脚本按对象最后写入语义修正有效加载表，不能报告2个现实404。

## 9. 独立待制作/补核清单与验收门槛

这不是已产美术清单。以resource-inventory逐路径为底账，以下交付批次在另行授权后执行：

| 优先级/批次 | 独立交付物 | 制作前必须补齐 | 不允许的扩大 |
|---|---|---|---|
| P0-A 几何/功能身份 | tables/0–4的board/corners/袋口与striker条，黑白红/striker、aim/滑条、暂停入口 | 所有原尺寸、alpha/主体中心、锚点、物理图示定位与配置实例；原版固定输入基线 | 不换引擎、不改规则/布局/命中区，不把棋盘合到bg |
| P0-B 启动/文字/输入 | preloader条、TTF/FNT/页图依赖、动态值底板、退出/恢复关键控件 | FNT正文/页表/字距、英文字符覆盖、加载路径、开关状态/输入禁用与恢复 | 不造假字体页；不以静态数字替代值，不改SDK/存档 |
| P1-A 主页面 | 大厅三模式与商城/设置入口，选桌五卡/箭头/select状态；匹配cover/头像/奖励池 | 当前未测同族尺寸、各up/down/off/disabled占位；实际cover遮挡关系 | 不按hover名字误做交互；不“修正”636/637差异 |
| P1-B 商店/教程/弹窗 | 商品母版及分件、选中/变暗、教学图、木底、手势、各弹窗底与按钮 | 全部页面截图/文字是否烘焙、商品对局复用实例、遮罩层 | 不合入价格/倒计时/教程箭头，不越权加光层 |
| P2 装饰与奖励 | winner光、转盘光/阴影/指针、confetti与5类帧动画、其余静态图文/音频 | 单件原尺寸、alpha、合成、转轴/帧序、是否需替换与来源许可 | 不把decor变成点击主体，不未经许可更换音频或宣称授权 |

JSON的priority为初筛，表中P0文字/输入依赖优先于命名分类。母版复用是风格一致性建议，仍导出原路径各状态；没有新图片/音频/字体产物，不创建伪art-manifest。

本轮检查项：
- 已满足：两包范围与缺证据说明；321项路径轻索引与逐文件候选证据；主要页面B/C级映射；15项真实头尺寸/哈希；主要几何、输入、计分保持边界；外扩光/坐标/离线/体积/性能风险；只做隔离研究。
- 部分满足：逐文件独立哈希记录仅15/321；全尺寸、所有状态实例与教学/转盘文字细分未完成。不能把清单长度作为全量核查通过。
- 未满足且不在本轮实施：竞品视觉观察、目视/alpha边界、完整字体页核对、当前主工程一致性、全页面运行与设备性能验收。
- 后续生产入口门槛：竞品截图或另行风格授权；原件来源许可；补齐待换资源尺寸/alpha/状态及306项哈希；当前版基线与范围；涉及光层/坐标非美术变更时必须真实提问授权。仅有本报告不得自动启动制作。

## 10. 产物、真实验证与限制

产物：
- `/workflow/prototype.md`：本独立静态核查报告。
- `/workflow/resource-inventory.json`：321项逐文件研究/待制作索引，unknown显式保留。
- `/workflow/archive-assets.txt`：321项原包assets相对路径。
- `/evidence/static-audit.json`：源码/解码哈希、映射锚点、15样本成员/字节/哈希/格式/尺寸、重复键与有效缺路径。
- `/evidence/source-decoded.txt`：保留行号的研究衍生文本。
- `/evidence/archive-metadata-coverage.json`：独立哈希覆盖缺口。
- `/evidence/validation-static.md`：本次恢复后真实执行结果与失败记录。
- `/reference-inputs/original-game.js`、`/reference-assets/`15原件：隔离引用，不是新作、不应发布。
- `/scripts/audit-static.mjs`、`/scripts/record-archive-metadata.mjs`：原创静态核查脚本，不执行参考游戏。

恢复后最后一次脚本修改之后实际执行：`node scripts/audit-static.mjs` exit0，321项/297声明/295有效键/15样本/有效缺路径0；`node scripts/record-archive-metadata.mjs` exit0，实测哈希15、未回填306。两命令source_before=source_after均为 `f6dfa4f51865b52c662c5f51d7c23b15a7f79e05a295643dac785c035885be67`。这是本研究工作区的工具指纹，不是主工程基线或原游戏性能证明。报告/evidence可在验证后补写，无游戏dist被修改或重建。

失败记录：曾尝试由原创脚本读取会话绝对路径以迁入已读ZIP元数据，Node返回ENOENT；文件工具可读会话并不代表Node可访问。已改为覆盖率核对，不伪造全量哈希恢复成功。FNT正文读取与提取均被参考工具拒绝，未取得字体文件，不重复相同失败操作。图像多模态读取没有返回可见画面，仅文件头/哈希核查成功。

本轮为原型隔离分析，无游戏package/build/dist接口，**未执行npm run build、npm test、npm run check、浏览器/真机/网络/性能验收**，不将静态脚本称为游戏测试。未生成美术、未实施换皮、未了解当前开发版本。源码研究副本哈希已核对，主工程未接入，因此不能声称主工程前后指纹一致。竞品视觉与全量资源实测须待补证，本次报告保留明确未知与范围边界。
