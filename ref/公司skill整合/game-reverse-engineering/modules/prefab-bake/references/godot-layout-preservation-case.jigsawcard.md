# 案例：Godot 换皮项目的"重新烘焙不砸美术"落地（jigsawcard-godot，2026-10-07）

> **何时读我**：哥哥说"美术在编辑器里调好了，重跑生成器/烘焙器又被打回原形"、"改了没生效"，或要判断某处排版该由生成器拥有还是编辑器拥有时。
> **读完能做到**：按取证顺序（先确认 tscn 是新值 → 运行时探针 → 搜写入者 → 比对生成器默认值与场景当前值）定位"两个写入者"，再用 G2 读回保留 / 生成器入口改 SceneTree / G3 基线驱动 / G4 回归门禁这套修法落地，并用 `修复回归门禁` 证明往返不变。
> **范围**：`CASE_ONLY_JIGSAWCARD`

> 这是 [1c 布局真源契约](../SKILL.md) 与 [G2/G3/G4](../SKILL.md) 的实证案例。
> 只取方法与命令，**不要复制坐标/字号等具体值**（`DO_NOT_COPY_LITERAL_VALUES`）。

## 症状
美术在 `scenes/shell/HomeArt.tscn` 里调 `ChapterTitle / TileCount / StaticLabel / DailyDate / 每日`
的位置与字号并保存，运行时**不生效**；同一批改动里**图片**的调整却生效。

## 取证顺序（照抄这个顺序，别先改代码）
1. **确认 tscn 里确实是新值**（不是编辑器没保存）：
   `Select-String -Path scenes/shell/HomeArt.tscn -Pattern 'offset_top = -506|font_size = 90'`
2. **运行时探针**：把场景 `instantiate()`  `add_child()`  等 3 帧，读节点几何。
   本项目在 `scripts/qa/probe_home_layout.gd`（`extends SceneTree`，headless 可跑）。
    结论：运行时拿到的就是 tscn 的值  **不是运行时丢弃，而是文件被别的写入者改回去了**。
3. **找写入者**（两条命令，输出都要逐条看）：
   ```powershell
   Get-ChildItem tools,scripts -Recurse -Include *.gd,*.py -File |
     Select-String -Pattern 'ResourceSaver\.save|save\(packed|\.tscn.*write_text'
   Get-ChildItem scripts -Recurse -Include *.gd -File |
     Select-String -Pattern '\.offset_(left|top|right|bottom)\s*=|add_theme_font_size_override|\.position\s*=\s*Vector2'
   ```
    命中  `tools/home_art_builder.gd`（硬编码 rect/字号）+ `tools/generate_home_art.gd`
     （把结果写回 `res://scenes/shell/HomeArt.tscn`，正是美术编辑的文件）；
      `HomeSlices.gd` 每次 refresh 覆写 rank 标签 rect/字号。
4. **确认"生成器默认值  场景当前值"**（证明被覆盖过）：
   生成器里 `Rect2(-250,-483,500,100)` 字号 95 白字 vs 场景里 `(-260,-506.25,500,131.25)` 字号 90 深蓝字。

## 修法
1. **生成器读回保留**（G2）：生成前 `_load_keep_values()` 读回现有 `HomeArt.tscn`，
   建 `节点名  pos/size/font_size/font_color/outline_size/alignment` 表；
   生成同名节点后套用；硬编码只作新节点默认值。
   - 坑：Godot 写盘把 `@Label@13` 写成 `_Label_13`  名字匹配要 `@``_` 规范化；
   - 坑：`_apply_keep()` 必须在**改名之后**调用（否则查的是默认名 `StaticLabel`）。
2. **生成器入口改成 SceneTree**：`extends Node` + `get_tree().quit()` 的写法在 `--script` 下会挂住
   （报 "Can't load the script ... as it doesn't inherit from SceneTree"）；改成
   `extends SceneTree` + `_initialize()`，并把"构建 + pack + save"搬进来。
3. **运行时改基线驱动**（G3）：
   - `HomeSlices.gd`：首次采样 rank 标签基线；Lv.N 用基线，倒计时按 19/24、128/102 比例推导；
   - `HardFinishToast.gd`：Body 两态 band，基线取"有标题"版，无标题态 = 顶端  标题高度；
   - `RankRow.gd`：标签宽度照测，**间距**取基线（不要写死 `+34`）；
   - `SettlementDialog.gd`：卡组静置位置改为读 prefab 首次值。
4. **回归门禁**（G4）：`scripts/qa/test_prefab_tuning_keep.gd`
    快照 5 个关键 Label  重跑生成器（pack 到 `user://` 临时场景，不覆盖真实资产） 逐项比对，
   `PREFAB_TUNING_KEEP_RESULT checks=5 failures=0`。
5. **同类生成器一起处理**：`tools/build_settlement_fireworks.gd` 同为"原地重写产物"，
   加同款保留；往返实测 32/32 节点位置不变。
   其余 `generate_settlement_scene.py` / `streak_generate_scene.py` / `restore_popup_slices.py` /
   `serialize_spine_prefabs.py` 是**一次性重建脚本**，未改重跑前必须先加 G2 逻辑。

## 交付物（可复用）
- 案例文档：项目内 `docs/PREFAB_LAYOUT_PRESERVATION_20261007.md`（含两类写入者的全仓审计表）
- 门禁：`scripts/qa/test_prefab_tuning_keep.gd`
- 探针：`scripts/qa/probe_home_layout.gd`、`tools/diag_home_keep.gd`
- 提交：`e9823b2`（生成器 + 运行时 + 门禁）、`c615eaf`（另外 3 处运行时覆写 + 审计文档）

## 一句话结论
**"改了没生效"在烘焙流程里几乎总是"两个写入者"问题**：先找写入者、再定唯一真源、再补门禁；
不要用"禁止重跑烘焙器"来规避那等于让烘焙流程死掉。
