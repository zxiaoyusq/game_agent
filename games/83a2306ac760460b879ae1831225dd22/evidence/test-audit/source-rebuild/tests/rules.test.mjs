import test from 'node:test';import assert from 'node:assert/strict';import {writeFile,mkdir,readFile} from 'node:fs/promises';
import {createGame,route,nextPos,remaining,legalMoves,roll,planMove,commitMove,skip,chooseAI,assertGame,clone,SAFE} from '../src/rules.js';
import {streams,uniform} from '../src/random.js';import {movementSegments,duration} from '../src/animation.js';import {validateSession} from '../src/storage.js';
const seats=['human','ai','ai','ai'];const game=(mode='classic')=>createGame(mode,seats,123);
function place(g,p,i,pos) {g.tokens[p][i]={pos,finished:pos===57+6*p};}
function turn(g,p,dice){g.current=p;g.dice=dice;}
test('四队路径、营地、精确终点与快速最后格衔接',()=>{
 for(let p=0;p<4;p++) {
  const g=game();turn(g,p,1);assert.equal(route(g,p,0),null);g.dice=6;assert.deepEqual(route(g,p,0),[13*p]);
  place(g,p,0,(13*p+50)%52);g.dice=1;assert.deepEqual(route(g,p,0),[52+6*p]);
  place(g,p,0,56+6*p);assert.deepEqual(route(g,p,0),[57+6*p]);g.dice=2;assert.equal(route(g,p,0),null);
  place(g,p,0,57+6*p);assert.equal(route(g,p,0),null);
  const q=game('quick');turn(q,p,1);place(q,p,0,(13*p+50)%52);assert.deepEqual(route(q,p,0),[(13*p+51)%52]);
  place(q,p,0,(13*p+51)%52);q.unlocked[p]=true;assert.deepEqual(route(q,p,0),[13*p]);assert.equal(remaining(p,q.tokens[p][0].pos),57);
 }
});
test('安全格、单敌、多子混叠、经过不吃、不封路',()=>{
 for(const pos of SAFE) {const g=game();turn(g,0,1);place(g,0,0,(pos+51)%52);place(g,1,0,pos);assert.equal(planMove(g,0).capture,null);}
 for(const count of [1,2,3]) {const g=game();turn(g,0,1);place(g,0,0,3);for(let i=0;i<count;i++)place(g,1,i,4);const plan=planMove(g,0);assert.equal(!!plan.capture,count===1);commitMove(g,plan);assert.equal(g.tokens[1][0].pos,count===1?-1:4);}
 const g=game();turn(g,0,2);place(g,0,0,3);place(g,1,0,4);place(g,2,0,4);assert.deepEqual(route(g,0,0),[4,5]);assert.equal(planMove(g,0).capture,null);
});
test('奖励OR、跳过、空席轮转、首次胜利与动作幂等',()=>{
 const g=createGame('classic',['human','off','ai','off'],12);turn(g,0,6);place(g,0,0,1);place(g,2,0,7);const plan=planMove(g,0);commitMove(g,plan);assert.equal(g.current,0);assert.equal(g.turn,1);assert.equal(commitMove(g,plan),false);
 const q=createGame('classic',['human','off','ai','off'],13);turn(q,0,2);skip(q);assert.equal(q.current,2);
 const h=game();turn(h,0,6);h.tokens[0].forEach((_,i)=>place(h,0,i,57));skip(h);assert.equal(h.current,0);
 for(const mode of ['classic','quick']) {const w=game(mode);w.unlocked[0]=true;turn(w,0,1);if(mode==='classic')for(let i=1;i<4;i++)place(w,0,i,57);place(w,0,0,56);commitMove(w,planMove(w,0));assert.equal(w.winner,0);assert.equal(w.turn,0);assert.deepEqual(legalMoves(w),[]);}
});
test('快速只吃子永久开门、友军与混色多子不解锁',()=>{
 const g=game('quick');turn(g,0,1);place(g,0,0,3);place(g,1,0,4);const before=g.tokens[0][1].pos;commitMove(g,planMove(g,0));assert.equal(g.unlocked[0],true);assert.equal(g.unlocked[1],false);assert.equal(g.tokens[0][1].pos,before);
 turn(g,1,1);place(g,1,0,3);commitMove(g,planMove(g,0));assert.equal(g.unlocked[0],true);
 const q=game('quick');turn(q,0,1);place(q,0,0,3);place(q,1,0,4);place(q,2,0,4);commitMove(q,planMove(q,0));assert.equal(q.unlocked[0],false);
});
test('确定性随机重放、流隔离、均匀点数抽样',()=>{
 const a=streams(23),b=streams(23);const counts=Array(6).fill(0);
 for(let i=0;i<60000;i++){const x=uniform(a.dice,6);counts[x]++;uniform(a.ai,3);assert.equal(x,uniform(b.dice,6));}
 assert.ok(counts.every(n=>n>9400&&n<10600));
});
test('阶段存档恢复与损坏校验、完整运动计划不提前提交',()=>{
 const g=game();turn(g,0,6);const plan=planMove(g,0),segments=movementSegments(g,plan);
 const base={schema:1,id:'测试局',game:g,elapsed:10,wait:10,phase:'moving',plan,segments};assert.deepEqual(validateSession(clone(base)),base);assert.equal(duration(segments),110);assert.equal(g.tokens[0][0].pos,-1);
 for(const phase of ['rolling','choosing','skip'])assert.equal(validateSession({...clone(base),phase}).phase,phase);
 assert.throws(()=>validateSession({...clone(base),elapsed:-1}));const corrupt=clone(base);corrupt.segments[0].ms=1;assert.throws(()=>validateSession(corrupt));const bad=clone(g);bad.tokens[0][0].pos=75;assert.throws(()=>assertGame(bad));
});
test('两模式×2/3/4席多种子完整合法对局，选择浏览器自然对局种子',async()=>{
 const results=[],best={};
 for(const mode of ['classic','quick'])for(const n of [2,3,4])for(let seed=1;seed<=20;seed++){
  const s=n===2?['human','off','human','off']:n===3?['human','human','human','off']:['human','human','human','human'];
  const g=createGame(mode,s,seed);let rolls=0,animationMs=0,captures=0,homes=0;
  while(g.winner===null&&rolls<15000){roll(g);rolls++;animationMs+=850;
   if(legalMoves(g).length){const i=chooseAI(g);assert.ok(legalMoves(g).includes(i));const plan=planMove(g,i);animationMs+=duration(movementSegments(g,plan));captures+=!!plan.capture;homes+=plan.home;commitMove(g,plan);}else{animationMs+=350;skip(g);}assertGame(g);
  }
  assert.notEqual(g.winner,null,`${mode}/${n}/${seed}未完成`);const record={mode,seats:n,seed,rolls,actions:g.action,captures,homes,winner:g.winner,animationMs};results.push(record);
  if(n===2&&captures>0&&(!best[mode]||animationMs<best[mode].animationMs))best[mode]=record;
 }
 await mkdir('evidence',{recursive:true});await writeFile('evidence/rule-games.json',JSON.stringify({games:results,browserSeeds:best},null,2));console.log('完整合法规则对局120场；浏览器候选：',JSON.stringify(best));
});
test('76格真实契约及全部资产哈希通过构建校验',async()=>{const b=JSON.parse(await readFile('workflow/board-contract.json','utf8'));assert.equal(b.grid_centers.length,76);assert.deepEqual(b.safe_grids,SAFE);assert.deepEqual(b.terminal_grids,[57,63,69,75]);});
