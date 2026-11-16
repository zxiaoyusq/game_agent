# 素材与图集换皮管线

**优先分流**：用户要求面板、按钮等 UI 锁原轮廓时，只在原几何母版内部重绘材质，禁止先生成新形状再缩放/裁切/回贴 alpha；下文 bbox、inpaint、alpha 回贴仅在相关资产类型、真实契约和用户允许时使用。用户指定的效果图局部须实际作为生图输入；用户选定方案不得因技术缺陷而擅自替换。

实际选择工程换皮时读取；概念效果图不需要执行本管线。命令以技能根目录为工作目录。结构、动作、轮廓与alpha需锁定时，优先 [结构锁定换皮](structure-locked-reskin.md)。后端选择以 [总入口](../SKILL.md) 为准。

## 先按引擎分流

本文主体讲 **Godot / Spine / `.atlas`** 链路。不同引擎的取证手段与工具链不可互换：

| 引擎 / 载体 | 读哪份 | 关键差异 |
|---|---|---|
| Godot / Spine / `.atlas` | 本文（§1~§7） | `.tres` 切片、`Rect2`、`--headless --import` 重导 |
| 结构、动作、轮廓与 alpha 必须锁定 | [结构锁定换皮](structure-locked-reskin.md) | 通用原理，两边都适用 |
| **H5 / canvas（Phaser 2.x、纯 HTML5 + WebView 壳 APK）** | **不在本 skill** → `game-reverse-engineering` skill 的 **`modules/h5-canvas-reskin/`** | canvas 游戏、WebView 调试协议取证、图片可能是伪装的 WebP、没有文件级"重新导入" |

> **H5/canvas 换皮的完整方法（四类分流、平铺整条重绘、保明度换色、色相回锁、
> 四级层级量化、运行时卡死诊断、错误流程汇总）已并入
> `game-reverse-engineering` skill 的专用模块，本文件不再重复维护。**
> 本 skill 只保留**生图侧**要用的分流判断与提示词要点（§2、§3 的提示词部分）。

### 跨引擎通用、且最容易翻车的几条（生图侧要点）

1. **换色相会把亮度一起拉低** —— 症状像"alpha 丢了"，其实是亮度差。
   底板的「亮胶囊 + 暗图标」分布还会骗过中位数/跨度判据，需要**无条件分位点重映射**。
   （Godot 侧的对应门禁见本文 §6.2 的 `dark_blob_in_visible`。）
2. **多段平铺资源：文件序号顺序 ≠ 视觉顺序**。接缝自检若量错配对，会一直"很干净"而实机拼不上。
   **拼接类必须整条重绘再按原段高切回**，不要逐张独立重绘（§4.1）。
3. **玩法对象的功能色不能被地区配色覆盖**，动了色相必须回锁并量化验证。
4. **只写材质不写形状 = 模型保持原轮廓**；要换形状必须把**形状名词**写进提示词。
5. **复合图标要按 alpha 连通域个数识别并点名保留每个元素。**

> 以上 1、2 的完整流程与判据、以及"锁存标志导致输入永久锁死""补丁要显式可审计"
> 等运行时问题，见 `game-reverse-engineering` skill 的 `modules/h5-canvas-reskin/`。


## 换皮模块：图集/素材 reskin（2026-09-13 工业级 v3.0 升级）

**触发**：用户要求"素材/图集/贴图/背景 换皮、换色、重设计皮肤"，且要求**保持原尺寸、原 alpha 透明通道、atlas 信息不变，或对原画背景进行同构重绘**。

### 1. 资产双轨分流策略（Asset Taxonomy Routing）
开工前必须先对待换皮资产进行分类，严禁一套逻辑套所有资产：
- **A 轨：功能性 UI 控件、图标与 Spine 图集**（带透明通道、NinePatch、骨骼绑定点）：核心目标是**几何严密贴合、主体 100% 完整无截断、零死斑、高对比度防融底**；
- **B 轨：原画与全屏风景大图**（100% 不透明、叙事地貌、作为底层背景）：核心目标是**构图透视同构、类别级语义元素深度置换、精细度克制防干扰 UI**。

---

### 2. A 轨：功能 UI 与图集换皮六步法（解决三大死穴）

>  **2026-10-07 更正**：本节第  步的「质心对齐 + 回写原 alpha」**不能替代主体框对齐**
> 实测多件资产的 alpha 逐字节相同、主体却在轮廓内偏移 5~77px，回写 alpha 反而切出黑块。
> **修复已有错位资产请直接走 6.2**；本节仅适用于「新画一件放到空槽位」的场景。

