# Carrom 比较器原件衍生证据复核

## 1. 当前阶段、范围与结论

- 项目：548c31d9d0344831a349d3163c5cab93；阶段：prototype；attempt=1。
- 本轮是证据复核，不是新游戏原型实现。不推进美术、代码或测试阶段，不改排序或玩法。
- **本 MCP 收到并读取的是三份 JSON，不是原始 so。未独立读取、哈希或反汇编原始库，未执行目标代码。**
- 本轮验证方式：读取工具返回的完整 JSON，人工复算 ASCII 长度/NUL、地址与槽位算术、ELF64 r_info 拆分，按小端 AArch64 指令编码人工复核所列 38 条机器码，并逐条对照旧指令文本。不使用独立解码器；无执行验证日志。
- 总结：提供的名称字节、5 组名称映射和 RELA 元数据、38 条比较器机器码/旧指令文本未发现内部矛盾。这只支持“衍生材料内部一致”，不能提升为“原件真实性已独立验证”。调用侧窗口只有指令文本，不能完成其机器码一致性验证。
- 名称—候选类型信息—表槽—候选代码地址存在一致的静态关联；运行顺序、字段业务语义、实际比较器调用和真实 AI 行为仍未闭合。

状态使用：PASS 只指注明范围的内部核对；BLOCKED 指缺原件/运行环境；NEEDS_CONTEXT 指缺项目事实。没有整体运行验收 PASS。

## 2. 参考与资料

以下路径相对 `ref/`，均由 read_reference 实际读取：

- E-01：`mcp-inputs/mac-codex/6bb4656c18abf6f8a51e1fe87e8d64d58af6cb9432b46c2934a43c33b34d4ae5/carrom_comparator_original_bytes.json`。
- E-02：`mcp-inputs/mac-codex/0b5a62678c4fc6a931cd251afffb789d7ab0df611605839f6e622cfa1b356a87/carrom_comparator_context.json`。
- E-03：`mcp-inputs/mac-codex/f43333b056f79b5f23746ec8c70ba55c11888ee39dd18353d9167bb823c0cc61/carrom_comparator_relocations.json`。

三者声明的源库 SHA256 均为 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`。本轮确认的是该字符串相同，并未确认原库实际哈希。目录中的哈希样式字符串不能替代本轮对文件内容的独立哈希。

已实际读取冻结资料：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/native-web.md`；选定技能 `game-reverse-engineering/SKILL.md` 及同包 `references/execution-protocol.md`、`global-rules.md`、`native-code-evidence.md`、`unknowns-ledger-template.md`。采用其证据分级、PT_LOAD 地址模型与未知清单方法。没有引擎身份资料，不选择 Unity/Cocos 专属执行模块，也未启用外部分析器或设备工具。

## 3. 名称字节及末尾 NUL

E-01 每段上下文均从 `74 6f 72 00`（`tor\0`）开始，随后是名称前缀。按十六进制逐字节转换，五段均与 name_with_prefix 完全吻合，无截断。前缀数字是名称本体的 ASCII 字节数，不包含前缀本身或 NUL；这种形式符合 Itanium ABI 类型名编码的外观，但不能仅凭外观确认 RTTI 类型。

| 名称本体 | 本体字节数 | 实际前缀 | 前缀+本体字节数 | 含终止 NUL 总长 | 声明起点 | 按起点计算的 NUL 偏移 | NUL 后所列字节 |
|---|---:|---|---:|---:|---|---|---|
| UnfouledStrikerComparator | 25 | 25 | 27 | 28 | 0x12eb925 | 0x12eb940 | `32 37 48 69`（27Hi） |
| HigherScoredPucksComparator | 27 | 27 | 29 | 30 | 0x12eb941 | 0x12eb95e | `32 36 4c 65`（26Le） |
| LeastFouledPucksComparator | 26 | 26 | 28 | 29 | 0x12eb95f | 0x12eb97b | `33 31 4e 61`（31Na） |
| ShortestShotComparator | 22 | 22 | 24 | 25 | 0x12eb9d9 | 0x12eb9f1 | `32 36 4c 65`（26Le） |
| LeastPoweredShotComparator | 26 | 26 | 28 | 29 | 0x12eb9f2 | 0x12eba0e | `00 75 73 65`（额外 NUL、use） |

