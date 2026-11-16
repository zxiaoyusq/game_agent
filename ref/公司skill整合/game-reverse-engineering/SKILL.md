---
name: game-reverse-engineering
description: Use when 用户要识别、解包、逆向、恢复、修复、换皮、对标分析、二次开发（SDK/广告/玩法移植）、UI prefab 烘焙固化、构建出包或验收游戏，尤其涉及 Cocos Creator、Unity IL2CPP、Android APK、远程 bundle、玩法算法、Trait、材质/特效生命周期、DragonBones/Spine 转换、广告/埋点或真机网络/视觉验证时；或用 Unity/Cocos 提取物在 Godot 4.6.2 重建可开发工程、做引擎迁移/Godot 二开，以及任何"做游戏/立项/策划/美术管线/游戏工作室流程"需要路由到 Godot 与工作流技能时。也适用于 Mono/IL2CPP 方法体取证、JNI/运行时 DEX 恢复、原生地址映射、跨版本符号迁移与自定义协议还原。也适用于 Cocos MCP 编辑器通道、宿主 App 内嵌功能识别、Transsion SDK 与 Unity AB 报告。也适用于 H5 包体、加载与低内存优化，以及 Phaser/HTML5 web 游戏识别、Phaser 3→4 迁移与 Phaser Agent MCP 云构建路由。也适用于新建或规范一个 Cocos Creator 工程：工程架构设计、代码与命名规范、框架接口边界、Luban 配置链路、用户数据模块、UI 预制体生成、资源目录契约、多语言、引擎与构建、交付自检。
metadata:
  version: "10.5.0"
  updated: "2026-11-11"
  base_version: "8.5.0"
  distribution: "portable-local-merge"
  author: bai-lian
  tags: [reverse-engineering, game-engine, engine-detection, cocos, cocos-creator, unity, il2cpp, assetripper, jsc, xxtea, hek, spine, dragonbones, asset-extract, reskin, skinning, sprite-atlas, replace, rollback, diff, verify, qa, android, adb, screenshot, ocr, logcat, visual-regression, content-mapping, story-audit, level-editor, trait, gameplay, prefab, bake, wysiwyg, ui-bake, competitive-analysis, sdk, sdk-replacement, vendor-isolation, offline-seed, secondary-development, godot, godot-rebuild, godot-migration, migration, hub, external-skill-router, landing-log, game-dev, cocos-mcp, funplay, editor-automation, mcp-channel, transsion, hisavana, athena, ahapush, palm, host-app-embedded, kuikly, ergo, filament, gltf-preview, model-viewer, phaser, phaser3, phaser4, html5, web-game, phaser-mcp, game-agent, hosted-minigame-harvest, minigame, storefront, bulk-harvest, asset-catalog, index-page, zip-game, h5game, cocos-project-standards, project-standards, project-architecture, code-conventions, project-scaffold, luban, naming-conventions, resource-contract]
  triggers: [游戏逆向, 识别引擎, 反编译 cocos, 解包 cocos, 解密 jsc, xxtea, HEK, 重建 cocos 工程, unity il2cpp, assetripper, 提取游戏资源, 换皮, 图集重建, skin_map, 回滚, 差异报告, .fire 场景修复, dragonbones 转 spine, db2spine, 真机视觉回归, 截图验收, ocr, logcat, 关卡图片配文, 图片配文错位, 剧情错配, 内容映射, 关卡配置表, 关卡编辑器, 广告隔离, athena, hisavana, blockmaster, block blast, trait, 玩法算法, UI 烘焙, prefab 固化, 烘焙, WYSIWYG, 编辑器看不到新界面, 美术无法编辑, 对标分析, 竞品拆解, 功能移植, SDK 修改, 二开, SDK 替换, 完全替换 SDK, 完全切断联网, 断网离线内置, 断网版, 原厂隔离, 原厂联网隔离, 换成自己的 SDK, 自定义 SDK 接入, 游戏构建, 出包, godot, godot 重建, 还原 godot 工程, unity 转 godot, 迁移到 godot, godot 二开, 做游戏, 游戏立项, 游戏策划, GDD, 游戏工作室, 美术管线, 游戏代码评审, 技能迭代, landing-log, flver, ba2, forge, EZST, 提取3D模型, 辐射4, 黑魂3, 尼尔, 命运2, DMC5, cocos MCP, funplay, AI 操控 cocos, MCP 通道, MCP 实时驱动编辑器, 无人值守 Cocos 开发, 宿主内嵌, QQ宠物, 社交App内置, Kuikly, Ergo引擎, Filament, gltf 预览, 3D模型预览, model-viewer, phaser, phaser 3, phaser 4, phaser迁移, html5游戏, web游戏, phaser mcp, 美术差异复核, 差异报告回写, 运行态复测, 小游戏包体, 拉取包体, 内嵌小游戏, 即点即玩, 批量拉游戏, 小游戏素材, 游戏介绍页, 索引页, aha games, 宿主小游戏, 工程规范, 代码规范, 接口规范, 分层规范, 目录规范, 命名规范, 配置规范, 数据规范, 资源规范, 预制体规范, 新工程, 工程架构, 工程评审, 规范沉淀, 框架引用规范]
