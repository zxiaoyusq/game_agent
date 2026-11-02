---
name: ai-art-automation
description: Use when 用户要求从口述方向、策划或 PRD、游戏源码、逆向工程、已有项目与美术资源中拆分美术需求，并需要生成或换皮游戏美术、批量生图、后处理质检、自动合入源码及程序联调验收；也适用于使用 GameArtAgent 完成端到端美术生产交付。
---

# AI美术自动化

把口述、策划、参考图或现有项目转化为范围明确、逐项可追溯的游戏美术交付。本skill负责编排需求、风格、生产和验收；实际后端由任务和生图技能决定。

## 先选择交付模式

|用户要求|流程与完成标准|
|---|---|
|整套UI效果图、策划/蓝图批量生图、换色、局部修订或分期整理|先读取[UI概念图生产模块](references/ui-concept-production.md)。交付逐图位图、文档、索引及视觉/文件检查；不扩展为源码合入。|
|可用单体素材包|涉及UI拆分、背景、透明修复、图集或引擎素材时，先读取[UI拆分与运行交付](references/ui-runtime-delivery.md)。按资源契约生产并校验素材、透明度及清单；不虚称已合入项目。|
|换皮、资源接入与可运行项目|执行下文生产与合入流程；完成标准包括目标项目使用新资源并通过运行和视觉验收。|

作为GPT生图（imagegen）的美术自动化模块使用时，保留imagegen的后端选择规则：默认内置image_gen，批量逐图调用；仅在用户明确选择CLI/API时走对应路径。GameArtAgent不是概念图生产的强制依赖。下文GameArtAgent CLI、ASSET_SPEC v2、后处理与合入步骤仅适用于实际选择该生产/工程路径的任务。

## 工作原则

- 先理解玩法、界面状态与资源契约，再列资产；不要只扫描图片文件名。
- 需求文档决定目标体验，实际源码决定路径、尺寸、锚点、切片和加载方式。两者冲突时分别记录“设计目标”和“技术约束”。
- 信息足以安全生产时自主推进；只有缺失项会改变资产集合、整体风格、成本或不可逆合入时才请求确认。
- 生产前建立逐项追溯：每个资产必须知道用途、出现位置、来源方式和交付位置；工程合入模式另记实际合入位置。
- 不修改 GameArtAgent 的全局 workflow/checkpoints 来绕过流程，不默认接受 QA 例外，不把程序内建能力说成已经自动合入源码。

## 环境入口

执行前用 `Test-Path` 确认实际位置；快捷方式可能变化，不要只依赖文档中的旧路径。

| 项 | 当前默认位置 |
|---|---|
| GameArtAgent | `E:/Artspace_task1_stabilize/美术AI自动化生产` |
| 启动快捷方式 | `C:/Users/nenghong.zhao/Desktop/启动 GameArtAgent.bat - 快捷方式.lnk` |
| Web 控制台 | `http://127.0.0.1:7788` |
| 任务根目录 | `%USERPROFILE%/GameArtAgent_output/<任务名>` |
| 状态文件 | 任务目录 `.game_art_state.json` |
| 交付包 | 任务目录 `delivery/` |

双击启动器适合需要查看预览或做审美确认的任务；它会结束占用 7788 端口的旧进程。源码/文档驱动任务优先使用基础启动台或 CLI，不依赖对话向导自动补全需求。

## 端到端检查表

```text
- [ ] 识别输入类型并读取全部证据
- [ ] 产出需求简报、资产清单和替换/合入映射
- [ ] 建立并校验 ASSET_SPEC.json v2
- [ ] 预检模型、预算和代表性样张
- [ ] 批量生成、后处理、自动 QA、修复和最终 QA
- [ ] 按映射实际修改目标项目
- [ ] 运行项目并完成资源、代码和视觉验收
- [ ] 输出交付、适配与联调报告
```

## 1. 自动拆分美术需求

先判断输入属于哪一类；多类同时存在时合并证据，不要强行只选一种。

### A. 口述方向

把用户在对话中的口述整理为文字需求，不要求用户先写文档。提取：

- 核心玩法循环、玩家操作和胜负/结算条件
- 页面、弹窗、状态、反馈、动画和特效
- 题材、受众、风格、色彩、镜头、平台与目标分辨率
- 必须生产、可复用和可延后资产

缺少源码时，根据常见实现给出明确假设，并在 `PROJECT_BRIEF.md` 标注；不要伪造精确代码路径或尺寸。真实音频输入先转写再分析。

### B. 工程源码

工程输入包括：带 PRD 但没有美术的原型、需要逆向理解的工程、已有完整项目源码。