#### 过去的三大历史翻车死穴与工业级解法：
1. **死穴 1：黑斑死斑（Black Fill）** ➔ PIL `convert("RGB")` 默认将透明底填纯黑 `(0, 0, 0)`，错位处直接 `putalpha` 强行拉满不透明度，产生数万像素刺眼黑死斑。**解法：在 `putalpha` 前执行 `cv2.inpaint` 边缘色彩漫延 15px（Edge Dilation），用边缘真实材质色填平空隙，黑斑彻底清零。**
2. **死穴 2：假吻合真切割（Element Truncation）** ➔ 生图模型对单体物品往往产生 **30%~45% 的尺度膨胀或 20~45px 的坐标漂移**。盲目贴回原图 Alpha 犹如“切菜断头台”，直接将偏大的书封底壳腰斩、光效偏心切断！**解法：自适应 Bounding Box 几何注册（Bbox Adaptive Fitting）与多象限质心解耦回正（Quadrant Center Alignment），先提取 AI 主体等比保形缩放并锚定回原图目标坐标，再做封装，保证元素 100% 完整展现。**
3. **死穴 3：循环论证伪自检（Fake QA Loophole）** ➔ 代码刚执行了 `putalpha` 紧接着只断言 `final.alpha == src.alpha`，永远判通过。**解法：建立黑斑检测（`black_fill_px == 0`）、内部未覆盖率（`missing_coverage <= 5%`）、轮廓交并比（`IoU >= 0.82`）三道真实硬防线，超标立即 FAIL 拦截重做。**

```
原图(如 96x96 图标 / 460x466 图集)
 ① 尺寸适配与居中 Pad（等比安全画布留白，mask 同步 pad）
 ② gpt_image.py --ref pad图 --background transparent --quality medium
    → 新模型直出带 alpha 的 PNG（2026-09-22 实测），脚本自动做 alpha 质检（退出码 3 = 不达标）
    prompt 必须含：材质关键词 + 严禁额外描边/外发光/霓虹
 ③ 自适应几何注册与象限质心对齐（Bbox Adaptive Fitting & Quadrant Centering）
    - 实体控件：自动抓取 AI 主体有效 Bbox，等比保形重采样至原图目标尺寸 (W, H)，原位贴入 (X, Y)
    - 多控件图集：按象限/Atlas 切片拆解，计算加权质心偏移向量 (dx, dy)，平移回正至正中心
 ④ cv2.inpaint 边缘色彩漫延防御（Edge Dilation 15px），填平边缘空洞
 ⑤ final.putalpha(原图alpha) 像素级严密封装
 ⑥ 严密 QA 闸门：尺寸匹配 + Alpha一致 + black_fill==0 + missing_coverage<=5% + IoU>=0.82
    任一项不合格直接判定 FAIL 并拦截丢弃，严禁交付
```

---

### 3. B 轨：原画大图与风景图【同类别同构语义重绘】

针对带有具体叙事构图、自然地貌与人文构筑物的原画/风景大图（如山谷风景、城镇成就插画）：

#### 三大同构重绘铁律：
1. **构图透视与引导动线拓扑同构（Compositional & Leading Line Homology）**：
   - 保留原画高机位/平视景深层次（前景 30% + 中景 40% + 远景 30%）；
   - 原画中引导玩家视线的线性动势（如斜坡铁轨、山脊线、河道），必须原位同构映射（如换为蜿蜒石板朝圣古道、溪谷小径）。
2. **类别级深度语义元素置换（Thematic Element-to-Element Replacement）**：
   - 现代工业交通（火车/汽车/游艇）➔ 目标文化交通（古代圣地商旅/朝圣者与驮货毛驴/加利利渔船）；
   - 现代电力通讯（木电线杆/铁塔/电缆）➔ 古代人文构筑（罗马引水石渠拱桥/界石/石堆 Cairns）；
   - 地表生态植被 ➔ 目标风貌植被（地中海粗壮盘根橄榄树林/金黄野麦/野百合）；
   - 天空远山 ➔ 目标神圣远峰与破晓黎明晨曦天光（Dawn Celestial Rays）。
3. **【关键铁律】精细度克制与 UI 可读性优先法则（Readability-First & Complexity Restraint）**：
   - **背景原画的第一要义是衬托 UI，绝不能喧宾夺主**！
   - 严禁盲目追求过度写实厚涂、高频碎石刻线与细碎噪点（否则叠放在上面的 UI 弹窗和控件会被背景杂乱纹理吞噬，导致严重视觉疲劳和融底）；
   - 必须采用**休闲插画大色块体块、简洁明朗的平涂/微渐变与大面积柔和空气透视（Clean Cel-shaded / Broad Flat Tones / Soft Ambient Gradients）**；
   - 让背景在视觉深度上主动“退后”，确保前景 UI 文字与按钮对比度始终 ≥ 4.5:1（WCAG AA）。

---

### 4. Mask 对齐与 Alpha 继承的五大深水坑与工业级 SOP（2026-09-14 沉淀）

>  **2026-10-07 补充**：本节的「双质心力矩对齐」仍有效，但**质心相等  内容框对齐**
> （质心对上了，主体仍可能整体偏移/缩放）。判据请用**主体内容框 vs 原 alpha 内容框**，见 6.2。

在实际移动端游戏换皮重制（如 JigsawCard 等项目）中，对齐 Mask 和处理 Alpha 通道曾踩过五大极其隐蔽的致命深水坑，必须严格执行以下工业级 SOP：

