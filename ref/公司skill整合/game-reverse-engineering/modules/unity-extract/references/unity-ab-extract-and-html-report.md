# Unity AB 提取、Spine 预览与 HTML 规则报告汇总（Tile Explorer 案例）

范围：`GENERALIZED_PATTERN`（方法）+ `CASE_ONLY_TILE_EXPLORER`（字面值）。
用途：当新项目是 Unity/IL2CPP 且需要“提取 AB 美术/规则 → 生成 Spine 预览 → 汇总成策划可读 MD/HTML”时，参考本文件的方法和交付物结构。
禁止照搬本文件中的包名、版本号、数量、路径、key、实验数量等案例值。

## 1. 案例背景

- 项目：Tile Explorer（包名与版本属于案例值，不通用）。
- 引擎：Unity 6000.3.16f1 / IL2CPP，Android。
- 拆解目标：
  1. 联网/线上内容拉取；
  2. 全量美术资源 + 所有 Spine 动画 preview HTML；
  3. 玩法/局外/商业化/美术加载/AB 测试规则整理成 MD；
  4. 全部 MD 汇总成可交互 HTML，制作人只看一个文件即可理解设计意图与落地细节。

## 2. 交付物结构（推荐模板）

```
<project>/
├── README.md                     # 快速索引、打开方式、资产清单
├── docs/
│   ├── 汇总总览.html              # 全量 MD 细则内嵌 + 图表/脑图/Spine 链接
│   ├── 00_总览与证据边界.md
│   ├── 01_线上内容拉取.md
│   ├── 02_美术资源与Spine预览.md
│   ├── 03_局内玩法规则.md
│   ├── 04_局外系统规则.md
│   ├── 05_商业化规则.md
│   ├── 06_美术动效加载与优化规则.md
│   ├── 07_AB测试规则.md
│   ├── 08_加密关卡数据说明.md
│   ├── 09_美术设计与实现规则.md
│   ├── 10_遗漏与后续补充.md
│   └── QA_预览验证结果.md
├── spine_preview/
│   ├── index.html                # 全部 Spine 动画预览（HTTP 版）
│   ├── 离线版.html               # 可选：全部资源 base64 内嵌，直接双击打开
│   ├── assets/<name>/.skel/.atlas/.png
│   └── libs/spine-player.min.js  # 必须匹配骨骼版本
├── art_preview/
│   └── index.html                # 全部纹理画廊 + 点击放大原图
├── art/
│   ├── textures/                 # Texture2D 导出
│   ├── sprites/                  # Sprite 导出
│   ├── audio/                    # AudioClip 导出
│   └── fonts/                    # Font 导出
├── unity_extract/                # 中间产物与 JSON 索引
└── scripts/                      # 生成器脚本（可复跑）
```

## 3. 关键方法

### 3.1 获取线上 AB

- APK 内 `assets/AssetBundle/*.ab` 是本地包；设备 `files/AssetBundle/` 是已下载的远程包。
- 通过 adb pull 获取设备缓存：
  - `adb pull /sdcard/Android/data/<pkg>/files/AssetBundle/ remote_ab/`
- 远程清单：`assets/config/abtest_config.json`、`manifest.json`、`manifest_chapter.json` 等 JSON 可提供 Bundle 列表、本地/远程标记、依赖、地址项。
- 若 CDN 地址未暴露，先把设备缓存作为“线上内容实体”交付，并如实标记 CDN 未定位。

### 3.2 解 AB 加密前缀

- 本案例 AB 文件带 32 字节 XOR/加密前缀，剥离前缀后 UnityPy 可解析：
  `tail -c +33 file.ab > stripped.ab`
- UnityPy 解析时设置 `UnityPy.config.FALLBACK_UNITY_VERSION` 为目标版本（例如 `6000.3.16f1`），否则报 No valid Unity version。
- 用 `env.objects` 按 ClassID 分类统计，输出 `ab_catalog.json`。

### 3.3 导出二进制 TextAsset（重要坑）

- TextAsset 的 `m_Script` 是 Python `str`，二进制内容会被 UnityPy 用 surrogate 表示。
- **不要用 `utf-8, errors='surrogatepass'` 写二进制文件**：每个高位字节会被膨胀成 3 字节 UTF-8 surrogate 序列，导致 Spine `.skel` 等二进制损坏。
- 正确写法：读回导出文件时用 `bytes.decode('utf-8', errors='surrogatepass')` 后，再 `str.encode('utf-8', errors='surrogateescape')` 还原原始字节；或导出时直接用 `errors='surrogateescape'` 写字节。
- 案例现象：`.skel` 被写成 3 字节序列后 Spine 播放器报 `Could not load skeleton data.`；还原后 113 条全部可解析。

### 3.4 导出纹理/精灵/音频/字体

