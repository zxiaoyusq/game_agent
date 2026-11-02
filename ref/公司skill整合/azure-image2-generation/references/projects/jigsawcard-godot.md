# 项目卡片：乐信拼图（jigsawcard-godot / Godot 4.6.2）

## 路径

| 项 | 值 |
|---|---|
| 工程根 | `E:\Gameprogram\jigsawcard-godot` |
| 素材目录 | `assets\textures\`（扁平存放，约 5000+ PNG） |
| 引擎 | Godot 4.6.2 stable |
| 编辑器 / 控制台可执行 | `E:\Godot\Godot_v4.6.2-stable_win64.exe` / `E:\Godot\Godot_v4.6.2-stable_win64_console.exe` |
| 主场景 | `scenes\GameHUD.tscn`（用户通常开着编辑器） |
| 重建工作目录 | `_tmp_icon_rebuild\`（历史）/ `_art_rebuild\`（本技能默认）——两者都必须有 `.gdignore` |

## 素材命名与成对关系

- 同一张贴图常有两份：Figma 导出的原始名（如 `5 3.png`、`Strong Icon  2.png`、`954406831b3f4765b504e305a1496258c73608db2 1.png`）与引擎内名 `tex_<数字>_<数字>.png`（字节相同）。
- **替换前必须查同内容副本**：按「同名 / 同字节大小 / 同 md5」三个口径各查一遍，再确认没有 `bin\`、`exports\` 之外的第三份。查法：
  - `Get-ChildItem -Recurse -Filter '95440683*'`（同名）
  - `Get-ChildItem -Recurse -File -Filter *.png | Where Length -eq <字节数>`（同大小）
  - Python 里对所有同尺寸 PNG 算 md5 取相同者（同内容）
- 场景引用方式：Godot 4 用 uid 引用（`uid://...`）。`findstr /s /m /c:"<文件名>"` 查不到不代表没人用；替换是原地覆盖 + 同名，uid 不变，因此不需要改场景。

## 导入设置（`<贴图>.png.import`）

~~~ini
compress/mode=0                 # Lossless（不压缩纹理，源 PNG 换了就等值换）
process/fix_alpha_border=true   # Godot 导入时会修 alpha 边界，边缘杂色会被淡化但仍建议自己做干净
process/premult_alpha=false
mipmaps/generate=false
~~~

缓存链路：`.godot\imported\<文件名>-<hash>.ctex` + `.md5`（内容：`source_md5` / `dest_md5`）。
**重新导入的判定**：`.md5` 里的 `source_md5` 变成新文件的 md5，即已完成。

## 编辑器运行时的行为（实测）

- 编辑器**开着**时：Godot 不会立刻扫描改动，而是在**窗口获得焦点**时扫描并重新导入。
  实测：替换后 20 分钟未自动重导；用户切到 Godot 窗口后立刻完成（00:11 看到 ctex 重生成、source_md5 更新）。
- 因此流程里：编辑器在跑 -> 轮询 `.md5` 等待；编辑器不在跑 -> `--headless --import`。
- **不要在编辑器开着时另起 headless 实例导同一个工程**，避免 `.godot` 缓存竞争。

## 已完成的案例（可作风格与流程基准）

