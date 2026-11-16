(function () {
  'use strict';
  var done = false, timer, slowPanel = null, visibleWait = 0, lastTick = Date.now();
  function clearSlow() { if (slowPanel) { slowPanel.remove(); slowPanel = null; } }
  function showSlow() {
    if (slowPanel || !document.body) return;
    slowPanel = document.createElement('div'); slowPanel.id = 'startup-slow'; slowPanel.setAttribute('role', 'status');
    slowPanel.style.cssText = 'position:fixed;left:10%;right:10%;bottom:8%;z-index:2147483646;padding:16px;border-radius:18px;background:#1c3473;color:white;text-align:center;font:16px system-ui,sans-serif;box-shadow:0 4px 12px #050a1d';
    var text = document.createElement('p'); text.textContent = 'Still loading. You can wait or retry.';
    var retry = document.createElement('button'); retry.type = 'button'; retry.textContent = 'Retry'; retry.style.cssText = 'margin-top:12px;padding:10px 26px;border:0;border-radius:18px;background:#168fe9;color:white;font-weight:bold'; retry.onclick = function () { location.reload(); };
    slowPanel.appendChild(text); slowPanel.appendChild(retry); document.body.appendChild(slowPanel);
    try { var p = window.parent; if (p && p !== window && p.h5_sdk && typeof p.h5_sdk.showGameLoadingError === 'function') p.h5_sdk.showGameLoadingError(); } catch (_) {}
  }
  function fail(reason) {
    if (done) return;
    done = true; window.oneConnectStartupFailed = true; clearInterval(timer); clearSlow();
    function show() {
      try { var p = window.parent; if (p && p !== window && p.h5_sdk && typeof p.h5_sdk.showGameLoadingError === 'function') p.h5_sdk.showGameLoadingError(); } catch (_) {}
      var screen = document.createElement('div'); screen.setAttribute('role','alert'); screen.id='startup-recovery';
      screen.style.cssText='position:fixed;top:0;right:0;bottom:0;left:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box;background:rgba(10,15,38,.92);font:16px system-ui,sans-serif;color:white;text-align:center';
      var card=document.createElement('div'); card.style.cssText='max-width:320px;padding:24px;border-radius:24px;background:#1c3473;box-shadow:inset 0 2px 12px #6caeff,0 6px 20px #050a1d';
      var message=document.createElement('p'); message.textContent='Unable to load the game. Check your connection and try again.';
      var retry=document.createElement('button'); retry.type='button'; retry.textContent='Retry'; retry.style.cssText='border:0;border-radius:18px;padding:12px 32px;background:#168fe9;color:white;font:600 16px system-ui,sans-serif;box-shadow:inset 0 3px 7px #8edbff,0 4px 0 #1249a0;cursor:pointer';
      retry.addEventListener('click',function(){window.location.reload()}); card.appendChild(message);card.appendChild(retry);screen.appendChild(card);document.body.appendChild(screen);
      if(window.oneConnectHost)window.oneConnectHost.emit('game.loading_error',{reason:reason});
    }
    if(document.body)show();else document.addEventListener('DOMContentLoaded',show,{once:true});
  }
  var requiredScripts=['jquery-3.4.1.min.js','c2runtime.js','html5games/gameapi/v1.js','event-hooks.js','board-error.js','board-hooks.js','round-save-model.js','round-save.js','tutorial-tenth.js','ad-policy.js','host-adapter.js','level-config.js','menu-score-plate.js'];
  window.addEventListener('error',function(e){
    var el=e.target;if(!el||el.tagName!=='SCRIPT'||!el.src)return;
    for(var i=0;i<requiredScripts.length;i++)if(el.src.split('?')[0]===new URL(requiredScripts[i],location.href).href){fail('script_failed');break}
  },true);
  var open=XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open=function(method,url){
    try { if(new URL(url,location.href).href.split('?')[0]===new URL('data.js',location.href).href) {
      this.addEventListener('error',function(){fail('data_failed')});
      this.addEventListener('load',function(event){
        var data = null;
        try { data = this.responseType === 'json' ? this.response : JSON.parse(this.responseText); } catch (_) {}
        if (this.status >= 400 || !data || !Array.isArray(data.project) || !data.project.length) {
          event.stopImmediatePropagation(); fail('data_invalid');
        }
      });
    }}catch(_){}
    return open.apply(this,arguments);
  };
  timer=setInterval(function(){
    var now = Date.now(); if (!document.hidden) visibleWait += Math.min(now-lastTick,1000); lastTick = now;
    var rt=window.cr_getC2Runtime&&window.cr_getC2Runtime();
    if(rt && rt.running_layout){done=true;clearInterval(timer);clearSlow();return}
    if(visibleWait >= 45000)showSlow();
    if(!rt)return;
    var bad=rt.wait_for_textures&&rt.wait_for_textures.filter(function(img){return img.c2error});
    if(bad&&bad.length)fail('asset_failed');
  },250);
}());
