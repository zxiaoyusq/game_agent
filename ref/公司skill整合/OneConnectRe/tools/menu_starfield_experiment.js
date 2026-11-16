/* Opt-in experiment: move the existing tiled menu background without a new image. */
(function(){'use strict';
 var state=null,phaseX=0,phaseY=0,waitForAnchor=false;
 function mod(n,d){return ((n%d)+d)%d;}
 function restore(){if(!state)return;var s=state,t=s.tile;t.x=s.x;t.y=s.y;t.width=s.width;t.height=s.height;t.set_bbox_changed();if(s.anchor)s.anchor.enabled=s.anchorEnabled;state=null;}
 function update(runtime,dt,enabled){
  if(!enabled||!runtime||!runtime.running_layout||runtime.running_layout.name!=='menu'){restore();return false;}
  if(waitForAnchor){waitForAnchor=false;return false;}
  var t=runtime.types&&runtime.types.t46&&runtime.types.t46.instances.find(function(v){return v.uid===63;});
  if(!t||!t.texture_img||!t.texture_img.width||!t.texture_img.height||!t.layer||typeof t.layer.canvasToLayer!=='function'){restore();return false;}
  if(!state||state.tile!==t){restore();var anchor=Array.isArray(t.behavior_insts)&&t.behavior_insts.find(function(b){return b&&b.type&&b.type.behavior&&window.cr&&window.cr.behaviors&&window.cr.behaviors.Anchor&&b.type.behavior instanceof window.cr.behaviors.Anchor;});state={tile:t,x:t.x,y:t.y,width:t.width,height:t.height,anchor:anchor,anchorEnabled:anchor&&anchor.enabled};if(anchor)anchor.enabled=false;phaseX=phaseY=0;}
  var tw=t.texture_img.width,th=t.texture_img.height,layer=t.layer;
  var x0=layer.canvasToLayer(0,0,true),y0=layer.canvasToLayer(0,0,false),dx=layer.canvasToLayer(1,-1,true)-x0,dy=layer.canvasToLayer(1,-1,false)-y0,mag=Math.hypot(dx,dy);
  if(!Number.isFinite(mag)||mag===0){restore();return false;}
  var elapsed=Math.min(.1,Math.max(0,Number(dt)||0));phaseX=mod(phaseX+dx/mag*8*elapsed,tw);phaseY=mod(phaseY+dy/mag*8*elapsed,th);
  t.width=state.width+2*tw;t.height=state.height+2*th;t.x=state.x-tw+phaseX;t.y=state.y-th+phaseY;t.set_bbox_changed();runtime.redraw=true;return true;
 }
 if(typeof window.addEventListener==='function')['resize','orientationchange'].forEach(function(name){window.addEventListener(name,function(){restore();waitForAnchor=true;});});
 window.oneConnectMenuStarfieldExperiment={update:update,restore:restore};
}());
