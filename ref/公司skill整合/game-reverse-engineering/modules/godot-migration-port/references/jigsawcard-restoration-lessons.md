# JigsawCard 原生还原落地经验（CASE_ONLY_JIGSAWCARD）

> **何时读我**：哥哥在做 JigsawCard（乐信拼图）相关还原时，要确认某个模块"到底做没做、做到哪、有没有证据"，或需要一份已证结果与未证边界的清单来防止把待证项写成已完成时。
> **读完能做到**：逐条查到资源与 Spine、切图页面包体、玩法提示反馈、通关数据跨页面、局外系统、Android 返回键与设备证据各自的已验证结论和证据路径，并明确避开末尾边界表里那些"不得写成已完成"的项（如猫脸身份、未覆盖的 Spine 触发点、完整音效时序）。
> **范围**：`CASE_ONLY_JIGSAWCARD`

更新时间：2026-10-12。本文只收录本项目已经取得工程、脚本、桌面渲染或 Android 实机证据的结果；其他项目只能复用验证方法，不能照搬包名、路径、关卡号、数量、时间、哈希或数值。没有写入“已完成”的项目仍在末尾的边界表中明确列出。

## 已完成且有证据的结果

### 资源与 Spine

- 原 Unity TextAsset 已保留原始字节，并对已确认的 surrogateescape/surrogatepass 损坏链做可逆恢复；恢复结果通过真实格式解析，未用“全部 Latin-1”替代。
- 原 Spine 4.1.24/4.1.08 资源已完整转换到目标 runtime 4.2.11，45 个文件别名归并为 42 份唯一数据；85 个动画条目完成加载与时间推进检查，Godot 4.6.2 桌面抽查可见真实画面。`source/runtime/atlas/animation` 的哈希和转换记录在项目 `data/spine_manifest.json` 与 `docs/atlas_dimension_spine_verify.log`。
- Spine atlas 逐页审计了声明页尺寸、PNG 实际尺寸、旋转 region、trim/original bounds 与 pathID。只有有证据的整页尺寸问题才改写，按 X/Y 两轴分别处理；Hint trailing 的越界问题按真实采样坐标修复。未获证据的 bow、Sold_out 等页面保持待查，不能批量拉伸。
- Spine 宿主和固定 UI 已落成可编辑 `.tscn/.tres`，包含 SkeletonData、Atlas、材质、稳定节点名和 AnimationPlayer/播放配置；运行时复用固定节点，不以运行时临时 `new Node` 代替 prefab。桌面和 Android 都验证过已接入宿主的加载/播放路径，但这不等于所有原版业务触发点已完成。

### 切图、页面与包体

- 530 张用户替换关卡 JPG 源文件哈希未改变。导入缓存从约 792.04 MiB 降至约 207.40 MiB；样本 PSNR 约 42.7–44.5 dB，明确记录为有损导入，不能称无损。
- 737 张 `tex_` 文件经逐项哈希确认是重复资源后删除，另外 25 张同前缀但不等价的纹理保留；没有按通配符删除。
- Home 拼图、设置、头像、火苗栏和结算页面已使用原切图/AtlasTexture 与可编辑节点重建。火苗栏按逻辑画布、实际裁切、透明留白、offset、父级变换分开恢复，避免把紧裁图直接拉伸。
- 结算页已由原先的小卡/三星底座改成当前大图、Last1、Last2 历史卡槽、三项统计和下一步按钮的可编辑场景结构；实际序列中的木柄 WIN 已接入 `effect_firstwin_01` 真实 Spine 资源。

### 拼图玩法、提示与反馈

- 原版实测证明拼图使用相对四邻接连接组。拖动任意组成员会移动整个组；组汇合、重叠回填、越界取消、单块撞入后拆组均已有真实回放和回归覆盖。
- 本案例中“两块组/两个独立两块组/四块组/拆组”产生的 5%/11% 进度变化支持“最大连通组”模型；这个数值和模型只属于本案例证据，不能推广到其他拼图。
- 成功拼接已接入原切图外框、粒子和边缘光；相邻整数边界修复了 1 像素黑缝和背景漏出。组内接缝按连接状态隐藏，普通边界保持独立。
- 提示道具已改为真实源块→目标块引导、手部动画、拖动成功条件和库存扣除事务；没有用自动换位冒充提示。暂停、取消、越界、零库存和末步顺序已纳入回归。
- 延迟反馈、光效和结算回调绑定 board generation/epoch，并在换关、暂停、离场和下一次拖动时淘汰旧 Timer/Tween；修复了末步结算被 pause 丢弃和旧光效残留。

