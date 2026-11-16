/* Home score is informational; tapping it does not open a star dialog. */
(function(){
 'use strict';
 var installed=false,badge=null,value=null,lastValue=null,lastBounds='';
 function install(){
  if(installed)return;installed=true;
  badge=document.createElement('div');badge.setAttribute('aria-label','Score');
  badge.style.cssText='display:none;position:fixed;z-index:24;box-sizing:border-box;min-width:86px;height:42px;padding:4px 12px;border:0;background:transparent url("images/ui-blue-button.png") center/100% 100% no-repeat;color:white;font:bold 21px sans-serif;text-align:center;pointer-events:none';
  var icon=document.createElement('img');icon.src='images/ui-star-filled.png';icon.alt='';icon.style.cssText='width:25px;height:25px;object-fit:contain;vertical-align:middle';value=document.createElement('span');badge.append(icon,value);document.body.appendChild(badge);
  function update(){
   var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),visible=r&&r.running_layout&&r.running_layout.name==='menu'&&r.canvas;
   if(visible){var rect=r.canvas.getBoundingClientRect(),left=Math.max(0,rect.left),top=Math.max(0,rect.top),right=Math.min(window.innerWidth,rect.right),bottom=Math.min(window.innerHeight,rect.bottom);visible=right-left>=160&&bottom-top>=60;
    if(visible){var score=r.all_global_vars&&r.all_global_vars.find(function(v){return v.name==='score';}),n=score&&Number.isFinite(score.data)&&score.data>=0?Math.floor(score.data):0;if(n!==lastValue){lastValue=n;value.textContent=' '+n;badge.setAttribute('aria-label','Score: '+n);}var bounds=(left+12)+':'+(top+12);if(bounds!==lastBounds){badge.style.left=(left+12)+'px';badge.style.top=(top+12)+'px';lastBounds=bounds;}}
   }
   badge.style.display=visible?'block':'none';requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
 }
 window.oneConnectHomeStarCandidate={install:install};
}());
