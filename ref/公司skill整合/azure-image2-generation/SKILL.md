---
name: azure-image2-generation
description: "GPT生图（GPT-Image 生图/改图，合并版）：用户明确说『GPT生图』时必用。默认走 HiModels 网关的 gpt-image-2.5-flare（标准档）/ gpt-image-2.5-sunburst（大图·精修档）生成图片或基于参考图编辑，支持直出真透明底 PNG 并自动做 alpha 质检；Azure gpt-image-2 保留为备用后端。本 harness 无原生生图工具时，通用生图诉求（画图/海报/头像/文生图）也走本技能；若所在 harness 自带生图工具（Codex 的 image_gen、QwenWork 的 qwenwork_image_generate 等）必须优先用自带的，禁止调用本技能；若环境另装 comfyui 等生图管线，通用生图优先由其处理，本技能不抢触发。内置 17 大类 94 个结构化提示词模板（海报/UI样机/产品图/信息图/学术配图/技术图/漫画/头像/分镜/编辑等），写 prompt 前先检索模板。含换皮模块：用户要求『素材/图集换皮、换色重设计但保持原尺寸原alpha透明通道atlas不变』时也使用本技能的 reskin 管线。含「重绘替换」流水线：要求保持原尺寸/原文件名/原 alpha 透明语义不变，批量重绘素材并原地替换回工程（含备份、硬门禁、Godot 重新导入校验）时也走本技能的换皮模块；图集切片用「原位局部重绘(mask) + 只收割目标矩形 + 原 alpha 逐字节回裁」，位置与 region 坐标由原图锁定、不靠模型。含「结构锁定换皮」模块（transfer.py）：用户要求『换皮/重绘材质/换配色/换花纹/换风格，且保持原图的结构、动作、轮廓、透明切边范围不变』（带透明通道的 PNG、spine 图集部件、UI 素材通用；毛色/花色迁移只是典型场景）时必用——图1=原图锁结构（alpha 逐字节回写+两步内容框配准）、图2=外观参考（可选，没有则纯文字描述外观）、preserve 色键回贴实现原图基础上的局部修改、七项 QA 硬门禁。"
version: 1.5.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [HIMODELS_API_KEY, AZURE_OPENAI_API_KEY]
  commands: [python3]
metadata:
  hermes:
    tags: [gpt-image-2.5-flare, gpt-image-2.5-sunburst, himodels, gpt-image-gen, azure-image2-generation, GPT生图, azure-openai, transparent-background, alpha, image-edit, reskin, atlas, structure-locked-reskin, appearance-transfer, 结构锁定换皮, 外观迁移, 换皮, 提示词模板, prompt-template, 视觉模板, 海报, 信息图, UI样机, spine]
    related_skills: [comfyui, spine-animation-pipeline]
    category: creative
---

# GPT 生图（默认 HiModels · Azure 备用）

> **版本沿革**：本技能由池内旧版 azure-image2-generation（2026-09-22 实测沉淀）与 gpt-image-gen v1.4.0（Hermes Agent，2026-10-09）合并迭代而来 —— 以 v1.4.0 为主体（换皮/重绘管线 + 94 提示词模板 + alpha 门禁），保留旧版的适用范围硬规则、安全铁律、尺寸像素预算、后处理兜底参数与常见错误表。旧主脚本 `scripts/azure_image2.py` 因 spine-animation-pipeline 按路径直调而**原样保留**，新任务一律用 `scripts/gpt_image.py`。v1.5.0（2026-10-12）新增「结构锁定换皮」模块 `scripts/transfer.py`（外观迁移 + 像素锁定后处理，见换皮模块第 8 节），专治旧管线「轮廓无法对齐、无法在原图基础上局部编辑」两大问题，替换旧换皮主流程中要求结构不变的场景。

## ⚠️ 适用范围（先读这条）

**判断顺序（硬规则）：**

