# CRIWARE（尼尔机械纪元：CPK → DAT/DTT → WMB3）
> **何时读我**：用户说"提取尼尔机械纪元模型"，或遇到 CRIWARE 音频容器 `.cpk`、`DAT\0` 容器、`WMB3` 模型时。
> **读完能做到**：用 CriPakTools 容错版整包抽 CPK 并批量解 DAT/DTT 容器，读 WMB3 面数，在 Blender ≥4.2 装 NieR2Blender2Nier 后 headless 导 OBJ，贴图 wtp 直接当 DDS 用。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_NIER_CPK_WMB3`

识别指纹：`*.cpk`（CPK 魔数）→ `DAT\0` 容器 → `WMB3` 模型。

Steam 版 `data\`（28 CPK/41GB）。工具 `${NIER_TOOLS}\`（CriPakTools + NieR2Blender2Nier 克隆）。战果：1822 wmb 解析 / **≥10 万面 250 件**（top = 场景 g52001 155 万、BOSS em4000/em4010 114 万）。

## 三层结构

1. **CPK**：CriPakTools（net10.0 重编译）原版抽区固定写 CWD、不认输出目录——已加 `-o OUT_DIR` 与单文件 try-catch 容错。**CRILAYLA 解压 EOF 是固定崩点**（FileSize 与实际短读），容错版可整包跑完。
2. **DAT/DTT**：CPK 内模型在 `DAT\0` 魔数容器（.dat/.dtt 成对，非明文 wmb）。格式：头 0x1C = FileCount/FileTableOffset/ExtensionTableOffset/NameTableOffset/SizeTableOffset（全 u32）；entry = FileOffset/4B 扩展名/Size/定宽名。批量解包 `dat_batch_extract.py`（7,135 容器 → 43,697 内部文件）。
3. **WMB3 面数**：魔数 `WMB3`，**bbox 实为 7 floats，meshArrayOffset@0x40 / meshCount@0x44**（NieR2Blender2Nier 源码头注释差 4 字节，以实测为准）；mesh 条目 0x1C，faceCount@+0x14 是**索引数 ÷3 = 三角面**。扫描必须校验「mesh 表在真实文件大小内 + faces 为 3 的倍数」，否则算出垃圾值。

## Blender 导入（NieR2Blender2Nier，≥4.2）

①便携版 legacy addons **必须装 `portable\scripts\addons\`**（4.2\scripts\addons 不被扫描）；②目录内 `blender_manifest.toml` 要删；③**不能 read_homefile**（会注销 addon 类）——enable 后手动删默认对象；④`hasattr(bpy.ops.x, 'op')` 恒 True 不可信，看 OPS 列表。
- wmb→OBJ headless：`尼尔模型\wmb_to_obj.py`；em4000（114 万面）约 3 分钟，OBJ 177MB 自带 mtl。
- **wtp 贴图本身就是完整 DDS**（魔数 DDS + BC7）——直接改名 .dds 即用，零转换。

## 通用坑

含中文路径调去重工具：bash→cmd 传参与含中文 bat 双双必炸——**绕法 = python subprocess 用 Blender 自带 python 直跑 main.pyc**。