1. 找到可运行入口、主玩法、页面/场景、状态变化和渲染链。
2. 搜索图片、图集、字体、Canvas/CSS、Prefab/Scene、配置表和动态拼接路径。
3. 记录现有资源的尺寸、透明度、锚点、九宫格、动画帧、图集和加载约束。
4. 将需求分为：保留、直接替换、参考重制、新增、删除候选。
5. Web 项目可用 GameArtAgent 扫描辅助；Unity、Godot、Cocos 或自定义引擎必须由 agent 继续阅读项目结构，不能把 HTML/CSS/JS 扫描结果当完整事实。

### C. 策划文档 + 现有项目/资源

先从策划或 PRD 提取目标体验，再与源码和现有资源逐项核对：

- 文档回答“应该表现什么”；源码回答“在哪里、何时、以什么格式显示”。
- 已有资源回答“哪些可保留、复用、作为参考或必须兼容”。
- 文档与实现不一致时写入差异，不静默选择一方。

### 统一生产契约

生产前至少建立以下文件：

1. `PROJECT_BRIEF.md`：输入来源、玩法、页面/状态、风格、平台、假设和冲突。
2. `ASSET_PLAN.md`：资产 ID、名称、用途、页面/状态、类型、尺寸、透明、优先级、来源方式。
3. `ASSET_SPEC.json`：GameArtAgent v2 生产规格。
4. `ART_INTEGRATION_PLAN.md`：已有项目的逐项替换和联调计划；仅做独立素材包时可省略。

`ART_INTEGRATION_PLAN.md` 每项必须包含：

| 原资源名/路径 | 新资源名/目标路径 | 代码或配置引用位置 | 合入方法 | 注意事项 | 联调验证 |
|---|---|---|---|---|---|

合入方法要写清直接覆盖、改路径引用、改图集/Prefab/配置、调整布局或新增加载逻辑；注意事项覆盖尺寸、透明度、锚点、九宫格、帧序、命名和平台导入设置。

## 2. 选择资源来源并建立规格

同一任务可以混合三种来源：

- `generated`：全新生成；使用目标规划尺寸，不携带来源图字段。
- `concept_art`：来自已确认效果图及控件裁切；使用 `source_image/source_bbox/reference_crop` 保持构图与风格。文字、精确 UI 或轮廓敏感控件优先直接复用确认裁切，避免无意义重绘。
- `imported`：保留或复用已有资源；记录真实 `source_image`，不要假装是 AI 生成。

必须使用项目当前 `models/asset_spec.py` 的 v2 校验器验证规格。不要凭旧示例手写不存在的字段，也不要把所有资产都归为 `generated`。

Prompt 要求：

- 全局风格只描述画风、材质、色彩、光照和视角；不要把完整场景词灌入所有单体资产。
- 单体/UI/图标写明 `single isolated element, no scene, no text`；透明资产使用流水线支持的纯色底策略。
- 背景、角色、道具、UI、文字层和特效分开生产；除非明确要求，不把可本地化文字烘焙进图片。
- 每个 prompt 写清主体、视角、轮廓、材质、色板、光照、留白和禁止项。

## 3. 启动生产

在 GameArtAgent 根目录使用当前 CLI；先运行帮助确认参数未变化。

```powershell
python -m art_agent doctor
# 首次或配置缺失时：python -m art_agent setup

# 从口述/文档/预制清单新建
python -m art_agent new --name <任务名> --dir <全新任务目录> --template <模板名>

# 从已有工程拆需求并换皮
python -m art_agent reskin --name <任务名> --dir <全新任务目录> --source <工程副本>

# 有效果图时追加：--concept-arts <图1>,<图2>
```

使用内置模板（如图标、背景、道具、UI、换皮或已确认清单），不要临时编辑全局模板。默认保留 Web 的审美确认门禁。生产目录必须与目标源码目录分离；不要对已有任务目录随意使用 `--force`。

当前生产主链：

```text
需求/源码扫描 → planning → concept（按任务需要）→ ASSET_SPEC v2
→ image_gen → postprocess → qa_auto → repair → qa_final
→ scene_compose → delivery
```

批量生产前先检查预算并生成少量代表资产，验证风格、构图和透明策略后再放大批量。费用与生成来源以任务账本和 manifest 为准，未知价格不得当作零成本。

## 4. 后处理与质量门禁

每张资产必须经过：

1. 精确尺寸适配：透明单体 contain-fit，背景按目标画幅处理，禁止拉伸。
2. 透明与边缘检查：洋红/假白底/棋盘残留、半透明脏边、占位比例。
3. 语义与风格检查：内容是否符合资产用途、是否误生成完整场景或文字。
4. 自动修复：失败项优先 edit 参考原图，必要时改 prompt 后重生。
5. 最终 QA：可按资产修复、返回控件拆分或重做效果图；接受例外必须有理由和范围。

当前复杂边缘抠图主要是确定性启发式，不得宣称已经使用 ML 真抠图。头发、发光、烟雾和半透明特效必须额外视觉复核。

