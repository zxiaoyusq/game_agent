/**
 * tools/tutorial_motion_integration.test.mjs
 * 独立测试（node:test + node:vm；无第三方依赖）
 * 运行：node --test tools/tutorial_motion_integration.test.mjs
 *
 * 本版针对**真实 game/tutorial-seventh.js 生命周期**设计（不是只测假元素）：
 *   真实事实（game/tutorial-seventh.js / 70293EC7DA1E）：
 *     · overlay = div#oc-seventh-guide（role=dialog, aria-modal=true）
 *     · 卡片 = overlay.firstElementChild（无 id/class）；按钮 #oc-seventh-continue
 *     · 打开：oneconnect:event ⇒ game.board_configured && detail.level===7 && !done() ⇒ active=true; overlay.style.display=''
 *     · 关闭 finish()：if(!active)return; active=false; **overlay.style.display='none'**; localStorage.setItem; oneConnectHost.emit
 *     · 暂停：all_global_vars 中 name==='pause'；每帧 frame() 判定
 *   ⇒ 本测试按上述时序驱动，验证"退出动画**真的能播**"（拦截写入 + 延后提交）且不改变语义。
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(HERE, 'tutorial_motion_integration.js'), 'utf8');

function load() {
  const sandbox = { console, setTimeout, clearTimeout };
  sandbox.document = { hidden: false };
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox, { filename: 'tutorial_motion_integration.js' });
  return { api: sandbox.oneConnectTutorialMotionIntegration, sandbox };
}

/** —— 真实语义的假 DOM：style 支持 setProperty 以便区分「真实值」与「读到的意图值」 —— */
function makeStyle(initial = {}) {
  const s = { _real: Object.assign({}, initial) };
  s.setProperty = (k, v) => { s._real[k] = v; };
  s.getPropertyValue = (k) => s._real[k];
  Object.defineProperty(s, 'display', { configurable: true, get: () => s._real.display, set: (v) => { s._real.display = v; } });
  return s;
}
function makeEl(tag, id) {
  const el = { tagName: tag, id, style: makeStyle({}), hidden: false, children: [], attributes: {}, _listeners: {} };
  el.setAttribute = (k, v) => { el.attributes[k] = v; };
  el.getAttribute = (k) => el.attributes[k];
  el.appendChild = (c) => { c.parentNode = el; el.children.push(c); return c; };
  Object.defineProperty(el, 'firstElementChild', { get: () => el.children[0] || null });
  el.addEventListener = (t, h) => { (el._listeners[t] = el._listeners[t] || []).push(h); };
  return el;
}

/** 构建与 tutorial-seventh.js 一致的最小真实场景（含生命周期与副作用计数） */
function makeSeventhScene({ paused = false, docHidden = false, doneKey = null } = {}) {
  const overlay = makeEl('div', 'oc-seventh-guide');
  const card = makeEl('div'); overlay.appendChild(card);
  const button = makeEl('button', 'oc-seventh-continue'); overlay.appendChild(button);

  const log = { persist: 0, emit: 0, openCalls: 0, closeCalls: 0, emitted: [] };
  const motion = {
    open(el, o) { log.openCalls++; log.lastOpenEl = el; },
    close(el, o, cb) { log.closeCalls++; log.lastCloseEl = el; log.closeCb = cb; },
  };
  const runtime = { running_layout: { name: 'game' }, all_global_vars: [{ name: 'pause', data: paused }] };
  const document = {
    hidden: docHidden,
    querySelector(sel) { return sel === '#oc-seventh-guide' ? overlay : null; },
    body: makeEl('body'), documentElement: null,
  };
  const env = { document, motion, runtime, MutationObserver: class { constructor(cb) { this.cb = cb; } observe() {} disconnect() { this.disconnected = true; } } };

  // —— 教程自身逻辑（与真实文件同序）——
  let active = false, installed = true;
  const done = () => { try { return window.localStorage.getItem('k') === 'done'; } catch (_) { return false; } };
  function finish() {
    if (!active) return;                 // 真实：重复关闭早退
    active = false;
    overlay.style.display = 'none';      // ★ 真实关闭写入（本层须拦截并延后提交）
    log.persist++;                       // 真实：localStorage.setItem
    log.emit++; log.emitted.push('finish');   // 真实：oneConnectHost.emit
  }
  function openTutorial() { if (done()) return; active = true; overlay.style.display = ''; }
  return { overlay, card, button, log, motion, runtime, document, env, finish, openTutorial, isActive: () => active };
}

function installScene(s, opts = {}) {
  const { api } = load();
  api.install(Object.assign({ env: s.env }, opts));
  return api;
}

// ---------- A. 加载与默认范围 ----------
test('A1 经典 script 加载：全局 API 就绪、源码无 ESM 语法', () => {
  assert.equal(/^\s*export\s/m.test(SRC), false);
  assert.equal(/^\s*import\s/m.test(SRC), false);
  const { api, sandbox } = load();
  for (const k of ['install', 'uninstall', 'diagnostics']) assert.equal(typeof api[k], 'function');
  assert.equal(sandbox.oneConnectTutorialMotionIntegration, api);
});

test('A2 启用有提示卡的教程', () => {
  const { api } = load();
  assert.equal(api.targets().filter((t) => t.enabled).map((t) => t.id).join(','), 'tutorial7,tutorial1,tutorial3,tutorial5,tutorial10');
});

