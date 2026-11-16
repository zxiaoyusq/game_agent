// 原型阶段只读诊断：摘录原函数隔离执行 + 明示的数学推导；不加载完整游戏。
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const source = fs.readFileSync('evidence/carrom-fragments.js','utf8');
const decoder = {0x197:'visible',0x294:'worldX',0x1dd:'worldY',0x4cf:'pos',0x1cd:'shoot',0x1c0:'concat',0x1f8:'floor',0x430:'cos',0x1c8:'sin',0x182:'length'};
const results=[];
function check(name,kind,run){run();results.push({name,kind,status:'PASS'});}
function setup(mode=0){
 const calls=[];
 const fallback={pos:{x:320,y:421},dir:1,dist:900};
 const context={Math,Number,Map,_0x157421:i=>{assert.ok(i in decoder,`未核对的字符串索引 ${i}`);return decoder[i]},_carromTurnId:7,_carromAiShotTurn:-1,_carromAiRetryTurn:-1,_carromAiRetryCount:0,_0x3fddb3:true,_0x209883:false,_0x5d148e:mode,_0x4268e2:false,_carromFreestyleQueenState:{phase:'none'},_0x5ebd99:true,_0x55e1a0:162,_0x187453:483,_0x429ae3:421,_0x133600:21.76,_0xc5bee4:{},_0x27e1b4:{shoot:(f,a)=>calls.push({type:'shoot',f,a})},_0x23a7dc:()=>false,_0x3d12d7:()=>fallback,_0xd6b627:(candidate,f)=>calls.push({type:'retry',candidate,f}),_0x24bb4a:()=>calls.push({type:'stopInput'}),_0x5e7a5f:()=>calls.push({type:'playerTurn'}),_0xbdafb3:turn=>calls.push({type:'settle',turn}),_0x338c29:(cb,ms)=>calls.push({type:'schedule',cb,ms}),_0x3e4566:[],_0x2a9c75:[],_0x3231b3:[],_0x2bd695:(a,b)=>Math.hypot(a.x-b.x,a.y-b.y)};
 vm.createContext(context);vm.runInContext(source,context,{timeout:1000});
 return {context,calls,fallback};
}
for(const mode of [0,1,2]){
 check(`模式${mode}：棋子移动2px后，替换候选沿用旧33力度`,'摘录函数隔离执行',()=>{
  const {context:c,calls,fallback}=setup(mode);
  const disc={x:300,y:500};c._0x2a9c75=[disc];
  const candidate={pos:{x:320,y:421},dir:0.8,dist:200,_carromBoardSnapshot:[{disc,group:1,x:298,y:500}]};
  c._0x4b3cc6(candidate,33,0);
  assert.equal(calls.length,1);assert.equal(calls[0].type,'retry');assert.equal(calls[0].candidate,fallback);assert.equal(calls[0].f,33);assert.notEqual(calls[0].f,100);assert.equal(c._carromAiShotTurn,-1);
 });
 check(`模式${mode}：候选连续失效最多2次重试后恢复`,'摘录函数隔离执行',()=>{
  const {context:c,calls}=setup(mode);const candidate={pos:{x:161,y:421},dir:0};
  c._0x4b3cc6(candidate,33,0);c._0x4b3cc6(candidate,33,0);c._0x4b3cc6(candidate,33,0);
  assert.equal(calls.filter(x=>x.type==='retry').length,2);assert.equal(calls.at(-1).type,'playerTurn');
 });
 check(`模式${mode}：有效提交一次，重复回调不二次发射`,'摘录函数隔离执行',()=>{
  const {context:c,calls}=setup(mode);const candidate={pos:{x:320,y:421},dir:1};
  c._0x4b3cc6(candidate,100,0.05);c._0x4b3cc6(candidate,100,0.05);
  const shots=calls.filter(x=>x.type==='shoot');assert.equal(shots.length,1);assert.equal(shots[0].f,100);assert.equal(shots[0].a,Math.PI-1+0.05);assert.equal(calls.at(-1).ms,2300);
 });
}
for(const mode of [1,2]) check(`模式${mode}：queen pending且无fallback转结算`,'摘录函数隔离执行',()=>{
 const {context:c,calls}=setup(mode);c._0x4268e2=true;c._carromFreestyleQueenState.phase='pending';c._0x3d12d7=()=>null;
 c._0x4b3cc6({pos:{x:161,y:421},dir:0},33,0);
 assert.equal(calls.at(-1).type,'settle');assert.equal(calls.at(-1).turn,7);assert.equal(c._carromAiShotTurn,7);
});
check('快照每轴误差边界：1px不重选，1.001px重选','摘录函数隔离执行',()=>{
 const {context:c}=setup();const disc={x:300,y:500};c._0x2a9c75=[disc];const snapshot=[{disc,group:1,x:300,y:500}];
 disc.x=301;disc.y=501;assert.equal(c._carromAiBoardChanged(snapshot),false);
 disc.x=301.001;assert.equal(c._carromAiBoardChanged(snapshot),true);
});
check('路径采样漏检：真实圆扫掠相交，但原函数返回false','摘录函数隔离执行 + 几何断言',()=>{
 const {context:c}=setup();const start={x:320,y:421};const blocker={x:385.28,y:456};c._0x2a9c75=[blocker];
 assert.ok(Math.hypot(blocker.x-start.x,blocker.y-start.y)>37.76);
 assert.equal(c._0x3ea989(start,43.52,0,200),false);
 assert.ok(35 < 21.76+16);assert.ok(65.28>0&&65.28<200);
});
check('排序与上限：hDot最高的长距离候选仍优先，800距离被截为125','数学推导；非原生成器自然运行',()=>{
 const candidates=[{hDot:0.99,dist:800},{hDot:0.98,dist:400}];candidates.sort((a,b)=>b.hDot-a.hDot);
 assert.equal(candidates[0].dist,800);const f=candidates[0].dist/100*60*0.2*1.1*1.25;assert.ok(Math.abs(f-132)<1e-9);assert.equal(Math.min(f,125),125);
});
check('显示角、提交角、最终力向量一致','数学推导；非渲染与物理引擎运行',()=>{
 for(const dir of [-2,-0.3,0,1.2,3])for(const error of [-0.1,0,0.1]){
  const display=Math.PI+dir-error;const submitted=Math.PI-dir+error;const vectorAngle=-submitted+Math.PI;
  assert.ok(Math.abs(-Math.cos(display)-Math.cos(vectorAngle))<1e-12);assert.ok(Math.abs(-Math.sin(display)-Math.sin(vectorAngle))<1e-12);
 }
});
const report={attempt:1,scope:'原型只读审计；不等价于完整游戏验收',sourceFragmentSha256:crypto.createHash('sha256').update(source).digest('hex'),naturalReachability:'未执行',browser:'未执行',results};
fs.writeFileSync('evidence/audit-checks.json',JSON.stringify(report,null,2));
console.log(`只读诊断：${results.length}项断言通过；自然对局与浏览器未执行。`);
console.log(JSON.stringify(report,null,2));
