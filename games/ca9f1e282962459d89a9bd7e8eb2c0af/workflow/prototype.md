# Carrom 红棋覆盖专项只读核查

## 范围与结论

本轮为 prototype 阶段的专项原生材料研究，只读取竞品参考与生成研究报告，不制作游戏，不修改参考，不推进美术、代码或测试阶段。未引用当前 H5 源码、通用 Carrom 规则或网上其他版本规则作为竞品事实。

|问题|本轮结论|证据层级|
|---|---|---|
|覆盖是否必须出杆方棋色|无法证明，也无法否定。候选函数存在整数及字符串相等筛选，但尚未证明它们代表棋色、玩家或队伍|客户端条件数据流，字段语义缺证|
|同杆红棋与普通棋入袋先后是否影响覆盖|所读函数对已有集合做计数和布尔 OR；在字段及外部状态固定时，交换集合元素排列不改变该候选布尔值。但不能据此认定实际入袋顺序无关，上游可能已编码顺序|局部客户端表达式；上游规则缺证|
|犯规与覆盖谁优先|无法证明。存在多个犯规原因键，未获得相应裁决分支或事件执行链|字符串键存在；优先级缺证|
|服务端最终规则|无法证明。消息类型与接收订阅名称不等于服务端实现或线上行为|协议命名线索；无动态结果|

## 已读取约定

已读取本轮冻结 casual-game-production/SKILL.md，以及 genre/docs/general.md、genre/docs/physics.md、framework/docs/web-common.md、framework/docs/native-web.md。该 Skill 自述独立 APK 取证使用专项技能；本轮未另行扩充所选入口，沿用其中参考包证据与阶段报告约定。物理步长、碰撞数值、输入窗口、胜负与界面布局均未由当前证据确认；本任务不创建玩法原型，不用自行设定参数填补竞品事实。

## 参考包与身份

参考路径均相对 ref/：

1. mcp-inputs/mac-codex/0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa/Carrom_native_chunks.zip
   - 工具返回包 SHA256：0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa。完整枚举 7 项，展开 49,000,042 字节。
   - manifest.json SHA256：72553230106447931a42aae6dc0ce218a946a5ca84275a25cddaf2c9330d12ef，已完整读取。
   - parts/arm64.part000 至 part004 各 8,388,608 字节，part005 为 7,055,952 字节，总计 48,998,992 字节。清单中六项尺寸及 SHA256 与工具枚举返回逐项一致。
   - 清单声明 original_sha256 为 4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4。本轮未读取分卷二进制、拼接原库或独立重算整库哈希，不把清单声明当作本轮二进制校验。
2. mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip
   - 工具返回包 SHA256：ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1。完整枚举 35 项，展开 2,411,908 字节。已实际读取相关报告、反汇编、交叉引用、调用边、协议候选及符号 JSON 开头；未全读所有条目。

analysis/native_elf_符号.json 已读字符 0–6500，声明文件 libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so，EM_AARCH64、ELF64、ET_DYN，SHA256 与分卷清单声明一致；列出 .dynsym 7,923 项及 .text 等节。此为所供分析文本的身份一致性，尚非本轮从 ELF 头独立验证。未取得 APK Manifest 的包名、versionName、versionCode、签名证书、原始 APK 哈希，未读取 GNU build-id 的实际值。1491 仅可作为库文件名的一部分，不能直接称为应用版本号；GooglePlay/Gold/Release 也只是文件名与嵌入路径线索。未证明材料对应当前线上版本或特定对局模式。

## 核心证据与可复算地址

以下地址均为所供材料标注的 ELF link VA，不是文件偏移或运行时地址。

### E1：queenCovered 字符串与候选函数

文件：disassembly/09_queenCovered_1aa3458.txt。SHA256：0d5ea8f1c3ec5bbded18719168b4f163c258aac3a4f748e8c37a33a0aae1bf09。已完整读取。

