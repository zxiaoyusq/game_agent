# 图片后处理（生图后 → 游戏可用资产）

> 来源：GameArtAgent（`E:\Gameprogram\PLAYFORGE-全套-2026-08-05\美术AI自动化生产`）的 postprocess / qa / delivery 阶段提炼。
> 目标：把"AI 生图 PNG"加工成**程序可直接用**的成品（透明底、精确尺寸、无背景残留、可追溯）。

## 1. 品红底约定（生图时就为后处理铺路）

- **透明底资产**：edit 模式 prompt 强制要求画在 **#FF00FF 纯品红**背景上（`solid magenta background #FF00FF`）
- 品红是游戏美术几乎不用的颜色，色键抠图可靠；纯文本生图（generation）则要求模型输出透明 PNG
- 任何"ML 真抠图"（如 BiRefNet）在许可证/基准核验前**禁止宣称**，只用确定性启发式

## 2. 管线（顺序固定）

```
色键抠图(#FF00FF) → 烘焙背景移除(白底/棋盘格) → alpha bbox 裁切
→ contain-fit 缩放(带 padding) → 透明画布居中合成 → 输出精确尺寸 PNG
```

非透明资源走分支：**cover-fit 居中裁切** + alpha 强制 255（防模型返回带透明洞的 RGBA，程序场景露出棋盘格）。

## 3. 色键抠图（chroma key）

判据（numpy 向量化）：

```
broad pink: A>10 且 R>150 且 B>150 且 |R-B|<110 且 G*100 < min(R,B)*70
strict pink: A>10 且 R>220 且 G<120 且 B>220
```

关键点：
- 只用 `R+B>3G` 会误杀红色蝴蝶结、棕色头发（暖色主体）→ 必须加 R/B 同时高且接近的约束
- **四边 BFS 洪泛**只删与画布边缘连通的品红；主体内部孤立品红像素单独用 strict 判据清理
- 顺序：先洪泛 broad → 再清 strict 残余

## 4. 烘焙背景移除（白底/棋盘格，画进不透明像素的背景）

**只分析画布边缘可达的不透明像素**，绝不因主体内部"长得像背景"（白高光/白字符细节）而删除。

- 边缘不透明像素中中性色占比 <70% → 不处理（有主体触边，放弃）
- **白底判据**：中性色亮度中位数 ≥230 且 极差 ≤28
- **棋盘格判据**：两档明显分离的中性色（极差 ≥28），score = 中性占比 × 两档平衡度 × 分离度 ≥ 0.05
- 候选像素判定：白底 = 亮度 ≥ max(220, 中位数-18)；棋盘格 = 亮度距两档 ±14 内（**纯白 255 排除**，防主体内白细节成为洪泛桥）
- **SUBJECT_TOUCHES_BORDER**：边缘有不属于背景的实心像素 → 整张不改动（fail-safe，交人工）
- 删除后 alpha 做 2px 高斯模糊 feather

## 5. alpha bbox + contain-fit + 居中合成

```python
# 可见区域：alpha > 10
bbox = alpha_bbox(img)          # 无可见像素 → None（异常告警）
img = img.crop(bbox)

# contain-fit：等比缩放到 (目标尺寸 - 2*padding)
effective_padding = min(padding, max(1, min(tw, th) // 10))  # 小控件自适应缩边距
scale = min(avail_w/sw, avail_h/sh)   # LANCZOS

# 特判：目标宽高比 ≥4 的细长 UI（进度条/分隔线）且素材比例远小于目标
# → 直接拉伸适配，否则等比 contain 会被高度约束缩成一个点
img = center_on_canvas(img, target)   # 透明画布 alpha_composite
```

## 6. 九宫格检测（nine-slice，零 AI 纯像素分析）

对 button/panel 类控件自动测可拉伸边距：
1. **alpha 透明边距**：四边 alpha<10 的行/列宽（该行 <10% 不透明即算边）
2. 全为 0 时用**纯色边距**：边中心参考色，行内颜色偏差 >15 即停
3. 都测不到 → 分类默认值兜底：button 4px、panel 12px、icon/background/text_label/decorative 不需要九宫格
4. 边距上限 40% 图片尺寸（防过度裁切）

