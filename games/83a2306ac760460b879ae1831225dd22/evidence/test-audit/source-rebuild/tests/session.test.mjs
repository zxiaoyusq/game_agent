import test from 'node:test';import assert from 'node:assert/strict';import {createGame,roll,planMove,commitMove,clone} from '../src/rules.js';import {validateSession,load,persist} from '../src/storage.js';import {movementSegments,segmentAt,duration} from '../src/animation.js';
function saved(game,phase,extra={}){return {schema:1,id:'阶段测试',game,phase,elapsed:0,wait:0,plan:null,segments:[],...extra};}
test('ready、rolling、choosing、skip、celebrating和result逐阶段序列化验证',()=>{
 const g=createGame('classic',['human','off','human','off'],44);validateSession(saved(g,'ready'));roll(g);for(const phase of ['rolling','choosing','skip']){const s=saved(clone(g),phase,{elapsed:90,wait:90});assert.deepEqual(validateSession(JSON.parse(JSON.stringify(s))),s);}
 const winner=createGame('quick',['human','off','human','off'],9);winner.current=0;winner.dice=1;winner.unlocked[0]=true;winner.tokens[0][0].pos=56;commitMove(winner,planMove(winner,0));for(const phase of ['celebrating','result'])validateSession(saved(clone(winner),phase));
 assert.throws(()=>validateSession(saved(g,'ready')));assert.throws(()=>validateSession(saved(winner,'choosing')));assert.throws(()=>validateSession(saved(g,'rolling',{elapsed:NaN})));assert.throws(()=>validateSession({...saved(g,'rolling'),schema:2}));
});
test('逐段弧线计划及吃子回程、归家均保存后恢复相同采样',()=>{
 const g=createGame('quick',['human','off','human','off'],3);g.current=0;g.dice=1;g.tokens[0][0].pos=5;g.tokens[2][0].pos=6;const plan=planMove(g,0),segments=movementSegments(g,plan);assert.equal(segments[0].ms,110);assert.equal(segments.at(-1).ms,180);assert.deepEqual(segments.at(-1).to,{p:2,i:0,pos:-1});
 for(let elapsed=0;elapsed<duration(segments);elapsed+=25){const s=saved(clone(g),'moving',{plan,segments,elapsed});const restored=validateSession(JSON.parse(JSON.stringify(s)));assert.deepEqual(segmentAt(restored.segments,restored.elapsed),segmentAt(segments,elapsed));}
 const invalid=saved(clone(g),'moving',{plan:clone(plan),segments});invalid.plan.path=[7];assert.throws(()=>validateSession(invalid));
 const home=clone(g);home.unlocked[0]=true;home.tokens[0][0].pos=56;const hs=movementSegments(home,planMove(home,0));assert.equal(hs.at(-1).kind,'home');assert.equal(hs.at(-1).ms,400);
});
test('真实Storage接口成功、损坏读取与拒绝写入错误不吞掉',()=>{
 const data=new Map(),storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k)||null};const s=saved(createGame('classic',['human','off','human','off'],3),'ready');persist(storage,s);assert.deepEqual(load(storage),s);data.set('ludo-original-session-v1','损坏');assert.throws(()=>load(storage));assert.throws(()=>persist({setItem(){throw Error('存储拒绝');}},s));
});