analysis/native_字符串交叉引用候选.json，SHA256 7ee49831a8e4a862af476446d66878c54f68f2b54ea2e57a7d9056921a5f717a，记录 queenCovered 字符串位于 0x1232240，引用 0x1aa3708，FDE 范围 [0x1aa3458,0x1aa38b8)。反汇编中 ADRP 0x1232000 加 0x240 与字符串目标吻合。FDE 只是栈展开范围，不能独立证明业务函数身份。

以 S 表示入口 x0（保存到 x19）、M 表示 [S+0x2a0]，T 表示 0x18d750c 后调用 0x18d7948 的返回对象（保存到 x20）。调用 0x1a0ab20(S+8) 返回对象的 +0x20/+0x28 为循环端点，记录步幅 0x60。字段名称均保持未知。

局部条件可写为：

```text
count = 0
flag = false
for record in collection:
    a = int32(record + 0x20)
    if a != 0 and a != int32(M + 0x1c0): continue
    if string(record + 0x40) != string(M + 0x00): continue
    count += 1
    k = int32(T + 0x18)
    if (a == 0 and k == 2) or (k == 4 and int32(record + 0x00) == 0):
        flag = true
```

对应地址：

- 0x1aa34b0–0x1aa34c4：读取 a，允许零或等于 M+0x1c0。
- 0x1aa34c8–0x1aa3540：比较两处字符串长度和字节；长字符串路径调用 0x2798920。字符串结构是基于指令形态的解释，库函数符号尚未独立绑定。
- 0x1aa3544–0x1aa3568：读取 k、递增 count，并按上式把 w23 置一。循环内未见把 w23 重新清零，符合 OR 聚合。
- 0x1aa356c–0x1aa3574：记录指针加 0x60 并继续遍历。
- 0x1aa36f8–0x1aa3704：将 w23 的最低位放入临时值。
- 0x1aa3708–0x1aa3744：构造 queenCovered 键并经 0x1aa763c、0x2706868 处理该值；与组装键值数据相容，具体容器 API 尚未绑定。
- 0x1aa37c8–0x1aa37e0：构造另一个未命名字符串后调用 0x1aa38b8。未提供该函数体，不能判定为网络发送、统计埋点或最终裁决提交。

这比仅发现键名更强：已读指令支持候选布尔值的来源和筛选条件。但 a、k、record+0、字符串 owner 均未定名；不能把 0/2/4 指认为红棋、黑白棋、犯规或比赛模式枚举。count 也不能直接叫入袋数。

在输入字段和外部状态相同、遍历合法且无额外副作用的局部模型下，计数与 OR 对排列不敏感；该观察不涵盖集合构造过程、同杆事件时序、前一杆待覆盖状态或服务端规则。

### E2：直接调用者与状态更新边界

文件 disassembly/caller_1aa2eb0.txt，SHA256 af2612149a270ceb4d9121d011dfe2efee0ab0e697f0215c5b5f958dece9cf0a，已完整读取。

0x1aa30ac 把原 S 传入 x0，0x1aa30b0 直接 BL 到 0x1aa3458。此前 0x1aa3014 调用 0x1a0c248(S+8,入口参数 x1)。这是后续追踪数据输入的具体入口，但其函数体和参数类型缺失。调用者后面读取入口参数 +0xb4 及 S+0x304 等字段；这些分支尚不能命名为犯规优先级。

analysis/native_候选函数直接调用.json，SHA256 2b224867627e101d78711410798bdb44ce79ac0bc2258d532c794393a3607bfc，支持上述 BL。扫描仅覆盖 BL 立即数匹配准确入口，不能排除间接调用、尾调用或范围中部入口。

### E3：命名及文案层线索

analysis/native_关键词字符串.txt 已逐字节提取为 /reference-inputs/native-keywords.txt，725,804 字节，SHA256 098c9c77cd66d97944947ce57691a23166527b498463b3772b01876b8d073f2e。已实际 grep 并读取相关行：