### 通关、数据和跨页面

- 原版录屏确认的顺序已落入结算结构：木柄 WIN → 文案停留 → 横向换卡 → 当前大图/历史叠卡 → 步数、用时、累计连击 → 下一步。当前 APK 两轮实机专项已走通木柄 WIN、大图叠卡、统计栏、火苗周历和下一关衔接。
- 结算连击已经改读实际成功连接累计值；原录像 29 次操作中 28 次产生新连接，与结算连击 28 对上。不能用“三秒最高连击”或截图固定值替代。
- 奖励提交保持幂等；完成记录、用时、步数和累计连击落入存档，跨大厅、后台和杀进程恢复测试通过。最新用户存档在测试前后逐字节核对并恢复。
- “下一个”后的连续登录火苗页已补入流程；隐私、条款、评分入口已按原版实际 URI 接入。入口跳转和当前版本的缓存/网络状态均单独记录。
- 跨会话续局完成 24 项棋盘、统计、返回、后台和进程恢复回归；显式隔离 save path，不能只依赖环境变量。

### 局外系统：每日挑战月历与章节图册（2026-09-12 已落地实证）

- **每日挑战月历（`DailyPageUI`）**：实现完整 42 单元格（7×6）月历矩阵，动态计算公历月份首日星期与天数（支持闰年 2 月 29 天），高亮今日光圈，已完成日期打上原版勾选印章（`daily_calender_finished.png`），点击日期联动底部开始挑战按钮文案；集成 1~12 月奖杯陈列室（`TrophyContainer`，`common_pic_calendar_trophy_09.png`），支持已集齐/挑战中/未解锁三种视觉状态与双向无缝切换。
- **章节图册（`CollectionPageUI`）**：还原原版章节图册卡片，包含章节标题（沿海/夜景/沙滩等）、动态收集进度条（`collection_progressbar_bg.png`、`collection_progress.png`，如 "8/25"、"0/25"）、左右翻页按钮边界置灰与翻页音效（`book_switch.wav`）、章节预览大图与 25 块拼图蒙版槽位（已解锁透光无缝显现，未解锁半透明暗化覆盖）。
- **持久化数据支持**：`SaveManager` 新增 `daily_completed: Dictionary` 及 `is_daily_completed` / `set_daily_completed` 接口，无缝落盘至 `savegame.json`，与主线关卡解耦。
- **GDScript 动态样式修改 API 避坑**：严禁用字典索引语法访问 Label 样式（如 `label.theme_override_font_sizes["font_size"] = 18` 报错），必须调用官方覆盖 API：`label.add_theme_font_size_override("font_size", val)` 与 `label.add_theme_color_override("font_color", color)`。

### Android 物理返回键与全局弹窗栈（2026-09-12 已落地实证）

- **根因**：Godot 默认 `auto_accept_quit = true`，在移动端按下物理/手势返回键（`KEY_BACK`）会导致系统直接将应用切退后台或杀死。
- **解决方案**：在 `Main.gd` 的 `_ready()` 中显式执行 `get_tree().set_auto_accept_quit(false)` 接管退回控制权；并在 `_unhandled_input` 中捕获 `event.keycode == KEY_BACK`，按照 `DailyPageUI` -> `CollectionPageUI` -> `SettingsDialog` -> `AvatarDialog` -> `StreakDialog` 的优先级栈逐层关闭弹窗，并调用 `get_viewport().set_input_as_handled()` 消费事件，彻底杜绝弹窗打开时按返回键误退桌面。

### 真机/模拟器证据与任务卫生（更新至 2026-09-13）

