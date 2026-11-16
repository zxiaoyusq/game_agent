(function(){
 'use strict';
 if(!('serviceWorker' in navigator)||!(location.protocol==='https:'||location.hostname==='127.0.0.1'||location.hostname==='localhost'))return;
 var notice=document.createElement('div'),waiting=false,checking=false;
 notice.id='oc-offline-update';notice.setAttribute('role','status');notice.textContent='Update ready. Close and reopen the game to apply it.';
 notice.style.cssText='display:none;position:fixed;top:4%;left:50%;transform:translateX(-50%);z-index:25;max-width:85%;padding:8px 14px;border-radius:18px;background:#183b82;color:#fff;font:bold 14px sans-serif;text-align:center;box-shadow:0 2px 8px #081331;pointer-events:none';document.body.appendChild(notice);
 function render(){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),display=waiting&&r&&r.running_layout&&r.running_layout.name==='menu'?'block':'none';if(notice.style.display!==display)notice.style.display=display;}
 if(window.addEventListener)window.addEventListener('oneconnect:event',function(e){var type=e.detail&&e.detail.type;if(type==='game.level_start'||type==='game.board_configured'||type==='game.round_ready')notice.style.display='none';else if(type==='screen.SCREEN_HOME')render();});
 setInterval(function(){render();if(checking)return;checking=true;navigator.serviceWorker.getRegistration(new URL('./',location.href).href).then(function(r){waiting=!!(r&&r.active&&r.active.scriptURL===new URL('./offline-worker.js',location.href).href&&r.waiting)}).catch(function(){waiting=false}).then(function(){checking=false;render()})},1000);
}());
