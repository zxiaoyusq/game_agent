/**
 * tools/tutorial_motion_adapter.js
 * 教程「提示卡」开合动效适配器（**独立新增文件；不改动任何既有游戏文件**）
 *
 * 加载：经典 <script> 直接可用（无 export/import）⇒ 挂 window.oneConnectTutorialMotion；兼容 CommonJS。
 *
 * 关键不变量：
 *  1) **保留并组合原有 transform**（如 translate(-50%,-50%)），不覆盖定位；不改 transform-origin；
 *  2) **关闭 / 取消 / 销毁 ⇒ 恢复原样**（transform、opacity 均还原接入前的值）；
 *  3) **不残留 WAAPI 填充效果**：finish 时先 `anim.cancel()` 再写最终样式（否则 `fill:'both'`
 *     会持续以更高优先级覆盖 inline 样式，尤其在 close/destroy 后重开时表现为"样式粘住"）；
 *  4) **动效进行中页面隐藏（document.hidden → true）⇒ 立即跳到终态**（取消动画、写终态、
 *     `done` 仍然**只调用一次**）；可见性监听懒安装、每元素至多一次收尾；
 *  5) 被取代/取消的动效不触发其 `done`（代际守卫 gen）；每次动效有墙钟兜底。
 */
(function (root, factory) {
  var api = factory(root);
  if (root) { root.oneConnectTutorialMotion = root.oneConnectTutorialMotion || api; }
  if (typeof module === 'object' && module && module.exports) { module.exports = api; }
})(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this), function (root) {
  'use strict';

  var DEFAULTS = {
    durationMs: 180, fromScale: 0.92, toScale: 1,
    easing: 'cubic-bezier(.2,.8,.2,1)', manageVisibility: false, fallbackExtraMs: 120
  };

  var states = typeof WeakMap === 'function' ? new WeakMap() : null;
  var pairs = [];                        // 无 WeakMap 兜底
  var pending = [];                      // 在途动效的 state 列表（供 visibilitychange 收尾）
  var visHooked = false;

  function newState() {
    return { anim: null, timer: null, closing: false, opened: false, settled: true, gen: 0,
             snapped: false, origTransform: '', origOpacity: '', pendingFinish: null };
  }
  function stateOf(el) {
    if (states) { var s1 = states.get(el); if (!s1) { s1 = newState(); states.set(el, s1); } return s1; }
    for (var i = 0; i < pairs.length; i++) { if (pairs[i][0] === el) return pairs[i][1]; }
    var s2 = newState(); pairs.push([el, s2]); return s2;
  }
  function stateOfOrNull(el) {
    if (states) return states.get(el) || null;
    for (var i = 0; i < pairs.length; i++) { if (pairs[i][0] === el) return pairs[i][1]; }
    return null;
  }
  function dropState(el) {
    if (states) { states['delete'](el); return; }
    for (var i = 0; i < pairs.length; i++) { if (pairs[i][0] === el) { pairs.splice(i, 1); return; } }
  }
  function win() {
    if (root && root.window) return root.window;
    if (typeof window !== 'undefined' && window) return window;
    return root || null;
  }
  function doc() {
    if (root && root.document) return root.document;
    if (typeof document !== 'undefined' && document) return document;
    var w = win(); return w && w.document ? w.document : null;
  }
  function reduced() {
    try {
      var w = win();
      var m = w && typeof w.matchMedia === 'function' ? w.matchMedia('(prefers-reduced-motion: reduce)') : null;
      return !!(m && m.matches);
    } catch (_) { return false; }
  }
  function pageHidden() { try { var d = doc(); return !!(d && d.hidden); } catch (_) { return false; } }

  /** 进行中页面隐藏 ⇒ 立即收尾（终态 + done 一次） */
  function hookVisibility() {
    if (visHooked) return;
    var d = doc();
    if (!d || typeof d.addEventListener !== 'function') return;
    visHooked = true;
    d.addEventListener('visibilitychange', function () {
      if (!pageHidden()) return;
      var snapshot = pending.slice();
      for (var i = 0; i < snapshot.length; i++) {
        var st = snapshot[i];
        if (st && st.pendingFinish) { var f = st.pendingFinish; st.pendingFinish = null; f(); }
      }
    });
  }
  function addPending(st) { if (pending.indexOf(st) < 0) pending.push(st); }
  function removePending(st) { var i = pending.indexOf(st); if (i >= 0) pending.splice(i, 1); st.pendingFinish = null; }

  function snapshot(el, st) {
    if (st.snapped || !el || !el.style) return;
    st.snapped = true;
    st.origTransform = el.style.transform || '';
    st.origOpacity = el.style.opacity || '';
  }
  function combine(prefix, scale) { return (prefix ? prefix + ' ' : '') + 'scale(' + scale + ')'; }
  function applyOpen(el, st, opts) { if (el && el.style) { snapshot(el, st); el.style.transform = combine(st.origTransform, opts.toScale); } }
  function restore(el, st) {
    if (!el || !el.style || !st.snapped) return;
    el.style.transform = st.origTransform;
    el.style.opacity = st.origOpacity;
  }
  function clearTimer(st) {
    if (st.timer !== null) { try { var w = win(); (w && w.clearTimeout ? w.clearTimeout : clearTimeout)(st.timer); } catch (_) {} st.timer = null; }
  }
  /** 取消动画并**解除填充效果**（关键：否则 fill:'both' 会继续覆盖 inline 样式） */
  function detachAnim(st) {
    var a = st.anim; st.anim = null;
    if (!a) return;
    try { if (typeof a.cancel === 'function') a.cancel(); } catch (_) {}
  }
  function setVisibility(el, opts, visible) {
    if (!opts.manageVisibility || !el) return;
    try {
      if (visible) { if ('hidden' in el) el.hidden = false; if (el.style && el.style.display === 'none') el.style.display = ''; }
      else if ('hidden' in el) { el.hidden = true; }
    } catch (_) {}
  }
  function canAnimate(el) { return !!(el && typeof el.animate === 'function' && !reduced() && !pageHidden()); }

  function run(el, opts, opening, done) {
    var st = stateOf(el);
    clearTimer(st); detachAnim(st);
    var gen = ++st.gen;
    st.settled = false;
    snapshot(el, st);
    var finish = function () {
      if (gen !== st.gen) return;
      if (st.settled) return;
      st.settled = true;                       // 先置位，避免 cancel 触发的 rejection 再次进入
      clearTimer(st);
      detachAnim(st);                          // ★ 解除 fill:'both' 残留
      removePending(st);
      st.closing = !opening;
      if (opening) { applyOpen(el, st, opts); } else { restore(el, st); }
      setVisibility(el, opts, opening);
      if (typeof done === 'function') { try { done(); } catch (_) {} }
    };
    if (!canAnimate(el)) { finish(); return true; }
    var frames = opening
      ? [{ transform: combine(st.origTransform, opts.fromScale), opacity: '0' },
         { transform: combine(st.origTransform, opts.toScale), opacity: '1' }]
      : [{ transform: combine(st.origTransform, opts.toScale), opacity: '1' },
         { transform: combine(st.origTransform, opts.fromScale), opacity: '0' }];
    try { st.anim = el.animate(frames, { duration: opts.durationMs, easing: opts.easing, fill: 'both' }); }
    catch (_) { st.anim = null; finish(); return true; }
    var p = st.anim && st.anim.finished;
    if (p && typeof p.then === 'function') { p.then(finish, finish); }
    var w = win();
    var setT = (w && w.setTimeout ? w.setTimeout : setTimeout);
    st.timer = setT(finish, opts.durationMs + opts.fallbackExtraMs);
    st.pendingFinish = finish;
    addPending(st);
    hookVisibility();                          // 懒安装可见性监听（进行中隐藏即收尾）
    return true;
  }
  function merge(options) {
    var o = {}, k;
    for (k in DEFAULTS) { if (Object.prototype.hasOwnProperty.call(DEFAULTS, k)) o[k] = DEFAULTS[k]; }
    if (options) { for (k in options) { if (Object.prototype.hasOwnProperty.call(options, k)) o[k] = options[k]; } }
    if (!(o.durationMs >= 0)) o.durationMs = DEFAULTS.durationMs;
    return o;
  }

  function open(el, options) {
    if (!el) return false;
    var opts = merge(options), st = stateOf(el);
    if (st.opened && !st.closing) { if (st.settled) applyOpen(el, st, opts); return false; }
    st.opened = true; st.closing = false;
    run(el, opts, true, null);
    return true;
  }
  function close(el, options, done) {
    var cb = typeof options === 'function' ? options : done;
    var opts = merge(typeof options === 'function' ? null : options);
    if (!el) { if (typeof cb === 'function') { try { cb(); } catch (_) {} } return false; }
    var st = stateOf(el);
    if (st.closing) return false;
    st.closing = true; st.opened = false;
    run(el, opts, false, cb);
    return true;
  }
  function cancel(el) {
    if (!el) return false;
    var st = stateOfOrNull(el); if (!st) return false;
    clearTimer(st); detachAnim(st); removePending(st);
    st.gen++; st.settled = true; st.closing = false;
    restore(el, st);
    return true;
  }
  function destroy(el) {
    if (!el) return false;
    var st = stateOfOrNull(el);
    if (st) { clearTimer(st); detachAnim(st); removePending(st); st.gen++; restore(el, st); dropState(el); }
    return true;
  }
  function isSupported(el) { return !!(el && typeof el.animate === 'function'); }
  function internals() { return { reduced: reduced, pageHidden: pageHidden, DEFAULTS: DEFAULTS, pendingCount: function () { return pending.length; }, hasVisibilityHook: function () { return visHooked; } }; }

  return { open: open, close: close, cancel: cancel, destroy: destroy, isSupported: isSupported, internals: internals };
});
