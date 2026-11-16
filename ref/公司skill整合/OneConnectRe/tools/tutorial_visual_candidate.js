/* Candidate tutorial art only. Existing guides retain all input and state. */
(function () {
  'use strict';
  function image(src,css){var el=document.createElement('img');el.src=src;el.alt='';el.style.cssText=css;return el;}
  function hand(parent){
    var el=image('images/ui-tutorial-hand.png','position:absolute;left:70%;top:65%;width:clamp(48px,12vw,76px);height:auto;pointer-events:none;filter:drop-shadow(0 2px 3px #11244a);animation:oc-guide-frame-pulse 1s ease-in-out infinite');
    parent.appendChild(el);return el;
  }
  function instruction(id,icon,shortText){
    var root=document.getElementById(id);if(!root)return;
    var frame=root.firstElementChild,label=frame&&frame.nextElementSibling,extra=label&&label.nextElementSibling;
    if(!frame||!label)return;
    frame.style.animation='oc-guide-frame-pulse 1s ease-in-out infinite';
    frame.style.boxShadow='0 0 0 200vmax rgba(4,10,30,.38),0 0 14px #ffe47a';
    label.textContent=shortText;
    // The guide updates label.textContent on every frame. A child image would
    // be deleted, so the icon is a pseudo-element above the card's border image.
    label.className='oc-guide-label';
    label.style.cssText='position:absolute;top:19%;left:12%;width:76%;min-height:76px;box-sizing:border-box;padding:2px 8px 2px clamp(48px,12vw,70px);display:flex;align-items:center;justify-content:center;border:18px solid transparent;border-image:url("images/ui-tutorial-card.png") 25% 14% fill / 18px stretch;--oc-guide-icon:url("'+icon+'");color:white;text-align:center;font:bold clamp(16px,4vw,23px) sans-serif;pointer-events:none';
    if(extra && extra.id!=='oc-tenth-guide-hand')extra.style.display='none';
    if(id==='oc-fifth-guide')hand(frame);
    if(id==='oc-tenth-guide'){
      var old=document.getElementById('oc-tenth-guide-hand');
      if(old){old.textContent='';old.style.cssText='position:absolute;left:70%;top:65%;width:clamp(48px,12vw,76px);aspect-ratio:1;background:url("images/ui-tutorial-hand.png") center/contain no-repeat;pointer-events:none;filter:drop-shadow(0 2px 3px #11244a);animation:oc-guide-frame-pulse 1s ease-in-out infinite';}
    }
  }
  function install(){
    // Original mark: Sine movement=size, triangle wave, period .3 s,
    // magnitude 5 on a 108 px mark (about 4.6%).
    var frameStyle=document.createElement('style');frameStyle.textContent='.oc-guide-label::before{content:"";position:absolute;left:8px;top:50%;width:clamp(38px,10vw,60px);height:clamp(38px,10vw,60px);transform:translateY(-50%);background:var(--oc-guide-icon) center/contain no-repeat;pointer-events:none;animation:oc-guide-label-icon 1s ease-in-out infinite}@keyframes oc-guide-frame-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}@keyframes oc-guide-frame-centered{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.1)}}@keyframes oc-guide-cursor-pulse{0%,100%{transform:translate(-12%,-8%) scale(1)}50%{transform:translate(-12%,-8%) scale(1.1)}}@keyframes oc-guide-label-icon{0%,100%{transform:translateY(-50%) scale(1)}50%{transform:translateY(-50%) scale(1.1)}}@media(prefers-reduced-motion:reduce){#oc-tutorial *,#oc-second-guide *,#oc-third-guide *,#oc-fifth-guide *,#oc-seventh-guide *,#oc-tenth-guide *, .oc-guide-label::before{animation:none!important}}';document.head.appendChild(frameStyle);
    var first=document.getElementById('oc-tutorial'),prompt=document.getElementById('oc-tutorial-prompt');
    if(first){var cursor=first.querySelector('[data-ui-tutorial-cursor]');if(cursor){cursor.textContent='';cursor.style.cssText='position:absolute;pointer-events:none;width:clamp(48px,12vw,76px);aspect-ratio:1;background:url("images/ui-tutorial-hand.png") center/contain no-repeat;transform:translate(-12%,-8%);animation:oc-guide-cursor-pulse 1s ease-in-out infinite;transition:left .45s ease-in-out,top .45s ease-in-out';}}
    if(prompt)prompt.style.cssText='position:absolute;top:17%;left:50%;transform:translateX(-50%);width:62%;min-height:68px;display:flex;align-items:center;justify-content:center;padding:0 4px;box-sizing:border-box;border:18px solid transparent;border-image:url("images/ui-tutorial-card.png") 25% 14% fill / 18px stretch;color:white;font:bold clamp(13px,3.5vw,18px) sans-serif;text-align:center';
    var skip=document.getElementById('oc-tutorial-skip');if(skip)skip.style.cssText='position:absolute;top:17%;right:2%;width:16%;height:68px;padding:6px;border:0;background:transparent url("images/ui-blue-button.png") center/100% 100% no-repeat;color:white;font:bold clamp(14px,3.5vw,18px) sans-serif;pointer-events:auto';
    instruction('oc-third-guide','images/ui-tutorial-clock.png','Clear before time runs out!');
    instruction('oc-fifth-guide','images/gamebuttons-sheet1.webp','Find a pair');
    instruction('oc-tenth-guide','images/gamebuttons-sheet0.webp','Shuffle the tiles');
    // The browser viewport can include native chrome or letterboxing. Keep
    // instructional UI aligned to the visible game canvas, not window edges.
    var lastCanvasBounds='';
    function position(){
      var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),canvas=r&&r.canvas;
      if(canvas){
        var rect=canvas.getBoundingClientRect(),x=Math.max(0,rect.left),y=Math.max(0,rect.top),right=Math.min(window.innerWidth,rect.right),bottom=Math.min(window.innerHeight,rect.bottom),w=right-x,h=bottom-y;
        var bounds=[x,y,w,h].join(',');
        if(w>0&&h>0&&bounds!==lastCanvasBounds){
          lastCanvasBounds=bounds;
          if(prompt){prompt.style.left=(x+w*.5)+'px';prompt.style.top=(y+h*.17)+'px';prompt.style.width=(w*.62)+'px';}
          if(skip){skip.style.left=(x+w*.82)+'px';skip.style.right='auto';skip.style.top=(y+h*.17)+'px';skip.style.width=(w*.16)+'px';}
          ['oc-third-guide','oc-fifth-guide','oc-tenth-guide'].forEach(function(id){var parent=document.getElementById(id),label=parent&&parent.children[1];if(label){label.style.left=(x+w*.12)+'px';label.style.top=(y+h*.19)+'px';label.style.width=(w*.76)+'px';}});
        }
      }
    }
    position();
    // The canvas may be reflowed by its host without a resize event. A low
    // frequency fallback catches that case without a permanent frame loop.
    setInterval(position,250);
    if(window.addEventListener){
      window.addEventListener('resize',position);
      window.addEventListener('orientationchange',position);
      window.addEventListener('oneconnect:event',function(e){if(e.detail&&e.detail.type==='tutorial.start')position();});
    }
    var seventh=document.getElementById('oc-seventh-guide');
    if(seventh&&seventh.firstElementChild){
      var card=seventh.firstElementChild;
      var illustrations=card.children&&card.children[1];if(illustrations&&illustrations.querySelectorAll)illustrations.querySelectorAll('img,svg').forEach(function(icon){icon.style.animation='oc-guide-frame-pulse 1s ease-in-out infinite';});
    }
  }
  window.oneConnectTutorialVisualCandidate={install:install};
}());
