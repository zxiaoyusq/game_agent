/* Animate the original Construct pause controls while retaining native input. */
(function(){'use strict';
 var installed=false,state=null,tutorial=null,WAIT_SID=874223100987651,TUTORIAL_WAIT_SID=874223100987652,DURATION=180;
 function reduced(){return !!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);}
 function layer(runtime){return runtime&&runtime.getLayerByName&&runtime.getLayerByName('OP');}
 function reset(){if(state){if(state.layer&&Number.isFinite(state.scale))state.layer.scale=state.scale;state.extra.forEach(function(size,item){item.width=size[0];item.height=size[1];if(item.set_bbox_changed)item.set_bbox_changed();});if(state.runtime)state.runtime.redraw=true;}state=null;}
 function resetTutorial(){if(tutorial){tutorial.item.width=tutorial.width;tutorial.item.height=tutorial.height;if(tutorial.item.set_bbox_changed)tutorial.item.set_bbox_changed();if(tutorial.runtime)tutorial.runtime.redraw=true;}tutorial=null;}
 function startTutorial(runtime,item,closing){if(!item)return;resetTutorial();var quiet=reduced();if(quiet&&!closing)return;tutorial={runtime:runtime,item:item,width:item.width,height:item.height,start:Date.now(),closing:closing,quiet:quiet};}
 function start(runtime,closing){if(!runtime||!runtime.running_layout||runtime.running_layout.name!=='game')return;reset();var quiet=reduced();if(quiet&&!closing)return;var l=layer(runtime);state={runtime:runtime,layer:l,scale:l&&l.scale,start:Date.now(),closing:closing,quiet:quiet,extra:new Map()};}
 function tick(runtime,controlsLaidOut){if(tutorial){if(runtime!==tutorial.runtime||!runtime.running_layout||runtime.running_layout.name!=='game')resetTutorial();else{var u=Math.min(1,Math.max(0,(Date.now()-tutorial.start)/DURATION)),e=1-(1-u)*(1-u),f=tutorial.quiet?1:(tutorial.closing?1-.16*e:.84+.16*e);tutorial.item.width=tutorial.width*f;tutorial.item.height=tutorial.height*f;if(tutorial.item.set_bbox_changed)tutorial.item.set_bbox_changed();runtime.redraw=true;if(u>=1&&!tutorial.closing)resetTutorial();}}
  if(!state)return;if(runtime!==state.runtime||!runtime.running_layout||runtime.running_layout.name!=='game'){reset();return;}
  var pause=runtime.all_global_vars&&runtime.all_global_vars.find(function(v){return v.name==='pause';});if(!pause||!pause.data){reset();return;}
  var t=Math.min(1,Math.max(0,(Date.now()-state.start)/DURATION)),ease=1-(1-t)*(1-t),factor=state.quiet?1:(state.closing?1-.16*ease:.84+.16*ease);
  if(state.layer&&Number.isFinite(state.scale))state.layer.scale=state.scale*factor;
  ['t22','t23','t12'].forEach(function(name){var items=runtime.types&&runtime.types[name]&&runtime.types[name].instances||[];items.forEach(function(item){if(!item.visible||!item.layer||item.layer.name!=='Top'||(name!=='t12'&&!controlsLaidOut))return;if(name==='t12'){if(!state.extra.has(item))state.extra.set(item,[item.width,item.height]);var base=state.extra.get(item);item.width=base[0]*factor;item.height=base[1]*factor;}else{item.width*=factor;item.height*=factor;}if(item.set_bbox_changed)item.set_bbox_changed();});});runtime.redraw=true;
  if(t>=1&&!state.closing)reset();
 }
 function install(){if(installed)return;var action=window.cr&&cr.action&&cr.action.prototype;if(!action||typeof action.run_system!=='function')return;
  var old=action.run_system;action.run_system=function(){if(this.sid===WAIT_SID)start(this.runtime,true);if(this.sid===TUTORIAL_WAIT_SID){var t=this.runtime.types.t33&&this.runtime.types.t33.instances[0];startTutorial(this.runtime,t,true);}var result=old.apply(this,arguments);if(this.sid===221372034106797)start(this.runtime,false);if(this.sid===912592268356661){var items=this.runtime.createRow||[],item=items.filter(function(x){return x.type&&x.type.name==='t33';}).pop();startTutorial(this.runtime,item,false);}if(this.sid===918927348401778)reset();return result;};
  var oldObject=action.run_object;if(typeof oldObject==='function')action.run_object=function(){if(this.sid===268127763738893)resetTutorial();return oldObject.apply(this,arguments);};
  var touch=cr.plugins_&&cr.plugins_.Touch&&cr.plugins_.Touch.prototype.cnds;if(touch)['OnTouchObject','OnTouchStart'].forEach(function(name){if(typeof touch[name]!=='function')return;var prev=touch[name];touch[name]=function(){var result=prev.apply(this,arguments);return (state&&state.closing)||(tutorial&&tutorial.closing)?false:result;};});installed=true;
 }
 window.oneConnectNativePauseMotion={install:install,tick:tick};
}());
