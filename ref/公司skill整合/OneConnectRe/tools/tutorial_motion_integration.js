/**
 * tools/tutorial_motion_integration.js
 * 教程提示卡开合动效**无冲突接入层**（独立新增；不改 game/、构建器、候选目录）
 *
 * V2 关键修正（针对真实生命周期）：
 *  真实教程（如 game/tutorial-seventh.js L5）关闭是 **直接写 `overlay.style.display='none'`**；
 *  MutationObserver 在写入**之后**才回调 ⇒ 子元素已不可见 ⇒ **退出动画无法播放**。
 *  ⇒ 本层改为对**显示写入做拦截**：
 *      · 写 `display='none'`（或 `hidden=true`）时，**不立即提交**，而是先播退出动效，
 *        动效结束后再**真正提交**隐藏；
 *      · 期间**读取**（`style.display` / `.hidden`）返回**写入的意图值** ⇒ 教程自身的判断、
 *        持久化与事件语义**完全不变**（仅"像素级隐藏时刻"延后 ≤ 一次动效时长）；
 *      · 暂停中 / 页面已隐藏 / 无动效能力 ⇒ **立即提交**（不做延后，保持原时序）；
 *      · `uninstall()` 还原原始写入行为。
 *  打开仍走"提交后触发"路径（显示写入或 MutationObserver 任一命中 ⇒ 播打开动效）。
 *
 * 安全边界：只操作**配置的元素**（overlay）与其**卡片子元素**；不触碰 pointer-events、DOM 顺序、
 *   高亮坐标（dim/挖洞在别处）、教程状态机（active/'done'/持久化/emit 均不由本层介入）。
 * 加载：经典 <script> 可用 ⇒ window.oneConnectTutorialMotionIntegration；兼容 module.exports。
 */
