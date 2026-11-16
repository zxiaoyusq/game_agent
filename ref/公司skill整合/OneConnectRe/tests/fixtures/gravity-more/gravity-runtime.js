(function () {
  'use strict';
  var installed=false,animation=null;
  function settle(){
    if(!animation)return;var a=animation;animation=null;
    a.moves.forEach(function(m){if(a.runtime.types.t5.instances.indexOf(m.tile)<0)return;m.tile.x=m.toX;m.tile.y=m.toY;m.tile.set_bbox_changed();});a.runtime.redraw=true;
  }
  function animate(now){
    var a=animation;if(!a)return;
    var r=a.runtime,level=r.all_global_vars.find(function(v){return v.name==='level';}),pause=r.all_global_vars.find(function(v){return v.name==='pause';});
    if(!r.running_layout||r.running_layout.name!=='game'||!level||level.data!==a.level){settle();return;}
    if(a.last===null)a.last=now;var dt=Math.min(Math.max(now-a.last,0),50);a.last=now;
    if(!(pause&&pause.data)&&!(document.hidden))a.elapsed+=dt;
    var t=Math.min(1,a.elapsed/260),ease=1-Math.pow(1-t,3);
    a.moves.forEach(function(m){if(r.types.t5.instances.indexOf(m.tile)<0)return;m.tile.x=m.fromX+(m.toX-m.fromX)*ease;m.tile.y=m.fromY+(m.toY-m.fromY)*ease;m.tile.set_bbox_changed();});r.redraw=true;
    if(t>=1){settle();return;}window.requestAnimationFrame(animate);
  }
  function apply(runtime,entry){
    var vars=runtime.all_global_vars, rowVar=vars.find(function(v){return v.name==='ROWS_COUNT';}), colVar=vars.find(function(v){return v.name==='COLUMNS_COUNT';}), sizeVar=vars.find(function(v){return v.name==='ITEM_SIZE';}), spacingVar=vars.find(function(v){return v.name==='ITEM_SPACING';});
    var rows=rowVar?rowVar.data:6,cols=colVar?colVar.data:12,stride=sizeVar&&spacingVar?sizeVar.data+spacingVar.data:101;
    var bounds=entry.gravity,dir=['gravity_down','gravity_up','gravity_left','gravity_right'].indexOf(entry.movement)!==-1?entry.movement.slice(8):null;
    if(!dir||!bounds||!Number.isInteger(bounds.top)||!Number.isInteger(bounds.left)||!Number.isInteger(bounds.rows)||!Number.isInteger(bounds.cols)||bounds.top<0||bounds.left<0||bounds.rows<1||bounds.cols<1||bounds.top+bounds.rows>cols||bounds.left+bounds.cols>rows||!window.oneConnectGravity)throw Error('invalid gravity configuration');
    var object=runtime.types.t0&&runtime.types.t0.instances[0],type=runtime.types.t5;
    if(!object||object.cx!==cols+2||object.cy!==rows+2||!type)throw Error('missing board state');
    var index=new Map(),grid=Array.from({length:bounds.rows},function(){return Array(bounds.cols).fill(0);});
    type.instances.forEach(function(t){index.set(t.uid,t);});
    for(var x=1;x<=cols;x++)for(var y=1;y<=rows;y++){
      var id=object.arr[x][y][0];if(!id)continue;var row=cols-x-bounds.top,col=y-1-bounds.left,tile=index.get(id);
      if(row<0||row>=bounds.rows||col<0||col>=bounds.cols||!tile||tile.instance_vars[2]!==x||tile.instance_vars[1]!==y)throw Error('board and tile positions do not agree');
      grid[row][col]=id;
    }
    var compact=window.oneConnectGravity.compact(grid,dir),moves=[];
    for(var row=0;row<bounds.rows;row++)for(var col=0;col<bounds.cols;col++){
      var id=compact[row][col];if(!id)continue;var tile=index.get(id),v=tile.instance_vars,nx=cols-(bounds.top+row),ny=bounds.left+col+1;
      moves.push({tile:tile,x:nx,y:ny,dx:nx-v[2],dy:ny-v[1]});
    }
    for(var row=0;row<bounds.rows;row++)for(var col=0;col<bounds.cols;col++)object.arr[cols-(bounds.top+row)][bounds.left+col+1][0]=0;
    var moved=0,animated=[];moves.forEach(function(m){var v=m.tile.instance_vars,fromX=m.tile.x,fromY=m.tile.y,toX=fromX+stride*m.dx,toY=fromY+stride*m.dy;if(m.dx||m.dy){moved++;animated.push({tile:m.tile,fromX:fromX,fromY:fromY,toX:toX,toY:toY});}else{m.tile.x=toX;m.tile.y=toY;}v[2]=m.x;v[1]=m.y;object.arr[m.x][m.y][0]=m.tile.uid;m.tile.set_bbox_changed();});
    if(animated.length&&typeof window.requestAnimationFrame==='function'){animation={runtime:runtime,level:entry.level,moves:animated,elapsed:0,last:null};window.requestAnimationFrame(animate);}else animated.forEach(function(m){m.tile.x=m.toX;m.tile.y=m.toY;m.tile.set_bbox_changed();});
    runtime.redraw=true;window.oneConnectHost.emit('game.gravity_applied',{level:entry.level,direction:dir,moved:moved});
  }
  function install(){if(installed)return;installed=true;var touch=window.cr&&cr.plugins_&&cr.plugins_.Touch&&cr.plugins_.Touch.prototype.cnds;if(touch){var oldTouch=touch.OnTouchObject;touch.OnTouchObject=function(type){var ok=oldTouch.apply(this,arguments);if(ok&&animation&&type&&(type.name==='t5'||type.name==='t26'))return false;return ok;};}window.addEventListener('oneconnect:event',function(e){if(!e.detail)return;if(e.detail.type==='game.auto_shuffle_start'||e.detail.type==='game.level_fail'||e.detail.type==='screen.SCREEN_BONUS'){settle();return;}if(e.detail.type!=='game.match')return;settle();var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),level=r&&r.all_global_vars.find(function(v){return v.name==='level';}),rows=window.oneConnectLevels&&window.oneConnectLevels.levels,entry=level&&Array.isArray(rows)&&rows.find(function(x){return x.level===level.data;});if(!entry||['gravity_down','gravity_up','gravity_left','gravity_right'].indexOf(entry.movement)===-1)return;try{apply(r,entry);}catch(error){window.oneConnectHost.emit('config.gravity_error',{level:entry.level,message:String(error)});}});}
  window.oneConnectGravityRuntime={install:install,state:function(){return {moving:!!animation};}};
}());