1. 先看当前 harness 有没有自带的生图/改图工具。**有 → 用自带的，本 skill 连读都不要读。**

| 你所在的 harness | 生图应该用什么 |
|---|---|
| **Codex**（自带 `image_gen`） | ✅ 用 Codex 自带的 `image_gen`。**禁止**用本 skill —— 会额外消耗用户的 HiModels 额度 |
| QwenWork（自带 `qwenwork_image_generate`） | ✅ 用 QwenWork 内置的媒体工具 |
| **DSH desk / 其他没有原生生图工具的 harness**（纯终端、纯脚本、文本模型 harness 等） | ✅ 用本 skill |

2. 没有原生工具时：用户**明确说「GPT生图」** → 直接走本 skill（见下「何时使用」）；用户只说「画一张/做海报/生成头像」这类通用诉求 → 若本环境另装了 comfyui 等生图管线则优先它们，**没有就也走本 skill**（DSH desk 当前未装 comfyui，通用生图默认落在本 skill，走标准档 flare）。
把用户的中文/英文需求变成图片。两条路径：

| 任务 | 场景 | 接口 |
|---|---|---|
| **文本生图** | 用户只给了描述，没有参考图 | `/images/generations` |
| **图生图 / 编辑** | 用户提供了 1 张或多张参考图，要求"以图1为主体、参考图2的风格" | `/images/edits` |

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

脚本内置同样的触发词自动检测（prompt 里出现「生成大图/精修/高清」会自动升档并在日志打印 `触发词: xxx`），但**不要依赖它代替判断**：该显式传 `--tier advanced` 时就显式传。

> 默认后端 **不传 `quality`**（交服务端决定）；Azure 备用后端沿用历史默认 `quality=low`。

## 何时使用

**唯一触发条件：用户明确说了"GPT生图"**（例如"用GPT生图做一张…"）。

- 用户明确指出使用 GPT 生图，且目标是通过 GPT-Image 出图
- 用户给了一张或多张图片，要求改背景、换风格、替换物体、加元素、做海报/头像/壁纸（前提：用户点的是"GPT生图"）

## 何时不用（避免与 comfyui 冲突）

**重要：通用生图请求默认归 comfyui，不要抢话。** 这类场景一律不走本技能：

- 用户只说"帮我画/生成一张/做张海报/生成头像"，**没有提"GPT生图"** → 优先 `comfyui`（或其它生图管线）；**本环境没装 comfyui 时走本 skill**（见「适用范围」）
- 用户提到 Stable Diffusion / Flux / SD / 本地模型 → `comfyui`
- 纯设计稿（生成 HTML 而非图片）→ `claude-design`
- 信息图 → `baoyu-infographic`；手绘草图 → `excalidraw`

若用户没指明"GPT生图"但需要在 GPT-Image 与 comfyui 间选择，**先问用户**，不要自行抢占。

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
| `--quality` / `-q` | 后端各自默认 | `low` / `medium` / `high` / `auto`（himodels 默认不传；azure 默认 low） |
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

0. **触发纪律**：本技能只在用户明确说"GPT生图"时使用；其它生图请求一律转 `comfyui`，不要主动调脚本。**例外：换皮模块有自己的触发词（素材/图集换皮+保持alpha），结构锁定换皮模块也有自己的触发词（换皮/换材质/换配色+保持结构动作轮廓透明切边），见下节第 6、8 节。**
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

## 已知限制 / 经验教训（旧版实测沉淀，与上文互补）

