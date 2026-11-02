# Android Cocos JSB 生命周期、Trait 与发布验收

> **何时读我**：要处理生命周期 Trait 与发布前 QA——注入本地 Trait/config 后清屏不换材质或变两次、特殊材质预消除消失、广告结算异常，或重打包后准备真机验收时读我。
> **读完能做到**：先在当前项目重新定位 owner、事件与稳定边界，把异步加载改成 prepare 再在稳定边界 commit，并按最低证据清单完成发布前验收。
> **范围**：`GENERALIZED_PATTERN`

范围：`GENERALIZED_PATTERN`。先在当前项目重新定位 owner、事件和稳定边界，再应用本参考。

用于 APK 注入本地 Trait/config、恢复材质/清屏表现、修改广告结算，或重打包后需要真机验收的任务。完整 BlockMaster V123/V124 回归案例见 `modules/gameplay-logic-reverse/references/blockmaster-v123-v124-lifecycle-regression.md`。

## 1. 先确认直接基底

同一产品的不同原版可能拥有不同事件顺序、资源格式和 owner。当前工程应优先对照 `apktool.yml`、构建脚本和实际 APK 所证明的直接基底；历史抓包只做辅助。BlockMaster 当前直接基底为 Block Blast 10.4.7，9.5.0 是历史行为/资源对照。

## 2. 保留原版 owner 与事件顺序

| 症状 | 首查证据 | 安全规则 |
|---|---|---|
| 清屏不换材质 | 原版清屏/皮肤 Trait 的 owner、feature flag、监听器和效果 config | 保留原 owner，只修本轮选择或启用条件 |
| 清屏变两次 | 同一 epoch 内所有 skin/color 写入者和动画前后事件 | 一个事件一个 owner，只允许一次最终 commit |
| 特殊材质预消除消失 | 特殊材质 handler 的 show/hide/restore 链 | 不调用全局 cleanup，不清对象池，不隐藏整层 |
| 预消除高亮残留 | touch 是否结束、引导手势是否退出、动画是否结算 | 沿 show owner 的原生 end/restore 路径排查 |
| 每一步都换材质 | 切组监听是否误挂普通消行/touch end | 材质组只在已证实的新局/清屏边界切换 |
| 加载完成后随机错乱 | Trait 是否在交互/动画中途启用 | load 只 prepare，稳定边界才 commit |

`clearAllPreEliminateEffects()` 一类名称不能证明它适合每次 touch-end。先读调用上下文：它可能是池/层级重置，而特殊材质 handler 还拥有恢复被隐藏方块的配对操作。

禁止：

- 遍历所有 proxy/节点并尝试调用 clear/hide/remove；

- 任意延迟再次清理；

- 为消除双重变色关闭整个清屏 Trait；

- 在拖拽、预消除或动画中途启停 Trait；

- 用跨局“前 N 次清屏”预算代替原版 guide 状态。

## 3. 异步 prepare 与稳定 commit

资源下载、解密、bundle load 和代码注册可异步执行，但加载完成只设置 `pendingPresentationBundle`。满足以下条件后才能 commit：

- 当前没有 touch/drag/预消除生命周期在途；

- 当前动画 owner 已完成 end/restore；

- 材质资源和配套效果 config/handler/pool 同时 ready；

- 边界是原代码证实的 `new_game` 或对应清屏动画结束。

未就绪就保留旧组，延期到下一稳定边界。禁止“材质先到先换、效果晚到再补”，这会产生闪帧、双重变色和半套表现。

## 4. Replay 与引导

- Replay 第一条 `newGame=true` 同步放行；短窗口只去重重复事件。后台切换不得 await 后才开局。

- Replay 换组不等于连续清屏，不能触发 SSS。

- 引导完成态以持久化 guide step 为主，残留 guideLayer 只作辅助。

- 引导手指仍等待操作时，预消除高亮持续可能是原版设计；只在 touch/手势/动画都结束后判残留。

## 5. 两份执行副本与设备缓存

1. 核对主 assets index JS、Seed/remote patch index JS 和设备 `files/patch`。

2. 标记迁移必须识别旧实现，不能看到旧 marker 就直接跳过。

3. 对所有生成 JS 做语法检查，并比较已知良好包的目标字节差异。

4. 覆盖安装只用于快速回归；最终冷启动用卸载后安装或经用户授权的数据清理路径。

5. 设备端 `pm path` 拉回 APK，核对 SHA-256，避免测错版本。

## 6. 广告、DEX 与签名边界

- 广告自动结算必须 exactly-once，奖励与关闭组合后走原 `goOnGame`；Loading 兜底目标约 2 秒，不再要求 Tap to Continue。

- 全屏广告关闭后恢复输入和 Banner。Banner 常驻需要健康检查与退避重试，不能无限创建新广告对象。

- 修改只落在拥有行为的 DEX 槽位；保护槽位按项目门禁保持字节不变，避免 `NoClassDefFoundError` 或早期 Loading 卡死。

- debug 签名 APK 不能覆盖正式签名包，也不能作为正式发布结论。记录包名、设备序列号、候选 SHA-256、证书和安装方式。

## 7. 最低证据

- 变更前失败场景和根因级自动测试/静态门禁；

- 两份 JS 的哈希、语法、迁移 marker 和关键原版 owner 调用链；

- APK version/ABI/zipalign/签名/SHA-256；

- 清装首启、引导、Replay、新局、普通消行、清屏、特殊材质预消除、SSS/警告/棋盘效果；

- 每个切换 epoch 为零次或一次之外都直接失败；

- 真机奖励/插屏/Banner、Athena/Firebase、原厂域名隔离分别取证；

- 低端机长时 FPS/ANR/FATAL/内存观察；

- Git 显式 allowlist，只提交源码、构建器、测试和报告。
