---
name: game-skinning-pipeline
description: Use when 用户要把已逆向或已导出的 Cocos/Unity 资源制作成可回滚的美术换皮工作台，包括 asset_manifest、图集记录与重建、skin_map、安全替换、rollback、diff 和 verify。本模块只编排现有逆向结果，不负责引擎逆向。
version: 1.1.0
created: "2026-08-10"
author: bai-lian
tags: [skinning, reskin, asset-manifest, sprite-atlas, skin-map, replace, rollback, diff, verify, cocos, unity]
triggers: [换皮, 美术换皮, 换肤, reskin, skin_map, skin map, 图集重建, 图集打回, atlas rebuild, 替换素材, 批量替换, 回滚, 差异报告, asset_manifest, 素材清单, 资源清单, 换皮流水线]
---

# 游戏美术换皮流水线 (game-skinning-pipeline)

## 执行卡（先用这张卡，再读正文）

**我管什么**：把已逆向完成的 Cocos/Unity 资源目录编排成可回滚的换皮工作台（manifest → 图集记录 → skin_map → 备份替换 → diff → verify → 回滚）；不管引擎逆向本身，也不管 prefab 结构固化。

**第一步做什么**：跑 `modules/skinning-pipeline/scripts/skinpipe.py manifest --input <导出目录> --engine <unity-il2cpp|cocos-2.4> --output <asset_manifest.json>`，产出并立刻重新解析 `asset_manifest.json`。

**做完怎么算完成**：
- [ ] `asset_manifest.json` 能被 JSON 重解析，UTF-8 写入、兼容 BOM、`ensure_ascii=False`
- [ ] 按 `type/path/id` 稳定排序；`.git/node_modules/library/build` 等默认目录已排除
- [ ] Unity 扫到 `.meta` guid 与 `.prefab/.unity/.asset/.mat` 引用，Cocos 扫到 `.meta/.fire/.prefab/.scene` uuid
- [ ] PNG 宽高来自 IHDR（不依赖 Pillow）；大文件 hash 为流式 blake2b-128
- [ ] 坏文件只记 warning 不中断；退出码符合 0/1/2/3/4 含义

**红线（不可违反）**
- `apply` 默认 dry-run，没加 `--execute` 绝不写入任何文件
- `--execute` 必须先写 `backup/`（记录 hash/大小/mtime/目标/备份路径），再原子替换（临时文件 → PNG header 校验 → `os.replace`）
- 替换后必须重跑 `manifest` 生成 after 清单，禁止只信复制动作或沿用旧清单
- 禁止直接改原图不备份；图集写回前必须备份 atlas PNG 与 meta，且主 uuid / subMetas uuid 原样继承
- `rotated` 或 `trimmed` 的图集子图一律进人工处理清单，禁止伪成功
- 所有读写显式 UTF-8，路径一律 `pathlib.Path`，禁止手拼反斜杠

**卡住时按顺序读**
- manifest 字段/枚举不认识 → `modules/skinning-pipeline/references/manifest-schema.json`
- skin_map 匹配歧义（同名多文件、跨格式、图集子图）→ `modules/skinning-pipeline/references/skin-map-schema.json`
- 图集 rect / rotated / trimmed 处理不确定 → 本文件 `### Phase 2: 图集记录与映射（M2）` 与 `### Phase 4: Cocos 图集原位重建（M4）`
- 真实数据路径、合成夹具、边界测试点 → `modules/skinning-pipeline/references/test-fixtures.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERAL_DEFAULT`。输入目录、引擎参数和构建器路径必须由调用方提供，不得依赖历史机器路径。

把已逆向完成的游戏资源目录（Cocos 2.x 工程 / AssetRipper、UnityPy 导出目录）编排为可复用的美术换皮工作台。**不做引擎逆向**：Cocos 逆向继续调用 `cocos-reverse-engineering`，Unity 提取继续调用 `assetripper-unity-extract`。

## 流水线

```text
逆向结果输入 -> asset_manifest.json -> atlas_extract/index.json
-> skin_map.json -> apply(备份+替换) -> skin_diff.md -> verify_report.md
-> atlas-rebuild(图集原位打回) -> rollback(随时可回滚)
```

## 环境

- 使用项目兼容的 Python（当前脚本建议 3.11+，标准库优先）；先发现实际可执行文件并运行 `--version`，不要假设系统 `python` 别名或固定补丁版本可用。图集像素合成需要 Pillow。

