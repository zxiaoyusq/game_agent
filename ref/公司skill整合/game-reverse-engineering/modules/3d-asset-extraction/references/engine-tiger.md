# Tiger 引擎（命运 2 / AKPK `w64_*.pkg`）
> **何时读我**：用户说"提取命运2模型"，或遇到 Tiger 引擎的 `packages/*.pkg`（AKPK + Oodle）时。
> **读完能做到**：按 Charm 无头宿主的五个必踩坑自研批量导出器，枚举 `SStaticMesh`/`SEntity`，按拼装成套与碎片度出 OBJ 与贴图，并守住不再分发的合规线。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_DESTINY2_TIGER`

识别指纹：`<安装>\packages\*.pkg`（AKPK 魔数，Oodle 压缩）——本机 2,458 个 / 152.82GB（已卸载，E 盘有全量提取成果）。包内是 Tiger 的 tag 图（`SStaticMesh`/`SEntity`），游戏 bin 不带 oo2core，用 Charm 自带 `ThirdParty\oo2core_9_win64.dll`。

## 工具链唯一选择 = Charm

`gh release download v3.3.6 --repo MontagueM/Charm --pattern 'Charm_Latest.zip'`（含 Tiger.dll / EntityNames.json / wordlist.txt.gz / keys.txt / ThirdParty）。发行版是 WPF GUI，**批量必须自研无头宿主**（本机 `3D渲染\命运2\d2tools\D2Export\`，net10.0-windows，直接 Reference Tiger.dll）。

**自研宿主五个必踩坑**：

1. **私有程序集加载**：Tiger.dll 若 `Private=false`，.NET Core 不探测 app base 目录 → FileNotFoundException。修法 a) `Private=true`；或 b) false 但**在 Main 第一行注册 AssemblyResolve，并把引用 Tiger 类型的代码隔离到 `[MethodImpl(NoInlining)]` 的另一方法**——否则 Main 的 JIT 在注册前就解析了 Tiger 类型 token。
2. **`TigerArgs` 是空格分隔**：传 `-strategy DESTINY2_LATEST` 两个参数，`-strategy=X` 会 IndexOutOfRange。
3. **子系统注册必须按 `[InitializeAfter]` 拓扑排序**（照抄 Charm MainWindow.xaml.cs 的 SortByInitializationOrder），乱序 → "Strategy instance has not been created"。
4. **`config.json` 认当前工作目录**——必须 cd 到 Charm 发行目录再跑，否则静默写默认配置 → "Strategy does not exist"。
5. 策略名 `DESTINY2_LATEST`；首次启动建 PackagePathsCaches（2,458 包约 5s）。

**别走弯路**：DestinyUnpacker/d2pkg 只解 pkg 容器、不含 mesh 提取；**Charm 已把 Tiger 的 tag 图、顶点/索引缓冲、材质、贴图全解完**——先搜 Charm，不要先写解包器。

## 枚举与导出

- `PackageResourcer.Get().GetAllHashesAsync<SStaticMesh>()` → 215,168 静态网格；`<SEntity>` → 84,064 实体 tag。
- `FileResourcer.Get().GetFile<StaticMesh>(new FileHash(h)).Load(ExportDetailLevel.MostDetailed)` → `List<StaticPart>`；实体 → `List<DynamicMeshPart>`。
- **成套拼装 = `entity.GetEntityChildren()`**（ModelParent/PhysicsModelParent/EntityChildren/Attachments/CarriedWeapon 全挂在一个 entity 上）；**面数必须按拼装后算**（单件 vs 含子件差一倍以上）。
- OBJ 直写绕过 FBX/Assimp：`part.VertexPositions` + `part.Indices`（strip 已转三角）→ Dictionary<uint,int> 索引重映射，逐行 v/f。
- 64 位哈希串先 `Hash64Map.Get().GetHash32Checked(str)` 转 32 位。`EntityNames.json` 的键不是 SEntity tag 哈希，别拿它反查名字。
- 空几何兜底：NaN/Inf 清零、无面部件跳过，否则 Blender 归一化抛异常。

## 完整性判定（★ 别用「数洞」）

- **`boundary == 0`（水密）不能当"完整资产"判据**——实测全库仅 10 件水密且多为岩块/球体；成套角色（装甲片/开口披风/独立尖刺）天生带边界边 1.4%~14%。
- 正确口径：①`kids > 0` = 拼装成套；②**碎片度 = 三角面 ÷ 连通壳体数 ≥ 30~50** 剔碎块（完整角色 1,500~4,000）。分档交付：T1 水密 → T2 近水密（br≤0.002）→ T3 成套，不混成一个"合格"数。
- 贴图：`material.Pixel.EnumerateTextures()` + `tex.SavetoFile()` 直出 PNG；角色件 `entity.SaveTexturePlates(dir)` 出全身四张板（要求 ModelParent != null，否则静默空目录）。
- **库内贴图去重用同卷硬链接**（os.link + os.replace 原子替换）：同模型族贴图几乎全重复（实测 10,748 张里 8,991 张相同，省 10.93GB），每目录仍独立自洽。

## 结构性结论（全量实测）

静态网格占 tag 总数 72% 但 **96.6% 不到 5,000 面**——Tiger 把场景切成几千个模块化小件复用，没有整张烘焙场景网格。**别拿"包体大"推断"高模多"**（152GB 里 27.84GB 是视频）。达标 304 件（≥10 万面）与尼尔同级。

**合规**：Bungie 对 datamining 有法律行动史。本地离线解包研究 + 白底几何快照可，**原素材/贴图不得再分发**。
