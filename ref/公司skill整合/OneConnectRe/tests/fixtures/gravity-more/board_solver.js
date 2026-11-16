/* Offline model for the editor. No game-runtime mutations. */
function solveBoard(board, level, maxNodes, movement) {
  if (!Array.isArray(board) || !board.length || !Array.isArray(board[0]) || !board[0].length ||
      board.some(r => !Array.isArray(r) || r.length !== board[0].length || r.some(v => !Number.isInteger(v) || v < 0))) throw Error('棋盘格式无效');
  if (!Number.isInteger(level) || level < 1 || !Number.isInteger(maxNodes) || maxNodes < 0) throw Error('关卡号或搜索预算无效');
  if (movement !== undefined && !['static','gravity_down','gravity_up','gravity_left','gravity_right'].includes(movement)) throw Error('移动模式无效');
  const rows=board.length, cols=board[0].length, mode=movement || ({1:'static',2:'fall_down',3:'fall_up',4:'move_right',0:'move_left'})[level%5];
  const cells=board.flat(),counts=new Map();for(const v of cells)if(v)counts.set(v,(counts.get(v)||0)+1);
  if([...counts.values()].some(n=>n%2))return {status:'unsolvable',mode,nodes:0,moves:[]};
  function canConnect(grid, a, b) {
    const dirs=[[-1,0],[1,0],[0,-1],[0,1]],queue=[[a[0],a[1],-1,0]],seen=new Set();
    for(let i=0;i<queue.length;i++){let [r,c,prev,turns]=queue[i];for(let d=0;d<4;d++){
      let nr=r+dirs[d][0],nc=c+dirs[d][1],n=turns+(prev!==-1&&prev!==d?1:0);
      if(n>2||nr < -1||nr>rows||nc < -1||nc>cols)continue;
      if(nr===b[0]&&nc===b[1])return true;
      if(nr>=0&&nr<rows&&nc>=0&&nc<cols&&grid[nr][nc])continue;
      let k=[nr,nc,d,n].join(',');if(!seen.has(k)){seen.add(k);queue.push([nr,nc,d,n])}
    }}return false;
  }
  function move(grid,a,b){
    if(mode==='static')return;
    // Global gravity packs every row/column, unlike the original C2 modes.
    if(mode==='gravity_down'||mode==='gravity_up'){
      for(let c=0;c<cols;c++){let values=[];for(let r=0;r<rows;r++)if(grid[r][c])values.push(grid[r][c]);for(let r=0;r<rows;r++)grid[r][c]=mode==='gravity_down'?(r<rows-values.length?0:values[r-(rows-values.length)]):(r<values.length?values[r]:0);}
      return;
    }
    if(mode==='gravity_right'||mode==='gravity_left'){
      for(let r=0;r<rows;r++){let values=grid[r].filter(Boolean);for(let c=0;c<cols;c++)grid[r][c]=mode==='gravity_right'?(c<cols-values.length?0:values[c-(cols-values.length)]):(c<values.length?values[c]:0);}
      return;
    }
    const vertical=mode.startsWith('fall_'),direction=(mode==='fall_down'||mode==='move_right')?1:-1;
    for(const [r,c] of [a,b]){const n=vertical?rows:cols;
      for(let i=direction===1?n-1:0;direction===1?i>0:i<n-1;i-=direction){let src=i-direction;
        let current=vertical?grid[i][c]:grid[r][i],source=vertical?grid[src][c]:grid[r][src];
        if(!current&&source){if(vertical){grid[i][c]=source;grid[src][c]=0}else{grid[r][i]=source;grid[r][src]=0}}
      }
    }
  }
  let nodes=0,dead=new Set(),exhausted=false;
  function search(state){
    if(!state.some(Boolean))return [];
    const key=state.join(',');if(dead.has(key))return null;
    if(nodes>=maxNodes){exhausted=true;return null}nodes++;
    const grid=Array.from({length:rows},(_,i)=>state.slice(i*cols,(i+1)*cols)),groups=new Map();
    state.forEach((v,i)=>{if(v){if(!groups.has(v))groups.set(v,[]);groups.get(v).push(i)}});
    for(const indexes of groups.values())for(let i=0;i<indexes.length;i++)for(let j=i+1;j<indexes.length;j++){
      let a=[Math.floor(indexes[i]/cols),indexes[i]%cols],b=[Math.floor(indexes[j]/cols),indexes[j]%cols];
      if(!canConnect(grid,a,b))continue;
      let next=grid.map(r=>r.slice());next[a[0]][a[1]]=next[b[0]][b[1]]=0;move(next,a,b);
      let rest=search(next.flat());if(rest!==null)return [[a,b],...rest];if(exhausted)return null;
    }
    dead.add(key);return null;
  }
  const moves=search(cells);return {status:exhausted?'unknown':moves!==null?'solved':'unsolvable',mode,nodes,moves:moves||[]};
}
globalThis.solveBoard=solveBoard;
