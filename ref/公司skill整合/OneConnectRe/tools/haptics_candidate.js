/* Candidate haptics preference. No effect is fired without an explicit call. */
(function () {
  'use strict';
  var key = 'oneconnect.haptics.candidate.v1', enabled = true;
  try {
    var saved = window.localStorage.getItem(key);
    if (saved === '0' || saved === '1') enabled = saved === '1';
  } catch (_) {}
  function supported() { return !!(window.navigator && typeof window.navigator.vibrate === 'function'); }
  function setEnabled(value) {
    if (typeof value !== 'boolean') return false;
    enabled = value;
    try { window.localStorage.setItem(key, value ? '1' : '0'); } catch (_) {}
    if (!value && supported()) try { window.navigator.vibrate(0); } catch (_) {}
    return true;
  }
  function pulse(milliseconds) {
    if (!enabled || !supported() || (window.document && window.document.hidden) ||
        !Number.isInteger(milliseconds) || milliseconds < 1 || milliseconds > 1000) return false;
    try { return window.navigator.vibrate(milliseconds) !== false; } catch (_) { return false; }
  }
  window.oneConnectHapticsCandidate = {supported:supported, enabled:function(){return enabled;}, setEnabled:setEnabled, pulse:pulse};
}());