(function (root, factory) {
  var api = factory(root);
  if (root) { root.oneConnectTutorialMotionIntegration = root.oneConnectTutorialMotionIntegration || api; }
  if (typeof module === 'object' && module && module.exports) { module.exports = api; }
})(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this), function (root) {
  'use strict';

  var TARGETS = [
    { // 真实：game/tutorial-seventh.js —— overlay#oc-seventh-guide，卡片为 firstElementChild
      id: 'tutorial7', enabled: true,
      overlaySelectors: ['#oc-seventh-guide'],
      cardFrom: 'firstChild',
      cardSelectors: ['.oc-guide-label'],
      hideProps: ['display', 'hidden']
    },
    { id: 'tutorial1', enabled: true, overlaySelectors: ['#oc-tutorial'], cardFrom: 'selector', cardSelectors: ['#oc-tutorial-prompt'], hideProps: ['display', 'hidden'] },
    { id: 'tutorial2', enabled: false, overlaySelectors: ['#oc-tutorial'], cardFrom: 'firstChild', cardSelectors: ['.oc-guide-label'], hideProps: ['display', 'hidden'] },
    { id: 'tutorial3', enabled: true, overlaySelectors: ['#oc-third-guide'], cardFrom: 'selector', cardSelectors: ['#oc-third-guide .oc-guide-label'], hideProps: ['display', 'hidden'] },
    { id: 'tutorial5', enabled: true, overlaySelectors: ['#oc-fifth-guide'], cardFrom: 'selector', cardSelectors: ['#oc-fifth-guide .oc-guide-label'], hideProps: ['display', 'hidden'] },
    { id: 'tutorial10', enabled: true, overlaySelectors: ['#oc-tenth-guide'], cardFrom: 'selector', cardSelectors: ['#oc-tenth-guide .oc-guide-label'], hideProps: ['display', 'hidden'] }
  ];

  var state = { installed: false, observers: [], restores: [], records: {}, env: null, options: null };

  function env() { return state.env; }
  function doc() { var e = env(); return (e && e.document) || (root && root.document) || null; }
  function Motion() { var e = env(); if (e && e.motion) return e.motion; return (root && root.oneConnectTutorialMotion) || null; }
  function MO() { var e = env(); if (e && e.MutationObserver) return e.MutationObserver; return (root && root.MutationObserver) || null; }
  function runtime() { var e = env(); if (e && e.runtime) return e.runtime; try { return (root && typeof root.cr_getC2Runtime === 'function') ? root.cr_getC2Runtime() : null; } catch (_) { return null; } }
  function options() { return state.options || {}; }
  function isPaused() {
    if (typeof options().isPaused === 'function') { try { return !!options().isPaused(); } catch (_) { return true; } }
    try { var g = runtime() && runtime().all_global_vars.find(function (v) { return v.name === 'pause'; }); return !!(g && g.data); } catch (_) { return true; }
  }
  function inGameLayout() {
    if (typeof options().inGameLayout === 'function') { try { return !!options().inGameLayout(); } catch (_) { return false; } }
    try { var r = runtime(); return !!(r && r.running_layout && r.running_layout.name === 'game'); } catch (_) { return false; }
  }
  function pageHidden() { try { var d = doc(); return !!(d && d.hidden); } catch (_) { return false; } }
  function firstMatch(selectors) { var d = doc(); if (!d || !d.querySelector) return null; for (var i = 0; i < (selectors || []).length; i++) { try { var el = d.querySelector(selectors[i]); if (el) return el; } catch (_) {} } return null; }
  function rec(id) { if (!state.records[id]) state.records[id] = { found: false, card: null, lastAction: null, opens: 0, closes: 0, deferred: 0, committed: 0, skipped: null, lastVisible: null }; return state.records[id]; }

  function resolveCard(target, overlay) {
    if (target.cardFrom === 'firstChild' && overlay) {
      var c = overlay.firstElementChild || (overlay.children && overlay.children[0]) || null;
      if (c) return c;
    }
    return firstMatch(target.cardSelectors);
  }

  /** 拦截 overlay 的 display / hidden 写入：延迟提交隐藏，先播退出动效 */
  function interceptHide(target, overlay, getCard) {
    var r = rec(target.id);
    var deferring = false;
    var store = { realDisplay: overlay.style ? (overlay.style.display || '') : '', virtualDisplay: overlay.style ? (overlay.style.display || '') : '' };

    function motionOk() {
      var M = Motion();
      if (!M || typeof M.close !== 'function' || typeof M.open !== 'function') { r.skipped = 'motion_unavailable'; return false; }
      if (isPaused()) { r.skipped = 'paused'; return false; }
      if (pageHidden()) { r.skipped = 'page_hidden'; return false; }
      if (!inGameLayout()) { r.skipped = 'layout'; return false; }
      return true;
    }
    function commitHide() {
      store.realDisplay = 'none'; store.virtualDisplay = 'none';
      applyRealDisplay(overlay, 'none');
      r.committed++;
      deferring = false;
    }
    var deferGen = 0;                                     // 关闭代际：被 reopen 放弃的 close 回调不得再提交
    function onOpenWrite() {
      // ★ 关闭未完成时被重新打开 ⇒ 放弃该次延后（适配器 open 已取消其回调），并提交为可见，
      //    否则 deferring 会永久为 true ⇒ 之后所有关闭都被忽略、永远无法提交隐藏。
      if (deferring) { deferring = false; deferGen++; r.abandoned = (r.abandoned || 0) + 1; }
      var openVal = store.virtualDisplay === 'none' ? '' : store.virtualDisplay;
      store.realDisplay = openVal;                        // ★ 同步真实值镜像（否则"已隐藏短路"会永久生效）
      applyRealDisplay(overlay, openVal);
      if (!motionOk()) return;
      var card = getCard();
      if (!card) { r.skipped = 'card_not_found'; return; }
      try { Motion().open(card, options().motionOptions || {}); r.opens++; r.lastAction = 'open'; r.skipped = null; } catch (_) { r.skipped = 'open_threw'; }
    }
    function onHideWrite() {
      if (deferring) return;                                 // 关闭在途 ⇒ 忽略重复写入
      if (store.realDisplay === 'none') return;               // ★ 已隐藏（真实教程逐帧写 'none'）⇒ 不再启动新动画
      if (!motionOk()) { commitHide(); return; }              // 暂停/后台/无动效 ⇒ 立即提交（保持原时序）
      var card = getCard();
      if (!card) { r.skipped = 'card_not_found'; commitHide(); return; }
      deferring = true; r.deferred++;
      var gen = ++deferGen;
      try {
        Motion().close(card, options().motionOptions || {}, function () { if (gen === deferGen) commitHide(); });
        r.closes++; r.lastAction = 'close_deferred'; r.skipped = null;
      } catch (_) { r.skipped = 'close_threw'; if (gen === deferGen) commitHide(); }
    }

    // display 访问器（读=意图值；写=拦截）
    if (overlay.style && 'display' in overlay.style || (overlay.style && typeof overlay.style.setProperty === 'function')) {
      try {
        var proto = Object.getPrototypeOf(overlay.style);
        var desc = proto ? Object.getOwnPropertyDescriptor(proto, 'display') : null;
        var virtual0 = store.virtualDisplay;
        Object.defineProperty(overlay.style, 'display', {
          configurable: true,
          get: function () { return store.virtualDisplay; },
          set: function (v) {
            store.virtualDisplay = v;
            if (v === 'none') { onHideWrite(); return; }
            store.realDisplay = v;                          // ★ 同步镜像
            applyRealDisplay(overlay, v); onOpenWrite();
          }
        });
        state.restores.push(function () {
          try {
            // 还原为"直通访问器"：读=真实值，写=真实值（等价于未拦截时的行为）；
            // 不用 delete，避免在非 CSSStyleDeclaration 的 style 对象上丢失访问器。
            Object.defineProperty(overlay.style, 'display', {
              configurable: true,
              get: function () { return store.realDisplay; },
              set: function (v) { store.realDisplay = v; store.virtualDisplay = v; applyRealDisplay(overlay, v); }
            });
            if (desc && desc.set) { try { desc.set.call(overlay.style, store.realDisplay); } catch (_) {} }
          } catch (_) {}
        });
      } catch (_) { r.skipped = 'display_patch_failed'; }
    }
    // hidden 访问器（读=意图值；写=拦截）
    try {
      var realHidden = !!overlay.hidden, virtualHidden = realHidden;
      Object.defineProperty(overlay, 'hidden', {
        configurable: true,
        get: function () { return virtualHidden; },
        set: function (v) {
          virtualHidden = !!v;
          if (v) {
            if (deferring) return;
            if (store.realDisplay === 'none') { virtualHidden = true; return; }   // ★ 已隐藏 ⇒ 不重复启动
            if (!motionOk()) { realHidden = true; r.committed++; return; }
            var card2 = getCard();
            if (!card2) { realHidden = true; r.committed++; return; }
            deferring = true; r.deferred++;
            var g2 = ++deferGen;
            try { Motion().close(card2, options().motionOptions || {}, function () { if (g2 !== deferGen) return; realHidden = true; store.realDisplay = 'none'; applyRealDisplay(overlay, 'none'); r.committed++; deferring = false; }); r.closes++; r.lastAction = 'close_deferred'; }
            catch (_) { realHidden = true; r.committed++; deferring = false; }
          } else { realHidden = false; onOpenWrite(); }
        }
      });
      state.restores.push(function () { try { delete overlay.hidden; overlay.hidden = realHidden; } catch (_) {} });
    } catch (_) {}
    r.__real = store;
  }
  function applyRealDisplay(el, v) {
    if (!el || !el.style) return;
    try {
      if (typeof el.style.setProperty === 'function') { el.style.setProperty('display', v); return; }
      var proto = Object.getPrototypeOf(el.style);
      var desc = proto ? Object.getOwnPropertyDescriptor(proto, 'display') : null;
      if (desc && desc.set) { desc.set.call(el.style, v); return; }
      if (el.setAttribute) el.setAttribute('style', 'display:' + v);      // 最后兜底
    } catch (_) {}
  }

  function install(opts) {
    if (state.installed) return false;
    state.options = opts || {};
    state.env = state.options.env || null;
    var d = doc();
    var list = state.options.targets || TARGETS;
    var enabled = list.filter(function (t) { return t.enabled; });
    var Observer = MO();
    for (var i = 0; i < enabled.length; i++) {
      (function (target) {
        var overlay = firstMatch(target.overlaySelectors);
        var r = rec(target.id);
        if (!overlay) { r.found = false; r.skipped = 'overlay_not_found'; return; }
        r.found = true;
        var getCard = function () { var c = resolveCard(target, overlay); r.card = c; return c; };
        interceptHide(target, overlay, getCard);
        if (d && Observer && d.body) {
          var obs = new Observer(function () { var c = getCard(); if (c && r.lastAction !== 'close_deferred') { /* 打开由写入路径负责，这里只记录 */ } });
          try { obs.observe(overlay, { attributes: true, attributeFilter: ['style', 'hidden', 'class'], subtree: true }); state.observers.push(obs); } catch (_) {}
        }
        // 初次同步：默认**不**在安装时补播打开动效（避免与真实打开路径重复）；
        // 仅在显式 openOnInstall:true 且当前可见时播一次。
        if (state.options.openOnInstall === true) {
          var card0 = getCard();
          if (card0 && r.__real && r.__real.virtualDisplay !== 'none' && !isPaused() && inGameLayout()) {
            try { Motion().open(card0, state.options.motionOptions || {}); r.opens++; r.lastAction = 'open'; } catch (_) {}
          }
        }
      })(enabled[i]);
    }
    state.installed = true;
    return true;
  }
  function uninstall() {
    for (var i = 0; i < state.observers.length; i++) { try { state.observers[i].disconnect(); } catch (_) {} }
    state.observers = [];
    for (var j = 0; j < state.restores.length; j++) { try { state.restores[j](); } catch (_) {} }
    state.restores = [];
    state.installed = false;
    return true;
  }
  function sync() { return diagnostics(); }
  function diagnostics() {
    var out = {};
    for (var k in state.records) { if (Object.prototype.hasOwnProperty.call(state.records, k)) {
      var r = state.records[k];
      out[k] = { found: !!r.found, hasCard: !!r.card, lastAction: r.lastAction, opens: r.opens, closes: r.closes,
                 deferred: r.deferred, committed: r.committed, skipped: r.skipped || null,
                 realDisplay: r.__real ? r.__real.realDisplay : null, virtualDisplay: r.__real ? r.__real.virtualDisplay : null };
    } }
    return { installed: state.installed, observing: state.observers.length, targets: out };
  }
  function targets() { return TARGETS.map(function (t) { return { id: t.id, enabled: !!t.enabled }; }); }

  return { install: install, uninstall: uninstall, sync: sync, diagnostics: diagnostics, targets: targets, isPaused: isPaused, inGameLayout: inGameLayout };
});
