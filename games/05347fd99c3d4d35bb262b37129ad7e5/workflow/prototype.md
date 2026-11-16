# Carrom 力度上游跳板与表结构复核

## 范围与结论

本轮 attempt=1，仅研究参考文本和用户提供的本机摘录，输出本报告；不修改游戏源码、不发布、不推进美术、代码或测试阶段。研究文本曾逐字节提取至 reference-inputs，属于参考副本，不是实现产物。

最合理的结构假设：0x1a924bc 是依赖对象首指针所指表内负偏移元数据的 this 调整跳板，符合 Itanium C++ ABI 风格的虚调整 thunk 模式；28 组相同三项指针与多个虚表或子虚表共享继承实现相容。尚不能确认其具体类型、虚函数角色、表边界或实际运行可达性。不能将该模式解释成 28 个力度档位、28 种对局或 28 个运行对象。

已有资料能将 0x18b31fc 范围中的两个直接 BL 与含 shotPowerLimits 字符串的 0x18b09d4 范围连起来；新增跳板到该范围的上游连接仍全部依赖未独立核验的本机摘录，且中间代码缺失。未获得力度数值、力度单位、限幅规则或业务触发条件。

## 证据等级

- A：本轮工具实际读取的 ZIP 清单、条目正文及工具返回哈希。A 证明资料内容存在，不能代替对原 ELF 字节的独立复核。包内反汇编、候选扫描及报告仍属于既有分析结果。
- B：用户补充的本机扫描与反汇编，原样作为待核验输入；本轮没有重组 ELF、重新散列原 ELF、解析重定位或重新反汇编。
- C：根据 A/B 作出的指令语义和 ABI 结构推断，必须附成立条件。
- 缺口：尚未取得的字节、完整数据流、类型绑定或运行证据。

所有相关地址按资料约定作为 ELF link VA 使用，不是文件偏移或进程地址。未计算 load bias。

## 参考路径与身份

参考根目录为 ref/，以下路径均相对该目录：

1. mcp-inputs/mac-codex/0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa/Carrom_native_chunks.zip；工具返回 SHA256：0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa。共 7 项，含 manifest.json 及 6 个二进制分片。
2. mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip；工具返回 SHA256：ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1。共 35 项。

chunks 包 manifest.json 声明原 ELF SHA256 为 4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4，与用户输入和证据包说明一致；仅为身份声明交叉一致，未重新计算原 ELF 哈希。manifest.json 条目 SHA256：72553230106447931a42aae6dc0ce218a946a5ca84275a25cddaf2c9330d12ef。

关键已读条目与 SHA256：

| evidence 包内路径 | SHA256 |
| --- | --- |
| report/竞品_ARM64代码定位.md | c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f |
| disassembly/caller_18b31fc.txt | b64aa9d2d4af3a097eb82fd21db048139b9c09be6568f4ec9ccd789fd6b67d12 |
| disassembly/01_shotPowerLimits_18b09d4.txt | e001c256d16c9ecfb846e9dbe318d2a8ee8b9fc1531a3b8592856944e51065aa |
| analysis/native_候选函数直接调用.json | 2b224867627e101d78711410798bdb44ce79ac0bc2258d532c794393a3607bfc |
| analysis/native_字符串交叉引用候选.json | 7ee49831a8e4a862af476446d66878c54f68f2b54ea2e57a7d9056921a5f717a |
| analysis/native_RTTI附近引用候选.json | db11af904f957691dbc7f307095d54873bc4790fff755e97258b0fbf6265f759 |
| analysis/native_对局消息类型信息候选.json | 42cad3218cae2342d1bc3bcdfeebc1ffba7ef13e8abbb5712afbd222efee41df |
| analysis/native_配置加载交叉引用候选.json | 4d984488b0186a91f13cb28b52235513c0794e09b20ca7b2cae583ecf80ac8bd |
| analysis/native_配置与加密字符串.txt | 8deecae45526c6b29000058f6173a24b01e933477959a2ac36a0db036f156614 |
| disassembly/shot_construct_call_1aa3e04.txt | efff8351985740a4e1d5ef0ba3b4b556934de6591e874395472a0d05b22cb87a |
| analysis/native_击球消息直接调用点.json | 5f3093b425a0388fc5ccefe3ddaf08cc147ae3a4a5d43aaa1bcece8e05ec1937 |
| analysis/native_关键词字符串.txt | 098c9c77cd66d97944947ce57691a23166527b498463b3772b01876b8d073f2e |
| analysis/native_elf_符号.json | d4d1f06dc49bb5878b8119779ef6a937d8e0e30a795a1b4955712c431f8011cc |

