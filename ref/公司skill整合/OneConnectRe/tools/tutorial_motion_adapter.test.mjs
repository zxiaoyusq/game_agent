/**
 * tools/tutorial_motion_adapter.test.mjs
 * 独立测试（Node 内置 test runner + node:vm；无第三方依赖）
 * 运行：node --test tools/tutorial_motion_adapter.test.mjs
 *
 * A) 真实加载方式：经典 script 语义（vm，globalThis===window），源码不得含 ESM 语法
 * B) transform 保序与还原（含 translate / rotate 前缀）
 * C) 行为回归（幂等、单次 done、代际守卫、降级、兜底、边界）
 * D) 新增：
 *    D1 动效进行中 document.hidden 变 true ⇒ 立即到终态（open 场景）
 *    D2 动效进行中隐藏 ⇒ close 的 done 仍**只一次**，且不残留 fill
 *    D3 **fill:'both' 残留回归**：模拟"已完成动画持续覆盖 inline 样式" ⇒ 必须先 cancel 才能还原
 *    D4 destroy 后重开：不得被上一代 fill 粘住
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(HERE, 'tutorial_motion_adapter.js'), 'utf8');

/** 经典 script 语义加载；返回 api + 沙箱（含假 document，支持手动触发 visibilitychange） */
function loadClassic({ hidden = false, reduce = false } = {}) {
  const visHandlers = [];
  const sandbox = { console, setTimeout, clearTimeout };
  sandbox.document = {
    hidden,
    addEventListener(type, h) { if (type === 'visibilitychange') visHandlers.push(h); },
  };
  sandbox.matchMedia = () => ({ matches: reduce });
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox, { filename: 'tutorial_motion_adapter.js' });
  return { api: sandbox.oneConnectTutorialMotion, sandbox, fireVisibility: () => visHandlers.slice().forEach((h) => h()) };
}

function makeElement(initial = {}) {
  const calls = { animate: 0, cancel: 0 };
  let latest = null;
  const el = {
    style: Object.assign({}, initial.style),
    hidden: initial.hidden === true,
    calls,
    _resolve: () => latest && latest.resolve(),
    _reject: () => latest && latest.reject(new Error('cancelled')),
    animate(frames, opts) {
      calls.animate++;
      el.lastFrames = frames; el.lastOpts = opts;
      let resolve, reject;
      const finished = new Promise((res, rej) => { resolve = res; reject = rej; });
      latest = { resolve, reject };
      return { finished, cancel() { calls.cancel++; } };
    },
  };
  return el;
}

/**
 * 模拟浏览器 **fill:'both' 已完成动画持续覆盖 inline 样式**：
 *  - 动画未 cancel 时，对 el.style 的任何写入都会被"当前填充值"覆盖回去；
 *  - cancel() 后填充解除，写入才生效。
 * 以此验证适配器必须先 detachAnim(cancel) 再写最终样式。
 */
function makeFillingElement(initial = {}) {
  const calls = { animate: 0, cancel: 0 };
  let latest = null, fill = null;
  const raw = Object.assign({}, initial.style);
  const style = {};
  Object.defineProperty(style, 'transform', {
    get() { return fill ? fill.transform : raw.transform; },
    set(v) { raw.transform = v; if (fill) raw.transform = fill.transform; },   // 写入被填充覆盖
  });
  Object.defineProperty(style, 'opacity', {
    get() { return fill ? fill.opacity : raw.opacity; },
    set(v) { raw.opacity = v; if (fill) raw.opacity = fill.opacity; },
  });
  const el = {
    style, hidden: initial.hidden === true, calls, _raw: raw, _fill: () => fill,
    _resolve: () => { if (latest) { fill = el.lastFrames[el.lastFrames.length - 1]; latest.resolve(); } },
    _reject: () => latest && latest.reject(new Error('cancelled')),
    animate(frames, opts) {
      calls.animate++;
      el.lastFrames = frames; el.lastOpts = opts;
      let resolve, reject;
      const finished = new Promise((res, rej) => { resolve = res; reject = rej; });
      latest = { resolve, reject };
      return { finished, cancel() { calls.cancel++; fill = null; } };
    },
  };
  return el;
}
const tick = (ms = 0) => new Promise((r) => setTimeout(r, ms));