## 7. 自动 QA（像素级，纯规则不调 LLM）

| 检测项 | 阈值（workflow.yaml 默认） |
|---|---|
| strict pink 残留（R>220,G<120,B>220） | = 0 |
| broad pink 残留 | ≤ 50（LLM 复核区间 30-100） |
| 边缘连通粉残留 | = 0 |
| 可见主体占比 occupancy | ≥ 0.3（细长控件/小图标不强制） |
| 棋盘格残留 score | ≤ 0.05 |
| 烘焙白底占比 | ≤ 0.03 |
| 尺寸 | 与规格**精确一致**（tolerance=0） |
| alpha 通道 | transparent=true 必须 RGBA |
| 来源 manifest | provenance 必须匹配（azure_gpt_image2 或 selected_concept_crop） |

决策三档：ACCEPTED / NEEDS_FIX / REGENERATE。NEEDS_FIX 进 repair（最多 2 次），REGENERATE 回 image_gen（最多 3 次）。

## 8. 视觉 QA（LLM 复核，抽查 20% + 全量）

6 项清单（输出 JSON `{pass, issues, confidence, details{...}}`）：
1. 粉残留：#FF00FF 残留即失败
2. 透明度：alpha 是否正确
3. 主体完整：是否被裁切
4. 主体占比：清晰可用、无过度留白
5. 边缘干净：锯齿/毛刺/彩色光晕/缺损即失败；**正常抗锯齿的 1-2px 半透明是正确 alpha，不得误判**
6. 语义准确：预期主体是否为唯一主要对象；建筑/道路自带的小地基、台阶、灯、植物属可接受装饰，只有大型独立次要主体/整段场景上下文才算无关物体

## 9. 输出物与交付

- **contact sheet**：每资产 4 种底预览（white/dark/checker/in-context）供人工 checkpoint 审查
- **文件名规范化**：非法字符/空格→`_`、连续下划线压缩、去首尾 `_. `、Windows 保留名（con/prn/aux/nul/com1-9/lpt1-9）加 `_` 前缀、stem 超长截断、空名兜底 `asset`
- **交付包**（delivery/）：
  - 成品 PNG（processed/ 原样）
  - `MANIFEST.json`：sha256 / 字节数 / 尺寸 / 用途
  - `README.md`：**资产用途与来源表**（文件/分类/用途/来源/尺寸/尺寸依据/使用场景）+ **程序字清单**（type=program 的文字：字号/颜色/位置，让程序代码渲染）
  - `DO_NOT_USE.txt` 说明
- **预检**：无 raw_generated 泄漏、无 rejected 混入、manifest 与文件数一致，未通过不得交付
- **来源追溯**：生图时写 `{stem}_*MANIFEST.json`（provenance 字段），后处理**必须随成品复制**该 manifest，否则 QA 判"来源缺失"进入无意义重生成循环

## 10. 后处理必读的避坑记录

1. 品红判据太松 → 暖色主体（红蝴蝶结/棕头发）整块缺失；太严 → 品红残留。用 §3 的双通道判据
2. 白底判据只扫边缘连通 → 主体内部白高光安全；不做边缘可达性判断 → 主体被打洞
3. 固定 20px padding 在 70px 高的按钮上只剩 30px 内容区 → padding 必须随目标尺寸自适应
4. 方图模型把长条控件画在方画布中央 → 细长目标必须走拉伸特判，否则缩成点
5. ML 抠图未经许可证核验时，enabled=true 必须 fail-closed（报错停止），不得静默交付白底图
6. 模型偶尔返回"透明洞"RGBA 当不透明背景 → 不透明规格强制铺白底再合成

## 11. 最小实现清单（零依赖 Pillow+NumPy）

色键（`remove_chroma_key`）→ 烘焙背景（`remove_baked_background`）→ `alpha_bbox` → `contain_fit` → `center_on_canvas` → `process_one`。全套在 GameArtAgent `tools/_postprocess.py`，可作为参考实现直接调用。
