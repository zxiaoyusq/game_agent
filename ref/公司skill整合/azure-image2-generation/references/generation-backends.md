# 外部生图后端操作参考

仅在当前任务实际选择脚本/API后端时读取。原生工具、是否调用付费后端及任务路由以 [总入口](../SKILL.md) 为准；只写提示词不需要读取密钥。以下命令以技能根目录为工作目录。

参数和实测数据来自现有脚本与历史本地记录，不代表所有原生工具或当前服务都相同。保留原操作细节供既有管线使用，不把它们注入普通视觉提示词。

**模型档位与美术风格解耦：**“精修动画3D”是绘制风格，不自动表示用户要求升级模型档位。`gpt_image.py`会按提示词触发词推断档位，因此外部调用应依据用户的质量/成本要求显式设置 `--tier standard` 或 `--tier advanced`，避免风格词误触发。模型、质量与尺寸不写进纯美术描述以代替真实工具参数。

## 后端与模型分档

| 档位 | 后端 / 模型 | 何时使用 |
|---|---|---|
| **标准档（默认）** | HiModels `gpt-image-2.5-flare` | 日常素材、批量出图、草图探索、UI 稿、图标 —— 一切常规生图 |
| **进阶档** | HiModels `gpt-image-2.5-sunburst` | 用户说「生成大图 / 精修 / 高清化 / 高精度 / 定稿图 / 关键视觉」等进阶需求 |
| **备用档** | Azure OpenAI `gpt-image-2` | **仅当 HiModels 不可用**（网关故障/额度问题）时显式 `--backend azure` 回退 |

**切换判据（必须遵守）：**

1. 用户明确说「生成大图 / 出大图 / 大尺寸 / 精修 / 精细修 / 高清化 / 超清 / 高精度 / 写真级 / 商业级 / 定稿图 / 关键视觉」等词 → 传 **`--tier advanced`**（sunburst）。
2. 其余一切情况 → 不传 `--tier`，默认走 **flare**。
3. 需要临时用别的模型 → `--model <完整模型名>` 覆盖一切。
4. 2.5 系走 `xhigh` / `max`：显式传 `--quality xhigh`（或 `max`），与 `--tier` 组合使用；注意 sunburst+max 实测 263s 起步且方差大（有 420s 超时先例），批量任务慎用，留给定稿单张。

脚本内置同样的触发词自动检测（prompt 里出现「生成大图/精修/高清」会自动升档并在日志打印 `触发词: xxx`），但**不要依赖它代替判断**：该显式传 `--tier advanced` 时就显式传。

> 默认后端 **不传 `quality`**（交服务端决定）；Azure 备用后端沿用历史默认 `quality=low`。

## 使用前：确认 API Key

**默认后端（HiModels）** —— key 解析顺序，脚本自动完成：

1. `--api-key` / `--key` 参数
2. 环境变量 `HIMODELS_API_KEY`（兼容 `HIMODELS_API_KEY_LINSHENG` / `_HONG`）
3. `~/.dsh/.credentials.yaml` 的 `refs` 段（同上三个名字，按序取第一个命中的）
4. `E:\hermes\.env`

**备用后端（Azure）** —— 老配置原样保留：`AZURE_OPENAI_API_KEY` / `_ENDPOINT` / `_DEPLOYMENT`（CLI > 环境变量 > `E:\hermes\.env` > `--html` 解析 > 内置默认 `https://aha-inhouse-eastus2.cognitiveservices.azure.com` + `gpt-image-2`）。

验证（只打印名字，不打印 key）：

```python
import re, pathlib
txt = (pathlib.Path.home() / ".dsh" / ".credentials.yaml").read_text(encoding="utf-8")
print("OK" if re.search(r"HIMODELS_API_KEY\s*:\s*\S+", txt) else "MISSING")
```

## 安全铁律（必须遵守）

1. **API_KEY 只能用于请求头，绝不写入** 报告、Manifest、日志、聊天回复、提交记录。
2. 记录接口配置只写 endpoint / model，不写 key。
3. 生图消耗额度：不要为了测试随意调用；批量任务先小样确认再放量。

## 网络与代理

