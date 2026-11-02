# 工具链与格式分支

## Python 工具

优先复用已有隔离环境；项目要求 conda base 时先激活。可将本技能的 Python 依赖装入独立目录，避免改动应用依赖：

```bash
python -m pip install --target "$TOOLS/python" -r "$SKILL_DIR/scripts/requirements.txt"
export APK_ANALYSIS_PYTHONPATH="$TOOLS/python"
```

`TOOLS` 为自行选定的工具目录，不用 HOME 等系统变量保存工作路径。脚本读取 `APK_ANALYSIS_PYTHONPATH`，未设置时直接使用当前环境。锁定版本是已验证组合，不意味着适配所有历史或未来包；格式错误时查工具官方文档，再隔离升级并重新验证。

已验证：UnityPy 1.25.3、androguard 4.1.4、pyelftools 0.33、TypeTreeGeneratorAPI 0.0.10、capstone 5.0.9、Pillow 12.3.0。

## Unity IL2CPP

识别 `lib/<ABI>/libil2cpp.so`、`assets/bin/Data/Managed/Metadata/global-metadata.dat`、Unity 数据文件。基包与 ABI split 需要一起分析；不要混用不同版本的库和 metadata。

使用 [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) 官方版本，外部二进制单独安装，不随技能分发。示意命令：

```bash
"$DOTNET" "$DUMPER/Il2CppDumper.dll" "$IL2CPP_LIBRARY" "$METADATA" "$WORK/code/il2cpp" > "$WORK/il2cpp.log" 2>&1
```

变量均指实际工具和输入路径。按工具发布说明安装对应 .NET 运行时；在自己安装的配置中将 `RequireAnyKey` 设为 false，避免无人值守流程卡在等待按键。已验证过 Dumper 6.7.46 与 .NET 6，但不能据此保证所有 metadata 版本适配。记录退出码、日志、实际生成文件，不只看命令是否返回。

重点产物：`dump.cs` 的类/字段/RVA，`script.json` 的方法地址和签名，`DummyDll` 的占位类型信息。`index_code.py` 使用 Dumper 的格式；输入不匹配时先检查，不把零条类型视为成功。需要进一步推断复杂算法时可用 Ghidra/IDA 等工具，结论注明反编译推断；本技能不内置这些大型工具。

[Unity IL2CPP 官方说明](https://docs.unity3d.com/Manual/scripting-backends-il2cpp.html)解释了 C# 转换为 C++ 再编译的流程，因此恢复类型并不等于恢复 C# 方法体。

## Java / Kotlin 与 DEX

[JADX](https://github.com/skylot/jadx) 分析启动 Activity、权限、桥接层、计费、广告、统计及 Java/Kotlin 游戏逻辑。扫描所有 DEX，包括容器或 SDK 内嵌 DEX，分别标注其位置和分析范围。

```bash
mkdir -p "$WORK/code/java"
timeout 300 "$JADX" --no-res -d "$WORK/code/java" /实际路径/classes.dex > "$WORK/jadx.log" 2>&1
```

300 秒是可调整的单次预算，不是准确性要求。退出码 124 表示超时，输出属于部分结果。记录失败类数；结构化反编译停滞时，查看当前版本帮助，使用 `--decompilation-mode fallback` 输出到独立目录，并明确结果退化。已验证 JADX 1.5.6 / Java 17；不要无限等待巨大的 SDK，也不要把 SDK 文件数当作业务复杂度。

## 其他格式

| 证据 | 分支与交付边界 |
| --- | --- |
| Unity Managed/*.dll | Mono，使用合适的 .NET 反编译器阅读真实 IL；Unity 资源导出仍适用。占位 DummyDll 与真实 Managed DLL 必须区分。 |
| Cocos JS/Lua、jsc、资源清单 | 优先阅读明文脚本和图集配置；编译、压缩、加密格式分别识别。未成功解码时保留原文件，不声称恢复业务代码。 |
| Unreal libUE、pak/ucas/utoc | 核实引擎版本与容器格式后选匹配工具；通用脚本只提供安装包库存和普通媒体，不承诺恢复 Blueprint。 |
| Flutter libapp.so、flutter_assets | 区分 Dart AOT 与明文资源；JADX 仅覆盖 Android 壳层。 |
| 普通 Android 与自研原生库 | JADX 阅读 DEX，按 ELF ABI 使用原生分析工具；本技能 native_methods.py 依赖 Dumper 地址表，不能直接用于任意 ELF。 |
| OBB、动态下载、加密容器 | 保留包内证据；可识别的归档安全解开后追加扫描，缺失远程文件要列出覆盖缺口。 |

资源工具的主参考：[UnityPy](https://github.com/K0lb3/UnityPy)、[TypeTreeGeneratorAPI](https://github.com/UnityPy-Org/TypeTreeGeneratorAPI)。特殊格式不确定时只依赖官方文档、源码或格式资料核实。
