---
name: game-3d-asset-extraction
description: Use when 用户要从 PC 端 3A 游戏离线提取 3D 模型/贴图（NeoX/Messiah、RE Engine、FromSoftware、REDengine、Anvil/刺客信条、Creation/辐射4、Tiger/命运2、CRIWARE/尼尔、MT Framework、Source 2、UE pak、米哈游 blk），需要选对解包工具链、破解加密容器、自研无头导出器、导入 Blender 并用官方去重工具渲染八视角白底图、按面数验收时；或逆向未知二进制容器格式需要方法论参考时。
version: 2.1.0
created: "2026-09-21"
updated: "2026-10-10"
author: bai-lian
tags: [reverse-engineering, 3d-assets, re-engine, messiah, neox, fromsoftware, flver, anvil, forge, creation-engine, ba2, nif, tiger-engine, destiny2, criware, wmb3, mt-framework, mod3, source2, vpk, ue4-pak, cue4parse, mihoyo, blk, blender, wolvenkit, retool, witchybnd, binder-tool]
triggers: [提取游戏模型, 3A模型, 游戏模型解包, 去重工具渲染, 八视角渲染, 模型面数验收, EZST, re_chunk_000, chrbnd, flver, wolvenkit, 辐射4, fallout, BA2, NIF, 黑魂3, dark souls, TPF, 尼尔, nier, CPK, WMB3, DMC5, 鬼泣, 刺客信条, anvil, forge, 彩虹六号, R6S, 命运2, Destiny 2, Tiger引擎, AKPK, 怪猎, 怪物猎人, mod3, 半条命, alyx, VPK, 鸣潮, 绝区零, 星穹铁道, 米哈游, mhy1, ENCR, 容器逆向, 未知格式, 二进制格式分析]
---

# PC 3A 游戏 3D 资产离线提取

## 执行卡（先用这张卡，再读正文）

**我管什么**：PC 端 3A 游戏 3D 模型/贴图的离线提取——按引擎指纹选对工具链、破解加密容器、自研无头导出器、导入 Blender 渲染八视角白底图、按面数验收；也提供未知二进制容器格式的逆向方法论。逐引擎深度章节与《3D 数据采买验收标准》在外部技能 re-engine-asset-audit；手游 Unity/Cocos 资产提取不归这里。

**第一步做什么**：用游戏指纹在「引擎路由表」里定位命中行，先读该行对应的 `modules/3d-asset-extraction/references/engine-*.md` 参考卡再动手；未命中任何一行，立刻转 `modules/3d-asset-extraction/references/method-container-reversing.md` 四步法。

**做完怎么算完成**
- [ ] 引擎判定已写出依据的指纹（容器魔数 / 扩展名族 / 游戏目录结构）
- [ ] 命中引擎时已读过对应 `engine-*.md`，工具链按其指定
- [ ] 未命中引擎时已走完四步法前两步：头部侦察 + 锚点定界
- [ ] 社区已有实现的格式没有自写解包器，而是编译互证
- [ ] 原始资产包在解包前已复制备份
- [ ] 模型/贴图能独立打开，面数按实测而非按体积下结论

**红线（不可违反）**
- 同厂商跨版本必按 ver 分支解析：entries 宽度、元数据宽度、名字解密 key step 逐代不同，套错版本必崩。
- 下载器预分配的空文件会污染遍历（全 0 空壳），遍历前先按魔数签名过滤。
- 宣称「顶点在关联资源 / 声明式引用」之前必须做偏移穷举；最小样本不代表格式，至少 3 件跨两个数量级体积复现。
- 含中文路径或中文 bat 的 cmd 调用一律 python subprocess 列表传参；外部工具常按自身安装目录解析相对路径，输入/输出一律传绝对路径。
- 按体积选品会踩坑：容器体积≠面数，包体大≠高模多，最大网格常是场景或特效。
- 密钥只随该游戏项目使用，不得外传或复用到其他项目。

**卡住时按顺序读**
- 未见格式、偏移穷举、无效穷举陷阱 → `modules/3d-asset-extraction/references/method-container-reversing.md`
- 渲染参数、交付四件套、提取质量自验证门禁 → `modules/3d-asset-extraction/references/render-delivery-spec.md`
- 引擎专属坑与战果 → 路由表对应的 `modules/3d-asset-extraction/references/engine-*.md`
- 采买验收标准对照 → 外部技能 re-engine-asset-audit

全局五步循环与六条铁律见 `references/execution-protocol.md`。

范围：`GENERAL_DEFAULT`。逐引擎的深度章节与《3D 数据采买验收标准》对照在外部技能 **re-engine-asset-audit**；本模块 = 引擎路由 + 逆向方法论 + 交付规范。**所有内容均为本机实挖验证**。

## 引擎路由表（命中引擎 → 读对应参考卡）

