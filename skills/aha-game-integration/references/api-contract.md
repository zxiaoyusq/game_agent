# AHA 接口契约与模板差异

依据：2026-11-04 用户上传的 [API 原文](sources/aha-bridge-api.md)、[Solitaire 壳](sources/solitaire-shell.html.txt)、[通用壳](sources/template-shell.html.txt) 和 [扩展壳](sources/template-shell-2.html.txt)。这是上传版本的整理，不代表当前线上 SDK 的最新行为。档案哈希见 [来源清单](source-manifest.json)。

## 两种调用方式

| 接入方式 | 广告与加载入口 | 适用条件 |
| --- | --- | --- |
| 原生 Bridge | `window.bridgeCore.callBridgeSync` / `callBridge` | AHA 容器实际注入 Bridge；普通浏览器没有此对象 |
| 上传 SDK 壳 | `window.h5sdk.init` / `adBreak` / `gameLoadingCompleted` | 外层初始化 SDK，游戏位于同源 `game/index.html`；原例用父窗口全局回调 |

`window.a_bridge` 是上传壳的分支判断标记，不能证明每个 API 均可用。原生 Bridge 的注入脚本、就绪事件以及 SDK 更详细的初始化契约未包含在附件中，需要渠道确认。适配器允许延迟获取 Bridge，但不自动无限轮询；调用方在就绪时重新初始化尚未成功注册的监听。

## 原生协议速查

| 能力 | 协议 / 形式 | 上传文档标注版本 | 关键参数与判定 |
| --- | --- | --- | --- |
| 环境版本 | `/api/headers`，同步 | 5.1.48+ | 使用 `X-VersionName`；不要把返回的设备标识全部写入日志 |
| 自定义埋点 | `/event/proxySend`，同步 | 6.1.2+ | `eventName: string`、`eventId: long`（文档称 appId）、`eventData: JSON.stringify(data)`；无到账回执 |
| 扩展埋点字段 | 同上 `expandData` | 6.1.3+ | 可选 Boolean；最多展开一层。适配器默认不传，兼容 6.1.2 |
| 页面退出时长 | `/event/regPageDurTime`，同步 | 6.1.2+ | `eventName/eventId/eventData` 加 `pickDatas:[1]`；事件 ID 的定义与代理埋点表述不同，需核对渠道事件表 |
| AHA 规则埋点 | `/event/sendNew`，同步 | 位于 5.1.49+ 章节 | `action/elementStructs`；原文参数格式不完整，未实现自动转换 |
| 插屏 | `/ad/adBreak`，异步多次回调 | 位于 5.1.49+ 章节，未另列独立最低版本 | `appKey:string`，`type:start/pause/next/browse`，可选 `name`、`timeout`（ms） |
| 激励请求 | `/ad/adBreak`，异步多次回调 | 6.1.8+ | 同上，`type:reward` |
| 激励展示 | `/ad/showAdFn`，异步、无响应 | 6.1.8+ | 使用本次 code=4 返回的 `adShowToken`；不能自己生成 |
| 插屏免广告 | `/ad/shouldShieldAdForUser`，同步 | 6.1.12+ | Boolean；true 跳过插屏，原文明确目前仅用于插屏 |
| Banner 展示 | `/ad/showBanner`，同步 | 位于 5.1.49+ 章节 | `appKey`；没有展示结果 |
| Banner 展示回调 | `/ad/showBanner`，异步 | 6.1.14+ | `code=0` 展示成功，1 加载失败，2 当前无需展示 |
| Banner 关闭监听 | `/ad/closeEventObserver`，异步 | 6.1.25.0+ | `appKey`；`code=0` 表示底部 Banner 关闭 |
| Web 加载完成 | `/load/jsLoadProgress`，同步 | 6.1.19.0+ | `node:'gameLoadingCompleted'`、`tmp:毫秒时间戳` |
| Offline 加载完成 | `/gameAbility/gameLoadProgress`，同步 | 6.1.31.0+ | Offline Game 专有；`progress:100` |
| Activity 生命周期 | `/lifecycle/activity`，异步持续回调 | 5.1.49+ | `code=0` 后检查 `data.status`：2 恢复，3 暂停，4 停止，5 销毁；0/1 尚未进入可玩态 |
| 游戏暂停/继续 | `/game/registerCallback`，异步持续回调 | 6.1.31.0+ | `code=0`，`data.method` 为 `pause` 或 `continue` |
| 域内 KV | `/storage/get`、`put`、`remove`，同步 | 5.1.49+ | `key`；put 的 `value` 是字符串，返回旧值或 null，不能用真值判断写入成功 |
| 游戏记录 | `/gameStorage/readGameRecord`、`writeGameRecord`，异步 | 6.1.34.0+ | 写入 `{record:{mode,level,contentJson}}`；本地存档先保留，原生记录需版本校验、冲突策略 |
| 分享 | `/util/share` 同步，`/util/share2` 异步 | 5.1.49+ | `title/content`；拉起目标界面不等于对方收到或达成业务转化 |
| 分数/输赢 | `/gameAbility/reportGamePointsOrGameResult`，异步 | 位于 6.1.30.0+ 章节 | `resultType:1赢/2平/3败/0不上报`，`points>0` 有效；示例 status=0 与说明 1/2 冲突，需要真机核对 |
| PVP | `/pvp/*` | 6.1.30.0+ | 房间、用户、托管、结算协议；不提供完整实时同步方案 |

