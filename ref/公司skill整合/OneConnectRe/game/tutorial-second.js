(function () {
  'use strict';
  var installed = false, pending = false, active = false, target = [], route = [], overlay, line, circles = [];
  var completionKey = 'oneconnect.tutorial2.v1';
  function completed(){try{return localStorage.getItem(completionKey)==='done';}catch(error){return false;}}
  function markCompleted(){try{localStorage.setItem(completionKey,'done');}catch(error){/* Guide remains available when storage is unavailable. */}}
  function findPair(tiles) {
    var xs = Array.from(new Set(tiles.map(function(t){return Math.round(t.x);}))).sort(function(a,b){return a-b;});
    var ys = Array.from(new Set(tiles.map(function(t){return Math.round(t.y);}))).sort(function(a,b){return a-b;});
    if (!xs.length || !ys.length) return null;
    var grid = new Map(), points = tiles.map(function(t){var x=xs.indexOf(Math.round(t.x))+1,y=ys.indexOf(Math.round(t.y))+1;grid.set(x+','+y,t);return {x:x,y:y,t:t};});
    function connect(a,b) {
      var dirs=[[1,0],[-1,0],[0,1],[0,-1]],q=[{x:a.x,y:a.y,d:-1,turn:0,path:[[a.x,a.y]]}],seen=new Set();
      for(var i=0;i<q.length;i++)for(var d=0;d<4;d++){
        var p=q[i],x=p.x+dirs[d][0],y=p.y+dirs[d][1],turn=p.turn+(p.d!==-1&&p.d!==d?1:0);
        if(turn>2||x<0||y<0||x>xs.length+1||y>ys.length+1)continue;
        var path=p.path.concat([[x,y]]);if(x===b.x&&y===b.y)return path;
        if(grid.has(x+','+y))continue;var key=[x,y,d,turn].join(',');if(!seen.has(key)){seen.add(key);q.push({x:x,y:y,d:d,turn:turn,path:path});}
      }return null;
    }
    var candidates=[];for(var i=0;i<points.length;i++)for(var j=i+1;j<points.length;j++)if(points[i].t.cur_frame===points[j].t.cur_frame)candidates.push([points[i],points[j]]);
    candidates.sort(function(a,b){return (Math.abs(a[0].x-a[1].x)+Math.abs(a[0].y-a[1].y))-(Math.abs(b[0].x-b[1].x)+Math.abs(b[0].y-b[1].y));});
    for(var k=0;k<candidates.length;k++) {var path=connect(candidates[k][0],candidates[k][1]);if(path)return {tiles:[candidates[k][0].t,candidates[k][1].t],path:path.map(function(p){return [xs[0]+(p[0]-1)*101,ys[0]+(p[1]-1)*101];})};}
    return null;
  }
  function dismiss(){pending=false;active=false;if(overlay)overlay.style.display='none';}
  function frame() {
    var r=window.cr_getC2Runtime&&window.cr_getC2Runtime(),level=r&&r.all_global_vars.find(function(v){return v.name==='level';});
    var game=r&&r.running_layout&&r.running_layout.name==='game'&&level&&level.data===2;
    if(pending && game && r.types.t5.instances.length===30){var pair=findPair(r.types.t5.instances);pending=false;if(pair){target=pair.tiles;route=pair.path;active=true;}}
    if(active && (!game || target.some(function(t){return r.types.t5.instances.indexOf(t)<0;})))dismiss();
    var pause=r&&r.all_global_vars.find(function(v){return v.name==='pause';});
    if(active && game && !(pause&&pause.data)){
      var rect=r.canvas.getBoundingClientRect(),layer=target[0].layer;
      function screen(x,y){return [rect.left+layer.layerToCanvas(x,y,true),rect.top+layer.layerToCanvas(x,y,false)];}
      line.setAttribute('points',route.map(function(p){return screen(p[0],p[1]).join(',');}).join(' '));
      target.forEach(function(t,i){var p=screen(t.x,t.y),edge=screen(t.x+101,t.y);circles[i].setAttribute('cx',p[0]);circles[i].setAttribute('cy',p[1]);circles[i].setAttribute('r',Math.hypot(edge[0]-p[0],edge[1]-p[1])*.46);});
      overlay.style.display='block';
    }else if(overlay)overlay.style.display='none';
    requestAnimationFrame(frame);
  }
  function install(){
    if(installed)return;installed=true;
    var ns='http://www.w3.org/2000/svg';overlay=document.createElementNS(ns,'svg');overlay.id='oc-second-guide';overlay.style.cssText='display:none;position:fixed;inset:0;width:100%;height:100%;z-index:29;pointer-events:none;overflow:visible';
    line=document.createElementNS(ns,'polyline');line.setAttribute('fill','none');line.setAttribute('stroke','#ffe35f');line.setAttribute('stroke-width','5');line.setAttribute('stroke-linecap','round');line.setAttribute('stroke-linejoin','round');overlay.appendChild(line);
    for(var i=0;i<2;i++){var c=document.createElementNS(ns,'circle');c.setAttribute('fill','none');c.setAttribute('stroke','#ffe35f');c.setAttribute('stroke-width','4');overlay.appendChild(c);circles.push(c);}document.body.appendChild(overlay);
    window.addEventListener('oneconnect:event',function(e){var x=e.detail;if(!x)return;if(x.type==='game.board_configured'&&x.detail.level===2){dismiss();pending=!completed();}else if(x.type==='game.match'){if(x.detail.level===2&&x.detail.source==='normal')markCompleted();dismiss();}else if(x.type==='game.shuffle'||x.type==='game.level_fail')dismiss();});
    requestAnimationFrame(frame);
  }
  window.oneConnectSecondGuide={install:install,state:function(){return {active:active,tiles:target.map(function(t){return t.uid;}),path:route.map(function(p){return p.slice();})};},findPair:findPair};
}());