- **HiModels（默认）**：公网 HTTPS，沿用系统/环境代理（Clash 等）。无需特殊设置。
- **Azure（备用）**：内网端点被 Clash fake-ip 劫持会出现 **WinError 10061**（2026-08-07 实测）。脚本已按后端分别处理：**azure 走直连（`ProxyHandler({})`），himodels 走系统代理**。自行调 Azure 接口时也要绕代理。
- **大响应截断**：sunburst 单张响应可达 1.8 MB，实测出现过 `IncompleteRead`（读到 1801348 字节、还差 11179）。脚本内置 **3 次重试（间隔 10s），覆盖 IncompleteRead / 超时 / 429 / 5xx**，无需手工重跑。

## Azure 安全系统拦截（仅备用后端，2026-08-07 实测）

Azure gpt-image-2 对人像写真类 prompt 有**随机性拦截**（同内容第一次成功、加修饰词后连续拒绝、猫图同尺寸秒过 → 内容级风控非账号级）：

| prompt 元素 | 结果 |
|---|---|
| 「金发美女特写照片，红唇，杂志写真风格，含情脉脉的看着镜头」 | ✅ 通过（1024 与 1152x2560 均通过） |
| 加「头顶留白」 | ✅ 通过 |
| 加身体部位词：「上半身」「胸前」「腰部」 | ❌ sexual 拒绝 |
| 加构图修饰：「特写构图」「占据画面主体」「完整入镜不被画面边缘截断」 | ❌ sexual 拒绝 |
| 加「亮片礼服」「无文字无水印」「时尚写真」等组合 | ❌ sexual 拒绝 |

**对策**：最小 prompt + 单变量加词；避免身体部位词，构图需求用「头顶留白」「人物完整」这类摄影语言；连续被拒≠封号，先用无辜 prompt 区分内容风控；生成后记得用 vision 检查效果。

## HTML 版参考（仅备用后端）

桌面版 HTML 工具（`C:\Users\Administrator\Desktop\AI生图工具-HTML版.html`）与 Azure 备用后端同源：HTML 在浏览器跑受 CORS 限制；请求参数 `quality=low`、`output_compression=100`、`output_format=png`、`n=1`；图生图 prompt 前缀与脚本一致；支持 Ctrl+V 粘贴与参考图排序。**默认走 HiModels 时与它无关**，仅在 `--backend azure --html <路径>` 时用。

## 透明底工作流（2026-09-22 实测，取代旧的「只能本地抠图」结论）

### 实测结论

| 实验 | 请求 | 结果 |
|---|---|---|
| **A** | flare + generations + `background=transparent` | HTTP 200，PNG **RGBA**；四角 alpha `[0,0,0,0]`；全透明 **44.5%**、实心（alpha≥250）**49.2%**、软边过渡 6.3% |
| **B** | flare + generations + **只在 prompt 里写「透明背景」** | HTTP 200，PNG **RGB（无 alpha）** → **光靠 prompt 拿不到透明底** |
| **E** | flare + **edits（带参考图）** + `background=transparent` | HTTP 200，**RGBA**；全透明 42.6%、实心 36.8%；服务端回执 `"background":"transparent"` |
| **F** | sunburst + generations + `background=transparent` | HTTP 200（首次响应 `IncompleteRead`，自动重试后成功），**RGBA**；全透明 29.1%、实心 59.3% |
| **C** | `gpt-image-2` + `background=transparent` | 180s 未返回（老模型不推荐承担透明需求） |

**结论：新模型（flare / sunburst）在 generations 与 edits 两条路径上都能直出真透明底。**
旧流程「先生成再本地 flood-fill 抠背景」**不再是必经步骤**，降级为**兜底手段**。

### 正确用法

```shell
# 素材/图标/贴纸/图集：直接要透明底（脚本自动做 alpha 质检）
python scripts/gpt_image.py \
  --prompt "扁平卡通风格的红色苹果图标，主体居中，不要底色不要投影" \
  --size 1024x1024 --background transparent \
  --out outputs/apple_icon.png

# 换皮/改图：参考图 + 透明底（edits 路径，实测同样返回 alpha）
python scripts/gpt_image.py \
  --ref assets/pad.png \
  --prompt "按原结构重绘材质，保持主体完整" \
  --background transparent --quality medium \
  --out outputs/pad_new.png
```