---

# 游戏研发·逆向与二开总集 (game-reverse-engineering)

这是游戏域的统一入口：**逆向**（识别/解包/恢复/换皮/对标）、**重建**（Unity→Godot 4.6.2 迁移、可开发工程还原）、**二开**（SDK/玩法/UI/发布）与**研发路由**（Godot 开发/立项/美术管线/工作室流程）。本文件是纯路由入口：**命中任务 → 查下方分发表定位模块 → 读模块 SKILL.md → 按需读 references**。全局证据规则、端到端流程、案例规则与版本史都在 references/，不在此展开。

路径约定：正文中反引号路径一律相对本总集根目录（如 `modules/skinning-pipeline/SKILL.md`）；markdown 链接 `[]()` 相对所在文件。

涉及 BlockMaster/Block Blast 离线体验恢复时，必须同时读取 [BlockMaster 案例规则](references/blockmaster-case-rules.md)（`CASE_ONLY_BLOCKMASTER`）与玩法逻辑模块及其最新生命周期回归参考。

## 适用范围标签

本技能所有内容按以下三层使用，完整索引见 `references/scope-map.md`：

| 标签 | 其他项目如何使用 |
|---|---|
| `GENERAL_DEFAULT` | 通用方法，默认可用于同类项目，但仍需验证当前工具和构建格式 |
| `GENERALIZED_PATTERN` | 从真实案例提炼的模式；可迁移判断方法，必须重新寻找当前项目的 owner、事件、资源和边界 |
| `FRAMEWORK_BOUND_CFW` | 绑定本团队自研框架 `driftsand-framework`（`framework_cfw_cocos`）的工程契约（门面、基类、生命周期语义）。**仅当体检确认目标工程使用同一框架时可用**；换框架即失效——只借鉴分层意图，API 必须重写。定义与使用约束见 `references/scope-map.md` |
| `CASE_ONLY_BLOCKMASTER` / `CASE_ONLY_BLOCKUDOKU` / `CASE_ONLY_SUDOKU` / `CASE_ONLY_JIGSAWCARD` / `CASE_ONLY_QQPET` | 项目专属证据，只在身份匹配或明确做案例对照时读取；禁止复制字面值 |

`DO_NOT_COPY_LITERAL_VALUES`：其他项目不得照搬包名、域名、appId、签名、版本号、路径、设备序列号、Trait 名、事件名、hook 偏移、资源数量和时间阈值。应复制"怎么证明"的方法，不复制"该案例证明出的具体值"。

## 执行协议（命中任务后先读这一节）

**不要通读本技能包。** 任何任务都按 [执行协议](references/execution-protocol.md) 的五步循环走：**定位 → 读模块执行卡 → 做第一步 → 按需读参考 → 收口**。

每个模块 `SKILL.md` 顶部都有一张「执行卡」，固定四块：**我管什么 / 第一步做什么 / 做完怎么算完成 / 红线**。读完执行卡就能开工，不需要先读完整模块正文。六条铁律（一次只走一个模块、没有证据不写结论、案例字面值不许复制、先备份再改动、交付必附未知清单、失败就报失败）在协议文件里，动手前读一遍。

## 任务意图快速分发（AI 先查这张表）

按用户任务措辞直达模块、首个动作和**做完标准**，避免全文扫描。一张任务常命中多行 → 按行序组合。表中「模块」列的第一个模块是必读模块；具体步骤、产出格式和红线在该模块的执行卡里。

**做完标准列是下限，不是上限。** 它回答「这一步做到什么样才算过」，不是整件事做完。

