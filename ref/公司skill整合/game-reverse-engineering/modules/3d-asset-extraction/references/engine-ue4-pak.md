# UE4/UE5 pak（鸣潮实测 + UE5 Nanite 储备）
> **何时读我**：用户说"提取UE4/UE5 pak 或鸣潮模型"，或遇到 `.pak` + Oodle + AES、需要 dynamicKeys 配对时。
> **读完能做到**：走 CUE4Parse 路线抓 wuwa-keys 并按 FGuid 逐对提交 dynamicKey，跑通批量枚举导出，并在选品时剔掉 HLOD/水面等虚高项、分清角色分件合并口径。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_WUWA_PAK`

识别指纹：传统 `.pak` + Oodle + AES；`GAME_WutheringWaves`。

## 密钥（CUE4Parse 通用路线）

- **密钥**：社区库 `wuwa-keys`（GitHub yarik0chka/wuwa-keys，端点 `yarik0chka.github.io/wuwa-keys/keys.json`）= `mainKey` + `dynamicKeys`（GUID 配对表，**随版本增长，大版本后重抓**）。落盘 `3D渲染\鸣潮模型\wuwa_keys.json`。
- **动态密钥提交姿势（关键坑）**：CUE4Parse `p.RequiredKeys` 是 **FGuid 集合**（不是字典）——`g.ToString()` 去掉 `-` 后与 keys.json 的 guid 逐对匹配，命中提交对应 dynamicKey，未命中才提交 mainKey；一律提交 mainKey 会挂不上一部分 pak。
- **鸣潮无需 usmap**（与黑猴 WeGame 版相反）：`EGame.GAME_WutheringWaves` + 密钥直接 Mount → `LoadPackageObject` 成功。CUE4Parse 1.2.2.202609 实测挂载 1,995,488 文件。

## 导出器

`${UE_AUDIT}\wuexport\`（bmexport 黑猴模板改造：PAK/AES/枚举/dynamicKeys/scan 前缀 `Client/Content/`）。scan 前缀规则 `SM_/SK_/CH_/Monster/Char + Entity/Character 路径` → 43,788 候选；export 4 分片并行 + `minTris=100000`，41,734 件 3 分钟跑完（147 达标 / 30,219 小件 / 11,279 no-geometry 预期失败）。

## 选品陷阱

- **HLOD 陷阱（虚高主力）**：`SM_HLOD_Landscape_*` 地形合并块单块 46~72 万面，是达标清单大头，采买口径属 GEO-N5 远景拼块**必须剔除**；水面（`*_Wat_*`）/特效平面（SM_Plane512）同理。鸣潮真实合格候选 = SK_ 场景演出生物/人物件（7 个，最高 1,438,368 面）。
- 玩家角色网格不在 SM_/SK_ 命中范围，存放路径待定位；角色分件存储（身/发/脸单件 <10 万面），需按角色合并统计。
- 渲染交付参考：`3D渲染\鸣潮模型\`（md+html+2 件 1024 白底 8 视角）。

## UE5 Nanite 储备（T1 购买线，2026-10-07 评估，待首批实挖验证）

UE5 Nanite 写实大作（Clair Obscur 33 / Stalker 2 / Silent Hill 2 remake / Remnant 2 / Lords of the Fallen / Avowed 等）理论高模密度最高（单款可达件按百计），是 T1 最大增量货源。路线 = 沿用本卡 CUE4Parse 导出器（UE5 pak 同格式）；**未验证项**：Nanite 网格在 CUE4Parse 下导出的是传统 LOD 链还是被简化代理、面数完整性是否达标。首挖一款后回填本节。
