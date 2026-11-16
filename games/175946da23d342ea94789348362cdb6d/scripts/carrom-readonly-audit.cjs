'use strict';
// 只执行当前源码中截取的函数；界面、物理提交和动画由替身记录。
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const source = fs.readFileSync('reference-inputs/current/game.js', 'utf8');
const hash = crypto.createHash('sha256').update(source).digest('hex');
assert.equal(hash, '3140ae1bd16fd91b6c025fc3641f2ff41e9f26e2b7200c94810199ada22a1573');
function extract(name) {
  const start = source.indexOf('    function ' + name + '(');
  assert.ok(start >= 0, name);
  const end = source.indexOf('\n    }', start);
  assert.ok(end >= 0, name + ' 函数结束边界');
  return source.slice(start, end + '\n    }'.length);
}
const decoder = source.slice(source.indexOf('function _0x3797('), source.indexOf('var ParticleManager ='));
const table = source.slice(source.indexOf('function _0x3f3a()'));
const rotation = source.slice(0, source.indexOf('var src ='));
const names = ['_0x3d12d7','_0x23a7dc','_0x8b2762','_0x2bd695','_0x338c29','_0x4662ac','_0x223471','_0x4b3cc6','_0xd6b627','_0x52106f','_0x25af2a','_0x521eef','_0x30849b','_0x3ea989','_0x247dad','_0x16430c','_0xbdafb3'];
function context() {
  const queue = [], shots = [];
  const math = Object.create(Math); math.random = () => 0.5;
  const c = {Math: math, console, _carromRoundId: 1, _carromTurnId: 1, _carromAiShotTurn: -1, _0x3fddb3: true, _0x2a9c75: [], _0x3e4566: [], _0x3231b3: [], _0x55e1a0: 162, _0x187453: 483, _0x429ae3: 421, _0x133600: 21.76, _0x3ce1ab: 15, _0x408018: 0, _0x18e0e1: [0.8], _0x301cde: 100, _0xc5bee4: {}, _0x27e1b4: {x: 320,y:421}, _0x24bb4a() {}, _0xbdafb3() {}, Tweener: {addTween(target, props, options) {queue.push({target, props, options});}}};
  vm.createContext(c);
  vm.runInContext(table + '\n' + decoder + '\n' + rotation + '\nvar _0x157421 = _0x3797;\n' + names.map(extract).join('\n'), c, {timeout: 2000});
  c._0x27e1b4[c._0x3797(0x1cd)] = (force, angle) => shots.push({force,angle});
  return {c,queue,shots};
}
const results = [];
function test(name, fn) {fn(); results.push({name,status:'通过',kind:'人工构造，执行当前实际函数'});}
test('空目标抛出 TypeError', () => {const {c}=context(); assert.throws(()=>c._0x3d12d7(), {name:'TypeError'});});
test('可用摆位返回有限坐标和角度', () => {const {c}=context(); c._0x2a9c75=[{x:320,y:600}]; const p=c._0x3d12d7(); assert.ok(Number.isFinite(p.dir)); assert.equal(c._0x23a7dc(p.pos,36.76),false);});
test('真实几何全阻仍返回受阻位置', () => {const {c}=context(); c._0x2a9c75=Array.from({length:10},(_,i)=>({x:162+i*35.66,y:421})); const p=c._0x3d12d7(); assert.equal(c._0x23a7dc(p.pos,36.76),true);});
test('非有限发射参数未被拒绝且消耗提交标记', () => {const {c,shots}=context(); c._0x4b3cc6({pos:{x:NaN,y:421},dir:NaN},Infinity,0); assert.equal(shots.length,1); assert.equal(shots[0].force,Infinity); assert.ok(Number.isNaN(shots[0].angle)); assert.equal(c._carromAiShotTurn,1);});
test('同回合重复提交被拒绝，新回合可提交', () => {const {c,shots}=context(); const p={pos:{x:320,y:421},dir:1}; c._0x4b3cc6(p,50,0); c._0x4b3cc6(p,50,0); assert.equal(shots.length,1); c._carromTurnId++; c._0x4b3cc6(p,50,0); assert.equal(shots.length,2);});
test('通用调度拒绝旧局但允许同局旧回合', () => {const {c,queue}=context(); let n=0; c._0x338c29(()=>n++,50); c._carromTurnId++; queue.shift().options.onComplete(); assert.equal(n,1); c._0x338c29(()=>n++,50); c._carromRoundId++; queue.shift().options.onComplete(); assert.equal(n,1);});
test('摆位完成回调拒绝旧回合', () => {const {c,queue}=context(); let n=0; c._0x223471=()=>n++; c.Math.random=()=>0.9; c._0x4662ac({pos:{x:320,y:421},dir:1},50,0); c._carromTurnId++; queue.shift().options.onComplete(); assert.equal(n,0);});
test('物理提交异常后同回合不能重试', () => {const {c}=context(); let n=0; c._0x27e1b4[c._0x3797(0x1cd)]=()=>{n++;throw Error('人工物理异常');}; const p={pos:{x:320,y:421},dir:1}; assert.throws(()=>c._0x4b3cc6(p,50,0)); c._0x4b3cc6(p,50,0); assert.equal(n,1);});
test('四个候选函数空目标返回空数组', () => {const {c}=context(); for(const name of ['_0x52106f','_0x25af2a','_0x521eef','_0x30849b']) assert.equal(c[name]({x:60,y:180},[],true).length,0);});
test('实际候选搜索存在可用方案', () => {const {c}=context(); c._0x24c0ca={x:3,y:306,width:634,height:636}; c._0x5ccc96=0.5; c._0x2a9c75=[{x:320,y:600}]; const all=[...c._0x52106f({x:60,y:180},c._0x2a9c75,true),...c._0x25af2a({x:580,y:180},c._0x2a9c75,true),...c._0x521eef({x:60,y:816},c._0x2a9c75,true),...c._0x30849b({x:580,y:816},c._0x2a9c75,true)]; assert.ok(all.length>0); for(const p of all) assert.ok([p.pos.x,p.pos.y,p.dir,p.dist,p.hDot].every(Number.isFinite));});
test('瞄准后的延迟出杆拒绝旧回合', () => {const {c,queue,shots}=context(); c._0x223471({pos:{x:320,y:421},dir:1},50); queue.shift().options.onComplete(); c._carromTurnId++; queue.shift().options.onComplete(); assert.equal(shots.length,0);});
test('结算入口重复进入会安排多个后续任务', () => {const {c,queue}=context(); c._0x56abf7=()=>false; c._0x89ccbb=()=>{}; c._0x5d148e=0; c._0x31089b=[]; c._0x530863=false; c._0xbdafb3(); c._0xbdafb3(); assert.equal(queue.length,2);});
fs.mkdirSync('evidence',{recursive:true});
const report={source:'reference-inputs/current/game.js',sha256:hash,node:process.version,results,limitations:['未启动参考游戏、真实 Planck 或浏览器','所有场景均为人工构造，不能证明自然可达性','通过表示复现断言成立，不表示缺陷已修复']};
fs.writeFileSync('evidence/carrom-readonly-audit.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