#### 坑点 1：异形互锁切片（Interlocking Shapes）的边缘形变与黑缝死穴
- **现象**：章节拼图盘的 25 块盖片（外三角、内三角、梯形、中心圆盘），具有严格数学解析曲率。若让 AI 直接生成带透明底的异形切片，AI 必然出现 5~20px 的轮廓扭曲、不对称边缘与毛刺，运行时拼接处出现无法消除的黑缝或锯齿重叠。
- **工业级解法【全画幅无界漫延 + 原始数学 Alpha 逐字节回裁】（Full-Bleed Texture + Mathematical Alpha Clamp）**：
  1. **严禁让生图模型负责异形外轮廓**！Prompt 必须指示生成无边界/大安全出血位（Bleed Margin ≥ 30px）的完整平铺材质纹理块；
  2. 后处理脚本提取原版切片的 **原始数学 Alpha 通道（100% 逐字节比对一致）** 作为硬掩模（Hard Stencil Mask），对 AI 生成的纹理大图进行像素级冲压裁切；
  3. 彻底杜绝 AI 轮廓形变，确保 25 块扇形与同心圆拼合时接缝达到 0 像素黑边、0 像素重叠。

#### 坑点 2：去背半透明抗锯齿边缘导致的“脏光晕 / 杂色外轮廓”（Halo & Fringe Artifacts）
- **现象**：模型直出的透明底（`--background transparent`）在半透明抗锯齿边缘（Anti-Aliased Edge）仍会混入底色杂色（刺眼白边圈或黑脏边）。直接回贴原图 Alpha 会把杂色压入边缘半透明像素中。
- **工业级解法【双重出血颜色漫延 + 预乘去边（Color Bleed Inpainting & De-fringing）】**：
  1. 在贴回原图 Alpha 之前，先提取 AI 主体的不透明核心区（Alpha > 200）生成核心掩模；
  2. 使用 `cv2.inpaint` 或形态学膨胀（Dilation 15~20px），让主体本身的纯净材质色彩向外漫延出血（Color Bleed）；
  3. 再贴回原图 Alpha。此时即使边缘存在半透明过渡，其采样的底层像素全部为主体真实材质色，杂色光晕彻底消除。

#### 坑点 3：Spine 骨骼动画与 UI 控件的“旋转轴心/质心漂移脱臼”（Bone Pivot / Centroid Drift）
- **现象**：Spine 动画切片（猫脸、手部指引、翻页书本）依赖固定几何中心或骨骼轴心（Pivot Point）进行旋转缩放。AI 生图常产生 15~40px 的重心漂移或主体尺寸缩放。若不做质心对齐，仅仅粗暴贴回 Alpha，会导致物理重心与旋转轴脱节，播放动画时出现“手臂脱臼、头部甩动偏摆”。
- **工业级解法【双质心力矩对齐与几何保形注册（Centroid Registration & Scale Normalization）】**：
  1. 计算原图与 AI 不透明像素的几何质心 $(C_x, C_y) = (\frac{\sum x \cdot A}{\sum A}, \frac{\sum y \cdot A}{\sum A})$；
  2. 计算重心偏移向量 $(\Delta x, \Delta y)$，对 AI 主体进行刚体亚像素平移回正；
  3. 依据有效包围盒计算缩放比 $s = \min(\frac{W_0}{W_{ai}}, \frac{H_0}{H_{ai}})$，等比缩放到原图安全区，严防“断头台式”截断。

#### 坑点 4：NinePatch 九宫格与大图集（UI Atlas）拉伸畸变与溢出污染
- **现象**：
  - **NinePatch**：按钮和行卡依赖边缘切片。若 AI 在中心区域绘制了方向性纹理或不对称高光，引擎拉伸时长宽失衡被拉成难看的横向长杠；
  - **UI/Spine 图集**：Atlas 内各切片间距只有几像素。整图生图，AI 锁不住区域坐标且会把 padding 一起改掉；拆成单图再回贴，AI 输出的主体又有 5%~45% 尺度漂移与 20~45px 位移，贴回原 Rect 就是"切头去尾"，运行时采样到错误像素 -> 图集失效。
- **工业级解法【原位局部重绘 + 只收割目标矩形 + 原 alpha 逐字节回裁】**（`scripts/rebuild.py atlas` 子命令已实装）：
  1. **NinePatch**：提示词强制"中心区域纯净均匀/单向水平微渐变，严禁中心绘制具体图案或强高光"，装饰只放角落；
  2. **图集**：不要拆图重绘再 Repack。改为把**整页（或目标周围一个窗口）+ mask（透明=重绘区）**喂给模型，让它只重绘那一块；产出后**只按原 Rect(+bleed) 抠出来贴回原图**，其余像素一个字节都不写，alpha 一律沿用原图。
     位置、轮廓、region 坐标、padding 全部由我们保证，模型只负责那一格内部的材质与风格 —— 它画歪了也只是那一格内部歪，**图集在结构上不可能失效**。
  3. **切片来源必须像素级可信**：`--rect`（显式）> `--at X,Y` / `--auto-index`（从 alpha 连通域算真实 bbox）> `--atlas-file x.atlas`（**必须先过体检**）。
     2026-09-29 体检本工程 45 个 spine 图集：**30 个元数据不可信**（声明页尺寸 ≠ PNG 实际尺寸，或 region 越出画布），
     直接用 `.atlas` 坐标收割会大面积命中错误区域，因此工具默认 **fail-closed 拒绝**，只接受能对齐的元数据。
  4. **越界检测**：安装门禁里 `regions_in_canvas` + `outside_untouched`（区域外逐字节一致）双保险。
