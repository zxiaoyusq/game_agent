(function () {
  'use strict';
  // Stop on board or gravity errors rather than allowing a mismatched game to continue.
  window.addEventListener('oneconnect:event', function (event) {
    if (!event.detail || ['config.board_error','config.gravity_error'].indexOf(event.detail.type) === -1 || document.getElementById('board-error-recovery')) return;
    var screen=document.createElement('div');screen.id='board-error-recovery';screen.setAttribute('role','alert');
    screen.style.cssText='position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box;background:rgba(10,15,38,.8);font:16px system-ui,sans-serif;color:white;text-align:center';
    var card=document.createElement('div');card.style.cssText='box-sizing:border-box;width:min(360px,92vw);padding:24px 18px;border:24px solid transparent;border-image:url("images/ui-dialog-panel.webp") 22% fill / 24px stretch;color:white';
    var warning=document.createElement('img');warning.src='images/warning-icon.webp';warning.alt='';warning.setAttribute('aria-hidden','true');warning.style.cssText='display:block;margin:0 auto;width:min(210px,75%);height:auto';card.appendChild(warning);
    var message=document.createElement('p');message.textContent='LEVEL UNAVAILABLE';message.style.cssText='margin:16px 0 20px;font:bold clamp(16px,5vw,22px) system-ui,sans-serif;white-space:nowrap';
    var home=document.createElement('button');home.type='button';home.textContent='HOME';home.style.cssText='min-width:180px;padding:10px 25px;border:16px solid transparent;border-image:url("images/ui-blue-button.webp") 35% fill / 16px stretch;background:none;color:white;font:bold 22px system-ui,sans-serif;cursor:pointer';
    home.addEventListener('click',function(){if(window.oneConnectUiMotion)window.oneConnectUiMotion.close(screen,card,function(){window.location.reload()});else window.location.reload();});card.appendChild(message);card.appendChild(home);screen.appendChild(card);document.body.appendChild(screen);
    if(window.oneConnectUiMotion)window.oneConnectUiMotion.open(screen,card);
    // Defer until Construct finishes the current synchronous event action.
    window.setTimeout(function(){if(typeof window.cr_setSuspended==='function')window.cr_setSuspended(true)},0);
  });
}());