- 无 Pillow 时：`atlas-rebuild` 明确失败并给出退化路径（仅备份/校验/复制，不做像素贴回），其余命令不受影响

- Windows 编码铁律：所有读写显式 UTF-8；JSON 读取兼容 BOM；JSON 输出 `ensure_ascii=False`

- 路径一律 `pathlib.Path`，禁止手拼反斜杠

## CLI 一览

```powershell
python scripts\skinpipe.py manifest --input "E:\download\sudoku-re\assets-export" --engine unity-il2cpp --game "Sudoku.com" --output "..\asset_manifest.json"
python scripts\skinpipe.py atlas-extract --manifest "..\asset_manifest.json" --output "..\atlas_extract"
python scripts\skinpipe.py map --manifest "..\asset_manifest.json" --new-assets "E:\path\new_art" --output "..\skin_map.json" --aliases "..\aliases.json"
python scripts\skinpipe.py apply --skin-map "..\skin_map.json" --backup-dir "..\backup"            # dry-run
python scripts\skinpipe.py apply --skin-map "..\skin_map.json" --backup-dir "..\backup" --execute   # 备份后替换
python scripts\skinpipe.py rollback --backup-dir "..\backup" --execute                              # 回滚
python scripts\skinpipe.py atlas-rebuild --index "..\atlas_extract\index.json" --atlas "..\ui_atlas_1.png" --new-assets "..\new_art" --backup-dir "..\backup" --execute
python scripts\skinpipe.py diff --before "..\asset_manifest.before.json" --after "..\asset_manifest.after.json" --skin-map "..\skin_map.json" --output "..\skin_diff.md"
python scripts\skinpipe.py verify --manifest "..\asset_manifest.after.json" --engine unity-il2cpp --output "..\verify_report.md"
```

全局参数：`--verbose` / `--fail-on-warning` / `--json-log `。  
退出码：`0` 成功，`1` 执行失败，`2` warning 且启用 `--fail-on-warning`，`3` 输入/参数无效，`4` 存在需人工确认的 ambiguous。

## 工作流

### Phase 1: manifest（M1）

- Unity：`--engine unity-il2cpp`，扫描 png/jpg/webp/wav/ogg/mp3/ttf/otf/fbx/obj/prefab/unity/asset/mat/controller/anim/json/plist/spriteatlas/txt；`.meta` 提取 guid；`.prefab/.unity/.asset/.mat/.controller/.overrideController` 扫描 guid/fileID 引用

- Cocos：`--engine cocos-2.4`，扫描 `assets/` 下 `.meta/.fire/.prefab/.scene/.anim/.json/png/音频/字体`；解析主 uuid + `subMetas..uuid` + `rawTextureUuid`；`.fire/.prefab/.scene/.anim/.json` 扫描 uuid 引用 → `referenced_by`

- PNG 宽高从 IHDR 读取，不依赖 Pillow；大文件 hash 流式 blake2b-128

- 默认跳过 `.git/node_modules/library/Library/temp/Temp/build/Build/.import/obj/bin`；输出目录若在输入目录内会自动排除

### Phase 2: 图集记录与映射（M2）

- `atlas-extract`：统一记录已有单图化结果，输出 `atlas_extract/index.json`；`rotated/trimmed/source_size/offset/pivot/border` 全部进入 `sprite_meta`；无法定位 rect 的图集子图 → `atlas_rect=null` + warning；rotated/trimmed → `needs_manual_review`

- `map`：匹配优先级 `aliases -> 完整文件名 -> 去扩展名 -> 规范化名称 -> 相对路径`；同名多文件进入 `ambiguous`；未使用的新素材进 `unused_new_assets`；图集子图标记 `atlas-child` 走重建流程；跨格式（PNG→JPG）默认 `format-mismatch` 不执行

### Phase 3: 安全替换与 diff（M3）

- `apply` 默认 dry-run，绝不写入；`--execute` 时先备份（记录 hash/大小/mtime/目标/备份路径）再原子写入（临时文件 → PNG header 校验 → `os.replace`）

- `rollback` 支持部分回滚：单文件恢复失败不阻塞其它文件，最终报告标红失败项

- 替换后必须重新 `manifest` 生成 after，不能只信复制动作

