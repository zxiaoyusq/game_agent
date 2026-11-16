# 五个原生比较器候选交叉复核

## 0. 范围与结果

本轮为 prototype 阶段的只读证据审查，不是游戏开发、玩法恢复或原生库独立反汇编。恢复执行 attempt=2；本报告依据本次实际读取，不引用上一轮成功日志。工作区初始目录清单为空，无既有源码可修改。本次仅提取一份研究文本并写报告，不改竞品源码、不执行目标代码、不推进美术/代码/测试阶段。

结论：给定 JSON 的槽位算术、候选入口与指令地址内部一致；ZIP 字符串文本支持五个带长度前缀的名字。可从给定 ARM64 指令文本推导三值/条件行为，但缺原始 so、五项原始重定位记录、名字所在原件字节及候选函数机器码，不能宣布原件级验证通过。来源是用户提供的本机提取材料；工具读取 ZIP/JSON 不等于 MCP 独立反汇编。

本任务没有可玩原型。物理步长、碰撞、计分、成功失败、输入窗口、物理容差、核心循环与界面布局均不适用；不从比较器名字补造这些规则。审查结构为“证据 → 地址/名字 → 重定位 → 指令行为 → 未知清单”。框架资料已读取，但本轮不创建 H5、英文玩家界面、dist 或发布 ZIP，不运行游戏构建验收。

## 1. 实际证据与出处

参考根为 ref/，以下路径相对此根。

- E-01：`mcp-inputs/mac-codex/f43333b056f79b5f23746ec8c70ba55c11888ee39dd18353d9167bb823c0cc61/carrom_comparator_relocations.json`，完整实际读取。5 rows、25 entries，五段候选指令共 38 条。路径中的哈希不得冒充本轮对 JSON 内容的独立计算。
- E-02：`mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip`，真实完整目录清单，35 文件、展开 2,411,908 字节；工具返回 archive SHA256 `ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1`。无原 so，无五个 comparator 专属反汇编文件；未全量解压。
- E-03：ZIP `analysis/native_关键词字符串.txt`，SHA256 `098c9c77cd66d97944947ce57691a23166527b498463b3772b01876b8d073f2e`；读取头部并逐字节提取为 `/reference-inputs/native_关键词字符串.txt`（725,804 字节）。对该副本检索 Comparator，并实际读取 2006–2185 行。行 2127、2149、2137、2089、2138 分别支持五个完整名字；文本按名字排列，不带原件偏移，也不保留字符串末尾 NUL。
- E-04：ZIP `report/竞品_ARM64代码定位.md`，完整读取；SHA256 `c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f`。描述本机 Capstone、ADRP/ADD 扫描、FDE 与 BL 扫描的局限，非本轮执行记录。
- E-05：ZIP `analysis/native_字符串relocation候选.json`，完整读取；SHA256 `2c4d60f177ea7eb0c646be2db736bc739d81e359b78e531905a6625bd54162dd`。只含 7 个 MatchShotSolver/physicsStopped 类型名，不包含本次五类。
- E-06：ZIP `analysis/native_RTTI附近引用候选.json`，完整读取；SHA256 `db11af904f957691dbc7f307095d54873bc4790fff755e97258b0fbf6265f759`。只有 2 条其他类型名附近候选，不能补证本次五类 RTTI。
- E-07：ZIP `analysis/native_候选函数直接调用.json`，完整读取；SHA256 `2b224867627e101d78711410798bdb44ce79ac0bc2258d532c794393a3607bfc`。3 条边针对 0x18b09d4/0x1aa3458，不针对五个入口。它不是五个入口的调用者扫描结果，不能说五个入口“零调用”。
- E-08：ZIP `analysis/native_字符串交叉引用候选.json`，完整读取；SHA256 `7ee49831a8e4a862af476446d66878c54f68f2b54ea2e57a7d9056921a5f717a`。其他字符串的 file_offset/link_va 相等只是该文本对那些项的声明，不能外推给五个名字。
- E-09：ZIP `disassembly/02_MatchShotSolver_18bc618.txt`，完整读取；SHA256 `2070412740ad04b7df074f719a60cb9cc4044b75f08f6eefe20cbc8b54a410b8`。实际含 7 条地址/机器码/指令，但窗口为 0x18bc618–0x18bc634，不是五个 comparator 入口。它加载 [x1+8]、比较名字地址并条件返回 x0+8，不是击球求解算法。
- E-10：ZIP `analysis/native_elf_符号.json`，只读取字符 0–2000，未通读 1,518,754 字符文件。头部声明 EM_AARCH64、ELF64、ET_DYN、库名及哈希；给出 section 地址/大小，不提供本轮可用的 PT_LOAD 原始映射或五项原始 RELA 记录。