符号 JSON 仅通过归档工具读取前 5000 字符，之后提取完整文本作限定检索，未声称逐项读完 7923 个符号。两个研究副本分别为 /reference-inputs/native_keywords.txt、/reference-inputs/native_symbols.json，哈希与对应条目一致。

## 用户补充摘录：全部为 B 级

```text
0x1a924bc ldr  x8,[x0]
0x1a924c0 ldur x8,[x8,#-0xc8]
0x1a924c4 add  x0,x0,x8
0x1a924c8 b    0x1a92434
0x1a924b8 b    0x18b3168
0x18b31e4 b    0x18b31fc  （用户说明：恢复栈后）
```

用户另报：ELF RELA addend 等于 0x1a924bc 共 28 项，各命中槽的 -8 相邻加数为 0x1a923d4，+8 相邻加数为 0x1a92650；示例槽 0x27b7c10。没有取得 28 项原始记录、重定位类型、r_info、完整槽地址清单或目标表字节，本轮不将数量及一致性升级为独立验证事实。

## 跳板语义与边界

若上述指令准确，设进入时 x0=p，则其效果为：先取 q=Mem64[p]，再取 d=Mem64[q-0xc8]，令 x0=p+d，最后直接分支到 0x1a92434。这里的 -0xc8 是表内取值位置，不是固定的对象调整量；真正的调整量来自加载的 64 位表项。偏移值在地址相加时可以表示负位移。

该模式高度符合虚调整 this thunk：对象子对象持有 vptr，从 vtable address point 前的元数据槽取 vcall 调整值，再转入共享实现。若满足相应 ABI，-0xc8 可对应负向元数据项，但不能据此确定基类偏移、继承层数或虚函数序号。

仍有替代解释：自定义对象分发表或其他元数据驱动适配器。需通过表头、RTTI、构造写入和调用槽用法区分。仅看到四条指令，不能严格证明 q 是 vptr，也不能单凭此区分所有 vcall/vbase 元数据角色。

末尾 B 不写 LR，支持尾分支适配器解释；实际返回方式仍取决于目标实现。摘录未展示返回值调整，不能称其为协变返回 thunk。它也不像典型经 GOT 间接跳转的 PLT 入口，但未据此排除所有自定义跳板。

关键断点：0x1a924c8 跳往 0x1a92434，并非 0x1a924b8。虽然 0x1a924b8 紧邻跳板入口且分支到 0x18b3168，必须读取 0x1a92434 至 0x1a924bc 的控制流，才能判断前者是否能到达后者。地址邻近不构成边。0x18b3168 到 0x18b31e4 的主体、条件和寄存器准备同样缺失。

## 重复三项布局可能是什么

若用户扫描完整准确，示例对应：

| 槽地址 | RELA addend（用户提供或据槽位算术推导） |
| --- | --- |
| 0x27b7c08 | 0x1a923d4 |
| 0x27b7c10 | 0x1a924bc |
| 0x27b7c18 | 0x1a92650 |

槽地址间隔 8 字节与 AArch64 的普通指针宽度一致。相同三元组重复，支持多个表复用相同接口布局、继承实现或子对象 thunk 的假设；也可能是构造虚表、其他函数指针数组或重复注册数据。还不能认定为完整 vtable、VTT 或某个类的主表。

若为 R_AARCH64_RELATIVE，运行时槽值通常按 B+A 重定位，B 为加载基址；用户仅称 RELA，仍须核对类型才能应用该公式。不能把 addend 与运行时已重定位指针等同。

28 是重定位命中数，不是类型数。一个类型可以有多个子虚表或构造表，不同类型也可以共享函数指针；链接优化亦可影响地址共享。邻项函数角色不能按顺序猜为析构、击球、限幅或回合处理。

## 已有配置数据流

以下仅为 A 级参考文本中可逐指令核对的静态关系，原 ELF 尚未独立反汇编：

1. caller_18b31fc.txt 中 0x18b321c 将入参 x0 保存到 x19；0x18b3374 与 0x18b339c 均 BL 0x18b09d4，分属由 0x18b3360 条件分支区分的路径。两条路径均在调用前把 x8 指向栈上 +0x38。不能据条件本身命名为在线/离线或玩家/机器人。
2. 0x18b09f8 将进入时 x8 保存至 x19，与 AArch64 间接结果地址的使用模式相容；因此该范围的 x19 不应直接当作传入 this。
3. 0x18b0a64/0x18b0a68 构造字符串地址 0x11cc3f0，既有字符串记录将其标为 shotPowerLimits；随后调用 0x26c1074，并根据返回对象 +8 的标签是否等于 4 选择指针或后备值。标签 4 的类型名称未独立确认。
4. 经 0x26e630c、标签 5 分支、容器复制候选 0x18b15a4，数据进入栈上 +0x50 容器。0x18b0f88 与 0x18b0f98/0x18b0f9c 分别取该容器数据起点及其 +0x10 的条目，调用 0x2706e20，随后 0x18b0f90、0x18b0fa4 将 d0 存至结果地址 +0x20、+0x28。
5. 因此可提出“两个源条目经转换，写入两个 64 位浮点寄存器存储字段”的候选映射。不能确定转换函数签名、源容器安全长度、结果字段名称、顺序含义、单位和实际值；不能把这两个字段直接宣布为最小/最大力度。预置 d0=0 也不能单独证明业务默认值为零。
6. 调用方在 0x18b33a8 起搬运结果，0x18b3414/0x18b3418 将新指针写入入口 x19 所指对象 +0x20，并对旧值作条件处理。这支持“持有构建结果的对象”描述，不能据此指定 C++ 类名或证明它就是 MatchControllerTurnBased。