| 用户任务措辞（命中即走） | 模块 | 首个动作 | 做完标准（这一步过没过） |
|---|---|---|---|
| "这是什么引擎做的" / 拿到包先识别 | engine-identification | 跑引擎指纹检测 | 能写出引擎 + 版本 + 是否加密，并说清依据哪个文件/字段 |
| "Phaser 游戏 / HTML5 web 游戏 / Phaser 3→4 迁移 / Phaser Agent 云构建" | engine-identification（先识别 3/4 与打包壳）+ 外部技能注册表 → phaser4-gamedev / 官方 skills / Phaser Game Agent MCP | 跑引擎指纹检测（dist `VERSION` 字符串） | 引擎与主版本有决定性指纹证据；开发/迁移按被加载外部技能自身完成定义收口 |
| "解包/拆解/提取资源/反编译/解密 jsc" | cocos-reverse-engineering | detect-project.sh 检测构建 | 识别出真实构建类型与加密层，原始密文有备份，解出的资产能打开 |
| "拆 Unity 游戏 / 提取 IL2CPP 资产" | unity-extract | AssetRipper/UnityPy 提取 | 提取产物能反查回原文件，缺失项已列入未知清单 |
| "Mono / IL2CPP 方法体 / JNI / 加壳 / 运行时 DEX / native so / 反混淆" | 引擎对应模块 + [原生代码取证](references/native-code-evidence.md) | 先配对构建/ABI/哈希，确定执行层与地址基准 | 地址基准、执行层、构建配对三者一致，未配对前不写任何偏移结论 |
| "版本升级后重新定位 / 迁移符号 / 旧偏移失效" | 引擎对应模块 + [版本差分](references/binary-version-diff.md) | 两版输入哈希与目标函数证据配对 | 差值标为静态候选，并经运行或第二证据核对后才提交 |
| "分析这个游戏好玩在哪 / 对标分析 / 竞品设计拆解 / 策划分析" | unity-extract（策划分析模板）+ gameplay-logic-reverse | 先提取配置与玩法证据，再按"四问结构"交付 | 结论逐条挂在配置/玩法证据上，无证据的体验判断单独标记 |
| **"新功能 UI 开发 / 画效果图 / 拆 UI 控件 / 拼界面 / 视觉还原效果图 / UI 重构链路"** | **ui-feature-pipeline** | 从功能需求表开始走六阶段链路（生图效果图→控件拆分→重组→视觉QA→烘焙） | 效果图不是运行时资源；切分资产有清单，视觉 QA 有同状态对比 |
| **"新建 Cocos 工程 / 工程规范 / 代码规范 / 接口规范 / 目录与命名规范 / 配置表规范 / 数据规范 / 资源规范 / 工程评审 / 规范沉淀"** | **cocos-project-standards** | 先做工程体检（Creator 版本 / 框架层身份 / 现有逻辑层骨架），再按迁移等级筛选条目 | 体检表已落盘；差异清单逐项标注符合/偏离/不适用；`[DADA]` 条目未被套用，`[CFW]` 条目仅在框架匹配时采用 |
| "抄某个玩法 / 移植机制 / 出块算法 / Trait 开关" | gameplay-logic-reverse | 定位真实执行路径与 owner | 找到原版唯一 owner 与稳定提交边界，行为对照原版可复现 |
| "换皮 / 替换图片 / 图集重建" | skinning-pipeline | skinpipe manifest（默认 dry-run） | dry-run manifest 覆盖全部目标，可回滚，verify 通过 |
| **"AHA/H5 换皮方向未定 / 没有效果图 / 先选市场与风格 / 全程 HTML 评审"** | **h5-canvas-reskin** → `intake-and-direction.md` | 读取已有选择；缺方向先在 HTML 提问市场、用户与产品定位，复用 GPT 生图风格库 | 真实选择形成简报、具体概念图和实施范围；页面选择实际回传，不能缺图就直接进入全库生产 |
| **"H5/canvas 游戏换皮 / Phaser 换皮 / WebView 壳 APK 换皮 / 拼图没拼上 / 底板发暗 / 背景太花 / 卡死无法拖动"** | **h5-canvas-reskin** | 先承接已有状态/目标；方向不明走 HTML 预输入，设计明确后冻结原版并建轻索引 | 代表屏、批量资源、实际合入与约定平台自然 QA 有分层证据；HTML 明示有效进度与未解决项 |
| **"编辑器里看不到新界面 / prefab 还是旧的 / 美术没法编辑 / UI 烘焙 / 固化回 prefab / WYSIWYG"** | **prefab-bake** | 读运行时换肤函数 → 备份 prefab → dump | 编辑器可见且与运行画面一致，prefab 有备份，固化幂等 |
| **"AI 操控 Cocos 编辑器 / MCP 实时通道 / 无人值守 Cocos 开发 / 编辑器起不来 / 进程秒退 / 自动拉起编辑器 / 不用手点扩展面板 / 编辑器老崩溃要自愈续跑 / 批量截运行态画面比设计稿 / 美术差异报告复核 / 差异清单回写与回归复测"** | **cocos-mcp-channel** | 确认 Creator 版本；要自己拉壳先读第 9 节 + `modules/cocos-mcp-channel/references/autonomous-startup.md`，跑 `modules/cocos-mcp-channel/scripts/ensure_cocos_mcp.py`；再用 `get_editor_state` 或 `server_status` 核对工程 | 3.8.x 服务与工程归属有返回证据；最终构建与设备验收仍走 QA |
| "宿主 App 内嵌小游戏 / QQ 宠物 / Kuikly / Ergo / Filament" | engine-identification + [宿主内嵌案例](references/host-app-embedded-qqpet-case.md) | 按前台窗口与 Activity 归属过滤后识别 | 引擎与目标归属有证据，案例路径与开关重新取证 |
| **"拉小游戏包体 / 内嵌小游戏批量出库 / 小游戏素材+介绍页 / 按 gameId 拉游戏 / AHA Games 拉取"** | **hosted-minigame-harvest** | 先判形态 A/B/C（缓存里有没有每游戏元数据文件），再挖商店匿名接口拿 `bundles[]` 直链 | 原包体逐个 MD5 通过、素材 magic bytes 与后缀一致、索引页 0 缺失 0 乱码 |
| **"H5 包体优化 / 减少加载与下载 / 低内存手机优化，保持现有体验"** | **hosted-minigame-harvest** → [包体与运行优化](modules/hosted-minigame-harvest/references/h5-package-runtime-optimization.md) | 对账当前磁盘输入、Git、开发/预览入口和构建，再备份并建立前后测量 | 下载包、解包、HTTP、启动和运行内存口径分别有证据；资源可达性、输入与缓存回归通过，目标真机/宿主未覆盖则明确登记 |
| **"AHA 小游戏从采集、拆解到还原和持续迭代 / 已有宿主 H5 包需要二开"** | **hosted-minigame-harvest** → `hosted-game-lifecycle.md` | 先核对目标、原包与已有成果；缺包才做采集，再按实际引擎拆解和自然运行 | 可追溯的原版基线、路线实验、模块接口、可运行回归与未知清单；真实宿主/SDK 不由模拟替代 |
| "传音 SDK / Transsion / Hisavana / Athena / AhaPush / PalmUpdate" | sdk-replacement | 读供应商参考与素材索引，核对当前契约 | 接入与隔离分别验证，示例配置和密钥按当前项目复核 |
| "Unity AB / TextAsset / Spine 预览 / 完整 HTML 报告" | unity-extract | 提取原始字节并建资源清单 | 资源可反查、runtime 匹配、HTML 内嵌全文经浏览器检查 |
| "Spine 特效错色/错图/不播/遮挡 / 评价字或点赞异常" | cocos-qa + prefab-bake | 先做 Spine 数据/Atlas/动画名静态门禁，再做 fresh-profile Web + 真机分层验收 | 静态门禁全绿，且真机分层证据齐（无真机证据不判 PASS） |
| "每关图片和配文对不上 / 剧情错配 / 导出关卡配置表 / 做关卡编辑器" | cocos-qa | 读真实运行时映射，先分开结构审计与语义审计，再生成可回写三联表/本地编辑器 | 结构 PASS 与语义 PASS 分开给结论；有 SEMANTIC_PENDING 不许整体判过 |
| "构建 web / 出 APK / 打包 / 出包" | cocos-qa | CLI 构建（注意 EPIPE 与 configPath 坑） | 产物能装能起，包哈希与签名已记录 |
| "上模拟器/真机验收 / 截图 QA / 回归测试" | cocos-qa + vision-device-testing | 构建 → 安装 → 逐步截图证据包 | 每步有截图/日志，状态用 PASS/FAIL/BLOCKED/NEEDS_CONTEXT 四词标注 |
| "广告未接入 / 广告未准备好 / 广告按钮无反馈 / 广告失败提示 / 重复领奖" | sdk-replacement + [离线广告与奖励生命周期](modules/sdk-replacement/references/ad-fallback-and-reward-lifecycle.md) | 盘点真实调用者、失败消费者和领取单位，先测同步返回与跨场景结果 | 同步/异步、请求与领取幂等、终态和暂停归属逐项有结论 |
| "广告不弹 / SDK 接入 / 埋点 / 原厂隔离 / 二开修改" | cocos-reverse-engineering（JSB 边界）+ gameplay-logic-reverse | 先取证真实请求 owner，再最小补丁 | 补丁有前后证据，可回退到最后一个已知良好版本 |
| **"完全替换/切断 SDK 与联网 / 断网离线内置 / 原厂联网隔离 / 换成自己的 SDK"** | **sdk-replacement** | 先读 P0-P2（基线+表面+隔离配置），再按 A/B/C 档交付并跑真机三层证据 | 档位已钉死；blocked 三层 0 命中、Seed 三门禁 0、真机联网+断网冷启动均可玩 |
| "工程打不开 / 黑屏 / .fire 修复 / prefab 修不好" | cocos-creator-repair | check_fire_refs.py | 工程能在编辑器打开，场景可见，引用无悬空 |
| "DragonBones 转 Spine / 骨骼动画迁移" | dragonbones-spine-convert | db2spine.py 转换 + 三级 QA | 三级 QA 全过：结构健全 → runtime 全量加载 → viewer 实测 |
| "交付一份分析报告书 / 解析全书" | deliverable-book-template | md2book_template.py 生成 | 目录规范齐、证据标注齐、HTML 能在浏览器独立打开 |
| **"3D 游戏资产逆向 / 采买高模审计 / 官方去重工具渲染 / 怪猎 / 法环 / 燕云 / 辐射4 / 黑魂3 / 尼尔 / DMC5 / 刺客信条 / 彩虹六号 / 命运2 / RE Engine / NeoX / Messiah / FromSoftware / FLVER / BA2 / forge / 未知游戏容器格式"** | **3d-asset-extraction**（引擎路由卡 + 通用容器逆向方法论 + 交付规范）+ 外部技能 re-engine-asset-audit（深度章节+验收标准） | 先按引擎指纹查模块路由表选工具链；未见格式走 method-container-reversing 四步法 | 模型/贴图能独立打开，面数口径与提取质量自验证门禁过 |
| **"用 Godot 重建/还原这个游戏 / Unity 转 Godot / 迁移到 Godot / Godot 二开"** | **godot-migration-port**（按需叠加外部 godot-* 技能） | 先做 S0 资产盘点清单 | S0 覆盖矩阵建立，未知项已标记；之后按 S0–S7 逐阶段过门禁 |
| "做新游戏 / 立项 / 策划 / GDD / 游戏工作室 / 多位角色协作 / 游戏代码评审" | 外部技能注册表 → claude-code-game-studios / gstack-game / godot-brainstorming | 按注册表用 skill() 加载对应独立技能 | 按被加载技能自身的完成定义收口 |
| "Godot 开发（场景/UI/动画/粒子/本地化/导出/性能/调试/测试）" | 外部技能注册表 → using-godot-prompter 引导 + godot-* 技能 | 先加载引导技能，再按子任务加载 | 按被加载技能自身的完成定义收口 |
| "游戏美术管线 / 生图 / 概念图 / 美术规范" | 外部技能注册表 → ai-game-art-pipeline-skill / imagegen-* / vision-skills | 按注册表用 skill() 加载 | 按被加载技能自身的完成定义收口 |

