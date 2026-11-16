/* Adapter for the supplied same-origin CombiMons iframe host. */
(function(){
 'use strict';
 var installed=false,busy=null;
 function host(){try{var p=window.parent;if(!p||p===window||!p.document||!p.document.querySelector('script[src*="/adsdk_1.8.0.0.js"]')||!p.document.getElementById('iframe'))return null;return p;}catch(_){return null;}}
 function request(kind,done){
  var p=host();if(!p||!p.h5sdk||typeof p.h5sdk.adBreak!=='function'||busy){done(false);return false;}
  var name=kind==='reward'?'MIAD':'MIAD_NEXT',token={},previous=p[name],timer=null;busy=token;
  function finish(ok){if(busy!==token)return;busy=null;if(timer!==null)clearTimeout(timer);if(p[name]===token)p[name]=previous;done(ok);}
  token._callback=function(){finish(true);};token._failback=function(){finish(false);};
  try{p[name]=token;timer=setTimeout(function(){finish(false);},180000);p.postMessage(kind,window.location&&window.location.origin&&window.location.origin!=='null'?window.location.origin:'*');return true;}catch(_){finish(false);return false;}
 }
 function install(){
  if(installed||!host()||!window.oneConnectHost||!window.oneConnectToolRewardCandidate)return false;
  // The supplied host already reserves a 50px banner outside the iframe.
  if(window.oneConnectLayoutCandidate&&typeof window.oneConnectLayoutCandidate.configure==='function')window.oneConnectLayoutCandidate.configure({bannerHeight:0});
  window.oneConnectHost.setAdProvider({showAd:function(kind,ok,fail){if(kind!=='Interstitial'){fail('unsupported');return;}request('next',function(success){if(success)ok();else fail('not viewed');});}});
  window.oneConnectToolRewardCandidate.setProvider({show:function(callbacks){request('reward',function(success){if(success){callbacks.earned({verified:true,source:'combi-host-viewed'});callbacks.closed();}else callbacks.error();});if(busy)callbacks.shown();}});
  installed=true;return true;
 }
 window.oneConnectCombiSdkAdapter={install:install};
}());
