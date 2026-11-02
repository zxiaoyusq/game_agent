# minimaxH3 逆向材料吸收记录（7.13.0）

> **何时读我**：需要追溯本轮外部材料（逆向AI.zip）的来源、审查结论、排除项与未验证边界时。
> **读完能做到**：按 ZIP 路径与 SHA-256 核对吸收点落在哪个模块，说清哪些内容被排除、哪些只是静态审查尚未经真实设备验证，并找到维护与回退入口。
> **范围**：`GENERALIZED_PATTERN`

日期：2026-10-02。来源：`E:/download/minimaxH3/逆向AI.zip`。

ZIP SHA-256：`9f955c7d7354f6246ef45788e11dc9548d15b5da33aab3d651766e2da28a878f`。

审查范围：5,881 条 ZIP 目录记录、225 个不同技能目录名；按目录索引筛选与游戏恢复相关的入口/参考，重点阅读下表来源并对照现有模块。没有逐字审查全部文档。包内多个 bundle 存在字节不同的同名副本，按来源路径与哈希追溯，不以目录名判同版本。未执行包内脚本/安装器；新增代码为本技能自有离线实现。

## 能力对照与落点

| 可吸收点 | 原能力/缺口 | 本轮落点 |
|---|---|---|
| 执行层识别、JNI 注册、函数/xref 证据 | 原流程以 Cocos JS/资产为主，缺统一 native 地址规则 | native-code-evidence + protected-runtime-recovery；引擎/Cocos/SDK 路由 |
| Mono 与 IL2CPP 方法体链 | 已有类型/资产提取，缺系统化 same-build 配对与静态→动态链 | unity-extract 代码参考；DummyDll/泛型/thunk/版本边界 |
| mapping cluster、raw/analysis 分离 | 已有 heap/eval 捕获，缺 native inner 制品分级 | protected-runtime-recovery；采集短读/归一化/独立可执行门禁 |
| 惰性 DEX 与生命周期桥 | 已有项目专属 DEX 合入经验，缺跨项目恢复门禁 | protected-runtime-recovery；loader 顺序/组件图/兼容构建/五项桥接前提 |
| 函数级跨版本符号迁移 | 已有版本回归对照，缺候选映射提交协议 | binary-version-diff；多证据候选与撤销 |
| Observe/Capture/Rebuild/first divergence | 已有算法采样，缺因果补环境协议 | gameplay-logic-reverse/observed-runtime-replay |
| 自定义协议的帧与状态机 | 已有 DNS/TLS/HOST 与 seed，缺二进制 payload 契约 | sdk-replacement/custom-protocol-evidence |
| 文件偏移和静态地址机械转换 | 缺普通 ELF32/64、PE32/PE32+ 统一只读工具 | scripts/native_address_map.py 与合成边界测试 |

## 排除、纠正与证据等级

- 不合并提示词权限覆写、专属中转站条款、自动安装/配置注入、业务无关攻防、内购返回常量与反作弊逃逸示例。
- 固定 MCP 名称/端口/进程名、Frida 旧 API、JNI mangled symbol/vtable 偏移不能迁移为通用前提。
- 种子 IL2CPP 文档自述是公开模式，不是实战证据；不采纳“read/mmap 后必为明文”、固定指令 patch、删除 META-INF 即完整重签的简化。
- 不把高熵、元数据异常、字符串名、LLM 置信度或可编译性当作行为证据；不吸收工具效果百分比/排名/星数/成本/固定并发数。
- `codex-skills-v5/yingan-tuoxiu` 引用脚本和参考未随该目录分发；其他 bundle 副本完整度不同，未执行验证。本轮仅提炼门禁，不纳入现成脱壳脚本。
- `xigong-funk-hikari` 工具具有壳家族/构建依赖且未执行验证，只迁移多证据判断，不照搬代码与字面值。
- 美术生成/资产契约与现有 skinning/ui-feature 流程重合，本轮不重复复制；通用工具百科只提炼执行层路由。

