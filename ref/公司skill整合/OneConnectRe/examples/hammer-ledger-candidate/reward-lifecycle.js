(function(){
 'use strict';
 // The provider must normalize its SDK's callback ordering before invoking this
 // contract. This module does not claim platform verification or durable grants.
 function create(options){
  options=options||{};var provider=null,pending=null,claimed=new Set(),next=0;
  var gate=options.gate||{},grant=options.grant,timeout=options.loadTimeoutMs,showTimeout=options.maxShowingMs;
  if(!Number.isInteger(timeout)||timeout<1||timeout>2147483647)throw Error('positive loading timeout required');
  if(showTimeout!==undefined&&(!Number.isInteger(showTimeout)||showTimeout<1||showTimeout>2147483647))throw Error('invalid showing timeout');
  function setProvider(value){if(value!==null&&(!value||typeof value.show!=='function'))throw Error('invalid reward provider');provider=value;}
  function request(claim){
   if(typeof claim!=='string'||!claim.trim())return Promise.resolve({status:'invalid_claim'});
   try{if(claimed.has(claim)||(typeof options.isClaimed==='function'&&options.isClaimed(claim)))return Promise.resolve({status:'already_claimed'});}catch(_){return Promise.resolve({status:'claim_store_error'});}
   if(pending)return Promise.resolve({status:'busy'});
   if(!provider)return Promise.resolve({status:'unavailable'});
   return new Promise(function(resolve){
    var state={id:++next,claim:claim,done:false,shown:false,rewarded:false,timer:null,ownsPause:false};pending=state;
    function finish(status){if(state.done)return;state.done=true;clearTimeout(state.timer);if(pending===state)pending=null;if(state.ownsPause&&typeof gate.resume==='function'){try{gate.resume(state.id);}catch(_){}}resolve({status:state.rewarded?'rewarded':status,attempt:state.id});}
    var callbacks={
     shown:function(){if(state.done||state.shown)return;state.shown=true;clearTimeout(state.timer);if(showTimeout!==undefined)state.timer=setTimeout(function(){finish('show_timeout');},showTimeout);},
     earned:function(proof){if(state.done||state.rewarded||!proof||proof.verified!==true||typeof grant!=='function')return;try{if(grant(claim,proof,state.id)===true){claimed.add(claim);state.rewarded=true;}}catch(_){}},
     closed:function(){finish('closed');},error:function(){finish('error');},cancelled:function(){finish('cancelled');}
    };
    state.cancel=function(){finish('cancelled');};
    try{if(typeof gate.pause==='function'){gate.pause(state.id);state.ownsPause=true;}state.timer=setTimeout(function(){finish('timeout');},timeout);var result=provider.show(callbacks,state.id);if(result&&typeof result.then==='function')Promise.resolve(result).catch(function(){finish('error');});}catch(_){finish('error');}
   });
  }
  return {setProvider:setProvider,request:request,cancel:function(){if(pending)pending.cancel();},state:function(){return {busy:!!pending};}};
 }
 window.oneConnectRewardLifecycle={create:create};
}());
