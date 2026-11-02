# game-reverse-engineering 版本说明（完整版本史）

8.0.0 起，根 `SKILL.md` 只保留路由入口，行为级变更记录统一落在本文件。版本规则见根 `SKILL.md`「落地迭代协议」：行为级内容更新 → minor bump；新模块/路由重构/结构级变更 → major bump。

- **8.5.1 (2026-10-12)**：以 8.5.0 portable 为基础融合旧版本 16 个独有有效文件；恢复 Cocos MCP 执行卡与路由、QQ 宿主识别、Transsion 素材/回收、BlockMaster V140–V142 竞态、Unity AB/全文 HTML，补齐模块/scope-map。修复两份文档尖括号损坏；合并 Seed 两端参数、同步/异步入口并修复非法 Java 和叶子重复路径，加入桌面编译/运行回归。PowerShell 路径改读真实环境变量，修复 env.example 引用/路径契约。发布使用本机 11 个 Junction 的维护源，缓存不入包；不承诺游戏/设备运行验收。

- **8.5.0 (2026-10-12)**：面向低能力执行者的可执行化重构（结构级 major）。新增 **执行协议** `references/execution-protocol.md`：五步循环（定位→读模块执行卡→做第一步→按需读参考→收口）、六条铁律、卡住时的四步排查顺序、报告状态四词表（PASS/FAIL/BLOCKED/NEEDS_CONTEXT）；根 `SKILL.md` 新增「执行协议」节并在文首指向它。根「任务意图快速分发」表新增第四列**做完标准**，逐行给出该步的通过判据（下限，非整件事完成）。15 个模块 `SKILL.md` 顶部各插入统一**执行卡**（我管什么 / 第一步做什么 / 做完怎么算完成 / 红线 / 卡住时按顺序读），使执行者读完执行卡即可开工，无需预读模块正文；执行卡内容全部从各模块既有正文提炼，未新增方法论。全部 73 个模块参考文件顶部另插入统一**路由头**（何时读我 / 读完能做到 / 范围），使执行者在模块「参考文件索引」之外也能单文件自解释，读到文件即知触发条件与产出边界。全库**零删减**：既有方法论、案例证据与脚本一条未动，参考文件仅做顶部插入，正文一字未改。验证器勘误：`scripts/validate_skill.ps1` 中 Godot 模块版本断言原为硬编码 `version: 1.9.0`（在该模块合法推进到 1.10.0 后必然失败），改为语义化版本正则 `^version:\s*\d+\.\d+\.\d+`，保留"模块必须声明版本号"的原意，不再把具体版本号写死。8端 Junction 共用维护源，无新增联网/SDK 权限。
- **8.4.0 (2026-10-12)**：从 JigsawCard 已验证修复提炼行为规则。sdk-replacement 1.2.0 新增未接广告专项参考与精确路由，区分原版语言/结构/行为证据，补齐同步返回身份、attempt与claim幂等、加载/播放终态、provider回调顺序、暂停归属和真实业务链QA；明确可选配置的inert success不适用于奖励广告/支付。godot-migration-port 1.10.0 接同一参考，补批量音效范围与WeakRef/代次规则，并纠正看门狗不能代替位移根因修复。案例只记录本项目数值、284项桌面回归及未验证边界；scope-map、两模块落地日志和版本接线同步。8端Junction共用维护源，无新增联网/SDK权限。
- **8.3.0 (2026-10-10)**：吸收 morluto/rea「证据纪律」机制并本域化（行为级 minor，未引入其 MCP server 化、provider 中立工具层与通用抽象，本总集保持游戏垂直域模块路由）。P0 新增 **未知清单模板** `references/unknowns-ledger-template.md`：UNKNOWNS 表（编号/未知项/还缺什么/当前证据/状态）、登记时机、闭合条件与通用示例；根 SKILL.md 新增「交付证据纪律」节，把「不宣称目标游戏动态恢复已验收」从措辞升级为交付必附机制；全局证据规则新增第 10 条、最小交付门禁补未知清单要求。P1 新增三条主链路 **义务清单模板**（均 `GENERAL_DEFAULT`）：`modules/godot-migration-port/references/obligation-ledger-template.md`（O-G1～G9）、`modules/skinning-pipeline/references/obligation-ledger-template.md`（O-S1～S10）、`modules/sdk-replacement/references/obligation-ledger-template.md`（O-K1～K10），把「导入成功、节点存在、截图相似都不能单独证明完成」等原则句拆为可逐条关闭的义务行；关闭条件统一为唯一 owner + 规定证据类型 + 验证器通过 + 证据落盘，豁免需用户同意；各模板附常见错误关闭反例。P2 `references/binary-version-diff.md` 新增 **证据等级** 节：显式证据/静态候选/仅推断三级与升级降级路径，映射表新增 `evidence_grade` 字段，静态差值只是候选差异、默认登记未知项。P2 新增 **采集负面清单** `modules/vision-device-testing/references/collection-boundaries.md`：凭据/Cookie/授权头/原始网络体/用户隐私/真实存档/未审阅截图一律不采集，抓包只留三层元数据；vision-device-testing、sdk-replacement（Phase 1）与全局规则接线。模块接线：godot-migration-port、skinning-pipeline、sdk-replacement、vision-device-testing 四个模块 SKILL.md 增加路由行（模块版本号不变，变更统一记入本总集版本）。scope-map 登记 8.3.0 扩展。版本勘误：8.2.0 条目仅写入本文件、根 metadata 未同步（仍为 8.1.0），本次将根版本直接推进到 8.3.0 修正该偏差。
- **8.2.0 (2026-10-10)**：3d-asset-extraction 新增 **Anvil R6S ver30（Y5S3 旧 depot）完整章节**（行为级）：entries 宽度逐代对照表（ver27/28=20B / **ver30=12B 明文** / ver34=20B 混淆）、322B 元数据布局、名字解密 FILE_KEY_STEP 且 offset 传 0、资源容器双层同构（chunk 内容又是一层 FileContainer）、MeshHeader/CompiledMeshObject 三锚点与 LOD0=前 numIslands 条口径、纯 python 解析器（r6s_mesh.py，无 pythonnet 依赖）；R6S v34 offset 混淆定性为**页号负计数**并附「无效穷举陷阱」清单（作废此前的固定 XOR key 结论）；面数口径结论：R6S 全场最高 44,048 面、干员密集 34–35k、**无 ≥10 万面件**（与二次元系同档）。根 SKILL.md 快速避坑新增两条通用规则（跨版本先按 ver 分支 / 下载器预分配空文件污染遍历 / 外部工具必须绝对路径）。CLI 实测交付：2 件 OBJ + 16 张 8 视角 1024 白底渲染。落地记录见 `modules/3d-asset-extraction/references/landing-log.md`。
- **8.1.0 (2026-10-10)**：3d-asset-extraction 模块重构 v2.0（结构级）。376 行单文件（章节乱序：双 §5、§8 插 §6 前）拆为 **12 张引擎参考卡**（neox-messiah/re/fromsoft/redengine4/ue4-pak/unity-mihoyo/anvil/creation/tiger/criware/mtframework/source2，各卡自包含：识别指纹→格式→工具链与坑→战果）+ **method-container-reversing.md**（未见格式四步法：头部侦察→锚点定界→物理约束验证→参照实现互证；无效穷举陷阱清单；pythonnet 跨语言桥接；作业铁律）+ **render-delivery-spec.md**（渲染参数/视角映射核验/交付四件套/提取质量自验证门禁/面数口径）+ landing-log。新增实测格式知识：FO4 DX10 ba2 变长记录流全破解（BAADF00D 分隔+'dds\0' lookahead 定界+理论 mip 链体积自验证）、DS3 TPF v3 直解判据（count>1 变体走 Yabber）、命运2 Tiger 全量实测口径（水密≠完整/碎片度判据/硬链接贴图去重）、R6S v34 逆向 90% 字节证据、AC3R mesh 引用式卡点、UE5 Nanite 方案储备。根路由表与触发词补引擎关键词（辐射4/黑魂3/FLVER/BA2/forge/EZST 等）。落地记录见 `modules/3d-asset-extraction/references/landing-log.md`。

