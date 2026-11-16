const assert=require('node:assert/strict');
const grid=[[0,5,0,8,3],[0,7,8,2,6],[3,1,0,1,2],[4,5,0,0,7],[6,4,0,0,0]];
const pairs=[[11,13],[8,14],[10,4],[3,7],[1,16]];
function connected(a,b){
 const q=[[Math.floor(a/5),a%5,-1,0]],seen=new Set(),dirs=[[-1,0],[1,0],[0,-1],[0,1]];
 for(let i=0;i<q.length;i++){const [y,x,last,turns]=q[i];for(let d=0;d<4;d++){
  const ny=y+dirs[d][0],nx=x+dirs[d][1],next=turns+(last>=0&&last!==d?1:0);
  if(ny< -1||ny>5||nx< -1||nx>5||next>2)continue;
  if(ny===Math.floor(b/5)&&nx===b%5)return true;
  if(ny>=0&&ny<5&&nx>=0&&nx<5&&grid[ny][nx])continue;
  const key=[ny,nx,d,next].join(':');if(!seen.has(key)){seen.add(key);q.push([ny,nx,d,next]);}
 }}return false;
}
for(const [a,b] of pairs){assert.equal(grid[Math.floor(a/5)][a%5],grid[Math.floor(b/5)][b%5]);assert(connected(a,b),'guided target must be connectable: '+a+','+b);grid[Math.floor(a/5)][a%5]=0;grid[Math.floor(b/5)][b%5]=0;}
console.log('first tutorial active target pairs are connectable in sequence PASS');