## 路由表（模块全览）

| 用户意图 | 模块 | 入口 |
|---|---|---|
| 引擎未知 / 确认 Cocos、Unity 或其他 | engine-identification | `modules/engine-identification/SKILL.md` |
| Phaser（HTML5 web 引擎）识别、3/4 区分、打包壳与工具链路由 | engine-identification（Phaser 小节） | `modules/engine-identification/SKILL.md` |
| Cocos 2.x/3.x 解包、JSC/资源解密、资产恢复、Android JSB 重打包 | cocos-reverse-engineering | `modules/cocos-reverse-engineering/SKILL.md` |
| DragonBones 转 Spine 3.8 + 真实 Spine QA | dragonbones-spine-convert | `modules/dragonbones-spine-convert/SKILL.md` |
| Cocos 项目打不开、黑屏、`.fire`/引用/场景修复 | cocos-creator-repair | `modules/cocos-creator-repair/SKILL.md` |
| Unity（含 IL2CPP）资产提取和工程还原 | unity-extract | `modules/unity-extract/SKILL.md` |
| 游戏玩法、出块算法、泳道、远程 Trait/机制开关、本地快照恢复 | gameplay-logic-reverse | `modules/gameplay-logic-reverse/SKILL.md` |
| 完全替换/切断原厂 SDK 与联网、断网离线内置远程内容、接入新 SDK | sdk-replacement | `modules/sdk-replacement/SKILL.md` |
| 美术换皮、图集重建、替换/回滚/diff/verify | skinning-pipeline | `modules/skinning-pipeline/SKILL.md` |
| AHA/H5/canvas 换皮：HTML 方向引导与设计评审、GPT 生图、代表屏、批量替换合入、分层运行 QA；含平铺、功能辨识和停摆诊断 | h5-canvas-reskin | `modules/h5-canvas-reskin/SKILL.md` |
| 新功能 UI 全链路（效果图/控件拆分/重组/视觉还原/开发顺序） | ui-feature-pipeline | `modules/ui-feature-pipeline/SKILL.md` |
| 新建/规范 Cocos 工程：架构、代码、接口、引擎、资源配置规范与工程评审 | cocos-project-standards | `modules/cocos-project-standards/SKILL.md` |
| 运行时代码换肤回写 prefab、WYSIWYG、美术可编辑、控件拆分复用 | prefab-bake | `modules/prefab-bake/SKILL.md` |
| Cocos 3.8.x 编辑器 MCP 实时操作与中间验证（Funplay / harady 双实现） | cocos-mcp-channel | `modules/cocos-mcp-channel/SKILL.md` |
| Cocos 构建、模拟器/真机、截图和验收 | cocos-qa | `modules/cocos-qa/SKILL.md` |
| Android 真机视觉回归 / OCR / UI dump / Logcat 验收 | vision-device-testing | `modules/vision-device-testing/SKILL.md` |
| Unity/Cocos 提取物 → Godot 可开发工程、引擎迁移与重建 | godot-migration-port | `modules/godot-migration-port/SKILL.md` |
| PC 3A 游戏 3D 资产离线提取（NeoX/Messiah、RE Engine、FromSoftware、REDengine、Anvil、Creation、Tiger、CRIWARE、MT Framework、Source 2、UE pak、米哈游 blk；含未知容器格式逆向方法论） | 3d-asset-extraction | `modules/3d-asset-extraction/SKILL.md` |
| 逆向拆解结果整理成系列 md / 单文件 HTML 解析全书 | deliverable-book-template | `modules/deliverable-book-template/SKILL.md` |
| 宿主商店/分发 App 内嵌小游戏批量出库（原包体 + icon/hotgame/banner/theme/preview 素材 + 文案 + 索引页） | hosted-minigame-harvest | `modules/hosted-minigame-harvest/SKILL.md` |
| 宿主 H5 原码还原与持续迭代（从采集或现有包出发） | hosted-minigame-harvest | `modules/hosted-minigame-harvest/references/hosted-game-lifecycle.md` |