---

### 5. 换皮自动化后处理与质心注册脚本（scripts/reskin_align.py）

>  **2026-10-07 定位**：本脚本适合「一整块新画面放进原轮廓」的场景。
> 若资产是**已存在且主体错位**，用 6.2 的流程（`fit=bbox` + `alpha=original` + 内容框残差门禁），
> 不要只用本脚本  它没有「主体框对齐」与「可见区黑斑」两项检查。

为确保上述 SOP 100% 落地、杜绝人为操作失误，换皮模块已内置自动化对齐工具 `scripts/reskin_align.py`：

```shell
python scripts/reskin_align.py \
  --src path/to/original.png \
  --ai  path/to/generated_ai.png \
  --out path/to/final_reskin.png \
  --bleed 15 \
  --mode auto
```

- `--mode auto`：自动计算原图与 AI 不透明像素的几何质心 $(C_x, C_y)$ 与有效 Bbox，执行亚像素平移与等比保形缩放，严防截断；
- `--bleed 15`：执行边缘色彩漫延防御（Inpainting 15px），消灭抗锯齿边缘白光晕与黑脏边；
- **全自动硬 QA 门禁输出**：实时打印尺寸、Alpha 逐字节、纯黑死斑、内部覆盖率（$\le 5\%$）、IoU（$\ge 0.82$）五项硬指标，任一不达标退出码为 1。
---

> **2026-10-13 实战警示（同一素材多花色换皮，五色连做验收通过）**：`reskin_align.py` 的 **0.96 缩放 + 15px bleed 存在系统性黑环**——参考 alpha 超出 AI 主体（缩到 96% 后必然如此）15px 以上的区域，会露出 AI 透明区 RGB(0,0,0)，`putalpha(原alpha)` 后即成数万纯黑死斑（实测 4.4~5.6 万/张，门禁正确报 FAIL 但工具不自愈）。**正解（已验收）**：① 生成前把原图等比 pad 到目标画幅（+6% 留白）；② `gpt_image.py` 双参考（图1=结构基准原图、图2=花色参考），prompt 明确"图1=结构/图2=仅取花色"分工并严禁改变轮廓/姿势/头身比；③ 后处理**不用 reskin_align 的 0.96 缩放**：生成体内容框与原图内容框 **1:1 贴合**（同姿态素材 bbox 天然对齐）+ 全量邻域填色（源=不透明真实内容，排除真黑）+ `putalpha(原alpha)`；④ QA：黑边像素从 5.6 万降至约 1300（残余为轮廓 AA 过渡），IoU=1.0、尺寸/alpha 逐字节不变。详见 `references/rebuild-pipeline.md` 附四。

### 6. 同尺寸 / 同命名 / 同透明语义的「重绘替换」流水线（2026-09-29 实装）

前 5 节解决「怎么对齐、怎么防黑斑」，本节解决**「批量重绘一批素材并原地替换回工程」**的端到端编排：
尺寸、文件名、alpha 透明语义一字不改 —— 生图 -> 适配 -> 硬门禁 -> 备份替换 -> 引擎重新导入校验。

**默认风格**：`mediterranean-casual-3d`（地中海古典配色 · 3D 立体 · 简约圆润可爱 · 色彩明亮）。
机读版 `scripts/styles.json`；人读版 `references/style-mediterranean-casual-3d.md`（含可直接复制的风格块、负面块、配色速查、按素材类型指引）。

```text
① 读原图      尺寸/模式/透明占比/四角/内容框(alpha bbox)/字节数/md5
② 定画幅+生成  按原长宽比挑 gpt-image 画幅(误差<9%) -> --background transparent -> N 个候选
③ 适配       候选内容框等比缩放到「原图内容框尺寸」+ 对齐原图内容框中心（预乘 alpha 缩放）
④ 看对比图     compare.png：原图 + 各候选（棋盘底 5x）
⑤ 安装        备份 -> 无损压缩(PIL vs ImageMagick 取小) -> 逐像素校验 -> 覆盖 -> 硬门禁 -> 引擎重导
```

**命令**（`scripts/rebuild.py`）：

```powershell
$P = 'E:\Migrated\Python\Python311\python.exe'
$R = 'E:\Gameprogram\skill-pool\skills\gpt-image-gen\scripts\rebuild.py'

# 单张：生成 + 适配 + 出对比图，先看不落地
& $P $R single --project 'E:\Gameprogram\jigsawcard-godot' --target 'E:\...\a.png' --prompt '一本画着橄榄枝的古典书…' --candidates 2

# 确认后复用同一份候选直接落地（--skip-existing 不重复调 API）
& $P $R single --project '...' --target '...' --prompt '…' --skip-existing --pick 1 --install

# 批量三步：gen -> prepare（离线）-> 看对比图 -> install
& $P $R gen     --manifest batch.json
& $P $R prepare --manifest batch.json
& $P $R install --manifest batch.json --godot

# 单张校验 / 引擎重新导入
& $P $R verify --target 'E:\...\a.png'
& $P $R godot  --project 'E:\Gameprogram\jigsawcard-godot' --target 'E:\...\a.png'
```

