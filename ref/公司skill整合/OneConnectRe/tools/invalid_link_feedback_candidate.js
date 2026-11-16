/* Feedback for an explicit failed same-image selection. Timing is provisional. */
(function(){
 'use strict';
 var installed=false,root=null,timer=null,shake=null,overlayShake=null;
 function clear(){if(timer!==null){clearTimeout(timer);timer=null;}if(shake&&typeof shake.cancel==='function')shake.cancel();if(overlayShake&&typeof overlayShake.cancel==='function')overlayShake.cancel();shake=null;overlayShake=null;if(root){root.remove();root=null;}}
 function show(detail){
  var points=detail&&detail.points,r=window.cr_getC2Runtime&&window.cr_getC2Runtime();
  if(!Array.isArray(points)||points.length!==2||points.some(function(p){return !p||!Number.isFinite(p.x)||!Number.isFinite(p.y);})||!r||!r.canvas||!r.running_layout||r.running_layout.name!=='game')return;
  clear();var a=points[0],b=points[1],ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('width','100%');svg.setAttribute('height','100%');svg.setAttribute('aria-hidden','true');svg.style.cssText='position:fixed;inset:0;z-index:35;pointer-events:none;overflow:visible';
  var line=document.createElementNS(ns,'line');line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);line.setAttribute('stroke','#ff3945');line.setAttribute('stroke-width','5');line.setAttribute('stroke-linecap','round');svg.appendChild(line);
  var cx=(a.x+b.x)/2,cy=(a.y+b.y)/2,size=Math.max(8,Math.min(15,Math.hypot(b.x-a.x,b.y-a.y)*.12));
  [-1,1].forEach(function(sign){var cross=document.createElementNS(ns,'line');cross.setAttribute('x1',cx-size);cross.setAttribute('y1',cy-sign*size);cross.setAttribute('x2',cx+size);cross.setAttribute('y2',cy+sign*size);cross.setAttribute('stroke','#ff2838');cross.setAttribute('stroke-width','6');cross.setAttribute('stroke-linecap','round');cross.style.transformOrigin=cx+'px '+cy+'px';svg.appendChild(cross);
   // Competitor DrawError scales the cross in over 0.06 seconds. Its total
   // display time is still unverified, so the removal timer remains provisional.
   if(typeof cross.animate==='function'&&!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches))try{cross.animate([{transform:'scale(0)'},{transform:'scale(1)'}],{duration:60,easing:'linear'});}catch(_){}
  });
  document.body.appendChild(svg);root=svg;
  if(typeof r.canvas.animate==='function'&&!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){
   try{var frames=[{translate:'0px 0px'},{translate:'-5px 0px'},{translate:'5px 0px'},{translate:'-3px 0px'},{translate:'0px 0px'}],options={duration:280,easing:'ease-out'};shake=r.canvas.animate(frames,options);if(typeof svg.animate==='function'){overlayShake=svg.animate(frames,options);if(shake.startTime!=null)overlayShake.startTime=shake.startTime;}}catch(_){}
  }
  timer=setTimeout(clear,450);
 }
 function install(){if(installed)return;installed=true;window.addEventListener('oneconnect:event',function(e){var d=e.detail;if(!d)return;if(d.type==='candidate.invalid_link')show(d.detail);else if(d.type==='game.auto_shuffle_start'||d.type==='game.board_configured'||d.type==='game.round_ready'||d.type==='game.level_fail'||d.type==='game.level_win'||d.type==='screen.SCREEN_HOME')clear();});}
 window.oneConnectInvalidLinkFeedbackCandidate={install:install};
}());
