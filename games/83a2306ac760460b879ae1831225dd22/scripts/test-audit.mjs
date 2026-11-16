import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {resolve,dirname,extname} from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createServer} from 'node:http';
import {existsSync} from 'node:fs';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {files,fingerprint} from './build.mjs';
import {chooseAI,clone} from '../src/rules.js';
const out='evidence/test-audit';await mkdir(out,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const report={started:new Date().toISOString(),results:[],errors:[],limitations:['移动端为Chromium触摸视口模拟，非实体设备','源码包在无node_modules目录重建；未执行清洁npm ci或联网安装']};
const sourceBefore=await fingerprint();
async function distMap(root='dist'){const result={};for(const p of await files(root))result[p.slice(root.length+1)]=hash(await readFile(p));return result;}
const before=await distMap();let browser,server;
function entries(data){const result=[];let offset=0;while(data.readUInt32LE(offset)===0x04034b50){assert.equal(data.readUInt16LE(offset+8),0,'交付ZIP须使用已知STORE编码');const size=data.readUInt32LE(offset+18),nameLength=data.readUInt16LE(offset+26),extra=data.readUInt16LE(offset+28),name=data.subarray(offset+30,offset+30+nameLength).toString('utf8'),start=offset+30+nameLength+extra;assert.ok(!name.startsWith('/')&&!name.split('/').includes('..'));result.push({name,data:data.subarray(start,start+size)});offset=start+size;}return result;}
async function packages(){
 const manifest=JSON.parse(await readFile('releases/manifest.json','utf8'));
 for(const pack of manifest.packages)assert.equal(hash(await readFile(pack.path)),pack.sha256);
 const play=entries(await readFile('releases/ludo-play.zip'));assert.equal(play.length,Object.keys(before).length);
 for(const e of play)assert.equal(hash(e.data),before[e.name],'试玩包与本轮dist不一致：'+e.name);
 const extracted=out+'/source-rebuild';await mkdir(extracted,{recursive:true});
 const source=entries(await readFile('releases/ludo-source.zip'));
 for(const e of source){assert.ok(!e.name.startsWith('reference-inputs/')&&!e.name.startsWith('node_modules/'));const p=extracted+'/'+e.name;await mkdir(dirname(p),{recursive:true});await writeFile(p,e.data);}
 const run=spawnSync(process.execPath,['scripts/build.mjs'],{cwd:extracted,encoding:'utf8'});await writeFile(out+'/source-build.log',run.stdout+run.stderr);assert.equal(run.status,0,'源码包独立重建失败');assert.deepEqual(await distMap(extracted+'/dist'),before,'源码包重建不一致');
 const unit=spawnSync(process.execPath,['--test','tests/rules.test.mjs','tests/session.test.mjs'],{cwd:extracted,encoding:'utf8'});await writeFile(out+'/source-test.log',unit.stdout+unit.stderr);assert.equal(unit.status,0);
 report.results.push({name:'交付包哈希、试玩包逐条一致、源码包无node_modules独立重建及单测',passed:true,sourceEntries:source.length,playEntries:play.length,buildExit:run.status,testExit:unit.status,distFiles:Object.keys(before).length});
}
const snap=p=>p.evaluate(()=>window.ludo.snapshot());
const act=async(p,id)=>{const el=p.locator(`[data-action="${id}"]`);await el.waitFor({state:'visible'});const b=await el.boundingBox();await p.touchscreen.tap(b.x+b.width/2,b.y+b.height/2);};
async function shots(p,label){const records=[];for(let i=0;i<3;i++){const s=await snap(p),path=`${out}/${label}-${i}.png`;await p.screenshot({path});records.push({at:Date.now(),path,phase:s.session.phase,elapsed:s.session.elapsed,plan:s.session.plan});await p.waitForTimeout(35);}await writeFile(`${out}/${label}-sequence.json`,JSON.stringify(records,null,2));}
function currentKind(s){if(s.phase!=='moving')return s.phase;let offset=0;for(const part of s.segments){if(s.elapsed<offset+part.ms)return part.kind;offset+=part.ms;}return 'moving';}
async function interruption(p,kind,mode){
 await act(p,'settings');const frozen=(await snap(p)).session;
 await p.waitForTimeout(150);assert.equal((await snap(p)).session.elapsed,frozen.elapsed);
 await p.reload();await p.waitForFunction(()=>window.ludo?.snapshot().assetsReady);await act(p,'continue');await act(p,'settings');
 const restored=(await snap(p)).session;assert.deepEqual(restored.game,frozen.game);assert.deepEqual(restored.plan,frozen.plan);assert.equal(restored.phase,frozen.phase);assert.ok(restored.elapsed-frozen.elapsed<100);
 await act(p,'close');await act(p,'restart');const paused=(await snap(p)).session;await p.waitForTimeout(130);assert.equal((await snap(p)).session.elapsed,paused.elapsed);await act(p,'cancel');
 // 导航BFCache触发真实visibilitychange/freeze/resume，不派发合成事件。
 await act(p,'settings');const saved=(await snap(p)).session;await act(p,'close');
 await p.goto(report.base+'/index.html?background=audit');await p.waitForTimeout(260);await p.goBack({waitUntil:'commit'});
 const back=await snap(p);assert.equal(back.session.id,saved.id);assert.deepEqual(back.session.game,saved.game);assert.deepEqual(back.session.plan,saved.plan);assert.ok(back.events.some(e=>e.kind==='后台暂停'&&e.reason==='visibilitychange'));assert.ok(back.events.some(e=>e.kind==='前台恢复'));assert.ok(back.session.elapsed-saved.elapsed<180,'后台不得推进动画');
 await shots(p,mode+'-'+kind+'-restored');report.results.push({name:mode+'/'+kind+'刷新、确认取消暂停、真实后台恢复',passed:true,beforeElapsed:frozen.elapsed,restoredElapsed:restored.elapsed,backgroundElapsed:back.session.elapsed,phase:back.session.phase});
}
async function ui(){
 const root=resolve('dist');server=createServer(async(req,res)=>{try{let path=new URL(req.url,'http://localhost').pathname.replace(/^\/audit\/ludo\//,'').replace(/^\//,'')||'index.html';const p=resolve(root,path);assert.ok(p.startsWith(root+'/'));const data=await readFile(p);res.writeHead(200,{'Content-Type':{'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.ogg':'audio/ogg'}[extname(p)]||'application/octet-stream','Cache-Control':'max-age=0, must-revalidate'});res.end(data);}catch{res.writeHead(404);res.end('文件不存在');}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));report.base=`http://127.0.0.1:${server.address().port}`;
 const executablePath=process.env.CHROMIUM_PATH||['/usr/bin/chromium','/usr/bin/chromium-browser','/opt/google/chrome/chrome'].find(p=>existsSync(p));browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{channel:'chromium'}),args:['--no-sandbox'],ignoreDefaultArgs:['--disable-back-forward-cache']});report.browser=browser.version();
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,recordVideo:{dir:out+'/video',size:{width:390,height:844}}}),p=await context.newPage();
 p.on('pageerror',e=>report.errors.push(e.message));p.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 await p.goto(report.base+'/audit/ludo/index.html?seed=14');await p.waitForFunction(()=>window.ludo?.snapshot().assetsReady);await act(p,'new');await act(p,'mode-quick');await act(p,'count-2');for(const seat of [0,2])await p.locator(`[data-seat="${seat}"]`).selectOption('human');await act(p,'start');
 let ai=clone((await snap(p)).session.game.rng.ai);const tested=new Set();const deadline=Date.now()+180000;
 while(Date.now()<deadline){const s=(await snap(p)).session;if(s.phase==='result')break;
  const kind=currentKind(s);
  if(['rolling','walk','return','home','celebrating'].includes(kind)&&!tested.has(kind)&&(kind!=='walk'||s.segments.filter(part=>part.kind==='walk').length>=3)){tested.add(kind);await interruption(p,kind,'quick');continue;}
  if(s.phase==='ready'){await act(p,'roll');continue;}
  if(s.phase==='choosing'){const g=clone(s.game);g.rng.ai=clone(ai);const index=chooseAI(g);ai=clone(g.rng.ai);await act(p,'token-'+index);continue;}
  // 棋盘真实连点不得提前提交或重新掷骰。
  if(s.phase==='moving'){await p.touchscreen.tap(196,410);const after=(await snap(p)).session;assert.ok(after.game.action===s.game.action||after.game.action===s.game.action+1);}
  await p.waitForTimeout(12);
 }
 const end=(await snap(p)).session;assert.equal(end.phase,'result');for(const kind of ['rolling','walk','return','home','celebrating'])assert.ok(tested.has(kind),'未覆盖动画：'+kind);assert.equal(end.game.winner,2);assert.equal(end.game.action,30);assert.equal(end.game.turn,29);
 await p.reload();await p.waitForFunction(()=>window.ludo?.snapshot().assetsReady);await act(p,'continue');assert.equal((await snap(p)).overlay,'result');await act(p,'again');assert.equal((await snap(p)).session.game.action,0);
 // 在新局的运动中确认重开，验证旧事务无法迟到提交。
 await act(p,'roll');await p.waitForFunction(()=>window.ludo.snapshot().session.phase==='choosing');await act(p,'token-0');await act(p,'restart');const old=(await snap(p)).session.id;await act(p,'confirm');await p.waitForTimeout(1000);assert.notEqual((await snap(p)).session.id,old);assert.equal((await snap(p)).session.game.action,0);
 report.results.push({name:'390触摸自然快速完整对局、结果刷新及运动中确认重开',passed:true,seed:14,winner:end.game.winner,actions:end.game.action,turns:end.game.turn});report.video=await p.video().path();await context.close();assert.deepEqual(report.errors,[]);
}
try{await packages();await ui();assert.deepEqual(await distMap(),before);assert.equal((await fingerprint()).sha256,sourceBefore.sha256);report.source=sourceBefore.sha256;report.distHashes=before;report.passed=true;console.log('独立补充验收通过：源码包重建一致，五类动画刷新与真实后台恢复，390触摸自然结算。');}catch(error){report.passed=false;report.error=error.stack;console.error('独立补充验收失败：',error);process.exitCode=1;}finally{await browser?.close();if(server)await new Promise(r=>server.close(r));report.finished=new Date().toISOString();await writeFile(out+'/report.json',JSON.stringify(report,null,2));}