### 三条硬规则

1. **必须显式传 `--background transparent`**。prompt 里写「透明背景/transparent background」**不会**产生 alpha 通道（实验 B 证据）；参数才是开关。
2. **prompt 只负责"别画底色/别画背景投影"**（减少主体外围杂色与假投影），不承担 alpha 语义。
3. **alpha 由脚本自动质检**（`--background transparent` 时启用）：PNG 模式必须是 RGBA、四角 alpha ≤16、全透明像素 ≥3%、实心主体 ≥1%。
   - 达标 → 退出码 **0**，manifest 写入 `alpha_qa` 明细（gate: pass）。
   - 不达标 → 退出码 **3**，并提示本地兜底命令；确需放行可加 `--allow-opaque-output`（降级为告警，退出码 0）。
   - 出口 alpha 上限实测为 **254 而非 255**，故质检按 `alpha ≥ 250` 计「实心」，不要用 `==255` 判定。

4. **要「新的」内容就别给参考图**：`-r` 会复刻参考图内容，且当参考图是满幅构图时输出也会烤满底（实测全透明 0.0%）。详见换皮模块第 7 节。

### 兜底（仅当上面失败时）

服务端没给 alpha（模式为 RGB）或 alpha 质量差时，才回落到本地抠图。**必须分两步**（`--check-alpha` 是只读短路开关，与抠图合并调用会不写文件）：

```shell
# ① 抠背景（写文件）
python scripts/postprocess.py --input raw.png --output cut.png --remove-bg --tol 30
# ② 校验（只读，不写文件）
python scripts/postprocess.py --input cut.png --check-alpha
```

白底约 `--tol 30`，深色底约 `--tol 60`。实测：本地抠图路径的 alpha 上限是 **255**（接口直出是 254），两条路径的「实心」判定都按 `>=250` 计。

模型直出主体 alpha 上限常为 253-254（A==255 的像素为 0），下游若按 A==255 判不透明会整张误判，需要严格 255 时归一化：

```shell
python scripts/postprocess.py --input out.png --output out255.png --alpha-floor 250
```

## 核心用法

脚本在 `scripts/gpt_image.py`，零依赖（只用标准库；PIL 仅用于可选质检），用 `python3` 运行。

### 1. 文本生图（默认 flare）

```shell
python3 scripts/gpt_image.py \
  --prompt "一只戴耳机喝可乐的卡通猫，赛博朋克霓虹背景" \
  --size 1024x1024 \
  --out outputs/cat.png
```

### 2. 图生图（1 张参考图）

```shell
python3 scripts/gpt_image.py \
  --ref path/to/base.png \
  --prompt "把背景换成雪景，保留主体不变" \
  --out outputs/snow.png
```

### 3. 多参考图（图1主体 + 图2风格）

```shell
python3 scripts/gpt_image.py \
  --ref subject.png \
  --ref style.png \
  --prompt "图1是主体，参考图2的风格，把它改成一张电影海报" \
  --out outputs/poster.png
```

> 顺序即编号：第一个 `--ref` 是图1，第二个是图2，以此类推（也能写成 `--refs a.png b.png`）。

### 4. 进阶档（大图 / 精修）

```shell
python3 scripts/gpt_image.py --tier advanced \
  --ref old.png \
  --prompt "生成大图并精修此图，保持内容不变，提升到 4K 级细节" \
  --size 2048x1152 --out outputs/final_kv.png
```

### 5. 透明底素材

见上一节「透明底工作流」。

### 6. 备用后端（HiModels 不可用时）

```shell
python3 scripts/gpt_image.py --backend azure \
  --html "E:\AI生图\ai_image_tool.html" \
  --ref a.png --prompt "..." --size 1152x2048 --quality high \
  --out outputs/fallback.png
```

### 7. 智能尺寸（推荐）

不传 `--size` 或传 `--size auto`，脚本自动判断画幅：