1. **任意长宽比没有对应固定规格**：要求"尺寸/长宽比与参考图完全一致"时：生成选最接近规格 + prompt 强调"保持完整构图、不裁切"，再 PIL 中心裁切/等比 resize 收口。**中心裁切会截掉上下内容**；要"不裁切完整横幅"就改直接 resize。区分两类需求：`保持比例` vs `不裁切超宽`。
2. **多帧 GIF 参考**：GIF 首帧或抽象中间帧若元素缺失，改用**中间清晰帧**作唯一参考，并在 prompt 显式列举"必须保留的每个关键元素"。
3. **中文 prompt 编码 & 本机环境**：
   - `python` 通常不在 PATH：本机可用 `C:\Program Files\Python312\python.exe` 或 `E:\Migrated\Python\Python311\python.exe`（rebuild 管线示例用的后者）。
   - 用 `subprocess.run(..., capture_output=True, encoding="utf-8", errors="replace")` 且脚本开头 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，否则打印中文会 `UnicodeEncodeError: 'gbk'`。
   - 把中文 prompt 存成 UTF-8 `.py` 再执行；不要用 `> 文件` 重定向（默认 GBK 会乱码）。
4. **素材对齐技巧**：当用户要求"用我工程里的资源替换生成物"，把**真实素材文件作为参考图**传入 edits，并按颜色/名称在 prompt 里一一对应说明，让模型"照着画"而不是原创，比纯文字描述更可控。
5. **模型差异**：sunburst 更慢但细节/清晰度更好；批量任务全部用 flare，只对最终定稿屏单独跑 sunburst，避免整体耗时翻倍。
6. **透明背景已原生支持（2026-09-22 实测）**：generations 与 edits 都可用；1024 / 2048 / 2880 各档位、flare 与 sunburst 均验证通过（透明像素占 45–59%，四角 `A==0`）。仍然要**校验而不是盲信**（`--check-alpha` / alpha_qa）；本地 flood fill 只是兜底。

## Manifest 记录（脚本自动生成）

两个主脚本都会产出 `IMAGE_<MODE>_MANIFEST.json`（输出目录旁），记录 backend/model/tier/mode/prompt/size/quality/background_requested/background_effective/alpha/response_echo/reference_images/output_path/elapsed_seconds/sha256 等字段；`gpt_image.py` 在 transparent 模式额外写入 `alpha_qa` 门禁明细（gate: pass/fail）。凭安全铁律：manifest 里**没有也不应有** key。

---

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

**六条铁律**：
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
| 2 | 只做 `use_ref=original` 不改 `fit` | 主体 5~45% 尺度漂移、20~77px 位移直接固化进资产 | 修复已有资产必须 `fit=bbox` + `alpha=original` |
| 3 | 拿**另一件**素材当参考图（如旁边那个图标） | 模型照抄参考图的位置/尺寸  主体偏到轮廓外 | 修复型一律用 `原版真图` 作参考，并写明"同位置同大小同朝向" |
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

### 8. 结构锁定换皮：外观迁移（Structure-Locked Reskin，2026-10-12 实装 v1.5.0）

**触发**：用户要求「换皮/重绘材质/换配色/换花纹/换风格」，且明确要求**保持原图的结构、动作、轮廓、透明切边范围不变**——适用于一切带透明通道的 PNG（角色部件、spine 图集切片、UI 素材、图标、宠物/角色毛色迁移等）。毛色/花色迁移只是典型场景，本模块不是换毛色专用。

**定位（对旧流程的替换关系）**：旧换皮主流程（第 6 节）是「整件素材重绘换风格」，实测对原图结构遵循不够——形状漂移、丢浮动元素、轮廓对不齐。凡是**要求结构锁定**的透明素材换皮，一律走本模块；只有「整件重画、不要求结构不变」才用第 6 节；图集切片（6.1）仍走 harvest 原位收割。8 专门解决旧管线两大顽疾：

| 顽疾 | 根因 | 本模块解法 |
|---|---|---|
| 轮廓无法对齐 | 内容框对齐只解决整体偏移，形状漂移和「丢了浮动元素导致的错位」解决不了；reskin_align 的质心对齐同样不检查主体框 | **alpha 逐字节回写**（轮廓像素级由原图锁死）+ **两步内容框配准**（粗配准整体 → 精配准未保护区域） |
| 无法在原图基础上局部编辑 | API 的 mask 字段上游会忽略（gpt_image.py 里「去掉 mask 重试」就是证据）；atlas 的 harvest 只覆盖图集 | 「局部」由两层保证：**prompt 三层约束**（哪些不许动）+ **后端 preserve 回贴**（不变区域原图像素原样恢复，支持色键） |

