(function(root){
  'use strict';
  // One Connect implementation based on the observed global gravity rule; this
  // is not the competitor's unrecovered algorithm. Search budget is bounded.
  function generate(config,seed){
    var mask=config&&config.mask,n=config&&config.typeCount,direction=config&&config.direction;
    if(!Array.isArray(mask)||!mask.length||!Array.isArray(mask[0])||!mask[0].length||mask.some(function(r){return !Array.isArray(r)||r.length!==mask[0].length||r.some(function(v){return v!==0&&v!==1;});}))throw Error('invalid mask');
    if(!['down','right','up','left'].includes(direction))throw Error('invalid direction');
    if(!Number.isInteger(seed)||seed<0||seed>4294967295)throw Error('invalid seed');
    var h=mask.length,w=mask[0].length,cells=[];mask.forEach(function(row,y){row.forEach(function(v,x){if(v)cells.push([y,x]);});});
    if(cells.length<2||cells.length%2||!Number.isInteger(n)||n<1||n>30||n>cells.length/2)throw Error('invalid type count');
    var state=(seed>>>0)||0x6d2b79f5;
    function random(){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;}
    function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t;}return a;}
    function can(b,a,z){var dirs=[[-1,0],[1,0],[0,-1],[0,1]],q=[[a[0],a[1],-1,0]],seen=new Uint8Array((h+2)*(w+2)*12);for(var i=0;i<q.length;i++){var p=q[i];for(var d=0;d<4;d++){var y=p[0]+dirs[d][0],x=p[1]+dirs[d][1],turn=p[3]+(p[2]!==-1&&p[2]!==d?1:0);if(turn>2||y< -1||y>h||x< -1||x>w)continue;if(y===z[0]&&x===z[1])return true;if(y>=0&&y<h&&x>=0&&x<w&&b[y][x])continue;var key=(((y+1)*(w+2)+(x+1))*4+d)*3+turn;if(!seen[key]){seen[key]=1;q.push([y,x,d,turn]);}}}return false;}
    var nodes=0,limit=12000;
    function solve(b,left,dead){if(!left)return [];if(++nodes>limit)return null;var key=b.map(function(r){return r.join(',');}).join(';');if(dead.has(key))return null;
      var groups={};b.forEach(function(row,y){row.forEach(function(v,x){if(v)(groups[v]||(groups[v]=[])).push([y,x]);});});var choices=[];Object.keys(groups).forEach(function(v){var g=groups[v];for(var i=0;i<g.length;i++)for(var j=i+1;j<g.length;j++)choices.push([g[i],g[j]]);});shuffle(choices);
      for(var k=0;k<choices.length;k++){var a=choices[k][0],z=choices[k][1];if(!can(b,a,z))continue;var next=b.map(function(r){return r.slice();});next[a[0]][a[1]]=next[z[0]][z[1]]=0;next=root.oneConnectGravity.compact(next,direction);var rest=solve(next,left-2,dead);if(rest)return [[a,z]].concat(rest);if(nodes>limit)break;}dead.add(key);return null;
    }
    if(!root.oneConnectGravity)throw Error('gravity model unavailable');
    var retryLimit=n>20&&cells.length!==h*w?12:4;
    for(var attempt=0;attempt<retryLimit;attempt++){var labels=Array.from({length:cells.length/2},function(_,i){return i<n?i+1:1+Math.floor(random()*n);}),values=shuffle(labels.reduce(function(a,v){a.push(v,v);return a;},[])),board=Array.from({length:h},function(){return Array(w).fill(0);});cells.forEach(function(p,i){board[p[0]][p[1]]=values[i];});nodes=0;var solution=solve(board,cells.length,new Set());if(solution)return {board:board,solution:solution,seed:seed,nodes:nodes,attempt:attempt};}
    // A deliberately simple fallback for solid, even-length gravity lanes.
    // Each adjacent pair is removed from the settling edge before the next pair.
    if(n>20 && cells.length===h*w && ((['down','up'].includes(direction)&&h%2===0)||(['right','left'].includes(direction)&&w%2===0))){
      var count=cells.length/2,labels=Array.from({length:count},function(_,i){return i<n?i+1:1+Math.floor(random()*n);});shuffle(labels);
      var board=Array.from({length:h},function(){return Array(w).fill(0);}),solution=[],at=0;
      if(direction==='down'||direction==='up'){
        var columns=shuffle(Array.from({length:w},function(_,i){return i;}));
        columns.forEach(function(x){for(var i=0;i<h/2;i++){var y=direction==='down'?h-2-2*i:2*i,value=labels[at++],edge=direction==='down'?h-2:0;board[y][x]=board[y+1][x]=value;solution.push([[edge,x],[edge+1,x]]);}});
      }else{
        var rows=shuffle(Array.from({length:h},function(_,i){return i;}));
        rows.forEach(function(y){for(var i=0;i<w/2;i++){var x=direction==='right'?w-2-2*i:2*i,value=labels[at++],edge=direction==='right'?w-2:0;board[y][x]=board[y][x+1]=value;solution.push([[y,edge],[y,edge+1]]);}});
      }
      return {board:board,solution:solution,seed:seed,nodes:nodes,attempt:4,strategy:'adjacent_lane_fallback'};
    }
    throw Error('unable to generate solved gravity board within search budget');
  }
  root.oneConnectGravityGenerator={generate:generate};
}(window));
