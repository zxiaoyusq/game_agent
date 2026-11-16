# Carrom Disc Pool 19.6.0：配置封装与原生加载链静态研究

## 范围与结论

本轮 attempt=1，仅研究提供的 ZIP 目录及选定 UTF-8 证据文本，写入本报告；不制作游戏、不修改参考源文件、不进入美术、代码或测试阶段。19.6.0 是任务指定版本，当前已读材料未提供可独立验证的 APK 版本元数据。

已定位 GameConfiguration.plist 文件名、decryptAES128 名称、配置加载/重载相关字符串及其候选引用范围，但尚未证明“文件读取→转换→解析→配置发布→业务使用”的完整数据流。不能确认目标文件使用 AES，也不能确认模式、密钥、IV、填充、压缩算法或转换顺序。

## 实际读取资料与来源

参考路径均相对 ref/。以下简称 C、E：

- C：mcp-inputs/mac-codex/0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa/Carrom_native_chunks.zip；工具返回 ZIP SHA256 为 0d79feb7b5157fcabda15fb105581acd9fceddad0a9c331cb61cec047863b7aa。完整列出 7 项，展开总计 49,000,042 字节。
- E：mcp-inputs/mac-codex/ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1/Carrom_native_evidence.zip；工具返回 ZIP SHA256 为 ce1f99b1803f8e00f17e0d4c168119167d73602be41d7d643b45c41d4568e9b1。完整列出 35 项，展开总计 2,411,908 字节。

实际读取正文：

|包|条目|读取范围（字符，左闭右开）|工具返回条目 SHA256|
|---|---|---|---|
|C|manifest.json|全文 0–1050|72553230106447931a42aae6dc0ce218a946a5ca84275a25cddaf2c9330d12ef|
|E|analysis/native_配置与加密字符串.txt|全文 0–11815|8deecae45526c6b29000058f6173a24b01e933477959a2ac36a0db036f156614|
|E|analysis/native_配置加载交叉引用候选.json|全文 0–3496|4d984488b0186a91f13cb28b52235513c0794e09b20ca7b2cae583ecf80ac8bd|
|E|analysis/native_字符串交叉引用候选.json|全文 0–9280|7ee49831a8e4a862af476446d66878c54f68f2b54ea2e57a7d9056921a5f717a|
|E|analysis/native_字符串relocation候选.json|全文 0–1964|2c4d60f177ea7eb0c646be2db736bc739d81e359b78e531905a6625bd54162dd|
|E|report/竞品_ARM64代码定位.md|全文 0–2911|c355afd71272a5e62b8fdb2da4ee773bcb1b56d7f4464a60c24f1e0df588526f|
|E|analysis/native_候选函数直接调用.json|全文 0–1005|2b224867627e101d78711410798bdb44ce79ac0bc2258d532c794393a3607bfc|
|E|analysis/native_elf_符号.json|仅 0–8000，总长 1518754；未读全表|d4d1f06dc49bb5878b8119779ef6a937d8e0e30a795a1b4955712c431f8011cc|
|E|disassembly/01_shotPowerLimits_18b09d4.txt|全文 0–33109|e001c256d16c9ecfb846e9dbe318d2a8ee8b9fc1531a3b8592856944e51065aa|
|E|disassembly/09_queenCovered_1aa3458.txt|全文 0–12408|0d5ea8f1c3ec5bbded18719168b4f163c258aac3a4f748e8c37a33a0aae1bf09|

完整目录中均没有 GameConfiguration.plist 本体。C 的 6 个原生二进制分块仅取得目录级尺寸/哈希，未读取其机器码、未提取、未重组。E 中其余条目仅列目录，不视为已读正文。包内报告引用的旧目录和分析脚本未包含在当前已读证据中，不据此声称执行过这些脚本。

已读冻结方法资料：casual-game-production/SKILL.md（1.3.0，08eaf31ae71453f9236dadefb21d4d6b38335b9ca8071190c0af8b156af88a5b）；genre/docs/general.md（8d5058f8368fece60ae844b0d40217481746a7d8f0697b8f95cda9d78de64047）；genre/docs/physics.md（1aa7a11ef4bee1cb3bbd8acdf8c29cfed381e6450c5d0f77655c91dd5b1bd606）；framework/docs/web-common.md（5631072d40b38dfcb641838ceb1836e65d2a9ed07347215f8eb90819e25ceb08）；framework/docs/native-web.md（aed64f0a7b6968b89c178abd3b0b2a3e8a299a3ada68354ee6468c394c3980e3）。它们提供流程约束，不构成竞品实现证据。本轮未扩充未选技能；若下轮开展 APK 工程取证，应在启动时补选对应专项技能。

## 分块完整性与地址前提

C 的 manifest 按顺序记录 part000–part005，前五块各 8,388,608 字节，末块 7,055,952 字节，合计 48,998,992 字节；各块清单哈希与本次目录工具返回一致。manifest 声明 original_sha256=4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4，与 E 文本声称分析的原库哈希一致。这是元数据一致性核对，不是本轮重组后验证。