- **MuMu 12 / 模拟器双模式与桌面会话隔离**：MuMu 12 在通过命令行或后台服务拉起时，默认采用无头虚拟机核心（`MuMuVMMHeadless.exe`），其 ADB 端口（16384/5554）正常连通且能够通过 ADB 捕获真实的 SurfaceFlinger 渲染帧，但其 Windows 桌面主窗口处于隐藏模式（`Visible=0, Rect=(0,0,0,0)`）；同时，自动化代理进程常运行于沙箱桌面工作站（如 `exebox-*`），直接调用 GUI API 无法将窗口传递到物理屏幕的 `default` 桌面。必须利用 Win32 API `OpenDesktopW('default')` 与 `SetThreadDesktop` 将线程桌面挂接回物理交互桌面，随后通过 `ShowWindow(hwnd, SW_RESTORE)` 与 `SetForegroundWindow(hwnd)` 成功将 MuMu 模拟器主界面调回物理桌面（坐标约 `(1400, 35)`）前台，实现了“底层 ADB 自动化持续运行 + 桌面肉眼实时可视”的统一。
- **权威存档基线双向不可变门禁**：当前现场基线已更新为下一关 14、金币 420、提示 0，Android 原始字节 SHA-256 `9827c33bdcdffb05accc0bad56e94b641bef6a9569f81f92ce64bb1918519b57`；旧第 9/13 关哈希只保留为历史证据，不得覆盖当前档。任何测试启动前先捕获并校验现场原始 bytes；测试结束后无论是否有进度变更，都在 `finally` 恢复这份 bytes 并再次核对 SHA-256。PowerShell 文本重定向会改变换行，不能用它生成“逐字节”备份。
- **自动化回归套件持续扩展**：早期 16 项套件已扩展为当前 13 个专项入口，覆盖 HomeSlices、HomeMotion、Daily/Collection/Rank、火苗、Daily 规则、商业服务、通关前置 Gate、结算后期 Gate、烟花、完整通关、移动音效、局内反馈和 Android 返回键；各入口内部检查数独立增长。报告应写实际入口和 failures，不继续把历史“16 项”当固定上限。
- Android 实机证据必须记录 APK SHA-256、包名/Activity、前台应用、存档哈希、网络状态和截图/录屏目录。应用被切到旧包、ADB 重启或前台 guard 失败的录像标为无效，不得用于视觉结论。
- 本轮已验证的 APK 证据包括：`exports/android/jigsawcard-finish-dev.apk`（402298374 bytes，SHA-256 `2fdfc4f1ed9030de96355504b2b80f4aff810a374bf180b253eb6d50ebb03a8f`）与全流程包 `jigsawcard-fullflow-dev.apk`（412529736 bytes，SHA-256 `36803e17a89ff2181db6f74706ab51ec375a86dda80500ecfc31c9c90b51c179`）。交付报告必须以最终安装包现场哈希为准，不复用旧包截图。
- 达到 12 张图像或约 60 分钟阈值时，先更新 `HANDOFF.md`，停止旧任务的工程/设备操作，再创建干净续作；交接必须包含当前 APK、哈希、存档、设备状态、已证结果、未证边界和回滚点。

## 经验如何泛化

1. 先用“资源身份→引用链→运行时 owner→稳定边界→真机画面”的顺序证明，不能从文件名、节点名或一张截图直接推断业务规则。
2. UI/Spine 固化必须保留可编辑节点和动态业务脚本；固定的是资源、宿主和时间线，不是整页截图或玩家状态。
3. 玩法模型要用同一初始布局逐步操作验证；旧的绝对归位 QA 在连接组玩法中会产生假通过，必须重写成真实拖放/释放/回填断言。
4. 所有延迟效果都要有 owner、generation/epoch 和可取消边界；“无报错”不足以证明生命周期正确。
5. 原版录像只证明录像所覆盖的分支；通关中的 Win、评价字、Emoji、猫、横幅、音效和其他页面必须分别定位资源与触发条件。

## 当前仍未完成或仅待证（不得写成已完成）

- 商店、帮助和未进入当前快照的其他外围页面仍需按覆盖矩阵确认；Daily/Collection/Rank 已有固定页面与首次引导，但不能据此宣布整个后期系统完成。
- 进度阶段猫脸身份、未覆盖的 Spine 业务触发点、未出现的结算评价字/Emoji 分支和完整音效时序仍需逐项取证。
- 原版开局发牌/翻牌、所有异形碰撞、数据库 slot 方向及全部关卡映射仍有待证项。
- 火苗经济、完整计分规则、原版网络缓存与版本差异不能由当前一轮设备状态推出。
- 本文件不代表项目 100% 还原；最终结论必须以逐项矩阵、最终 APK 和同尺寸原版/重制实机证据为准。

## 2026-09-13 增量：通关协调、主页动效与外围系统