// ---------- A ----------
test('A1 经典 script 加载：全局 API 就绪，源码无 export/import', () => {
  assert.equal(/^\s*export\s/m.test(SRC), false);
  assert.equal(/^\s*import\s/m.test(SRC), false);
  const { api, sandbox } = loadClassic();
  assert.equal(typeof api, 'object');
  for (const k of ['open', 'close', 'cancel', 'destroy', 'isSupported']) assert.equal(typeof api[k], 'function');
  assert.equal(sandbox.oneConnectTutorialMotion, api);
});

test('A2 加载后可驱动（reduced ⇒ 终态、保留 translate、关闭还原）', () => {
  const { api } = loadClassic({ reduce: true });
  const el = { style: { transform: 'translate(-50%, -50%)' }, hidden: false };
  api.open(el);
  assert.equal(el.style.transform, 'translate(-50%, -50%) scale(1)');
  let done = 0; api.close(el, {}, () => { done++; });
  assert.equal(done, 1);
  assert.equal(el.style.transform, 'translate(-50%, -50%)');
});

// ---------- B ----------
test('B1 无 WAAPI：组合「原 transform + scale」', () => {
  const { api } = loadClassic();
  const el = { style: { transform: 'translate(-50%, -50%)' }, hidden: false };
  api.open(el);
  assert.equal(el.style.transform, 'translate(-50%, -50%) scale(1)');
});

test('B2 WAAPI：两个关键帧都带原 transform 前缀', async () => {
  const { api } = loadClassic();
  const el = makeElement({ style: { transform: 'translate(-50%, -50%) rotate(2deg)' } });
  api.open(el);
  assert.equal(el.lastFrames[0].transform, 'translate(-50%, -50%) rotate(2deg) scale(0.92)');
  assert.equal(el.lastFrames[1].transform, 'translate(-50%, -50%) rotate(2deg) scale(1)');
  el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'translate(-50%, -50%) rotate(2deg) scale(1)');
});

test('B3 close 恢复原样（transform 与 opacity）', async () => {
  const { api } = loadClassic();
  const el = makeElement({ style: { transform: 'translate(-50%,-50%)', opacity: '0.8' } });
  api.open(el); await tick(1);
  let done = 0; api.close(el, {}, () => { done++; });
  el._resolve(); await tick(5);
  assert.equal(done, 1);
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
  assert.equal(el.style.opacity, '0.8');
});

test('B4 reduced：保序 + 还原', () => {
  const { api } = loadClassic({ reduce: true });
  const el = { style: { transform: 'translate(-50%,-50%)' }, hidden: false };
  api.open(el);
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)');
  api.close(el, {}, () => {});
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
});

test('B5 cancel / destroy 恢复原样', () => {
  const { api } = loadClassic();
  const el = { style: { transform: 'translate(-50%,-50%)' }, hidden: false };
  api.open(el); api.cancel(el);
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
  api.open(el); api.destroy(el);
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
});

test('B6 无原 transform：行为不变', () => {
  const { api } = loadClassic();
  const el = { style: {}, hidden: false };
  api.open(el);
  assert.equal(el.style.transform, 'scale(1)');
});

// ---------- C ----------
test('C1 open：animate 一次、finished 后终态', async () => {
  const { api } = loadClassic();
  const el = makeElement();
  assert.equal(api.open(el), true);
  assert.equal(el.calls.animate, 1);
  assert.equal(el.lastOpts.duration, 180);
  el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'scale(1)');
});

test('C2 open 重复幂等（在途不重启）', () => {
  const { api } = loadClassic();
  const el = makeElement();
  assert.equal(api.open(el), true);
  assert.equal(api.open(el), false);
  assert.equal(el.calls.animate, 1);
});

test('C3 close done 恰好一次；重复 close 忽略', async () => {
  const { api } = loadClassic();
  const el = makeElement();
  let done = 0;
  api.open(el); await tick(1);
  assert.equal(api.close(el, {}, () => { done++; }), true);
  assert.equal(api.close(el, {}, () => { done++; }), false);
  el._resolve(); await tick(5);
  assert.equal(done, 1);
});

test('C4 close 中途 open：旧 done 不触发', async () => {
  const { api } = loadClassic();
  const el = makeElement();
  let stale = 0;
  api.open(el); await tick(1);
  api.close(el, {}, () => { stale++; });
  assert.equal(api.open(el), true);
  el._reject(); await tick(5);
  assert.equal(stale, 0);
});

test('C5 起始即隐藏 ⇒ 不播动效', () => {
  const { api } = loadClassic({ hidden: true });
  const el = makeElement();
  api.open(el);
  assert.equal(el.calls.animate, 0);
  let done = 0; api.close(el, {}, () => { done++; });
  assert.equal(done, 1);
});

