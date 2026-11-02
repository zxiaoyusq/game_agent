# FromSoftware（黑魂3 / 只狼 / 法环）
> **何时读我**：用户说"提取法环/黑魂3/只狼模型"，或遇到 `Data*.bdt/bhd`、`.chrbnd.dcx`、FLVER/TPF 格式时。
> **读完能做到**：按游戏选对 BHD 解包器（黑魂3 用 BinderTool 0.5.2）递归解 bnd 拿明文路径与 FLVER，头直读面数初筛，跑 FLVER→FBX 与 TPF→DDS 两套判据出模型与贴图。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_DS3`、`CASE_ONLY_SEKIRO`、`CASE_ONLY_ELDENRING`

识别指纹：`Data*.bdt/bhd`；模型 `.chrbnd.dcx`/`.flver`，贴图 `.tpf`。

## 解包工具选择

- **BHD 头部加密**（磁盘魔数不是 BHD5）：WitchyBND 处理不了。
  - 法环：`ER.Unpacker.exe <Data3.bhd> <out>`（BouncyCastle 解密 + oo2core，dll 须在工作目录）
  - 只狼：UXM Selective Unpack（密钥内置）；UXM 是 GUI，UIA 自动化三步（set_value 写路径 → invoke Unpack → 读 Status/ProgressBar）实测可行但**黑魂3 UIA 不稳**，弃。
  - **黑魂3 = BinderTool 0.5.2 纯 CLI 首选**（`${FROMSOFT_TOOLS}\bindertool052\`，DS3 密钥内置）：`BinderTool.exe <X.bdt> <out>` 自动解密同名 BHD 并按 8 包解出。**0.7.0-pre4 有致命 bug**（写文件抛 IOException"句柄无效"静默崩），必须 0.5.2。
- **容器扩展名是钥匙（DS3 特有）**：BDT 解出后只挑 `.bnd` 会漏大头——`.chrbnd`（角色）/.mapbnd（地图）/.partsbnd（装备）/.objbnd（物件）/.anibnd 全部要再跑 `--extract-bnd` 递归。解出后是 `INTERROOT_win64/chr|map|obj|parts/...` 明文路径 + FLVER。
- WitchyBND 拖入 `.chrbnd.dcx` 一次递归解出 .flver（交互场景好用；但 **WitchyBND 拒绝输出重定向环境**，PromptPlus 检测 `-s` 也拦不住——批量 CLI 用 BinderTool）。
- FLVER→FBX：**SoulsModelTool 单参数** `dotnet exec --roll-forward Major SoulsModelTool.dll <x.flver>`（多给输出参数会把它当输入读而报错）。dll 在 `${AQUA_TOOLSET}\bin\net9.0-windows7.0\`。

## FLVER 面数直读（免解析 mesh）

头 `FLVER\0`，0x08 version=0x20013/0x20014，**0x40 = 有效面数 / 0x44 = 总面数（uint32）**；与 Blender/OBJ 实测差约 45%（含背面/双材质面集），**交付口径以 OBJ 实测为准**（c6211：头 538,691 → 实测 299,256）。最大的 chrbnd = 巨型 BOSS（只狼 c5200=樱龙 10.4MB；法环 c4760=火焰巨人 36.9MB；DS3 top = o502080 93.3 万面/c6211 53.9 万面）。

## TPF 贴图直解（2026-10-10，免 Yabber 的 python 判据）

TPF v3 头 12B = `'TPF\0' + totalSize u32 + count u32`；每贴图条目 24B = `A(恒0x00010300) + fmt(DXGI u32) + size + B(0x00010066) + nameLen + C` + nameLen 字节 UTF-16LE 名。

- **count==1 且字段合法**：数据紧跟名后（4B 内找 `'DDS '`），可直接切出完整 DDS。
- **count>1 或字段异常 = 变体布局**（条目/名字表分离，c6xxx sfx 包实测）——**别硬解，走 Yabber**（`${FROMSOFT_TOOLS}\yabber\Yabber 1.3.1\yabber.exe <x.tpf>` → 输出 `<名>-tpf/` 目录收 dds）。
- 批量脚本参考：`3D渲染\黑魂3模型\tpf2dds_all.py`（直解）+ `tpf2dds_yabber.py`（Yabber 兜底，幂等）。DS3 全量 = 4,678 tpf → 11,862 dds。

## 战果参考

DS3：9,212 FLVER 解析 / ≥10 万面 1,304 件（chr76/obj101/map1121/parts6，单游戏最高）；解包文件名是 hash（UXM 字典未命中），BND 内部名明文不影响选件。首件 c6211（环印城 BOSS）29.9 万面交付。台账 `_flver_faces_all.json`。