manifest 样例：`scripts/batch.example.json`；离线自测（13 项断言、不调 API）：`scripts/selftest_rebuild.py`。

**安装硬门禁**（任一不过即拒绝写入）：尺寸不变 / 命名不变 / 四角 alpha<=16 / 透明>=3% 且实心>=1% /
主体不出血 / 压缩后逐像素一致 / 体积不增 / 覆盖前已有备份 / md5 必须变化。

**以下六条仅适用于用户允许调整主体形状及内容框的资产，不适用于锁原轮廓 UI**：
① 绝不让模型负责外轮廓与尺寸 —— 候选先按 alpha 内容框裁切，再等比缩放到「原图内容框尺寸」并居中回原图内容框中心，
   模型那 5%~45% 的尺度漂移与 20~45px 位移被强制抹平，这是「不切断主体」的唯一保证；
② 缩放必须预乘 alpha，否则透明区黑像素渗进边缘 -> 脏光晕/白边；
③ 透明底靠 `--background transparent` 参数而非 prompt（prompt 里写「透明背景」不产生 alpha 通道）；
④ 工作目录放在项目内必须写 `.gdignore`，否则 Godot 会把候选图/对比图全导进资源库（脚本自动写）；
⑤ 先备份后覆盖、可回滚（备份在 `<work_root>/<batch>/<id>/ORIGINAL_<原文件名>`）；
⑥ 透明素材 fit=bbox，不透明原画/背景 fit=full。

**引擎侧重新导入**：Godot 编辑器**在跑**时靠窗口焦点触发扫描 —— 轮询 `.godot/imported/*.md5` 等 `source_md5` 变新；
编辑器**没跑**才用 `--headless --path <proj> --import`。不要两边同时导入同一个工程。

细节与失败模式：`references/rebuild-pipeline.md`；已落地案例与项目约定：`references/projects/jigsawcard-godot.md`。

> 修复「切图外轮廓被裁坏、形状被切平」的资产就是这条流水线：`use_ref=original`
> + 「保持与原图完全一致的透视/构图/配色，补全被裁掉的轮廓」。

#### 6.1 图集切片（Spine .atlas / UI Atlas）：原位局部重绘

图集的几何（region 坐标 / padding / bleed）**绝不由模型决定**。流程：

```text
① 定目标    --rect x,y,w,h  或  --at X,Y（点选：像素级从 alpha 连通域取真实 bbox）
② 取窗口    目标 rect + bleed(16) + context(96) 外扩 -> 调成 API 可用长宽比 -> 夹进画布
③ 建 mask   窗口内除「rect+bleed」外全不透明（保留）；透明区 = 允许重绘区
④ 生成      --ref 窗口图 --mask mask图 --background transparent + 「只重绘蒙版内这一件，位置/大小/朝向/透视与参考图完全一致」
⑤ 收割      AI 输出缩回窗口尺寸后，只按原 Rect 抠出来贴回原图，其余像素一字不写；alpha 一律用原图的（逐字节）
⑥ 门禁      outside_untouched(区域外逐字节一致) / alpha_identical / size_same / region_content_changed / region_not_emptied
```

```powershell
$P = 'E:\Migrated\Python\Python311\python.exe'
$R = 'E:\Gameprogram\skill-pool\skills\gpt-image-gen\scripts\rebuild.py'
# 点选目标（推荐）：给该物品在页内的任意一点，自动取它的真实切片框
& $P $R atlas --project 'E:\Gameprogram\jigsawcard-godot' --target 'assets\spine\combo\combo.png' --at 440,120 --prompt '把这块重新绘制成……'
# 或显式矩形（最可靠）
& $P $R atlas --target '该页.png' --rect 400,100,120,80 --prompt '...' --install
# 需要换物品形状时才用 --alpha-from ai，且必须人工复核
& $P $R atlas --target '该页.png' --at 440,120 --alpha-from ai --prompt '...'
```

- 元数据路径只在体检通过时才放行；不可信时工具直接拒绝并提示改用 `--at`。
- 窗口通常远小于 API 画幅（如 469² 窗口 vs 1024² 输出）= **超采样后缩回**，成品比原分辨率更干净。
- 自测：`scripts/selftest_atlas.py`（25 项断言，含"模型把东西画歪 23px 后图集依然逐字节完好"的漂移仿真与旧流程反证）。
- 取舍：alpha 锁定原图 = 轮廓不变、只换材质/风格。要换物品形状必须 `--alpha-from ai` 并人工复核该格。

#### 6.2 【2026-10-07 实证】「资产已存在、只是画错位」轮廓对齐修复法（替代旧的对齐脚本）

**适用**：素材已经在工程里、尺寸/命名/alpha 都对，但**画上去的主体在轮廓内偏了**（用户口径：
"没有按原版 alpha 通道轮廓生成、图案出现明显错位"）。

##### 一、先分清两种"错位"（判错就白干）

| 现象 | 判据 | 处置 |
|---|---|---|
| **真轮廓不同** | 我们的 alpha 与原版 alpha 相似度低（IoU < 1 或不逐字节相等） | 用 6 主流程：`alpha=original` 回写原 alpha |
| **假轮廓同、主体错位** | **alpha 逐字节相同（IoU = 1.000）**，但主体内容框与原 alpha 内容框有平移/缩放差 | **本节 6.2：内容框重对齐**（只改写 RGB，alpha 原样不动） |

