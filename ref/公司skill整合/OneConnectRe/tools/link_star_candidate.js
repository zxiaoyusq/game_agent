/* Reference-based path star count. This does not alter gameplay. Invalid or
 * self-overlapping paths return null rather than guessed scores. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.oneConnectLinkStarCandidate = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function count(points, source) {
    if ((source !== 'normal' && source !== 'hammer') || !Array.isArray(points) || points.length < 2 || points.length > 128 ||
        points.some(function(p){return !p || !Number.isSafeInteger(p.x) || !Number.isSafeInteger(p.y);})) return null;
    var unique = new Set(points.map(function(p){return p.x+','+p.y;}));
    if (unique.size !== points.length) return null;
    if (source === 'hammer') return points.length === 2 ? 2 : null;
    var visited=new Set([points[0].x+','+points[0].y]), direction=null, turns=0;
    for(var i=1;i<points.length;i++){
      var a=points[i-1],b=points[i],dx=b.x-a.x,dy=b.y-a.y;
      if((dx!==0&&dy!==0)||(!dx&&!dy))return null;
      var sx=Math.sign(dx),sy=Math.sign(dy),dir=sx+','+sy,steps=Math.abs(dx)+Math.abs(dy);
      if(!Number.isSafeInteger(steps)||steps>127||visited.size+steps>128)return null;
      if(direction!==null&&direction!==dir&&++turns>2)return null;
      direction=dir;
      for(var n=1;n<=steps;n++){
        var key=(a.x+sx*n)+','+(a.y+sy*n);
        if(visited.has(key))return null;
        visited.add(key);
      }
    }
    return visited.size;
  }
  return {count:count};
});