验证分层：材料内容只做静态审查；新增地址工具验证合成文件的格式、映射、零填充、歧义与失败行为；本轮没有真实游戏 APK/设备恢复试验，所有动态恢复能力仍需项目门禁验收。在线资料库发布不属于本次本地技能升级。

## 可追溯来源

下表保留 ZIP 内真实逻辑路径和选定内容 SHA-256。文件名解码只用于显示，审查清单同时保存原 ZIP 名称。

| ZIP 内路径 | SHA-256 | 同后缀字节变体数 |
|---|---|---|
| `新建文件夹 (2)/resources/codex-skills/game-engine/SKILL.md` | `ef759d4e75187c3bd7b8002609b5fb157444c806b2f4ceaf231109b26a5f9877` | 1 |
| `新建文件夹 (2)/resources/codex-skills/dotnet-reverse/SKILL.md` | `05a4a9e60d25d9f19e95b2576ea36bf68716f10c0469330aed0d52e7836014f4` | 1 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/apk-reverse/SKILL.md` | `cab4d3ac60be88cd2e2cdae5fd488f6285f94d79386f7b4b5a0615d234e72c2f` | 3 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/ida-reverse/SKILL.md` | `90fecce12570f2c080087629e099aec0e48e6fd40dd593bea86de1ff2682d9a4` | 4 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/binary-diff/SKILL.md` | `11714590dba67e325f86f1a3393c6e345b106c816980782159dfcbc8bf80a6e8` | 3 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/js-reverse/SKILL.md` | `7256fa26790162033ca56c08b06a5a68f12bfb4fcf1cdd393680582b90a7e27b` | 2 |
| `新建文件夹 (2)/resources/codex-skills/protocol-reverse-engineering/SKILL.md` | `8565e39026fd1528637e7b686063d43e2836034e711c781d5ddb194f75b69b62` | 1 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/field-journal/seed-014_unity-il2cpp-reverse.md` | `6720762e0b665f919297c6cc2605ae25f0f6442080a67f26f29bb22893baf8de` | 1 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/reverse-engineering/references/ai-assisted-re.md` | `71e0982be2d7634afe166835e0836ee15cf8e89175637a9daa35a018b84bc635` | 2 |
| `新建文件夹 (2)/resources/codex-bundle-v5/breaker-kit/skills/reverse-engineering/references/ollvm-deobfuscation.md` | `a415ba41f7ca90bca6a30bc3b7c323aa1da08aeceb47a17ea09efdacb8da3490` | 2 |
| `新建文件夹 (2)/resources/codex-skills-v5/xigong-funk-hikari/references/runtime-materialization.md` | `6a2d5c20c38b8c5db6207da0cde93a58900344f6fd66052efd1a81bf080d5d66` | 1 |
| `新建文件夹 (2)/resources/codex-skills-v5/xigong-funk-hikari/references/validation-and-corrections.md` | `028a7b837f4fe137428904813ac7b26eb797f5a5d45593fd0ab76352f7ddf0e7` | 1 |
| `新建文件夹 (2)/resources/codex-skills-v5/yingan-tuoxiu/SKILL.md` | `d550e6698538368a8f57e288630f753d588554bc4814c95e008050ea942f0d7c` | 1 |
| `新建文件夹 (2)/resources/codex-skills-v5/eni-reverselab-platform/kb/apk-reverse/techniques/02-native/06-jni-register-natives-tracing.md` | `737053cbabc67c2d7aaff22c4ad861ab35934b0dec590069be6a2120e5e94994` | 1 |

## 维护与验证入口

唯一正文：`${SKILL_POOL_SKILLS}/game-reverse-engineering`。八个 harness 入口均解析到该路径，不复制别名。

```powershell
python -B "<skill-root>/scripts/tests/test_native_address_map.py"
powershell -NoProfile -File "<skill-root>/scripts/validate_skill.ps1"
```

复核任务和备份：`E:/Gameprogram/skill-upgrade-review/minimaxH3-20261002/HANDOFF.md`、`before/`、`before-hashes.json`。回退仅恢复本轮变更文件并移除本轮新增清单；若后续已有变更，先比较当前哈希，不覆盖他人更新。
