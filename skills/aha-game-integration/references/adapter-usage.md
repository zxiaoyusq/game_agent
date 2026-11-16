# 适配代码使用说明

`assets/aha/` 是基于上传文档编写的参考实现，不是 AHA 官方 SDK。无第三方依赖，可复制到原生 Web 工程；Cocos Web 可按工程模块规则引入，并把暂停函数接到引擎层。Node 测试覆盖调用与回调，不证明当前渠道原生实现与文档完全一致。

## 文件边界

| 文件 | 职责 |
| --- | --- |
| `client.mjs` | 原生 Bridge、版本门槛、代理埋点、时长注册、加载完成、生命周期、Banner、广告协议 |
| `ads.mjs` | 一次广告请求的状态、两种传输、并发锁、超时、尾部回调、完成证据、冷却 |
| `pause.mjs` | 多个暂停原因的合并与恢复 |

没有自动加载远端 SDK、猜测账户、伪造广告完成、开启生产埋点或上传存档的逻辑。SDK 方式只调用已由渠道壳初始化好的 `h5sdk.adBreak`。埋点客户端当前仅实现原生代理接口；`athenaSend` 的自定义字段签名在附件中未给出，不做猜测实现。

## 原生接入骨架

以下需要替换的业务函数必须接到真实工程，不能原样粘贴后就宣称完成：

```javascript
import { createAhaClient } from './platform/aha/client.mjs';
import { createAdManager } from './platform/aha/ads.mjs';
import { createPauseController } from './platform/aha/pause.mjs';

// 通过项目配置注入，测试替身与生产配置分开；配置不全时保持关闭。
const config = {
  analyticsEnabled: false,
  adsEnabled: false,
  appKey: '',
  eventId: null,
  offline: false,
};
const platform = createAhaClient({
  enabled: config.analyticsEnabled || config.adsEnabled,
  appKey: config.appKey,
  eventId: config.eventId,
});
const gate = createPauseController({
  pause: () => pauseGameAndAudio(),
  resume: () => resumeGameAndAudioIfStillActive(),
});
const ads = createAdManager({
  enabled: config.adsEnabled,
  client: platform,
  pause: () => gate.set('ad', true),
  resume: () => gate.set('ad', false),
});

// 在已确认 Bridge 就绪时注册一次；页面卸载时 dispose，避免重入重复监听。
const subscription = platform.onLifecycle((source, paused) => gate.set(source, paused));
document.addEventListener('visibilitychange', () => gate.set('visibility', document.hidden));
gate.set('visibility', document.hidden);

// 首屏资源和操作可用时调用；不是“开始下载资源”时调用。
platform.loadingCompleted({ offline: config.offline });
if (config.analyticsEnabled) platform.track('game_ready', { game_slug: 'your-game' });

async function nextMatch() {
  // 同时锁住业务按钮；管理器的 busy 结果不能被第二次点击当成“现在就重开”。
  if (transitionInProgress) return;
  transitionInProgress = true;
  try {
    await ads.showInterstitial('result_play_again');
    startNextMatch(); // 失败、无广告和屏蔽均继续。
  } finally { transitionInProgress = false; }
}

async function requestCosmeticReward() {
  if (rewardInProgress) return;
  rewardInProgress = true;
  const requestId = crypto.randomUUID();
  const matchId = currentMatch.id;
  try {
    const result = await ads.showRewarded('cosmetic_unlock');
    // 真正记账仍在业务层：校验场景、使用 requestId 幂等持久化，成功后才显示到账。
    if (result.rewarded && currentMatch.id === matchId) {
      grantAndPersistRewardOnce(requestId);
    }
  } finally { rewardInProgress = false; }
}
```

以上 `transitionInProgress`、`rewardInProgress` 应在业务模块初始化为 false。平台调用的开关不等于游戏输入锁；暂停期间点击、键盘和 AI 都应检查统一的暂停状态。`subscription.dispose()` 仅屏蔽 JS 回调，上传文档未定义原生取消订阅协议。

`createAhaClient` 的 `version` 可作为已确认渠道版本的显式配置，默认从 headers 读取。未知版本返回 `unsupported`；不要为了通过测试而在生产虚报新版本。同步原生返回 `false` 或未知协议静默失败的实际语义仍需真机验证，`called` 不能当作统计到账。

## SDK 壳方式

在父页创建唯一的广告管理器：

```javascript
const ads = createAdManager({
  enabled: sdkReady && config.adsEnabled,
  transport: 'sdk',
  getSdk: () => window.h5sdk,
  pause: () => tellGameAdPaused(true),
  resume: () => tellGameAdPaused(false),
});
```

父页 `tellGameAdPaused` 和结果回传必须使用已校验的同源/显式跨域协议；子页把广告原因加入自己的暂停集合。通用消息通道未包含在本参考代码内。不要把一个 iframe 对另一个父域的任意访问当成已支持。

样例里 SDK 初始化后直接发送 `athenaSend('game_start')`，再请求 preroll。这个“game_start”属于原样例，不能同时当作业务新对局埋点；SDK 外层加载就绪也不能代替内层游戏 ready。

## 返回值与限制

- 广告返回 `{status, rewarded}`。只有 `rewarded === true` 进入奖励事务；普通插屏永远为 false。
- `disabled/unavailable/unsupported/configuration_required/shielded/shield_unknown/busy/cooldown/error/timeout` 都不是观看成功。
- `done/closed` 表示流程结束或广告关闭，不自动代表奖励成立；业务只看 `rewarded`。
- 适配器默认请求超时 8 秒、总看门狗 120 秒、关闭尾部等待 300 毫秒、插屏冷却 45 秒。这些是可调的本地兜底，不是 AHA 保证或正式运营策略。
- 单个管理器每次请求隔离；换局、换页面、跨刷新及已持久化奖励的去重由业务负责。不要为每次按钮点击新建管理器。
- Banner 仅提供展示与关闭通知；占位尺寸、失败后的布局和关闭状态由游戏负责。
- 生命周期初始状态可能在注册前已变化。真机若不回放当前状态，应在渠道确认后结合 `/session/env` 初始化暂停原因；本参考实现未自动推断。

## 本地验证

```bash
node --test skills/aha-game-integration/tests/*.test.mjs
```

集成到目标游戏后，还要跑工程测试、构建与浏览器验收，实际点击广告入口验证游戏输入、AI、音频、奖励记账和对局去重。接口测试不能替代这些业务验收。
