(function () {
  'use strict';
  var key = 'oneconnect.currentLevel.v1', memory = 1, installed = false;
  function valid(value) { return Number.isInteger(value) && value >= 1 && value <= 100000; }
  function get() {
    try {
      var raw = window.localStorage.getItem(key);
      if (typeof raw === 'string' && /^[1-9]\d*$/.test(raw)) {
        var parsed = Number(raw);
        if (valid(parsed)) memory = Math.max(memory, parsed);
      }
    } catch (_) {}
    return memory;
  }
  function recordWin() {
    var runtime = window.cr_getC2Runtime && window.cr_getC2Runtime();
    if (!runtime || !runtime.running_layout || runtime.running_layout.name !== 'game') return;
    var tiles = runtime.types && runtime.types.t5 && runtime.types.t5.instances;
    var state = runtime.types && runtime.types.t32 && runtime.types.t32.instances[0];
    var level = runtime.all_global_vars && runtime.all_global_vars.find(function (v) { return v.name === 'level'; });
    var rows = runtime.all_global_vars && runtime.all_global_vars.find(function (v) { return v.name === 'ROWS_COUNT'; });
    var cols = runtime.all_global_vars && runtime.all_global_vars.find(function (v) { return v.name === 'COLUMNS_COUNT'; });
    var total = !rows && !cols ? 72 : rows && cols && Number.isInteger(rows.data) && rows.data > 0 && Number.isInteger(cols.data) && cols.data > 0 ? rows.data * cols.data : null;
    if (!tiles || tiles.length !== 0 || !state || !state.instance_vars || state.instance_vars[3] !== total || !level || !valid(level.data) || level.data !== get() || level.data >= 100000) return;
    memory = level.data + 1;
    try { window.localStorage.setItem(key, String(memory)); }
    catch (_) {
      try { if (window.oneConnectHost) window.oneConnectHost.emit('candidate.progress_save_deferred', {level: memory}); } catch (_) {}
    }
  }
  function install() {
    if (installed) return;
    installed = true;
    window.addEventListener('oneconnect:event', function (event) {
      if (event && event.detail && event.detail.type === 'screen.SCREEN_BONUS') recordWin();
    });
  }
  // Reuse the same cleared-board checks when a confirmed native success
  // callback arrives but its bonus screen is delayed or missing.
  window.oneConnectProgress = { get: get, install: install, recordCleared: recordWin };
}());
