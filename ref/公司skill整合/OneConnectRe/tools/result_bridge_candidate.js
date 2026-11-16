/* Candidate win-result bridge: preserve the native reward before displaying
 * the panel, and defer the native completion callback until Next is chosen. */
(function () {
  'use strict';
  var installed=false, panel=null, pending=null, preflight=null, resetWaitClock=null;
  function runtime(){return window.cr_getC2Runtime && window.cr_getC2Runtime();}
  function variable(r,name){return r.all_global_vars && r.all_global_vars.find(function(v){return v.name===name;});}
  function goHome(){if(typeof window.c2_callFunction==='function')window.c2_callFunction('levelFailQuit');}
  function dismiss(action){if(window.oneConnectUiMotion)panel.hide(action);else{panel.hide();action();}}
  function failureAction(action){
    if(!pending||pending.kind!=='fail'||pending.adPending)return;
    var call=pending;call.adPending=true;
    function finish(){if(pending!==call)return;pending=null;dismiss(action);}
    try{
      var host=window.oneConnectHost;
      if(!host||typeof host.showInterstitialFor!=='function'){finish();return;}
      Promise.resolve(host.showInterstitialFor('fail')).then(finish,finish);
    }catch(error){console.warn('Failure interstitial unavailable',error);finish();}
  }
  function retryFromHome(){
    if(typeof window.c2_callFunction!=='function')return;
    goHome();
    var deadline=Date.now()+3000;
    function startWhenReady(){
      var r=runtime();
      if(r && r.running_layout && r.running_layout.name==='menu'){
        window.c2_callFunction('levelStart');
      }else if(Date.now()<deadline){requestAnimationFrame(startWhenReady);}
    }
    requestAnimationFrame(startWhenReady);
  }
  function install(){
    if(installed)return;
    var actions=window.cr && cr.plugins_ && cr.plugins_.Famobi && cr.plugins_.Famobi.prototype.acts;
    var proto=actions && Object.getPrototypeOf(actions), original=proto && proto.callback;
    if(typeof original!=='function' || !window.oneConnectResultPanelCandidate) return;
    panel=window.oneConnectResultPanelCandidate.create(document,{
      next:function(){if(!pending)return;var call=pending;pending=null;dismiss(function(){original.apply(call.receiver,call.args);});},
      home:function(){if(!pending)return;if(pending.kind==='fail'){failureAction(goHome);return;}pending=null;dismiss(goHome);},
      retry:function(){if(!pending)return;failureAction(retryFromHome);}
    });
    if(typeof document!=='undefined'&&document.addEventListener)document.addEventListener('visibilitychange',function(){if(resetWaitClock)resetWaitClock();if(preflight)preflight.last=null;});
    if(window.addEventListener)window.addEventListener('oneconnect:event',function(e){var type=e.detail&&e.detail.type;if(type==='screen.SCREEN_HOME'||type==='game.board_configured'||type==='game.round_ready'||type==='game.level_fail'){preflight=null;if(pending&&(pending.waiting||(pending.adPending&&type!=='game.level_fail'))){pending=null;resetWaitClock=null;panel.hide();}}});
    proto.callback=function(name){
      var r=runtime(), level=r && variable(r,'level'), score=r && variable(r,'score');
      var tiles=r && r.types && r.types.t5 && r.types.t5.instances;
      if(preflight&&name==='levelSuccess')return;
      if(preflight&&name==='levelFail')preflight=null;
      var eligible=name==='levelSuccess' && r && r.running_layout && r.running_layout.name==='game' &&
        level && Number.isInteger(level.data) && level.data>1 && tiles && tiles.length===0 &&
        window.oneConnectProgress && window.oneConnectProgress.get()>level.data;
      // The native bonus event advances progress independently of this callback.
      // If the callback arrives first, wait briefly rather than bypassing the panel.
      if(!eligible&&name==='levelSuccess'&&r&&r.running_layout&&r.running_layout.name==='game'&&level&&
         Number.isInteger(level.data)&&level.data>1&&tiles&&tiles.length===0&&window.oneConnectProgress&&
         window.oneConnectProgress.get()===level.data&&typeof window.setTimeout==='function'){
        if(preflight||pending)return;
        var wait={receiver:this,args:Array.prototype.slice.call(arguments),level:level.data,elapsed:0,last:Date.now()};preflight=wait;
        function awaitBonus(){if(preflight!==wait)return;var current=runtime(),currentLevel=current&&variable(current,'level');
          var currentTiles=current&&current.types&&current.types.t5&&current.types.t5.instances;
          if(!current||!current.running_layout||current.running_layout.name!=='game'||!currentLevel||currentLevel.data!==wait.level||!currentTiles||currentTiles.length!==0){preflight=null;return;}
          var now=Date.now(),hidden=typeof document!=='undefined'&&document.hidden;if(!hidden&&wait.last!==null)wait.elapsed+=Math.max(0,now-wait.last);wait.last=hidden?null:now;
          if(window.oneConnectProgress.get()>wait.level){preflight=null;proto.callback.apply(wait.receiver,wait.args);return;}
          if(!hidden&&wait.elapsed>=2500){
            try{if(typeof window.oneConnectProgress.recordCleared==='function')window.oneConnectProgress.recordCleared();}catch(error){console.warn('Cleared level progress unavailable',error);}
            preflight=null;
            if(window.oneConnectProgress.get()>wait.level)proto.callback.apply(wait.receiver,wait.args);
            else original.apply(wait.receiver,wait.args);
            return;
          }
          window.setTimeout(awaitBonus,hidden?250:50);
        }
        window.setTimeout(awaitBonus,50);return;
      }
      var failure=name==='levelFail' && r && r.running_layout && r.running_layout.name==='game' &&
        level && Number.isInteger(level.data) && level.data>0;
      if(!eligible&&!failure)return original.apply(this,arguments);
      if(pending)return;
      pending={receiver:this,args:Array.prototype.slice.call(arguments),kind:failure?'fail':'win'};
      var roundScore=window.oneConnectLevelScoreCandidate && score ?
        window.oneConnectLevelScoreCandidate.earned(level.data,score.data) : null;
      var call=pending, data={kind:failure?'fail':'win',level:level.data,score:score && score.data,levelScore:roundScore};
      function show(){if(pending!==call)return;call.waiting=false;resetWaitClock=null;try{panel.show(data);}catch(error){pending=null;original.apply(call.receiver,call.args);}}
      if(failure||!window.oneConnectFlyStarCandidate||typeof window.oneConnectFlyStarCandidate.state!=='function'||typeof window.setTimeout!=='function'){show();return;}
      var elapsed=0,last=Date.now();call.waiting=true;resetWaitClock=function(){last=null;};
      function check(){if(pending!==call)return;var current=runtime(),currentLevel=current&&variable(current,'level');if(!current||!current.running_layout||current.running_layout.name!=='game'||!currentLevel||currentLevel.data!==data.level){pending=null;resetWaitClock=null;return;}
        var count=0;try{count=window.oneConnectFlyStarCandidate.state().active;}catch(_){}
        var now=Date.now(),hidden=typeof document!=='undefined'&&document.hidden;if(!hidden&&last!==null)elapsed+=Math.max(0,now-last);last=hidden?null:now;
        if(Number.isInteger(count)&&count>0&&(hidden||elapsed<2500)){window.setTimeout(check,hidden?250:50);return;}show();}
      check();
    };
    installed=true;
  }
  window.oneConnectResultBridgeCandidate={install:install,handlesFailure:function(){var r=runtime(),level=r&&variable(r,'level');return !!(installed&&r&&r.running_layout&&r.running_layout.name==='game'&&level&&Number.isInteger(level.data)&&level.data>0);}};
})();