E 的符号 JSON 开头声明原库名 libgame-CARROM-GooglePlay-Gold-Release-Module-1491.so、EM_AARCH64、ELF64、ET_DYN，7923 个动态符号。仅阅读开头 8000 字符，不能声称全表检索不到某符号。下述地址均按证据定义为 ELF link VA，不是运行地址；不因若干字符串的 file_offset 与 link_va 数字相同，就将所有代码地址直接当文件偏移。

## 操作者观察：尚未独立复验

用户提供：目标文件 1,241,984 字节；SHA256=8ac8ad337c3c2f89812aa44f22a4bf01c09d05e2e8459d2e18918398592621f6；前 64 字节为：

```text
5d749775eaa741748adfbae818b3a2607b02a09999d9ed097a0d14ffcfb9115f5cdd94ae06b68bcbf0a1f67f12d2c8d2f978d2e9b27efa4db765120ffc8bade0
```

用户还报告长度整除 16、plistlib 报 InvalidFileException。本轮没有目标文件本体，未独立计算哈希、读取头字节、测量熵或运行 plistlib。根据给定数字算术可得 1,241,984=77,624×16；这不能识别加密算法、分组模式或填充。给定头部不是 bplist00，也不直接呈现常规 XML plist 起始标记，只能作为“需继续识别格式”的线索。解析失败不能区分加密、压缩、自定义封装、其他序列化、文件不完整或解析器兼容问题。

## 文件名及原生加载候选

以下为已读证据文本的确定内容，尚未用原生字节独立复验：

|线索|字符串 link VA|引用候选与 FDE 范围|可支持的判断|
|---|---|---|---|
|GameConfiguration.plist|0x1268b68|xref 0x1e3f710；[0x1e3f710,0x1e3f71c)，12 字节|存在文件名地址构造候选；短范围可能是名称访问器，未证明打开文件|
|decryptAES128|0x127251a|xref 0x2711cc4；[0x2711cb0,0x2711cd4)，36 字节|存在算法命名/分发相关候选；未证明处理目标配置|
|Configuration reload start|0x113d5bc|xref 0x1e418fc；[0x1e41898,0x1e41b0c)，628 字节|可优先追查重载过程，日志引用不等于文件读取或转换|
|downloadClientConfiguration|0x111a568|xref 0x1cbf6b8；[0x1cbf2fc,0x1cbfc44)，2376 字节|下载入口命名线索，未证明实际联网或本地文件来源|
|load_configuration|0x1268774|xref 0x1e37314；[0x1e36818,0x1e3b6d8)，20160 字节|可能是标签/操作名，不直接等于加载函数|
|$load_configuration|0x1338b60|xref 0x1c113b8；[0x1c112cc,0x1c11440)，372 字节|另一标签引用候选，与上一条不应自动合并|

扫描方法限于 ADRP 后 8 条指令内的 ADD immediate 匹配字符串起点；遗漏 literal load、间接指针、重定位和寄存器传递，且仍需排除中途寄存器改写。FDE 是栈展开范围，不自动证明函数语义、入口或可达性。本包没有上述配置候选的完整反汇编文本，因此不能补写其实际调用与返回值。

## 转换与后续配置使用

### 转换层：未闭合

当前只能列研究模型：文件名→路径解析/读取→零或多次转换→结构解析→配置容器→业务取值。所有相邻箭头均需数据流证据；decryptAES128 目前是孤立节点。不能把文件名与它在同一库中出现，当作两者存在调用关系。压缩后加密、加密后压缩、自定义头/校验、纯自定义二进制均属于待检验假设，不给出具体密钥或参数。

### 配置生命周期：名称层证据

配置字符串文本含 ConfigurationModel::reload、PackageManager::reloadConfiguration、mc::ConfigurationData::reloadInternal(bool,bool)、ConfigurationRecord、ConfigurationProperty<bool/int/float/string/unsigned/vector>，以及 ConfigurationReloaded、ConfigurationValueMapReloaded。可据此提出“配置对象、类型化属性和重载通知存在”的候选架构。类型名并不证明布局、执行顺序、默认值策略或与目标文件的绑定；downloadLatestConfiguration:andApplyConfiguration: 也不证明本轮有网络行为。

### shotPowerLimits：较强的候选取值链

已读已有反汇编文本显示：0x18b0a5c 调用 0x1c128d8，返回 x0 存入 x23；0x18b0a64/68 构造 shotPowerLimits 地址；0x18b0a70 调用 0x18ab3d4；0x18b0a74–80 将 x23+0x40、栈上键对象和来自入口 x0 的 x20 交给 0x26c1074。随后读取返回对象 +8 字节并与 4 比较，按条件选择载荷或后备指针；0x18b0aac 调用 0x26e630c，之后出现与 5 的标签比较及集合式处理。

沿正常分支，shotPowerLimits 对应结果进入 sp+0x50 所指临时集合；0x18b0f88–0x18b0fa4 对首元素和 +0x10 的下一元素分别调用 0x2706e20，并把 d0 写入输出 x19+0x20、x19+0x28。x19 来自入口 x8，符合 AArch64 间接结果位置的解释，但函数签名未恢复。