候选上游链应写成：

```text
[用户摘录] 表槽 -> 0x1a924bc -> 0x1a92434
[缺失控制流] 0x1a92434 ... ? ... 0x1a924b8
[用户摘录] 0x1a924b8 -> 0x18b3168
[缺失主体] 0x18b3168 ... ? ... 0x18b31e4
[用户摘录] 0x18b31e4 -> 0x18b31fc
[已有反汇编文本] 0x18b3374 / 0x18b339c -> 0x18b09d4
[已有反汇编文本] shotPowerLimits 相关数据 -> 结果 +0x20 / +0x28 候选
```

这是证据等级混合的待补全链，不是已闭合调用图。即便全部静态边补齐，也只证明代码路径存在，不证明运行时触发。

## 类型名、调用者与对局关联检索

### 能支持的类型线索

/reference-inputs/native_keywords.txt 的实际检索命中：2112 行存在 24MatchControllerTurnBased；1403 行含该类 .mm 文件的构建路径字符串；3038–3040、3846–3848 行有 setupAimControls(const Player&) 局部闭包类型名，3039 行编码 EEFviddbjEEE 与参数形状 void(int,double,double,bool,unsigned int) 相容。另有 setupTable、physicsStopped、prepareStrikers、scorePucksForTeam、createStrikerBarDelegate 等闭包名字。

这些是命名线索，不是 0x1a92434、0x1a924bc 或 0x27b7c10 的符号绑定。两个 double 的语义未知，不得命名为角度与力度。构建路径是二进制中的文字，不代表当前环境拥有该源文件。

符号 JSON 限定检索 MatchController 命中六个 _You_Forgot_To_Register_Module_* 注册标记，涉及 Carrom、GoldenShot、DiscPool、Tutorial、PointCarrom、PointDiscPool；没有得到目标地址对应的方法名。对已提取两个文本检索字面量 1a924 和 18b31 均未命中；这是有限文本搜索结果，不证明原 ELF 无相关引用，符号 value 也可能使用十进制。

### 邻近 RTTI 不能绑定新增跳板

native_RTTI附近引用候选.json 将 0x2846e38 -> 0x27a2868 标为 MatchShotSolver::simulateShot 局部闭包附近候选，将 0x284a398 -> 0x27b92f8 标为 MatchControllerCarrom::physicsStoppedExtra 局部闭包附近候选。这两项都不是 0x27b7c10 表的已证类型头。不能用地址相近或模块名相同跨表认领类型。

已有 MatchShotSolver 的构造、startSolving、simulateShot 字符串引用范围多为 28 字节，仅支持类型名访问辅助代码候选，不能当成求解算法。

### 对局消息关联是独立线索

native_字符串交叉引用候选.json 含 MatchFlowTurnBasedOnline 对 ServerMessage<const gameplay_aim_event> 的 EventBus 注册相关类型字符串；native_对局消息类型信息候选.json 含 19gameplay_shot_taken、21gameplay_shot_outcome 字符串及其 RTTI/vtable 相容重定位候选。

shot_construct_call_1aa3e04.txt 确有 0x1aa3e04 BL 0x1fa8e80，随后在栈上结构写入 d9/d8 和 w21/w20，后续还调用 0x1fa989c、0x18d8e0c 等。可作为击球消息构造/封装的研究入口；仅凭本轮所读摘录不能确认每个字段或网络发送语义。

上述消息入口没有已建立的数据流或控制流边连接到新增 thunk、28 组表、0x18b31fc 或结果 +0x20/+0x28。对局关联目前停留在同构建命名与独立静态入口层，不能声称该 thunk 用于瞄准、击球限幅、机器人、联网同步或任何特定模式。

配置加载候选中 GameConfiguration.plist、decryptAES128、downloadClientConfiguration 等名称彼此独立；本轮没有证明 shotPowerLimits 来源于该文件、使用 AES 或来自线上。

