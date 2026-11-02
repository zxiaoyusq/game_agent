# MT Framework（怪物猎人：世界）
> **何时读我**：用户说"提取怪物猎人世界模型"，或遇到 MT Framework/卡普空系容器、`chunk/chunk0.bin`（`CMP\0`）、`.mod3` 模型时。
> **读完能做到**：按游戏自带 oo2core 版本判定是否冰原并跑 WorldChunkTool 解包，再用 fake bpy + mathutils shim 在无 Blender 环境 headless 把 mod3 转 OBJ。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_MHW_CHUNK_MOD3`

识别指纹：`chunk/chunk0.bin`（17.8GB，魔数 `CMP\0`）；模型 `.mod3`、材质 `.mrl3`、贴图 `.tex`。

## 版本判定（关键，两次实测踩坑）

- 游戏根目录**自带 `oo2core_5_win64.dll` = 基础包（无冰原）** → WorldChunkTool 必须 `-BaseGame -AutoConfirm`；冰原包才用 oo2core_8 + 默认模式。
- **用错模式不是报错而是"合法解析 33 分钟零产出"**——以"游戏自带哪个 oo2core"判定版本，不要猜；`-BaseGame` 缺 dll 直接崩，复制游戏自带的，勿从网上随机下载。

## 解包与转换

```
WorldChunkTool.exe <chunk0.bin> -BaseGame -AutoConfirm
```

产物按原始路径落盘（em/ 怪物 105 个 mod3、pl/ 玩家装备）。表解析 CPU 密集（17.8GB 约 20-30 分钟）属正常。

**mod3 → OBJ：Headless 自解析**（社区 Blender 插件在 Blender 3.6/4.5 导入即 ACCESS_VIOLATION；但 Mod3-MHW-Importer 的解析层 mod3/ 目录 12 文件零 bpy 依赖）：

1. **fake bpy 体系**（import 前注入 sys.modules）：bpy.types 用可子类普通类、bpy.props 返回 `lambda **k: None`、bpy_extras 同 types、bpy.utils/ops/context/app 用 MagicMock。
2. **自动兜底导入器**：自定义 MetaPathFinder 放 sys.meta_path 末尾——真模块正常加载，不存在的 Blender 专属模块（bmesh/idprop）返回 MagicMock。
3. **mathutils**：PyPI 无 3.11 wheel → numpy 后端 shim（Vector/Matrix/Quaternion/Euler 约 80 行）。
4. **HeadlessAPI**：实现 Mod3ToModel 调用的 12 个 Api 方法；核心 createMeshParts 收集 vertices/faces/uvs/normals 直写 OBJ。
5. **options 最小集**：`{"Mesh Parts": True, "Split Weights": "Group"}`。

转换器 `E:\Gameprogram\yysls-audit\research\mhw\headless_mod3.py`（可复用于任意 mod3）。实测 em106（29.1MB）→ 918,924 面；em100 → 183,549 面。怪物档案 ID：`em/emXXX/00/mod/emXXX_00.mod3`（按体积排 = 大型怪）。
