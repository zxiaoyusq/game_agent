(function () {
  'use strict';
  var installed = false, pending = false, epoch = 0, resetWaitClock = null;
  function runtimeAtClearedFirst() {
    var r = window.cr_getC2Runtime && window.cr_getC2Runtime();
    if (!r || !r.running_layout || r.running_layout.name !== 'game') return null;
    var level = r.all_global_vars.find(function (v) { return v.name === 'level'; });
    var tiles = r.types.t5 && r.types.t5.instances;
    var globals = r.types.t32 && r.types.t32.instances[0];
    return level && level.data === 1 && tiles && tiles.length === 0 && globals && globals.instance_vars[3] === 72 ? r : null;
  }
  function install() {
    if (installed) return;
    installed = true;
    if(typeof document!=='undefined'&&document.addEventListener)document.addEventListener('visibilitychange',function(){if(resetWaitClock)resetWaitClock();});
    window.addEventListener('oneconnect:event', function (e) {
      var type=e&&e.detail&&e.detail.type;
      if(type==='game.board_configured'||type==='game.round_ready'||type==='game.level_fail'||type==='screen.SCREEN_HOME'){epoch++;pending=false;resetWaitClock=null;return;}
      if (!e || !e.detail || e.detail.type !== 'screen.SCREEN_BONUS' || pending || !runtimeAtClearedFirst()) return;
      pending = true;var token=epoch;
      window.setTimeout(function () {
        if(token!==epoch)return;
        var r = runtimeAtClearedFirst();
        if (!r || !window.oneConnectProgress || window.oneConnectProgress.get() < 2 || typeof window.c2_callFunction !== 'function') { pending = false; return; }
        ['t35','t43','t41'].forEach(function (name) {
          var type = r.types[name];
          if (type && type.instances) type.instances.slice().forEach(function (inst) { r.DestroyInstance(inst); });
        });
        if (window.oneConnectHost) {
          var score=r.all_global_vars.find(function(v){return v.name==='score';}),detail={level:1};
          if(score&&Number.isFinite(score.data)&&score.data>=0)detail.score=score.data;
          window.oneConnectHost.emit('game.level_win', detail);
        }
        // Allow the final pair's stars to reach the HUD before the next board
        // clears them. A bounded wait keeps a broken visual effect non-blocking.
        var waited=0,last=Date.now();resetWaitClock=function(){last=null;};
        function advanceWhenReady(){
          if(token!==epoch)return;
          if(!runtimeAtClearedFirst()||typeof window.c2_callFunction!=='function'){pending=false;resetWaitClock=null;return;}
          var stars=window.oneConnectFlyStarCandidate,active=0;
          try{if(stars&&typeof stars.state==='function')active=stars.state().active;}catch(_){}
          var now=Date.now(),hidden=typeof document!=='undefined'&&document.hidden;
          if(!hidden&&last!==null)waited+=Math.max(0,now-last);last=hidden?null:now;
          if(Number.isInteger(active)&&active>0&&(hidden||waited<2500)){window.setTimeout(advanceWhenReady,hidden?250:50);return;}
          resetWaitClock=null;try{window.c2_callFunction('nextLevel');}finally{pending=false;}
        }
        advanceWhenReady();
      }, 0);
    });
  }
  window.oneConnectFirstTransition = { install: install };
}());
