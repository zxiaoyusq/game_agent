(function () {
 'use strict';
 // Local demonstration only: no SDK, durable reward ledger, or production placement.
 function create(options) {
  options = options || {};
  function runtime() { return window.cr_getC2Runtime && window.cr_getC2Runtime(); }
  return window.oneConnectRewardLifecycle.create({
   loadTimeoutMs: options.loadTimeoutMs,
   maxShowingMs: options.maxShowingMs,
   grant: function () {
    var r = runtime();
    if (!r || !r.running_layout || r.running_layout.name !== 'game' || !window.oneConnectHammer) return false;
    try {
     var count = window.oneConnectHammer.state().count;
     if (!Number.isInteger(count) || count < 0 || count >= 999) return false;
     window.localStorage.setItem('oneconnect.hammer.v1', String(count + 1));
     return window.localStorage.getItem('oneconnect.hammer.v1') === String(count + 1);
    } catch (_) { return false; }
   }
  });
 }
 window.oneConnectLocalHammerExample = { create: create };
}());