核对结果：

1. 五个字符串的终止字节均明确为 `00`；最后一项是字符串 NUL 后另有 `00`，不能把第二个 NUL 算进名称长度。
2. `0x12eb941 - 0x12eb925 = 0x1c = 28`；`0x12eb95f - 0x12eb941 = 0x1e = 30`；`0x12eb9f2 - 0x12eb9d9 = 0x19 = 25`，与含 NUL 长度一致，邻接片段也一致。
3. LeastFouled 与 Shortest 之间不是所列字符串直接相邻；不能据此声称完整名称表已穷尽。
4. 上下文未给出自己的文件起点。本轮没有验证 `tor\0` 真的位于声明名称起点之前四字节；表中 NUL 偏移是以声明起点成立为前提的算术结果。

状态：ASCII、长度及上下文 NUL 内部核对 PASS；原件对应位置 BLOCKED。

## 4. PT_LOAD：文件偏移到 link VA

E-01 对五项提供同一参数：`p_offset=0`、`p_vaddr=0`、`p_filesz=0x279d710`。

文件支持区间为 `[0, 0x279d710)`；转换公式：

`link_va = p_vaddr + (file_offset - p_offset)`。

因此五个名称起点及含 NUL 的完整范围均在该文件区间内，分别映射为 `0x12eb925`、`0x12eb941`、`0x12eb95f`、`0x12eb9d9`、`0x12eb9f2`，与 JSON 的 link_va 一致。38 条指令的完整四字节范围也在该区间内，file_offset 与 va 相等，最末指令覆盖到 `0x18cce90`（不含），未越界；所有指令 VA 四字节对齐，各窗口按 4 递增。

重要边界：

- 未收到 ELF 头、完整 program headers、p_flags、p_memsz，不能独立确认此 PT_LOAD 参数来自原件、是否为可执行段，或存在其他段/权限。
- 名称 RELA 的写入位置 `0x27a2d18` 至 `0x27a2f10`，以及候选表/类型信息，**都在已提供段的文件覆盖区间之外**。不能把这段的零差映射推广过去；它们的文件偏移、可写映射及装载覆盖尚未验证。
- 所有地址都是声明的 ELF link VA 或 file_offset；没有运行进程 maps/load bias。运行地址应另证 `runtime_va = load_bias + link_va`，不得把这些数当 runtime VA。

状态：给定段参数下的映射算术 PASS；完整 ELF 段与运行映射 BLOCKED。

## 5. 名称 RELA：类型、符号索引、addend

按 ELF64 Rela 解释给定 r_info：

- `symbol_index = r_info >> 32 = 0`。
- `type = r_info & 0xffffffff = 0x403 = 1027`。
- 在 AArch64 ABI 下，1027 是 `R_AARCH64_RELATIVE`，写入值为 `B + A`（B 为 load bias，A 为 addend），不是“解析符号 0 得到函数”。

| 名称 | 声明 .rela.dyn 索引 | r_offset（写入 link VA） | r_info / symbol / type | addend | E-03 typeinfo_candidate | r_offset 与 typeinfo |
|---|---:|---|---|---|---|---|
| UnfouledStrikerComparator | 647 | 0x27a2d18 | 0x403 / 0 / 1027 | 0x12eb925 | 0x27a2d10 | +8 |
| HigherScoredPucksComparator | 655 | 0x27a2d60 | 0x403 / 0 / 1027 | 0x12eb941 | 0x27a2d58 | +8 |
| LeastFouledPucksComparator | 663 | 0x27a2da8 | 0x403 / 0 / 1027 | 0x12eb95f | 0x27a2da0 | +8 |
| ShortestShotComparator | 695 | 0x27a2ec8 | 0x403 / 0 / 1027 | 0x12eb9d9 | 0x27a2ec0 | +8 |
| LeastPoweredShotComparator | 703 | 0x27a2f10 | 0x403 / 0 / 1027 | 0x12eb9f2 | 0x27a2f08 | +8 |

五个 addend 都指向包含数字前缀的名称起点，与 E-01 声明的 link VA 相等；五个 r_offset 与 E-03 的 name_relocation 相同。