| 判定来源 | 规则 |
|---|---|
| 关键词 | 提示词含"方图/头像/icon/1:1"→方图；"16:9/横屏/视频封面"→16:9；"9:16/竖屏/手机壁纸/小红书"→9:16；"横图/banner"→横图；"海报/竖图"→竖图 |
| 参考图1比例 | ≥1.55→16:9；≥1.1→横图；≤0.65→9:16；≤0.9→竖图；其余→方图 |
| 兜底 | 都识别不到 → 1024×1024 方图 |

### 8. 支持的尺寸

```
1024x1024  1280x720   2048x1152  2560x1440  3584x2016
720x1280   1152x2048  1440x2560  2016x3584
1536x1024  1024x1536
```

> `1152x2560`（9:20）在允许列表内，但未在 HiModels 实测清单中；显式指定时脚本会告警，被拒请改用 `1152x2048`。

### 尺寸硬约束（2026-09-22 实测，超出即 HTTP 400）

1. **最长边 ≤ 3840** —— `4096x4096` 报 `The longest edge must be less than or equal to 3840`。
2. **总像素有上限（约 8.3MP）** —— `3840x3840`（14.7MP）报 `Requested resolution exceeds the current pixel budget`；`3840x2160`（8.29MP）和 `2880x2880`（8.29MP）都通过。

**想要"最大尺寸"：** 方形取 **`2880x2880`**（正方形能过的最大值）；横图取 `3584x2016`；竖图取 `2016x3584`。再往上只能靠本地 LANCZOS 放大（见「后处理与规格化」的母版配方）。

## 参数明细

| 参数 | 缺省 | 说明 |
|---|---|---|
| `--prompt` / `-p` | 必填 | 提示词。图生图时可引用"图1/图2/图3" |
| `--ref` / `-r` | 无 | 参考图路径，可重复；顺序即编号（`--refs a.png b.png` 等价写法） |
| `--mask` | 无 | 编辑蒙版 PNG（与图1同尺寸；**透明区域=重绘区，不透明=保留**）；上游不吃该字段时自动去掉重试 |
| `--mode` | 自动 | `generation` / `edit`；不传则按有无参考图判定 |
| `--backend` | `himodels` | `himodels`（默认）/ `azure`（备用） |
| `--tier` | 无（=flare） | `standard`=flare；`advanced`=sunburst（大图/精修） |
| `--model` | 无 | 直接指定模型名，覆盖 `--tier` |
| `--background` / `-b` | `auto` | `transparent`=直出透明底并做 alpha 质检；`auto`=不下发该参数；`opaque`=强制不透明 |
| `--allow-opaque-output` | 关 | 要求 transparent 但未达标时仅告警（默认退出码 3） |
| `--size` / `-s` | `auto` | 见"支持的尺寸" |
| `--quality` / `-q` | 后端各自默认 | `low` / `medium` / `high` / `auto`；**2.5 系（flare/sunburst）额外支持 `xhigh` / `max`**（OpenAI 官方取值，2026-10-12 HiModels 实测 generations/edits 均通过：max 档 output_tokens 为 xhigh 的 2.2 倍、flare 耗时 ~33s→66s、sunburst ~133s→263s 且可能更久） |
| `--out` / `-o` | `gpt-image-<时间戳>.png` | 输出 PNG 路径 |
| `--api-key` / `--key` | 自动解析 | 覆盖 key |
| `--endpoint` | 仅 azure | 覆盖请求端点 |
| `--html` | 仅 azure | 从本地 `ai_image_tool.html` 解析 endpoint/deployment/key |
| `--timeout` | 600 | 请求超时（秒） |

**退出码**：`0` 成功 ｜ `1` 生成/网络失败 ｜ `2` 参数或 key 缺失 ｜ `3` 透明底未达标（alpha 门禁拦截）

## 接口细节（调试与自建脚本用）

### 默认后端：HiModels（`https://api.himodels.ai/v1`）

| 场景 | 请求 | 说明 |
|---|---|---|
| 无参考图 | `POST /images/generations` | JSON：`{model, prompt, size, n, output_format[, background][, quality]}` |
| 有参考图 | `POST /images/edits` | multipart/form-data：`model, prompt, size, n` + 图片字段（单图 `image`，多图 `image[]`，400 时脚本自动互换兜底） |

