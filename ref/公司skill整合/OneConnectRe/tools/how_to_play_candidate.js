/* Reuses the original in-game tutorial artwork in the settings flow. */
(function () {
  'use strict';
  var overlay = null, closeButton = null, previousFocus = null;
  function close() {
    if (!overlay || overlay.hidden) return;
    var done=function(){if(previousFocus&&typeof previousFocus.focus==='function')previousFocus.focus();};
    if(window.oneConnectUiMotion)window.oneConnectUiMotion.close(overlay,overlay.firstElementChild,done);else{overlay.hidden=true;done();}
  }
  function install() {
    if (overlay) return;
    var style=document.createElement('style');
    style.textContent='#oc-how-to-play[hidden]{display:none!important}#oc-how-to-play{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(3,8,24,.76);padding:16px;box-sizing:border-box}#oc-how-to-play .art{position:relative;width:min(455px,92vw,calc((100vh - 32px)*455/515));aspect-ratio:455/515}#oc-how-to-play img{display:block;width:100%;height:100%;object-fit:contain}#oc-how-to-play button{position:absolute;right:7%;top:5%;width:18%;height:15%;border:0;background:transparent;cursor:pointer}';
    document.head.appendChild(style);
    overlay=document.createElement('div');overlay.id='oc-how-to-play';overlay.hidden=true;
    overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','How to play');
    var art=document.createElement('div');art.className='art';
    var image=document.createElement('img');image.src='images/tutorial-sheet0.webp';image.alt='Match identical tiles using a path with at most two turns.';
    closeButton=document.createElement('button');closeButton.type='button';closeButton.setAttribute('aria-label','Close how to play');closeButton.addEventListener('click',close);
    art.append(image,closeButton);overlay.appendChild(art);document.body.appendChild(overlay);
    ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click'].forEach(function(name){overlay.addEventListener(name,function(event){event.stopPropagation();});});
    overlay.addEventListener('click',function(event){if(event.target===overlay)close();});
    document.addEventListener('keydown',function(event){if(event.key==='Escape'&&!overlay.hidden){event.stopPropagation();close();}});
  }
  function open() {
    install();previousFocus=document.activeElement;if(window.oneConnectUiMotion)window.oneConnectUiMotion.open(overlay,overlay.firstElementChild);else overlay.hidden=false;closeButton.focus();
  }
  window.oneConnectHowToPlayCandidate={install:install,open:open,close:close,isOpen:function(){return !!(overlay&&!overlay.hidden);}};
}());
