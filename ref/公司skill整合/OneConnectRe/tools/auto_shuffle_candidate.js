(function () {
  'use strict';
  var installed=false, pending=null, maxAttempts=8, roundEpoch=0, notice=null, noticeTimer=null, noticeCloseTimer=null;
  function variable(runtime,name){return runtime.all_global_vars.find(function(v){return v.name===name;});}
  function hideNotice(){if(typeof window.clearTimeout==='function'){if(noticeTimer!==null)window.clearTimeout(noticeTimer);if(noticeCloseTimer!==null)window.clearTimeout(noticeCloseTimer);}noticeTimer=null;noticeCloseTimer=null;if(notice){notice.hidden=true;if(window.oneConnectTutorialMotion)window.oneConnectTutorialMotion.destroy(notice);}}
  function clearPending(keepNotice){if(pending&&pending.timer!==undefined&&typeof window.clearTimeout==='function')window.clearTimeout(pending.timer);pending=null;if(!keepNotice)hideNotice();}
  function showNotice(){
    if(typeof document==='undefined'||!document.createElement||!document.body)return;
    if(!notice){notice=document.createElement('div');notice.setAttribute('role','status');notice.style.cssText='position:fixed;left:50%;top:45%;transform:translate(-50%,-50%);z-index:48;box-sizing:border-box;width:min(340px,85vw);padding:20px 24px;border:22px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% fill / 22px stretch;text-align:center;color:white;font:700 clamp(16px,4vw,22px) sans-serif;pointer-events:none';notice.textContent='No matches! Free shuffle';document.body.appendChild(notice);}hideNotice();notice.hidden=false;
    var motion=window.oneConnectTutorialMotion,quiet=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(motion){motion.open(notice);if(!quiet)noticeCloseTimer=window.setTimeout(function(){noticeCloseTimer=null;motion.close(notice,{durationMs:160},hideNotice);},1340);}
    noticeTimer=window.setTimeout(hideNotice,1500);
  }
  function clearStale(runtime){if(!pending)return;if(!runtime||pending.runtime!==runtime||!runtime.running_layout||runtime.running_layout.name!=='game'||!variable(runtime,'level')||variable(runtime,'level').data!==pending.level)clearPending();}
  function enabled(runtime){
    var level=variable(runtime,'level'),config=window.oneConnectLevels,rows=config&&config.levels;
    if(typeof window.c2_callFunction!=='function'||!level||!Array.isArray(rows))return false;
    var entry=rows.find(function(e){return e.level===level.data;});
    if(entry&&entry.autoShuffle==='free')return true;
    if(entry&&entry.autoShuffle!==undefined)return false;
    return !!(config.fallbackAutoShuffle==='free'&&(!entry||(!entry.board&&!entry.generator)));
  }
  function install(){
    if(installed)return;installed=true;
    var oldObject=cr.action.prototype.run_object,oldSystem=cr.action.prototype.run_system;
    ['pointerdown','touchstart','mousedown'].forEach(function(type){window.addEventListener(type,hideNotice,true);});
    cr.action.prototype.run_object=function(){
      var runtime=this.runtime;
      clearStale(runtime);
      if(this.sid===484278472184714 && !pending && enabled(runtime)){
        var stock=variable(runtime,'shuffle');
        if(stock && Number.isInteger(stock.data) && stock.data>=0){pending={runtime:runtime,level:variable(runtime,'level').data,epoch:roundEpoch,stock:stock.data,attempts:0,failed:false};var token=pending;pending.timer=window.setTimeout(function(){if(pending===token){clearPending();window.oneConnectHost.emit('game.auto_shuffle_expired',{level:token.level});}},5000);showNotice();window.oneConnectHost.emit('game.auto_shuffle_start',{level:variable(runtime,'level').data});}
      }
      if(pending && pending.runtime===runtime && (this.sid===987355312738297||this.sid===143347589055852)){
        var state=pending,stock=variable(runtime,'shuffle');
        if(++state.attempts>maxAttempts){
          if(!state.failed){state.failed=true;if(stock)stock.data=state.stock;window.oneConnectHost.emit('game.auto_shuffle_exhausted',{attempts:maxAttempts});window.setTimeout(function(){var level=variable(runtime,'level');if(roundEpoch!==state.epoch||!runtime.running_layout||runtime.running_layout.name!=='game'||!level||level.data!==state.level)return;var draw=variable(runtime,'isDraw');if(draw)draw.data=1;if(typeof window.c2_callFunction==='function')window.c2_callFunction('GameOver');},0);}
          if(pending===state)clearPending();
          return;
        }
        if(stock)stock.data=state.stock;
        try{var result=oldObject.apply(this,arguments);if(this.sid===987355312738297&&!state.failed)window.oneConnectHost.emit('game.auto_shuffle_complete',{level:state.level,attempts:state.attempts});return result;}finally{if(this.sid===987355312738297&&pending===state)clearPending(true);}
      }
      return oldObject.apply(this,arguments);
    };
    cr.action.prototype.run_system=function(){clearStale(this.runtime);if(pending && pending.runtime===this.runtime && (this.sid===965952694452064||this.sid===525411699780964))return;
      var hideNative=pending&&pending.runtime===this.runtime&&(this.sid===794890657400181||this.sid===917466126729791),r=this.runtime;
      var before=hideNative&&Array.isArray(r.createRow)?new Set(r.createRow):null,result=oldSystem.apply(this,arguments);
      if(before){r.createRow.forEach(function(instance){if(!before.has(instance)&&instance.type&&(instance.type.name==='t50'||instance.type.name==='t49')){instance.visible=false;r.redraw=true;}});}
      return result;};
    var oldCondition=cr.condition.prototype.run_system;
    cr.condition.prototype.run_system=function(){clearStale(this.runtime);if(pending && pending.runtime===this.runtime){if(this.sid===987481312341994)return false;if(this.sid===125602826208485)return true;}return oldCondition.apply(this,arguments)};
    var touch=window.cr&&cr.plugins_&&cr.plugins_.Touch&&cr.plugins_.Touch.prototype.cnds;
    if(touch&&typeof touch.OnTouchObject==='function'){
      var previousTouch=touch.OnTouchObject;
      touch.OnTouchObject=function(type){if(this.runtime)clearStale(this.runtime);var result=previousTouch.apply(this,arguments);return result&&pending&&pending.runtime===this.runtime&&type&&(type.name==='t5'||type.name==='t26')?false:result;};
    }
    window.addEventListener('oneconnect:event',function(e){var t=e.detail&&e.detail.type;if(t==='game.board_configured'||t==='game.round_ready'||t==='game.level_fail'||t==='game.level_win'){roundEpoch++;clearPending();}});
  }
  window.oneConnectAutoShuffle={install:install};
}());
