(function(root){
  'use strict';
  // Randomly select one pair of equal types, whether or not a link is available.
  // The selection distribution is a local design; competitor weighting is unknown.
  function choosePair(tiles,random){
    if(!Array.isArray(tiles)||typeof random!=='function')throw Error('invalid hammer input');
    var groups=new Map(),seen=new Set();tiles.forEach(function(t){if(!t||!Number.isInteger(t.uid)||t.uid<1||!Number.isInteger(t.type)||t.type<1||seen.has(t.uid))throw Error('invalid tile');seen.add(t.uid);if(!groups.has(t.type))groups.set(t.type,[]);groups.get(t.type).push(t.uid);});
    var pairs=[];groups.forEach(function(g){for(var i=0;i<g.length;i++)for(var j=i+1;j<g.length;j++)pairs.push([g[i],g[j]]);});if(!pairs.length)return null;
    var n=random();if(typeof n!=='number'||!Number.isFinite(n)||n<0||n>=1)throw Error('invalid random value');return pairs[Math.floor(n*pairs.length)];
  }
  root.oneConnectHammerModel={choosePair:choosePair};
}(window));
