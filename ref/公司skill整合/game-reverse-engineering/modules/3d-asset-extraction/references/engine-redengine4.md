# REDengine 4（赛博朋克 2077）
> **何时读我**：用户说"提取巫师3/赛博朋克2077模型"，或遇到 REDengine 的 `archive/pc/content/*.archive` 时。
> **读完能做到**：用 WolvenKit.Console 下 CLI zip 做 uncook 出 GLB，经 Blender 转纯几何 OBJ 解决黑模，并按分件规则合并出完整高模。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_CP77_ARCHIVE`

识别指纹：`archive/pc/content/*.archive`。

## 工具链

- 下 **WolvenKit.Console**（官方 CLI zip，43MB），别下 154MB 的 GUI。本机 `E:\Gameprogram\yysls-audit\research\cp77\cli\`。
- `uncook <archive> -o <out> -gp <游戏目录> -r <正则> --mesh-export-type MeshOnly` → GLB；`-gp` 给了会扫全游戏档案（正则跨库命中）。
- `archiveinfo` 静默无输出；用 `uncook -r` 的 "Found N/M entries" 计数探测路径是否存在。

## 材质与合并

- **MeshOnly 导出的 GLB 材质是黑的**，官方工具渲染出黑模；**经 Blender 转纯几何 OBJ 后官方工具赋默认浅色材质**，出图正常。
- 角色/载具**分件存储**（单件 4~6 万面），≥10 万面的完整模型需**合并部件**（Basilisk 15 件合并 = 260 万面）；合并时剔除 `interaction_collider`（碰撞壳）与 `kit_` 变体。

## 资产状态（2026-10-07 探针）

6,800 GLB 已 uncook 在 `3D渲染\赛博朋克2077\_cp77_uncook归档\`；载具线未挖完，ep1 往日之影未购买。CP77 达标密度高（本体 272 件口径内），管线现成。