实测（jigsawcard 5 件，2026-10-07）：5 件的 alpha 全部与原版**逐字节相同**，
但主体框偏移 5~77px、尺寸偏差 6~11%。所以"回写 alpha"这步根本没做错，**错的是没人检查主体框**。

##### 二、先量，再改（诊断三件套）

```python
#  alpha 是否真的不一致？ 决定走 6 还是 6.2
same_alpha = (ours[...,3] == orig[...,3]).all()      # 实测这 5 件都是 True

#  主体框 vs 原 alpha 内容框：偏移与缩放
sub_box  = bbox( detect_subject(ours) )   # 「画上去的图案」的包围盒
ref_box  = bbox( orig[...,3] > 16 )       # 原版内容框
offset   = center(sub_box) - center(ref_box)
scale    = size(ref_box) / size(sub_box)
```

`detect_subject`：在 alpha 内部，用**沿轮廓一圈的像素**当底色参考，
算色距 `dist > 45` 再开闭运算、取最大连通域  这样"图案"与"轮廓内留白"能分开。
实测偏移：Flower 下移 23px、effect_radar_search (-39, +77)px、banner 左移 16px、火苗上移 5px。

##### 三、标准修法（两条路，都要过同一套门禁）

1. **重生成路线（推荐）**：`use_ref=original` + `fit=bbox` + `alpha=original`（6 主流程）
   - `use_ref=original` 锁构图与配色；`fit=bbox` 把候选主体缩放到原内容框并对齐中心；
   - `alpha=original` 把原 alpha 逐字节写回。
   - 本轮实测：5 件  2 候选，**IoU=1.000 / 覆盖 100% / 脏透明 0**，主体框残差降到 0~4px。
2. **本地对齐路线（API 不可用时的兜底）**：`_art_rebuild/ui_refix5/align_fix.py` 思路
   - 用上面的 `detect_subject` 算出 `sub_box`，求把 `sub_box` 仿射到 `ref_box` 的 `(sx, sy, tx, ty)`；
   - **预乘 alpha** 后仿射 RGB（否则透明区颜色渗入边缘），再 `putalpha(原 alpha)`；
   - 零 API 成本、秒级；对"只是偏了"的资产足够（实测量完残差 1~4px：火苗 1px、banner 0px）。
   - 局限：**只治位置/尺度，不治题材**（对话框那件尺寸没错、是画面风格不对，路线 2 治不了）。

##### 四、门禁（比 6 多两项，缺一不可）

| 门禁 | 阈值 | 说明 |
|---|---|---|
| size_same | 必须 | 尺寸不变 |
| alpha_identical | 必须 | 与原版 alpha 逐字节相等 |
| **subject_box_residual** |  4px | **新增**：主体框 vs 原内容框四边最大残差 |
| **dark_blob_in_visible** | 越小越好（报数） | **新增**：可见区（alpha>200）内亮度<40 的像素量；纯黑矩形块=缺陷 |
| IoU / 覆盖 / 脏透明 | 0.82 / 100% / 0 | 沿用 6 |

实测选稿：黑斑量是第一判别指标  对话框 cand1 有 **77,106px 纯黑矩形块**（5.3% 可见区）、
cand2 只有 1,173px，选 cand2；困难横幅 cand2 26,371px vs cand1 4,433px，选 cand1。

##### 五、旧流程的 5 个 BUG（已弃用，别再照做）

| # | 旧做法 | 后果 | 新规矩 |
|---|---|---|---|
| 1 | 拿"回写原 alpha 后 `final.alpha == src.alpha`"当验证 | **循环论证**：alpha 是我们自己写回去的，必然通过 | 增加 `subject_box_residual` + `dark_blob_in_visible` 两项真实门禁 |
| 2 | 只做 `use_ref=original` 不改 `fit` | 主体 5~45% 尺度漂移、20~77px 位移直接固化进资产 | 仅在资产允许内容框配准和 alpha 回写时使用 `fit=bbox` + `alpha=original` |
| 3 | 拿**另一件**素材当参考图（如旁边那个图标） | 模型照抄参考图的位置/尺寸  主体偏到轮廓外 | 仅在用户允许原版作参考的修复场景使用 `原版真图`，并写明"同位置同大小同朝向" |
| 4 | 让小尺寸资产走满幅/放大生成 | 内容越界、黑斑 | 先按 alpha 内容框裁切  缩到内容框尺寸  居中回填 |
| 5 | 把"生图超时/0 产出"当成提示词或模型问题，反复改词重试 | 浪费 1~2 小时且必然失败 | 先做**网络出口诊断**（见下），链路问题就换节点 |

##### 六、网络出口诊断（本轮最贵的教训）

**同一批提示词，仅换网络出口，就从"必然超时"变成"1 分钟出图"**：

| 出口 | `/v1/models` | `/v1/images/generations` |
|---|---|---|
| 旧链路（无代理） | 8.9s | **388~680s 或 900s 超时**、26 分钟 0 产出、两个并发作业各跑 2 轮全失败 |
| 新加坡节点 | **1.6s** | **47s 返回 200**，单张 60~77s 稳定出图 |