- 实机确认末次正确拼接可以同时出现边缘光、`Nice x2` 评价字和 Emoji；固定协调器等待该 HUD 反馈结束后才进入 2.83 秒每日首胜 WIN，再进入历史叠卡结算。由此修复“Spine 已接入但切页过早导致看似消失”。
- 木柄 WIN 的资格仍是每日首次完局激励；不能改成每关必播。当前录像分支不支持把三猫或 SettlementBanner 强制叠加到普通结算。
- 主页恢复了原 prefab 的页面、Logo、章节和按钮状态族及已证时长。缺少 Timeline 曲线的 Logo 呼吸、按钮缩放和章节淡变明确标为保守拟合；名称相近的 `effect_logo/effect_pintu` 未误挂主页。
- 新建 Godot 商业服务插件层：9 类外围服务 facade、Null/Local adapter、同意/服务双门禁、广告频控、A010/A011 稳定边界、奖励 proof 幂等账本，以及 35 项事件契约。默认完全离线；没有正式供应商回执时不称 SDK 接入完成。
- Android 专项用两组错位制造连续正确拼接，录像覆盖评价/Emoji→WIN→结算；历史尾部为三个不同关卡图，runtime errors 为空。测试开始捕获设备原始 LF 字节并在 finally 恢复，避免 PowerShell 重定向换行转换造成假哈希差异。

## 2026-09-13 增量：后期系统、门槛探针与烟花返工

- 原版 Rank 不能靠写 `RankUnlocked/rank_first_unlock` 强开；在完整备份后补齐 70 个 `IsDaily=false` 普通关完成记录，主页才从 `Lv.70` 变为倒计时入口，并出现“快乐花朵→26/50 到 50/50 匹配→稳定榜单”。恢复后 PlayerPrefs、save、StageDB 哈希与备份一致。该 70 只属于受检 1.5.19 构建。
- Daily 的 `daily_unlock=45` 是每天开放普通内容的数量策略，不是 Daily 页面资格。受控补齐 8 至 70 个普通关完成记录均没有让原版写 `Daily_Unlock`；直接诊断写 `Daily_Unlock=1` 能打开页面。Godot 默认采用当前快照的锁定状态，并保留独立外部资格，不再写死 10/45/70。
- `current_original_snapshot_defaults.json` 不是证据附件：`HomeFeatureState` 直接读取其中的 Daily 默认态和 Rank 70 门槛，入口、返回主页解锁演出和 QA 共用同一来源，避免文档与场景脚本再次分叉。
- 火苗持久键和 helper 证明它是“每日首次完局连续天数”。第二天只启动仍显示 1 属于正确行为；第二天首次完成后才变 2。测试覆盖本地民用日期、断档、回拨、时区和跨进程。
- Rank/Daily/Collection 已拆为资格、首次引导、主页入口、局内增量、结算、返回主页和周期结束状态。结算分支只接受显式 payload；测试曾发现 gate 场景存在却未从 SettlementDialog 调用，说明固定宿主与单元测试不能替代调用链集成测试。
- 原版烟花由多组边框星光、紫金线状主烟花、彩带和记录框粒子构成。第一次 Godot 近似在中心堆出爱心/密集星点、统计框过早，虽然 21 项粒子测试通过，按同 PTS 联系表仍判 FAIL。图集 ribbon 必须按 3×3/2×2 单格采样；后续仍以起爆/峰值/衰减视觉为关闭条件。

## 2026-09-13 增量：最终快照接线、后期分支与设备脚本纠偏

- 所有未知配置已统一落入 `current_original_snapshot_defaults.json`，范围包含资格、配额、AB 分组、样式、奖励、payload、开关和位置。`CommercialServices.remote_values` 载入同一快照，后续 provider 覆盖；`HomeFeatureState`、入口、解锁演出和结算消费者不再各自保存默认值。
- 当前快照 `rank_result=null`、`collect_elements=[]`、`daily_result=null`。结算固定 Gate 已具备收集飞入、榜单移动、x1–x5 连胜、晋升/降级/不变和 Daily 结果分支，但只在显式 completion payload 出现时播放。固定坐标和原切图属于 `static_confirmed`；缺少 Lv70+ 连续原版 payload 时，0.72/0.75/1.75/2.65/3.60 秒阶段仍为 `fitted`。
- Android 页面 fixture 第一次用固定 `sleep` 截到启动帧，第二次又把排行榜底部绿色按钮误判成首页 ready；排行榜首次引导遮罩尚未完成时点返回，导致后续 Daily 点击落在错误页面。修复后使用首页按钮加头像两个视觉锚点、空白区唤醒输入，并按“确认引导→等待 GuideMatch 完成→返回→等待首页 ready→打开 Daily”的状态机执行。
- 生产配置补充发生在候选 APK 导出后，旧包因此作废。最终包重新导出、v2/v3 验签、ADB 重连、安装和同 fixture 复跑；包内确认快照 JSON 与三个结算场景存在，QA/docs/tools 未进入包。最终 APK 为 424456264 bytes，SHA-256 `8d8dc3400ee30478bbec5f2d443861420d25fe5133bff74df375127e7e0f4f15`；测试前后存档和 `home_feature_state.cfg` 均逐字节恢复。
- 烟花较初版已纠正错误爱心、整图集粒子、十倍重力、统计栏时机和屏幕边缘备用彩带，但衰减亮度、右上簇和边缘拖尾仍与原版不同。测试全绿、参数可追溯和固定宿主可编辑都不能把该项升级为 `verified`。


