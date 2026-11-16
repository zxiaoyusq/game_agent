// 中文：原型审查脚本；仅执行独立几何模型，不装载原游戏或远程服务。
import assert from 'node:assert/strict';
import {readFileSync, mkdirSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {trajectoryBlocked as trajectory, startPathBlocked as start, safeDeviation as safe, circleEntry, captureBoard, boardChanged} from './audit-model.mjs';
const results = [];
function test(id, fn) { try { const detail = fn(); results.push({id, status:'PASS', detail: detail || '断言通过（独立模型）'}); } catch (error) { results.push({id,status:'FAIL', detail:error.stack}); } }
function setup(target={x:400,y:400}, obstacles=[], origin={x:300,y:300}, board={x:0,y:0,width:600,height:600}, strikerRadius=22) {
  return {context:{strikerRadius,board,groups:[[target],obstacles,[]]},shot:{pos:origin,dir:Math.atan2(target.y-origin.y,target.x-origin.x),_carromFallbackTarget:target}};
}
function trace(s, angle, version='after') { const t={}; const blocked=trajectory(s.context,s.shot,angle,version,t); return {...t,blocked}; }
function near(a,b,e=1e-9) { assert.ok(Math.abs(a-b)<=e, `${a} 与 ${b} 的误差超过 ${e}`); }
test('G01-补漏',()=>{const s=setup(undefined,[{x:500,y:300}]);assert.equal(trace(s,0,'before').blocked,false);assert.equal(trace(s,0).blocked,true);near(trace(s,0).travel,252);});
test('G02-真实偏差幅度回零',()=>{const s=setup({x:550,y:300},[{x:700,y:360}],{x:100,y:300},{x:0,y:0,width:800,height:600});assert.equal(safe(s.context,s.shot,-.1,'before'),-.1);assert.equal(safe(s.context,s.shot,-.1),0);});
test('G03-余量抵消',()=>{const s=setup(undefined,[{x:595,y:300}]);const t=trace(s,0);near(t.passedLength-t.radius,t.travel);assert.equal(t.blocked,false);});
for (const [id,angle,target] of [['右',0,{x:400,y:400}],['左',Math.PI,{x:400,y:400}],['下',Math.PI/2,{x:400,y:400}],['上',-Math.PI/2,{x:400,y:400}]]) test('G04-'+id,()=>near(trace(setup(target),angle).travel,252));
test('G05-极小方向分量',()=>{for(const a of [1e-14,-1e-14,Math.PI/2+1e-14]) near(trace(setup(),a).travel,252,1e-8);});
test('G06-边界向外零段',()=>{const s=setup({x:400,y:400},[{x:48,y:310}],{x:48,y:300});const t=trace(s,Math.PI);near(t.travel,0);assert.equal(t.blocked,true);assert.equal(start(s.context,s.shot.pos,Math.PI,0,null,true),false);});
test('G07-边界向内与沿墙',()=>{const s=setup({x:400,y:400},[],{x:48,y:300});near(trace(s,Math.PI/2).travel,252);near(trace(s,0).travel,504);});
test('G07b-边界数学平行浮点向外',()=>{const s=setup({x:450,y:400},[],{x:552,y:300});near(trace(s,Math.PI/2).travel,0);return 'cos(PI/2)>0，在右边界使 tx=0；不是精确平行语义。';});
test('G08-角点同距',()=>{const s=setup({x:400,y:200});near(trace(s,Math.PI/4).travel,252*Math.SQRT2);});
test('G09-无效棋盘回退',()=>{for(const board of [undefined,null,{x:0,y:0,width:80,height:600},{x:NaN,y:0,width:600,height:600},{x:0,y:0,width:-600,height:600}]) {const s=setup();s.context.board=board;near(trace(s,0).travel,Math.sqrt(20000));}});
test('G10-起点在矩形外回退',()=>{const s=setup({x:100,y:400},[],{x:47,y:300});near(trace(s,0).travel,Math.hypot(53,100));});
test('G11-目标在射线后方',()=>near(trace(setup({x:200,y:300}),0).travel,252));
test('G12-命中保留旧行为',()=>{const s=setup({x:400,y:300});const a=trace(s,0),b=trace(s,0,'before');near(a.travel,62);assert.deepEqual(a,b);});
test('G13-擦边截断不连续',()=>{const board={x:0,y:0,width:800,height:600},origin={x:100,y:300};const a=setup({x:460,y:338},[{x:600,y:300}],{...origin},board);const b=setup({x:460,y:338.0001},[{x:600,y:300}],{...origin},board);near(trace(a,0).travel,360,1e-6);near(trace(b,0).travel,652);assert.equal(trace(a,0).blocked,false);assert.equal(trace(b,0).blocked,true);});
test('G13b-消差改变精确切线分支',()=>{const s=setup({x:400,y:338},[{x:500,y:300}]);assert.equal(circleEntry(s.shot.pos,0,s.shot._carromFallbackTarget,38),100);assert.equal(trace(s,0).targetHit,false);return '当前 Node 中 distance²-projection² 的消差使数学切线走未命中分支；无容差。';});
test('G14-障碍恰切不受阻',()=>{const s=setup(undefined,[{x:500,y:338}]);assert.equal(trace(s,0).blocked,false);s.context.groups[1][0].y-=1e-4;assert.equal(trace(s,0).blocked,true);});
test('G15-同接触严格边界',()=>{const s=setup({x:400,y:300},[{x:400,y:300}]);assert.equal(trace(s,0).blocked,false);s.context.groups[1][0].x-=1e-6;assert.equal(trace(s,0).blocked,true);return '重合圆用于隔离严格边界语义；不是声称合法棋盘可重合。';});
test('G16-中心在后但首接触在前不是误判',()=>{const s=setup({x:400,y:334},[{x:415,y:300}]);const t=trace(s,0);assert.ok(circleEntry(s.shot.pos,0,s.context.groups[1][0],38)<t.targetEntry);assert.equal(t.blocked,true);});
test('G17-真正在目标接触之后不受阻',()=>{const s=setup({x:400,y:300},[{x:435,y:300}]);assert.equal(trace(s,0).blocked,false);});
test('G18-墙可缩短而非一律延伸',()=>{const s=setup({x:500,y:500},[{x:540,y:300}],{x:530,y:300});near(trace(s,0).travel,22);assert.ok(trace(s,0,'before').travel>22);});
test('G19-首反弹未覆盖',()=>{const obstacle={x:752,y:726};const s=setup({x:400,y:200},[obstacle],{x:300,y:300},{x:0,y:0,width:1000,height:1000});const a=Math.atan(.5),t=trace(s,a);assert.equal(t.blocked,false);const hit={x:952,y:626};near(s.shot.pos.x+t.travel*Math.cos(a),hit.x);near(s.shot.pos.y+t.travel*Math.sin(a),hit.y);assert.ok(circleEntry(hit,Math.atan2(.5,-1),obstacle,38)<Infinity);return '另行解析反弹段可碰同一棋子；原函数只检查第一直段（不推断实际反弹速度）。';});
test('G20-原方向也受阻不回零',()=>{const s=setup({x:550,y:300},[{x:200,y:300},{x:700,y:360}],{x:100,y:300},{x:0,y:0,width:800,height:600});assert.equal(safe(s.context,s.shot,-.1),-.1);});
test('G21-零偏差与异常偏差',()=>{const s=setup();assert.equal(safe(s.context,s.shot,0),0);assert.ok(Number.isNaN(safe(s.context,s.shot,NaN)));});
test('G22-目标失效三值结果',()=>{const s=setup();s.context.groups[0]=[];assert.equal(trace(s,0).blocked,null);assert.equal(safe(s.context,s.shot,.1),.1);});
test('G23-近目标与无效输入',()=>{const s=setup({x:310,y:300});assert.equal(trace(s,0).blocked,null);assert.equal(trajectory(s.context,null,0),null);assert.equal(trace(setup(),Infinity).blocked,null);});
test('G24-派生距离溢出',()=>{const s=setup({x:1e308,y:1e308});assert.equal(trace(s,0).blocked,null);});
test('G25-非法棋子保守阻挡',()=>{assert.equal(trace(setup(undefined,[{x:NaN,y:300}]),0).blocked,true);});
test('G26-物理半径与单位',()=>{const r=34*.8*.8;near(r,21.76);near(r+16,37.76);const s=setup(undefined,[],undefined,undefined,r);near(trace(s,0).travel,252.24);near((r+16)/100,.3776);});
test('G27-平移不变性',()=>{const s=setup();const t=trace(s,0);for(const p of [...s.context.groups.flat(),s.shot.pos,s.context.board]) {p.x+=100;p.y-=200;}near(trace(s,0).travel,t.travel);});
test('G28-角度符号',()=>{for(const dir of [0,.3,Math.PI,-Math.PI/2])for(const dev of [-.1,0,.1]) {const passed=Math.PI-dir+dev;near(Math.cos(-passed+Math.PI),Math.cos(dir-dev));near(Math.sin(-passed+Math.PI),Math.sin(dir-dev));}});
test('G29-袋口先于墙的几何反例',()=>{const board={x:5,y:306,width:630,height:636};const origin={x:320,y:421},pocket={x:61,y:362},r=21.76;const a=Math.atan2(pocket.y-origin.y,pocket.x-origin.x);const s=setup({x:320,y:600},[],origin,board,r);const t=trace(s,a);const p=circleEntry(origin,a,pocket,20);assert.ok(p<t.travel);const obstacle={x:48,y:392};s.context.groups[1]=[obstacle];assert.ok(circleEntry(origin,a,obstacle,r+16)>p);assert.equal(trace(s,a).blocked,true);return {pocketEntry:p,wallDistance:t.travel,warning:'连续几何可先入袋；每帧离散袋口检测与棋盘配置真实性尚未验证。'};});
test('G30-墙距解析性质随机2000次',()=>{let seed=1234567;function random(){seed=(1664525*seed+1013904223)>>>0;return seed/2**32;}let compared=0;for(let i=0;i<2000;i++){const origin={x:49+502*random(),y:49+502*random()},a=-Math.PI+2*Math.PI*random();const s=setup({x:origin.x+100*Math.cos(a+Math.PI/2),y:origin.y+100*Math.sin(a+Math.PI/2)},[],origin);const t=trace(s,a);const end={x:origin.x+t.travel*Math.cos(a),y:origin.y+t.travel*Math.sin(a)};assert.ok(end.x>=48-1e-8&&end.x<=552+1e-8&&end.y>=48-1e-8&&end.y<=552+1e-8);assert.ok(Math.min(Math.abs(end.x-48),Math.abs(end.x-552),Math.abs(end.y-48),Math.abs(end.y-552))<1e-8);compared++;}return {seed:1234567,compared};});
test('G31-非备用检测不改',()=>{const s=setup(undefined,[{x:500,y:300}]);assert.equal(start(s.context,s.shot.pos,0,500,null,false),false);assert.equal(start(s.context,s.shot.pos,0,500,null,true),true);});
test('S01-快照未变',()=>{const s=setup();assert.equal(boardChanged(s.context,captureBoard(s.context)),false);});
test('S02-目标移除',()=>{const s=setup(),snap=captureBoard(s.context);s.context.groups[0]=[];assert.equal(boardChanged(s.context,snap),true);assert.equal(trace(s,0).blocked,null);});
test('S03-目标替换同坐标',()=>{const s=setup(),snap=captureBoard(s.context);s.context.groups[0]=[{...s.shot._carromFallbackTarget}];assert.equal(boardChanged(s.context,snap),true);});
test('S04-目标换组',()=>{const s=setup(),snap=captureBoard(s.context);s.context.groups[2]=s.context.groups[0];s.context.groups[0]=[];assert.equal(boardChanged(s.context,snap),true);});
test('S05-快照位移阈值每轴严格大于1',()=>{const s=setup(),snap=captureBoard(s.context);s.shot._carromFallbackTarget.x+=1;s.shot._carromFallbackTarget.y+=1;assert.equal(boardChanged(s.context,snap),false);s.shot._carromFallbackTarget.x+=.0001;assert.equal(boardChanged(s.context,snap),true);});
test('S06-快照非法与重复对象',()=>{const s=setup(),snap=captureBoard(s.context);assert.equal(boardChanged(s.context,null),true);assert.equal(boardChanged(s.context,[...snap,...snap]),true);s.shot._carromFallbackTarget.x=NaN;assert.equal(boardChanged(s.context,snap),true);});
// 中文：成本只是当前 Node 模型微基准，不能代替 H5 / 低端设备实测。
const benchmarks=[];
for(const count of [19,2000]) { const s=setup();s.context.groups[1]=Array.from({length:count},(_,i)=>({x:100+i*.001,y:500}));for(const version of ['before','after']) {for(let i=0;i<1000;i++)trajectory(s.context,s.shot,0,version);const times=[];for(let round=0;round<5;round++){const begin=performance.now();for(let i=0;i<5000;i++)trajectory(s.context,s.shot,0,version);times.push(performance.now()-begin);}benchmarks.push({count,version,iterationsPerRound:5000,rounds:5,ms:times});}}
const sources=['scripts/audit-model.mjs','scripts/run-audit.mjs'].map(path=>({path,sha256:createHash('sha256').update(readFileSync(path)).digest('hex')}));
mkdirSync('evidence',{recursive:true});
const report={stage:'prototype',attempt:4,scope:'独立转写几何模型，不是原游戏运行验收',node:process.version,platform:process.platform,arch:process.arch,sources,results,benchmarks,passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length};
writeFileSync('evidence/geometry-audit.json',JSON.stringify(report,null,2)+'\n');
for(const r of results)console.log(`${r.status} ${r.id}${r.status==='FAIL'?' '+r.detail:''}`);
console.log(`中文：独立模型通过 ${report.passed}，失败 ${report.failed}；详情 evidence/geometry-audit.json`);
process.exitCode=report.failed?1:0;
