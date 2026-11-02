# Unity Mono / IL2CPP 代码恢复证据链

> **何时读我**：哥哥要的不只是资产而是方法体、机制移植或加密初始化，或手上出现 metadata 解析失败 / magic 异常 / 高熵 / DummyDll 里没代码，需要判断是选错文件、拆包遗漏、构建不配对还是真加密时。
> **读完能做到**：把 base 与 ABI split 配对成一套不可混用的制品组，用 Il2CppInspectorRedux/Il2CppDumper 做小样本解析并定位 native 方法体，按四步分流 metadata 异常再决定是否上真实 loader，最后明确说出交付到了"类型与签名 / 方法体静态分析 / 原版调用采样 / 可编辑工程"哪一级。
> **范围**：`GENERAL_DEFAULT`

范围：`GENERAL_DEFAULT`。资产提取沿用本模块原流程；需要方法体、机制移植或加密初始化时再读本文。

## 构建配对

1. 收齐 APK/XAPK 的 base 与目标 ABI split；按实际文件搜索 metadata，常见位置包括 `Data/global-metadata.dat` 与 `Data/Managed/Metadata/global-metadata.dat`。PC 对应 GameAssembly.dll；不要假定 metadata 和 native 总在同一个 APK。
2. 为每个输入记录版本、ABI、哈希和来源。同名文件、相同包名或相近日期不能证明是同构建。
3. 真实 Managed/Assembly-CSharp.dll + CLR/IL 证据走 Mono；native+metadata 走 IL2CPP。导出的 DummyDll 只承载类型/签名，不等于原 C# 方法体。

## 静态 → 方法体 → 运行观测

- 用实际兼容的 Il2CppInspectorRedux / Il2CppDumper 做小样本解析；记录工具版本/参数/错误。工具支持新 Unity 不能由“更新到最新版”自动保证。
- 一次解析的 `dump.cs`/DummyDll、结构头、script.json/il2cpp.json 与 native 输入作为一个不可混用的制品组。验证可定位的类型/方法和若干入口地址后，再把对应 IDA/Ghidra 脚本导入工作库。
- 以业务入口、签名、调用者/被调用者及状态写入联合定位 native 方法体；泛型共享、内联、thunk、裁剪和缺失导出都要单独记录。字段 offset、方法 RVA 和文件 offset 不互换，遵循 [地址模型](../../../references/native-code-evidence.md)。
- 若需运行观测，等 IL2CPP 初始化和目标程序集就绪，核对当前类/命名空间/重载签名/静态或实例方法；只观察已定位的调用。桥接库是可选工具，不默认安装、不硬编码旧 API 或版本。

## metadata 异常分流

magic 异常、解析失败和高熵不能单独证明加密。依次排查选错文件、拆包遗漏、构建/ABI 不配对、解析器不兼容，再看真实 loader。`open/read/mmap` 后的数据可能仍是密文，必须证明解密完成和解析器实际消费的缓冲区再捕获；保留地址/长度/触发时机/原始哈希，验证结构边界与类型/方法关联。

runtime memory dump 与磁盘 ELF 有不同的重定位/指针语义，不能只拼接 maps 当作可加载 so。恢复方法见 [运行时恢复](../../../references/protected-runtime-recovery.md)。

## 交付级别

明确交付是“类型与签名”“方法体静态分析”“原版调用采样”“重建函数采样一致”还是“可编辑工程”；逐项标注未覆盖路径。至少选一个真实机制入口对照失败/正常输入和状态写入；只拿到方法名不能宣称玩法算法已恢复。

包内来源：`game-engine/SKILL.md`、`dotnet-reverse/SKILL.md` 与 `field-journal/seed-014_unity-il2cpp-reverse.md`。后者自述为公开模式种子，未视为实战验收；不吸收内购返回常量和全局绕过示例。[Il2CppDumper 官方说明](https://github.com/Perfare/Il2CppDumper)明确 DummyDll 不含代码、产物需 native 与 metadata 配对，工具兼容性仍以当前版本实测为准。