- 认证头：`Authorization: Bearer <HIMODELS_API_KEY>`
- 响应：`{"data":[{"b64_json":"..."}], "background":..., "size":..., "quality":..., "output_format":..., "usage":...}`；也兼容 `data[0].url`
- 实测耗时：flare 约 15–20s；sunburst 约 35s+（1024×1024 单次）
- 可用模型（`GET /v1/models` 实测）：`gpt-image-2`、`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst`、`gemini-3-pro-image`、`gemini-3.1-flash-image`、`gemini-3.1-flash-lite-image`
- 参考图模式的 prompt 由脚本自动包装：`参考图按上传顺序编号为图1、图2、图3……。请严格按照用户描述理解这些编号。用户需求：{user_prompt}`

### 备用后端：Azure OpenAI

- 文本生图 `POST /openai/deployments/{deployment}/images/generations?api-version=2024-02-01`，JSON 含 `output_compression:100`、`output_format:"png"`、`n:1`
- 图生图 `POST /openai/deployments/{deployment}/images/edits?api-version=2025-04-01-preview`，multipart，字段 `image[]`
- 认证头：`api-key: <KEY>`；响应同形，取 `data[0].b64_json`

## 请求大小与约束

- 参考图仅支持 **PNG / JPG / WebP**，单张 ≤ 50 MB
- 一次最多约 10 张参考图（接口以上传文件数为准）
- 输出固定 PNG；`--background transparent` 时才是带 alpha 的 PNG
- 透明底**没有任意长宽比规格**：接口 size 只有上面列出的几种。要求"尺寸/长宽比与参考图完全一致"时，选最接近规格 + prompt 强调"保持完整构图、不裁切"，再用 PIL 中心裁切/等比 resize 收口
- 图两侧被截断 = size 与原图比例不一致（如横图用方图）：换同比例 size

## 后处理与规格化（本地 PIL，不耗 API）

**透明背景不再是后处理步骤** —— 由 `--background transparent` 直接产出。`scripts/postprocess.py` 的角色是 **校验 + 兜底 + 规格化**（合并版已含旧版全部兜底参数，并保留「按 alpha 通道裁剪」的修复）：

```bash
# 校验 alpha（不写文件）—— 生成透明图后必跑（带 VERDICT 判定）
python scripts/postprocess.py --input in.png --check-alpha
# VERDICT: 真透明 OK      -> mode==RGBA 且四角 A==0
# VERDICT: 不合格 —— ...  -> 用 --remove-bg 兜底

# 兜底：仅在模型没给出真 alpha 时用（flood fill 从边缘抠纯色背景）
python scripts/postprocess.py --input in.png --output out.png --remove-bg --tol 30

# 规格化：裁掉透明空白 + 缩到目标尺寸
python scripts/postprocess.py --input in.png --output out.png --crop-trim --fit-max 2048
python scripts/postprocess.py --input in.png --output out.png --compress --close-size 8020
```

常用参数：`--check-alpha`（mode/尺寸/角落 alpha/透明占比 + VERDICT）、`--remove-bg`（兜底 flood fill，`--tol` 白底约 30、深色底约 60）、`--crop-trim`（**按 alpha 通道裁**）、`--fit-max N`（长边≤N，**只缩不放**）、`--height N` / `--width N`（同只缩不放）、`--resize WxH`（等比放进框，**可放大**，不变形）、`--alpha-floor N`（alpha≥N 置 255）、`--sharpen P`（UnsharpMask，放大后建议 40-70）、`--pad-canvas N`（居中贴 NxN 透明画布）、`--compress --close-size N`、`--paste-bg bg.png`、`--flatten COLOR`。

### 常用规格化配方："最大方形 + 固定母版画布"

母版约定示例：**4096x4096 透明画布、主体长边 3840 居中**。从 2880 原生（接口方形上限）走一遍：

```bash
python scripts/postprocess.py --input gen_2880.png --output out_4096.png \
  --crop-trim --resize 3840x3840 --sharpen 55 --pad-canvas 4096
```

**三个坑（都是实测踩到的）：**

