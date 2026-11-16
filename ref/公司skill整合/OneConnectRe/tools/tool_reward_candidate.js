/* Local candidate: platform must provide verified earned callbacks. */
(function(){
 'use strict';
 var life=null,root=null,icon=null,status=null,watch=null,current=null,sequence=0,dialogVersion=0,installed=false,requestLevel=null,roundEpoch=0,requestEpoch=null,roundEnded=false;
 var inventoryRetries=Object.create(null);
 var icons={hint:'images/gamebuttons-sheet1.webp',shuffle:'images/gamebuttons-sheet0.webp',hammer:'images/hammer-icon.png',theme:'images/replace-theme-icon.png'};
 function runtime(){return window.cr_getC2Runtime&&window.cr_getC2Runtime();}
 function variable(r,n){return r&&r.all_global_vars&&r.all_global_vars.find(function(v){return v.name===n;});}
 function retryInventorySave(inventory,before,kind,level){
  if(inventoryRetries[kind]||!Number.isInteger(before)||typeof inventory.retryRewardSave!=='function')return;
  var attempts=0,revision=typeof inventory.rewardRevision==='function'?inventory.rewardRevision():undefined;
  var job={timer:null};inventoryRetries[kind]=job;
  function retry(){var outcome;try{outcome=inventory.retryRewardSave(before,revision);}catch(_){outcome='retry';}
   if(outcome==='retry'&&++attempts<3){job.timer=setTimeout(retry,5000);return;}
   if(inventoryRetries[kind]===job)delete inventoryRetries[kind];
   if(outcome!=='saved'&&window.oneConnectHost){try{window.oneConnectHost.emit('candidate.reward_save_retry_stopped',{level:level,kind:kind,reason:outcome});}catch(_){}}
  }
  job.timer=setTimeout(retry,5000);
 }
 function grant(claim){
  var kind=claim.split(':')[0],r=runtime(),v;
  var level=variable(r,'level');if(!r||!r.running_layout||r.running_layout.name!=='game'||!level||level.data!==requestLevel||requestEpoch!==roundEpoch)return false;
  if(kind==='hammer'||kind==='theme'){
   var inventory=kind==='hammer'?window.oneConnectHammer:window.oneConnectThemeInventoryCandidate;
   if(!inventory||typeof inventory.credit!=='function')return false;
   var beforeInventory=kind==='hammer'?(inventory.state&&inventory.state().count):(inventory.count&&inventory.count());
   if(!inventory.credit(2))return false;
   if(typeof inventory.rewardPersisted==='function'&&inventory.rewardPersisted()&&inventoryRetries[kind]){clearTimeout(inventoryRetries[kind].timer);delete inventoryRetries[kind];}
   if(typeof inventory.rewardPersisted==='function'&&!inventory.rewardPersisted()&&window.oneConnectHost){
    try{window.oneConnectHost.emit('candidate.reward_save_deferred',{level:level.data,kind:kind});}catch(error){console.warn('Reward save notification failed',error);}
   }
   if(typeof inventory.rewardPersisted==='function'&&!inventory.rewardPersisted())retryInventorySave(inventory,beforeInventory,kind,level.data);
   return true;
  }
  if(kind!=='hint'&&kind!=='shuffle')return false;
  v=variable(r,kind==='hint'?'tip':'shuffle');if(!v||!Number.isInteger(v.data)||v.data<0||v.data>997)return false;
  var before=v.data;v.data+=2;
  // The credit is already applied. Display/save failures must not cause the
  // lifecycle to retry the same reward and credit it a second time.
  try{var uid=kind==='hint'?46:2,role=kind==='hint'?4:3,fonts=r.types.t25&&r.types.t25.instances||[],font=fonts.find(function(x){return x.instance_vars&&x.instance_vars[0]===role;})||fonts.find(function(x){return x.uid===uid&&(!x.instance_vars||x.instance_vars.length===0||x.instance_vars[0]===role);});
   if(font&&window.cr&&cr.plugins_.Spritefont2)cr.plugins_.Spritefont2.prototype.acts.SetText.call(font,String(v.data));
  }catch(error){console.warn('Reward display update failed',error);}
  var save=window.oneConnectRoundSave,saved=false;
  try{saved=!!(save&&save.capture());}catch(error){console.warn('Reward save failed',error);}
  if(!saved&&save&&typeof save.checkpointRewardCounter==='function'){
   try{saved=!!save.checkpointRewardCounter(kind==='hint'?'tip':'shuffle',level.data,before);}catch(error){console.warn('Reward checkpoint failed',error);}
  }
  if(!saved&&window.oneConnectHost){try{window.oneConnectHost.emit('candidate.reward_save_deferred',{level:level.data,kind:kind});}catch(error){console.warn('Reward save notification failed',error);}}
  return true;
 }
 function hide(force){if(!force&&life&&life.state().busy)return;current=null;dialogVersion++;if(!force&&window.oneConnectUiMotion)window.oneConnectUiMotion.close(root,root.firstElementChild);else root.hidden=true;}
 function open(kind){if(roundEnded||!icons[kind]||!root||!root.hidden||(life&&life.state().busy))return false;var r=runtime();if(!r||!r.running_layout||r.running_layout.name!=='game')return false;dialogVersion++;current=kind;icon.src=icons[kind];status.textContent='';watch.disabled=false;if(window.oneConnectUiMotion)window.oneConnectUiMotion.open(root,root.firstElementChild);else root.hidden=false;return true;}
 function install(){
  if(installed)return;installed=true;
  life=window.oneConnectRewardLifecycle.create({loadTimeoutMs:10000,maxShowingMs:180000,grantTimeoutMs:15000,grant:grant});
  var style=document.createElement('style');style.textContent='#oc-tool-reward[hidden]{display:none!important}#oc-tool-reward{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(3,8,24,.52);font-family:sans-serif}#oc-tool-reward .panel{box-sizing:border-box;width:min(320px,85vw);min-height:340px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px;color:white;text-align:center;border:28px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% fill / 28px stretch}#oc-tool-reward img{width:94px;height:94px;object-fit:contain}#oc-tool-reward .qty{font-size:30px;font-weight:bold}#oc-tool-reward button{min-width:155px;min-height:55px;border:0;background:transparent url("images/ui-blue-button.png") center/100% 100% no-repeat;color:white;font:bold 17px sans-serif}#oc-tool-reward .close{min-width:100px;min-height:42px}#oc-tool-reward .status{min-height:22px;font-size:14px}';document.head.appendChild(style);
  root=document.createElement('div');root.id='oc-tool-reward';root.hidden=true;root.setAttribute('role','dialog');root.setAttribute('aria-modal','true');root.setAttribute('aria-label','Watch an ad to receive two tools');
  // Approved title-free composition. The nine-slice panel is a pseudo-element
  // so its border cannot shrink the coordinate space used by the contents.
  style.textContent+='#oc-tool-reward .panel{position:relative;display:block;width:min(440px,90vw,calc((100vh - 32px)*.78));min-height:0;aspect-ratio:.78;padding:0;border:0;isolation:isolate;container-type:inline-size}#oc-tool-reward .panel::before{content:"";position:absolute;inset:0;box-sizing:border-box;border:28px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% fill / 28px stretch;z-index:-2}#oc-tool-reward .panel::after{content:"";position:absolute;left:18%;top:20%;width:64%;height:29%;background:url("images/ui-victory-rays.png") center/contain no-repeat;opacity:.45;pointer-events:none;z-index:-1}#oc-tool-reward .tool-icon{position:absolute;left:24%;top:17%;width:52%;height:34%;object-fit:contain}#oc-tool-reward .qty{position:absolute;left:0;top:49%;width:100%;font-size:clamp(30px,9vw,44px);font-size:10cqw;line-height:1}#oc-tool-reward .watch{position:absolute;left:5%;top:60%;width:90%;height:19%;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center;border:0;background:url("images/ui-victory-next.png") center/100% 100% no-repeat;font-size:clamp(22px,7.2vw,35px);font-size:8cqw;font-weight:900;white-space:nowrap}#oc-tool-reward .watch img{width:19%;height:70%;margin-right:3%}#oc-tool-reward .close{position:absolute;left:25%;top:84%;width:50%;height:11%;min-width:0;min-height:0;font-size:clamp(19px,6.3vw,31px);font-size:7cqw}#oc-tool-reward .status{position:absolute;left:8%;top:79%;width:84%;min-height:0;font-size:clamp(11px,3vw,14px)}';
  style.textContent+='#oc-tool-reward .watch,#oc-tool-reward .close{background:none;isolation:isolate}#oc-tool-reward .watch::before,#oc-tool-reward .close::before{content:"";position:absolute;inset:0;box-sizing:border-box;border:14px solid transparent;z-index:-1;pointer-events:none}#oc-tool-reward .watch::before{border-image:url("images/ui-victory-next.png") 45% 15% fill / 45% 15% stretch}#oc-tool-reward .close::before{border-image:url("images/ui-blue-button.png") 45% 20% fill / 14px stretch}';
  var panel=document.createElement('div');panel.className='panel';icon=document.createElement('img');icon.className='tool-icon';icon.alt='';var qty=document.createElement('div');qty.className='qty';qty.textContent='×2';
  watch=document.createElement('button');watch.type='button';watch.className='watch';var play=document.createElement('img');play.src='images/startbutton-sheet0.webp';play.alt='';play.style.cssText='object-fit:contain';watch.append(play,document.createTextNode('WATCH AD'));status=document.createElement('div');status.className='status';var close=document.createElement('button');close.type='button';close.className='close';close.textContent='CLOSE';close.onclick=function(){hide();};
  watch.onclick=function(){if(!current||life.state().busy)return;var level=variable(runtime(),'level');if(!level)return;requestLevel=level.data;requestEpoch=roundEpoch;
   // Establish a stable, current-round fallback before the ad when possible.
   // Failure must not prevent the provider from returning a verified reward.
   if((current==='hint'||current==='shuffle')&&window.oneConnectRoundSave){try{window.oneConnectRoundSave.capture();}catch(error){console.warn('Pre-ad round save failed',error);}}
   watch.disabled=true;var version=dialogVersion,claim=current+':'+Date.now()+':'+(++sequence);life.request(claim).then(function(result){if(version!==dialogVersion||!current)return;watch.disabled=false;if(result.status==='rewarded'){status.textContent='';hide();}else status.textContent=result.status==='unavailable'?'Ad unavailable':result.status==='grant_pending'?'Reward pending':'No reward received';});};
  panel.append(icon,qty,watch,status,close);root.appendChild(panel);document.body.appendChild(root);['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click'].forEach(function(n){root.addEventListener(n,function(e){e.stopPropagation();});});
  var cond=cr.plugins_.Touch.prototype.cnds,previous=cond.OnTouchObject;cond.OnTouchObject=function(type){
   var ok=previous.apply(this,arguments),r=runtime();if(root&&!root.hidden)return false;if(!ok||!type||type.name!=='t26'||!r)return ok;if(roundEnded)return false;
   var pause=variable(r,'pause');if(!r.running_layout||r.running_layout.name!=='game'||!pause)return ok;if(pause.data!==0)return false;
   var blockingGuides=['oneConnectTutorial','oneConnectSecondGuide','oneConnectThirdGuide','oneConnectSeventhGuide'];if(blockingGuides.some(function(n){var g=window[n];return g&&typeof g.state==='function'&&g.state().active;}))return false;
   var guides=['oneConnectFifthGuide','oneConnectTenthGuide'];if(guides.some(function(n){var g=window[n];return g&&typeof g.state==='function'&&g.state().active;}))return ok;
   var hit=type.getCurrentSol().getObjects();var target=hit.find(function(x){return x.cur_frame===1;})||hit.find(function(x){return x.cur_frame===0;});
   var kind=target&&target.cur_frame===1?'hint':target&&target.cur_frame===0?'shuffle':null;
   var v=kind&&variable(r,kind==='hint'?'tip':'shuffle');if(v&&v.data<=0&&open(kind))return false;return ok;
  };
  ['OnTouchStart','OnTouchEnd','OnTapGesture','OnTapGestureObject','OnDoubleTapGesture','OnDoubleTapGestureObject'].forEach(function(name){var prior=cond[name];if(typeof prior!=='function')return;cond[name]=function(){var ok=prior.apply(this,arguments);return root&&!root.hidden?false:ok;};});
  var old=cr.action.prototype.run_system;cr.action.prototype.run_system=function(){if(root&&!root.hidden&&this.sid===367702696840255)return;return old.apply(this,arguments);};
  window.addEventListener('oneconnect:event',function(e){var type=e.detail&&e.detail.type;if(type==='game.board_configured'||type==='game.round_ready'||type==='game.level_fail'||type==='game.level_win'||type==='screen.SCREEN_BONUS'||type==='screen.SCREEN_HOME'){roundEnded=type!=='game.board_configured'&&type!=='game.round_ready';roundEpoch++;if(life.state().busy)life.cancel();if(root&&!root.hidden)hide(true);}});
 }
 window.oneConnectToolRewardCandidate={install:install,open:open,setProvider:function(provider){if(!life)throw Error('not installed');life.setProvider(provider);},state:function(){return {open:!!root&&!root.hidden,kind:current,busy:!!life&&life.state().busy};}};
}());
