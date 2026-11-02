# Source 2（半条命 Alyx，全场零攻坚成本）
> **何时读我**：用户说"提取半条命 Alyx 模型"，或遇到 Source 2 系 `.vpk` 容器、`vmdl_c` 清单时。
> **读完能做到**：用 Source2Viewer-CLI 列清单并批量导出自带 PBR 材质的 glb，读 glb 面数速查，再用 Blender CLI 转 OBJ。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_HLA_VPK_VMDL`

识别指纹：`.vpk` 容器（无加密）。

## 工具链

Source2Viewer-CLI（GitHub ValveResourceFormat，开源；本机 `${SOURCE2_TOOLS}\`）。**Source 2 系（HLA/CS2/Dota2/Deadlock）是所有引擎里挖掘成本最低的**。

- 清单：`-i <pak01_dir.vpk> -l -e vmdl_c`
- 批量导出：`-d -e vmdl_c -f "models/characters/" --gltf_export_format glb --gltf_export_materials -o <out>`——**glb 自带 PBR 材质与贴图**（vmat/vtex 自动联动，省去材质还原）。

## 选品与战果

- HL Alyx：vmdl_c 7,140 个（props 3191/architecture 679/characters 154/creatures 101/weapons 138）；584 个已导 glb 中 **≥10 万面仅 4 个**（dog 251,338 / G-Man 109,267 / Eli_end 102,892 / Alyx 100,201）。
- **★ VR 性能红线（行业特征）**：VR 双目渲染使 Valve 把全部角色网格**强制压在 10 万面内**——达标件恰好压线，同类 VR 游戏同此约束。定级 T2。
- **vmdl_c 体积 ≠ 面数**：42.9MB 的 zombie_classic 实际 <5 万面（大头是骨架/动画）。选品看导出后 glb 实数。
- glb 面数速查：python 读 JSON chunk（12B header + 8B chunk 头）→ meshes[].primitives[] mode=4 的 indices count/3 求和。
- glb→OBJ：Blender CLI `wm.read_homefile(use_empty=True)` + `import_scene.gltf` + `wm.obj_export`（4.2 新 API，旧 `export_scene.obj` 已移除）。