#### 8.1 参考图职责（铁律）

- **图1 = source（原图，必填）**：结构基准，决定 WHAT AND WHERE —— 结构、姿态、比例、轮廓、五官、配饰、透明切边。alpha 最终**逐字节**来自它。
- **图2 = reference（外观参考，可选）**：只决定 APPEARANCE —— 配色、花纹位置与边界、材质质感、颜色过渡。给了图2 就从它迁移；**没给就用纯文字描述外观，两条路径的后端像素管线完全相同**。
- 有图2 时，**严禁**把它的形状、姿态、配饰（典型：参考图有铃铛而原图没有 → prompt 必须点名 `do not add a bell`）、表情、背景带进结果。
- **多候选/多花色纪律**：每一次生成都从同一张原图重新出发，**绝不用上一轮结果当结构基准**（多轮链式 = 结构漂移）。

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

## 提示词模板库（2026-09-15 内化自 gpt-image-2）

> 本模板库原属独立技能 `gpt-image-2`（来源 ConardLi/garden-skills v1.0.3），2026-09-15 内化合并进本技能，原技能已移除。

**位置**：`references/prompt-templates/` —— 17 大类 / 93 个模板 + 1 个方法论文档 `prompt-writing.md`。

**核心原则：先检索模板，再写 prompt。** 只读最贴近的 1~2 个模板文件，**不要一次性读整个目录**。

### 模板索引

1. **学术配图 Academic Figures** --- 9 个  (目录 academic-figures/)
   - graphical-abstract
   - mechanism-diagram
   - method-pipeline-overview
   - multi-condition-comparison
   - neural-network-architecture
   - publication-chart
   - qualitative-comparison-grid
   - research-overview-poster
   - scientific-schematic
2. **素材与道具 Assets & Props** --- 2 个  (目录 assets-and-props/)
   - game-screenshot-mockup
   - retro-skeuomorphic-icons
3. **头像与人设 Avatars & Profile** --- 5 个  (目录 avatars-and-profile/)
   - character-grid-portrait
   - cultural-portrait-series
   - sticker-set
   - style-transfer-selfie
   - themed-3d-icon
4. **品牌与包装 Branding & Packaging** --- 6 个  (目录 branding-and-packaging/)
   - beverage-label-design
   - brand-identity-board
   - character-merch-board
   - cosmetic-packaging
   - full-mascot-brand-doc
   - mascot-brand-kit
5. **编辑工作流 Editing Workflows** --- 5 个  (目录 editing-workflows/)
   - background-replacement
   - local-object-replacement
   - object-removal
   - portrait-local-edit
   - product-retouching
6. **网格与拼贴 Grids & Collages** --- 5 个  (目录 grids-and-collages/)
   - ad-banner-multi-grid
   - anime-pitch-board
   - banner-grid-2x2
   - lookbook-grid
   - mixed-style-multi-panel
7. **信息图 Infographics** --- 6 个  (目录 infographics/)
   - bento-grid-infographic
   - comparison-infographic
   - hand-drawn-infographic
   - kpi-dashboard-infographic
   - legend-heavy-infographic
   - step-by-step-infographic
8. **地图 Maps** --- 5 个  (目录 maps/)
   - food-map
   - illustrated-city-map
   - itinerary-day-trip-map
   - store-distribution-map
   - travel-route-map
9. **肖像与角色 Portraits & Characters** --- 5 个  (目录 portraits-and-characters/)
   - character-sheet
   - founder-portrait
   - pose-reference-sheet
   - professional-portrait
   - virtual-host
