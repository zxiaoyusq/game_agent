import test from 'node:test';
import assert from 'node:assert/strict';
import { createAhaClient, versionAtLeast } from '../assets/aha/client.mjs';
import { createAdManager } from '../assets/aha/ads.mjs';
import { createPauseController } from '../assets/aha/pause.mjs';

/** 测试只用本地替身，不加载第三方脚本、不发送埋点、不请求真实广告。 */
function fixture({ version = 'V6.1.49.8_debug', shield = false, ...options } = {}) {
  const calls = [];
  const callbacks = new Map();
  const bridge = {
    callBridgeSync(path, data) {
      calls.push({ path, data });
      if (path === '/api/headers') return { 'X-VersionName': version };
      if (path === '/ad/shouldShieldAdForUser') return shield;
      return true;
    },
    callBridge(path, data, callback) {
      calls.push({ path, data });
      if (callback) callbacks.set(path, callback);
    },
  };
  const client = createAhaClient({ enabled: true, appKey: 'test-only', eventId: 1, getBridge: () => bridge, ...options });
  let paused = 0;
  let resumed = 0;
  const ads = createAdManager({ enabled: true, client, pause: () => paused++, resume: () => resumed++,
    requestTimeoutMs: 25, watchdogMs: 60, closeGraceMs: 5 });
  return { client, ads, calls, callbacks, bridge,
    emit(code, data = {}) { callbacks.get('/ad/adBreak')({ code, data }); },
    counts: () => ({ paused, resumed }),
  };
}

test('版本按数值逐段比较，未知版本不猜测支持', () => {
  assert.equal(versionAtLeast('V6.1.49.8_debug', '6.1.8'), true);
  assert.equal(versionAtLeast('6.1.9', '6.1.14'), false);
  assert.equal(versionAtLeast('6.1.31', '6.1.31.0'), true);
  assert.equal(versionAtLeast('', '6.1.2'), false);
});

test('埋点使用数字 eventId 和 JSON 字符串，时长走独立协议', () => {
  const f = fixture();
  assert.equal(f.client.track('match_start', { match_id: 'a', mode: 'quick' }).status, 'called');
  const event = f.calls.find(call => call.path === '/event/proxySend');
  assert.deepEqual(event.data, { eventName: 'match_start', eventId: 1, eventData: '{"match_id":"a","mode":"quick"}' });
  f.client.registerPageDuration('page_duration', { scene: 'game' });
  assert.deepEqual(f.calls.find(call => call.path === '/event/regPageDurTime').data.pickDatas, [1]);
  const circular = {}; circular.self = circular;
  assert.equal(f.client.track('bad', circular).status, 'invalid_data');
  assert.equal(fixture({ eventId: '1' }).client.track('bad').status, 'configuration_required');
});

test('默认关闭、普通浏览器、旧宿主和异常均不破坏调用方', async () => {
  assert.equal((await createAdManager().showRewarded('reward')).rewarded, false);
  assert.equal(createAhaClient({ eventId: 1 }).track('x').status, 'disabled');
  assert.equal(fixture({ getBridge: () => undefined }).client.track('x').status, 'unavailable');
  assert.equal(fixture({ getBridge: () => { throw Error('模拟宿主访问失败'); } }).client.track('x').status, 'error');
  const old = fixture({ version: '6.1.7' });
  assert.equal((await old.ads.showRewarded('reward')).status, 'unsupported');
  assert.equal(old.calls.some(call => call.path === '/ad/adBreak'), false);
});

test('延迟注入可以重试加载完成，成功调用后去重', () => {
  const f = fixture();
  let bridge;
  const client = createAhaClient({ enabled: true, getBridge: () => bridge });
  assert.equal(client.loadingCompleted().status, 'unavailable');
  bridge = f.bridge;
  assert.equal(client.loadingCompleted().status, 'called');
  assert.equal(client.loadingCompleted().status, 'duplicate');
  assert.equal(f.calls.filter(call => call.path === '/load/jsLoadProgress').length, 1);
  const offline = fixture();
  offline.client.loadingCompleted({ offline: true });
  assert.deepEqual(offline.calls.find(call => call.path === '/gameAbility/gameLoadProgress').data, { progress: 100 });
});

test('原生激励先使用 token 展示，完成并结束后才返回奖励；重复回调无效', async () => {
  const f = fixture();
  const result = f.ads.showRewarded('cosmetic');
  f.emit(4, { adShowToken: 'token-a' });
  f.emit(4, { adShowToken: 'token-a' });
  f.emit(1);
  f.emit(6);
  f.emit(6);
  f.emit(2);
  f.emit(3);
  assert.deepEqual(await result, { status: 'viewed', rewarded: true });
  f.emit(3);
  assert.equal(f.calls.filter(call => call.path === '/ad/showAdFn').length, 1);
  assert.deepEqual(f.calls.find(call => call.path === '/ad/showAdFn').data, { adShowToken: 'token-a' });
  assert.deepEqual(f.counts(), { paused: 1, resumed: 1 });
});

test('关闭广告、没有完成证据和乱序尾部事件均不冒领奖励', async () => {
  for (const codes of [[1, 2, 3], [1, 5, 3], [1, 6, 5, 3], [3, 6]]) {
    const f = fixture();
    const result = f.ads.showRewarded('reward');
    for (const code of codes) f.emit(code);
    assert.equal((await result).rewarded, false);
    assert.equal(f.counts().resumed, 1);
  }
});

