// 原型审查：只做文本差分与隔离几何验证，不启动或修改参考游戏。
const fs = require('node:fs');
const crypto = require('node:crypto');
const vm = require('node:vm');
const paths = ['reference-inputs/after_d0af667f.js','reference-inputs/before_342e46b7.js'];
try {
// 用户提供ZIP后逐字节提取的两份冻结源码；全文比较不执行宿主代码。
const buffers=paths.map(p=>fs.readFileSync(p));
const metadata=buffers.map((b,i)=>({path:paths[i],bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')}));
if(metadata[0].sha256!=='d0af667f4c37f50845e94588d3f705c169a3e680c9c247e7477bc2d98609b2ac'||metadata[1].sha256!=='342e46b75c9b2c5023756b13d1ec1939c2ac83880659ec45de17c126dec118ad') throw Error('冻结源码哈希不匹配');
const [start,base]=buffers.map(b=>b.toString('utf8'));
new vm.Script(start);new vm.Script(base);
const helperStart=start.indexOf('    function _carromStartPathBlocked('),helperEnd=start.indexOf('    function _0x3ea989(',helperStart);
if(helperStart<0||helperEnd<0) throw Error('缺公共函数');
const helper=start.slice(helperStart,helperEnd);
const callPattern=/ \|\| _carromStartPathBlocked\(([^\r\n]+)\)/g;
const calls=[...start.matchAll(callPattern)].map(m=>({line:start.slice(0,m.index).split('\n').length,args:m[1]}));
const restored=(start.slice(0,helperStart)+start.slice(helperEnd)).replace(callPattern,'');
const onlyHelperAnd12Calls=restored===base;
const details={metadata,calls,helper,helperSha256:crypto.createHash('sha256').update(helper).digest('hex'),onlyHelperAnd12Calls,fullDiffStatus:onlyHelperAnd12Calls&&calls.length===12?'PASS：删除一个公共函数与12个OR后，全文逐字符与基线一致（含换行）':'FAIL：存在额外差异'};
if(!onlyHelperAnd12Calls||calls.length!==12) throw Error(details.fullDiffStatus);
const oldStart=base.indexOf('    function _0x3ea989('),oldEnd=base.indexOf('    function _0x247dad(',oldStart);
const oldHelper=base.slice(oldStart,oldEnd);
const context = {_0x133600:21.76,_0x3e4566:[],_0x2a9c75:[],_0x3231b3:[]};
context._0x157421=key=>{if(key===0x1c0)return 'concat';throw Error('未确认的混淆属性');};
vm.createContext(context); vm.runInContext(helper+oldHelper,context);
const results=[];
function check(name,origin,angle,length,discs,target,expected){context._0x3e4566=discs;context._0x2a9c75=[];context._0x3231b3=[];let actual;try {actual=context._carromStartPathBlocked(origin,angle,length,target);}catch(e){actual=e.name;}results.push({name,origin,angle:String(angle),length:String(length),discs,targetIdentity:target===null?'null':discs.indexOf(target),expected,actual,pass:actual===expected});}
const o={x:0,y:0};
check('起段盲区修复',o,0,20,[{x:10,y:0}],null,true);
check('第三棋在起点后方但重叠',o,0,100,[{x:-10,y:0}],null,true);
// 首次运行揭示37.76字面量与21.76+16存在浮点差别；相切用实际表达式校准，保留字面量案例。
check('第三棋按实际半径精确相切',o,0,100,[{x:20,y:21.76+16}],null,false);
check('半径字面量浮点边界',o,0,100,[{x:20,y:37.76}],null,true);
const target={x:37.76,y:0,id:1};
check('预期目标初始接触排除',o,0,20,[target],target,false);
check('反弹前段不得排除目标',o,0,20,[target],null,true);
check('同ID不同对象仍为障碍',o,0,20,[{x:10,y:0,id:1}],target,true);
check('克隆目标不是同一引用',o,0,20,[target],{...target},true);
check('零长绕过重叠棋',o,0,0,[{x:0,y:0}],null,false);
check('负长拒绝',o,0,-1,[],null,true);
check('NaN角度拒绝',o,NaN,20,[],null,true);
check('无限长度拒绝',o,0,Infinity,[],null,true);
check('缺字段起点拒绝',{x:0},0,20,[],null,true);
check('坏棋数据拒绝',o,0,20,[{x:NaN,y:0}],null,true);
const badTarget={x:NaN,y:0};check('预期目标先排除后验证',o,0,20,[badTarget],badTarget,false);
check('零长跳过坏棋',o,0,0,[null],null,false);
check('null棋与null目标相等先跳过',o,0,20,[null],null,false);
check('截短段外不在胶囊内',o,0,100,[{x:100,y:0}],null,false);
check('实际棋半径16下37.3为真实重叠',o,0,20,[{x:10,y:37.3}],null,true);
const fallbackTarget={x:320,y:600};
check('回退坐标的起段第三棋', {x:320,y:421}, Math.PI/2, 179, [{x:357,y:441},fallbackTarget],fallbackTarget,true);
check('容许1单位棋盘漂移可跨入胶囊',o,0,20,[{x:10,y:37.7}],null,true);
check('漂移前不在胶囊内',o,0,20,[{x:10,y:38.2}],null,false);
check('反弹起点零长重叠',o,0,0,[{x:0,y:0}],null,false);
// 组合用例直接执行基线切取的真实旧函数，保留旧→新短路顺序。
const composed=[];
function composedCheck(name,origin,angle,length,discs,target,expected){
  context._0x3e4566=discs;context._0x2a9c75=[];context._0x3231b3=[];
  let actual;try{actual=context._0x3ea989(origin,43.52,angle,length)||context._carromStartPathBlocked(origin,angle,length,target);}catch(error){actual=error.name;}
  composed.push({name,expected,actual,pass:actual===expected});
}
composedCheck('旧检测先执行：null起点抛错',null,0,100,[{x:100,y:0}],null,'TypeError');
composedCheck('旧检测先执行：null棋抛错',o,0,100,[null],null,'TypeError');
composedCheck('短段null棋被新保护跳过',o,0,20,[null],null,false);
composedCheck('正常第三棋新保护补起段', {x:320,y:421},Math.PI/2,179,[{x:357,y:441},fallbackTarget],fallbackTarget,true);
details.composedResults=composed;
// 实际fallback函数隔离执行；仅宿主几何与随机源作确定性替身。
const fallbackStart=start.indexOf('    function _0x3d12d7('),fallbackEnd=start.indexOf('    function _0x52106f(',fallbackStart);
context._0x157421=key=>({[0x1c0]:'concat',[0x182]:'length',[0x1f8]:'floor',[0xec]:'random'})[key]||(()=>{throw Error('未确认的混淆属性 '+key);})();
context._0x55e1a0=162;context._0x187453=483;context._0x429ae3=421;context._0x133600=21.76;context._0x5d148e=0;
context._0x2a9c75=[fallbackTarget];context._0x3e4566=[{x:357,y:441}];context._0x3231b3=[];
context._0x8b2762=(a,b)=>Math.atan2(b.y-a.y,b.x-a.x);
context._0x23a7dc=(p,r)=>[...context._0x2a9c75,...context._0x3e4566,...context._0x3231b3].some(d=>Math.hypot(p.x-d.x,p.y-d.y)<r);
context._carromFindOpenBaseline=()=>{throw Error('夹具不应需要额外基线搜索');};
const randomValues=[0,158/321];context.Math=Object.create(Math);context.Math.random=()=>{if(!randomValues.length)throw Error('随机序列用尽');return randomValues.shift();};
vm.runInContext(start.slice(fallbackStart,fallbackEnd),context);
const fallback=context._0x3d12d7();
const fallbackGuard=context._carromStartPathBlocked(fallback.pos,fallback.dir,179,fallbackTarget);
const fallbackPass=fallback.pos.x===320&&fallback.pos.y===421&&fallbackGuard===true&&randomValues.length===0;
details.fallbackReplay={fallback,guardWouldBlock:fallbackGuard,pass:fallbackPass,scope:'实际fallback源码，几何宿主与随机源替身；非真实射击物理'};
if(!fallbackPass)throw Error('回退复现不符');
fs.mkdirSync('evidence',{recursive:true});fs.writeFileSync('evidence/carrom-static-audit.json',JSON.stringify({...details,results,scope:'冻结源码完整哈希、逐字符差分、语法编译；从真实源码切取新旧检测函数隔离验证，不是物理、浏览器或设备验收'},null,2));
console.log(JSON.stringify({metadata,fullDiffStatus:details.fullDiffStatus,calls,caseCount:results.length+composed.length,matched:results.filter(r=>r.pass).length+composed.filter(r=>r.pass).length,fallbackReplay:details.fallbackReplay,composedResults:composed},null,2));
if([...results,...composed].some(r=>!r.pass)) process.exitCode=1;
} catch(error) {console.error('审查执行失败：'+error.message);process.exitCode=1;}