- `diff` 输出 `skin_diff.md`：数字摘要 + 已替换/新增/移除/未替换/尺寸变化/引用受影响 + 未进包新素材

### Phase 4: Cocos 图集原位重建（M4）

- 输入 atlas PNG + `atlas_extract/index.json` + 替换单图目录（或 skin_map）

- 只自动处理 `rotated=false && trimmed=false && 新旧尺寸一致` 的子图；尺寸不一致默认拒绝（`--allow-resize` 可缩放 + warning）

- meta 原样继承：主 uuid 与所有 subMetas 子 uuid 不变

- 写入前备份 atlas PNG 与 meta；重建后校验 PNG header、rect 不变、被替换 rect crop hash 变化、未替换 rect 不变

- rotated/trimmed 子图一律进人工处理清单，禁止伪成功

### Phase 5: Unity 图集策略与验证闭环（M5）

- Unity 独立 PNG：直接走 `apply` 文件覆盖 + 回滚

- Unity SpriteAtlas：无 rect 元数据时在 `skin_map`/`verify_report` 明确标注「需要 Unity Editor 重打包 / 仅完整性验证」，不静默失败；不修改无法确认的 meta 字段

- `verify`：文件存在 + hash 全量复核 + 引用 uuid/guid 可解析 + 图集 rect 合法；Cocos 可传 `--cocos-build ` 执行 web-mobile CLI 构建；无构建能力时明确写「未执行 Editor 构建，仅执行素材完整性校验」

- 结论 `PASS / PASS_WITH_WARNINGS / FAIL`；`--fail-on-warning` 时 warning → 退出码 2

## QA 边界（开发 plan 第 12 节对应）

- 图集元数据：rect 只是位置，`rotated/trimmed/source_size/offset/pivot/border` 必须同步记录；第一版只自动重建 `rotated=false && trimmed=false && 尺寸一致` 的子图

- 路径/命名：Windows 匹配大小写不敏感但保留原始路径；同名/同 base name 不同目录/同名不同扩展 → ambiguous；中文/空格/括号/emoji 文件名必须实测一次

- 替换安全：默认 dry-run；backup 记录 hash/大小/mtime；部分回滚；替换后重扫 after manifest

- 格式：P0 读取列表见 Phase 1；B2 只承诺 PNG atlas 原位重建，JPG/WebP/KTX/PVR/DDS 只识别 + warning；音频/字体/模型进 manifest 与 diff，不进 atlas 流程

- 引用：Cocos 覆盖 `.fire/.prefab/.scene/.anim/.json` uuid；Unity 覆盖 `.prefab/.unity/.asset/.mat/.controller/.overrideController` guid/fileID；尽力而为，报告标注覆盖范围

- 性能：hash 流式；manifest 按 `type/path/id` 稳定排序；单文件坏文件只记 warning 不中断

## 测试数据

见 `modules/skinning-pipeline/references/test-fixtures.md`（真实数据路径 + 合成夹具 + 边界测试点）。

## 产出物

- `asset_manifest.json` — 统一资产清单（schema: `modules/skinning-pipeline/references/manifest-schema.json`）

- `atlas_extract/index.json` — 图集子图记录（rect + sprite_meta + uuid/sub_uuid）

- `skin_map.json` — 替换映射（schema: `modules/skinning-pipeline/references/skin-map-schema.json`）

- `skin_diff.md` / `skin_diff.json` — 新旧差异报告

- `verify_report.md` — 替换后完整性/构建验证

- `backup/backup_index.json` + `rollback` — 回滚闭环

## 完成定义（义务清单）

换皮任务交付前，按[义务清单模板](references/obligation-ledger-template.md)逐条关闭：运行资源链映射、备份回滚闭环、元数据守恒、单一比例、替换后重扫、verify 门禁、真实播放、状态覆盖、设备复验与交接完整。关闭条件为唯一 owner + 规定证据类型 + 验证器通过 + 证据落盘，反例见模板文内。事实缺口同步登记根级[未知清单](../../references/unknowns-ledger-template.md)。

---

## AI 辅助换皮：结构先行闭环（2026-09-14 验证版）

本节替代 2026-09-13 的 Bbox/质心/inpaint 固定配方。旧配方把未经证明的阈值和单一算法写成通用铁律，无法防止附件语义错误、非等比挤压、静态图冒充动画及运行页面功能丢失。

