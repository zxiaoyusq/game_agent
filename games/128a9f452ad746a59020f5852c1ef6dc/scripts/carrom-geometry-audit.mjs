// 只读审查辅助：不执行、不修改参考游戏；合成几何不代表真实物理进球。
import fs from 'node:fs';
import assert from 'node:assert/strict';
const refs = [
  'mcp-inputs/mac-codex/4d4eab92df392599c54730b6e087a0949d4875f602c010358e18095007e2275d/Carrom_retry_4d4eab92.js',
  'mcp-inputs/mac-codex/98cdce5f52ad498f6aea9fabb86f9c9020ad7b5c594c9cd6c1ac9dd03a769262/Carrom_ai_force_98cdce5f.js'
];
const evidence = { scope: '独立合成几何；参考正文通过read_reference阅读，未启动游戏', references: refs.map(ref=>({path:ref,status:'NEEDS_CONTEXT',reason:'脚本不读取或执行参考源码；未取得完整文件哈希及全文调用检索证据'})), cases: [] };
const distance = (a,b) => Math.hypot(a.x-b.x,a.y-b.y);
const point = (a,u,t) => ({x:a.x+u.x*t,y:a.y+u.y*t});
// 按已读源码还原采样语义，非调用游戏中的混淆函数。
function sampled(a,b,h,pieces) {
  const angle=Math.atan2(b.y-a.y,b.x-a.x), length=distance(a,b);
  const q={...a}; const samples=[]; let blocked=false;
  for(let i=0;i<Math.floor(length/h);i++) {
    q.x+=Math.cos(angle)*h; q.y+=Math.sin(angle)*h;
    samples.push({...q});
    if(pieces.some(p=>distance(q,p)<h*.9)){blocked=true;break;}
  }
  return {blocked, samples, length, radius:h*.9};
}
function segmentDistance(a,b,p) {
  const dx=b.x-a.x,dy=b.y-a.y,l2=dx*dx+dy*dy;
  const t=l2?Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/l2)):0;
  return distance({x:a.x+dx*t,y:a.y+dy*t},p);
}
// 仅验证接触契约的研究模型：真实切点、指定移动体、唯一终端目标。
// 终端目标必须位于真实半径和的切点，且沿入射方向靠近；不可全段豁免。
function contract(a,b,moverRadius,pieces,moverId=null,terminalId=null) {
  const length=distance(a,b), eps=1e-7;
  if(!Number.isFinite(length)||length<=eps) return {blocked:true, reason:'invalid-segment'};
  const u={x:(b.x-a.x)/length,y:(b.y-a.y)/length};
  for(const p of pieces) {
    if(p.id===moverId) continue;
    const radius=moverRadius+p.radius;
    if(p.id===terminalId) {
      const end=distance(b,p), dot=(p.x-b.x)*u.x+(p.y-b.y)*u.y;
      if(Math.abs(end-radius)>eps||dot<=eps||distance(a,p)<radius-eps) return {blocked:true,reason:'invalid-terminal'};
      // 非零正向入射使终点前在圆外；仍核对全段最短距离。
      if(segmentDistance(a,b,p)<radius-eps) return {blocked:true,reason:'early-terminal'};
    } else if(segmentDistance(a,b,p)<radius-eps) return {blocked:true,reason:'third-body'};
  }
  if(terminalId&&!pieces.some(p=>p.id===terminalId)) return {blocked:true,reason:'missing-terminal'};
  return {blocked:false};
}
function add(name,input,expected,level='纯几何') {
  const legacy=sampled(input.a,input.b,input.h,input.pieces);
  const continuous=input.pieces.filter(p=>p.id!==input.moverId).some(p=>segmentDistance(input.a,input.b,p)<input.moverRadius+p.radius);
  const semantic=contract(input.a,input.b,input.moverRadius,input.pieces,input.moverId,input.terminalId);
  if('legacy' in expected)assert.equal(legacy.blocked,expected.legacy,name);
  if('contract' in expected)assert.equal(semantic.blocked,expected.contract,name);
  if('continuous' in expected)assert.equal(continuous,expected.continuous,name);
  evidence.cases.push({name,level,input,expected,legacy,continuousBlocked:continuous,contract:semantic,status:'PASS'});
}
const puck=(id,x,y)=>({id,x,y,radius:16});
add('普通子内部采样间掠碰',{a:{x:0,y:0},b:{x:120,y:0},h:30,moverRadius:16,pieces:[puck('O',45,26)]},{legacy:false,continuous:true,contract:true});
add('击球器内部采样间掠碰',{a:{x:0,y:0},b:{x:174.08,y:0},h:43.52,moverRadius:21.76,pieces:[puck('O',65.28,35)]},{legacy:false,continuous:true,contract:true});
add('短于步长零采样',{a:{x:0,y:0},b:{x:20,y:0},h:30,moverRadius:16,pieces:[puck('O',19,31)]},{legacy:false,continuous:true,contract:true});
add('非整倍数末段遗漏',{a:{x:0,y:0},b:{x:89,y:0},h:30,moverRadius:16,pieces:[puck('O',89,31)]},{legacy:false,continuous:true,contract:true});
add('零长段必须拒绝',{a:{x:0,y:0},b:{x:0,y:0},h:30,moverRadius:16,pieces:[puck('O',0,0)]},{legacy:false,contract:true});
add('严格小于阈值边界',{a:{x:0,y:0},b:{x:60,y:0},h:30,moverRadius:16,pieces:[puck('O',30,27)]},{legacy:false,continuous:true,contract:true});
add('旧ghost整倍数末采样误杀',{a:{x:0,y:0},b:{x:87.04,y:0},h:43.52,moverRadius:21.76,terminalId:'T',pieces:[puck('T',123.8,0)]},{legacy:true,contract:true});
add('真实切点合法接触仍被旧阈值误杀',{a:{x:0,y:0},b:{x:87.04,y:0},h:43.52,moverRadius:21.76,terminalId:'T',pieces:[puck('T',124.8,0)]},{legacy:true,contract:false});
add('真实切点非整倍数合法接触',{a:{x:0,y:0},b:{x:90,y:0},h:43.52,moverRadius:21.76,terminalId:'T',pieces:[puck('T',127.76,0)]},{legacy:false,contract:false});
add('普通子到袋口不得把移动子当障碍',{a:{x:0,y:0},b:{x:120,y:0},h:30,moverRadius:16,moverId:'M',pieces:[puck('M',0,0)]},{legacy:false,contract:false});
add('组合末端真实接触合法',{a:{x:0,y:0},b:{x:120,y:0},h:30,moverRadius:16,moverId:'M',terminalId:'T',pieces:[puck('M',0,0),puck('T',152,0)]},{legacy:false,contract:false});
add('组合不能豁免第三子',{a:{x:0,y:0},b:{x:120,y:0},h:30,moverRadius:16,moverId:'M',terminalId:'T',pieces:[puck('M',0,0),puck('T',152,0),puck('O',60,0)]},{legacy:true,contract:true});
add('全局排除目标会掩盖提前穿透',{a:{x:0,y:0},b:{x:120,y:0},h:30,moverRadius:16,terminalId:'T',pieces:[puck('T',60,0)]},{legacy:true,contract:true});
add('反弹连接点第三子不可忽略',{a:{x:0,y:0},b:{x:29,y:0},h:43.52,moverRadius:21.76,pieces:[puck('O',29,37)]},{legacy:false,contract:true});
const s={x:250,y:421},u={x:-.6,y:.8};
// 精确baseline候选：BL方向、x/y区域、hDot=1、起点真实clearance均成立。
for(const [suffix,length,offset,expect] of [['miss',130.56,3,false],['terminal',130.56,2,true]]) {
  const L=length+offset,g=point(s,u,L),t=point(g,u,36.76);
  const pocket={x:61,y:886};
  // 将T置于固定袋口射线上，反求S.x，保证不是假袋口数学替代。
  const d=(pocket.y-t.y)/u.y;
  const shift=pocket.x-(t.x+u.x*d);
  const a={x:s.x+shift,y:s.y},b={x:g.x+shift,y:g.y},target=puck('T',t.x+shift,t.y);
  assert(a.x>=162&&a.x<=483);assert(target.y>=436&&target.y<886&&target.x>=61);
  assert(distance(a,target)>37.76);
  let pieces=[target];
  if(suffix==='miss') {
    const mid=point(a,u,65.28),normal={x:-u.y,y:u.x};
    pieces.push(puck('O',mid.x+normal.x*35,mid.y+normal.y*35));
  }
  assert.equal(sampled(target,pocket,30,pieces).blocked,false,'出袋段不应阻挡');
  add('BL精确直击候选-'+suffix,{a,b,h:43.52,moverRadius:21.76,terminalId:'T',pieces,pocket,hDot:1}, {legacy:expect,continuous:true,contract:true},'候选公式及区域约束可达；未执行原候选函数');
  if(suffix==='miss') {
    const mid=point(target,u,45),normal={x:-u.y,y:u.x};
    const third=puck('O2',mid.x+normal.x*26,mid.y+normal.y*26);
    assert.equal(sampled(a,b,43.52,[target,third]).blocked,false,'入射段旧检测通过');
    assert(distance(target,third)>=32);
    add('BL固定袋口普通子漏检',{a:target,b:pocket,h:30,moverRadius:16,moverId:'T',pieces:[target,third],strikerStart:a,strikerGhost:b}, {legacy:false,continuous:true,contract:true},'精确直击公式与两段旧检测通过；未执行原候选函数');
  }
}
// 另给固定袋口的合法真实切点，证明不能用全障碍闭线段检测替换。
const L=130.56, g=point(s,u,L),t=point(g,u,37.76),d=(886-t.y)/u.y,shift=61-(t.x+u.x*d);
add('BL固定袋口真实切点保护',{a:{x:s.x+shift,y:421},b:{x:g.x+shift,y:g.y},h:43.52,moverRadius:21.76,terminalId:'T',pieces:[puck('T',t.x+shift,t.y)],pocket:{x:61,y:886}}, {contract:false},'真实切点设计保护；非当前ghost候选');
const forceCases=[60,100,120,200].map(force=>({input:force,capped:Math.min(force,125),retryA:100,retryB:Math.min(force,125)}));
assert.deepEqual(forceCases.map(c=>c.retryB),[60,100,120,125]);
evidence.forceCases=forceCases;
evidence.count=evidence.cases.length;
evidence.result='PASS：合成断言通过；不代表原游戏验收';
fs.mkdirSync('evidence',{recursive:true});
fs.writeFileSync('evidence/carrom-geometry-results.json',JSON.stringify(evidence,null,2));
console.log(`合成几何断言通过：${evidence.count}项；未执行原游戏；输出 evidence/carrom-geometry-results.json`);
