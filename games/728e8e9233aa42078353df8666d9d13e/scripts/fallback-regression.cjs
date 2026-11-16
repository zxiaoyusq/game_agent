// 仅原型阶段：逐字转录已读取的几何函数，在隔离上下文做合成数据测试。
// 不加载原游戏、不模拟 Planck、不宣称设备或浏览器验收。
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { performance } = require('node:perf_hooks');
const before = `function _carromStartPathBlocked(origin, angle, length, intendedTarget) {
      if (!origin || !Number.isFinite(origin.x) || !Number.isFinite(origin.y) ||
          !Number.isFinite(angle) || !Number.isFinite(length) || length < 0) return true;
      if (length === 0) return false;
      var dx = Math.cos(angle), dy = Math.sin(angle), end = Math.min(length, _0x133600 * 2),
        radius = _0x133600 + 16, discs = _0x3e4566.concat(_0x2a9c75, _0x3231b3);
      for (var disc of discs) {
        if (disc === intendedTarget) continue;
        if (!disc || !Number.isFinite(disc.x) || !Number.isFinite(disc.y)) return true;
        var x = disc.x - origin.x, y = disc.y - origin.y,
          along = Math.max(0, Math.min(end, x * dx + y * dy)),
          ex = x - along * dx, ey = y - along * dy;
        if (ex * ex + ey * ey < radius * radius) return true;
      }
      return false;
    }`;
