(function (window) {
  'use strict';
  var nativeStorage = null;
  try { nativeStorage = window.localStorage; } catch (_) {}
  var keys = ['tables', 'upgrades', 'strikers', 'stones', 'coins', 'tutorial', 'lastRewardTime'];
  var prefix = 'carrom-clash-master:v1:';
  var dirty = Object.create(null);
  var localActive = false;
  function isGameKey(key) { return keys.indexOf(key) !== -1; }
  function hasHostData() {
    try {
      var location = window.location;
      return new URLSearchParams(location.search || '').has('gameData') ||
        new URLSearchParams((location.hash || '').replace(/^#\??/, '')).has('gameData');
    } catch (_) { return true; }
  }
  function valid(value, fallback) {
    if (typeof fallback === 'number') {
      if (typeof value !== 'number' && !(typeof value === 'string' && value.trim() !== '')) return fallback;
      var number = Number(value);
      return Number.isFinite(number) && number >= 0 ? number : fallback;
    }
    return typeof value === typeof fallback ? value : fallback;
  }
  function preserveInvalid(key, raw) {
    if (!localActive || !isGameKey(key) || typeof raw !== 'string' || raw.length > 32768) return;
    try {
      var backupKey = prefix + 'invalid:' + key;
      if (nativeStorage.getItem(backupKey) === null) nativeStorage.setItem(backupKey, raw);
    } catch (_) {}
  }
  function recover(raw, fallback, key) {
    var parsed;
    try { parsed = JSON.parse(raw); } catch (_) { preserveInvalid(key, raw); return fallback; }
    var result;
    if (Array.isArray(fallback)) {
      result = Array.isArray(parsed) ? fallback.map(function (item, index) { return valid(parsed[index], item); }) : fallback;
    } else {
      result = parsed === null ? fallback : valid(parsed, fallback);
    }
    if (JSON.stringify(parsed) !== JSON.stringify(result)) preserveInvalid(key, raw);
    return result;
  }
  function install() {
    var storage = window.GameSnacks && window.GameSnacks.storage;
    if (!nativeStorage || !storage || storage.channel != null || hasHostData()) return false;
    var get = storage.getItem.bind(storage), set = storage.setItem.bind(storage);
    var remove = storage.removeItem.bind(storage), clear = storage.clear.bind(storage);
    storage.getItem = function (key) {
      if (!isGameKey(key) || dirty[key]) return get(key);
      try { var value = nativeStorage.getItem(prefix + key); return value === null ? get(key) : value; }
      catch (_) { return get(key); }
    };
    storage.setItem = function (key, value) {
      set(key, value);
      if (!isGameKey(key)) return;
      try { nativeStorage.setItem(prefix + key, String(value)); delete dirty[key]; }
      catch (_) { dirty[key] = true; }
    };
    storage.removeItem = function (key) {
      remove(key);
      if (!isGameKey(key)) return;
      try { nativeStorage.removeItem(prefix + key); delete dirty[key]; }
      catch (_) { dirty[key] = true; }
    };
    storage.clear = function () {
      clear();
      keys.forEach(function (key) {
        try { nativeStorage.removeItem(prefix + key); delete dirty[key]; }
        catch (_) { dirty[key] = true; }
      });
    };
    localActive = true;
    return true;
  }
  window.CarromLocalSave = { install: install, recover: recover };
})(window);