1. **`--crop-trim` 必须按 alpha 通道裁，不能按 `Image.getbbox()`。** 模型直出的透明 PNG 里，背景像素常是「RGB 有值 + A=0」（实测 `(29,24,16,0)` 这类），而 `getbbox()` 看的是全部通道 → 返回整幅画布，一个像素都裁不掉（症状：输出尺寸和输入一模一样）。合并版脚本已按 alpha 通道裁；同一个坑也影响下游工具：**别假设透明区域的 RGB 是干净的**。
2. **`--fit-max` / `--height` / `--width` 只缩小、不放大**（语义是"不超过 N"）。要把 2880 原生放大到 3840 母版，必须用 **`--resize 3840x3840`**。
3. **放大后要配 `--sharpen 40~70`** 找回锐度。1.4x 左右的 LANCZOS 放大不补锐会明显发糊。

## 工作流提示

1. 判断是否有参考图 → 决定 `--ref` 是否传
2. 判断画幅（尺寸）——尽量让用户表达（手机壁纸=9:16，头像=方图，海报=竖图），也可直接交给 `auto`
3. 判断是否需要透明底（图标/贴纸/素材/图集/可叠加元素 → 是）→ 加 `--background transparent`，并检查退出码与 `alpha_qa`
4. 判断档位：用户说"大图/精修/高清/定稿" → `--tier advanced`
5. 运行脚本前**先检查 key**：无 key 就不要空跑
6. 完成后告知用户图片存放路径，并回报 manifest 里的 `model` / `tier` / `alpha_qa`

## 常见错误与修复

| 症状 | 原因 | 修复 |
|------|------|------|
| HTTP 401 / `auth_invalid_token` | Key 无效或未解析到 | 检查 `~/.dsh/.credentials.yaml` 的 `HIMODELS_API_KEY`，或 `--key` 显式传 |
| HTTP 400 提到 `image` | 图片字段名不被接受 | 脚本已自动互换 `image` / `image[]` 重试 |
| HTTP 400 提到 `quality` | 上游不接受该参数 | 不传 `--quality`（默认即不传） |
| HTTP 429 / 5xx / IncompleteRead | 限流、服务端错误、大响应截断 | 脚本内置 3 次重试（间隔 10s）；仍失败等 10-30s 手工重试 1-2 次 |
| DNS 解析失败 (getaddrinfo) | 网络临时中断 | ping 域名确认恢复后重跑 |
| 生成超时/极慢 | 网络出口质量差（详见换皮模块 6.2 节「网络出口诊断」） | `GET /v1/models` >5s = 链路慢；generations >300s = 换节点/换出口；并发 2 即可能被压垮，宁可串行 |
| 图两侧被截断 | size 与原图比例不一致（如横图用方图） | 换与原图同比例的 size |
| 文字错乱 | 中文 prompt 经 PowerShell 管道编码损坏 | 把脚本存成 UTF-8 .py 再执行 |
| 输出太小/变形 | resize 强制尺寸 | 用 --fit-max / --height 等比缩放 |
| 不需要球门/奖杯等残留元素 | 模型未严格遵守 | prompt 末尾显式加"不要出现XX元素" |
| UI 元素风格不统一 | 缺少风格约束 | prompt 明确"休闲游戏原画手绘风格/扁平简约卡通/与图X UI风格统一" |
| 该用 sunburst 却用了 flare | 没传 `--tier advanced` | 用户说"大图/精修/高清"时必须显式传 |
| 请求了透明背景但输出是 RGB | 模型/网关忽略了 `background` | 看脚本打印的 WARN 与 manifest 的 `background_effective`；兜底 `postprocess.py --remove-bg` |
| `background` 字段报 400 | 该模型/网关不支持该字段 | 脚本已自动去掉它重试一次；换用 `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst` |
| 透明图边缘有灰/白描边光晕 | prompt 没提透明，或还写着"白底/黑底" | prompt 明确"背景完全透明、不要黑底也不要白底、边缘不要背景色描边"后重跑 |
| `4096x4096` / `3840x3840` 报 400 | 超最长边 3840 或超像素预算 | 方形用 `2880x2880`，横图 `3584x2016`，竖图 `2016x3584` |
| 换皮/重绘后图片内出现成片纯黑像素或黑环 | `reskin_align.py` 默认 0.96 缩放 + 15px bleed：参考 alpha 超出 AI 主体 15px 以上的区域会露出 AI 透明区 RGB(0,0,0) | 先对 AI 做全量邻域填色（不透明真实内容为源，排除真黑），再做内容框 1:1 贴合 + `putalpha(原alpha)`；或 `--bleed` 加大并复检 |
| `gpt_image.py` 报 `unrecognized arguments: --filename` / `--out` 当目录用无效 | 混用了旧脚本 `azure_image2.py` 的参数风格 | `gpt_image.py` 的 `--out` 是**完整输出文件路径**（含文件名），无 `--filename`；旧脚本才是 目录+`--filename` |
| `subprocess` 报 `expected str, ... not tuple` | PROMPT 用了多行圆括号元组 `PROMPT = ("..", "..")` 直接传参 | 元组必须 `"".join((...))` 成单字符串后再传；模板复用时最容易踩 |

