/* Candidate: animate actual C2 tiles after the original shuffle updates the board. */
(function(){
 'use strict';
 var installed=false,active=null,depth=0;
 var shuffleCalls={342934048923318:true,987355312738297:true,143347589055852:true};
 function skipped(reason){try{if(window.oneConnectHost)window.oneConnectHost.emit('candidate.shuffle_motion_skipped',{reason:reason});}catch(_){}}
 function level(r){var v=r&&Array.isArray(r.all_global_vars)&&r.all_global_vars.find(function(x){return x.name==='level';});return v&&v.data;}
 function snapshot(r){var tiles=r&&r.types&&r.types.t5&&r.types.t5.instances;if(!Array.isArray(tiles)||!tiles.length)return null;
  if(tiles.some(function(t){return !t||!t.instance_vars||t.instance_vars[3]||t.inAnimTrigger||!Number.isInteger(t.cur_frame);}))return null;
  return tiles.map(function(t){return {uid:t.uid,kind:t.cur_frame,x:t.x,y:t.y,tile:t};});}
 function safeSnapshot(r){try{return snapshot(r);}catch(_){return null;}}
 function settle(){var a=active;active=null;if(!a)return;var r=a.runtime;if(!r.running_layout||r.running_layout.name!=='game'||level(r)!==a.level)return;
  a.moves.forEach(function(m){try{if(r.types.t5.instances.includes(m.tile)){m.tile.x=m.toX;m.tile.y=m.toY;m.tile.set_bbox_changed();}}catch(_){}});r.redraw=true;}
 function frame(now,a){if(!a||active!==a)return;var r=a.runtime;if(!r.running_layout||r.running_layout.name!=='game'||level(r)!==a.level){active=null;return;}
  var pause=r.all_global_vars.find(function(x){return x.name==='pause';});if(a.last!==null&&!document.hidden&&!(pause&&pause.data))a.elapsed+=Math.min(50,Math.max(0,now-a.last));a.last=now;
  var t=Math.min(1,a.elapsed/1000),ease=t*t*(3-2*t);try{a.moves.forEach(function(m){if(r.types.t5.instances.includes(m.tile)){m.tile.x=m.fromX+(m.toX-m.fromX)*ease;m.tile.y=m.fromY+(m.toY-m.fromY)*ease;m.tile.set_bbox_changed();}});}catch(error){settle();console.warn('Shuffle animation stopped',error);return;}r.redraw=true;
  if(t>=1)settle();else window.requestAnimationFrame(function(now){frame(now,a);});}
 function install(){if(installed)return;var action=window.cr&&cr.action&&cr.action.prototype;if(!action||typeof action.run_object!=='function')return;
  var old=action.run_object;action.run_object=function(){if(!shuffleCalls[this.sid]||!this.runtime||depth)return old.apply(this,arguments);settle();var r=this.runtime,before=safeSnapshot(r),oldLevel=level(r),result;depth++;try{result=old.apply(this,arguments);}finally{depth--;}var after=safeSnapshot(r);
   if(!before||!after||!r.running_layout||r.running_layout.name!=='game'||level(r)!==oldLevel){skipped('snapshot_unavailable');return result;}
   if(!window.oneConnectShuffleMotionMap||typeof window.oneConnectShuffleMotionMap.map!=='function'){skipped('mapping_unavailable');return result;}var map;try{map=window.oneConnectShuffleMotionMap.map(before,after);}catch(_){skipped('mapping_error');return result;}if(!map||map.some(function(m){return m.sourceUid!==m.targetUid;})){skipped('identity_changed');return result;}
   var byId=new Map(after.map(function(x){return [x.uid,x.tile];})),moves=map.filter(function(m){return m.fromX!==m.toX||m.fromY!==m.toY;}).map(function(m){m.tile=byId.get(m.targetUid);return m;});
   if(moves.length){active={runtime:r,level:oldLevel,moves:moves,elapsed:0,last:null};var current=active;try{moves.forEach(function(m){m.tile.x=m.fromX;m.tile.y=m.fromY;m.tile.set_bbox_changed();});r.redraw=true;window.requestAnimationFrame(function(now){frame(now,current);});}catch(error){settle();console.warn('Shuffle animation unavailable',error);}}return result;};
  var touch=window.cr&&cr.plugins_&&cr.plugins_.Touch&&cr.plugins_.Touch.prototype.cnds;if(touch){var prior=touch.OnTouchObject;touch.OnTouchObject=function(type){var ok=prior.apply(this,arguments);return ok&&active&&type&&(type.name==='t5'||type.name==='t26')?false:ok;};}
  if(typeof document!=='undefined'&&document.addEventListener)document.addEventListener('visibilitychange',function(){if(active)active.last=null;});
  window.addEventListener('oneconnect:event',function(e){var t=e.detail&&e.detail.type;if(t==='game.board_configured'){active=null;return;}if(t==='game.level_fail'||t==='game.level_win')settle();});installed=true;}
 window.oneConnectShuffleMotionCandidate={install:install,state:function(){return {moving:!!active};}};
}());
