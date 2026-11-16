/** 按上传文档解析版本，兼容 V6.1.49.8_debug；不把版本代码当成版本名称。 */
export function versionAtLeast(actual, minimum) {
  const parse = value => String(value || '').match(/(?:^|V)(\d+\.\d+\.\d+(?:\.\d+)?)/i)?.[1].split('.').map(Number);
  const left = parse(actual);
  const right = parse(minimum);
  if (!left || !right) return false;
  for (let index = 0; index < 4; index++) {
    const difference = (left[index] || 0) - (right[index] || 0);
    if (difference) return difference > 0;
  }
  return true;
}

/** 默认关闭。called 仅表示调用未抛错，不代表原生支持该协议或服务器已收到。 */
export function createAhaClient({ enabled = false, appKey = '', eventId = null, version = '', getBridge = () => globalThis.bridgeCore } = {}) {
  let readySent = false;

  function access(minimum, asynchronous = false) {
    if (!enabled) return { status: 'disabled' };
    try {
      const bridge = getBridge();
      if (typeof bridge?.callBridgeSync !== 'function' || (asynchronous && typeof bridge.callBridge !== 'function')) return { status: 'unavailable' };
      // 每次重新探测，允许宿主延迟注入；不采集或记录 headers 中的设备标识。
      const actual = version || bridge.callBridgeSync('/api/headers', {})?.['X-VersionName'];
      if (!versionAtLeast(actual, minimum)) return { status: 'unsupported' };
      return { status: 'available', bridge };
    } catch { return { status: 'error' }; }
  }

  function invoke(path, payload, minimum, callback) {
    const state = access(minimum, !!callback);
    if (!state.bridge) return { status: state.status };
    try {
      const value = callback
        ? state.bridge.callBridge(path, payload, callback)
        : state.bridge.callBridgeSync(path, payload);
      return { status: 'called', value };
    } catch { return { status: 'error' }; }
  }

  function event(path, name, data, extra = {}) {
    if (!Number.isSafeInteger(eventId) || eventId <= 0 || typeof name !== 'string' || !name) return { status: 'configuration_required' };
    try {
      return invoke(path, { eventName: name, eventId, eventData: JSON.stringify(data), ...extra }, '6.1.2');
    } catch { return { status: 'invalid_data' }; }
  }

  return {
    track(name, data = {}) { return event('/event/proxySend', name, data); },
    registerPageDuration(name, data = {}) { return event('/event/regPageDurTime', name, data, { pickDatas: [1] }); },
    loadingCompleted({ offline = false } = {}) {
      if (readySent) return { status: 'duplicate' };
      const result = offline
        ? invoke('/gameAbility/gameLoadProgress', { progress: 100 }, '6.1.31.0')
        : invoke('/load/jsLoadProgress', { node: 'gameLoadingCompleted', tmp: Date.now() }, '6.1.19.0');
      if (result.status === 'called' && result.value !== false) readySent = true;
      return result;
    },
    /** 持续订阅不能包装成单次 Promise；原文无反注册协议，dispose 仅使回调失效。 */
    onLifecycle(onChange) {
      let active = true;
      const activity = invoke('/lifecycle/activity', {}, '5.1.49', result => {
        if (!active || result?.code !== 0) return;
        const status = result.data?.status;
        if (status === 2) onChange('activity', false);
        else if ([3, 4, 5].includes(status)) onChange('activity', true);
      });
      const game = invoke('/game/registerCallback', {}, '6.1.31.0', result => {
        if (!active || result?.code !== 0) return;
        const method = result.data?.method;
        if (['pause', 'continue'].includes(method)) onChange('game', method === 'pause');
      });
      return { activity: activity.status, game: game.status, dispose() { active = false; } };
    },
    showBanner(onResult = () => {}) {
      if (!appKey) return { status: 'configuration_required' };
      return invoke('/ad/showBanner', { appKey: String(appKey) }, '6.1.14', onResult);
    },
    onBannerClosed(onClose) {
      if (!appKey) return { status: 'configuration_required' };
      return invoke('/ad/closeEventObserver', { appKey: String(appKey) }, '6.1.25.0', result => {
        if (result?.code === 0) onClose();
      });
    },
    /** 广告流 code 不是通用成功码：1/2/3/4/5/6 分别是六类生命周期事件。 */
    requestAd(type, name, timeout, onEvent) {
      if (!['next', 'reward'].includes(type)) return { status: 'invalid_type' };
      if (!appKey) return { status: 'configuration_required' };
      const minimum = type === 'reward' ? '6.1.8' : '5.1.49';
      const state = access(minimum, true);
      if (!state.bridge) return { status: state.status };
      if (type === 'next' && access('6.1.12').status === 'available') {
        const shield = invoke('/ad/shouldShieldAdForUser', {}, '6.1.12');
        if (shield.status !== 'called' || typeof shield.value !== 'boolean') return { status: 'shield_unknown' };
        if (shield.value) return { status: 'shielded' };
      }
      return invoke('/ad/adBreak', { appKey: String(appKey), type, name, timeout }, minimum, onEvent);
    },
    showReward(adShowToken) {
      if (typeof adShowToken !== 'string' || !adShowToken) return { status: 'invalid_token' };
      // 此接口无响应，但调用形式仍为异步，不能换成 callBridgeSync。
      const state = access('6.1.8', true);
      if (!state.bridge) return { status: state.status };
      try {
        state.bridge.callBridge('/ad/showAdFn', { adShowToken });
        return { status: 'called' };
      } catch { return { status: 'error' }; }
    },
  };
}