- **8.0.0 (2026-10-04)**：路由重构（结构级 major）。根 SKILL.md 瘦身为纯路由入口（45KB→约19KB）：版本说明移至本文件，端到端总流程移至 `references/end-to-end-pipeline.md`，全局证据规则/格式与解密边界/JSB 边界/工具环境/脚本清单/交付门禁移至 `references/global-rules.md`，BlockMaster 案例规则移至 `references/blockmaster-case-rules.md`；路由表与 scope-map 补齐 `3d-asset-extraction`、`deliverable-book-template`；归档 8 个被取代的顶层旧 skill（game-build-engine-identification / cocos-reverse-engineering / cocos-creator-project-repair / assetripper-unity-extract / game-skinning-pipeline / blockudoku-cocos-qa / db2spine-spine38-qa / vision-device-testing）至 `skill-pool/archive/superseded-2026-10/`，消除 harness 激活竞争；统一路径基准（反引号路径=总集根相对，markdown 链接=所在文件相对）并修复全部错基准路径；收编 game-dev 散落参考 `builtin-assets-and-spriteframes.md` 进 cocos-creator-repair 模块；模块级 Changelog 移至各模块 `references/changelog.md`；openai.yaml 旧技能名改指总集；validate_skill.ps1 新增路径基准校验、scope-map↔modules 对账、顶层被取代 skill 复发检测；落地迭代协议新增 landing-log 轮转规则（超 20KB 归档）。

