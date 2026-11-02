# 加壳、混淆与运行时恢复门禁

> **何时读我**：静态文件里找不到关键代码或明文，或遇到 JNI 动态注册、惰性 DEX、匿名 native inner。
> **读完能做到**：追踪 JNI owner，做原始采集与分析副本的分离，按语义而非一键去混淆处理混淆，并走通惰性 DEX 与生命周期 wrapper 的恢复门禁和最终验收。
> **范围**：`GENERALIZED_PATTERN`

范围：`GENERALIZED_PATTERN`。适用：静态文件缺关键代码/明文、JNI 动态注册、惰性 DEX、匿名 native inner。具体 Hikari/影安特征只是来源案例，不作为当前游戏壳身份。

## JNI owner 追踪

从 Application/Activity、`System.loadLibrary`、native 声明、`JNI_OnLoad` 和实际组件进程关联启动链。动态注册时记录 Java 类、方法、JNI descriptor、注册时机、目标函数、模块/映射、地址基准及 consumer；静态 `Java_*` 导出不是全部 JNI 方法。

按当前 ART/ABI/工具枚举或验证 RegisterNatives 入口，不硬编码 mangled symbol 或函数表偏移。未命中先排查 attach 太晚、注册发生在另一进程、模块尚未加载或错误签名，不立即推断“没有注册”。

## Native 原始采集与分析副本

选 loader 完成且业务仍存活的稳定点，以 PID+进程名+参数核对对象。mapping cluster 由 loader 分配/权限转换、业务 PC/LR、字符串 consumer、相对布局多证据共同定位；“匿名/最大/RX”都不能单独定主程序。

保存原始 maps、时间、每段地址/权限/文件 offset/路径/哈希、捕获范围和 short-read/error。捕获失败页不得填零冒充成功；未映射 gap 与不可读页分开。已知运行时输出在静态文件搜不到，先查真实 consumer/inner，而非继续修改外层 helper。

原始段字节永不改；分析 ELF 是单独副本，记录 header、PT_LOAD、padding 的合成关系，保持 `p_offset/p_vaddr` 对齐约束。地址归一化逐处记录原值/新值/offset，先区分真正指针、普通整数、PAC/标签/压缩指针。不能全缓冲减 base。

区分：string snapshot、raw memory、analysis ELF、依赖原 loader 的可运行包、可由系统 linker 独立加载的镜像。IDA/readelf 能打开 synthetic ELF 不等于独立可执行；entry/import/reloc/TLS/constructor 缺失必须留为未完成。

## 反混淆以语义为准

识别字符串解密、不透明谓词、控制流平坦化、MBA、间接跳转/VM 各自证据，再按依赖处理；顺序由具体数据流决定，不套用“一键去混淆”。未解析分支保留，记录候选 CFG 与原反汇编。符号执行路径爆炸/工具不兼容时缩小函数或用受控动态观测，不强行猜边。

所有 patch 只作用工作副本，保存原字节/新字节/地址类型/原因/allowlist。新增补丁造成差异时分组消融定位；对照正常、失败和状态副作用。代码变短、伪代码好看、CFG 变直均不能替代行为验证。

## 惰性 DEX 恢复

原 APK、Manifest、Application、路由和 ClassLoader 图先冻结。走目标页面/功能触发惰性加载，逐轮保存实际 DEX 字节和来源；列文件名或类名不能充当 DEX 捕获。不要假定 ClassLoader 有通用 `getDexFileList()` API。

先识别 DEX 版本/容器（CompactDex 等另选匹配工具），校验 header、长度/区间、SHA-1 signature、Adler-32 checksum、map/class/method/code 引用及截断。新版 DEX 容器按对应规范验证，不能用旧 header 模板覆盖；格式校验通过不证明业务可执行。

同描述符的重复类比较定义与实际 loader 优先级，不能任意去重。按真实 Application/组件继承图和 runtime 路由制定显式恢复计划：源条目/哈希、目标位置、顺序、改动和门禁。首轮兼容构建保留必要 shell/native/assets；删除壳另算目标，不能静默删库。

native 生命周期 wrapper 改成 superclass 调用，仅在这五项同时有证据时考虑：实际 route 进入 wrapper；该方法为无代码 native 生命周期；直接父类是恢复后的具体类；父类存在相同 void 签名实现；原版/恢复日志能证明缺注册或桥接失败。还需追踪 native 初始化/副作用，不能凭五项匹配直接宣布等价。

## 最终验收与能力边界

恢复后核对包哈希/签名/ABI/版本，冷启动新 PID，确认 resumed 组件、真实目标路由、UI 和 logcat，覆盖惰性页面、返回/恢复及失败分支。补抓后重新验证 DEX 集合与组件图，原版存档逐字节恢复。

包内 `codex-skills-v5/yingan-tuoxiu` 只带入口与 requirements，缺其宣称的脚本/参考；其他 bundle 有不同完整度副本，也未经过本次执行验证。本文只吸收门禁，不提供或宣称可用的脱壳器。若缺工具/访问条件，交付证据与阻塞，不能虚构捕获成功。

来源：`xigong-funk-hikari/references/runtime-materialization.md`、`validation-and-corrections.md`、`yingan-tuoxiu/SKILL.md`、JNI tracing 与 OLLVM 参考，具体路径/哈希见 [合并记录](minimaxh3-absorption.md)。DEX 字段依据 [Android 官方规范](https://source.android.com/docs/core/runtime/dex-format)。
