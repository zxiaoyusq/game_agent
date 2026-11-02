---
name: assetripper-unity-extract
description: Use when 用户要从 Unity 游戏构建提取或还原贴图、模型、动画、音频、字体、材质、场景或 Prefab，或要为 Unity/IL2CPP 构建制作可回滚的美术换皮资产工作台，或用 UnityPy 提取 TextAsset/Spine 骨骼/远程 manifest/配置 JSON 做系统拆解分析。先验证当前 AssetRipper/UnityPy 与目标 Unity 版本兼容性。
version: 1.3.0
updated: "2026-10-02"
created: "2026-08-10"
author: bai-lian
tags: [unity, assetripper, reverse-engineering, asset-extract, texture, fbx, art-replacement, reskin]
triggers: [unity 提取, unity 逆向, unity 资产, unity 换皮, 提取 unity 贴图, 还原 unity 工程, assetripper, unity asset extract, unity reskin, unity il2cpp 资产, 不是 cocos]
---

# Unity 美术资源提取与换皮 (AssetRipper)

## 执行卡（先用这张卡，再读正文）

**我管什么**：把 Unity（含 IL2CPP）构建的资产提取出来、还原成可编辑工程或素材包，支撑美术换皮二开，以及 TextAsset / Spine / 配置的脚本式证据挖掘。不管玩法逻辑（走 gameplay-logic-reverse），不管 Cocos 构建（走 cocos-reverse-engineering）。

**第一步做什么**：按 Phase 1 查 Unity 指纹（`libil2cpp.so` + `libunity.so`、`assets/bin/Data/global-metadata.dat`、`assets/bin/Data/data.unity3d` 的 UnityFS 头）；命中后用 AssetRipper GUI 的 Open Folder 加载游戏根目录。非 Unity 立即转走，不进入提取。

**做完怎么算完成**
- [ ] 引擎结论写成「Unity + 版本串 + 是否加密」，并指出依据哪个文件/字段
- [ ] AssetRipper 已加载目标目录并列出资产树（大游戏等状态栏进度结束）
- [ ] Settings 已按目的配好：换皮选 Script Content Level = `No Scripts`
- [ ] 导出目录能按扩展名统计出各类资产数量（PNG/FBX/WAV/OGG/TTF/OTF/MAT/PREFAB/UNITY）
- [ ] 关键贴图已目视确认尺寸与透明通道正确
- [ ] 缺失项已写入未知清单

**红线（不可违反）**
- jigsawcard 全案的包名、域名、实验数、资源数等字面值属 `CASE_ONLY_JIGSAWCARD`，禁止照搬，只迁移方法。
- TextAsset 的 `m_Script` 必须字节保真：先确认解码方式再逆编码，只有证明逐字节 Latin-1 映射才能用 Latin-1；禁止 replace/ignore。
- Spine 六件套缺一不可（`.skel.bytes` + `.atlas.txt` + `.png` + SkeletonDataAsset/AtlasAsset/Material）；导出后自查缺件缺图，按 atlas 的 `image:` 行匹配补齐。
- `global-metadata.dat` 的 magic 不可信：标准 `0xFAB11BAF` 可能被改写（如 `0x94437212`）只为骗静态分析器，必须实际尝试加载验证。
- Sprite 身份以 bundle/CAB + pathID 标识，不能仅以名称去重；像素差异不代表用途匹配，须实际视觉确认。
- 不把「3.5.0 ~ 6000.5.X」当永久兼容保证，也不把旧价格/旧 CLI 能力写进交付结论。

