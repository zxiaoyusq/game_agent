/* Explicit local simulation only; never load this in a release build. */
(function(){
 'use strict';
 window.oneConnectToolRewardMock={
  enable:function(outcome){
   if(['rewarded','closed','error'].indexOf(outcome)<0)throw Error('unknown mock outcome');
   window.oneConnectToolRewardCandidate.setProvider({show:function(callbacks){
    callbacks.shown();setTimeout(function(){if(outcome==='rewarded'){callbacks.earned({verified:true});callbacks.closed();}else if(outcome==='closed')callbacks.closed();else callbacks.error();},200);
   }});
  },
  disable:function(){window.oneConnectToolRewardCandidate.setProvider(null);}
 };
}());
