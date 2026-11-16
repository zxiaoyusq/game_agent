(function(){
 'use strict';
 // The provider must normalize its SDK's callback ordering before invoking this
 // contract. This module does not claim platform verification or durable grants.
 function create(options){
  options=options||{};var provider=null,pending=null,claimed=new Set(),inflight=new Set(),next=0;
  var gate=options.gate||{},grant=options.grant,timeout=options.loadTimeoutMs,showTimeout=options.maxShowingMs,grantTimeout=options.grantTimeoutMs;
  if((typeof gate.pause==='function')!==(typeof gate.resume==='function'))throw Error('pause and resume must be provided together');
  if(!Number.isInteger(timeout)||timeout<1||timeout>2147483647)throw Error('positive loading timeout required');
  if(showTimeout!==undefined&&(!Number.isInteger(showTimeout)||showTimeout<1||showTimeout>2147483647))throw Error('invalid showing timeout');
  if(grantTimeout!==undefined&&(!Number.isInteger(grantTimeout)||grantTimeout<1||grantTimeout>2147483647))throw Error('invalid grant timeout');
  function setProvider(value){if(value!==null&&(!value||typeof value.show!=='function'))throw Error('invalid reward provider');provider=value;}
  function request(claim){
   if(typeof claim!=='string'||!claim.trim())return Promise.resolve({status:'invalid_claim'});
   if(claimed.has(claim))return Promise.resolve({status:'already_claimed'});
   if(inflight.has(claim))return Promise.resolve({status:'grant_pending'});
   if(pending)return Promise.resolve({status:'busy'});
   if(inflight.size)return Promise.resolve({status:'grant_pending'});
   if(!provider)return Promise.resolve({status:'unavailable'});
   return new Promise(function(resolve){
    var state={id:++next,claim:claim,done:false,shown:false,rewarded:false,granting:false,grantAttempted:false,finishAfterGrant:null,timer:null,grantTimer:null,ownsPause:false};pending=state;
    function finish(status){if(state.done)return;if(state.granting){if(state.finishAfterGrant===null)state.finishAfterGrant=status;return;}state.done=true;clearTimeout(state.timer);clearTimeout(state.grantTimer);if(pending===state)pending=null;if(state.ownsPause&&typeof gate.resume==='function'){try{gate.resume(state.id);}catch(_){}}resolve({status:state.rewarded?'rewarded':status,attempt:state.id});}
    var callbacks={
     shown:function(){if(state.done||state.shown)return;state.shown=true;clearTimeout(state.timer);if(showTimeout!==undefined)state.timer=setTimeout(function(){finish('show_timeout');},showTimeout);},
     earned:function(proof){if(state.done||state.rewarded||state.grantAttempted||!proof||proof.verified!==true||typeof grant!=='function')return;state.grantAttempted=true;state.granting=true;inflight.add(claim);
      function settled(success){clearTimeout(state.grantTimer);inflight.delete(claim);if(success===true){claimed.add(claim);state.rewarded=true;}state.granting=false;if(!state.done&&state.finishAfterGrant!==null)finish(state.finishAfterGrant);}
      try{var result=grant(claim,proof,state.id);if(result&&typeof result.then==='function'){if(grantTimeout!==undefined)state.grantTimer=setTimeout(function(){state.granting=false;finish('grant_pending');},grantTimeout);Promise.resolve(result).then(settled,function(){settled(false);});}else settled(result);}catch(_){settled(false);}},
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
