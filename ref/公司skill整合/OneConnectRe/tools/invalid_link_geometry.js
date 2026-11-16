/* Competitor DrawError selects the middle segment of its computed path.
 * Path search and the source of path points remain separate responsibilities. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.oneConnectInvalidLinkGeometry=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 function middleSegment(path){
  if(!Array.isArray(path)||path.length<2||path.some(function(p){return !p||!Number.isFinite(p.x)||!Number.isFinite(p.y);}))return null;
  var mid=Math.floor(path.length/2),a=path[mid-1],b=path[mid];
  return {x:(a.x+b.x)/2,y:(a.y+b.y)/2};
 }
 return {middleSegment:middleSegment};
});
