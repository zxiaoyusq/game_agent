# jigsawcard 休闲拼图逆向：TextAsset/Spine/远程 manifest/配置挖掘/策划分析交付全案

> **何时读我**：哥哥要拆一款 Unity IL2CPP 休闲手游、结果收在"一屏类名"上被嫌证据链不够，或具体卡在 TextAsset 二进制读出来是脏数据、Spine 六件套认不出来、远程 manifest 解不开、CDN 403、配置不知从哪挖时。
> **读完能做到**：从 APK 走到"策划能看懂的交付文档"——用 `m_Script`+`latin-1` 还原 TextAsset 二进制、按 `.skel.bytes` 识别 Spine 并补齐缺图、分层解析 `manifest_ext.bs`、把配置数值批量出成证据表，最后按四问模板 + 图表化的全景 HTML 交付。
> **范围**：`GENERALIZED_PATTERN` + `CASE_ONLY_JIGSAWCARD`

范围：`GENERALIZED_PATTERN`（方法可迁移）+ `CASE_ONLY_JIGSAWCARD`（项目专属值，禁止复制字面值）。

目标：Unity 6000.3.16f1 (IL2CPP) 的休闲拼图游戏（乐信拼图 jigsawcard），从 APK 一路到"策划分析文档 + 全景 HTML"交付。本案最有价值的部分不是单点技术，而是**把 Unity IL2CPP 项目拆到"策划可理解"的完整方法链**，以及若干易踩坑的资源提取技巧。

---

## 1. 方法链总览（GENERALIZED_PATTERN，可迁移）

> 本方法链覆盖"APK → 引擎确认 → 资源提取 → 配置挖掘 → 分析文档"全流程。**每一步的产出都应当是"人话级别的证据"，而不是类名堆砌。**

```
APK 解包 → 指纹确认引擎 → 元数据/加密检查 → 三路提取：
  A. 美术资源(Texture2D/Sprite/Spine)
  B. 配置证据(assets/*.json/TextAsset/关卡库)
  C. 网络面(远程 manifest/CDN URL/AndroidManifest AXML)
    → 证据挖掘脚本(批量出表) → 策划分析文档 → 全景 HTML
```

### 1.1 引擎确认与加密检查（先查再拆，别被壳误导）

- APK 外层 Java/Kotlin 壳（classes*.dex ×10：广告 SDK/内购/推送）≠ 游戏本体。Unity 本体在 `assets/bin/Data/`，数据面看 `data.unity3d`（UnityFS 头 + 版本串）与 `global-metadata.dat`。
- **`global-metadata.dat` 的 magic 值必须第一步验证**：标准魔数是 `0xFAB11BAF`；本案 magic 被改写成 `0x94437212`（加密/混淆标记），但里面 IL2CPP 类名仍可读——说明只是写死了 magic 欺骗静态分析器，元数据本体并未整体加密。**结论方法：不能只看 magic，要直接尝试加载验证**。
- 工具链：Il2CppInspectorRedux（C# stub 转储，类型/字段/签名/方法 RVAs，方法体为空）→ 需求方法体时再上 Ghidra/IDA + il2cpp.json（本案例未做，signature 级已足够支撑"系统清单"结论）。
- PowerShell 下 UTF-8 处理：读写用 `.read_text('utf-8')`，别内联长 Unicode 字符串到 `powershell -Command`。

### 1.2 TextAsset 二进制提取（易踩坑，最实用）

UnityPy 里 TextAsset 是"文本/二进制皆可"的容器：

- **字段**：`m_Name`（保留原始文件名，常是找回用途的关键索引）+ `m_Script`（字节体）。
- **坑**：直接用 `.text` 读 TextAsset 可能拿到被当作 UTF-8 字符串误解码的脏数据（含非法字符）；**二进制内容必须用 `m_Script` + `latin-1` 编码还原字节**，再按实际格式（json / skel 二进制 / compress）解析。
- Spine 场景（本案提取 46 组）：Spine 六件套 = `xxx.skel.bytes`（二进制骨骼数据，TextAsset）+ `xxx.atlas.txt`（TextAsset）+ `xxx.png`（Texture2D） + 运行时包装（SkeletonDataAsset/AtlasAsset/Material）。**as 判断：assets 下带 `.skel.bytes` 后缀的 TextAsset = Spine 骨骼**。
- 导出后先复查：TextAsset 数量、SkeletonData 数量、atlas 引用贴图是否齐全，缺图从其他 AB 包 Texture2D 里按 atlas `image:` 行匹配补齐（本案补 47 张）。

### 1.3 配置证据挖掘（"策划分析"与"证据链"的分水岭）

用户最终验收的不是"有多少个类"，而是**"这个系统为什么这么设计、数值怎么定、效果如何"**。因此：

- **优先挖 `assets/` 下配方型配置**：AB 实验配置（v6_exp 结构）、广告配置（networkMapping/planList/timeoutConfig/缓存预留）、关卡/章节 JSON、震动表、掉落表、StageDatabase（SQLite）等。这些 JSON 是"策划填的数值"，天然可以直接翻译成分析。
- **用脚本批量出表**（mine_evidence.py 式）：把实验清单、广告位、关卡数值抽成 Markdown 表，作为"证据索引"附录；正文只写分析，附录放证据。避免正文变代码堆砌。
- **证据等级标注贯穿全文**：`[证据]`=配置/代码里看到的事实；`[推断]`=基于行业常识与数据模式的分析。交付时两者显式区分。