- **7.13.0 (2026-10-02)**：审查逆向AI.zip 后，按现有模块补齐原生/JNI 取证、Mono/IL2CPP 代码链、加壳运行时与 DEX 门禁、函数级版本差分、观测驱动的算法复现和自定义协议契约；新增只读 ELF/PE 地址映射工具与合成测试。纠正静态/运行时/文件地址混用、DummyDll 等于源码、analysis ELF 等于可执行、缺失脚本等于已有能力等误判；保留来源路径/哈希和文档级、工具级、项目级证据边界。

- **7.12.0 (2026-09-14)**：替换 2026-09-13 未经完整运行态证明的 AI 换皮章节。新增“结构先行的动画/UI 换皮”闭环：先确认实际运行资源链和风格锚，再从权威原资源直接重绘；Spine 必须改真实 atlas 页并保持 page/region/rotate/Alpha/骨架/动画名不变，静态截图只能作为 fallback；所有生成图只允许等比 contain/cover，禁止 X/Y 独立缩放；Alpha 相等只证明几何通道，不能证明语义轮廓、附件职责或运行画面正确；Godot 命令行截图必须先设置设计 Viewport，禁止把桌面横屏位图强拉为竖屏。验收升级为结构哈希、真实骨骼中间帧、多状态页面、设计分辨率截图与最终设备五层证据，并记录 JigsawCard 中错误庆祝附件和 QA 截图挤压的可迁移根因。

- **7.11.0 (2026-09-13)**：整体重组 Godot 重制模块为唯一 S0–S7 端到端流程，统一证据状态、阶段门禁和专项参考边界；新增全部未知配置快照/provider 优先级、后期系统显式 payload、复杂粒子同 PTS、最终 APK 新鲜度、ADB 重连、页面 ready 多锚点、首次引导状态机、存档 finally 原字节恢复和交接/Skill 回填门禁。修正旧入口“六阶段”与历史 S7/S8 混用。

- **7.10.1 (2026-09-13)**：明确“当前版本快照缺省”适用于全部未知配置字段，包括资格、配额、AB 分组、样式、数值、payload 与开关，不得缩窄为位置参数或自然解锁规则；运行时只保留一份快照缺省源，由显式本地状态或后续 provider payload 覆盖，并测试业务入口实际读取该源。

- **7.10.0 (2026-09-13)**：新增后期解锁系统与高密度特效的恢复门禁：受控数据探针必须备份/哈希/最小变更/finally 逐字节恢复；配置同名时先区分“功能资格”和“内容配额”；未知值使用当前受检版本快照并保留 null/证据等级；Rank/Daily/Collection 按解锁、首次引导、局内收集、结算、晋降级、赛季结束建立状态矩阵和显式 payload；粒子特效要求逐 emitter 参数、图集分帧和原版/重制同 PTS 起爆/峰值/衰减对比，固定宿主存在或测试全绿不等于视觉还原。

- **7.9.0 (2026-09-13)**：新增 Godot 通关演出协调门禁：末次局内反馈不得被结算场景切换截断，使用固定 owner、有限等待、epoch/cancel 和分支资格依次衔接 HUD Spine、每日激励、结算页；新增主页 prefab 动画恢复方法，区分可取证的状态名/时长与需要明确标注的拟合曲线；扩展 SDK 替换模块为 Godot vendor-neutral 插件模式，加入 consent/service 双门禁、广告频控、稳定 AB 提交边界、奖励 proof 幂等账本、事件契约和 APK 动态 JSON 打包检查；补充 Android 存档原始字节与 PowerShell 文本重定向换行差异的验收规则。