由此可提出“按键取值→类型/后备处理→集合元素转数值→输出结构字段”的较强假设。仍未读这些被调用函数的实现或符号映射，不能把标签 4/5 命名为确定的枚举，也不能确定两项为力度最小/最大、单位、实际数值、夹取规则或来源就是该 plist。直接调用索引另报告 0x18b3374、0x18b339c 两处 BL 指向 0x18b09d4；这是已有索引结果，调用者正文本轮未读。

### queenCovered：防止把状态字段误作配置键

0x1aa36f8–0x1aa3704 将 x23 的最低位与数值标签 3 写入栈上临时值，随后 0x1aa3708/0c 构造 queenCovered 键；0x1aa3738 调用 0x1aa763c，再于 0x1aa373c–44 对返回对象 +0x28 和临时值调用 0x2706868。相邻键也遵循类似路径。

这更符合“计算状态后按键组装记录”的解释，不能列为从 GameConfiguration.plist 读取 queenCovered 的证据。是否为统计、事件、序列化或其他记录，需解析 0x1aa763c、0x2706868、0x1aa38b8 后才可确定。索引报告 0x1aa30b0 直接调用该范围，但本轮未读调用者正文。

## 下一步：按真实字节逐项证伪

以下均为建议，尚未执行。当前工具没有任意二进制分析/重组执行器；不使用 run_validation 包装取证程序绕过边界。

1. 取得原始 GameConfiguration.plist 的只读副本及包内路径、版本元数据。独立记录长度、SHA256、首尾字节，与用户观察逐项比对；若哈希不符，先停止沿用本报告目标身份。对工作副本操作，不修改源文件。
2. 在具备授权的离线二进制工具环境，按 manifest 顺序拼接 6 块，逐块核哈希，再核整体是否为 4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4。匹配前不复用地址。解析 ELF PT_LOAD，按 p_offset+(VA-p_vaddr) 映射实际文件字节，并检查地址落在文件支持的范围内，不能直接用 VA 截取。
3. 对配置文件做无破坏格式检查：首尾/内部 magic、重复块、区段熵、可能头尾长度及结构边界。命中 magic 仍需完整解析与边界验证；未命中不证明加密。不得通过盲试密钥、IV 或长度整除关系选定 AES。
4. 先核 0x1e3f710 的完整 12 字节及分支，再找直接 BL/B 和重定位/函数指针引用者，分清返回文件名与实际打开文件。追踪调用者到路径选择、读取 API、返回缓冲区和长度；记录每步调用点、寄存器、字节范围和错误路径。
5. 展开 0x1e41898、0x1e36818、0x1c112cc、0x1cbf2fc 的相关控制流与被调用者，区分本地默认、缓存、下载及回退分支。只有同一缓冲区的定义/使用链或明确拷贝关系才能连接两节点，函数名相近不算证据。
6. 单独展开 0x2711cb0，先判断它是名称包装、分发注册还是实际转换。沿调用者验证输入是否来自步骤 4 的字节；若无路径，保留为无关联候选。仅从确证实现恢复参数来源，不猜参数。
7. 对每个已确认转换记录输入/输出长度、哈希、首尾字节、返回状态及消费方；若输出声称为 plist，要求解析成功、边界完整、根类型及代表字段合理。可解析片段或可打印字符串不能代替完整格式验证。没有实际输出不得声称解封成功。
8. 解析 0x1c128d8、0x26c1074、0x26e630c、0x2706e20，建立配置容器与 shotPowerLimits 的来源链；确认字段类型、回退、元素数量和输出字段的消费方。配置原文件→解析根→取值容器→业务字段每段都需独立证据。
9. 若静态链止于虚调用或动态分发，如实标注断点。运行时观察属于另行约定范围，本轮不启动、不用已有静态地址冒充运行地址。

## 验收与真实执行记录

- 已执行：两 ZIP 全量目录核对；10 个条目正文读取（其中符号 JSON 仅开头 8000 字符）；已选技能与全部 4 份冻结知识读取；分块清单尺寸/哈希元数据一致性核对；已有反汇编文本的局部人工数据流分析。
- 本轮产物：/workflow/prototype.md。
- 未执行：原库重组、原生机器码复验、新反汇编、目标文件哈希与 plistlib 复验、解密/解压/解析、联网采集、ADB、运行时观察、游戏构建与浏览器测试。现有 disassembly 文件是输入证据，不是本轮生成。
- npm run build、npm test、npm run check：未执行；当前为只读研究的原型报告阶段，不是代码或测试交付，不能记录为通过。
- 研究验收标准：证据与操作者观察分层；地址类型、读取范围和哈希可追溯；缺失箭头明确；算法及参数不猜测；下一步有输入与成功/失败判据。完整加载链、真实文件格式和版本独立核验仍未完成。

## 对生产模板的取舍

用户明确要求配置静态研究，因此不新增主循环、界面布局、规则状态、计分与胜负设计。竞品物理步长、碰撞参数、输入窗口和可接受误差在当前证据中均未确定，不以 Web 原型默认值代替竞品事实。本轮没有玩家界面或语言素材，不生成 dist 或试玩 ZIP，也不自动推进下一阶段。
