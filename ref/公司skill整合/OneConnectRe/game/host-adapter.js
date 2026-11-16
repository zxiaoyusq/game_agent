(function () {
  'use strict';
  var records = [], sequence = 0, wins = 0, lastInterstitialRequest = null, injectedAdProvider = null;
  function snapshot(value) {
    try { var encoded = JSON.stringify(value); return encoded === undefined ? {} : JSON.parse(encoded); }
    catch (_) { return { serializationError: true }; }
  }
  function emit(type, detail) {
    var event = { id: ++sequence, type: type, detail: snapshot(detail || {}), time: new Date().toISOString() };
    records.push(event);
    if (records.length > 1000) records.shift();
    var dispatched = snapshot(event);
    window.dispatchEvent && window.dispatchEvent(new CustomEvent('oneconnect:event', { detail: dispatched }));
    return dispatched;
  }
  function provider() {
    try { return window.top && window.top.h5_sdk; } catch (_) { return null; }
  }
  function setAdProvider(value) {
    if (value !== null && (!value || typeof value.showAd !== 'function')) throw new Error('invalid ad provider');
    injectedAdProvider = value;
  }
  function adProvider() { return injectedAdProvider || provider(); }
  function loadingCompleted() {
    var sdk = provider();
    // Nested wrappers can expose the loading callback on the immediate parent.
    // Keep the ad provider unchanged; this fallback is only for the loading signal.
    if (!sdk || typeof sdk.showGameLoadingCompleted !== 'function') {
      try {
        var parent = window.parent;
        if (parent && parent !== window && parent.h5_sdk && typeof parent.h5_sdk.showGameLoadingCompleted === 'function') sdk = parent.h5_sdk;
      } catch (_) {}
    }
    if (!sdk || typeof sdk.showGameLoadingCompleted !== 'function') { emit('host.unavailable', { method: 'showGameLoadingCompleted' }); return; }
    try { sdk.showGameLoadingCompleted(); emit('host.ready'); }
    catch (error) { emit('host.error', { method: 'showGameLoadingCompleted', message: String(error) }); }
  }
  function showAd(kind) {
    emit('ad.request', { kind: kind });
    var sdk = adProvider();
    if (!sdk || typeof sdk.showAd !== 'function') { emit('ad.unavailable', { kind: kind }); return Promise.resolve({ status: 'unavailable' }); }
    return new Promise(function(resolve){
      var settled=false,timer=null;
      function done(status,error){if(settled)return;settled=true;if(timer!==null&&window.clearTimeout)window.clearTimeout(timer);
        emit(status==='returned'?'ad.returned':'ad.error',status==='returned'?{kind:kind}:{kind:kind,message:String(error||status)});resolve({status:status});}
      // The bundled h5_sdk reports interstitial completion through callbacks.
      // A timeout prevents a broken provider from trapping the result screen.
      if(window.setTimeout)timer=window.setTimeout(function(){done('timeout','provider callback timeout');},180000);
      try{
        var value=sdk.showAd(kind,function(){done('returned');},function(error){done('error',error);});
        if(value&&typeof value.then==='function')Promise.resolve(value).then(function(){done('returned');},function(error){done('error',error);});
        else if(sdk===injectedAdProvider&&sdk.showAd.length<2)done('returned'); // Explicit local synchronous mock.
      }catch(error){done('error',error);}
    });
  }
  function showInterstitialFor(trigger) {
    if (trigger !== 'win' && trigger !== 'fail') throw Error('unsupported interstitial trigger');
    var config = window.oneConnectAdPolicy || {};
    var every = Number.isInteger(config.winEvery) && config.winEvery >= 1 ? config.winEvery : 1;
    var interval = Number.isFinite(config.minIntervalSeconds) && config.minIntervalSeconds >= 0 ? config.minIntervalSeconds : 0;
    var showFailure = typeof config.showOnFailure === 'boolean' ? config.showOnFailure : true;
    var reason = null;
    if (trigger === 'win' && ++wins % every !== 0) reason = 'win_frequency';
    if (trigger === 'fail' && !showFailure) reason = 'failure_disabled';
    var now = Date.now();
    if (!reason && lastInterstitialRequest !== null && now - lastInterstitialRequest < interval * 1000) reason = 'interval';
    if (reason) { emit('ad.policy_skip', { trigger: trigger, reason: reason }); return Promise.resolve({ status: 'skipped', reason: reason }); }
    var sdk = adProvider();
    if (sdk && typeof sdk.showAd === 'function') lastInterstitialRequest = now;
    return showAd('Interstitial');
  }
  function analytics(name, detail) {
    emit('analytics.' + name, detail);
    var mapped = { EVENT_LEVELSTART: 'game.level_start', EVENT_LEVELSUCCESS: 'game.level_win', EVENT_LEVELFAIL: 'game.level_fail' }[name];
    if (mapped) {
      var data = detail || {}, value = Number(data.levelName);
      var normalized = { level: Number.isFinite(value) && value > 0 ? value : null };
      if (data.totalScore !== undefined) normalized.score = data.totalScore;
      else if (name !== 'EVENT_LEVELSTART' && normalized.level !== null) {
        try {
          var runtime = window.cr_getC2Runtime && window.cr_getC2Runtime();
          var vars = runtime && runtime.all_global_vars;
          var level = vars && vars.find(function (v) { return v.name === 'level'; });
          var score = vars && vars.find(function (v) { return v.name === 'score'; });
          if (runtime && runtime.running_layout && runtime.running_layout.name === 'game' && level && level.data === normalized.level && score && Number.isFinite(score.data) && score.data >= 0) normalized.score = score.data;
        } catch (_) {}
      }
      if (data.reason !== undefined) normalized.reason = data.reason;
      emit(mapped, normalized);
    }
  }
  window.oneConnectHost = { setAdProvider: setAdProvider, analytics: analytics, loadingCompleted: loadingCompleted, showAd: showAd, showInterstitialFor: showInterstitialFor, emit: emit, events: function () { return snapshot(records); } };
}());
