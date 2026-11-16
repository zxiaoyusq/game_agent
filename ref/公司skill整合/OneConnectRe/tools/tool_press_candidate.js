/* Provisional press feedback. Competitor scale and duration are not known. */
(function(){
 'use strict';var installed=false,pressed=null,pointer=null;
 function release(){if(pressed){pressed.style.transform='';pressed=null;}pointer=null;}
 function install(targets,enabled){if(installed)return;installed=true;
  window.addEventListener('pointerdown',function(e){if(pressed||!enabled()||!Number.isFinite(e.clientX)||!Number.isFinite(e.clientY))return;
   var entries=targets();for(var i=0;i<entries.length;i++){var item=entries[i];if(!item||!item.box||!item.icon||item.box.hidden||item.box.disabled||item.box.style.display==='none')continue;
    var r=item.box.getBoundingClientRect();if(e.clientX>=r.left&&e.clientX<=r.right&&e.clientY>=r.top&&e.clientY<=r.bottom){pressed=item.icon;pointer=e.pointerId;pressed.style.transition='transform .12s ease-out';pressed.style.transform='scale(.92)';break;}}
  },true);
  function finish(e){if(pointer===null||e.pointerId===pointer)release();}
  window.addEventListener('pointerup',finish,true);window.addEventListener('pointercancel',finish,true);window.addEventListener('blur',release);
  document.addEventListener('visibilitychange',function(){if(document.hidden)release();});
  window.addEventListener('oneconnect:event',function(e){var t=e.detail&&e.detail.type;if(t==='game.level_fail'||t==='game.level_win'||t==='game.board_configured'||t==='game.auto_shuffle_start')release();});
 }
 window.oneConnectToolPressCandidate={install:install};
}());
