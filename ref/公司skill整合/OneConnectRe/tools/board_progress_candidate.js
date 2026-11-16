/* Candidate player level progress; independent of the current round. Initial
 * level 0 is a project choice, since the competitor initial state is unknown. */
(function(){
 'use strict';
 var key='oneconnect.user-level.candidate.v1',root=null,track=null,crop=null,fill=null,fillArt=null,left=null,right=null,last='',installed=false,unavailable=false,loaded=false;
 // All extracted fallback rows have NeedScore=50. Random reward selection is
 // deliberately not reproduced here: its reward semantics remain unknown.
 var thresholds={1:120,2:50,3:50,4:50,5:50,6:50,7:50,8:50,9:50,10:50};
 function needFor(level){return thresholds[level+1]||(level>=10&&level<100000?50:null);}
 var memory={version:1,level:0,score:0};
 function setStyle(node,name,value){if(node.style[name]!==value)node.style[name]=value;}
 function valid(x){return x&&x.version===1&&Number.isInteger(x.level)&&x.level>=0&&x.level<=100000&&Number.isInteger(x.score)&&x.score>=0&&x.score<=1000000;}
 function load(){if(unavailable)return null;if(loaded)return memory;try{var raw=localStorage.getItem(key);if(raw!==null){var parsed=JSON.parse(raw);if(!valid(parsed))throw Error('invalid player level data');memory=parsed;}else memory={version:1,level:0,score:0};loaded=true;}catch(error){unavailable=true;return null;}return memory;}
 function match(){var data=load();if(!data)return;var threshold=needFor(data.level);if(!threshold)return;var next={version:1,level:data.level,score:data.score+1};if(next.score>=threshold){next.level++;next.score=0;}try{localStorage.setItem(key,JSON.stringify(next));memory=next;last='';}catch(error){unavailable=true;}}
 function install(){
  if(installed)return;installed=true;
  root=document.createElement('div');root.setAttribute('role','progressbar');root.setAttribute('aria-label','Player level progress');root.style.cssText='display:none;position:fixed;z-index:18;pointer-events:none';
  track=document.createElement('div');track.style.cssText='position:absolute;inset:0;box-sizing:border-box;border:8px solid transparent;border-image:url("images/ui-progress-track.png") 45% 8% fill / 8px stretch';
  crop=document.createElement('div');crop.style.cssText='position:absolute;left:3%;top:24%;width:94%;height:52%;overflow:hidden';fill=document.createElement('div');fill.style.cssText='position:relative;width:0;height:100%;overflow:hidden;border-radius:999px;transition:width .2s ease-out';fillArt=document.createElement('div');fillArt.style.cssText='position:absolute;left:0;top:0;height:100%;background:url("images/ui-progress-fill.png") left center/100% 100% no-repeat';fill.appendChild(fillArt);crop.appendChild(fill);
  left=document.createElement('span');right=document.createElement('span');left.style.cssText='position:absolute;right:100%;top:50%;transform:translateY(-50%);color:white;font:bold clamp(12px,3vw,18px) sans-serif;text-shadow:0 1px 3px #06112f';right.style.cssText='position:absolute;left:100%;top:50%;transform:translateY(-50%);color:white;font:bold clamp(12px,3vw,18px) sans-serif;text-shadow:0 1px 3px #06112f';root.append(track,crop,left,right);document.body.appendChild(root);
  function retryUnavailable(){if(unavailable){loaded=false;unavailable=false;last='';}}
  window.addEventListener('oneconnect:event',function(e){var d=e.detail;if(d&&d.type==='game.board_configured')retryUnavailable();if(d&&d.type==='game.match')match();});
  window.addEventListener('visibilitychange',function(){if(document.visibilityState==='visible')retryUnavailable();});
  window.addEventListener('storage',function(e){if(e.key===key||e.key===null){loaded=false;unavailable=false;last='';}});
 }
 function update(r,area){
  if(!installed)install();if(!r||!r.running_layout||r.running_layout.name!=='game'||!area){setStyle(root,'display','none');return;}
  var data=load(),need=data&&needFor(data.level),levelAvailable=!!(!unavailable&&data&&need);
  setStyle(root,'left',area.left+'px');setStyle(root,'top',area.top+'px');setStyle(root,'width',area.width+'px');setStyle(root,'height',area.height+'px');setStyle(root,'display','block');setStyle(fillArt,'width',(area.width*.94)+'px');
  [track,crop,left,right].forEach(function(node){setStyle(node,'visibility',levelAvailable?'visible':'hidden');});
  if(!levelAvailable){last='';root.setAttribute('aria-label','Player level progress unavailable');root.removeAttribute('aria-valuemin');root.removeAttribute('aria-valuemax');root.removeAttribute('aria-valuenow');}
  if(levelAvailable){var value=data.level+':'+data.score;if(value!==last){last=value;var fraction=Math.max(0,Math.min(1,data.score/need));fill.style.width=(fraction*100)+'%';fill.style.visibility=fraction>0?'visible':'hidden';left.textContent=String(data.level);right.textContent=String(data.level+1);root.setAttribute('aria-label','Player level progress');root.setAttribute('aria-valuemin','0');root.setAttribute('aria-valuemax',String(need));root.setAttribute('aria-valuenow',String(data.score));}}
 }
 window.oneConnectBoardProgressCandidate={update:update};
}());
