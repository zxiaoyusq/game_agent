/* Limit gravity destinations to whole cells visible in the canvas viewport. */
(function(){'use strict';
 function clip(runtime,bounds,tiles,rows,cols,stride){
  if(!tiles||!tiles.length)return bounds;
  var ref=tiles[0],layer=ref.layer,canvas=runtime.canvas;
  if(!canvas||!canvas.width||!canvas.height||!layer||typeof layer.layerToCanvas!=='function'||!ref.instance_vars)return null;
  var rect=canvas.getBoundingClientRect(),ratio=runtime.isRetina?runtime.devicePixelRatio:1;
  if(!rect.width||!rect.height||!Number.isFinite(ratio)||ratio<=0)return null;
  // A tile may be temporarily shrunk by its spawn or elimination tween. Use
  // its full configured size so a later restored sprite cannot leave view.
  var configured=runtime.all_global_vars&&runtime.all_global_vars.find(function(v){return v.name==='ITEM_SIZE';});
  var fullSize=configured&&Number.isFinite(configured.data)&&configured.data>0?configured.data:0;
  var halfX=Math.max(Math.abs(ref.width),fullSize)/2,halfY=Math.max(Math.abs(ref.height),fullSize)/2,allowed=[];
  if(!Number.isFinite(halfX)||!Number.isFinite(halfY)||!halfX||!halfY)return null;
  for(var r=bounds.top;r<bounds.top+bounds.rows;r++)for(var c=bounds.left;c<bounds.left+bounds.cols;c++){
   var x=cols-r,y=c+1,cx=ref.x+(x-ref.instance_vars[2])*stride,cy=ref.y+(y-ref.instance_vars[1])*stride;
   var points=[[-1,-1],[-1,1],[1,-1],[1,1]].map(function(p){return {x:rect.left+layer.layerToCanvas(cx+p[0]*halfX,cy+p[1]*halfY,true)*ratio*rect.width/canvas.width,y:rect.top+layer.layerToCanvas(cx+p[0]*halfX,cy+p[1]*halfY,false)*ratio*rect.height/canvas.height};});
   if(points.every(function(p){return Number.isFinite(p.x)&&Number.isFinite(p.y)&&p.x>=rect.left-0.5&&p.x<=rect.right+0.5&&p.y>=rect.top-0.5&&p.y<=rect.bottom+0.5;}))allowed.push([r,c]);
  }
  if(!allowed.length)return null;
  var top=Math.min.apply(null,allowed.map(function(p){return p[0]})),bottom=Math.max.apply(null,allowed.map(function(p){return p[0]})),left=Math.min.apply(null,allowed.map(function(p){return p[1]})),right=Math.max.apply(null,allowed.map(function(p){return p[1]}));
  if(allowed.length!==(bottom-top+1)*(right-left+1))return null;
  // Never silently discard a live tile or break a pair.
  if(tiles.some(function(t){var v=t.instance_vars,rr=cols-v[2],cc=v[1]-1;return rr<top||rr>bottom||cc<left||cc>right;}))return null;
  return {top:top,left:left,rows:bottom-top+1,cols:right-left+1};
 }
 window.oneConnectVisibleGravityBounds={clip:clip};
}());