- 用 UnityPy `exportTexture2D` / `exportSprite` / `exportAudioClip` / `exportFont` 批量导出。
- Sprite 可能因 PPtr 解引用失败而部分缺失，保留导出错误日志。
- 音频使用 `fmod_toolkit` 转 WAV，若原始是 OGG/M4A 则保留原始容器。

### 3.5 Spine 预览

- 文件格式：Spine 4.1.x 二进制 `.skel` + 文本 `.atlas` + PNG。
- 播放器版本必须匹配骨骼版本：
  - 游戏 Spine 4.1.x → 使用 `@esotericsoftware/spine-player@4.1.x`；
  - 使用 4.3.x 会因空字符串表项/空 bone name 报错 `Could not load skeleton data.`
- 预览页建议支持 `#动画名` hash 直达，方便汇总 HTML 跳转。
- 自检方式：用 Node + Spine 4.1 运行时遍历所有 `.skel`，通过 dummy atlas loader 验证可解析，再通过 Chrome Headless HTTP 打开页面确认 `✅ 加载成功` 与 canvas/controls 出现。

### 3.6 规则文档

- 每份 MD 开头加“设计意图速览”表：
  `设计意图 | 当前实现效果 | 策划可调点`
- 文档分：线上内容、美术资源/Spine、局内玩法、局外系统、商业化、美术动效加载、AB 测试、加密说明、美术设计与实现、遗漏补充。
- 保留证据边界：哪些是静态确定、哪些是推断、哪些未解出（如加密关卡、CDN URL）。

### 3.7 HTML 汇总

- 必须把**全部 MD 完整内容**内嵌进 HTML，而不是只做目录索引。
- 使用 Python `markdown` 库渲染 MD 表格，CSS 统一表格/代码块/引用样式。
- 增加数据总览、设计意图总纲、柱状图、脑图、文档搜索、Spine 链接、美术画廊链接。
- 输出 12+ 份文档全量细则后，制作人只需打开一个 HTML 即可阅读全部设计意图与落地细节。

### 3.8 美术资源画廊

- 生成 1279 张纹理缩略图页，支持名称/Bundle 搜索。
- 必须支持点击缩略图弹出全屏原图，不能只有小图。

### 3.9 启动方式

- 直接双击普通 HTML 会走 `file://`，浏览器禁止 `fetch` 本地 `.skel/.atlas`，报 `status 0`。
- 两种解法：
  1. **HTTP 服务**：提供一键启动脚本（.bat）：
     - 纯 ASCII 输出，避免 GBK/UTF-8 编码乱码；
     - 自动查找真实 Python（不要依赖 `WindowsApps` 占位 `python.exe`）；
     - 启动 `python -m http.server 8000` 并打开浏览器。
     - 页面内检测 `location.protocol === 'file:'` 并提示用户用 HTTP 访问。
  2. **离线单文件**（参考 Block Blast spine-preview/preview.html 的做法）：
     - 把 `.skel`/`.atlas`/`.png` 全部 base64 内嵌进 HTML；
     - 用 `SpinePlayer` 的 `rawDataURIs` 把逻辑路径映射到 `data:` URI；
     - `downloadBinary/downloadText/loadTexture` 会直接使用 `rawDataURIs`，不再走 XHR/fetch；
     - 可双击直接打开，文件体积大（本案例约 101 MB）但无需服务器；
     - 可用生成器脚本 `<项目目录>/scripts/build_spine_preview_offline.py`（历史项目生成器，未随技能分发） 从同一套 `index.html` + `assets/` 自动产出。

## 4. 可迁移方法清单

1. 先确认 Unity 版本与 AB 是否带加密前缀；用目标版本 fallback 解析。
2. 远程内容先看设备缓存，再看 manifest JSON；CDN 未定位时如实标注。
3. 二进制 TextAsset 导出用 surrogateescape，不用 surrogatepass。
4. 音频/字体/纹理用 UnityPy 官方 export 函数，保留索引 JSON。
5. Spine 播放器版本必须与骨骼二进制版本一致。
6. HTML 汇总必须内嵌全量 MD 内容，并配图表/脑图/搜索/预览链接。
7. 本地预览必须通过 HTTP，不能依赖 file://。

## 5. 案例专属值（禁止直接复制）

- 包名、版本号、AB 数量、远程包数量、Spine 数量、纹理数量、实验数量、策略数量、路径、加密 key、CDN 结论。
- 这些只属于 Tile Explorer 案例，其他项目必须重新测量。

## 6. 相关文件（案例路径）

- 工程：`E:\codex_apk_work\tile_explorer\`
- 汇总 HTML：`docs\汇总总览.html`
- Spine 预览（HTTP 版）：`spine_preview\index.html`
- Spine 预览（离线双击版）：`spine_preview\离线版.html`
- 美术画廊：`art_preview\index.html`
- 一键启动：`开启预览.bat`
- 生成脚本：`scripts\build_summary_html.py`、`scripts\build_art_preview.py`、`scripts\build_spine_preview_offline.py`、`scripts\fix_spine_binary.py`
