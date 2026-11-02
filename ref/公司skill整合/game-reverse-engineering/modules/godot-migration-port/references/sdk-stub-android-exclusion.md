# SDK Stub 契约与 Android 排除边界 (Godot 迁移参考)

> **何时读我**：原版的真实 SDK 在克隆工程里不可用或不应上线，哥哥要按「接口契约 + 本地 stub」收口，或要处理 Android 导出侧的扩展与权限排除边界时。
> **读完能做到**：列出原版 SDK 接口清单并在 Godot 侧实现同名本地化 stub 服务，用 verify 脚本与仓库级门禁断言「接口齐全 + 无真实 SDK 调用 + 无外部域名/密钥/权限」，并在 export_presets 显式排除零调用扩展使导出包权限声明为空。
> **范围**：`GENERALIZED_PATTERN`

应用场景：Unity 迁移工程中，原版接入的真实 SDK 对研究克隆不可用/不应上线时，按"接口契约 + 本地 stub"收口。

## 1. SDK stub 契约模式

- 原版 SDK 接口先按反编译/日志/资源盘点列出接口清单（ads、IAP、RemoteConfig、社交、推送、归因、埋点、崩溃上报等），
  每个接口只保留签名与语义，不引入任何真实 SDK 二进制。
- Godot 侧按接口清单实现同名服务类（autoload + 统一信号/方法签名），行为全部本地化：
  - 广告/推送/归因 → no-op + 日志；
  - IAP → 本地商店 stub（购买直接成功/失败可配置）；
  - RemoteConfig → 本地默认值表；
  - 社交 → 本地玩家/好友 stub；
  - 崩溃上报 ICrashReporter → 本地文件/控制台，debug 可注入异常。
- 校验：verify 脚本断言"接口齐全 + 无真实 SDK 调用 + 无外部域名/密钥/权限"。仓库级门禁脚本按
  repo/build/manifest 三面扫描（SDK 二进制、secret、域名、权限声明），命中 0 才放行。

## 2. Android 导出排除边界

- Godot 导出默认会带上全部 GDExtension/插件；**未被调用（零调用）的扩展必须在 export_presets
  的 exclude_filter / 插件配置中显式排除**，并用"零调用守卫"（运行时无该扩展符号参与）双保险，否则
  arm64 lib 体积虚高且可能触发 ABI 启动问题。
- 判断"零调用"的口径：代码搜索引用数为 0 + 运行时符号未加载 + 导出包内该扩展不在 apk/so 清单。
- 移动端构建全程无真实 SDK 后，权限声明应为 0（minSdk/targetSdk 按要求配置），
  aapt dump permissions 空为合格。

## 3. 验证要点

- 每个 stub 服务存在测试（headless 可跑，如 test_sdk_stubs.gd），断言数量显式记录。
- 全量门禁脚本（汇总各阶段门禁）作为最终 gate 之一，结果落日志。
- 冷启动/包体/权限作为发布收口三项设备证据（am start -W、apk 大小、aapt 权限）。
