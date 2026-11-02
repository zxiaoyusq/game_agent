# NeoX / Messiah（燕云十六声）
> **何时读我**：用户说"提取燕云十六声模型"，或遇到 NeoX/Messiah 米哈游系容器、`EZST` magic、`Patch*.mpk` + `Patch.mpkdb` 时。
> **读完能做到**：按 EZST 记录结构枚举 K 并完整解压验证（避开 AES-ECB 首块恒命中的假 K），跑通燕云 mpk 全量扫描与补丁增量重扫。
> **范围**：`GENERAL_DEFAULT` + `CASE_ONLY_YANYUN_EZST`

识别指纹：包记录魔数 `EZST`；`Patch*.mpk` + `Patch.mpkdb`。

## 格式与算法（自研破解，1200/1200 = 100%）

```
记录 = 'EZST'(4) + u32 declared_size(4) + payload
payload = [前 K 字节 AES-256-ECB 密文] + [其余为明文 zstd 流]
K = 16 的倍数；枚举取第一个能精确解出 declared 字节的 K
密钥 = 753572326e586a556728153f912f78385667536250613b2d397636733370596b
```

证据链：解压器注册表 `.data` VA 0x147FDCA80 → EZST 虚表 0x14584CBC8 [3]=Decompress=0x141D03A00 → 变换 0x14438BDD0（240B 上下文 = 15×16 轮密钥 = AES-256，密钥硬编码于 0x14438BCF0）。变换长度 `min(对齐(size)-16, 256)` 与实测 K 分布吻合。**静态磁盘拿不到算法**（`.text/.rdata` RawSize=0，藏于 62MB 加密段 `.33V`），必须运行时只读转储。

## ★ K 枚举的 ECB 陷阱（全量扫描实测）

- 判据**不能**用"解密后首 4 字节 == zstd magic"——AES-ECB 各块独立解密，**任意 K≥16 的枚举首块结果完全相同**，K=16 恒命中（7,892/7,892 条假命中）。
- 正确判据：对每个 K∈{16,32,…,256}，拼接 `AES_dec(payload[:K]) + payload[K:]` **完整解压（流式读到 declared+1 即停）**，输出长度 == declared 才是真 K（实测一条 1.5MB 记录真 K=80）。
- 流式解压验证 K 时**必须读完整记录**：只读头部 512KB 会导致 declared 永远对不上、全部误判 noK。

## 工具与战果

- 解码器：`E:\Gameprogram\3D渲染\燕云十六声模型\_research_offline_v13\ezst.py`（offline_v12 已删，v13 为重建版）。
- 全量普查性能：53,816 条记录（v1≥0.9MB）先读 4 字节验魔数、仅 EZST 读全文，7,892 条完整解压 ≈ 4 分钟；≥10 万面达标 204 → 剔结构异常（tris/vnum 比例 >8 或 <0.5）→ 175。
- 补丁增量：补丁版本涨 521 个 mpk 属正常，重跑全量扫描即可补齐（管线幂等）。
