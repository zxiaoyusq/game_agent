# 结构锁定换皮

仅用于实际要求保持结构/动作/轮廓/透明切边的素材编辑。命令以技能根目录为工作目录；外部脚本/API调用仍遵守 [总入口](../SKILL.md) 的后端与授权边界，不因读取本参考就自动调用。

### 8. 结构锁定换皮：外观迁移（Structure-Locked Reskin，2026-10-12 实装 v1.5.0）

**触发**：用户要求「换皮/重绘材质/换配色/换花纹/换风格」，且明确要求**保持原图的结构、动作、轮廓、透明切边范围不变**——适用于一切带透明通道的 PNG（角色部件、spine 图集切片、UI 素材、图标、宠物/角色毛色迁移等）。毛色/花色迁移只是典型场景，本模块不是换毛色专用。

**定位（对旧流程的替换关系）**：旧换皮主流程（第 6 节）是「整件素材重绘换风格」，实测对原图结构遵循不够——形状漂移、丢浮动元素、轮廓对不齐。凡是**要求结构锁定**的透明素材换皮，一律走本模块；只有「整件重画、不要求结构不变」才用第 6 节；图集切片（6.1）仍走 harvest 原位收割。8 专门解决旧管线两大顽疾：

| 顽疾 | 根因 | 本模块解法 |
|---|---|---|
| 轮廓无法对齐 | 内容框对齐只解决整体偏移，形状漂移和「丢了浮动元素导致的错位」解决不了；reskin_align 的质心对齐同样不检查主体框 | **alpha 逐字节回写**（轮廓像素级由原图锁死）+ **两步内容框配准**（粗配准整体 → 精配准未保护区域） |
| 无法在原图基础上局部编辑 | API 的 mask 字段上游会忽略（gpt_image.py 里「去掉 mask 重试」就是证据）；atlas 的 harvest 只覆盖图集 | 「局部」由两层保证：**prompt 三层约束**（哪些不许动）+ **后端 preserve 回贴**（不变区域原图像素原样恢复，支持色键） |

> **分流优先级**：用户明确要求 UI 外轮廓、透明留白与拉伸结构不变时，不使用本参考中“先生成新主体、bbox 配准、强贴原 alpha”的后处理；应以原版几何母版直接重绘内部材质，检查完整 RGBA 与半透明边缘。下列 source/配准规则仅用于其适用的透明角色/部件工作流，且服从用户对参考输入和候选基准的明确要求。用户禁止原图作为背景参考或要求在选定候选上编辑时，不得强制输入原图或退回原图。

#### 8.1 参考图职责（铁律）

- **图1 = source（该角色/部件流程的原图；用户另有参考限制时按用户要求分流）**：结构基准，决定 WHAT AND WHERE —— 结构、姿态、比例、轮廓、五官、配饰、透明切边。alpha 最终**逐字节**来自它。
- **图2 = reference（外观参考，可选）**：只决定 APPEARANCE —— 配色、花纹位置与边界、材质质感、颜色过渡。给了图2 就从它迁移；**没给就用纯文字描述外观，两条路径的后端像素管线完全相同**。
- 有图2 时，**严禁**把它的形状、姿态、配饰（典型：参考图有铃铛而原图没有 → prompt 必须点名 `do not add a bell`）、表情、背景带进结果。
- **多候选/多花色纪律**：通常保持同一结构基准以降低漂移；用户明确选择已有候选作为后续编辑基准时尊重其选择，记录结构和目标偏差，不擅自切回原图。

#### 8.2 三层英文约束 prompt（脚本自动组装）

用户（或上游 Agent）只需给「外观描述行 + 必须保留的对象 + 禁止带入项」（forbid 项仅在有图2时有意义），`transfer.py` 组装成：

```
[LAYER 1 - STRUCTURE INHERITANCE]  Image 1 is the direct edit target...（结构/姿态/轮廓/配饰/透明切边逐一列举）
[LAYER 2 - FORBIDDEN CHANGES]      do not change... + Preserve the <对象> exactly as in Image 1... + do not add a bell
[LAYER 3 - APPEARANCE ONLY]        有图2：Image 2 is the appearance reference ONLY... map onto the EXACT original shapes；
                                   无图2：appearance is fully specified in words below（纯文字描述外观）
TARGET APPEARANCE DESCRIPTION:     <外观描述逐行>
```

实测写法要点：① 外观描述**按部位拆行**（眉/口鼻/胸/爪/尾尖/毛质/边界过渡），比一句「把颜色改成图2」效果好得多；② preserve 对象逐个点名；③ 参考图里有而原图没有的东西必须显式 forbid。`transfer.py prompt` 子命令可只渲染 prompt 检查（不调 API）。

#### 8.3 像素锁定后处理管线（每候选自动执行）

```text
① 粗配准   候选整体内容框 --fit=bbox--> 原图整体内容框（预乘 alpha 等比缩放）
② 精配准   在粗配准结果上，取「未保护区域」的内容框再对齐一次
           （模型丢了浮动图标时，整体内容框被缺角带偏；保护对象反正要回贴，锚定必须落在主体上）
③ 出血修补 原图可见但候选透明处，用候选材质色 cv2.inpaint 漫延（防黑斑死穴，需 cv2）
④ alpha 回写 原图 alpha 逐字节写回；透明区 RGB 清零（防脏透明）
⑤ preserve 回贴 不变区域恢复原图像素；支持色键（见 8.4）
⑥ QA 门禁  七项全过才算 PASS（见 8.5）
```

