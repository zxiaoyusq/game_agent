(function(){
 'use strict';
 function create(options){options=options||{};return window.oneConnectRewardLifecycle.create({
  loadTimeoutMs:options.loadTimeoutMs,maxShowingMs:options.maxShowingMs,
  isClaimed:function(claim){return window.oneConnectHammerStock.has(claim);},
  grant:function(claim){var r=window.cr_getC2Runtime&&window.cr_getC2Runtime();if(!r||!r.running_layout||r.running_layout.name!=='game')return false;return window.oneConnectHammerStock.grant(claim)==='granted';}
 });}
 window.oneConnectLocalHammerExample={create:create};
}());
