/* Shared popup motion; the underlying input remains blocked during exit. */
(function(){'use strict';
 var active=new WeakMap();
 function cancel(el){var a=active.get(el);if(a){active.delete(el);if(a._timer!==undefined&&window.clearTimeout)window.clearTimeout(a._timer);if(a.cancel)a.cancel();}}
 function reduced(){return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;}
 function open(el,target){cancel(el);el.hidden=false;if(!target||typeof target.animate!=='function'||reduced())return;try{var a=target.animate([{transform:'scale(.84)',opacity:0},{transform:'scale(1)',opacity:1}],{duration:200,easing:'ease-out'});active.set(el,a);a.onfinish=function(){if(active.get(el)===a)active.delete(el);};}catch(_){}}
 function close(el,target,done){var previous=active.get(el);if(previous&&previous._ocClosing)return;cancel(el);function finish(){el.hidden=true;if(done)done();}if(!target||typeof target.animate!=='function'||reduced()){finish();return;}try{var a=target.animate([{transform:'scale(1)',opacity:1},{transform:'scale(.84)',opacity:0}],{duration:160,easing:'ease-in',fill:'forwards'});a._ocClosing=true;active.set(el,a);a.onfinish=function(){if(active.get(el)!==a)return;active.delete(el);if(a._timer!==undefined&&window.clearTimeout)window.clearTimeout(a._timer);el.hidden=true;if(a.cancel)a.cancel();if(done)done();};if(window.setTimeout)a._timer=window.setTimeout(a.onfinish,400);}catch(_){finish();}}
 window.oneConnectUiMotion={open:open,close:close};
}());
