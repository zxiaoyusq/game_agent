/* Captures the original connectDots input before the original action runs.
 * The ordering and coordinate interpretation remain unverified. */
(function () {
  'use strict';
  var installed = false, gridPoints = [], pendingScreenPoints = null;
  function selectedScreenPoints(runtime) {
    var locals=runtime.all_local_vars || [], tiles=runtime.types.t5 && runtime.types.t5.instances || [];
    var ids=[549914461589189,205709254634256].map(function(sid){var v=locals.find(function(item){return item.sid===sid;});return v&&v.data;});
    if (!ids.every(Number.isInteger) || ids[0]===ids[1]) return null;
    var selected=ids.map(function(uid){return tiles.find(function(tile){return tile.uid===uid;});});
    if (selected.some(function(tile){return !tile || !tile.layer;})) return null;
    var rect=runtime.canvas.getBoundingClientRect(), ratio=runtime.isRetina?runtime.devicePixelRatio:1;
    if (!rect.width || !rect.height || !runtime.canvas.width || !runtime.canvas.height) return null;
    return selected.map(function(tile){
      return {x:rect.left+tile.layer.layerToCanvas(tile.x,tile.y,true)*ratio*rect.width/runtime.canvas.width,
        y:rect.top+tile.layer.layerToCanvas(tile.x,tile.y,false)*ratio*rect.height/runtime.canvas.height};
    });
  }
  function screenPath(runtime, grid, selected) {
    if(!Array.isArray(grid)||grid.length<2||!selected||selected.length!==2)return null;
    var tiles=runtime.types.t5&&runtime.types.t5.instances,base=tiles&&tiles[0],vars=runtime.all_global_vars||[];
    var size=vars.find(function(v){return v.name==='ITEM_SIZE';}),spacing=vars.find(function(v){return v.name==='ITEM_SPACING';});
    if(!base||!base.layer||!base.instance_vars||!size||!spacing)return null;
    var pitch=size.data+spacing.data,rect=runtime.canvas.getBoundingClientRect(),ratio=runtime.isRetina?runtime.devicePixelRatio:1;
    if(!Number.isFinite(pitch)||pitch<=0||!rect.width||!rect.height||!runtime.canvas.width||!runtime.canvas.height)return null;
    var cells=[grid[0]];
    for(var i=1;i<grid.length;i++){
      var a=grid[i-1],b=grid[i],dx=Math.sign(b.x-a.x),dy=Math.sign(b.y-a.y),length=Math.abs(b.x-a.x)+Math.abs(b.y-a.y);
      if((dx&&dy)||length<1||length>128||cells.length+length>128)return null;
      for(var n=1;n<=length;n++)cells.push({x:a.x+dx*n,y:a.y+dy*n});
    }
    var result=cells.map(function(p){
      var x=base.x+(p.y-base.instance_vars[2])*pitch,y=base.y+(p.x-base.instance_vars[1])*pitch;
      return {x:rect.left+base.layer.layerToCanvas(x,y,true)*ratio*rect.width/runtime.canvas.width,
        y:rect.top+base.layer.layerToCanvas(x,y,false)*ratio*rect.height/runtime.canvas.height};
    });
    function near(a,b){return Math.hypot(a.x-b.x,a.y-b.y)<Math.max(3,rect.width*.02);}
    var first=result[0],last=result[result.length-1];
    if(!(near(first,selected[0])&&near(last,selected[1]))&&!(near(first,selected[1])&&near(last,selected[0])))return null;
    return result;
  }
  function install() {
    if (installed) return;
    var proto = window.cr && cr.action && cr.action.prototype;
    if (!proto || typeof proto.run_object !== 'function') return;
    var previous = proto.run_object;
    proto.run_object = function () {
      // The matching branch clears UID1/UID2 after _release_initials and
      // before connectDots; capture while both selected instances still exist.
      if (this.sid === 847273165608027) pendingScreenPoints = selectedScreenPoints(this.runtime);
      if (this.sid === 342897974427682) gridPoints = [];
      if (this.sid === 416597964705574) {
        try {
          var locals=this.runtime.all_local_vars || [];
          var index=locals.find(function(v){return v.sid===286246248258364;});
          var token=locals.find(function(v){return v.sid===144847393796262;});
          var arrayType=this.runtime.types.t0, board=arrayType && arrayType.instances[0];
          if (index && token && board && Number.isInteger(index.data) && index.data>=0 && index.data<128 &&
              Number.isInteger(token.data) && token.data>=0 && Number.isInteger(board.cx) && board.cx>0) {
            gridPoints[index.data]={x:Math.floor(token.data/board.cx),y:token.data%board.cx};
          }
        } catch (error) { gridPoints=[]; }
      }
      if (this.sid === 293018238331220) {
        try {
          var r=this.runtime, type=r && r.types && r.types.t1;
          var array=type && type.instances && type.instances[0], points=[];
          if (array && Number.isInteger(array.cx) && array.cx>0 && array.cx<=128 && array.cy>=2 && array.cz>=1) {
            for (var x=0;x<array.cx;x++) {
              var px=array.arr[x][0][0], py=array.arr[x][1][0];
              if (!Number.isFinite(px) || !Number.isFinite(py)) { points=[];break; }
              points.push({x:px,y:py});
            }
            if (points.length && window.oneConnectHost) {
              var geometry={}, names=['ITEM_SIZE','ITEM_SPACING','HALF_ITEM_SIZE','BOARD_OFFSET_X','BOARD_OFFSET_Y'];
              var level=null;
              (r.all_global_vars || []).forEach(function (v) {
                if (names.indexOf(v.name)!==-1 && Number.isFinite(v.data)) geometry[v.name]=v.data;
                if (v.name==='level' && Number.isInteger(v.data) && v.data>0) level=v.data;
              });
              var grid=gridPoints.length===points.length && Array.from(gridPoints).every(function(p){return p && Number.isInteger(p.x) && Number.isInteger(p.y);}) ? gridPoints.slice() : null;
              var estimate=grid && window.oneConnectLinkStarCandidate ? window.oneConnectLinkStarCandidate.count(grid,'normal') : null;
              window.oneConnectHost.emit('candidate.link_points', {level:level, points:points, gridPoints:grid, geometry:geometry, coordinateSpace:'unverified', starCountEstimate:estimate, selectedScreenPoints:pendingScreenPoints, pathScreenPoints:screenPath(r,grid,pendingScreenPoints)});
            }
          }
        } catch (error) { console.warn('Candidate link-point capture failed', error); }
        pendingScreenPoints = null;
      }
      return previous.apply(this, arguments);
    };
    installed=true;
  }
  window.oneConnectLinkPointsCandidate={install:install};
}());