const after = before.replace('intendedTarget)', 'intendedTarget, fullFallbackPath)').replace('end = Math.min(length, _0x133600 * 2)', 'end = fullFallbackPath ? Math.max(0, length - (_0x133600 + 16)) : Math.min(length, _0x133600 * 2)');
const r = 0x22 * 0.8 * 0.8, R = r + 16;
function engine(text) {
  const ctx=vm.createContext({_0x133600:r,_0x3e4566:[],_0x2a9c75:[],_0x3231b3:[]});
  vm.runInContext(text,ctx,{timeout:1000});
  return {ctx, call:ctx._carromStartPathBlocked};
}
const old=engine(before), current=engine(after);
function check(groups, origin={x:0,y:0}, angle=0, length=300, target={x:300,y:0}, full=true, eng=current) {
  [eng.ctx._0x3e4566,eng.ctx._0x2a9c75,eng.ctx._0x3231b3]=groups;
  return eng.call(origin,angle,length,target,full);
}
function hitTime(p,origin,angle,radius=R) {
  const dx=p.x-origin.x,dy=p.y-origin.y,u=dx*Math.cos(angle)+dy*Math.sin(angle);
  const cross=dx*Math.sin(angle)-dy*Math.cos(angle), q=radius*radius-cross*cross;
  if(q<0) return Infinity;
  const a=u-Math.sqrt(q),b=u+Math.sqrt(q);
  return b<0 ? Infinity : Math.max(0,a);
}
const results=[];
function test(name,fn){try {const detail=fn();results.push({name,status:'PASS',detail:detail??null});} catch(e){results.push({name,status:'FAIL',error:e.stack});}}
test('直线目标无阻挡且身份豁免',()=>{const t={x:300,y:0};assert.equal(check([[t],[],[]],undefined,0,300,t),false);});
test('远处阻挡由旧漏检变为新命中',()=>{const g=[[{x:150,y:0}],[],[]];assert.equal(check(g,undefined,0,300,undefined,false,old),false);assert.equal(check(g),true);});
test('起点端帽检查负投影初始重叠',()=>assert.equal(check([[{x:-10,y:5}],[],[]]),true));
test('远离起点的后方棋不阻挡',()=>assert.equal(check([[{x:-R-2,y:0}],[],[]]),false));
test('终点端帽检查投影超过终点的提前碰撞',()=>{const p={x:280,y:20};assert(hitTime(p,{x:0,y:0},0)<300-R);assert.equal(check([[p],[],[]]),true);});
test('目标首次接触之后的棋不阻挡',()=>assert.equal(check([[{x:320,y:0}],[],[]]),false));
test('严格切线及两侧微扰',()=>{assert.equal(check([[{x:150,y:R}],[],[]]),false);assert.equal(check([[{x:150,y:R-1e-7}],[],[]]),true);assert.equal(check([[{x:150,y:R+1e-7}],[],[]]),false);});
test('三组任一棋都可阻挡，与颜色无关',()=>{for(let k=0;k<3;k++){const g=[[],[],[]];g[k].push({x:150,y:0});assert.equal(check(g),true);}});
test('多棋顺序不改变有限有效数据结果',()=>{const a={x:150,y:0},b={x:310,y:80};assert.equal(check([[a,b],[],[]]),check([[b,a],[],[]]));});
test('仅对象身份豁免，坐标副本在短路径自阻挡',()=>{const t={x:60,y:0};assert.equal(check([[t],[],[]],undefined,0,60,t,false),false);assert.equal(check([[t],[],[]],undefined,0,60,{...t},false),true);});
test('克隆目标的终点切线受浮点消减误差影响',()=>{const t={x:300,y:0},actual=check([[t],[],[]],undefined,0,300,{...t}),offset=300-(300-R);assert.equal(actual,offset*offset<R*R);return {blocked:actual,offset,radius:R,residual:offset*offset-R*R};});
test('未在棋盘上的目标不被合法性校验拒绝',()=>assert.equal(check([[],[],[]],undefined,0,300,{x:300,y:0}),false));
test('被豁免目标含 NaN 仍放行',()=>{const t={x:NaN,y:0};assert.equal(check([[t],[],[]],undefined,0,300,t),false);});
test('普通错误棋 fail-closed',()=>{for(const p of [null,undefined,{x:NaN,y:0},{x:Infinity,y:0},{x:"150",y:0}]) assert.equal(check([[p],[],[]],undefined,0,300,{}),true);});
test('null身份先跳过可吞掉错误棋',()=>assert.equal(check([[null],[],[]],undefined,0,300,null),false));
test('零长度提前放行重叠与错误数据',()=>assert.equal(check([[null,{x:0,y:0}],[],[]],undefined,0,0,{}),false));
test('短于半径和仍检测起点重叠',()=>assert.equal(check([[{x:0,y:0}],[],[]],undefined,0,10,{}),true));
test('非法输入基本门禁',()=>{for(const [o,a,l] of [[null,0,30],[{x:NaN,y:0},0,30],[{x:0,y:0},NaN,30],[{x:0,y:0},0,-1],[{x:0,y:0},0,Infinity]])assert.equal(check([[],[],[]],o,a,l),true);});
test('有限但极大坐标算术溢出会放行',()=>assert.equal(check([[{x:1e308,y:0}],[],[]],{x:-1e308,y:0},0,1e308,{}),false));
test('真值字符串误启用全程',()=>{const g=[[{x:150,y:0}],[],[]];assert.equal(check(g,undefined,0,300,{},false),false);assert.equal(check(g,undefined,0,300,{},'false'),true);});
test('非共线目标使中心距减半径和终点提前，产生漏检',()=>{const t={x:300,y:30}, length=Math.hypot(t.x,t.y),p={x:310,y:0};assert(hitTime(p,{x:0,y:0},0)<hitTime(t,{x:0,y:0},0));assert.equal(check([[p,t],[],[]],undefined,0,length,t),false);return {targetContact:hitTime(t,{x:0,y:0},0),blockerContact:hitTime(p,{x:0,y:0},0),assumedEnd:length-R};});
test('固定16宽度对物理半径15产生保守误报',()=>{const p={x:150,y:r+15.5};assert.equal(check([[p],[],[]]),true);assert.equal(hitTime(p,{x:0,y:0},0,r+15),Infinity);});
test('异半径目标15阻挡16的理论提前截断反例',()=>{const q={x:300+0.5,y:0};assert.equal(check([[q],[],[]]),false);assert(hitTime(q,{x:0,y:0},0,R)<300-(r+15));});
test('随机偏角0.1可把名义安全路径变成提前撞棋',()=>{const t={x:300,y:0},p={x:150,y:40};assert.equal(check([[p,t],[],[]],undefined,0,300,t),false);assert(hitTime(p,{x:0,y:0},0.1)<hitTime(t,{x:0,y:0},0.1));return {targetContact:hitTime(t,{x:0,y:0},0.1),blockerContact:hitTime(p,{x:0,y:0},0.1)};});
let state=123456789;function random(){state=(1664525*state+1013904223)>>>0;return state/4294967296;}
test('四参数普通调用3000固定种子兼容比较',()=>{for(let i=0;i<3000;i++){const g=Array.from({length:3},()=>Array.from({length:6},()=>({x:random()*600-100,y:random()*500-250})));const o={x:random()*100,y:random()*100},a=random()*Math.PI*2,l=random()*700;check(g,o,a,l,null,false,old);check(g,o,a,l,null,false);assert.equal(old.call(o,a,l,null),current.call(o,a,l,null));}});
// 以下为源码控制流的等价模型，不是原混淆函数直接集成测试。
function choose(mode,own,other,queen){let targets=mode===2?own.concat(other,queen):own.length===1&&queen.length?queen.slice():own.slice();if(!targets.length)targets=targets.concat(other,queen);return targets;}
test('模式0/1/2目标池及空池回退等价模型',()=>{const a={},b={},q={};for(const m of [0,1]){assert.deepEqual(choose(m,[a,a],[b],[q]),[a,a]);assert.deepEqual(choose(m,[a],[b],[q]),[q]);assert.deepEqual(choose(m,[],[b],[q]),[b,q]);}assert.deepEqual(choose(2,[a],[b],[q]),[a,b,q]);assert.deepEqual(choose(0,[],[],[]),[]);});
function scan(initial,isBlocked,placementBlocked=()=>false){let pos=initial,visited=[];if(isBlocked(initial)){for(let k=0;k<=6;k++){const x=162+321*k/6;visited.push(x);if(placementBlocked(x))continue;if(!isBlocked(x)){pos=x;break;}}}return {pos,visited};}
test('七点全挡仍返回原位置，不能宣称安全',()=>{const s=scan(320,()=>true);assert.equal(s.pos,320);assert.equal(s.visited.length,7);});
test('七点按左到右取第一个通过位置',()=>assert.equal(scan(320,x=>x!==269).pos,269));
test('存在未采样窄通道仍会错过',()=>{const s=scan(320,x=>!(x>240&&x<245));assert.equal(s.pos,320);assert.equal(s.visited.length,7);});
test('初始路径已安全不执行七点扫描',()=>assert.equal(scan(320,()=>false).visited.length,0));
test('位置禁止优先于路径检测',()=>{const s=scan(320,()=>true,()=>true);assert.equal(s.visited.length,7);assert.equal(s.pos,320);});
const bench=[];
for(const n of [19,100,1000]){const groups=[Array.from({length:n},(_,i)=>({x:100+i,y:1000})),[],[]];for(let k=0;k<1000;k++)check(groups);const start=performance.now();for(let k=0;k<5000;k++)check(groups);bench.push({discs:n,calls:5000,elapsedMs:performance.now()-start});}
fs.mkdirSync('evidence',{recursive:true});
const report={kind:'转录几何函数合成回归；含等价控制流模型，非目标游戏运行验证',node:process.version,attempt:1,constants:{strikerRadius:r,assumedCoinRadius:16,capsuleRadius:R},passed:results.filter(x=>x.status==='PASS').length,failed:results.filter(x=>x.status==='FAIL').length,results,benchmark:{kind:'当前Node环境合成微基准，不是手机性能',samples:bench},scriptSha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),transcriptionSha256:{before:crypto.createHash('sha256').update(before).digest('hex'),after:crypto.createHash('sha256').update(after).digest('hex')}};
fs.writeFileSync('evidence/fallback-regression.json',JSON.stringify(report,null,2));
console.log('合成回归：通过'+report.passed+'，失败'+report.failed+'；详见 evidence/fallback-regression.json');
for(const x of results.filter(x=>x.status==='FAIL'))console.error(x.name+'\n'+x.error);
console.log('Node合成微基准：'+JSON.stringify(bench));
process.exitCode=report.failed?1:0;