test('错误 token、广告调用异常都返回失败并恢复', async () => {
  const f = fixture();
  const pending = f.ads.showRewarded('reward');
  f.emit(4, {});
  assert.equal((await pending).status, 'invalid_token');
  const g = fixture();
  g.bridge.callBridge = () => { throw Error('模拟调用失败'); };
  assert.equal((await g.ads.showInterstitial('next')).status, 'error');
  assert.equal(g.counts().resumed, 1);
});

test('无回调超时恢复，旧请求迟到回调不能奖励新请求', async () => {
  const f = fixture();
  const first = f.ads.showRewarded('first');
  const old = f.callbacks.get('/ad/adBreak');
  assert.equal((await first).status, 'timeout');
  const second = f.ads.showRewarded('second');
  old({ code: 6 }); old({ code: 3 });
  f.emit(3);
  assert.equal((await second).rewarded, false);
  assert.deepEqual(f.counts(), { paused: 2, resumed: 2 });
});

test('已开始但没有结束的广告有看门狗，只有 afterAd 时也能释放', async () => {
  const f = fixture();
  const pending = f.ads.showRewarded('reward');
  f.emit(1);
  assert.equal((await pending).status, 'timeout');
  const next = f.ads.showRewarded('reward');
  f.emit(1); f.emit(2);
  assert.deepEqual(await next, { status: 'closed', rewarded: false });
});

test('并发调用不覆盖活动广告，插屏实际展示后进入冷却', async () => {
  const f = fixture();
  const pending = f.ads.showInterstitial('next');
  assert.equal((await f.ads.showRewarded('reward')).status, 'busy');
  f.emit(1); f.emit(3);
  await pending;
  assert.equal((await f.ads.showInterstitial('next')).status, 'cooldown');
  assert.deepEqual(f.counts(), { paused: 1, resumed: 1 });
});

test('免广告只屏蔽插屏；未知屏蔽结果不绕过检查', async () => {
  for (const [shield, status] of [[true, 'shielded'], [null, 'shield_unknown']]) {
    const f = fixture({ shield });
    assert.equal((await f.ads.showInterstitial('next')).status, status);
    assert.equal(f.calls.some(call => call.path === '/ad/adBreak'), false);
    const reward = f.ads.showRewarded('reward');
    f.emit(3);
    await reward;
  }
});

test('SDK viewed 成功，dismissed 或失败不发奖，展示函数只调用一次', async () => {
  for (const status of ['viewed', 'dismissed', 'noAdPreloaded', 'frequencyCapped']) {
    let callbacks;
    let shown = 0;
    const manager = createAdManager({ enabled: true, transport: 'sdk', getSdk: () => ({ adBreak(value) { callbacks = value; } }) });
    const pending = manager.showRewarded('reward');
    callbacks.beforeReward(() => shown++);
    callbacks.beforeReward(() => shown++);
    callbacks.beforeAd();
    if (status === 'viewed') callbacks.adViewed();
    if (status === 'dismissed') callbacks.adDismissed();
    callbacks.adBreakDone({ breakStatus: status });
    assert.equal((await pending).rewarded, status === 'viewed');
    assert.equal(shown, 1);
  }
});

test('SDK 缺失或抛错时可继续游戏', async () => {
  for (const getSdk of [() => undefined, () => { throw Error('模拟 SDK 加载失败'); }]) {
    const manager = createAdManager({ enabled: true, transport: 'sdk', getSdk });
    assert.equal((await manager.showInterstitial('next')).rewarded, false);
  }
});

test('广告结束不解除手动暂停和宿主暂停，持续回调可停止接收', () => {
  let pauses = 0;
  let resumes = 0;
  const gate = createPauseController({ pause: () => pauses++, resume: () => resumes++ });
  const f = fixture();
  const subscription = f.client.onLifecycle((source, paused) => gate.set(source, paused));
  gate.set('modal', true);
  gate.set('ad', true);
  f.callbacks.get('/lifecycle/activity')({ code: 0, data: { status: 3 } });
  gate.set('ad', false);
  gate.set('modal', false);
  assert.equal(gate.paused, true);
  f.callbacks.get('/game/registerCallback')({ code: 0, data: { method: 'pause' } });
  f.callbacks.get('/lifecycle/activity')({ code: 0, data: { status: 2 } });
  assert.equal(resumes, 0);
  f.callbacks.get('/game/registerCallback')({ code: 0, data: { method: 'continue' } });
  assert.equal(gate.paused, false);
  assert.deepEqual({ pauses, resumes }, { pauses: 1, resumes: 1 });
  subscription.dispose();
  f.callbacks.get('/lifecycle/activity')({ code: 0, data: { status: 3 } });
  assert.equal(gate.paused, false);
});

test('Banner 展示与关闭是独立回调，使用文档协议和正确版本', () => {
  const f = fixture();
  let shown = false;
  let closed = false;
  f.client.showBanner(result => { shown = result.code === 0; });
  f.client.onBannerClosed(() => { closed = true; });
  f.callbacks.get('/ad/showBanner')({ code: 0 });
  f.callbacks.get('/ad/closeEventObserver')({ code: 0 });
  assert.equal(shown && closed, true);
  assert.equal(fixture({ version: '6.1.13' }).client.showBanner().status, 'unsupported');
});
