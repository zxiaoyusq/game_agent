(function(){
  'use strict';
  var key='oneconnect.tutorial7.v1',active=false,installed=false,overlay;
  function done(){try{return localStorage.getItem(key)==='done';}catch(_){return false;}}
  function finish(){if(!active)return;active=false;overlay.style.display='none';try{localStorage.setItem(key,'done');}catch(_){}window.oneConnectHost.emit('tutorial.complete',{level:7});}
  function frame(){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),pause=r&&r.all_global_vars.find(function(v){return v.name==='pause';});overlay.style.display=active&&r&&r.running_layout&&r.running_layout.name==='game'&&!(pause&&pause.data)?'flex':'none';window.requestAnimationFrame(frame);}
  function install(){if(installed)return;installed=true;
    overlay=document.createElement('div');overlay.id='oc-seventh-guide';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','Hammer tutorial');overlay.style.cssText='display:none;position:fixed;inset:0;z-index:35;align-items:center;justify-content:center;background:rgba(4,10,30,.76);padding:20px;box-sizing:border-box';
    var card=document.createElement('div');card.style.cssText='box-sizing:border-box;width:min(380px,92vw);padding:28px 20px 26px;border:24px solid transparent;border-image:url("images/ui-dialog-panel.webp") 22% fill / 24px stretch;text-align:center;color:#fff;font-family:sans-serif';
    var title=document.createElement('div');title.textContent='HAMMER';title.style.cssText='font-size:27px;font-weight:bold;text-shadow:0 3px 4px #10234c';card.appendChild(title);
    var illustration=document.createElement('div');illustration.style.cssText='display:flex;align-items:center;justify-content:center;gap:6px;margin:22px 0 12px';
    var icon=document.querySelector('#oc-hammer svg');if(icon){var copy=icon.cloneNode(true);copy.setAttribute('width','72');copy.setAttribute('height','72');copy.style.cssText='width:35%;height:auto;object-fit:contain';illustration.appendChild(copy);}
    function tile(){var img=document.createElement('img');img.src='images/ui-tutorial-tile.png';img.alt='';img.style.cssText='width:20%;height:auto;object-fit:contain';return img;}
    illustration.appendChild(tile());var line=document.createElement('span');line.style.cssText='width:12%;height:5px;border-radius:4px;background:#ffe35c;box-shadow:0 0 8px #ffcd2b';illustration.appendChild(line);illustration.appendChild(tile());card.appendChild(illustration);
    var text=document.createElement('p');text.textContent='Remove a matching pair!';text.style.cssText='font-size:18px;line-height:1.3;font-weight:bold';card.appendChild(text);
    var button=document.createElement('button');button.id='oc-seventh-continue';button.textContent='GOT IT';button.style.cssText='min-width:180px;padding:10px 22px;border:16px solid transparent;border-image:url("images/ui-blue-button.webp") 35% fill / 16px stretch;background:none;color:#fff;font:bold 22px sans-serif;cursor:pointer';button.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();finish();});card.appendChild(button);overlay.appendChild(card);document.body.appendChild(overlay);
    var previous=cr.action.prototype.run_system;cr.action.prototype.run_system=function(){if(active&&this.sid===367702696840255){var level=this.runtime.all_global_vars.find(function(v){return v.name==='level';});if(level&&level.data===7)return;}return previous.apply(this,arguments);};
    window.addEventListener('oneconnect:event',function(e){var x=e.detail;if(!x)return;if(x.type==='game.board_configured'&&x.detail.level===7&&!done()){active=true;window.oneConnectHost.emit('tutorial.start',{level:7});}else if(x.type==='game.level_fail')active=false;});window.requestAnimationFrame(frame);
  }
  window.oneConnectSeventhGuide={install:install,state:function(){return {active:active};}};
}());