### 1. 先确认运行资源链，再决定画什么

对每个可见对象记录 `screen/state -> scene/prefab -> node/component -> resource -> atlas page/region -> animation`。同一画面里的静态 fallback、真实 Spine、粒子页和普通 Sprite 是不同资产职责；必须从运行时引用证明谁实际播放。未完成这张映射表前，不批量生图或覆盖资源。

按资产契约分流：

- 普通独立 Sprite：画布尺寸、色彩模式和 Alpha 为几何契约；布局、pivot、NinePatch 边距另行校验。
- 普通 UI Atlas：以 atlas 元数据和原切片为权威，保持页尺寸、region rect、rotate、trim、offset、pivot、border；优先对原切片重绘后原位打回。
- Spine/DragonBones Atlas：从已验证原 atlas 页或 region 开始重绘；保持 page 尺寸、每个附件的 region/rotate/bounds、Alpha、骨架数据、skin/slot/attachment 名与动画名。source/runtime 镜像页必须字节一致。禁止用动画截图替代 atlas，禁止把整个人物或表情画成一张扁平静态图。
- 全屏背景/原画：保持构图焦点、透视、前景安全区和设计宽高比；允许无 Alpha，但仍需在真实页面验证 UI 可读性。

### 2. 先建立风格目标卡

从用户批准参考图提取并落盘：主辅强调色色值与比例、材质、边框、阴影、圆角、字体气质、插画抽象程度、允许元素和禁止元素。必须写明负向方向，例如“避免写实 PBR、霓虹、赌场塑料质感、暗黑宗教装饰”。参考工程只提供风格，不覆盖目标工程的布局、交互、资源身份和动画职责。

### 3. 生成与回贴规则

1. 优先在权威原资源上做图像编辑或受控调色，保留语义轮廓和附件职责；只有原资源无法满足主题时才重画。
2. 生成结果进入隔离目录，先检查主体是否完整、无文字污染、无烘焙棋盘格/黑底、语义和风格正确，再进入适配器。
3. 尺寸适配只允许单一比例：`contain = min(target_w/src_w, target_h/src_h)` 或 `cover = max(...)`。禁止分别按目标宽高 `resize(w,h)`；补边和裁切策略必须显式记录。
4. 目标 Alpha 来自基线资源并逐像素复用。仅在生成预览背景需要去除时对 RGB 空洞做受控修复；不使用固定 15px inpaint 作为通用步骤，也不得覆盖半透明光效的真实 RGB。
5. Alpha 完全一致只是必要条件。仍需检查主体是否被旧 mask 截断、轮廓语义是否匹配、局部是否偏移、透明边缘是否有旧皮肤 halo，以及 region 拼装后是否正确。

### 4. 页面与动画验收

- 截图工具先把 Viewport 设置成项目设计分辨率和方向，再渲染页面；预览缩图保持同一比例。禁止先按桌面默认横屏渲染，再把位图强拉为竖屏。
- 比对项目全局 stretch/aspect 与基线 diff；局部锚点、TextureRect stretch mode、Control size 和资源内部适配分别审计，不能把截图脚本问题误报成引擎屏幕适配问题。
- 普通页面按锁定/解锁、首次/重复、空/有数据、弹窗/子页、返回等状态逐个触发和截图；静态首页通过不代表章节、排行、每日或结算功能仍在。
- Spine/粒子必须在真实运行库播放，捕获起始、主体展开、峰值、结束/回收帧。atlas 展开图、资源可加载、节点 active 或静态 fallback 均不能替代播放证据。

### 5. 交付门禁

- 结构：代码/场景变更白名单；非视觉逻辑默认零差异。
- 位图：所有改动 PNG 的尺寸、模式和 Alpha 对基线逐项检查。
- Atlas：元数据不变、region 全在页内、切片/页像素一致；Spine source/runtime 页哈希一致。
- 运行：设计分辨率页面截图、真实动画中间帧、交互和状态回归通过。
- 设备：最终构建在目标设备/模拟器复验，确认安全区、缩放、输入、动画层级和日志。
- 记录：manifest、差异报告、失败资产和证据路径写入交接文件；任何未覆盖状态明确标为待验。

Godot 重制的完整说明见 `modules/godot-migration-port/references/art-remake-playbook.md` 第 9 章。

