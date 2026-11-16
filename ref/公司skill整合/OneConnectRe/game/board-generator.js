(function () {
  'use strict';
  // Seeded reverse construction: every inserted pair can be removed in reverse order.
  // This is a One Connect design, not a decoded competitor algorithm.
  function generate(config, seed) {
    var mask=config && config.mask, types=config && config.typeCount;
    if (!Array.isArray(mask) || !mask.length || mask.length>12 || !Array.isArray(mask[0]) || !mask[0].length || mask[0].length>12 || mask.some(function (r) { return !Array.isArray(r) || r.length!==mask[0].length || r.some(function(v){return v!==0 && v!==1;}); })) throw Error('mask must be rectangular, up to 12x12, of 0 or 1');
    var height=mask.length,width=mask[0].length;
    var cells=[];mask.forEach(function(row,y){row.forEach(function(v,x){if(v)cells.push([y,x]);});});
    if (cells.length<2 || cells.length%2 || !Number.isInteger(types) || types<1 || types>30 || types>cells.length/2 || !Number.isInteger(seed) || seed<0 || seed>4294967295) throw Error('invalid board parameters');
    var state=(seed>>>0)||0x6d2b79f5;
    function random(){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;}
    function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t;}return a;}
    var board=Array.from({length:height},function(){return Array(width).fill(0);}), path=[], nodes=0, limit=250;
    function canConnect(a,b){
      var dirs=[[-1,0],[1,0],[0,-1],[0,1]], queue=[[a[0],a[1],-1,0]],seen=new Set();
      for(var i=0;i<queue.length;i++){var q=queue[i];for(var k=0;k<4;k++){
        var y=q[0]+dirs[k][0],x=q[1]+dirs[k][1],turn=q[3]+(q[2]!==-1&&q[2]!==k?1:0);
        if(turn>2||y< -1||y>height||x< -1||x>width)continue;
        if(y===b[0]&&x===b[1])return true;
        if(y>=0&&y<height&&x>=0&&x<width&&board[y][x])continue;
        var key=[y,x,k,turn].join(',');if(!seen.has(key)){seen.add(key);queue.push([y,x,k,turn]);}
      }}return false;
    }
    // Try a shuffled distribution first and keep only boards with a complete solution.
    // Search is bounded; exhaustion is never treated as proof of no solution.
    function solve(depth, solution, dead) {
      if(depth===0)return true;if(++nodes>limit)return false;
      var key=board.map(function(row){return row.join(',');}).join(';');if(dead.has(key))return false;
      var groups={};cells.forEach(function(pos){var v=board[pos[0]][pos[1]];if(v)(groups[v]||(groups[v]=[])).push(pos);});
      var choices=[];Object.keys(groups).forEach(function(v){var g=groups[v];for(var i=0;i<g.length;i++)for(var j=i+1;j<g.length;j++)choices.push([g[i],g[j]]);});shuffle(choices);
      for(var k=0;k<choices.length;k++){var a=choices[k][0],b=choices[k][1],value=board[a[0]][a[1]];if(!canConnect(a,b))continue;board[a[0]][a[1]]=board[b[0]][b[1]]=0;solution.push([a,b]);
        if(solve(depth-1,solution,dead))return true;
        solution.pop();board[a[0]][a[1]]=board[b[0]][b[1]]=value;if(nodes>limit)break;
      }dead.add(key);return false;
    }
    for(var attempt=0;attempt<4;attempt++){
      var labels=Array.from({length:cells.length/2},function(_,i){return i<types?i+1:1+Math.floor(random()*types);});
      var shuffled=shuffle(labels.reduce(function(a,v){a.push(v,v);return a;},[]));
      cells.forEach(function(pos,i){board[pos[0]][pos[1]]=shuffled[i];});
      var initial=board.map(function(row){return row.slice();}),solution=[];nodes=0;limit=1000;
      if(solve(cells.length/2,solution,new Set()))return {board:initial,solution:solution,seed:seed,nodes:nodes,strategy:'shuffled'};
    }
    board.forEach(function(row){row.fill(0);});nodes=0;limit=250;
    function place(free){
      if(!free.length)return true;if(++nodes>limit)return false;
      var choices=[];for(var i=0;i<free.length;i++)for(var j=i+1;j<free.length;j++)choices.push([i,j,Math.abs(free[i][0]-free[j][0])+Math.abs(free[i][1]-free[j][1])+random()*4]);choices.sort(function(a,b){return a[2]-b[2]});
      for(var k=0;k<choices.length;k++){
        var ij=choices[k],a=free[ij[0]],b=free[ij[1]];board[a[0]][a[1]]=board[b[0]][b[1]]=1;
        if(canConnect(a,b)){path.push([a,b]);var rest=free.filter(function(_,idx){return idx!==ij[0]&&idx!==ij[1];});if(place(rest))return true;path.pop();}
        board[a[0]][a[1]]=board[b[0]][b[1]]=0;if(nodes>limit)break;
      }return false;
    }
    if(!place(cells)) {
      // Bounded fallback: cover the shape with adjacent pairs; every pair is removable.
      board.forEach(function(row){row.fill(0);}); path=[]; nodes=0;
      function domino(free) {
        if(!free.length)return true;if(++nodes>5000)return false;
        var a=free[0], candidates=shuffle(free.slice(1).filter(function(b){return Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])===1;}));
        for(var i=0;i<candidates.length;i++){var b=candidates[i];path.push([a,b]);if(domino(free.filter(function(p){return p!==a&&p!==b;})))return true;path.pop();}return false;
      }
      if(!domino(cells)){
        // Preserve the existing four attempts and both fallbacks. Only when all
        // of them fail, give high-variety boards a bounded second chance.
        if(types>20)for(var retry=0;retry<16;retry++){
          var retryLabels=Array.from({length:cells.length/2},function(_,i){return i<types?i+1:1+Math.floor(random()*types);});
          var retryValues=shuffle(retryLabels.reduce(function(a,v){a.push(v,v);return a;},[]));
          cells.forEach(function(pos,i){board[pos[0]][pos[1]]=retryValues[i];});
          var retryBoard=board.map(function(row){return row.slice();}),retrySolution=[];nodes=0;limit=1000;
          if(solve(cells.length/2,retrySolution,new Set()))return {board:retryBoard,solution:retrySolution,seed:seed,nodes:nodes,strategy:'shuffled_retry'};
        }
        throw Error('unable to build a solvable board within search budget');
      }
    }
    var kinds=Array.from({length:path.length},function(_,i){return i<types?i+1:1+Math.floor(random()*types);});shuffle(kinds);
    path.forEach(function(pair,i){pair.forEach(function(pos){board[pos[0]][pos[1]]=kinds[i];});});
    return {board:board,solution:path.slice().reverse(),seed:seed,nodes:nodes,strategy:'reverse_or_adjacent'};
  }
  window.oneConnectBoardGenerator={generate:generate};
}());