## 最小额外验证：按结论分层

以下均为待执行方案，不是本轮结果。优先索取小范围证据，无需整包重新分析。

### 第一批：核验跳板及闭合静态链

1. 对原 ELF 重新计算 SHA256，并提供 PT_LOAD 映射和相关节区范围。对目标 VA 按 p_offset+(VA-p_vaddr) 映射，保留映射依据；不要默认 VA 等于文件偏移。
2. 导出 0x1a923d4 至至少 0x1a924cc 的原始字节及完整反汇编，覆盖 0x1a92434 实现和 0x1a924b8 尾分支。若需识别 +8 邻项角色，再补 0x1a92650 所在真实函数范围。结合 FDE、分支和返回检查边界，不单靠 FDE 命名语义函数。
3. 导出 0x18b3168 至 0x18b31fc 的字节、反汇编和栈恢复序列，追踪到尾分支时 x0、其他参数及 LR；验证是否可到达尾分支，并确认恢复的是当前帧。尾 B 不是普通 BL，须明确返回地址继承。

通过条件：原始字节支持指令，所有中间可达基本块及条件可列明。若无法连接 0x1a92434 到 0x1a924b8，则保留为两条独立路径，不能拼接。

### 第二批：证明表结构及取得最小类型名

4. 提供全部 28 项原始 RELA 记录，至少含重定位节、r_offset、r_info/类型、符号索引和 r_addend，以及每项 ±8 邻项记录；检查命中去重、槽对齐和所属节区。先核对示例 0x27b7c10，再验证“所有”这一全称结论。
5. 对示例槽导出足够向前覆盖可能 address point 及其 -0xc8 的窗口，并带后续函数槽、所有重定位和按有符号整数解释的负向元数据。应先定位候选 address point，不能把 0x27b7c10 自身直接当作 address point。若发现 offset-to-top/typeinfo 表头，沿 RTTI 名字指针读取真实字符串，核验 typeinfo 自身结构及基类关系；零 RTTI 或结构不符时不强行定型。
6. 找一个将该候选 address point 写入对象的构造/初始化引用，并核对写入的子对象偏移；再找一个匹配槽索引的间接调用。两者与 RTTI 共同支持类型归属。最小起点是一组完整表，其他 27 组只在需要概括其共性时扩展。

通过条件：表头、address point、-0xc8 元数据及函数槽关系自洽，并获得实际类型名字或明确无 RTTI 的限制。仅确认三元组不满足类型确认。

### 第三批：区分静态调用者、业务与运行证据

7. 扫描 BL、B 和地址取用至跳板/实现/中间入口，保留间接调用遗漏范围。对候选调用者追踪 x0 的对象来源、vptr 和槽偏移；静态 xref 只能给出潜在调用者。
8. 仅在需要证明运行可达时，取得匹配进程 maps，计算 load bias，在获授权的只读观测环境记录某次真实对局场景、PC 序列、x0、vptr、负向调整值和调用栈。静态工具不能替代此步骤；当前工具未提供 ADB 或原生调试器，本轮未执行。
9. 仅在需要确定力度业务时，再沿结果 +0x20/+0x28 的读取者追踪到明确运算和输入/输出，确认字段及配置来源；实际值须来自可追溯配置或运行观测，不能由函数地址、字段宽度或英文键名推导。

结构验证不必等待运行观测；运行与业务结论则不能由结构验证自动推出。

## 本轮验证、产物与限制

已执行：读取所选 casual-game-production/SKILL.md 及四份冻结品类/框架正文；列出两个 ZIP 全部条目；读取上表相关正文；提取两个研究文本并进行上述限定检索；人工对照已有反汇编文本的数据流和证据边界。

未执行：原 ELF 重组与哈希复算、机器码重反汇编、28 项重定位重扫、完整符号逐项审查、RTTI/vtable 原始结构解析、原生进程或对局观测、力度参数测量。没有运行 npm run build、npm test、npm run check；本轮为只读研究报告阶段，不产出或验证 Web 游戏，也不通过验证命令绕过工具边界执行二进制分析。

产物：/workflow/prototype.md。参考副本：/reference-inputs/native_keywords.txt、/reference-inputs/native_symbols.json。未生成图片、游戏、dist、源码包或发布包。

本轮需求为原生证据复核，通用生产模板中的核心游戏循环、界面布局、胜负计分、物理步长、输入窗口和可接受误差均不适用，亦未从摘录中得到这些规则；不编造原型数值或英文玩家界面。本报告以证据分级、静态链是否闭合、类型绑定是否成立及最小补证方案作为研究验收条件。仅完成当前报告，不表示用户已确认下一阶段。