## 全局规则与流程（按需加载，不在本文件展开）

| 内容 | 位置 | 何时读 |
|---|---|---|
| **执行协议（五步循环 / 六条铁律 / 卡住怎么办 / 状态四词）** | [执行协议](references/execution-protocol.md) | **命中任何任务后第一份读**，之后才按分发表走 |
| 端到端总流程（识别→提取→修复→换皮→烘焙→构建QA→SDK→真机） | [端到端总流程](references/end-to-end-pipeline.md) | 首次走全链路，或不确定阶段顺序时 |
| 全局证据规则（10 条）、格式与解密边界、Android JSB 通用边界、工具环境表、仓库内脚本清单、最小交付门禁 | [全局规则](references/global-rules.md) | 任何取证/二开任务动手前 |
| 未知清单模板（交付必附） | [未知清单模板](references/unknowns-ledger-template.md) | 交付任何逆向/重建/换皮/二开报告前 |
| 采集负面清单（不采集什么） | [采集负面清单](modules/vision-device-testing/references/collection-boundaries.md) | 涉及截图、抓包或运行时采集的任务 |
| BlockMaster/Block Blast 案例专属规则 | [BlockMaster 案例规则](references/blockmaster-case-rules.md) | 仅 `CASE_ONLY_BLOCKMASTER` 匹配时 |
| 本机旧分支独有历史 | [本地分支历史](references/local-branch-history.md) | 追溯同号异义与本次旧能力来源时 |
| 完整版本说明与变更史 | [CHANGELOG](references/CHANGELOG.md) | 需要追溯行为变更时 |
| 三层范围标签、案例分类与模块范围全表 | [scope-map](references/scope-map.md) | 判断内容能否跨项目复用时 |