判别顺序（照这个顺序查，别跳步）：
1. `GET /v1/models` 的**耗时**  秒级 = 链路通；>5s = 链路本身慢；
2. 单张 generations：**< 90s = 正常**；90~300s = 网关排队（可等）；> 300s 或超时 = **换节点/换出口**；
3. 并发上限：本环境实测**并发 2 作业就会被服务端压到超时**，宁可串行；
4. 复现命令：`python -c` 直连 urllib（见 `references/rebuild-pipeline.md` 附三），别用 CLI 反复试。

##### 七、速查

```powershell
$P = 'E:\Migrated\Python\Python311\python.exe'
$RB = '<proj>\_art_rebuild\rebuild_batch.py'
# 0) 判性质：alpha 是否逐字节相同（相同 -> 6.2，不同 -> 6）
# 1) 重建 manifest：ref=原版真图 / fit=bbox / alpha=original / candidates=2
& $P $RB gen     --manifest <mf>      # 生成候选
& $P $RB prepare --manifest <mf>      # 适配 + IoU/覆盖/黑斑
# 2) 用 verify_candidates.py 量 subject_box_residual 与 dark_blob，挑 pick
& $P $RB install --manifest <mf>      # 备份 -> 替换 -> 门禁
# 3) 该素材在对照页里的缩略图必须一起重生成，否则页面上看到的还是旧图
```