// ---------- B. 真实生命周期：退出动画真的播 ----------
test('B1 真实 finish()：读值语义不变，但真实隐藏被延后到动效结束（退出动画可播）', () => {
  const s = makeSeventhScene();
  const api = installScene(s);
  s.openTutorial();                                   // game.board_configured ⇒ display=''
  assert.equal(s.log.openCalls, 1, '打开时播动效');

  s.finish();                                        // 真实关闭路径
  assert.equal(s.overlay.style.display, 'none', '读取应得到写入的意图值（语义不变）');
  assert.equal(s.overlay.style._real.display, '', '★ 真实 display 仍可见 ⇒ 退出动画能播');
  assert.equal(s.log.closeCalls, 1, '关闭动效已启动');
  assert.equal(s.log.persist, 1, '持久化未被延后（语义不变）');
  assert.equal(s.log.emit, 1, 'emit 未被延后（语义不变）');

  s.log.closeCb();                                   // 动效结束 ⇒ 提交真实隐藏
  assert.equal(s.overlay.style._real.display, 'none', '动效结束后真正提交隐藏');
  const d = api.diagnostics().targets.tutorial7;
  assert.equal(d.deferred, 1); assert.equal(d.committed, 1);
});

test('B2 暂停中：不做延后，立即提交（保持原时序）', () => {
  const s = makeSeventhScene({ paused: true });
  const api = installScene(s);
  s.openTutorial();
  assert.equal(s.log.openCalls, 0, '暂停中不播打开动效');
  s.finish();
  assert.equal(s.overlay.style._real.display, 'none', '暂停 ⇒ 立即提交');
  assert.equal(s.log.closeCalls, 0);
  assert.equal(api.diagnostics().targets.tutorial7.skipped, 'paused');
});

test('B3 页面隐藏：不做延后，立即提交', () => {
  const s = makeSeventhScene({ docHidden: true });
  installScene(s);
  s.openTutorial(); s.finish();
  assert.equal(s.overlay.style._real.display, 'none');
  assert.equal(s.log.closeCalls, 0);
});

test('B4 重复关闭幂等：真实 finish 早退 + 适配器 deferring 不叠加', () => {
  const s = makeSeventhScene();
  const api = installScene(s);
  s.openTutorial();
  s.finish(); s.finish(); s.finish();                // 连点/多次触发
  assert.equal(s.log.closeCalls, 1, '只启动一次退出动效');
  assert.equal(s.log.persist, 1, '持久化一次');
  assert.equal(s.log.emit, 1, 'emit 一次');
  assert.equal(api.diagnostics().targets.tutorial7.deferred, 1);
});

test('B5 非 game 布局：不播动效、立即提交（不改语义）', () => {
  const s = makeSeventhScene();
  s.env.runtime.running_layout.name = 'menu';
  const api = installScene(s);
  s.openTutorial(); s.finish();
  assert.equal(s.overlay.style._real.display, 'none');
  assert.equal(s.log.closeCalls, 0);
  assert.equal(api.diagnostics().targets.tutorial7.skipped, 'layout');
});

test('B6 状态事件语义：done() 已置位后不再打开；emit/持久化次数不受影响', () => {
  const s = makeSeventhScene();
  installScene(s);
  s.finish();                                        // active=false ⇒ 真实早退（无副作用）
  assert.equal(s.log.closeCalls, 0, '未激活时不触发关闭动效');
  assert.equal(s.log.persist, 0);
  s.openTutorial();
  assert.equal(s.log.openCalls, 1);
  s.finish();
  assert.equal(s.log.persist, 1);
});

test('B7 hidden 写入同样被拦截并延后提交', () => {
  const s = makeSeventhScene();
  const api = installScene(s);
  s.openTutorial();
  s.overlay.hidden = true;                           // 另一类隐藏写法
  assert.equal(s.overlay.hidden, true, '读取=意图值');
  assert.equal(s.overlay.style._real.display, '', '真实仍可见 ⇒ 动效可播');
  s.log.closeCb();
  assert.equal(s.overlay.style._real.display, 'none', '动效结束后提交');
  assert.equal(api.diagnostics().targets.tutorial7.deferred >= 1, true);
});

test('B8 uninstall 还原写入行为（不再拦截、不播动效）', () => {
  const s = makeSeventhScene();
  const api = installScene(s);
  s.openTutorial();
  api.uninstall();
  s.finish();
  assert.equal(s.overlay.style.display, 'none');
  assert.equal(s.overlay.style._real.display, 'none', '还原后立即生效');
  assert.equal(s.log.closeCalls, 0, '不再播动效');
});

test('B9 overlay 不存在：安全 no-op（不抛错、记录 overlay_not_found）', () => {
  const s = makeSeventhScene();
  s.env.document.querySelector = () => null;
  const api = installScene(s);
  s.finish();
  assert.equal(api.diagnostics().targets.tutorial7.found, false);
  assert.equal(api.diagnostics().targets.tutorial7.skipped, 'overlay_not_found');
});

test('B10 不触碰 pointer-events / 卡片之外的兄弟元素', () => {
  const s = makeSeventhScene();
  installScene(s);
  s.openTutorial(); s.finish();
  assert.equal(s.overlay.style.pointerEvents, undefined);
  assert.equal(s.button.style.transform, undefined, '按钮不被动画');
  assert.equal(s.card.style.pointerEvents, undefined);
});
