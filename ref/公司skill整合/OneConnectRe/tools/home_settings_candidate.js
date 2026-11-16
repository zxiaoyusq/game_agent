/* Independent UI candidate. Audio calls the existing GameSnacks adapter. */
(function () {
  'use strict';
  var launcher, overlay, sound, vibration, installed = false, lastFocus = null;
  function runtime() { return window.cr_getC2Runtime && window.cr_getC2Runtime(); }
  function menuVisible() { var r = runtime(); return !!(r && r.running_layout && r.running_layout.name === 'menu'); }
  function api() { var a = window.GAMESNACKS; return a && typeof a.isAudioEnabled === 'function' && typeof a.handleAudioUpdates === 'function' ? a : null; }
  function audioEnabled(adapter) {
    var r=runtime(), v=r&&r.all_global_vars&&r.all_global_vars.find(function(item){return item.name==='sound';});
    // The original C2 sound variable is 0 when audible and 1 when muted.
    return v && (v.data===0 || v.data===1) ? v.data===0 : adapter.isAudioEnabled();
  }
  function refresh() {
    var adapter = api();
    sound.disabled = !adapter;
    var enabled=adapter&&audioEnabled(adapter);
    sound.querySelector('.state').textContent = adapter ? (enabled ? 'ON' : 'OFF') : '—';
    sound.classList.toggle('off', !enabled);
    sound.setAttribute('aria-pressed', enabled ? 'true' : 'false');
    var h=window.oneConnectHapticsCandidate, supported=!!(h&&h.supported()), vib=!!(h&&h.enabled());
    vibration.disabled=!supported;
    vibration.title=supported?'':'Vibration unavailable on this device';
    vibration.querySelector('.state').textContent=supported?(vib?'ON':'OFF'):'—';
    vibration.classList.toggle('off',!supported||!vib);
    vibration.setAttribute('aria-pressed',supported&&vib?'true':'false');
  }
  function close() { var done=function(){if(lastFocus&&lastFocus.focus)lastFocus.focus();};if(window.oneConnectUiMotion)window.oneConnectUiMotion.close(overlay,overlay.firstElementChild,done);else{overlay.hidden=true;done();} }
  function install() {
    if (installed) return;
    installed = true;
    var style = document.createElement('style');
    style.textContent = '#oc-home-settings-launch{position:fixed;top:max(12px,env(safe-area-inset-top));right:max(12px,env(safe-area-inset-right));z-index:24;width:48px;height:48px;border:0;background:transparent url("images/ui-settings-button.png") center/contain no-repeat;touch-action:manipulation}#oc-home-settings[hidden]{display:none!important}#oc-home-settings{position:fixed;inset:0;z-index:40;display:grid;place-items:center;background:rgba(3,8,24,.74);padding:12px}#oc-home-settings .panel{box-sizing:border-box;width:min(320px,95%,calc((100vh - 48px)*.77));aspect-ratio:463/600;display:flex;flex-direction:column;justify-content:center;padding:clamp(24px,7vw,38px);border:28px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% 22% fill / 28px stretch;text-align:center;color:white;font-family:sans-serif}#oc-home-settings h2{margin:0 0 18px;font-size:24px}#oc-home-settings .control{display:block;width:100%;min-height:50px;padding:12px;border:0;background:transparent url("images/ui-blue-button.png") center/100% 100% no-repeat;color:white;font:bold 17px sans-serif;touch-action:manipulation}#oc-home-settings .close{margin-top:12px}';
    // Self-designed feedback pending the reference animation evidence.
    style.textContent += '@keyframes oc-settings-enter{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}#oc-home-settings:not([hidden]) .panel{animation:oc-settings-enter .18s ease-out}#oc-home-settings .control:active,#oc-home-settings-launch:active{transform:scale(.96)}@media(prefers-reduced-motion:reduce){#oc-home-settings:not([hidden]) .panel{animation:none}#oc-home-settings .control:active,#oc-home-settings-launch:active{transform:none}}';
    style.textContent += '#oc-home-settings .panel{width:min(380px,96%,calc((100vh - 40px)*.76));aspect-ratio:463/600;padding:4% 5%;justify-content:space-evenly}#oc-home-settings .heading{position:relative;width:100%;height:22%;display:grid;place-items:center;background:url("images/ui-victory-rays.webp") center/contain no-repeat}#oc-home-settings .heading img{width:94%;height:70%;object-fit:contain}#oc-home-settings .control{position:relative;min-height:0;height:15%;display:grid;grid-template-columns:22% 1fr 23%;align-items:center;gap:1%;padding:1% 4%;background:none;border:18px solid transparent;border-image:url("images/ui-blue-button.webp") 45% 20% fill / 18px stretch;text-align:left;font-size:clamp(11px,4vw,18px);white-space:nowrap}#oc-home-settings .control .icon{width:100%;height:100%;object-fit:contain}#oc-home-settings .control .state{height:80%;display:grid;place-items:center;background:url("images/settings-toggle_on.png") center/contain no-repeat;font-size:.65em;padding-right:28%}#oc-home-settings .control.off .state{background-image:url("images/settings-toggle_off.png");padding-right:0;padding-left:28%}#oc-home-settings .control .arrow{width:100%;height:80%;object-fit:contain}#oc-home-settings .close{display:block;height:14%;margin:0;text-align:center;font-size:clamp(16px,5vw,24px)}';
    style.textContent += '#oc-home-settings .control{box-sizing:border-box}';
    // Position each child against the button itself: native button contents
    // are not consistently laid out as CSS grid in embedded WebViews.
    style.textContent += '#oc-home-settings .heading img{width:100%;height:100%}#oc-home-settings .control:not(.close)>.icon{position:absolute;left:5%;top:50%;width:17%;height:68%;transform:translateY(-50%)}#oc-home-settings .control:not(.close)>span:not(.state){position:absolute;left:28%;top:50%;transform:translateY(-50%);line-height:1}#oc-home-settings .control:not(.close)>.state,#oc-home-settings .control:not(.close)>.arrow{position:absolute;right:5%;top:50%;width:22%;height:72%;transform:translateY(-50%);box-sizing:border-box}#oc-home-settings .control:not(.close)>.state{padding-right:5%;padding-left:0}#oc-home-settings .control.off:not(.close)>.state{padding-left:5%;padding-right:0}#oc-home-settings .close-label{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);line-height:1}';
    // Keep the nine-slice artwork out of the button's content box so child
    // percentages are based on the full button rather than its inset centre.
    style.textContent += '#oc-home-settings .control{border:0;padding:0;isolation:isolate}#oc-home-settings .control::before{content:"";position:absolute;inset:0;z-index:-1;box-sizing:border-box;border:18px solid transparent;border-image:url("images/ui-blue-button.webp") 45% 20% fill / 18px stretch;pointer-events:none}#oc-home-settings .control:not(.close)>.icon{width:20%;height:86%}#oc-home-settings .control:not(.close)>.state,#oc-home-settings .control:not(.close)>.arrow{width:26%;height:82%}';
    // Place the approved layout against the complete panel, not the inset
    // interior of its nine-slice border. Keep controls separately interactive.
    style.textContent += '#oc-home-settings .panel{position:relative;display:block;padding:0;border:0;isolation:isolate;container-type:inline-size}#oc-home-settings .panel::before{content:"";position:absolute;inset:0;z-index:-2;box-sizing:border-box;border:28px solid transparent;border-image:url("images/ui-dialog-panel.png") 22% fill / 28px stretch;pointer-events:none}#oc-home-settings .heading{position:absolute;left:10%;top:8%;width:80%;height:13%}#oc-home-settings .control{position:absolute;left:5%;width:90%;height:16%;font-size:clamp(14px,5vw,22px);font-size:5.8cqw}#oc-home-settings .control:nth-child(2){top:23%}#oc-home-settings .control:nth-child(3){top:42%}#oc-home-settings .control:nth-child(4){top:61%}#oc-home-settings .close{left:11%;top:81%;width:78%;height:13%;font-size:clamp(18px,6vw,28px);font-size:7.2cqw}';
    document.head.appendChild(style);
    launcher = document.createElement('button'); launcher.id = 'oc-home-settings-launch'; launcher.type = 'button'; launcher.setAttribute('aria-label','Settings');
    overlay = document.createElement('div'); overlay.id = 'oc-home-settings'; overlay.hidden = true; overlay.setAttribute('role','dialog'); overlay.setAttribute('aria-modal','true'); overlay.setAttribute('aria-label','Settings');
    var panel = document.createElement('div'); panel.className = 'panel';
    var heading = document.createElement('div'); heading.className='heading';
    var titleImage=document.createElement('img');titleImage.src='images/settings-title_word_settings_en.png';titleImage.alt='Settings';heading.appendChild(titleImage);
    var iconPaths={sound:'images/settings-icon_sound.png',help:'images/settings-icon_help.png',vibration:'images/settings-icon_vibration.png'};
    function row(label,icon,help){var button=document.createElement('button');button.type='button';button.className='control';button.setAttribute('aria-label',label);var img=document.createElement('img');img.className='icon';img.src=iconPaths[icon];img.alt='';var text=document.createElement('span');text.textContent=label;var end=document.createElement(help?'img':'span');end.className=help?'arrow':'state';if(help){end.src='images/settings-chevron_right.png';end.alt='';}button.append(img,text,end);return button;}
    sound=row('SOUND','sound',false);sound.addEventListener('click', function () { var adapter = api(); if (!adapter) return; var enabled=!audioEnabled(adapter);adapter.handleAudioUpdates({isAudioEnabled:enabled});var r=runtime(),v=r&&r.all_global_vars&&r.all_global_vars.find(function(item){return item.name==='sound';}),target=enabled?0:1;if(adapter.isAudioEnabled()===enabled&&v&&(v.data===0||v.data===1)&&v.data!==target&&typeof window.c2_callFunction==='function'){v.data=target;window.c2_callFunction('volumeChanged');}refresh(); });
    var help=row('HOW TO PLAY','help',true);help.addEventListener('click',function(){var view=window.oneConnectHowToPlayCandidate;if(view)view.open();});
    vibration=row('VIBRATION','vibration',false);vibration.addEventListener('click',function(){var h=window.oneConnectHapticsCandidate;if(!h)return;h.setEnabled(!h.enabled());if(h.enabled())h.pulse(25);refresh();});
    var done = document.createElement('button'); done.type = 'button'; done.className = 'control close'; var closeLabel=document.createElement('span');closeLabel.className='close-label';closeLabel.textContent='CLOSE';done.appendChild(closeLabel);done.addEventListener('click', close);
    panel.append(heading, sound, help, vibration, done); overlay.appendChild(panel); document.body.append(launcher, overlay);
    // Construct 2 also registers mouse input on document, even when pointer
    // events are enabled. Stop compatibility mouse events at the overlay too.
    ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click'].forEach(function (name) {
      overlay.addEventListener(name, function (event) { event.stopPropagation(); });
      launcher.addEventListener(name, function (event) { event.stopPropagation(); });
    });
    var touch=window.cr&&window.cr.plugins_&&window.cr.plugins_.Touch&&window.cr.plugins_.Touch.prototype.cnds;
    if(touch)['OnTouchObject','OnTouchStart','OnTouchEnd','OnTapGesture','OnTapGestureObject','OnDoubleTapGesture','OnDoubleTapGestureObject'].forEach(function(name){
      var previousTouch=touch[name];if(typeof previousTouch!=='function')return;
      touch[name]=function(){var result=previousTouch.apply(this,arguments),help=window.oneConnectHowToPlayCandidate;return !overlay.hidden||(help&&help.isOpen&&help.isOpen())?false:result;};
    });
    launcher.addEventListener('click', function () { if (!menuVisible()) return; lastFocus = document.activeElement; refresh(); if(window.oneConnectUiMotion)window.oneConnectUiMotion.open(overlay,overlay.firstElementChild);else overlay.hidden = false; done.focus(); });
    overlay.addEventListener('click', function (event) { if (event.target === overlay) close(); });
    var audioApi=api();if(audioApi&&typeof audioApi.subscribeToAudioUpdates==='function')audioApi.subscribeToAudioUpdates(function(){if(!overlay.hidden)requestAnimationFrame(function(){if(!overlay.hidden)refresh();});});
    document.addEventListener('keydown', function (event) {
      var help = window.oneConnectHowToPlayCandidate;
      if (event.key === 'Escape' && !overlay.hidden && !(help && help.isOpen())) close();
    });
    function update() {
      var r = runtime(), visible = !!(r && r.running_layout && r.running_layout.name === 'menu' && r.canvas);
      if (visible) {
        var rect = r.canvas.getBoundingClientRect();
        var left = Math.max(0, rect.left), top = Math.max(0, rect.top);
        var right = Math.min(window.innerWidth, rect.right), bottom = Math.min(window.innerHeight, rect.bottom);
        visible = right - left >= 60 && bottom - top >= 60;
        if (visible) {
          var buttonLeft=Math.max(left,right-60)+'px',buttonTop=(top+12)+'px';
          if(launcher.style.left!==buttonLeft)launcher.style.left=buttonLeft;
          if(launcher.style.top!==buttonTop)launcher.style.top=buttonTop;
          if(launcher.style.right!=='auto')launcher.style.right='auto';
          var bounds = 'box-sizing:border-box;inset:auto;left:' + left + 'px;top:' + top +
            'px;width:' + (right-left) + 'px;height:' + (bottom-top) + 'px';
          if (overlay.dataset.canvasBounds !== bounds) {
            overlay.style.cssText = bounds;
            overlay.dataset.canvasBounds = bounds;
          }
        }
      }
      if(launcher.hidden===visible)launcher.hidden=!visible;
      if (!visible && !overlay.hidden) close();
      requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }
  window.oneConnectHomeSettingsCandidate = {install:install};
})();
