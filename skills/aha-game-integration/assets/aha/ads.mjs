/** 同一管理器只拥有一条广告通道。SDK 必须由外层完成初始化，不自动加载或切换渠道。 */
export function createAdManager({ transport = 'native', client, getSdk = () => globalThis.h5sdk,
  enabled = false, pause = () => {}, resume = () => {}, requestTimeoutMs = 8000,
  watchdogMs = 120000, closeGraceMs = 300, cooldownMs = 45000, now = Date.now } = {}) {
  let active = false;
  let lastInterstitial = -Infinity;

  function show(type, name) {
    const skip = status => Promise.resolve({ status, rewarded: false });
    if (!enabled) return skip('disabled');
    if (active) return skip('busy');
    if (type === 'next' && now() - lastInterstitial < cooldownMs) return skip('cooldown');
    if (!['native', 'sdk'].includes(transport)) return skip('invalid_transport');
    active = true;

    return new Promise(resolve => {
      let finished = false;
      let viewed = false;
      let dismissed = false;
      let tokenSent = false;
      let paused = false;
      let closeTimer;
      let requestTimer;
      let watchdog;

      // 每次请求独立闭包，任何迟到、重复回调都不能影响下一次请求或再次发奖。
      function finish(status, allowReward = false) {
        if (finished) return;
        finished = true;
        clearTimeout(requestTimer);
        clearTimeout(watchdog);
        clearTimeout(closeTimer);
        try { if (paused) resume(); } catch { /* 恢复函数异常不能挂住广告请求。 */ }
        active = false;
        resolve({ status, rewarded: type === 'reward' && allowReward && viewed && !dismissed });
      }

      function started() {
        clearTimeout(requestTimer);
        if (type === 'next') lastInterstitial = now();
      }

      function beforeReward(showAd) {
        if (finished || tokenSent) return;
        tokenSent = true;
        // showRewarded 只能由明确的“观看广告获取奖励”业务操作触发。
        try { showAd(); } catch { finish('error'); }
      }

      function afterAd() {
        if (finished || closeTimer) return;
        // 部分宿主只发送 afterAd；等待尾部事件后释放游戏，但没有完成证据仍不发奖。
        clearTimeout(requestTimer);
        closeTimer = setTimeout(() => finish(viewed && !dismissed ? 'viewed' : 'closed', true), closeGraceMs);
      }

      try {
        paused = true;
        pause();
        requestTimer = setTimeout(() => finish('timeout'), requestTimeoutMs);
        watchdog = setTimeout(() => finish('timeout'), watchdogMs);
        if (transport === 'native') {
          const result = client?.requestAd(type, name, requestTimeoutMs, event => {
            if (finished) return;
            if (event?.code === 1) started();
            else if (event?.code === 2) afterAd();
            else if (event?.code === 3) finish(viewed && !dismissed ? 'viewed' : dismissed ? 'dismissed' : 'done', true);
            else if (event?.code === 4 && type === 'reward') beforeReward(() => {
              const result = client.showReward(event.data?.adShowToken);
              if (result.status !== 'called') finish(result.status);
            });
            else if (event?.code === 5) { dismissed = true; afterAd(); }
            else if (event?.code === 6) viewed = true;
          });
          if (result?.status !== 'called') finish(result?.status || 'unavailable');
        } else {
          const sdk = getSdk();
          if (typeof sdk?.adBreak !== 'function') { finish('unavailable'); return; }
          sdk.adBreak({ type, name,
            beforeAd: () => { if (!finished) started(); },
            afterAd,
            beforeReward,
            adViewed: () => { if (!finished) viewed = true; },
            adDismissed: () => { if (!finished) { dismissed = true; afterAd(); } },
            adBreakDone: info => {
              if (finished) return;
              // 样例以 viewed 为完成依据；失败状态即使出现过 adViewed 也保守地不发奖。
              const status = info?.breakStatus || 'done';
              if (status === 'viewed') { viewed = true; if (type === 'next') lastInterstitial = now(); }
              finish(status, status === 'viewed' || status === 'done');
            },
          });
        }
      } catch { finish('error'); }
    });
  }

  return {
    showInterstitial(name) { return show('next', name); },
    showRewarded(name) { return show('reward', name); },
  };
}
