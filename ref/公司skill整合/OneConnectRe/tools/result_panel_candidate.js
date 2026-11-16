/* Presentation-only result panel. It is not installed in the game and does
 * not award stars, write saves, advance levels or invoke advertisements. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectResultPanelCandidate = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function create(document, options) {
    options = options || {};
    if (!document || !document.body) throw Error('document body required');
    var root = document.createElement('div'); root.className = 'oc-result-candidate'; root.hidden = true;
    root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true');
    var style = document.createElement('style');
    style.textContent = '.oc-result-candidate[hidden]{display:none!important}.oc-result-candidate{position:fixed;inset:0;z-index:45;display:grid;place-items:center;padding:12px;background:rgba(3,8,25,.76);font-family:system-ui,sans-serif}.oc-result-candidate .card{box-sizing:border-box;width:min(340px,95%,calc((100vh - 48px)*.77));aspect-ratio:463/600;padding:clamp(18px,6vw,32px);display:flex;flex-direction:column;align-items:center;justify-content:center;border:28px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% 22% fill / 28px stretch;text-align:center;color:white}.oc-result-candidate h2{margin:0 0 5px;font-size:clamp(20px,6vw,28px)}.oc-result-candidate .level{font-size:clamp(15px,4vw,19px);font-weight:700}.oc-result-candidate .score{margin:8px 0;font-size:clamp(13px,4vw,19px);font-weight:700}.oc-result-candidate .stars{display:flex;justify-content:center;gap:2px;min-height:38px}.oc-result-candidate .stars img{width:clamp(32px,10vw,52px);height:auto;object-fit:contain}.oc-result-candidate .stars img.off{filter:grayscale(1) brightness(.55);opacity:.65}.oc-result-candidate .actions{display:flex;width:100%;gap:3px}.oc-result-candidate button{flex:1;min-width:0;min-height:48px;border:0;background:transparent url("images/ui-blue-button.png") center/100% 100% no-repeat;color:white;font:bold clamp(14px,4vw,17px) system-ui;touch-action:manipulation}.oc-result-candidate button:disabled{opacity:.5}.oc-result-candidate:not([hidden]) .card{animation:oc-result-enter .2s ease-out}@keyframes oc-result-enter{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:scale(1)}}@media(prefers-reduced-motion:reduce){.oc-result-candidate:not([hidden]) .card{animation:none}}';
    style.textContent += '.oc-result-candidate.win .card{justify-content:space-evenly}.oc-result-candidate.win h2{width:100%;margin:0}.oc-result-candidate.win h2 img{display:block;width:100%;height:auto}.oc-result-candidate.win .level,.oc-result-candidate.win .score{box-sizing:border-box;width:85%;min-height:38px;display:flex;align-items:center;justify-content:center;gap:6px;border:14px solid transparent;border-image:url("images/ui-blue-button.png") 45% 20% fill / 14px 15px stretch;font-size:clamp(16px,5vw,22px)}.oc-result-candidate.win .stars{min-height:60px;gap:3px}.oc-result-candidate.win .stars img{width:clamp(48px,17vw,75px)}.oc-result-candidate.win .score img{width:26px;height:26px;object-fit:contain}.oc-result-candidate.win .actions{align-items:center;gap:8px}.oc-result-candidate.win .actions .home{flex:none;width:60px;height:60px;min-height:0;background:url("images/ui-victory-home.png") center/contain no-repeat}.oc-result-candidate.win .actions .next{min-height:60px;box-sizing:border-box;border:14px solid transparent;border-image:url("images/ui-blue-button.png") 45% 20% fill / 14px 15px stretch;font-size:22px}';
    var card=document.createElement('div');card.className='card';
    var encouragement=document.createElement('div');encouragement.className='oc-encouragement';encouragement.hidden=true;
    var confetti=document.createElement('div');confetti.className='oc-confetti';encouragement.appendChild(confetti);
    var bannerWrap=document.createElement('div');bannerWrap.className='oc-encouragement-art';
    var banner=document.createElement('img');banner.src='images/ui-encouragement-banner.png';banner.alt='';
    var cheer=document.createElement('span');cheer.textContent='GREAT JOB!';bannerWrap.append(banner,cheer);encouragement.appendChild(bannerWrap);
    var introStyle=document.createElement('style');introStyle.textContent='.oc-encouragement[hidden]{display:none!important}.oc-encouragement{position:absolute;inset:0;display:grid;place-items:center;pointer-events:none}.oc-encouragement-art{position:relative;width:min(94%,420px);animation:oc-cheer-in .3s ease-out}.oc-encouragement img{display:block;width:100%;height:auto}.oc-encouragement span{position:absolute;top:67%;left:0;width:100%;transform:translateY(-50%);text-align:center;color:white;font:900 clamp(20px,6vw,30px) system-ui,sans-serif;text-shadow:0 3px 3px #06418f}@keyframes oc-cheer-in{from{transform:scale(.85)}to{transform:scale(1)}}@media(prefers-reduced-motion:reduce){.oc-encouragement-art{animation:none}}';
    introStyle.textContent += '.oc-confetti{position:absolute;inset:0;overflow:hidden}.oc-confetti i{position:absolute;width:12px;height:20px;animation:oc-confetti-x 2s linear both;animation-delay:var(--delay)}.oc-confetti i b{display:block;width:100%;height:100%;background:var(--color);mask:var(--sprite) center/contain no-repeat;-webkit-mask:var(--sprite) center/contain no-repeat;animation:oc-confetti-y 2s linear both;animation-delay:var(--delay)}@keyframes oc-confetti-x{to{transform:translateX(var(--dx))}}@keyframes oc-confetti-y{0%{transform:translateY(0) rotate(0deg) scale(.7);animation-timing-function:ease-out}48%{transform:translateY(var(--apex)) rotate(var(--mid-spin)) scale(1);animation-timing-function:ease-in}100%{transform:translateY(var(--dy)) rotate(var(--spin)) scale(0)}}@media(prefers-reduced-motion:reduce){.oc-confetti{display:none}}';
    style.textContent += '.oc-result-candidate.win .actions .home{background-size:150% 150%}';
    // Position against the approved portrait composition; the win card is a
    // single coordinate space so text and image alpha margins cannot shift rows.
    style.textContent += '.oc-result-candidate.win .card{position:relative;display:block;padding:0}.oc-result-candidate.win h2{position:absolute;left:9%;top:9%;width:82%}.oc-result-candidate.win .level{position:absolute;left:28%;top:24%;width:44%;height:8%;min-height:0;margin:0}.oc-result-candidate.win .stars{position:absolute;left:3%;top:32%;width:94%;height:27%;min-height:0;align-items:center;gap:0}.oc-result-candidate.win .stars img{width:33.333%;height:100%;min-width:0;object-fit:contain}.oc-result-candidate.win .stars img.off{filter:grayscale(1) brightness(.9);opacity:.85}.oc-result-candidate.win .score{position:absolute;left:16%;top:60%;width:68%;height:11%;min-height:0;margin:0}.oc-result-candidate.win .actions{position:absolute;left:8%;top:77%;width:84%;height:14%;gap:3%;align-items:center}.oc-result-candidate.win .actions .home{height:100%;width:auto;aspect-ratio:1;min-height:0;background-size:contain}.oc-result-candidate.win .actions .next{height:100%;min-height:0;font-size:clamp(18px,6vw,25px)}';
    style.textContent += '.oc-result-candidate.win h2::before{content:"";position:absolute;z-index:-1;left:-5%;top:-62%;width:110%;height:190%;background:url("images/ui-victory-rays.png") center/contain no-repeat;opacity:.48;pointer-events:none}.oc-result-candidate.win h2{isolation:isolate}';
    style.textContent += '.oc-result-candidate.win h2{left:0;top:6%;width:100%}.oc-result-candidate.win .actions{left:0;width:100%}.oc-result-candidate.win .stars img:not(.off){filter:drop-shadow(0 0 9px rgba(255,185,25,.65))}.oc-result-candidate.win .score{border-image-source:url("images/ui-dialog-panel.png");border-image-slice:22% fill;border-image-width:14px}';
    style.textContent += '.oc-result-candidate.win .actions .next{background:none;border-image-source:url("images/ui-victory-next.png");border-image-slice:45% 15% fill;border-image-width:45% 15%}';
    // The approved timeout design reuses the panel, score, home and button
    // artwork; its title and expressive clock are separate transparent assets.
    style.textContent += '.oc-result-candidate.fail .card{width:min(420px,95%,calc((100vh - 48px)*.965));aspect-ratio:.965}';
    // Reuse the existing rays behind the clock, tinted to the approved blue.
    style.textContent += '.oc-result-candidate.fail .card{isolation:isolate}.oc-result-candidate.fail .card::before{content:"";position:absolute;left:3%;top:18%;width:94%;height:36%;background:url("images/ui-victory-rays.png") center/contain no-repeat;filter:hue-rotate(165deg);opacity:.36;pointer-events:none;z-index:0}';
    style.textContent += '.oc-result-candidate.fail .card{position:relative;display:block;padding:0}.oc-result-candidate.fail h2{position:absolute;left:6%;top:8%;width:88%;margin:0}.oc-result-candidate.fail h2 img{display:block;width:100%;height:auto}.oc-result-candidate .timeout-clock{display:none}.oc-result-candidate.fail .timeout-clock{display:block;position:absolute;left:36%;top:27%;width:28%;height:20%;object-fit:contain}.oc-result-candidate.fail .level{position:absolute;left:24%;top:50%;width:52%;height:9%;box-sizing:border-box;display:flex;align-items:center;justify-content:center;border:12px solid transparent;border-image:url("images/ui-blue-button.png") 45% 20% fill / 12px stretch;font-size:clamp(16px,5vw,22px)}.oc-result-candidate.fail .score{position:absolute;left:19%;top:63%;width:62%;height:10%;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:6px;margin:0;border:14px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% fill / 14px stretch;font-size:clamp(16px,5vw,22px)}.oc-result-candidate.fail .score img{width:26px;height:26px;object-fit:contain}.oc-result-candidate.fail .actions{position:absolute;left:8%;top:78%;width:84%;height:14%;gap:3%;align-items:center}.oc-result-candidate.fail .actions .home{flex:none;height:100%;width:auto;aspect-ratio:1;min-height:0;background:url("images/ui-victory-home.png") center/contain no-repeat}.oc-result-candidate.fail .actions .retry{height:100%;min-height:0;background:none;border:14px solid transparent;border-image:url("images/ui-victory-next.png") 45% 15% fill / 45% 15%;font-size:clamp(18px,6vw,25px)}';
    // Keep the nine-slice outside the text box: its border must not consume
    // the short level badge's usable height or force a second line.
    style.textContent += '.oc-result-candidate.win .level,.oc-result-candidate.fail .level{border:0;padding:0 6%;white-space:nowrap;overflow:hidden;line-height:1;isolation:isolate}.oc-result-candidate.win .level::before,.oc-result-candidate.fail .level::before{content:"";position:absolute;inset:0;box-sizing:border-box;border:12px solid transparent;border-image:url("images/ui-blue-button.png") 45% 20% fill / 12px 15px stretch;z-index:-1;pointer-events:none}';
    style.textContent += '.oc-result-candidate .stars{display:none!important}.oc-result-candidate.win .level{left:14%;top:33%;width:72%;height:13%;font-size:clamp(22px,7vw,32px)}.oc-result-candidate.win .score{left:11%;top:51%;width:78%;height:14%;font-size:clamp(22px,7vw,32px)}.oc-result-candidate.win .score img{width:clamp(28px,8vw,40px);height:clamp(28px,8vw,40px)}';
    var title=document.createElement('h2'), level=document.createElement('div'), stars=document.createElement('div'), score=document.createElement('div'), actions=document.createElement('div');
    level.className='level';stars.className='stars';score.className='score';actions.className='actions';
    var timeoutClock=document.createElement('img');timeoutClock.className='timeout-clock';timeoutClock.src='images/timeout-clock.png';timeoutClock.alt='';
    card.append(title,level,stars,score,actions,timeoutClock);root.append(card,encouragement);document.head.append(style,introStyle);document.body.appendChild(root);
    ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click'].forEach(function(name){root.addEventListener(name,function(event){event.stopPropagation();});});
    var view = document.defaultView;
    function fitLevelText() {
      if (!view || !view.getComputedStyle || !level.clientWidth || !level.clientHeight) return;
      level.style.fontSize='';
      var computed=view.getComputedStyle(level),size=parseFloat(computed.fontSize);
      var measure=document.createElement('canvas'),context=measure.getContext&&measure.getContext('2d');
      if(!context||!Number.isFinite(size)||size<=0)return;
      context.font=(computed.fontWeight||'700')+' '+size+'px '+(computed.fontFamily||'sans-serif');
      var width=context.measureText(level.textContent).width;
      var available=level.clientWidth-(parseFloat(computed.paddingLeft)||0)-(parseFloat(computed.paddingRight)||0);
      if(width>0&&available>0)level.style.fontSize=(size*Math.min(1,available/width,level.clientHeight/size))+'px';
    }
    function position() {
      var runtime = view && view.cr_getC2Runtime && view.cr_getC2Runtime();
      var canvas = runtime && runtime.canvas;
      if (!canvas || !view) { root.style.cssText = ''; return; }
      var rect = canvas.getBoundingClientRect();
      var left = Math.max(0, rect.left), top = Math.max(0, rect.top);
      var right = Math.min(view.innerWidth, rect.right), bottom = Math.min(view.innerHeight, rect.bottom);
      if (right <= left || bottom <= top) { root.style.cssText = ''; return; }
      root.style.cssText = 'box-sizing:border-box;inset:auto;left:' + left + 'px;top:' + top +
        'px;width:' + (right-left) + 'px;height:' + (bottom-top) + 'px';
      fitLevelText();
    }
    if (view) { view.addEventListener('resize', position); view.addEventListener('scroll', position); }
    var introTimer=null;
    function playConfetti(){
      confetti.replaceChildren();
      // Four serialized emitters: two positions, two textures, bursts of 5 + 3.
      // Screen mapping and flight are provisional pending the remaining evidence.
      var colors=['#ffdc2d','#ff4eb4','#20cffa','#a42dff'];
      for(var side=0;side<2;side++)for(var texture=0;texture<2;texture++)for(var i=0;i<8;i++){
        var p=document.createElement('i'),seed=side*37+texture*19+i*13,jitter=Math.random();
        p.style.left=side?'90%':'10%';p.style.top=(43+(seed%7)-3)+'%';
        p.style.setProperty('--sprite','url("images/victory-confetti-'+(texture?'square':'strip')+'.png")');
        p.style.setProperty('--color',colors[(seed+texture)%colors.length]);
        p.style.setProperty('--delay',i<5?'0s':'.1s');
        var dx=(side?-1:1)*(80+seed%230+jitter*120),spin=(seed%2?1:-1)*(180+seed%360+jitter*90);
        p.style.setProperty('--dx',dx+'px');
        p.style.setProperty('--apex',(-70-(seed*7)%150-jitter*70)+'px');
        var dy=25+(seed*7)%65+jitter*25;
        p.style.setProperty('--dy',dy+'px');
        p.style.setProperty('--spin',spin+'deg');p.style.setProperty('--mid-spin',(spin*.45)+'deg');
        p.appendChild(document.createElement('b'));
        confetti.appendChild(p);
      }
    }
    function show(state) {
      if (!state || !['win','fail'].includes(state.kind) || !Number.isInteger(state.level) || state.level < 1) throw Error('invalid result state');
      root.classList.toggle('win',state.kind === 'win');
      root.classList.toggle('fail',state.kind === 'fail');
      title.textContent = '';
      if(state.kind === 'win'){var word=document.createElement('img');word.src='images/ui-victory-title.png';word.alt='Victory';title.appendChild(word);}
      else{var timeoutTitle=document.createElement('img');timeoutTitle.src='images/timeup-title.png';timeoutTitle.alt='Time up';title.appendChild(timeoutTitle);}
      level.textContent = 'LEVEL ' + state.level;
      // The current game owner exposes a cumulative score, not a per-level score.
      var scores=[];
      if (Number.isFinite(state.levelScore) && state.levelScore >= 0) scores.push('Level score: ' + Math.floor(state.levelScore));
      if (Number.isFinite(state.score) && state.score >= 0) scores.push('Total score: ' + Math.floor(state.score));
      score.textContent = scores.join(' · ');
      if(state.kind==='win'||state.kind==='fail'){
        var displayScore=Number.isFinite(state.levelScore)&&state.levelScore>=0?state.levelScore:state.score;
        score.textContent=Number.isFinite(displayScore)&&displayScore>=0?String(Math.floor(displayScore)):'';
        if(score.textContent){var scoreIcon=document.createElement('img');scoreIcon.src='images/ui-star-filled.png';scoreIcon.alt='';score.prepend(scoreIcon);score.setAttribute('aria-label',(Number.isFinite(state.levelScore)?'Level score ':'Total score ')+Math.floor(displayScore));}
      }
      stars.replaceChildren();
      stars.setAttribute('aria-label', '');
      actions.replaceChildren();
      var buttons = state.kind === 'win' ? [['Home','home'],['Next','next']] : [['Home','home'],['Retry','retry']];
      buttons.forEach(function(pair){var button=document.createElement('button');button.type='button';button.className=pair[1];button.setAttribute('aria-label',pair[0]);button.textContent=pair[1]==='home'?'':pair[0].toUpperCase();var handler=options[pair[1]];button.disabled=typeof handler!=='function';button.addEventListener('click',function(){if(typeof handler==='function')handler();});actions.appendChild(button);});
      if(introTimer!==null){clearTimeout(introTimer);introTimer=null;}
      position();root.hidden=false;
      if(state.kind==='win'){
        card.hidden=true;card.style.display='none';encouragement.hidden=false;playConfetti();
        introTimer=setTimeout(function(){introTimer=null;encouragement.hidden=true;confetti.replaceChildren();card.hidden=false;card.style.display='';fitLevelText();if(view&&view.oneConnectUiMotion)view.oneConnectUiMotion.open(root,card);},2100);
      }else{encouragement.hidden=true;card.hidden=false;card.style.display='';fitLevelText();if(view&&view.oneConnectUiMotion)view.oneConnectUiMotion.open(root,card);}
    }
    function hide(done){if(introTimer!==null){clearTimeout(introTimer);introTimer=null;}encouragement.hidden=true;confetti.replaceChildren();card.hidden=false;card.style.display='';if(done&&view&&view.oneConnectUiMotion)view.oneConnectUiMotion.close(root,card,done);else{root.hidden=true;if(done)done();}}
    function destroy(){hide();if(view){view.removeEventListener('resize',position);view.removeEventListener('scroll',position);}root.remove();style.remove();introStyle.remove();}
    return {show:show,hide:hide,destroy:destroy};
  }
  return {create:create};
});