| 引擎 / 代表作 | 识别指纹 | 工具链一句话 | 参考卡 |
|---|---|---|---|
| NeoX/Messiah（燕云） | `EZST` 魔数，`Patch*.mpk` | 自研 AES-256-ECB+zstd 解码器 | [engine-neox-messiah.md](references/engine-neox-messiah.md) |
| RE Engine（RE2/DMC5/怪猎荒野） | `re_chunk_000.pak`，MESH 魔数 | REtool + Blender REMeshEditor | [engine-re.md](references/engine-re.md) |
| FromSoftware（黑魂3/只狼/法环） | `Data*.bdt/bhd`，`.flver` | BinderTool 0.5.2 / ER.Unpacker + SoulsModelTool | [engine-fromsoft.md](references/engine-fromsoft.md) |
| REDengine 4（2077） | `archive/pc/content/*.archive` | WolvenKit.Console uncook → GLB | [engine-redengine4.md](references/engine-redengine4.md) |
| UE4/UE5 pak（鸣潮等） | 传统 `.pak`+Oodle+AES | CUE4Parse 自研导出器 + 社区密钥库 | [engine-ue4-pak.md](references/engine-ue4-pak.md) |
| Unity/米哈游（绝区零/星铁） | `mhy1/mr0k/ENCR` blk | 密钥硬编码于 Escartem 源码，python 全链自研 | [engine-unity-mihoyo.md](references/engine-unity-mihoyo.md) |
| Anvil（起源/AC3R/R6S） | `DataPC*.forge`，scimitar 索引，ver 27/28/**30**/34 | 起源/AC3R 走 ATK（**AC3R Mesh 顶点缓冲内联，`fd.Data[2:]` 后直解**）；**R6S ver30 走自研 12B 条目解析（已出模型）** | [engine-anvil.md](references/engine-anvil.md) |
| Creation（辐射4） | `*.ba2`（BTDX），`.nif` | BA2 直解（GNRL/DX10 格式已全破）+ PyNifly | [engine-creation.md](references/engine-creation.md) |
| Tiger（命运2） | `packages\w64_*.pkg`（AKPK） | Charm + 自研无头宿主（勿自写解包器） | [engine-tiger.md](references/engine-tiger.md) |
| CRIWARE（尼尔） | `*.cpk` → `DAT\0` → `WMB3` | CriPakTools + 自写 DAT 解包 + Blender 导入 | [engine-criware.md](references/engine-criware.md) |
| MT Framework（怪猎世界） | `chunk0.bin`（CMP\0），`.mod3` | WorldChunkTool（按游戏自带 oo2core 定版本）+ headless mod3 | [engine-mtframework.md](references/engine-mtframework.md) |
| Source 2（半条命 Alyx 等） | `.vpk`（无加密） | Source2Viewer-CLI，glb 自带 PBR，零攻坚 | [engine-source2.md](references/engine-source2.md) |

## 跨引擎方法论（接手新游戏/未见格式先读这两张）

- **[method-container-reversing.md](references/method-container-reversing.md)** —— 未见格式的标准打法：头部侦察 → 锚点定界 → 字段语义物理约束验证 → 参照实现互证；含**无效穷举陷阱清单**（开跑前必过）与 pythonnet 跨语言桥接姿势、作业铁律（资产保全/长任务容错/cmd 编码坑）。
- **[render-delivery-spec.md](references/render-delivery-spec.md)** —— 渲染管线参数、视角映射核验、交付四件套、**提取质量自验证门禁**（体积=理论值、面数以实测为准）、面数口径与选品规则（HLOD/VR/合并件陷阱）。

## 引擎未命中时

1. 按指纹侦察：容器魔数、扩展名族、游戏目录结构 → 先查族谱（同厂商历代格式往往同构）。
2. 走 [method-container-reversing.md](references/method-container-reversing.md) 四步法；有社区实现优先编译互证，无社区实现按方法论自研。
3. 打通后新建 `engine-<name>.md` 参考卡（格式：识别指纹 → 容器/资源格式 → 工具链与坑 → 战果参考），并更新本路由表 + landing-log。

## 快速避坑（全引擎通用，细节在两张方法卡）

- **同厂商跨版本先按 ver 分支解析**：Anvil 一族 ver27/28/30/34 的 entries 宽度（20B/12B/20B）、元数据宽度（192B/322B/0）与名字解密 key step 逐代不同，套错版本必崩（R6S v30 用 12B，RF 内置 20B 解析器对其无效）。
- **下载器预分配的空文件会污染遍历**：DepotDownloader/steamcmd 会把未下完的包预分配成全 0（Y5S3 depot 368 个 forge 里 310 个是空壳）——遍历前先按魔数签名过滤。
- 解包没跑通**先拷原始资产包保底**；后台长任务必须多进程+容错+幂等（单进程遇坏条目静默死）。
- **解析失败先怀疑自己的对齐，别急着下"数据在别处"的结论**：宣称某资源是"声明式引用/顶点在关联资源"之前，必须做**偏移穷举**（起点 0..32 + 所有 magic 偏移各试一次，用领域量判定）；同时**最小样本（占位件/LOD3/几百字节）不代表格式**，至少 3 件跨两个数量级体积复现。AC3R 就因这两点白扔一整轮（详见 engine-anvil.md）。
- 含中文路径/中文 bat 的 cmd 调用是地雷区——一律 python subprocess 列表传参。**外部工具常按自身安装目录解析相对路径 → 输入/输出一律传绝对路径**。
- F 盘游戏文件只读：解包前先把档案复制到 E:；游戏未安装时先验证本体存在（目录可能只剩 win64_save）。
- 按体积选品会踩坑：最大网格常是场景/特效（RE/FO4），容器体积≠面数（Source 2 骨架动画占大头），包体大≠高模多（命运2 模块化小件）。
- REtool-filtered 按名查找是 O(N×M) 线性扫描——只喂真正需要的几十行清单，全量清单 40 分钟零产出。
