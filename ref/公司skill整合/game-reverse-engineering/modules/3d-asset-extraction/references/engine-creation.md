# Creation Engine（辐射4：BA2 / NIF）
> **何时读我**：用户说"提取上古卷轴/辐射4模型"，或遇到 `.ba2`（BTDX 魔数）、Creation 容器、`.nif` 模型、DX10 贴图条目时。
> **读完能做到**：直解 BA2 GNRL/DX10 条目取出 nif 与贴图（DDS 输出体积逐字节对齐 mip 链和），并用 PyNifly headless 把 nif 转 OBJ。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_FO4_BA2_V7_V8`

识别指纹：`*.ba2`（BTDX 魔数）；模型 `.nif`。

## BA2 容器（GNRL 直解）

头 24B：`BTDX` + ver（老版=7，次世代=8）+ GNRL/DX10 + numFiles(u32) + nameTableOffset(u64)。

- **GNRL 条目**：ver8 步进 36B（hash4+ext4+dir4+flags4+offset u64@16+packed@24+full@28+4B 尾），ver7 步进 32B（offset@12）。flags&0x100=zlib **直接流**（78 9c，无 4B 前缀）。名字表 @nameTableOffset：u16 len + 路径。
- 提取器 `辐射4模型\ba2_extract3.py`（多进程容错版；**单进程版遇坏条目静默死，必须容错+多进程**）。FO4 全量 = 193,434 文件 / 94,819 nif。
- 79 ba2+6 csg（32GB）原样保 `辐射4模型\原素材_ba2\`。本机是次世代更新版（ver8 含新压缩分支）。

## DX10 贴图条目（2026-10-10 实测破解）

**不是定长条目表，是变长记录流**：

```
记录 = dirHash(4)+ext(4,恒'dds\0')+fileHash(4)+meta(12)+块头×n
meta = [4B忽略][w u16@4][h u16@6][mips u8@8][fmt u8@9=DXGI][flags u16@10]
块头 = off u64 + ps u32 + us u32 + tag4 + sep4（sep=0d f0 ad ba，BAADF00D）
```

- **块数不定**（整条 mip 链可压成一块或按 mip 切）——用**下一条记录 +4 处的 'dds\0' 特征 lookahead 定界**（探 8B：b8[4:8]=='dds\0' 即新记录头）。
- mips 数 = DDS mipMapCount；fmt 直接进 DDS DX10 扩展头；flags&1 = cubemap（caps2=0xFE00）。
- **末条记录后面直接是数据区**（无终止符）——chunk 校验失败即表结束，别当错误。
- DDS 拼装 = 148B 头（magic+124+flags+H+W+0+0+mips+11×0+ddpf(FOURCC 'DX10')+caps+caps2+DX10 五元组）+ 各块解压（zlib，ps<us 时）串联。
- **自验证：输出体积必须逐字节等于理论 mip 链和**（BC1 2048² 12mips=2,730KB、BC5 1024² 11mips=1,365KB）。
- ver1 与 ver7 布局相同；ver8 未验。提取器 `辐射4模型\fo4_dx10_extract.py`。
- 模型贴图定位：python 正则从 NIF 抽 `[\x20-\x7e]{4,}\.dds` 引用 → 按后缀匹配 ba2 名字表（**NIF 内路径无 textures\ 前缀**）。

## NIF → OBJ

**PyNifly**（BadDogSkyrim，release zip 装 portable addons）→ headless `import_scene.pynifly` → `wm.obj_export`。

## 选品与战果

- **nif 选品按体积**：top 是特效/场景拼装件（SCOL/DemoFX），角色 BOSS 在 Actors/ 下体积中等（4.6MB 已是 15 万面）。
- 首件 LibertyPrime 152,303 面 8 视角白底交付；25 张引用贴图全提取（DX10 重组）。

## BA2 变体陷阱

DLC 档可能混 ver1/ver7/ver8 三种版本（本机实测同目录共存）——解析器按版本分支，未知版本先跳过打日志。
