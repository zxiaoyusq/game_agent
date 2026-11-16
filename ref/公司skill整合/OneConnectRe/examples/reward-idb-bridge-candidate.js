/* Isolated wiring experiment. The provider must authenticate transaction IDs. */
(function(root){
 'use strict';
 function create(ledger){
  if(!ledger||typeof ledger.grant!=='function')throw Error('transactional ledger required');
  return function(_claim,proof){
   if(!proof||proof.verified!==true||typeof proof.transactionId!=='string'||!proof.transactionId.trim()||proof.transactionId.length>128)return false;
   return Promise.resolve(ledger.grant(proof.transactionId)).then(function(result){return result==='granted'||result==='already_claimed';});
  };
 }
 root.oneConnectRewardIDBBridgeExperiment={create:create};
})(typeof window!=='undefined'?window:globalThis);