test('C6 finished 永不 settle ⇒ 墙钟兜底收尾一次', async () => {
  const { api } = loadClassic();
  const el = makeElement();
  let done = 0;
  api.close(el, { durationMs: 5 }, () => { done++; });
  await tick(200);
  assert.equal(done, 1);
});

test('C7 manageVisibility=true 才切换 hidden', () => {
  const { api } = loadClassic();
  const el = { style: {}, hidden: true };
  api.open(el, { manageVisibility: true });
  assert.equal(el.hidden, false);
  api.close(el, { manageVisibility: true });
  assert.equal(el.hidden, true);
});

test('C8 空输入安全', () => {
  const { api } = loadClassic();
  assert.equal(api.open(null), false);
  let done = 0;
  assert.equal(api.close(null, {}, () => { done++; }), false);
  assert.equal(done, 1);
  assert.equal(api.isSupported(null), false);
});

test('C9 不触碰 pointer-events / 兄弟节点 / transform-origin', () => {
  const { api } = loadClassic();
  const el = { style: { transform: 'translate(-50%,-50%)' }, hidden: false };
  const sibling = { style: {} };
  api.open(el);
  assert.equal(el.style.pointerEvents, undefined);
  assert.equal(el.style.transformOrigin, undefined);
  assert.equal(sibling.style.transform, undefined);
});

// ---------- D. 新风险回归 ----------
test('D1 动效进行中页面隐藏（open 在途）⇒ 立即到终态、无半缩放', async () => {
  const { api, sandbox, fireVisibility } = loadClassic();
  const el = makeElement({ style: { transform: 'translate(-50%,-50%)' } });
  api.open(el);
  assert.equal(el.calls.animate, 1);
  assert.equal(api.internals().pendingCount(), 1, '在途应有 1 个待收尾');
  sandbox.document.hidden = true;
  fireVisibility();                                   // 模拟浏览器 visibilitychange
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)', '跳到终态（打开态）');
  assert.ok(el.calls.cancel >= 1, '必须先取消动画以解除 fill');
  assert.equal(api.internals().pendingCount(), 0, '待收尾已清空');
  el._resolve(); await tick(5);                       // 晚到的 finished 不得再改变状态
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)');
});

test('D2 动效进行中隐藏 ⇒ close 的 done 仍只一次，且无 fill 残留', async () => {
  const { api, sandbox, fireVisibility } = loadClassic();
  const el = makeElement({ style: { transform: 'translate(-50%,-50%)', opacity: '1' } });
  let done = 0;
  api.close(el, {}, () => { done++; });
  sandbox.document.hidden = true; fireVisibility();
  assert.equal(done, 1, '收尾触发一次 done');
  assert.equal(el.style.transform, 'translate(-50%,-50%)', '恢复原样');
  assert.equal(el.style.opacity, '1', 'opacity 恢复原样');
  el._resolve(); await tick(5); fireVisibility();
  assert.equal(done, 1, '既不会重复 done，也不因二次 visibilitychange 再收尾');
});

test('D3 fill 残留回归：已完成 fill 不得粘住样式（close/destroy）', async () => {
  const { api } = loadClassic();
  const el = makeFillingElement({ style: { transform: 'translate(-50%,-50%)', opacity: '1' } });
  api.open(el);
  el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)', 'open 完成后应为打开终态');

  api.close(el, {}, () => {});
  el._resolve(); await tick(5);
  assert.ok(el.calls.cancel >= 2, '每次 finish 都要 cancel 以解除 fill');
  assert.equal(el._fill(), null, '填充已解除');
  assert.equal(el.style.transform, 'translate(-50%,-50%)', 'close 后恢复原样（未被 fill 覆盖）');
  assert.equal(el.style.opacity, '1', 'opacity 恢复原样');

  api.open(el); el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)', '重开正常');

  api.destroy(el);
  assert.equal(el.style.transform, 'translate(-50%,-50%)', 'destroy 后恢复原样');
});

test('D4 destroy 后重开不被上一代 fill 粘住', async () => {
  const { api } = loadClassic();
  const el = makeFillingElement({ style: { transform: 'translate(-50%,-50%)' } });
  api.open(el); el._resolve(); await tick(5);
  api.destroy(el);
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
  api.open(el);                                    // 同元素再次使用
  el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'translate(-50%,-50%) scale(1)');
  api.close(el, {}, () => {});
  el._resolve(); await tick(5);
  assert.equal(el.style.transform, 'translate(-50%,-50%)');
});