**未验证部分**：JSON 给的是拆解后的记录字段，不是原始 24 字节 Elf64_Rela 记录；没有 section header/sh_offset/sh_size/sh_entsize，不能复验索引 647/655/663/695/703、所在 `.rela.dyn` 或记录字节。E-03 的 25 个表项只给 type/addend/location，没有 r_info 或 symbol_index，不能把名称记录的 symbol=0 拆分结果冒充对全部表项的独立检验。

索引每增加 8 与写入位置增加 0x48 不矛盾：索引是重定位记录位置，r_offset 是被重定位的目标位置，二者不是同一坐标。

状态：名称 r_info 拆分及跨 JSON 对照 PASS；原始记录/索引真实性 BLOCKED。

## 6. 表、候选代码与调用侧关联

E-03 每行 5 个槽位均满足 `relocation_location = table_candidate + slot_offset`，slot_offset 为 0、8、0x10、0x18、0x20；type 均为 1027。slot 0 的 addend 等于 typeinfo_candidate；slot 0x18 的 addend 等于 candidate_code_va；这些是材料内部可直接复算的关系。

E-02 的地址构造为 `ADRP 页 + ADD 常数 + 0x10`，最终写入 `[x0]` 的值 P 如下：

| 名称 | E-02 xref | 构造 P | E-03 table T | P 与 T | P+0x10 的表项 addend | 随后直接 BL 目标 |
|---|---|---|---|---|---|---|
| UnfouledStrikerComparator | 0x18c71c4 | 0x27a2cf0 | 0x27a2ce8 | T+8 | 0x18cb8b4 | 0x18cb62c |
| HigherScoredPucksComparator | 0x18c7218 | 0x27a2d38 | 0x27a2d30 | T+8 | 0x18cbbe4 | 0x18cb95c |
| LeastFouledPucksComparator | 0x18c726c | 0x27a2d80 | 0x27a2d78 | T+8 | 0x18cbefc | 0x18cbc74 |
| ShortestShotComparator | 0x18c73bc | 0x27a2ea0 | 0x27a2e98 | T+8 | 0x18ccb5c | 0x18cc8d4 |
| LeastPoweredShotComparator | 0x18c7410 | 0x27a2ee8 | 0x27a2ee0 | T+8 | 0x18cce74 | 0x18ccbec |

静态候选链为：`P-8 (=T)` 的 RELATIVE addend → 类型信息候选 TI；`TI+8` 的名称 RELA → 名称；`P+0x10 (=T+0x18)` 的 RELATIVE addend → 比较器代码候选。**table_relative_-8 不是 P-8 直接指向名称。** T 也不等于窗口中写入的地址点 P；不能混用二者的槽位偏移。

五组尾部均出现 `ldr x8,[x0]; ldr x8,[x8,#8]; blr x8`，它们取的是 P+8（T+0x10）槽，不是本轮比较器所在 P+0x10 槽。附近置零/条件释放形态可作为清理候选，但没有目标签名，不把它直接命名为析构。后续 BL 指向的五个函数也不等于比较器入口；没有它们的函数体，不能确认“此处已经比较/排序”。

E-02 五个 xref 均落在声明的 FDE 候选 `[0x18c6b20,0x18c76a8)` 内，只证明材料中的范围包含关系。入口窗口对 x0 写入零值及 `0x3f800000`，结合上游 `add x0,sp,#0x38; bl #0x18c6b20`，存在对象初始化/配置构造的候选解释，不能命名为真实 AI 决策入口。唯一列出的 direct caller 位于 `0x18b3440`；“清单只有一个”不等于全部间接或条件调用被排除。

状态：槽位/地址点/跨材料链条算术 PASS；正式 RTTI、vtable 身份与调用角色 NEEDS_CONTEXT。

## 7. 机器码与先前提取的一致性：38 条逐项复核

下表 word 为 E-01 的四个字节按小端组合后的 32 位数，不是从原库新读取。每行地址与指令文本也与 E-03 对应项一致（包括 ret 的尾随空格，无语义差异）。人工检查 load 的寄存器、缩放偏移、比较与条件选择编码；未运行独立 decoder。

### 7.1 UnfouledStrikerComparator（10 条）