- **7.8.0 (2026-09-12)**：把 JigsawCard 重建实战中落地验证的“局外核心子系统（42格月历每日挑战+12月奖杯陈列室、章节图册25块拼图蒙版+首尾翻页边界与音效）”、“Android 物理返回键全局弹窗栈治理（`set_auto_accept_quit(false)` 与 `_unhandled_input` `KEY_BACK` 拦截）”、“GDScript 动态样式修改 API 避坑（严禁字典访问，必走 `add_theme_*_override`）”、“MuMu 12 / 模拟器双模式与 Win32 default 桌面会话窗口恢复（解决无头 VM 自动化通过但用户物理屏幕不可见假象）”、“权威基线存档（Lv9/金币300/提示0）双向哈希不可变铁律”与“16 项全自动化回归测试套件（0 FAIL）”提炼进 Godot 迁移模块、原生还原门禁（新增 Gate 11 与 Gate 12）及 landing-log。

- **7.7.0 (2026-09-12)**：把本次重建中“发现原版差距→建立差距矩阵→定位资源/坐标/owner/事件根因→最小修复→静态/逻辑/桌面/Android 四层自测→失败分类与回归→交接和 skill 回填”的完整闭环抽成 Godot 共用参考 `restoration-gap-to-qa.md`。明确原版/重制同状态基线、证据污染判无效、八类根因、差距字段、真实拖放回放、编辑器可编辑性、APK/存档/前台 guard 和未覆盖项记录。

- **7.6.0 (2026-09-11)**：把已验证的 JigsawCard Spine 接入经验抽成 Godot 重构模块可复用流程，新增 `godot-spine-integration.md`：GDExtension/ABI 选择、Spine 版本转换、骨骼/atlas/PNG/材质资源链、`.tres/.tscn` 固定宿主、SpineSprite 播放适配层、主轨道/overlay/后续动画、编辑器预览、生命周期取消、Overlay 层级及桌面/Android 验收矩阵；案例专属数量和路径仍留在 CASE_ONLY 文档。

- **7.5.0 (2026-09-11)**：回填 JigsawCard 已验证的 Godot 原生还原经验：Spine 4.1→目标 runtime 转换与 atlas 双轴/pathID 证据、逻辑画布与紧裁图分离、连接组玩法和最大组候选验证、提示/拼接光效/epoch 生命周期、木柄 WIN 与大图历史叠卡结算、累计连击统计、火苗页与跨进程续局、APK/存档/前台 guard 证据和 12 图像/60 分钟交接卫生。新增 `godot-migration-port/references/jigsawcard-restoration-lessons.md`，所有未完成项仍标为待证，未把案例数值推广为通用规则。

- **7.4.0 (2026-09-11)**：新增原切图身份、TextAsset 字节保真、Spine 实际播放、功能事务、Godot 场景固化与包体实测门禁；撤销二进制一律 Latin-1 的规则。合并 ZCode 有效 frontmatter 和 seed JSON 解析差异；多端同步先暂存字节，防止父目录别名导致自覆盖。

- **7.3.1 (2026-09-08)**：补充 Cocos UI/Spine 精修与 QA 三条实战门禁：Spine 缩放从“作者画布比例”升级为“骨架可见 bounds × 完整父级世界缩放”的占屏校准，禁止不同骨架共用 scale；全屏图片背景统一用 `originalSize + max(viewW/srcW, viewH/srcH)` 等比 Cover，Prefab 和运行时同时禁用四边拉伸 Widget；Headless Web 启动前检查 Windows TCP excluded range、HTTP 200 与 `System/cc`，遇到空白错误页时整轮截图作废。另补充拼图块状态标记与可视 Graphics 解耦规则；无损合并 Codex/ZCode 的 Godot S6-qa/S7 landing 记录与快照页功能化四联契约。

- **7.3.0 (2026-09-06)**：新增 `cocos-qa/assets/content-mapping-editor/` 无 npm 依赖本地 HTML 编辑器模板，提供图片+配文+出处同屏审核、自然语言界面、草稿/预览/正式写回分离、SHA-256 并发保护、自动备份和白名单原子回写；关卡数改为动态发现，支持新增关卡缺键待补全与安全追加文案键；定时发现工程变化并保护未保存内容；明确大图列表必须用可视区惰性请求，不能把 530 等历史数量固化为产品上限。