样例里存在 `"**/pvp/...**"` 等 Markdown 标记混入字符串、`status = 2` 赋值写法、中文弯引号以及不闭合的存档示例。协议以明确的调用协议字段为准，不能直接整段复制。未发布版本的宠物、DADA、PS 广告等不列为已可用能力。

## 广告回调语义

原生 `/ad/adBreak` 的 `code` 是事件类型，**不遵循普通接口的 code=0 成功约定**：

| code | 事件 | 业务处理 |
| --- | --- | --- |
| 1 | beforeAd | 暂停保持，停止请求等待计时，继续总看门狗 |
| 2 | afterAd | 广告离开；等待尾部结果，不等同于观看完成 |
| 3 | adBreakDone | 请求结束；只有此前有完成证据才可发奖 |
| 4 | beforeReward | 从 `data.adShowToken` 取展示凭证，玩家已主动请求时调用 showAdFn 一次 |
| 5 | adDismissed | 取消/未完成；不发奖，最终恢复游戏 |
| 6 | adViewed | 本次观看完成证据；等关闭或结束后返回一次可领奖结果 |

原文没有规定全部回调顺序和 code=3 是否携带 breakStatus。适配器采用保守策略：缺少 code=6 不发奖；终止后的迟到 code=6 忽略；afterAd 等待短暂尾部窗口后结束。窗口和总超时都是本地策略，必须按真机回调调整。看门狗只是防止永久卡死，不能凭超时认定广告播放成功，也不能代表奖励已记账。

SDK 方式依据上传壳 `h5sdk.adBreak` 的 `beforeReward(showAdFn)`、`adViewed`、`adDismissed`、`adBreakDone(info)`；原例只在 `info.breakStatus === 'viewed'` 时调用成功回调。适配器兼容 adViewed 完成证据，并把显式失败状态视为失败。不能把原生整数 code 与 SDK 字符串状态混用。

## 上传模板需要处理的问题

- Solitaire 包仅有外壳、说明和两个广告测试按钮，没有完整纸牌玩法、关卡或资源。它与 template 主要差别是 SDK game ID，不能据名称识别为不同完整游戏。
- SDK URL 为 `https://www.hippoobox.com/static/sdk/adsdk_1.8.0.0.js`。本次只分析了调用样例，未下载、执行或核验远端脚本；是否适用于目标容器由渠道确认。
- Solitaire 使用 `5027206`，template 使用 `5023178`；两份壳还内置 GA、AdSense client/slot/channel。它们是原样例配置，不是《琥珀商路》的分配结果。
- 原壳监听所有窗口消息，不校验 `origin/source`。内层 `postMessage('*')` 和 `window.parent.MIAD` 也意味着它实际依赖同源，并非可直接部署成跨域通信方案。
- 单个全局 `MIAD/MIAD_NEXT` 容易被下一次请求覆盖；先注册回调再发消息只能修正初始化顺序，不能解决旧回调误命中新请求的问题。推荐让父页每次请求持有独立 request ID 和闭包。
- `window.onload` 就调用加载完成，内层又可能重复上报；应由真实游戏就绪通知触发，并由唯一所有者去重。
- SDK 缺失时直接访问 `window.h5sdk` 会报错；原壳在 `a_bridge` 分支里还可能影响 iframe 加载。游戏加载应独立于广告脚本是否成功。
- 固定预留 50px 仅是壳的 CSS；不能认为所有原生 Banner 均为 50px。底部安全区、横竖屏、展示失败/关闭时空间释放需要按渠道实测。
- `index(2).html` 额外包含宠物、DADA 消息转发和可见性全局钩子，这些不是普通游戏广告的前置条件。
- 附件 readme 的“根目录 index.html 不要动”描述原模板用法，不是用户对本工程的限制。若必须保持渠道壳字节不变，应记录其局限，不能宣称已经修复消息隔离和超时关联。