- 4914–4918：hint_cover_queen、hint_pot_queen_first、hint_unable_cover_queen、hint_unable_cover_queen_opponent、hint_unable_cover_queen_teammate。
- 4742–4746：effect_foul_reason_pot_last_puck_before_queen、effect_foul_reason_pot_opponent_last_puck、effect_foul_reason_pot_opponent_last_puck_and_queen、effect_foul_reason_pot_opponent_last_puck_before_cover、effect_foul_reason_striker_pot。
- 5200：queenCovered；5204–5205：queen_covered、queen_pocketed。
- 4558：addPuckWithColor:puckId:position:ownerPuckBase:ownerPlayerId:，仅证明命名中区分 Color 与 owner，未证明与候选结构偏移对应。

这些是键名、类型名或选择子，未读取其本地化显示正文、触发条件与使用分支。opponent/teammate 名称提示值得追踪，但不足以证明必须本方棋色；before 键名不足以证明同杆物理入袋先后；字符串文件排序不是规则优先级。小写 color 检索主要命中 shader，不能据此断言不存在棋色判定。

### E4：消息与客户端裁决入口线索

关键词文件 3304/3306 行存在 MatchFlowTurnBasedOnline 对 ServerMessage<gameplay_shot_taken/outcome> 的订阅类型名；3050–3053、3858–3861 行存在 MatchRefereeShotDiscPool::process(gameplay_referee_animation_outcome_request) 的 lambda 类型名。它们支持后续定位客户端处理链，不能证明本任务红棋规则属于 DiscPool 模式，也不能证明服务端独占或客户端独占裁决。

analysis/native_对局消息类型信息候选.json（SHA256 42cad3218cae2342d1bc3bcdfeebc1ffba7ef13e8abbb5712afbd222efee41df）记录 gameplay_shot_taken 与 gameplay_shot_outcome 的 RTTI/vtable 候选。analysis/native_击球消息线格式候选.json（SHA256 f20ada502ec9e76a5b8bbb3e66a895ef1d27ae5ac948bb1f603817333b26a9e6）只给 gameplay_shot_taken 候选的字段号及 wire type，未证明字段名、棋色或事件顺序。disassembly/shot_construct_call_1aa3e04.txt 已读，显示构造及包装调用；未见线上返回结果，不能提升为服务端规则证据。

### E5：排除短类型匹配辅助代码误读

完整读取 disassembly/07_physicsStopped_1a855b8.txt 与 08_physicsStopped_1a94c3c.txt。两段均仅 28 字节，加载指针、对比类型名地址、条件返回 x0+8 或零。它们不是 physicsStopped 结算函数主体，不支持先犯规后覆盖或相反顺序。

## 最短可执行补证路径

当前工具没有二进制拼接/解析、反汇编执行器、ADB、调试器或原生运行环境；不得用 npm 验证脚本绕过限制。以下是下一轮应执行的步骤，不是本轮执行结果。

### 静态路径（先补最少材料）

1. 在获准原生分析环境按 manifest 的 parts 顺序拼接六卷，逐卷重算 SHA256，再检查整库 SHA256 是否为 4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4。读取 ELF header、PT_LOAD、GNU build-id；补同来源 APK Manifest 与签名、包名、versionCode/versionName、APK 哈希，建立版本和库的绑定。
2. 优先补 0x1a0c248、0x1a0ab20、0x18d7948、0x1aa763c、0x2706868、0x1aa38b8、0x1ab1744 的符号绑定和完整反汇编；追踪 record+0、record+0x20、record+0x40、M+0x1c0、T+0x18 的写入点。先查清筛选究竟是棋色、玩家、队伍还是其他标识，再讨论本方覆盖。
3. 对 hint_unable_cover_queen_opponent/teammate、各 effect_foul_reason 键、queen_covered/queen_pocketed/puck_potted 做字符串地址定位与真实 xref，追踪到分支、事件生产者和消费者；不要继续把 RTTI 辅助范围当作业务函数体。
4. 为同杆顺序追踪集合生产者：确认是否保存事件发生序号、棋子 ID、棋色和出杆方，以及红棋 pending 状态如何跨杆保存。为犯规优先级读取覆盖和犯规共同上游的完整控制流与提交点。