- **7.2.0 (2026-09-06)**：合并 DSH 的 Godot 美术重制 Playbook（烘焙页与动态组件单层纪律、同纹理覆盖、9-slice/几何实测和双证据 QA），修正其 scope-map 相对链接；新增 Cocos `content-image-mapping-qa.md`，明确结构完整不等于图片/配文语义正确，提供图片+标题/配文+出处三联审计、可回写配置表/本地编辑器、白名单回写与 Web/APK 数据复验流程；从 Claude 旧副本恢复文档已引用但维护源缺失的 `install-dep.sh`；多 Harness 发布从固定六端改为发现并验证 WorkBuddy/Agents/Codex/OpenCode/DSH/Trae/Claude/ZCode 八端。

- **7.1.2 (2026-09-06)**：补充 Cocos Creator 3.8.x JSB 的烘焙 Spine 唤醒规则：Prefab 中初始 inactive 且已绑定 SkeletonData 的组件，可能因同值 setter 短路而只有逻辑状态、无原生画面；native 播放前执行一次 null→原 SkeletonData 重绑，再 clearTracks/setAnimation，并用真实设备早期帧判定。明确 `_instance`/`_renderData` 等 Web 私有字段在 JSB 为空不能单独判 FAIL。

- **7.1.1 (2026-09-05)**：补充首胜结算的多层触发与视觉 QA：首胜徽记和通用祝贺 Emoji 不得无证据二选一；按后→前顺序播放并把 Emoji 设为根级 Overlay 最后 sibling；自动淡出动效采用 0/300/750ms 早期帧连拍，要求画面看到 Emoji 主体，禁止仅凭 `active`、动画名或彩纸判 PASS。

- **7.1.0 (2026-09-05)**：把怀旧时光拼图 Spine FX 修复与 QA 提炼为通用流程：新增 `cocos-qa/references/spine-fx-repair-qa.md`，覆盖无 `#` 颜色格式、转换后加权网格完整性、Atlas 声明页与物理 PNG 归一化、真实动画名、Web non-loop 完成点安全回收、声音/触发 owner、根级 Overlay 层级、fresh Chrome profile、像素分类、MuMu 与 APK 包内数据三层证据；`prefab-bake` 新增可编辑 Spine 宿主序列化字段和“停用复用、不销毁”的生命周期规则；补齐两模块 landing log。

- **7.0.0 (2026-09-04)**：新增第十三模块 `sdk-replacement`（完全替换 SDK 一条龙工作流：A 供应商切换 / B 断网离线内置 / C 二进制级消失三档结果定义、P0-P8 八阶段、证据分级与误判表、静态/网络/Seed 三层门禁、真机 DNS/TLS/HOST 验收与报告；附 6 个配套脚本）。补回 `modules/cocos-reverse-engineering/references/android-jsb-reskin-pitfalls.md` 与全部历史缺失脚本（cocos `decrypt_jsc.py`/`pkm_to_png.py`、gameplay 7 脚本），并把"维护源补充清单"升级为"仓库内脚本清单"；cocos `decrypt_jsc.py` 修复最后一条 mx 的 p 索引（对齐 JS 循环后 p=0），`pkm_to_png.py` 按 AOSP ETC1 算法与独立参考实现交叉验证；gameplay `gen_remote_manifest.py`/`download_remote_trait_bundles.py` 修正 config_url 拼接；`verify_vendor_isolation.py` 修正 seed 门禁 JSON 解析与失败码处理；意图分发表、路由表、scope-map、V35 §8 同步更新；validate_skill 校验清单加入 sdk-replacement。

- **6.0.0 (2026-09-04)**：总集从"逆向总集"扩展为"游戏研发·逆向与二开总集"。新增第十二模块 `godot-migration-port`（Unity/Cocos 提取物 → Godot 4.6.2 可开发工程：十项迁移清单、六阶段工作流、每阶段门禁、工具/技能映射、落地迭代）；新增 `references/external-game-skills.md` 外部技能注册表（GodotPrompter v1.13.0 技能全集、gstack-game、claude-code-game-studios、superpowers 方法系、美术管线类；含触发词/来源仓库/更新命令/本地改动提醒）；新增"落地迭代协议"（landing-log 驱动回填、外部更新检查、多端验证）；意图分发表与路由表同步扩展；Godot 基线明确为本机 4.6.2 stable（skills 声明 4.3+ 兼容）；首次回填：GodotPrompter 拉取 8 个提交（eae755a）并同步三端技能副本。