实测数据与脚本：`<proj>\_art_rebuild\ui_refix5\`（manifest / verify_candidates.py / align_fix.py / compare.png 5 / 报告）。

---

### 7. 新命名素材 / 游戏 Logo：文生图透明底与「参考图污染」铁律（2026-10-02 实证）

案例：为 `jigsawcard-godot` 重设计游戏 logo（6 个新英文名，v1~v5 共 5 轮 17 张）。结果 **只有 1 张全项达标**——文生图 + 短提示词 + `-b transparent` 的那张。失败高度集中在「烤底」与「多出 slogan 小字」，值得固化成规则。

**7.1 两条路径的分工**

| 需求 | 路径 | 原因 |
|---|---|---|
| 换**新名称 / 新构图 / 新内容** | **文生图，禁用 `-r`** | 给参考图（主页截图 + 旧 logo 裁切）后，模型直接重画了整张主页和旧品牌名「Jigsawcard Solitaire」；alpha 质检就算 PASS 也不能用，因为**内容被复刻**了 |
| **同名同布局**改字 / 改风格 / 改材质 | edits（`-r`） | 构图由参考图锁定，正是第 6、6.1 节的用法 |

**参考图污染**是本技能最贵的坑：`-r` 的语义是「照这张改」，不是「参考风格画一张新的」。要新东西就别给图。

**7.2 「参考图 + 透明底」的真相**（补充第 106 行实验 E）

实验 E 只证明 edits 路径**会返回 alpha 通道**，**不保证画面里有透明区**：本次 6/6 带参考图的输出全部烤满底（全透明 0.0%），因为参考图本身是满幅构图，模型照抄了满幅构图。
=> 成品需要四周留白/透明时走文生图；edits 只适合「主体本来就占满画布」的素材。

**7.3 提示词要短**（唯一达标那张的全部提示词，约 150 字）

```text
<风格锚点一句：3D 立体休闲游戏 logo + 3 个 hex 配色 + 质感词（圆润饱满、柔和棚光、干净通透）>
<元素一句：拼图块 + 基督教符号，拼图块要有 3D 软体积感>
主标题文字必须拼写完全正确、字重粗壮、带描边与柔和投影；下方一条金边丝带写小字副标题「SOLITAIRE」。
纯透明背景，无地面无背景板，除主标题与丝带副标题外不得出现任何其他文字、字母、数字。
主标题写「HOLY SOLITAIRE」；意象：……
```

把同样的要求展开成 6 条「铁律」清单后（v3），5 张里 3 张烤底 —— **约束越像清单，模型越当装饰**。保持两段、150 字上下。

**7.4 两大顽疾：slogan 与暗底**

17 张里 11 张被塞了英文 slogan 小字（`PIECES OF HOPE` / `SMALL PIECES. A BIGGER STORY.` 等），即使提示词明写「不得出现任何其他文字」。有效（非 100%）的禁用句：

```text
禁止地面、云、烟雾、光弧、背景板、光晕、口号标语、任何其他文字字母数字；整体保持明亮，禁止深色压底。
```

意象用词同样会诱发烤底：「圣火」「光芒」「天堂」「神圣光辉」容易生成光晕/圣光背景；换成**纯实体名词**（拼图块、十字架、白鸽、橄榄枝、翻开的书、竖琴）显著降低烤底率。

**7.5 重试纪律**

同一 prompt 方差极大：同一句话两次可分别得到「全透明 27%」与「0% 透明」。因此——
- 重试**先改词**（换掉可疑意象词、强化禁用句），不要原样复读；
- 2~3 次仍不过就**换构图思路或换方案**（本次 trinity_tiles 连败 6 次才止损）；
- 每次失败先确认是否已被失败版本覆盖原候选，覆盖前把上一版另存 `archive_*`。

**7.6 alpha 质检 PASS ≠ 可交付**

脚本门线只管四角与透明占比。**人工四查**：① 拼写（AI 标题常拼错/漏字）② 是否多出文字 ③ 是否多出背景/阴影 ④ 是否匹配目标美术风格。
经验阈值：**全透明 <10% 基本等于有底**（脚本 3% 门线适合图集切片，对整图 logo 偏松）。验收务必 `read_image` 打开原图逐字核对，别看缩略图。

**7.7 批量实操（Windows）**

- 批量生成放 pwsh 后台作业，并显式打印关键行，否则作业输出为空、失败静默：
  `... | Select-String -Pattern 'alpha 质检|已保存|生成失败' | Out-String -Width 180`
- **不要**用 `python -c` 写带嵌套引号的脚本（静默不执行、无报错）：落成 `.py` 文件再跑。
- 复核 HTML 对照页用 Playwright 时，本机未装 playwright 浏览器 -> `p.chromium.launch(channel="chrome")` 复用系统 Chrome；无头截图先确认 `document.images.every(i => i.complete && i.naturalWidth > 0)`。

**7.8 构图比例与槽位不匹配时：改槽位几何，不要逼模型改构图**（2026-10-02 追加实证）

案例：达标稿是 1380×1058（1.304，竖排堆叠：天使翼 + 四张 A + 金 3D 标题 + 丝带），而目标槽位是 957×398（实机显示 390×180，2.167 横幅）。等比装入只剩 199×169 —— 宽度只有旧素材的 56%。

于是试图让模型改画横幅，**4/4 全部烤满底**（唯一达标稿的提示词只改了意象句）：

| 做法 | 结果 |
|---|---|
| 文生图 +「横幅构图 / 宽约为高的 2.4 倍 / 丝带横贯底部」 | 透明 0.00%，四角 alpha 226–240 |
| 文生图 +「横向单行标题 + 双翼左右展开」 | 透明 0.00%，四角 216–240 |
| 最小改动版（删掉"横幅"字样，只把意象改横向） | 透明 0.00%，四角 236–245 |
| **以已达标透明稿为参考图**重画构图（edits） | 透明 0.00%，四角 19–30 |

=> 「横向铺开 / 横贯 / 宽高比」这类**构图指令是本技能最强的烤底触发器**（比"光亮/神圣"意象更猛）；参考图路线第 3 次被证不可用（见 7.1/7.2）。
**正解 = 保留已达标构图，改槽位几何**：

1. 先扫图集占用找空位（本次目标区域正下方 957×400 全空，可把区域从 398 拉到 700）；
2. 改槽位 `Rect2` 高度，**节点缩放 / 动画关键帧 / 代码里的 scale 常量一律不动** —— 它们是绝对值，改区域不牵连，**零代码风险**（本次未动一行场景/动画代码）；
3. 槽位在实机常是**非等比**显示（本次 x 0.4075235 / y 0.4522613）→ 图集内的贴入尺寸要**预补偿**：贴 937×647 → 实机 381.8×292.6（宽高比不变）；
4. 落位必须按**动画最大放大倍率**验算（本次呼吸动画峰值 ×1.04）：静止 260.3..552.9、峰值 254.1..558.5，与相邻 UI（章节牌中心带最早内容 y=574）留 15.5 px。

**7.9 「重绘替换」落地清单：六处接线点 + 三道验算 + 两项复验**（2026-10-02 实证）

图集区域一变，**六处必须同步**，否则重跑生成器或校验就会互相打架：

| # | 文件 | 内容 |
|---|---|---|
| 1 | `assets/ui_atlases/<x>.png` | 图集本体（区域内容重绘） |
| 2 | `assets/ui_slices/<page>/<name>.tres` | `region = Rect2(...)` 新区域 + `filter_clip` 保持 |
| 3 | `assets/ui_slices/<page>/<name>.png` | 单图切片（换皮管线的书账），同步重导出 |
| 4 | `data/*_atlas_regions.json` | 区域表 |
| 5 | `data/*_sprite_manifest.json` | `"size": [w, h]` |
| 6 | `tools/*_art_builder.gd` | 生成器的 `_slice(..., Vector2(display_w, display_h))` —— 按 **display ÷ scale 反算**（本次 390×316.58），否则重跑生成器会改掉缩放 |

三道验算（写入前跑，**全 PASS 才落盘**）：
- **区域外逐像素不变**：`ImageChops.difference(before, after).getbbox()` 必须完全落在新区域内（本次新区域扩大后依然 PASS）；
- **落位验算**：显示尺寸 = 区域尺寸 × 节点缩放，再乘动画峰值倍率，与**从截图量出来的相邻 UI 边界**比大小（不要凭肉眼估）；
- **透明/实心门线 + 区域四角 alpha ≤16**（整图 logo 的透明经验阈值仍是 <10% 即视为有底，见 7.6）。

两项复验（落地后跑）：
- `--headless --import` 退出码 0，且 `.godot/imported/*.md5` 的 `source_md5` == 新图 MD5（证明真的重导了）；
- 该页相关 QA 测试（本次 `test_home_motion` 18/18、`test_logo_loop` 6/6）。
- 回滚三件套：图集备份进 `_art_rebuild/.../atlas_backup/`、六处尺寸改回、再 import 一次。

---
