/* Opt-in local simulation only. Never use as a real advertising provider. */
(function (root) {
  'use strict';
  function create(options) {
    options = options || {};
    var mode = options.mode, delay = options.delayMs === undefined ? 250 : options.delayMs;
    if (['reward', 'closed', 'cancelled', 'error'].indexOf(mode) === -1) throw Error('invalid simulation mode');
    if (!Number.isInteger(delay) || delay < 0 || delay > 60000) throw Error('invalid simulation delay');
    return {show: function (callbacks) {
      setTimeout(function () {
        if (mode === 'error') { callbacks.error(); return; }
        callbacks.shown();
        if (mode === 'reward') callbacks.earned({verified: true, simulated: true});
        if (mode === 'cancelled') callbacks.cancelled(); else callbacks.closed();
      }, delay);
    }};
  }
  root.oneConnectLocalRewardProvider = {create: create};
})(window);
