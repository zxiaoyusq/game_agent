(function () {
  'use strict';
  var installed=false, pending=null, maxAttempts=8;
  function variable(runtime,name){return runtime.all_global_vars.find(function(v){return v.name===name;});}
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
    cr.action.prototype.run_object=function(){
      var runtime=this.runtime;
      if(this.sid===484278472184714 && !pending && enabled(runtime)){
        var stock=variable(runtime,'shuffle');
        if(stock && Number.isInteger(stock.data) && stock.data>=0){pending={runtime:runtime,level:variable(runtime,'level').data,stock:stock.data,attempts:0,failed:false};window.oneConnectHost.emit('game.auto_shuffle_start',{level:variable(runtime,'level').data});}
      }
      if(pending && pending.runtime===runtime && (this.sid===987355312738297||this.sid===143347589055852)){
        var state=pending,stock=variable(runtime,'shuffle');
        if(++state.attempts>maxAttempts){
          if(!state.failed){state.failed=true;if(stock)stock.data=state.stock;window.oneConnectHost.emit('game.auto_shuffle_exhausted',{attempts:maxAttempts});window.setTimeout(function(){var level=variable(runtime,'level');if(!runtime.running_layout||runtime.running_layout.name!=='game'||!level||level.data!==state.level)return;var draw=variable(runtime,'isDraw');if(draw)draw.data=1;if(typeof window.c2_callFunction==='function')window.c2_callFunction('GameOver');},0);}
          return;
        }
        if(stock)stock.data=state.stock;
        try{var result=oldObject.apply(this,arguments);if(this.sid===987355312738297&&!state.failed)window.oneConnectHost.emit('game.auto_shuffle_complete',{level:state.level,attempts:state.attempts});return result;}finally{if(this.sid===987355312738297)pending=null;}
      }
      return oldObject.apply(this,arguments);
    };
    cr.action.prototype.run_system=function(){if(pending && pending.runtime===this.runtime && this.sid===965952694452064)return;return oldSystem.apply(this,arguments)};
    var oldCondition=cr.condition.prototype.run_system;
    cr.condition.prototype.run_system=function(){if(pending && pending.runtime===this.runtime){if(this.sid===987481312341994)return false;if(this.sid===125602826208485)return true;}return oldCondition.apply(this,arguments)};
  }
  window.oneConnectAutoShuffle={install:install};
}());
