/* Scale the original animated selection mark with the selected tile. */
(function(){
 'use strict';
 var installed=false;
 function install(){
  if(installed)return;var action=window.cr&&cr.action&&cr.action.prototype;if(!action||typeof action.run_object!=='function')return;
  var previous=action.run_object;action.run_object=function(){
   if(this.sid!==881765380413314||!this.runtime)return previous.apply(this,arguments);
   var r=this.runtime,rows=Array.isArray(r.createRow)?r.createRow:null,before=rows?new Set(rows):null,tiles=r.types&&r.types.t5,selected=tiles&&tiles.getCurrentSol&&tiles.getCurrentSol().getObjects(),tile=selected&&selected[0];
   var result=previous.apply(this,arguments);
   if(!before||!tile||!Number.isFinite(tile.width)||!Number.isFinite(tile.height)||!tile.width||!tile.height)return result;
   r.createRow.forEach(function(mark){if(before.has(mark)||!mark.type||mark.type.name!=='t28')return;
    var width=Math.abs(tile.width)*1.125,height=Math.abs(tile.height)*1.125;
    mark.width=width;mark.height=height;
    (mark.behavior_insts||[]).forEach(function(behavior){if(behavior&&behavior.movement===2&&Number.isFinite(behavior.initialValue)&&Number.isFinite(behavior.mag)){behavior.initialValue=width;behavior.ratio=height/width;behavior.mag=5*width/108;}});
    if(typeof mark.set_bbox_changed==='function')mark.set_bbox_changed();r.redraw=true;
   });return result;
  };installed=true;
 }
 window.oneConnectSelectionFrameCandidate={install:install};
}());
