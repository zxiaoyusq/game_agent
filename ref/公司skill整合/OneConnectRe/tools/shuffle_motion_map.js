/* Deterministic visual correspondence; never modifies game state. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.oneConnectShuffleMotionMap=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 function map(before,after){
  if(!Array.isArray(before)||!Array.isArray(after)||before.length!==after.length)return null;
  function valid(item){return item&&Number.isInteger(item.uid)&&Number.isInteger(item.kind)&&item.kind>=0&&Number.isFinite(item.x)&&Number.isFinite(item.y);}
  if(!before.every(valid)||!after.every(valid)||new Set(before.map(x=>x.uid)).size!==before.length||new Set(after.map(x=>x.uid)).size!==after.length)return null;
  const groups=new Map();
  before.forEach(function(item){if(!groups.has(item.kind))groups.set(item.kind,[]);groups.get(item.kind).push(item);});
  const matches=new Map();
  // Reserve unchanged identities first so earlier destinations cannot steal them.
  for(const dest of after){const available=groups.get(dest.kind);if(!available)return null;const i=available.findIndex(item=>item.uid===dest.uid);if(i>=0)matches.set(dest.uid,available.splice(i,1)[0]);}
  const moves=[];
  for(const dest of after){let source=matches.get(dest.uid);if(!source){const available=groups.get(dest.kind);if(!available||!available.length)return null;
   let index=0;for(let i=1;i<available.length;i++){let a=available[i],b=available[index],da=(a.x-dest.x)**2+(a.y-dest.y)**2,db=(b.x-dest.x)**2+(b.y-dest.y)**2;if(da<db||(da===db&&a.uid<b.uid))index=i;}
   source=available.splice(index,1)[0];}
   moves.push({kind:dest.kind,sourceUid:source.uid,targetUid:dest.uid,fromX:source.x,fromY:source.y,toX:dest.x,toY:dest.y});
  }
  return moves;
 }
 return {map:map};
});