E-01/E-04/E-07/E-08/E-09/E-10 都声明原件 SHA256 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`；库名见 E-04/E-10：`libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so`。这是衍生材料之间的身份标签一致，不是本轮对缺失 so 的哈希验证。

已实际读取全部冻结品类/框架正文：`genre/docs/general.md`、`genre/docs/physics.md`、`framework/docs/web-common.md`、`framework/docs/native-web.md`。技能实际读取 `game-reverse-engineering/SKILL.md` 及同包 `references/execution-protocol.md`、`global-rules.md`、`native-code-evidence.md`、`unknowns-ledger-template.md`；采用地址坐标系、静态/动态分级与未知清单方法。不采纳案例地址或假定工具已安装。

## 2. 名字与字节级边界

|JSON name|E-03 完整可打印串|名字 ASCII 长度|JSON name_file_offset|可核对与不可核对|
|---|---|---:|---|---|
|UnfouledStrikerComparator|`25UnfouledStrikerComparator`|25|0x12eb925|大小写、拼写、25 前缀匹配；原件偏移/NUL 未证|
|HigherScoredPucksComparator|`27HigherScoredPucksComparator`|27|0x12eb941|大小写、拼写、27 前缀匹配；原件偏移/NUL 未证|
|LeastFouledPucksComparator|`26LeastFouledPucksComparator`|26|0x12eb95f|大小写、拼写、26 前缀匹配；原件偏移/NUL 未证|
|ShortestShotComparator|`22ShortestShotComparator`|22|0x12eb9d9|大小写、拼写、22 前缀匹配；原件偏移/NUL 未证|
|LeastPoweredShotComparator|`26LeastPoweredShotComparator`|26|0x12eb9f2|大小写、拼写、26 前缀匹配；原件偏移/NUL 未证|

这些文本与 Itanium C++ ABI 非限定 source-name 的十进制长度编码相容；不能据此确定类继承、模板参数或 RTTI 实例身份。前缀的期望 ASCII 字节分别为 `32 35`、`32 37`、`32 36`、`32 32`、`32 36`；余下是表内大小写敏感名字的 ASCII 编码。若是完整 C 字符串，应再有 `00`，但 E-03 的换行并非原件 `00` 的证据。不能把上述期望重编码说成实际 so hexdump。

相邻 offset 差：0x941−0x925=0x1c=28，0x95f−0x941=0x1e=30，0x9f2−0x9d9=0x19=25；恰分别等于两位长度前缀+25/27/22 个 ASCII 字符+一个 NUL。只能说布局相容，不能证明 offset 指向前缀起点；它也可能指向剥前缀后的名字。E-01 未保存 name relocation 的 addend，不能确认加载器实际指向前缀还是名字，也不能将 file_offset 直接当 link VA。

## 3. ELF relative relocation 链

### 3.1 已核对的算术与缺失环节

在 E-10 声明的 AArch64 ELF64 环境下，类型 1027 即 `R_AARCH64_RELATIVE`。普通 ELF64 RELA 语义是：在 `P = B + r_offset` 处写入 `B + A`，B 为经映射求证的 load bias，A 为记录中的显式 addend；不是“把 addend 直接作为运行地址”，也不是“在文件原指针上再相加”。这类记录通常要求 symbol index=0；E-01 只给 type，未给完整 r_info，不能验证该项。

每行的 5 个 relocation_location 都准确等于 table_candidate+slot_offset，步长 8 字节。+0 的 addend 准确等于 typeinfo_candidate；typeinfo_candidate 均为 table_candidate+0x28，name_relocation 均为 typeinfo_candidate+8；+0x18 的 addend 准确等于 candidate_code_va。25 个记录都声明 type=1027。

|类型缩写|T：table_candidate|T+0 → R：typeinfo_candidate|N=R+8：name_relocation|C：T+0x18 addend / candidate_code_va|
|---|---|---|---|---|
|Unfouled|0x27a2ce8|0x27a2d10|0x27a2d18|0x18cb8b4|
|HigherScored|0x27a2d30|0x27a2d58|0x27a2d60|0x18cbbe4|
|LeastFouled|0x27a2d78|0x27a2da0|0x27a2da8|0x18cbefc|
|Shortest|0x27a2e98|0x27a2ec0|0x27a2ec8|0x18ccb5c|
|LeastPowered|0x27a2ee0|0x27a2f08|0x27a2f10|0x18cce74|

完整槽位交叉核对（箭头右侧均为 E-01 addend，不是已读取的运行时指针）：

|类型|+0|+8|+0x10|+0x18|+0x20|
|---|---|---|---|---|---|
|Unfouled|0x27a2ce8→0x27a2d10|0x27a2cf0→0x18b2ed4|0x27a2cf8→0x18cb8b0|0x27a2d00→0x18cb8b4|0x27a2d08→0x18cb8dc|
|HigherScored|0x27a2d30→0x27a2d58|0x27a2d38→0x18b2ed4|0x27a2d40→0x18cbbe0|0x27a2d48→0x18cbbe4|0x27a2d50→0x18cb8dc|
|LeastFouled|0x27a2d78→0x27a2da0|0x27a2d80→0x18b2ed4|0x27a2d88→0x18cbef8|0x27a2d90→0x18cbefc|0x27a2d98→0x18cb8dc|
|Shortest|0x27a2e98→0x27a2ec0|0x27a2ea0→0x18b2ed4|0x27a2ea8→0x18ccb58|0x27a2eb0→0x18ccb5c|0x27a2eb8→0x18cb8dc|
|LeastPowered|0x27a2ee0→0x27a2f08|0x27a2ee8→0x18b2ed4|0x27a2ef0→0x18cce70|0x27a2ef8→0x18cce74|0x27a2f00→0x18cb8dc|

共享 +8/+0x20 目标和候选 C−4 的相邻目标支持相似表布局，不证明任何一个槽是析构器、虚方法或特定签名。

**链条尚未闭合**：E-01 支持文本声明的 `T → R` 和 `T+0x18 → C`；`R+8=N → 名字 link VA` 缺实际 relocation addend/type/r_info/section。名字只有 file_offset。E-05/E-06 是其他类型的链，不能填补缺口。

按 Itanium vtable 常见结构，T 处 RTTI 指针与位于其后 +8 的函数槽相容；若采用此解释，通常还需检查 T−8 的 offset-to-top，真实对象 vptr/address point 可能是 T+8，不能直接认定 T 为 vptr。还需核对 R 的 type_info vptr、父类型或标志、名字指针及对象构造写入。当前保持 table/typeinfo 为候选。

E-10 的 section 大小还支持报告中重定位数量的算术一致性：若普通 ELF64 Rela 每项 24 字节，16,079,088/24=669,962，30,120/24=1,255，合计 671,217，与 E-04 声明相符。这仍是 section 摘要校核，不是扫描了 671,217 条原始记录。

### 3.2 地址纪律

候选 T/R/N/C 按 E-04 与 E-01 语境作为声明的 ELF link VA 分析；name_file_offset 保持文件坐标。原件哈希仅为材料声明，架构为材料声明的 AArch64。无 PT_LOAD 原字节、无运行 maps，因此不能产生 runtime_va，也不能证明 file_offset=link_va。静态映射须 `VA=p_vaddr+(offset−p_offset)` 且 offset 在 p_filesz 覆盖内；运行地址须 `B+VA`。字段偏移和表槽偏移不是函数地址。

## 4. ARM64 指令逐项复核

以下结论均有前提：E-01 指令文本忠实于原件、从所列入口执行、相关内存可读、无中途异常。窗口没有所给之外的调用上下文或原始 opcode，因此只证明该文本的架构条件语义。五段地址均 4 字节对齐、每条相邻地址递增 4、末尾 ret；范围为所给线性窗口，不宣称真实完整函数/FDE 已验证。返回只核对 W0；`-1` 是低 32 位 `0xffffffff`，写 W0 会使 X0 高 32 位清零，不证明真实 C++ 返回类型是 int 或 64 位负数。

### 4.1 UnfouledStrikerComparator，0x18cb8b4–0x18cb8dc（10 条）

定义 a=uint8([X1+0x48])、b=uint8([X2+0x48])。

- 0x18cb8b4 `ldrb w9,[x2,#0x48]`：W9=b，零扩展；0x18cb8b8 `ldrb w10,[x1,#0x48]`：W10=a。不能倒置对象次序。
- 0x18cb8bc `mov w8,#1`。
- 0x18cb8c0 `cmp w9,#0`，0x18cb8c4 `cneg w8,w8,ne`：b≠0 时 W8=-1，否则 +1。
- 0x18cb8c8 `cmp w10,#0`，0x18cb8cc `csinc w8,w8,wzr,eq`：a=0 保留 W8；a≠0 选择 WZR+1，即 +1。
- 0x18cb8d0 `cmp w10,w9`，0x18cb8d4 `csel w0,wzr,w8,eq`：a=b 返回 0，否则返回上述 W8；0x18cb8d8 ret。

|a|b|W0（有符号32位解释）|
|---|---|---:|
|等于 b|任意相等字节|0|
|0|非零|-1|
|非零|0|+1|
|非零且 a≠b|非零|+1|

只能证明三值输出。若取值域确为 {0,1}，行为与该布尔位升序相容；LDRB 不证明 C++ bool 或“未犯规”。反例 a=1,b=2 与 a=2,b=1 均返回 +1。故在任意字节域上，宣称“该代码满足反对称排序比较关系”是 FAIL；是否真实数据域严格为布尔仍 NEEDS_CONTEXT。

### 4.2 HigherScoredPucksComparator，0x18cbbe4–0x18cbc00（7 条）

- 0x18cbbe4 `ldr w9,[x1,#0x4c]`、0x18cbbe8 `ldr w10,[x2,#0x4c]`：a、b 为各自 32 位载入位型。
- 0x18cbbec `mov w8,#-1`；0x18cbbf0 `cmp w9,w10`。
- 0x18cbbf4 `cneg w8,w8,ls`：LS 为无符号 lower-or-same（C=0 或 Z=1），不是有符号小于等于。a≤u b 时由 -1 变 +1。
- 0x18cbbf8 `csel w0,wzr,w8,eq`：相等覆盖为 0；0x18cbbfc ret。

因此：a>u b 返回 -1，a<u b 返回 +1，相等返回 0。证明无符号比较的三值方向，不证明成员声明 uint32_t，更不证明“得分”“球数”或返回符号在调用者中的排序含义。例如 a=0xffffffff,b=0 返回 -1，不能按 signed int 的 -1<0 解读。

### 4.3 LeastFouledPucksComparator，0x18cbefc–0x18cbf18（7 条）

- 0x18cbefc `ldr w9,[x1,#0x50]`；0x18cbf00 `ldr w10,[x2,#0x50]`；0x18cbf04 `mov w8,#-1`。
- 0x18cbf08 `cmp w9,w10`；0x18cbf0c `cneg w8,w8,hs`：HS 为无符号 higher-or-same（C=1），不是有符号大于等于。
- 0x18cbf10 `csel w0,wzr,w8,eq`；0x18cbf14 ret。

因此 a<u b 返回 -1，a>u b 返回 +1，相等返回 0。与上一项方向相反；偏移 +0x50 和“LeastFouled”名字不证明这是犯规计数、球实体或同一对象结构。

### 4.4 ShortestShotComparator，0x18ccb5c–0x18ccb78（7 条）

- 0x18ccb5c `ldr d0,[x1,#0x28]`；0x18ccb60 `ldr d1,[x2,#0x28]`：各加载 64 位到 D 寄存器。
- 0x18ccb64 `mov w8,#-1`；0x18ccb68 `fcmp d0,d1`：按 FP64 比较载入位型。
- 0x18ccb6c `csinc w8,w8,wzr,mi`：MI 即 N=1 时保留 -1，否则生成 +1。
- 0x18ccb70 `csel w0,wzr,w8,eq`：Z=1 时归零；0x18ccb74 ret。

### 4.5 LeastPoweredShotComparator，0x18cce74–0x18cce90（7 条）

- 0x18cce74 `ldr d0,[x1,#0x30]`；0x18cce78 `ldr d1,[x2,#0x30]`；0x18cce7c `mov w8,#-1`。
- 0x18cce80 `fcmp d0,d1`；0x18cce84 `csinc w8,w8,wzr,mi`；0x18cce88 `csel w0,wzr,w8,eq`；0x18cce8c ret。

与 4.4 完全相同的条件形式，仅偏移和地址不同。两项共同真值表：

|FP64 关系|FCMP NZCV|MI/EQ|W0|
|---|---|---|---:|
|a<b|1000|真/假|-1|
|a=b|0110|假/真|0|
|a>b|0010|假/假|+1|
|unordered（任一 NaN，正常完成比较）|0011|假/假|+1|

+0 与 -0 比较相等；有序 infinities 按正常关系处理。若允许 NaN，交换参数仍返回 +1，不能称为全 FP64 域的严格弱序或 NaN-safe 比较。sNaN/异常使能的实际行为还依赖 FP 环境，不能只凭文本断言必达 ret。LDR D+FCMP D 支持“此处以 FP64 方式使用 64 位载入”，不证明 C++ 字段声明 double，更不证明长度、耗时、力度、单位、归一化或可接受物理误差。

## 5. 可证实、假设和禁止外推

- PASS（仅衍生文本层）：五个全名字的 ASCII 拼写/长度前缀匹配；25 个槽位地址和 addend 内部算术匹配；38 条指令地址步长匹配；给定指令语义的上述条件推导。
- BLOCKED（原件级）：名字原件字节/NUL/偏移，RELA 原始 r_info/r_addend，名字指针目标，PT_LOAD 映射，五段机器码及独立反汇编。
- NEEDS_CONTEXT：T/R 是真实 vtable/RTTI、对象 vptr address point、槽位名称、函数入口/签名、X0/X1/X2 对象身份、成员类型与取值域。
- FAIL：无条件把 Unfouled 的任意字节比较视为反对称关系；把两个浮点窗口视为支持所有 NaN 的合法全序；把非比较器的 E-05/E-07 当作五个候选的重定位/调用者证据。

候选窗口确实从 X1/X2 相对偏移读取，未在给定文本使用 X0 作为载入基址；与 C++ 成员方法 X0=this、X1/X2=两个参数相容，但自由函数、thunk、其他约定或传入子对象均未排除。三个 Comparator 模板类型名（ShotSimulation、ShotTest、PuckLogic）只作为 E-03 附近字符串存在；邻近文本不证明五类各自的继承关系。

表空间排列不等于调用优先级；+0x18 槽位不等于第三个排序键。没有证明五者被构造、注册、安装到实际对象、被间接调用，或由求解器在平分时依次执行。候选顺序也可能被配置覆盖、未运行、只用于特定模式。名字存在不证明机器人击球算法、在线使用、玩家是不是机器人，更不能推断真人身份或采集用户数据。

## 6. 可复现后续步骤（本轮未执行）

### A. 静态原件闭环

1. 在获授权环境取得精确配对 so；记录原件 SHA256、ELF build-id、ABI、文件大小、来源与工具版本。预期哈希只用上述材料声明作比对，若不同立刻停止复用本报告地址。保留只读原件与已哈希工作副本。
2. 使用实际安装的 ELF 工具读取 ELF header、PT_LOAD、section headers、完整 RELA。例如在外部工作环境执行 `readelf -h -l -S -r -W <so>`；记录真实输出与版本。本平台没有执行这些命令，报告不宣称已安装或执行。
3. 针对五个 name_file_offset 输出至少“前4字节+完整名字+后4字节”的 hexdump，确定是否含两位前缀和 NUL，保存 file_offset/link_va 映射。按 PT_LOAD 检查文件覆盖，不按 section 地址猜 p_offset。
4. 对每个 T−8 至 R 所属完整 RTTI 范围读取原字节、相关 RELA；逐项保存 section、record index、r_offset、完整 r_info/type/symbol、signed addend。尤其补 N 的 addend，核对它实际指向名字串起点。用 B 为符号变量模拟加载，明确 P=B+r_offset、value=B+A，不执行目标。
5. 用第二个独立解码器核对五段机器码，输出每条 VA/file_offset/4字节 opcode/mnemonic；检查 C−4 及更广邻接窗口、FDE、分支入口、thunk 和 ret。不要把一段线性窗口等同完整函数。若使用 LLVM，可在外部按每个 C 调用 `llvm-objdump -d --start-address=<C> --stop-address=<窗口末端> <so>`，并再查看上下文。
6. 追踪 T/R 的真实 xref、构造函数中 vptr 写入、间接调用的 address point/槽位、调用点参数与返回值消费者，构建含条件的 CFG。BL 扫描之外覆盖 BLR、尾跳、范围中部入口。确认比较器组合器、短路和平分分支后才能描述优先级。
7. 为文本语义建立隔离夹具：字节域全部 256×256 输入，32 位含 0、1、0x7fffffff、0x80000000、0xffffffff、相等/邻接值，FP64 含负数、±0、±∞、qNaN/sNaN 位型。检查输出集合和交换参数关系。分别记录“语义模型测试”和“原始 opcode 仿真”；模型通过不提升为原件或运行时验证。本轮没有生成或执行该夹具。

### B. 只读运行观察闭环

1. 必须先有合法授权、精确配对安装包/so、测试设备或模拟器及实际可用调试工具。核对当前进程、模块映射文件偏移、ABI/build-id/哈希；从 PT_LOAD 与 maps 页对齐映射计算 load bias，不能把第一段可执行映射起点当 B。
2. 先验证运行内存中候选代码与配对原件字节，再验证 R+8 的名字指针和真实对象 vptr/address point。ARM64 标签/PAC、thunk 按实际环境处理，不照搬别的构建。
3. 在测试账号和受控场景做观察式断点/探针，记录动作编号、线程、模块相对 PC、调用栈、X0/X1/X2、必要偏移的最小位型、W0 返回值。只对确认可读且生命周期有效的对象读取；不在签名未证时主动调用函数，不 patch 返回、不改排序结果。
4. 采用可复现的合法动作触发，并记录五候选是否命中、同一调用链的先后与条件、平分触发路径；缺命中只说明该样本未观测，不证明不可达。并发线程的时间顺序不自动等于算法优先级。
5. 用真实写入路径/匹配类型资料/受控变量变化交叉确认字段定义；本轮不给字段命名。避免账号、凭据、原始网络体和可识别玩家信息。采样只证明所测版本/模式/输入，不证明全部场景或真人身份。

## 7. 未知清单

|编号|未知项|还缺什么|当前证据|状态|
|---|---|---|---|---|
|U-01|材料与真实构建身份及原件哈希|精确配对 so、build-id、实际 SHA256|E-01/04/07/08/09/10 身份声明一致|未闭合|
|U-02|五个名字原件字节、NUL 与 offset 的起点含义|带偏移 hexdump 和 PT_LOAD|E-01 offset；E-03 可打印串|未闭合|
|U-03|五个 N 名字重定位和完整 RELA 链|N 的 r_info/r_addend，25 条原记录，映射|E-01 缺名字 addend；E-05 非目标项|未闭合|
|U-04|真实 RTTI/vtable/address point/槽位身份|T−8、R 完整结构、对象 vptr 写入/xref|E-01 候选表，E-06 非目标项|未闭合|
|U-05|38 条指令与原始机器码、入口/CFG 一致|原 so opcode、第二解码器、邻接 CFG/FDE|E-01 仅指令文本；E-09 非目标窗口|未闭合|
|U-06|对象身份、函数签名、字段类型/取值域/语义|调用点、匹配结构、写入者、受控观察|E-01 X1/X2 偏移读取；E-03 名字|未闭合|
|U-07|候选可达性、组合顺序、平分/排序约定|真实调用/构造/注册路径与运行 trace|E-07 只扫描其他目标|未闭合|
|U-08|NaN/FP 异常环境与真实数据不变量|FPCR/FPSR、合法对象采样、边界夹具|E-01 FCMP 文本语义|未闭合|
|U-09|运行与设备验证条件|授权设备、配对包、maps、实际调试工具|无本轮运行证据|未闭合|

## 8. 验收记录与产物

本轮真实执行：冻结资料/技能读取；JSON 完整读取；ZIP 35 项清单；上述关键证据文本读取；关键词文本按件提取、检索和行读取；人工逐项槽位/地址/条件语义交叉复核。未执行 ELF 工具、独立 MCP 反汇编、浏览器、模拟器、ADB、Frida、目标代码或自动化语义测试。这里的 PASS 限于报告列出的文本一致性和架构语义推导，不能代替原件 PASS。

当前阶段无源码或构建任务，`npm run build`、`npm test`、`npm run check` 未执行且不适用；没有引用旧 attempt 验证日志，也没有伪造退出码。本次服务工具已恢复并返回读取/提取结果；不宣称独立检测或修复了平台服务。后续若进入代码/测试阶段，需按当轮最终源码真实执行全部必需验证，不以本报告代替。

产物：`/workflow/prototype.md`（本审查报告）；`/reference-inputs/native_关键词字符串.txt`（原样研究副本，非本轮新生成分析代码/资源，不进入 dist）。没有源码包、试玩 ZIP 或不存在的截图。

验收条件：五项均有名字文本/地址/槽位/寄存器/条件行为记录；原件字节、名字重定位缺口显式登记；unsigned 与 FP unordered 不被误读；静态关联不提升为调用顺序/可达性/字段语义/真人身份；后续静态及运行路径可复核。以上报告范围已满足；原件和运行级义务仍 BLOCKED，不以缺少原 so 为由扩展任务或索取用户已允许缺省的证据。