地址换算必须使用实际 PT_LOAD：文件偏移 = p_offset + (linkVA - p_vaddr)，仅适用于目标位于该段文件映射区间；跨分卷时 partIndex=floor(fileOffset/8388608)，卷内偏移为余数。运行时地址 = loadBias + linkVA，loadBias 用匹配进程 maps 与 PT_LOAD 配对推导，不能直接把 maps 第一行起始值当 loadBias。本轮无 program headers，未填造具体文件偏移。

### 最短动态路径（匹配版本、固定模式）

先记录可运行 APK 的版本、原生库哈希、比赛模式/队伍与出杆方棋色。若设备库不匹配，不沿用本报告地址。选普通本方/对方棋均非最后一枚的局面，保持其他条件相同：

|用例|入袋序列|隔离目标|
|---|---|---|
|D1|红棋→本方普通棋，同杆且无犯规|正向基线|
|D2|红棋→对方普通棋，同杆且无犯规|覆盖棋色|
|D3|本方普通棋→红棋，同杆且无犯规|与 D1 对照同杆先后|
|D4|对方普通棋→红棋，同杆且无犯规|与 D2 对照同杆先后|
|D5|前一杆只入红棋，下一合法杆入本方普通棋|跨杆覆盖基线|
|D6|前一杆只入红棋，下一合法杆入对方普通棋|跨杆棋色|
|D7|D1 条件再加入 striker 入袋，分别控制其在覆盖棋前后入袋|犯规对覆盖影响及顺序|

最后一枚本方棋、最后一枚对方棋与红棋同杆、对方最后一枚与待覆盖状态分别单列，避免与普通覆盖测试混淆。每例保存入袋事件顺序、出杆前后局面、红棋返台与否、覆盖事件、犯规原因、回合 owner、得分及结算。尽量捕获客户端预提交结果与服务端返回后的权威状态；只看动画或提示不能区分本地预测和最终裁决。

若具备获准只读调试能力，最短观测点是匹配版本 0x1aa3458 入口、0x1aa3568、0x1aa3704 与直接调用处 0x1aa30b0；记录集合字段与 w23，并回溯生产者。不修改字段、不注入成功状态。若该函数输出与最终覆盖状态不一致，优先检查它是否只是统计/展示数据，不能强行认定为裁决核心。

判定标准：棋色要求必须由已绑定字段的可达分支或成对动态结果支持；顺序要求必须有交换顺序且其他条件匹配的对照；犯规优先级必须区分最终状态影响与消息展示先后，并用共同裁决链或组合用例证明。单次观测只说明该版本、模式、局面，不能外推全部 Carrom 模式。

## 实际操作、产物与限制

- 两包均完整枚举，相关清单和上述证据已实际读取；整库二进制重建、原始指令重反汇编与在线测试均未执行。所供反汇编指令字节与其文本解释只做人工阅读，未用独立解码器复核。
- /reference-inputs/native-keywords.txt 是真实提取的参考文本，不是新生成竞品资源或可发布源码。
- analysis/native_carrom_proto符号索引.csv 的读取被工具拒绝；保持 .csv 后缀提取到 reference-inputs/ 也被拒绝。未伪装扩展名或重复绕过，未将其内容当作已读。其他未读条目不作结论依据。
- 本轮报告路径：/workflow/prototype.md。参考包及游戏源码未修改。
- 未执行 npm run build、npm test、npm run check；本轮无游戏代码或测试阶段，不宣称构建、浏览器、真机、物理模拟或服务端验证通过。
- 无完整玩法主循环、界面或物理参数产出；这是按用户专项只读请求保留的研究边界。后续若继续逆向，应补选适用 APK 工程分析技能及必要原生工具/证据，不自动进入游戏生产下一阶段。
