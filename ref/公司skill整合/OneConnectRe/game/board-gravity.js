(function(root){
  'use strict';
  // Screen-oriented rectangular grid. The shape selects opening cells; after a
  // match, all surviving tiles settle against the same bottom or right edge.
  function compact(board,direction){
    if(!Array.isArray(board)||!board.length||!Array.isArray(board[0])||!board[0].length||board.some(function(row){return !Array.isArray(row)||row.length!==board[0].length||row.some(function(v){return !Number.isInteger(v)||v<0;});}))throw Error('invalid board');
    if(!['down','right','up','left'].includes(direction))throw Error('invalid gravity direction');
    var h=board.length,w=board[0].length,out=Array.from({length:h},function(){return Array(w).fill(0);});
    if(direction==='down'||direction==='up')for(var x=0;x<w;x++){var column=[];for(var y=0;y<h;y++)if(board[y][x])column.push(board[y][x]);for(var i=0;i<column.length;i++)out[(direction==='down'?h-column.length:0)+i][x]=column[i];}
    else for(var y=0;y<h;y++){var row=board[y].filter(function(v){return v!==0;});for(var i=0;i<row.length;i++)out[y][(direction==='right'?w-row.length:0)+i]=row[i];}
    return out;
  }
  root.oneConnectGravity={compact:compact};
}(globalThis));
