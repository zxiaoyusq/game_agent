---
name: azure-image2-generation
description: Use when 用户要求GPT生图、参考图编辑、透明素材、结构锁定换皮，或使用休闲游戏美术风格与地区配色指导。支持仅规划和编写提示词；实际生图优先当前环境原生工具，外部后端按需使用。
license: MIT
metadata:
  hermes:
    tags:
    - gpt-image-2.5-flare
    - gpt-image-2.5-sunburst
    - himodels
    - gpt-image-gen
    - azure-image2-generation
    - GPT生图
    - azure-openai
    - transparent-background
    - alpha
    - image-edit
    - reskin
    - atlas
    - structure-locked-reskin
    - appearance-transfer
    - 结构锁定换皮
    - 外观迁移
    - 换皮
    - 提示词模板
    - prompt-template
    - 视觉模板
    - 海报
    - 信息图
    - UI样机
    - spine
    related_skills:
    - comfyui
    - spine-animation-pipeline
    category: creative
  version: 2.0.0
  author: Hermes Agent
  platforms:
  - linux
  - macos
  - windows
  external_backend_prerequisites:
    env_vars:
    - HIMODELS_API_KEY
    - AZURE_OPENAI_API_KEY
    commands:
    - python3
---

# GPT 生图

把需求转成图像或简洁的视觉提示词。先判断交付类型与工具，再按需读取相关参考；不要把全部操作手册、历史失败或美术规则拼进一次提示词。

## 选择任务

|任务|读取什么|不额外扩展什么|
|---|---|---|
|仅选风格、配色或写提示词|休闲游戏使用 [美术指导模块](modules/casual-game-art-style/SKILL.md)；其他需求按需找 [模板](references/prompt-template-routing.md)|不检查密钥，不调用生图|
|普通生图/参考图编辑|下方简要流程；需要场景模板时再查模板|不默认走换皮/图集流程|
|休闲游戏效果图、单体素材或风格比较|[美术指导模块](modules/casual-game-art-style/SKILL.md)|概念图不等于切图/可运行UI|
|素材/图集替换，需原尺寸、命名、alpha或atlas契约|[换皮管线](references/reskin-pipeline.md)（先按其顶部表格按引擎分流）|不靠整屏生成替代素材合入|
|**Phaser 2 / 纯 H5 / WebView 壳 APK** 的换皮|不在本 skill → `game-reverse-engineering` skill 的 `modules/h5-canvas-reskin/`|不把 Godot/Spine 的命令照搬到 canvas 游戏|
|结构、动作、轮廓和透明切边必须锁定|[结构锁定换皮](references/structure-locked-reskin.md)|不把模型参考一致性当像素锁定保证|
|实际选择外部脚本/API后端|[后端操作](references/generation-backends.md)|原生工具任务无需读取整份API手册|

## 工具与调用边界

- 当前环境有原生生图/改图工具时，优先原生工具。Codex使用`image_gen`，批量逐图调用；不因“批量”或文件路径需求切换到外部付费脚本。
- 只有实际选择外部后端的任务才使用其密钥、模型分档和命令。原生可用时，不擅自额外消耗HiModels等额度；无原生环境按本地可用管线和用户指定选择，明确指定其他模型/工具时尊重其选择。
- 提示词指导与执行后端解耦；不因“GPT生图”调用而禁止读取指导模块，也不强迫仅写提示词的任务执行后端预检。
- 不把原生工具的未公开模型名猜作image2.5；外部模型/档位以真实配置和返回记录为准。选择画风不等于升级模型档位。
- API Key只用于请求认证，不写入提示词、报告、清单、聊天或命令输出。

## 换皮执行要点

- 原版约束必要的结构与资源契约；用户指定的效果图或对应完整局部必须实际输入生图工具，负责造型、颜色和材质。多种材质可分别给局部参考并说明职责；按用户要求选择同界面方案。
- 用户选定的候选是后续编辑基准；若用户要求只用候选与目标局部，不能传原版。接缝、裁切等单独检查，不擅自替换已认可的画面。用户允许直接复用效果图裁切时才可将其作为成品。
- 用户要求 UI 保原轮廓时，只在原几何内部重绘；不先生成新外形再强贴原 alpha。背景不烤入动态 UI；独立图标按真实占位、状态与契约处理。
- 先校准代表屏，再同族批量生产、累计回填和集中验收；按共同原因返修，不逐件重复审批、构建或报告。遵守用户的候选上限，无有效变化不重复核验同一 hash。风格编号按项目上下文识别；M03 与 T03 不能混同。

## 简要流程

1. 确认输出是概念图、素材、编辑还是工程换皮；保留用户明确的交付范围、布局、文字、尺寸和透明度要求。
2. 查看实际参考图，逐张指定职责：布局、内容身份、画风或编辑目标。参考职责冲突时择取必要信息，不盲目继承旧图画风与空白构图。
3. 把需求压成一次可执行的画面简报。只选当前任务需要的模板/母版，删除重复和互相抵消的词；精确技术约束与视觉方向分开写。
4. 使用选定工具生成/编辑。需要透明时请求真实透明背景并验证alpha；局部编辑明确保留项。原生图先生成再复制到用户指定项目目录。
5. 检查实际输出中的布局、文字、身份、识别、风格和透明语义。失败时只改对应变量；先代表样图验证，再执行已授权批量，避免重复量产同一缺陷。
6. 保存源图、实际提示词/参考职责和交付图；更新引用图像的HTML/内嵌预览。文件与尺寸检查不替代视觉或运行验收。

## 不变的交付约束

已有授权范围内持续完成，不重复索要相同确认。覆盖前保留可恢复原件；比例缩放、裁切、alpha回写分别记录，不能把拉伸/裁切当作所有图像的默认步骤。结构锁定素材使用对应管线验证。

不改现有脚本接口与配置来解决提示词问题。旧入口`scripts/azure_image2.py`和既有`scripts/gpt_image.py`、`scripts/transfer.py`等保持兼容；需要它们时才读取相应操作参考。
