/* Confine original fall/move destinations to fully visible board cells. */
(function(){'use strict';
 var installed=false,active=null,targets={155796769104064:[0,'x'],491047488641600:[7,'x'],657297107410907:[1,'y'],422821596409828:[8,'y']};
 // Native fall/move overrides its target and loop start with the full array
 // edges. Replace both with visible edges on the live local-variable stack.
 var edges={922153812375164:[783261599223611,'minY'],691686252704739:[453172112289854,'maxY'],421370285882167:[783261599223611,'maxY'],416010416102780:[453172112289854,'minY'],506470056427101:[621443846527208,'minX'],256199955986944:[445808041118853,'maxX'],919370349324370:[621443846527208,'maxX'],219294900490487:[445808041118853,'minX']};
 function value(runtime,name){var v=runtime.all_global_vars&&runtime.all_global_vars.find(function(x){return x.name===name;});return v&&v.data;}
 function permitted(runtime,definition){
  if(!runtime||!runtime.running_layout||runtime.running_layout.name!=='game')return {passthrough:true};
  var rows=value(runtime,'ROWS_COUNT'),cols=value(runtime,'COLUMNS_COUNT'),size=value(runtime,'ITEM_SIZE'),spacing=value(runtime,'ITEM_SPACING');
  var board=runtime.types&&runtime.types.t0&&runtime.types.t0.instances[0],tiles=runtime.types&&runtime.types.t5&&runtime.types.t5.instances;
  var globalsType=runtime.types&&runtime.types.t32,selected=globalsType&&typeof globalsType.getCurrentSol==='function'&&globalsType.getCurrentSol().getObjects();
  var globals=selected?(selected.length===1?selected[0]:null):(globalsType&&globalsType.instances.length===1?globalsType.instances[0]:null),clip=window.oneConnectVisibleGravityBounds;
  if(!Number.isInteger(rows)||!Number.isInteger(cols)||!Number.isFinite(size)||!Number.isFinite(spacing)||!board||!board.arr||!Array.isArray(tiles)||!globals||!globals.instance_vars||!clip)return false;
  var needed=definition[1]==='x'?[783261599223611,453172112289854]:[621443846527208,445808041118853],locals=runtime.all_local_vars||[];
  if(!needed.every(function(sid){var v=locals.find(function(item){return item.sid===sid;});return v&&typeof v.setValue==='function';}))return false;
  var live=tiles.filter(function(t){var v=t.instance_vars,x=v&&v[2],y=v&&v[1];return Number.isInteger(x)&&Number.isInteger(y)&&board.arr[x]&&board.arr[x][y]&&board.arr[x][y][0]===t.uid;});
  if(!live.length)return false;
  var b=clip.clip(runtime,{top:0,left:0,rows:cols,cols:rows},live,rows,cols,size+spacing),target=globals.instance_vars[definition[0]];
  if(!b||!Number.isInteger(target))return false;
  var limits={minX:cols-(b.top+b.rows-1),maxX:cols-b.top,minY:b.left+1,maxY:b.left+b.cols};
  return (definition[1]==='x'?target>=limits.minX&&target<=limits.maxX:target>=limits.minY&&target<=limits.maxY)?limits:false;
 }
 function install(){if(installed)return;var p=window.cr&&cr.action&&cr.action.prototype;if(!p||typeof p.run_object!=='function')return;var old=p.run_object;
  var system=p.run_system;if(typeof system!=='function')return;
  p.run_system=function(){var result=system.apply(this,arguments),edge=edges[this.sid];if(edge&&active&&active.runtime===this.runtime&&active.limits&&!active.limits.passthrough){var vars=this.runtime.all_local_vars||[],v=vars.find(function(item){return item.sid===edge[0];});if(v&&typeof v.setValue==='function')v.setValue(active.limits[edge[1]]);}return result;};
  p.run_object=function(){var definition=targets[this.sid],allow=true;if(definition){try{allow=permitted(this.runtime,definition);}catch(_){allow=false;}}
   if(!allow){try{if(window.oneConnectHost)window.oneConnectHost.emit('game.native_move_bounds_blocked',{level:value(this.runtime,'level'),sid:this.sid});}catch(_){}return;}
   if(!definition)return old.apply(this,arguments);var prior=active;active={runtime:this.runtime,limits:allow};try{return old.apply(this,arguments);}finally{active=prior;}};installed=true;
 }
 window.oneConnectNativeMoveBounds={install:install};
}());