**卡住时按顺序读**
- 字节/编码/还原边界 → `modules/godot-migration-port/references/native-restoration-gates.md`
- Spine 缺件或缺图 → 本文件 Phase 6，再读 `modules/unity-extract/references/jigsawcard-puzzle-case.md`
- 系统拆解、远程 manifest、CDN 403 → 本文件 Phase 7 + 上述案例文件
- 需要方法体 / Mono / IL2CPP 地址模型 → `modules/unity-extract/references/managed-native-code-recovery.md`

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERAL_DEFAULT` + `GENERALIZED_PATTERN`。本机安装路径、工具版本和 Sudoku.com / jigsawcard 数据属于案例值。

双用途：① 用 AssetRipper 把编译后的 Unity 游戏还原为可编辑工程/素材包，支撑**美术换皮二开**（保留玩法，只替换贴图/模型/音频等美术资源）；② 用 UnityPy 做**脚本式证据挖掘**（TextAsset 二进制、Spine 骨架、远程 manifest、配置 JSON），产出策划可读的系统拆解分析（见下方新章节与案例）。

## 工具位置

- 历史安装路径：`${ASSETRIPPER}`。每次先检查文件、实际版本和目标构建兼容性。

- AssetRipper 官方支持范围和具体格式会随版本变化；不要把“3.5.0 ~ 6000.5.X”当成永久保证。先用小样本加载并检查导出警告，再决定是否全量处理。

- 本历史环境的 Free 版以 GUI 为主。CLI/订阅能力和价格可能变化，使用前查看当前安装版本/官方说明，不把旧价格写入交付结论。

## 适用场景

| 场景 | 说明 |
|---|---|
| 美术换皮二开 | 提取贴图/模型/音频 → 替换 → 重新打包（核心目的） |
| 提取单类资源 | 只导 Texture/Sprite/AudioClip/Font/Mesh，不导代码 |
| 还原工程 | 还原 .unity 场景 / .prefab / 资源引用链 / meta |
| 版本兼容 | 任意 Unity 版本（3.5 ~ 6000.x）构建 |

## 不适用（转其它工具）

- Cocos 构建 → `cocos-reverse-engineering`（指纹：settings.js/main.js/assets/main/config.json/.jsc）

- 引擎未知 → 先跑 `game-build-engine-identification`

- 只需代码逻辑（IL2CPP 反编译）→ 免费版能力弱，考虑 Il2CppInspectorRedux（本机 `${IL2CPP_INSPECTOR}\`）；换皮目的**不需要代码**

## 工作流

### Phase 1: 确认目标是 Unity 构建

检查指纹（来自 game-build-engine-identification）：

- `lib//libil2cpp.so` + `libunity.so`（Android）

- `assets/bin/Data/global-metadata.dat`（magic `0xFAB11BAF`，查是否加密）

- `assets/bin/Data/data.unity3d`（UnityFS 头 + 版本串）

- WebGL: `Build/*.data.gz` / `*.wasm`；PC: `*_Data/data.unity3d`

非 Unity → 交给 cocos-reverse-engineering 或提示引擎未知。

### Phase 2: 启动 GUI 并加载游戏文件

```powershell
Start-Process -FilePath "${ASSETRIPPER}"
```

GUI 操作路径：

1. 主界面 → **Open Folder**（选择游戏根目录：APK 解包后的目录 / `*_Data` 目录 / 含 data.unity3d 的目录）

2. 等待左侧资产树加载（大游戏可能数分钟，状态栏显示进度）

3. 顶部 **Settings** → 按需求配置：

- **Export Settings → Script Content Level**：换皮选 `No Scripts`（不要代码，快）

- **Bundle Scheme**：保持默认（Unity 原生结构）

- 勾选需要导出的类型（Texture2D/Mesh/AudioClip/Font/Material 等）

1. 点 **Export** → 选输出目录（建议 `E:\download\-ripped\` 风格）

若目标文件是 APK：先用 `apktool`/`7z` 解包拿 `assets/bin/Data/`，AssetRipper 直接打开 Data 目录即可。

### Phase 3: 提取结果验证（QA 必做）

导出后验证完整性：

```powershell
# 统计导出目录资产类型与数量
Get-ChildItem -LiteralPath "" -Recurse -File -Include *.png,*.fbx,*.wav,*.ogg,*.ttf,*.otf,*.mat,*.prefab,*.unity | Group-Object Extension | ForEach-Object { "{0}: {1}" -f $_.Name, $_.Count }

