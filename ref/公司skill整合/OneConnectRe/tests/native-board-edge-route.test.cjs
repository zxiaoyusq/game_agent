const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
function Arr() {} Arr.prototype.Instance = function() {};
Arr.prototype.Instance.prototype.at = function(x, y, z) { return this.arr[x]?.[y]?.[z] ?? -1; };
const board = new Arr.prototype.Instance();
board.type = { name: 't0' };
board.arr = Array.from({length: 8}, () => Array.from({length: 6}, () => [0]));
const runtime = {tickcount: 1, running_layout: {name:'game'}, all_global_vars:
  [['ROWS_COUNT',4],['COLUMNS_COUNT',6],['ITEM_SIZE',80],['ITEM_SPACING',4]].map(([name,data])=>({name,data})),
  types:{t5:{instances:[{uid:1,instance_vars:[0,2,2]},{uid:2,instance_vars:[0,2,5]}]}},
  getCurrentEventStack:()=>({current_event:{sid:101}})};
board.runtime=runtime;
for (const [x,y,value] of [[2,2,1],[5,2,2],[3,2,3],[4,2,4]]) board.arr[x][y][0]=value;
const cr={plugins_:{Arr}}, window={cr,oneConnectNativePathSids:[101],
  oneConnectVisibleGravityBounds:{clip:()=>({top:1,left:1,rows:4,cols:2})}};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/native_board_mask_candidate.js','utf8'),{window,cr,Number,Array,Math,Set});
window.oneConnectNativeBoardMask.install();

function findRoute() {
  const start=[2,2], end=[5,2], dirs=[[1,0],[-1,0],[0,1],[0,-1]], queue=[], seen=new Set();
  for(let d=0;d<4;d++) queue.push([start[0],start[1],d,0]);
  for(let i=0;i<queue.length;i++) {
    const [x,y,d,turns]=queue[i], key=[x,y,d,turns].join(',');
    if(seen.has(key)) continue; seen.add(key);
    for(let next=0;next<4;next++) {
      const t=turns+(next!==d), nx=x+dirs[next][0], ny=y+dirs[next][1];
      if(t>2 || nx<0 || nx>7 || ny<0 || ny>5) continue;
      if(nx===end[0] && ny===end[1]) return true;
      if(board.at(nx,ny,0)!==0) continue;
      queue.push([nx,ny,next,t]);
    }
  }
  return false;
}
// Block the inner side: the only <=2-turn path lies in the outside y=1 lane.
for(let x=2;x<=5;x++) board.arr[x][3][0]=30+x;
assert.equal(findRoute(),true,'the outside lane permits a two-turn route');
board.arr[2][1][0]=99; board.arr[5][1][0]=98; runtime.tickcount++;
assert.equal(findRoute(),false,'an occupied outside lane cannot be crossed');
console.log('visible board edge route and obstruction: PASS');