## 已知限制 / 经验教训（旧版实测沉淀，与上文互补）

1. **任意长宽比没有对应固定规格**：要求"尺寸/长宽比与参考图完全一致"时：生成选最接近规格 + prompt 强调"保持完整构图、不裁切"，再 PIL 中心裁切/等比 resize 收口。**中心裁切会截掉上下内容**；要"不裁切完整横幅"就改直接 resize。区分两类需求：`保持比例` vs `不裁切超宽`。
2. **多帧 GIF 参考**：GIF 首帧或抽象中间帧若元素缺失，改用**中间清晰帧**作唯一参考，并在 prompt 显式列举"必须保留的每个关键元素"。
3. **中文 prompt 编码 & 本机环境**：
   - `python` 通常不在 PATH：本机可用 `C:\Program Files\Python312\python.exe` 或 `E:\Migrated\Python\Python311\python.exe`（rebuild 管线示例用的后者）。
   - 用 `subprocess.run(..., capture_output=True, encoding="utf-8", errors="replace")` 且脚本开头 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，否则打印中文会 `UnicodeEncodeError: 'gbk'`。
   - 把中文 prompt 存成 UTF-8 `.py` 再执行；不要用 `> 文件` 重定向（默认 GBK 会乱码）。
4. **素材对齐技巧**：当用户要求"用我工程里的资源替换生成物"，把**真实素材文件作为参考图**传入 edits，并按颜色/名称在 prompt 里一一对应说明，让模型"照着画"而不是原创，比纯文字描述更可控。
5. **模型差异**：sunburst 更慢但细节/清晰度更好；批量任务全部用 flare，只对最终定稿屏单独跑 sunburst，避免整体耗时翻倍。**结构保持实测（2026-10-12，蒙版外像素漂移越低越好）**：sunburst 默认 32.7% → xhigh 22.7% → max 22.1%（xhigh/max 显著提升换皮一致性，验证官方「编辑精度推荐 sunburst」）；flare 默认 36.7% → xhigh 33.2% → **max 48.3%（反而最差，结构敏感任务禁用 flare+max）**。结构锁定换皮（第 8 节）重绘质量敏感时选 `--tier advanced --quality xhigh`。
6. **透明背景已原生支持（2026-09-22 实测）**：generations 与 edits 都可用；1024 / 2048 / 2880 各档位、flare 与 sunburst 均验证通过（透明像素占 45–59%，四角 `A==0`）。仍然要**校验而不是盲信**（`--check-alpha` / alpha_qa）；本地 flood fill 只是兜底。

## Manifest 记录（脚本自动生成）

两个主脚本都会产出 `IMAGE_<MODE>_MANIFEST.json`（输出目录旁），记录 backend/model/tier/mode/prompt/size/quality/background_requested/background_effective/alpha/response_echo/reference_images/output_path/elapsed_seconds/sha256 等字段；`gpt_image.py` 在 transparent 模式额外写入 `alpha_qa` 门禁明细（gate: pass/fail）。凭安全铁律：manifest 里**没有也不应有** key。

---