#### 8.4 preserve 色键（2026-10-12 冒烟实测出的坑）

**整块回贴会把矩形里对象周围的旧底色一起贴回来**：项圈叠在身体上时，项圈矩形内的原图棕色身体像素被贴到新灰色身体上 → 矩形接缝；矩形上缘盖住口鼻 → 米色残留带。所以：

- 对象**叠在会变色的区域上**（项圈/衣服/手持物贴身部位）→ **必须色键**：`x,y,w,h:R,G,B:tol`，只回贴矩形内颜色距离 ≤tol 的原图像素（tol 实测 90 可靠区分红项圈与棕身体）；
- 对象在**透明背景上**（浮动图标、独立贴纸）→ 整块回贴即可：`x,y,w,h`；
- spec JSON 写法：`{"rect":[x,y,w,h], "key":[R,G,B], "tol":90}`。

#### 8.5 QA 门禁（七项，任一不过即 FAIL 拒绝落地）

| 门禁 | 默认阈值 | 抓什么 |
|---|---|---|
| size_same / alpha_identical / preserve_identical | 必须 | 尺寸、alpha 逐字节、保护区像素级复原 |
| clean_transparent | 脏像素=0 | 透明区 RGB 残留 |
| no_missing_structure | missing ≤5% | 结构丢失（保护区域之外，原图实心处候选没画出来） |
| shape_deviation_ok | ≤8% | 主体形变度（精配准前后的比例差；模型把主体画变形/丢部件时会被撑大填框，此门禁拦截） |
| no_black_blobs | ≤0.5% 可见区 | 纯黑死斑（inpaint 失败兜底） |
| transfer_applied | ≥2% | 迁移量（可见区颜色变化占比；太小=模型没干活） |

阈值可调：`--gates gates.json`（键同上表）。**门禁只管像素层；毛色像不像、五官有没有走形仍需人工/视觉复核对比图**（compare.png，ORIGINAL 与各候选并排）。

#### 8.6 命令速查

```powershell
$P = 'C:\Program Files\Python312\python.exe'
$T = '<技能目录>\scripts\transfer.py'

# 全流程：生成 N 候选 -> 配准合成 -> QA -> 对比图（不落地）。外观描述行可重复
& $P $T run `
  --source 'dog.png' --ref 'coat_ref.png' `
  --appearance 'cool medium-gray and white coat with soft furry texture' `
  --appearance 'white fluffy eyebrow patches above both eyes' `
  --appearance 'white muzzle and chest patch; white paws and white tail tip' `
  --preserve-object 'small floating paw icon on the right' `
  --preserve-object 'simple brown collar' `
  --forbid 'bell' `
  --preserve-rect '88,124,84,26:200,44,44:90' `   # 项圈：色键限定
  --preserve-rect '206,6,50,50' `                # 浮动图标：透明背景整块回贴
  --candidates 2

# 只渲染三层约束 prompt（不调 API，检查用）
& $P $T prompt --source dog.png --ref coat_ref.png --appearance '...'

# 无参考图（纯文字描述外观）：去掉 --ref 即可，像素锁定管线不变
& $P $T run --source 'part.png' --appearance 'weathered dark iron material, matte finish, subtle scratches' `
  --preserve-object 'bottom-left rivet' --preserve-rect '12,210,40,40' --candidates 2

# 确认后落地（备份 -> 无损压缩 -> 门禁 -> 覆盖；--pick 缺省取第一个 PASS 的候选）
& $P $T run --spec spec.json --install --pick 1
& $P $T install --work '<work目录>' --pick 1 --target 'dog.png'

# 离线自测（31 项断言，不调 API）
& $P $T selftest
```

spec JSON 示例：`scripts/transfer.example.json`。work 目录默认在原图旁 `_appearance_transfer/<原名_时间戳>/`（prompt.txt / candN.png / candN_locked.png / compare.png / report.json / ORIGINAL_备份）。

#### 8.7 已验证记录（2026-10-12）

- `selftest_transfer.py` 31 项断言全过：三层 prompt 关键句（含无参考图分支不出现 Image 2）；换毛色+漂移候选全门禁 PASS 且 alpha 逐字节一致；丢浮动图标候选被 preserve 回贴救回（图标区域像素级复原、色键不贴回旧底色）；丢尾巴候选被 missing+形变双门禁拦截。
- flare 真机冒烟 2 轮（合成狗 256²，1024² 画幅生成）：第 1 轮全门禁 PASS 但目检发现**项圈整块回贴接缝** → 加色键后第 2 轮干净（missing 3.4%、形变 4.2%、迁移量 70.6%、零黑斑零脏透明）。真机端到端验证的是「有图2」路径；「无图2（纯文字外观）」路径只差 prompt 文案，像素管线相同，由自测覆盖。
- install 落地 + `rebuild.py verify`：尺寸/四角透明/内容框与原图一致，md5 变化，备份可回滚。

---