### 后处理落地工具（scripts/postprocess.py，本地 PIL 不耗 API）

上述步骤统一用 `scripts/postprocess.py` 执行。依赖 Pillow（必需）、numpy（仅 `--remove-bg` 需要）：

```bash
python -m pip install pillow numpy   # 无管理员权限时加 --user；ENABLE_USER_SITE 禁用时改 --target 到 sys.path 目录

# 抠纯色底 + contain 到目标范围 + 透明校验（抠底后 check-alpha 必跑）
python scripts/postprocess.py --input raw.png --output final.png --remove-bg --tol 30 --resize 512x512
python scripts/postprocess.py --input final.png --check-alpha
# 压缩到目标体积 / 裁透明空白 / 居中贴背景图 / 底色拍平
python scripts/postprocess.py --input final.png --output small.png --compress --close-size 8000
python scripts/postprocess.py --input final.png --output trim.png --crop-trim
python scripts/postprocess.py --input final.png --output card.png --paste-bg bg.png
python scripts/postprocess.py --input final.png --output flat.png --flatten white
```

参数速查：`--remove-bg`（配 `--tol`：白底约 30、深色底约 60）、`--crop-trim`、`--fit-max N`、`--height/--width N`、`--resize WxH`（contain 等比、不变形）、`--compress`（配 `--close-size N` 选 256/128/64/32 色板）、`--paste-bg`、`--flatten`、`--check-alpha`。每张资产处理后必须用 `--check-alpha` 核对 mode/四角 alpha/透明像素计数，并实数像素尺寸，再进入 qa_auto；禁止只凭脚本退出码 0 判定通过。

## 5. 自动交接并合入项目

GameArtAgent 的 `delivery/` 是生产交付包，不等于已经合入目标源码。由本 skill 继续执行：

1. 在项目副本或独立分支上操作，保留可回退点。
2. 按 `ART_INTEGRATION_PLAN.md` 将每个资源放到准确目标路径。
3. 修改真实代码/配置引用；不能只复制文件。
4. 保留资源契约：尺寸、锚点、九宫格、图集帧序、动画关系、透明和颜色空间。
5. Web 项目检查 `<img>`、CSS、Canvas、预加载和动态路径；引擎项目检查导入设置、Prefab/Scene、图集和资源表。
6. 删除旧引用前搜索全项目，确认没有运行时、主题、关卡或语言分支仍使用它。
7. 启动目标项目，走主玩法和关键状态，修复程序联调问题后再收口。

可使用 GameArtAgent 的 engine pack/接入指南整理 Cocos、Unity、Godot 目录，但它不能替代对目标项目的实际代码修改和运行验证。

## 6. 验收与交付

至少完成以下验证：

- `delivery/assets` 与 `ASSET_SPEC.json` 必需资产一一对应，`MANIFEST.json` 可校验。
- 替换映射中的每个目标文件存在、可解码，旧引用没有遗漏，新引用没有破图或缺资源。
- 项目可构建/启动，控制台无新增资源错误；关键页面、状态、动画和交互可运行。
- 实际运行截图中的语义、布局、比例、透明边缘和整体风格通过视觉复核。
- `ART_ADAPTATION_REPORT.md` 记录逐资产 OK/CONCERN/MISMATCH；MISMATCH 修复并复验。
- `ART_DELIVERY_REPORT.md` 记录替换映射、修改过的源码/配置、运行命令、联调结果、例外与回退方式。

只有上述检查完成，才能告诉用户“已完成自动美术生产和合入”。

## 安全恢复

```powershell
python -m art_agent status --dir <任务目录>
python -m art_agent resume --dir <任务目录>
# 需要从后处理重新派生成品时：
python -m art_agent resume --dir <任务目录> --from-phase postprocess
```

- 普通中断优先直接 `resume`，保留已完成阶段和原始产物。
- 整体重跑不要从 `repair` 开始；无精确资产范围时它会清理整批 `processed`。优先从 `postprocess` 安全重建派生产物。
- 不手工删除状态或产物目录，不通过清空 checkpoints/默认接受例外来“解卡”。
- `doctor` 是配置自检，不等于 API 真实连通；还要执行连接测试或最小样张。

## 常见失败

- 只有泛化 brief，没有读取实际源码、状态和资源引用。
- 只有资产清单，没有“原路径 → 新路径 → 引用位置 → 联调项”的替换映射。
- 把已有资源全部重生，丢失文字、锚点、切片和动画关系。
- 把完整场景描述写进每个单体 prompt，导致图标变场景。
- 把 delivery 包当成完成，没有修改项目或运行验证。
- 自动接受 QA 例外后直接交付，没有记录和复验。
- 只看静态图片，不在真实运行画面里验证比例和交互。
