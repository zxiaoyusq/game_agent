# RE Engine（Capcom：RE2 / DMC5 / 怪猎荒野）
> **何时读我**：用户说"提取RE Engine/生化危机/鬼泣5/怪猎荒野模型"，或遇到 `re_chunk_000.pak`（AKPK）、`4D455348`（"MESH"）时。
> **读完能做到**：分清有/无名字表两套打法（MHWilds art+streaming 配对 / RE2·DMC5 按 `.mesh` 扩展名全量解包），修好 REMeshEditor 版本字典缺行并用 Blender ≥4.3.2 导入，批量转 `.tex` 出贴图。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_MHWILDS_ART_STREAMING`、`CASE_ONLY_DMC5_MESH_VERSION`

识别指纹：`re_chunk_000.pak`（AKPK 魔数）；网格魔数 `4D455348`（"MESH"）。

工具链：REtool-filtered（`E:\Gameprogram\mhwilds-audit\tools\REtool-filtered.exe`）+ Blender RE Mesh Editor 插件。

## 有/无名字表两套打法

- **有名字表（MHWilds）**：`art/` 索引版（主 pak）+ `streaming/art/` 真几何（常在 patch pak）**必须配对且置于同一 `natives/stm/` 根**；文件版本号 `.241111606` 不可去。导入：`bpy.ops.re_mesh.importfile(...)`，857,400 面实测 33.4s。
- **无名字表（RE2/DMC5）**：pak TOC 只存 Murmur3 哈希，但 `REtool -x` **全量解包时文件名自带真实扩展名**（`<hash>.mesh.21041600`、`<hash>.tex.34`——扩展名数字即内部版本号）→ 按 `.mesh` 过滤即可，无需名字表。RE2：23.7GB pak → 32.9GB / 2,891 个 .mesh；DMC5：31.9GB → 37GB / 1,710 个 .mesh（版本号 386270720）。
- 角色网格判据：包围盒比例 ≈1:1:1.5（2 米级）+ 面数 10 万级；**最大的网格是场景/环境**（实测 2000 单位长条），勿按体积取最大。

## ★ REMeshEditor 两个硬坑（DMC5 实测）

1. **版本字典缺行**：插件按**文件扩展名**查 `meshFileVersionToNewVersionDict`；RETool 解包扩展名是**内部版本号**（DMC5=386270720），字典键是**文件版本号**（DMC5=1808282334）→ 全部 "not supported"。**修复 = 用户目录插件 `file_re_mesh.py` 的字典加 `386270720: VERSION_DMC5` 一行**。新版游戏"not supported"先查这里，不是格式真变了。
2. **Blender ≥4.3.2 硬要求**：4.2.10 直接 EXCEPTION_ACCESS_VIOLATION（连 RE2 mesh 都崩，与文件无关）。用 TUNA 镜像 `blender-4.5.14-windows-x64.zip` + portable scripts/addons 装。

## 贴图

- `.tex.NN` → dds：REtool `-tex` 逐文件转（**目录参数 = 打包模式，误传目录会反向打包出新 pak**）。批量多进程 8 并发；环境变量 `DOTNET_ROLL_FORWARD` 必须带。
- DMC5 白模白底不可见：clay 材质近纯白，合成时 `point(lambda v: min(255, v*0.86))` 压暗。

## 战果参考

DMC5 首件 4015955367 大型恶魔 165.9 万多边形 8 视角渲染交付（`3D渲染\DMC5\`）。DMC5 mesh 单文件自包含（同 RE2，无 art/streaming 分离）。
