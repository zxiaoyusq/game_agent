/* Optional visual effect, based on DSH's decoded CreateStar timing. It does not
 * change score, inventory or the original connection/elimination textures. */
(function(){
 'use strict';
 var installed=false,active=[],running=false,ending=false,closed=false;
 function target(){
  var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();
  if(!r||!r.running_layout||r.running_layout.name!=='game'||!r.canvas)return null;
  var star=r.types.t24&&r.types.t24.instances.find(function(x){return x.uid===31;});
  if(!star||!star.layer)return null;
  var rect=r.canvas.getBoundingClientRect(),ratio=r.isRetina?r.devicePixelRatio:1;
  if(!rect.width||!rect.height||!r.canvas.width||!r.canvas.height)return null;
  return {x:rect.left+star.layer.layerToCanvas(star.x,star.y,true)*ratio*rect.width/r.canvas.width,
    y:rect.top+star.layer.layerToCanvas(star.x,star.y,false)*ratio*rect.height/r.canvas.height};
 }
 function frame(now){
  var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),goal=target(),pause=r&&r.all_global_vars.find(function(v){return v.name==='pause';});
  active=active.filter(function(item){
   if(!goal){item.node.remove();return false;}
   if(item.last===null)item.last=now;
   var dt=Math.min(Math.max(0,now-item.last),50);item.last=now;
   if((ending||!(pause&&pause.data))&&!document.hidden)item.elapsed+=dt;
   var growth=Math.min(1,item.elapsed/250),t=Math.max(0,Math.min(1,(item.elapsed-250)/600)),ease=t*t;
   // The original calls a Bezier flight. The horizontal bow is provisional:
   // control-point parameters and timing are still under investigation.
   var bend=Math.max(-40,Math.min(40,(goal.y-item.y)*.12));
   var x=item.x+(goal.x-item.x)*ease+4*ease*(1-ease)*bend,y=item.y+(goal.y-item.y)*ease;
   item.node.style.transform='translate('+x+'px,'+y+'px) translate(-50%,-50%) scale('+growth+')';
   if(t>=1){item.node.remove();return false;}return true;
  });
  if(active.length)requestAnimationFrame(frame);else running=false;
 }
 function spawn(points){
  if(!Array.isArray(points)||points.length<2||points.length>128||!target()||points.some(function(p){return !p||!Number.isFinite(p.x)||!Number.isFinite(p.y);}))return;
  points.forEach(function(p){var node=document.createElement('img');node.src='images/ui-star-filled.png';node.alt='';node.setAttribute('aria-hidden','true');node.style.cssText='position:fixed;left:0;top:0;z-index:24;width:56px;height:56px;object-fit:contain;pointer-events:none;will-change:transform';document.body.appendChild(node);active.push({node:node,x:p.x,y:p.y,elapsed:0,last:null});});
  if(!running){running=true;requestAnimationFrame(frame);}
 }
 function clear(){active.forEach(function(item){item.node.remove();});active=[];}
 function install(){if(installed)return;installed=true;if(document.addEventListener)document.addEventListener('visibilitychange',function(){active.forEach(function(item){item.last=null;});});window.addEventListener('oneconnect:event',function(e){var d=e.detail;if(!d)return;if(d.type==='game.board_configured'||d.type==='game.round_ready'){clear();ending=false;closed=false;}else if(d.type==='game.level_fail'||d.type==='screen.SCREEN_HOME'){clear();ending=false;closed=true;}else if(d.type==='game.level_win'||d.type==='screen.SCREEN_BONUS')ending=true;else if(!closed&&d.type==='candidate.link_points'&&d.detail)spawn(d.detail.pathScreenPoints||d.detail.selectedScreenPoints);});}
 window.oneConnectFlyStarCandidate={install:install,state:function(){return {active:active.length};}};
}());
