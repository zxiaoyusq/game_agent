# 流水线细节 / gpt-image-gen

## 阶段 0 · 准备

1. 确认 API key（脚本自动解析，不必打印 key）：
   `%USERPROFILE%\.dsh\.credentials.yaml` 的 `refs` 段里有 `HIMODELS_API_KEY` 即可。
2. 确认生图脚本在位：`C:\Users\Administrator\.dsh\skills\gpt-image-gen\scripts\gpt_image.py`
   （`.dsh\skills` 是指向 `E:\Gameprogram\skill-pool\skills` 的 junction，两边等价）
3. 工作目录：默认 `<project>/_art_rebuild/<batch>/<id>/`；放项目内时脚本自动写 `.gdignore`。
   想彻底不碰项目就传 `work_root` 到项目外。

## 阶段 1 · 读原图（png_stats）

| 字段 | 用途 |
|---|---|
| size / mode | 目标尺寸、有无 alpha 通道 |
| transparent_pct | > 2% 且有 alpha -> 判为透明素材，走 transparent 生成 + bbox 适配 |
| corners | 原图四角是否透明；也是新图的门禁项 |
| content_bbox | alpha>8 的内容框；**适配的锚点**：新主体缩放到这个框的尺寸、并对齐它的中心 |
| bytes / md5 | 压缩基准、替换是否真的发生 |

## 阶段 2 · 定画幅 + 生成

- 画幅只能从 gpt-image 允许列表里挑（脚本 `pick_api_size`）：
  1024x1024 / 1536x1024 / 1024x1536 / 1280x720 / 720x1280 / 2048x1152 / 1152x2048 /
  2560x1440 / 1440x2560 / 3584x2016 / 2016x3584 / 1152x2560
  规则：比例误差 < 9% 才入选；在「面积 >= 目标面积」里选最小者（保证最后是**缩小**而不是放大）。
- 档位：面积 > 150 万像素自动升 `advanced`（sunburst，更贵更慢但细节够）；其余走 flare。
- 透明素材固定 `--background transparent` 且脚本会做 alpha 质检（退出码 3 = 不达标，自动重试）。
- `--ref` 用法：
  - 修复型（轮廓被切坏/要保持原设计）-> `use_ref: "original"`，prompt 里写「保持与原图完全一致的透视/构图/配色，补全被裁掉的轮廓」。
  - 换风格型 -> 传**已验收的成品**当风格参考，prompt 里写明「参考图只用于风格、材质、光照与配色，不要复制主体造型」。
- 候选数：默认 2 张（1 张修复型 + 1 张从零生成）；能一次过的简单素材 1 张即可。

## 阶段 3 · 适配（最关键的一步）

~~~text
候选(1024² RGBA)
  -> alpha 内容框裁切
  -> 等比缩放到「原图内容框尺寸」(fit=bbox)      # 保体量
  -> 中心对齐「原图内容框中心」，并夹紧在画布内   # 保占位
  -> 预乘 alpha LANCZOS 重采样                  # 防光晕
  -> 贴进原尺寸画布（透明底）
~~~

- `fit=full`：不透明素材（背景/原画）整幅缩放，不做内容框对齐。
- `margin`（默认 1px）：锁死主体不许贴边。
- 结果写 `candN_fit.png`，尺寸必须 == 原图尺寸，否则安装阶段直接拒绝。

## 阶段 4 · 评审（compare.png）

- `compare.png` = 原图 + 各候选，棋盘底 5x 放大并排。
- 不合格判据：主体被裁/变形、风格漂移（配色、光照方向、材质语言不一致）、
  透明底有白边/黑边、细节糊成一团（缩到 96px 认不出）、出现了多余元素（文字、地面、投影、多主体）。
- 不合格 -> 改 prompt 重生成，不要靠后期硬修（外轮廓靠模型改不回来）。
- 批量时建议**先出 1~2 张定稿风格**，用户/你自己确认后再整批跑，避免整批返工。

## 阶段 5 · 安装（备份 -> 压缩 -> 门禁 -> 替换 -> 引擎重导）

1. 备份 `ORIGINAL_<原文件名>`（已存在则保留最早那份）。
2. 无损压缩：PIL `optimize=True, compress_level=9` 与 ImageMagick `-strip -define png:compression-level=9` 各出一份，取更小者
   （实测 PIL 通常更小；两者都必须先通过**逐像素一致**校验）。
