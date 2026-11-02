# Anvil 引擎（刺客信条起源 ver28 ★ / AC3重置版 ver27 / 彩虹六号围攻 ver30 ✅ ver34 ◐）
> **何时读我**：用户说"提取刺客信条起源/AC3重置版/彩虹六号模型"，或遇到 `.forge` 容器、`scimitar` 魔数、R6S v30/v34 混淆条目时。
> **读完能做到**：用 GRB 知识库 python 工具直解 ver27/28 forge 索引与 CFD 资源；按 12B 条目解析 R6S v30 名字解密并导出 OBJ；分清 v34 已解/未解边界，不再重跑已知无效穷举。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_AC3R_V27`、`CASE_ONLY_R6S_V30`、`CASE_ONLY_R6S_V34`

识别指纹：`DataPC*.forge`；索引魔数 scimitar；资源容器魔数 `0x...57FBAA33/34/37`。

> **版本分支速查**：ver27/28（GRB 知识库工具）/ ver30（★ R6S Y5S3，已完全打通出模型）/ ver34（R6S Y6+，混淆层未解）。
> 同厂商历代格式同构但**条目宽度与元数据布局逐代变更**，跨版本套用布局必错——先按 ver 分支解析（见下）。

## forge 索引格式（ver27/28，GRB 知识库工具直用）

- **forge 解析直接用 GRB 知识库 python 工具**（`${ANVIL_TOOLS}\grb-kb\tools\forge_inspect.py`，克隆自 dataterminals/grb-modding-knowledgebase）：forge 索引 = scimitar 魔数 + ver(u32@9) + hdrsize(u64@13) + 索引表 @hdrsize+32，FileSet 链式（≤5000 条/组），offset 表 20B {i64 off, u64 id, i32 len}，info 表 192B（Extension u32@+16，Name@+44 定长 128）。**起源 ver28 与 GRB ver27 索引布局一致，工具直接可用**。
- 起源资产结构：62 forge / 661,838 条目（台账 `刺客信条起源模型\forge_index_all.json`）；Mesh 集中在 Egypt 系 forge（Egypt 25,902 + ext 5,205 + Duat 2,483 + AegeanCoast 2,254 + Arena 4,409）。

## .data 资源解压（CFD 容器）

- 起源老格式：CFD magic 0x1004FA9957FBAA33 相同，但 **ver=2、BlockCount 是 int16 @15**（GRB ver3 是 int32 @16），块表 {i32 un, i32 cn}×N + 每块 4B adler32 前缀；**algo=8 = Oodle**，用游戏自带 `oo2core_4_win64.dll`（ctypes，OodleLZ_Decompress 同 14 参签名）。实测解包器 `刺客信条起源模型\aco_extract.py`：**41,027 Mesh 全解仅 4 失败**（超大文件边界）。
- 起源 forge 原件 39GB 保 `刺客信条起源模型\原素材_forge\`。

## ATK（AnvilToolkit）桥接（起源/AC3R 通用）

- ATK 1.3.7（Nexus assassinscreedorigins/mods/238，Kamzik123 维护）对起源/AC3R 全支持；**ForgeFile.Deserialize 的 switch 不含 R6S ver34**（只 25/27/29/42/50），Game 枚举里 RainbowSix 是占位。
- 桥接栈：pip pythonnet → **DOTNET_ROOT=E:/dotnet-sdk/sdk + DOTNET_ROLL_FORWARD=LatestMajor**（ATK 要 net9.0，本机 10.0）。DataFile(Byte[] data, Game.X) + Deserialize → FilesByID；Oodle resolver 注入（OodleDllResolver 静态字段，dll 用 WitchyBND 的 oo2core_6 改名顶替）。
- ATK 转换管线：forge 条目 → DataFile.Deserialize → Mesh.ReadVertexData → AnvilGLTF.CreateGLTF → Blender → OBJ → 去重渲染。
- **起源 Mesh 顶点格式量化解码只有 ATK 有实现**——41,027 Mesh .data 在手，ATK 到位即可批量 GLB。

## AC3R（ver27）Mesh → GLB 已打通（2026-10-10 推翻旧结论）

**旧结论作废**：曾判定"AC3R mesh = 声明式引用，顶点缓冲在关联资源"。**错**。顶点缓冲**内联在 Mesh 资源里**，不需要跨资源组装；`Failed=True / No vertex data found` 是自研脚本在 payload 前多加了 16 字节垃圾导致的解析错位。

正确路径（**Boston 全量实测：1,828 Mesh → 1,808 GLB，98.9%**；LOD0 669/680、LOD1 512/518、LOD2 414/417、LOD3 213/213）：

```
raw  = read(.data)
df   = DataFile(byte[], Game.AC3Remastered)          # .data 本身就是 DataFile 容器
fd   = df.FilesByID 中 Type == 0x415D9568 的那条      # 0x415D9568 = Mesh 资源类哈希
br   = BinaryReader(MemoryStream(fd.Data[2:]))        # ★ 前 2 字节 FileHeader 必须剥掉
base = ScimitarClass(br, AC3Remastered, 0)           # 读 ID(u64) + Hash(u32)
mesh = Mesh(br, base)                                 # 内含 CompiledMesh，顶点/索引就地解出
AnvilGLTF.CreateGLTF(out.glb, [mesh], [], [], {})     # 5 参重载（6 参含 Animations）
```

资源 payload 布局：`[0:2] FileHeader` → `[2:14] ScimitarClass` → `[14:…] Mesh(含 CompiledMesh)`。
面数口径：`mesh.Faces.Count` **已是三角数**（BOS_LM_Tavern_GreenDragon_LOD0 = 59,392 tris / 106,595 verts）。

**AC3R 专属坑（别重踩）**

| 坑 | 现象 | 正解 |
|---|---|---|
| payload 错位 | `Failed=True`、verts=0、"No vertex data found" | `fd.Data[2:]`；**不要**"补 16 字节对齐" |
| 小样本误判 | 拿 306B 的 `*_FakeInterior_LOD0` 当格式代表 → 误判"声明式引用" | 样本跨 300B～100KB 至少 3 件再下结论 |
| GLB 目录缺失 | SharpGLTF `dinfo is invalid or does not exist` | 先 `os.makedirs` |
| ATK 日志噪声 | `Console.WriteLine` 淹没自研 print | `System.Console.SetOut(StringWriter())` |
| 手写 Mesh 构造 | `_ac3r_mesh.py` 式"自己 new Mesh" + 手动补字节必错位 | 一律走 `DataFile` → `fd.Data[2:]` 路线 |
| 渲染必达集被稀释 | 去重工具渲染阶段**不看 dedup 清单**，只遍历 `-i` 目录 | 要控范围就把目标文件复制到独立输入目录再渲 |
| 失败条目 | 10 件 NullReference（疑似 Cloth/特殊类型）+ 坏条目 | 逐条记录 + 幂等重跑，不阻塞整批 |

AC3R forge 48 个 24.8G 已保 `刺客信条3重置版\原素材_forge`；脚本 `_ac3r_batch.py` / `_render.py` 在项目目录。
Boston 1,828 Mesh（LOD0 679 / LOD1 519 / LOD2 417 / LOD3 213），Frontier 1,260。

**交付实测（2026-10-10）**：1,808 GLB + 1,808 OBJ（268 MB）+ LOD0 669/669 件 8 视角 1024 白底渲染（5,848 张 PNG）。
首轮渲染 600/669，尾部 69 件同秒集体失败（Blender `0xC0000142`）——**资源耗尽不是模型坏**：
把 69 件复制到独立输入目录重渲得 **69/69 全成功**，GLB 结构自检也 0 损坏。处置要点见 render-delivery-spec.md。
关键类哈希（`_type_census.py` 现场从 `ScimitarClassRegistry.ScimitarClasses` 反查，331 类）：
Mesh `0x415D9568`、TextureMap `0xa2b7e917`、Material `0x85c817c3`、TextureSet `0xd70e6670`、Animation `0x0fa3067f`。
Boston 资源量级（1,000 文件抽样外推）：TextureMap ≈ 8,380、Material ≈ 2,190、Animation ≈ 17,000。

## R6S ver30（Y5S3 旧 depot）★ 已完全打通，一键出 OBJ（2026-10-10 实测交付）

**数据源**：`${R6S_AUDIT}\`（DepotDownloader 拉的旧版 depot）。368 个 .forge 里 **只有 58 个有效 / 32.3GB**，其余 310 个是 DepotDownloader 预分配的**全 0 空占位**——遍历前必须先按 `scimitar\0` 签名过滤，否则整批 open 失败。

### 三处与 v34/GRB 都不同的关键差异（套错必崩）

| 层 | ver27/28（GRB） | **ver30（R6S Y5S3）** | ver34（R6S Y6+） |
|---|---|---|---|
| entries 宽度 | 20B | **12B** `{offset u64 明文, uid u32, size u32}` | 20B（混淆） |
| 元数据宽度 | 192B | **322B**（含 255B 名字 + 尾部 u64） | 全 0（退化） |
| 名字解密 | — | **FILE_KEY_STEP** `0xE684BFF857699452`，key 里 **offset 传 0** | 不可用 |

RF/RainbowForgeDK 的 `Entry.Read` 是 20B 版，**对 v30 会错位**（第 3 条起 uid 变 0/乱码）——必须自己按 12B 解析。

### v30 头 / Fat 表
`scimitar\0`(9B) + ver u32@9 + fatLocation u32@0x0D + metaKey u64@0x11(=0x1000000000) + x19@0x19 + x1D@0x1D(=1) + numEntries u32@0x1E + numDirs u32@0x22(=2) + unk2/unk3@0x26 + unk4(u32, ver≥27)+firstFreeFile+firstFreeDir@0x2A + sizeOfFat+numTables@0x36 + firstTablePos u64@0x3E(默认 74)。
Fat 表 40B @firstTablePos：MaxFile/MaxDir/PosFat/NextPosFat/FirstIndex/LastIndex/MetaTableOffset/DirectoryOffset。

### v30 名字解密（实测可读）
```python
key  = 0xA860F0ECDE3339FB + uid + 0 + fileType + (fileType << 32)   # ★ offset 参数传 0
step = 0xE684BFF857699452        # FILENAME_ENCODING_FILE_KEY_STEP
每 8 字节：out = in ^ key; key += step
```
样本：`d8 f1 30 00 | fb 2d eb ab | 5d 28 0c d0 09 00 00 00` + 0x25B 密文 → `CHR_SAT_Echo_UNF_Body_Default_LOD0_CM`（fileType=0xABEB2DFB, uid=0x9D00C285D）。

### 资源 → mesh
资源容器与 v34 **同构两层**：`magic u64=0x1014FA9957FBAA34 | u16=3 | u16 deser(3=Chunked,13/15=Chunked+Oodle,7=Flat)`，其后是 ChunkedDataBlock `u16 numChunks | u16 u2 | [un u32, pk u32]×n | [hash u32]×n | data`。**解出的 chunk 内容本身又是一层 FileContainer（再一个同款 magic）**——所以 `GetContainer().GetDataStream()` 拿到的 payload = 内层容器，`FileMetaData` 从 payload[0] 开始，mesh 体其后。

Mesh 解析（`MeshHeader` → `CompiledMeshObject`）要点：
- Header：`secondMagic/var2/var3 | magic u32=0xFC9E1595 | sizeUntilFooter | x00 | revision | vertLen | vertsDataLen | faceDataLen | vertmapsDataLen | unknownBlock1Len | faceStatDataLen | faceUnknownDataLen | ×3 | numLods | meshType | numIslands | …`
- 三个锚点：`vertBlock = 当前位置`，`trisBlock = vertBlock+vertsDataLen`，`extra = trisBlock+faceDataLen`；`tail = extra+vertmaps+unk1+faceStat+faceUnknown` 之后是 `ObjectHeader[numIslands*numLods]`(36B/条) + Bbox[numIslands] + SkinMap[numIslands]
- 顶点：`rev0` → 4×i16(x,y,z,s)，`pos = x*s/0x7FFF`；`rev1/2` + vertLen ∈ {0x18,0x1C,0x24,0x28,0x2C,0x5C}。法线/切线/副法线 = 每字节 `c/0x7F-1`；UV = 两个 half
- 三角：每 island 的 `NumFaceChunks × 64` 个 (a,b,c) u16，剔除 `a==b / b==c`
- **LOD0 = ObjectHeader 表的前 numIslands 条**（表按 LOD 分组：8 islands × 6 lods 时前 8 条即 LOD0，是最高模）
- 顶点为 **Z-up**（Amaru bbox Z[0,1.62]），OBJ 直交 Blender 无需转轴

### 工具链（本项目目录 `3D渲染\彩虹六号模型\`）
`r6s_mesh.py`（纯 python mesh 解析+OBJ 导出，无 pythonnet 依赖）/ `r6s_batch.py list|meta|dump`（解压取 payload → OBJ）/ `y5s3_survey.py`（全量面数盘点）/ `r6s_render.py`（官方去重工具 8 视角）/ `flatten_white.py`（RGBA→白底）/ `y5s3_inventory.py`（forge 有效性清单）。

### 面数口径结论（★ 立项前必读）
全量 1,081 件 ≥200KB mesh：**最高仅 44,048 面**（训练场尸体），场景大件 40–44k，干员身体密集 **34–35k**，武器 15–25k，**全场无 ≥10 万面件**。R6S 与二次元系同属中模量级——价值在题材（写实战术射击）与贴图，不在几何面数。

## R6S v34（自研逆向 90%，卡最后混淆层）

- **Y6+ 反 modding 三层闭环**：entries 混淆 + 数据 4KB 块散布 + 块映射表——社区零公开破解（2022 至今）。
- **v34 头布局（六 forge 对拍锁定）**：magic9B + ver u32@9=34 + fatLocation u32@0x0D（v34 用 u32 非 u64）+ metaKey u64@0x11=0x10 + u32=6@0x1E（v34 新增常量）+ numFiles u32@0x22 + numDirs=2@0x26 + totalFiles+2@0x3E + numTables=1@0x42 + firstTablePos u64@0x46=78。Fat 表 @78（40B）：MaxFile/MaxDir/PosFat/NextPosFat/FirstIndex/LastIndex/MetaTableOffset/DirectoryOffset。**entries 表 20B/条：{混淆offset 8B, UID u64 明文, 混淆size 4B}**（低 4B 第 2 字节每条 -0x10 的规律；size 高 16 位恒 0x5108）。
- **资源块头**：magic u64 = 0x1015FA9957FBAA37 + x u16=3 + deser u16=15（deser15 = Oodle 版 ChunkedDataBlock）。容器层已 100% 打通：fork 的 GetEntryStarts 第三 u64 签名放宽 `!= 0` 后 108/108 资源 payload 解压落盘（pythonnet 反射调 fork，oo2core_8 用 ATK 的 oo2core_9 改名顶替）。
- **卡点 = deser15 表混淆**：表项呈 `00 04 00` 恒定 3B 前缀 + 乱序字节（非明文 un/pk）；大资源的表经过变换，小样本 (un=pk) 例外。Oodle 盲扫全是 fuzz-safe 假阳性——**必须先定表再解压**。
- **v34 entries offset 混淆已定性（2026-10-10，暴力破解阶段结论）**：低 32 位是**页号的负计数**——相邻条 `low32[i]-low32[i+1]` **逐项等于物理 4K 资源页差**（v34 资源按文件顺序紧密倒序排布，`magic 0x1015FA9957FBAA37` 就是每资源起点）。**已穷举排除**：XOR 常量、`K-low32` 加法、线性同余 `a*x+b mod 2^32`、字节旋转/置换、纯位翻转（bit12/13/14 是翻转谱主频，与页号 bit0/1/2 对应但整体映射非线性）。
- **v34 size 字段未解**：高 16 位恒 `0x5108`（key 残留），低 16 位与真实 gap **无** XOR / 加减 / 字节旋转关系 → 疑为摘要或独立编码。
- **v34 payload 未解**：解压后 payload[0:2] 是变化的 1 字节（0x18/0x1a/0x1b/0x1c/0x20）+ `00 02`，其后无 ASCII 名字（v30 同位置是明文可解 FileMetaData）→ **payload 的 FileMetaData 区被整体变换**，未定位 mesh 体。
- **无效穷举陷阱（勿重跑）**：Oodle 盲扫、`K1/K0` 双字节穷举（16384 组全同构）、锚点法搜 K、字节旋转/置换穷举。
- **决胜动作（已存档待专项）**：写"RF ChunkedDataBlock 参数化穷举器"——穷举 {numChunks 位置+端序}×{项宽 8/12/16}×{表偏移}，验证器 = sum(packed)≈资源长-表长 + 每 chunk Oodle 解压成功 + 首 4 字节合理。
- **替代路线（★ 已于 2026-10-10 落地出模型，见上一节）**：Y5S3 旧 depot（ver30 = 自研 12B 条目解析直接出模型）+ 同 UID 新旧资源做已知明文对拍反推 v34 混淆 key。**v30 `datapc64.forge` 88 条明文 {offset,uid,size} 已全解出**，可直接做「已知明文 ↔ v34 混淆值」差分表。下载脚本 `${R6S_AUDIT}_下载.bat`（DepotDownloader 直跑，**self-contained 单文件 exe 勿加 dotnet 前缀**；预分配陷阱：du 恒定不能反映进度，用进程 WriteTransferCount 判活）。
- 工具资产：`${ANVIL_TOOLS}\RainbowForgeDK\`（fork 编译产物 + ver34 patch）、`rf_payloads2.py`（pythonnet 一键解压）、`_gi_scan/_flat_scan`（扫描器）。R6S forge 47G 保 `彩虹六号模型\原素材_forge`。