## 2026-09-14 增量：页面语义、换皮主题与 prefab 审计

- metadata 中出现 `HasShown*`、`Guide*` 等状态字段，只能证明存在某类状态，不能证明目标页面拥有一层特定引导。Daily 的直接运行截图显示解锁后进入月历，因此删除了此前依据字段名臆造的说明遮罩；页面结构必须以可见运行证据或完整调用链为准。
- 首次引导的底层页面也是演出的一部分。Rank 原版先在 Home 上覆盖活动说明，再在 Home 上播放雷达匹配，完成后才揭示榜单；若打开 Rank 页再盖遮罩，即使前景元素正确，页面 owner 和视觉层级仍错误。
- 换皮验收除了尺寸、Alpha、atlas region 和引用链，还要增加“元素身份表”：头像槽位的动物/人物类型、货币花朵、黑桃段位徽章、Daily 奖杯等主题语义不得被统一画风重绘成另一种物件。尺寸与 Alpha 全通过无法发现这类错误。
- 常驻背景与章节奖励图必须分职责。章节竖图可用于章节完成展示，不能因风格一致就替换 Home 和启动页的简洁底色；背景密度、主体占比和文字安全区应单独验收。
- Godot prefab 审计要同时检查 `.tscn` 固定节点、`.tres` AnimationLibrary 和脚本中的 `Control.new()/TextureRect.new()/Button.new()`。固定日期格、头像格、榜单行、按钮命中区和 VFX 宿主应烘焙；按关卡数据实例化拼图片、路由 PackedScene 和播放器池属于合理运行时对象，不能为了“零 new”错误固化。


## 2026-09-14 用户QA反证：旧图册/排行榜/结算不能混用

- 原版实机排行“去收集”进入普通关卡；旧文档说进入CollectionPage错误，已纠正。KEY OuterLoopMode_LastKnown实际值image；metadata有CollectionToImageUpgradeFlow。
- Collection原资源四主题各50个，共200Sprite；旧实现把PartCollectionGame六猫循环到章节25格，是业务资源错绑。原Grid四列、24间隔、10边距、900x1500滚动；BookBg/Spine相同(-230,0)坐标，旧换皮却把出屏左页改成对称双页导致折线错位。
- 原RankEntity当前事件已选49bots，保存StartTime/EndTime、积分时间曲线、EnterHigherPos15、EnterLowerPos41；包内3485候选不应重新乱抽。现LocalRankService用原快照，还原完整50人排行并接正常通关；权重随机、平分规则和精确提交时机标fitted，周期奖励/下一期未实现。
- 新RankSettlementOverlay不是主页RankActivity复用：Win/Emoji/评价之后追加飞花、计分、重排、评价和继续。独立fixture截图仅用于视觉对齐，另测GameState→LocalRankService→Settlement，不能拿手工payload当自然链路。
- 桌面阶段：活动32项、本地排行15项、独立排行结算20项、图册11项通过；Android最终包结果以项目HANDOFF和QA_CORRECTIONS_20260914为准，不能在APK导出前标记全平台verified。

## 2026-09-15 ~ 10-11 增量索引（逐轮细节以项目 `docs/DEV_HISTORY.md` 与根 `HANDOFF.md` 为准）

本文件此后不再逐轮展开。下列结论已获工程或实机证据；可泛化的规则已抽入 `native-restoration-gates.md` 第 14 节与 `godot-engine-pitfalls.md`，此处只留案例锚点：

