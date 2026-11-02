# Unity/米哈游 blk 族（绝区零 mhy1 ★ / 星铁 ENCR ★★）
> **何时读我**：用户说"提取绝区零/星穹铁道模型"，或遇到 `mhy1/mr0k/ENCR` blk 块 + IL2CPP 时。
> **读完能做到**：按 mhy1 与星铁 ENCR 两条链解开 blocksInfo 与块（重点：k1^k3 必须写回 [0x84:0x94]），并用自研 zzz_mesh.py/zzz_export.py 绕过 UnityPy 2019.4 模板错位导出网格。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_ZZZ_MHY1`、`CASE_ONLY_SR_ENCR`

识别指纹：`mhy1/mr0k/ENCR` blk 块 + IL2CPP。

**权威实现来源**：`Escartem/AssetStudio`（GI 4.6+/SR 2.7+/ZZZ）与 `Escartem/AnimeStudio`——密钥材料全部硬编码在其源码（CryptoHelper.cs + MhyFile.cs），**不存在"用户输入 block key"**。国内拉 GitHub 用 `gh-proxy.com/https://github.com/...` 镜像。RazTools/Studio 2023-05 停更，仅适合 1.x。**UnityCNBurst 是范畴错误**：只认 UnityFS + `#$unity3dchina` 签名（PGR 等 UnityCN 游戏），米哈游 blk 族根本不走这套。

## mhy1（绝区零 2.x）全链（python：`绝区零模型\_memscan\zzz_mhy1.py`）

```
blk = mhy1(4B) + u32 blocksInfoSize(LE)   ← mhy1 后【没有】\0，ReadStringToNull(4) 到 4 字符即停
blocksInfo 解扰（ZZZ 与 GI 共用同一套 GI 表——零版本轮换秘密）：
  1. DescrambleChunk(GF256 扰码 3 轮, 16B/块) @ [4:20] → 必须出现签名 "mhynewec"
  2. DescrambleChunk @ [20:36]；seed = blocksInfo[0:16]（原始文件字节直接当 AES key）
  3. AES-128-ECB 加密(seed, data[20:36]) 写回；blocksInfo[0:4] ^= 密文[0:4]
  4. 变体 RC4（256B 硬编码 Key 表；key=[20:28]、op=[28:36]；op[i%8]%3 → XOR/减/加）@ [52:128]
blocksInfo[48:] → ReadMhyUInt(7B 乱序 b1|b6<<8|b3<<16|b2<<24) → Oodle 或 LZ4 → 节点表+块表
  （ReadMhyInt 6B 乱序 b2|b4<<8|b0<<16|b5<<24；ReadMhyString 按 0x105 对齐；Oodle 判据=压缩流首字节 0x8C，ZZZ 2.0+ 全 Oodle）
每块 DescrambleEntry2（entrySize=8 → RC4 @ [36:128]）→ Oodle/LZ4(block[28:]) → 拼块流 → 节点切文件
```

- **python 移植坑**：bytearray 切片是拷贝，C# Span 是引用——扰码/RC4 必须按 (buf, off, len) 原地写回；多进程 worker 不能从 stdin 脚本起（写成 .py 文件再跑）。
- 跨块引用：Mesh 的 resS 常在同一 blk 内（节点表可查）；建 CAB→blk 索引只需解 blocksInfo（每 blk ~50ms）。
- **反推陷阱**："keystream 前 12 字节"（UnityFS 已知明文 XOR）是红鲱鱼——那是 blocksInfo[0:16]（AES seed）与 UnityFS 的 XOR 巧合。**不要沿着 keystream 走**。

## ZZZ 2.x Mesh 解析（类型树被剥离 → 自研 `zzz_mesh.py`/`zzz_export.py`）

- **发行版对象数据无 EditorExtension 的 2×PPtr**（platform==NoTarget 才有），直接从 m_Name 开始；UnityPy 内置 2019.4 模板因此差 24B 起步全错。
- ZZZ 2.x Mesh 尾部专属块（AnimeStudio IsZZZ 分支）：MetricsDirty/CloseMeshDynamicCompression/压缩等级×3/PackSkinDataToUV2UV3/BakeBVH×2/BVHBakeLevels/BakedBVHSize(u64)/BVHDataBuffer/额外 u64。个别 mesh 仍差 8~11B——**统计只依赖前段，尾部容错即可**。
- **StreamingInfo = offset u32 + size u32 + pathLen u32 + path**（比标准多一个路径长度前缀，pathLen=len(path)+1）；解析错位时倒向锚定 `.resS` 回溯 12 字节取 (offset,size)。
- 顶点通道 dimension 字节偶发异常：用"同流下一通道偏移"钳制真实维度；**16B 对齐只作用流间基址，不改顶点 stride**。
- 拓扑面数：Triangles=ic/3，Strip=ic-2，Quads=ic/4×2；索引要加 baseVertex。
- **风格结论**：ZZZ 低模（唯一 ≥10 万面是特效；贴花合批占 79%；角色分件最高 20,053 面）。要高模必须按角色/场景合并分件。

## 星铁 ENCR block（4.6 终局：2022 密钥至今有效）

资产 `StarRail_Data/StreamingAssets/Asb/Windows/*.block`（容器魔数 `ENCR\0`，头全大端：signature(5B)+Int64 totalSize+u32 cbi+u32 ucbi+u32 flags(0x43)；blocksInfo=LZ4HC 未加密全 BE）。块解码（python `星穹铁道模型\_memscan\sr_mrk.py`，与 AnimeStudio 编译版逐字节互证）：

1. 块头 `mr0k`(flag=7) → Mr0k 解密（flag=6 无 mr0k 头直接 Oodle）；key1=[4:0x14]、key2=[0x74:0x84]^IV、key3=[0x84:0x94]；k1=AESdec(key1,EXP)、k3=AESdec(key3,EXP)、k1^=k3；
2. **★k1^k3 必须写回块内 [0x84:0x94]**——该 16 字节是后续 Oodle 流的一部分，漏写 = 全线失败且无报错指向（最大坑）；
3. seed = seed2^seed1^(seed1+(uint)块长-20)；pad = seedB[i%8]^BlockKey[i] 异或数据区前 ≤1024B；
4. 剥 0x14 → **OodleLZ_Decompress（oo2core_9）**，expected 必须精确 = blockInfo.uncompressedSize（差 1 字节返回 0）；块内容全部 Oodle（流首 0x8C），不是 LZ4；
5. 拼块流 → 节点切 CAB-xxx（SerializedFile）+ .resS。SR 网格 = 标准 2019.4 布局，**UnityPy 可直接读**。

2022 三件套（EXP 176B/BK 1024B/IV 16B）4.6 仍有效（AnimeStudio CryptoHelper.cs 公开可考）。SR 角色分件（Body 单件最高 41,004 面），拼合合格第一 = monster_w2_huanlong_00（幻胧）56,732 面已交付。

**方法论教训**：曾误判"格式改版/新加密"——根因是自家 python 三个 bug（漏写回/LZ4 代替 Oodle/Oodle expected 错误）。**金标准 = 编译参照实现互测 + 双实现逐字节 diff**，指纹搜索只能当辅助。工程坑：oo2core ctypes 畸形流会越界读写 → python 静默崩 rc=127——缓冲必须加垫片；**临时文件一律放项目目录**（C 盘曾被 temp 写满致 3,571 容器首轮失败）。