## 交付证据纪律（未知清单与义务清单）

任何逆向、重建、换皮、二开任务交付时，**必须附带[未知清单](references/unknowns-ledger-template.md)**。未解决问题、缺失的权限与环境、矛盾证据显式登记，不得沉默。「不宣称目标游戏动态恢复已验收」不是措辞习惯，而是清单里可勾选的条目。

三条主链路各自定义「什么算真正完成」，交付前逐条关闭义务清单：

| 链路 | 义务清单模板 |
|---|---|
| Godot 迁移/重建 | [义务清单模板](modules/godot-migration-port/references/obligation-ledger-template.md) |
| 美术换皮 | [义务清单模板](modules/skinning-pipeline/references/obligation-ledger-template.md) |
| SDK 替换 | [义务清单模板](modules/sdk-replacement/references/obligation-ledger-template.md) |

关闭一条义务需要：唯一 owner、规定证据类型、验证器通过、证据路径落盘。缺任一项即为未闭合；豁免需用户明确同意。跨版本差分的对应关系另按[证据等级](references/binary-version-diff.md)标注，静态候选不是因果证明。涉及采集的任务同时遵守[采集负面清单](modules/vision-device-testing/references/collection-boundaries.md)。

## 外部技能路由注册表（Godot 研发 / 工作流 / 美术）