- **09-15~09-18（DSH ab007353 主开发线程）**：榜单周期边界、结算印章/皇冠、原版动画时距契约（结算 3.417 s、榜单变化 2.167/1.167 s）、按段位索引音效；09-17 单日 143 次提交完成可浏览 UI 参考页（45 场景）与广告点位还原。
- **09-21~09-23 视觉可信度**：12 张尺寸不符换皮贴图回退原版、8 个伤可用性图标回退、2 px 接缝精确测量、整数图集切片、430 px 位移自愈 + 拖动/接缝看门狗、220 步零看门狗触发验收。
- **09-28~10-02 工程框架**：显式输入状态机与具名禁用输入栈、SaveManager 迁移链与存档原子事务、DebugApiServer 绑 loopback + 独立 INTERNET 权限、DDA 纯规则、事件常量代码生成、实施账本 10/10 落地。
- **10-07~10-08 性能 P0~P6**：沙盒隔离与基线、日志/生命周期、ResourcePreparationService（准备与激活分离）、LRU 24 MiB 预算 + 切后台释放、无损缩包（仅 `_art_rebuild/` 挡 632.28 MiB）、ContentCatalog + 章节 PCK（小包版剥离 90.8% 关卡资产）、94 项门禁；同窗修复生成器覆盖 prefab 排版根因。
- **10-09~10-10 加载与灰屏**：OptimizedTranslation（初始化 p50 605.61 → 41.14 ms）、字体 fallback 行框修复（1,890 项通过）、`jigsawcard-optimized-20261009.apk`（297.1 MiB）被用户拒收 → 灰屏根因修复（隔离副本/类索引门禁，见 gates 第 14 节）+ 拖动跟随/合并延迟/亮色接缝修复 → `jigsawcard-fixed-20261010.apk`（300.9 MiB，SHA-256 `b6259506…d302`）用户确认。
- **10-11 收尾**：34 头像槽位内切圆化（21 烘焙/12 逐字节不变）、UI 参考页直连真实原件、应用图标替换；工程清理 21.4 → 10.74 GB（`CLEANUP_20261011.md`）。
- **遗留待拍板**：`assets/textures/` 1684 个 tracked-but-missing 纹理处置；`export_presets.cfg` 的 icon/launcher/adaptive 槽位命中 0（APK 仍用默认图标）；低端 armv7 实机未验收；榜单页完整动画/音效仍因缺资源身份证据挂起。

## 2026-10-12 增量锚点（CASE_ONLY_JIGSAWCARD）

- **广告离线反馈**：实际调用只有 hint_refill、hard_double_reward、home_banner、level_complete。原语言包确认 unable_load_ad/ad_is_not_ready/confirm；metadata 的 HintToastHelper/ShowAdNotReadyToast 与 HintPlugin 证实接口，ToastUI 与 NoNetDialogUI 结构分别核对。固定“双按钮重试”未获证明，本轮按用户要求重建单确认提示。每日、Pinata、免广告等无当前 caller，未臆造领奖或放开功能。
- **奖励与暂停回归**：预登记事务处理同步失败；只匹配自身请求，同 run 一次领取，新 run 复位；失败、无 proof、加载超时、取消和迟到结果不发奖。修结算自身 modal 永久抑制、level=-1、暂停退出误插屏和横幅离场；真实 Game 覆盖最后一块与两种后台通知顺序。6 组隔离回归共 284 项通过，包含真实 OpenGL；现有粒子拖尾兼容警告不属于新增错误。权威证据：项目 docs/ad-fallback-audit-20261012.md 与 docs/evidence/ad-fallback-20261012/verification.json。
- **开局重复音效**：批量声音与逐牌声音叠播，后者实际是约 2.526 秒序列；修复只保留批次的一次约 0.109 秒短音，独立翻牌默认仍播。发牌延迟直接捕获销毁 Node 曾产生 36 次错误，改 generation 与明确类型 WeakRef。无窗口/真实 OpenGL 各 52 项、按钮 8 项、移动 14 项、玩法表现 19 项通过；项目 docs/deal-audio-fix-20261012.md 保留失败到成功证据。
- **声明边界**：本轮未导出/安装 APK、未操作 MuMu，音效硬件听感和厂商 SDK 回执未验证。隔离注入使用测试 adapter proof，不等于供应商真实性验证。此案 provider 当前按 earned 在 closed 之前规范化；其他 SDK 必须重新确认顺序。奖励跨进程交付与存档失败补偿仍待真实接入时落实。

通用规则集中维护在 [广告生命周期](../../sdk-replacement/references/ad-fallback-and-reward-lifecycle.md) 与 [Godot 引擎行为](godot-engine-pitfalls.md)，不得复制此案数字为其他工程的前置条件。