3. 覆盖同名文件 -> 复算尺寸/alpha/内容框/字节数 -> 跑门禁表 -> 写 `state_install.json` + `report_install.md`。
4. 引擎侧：
   - Godot 编辑器**在运行** -> 等它文件系统扫描（.godot/imported/*.md5 里的 source_md5 变成新值即完成）；
     等不到就提示用户点一下 Godot 窗口（聚焦即扫描）。
   - 编辑器**没在运行** -> `godot --headless --path <project> --import`，校验退出码 + md5 更新。
   - 注意：编辑器在跑时**不要**再起 headless 实例去导同一个项目，避免 .godot 缓存竞争。

## 失败模式与处置

| 失败 | 处置 |
|---|---|
| gpt-image 退出码 1 | 网络/网关问题，`--retries` 已重试；仍失败就换 `--tier standard` 或稍后再跑 |
| generations 超时 / 0 产出（900s 级）| **先查网络出口**：`/v1/models` 秒级响应但单张 generations >300s = 链路问题，换节点；见 SKILL.md 6.2 第六节与本文附三 |
| 轮廓对但主体偏（alpha 逐字节相同）| 走 SKILL.md 6.2：`fit=bbox` + `alpha=original` + 主体框残差门禁；不要只用 `reskin_align.py` 的质心对齐（质心相等 != 内容框对齐）|
| gpt-image 退出码 3 | alpha 质检不过：prompt 里加强「纯透明背景、无投影」，或检查是不是被要求画了不透明满幅 |
| 找不到匹配画幅 | 目标长宽比太极端：加 `allow_upscale`，或先确认这个素材真的该按原比例重绘 |
| 压缩后像素不一致 | 拒绝写入；换回 PIL 结果或检查是否有 CMYK/调色板模式干扰 |
| 尺寸不一致 | 拒绝写入；说明原图在流程中间被改过，重新跑阶段 1 |

## 回滚

每个 item 的目录里都有 `ORIGINAL_<原文件名>`。回滚 = 把它复制回原位并重新导入。
批量回滚可以直接照 `state_install.json` 逐条还原（该文件记录了 target 与 backup 的完整路径）。

## 批处理协议（建议）

1. 按**素材家族**分组（同一类图标一组、同一屏 UI 一组、背景原画一组），每组先出 2~3 张看风格是否稳定。
2. 每组用**同一** `style` 与同一 `notes` 语境；跨组之间只改主体描述，不改风格块。
3. 单次批量建议 <= 10 张（一次 API 调用 15~40s，且人工看对比图有成本）。
4. `gen -> prepare -> 看对比图 -> install --godot` 四步走，任何一步中断都能靠 `--skip-existing` 续跑。
5. 每批结束留一份 `report_install.md` 作为交付凭证。

## 参考案例：橄榄枝古典书图标（2026-09-29）

- 目标：`jigsawcard-godot` 的 `assets/textures/954406831b3f4765b504e305a1496258c73608db2 1.png`（96x96 RGBA）
- 故障：alpha 外轮廓被矩形裁切，右侧搭扣/书口/右下书角被切平（mask 右侧是一条直线）
- 处置：`use_ref=original` + 「补全轮廓、保持原设计」的 prompt，2 个候选 -> 取"修图型"那张
- 结果：96x96 不变、四角透明、主体留白 8px；24404 B -> 14012 B（-42.6%），逐像素无损
- 引擎侧：Godot 编辑器自动重新导入（.md5 的 source_md5 更新、ctex 重生成）


---

## 附：图集（Atlas）切片专章（2026-09-29）

### 为什么旧流程必须改

| 风险 | 机理 | 实测 |
|---|---|---|
| 贴回切头去尾 | AI 输出主体有 5%~45% 尺度漂移、20~45px 位移，按原 Rect 硬贴就切坏主体 | 见 `selftest_atlas.py` 漂移仿真 |
| 图集失效 | 整图重绘会连 padding / 相邻格子一起改，运行时按 region 采样到错误像素 | combo.png(512²) 整图替换会改坏区域外 **508,858** 个像素 |
| 坐标本身就错 | 工程里的 `.atlas` 元数据与 PNG 实际尺寸不一致 | 45 个图集里 **30 个不可信**（597 个 region 大量越界） |

### 新流程的保证

1. **模型只在方框里作画**：mask 之外它无权改动；就算它无视 mask 整图重绘，我们也只收割目标矩形。
2. **区域外逐字节保留**：`outside_untouched` 门禁直接证明"图集结构不可能失效"。
3. **alpha 逐字节沿用原图**：轮廓、位置、抗锯齿边缘 100% 守恒（实测全图 alpha 完全重合、alpha 质量守恒）。
4. **像素级切片来源**：alpha 连通域算出的 bbox 天然在画布内；`.atlas` 元数据必须过体检（声明尺寸 == 实际尺寸 且 region 全在画布内），否则 fail-closed 拒绝。
5. **超采样**：窗口（如 469²）远小于 API 画幅（1024²），缩小回来等于超采样，边缘比原图更干净。

### 命令速查

```powershell
& $P $R atlas --target <页.png> --at X,Y --prompt '...' [--install]
& $P $R atlas --target <页.png> --rect x,y,w,h --prompt '...'
& $P $R gen --manifest batch.json ; & $P $R prepare --manifest batch.json ; & $P $R install --manifest batch.json --godot
& $P $R atlas --target <页.png> --at X,Y --alpha-from ai --prompt '...'   # 放弃几何保证，需人工复核
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--rect x,y,w,h` | - | 显式切片框，可重复；最可靠 |
| `--at X,Y` | - | 点选，取包含该点的 alpha 连通域真实 bbox |
| `--auto-index N` / `--auto-top N` | - | 按面积排序取切片 |
| `--atlas-file x.atlas` | - | 元数据路径，**必须过体检**；不过则拒绝 |
| `--allow-untrusted-atlas` | 关 | 明知元数据不可信仍要用（不推荐） |
| `--bleed` | 16 | 目标框外扩多少像素一起重绘（吃掉边缘杂色/光晕） |
| `--context` | 96 | 再外扩多少上下文给模型参考（不重绘） |
| `--alpha-from` | original | `original`=轮廓锁死（推荐）；`ai`=允许改轮廓（需人工复核） |

### 已知边界

- **非透明切片图集**：整页是一个大连通域（如 `bow.png`），alpha 自动切片会给出"不是透明切片图集"告警，此时必须 `--rect` 显式指定。
- **旋转的 region**（`rotate: true`）：元数据里标记旋转的切片需要先逆变换，当前不自动处理，请用 `--rect` 给正立框。
- **多页图集**：`--target` 传哪一页就只处理哪一页；跨页请分次处理。

---

## 附二：第 1 类资产（轮廓锁死）的正解 —— `fit=mask` + 邻域填色（2026-09-29 沉淀）

背景：`part_collection_item_*` 这类「猫从方块边缘探出头」的切片，原 alpha 轮廓的两耳之间
有窄缝、两侧还有抬起的小爪。用 `fit=bbox` 把新内容按原内容框铺满，再套原 alpha，
会出现三个连锁故障（本批实测全部踩到）：

| 故障 | 现象 | 根因 |
|---|---|---|
| **黑边描边** | 耳缘/轮廓一圈深色 | 原 alpha 的 1~249 过渡带只有 ~1270 像素；候选在该处的颜色是模型画的外描边，回裁后变成可见深色环 |
| **硬切平** | 耳朵顶部被一条水平线切掉 | 内容框顶部 `y=26` 而耳朵尖在处理中被抹平；按框铺满必然溢出安全区 |
| **不透明纯黑** | 大面积黑块（4000~7000 px） | `putalpha(原alpha)` 把「候选没盖到、但原图可见」的口袋填成不透明黑 |

### 正确配方

1. **`fit=mask`**：候选内容框等比缩到「原 alpha 安全区」（`alpha>24` 腐蚀 2px）之内、正心放置。
   扫描比例 0.99→0.30，取**第一个能完整装下**的比例（=最大可用尺寸）。主体 100% 落在安全区里，回裁时不切、不描边。
2. **`dilate_edge_rgb` 的颜色源必须排除真黑**：全透明像素的 RGB 常是 `(0,0,0)`（PNG 规范允许），
   若把它当源，漫延出去的就是黑块。判据：`alpha >= 250 且 非(亮度极低 且 无色偏)`。
3. **`dilate_into_mask` 填平口袋**：把颜色漫延到「原图可见但候选没盖到」的区域（band 给 160~300），
   否则这些口袋会被 `putalpha` 变成不透明黑。
4. **`clean_transparent` 只准归零 RGB，绝不准动 alpha**：写成 `out[m] = 0` 会把整行 RGBA（含 alpha）清零，
   于是「alpha 逐字节一致」门禁必然失败。正确写法 `out[:, :, :3][m] = 0`。
5. **alpha 门禁给容差**：PIL 编解码会引入 0~3 个像素、差值 1 的抖动，判据用
   `差异像素 <= 8 且 最大差 <= 1`，不要用 `array_equal`。
6. **黑块门禁用「最大连通域」而不是「黑像素总数」**：抗锯齿细线会有几百个孤立暗像素，
   真黑块是一个大连通域。判据 `largest_blob <= 该项阈值`（默认 400 px）。
   木质基座等**自然暗部**会把 blob 撑大，这类项要单独放宽阈值并在报告里注明。

### 三条 prompt 提示（这批实测有效）

- 参考图里的棋盘格区域**必须显式说明是「透明区、只有透明信息、不要画它」**，否则模型会把棋盘格当图案画进去。
- 第 1 类资产要**先讲清构图分段**（例如「上段 55% 两耳、中段 33% 脸、下段 12% 前爪扒边」），
  模型才会把主体放进原轮廓的范围内；只说「保持姿势」不够。
- 参考图透明区**不要预先填黑底**再喂给模型——那会被当成「黑色主体」照抄。

### 命令

```powershell
# manifest 里给该项加："fit": "mask", "alpha": "original", "mask_thresh": 24, "mask_erode": 2,
#                    "hole_fill": 300, "alpha_tol_px": 8, "alpha_tol_val": 1
& $P $R prepare --manifest m.json   # 出 cand*_fit.png + compare.png + 门禁指标
& $P $R install --manifest m.json   # 备份 -> 无损压缩 -> 逐像素校验 -> 覆盖 -> 门禁
& $P $R report  --manifest m.json   # 交付报告（per-batch 文件名）
```

### 「生效槽位」陷阱（卡背实例）

`BoardModel.gd` 的资源候选是**有序回退列表**：
`gp_card_back_reskin_hard_N -> gp_card_back_hard_N -> gp_card_back_reskin_N -> gp_card_back_<prefix>_N -> gp_card_back_normal_1`。
只替换后面的槽位，游戏里读到的仍是更早注册的 `reskin_*` —— 必须把新设计同步到**第一个命中**的槽位
（`_art_rebuild/repoint_cardbacks.py`，先备份再覆盖）。替换任何素材前先 grep 一遍引用点，确认没有优先级更高的同名资源。

---

## 附三：网络出口诊断与「轮廓对、主体偏」两类故障速查（2026-10-07 沉淀）

### A. 生图超时 / 0 产出：先查链路，别改提示词

| 出口 | `/v1/models` | `/v1/images/generations` | 结论 |
|---|---|---|---|
| 旧链路 | 8.9s | 388~680s，或 900s 超时；两并发作业各 2 轮全失败、26 分钟 0 产出 | 链路问题 |
| 新加坡节点 | **1.6s** | **47s 返回 200**，单张 60~77s 稳定出图 | 正常 |

判别顺序（别跳步）：
1. `GET /v1/models` 耗时：秒级 = 链路通；>5s = 链路本身慢；
2. 单张 generations：<90s 正常 / 90~300s 网关排队可等 / **>300s 或超时 = 换出口**；
3. 并发：本环境实测**并发 2 个作业就会被压到超时**，宁可串行（逐件跑）；
4. 复现：用 urllib 直连探测（见下），别拿 CLI 反复试。

```python
# 直连探测：先 /models 再一张小图，两个数就能定性
import json, time, urllib.request
key = "<HIMODELS_API_KEY>"
def probe(path, payload=None, timeout=150):
    req = urllib.request.Request("https://api.himodels.ai/v1" + path,
        data=json.dumps(payload).encode() if payload else None,
        method="POST" if payload else "GET")
    req.add_header("Authorization", "Bearer " + key)
    if payload:
        req.add_header("Content-Type", "application/json")
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, round(time.time() - t, 1), len(r.read())
print(probe("/models", timeout=60))
print(probe("/images/generations",
            {"model": "gpt-image-2.5-flare", "prompt": "a red apple",
             "size": "1024x1024", "n": 1}, timeout=150))
```

### B. 「轮廓对、主体偏」的诊断与两种修法

```python
same_alpha = (ours[..., 3] == orig[..., 3]).all()   # True => 走内容框重对齐（不是重画轮廓）
sub_box    = bbox(detect_subject(ours))             # 画上去的图案
ref_box    = bbox(orig[..., 3] > 16)               # 原版内容框
residual   = max(abs(sub_box[i] - ref_box[i]) for i in range(4))   # 阈值 <= 4px
```

- **修法 1（重生成，推荐）**：`use_ref=original` + `fit=bbox` + `alpha=original`，候选 2 张；
  门禁 = size_same + alpha_identical + `subject_box_residual <= 4` + `dark_blob_in_visible`（报数，纯黑矩形块 = 缺陷）
- **修法 2（本地兜底，秒级）**：算出把 `sub_box` 仿射到 `ref_box` 的 `(sx, sy, tx, ty)`，
  **预乘 alpha** 后仿射 RGB，再 `putalpha(原 alpha)`。只治位置/尺度，**不治题材**。
- 两法共同注意：**替换后该素材在对照页里的缩略图必须一起重生成**，否则页面上看到的还是旧图。

实测记录（jigsawcard 5 件，2026-10-07）：alpha 全部与原版逐字节相同；主体偏移 5~77px、尺寸偏差 6~11%；
修法 1 把 5 件全部压到 IoU=1.000、主体框残差 0~4px；**选稿第一指标是可见区黑斑量**
（对话框候选 1 有 77,106px 纯黑矩形块 -> 弃，改选 1,173px 的候选 2）。