本总集只持有"路由与迁移映射"，**不复制外部技能正文**。命中即用 skill("name") 按名加载；外部技能以各自仓库为版本源，更新与本地改动处理见 `references/external-game-skills.md`。

| 用户意图 | 加载技能（skill 工具按名加载） | 来源 |
|---|---|---|
| Godot 开发（场景/UI/动画/粒子/音频/本地化/存档/导出/性能/调试/测试） | using-godot-prompter 引导 + 对应 godot-* 技能（godot-ui / animation-system / tween-animation / particles-vfx / localization / save-load / export-pipeline / mobile-development / godot-optimization / godot-debugging / godot-testing ...） | jame581/GodotPrompter |
| 游戏立项/策划/设计评审/创意发散 | godot-brainstorming / gstack-game（/game-ideation 等）/ claude-code-game-studios（Producer/Game Designer 角色） | fagemx/gstack-game、Donchitos/Claude-Code-Game-Studios |
| 多角色游戏工作室协作 / 开发流程 | claude-code-game-studios（49 agents + 42 workflow skills） | Donchitos/Claude-Code-Game-Studios |
| 代码质量/测试/评审纪律 | superpowers 方法系（test-driven-development / systematic-debugging / verification-before-completion / requesting-code-review / receiving-code-review / writing-plans / executing-plans / subagent-driven-development） | obra/superpowers |
| 游戏美术管线 / 生图 / 美术规范 | ai-game-art-pipeline-skill / imagegen-frontend-mobile / gpt-image-2 / vision-skills | ybuild-ai 等 |
| 真机视觉验收（任何引擎） | vision-device-testing（本总集模块） | 本总集 |
| Phaser 4 开发 / 脚手架 / 玩法子系统 / v3→v4 迁移 / 无头 playtest / Agent 云构建 | 外部技能注册表 → phaser4-gamedev（26 个 phaser-* 技能，本机克隆）+ phaserjs/phaser 官方 skills 与迁移指南 + Phaser Game Agent MCP | Yakoub-ai/phaser4-gamedev、phaserjs/phaser、phaser.io/agent |

## 按需取证扩展

- 原生代码/JNI/Mono/IL2CPP 方法体：读 [执行层与地址模型](references/native-code-evidence.md)；加壳、匿名 inner、惰性 DEX 或反混淆再读 [运行时恢复](references/protected-runtime-recovery.md)。
- 游戏更新后迁移 owner/函数/字段：读 [跨版本差分门禁](references/binary-version-diff.md)，旧地址与模型候选不能直接提交。
- Cocos 本地算法复现：读 [基于运行观测的重放](modules/gameplay-logic-reverse/references/observed-runtime-replay.md)。非 JSON 的联网/离线契约：读 [自定义协议取证](modules/sdk-replacement/references/custom-protocol-evidence.md)。
- 本轮外部材料的吸收、排除与证据等级：见 [minimaxH3 合并记录](references/minimaxh3-absorption.md)。新文档与离线工具已校验，不宣称目标游戏动态恢复已验收。

