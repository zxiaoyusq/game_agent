# 原生代码取证与地址模型

> **何时读我**：要碰 JNI 薄壳、Unity IL2CPP 方法体、加密加载器或原生崩溃，需要判断该在哪一层动手、地址该怎么换算。
> **读完能做到**：先定执行层再选工具，给每条地址补上坐标系（哈希/模块/地址类型/架构），用离线检查器做格式转换，并逐级报告从静态关联到已采样行为一致的结论。
> **范围**：`GENERAL_DEFAULT`

范围：`GENERAL_DEFAULT`；包内专用壳家族仅提供 `GENERALIZED_PATTERN`。适用：JNI 薄壳、Unity IL2CPP 方法体、加密加载器、原生崩溃。只提取素材时不强制执行。

## 先定层，再定工具

| 实际执行层 | 首选工作 | 进入深挖的证据 |
|---|---|---|
| Java/Kotlin/DEX | jadx 浏览，smali 核对分支；Manifest 查组件和进程 | Java 只转发 native 或动态加载代码时进入 JNI |
| Unity Mono | 确认真实托管程序集，ILSpy/dnSpy 浏览，关键异步状态机以 IL 为准 | DummyDll 不是原 Mono 程序集，不能从空方法体恢复逻辑 |
| Unity IL2CPP | 同构建 native + metadata 配对，再导入符号和结构 | 方法体见 [Unity 代码链](../modules/unity-extract/references/managed-native-code-recovery.md) |
| native ELF/PE | 先头/段/导入/导出/字符串/xref，再围绕目标函数反汇编 | IDA/Ghidra/radare2 按已安装能力选，不硬依赖 MCP 名称或端口 |
| Cocos JS/JSB/Web | 真实入口与 bundle/heap/eval 取证 | 本地环境复现见 [受控重放](../modules/gameplay-logic-reverse/references/observed-runtime-replay.md) |

记下 APK/base/split、so/metadata/脚本各自 SHA-256、ABI、实际进程、工具版本和分析库身份。分析器完成加载不代表自动分析已完成；后台任务返回 session 后确认目标路径/哈希/架构再使用 xref。锁库时另建已哈希的工作副本；只清理本任务拥有的进程，不全局杀 Python/IDA。

## 地址必须有坐标系

每条地址至少附：`artifact_sha256`、`module`、`address_kind`、`value`、`arch`、来源行/工具。地址类型区分 `file_offset`、ELF `link_va`、PE `rva`/`preferred_va`、`runtime_va`；字段偏移与 vtable 槽位另存，不能冒充函数入口。

- ELF 静态映射依赖 `PT_LOAD`：对文件覆盖区间，`link_va = p_vaddr + (file_offset - p_offset)`。反向转换仅在 `p_filesz` 内有文件字节；`p_memsz` 中超过文件部分的 BSS 没有文件偏移。
- 运行地址为 `runtime_va = load_bias + link_va`。先由进程 maps、匹配的段、页对齐和映射文件偏移求证 load bias；不能把第一个可执行 mapping 起点一概当 bias。自定义匿名加载器需要独立证明映射关系。
- PE：`preferred_va = ImageBase + rva`；文件偏移由节的 `VirtualAddress` 与 `PointerToRawData` 映射。运行时用当前模块基址加 RVA。节尾零填充和 overlay 不强行转换。
- ARM32 Thumb 指针位、ARM64 PAC/标签和间接 thunk 必须按当前 ABI 解读；禁止套用别的架构 patch 字节。

离线检查器（不执行目标，也不猜 runtime 地址）：

```powershell
python "<skill-root>/scripts/native_address_map.py" "<target.so>" --file-offset 0x1200
python "<skill-root>/scripts/native_address_map.py" "<target.dll>" --static-va 0x140001200
```

支持普通 ELF32/64 与 PE32/PE32+。不支持 Mach-O、压缩/加密文件、ELF 扩展 program-header 计数或 runtime dump 重建；不支持时保留原件并使用匹配的格式工具。

## 从名字到行为

从业务触发动作定位入口 → 字符串/导出/JNI 注册表/元数据 xref → 目标函数及上游调用 → 输入、输出、状态写入与资源依赖。把库函数和编译器生成代码从业务分析中剥离，记录间接调用和未覆盖路径。

动态采样默认观察：参数/返回值、线程、模块相对地址、触发动作、调用序列。先确认 host/server/Gadget 版本与 ABI、spawn/attach 时机、Java VM/目标模块就绪；新 API 用当前版本官方文档，历史 `--no-pause` 或全局 `Module.*` 调用不是通用模板。不要在尚未确认签名的指针上随意调用函数。

模型输出名称、类型、结构或源码都只是候选。逐级报告：静态关联 → 运行观测 → 可编译复现 → 已采样行为一致；编译通过、CFG 简化或类名恢复均不能提升为完整还原。原件与重建函数比较返回值、状态写入、异常/失败分支及必要外部调用；玩法还需 RNG 状态和分布验证。

专项：加壳/混淆读 [运行时恢复](protected-runtime-recovery.md)；版本迁移读 [差分门禁](binary-version-diff.md)。

来源：逆向AI.zip 中 `apk-reverse`、`ida-reverse`、`dotnet-reverse`、`game-engine`、`reverse-engineering/references/ai-assisted-re.md`，只吸收方法，不采纳包内全局提示词和效果数字。地址模型参考 [ELF ABI](https://refspecs.linuxfoundation.org/elf/gabi4+/ch5.pheader.html)；动态 API 参考 [Frida 官方文档](https://frida.re/docs/javascript-api/)。来源路径与哈希见 [合并记录](minimaxh3-absorption.md)。