| 项 | 内容 |
|---|---|
| 目标 | `assets\textures\954406831b3f4765b504e305a1496258c73608db2 1.png`（96x96 RGBA，橄榄枝古典书图标） |
| 故障 | alpha 外轮廓被矩形裁切：右侧搭扣带右端、书口、右下书角被切平，mask 右侧是一条直线 |
| 方法 | `use_ref=original` + 「保持原透视/构图/配色，补全被裁掉的轮廓」；2 候选取"修图型" |
| 结果 | 96x96 RGBA 不变、四角 alpha=0、主体留白 8px；24404 B -> 14012 B（-42.6%，逐像素无损） |
| 产物 | `_tmp_icon_rebuild\`（1024 母版 `book_edit_v2.png`、对比图 `compare_sheet.png`、破损原图备份 `ORIGINAL_broken_backup.png`） |

## 同屏素材家族（风格对照用）

`5 3.png`（奖章）、`Strong Icon  2.png`（关闭按钮）、`gold_04.png`（黑桃）、
`ranks_detailpage_icon_top1.png`（金币 1）、`img_pinata_progress_lock.png`（金锁）、
`gameplay_hint_default.png`（灯泡）、`setting_ic_upgrade.png`（点赞）等。
共同特征：**半哑光塑胶/黏土质感 + 抛光金属金 + 明亮高饱和 + 圆润饱满 + 缩到 96px 仍一眼可辨**——
与 `references/style-mediterranean-casual-3d.md` 的地中海古典配色完全同源，重绘时按那套锚定词走即可无缝融入。

## 重绘返工批（2026-09-29，四类分型）

索引：`docs/REBUILD_INDEX.md`（99 组重绘对照逐条状态）+ `docs/rebuild_index.json`。
流水线：`_art_rebuild/rebuild_batch.py`（gen / prepare / install / report 四段，支持 `fit=bbox|full|contain|mask`
与 `alpha=ai|original`）；工作目录 `_art_rebuild/`（已带 `.gdignore`）。

| 批 | 类别 | 张数 | 关键手法 |
|---|---|---|---|
| 奖杯 | 3 类（尺寸/比例不变、alpha 可变） | 12 | `fit=contain`；银版由 `tools/build_silver_trophies.py` 从金版重算 |
| 困难卡背 | 1 类（轮廓锁死） | 4 | `fit=contain` + 红/绿主色；**必须同步 `gp_card_back_reskin_hard_*` 才生效** |
| 图鉴小物（猫） | 1 类（原 alpha 逐字节回裁） | 6 | `fit=mask`（安全区锁定）+ 邻域填色；`alpha_byte_identical` 实测 0~3 像素差 |
| Bg__1 / Bg__2 | 4 类（回退原版） | 2 | 原图仍在工程内：`tex_-3399035082897568113_*.png` / `tex_711539600110562312_*.png`，sha256 与 `reskin_manifest.json` 的 `baseline_sha256` 一致 |

提交件：`_art_rebuild/state/REBUILD_DELIVERY_REPORT.md` + `report_install_*.md`。
回滚：`_art_rebuild/<batch>/<id>/ORIGINAL_*.png`；卡背槽位备份 `_art_rebuild/cardback_reskin_backup/`；
回退前背景 `_art_rebuild/revert_bg/BEFORE_*.png`；旧银版 `_art_rebuild/trophy_silver/BEFORE/`。

### 本批踩过的坑（详见技能 `references/rebuild-pipeline.md` 附二）

- 第 1 类资产必须用 `fit=mask`：按原内容框铺满会「切平耳朵 + 黑边描边 + 不透明纯黑口袋」三连故障。
- 边缘漫延的颜色源要排除「全透明处的 (0,0,0)」，否则漫延出去就是黑块。
- `clean_transparent` 只准归零 RGB，写成 `out[m]=0` 会连 alpha 一起清零，导致 alpha 门禁必挂。
- 黑块门禁用「最大连通域」而非黑像素总数；木质基座的自然暗部要单独放宽。
- 喂给模型的参考图，透明区不要预填黑底，且 prompt 必须写明棋盘格是「透明信息、不要画」。

## Logo 重设计（2026-10-02，已定稿 Holy Solitaire 并落地）

| 项 | 值 |
|---|---|
| 工作目录 | `_art_rebuild\logo_redesign\`（`build_compare_html.py` / `shot_html.py` / `prompt_<name>.txt` / `logo_<name>.png` / 历史版本 `archive_v3\`） |
| 对照页 | `docs\ui_reference\logo-redesign-20261002.html`（主页实机底图 + CSS 叠加，逐候选展示替换效果与透明底原图） |
| 主页 logo 槽位 | `assets\ui_slices\home\jigssawcard_logo.tres`（AtlasTexture 区域 `Rect2(806,2,957,398)`，图集 `assets/ui_atlases/home.png`）；显示矩形 (345,325)-(735,505)@1080×1920 → 对照页叠加 CSS `left:29%; top:14.6%; width:42%; height:14%; object-fit:contain` |
| 名字核查 | 2026-10-02 Google Play 精确名核查通过的 6 个候选：Holy Solitaire / Holy Jigsaw / Faith Pieces / Gospel Pieces / Psalm Puzzle / Trinity Tiles；`Grace Solitaire` 已被占用（50K+ 下载）弃用 |

5 轮 17 张的结果：

- ✅ `logo_holy_solitaire.png`（v1：文生图 + 约 150 字短提示词）：拼写正确、透明 61%、金色 3D 字 + 藏青丝带 + 拼图牌背 + 光环天使翼 —— **唯一全项达标，兼作风格基准与候选**。
- ⚠ 其余 5 名均未同时满足「透明 + 无 slogan + 目标 3D 风格」：holy_jigsaw / faith_pieces / gospel_pieces / psalm_puzzle 为带 slogan 或偏插画的过渡稿；**trinity_tiles 连败 6 次**（每次烤满底），已止损。
- 失败版本未删：`archive_v3\logo_<name>_v3.png`、`_v4.png`；透明质检明细见同目录 `IMAGE_logo_*_MANIFEST.json`。

### 定稿落地（2026-10-02 同日完成）

| 项 | 值 |
|---|---|
| 选定 | **Holy Solitaire**（用户从对照页直选；素材 = 上面全项达标的 v1 稿） |
| 槽位改动 | 区域高 398 → **700**（`Rect2(806,2,957,700)`）；节点缩放 / 动画关键帧 / `HomeMotion.LOGO_BASE_SCALE` 一律不动 |
| 实机尺寸 | 显示框 390×180 → **390×316.6**；logo 本体 **381.8×292.6**（横向 349.1..730.9，对齐旧 logo 345..735） |
| 为什么加高 | 达标稿 1.304 竖排构图 vs 槽位 2.167：等比装入只剩 199×169；**逼模型改横幅 4/4 全部烤底**（详见 SKILL.md 7.8） |
| 落位余量 | 章节牌中心带最早内容 y=574：静止留 21.1 px、动画峰值（×1.04）留 15.5 px |
| 图集备份 | `_art_rebuild\logo_redesign\atlas_backup\home.png.3d06f571e4fc.bak`（旧 md5 `3d06f571…` → 新 `a2762892…`） |
| 工程侧文档 | `docs\LOGO_HOLY_SOLITAIRE_20261002.md`（六处接线点对照 + 门禁 + 复现命令） |
| 证据 | `docs\evidence\logo_redesign_20261002\home_holysolitaire_installed.png`、`logo_band_installed.png`（脚本 `scripts\qa\capture_logo_installed.gd`） |
| 提交 | `485af78` art(reskin) / `5e0da72` docs(art) |
| 回归 | `--headless --import` 退出码 0 + `source_md5` 对齐；`test_home_motion` 18/18、`test_logo_loop` 6/6 |

**待办**：商店素材（512 图标 / 1024×500 特色图 / 启动页 logo）未做；工程名仍是中文「乐信拼图(Godot)」，英文名只作字标。

## UI 重置 5 件：错位修复（2026-10-07）

用户报告 `CommonDialogBg / gameplay_hard_banner_bg / gameplay_hard_fire_icon / Flower / effect_radar_search`
"没有按原版 alpha 通道轮廓生成、图案明显错位"。**真正的病因不是轮廓**：5 件的 alpha 与原版**逐字节相同**，
是**画上去的主体在轮廓内偏移**：

| 资产 | 主体框中心偏移 | 主体框尺寸（原 -> 旧） |
|---|---|---|
| Flower | 下移 23px | 266x261 -> 238x215 |
| effect_radar_search | (-39, +77)px | 927x1001 -> 848x848 |
| gameplay_hard_banner_bg | 左移 16px | 982x285 -> 950x282 |
| gameplay_hard_fire_icon | 上移 5px | 54x65 -> 51x55 |
| CommonDialogBg | 基本对正（是风格不匹配） | 1027x1368 -> 1024x1359 |

**做法**：按旧批 `manifest_ui_fix_a/c/d` 的字段重建 manifest 
`ref=原版真图` + `fit=bbox` + `alpha=original`，5 件 x 2 候选；
`prepare` 门禁全部 IoU=1.000 / 覆盖 100% / 脏透明 0；再用内容框残差 + 可见区黑斑量挑稿。

| 资产 | 选用 | 主体框残差 | 可见区黑斑 |
|---|---|---|---|
| gameplay_hard_fire_icon | cand2 | 1px | 0 |
| Flower | cand1 | 0px | 0 |
| effect_radar_search | cand1 | 0px | 868px（右下小暗点） |
| CommonDialogBg | cand2 | 4px | 1,173px（cand1 有 77,106px 纯黑矩形，弃） |
| gameplay_hard_banner_bg | cand1 | 0px | 4,951px（cand2 是 26,371px，弃） |

**网络教训（最贵的一条）**：同一批提示词，旧链路 `/images/generations` 388~680s 或 900s 超时、
26 分钟 0 产出；换**新加坡节点**后 `/models` 1.6s、生图 47s 返回 200、单张 60~77s 稳定出图。
=> 生图超时先查链路，不要反复改提示词。诊断顺序见 SKILL.md 6.2 第六节。

**产物**：工作目录 `_art_rebuild/ui_refix5/`（manifest、cand x10、fit x10、`verify_candidates.py`、
`align_fix.py` 本地对齐兜底、compare.png x5、备份 x5、`UI_REFIX5_REPORT.md`）；
工程提交 `7e89007`（素材 + 缩略图 + 对照页）+ `97375d4`（流水线状态）。
替换后**对照页里这 5 件的缩略图必须一起重生成**（否则页面还是旧图）。