### 1.4 远程资源 manifest 与 CDN（IAA 休闲游戏标配）

- **`manifest_ext.bs` 结构**（远程资源清单，Base64 包装）：外层 Base64 → 内层二进制头 `[uint32][uint32][uint8]` + ASCII 版本串 + 压缩资源体段。本案解析出 54 个远程 bundle，家族为"章节地图 / 连线玩法 / 收集玩法"。
- **CDN 域名从数据文件提取**：如关卡 JSON 里图片 URL 前缀（`jigsaw-cdn.dailyinnovation.biz`）。内容寻址 URL 带 md5（改名 → 缓存友好 + 防篡改 + 增量判断）。
- **下载链路设计**（可复用为架构理解）：manifest 对账 → 分片下载 .tmp → CRC32 校验 → 原子改名 .ab（瞬时生效）→ 失败断点续传。CRC 防损坏文件上线；原子改名防"半个文件"。
- **CDN 403 鉴权**：现代休闲游戏 CDN 有请求头/签名防爬。拼 URL 直连拿 403 = 正常现象，**破解需真机 mitmproxy 抓一次真实请求头（Referer/Origin/UA/签名参数）**。要先把这条作为"阻塞点"写进交付报告，而不是卡死整个项目。

### 1.5 AndroidManifest AXML 解析（权限/广告 SDK 清单）

二进制 AndroidManifest 用 Python（androguard）解析出 string pool + 元素树：services/receivers/providers、权限、intent-filter。广告网络清单 = 四维验证（Activity/Service/Provider/MetaData 联合）。

### 1.6 策划分析交付模板（本案最受好评的部分）

用户反馈"证据链不够"后，重写的交付模板：

1. **每个章节回答四问**：系统定位 / 核心规则与流程 / 数值配置表（带证据）/ 设计意图与效果复盘。
2. **总纲先行**：设计哲学（如"10~90s 轻智一局/玩家永不卡死/每个行为都有多巴胺反馈"）、核心三循环（局外/留存/商业）、经济流转、系统关系图谱。
3. **图表化**：经济流转 Sankey、系统关系图、难度曲线、广告位时间线、AB 实验分布、震动反馈阶梯、美术资源构成、SDK 数据流、每日钩子卡片、CDN 进度 —— 全景 HTML 用 ECharts + Mermaid 渲染，章节正文 MD 内联。
4. **"反直觉发现"板块**：每个系统补 2-4 条数据支撑的反直觉结论（如"表现层实验远多于数值层"、"卡关兜底是系统工程"），让读者觉得"挖到了门道"。
5. **证据索引附录**：列清每个结论对应的配置/资源路径，可复核。

---

## 2. 项目专属证据（CASE_ONLY_JIGSAWCARD，禁止复制到其他项目）

- 包名 `com.oakever.jigsawcard`，版本 1.5.19 (code=82)，Unity 6000.3.16f1。
- 元数据 magic `0x94437212`（本案例专属；其他项目必须自己验证）。
- CDN 域 `jigsaw-cdn.dailyinnovation.biz`；远程包 54 个（3 家族）；章节远程到 51 章、本地 StageDatabase 仅到第 3 章。
- AB 实验：包内快照 27 个在线 / 全量配置 57 实验 + 208 策略；广告网络 23 家（AppLovin MAX 主 + AdMob 次聚合）；内购 Google Play Billing 8.1 自研补单/防刷。
- 关卡规模：76 章 / 约 1490 关；金币 普通20 / 困难30；震动 40 档（0.27~0.98）；多语言 20+（含阿语/希伯来 RTL）。
- 资源规模：114 AB 包、967 Texture2D、46 组 Spine（42 组动画）、83.36MB 本地 + 远程扩展 ≈88MB+。
- 推送：FCM（海外）+ HMS（华为）+ 本地闹钟三路冗余；埋点：AppsFlyer/Firebase/AppMetrica/GA4/TikTok/私域 6 路。

## 3. 可迁移 vs 不可照搬速查

| 内容 | 标签 |
|---|---|
| TextAsset `m_Script`+latin-1 还原二进制、Spine 六件套识别与缺图补齐 | `GENERALIZED_PATTERN` |
| manifest_ext.bs 分层解析、CDN 403 → 真机 mitmproxy 方法 | `GENERALIZED_PATTERN` |
| 配置证据挖掘+策划分析四问/图表化交付模板 | `GENERALIZED_PATTERN` |
| jigsawcard 的包名/域名/实验数/资源数/关卡数/震档列表 | `CASE_ONLY_JIGSAWCARD` |

## 4. 产物路径（案例）

- 交付目录：`E:\Gameprogram\乐信拼图\`（13 个策划分析 MD + `jigsawcard_系统架构全景.html` + spine_preview.html + 美术资产目录）
- 工程脚本：`scripts\mine_evidence.py` / `mine_evidence2.py`（配置证据）、`build_analysis_html_v3.py`（全景 HTML）