10. **海报与战役 Poster & Campaigns** --- 8 个  (目录 poster-and-campaigns/)
    - banner-hero
    - biomimetic-concept-poster
    - brand-poster
    - campaign-kv
    - character-catalog-poster
    - editorial-cover
    - lineup-comparison-poster
    - vintage-editorial-infographic
11. **产品视觉 Product Visuals** --- 6 个  (目录 product-visuals/)
    - ecommerce-marketing-board
    - exploded-view-poster
    - lifestyle-product-scene
    - packaging-showcase
    - premium-studio-product
    - white-background-product
12. **场景与插画 Scenes & Illustrations** --- 4 个  (目录 scenes-and-illustrations/)
    - concept-scene
    - healing-scene
    - minimalist-mood-scene
    - picture-book-scene
13. **幻灯片与视觉文档 Slides & Visual Docs** --- 4 个  (目录 slides-and-visual-docs/)
    - dense-explainer-slides
    - educational-diagram-slide
    - policy-style-slide
    - visual-report-page
14. **分镜与序列 Storyboards & Sequences** --- 8 个  (目录 storyboards-and-sequences/)
    - anime-key-visual
    - character-relationship-diagram
    - cinematic-storyboard-grid
    - four-panel-comic
    - manga-spread-page
    - process-photo-board
    - product-tvc-storyboard
    - recipe-process-flowchart
15. **技术图 Technical Diagrams** --- 7 个  (目录 technical-diagrams/)
    - er-diagram
    - flowchart-decision
    - mind-map-tech
    - network-topology
    - sequence-diagram
    - state-machine
    - system-architecture
16. **字体与版式 Typography & Text Layout** --- 2 个  (目录 typography-and-text-layout/)
    - bilingual-layout-visual
    - title-safe-poster
17. **UI 样机 UI Mockups** --- 6 个  (目录 ui-mockups/)
    - chat-interface-scene
    - landing-page-case-study
    - live-commerce-ui
    - product-card-overlay
    - short-video-cover-ui
    - social-interface-mockup

### 模板工作方式

1. 从上面索引找到最贴近的分类目录；
2. 定位到具体模板文件，只读该文件；
3. 模板里的 `{argument ...}` 表示可替换参数；
4. 用户明确给的值直接填入；模板标了 `default` 的可用默认值；缺失信息会显著影响结果时主动询问；
5. 用户说「你随机生成」时，可在模板允许范围内合理随机化。

> ⚠️ 模板里的 JSON 是**提示词结构模板**，**不是 API 请求体模板**。最终交给 `scripts/gpt_image.py` 的是「渲染后的 prompt 字符串」——可以是拍平的 JSON，也可以是结构化自然语言段落，按模板原样使用。

### 何时先读方法论文档

先读 `references/prompt-templates/prompt-writing.md`，当：
- 还没决定怎么构造 JSON 模板
- 需要判断哪些字段该问、哪些可默认、哪些可随机
- 需要把新案例抽象成可复用模板

### 询问规则（禁止笼统地问「你想要什么风格」）

按模板字段精确提问，例如：
- 直播 UI 模板缺主体 → 问「主播是谁？用真人照片、名人名字、人物描述，还是完全随机生成？」
- 缺商品信息 → 问「商品名称是什么？价格是否指定？评论和礼物内容要我自动补全吗？」

### 与生图流程的衔接

渲染好 prompt 后回到本技能主流程：
- **无参考图** → `python scripts/gpt_image.py --prompt "<渲染后的prompt>" --size auto`
- **有参考图** → 追加 `--ref`
- **需要透明底**（图标/贴纸/素材/可叠加元素）→ 追加 `--background transparent`，检查退出码（3=未达标）
- **要大幅提升精度** → 追加 `--tier advanced`
- **换皮类**（编辑工作流 + 要求保持 alpha/尺寸不变）→ 走上方「换皮模块」的 reskin 管线，不要直接调脚本硬贴