## Godot 完整还原追加入口

涉及原切图、Spine、提示道具或可编辑场景时，在现有迁移流程中执行 [原生还原门禁](modules/godot-migration-port/references/native-restoration-gates.md)。导入成功、节点存在、截图相似都不能单独证明完成。

## 落地迭代协议（按实际效果持续更新）

本技能群的"缺失能力"不允许静态等待，必须由真实落地结果驱动更新：

1. **每次项目里程碑立即记录**：在对应模块目录下的 references/landing-log.md（例如 `modules/prefab-bake/references/landing-log.md`）追加一行（日期/阶段/实际结果/与预期偏差/回填动作/验证），不凭记忆补写；新模块自带模板。
2. **landing-log 轮转**：单个 landing-log.md 超过 20KB 时，把较早条目整体移入同目录 `landing-log-archive-<YYYYQn>.md`（只增不改），当前文件保留头部规则与最近条目。
3. **回填触发器**：技能描述的步骤在本项目失效、或发现缺失能力（如 shader 还原比例、godot-spine 版本矩阵、导入器成功率）→ 两周内回填到该模块 `SKILL.md` / `references/scope-map.md` / 门禁清单，并 bump 版本。
4. **版本规则**：行为级内容更新 → minor bump；新模块/路由重构/结构级变更 → major bump，同步更新 `references/CHANGELOG.md` 与 WorkBuddy 资料库在线副本。
5. **外部技能更新检查**：每次游戏项目开始前，按 `references/external-game-skills.md` 的更新命令 fetch 外部仓库（GodotPrompter / gstack-game / claude-code-game-studios / ai-game-art-pipeline / phaser4-gamedev）；有更新且工作树干净才 pull 并同步技能副本；本地有改动先 diff 再决定，禁止盲 pull 覆盖。
6. **多端一致性**：先解析实际目录联接；同一维护源的入口共享修改，无需复制。发现独立有效副本才对照合并并校验全树。缓存和孤儿目录不作为版本源。

## 取代关系

本 skill 总集取代以下独立 skill（新任务一律从本入口开始）。以下名称只用于识别被取代的历史入口；独立目录的归档位置须在当前电脑实查，需要追溯时从备份读取，不把旧独立入口当作版本源：

- `game-build-engine-identification` → engine-identification
- `cocos-reverse-engineering` → cocos-reverse-engineering（模块）
- `cocos-creator-project-repair` → cocos-creator-repair
- `assetripper-unity-extract` → unity-extract
- `game-skinning-pipeline` → skinning-pipeline
- `blockudoku-cocos-qa` → cocos-qa
- `db2spine-spine38-qa` → dragonbones-spine-convert
- `vision-device-testing`（独立真机视觉验收流程） → vision-device-testing（模块）

外部 Godot/工作室/美术技能**不在取代范围**：由本总集路由、外部技能自持内容与版本，见"外部技能路由注册表"。

## 技能发布与同步

本机维护源为 `D:\skills\game-reverse-engineering`。本次实际发现 11 个有效目录联接，替换维护源即可共享更新，保留现有联接。新机器按 `README-部署说明.md` 和 `env.example` 配置工具路径。文档 `${VAR}` 是路径约定；PowerShell 工具脚本读取 `$env:VAR`，不自动加载 `.env`。

| 当前有效入口 | 路径 |
|---|---|
| 共享 Agents | `%USERPROFILE%\.agents\skills` |
| Codex | `%USERPROFILE%\.codex\skills` |
| OpenCode C / D | `%USERPROFILE%\.config\opencode\skills` / `D:\Config\opencode\skills` |
| DSH | `%USERPROFILE%\.dsh\skills` |
| Trae / Trae CN | `%USERPROFILE%\.trae\skills` / `%USERPROFILE%\.trae-cn\skills` |
| Claude | `%USERPROFILE%\.claude\skills` |
| QwenWork CN | `%USERPROFILE%\.qwenworkcn\skills` |
| WorkBuddy / WorkBuddy AI | `%USERPROFILE%\.workbuddy\skills` / `%USERPROFILE%\.workbuddy-ai\skills` |

各入口的同名技能指向维护源。新机器或未安装的 harness 不属于已验证入口。独立副本先对照，再用 `scripts/validate_skill.ps1 -CompareRoots <各端路径>` 校验；外部资料库只在用户授权发布时更新。