- **5.3.0 (2026-09-01)**：新增第十一模块 `ui-feature-pipeline`（新功能 UI 开发六阶段链路：理解功能→生图效果图→控件拆分→重组实现→视觉QA闭环→烘焙固化；含每阶段产物/门禁、prefab-first vs 代码+烘焙的选型、AI 效率执行顺序约束、效果图 QA 标准、新视图注册三件套）。意图分发表与路由表同步；prefab-bake 保持为链路第 6 阶段的深挖模块。

- **5.2.0 (2026-09-01)**：新增第十个模块 `prefab-bake`（UI 烘焙/WYSIWYG 固化，`GENERAL_DEFAULT` 序列化字段表 + `GENERALIZED_PATTERN` 七步工作流，源自怀旧时光拼图四界面烘焙案例的提炼；含 Cocos 3.x prefab JSON 字段速查、fitSpriteInside 换算、幂等 guard、Cocos CLI EPIPE 坑）。根 SKILL.md 重构为"任务意图快速分发"双层表（意图措辞→模块→首个动作），把拆解/对标分析/二开 SDK/UI 烘焙/构建/QA 等任务面显式映射到模块，提升 AI 激活命中率；scope-map 同步新增模块行；validate_skill 校验清单同步。

- **5.1.0 (2026-09-01)**：新增 jigsawcard 休闲拼图（Unity 6000.3.16f1 IL2CPP）逆向全案 `CASE_ONLY_JIGSAWCARD`。把以下经验提炼为 `GENERALIZED_PATTERN` 写入 `unity-extract` 模块：TextAsset 二进制提取（`m_Script` + latin-1）、Spine 六件套识别与缺图补齐、`global-metadata.dat` magic 值不可信需实测、远程 manifest（manifest_ext.bs）分层解析与 CDN 403 → 真机 mitmproxy、配置证据挖掘与"策划分析交付模板"（四问结构 + 图表化 + 证据/推断分级 + 反直觉发现）。模块范围由纯 `GENERAL_DEFAULT` 扩展为 `GENERAL_DEFAULT` + `GENERALIZED_PATTERN`。

- **5.0.0 (2026-08-31)**：合并两条总集线——资料库 4.2.0（scope map 三层标签、全局证据规则、9 篇 Android 案例参考、15+ 新脚本）与本机 2.2.0（dragonbones-spine-convert、vision-device-testing 两个模块，cocos-qa 的 build_android/gradle_apk，skinning-pipeline 的 atlas/mapping 及测试数据）。全面去重：移除死链 `android-jsb-reskin-pitfalls.md` 引用并列入维护源补充清单；统一全部文档为干净 Markdown + 结构化 frontmatter；修复嵌套代码围栏与列表编号。同步范围扩展为 WorkBuddy / .agents / Codex / OpenCode / DSH / Trae 六端，用 `scripts/validate_skill.ps1` 做结构与哈希一致性验证。

- **4.2.0 (2026-08-28)**：补充玩法安全保护器边界：复用原版 solver 的成功语义、原始输出优先、最少槽位修复、退化候选最后使用、partial tray 不可变，并把分布漂移纳入回归门禁；新增 BlockMaster V128 三块保护与 1x1 洪水专项案例。

- **4.1.0 (2026-08-26)**：新增 `GENERAL_DEFAULT`、`GENERALIZED_PATTERN`、`CASE_ONLY_*` 三层范围标签和完整 scope map；将 Android Cocos 通用方法与 BlockMaster/Block Blast、Blockudoku、Sudoku 历史案例分离，防止其他 Agent 照搬路径、事件名、版本号和服务配置。

- **4.0.0 (2026-08-26)**：补回玩法逻辑/Trait 路由；明确 10.4.7 直接基底与 9.5.0 历史对照；加入原版 owner、稳定激活边界、一次提交、引导预消除判定、特殊材质双就绪、低端机与真机证据规则；移除会过时的固定环境和固定检查数；建立多端同步与一致性验证基线。

- 3.x：完成 Android Cocos 逆向、换皮、网络隔离和运行时回归参考的初步汇总。

- 2.x：建立七模块总集结构（引擎识别 / Cocos 逆向 / 工程修复 / Unity 提取 / 玩法逻辑 / 换皮流水线 / Cocos QA）。