| link VA | bytes | word | 复核指令 |
|---|---|---|---|
| 0x18cb8b4 | 49204139 | 0x39412049 | ldrb w9, [x2, #0x48] |
| 0x18cb8b8 | 2a204139 | 0x3941202a | ldrb w10, [x1, #0x48] |
| 0x18cb8bc | 28008052 | 0x52800028 | mov w8, #1 |
| 0x18cb8c0 | 3f010071 | 0x7100013f | cmp w9, #0 |
| 0x18cb8c4 | 0805885a | 0x5a880508 | cneg w8, w8, ne |
| 0x18cb8c8 | 5f010071 | 0x7100015f | cmp w10, #0 |
| 0x18cb8cc | 08059f1a | 0x1a9f0508 | csinc w8, w8, wzr, eq |
| 0x18cb8d0 | 5f01096b | 0x6b09015f | cmp w10, w9 |
| 0x18cb8d4 | e003881a | 0x1a8803e0 | csel w0, wzr, w8, eq |
| 0x18cb8d8 | c0035fd6 | 0xd65f03c0 | ret |

### 7.2 HigherScoredPucksComparator（7 条）

| link VA | bytes | word | 复核指令 |
|---|---|---|---|
| 0x18cbbe4 | 294c40b9 | 0xb9404c29 | ldr w9, [x1, #0x4c] |
| 0x18cbbe8 | 4a4c40b9 | 0xb9404c4a | ldr w10, [x2, #0x4c] |
| 0x18cbbec | 08008012 | 0x12800008 | mov w8, #-1 |
| 0x18cbbf0 | 3f010a6b | 0x6b0a013f | cmp w9, w10 |
| 0x18cbbf4 | 0885885a | 0x5a888508 | cneg w8, w8, ls |
| 0x18cbbf8 | e003881a | 0x1a8803e0 | csel w0, wzr, w8, eq |
| 0x18cbbfc | c0035fd6 | 0xd65f03c0 | ret |

### 7.3 LeastFouledPucksComparator（7 条）

| link VA | bytes | word | 复核指令 |
|---|---|---|---|
| 0x18cbefc | 295040b9 | 0xb9405029 | ldr w9, [x1, #0x50] |
| 0x18cbf00 | 4a5040b9 | 0xb940504a | ldr w10, [x2, #0x50] |
| 0x18cbf04 | 08008012 | 0x12800008 | mov w8, #-1 |
| 0x18cbf08 | 3f010a6b | 0x6b0a013f | cmp w9, w10 |
| 0x18cbf0c | 0835885a | 0x5a883508 | cneg w8, w8, hs |
| 0x18cbf10 | e003881a | 0x1a8803e0 | csel w0, wzr, w8, eq |
| 0x18cbf14 | c0035fd6 | 0xd65f03c0 | ret |

### 7.4 ShortestShotComparator（7 条）

| link VA | bytes | word | 复核指令 |
|---|---|---|---|
| 0x18ccb5c | 201440fd | 0xfd401420 | ldr d0, [x1, #0x28] |
| 0x18ccb60 | 411440fd | 0xfd401441 | ldr d1, [x2, #0x28] |
| 0x18ccb64 | 08008012 | 0x12800008 | mov w8, #-1 |
| 0x18ccb68 | 0020611e | 0x1e612000 | fcmp d0, d1 |
| 0x18ccb6c | 08459f1a | 0x1a9f4508 | csinc w8, w8, wzr, mi |
| 0x18ccb70 | e003881a | 0x1a8803e0 | csel w0, wzr, w8, eq |
| 0x18ccb74 | c0035fd6 | 0xd65f03c0 | ret |

### 7.5 LeastPoweredShotComparator（7 条）

| link VA | bytes | word | 复核指令 |
|---|---|---|---|
| 0x18cce74 | 201840fd | 0xfd401820 | ldr d0, [x1, #0x30] |
| 0x18cce78 | 411840fd | 0xfd401841 | ldr d1, [x2, #0x30] |
| 0x18cce7c | 08008012 | 0x12800008 | mov w8, #-1 |
| 0x18cce80 | 0020611e | 0x1e612000 | fcmp d0, d1 |
| 0x18cce84 | 08459f1a | 0x1a9f4508 | csinc w8, w8, wzr, mi |
| 0x18cce88 | e003881a | 0x1a8803e0 | csel w0, wzr, w8, eq |
| 0x18cce8c | c0035fd6 | 0xd65f03c0 | ret |

容易误读的编码：

- MOV #1 为 MOVZ 别名，MOV #-1 为 MOVN #0 别名。
- CNEG 是 CSNEG 的别名：上述三处实际编码条件分别 EQ、HI、LO，别名取反后才是 NE、LS、HS。不能把别名条件再反转一次。
- W load 的 imm12 乘 4，D load 的 imm12 乘 8，LDRB 乘 1；这支持 0x4c/0x50、0x28/0x30、0x48 的读取偏移与宽度。
- CSEL EQ 的结果为相等时 W0=0，否则 W0=W8；CSINC 的 EQ/MI 是原始条件而非 CNEG 式的反条件。

结果：5 个代码起点、38 个 VA、38 条文本与 E-03 一致，E-01 的 38 个四字节编码人工复核未发现不符。E-03 没有机器码，所以不能声称“两次提取的机器码逐字节相同”。E-02 的入口、引用和 caller 窗口也没有 bytes，不能验证 ADRP/BL/BLR 的原件编码或扫描完整性。

## 8. 指令允许的窄语义与不能推断的结论

以下只是所列窗口在 AArch64 语义下的推导，不是目标运行采样。设 a 为 x1 所指字段，b 为 x2 所指字段；不推定对象类型。W0 的 `0xffffffff` 按有符号 32 位解释为 -1，但真实 ABI/调用者如何消费返回值仍未验证。

| 窗口 | 可推导读取与返回 | 不能据此确认 |
|---|---|---|
| UnfouledStriker | 读取 a、b 的 +0x48 单字节；a=b 返回0；a=0,b非0 返回-1；a非0,b=0 返回+1；a、b为不同非零值时返回+1 | 不证明字段为 bool 或犯规标记；更不证明“未犯规优先”的实际选择 |
| HigherScoredPucks | +0x4c 的32位位模式；按无符号比较，a>b 返回-1，a=b 返回0，a<b 返回+1 | 不证明是得分、单位、范围或写入时机；不证明调用者按负数优先 |
| LeastFouledPucks | +0x50 的32位位模式；按无符号比较，a<b 返回-1，a=b 返回0，a>b 返回+1 | 不证明是犯规次数或规则；不能当有符号整数比较 |
| ShortestShot | +0x28 的64位值加载到D寄存器，FCMP binary64；有序 a<b 返回-1，等于返回0，a>b 返回+1 | 不证明是路径长度、单位、计算来源或有效范围 |
| LeastPoweredShot | +0x30，同上 | 不证明是力度、能量、速度或其物理公式 |

边界反例与意义：

1. +0x48 若只允许 {0,1}，上述输出可形成常见三路布尔键比较；若允许 {1,2}，cmp(1,2)=cmp(2,1)=+1，不满足反对称性。**字段值域待证，不据此判原实现错误或建议排序改造。**
2. +0x4c 输入 a=0xffffffff、b=0 时返回-1，体现 unsigned 语义；+0x50 同输入返回+1。不能按 -1<0 的有符号直觉解释。
3. 两个浮点窗口：+0 与 -0 相等，等值无穷返回0；安静 NaN 的 unordered 标志使 MI/EQ 均为假，返回+1，交换仍+1。信号 NaN/浮点异常、FPCR/FPSR 环境未实测；不能承诺 NaN 的可排序性或用 epsilon 替换精确比较。
4. 返回 -1/0/+1 是窄窗口推导，不等于 std::sort 的 bool less 契约。直接把非零转 true 会丢失方向。尚不知真实调用者做符号判断、链式比较、容器注册还是别的操作。

### 运行顺序

能确认的是 E-02 地址升序为 Unfouled → HigherScored → LeastFouled → Shortest → LeastPowered，且每个局部窗口都把构造的 P 写入对象后出现一个 BL。不能确认五个比较器每局均运行、按此顺序执行、谁是主键、是否稳定排序、是否逆序应用或后续排序覆盖。窗口之间并非完整连续 CFG（特别是 LeastFouled 到 Shortest 之间存在未提供区域）；FDE 相同也不证明单一路径或语义函数身份。

### 字段语义与真实 AI

名称只是字段业务语义的线索。尚无字段写入点、对象布局/生命周期、实际调用签名、排序消费代码、候选生成、随机源或最终出杆动作。不能声称已恢复真实 AI 的择杆策略、难度、出杆方向/力度、犯规避免、物理预测或最终行为一致。

### 可用于开发的边界

可用于建立证据索引、地址/槽位映射候选、读取宽度与三路输出的隔离测试夹具，以及后续采样断言。不能直接作为原游戏业务结构定义、实际排序优先级、补丁地址、bool 比较器、AI 替代实现或原版物理参数。当前不建议任何排序改造。

## 9. 最小后续可复现实验（尚未执行）

按“先原件静态闭合，后最小运行观测”顺序；不需要先重建整款游戏。

### A. 本地原件复验

由持有原库的一侧，在合法可用的本地分析环境执行只读提取：

1. 对实际 so 计算 SHA256，记录文件名、大小、ELF class、EI_DATA、e_machine、工具版本；与声明源哈希配对。不一致则停止套用本报告地址。
2. 导出完整 program headers（含 p_offset/vaddr/filesz/memsz/flags），按区间重新映射五个完整名称、38 条指令、全部表项与名称 RELA 写入目标。不在文件支持范围的地址不得伪造文件偏移。
3. 每个名称输出实际文件起点、原始前后上下文、含 NUL 字节；每个名称 RELA 输出 section 元数据、索引计数约定、记录文件偏移和原始24字节，重新按小端 `r_offset:u64, r_info:u64, r_addend:i64` 解码。
4. 输出 E-03 全部25个表项的原始 RELA 记录与完整 typeinfo/vtable 周边字节，检验地址点 P、负槽与调用槽，而不只重复候选名称。
5. 用本地可用且记录版本的独立 AArch64 decoder 重解五个比较器窗口，并导出 E-02 所列调用侧窗口的机器码。检查 BL 精确目标、代码段属性以及目标函数边界。

成功条件：提取可重跑、源哈希匹配；名称包括 NUL 全字节相符；PT_LOAD 和每个原始 RELA 记录可反查；五个比较器38条指令与当前文本相符。此实验只能闭合静态证据来源，不证明运行顺序。

### B. 单次受控动作的运行观测

在拥有授权且工具实际可用的环境中，先确认模块哈希、ABI、maps/load bias 与线程，再做观察型日志，不修改参数、返回值或排序。

- 固定一个合法局面、AI等级与可控 RNG 状态（若无法固定随机源，应明确记录限制），触发一次候选生成/选择动作，再从同一状态重复。
- 分开记录候选初始化入口、五个后续 BL helper 与五个实际比较器入口的命中；日志包括递增序号、线程、动作ID、模块 link VA、调用点/返回点、x1/x2身份、被比较字段原始值、W0原始值，以及最终被选择的候选和实际出杆提交。
- 顺序结论按每条线程和动作归属建立，不能用多线程时间戳混排替代因果顺序。未命中只说明本次样本未覆盖。
- 回查比较器返回值的消费者和字段写入点，用同一对象关联日志把偏移对应到生成数据。只读已确认有效对象；未确认签名前不要按猜测 ABI 直接调用原函数。

成功条件：一次动作可关联到实际比较器调用及其返回值消费、最终候选；重复样本的异同有解释。只能证明已采样条件下行为，不扩大为所有难度/局面。

### C. 小规模边界夹具

确认签名/调用契约后再选择隔离模拟或合法测试 harness；隔离语义模拟不能冒充原件运行。

- 字节字段：全测 {0,1} 的四对；另外测试 (1,2)/(2,1)，确认真实值域是否可能出现此类值。
- 无符号字段：0、1、0x7fffffff、0x80000000、0xffffffff，覆盖相等和双向比较。
- binary64：小于/等于/大于，+0/-0、±Infinity、quiet NaN 双向；记录实际 FPCR/FPSR，异常单独报告。
- 每个输入比较返回原始W0、状态写入和外部调用；不要通过重排序列表代替函数输出比对。

## 10. 原型定义契约与参考取舍

本轮原型对象是“证据复核流程”，不是可玩 Carrom 游戏。核心循环为读取证据 → 解码/复算 → 跨材料对照 → 标记事实等级 → 登记未知 → 指定最小闭合实验；成功是每项都有核对结果和边界，失败是实测不符，缺材料则 BLOCKED 而非假定成功。

- 状态：源身份声明、地址坐标、名称字节、RELA元数据、机器码窗口、静态关联、验证等级、未知项。
- 输入窗口：只接受本轮三份 JSON 的明确字段；不会把缺失值、上下文推测或名称含义补成事实。数值算术与机器码/文本相符要求精确匹配，无 epsilon。
- 界面布局：本阶段只交付本文的证据表、逐指令表、边界与实验清单，无玩家界面、截图或运行交互；没有真实 Web 产物。
- 物理步长、碰撞/计分、游戏成功失败、玩家输入窗口与物理误差：本材料均未提供，不能从比较器恢复，保持 NEEDS_CONTEXT，不发明参数或胜负规则。
- 框架只保留后续交付约束，未实施 DOM/SVG/Canvas 或存档。如另行授权开发默认英文游戏，界面文案与 html lang=en 应在对应阶段落实；本文中文分析不是要求中文游戏。
- 参考取舍：采用三份材料的具体字节和结构关联；排除将 FDE 当语义身份、将类型名当字段声明、将地址升序当排序优先级、将静态存在当 AI 执行的推论。

## 11. 未知清单

| 编号 | 未知项 | 还缺什么 | 当前证据 | 状态 |
|---|---|---|---|---|
| U-01 | 原件与三份JSON是否确为同一构建 | 原始so只读哈希、文件身份与可重跑提取 | E-01/02/03仅声明相同源哈希 | 未闭合 |
| U-02 | 完整段与目标写入位置的映射/权限 | ELF头、完整PT_LOAD及目标地址反查 | E-01只提供一段，表/名称RELA目标在其文件覆盖外 | 未闭合 |
| U-03 | 名称RELA索引和原始记录真实性 | section元数据、24字节RELA记录；全部表项r_info | E-01名称记录已拆字段；E-03表项缺r_info | 未闭合 |
| U-04 | 正式RTTI/vtable身份及签名 | 完整表/类型信息与ABI布局、调用消费代码 | E-02/03候选槽位算术一致 | 未闭合 |
| U-05 | 机器码在原件中的真实性与调用侧解码 | 原件对应字节及独立decoder、E-02窗口bytes | E-01有38条bytes；E-02/03只给文本 | 未闭合 |
| U-06 | 实际调用路径与排序顺序/契约 | 完整CFG、helper函数体、运行调用/消费日志 | E-02线性窗口/FDE；比较器调用未出现 | 未闭合 |
| U-07 | 字段语义、值域、单位和对象身份 | 字段写入点、对象关联日志、类型布局 | E-01/03读取偏移与宽度；名称仅线索 | 未闭合 |
| U-08 | 真实AI行为及物理规则 | 固定局面/随机状态、候选到出杆链、物理配置 | 无动态证据 | 未闭合 |

## 12. 真实验证、产物与限制

产物：`/workflow/prototype.md`（本次新写报告；也是人工核对记录）。三份参考未修改，未提取/执行原始库，没有源码或试玩ZIP。

本轮已执行：read_reference读取3份JSON；read_skill读取选定入口；read_game_knowledge读取4份冻结资料；read_skill_resource读取4份相关方法资料；人工完成5段名称、5组映射、5条名称r_info、25个表项位置关系、5组地址点关系和38条指令的内部复核。

本轮未执行：原库哈希/反汇编、独立decoder、Node/Python审计程序、浏览器、真机、AI动作重放、构建与测试。当前是原型证据复核阶段，`npm run build`、`npm test`、`npm run check` 未执行，不能报告其通过。最小实验A/B/C均为待执行步骤，不是验证结果。

验收条件：逐项可反查引用、精确复算、明确区分材料声称/本轮核对/未验证、附未知项和最小复现实验；本文达到该限定的报告条件。原件真实性及运行行为仍为 BLOCKED/NEEDS_CONTEXT，不给予原库还原、真实AI或游戏交付整体PASS。不自动确认本阶段或进入下一阶段。
