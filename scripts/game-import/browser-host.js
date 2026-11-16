// 普通浏览器只提供失败兜底，不加载渠道广告或统计，不伪造观看完成和奖励。
(() => {
  const frame = document.getElementById('iframe');
  window.h5sdk = {
    gameLoadingCompleted() { document.documentElement.dataset.gameReady = 'true'; },
    adBreak(options) { queueMicrotask(() => options.adBreakDone?.({ breakStatus: 'unavailable' })); },
  };
  window.CrazyKnifesAhaHost = Object.freeze({ ready: true, mode: 'browser-preview' });
  window.addEventListener('message', (event) => {
    // 只处理本页所承载游戏的固定消息，拒绝其他页面或任意协议转发。
    if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
    if (event.data === 'gameLoadingCompleted') {
      window.h5sdk.gameLoadingCompleted();
      return;
    }
    if (!['next', 'reward'].includes(event.data)) return;
    const callbacks = window[event.data === 'reward' ? 'MIAD' : 'MIAD_NEXT'];
    window.h5sdk.adBreak({ type: event.data, adBreakDone() { callbacks?._failback?.('unavailable'); } });
  });
  // 监听先注册，再加载子页；所有游戏资源保持压缩包内的相对目录结构。
  frame.src = './game/index.html';
})();