# 对比原始贴图数（若原始游戏有已知清单）
```

**检查清单**：

- Texture2D → PNG：检查关键贴图（UI 按钮/角色立绘/背景）存在且**尺寸/透明通道正确**

- SpriteAtlas → PNG 图集 + 子图位置信息（meta 或 .spriteatlas）

- Mesh → FBX 可导入

- AudioClip → WAV/OGG 可播放

- 引用关系：导出工程含 `.meta`，可导入 Unity Editor 重新打开

### Phase 4: 换皮操作（美术替换）

AssetRipper 导出 = **静态素材 + meta**，换皮流程：

1. 在 Unity Editor 中打开导出工程（或直接替换素材文件）

2. 替换贴图：同名覆盖 PNG（保持路径/尺寸一致）

3. 重新构建游戏（原游戏构建方式：Unity Build / 原工程构建脚本）

4. 若目标无原工程，用导出素材组装（参考 cocos-creator-project-repair 的思路：手写场景引用官方素材）

注意：AssetRipper 还原的工程需要 Unity Editor 重新导入生成 .meta 缓存；贴图替换后需在 Editor 里 re-import。

## Phase 5: TextAsset 二进制提取（先确认字节表示）

UnityPy 里 TextAsset 是"文本/二进制皆可"的容器，最容易踩坑：

- **字段**：`m_Name`（保留原始文件名，常是找回用途的关键索引）+ `m_Script`（字节体）。
- **字节保真**：检查 m_Script 实际类型，bytes 原样保存；字符串先确认解码方式再逆编码。只有证明逐字节 Latin-1 映射才能用该编码。禁止 replace/ignore；修复旧文件须保留哈希并验证回环与真实解析。见 [还原门禁](../godot-migration-port/references/native-restoration-gates.md)。
- 文本类 TextAsset（json/localization/csv）直接用 `m_Script` 解码后按字符串处理，别名与内容同时保留作为索引。

## Phase 6: Spine 骨骼资源识别与缺图补齐（GENERALIZED_PATTERN）

Spine 资源在 Unity 里是"六件套"一个都不能少：

- 数据侧：`xxx.skel.bytes`（二进制骨骼数据，TextAsset）+ `xxx.atlas.txt`（图集描述，TextAsset）+ `xxx.png`（Texture2D）。
- 运行时侧：SkeletonDataAsset / AtlasAsset / Material 包装，预览可用 Spine Player 或网页端 renderer。
- **识别判据**：assets 下带 `.skel.bytes` 后缀的 TextAsset = Spine 骨骼（区别于普通 TextAsset）。
- **导出后必做自查**：TextAsset 数量、SkeletonData 数量、atlas 引用贴图是否齐全；缺图从其他 AB 包 Texture2D 里按 atlas 的 `image:` 行匹配补齐（jigsawcard 案例补 47 张）。

## Phase 7: 配置证据挖掘与远程 manifest/CDN（系统拆解，GENERALIZED_PATTERN）

当用户要"拆解系统/评价商业设计"而非"拿美术换皮"时，AssetRipper 只解决一半。另一半是**把配置翻译成策划语言**：

1. **优先挖 `assets/` 下配方型配置**：AB 实验 JSON、广告配置 JSON（networkMapping/planList）、关卡/章节 JSON、震动/掉落表、SQLite 关卡库。这些是"策划填的数值"，天然可直接翻译成分析；不要停留在 Il2CppInspector 的类名清单。
2. **`global-metadata.dat` 的 magic 值不可信**：标准魔数是 `0xFAB11BAF`，但某些构建改写 magic（如 `0x94437212`）只为欺骗静态分析器，元数据本体可能并未整体加密。**不能只看 magic 下结论，要直接尝试加载验证**（Il2CppInspector/Il2CppDumper 跑一遍）。
3. **远程资源 manifest（IAA 标配）**：如 `manifest_ext.bs` —— 外层 Base64 → 内层二进制头 `[uint32][uint32][uint8]` + ASCII 版本串 + 压缩资源体段，解析出远程 bundle 清单（家族/数量）。CDN 域名常藏在数据文件里（如关卡 JSON 的图片 URL 前缀），内容寻址 URL 带 md5（缓存友好 + 防篡改 + 增量判断）。
4. **下载链路设计**（architecture 解读）：manifest 对账 → 分片下载 .tmp → CRC32 校验 → 原子改名上线 → 失败断点续传。CRC 防损坏文件上线；原子改名防"半个文件"。
5. **CDN 403 鉴权**：现代休闲游戏 CDN 有请求头/签名防爬，拼 URL 直连拿 403 属正常现象；破解需真机 mitmproxy 抓一次真实请求头（Referer/Origin/UA/签名参数）。先把这条作为"阻塞点"写进交付报告，而不是卡死整个项目。
6. **用脚本批量出表**：把实验清单、广告位、关卡数值抽成 Markdown 表作为"证据索引"附录；正文只写分析，避免正文变代码堆砌。
7. **策划分析交付模板**（用户最看重的部分）：每个章节回答四问（系统定位 / 核心规则与流程 / 数值配置表带证据 / 设计意图与效果复盘）；总纲先行（设计哲学、核心三循环、经济流转、系统关系图谱）；图表化（ECharts/Mermaid 渲染经济流转 Sankey、系统关系图、难度曲线等；MD 内联进全景 HTML）；每个系统补 2-4 条数据支撑的"反直觉发现"；证据等级标注贯穿全文（`[证据]`=配置/代码看到的事实，`[推断]`=基于行业常识与数据模式的分析）。
8. **AndroidManifest 二进制 AXML**：用 androguard 解析 string pool + 元素树，广告网络清单 = Activity/Service/Provider/MetaData 四维验证。

完整套路见 `modules/unity-extract/references/jigsawcard-puzzle-case.md`。

## 常见问题

- **导出慢/内存高**：大游戏建议只勾选所需资源类型（不导代码），分批次导出

- **Shader 还原实验性**：Free 版不还原 shader（premium 可解部分）；换皮保留原 shader 不受影响

- **IL2CPP 代码**：免费版代码还原弱（10-20%），换皮不需要，忽略

- **静态批处理网格合并**：premium 的 Static Mesh Separation 可拆回单体；免费版接受合并网格，仅影响 3D 场景级精细换模型

- **多 bundle 重复资产**：premium Deduplication 可去重；免费版接受重复，仅体积问题

## 与其它 skill 协同

- 引擎识别 → `game-build-engine-identification`

- Cocos 换皮 → `cocos-reverse-engineering`（CC 侧对标能力：packedAssets 图集切回单图、Spine/DragonBones、UUID/meta 保真、Phase 6 重建验证）

- 换皮映射表生成 → 待开发（见下方参考）

## 参考

- 官方文档: [https://assetripper.github.io/AssetRipper/](https://assetripper.github.io/AssetRipper/)

- Premium 功能清单: [https://assetripper.github.io/AssetRipper/articles/PremiumFeatures.html](https://assetripper.github.io/AssetRipper/articles/PremiumFeatures.html)

- 本机 Unity 案例: `E:\download\sudoku-re\REVERSE_ANALYSIS_REPORT.md`（UnityPy 路线）；AssetRipper 可同目标做工程还原对照

- jigsawcard 全案（Unity 6000.3.16f1 IL2CPP 休闲拼图，含 TextAsset/Spine/manifest_ext.bs/CDN/配置挖掘/策划分析交付模板）: `modules/unity-extract/references/jigsawcard-puzzle-case.md`；其包名、域名、实验数、资源数等字面值属于 `CASE_ONLY_JIGSAWCARD`，禁止照搬

### Sprite 身份

以 bundle/CAB + pathID 标识，先加载外部 PPtr 依赖，不能仅以名称去重。像素差异不代表用途匹配，须实际视觉确认。

## Mono / IL2CPP 方法体（按需）

只提取美术沿用原流程；需要方法体、玩法移植或 metadata 异常时读 [代码恢复证据链](references/managed-native-code-recovery.md)，配对 base/split/native/metadata 哈希，分清真实 Mono 程序集和 IL2CPP DummyDll，按原生地址模型关联实际调用。

## Unity AB 提取与完整 HTML 报告

远程 AssetBundle、TextAsset 字节保真、Spine 匹配 runtime 预览或单文件全书任务读 `modules/unity-extract/references/unity-ab-extract-and-html-report.md`。保留资源身份和字节证据，按实际解码链选择 surrogateescape / latin-1，不固定编码套全部资源；全文 HTML 经浏览器检查。
