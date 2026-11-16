import {chromium} from 'playwright';
import {createServer} from 'node:http';import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';import {existsSync} from 'node:fs';import {resolve,extname} from 'node:path';import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';import {chooseAI,clone,assertGame} from '../src/rules.js';import {files,fingerprint} from './build.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const root=resolve('dist'),out='evidence/browser';await mkdir(out,{recursive:true});
const source=await fingerprint();const info=JSON.parse(await readFile('dist/build-info.json','utf8'));assert.equal(source.sha256,info.source.sha256,'源码改变后须重新构建');
async function distMap() {const map={};for(const p of await files('dist'))map[p]=hash(await readFile(p));return map;}
const before=await distMap();const requests=[],errors=[],report={started:new Date().toISOString(),source:source.sha256,results:[],screenshots:[],limitations:['Chromium移动视口模拟，非真机','未取得参考游戏实际运行截图，按真实图集/坐标装配对照']};
const server=createServer(async(req,res)=>{
 try {let path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);requests.push(path);if(path.startsWith('/independent/ludo/'))path=path.slice('/independent/ludo/'.length);else path=path.replace(/^\//,'');if(!path)path='index.html';const p=resolve(root,path);if(!p.startsWith(root+'/'))throw Error('非法路径');const data=await readFile(p);const type={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.ogg':'audio/ogg'}[extname(p)]||'application/octet-stream';res.writeHead(200,{'Content-Type':type,'Cache-Control':'max-age=0, must-revalidate'});res.end(data);}catch{res.writeHead(404);res.end('文件不存在');}
});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
let browser;
const screenshot=async(page,name)=>{const path=`${out}/${name}.png`;await page.screenshot({path});report.screenshots.push(path);};
const snap=page=>page.evaluate(()=>window.ludo.snapshot());
const act=async(page,id,touch=false)=>{const el=page.locator(`[data-action="${id}"]`);if(touch)await el.tap();else await el.click();};
async function open(context,path) {const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('requestfailed',r=>{const message=r.url()+':'+r.failure()?.errorText;if(r.failure()?.errorText==='net::ERR_ABORTED'&&/\.(mp3|ogg)$/.test(r.url()))(report.cancelledAudioRequests??=[]).push(message);else errors.push(message);});await page.goto(base+path);await page.waitForFunction(()=>window.ludo?.snapshot().assetsReady);return page;}
async function setup(page,mode,count,touch=false,allHuman=true) {
 await act(page,'new',touch);await act(page,'mode-'+mode,touch);await act(page,'count-'+count,touch);
 if(allHuman)for(let p=0;p<4;p++){const select=page.locator(`[data-seat="${p}"]`);if(await select.inputValue()!=='off')await select.selectOption('human');}
 await act(page,'start',touch);await page.waitForFunction(()=>window.ludo.snapshot().session?.phase==='ready');
}
async function captureAnimation(page,name,kind,count=6,interval=75) {
 const records=[];for(let i=0;i<count;i++){const s=await snap(page);records.push({at:Date.now(),phase:s.session?.phase,elapsed:s.session?.elapsed,game:s.session?.game});await screenshot(page,`${name}-${kind}-${i}`);await page.waitForTimeout(interval);}
 await writeFile(`${out}/${name}-${kind}-sequence.json`,JSON.stringify(records,null,2));
}
async function lifecycle() {
 const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const page=await open(ctx,'/independent/ludo/index.html?seed=14');
 await screenshot(page,'390-menu');await setup(page,'classic',2,true,true);
 // 真实触摸掷骰与连点锁定，刷新恢复同点数。
 await act(page,'roll',true);await page.waitForTimeout(180);let a=await snap(page);assert.equal(a.session.phase,'rolling');const dice=a.session.game.dice,turn=a.session.game.turn;
 await page.touchscreen.tap(195,785);assert.equal((await snap(page)).session.game.turn,turn);
 await act(page,'settings',true);a=await snap(page);await page.waitForTimeout(300);let b=await snap(page);assert.equal(b.session.elapsed,a.session.elapsed,'设置期间必须冻结');await act(page,'close',true);
 await page.reload();await page.waitForFunction(()=>window.ludo.snapshot().assetsReady);await act(page,'continue',true);assert.equal((await snap(page)).session.game.dice,dice,'刷新不得重新掷骰');
 await page.waitForFunction(()=>['ready','choosing'].includes(window.ludo.snapshot().session.phase));
 await act(page,'restart',true);await act(page,'cancel',true);const id=(await snap(page)).session.id;await act(page,'restart',true);await act(page,'confirm',true);assert.notEqual((await snap(page)).session.id,id);
 await screenshot(page,'390-classic');
 // 真实导航进入BFCache会触发visibilitychange/freeze，返回触发resume，不伪造事件。
 await act(page,'roll',true);await page.waitForTimeout(140);const beforeBackground=await snap(page);
 await page.goto(base+'/index.html?background=1');await page.waitForTimeout(360);await page.goBack({waitUntil:'commit'});
 const lifecycleSnap=await snap(page);assert.equal(lifecycleSnap.session.id,beforeBackground.session.id);assert.equal(lifecycleSnap.session.game.dice,beforeBackground.session.game.dice);assert.ok(lifecycleSnap.events.some(e=>e.kind==='后台暂停'&&e.reason==='visibilitychange'),'真实页面未触发后台事件');assert.ok(lifecycleSnap.events.some(e=>e.kind==='前台恢复'),'页面未恢复前台');assert.ok(lifecycleSnap.session.elapsed-beforeBackground.session.elapsed<120,'后台动画不应跳完');
 report.results.push({name:'390触摸、连点、摇骰刷新、设置暂停、重开与真实生命周期冻结',passed:true,events:lifecycleSnap.events});
 // 3/4席和AI真实轮转入口。
 await act(page,'menu',true);await act(page,'confirm',true);await setup(page,'quick',4,true,false);await screenshot(page,'390-four-ai');
 for(let i=0;i<100;i++) {const s=await snap(page);if(s.session.events){}if(s.session.game.seats[s.session.game.current]==='human'){if(s.session.phase==='ready')await act(page,'roll',true);else if(s.session.phase==='choosing')await act(page,'token-'+chooseAI(clone(s.session.game)),true);}await page.waitForTimeout(80);if((await snap(page)).events.filter(e=>e.kind==='动作提交').length>=4)break;}
 assert.ok((await snap(page)).events.some(e=>e.kind==='动作提交'&&e.plan.p!==0),'电脑未完成动作');
 await act(page,'menu',true);await act(page,'confirm',true);await setup(page,'quick',2,true,true);await act(page,'roll',true);await page.waitForFunction(()=>window.ludo.snapshot().session.phase==='choosing');await act(page,'token-0',true);await act(page,'restart',true);const oldMovingId=(await snap(page)).session.id;await act(page,'confirm',true);await page.waitForTimeout(1100);assert.notEqual((await snap(page)).session.id,oldMovingId);assert.equal((await snap(page)).session.game.action,0,'重开后旧运动不得提交');
 report.results.push({name:'真实运动中确认重开取消旧局',passed:true});
 report.results.push({name:'4席混合AI真实合法动作',passed:true});
 await act(page,'menu',true);await act(page,'confirm',true);await setup(page,'classic',3,true);assert.equal((await snap(page)).session.game.seats.filter(x=>x!=='off').length,3);report.results.push({name:'3席同屏配置',passed:true});
 await ctx.close();
}
async function resourceChecks() {
 const ctx=await browser.newContext({viewport:{width:320,height:568},isMobile:true,hasTouch:true});const page=await ctx.newPage();
 await page.route('**/assets/*.png',async route=>{await new Promise(r=>setTimeout(r,450));await route.continue();});
 await page.goto(base+'/independent/ludo/index.html',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>!!window.ludo);assert.equal((await snap(page)).overlay,'loading');assert.equal(await page.locator('[data-action="start"]').count(),0);
 await page.waitForFunction(()=>window.ludo.snapshot().assetsReady);await screenshot(page,'320-menu');
 await page.unroute('**/assets/*.png');await ctx.close();
 const fail=await browser.newContext();const p=await fail.newPage();let blocked=true;
 await p.route('**/assets/board.png',async route=>{if(blocked)await route.fulfill({status:200,body:'损坏图像',contentType:'image/png'});else await route.continue();});
 await p.goto(base+'/');await p.waitForSelector('[data-action="retry"]');assert.equal((await snap(p)).assetsReady,false);blocked=false;await act(p,'retry');await p.waitForFunction(()=>window.ludo.snapshot().assetsReady);
 const audioResults=await p.evaluate(async()=>{const context=new AudioContext(),results=[];for(const name of ['bgm.mp3','roll.mp3','walk.mp3','capture.mp3','home.mp3','win.mp3','turn.mp3','click.ogg']){const data=await (await fetch('./assets/'+name)).arrayBuffer();const decoded=await context.decodeAudioData(data);results.push({name,duration:decoded.duration,channels:decoded.numberOfChannels});}await context.close();return results;});assert.ok(audioResults.every(r=>r.duration>0));
 report.results.push({name:'慢素材加载锁定及损坏核心图像重试',passed:true},{name:'八份原音频真实浏览器解码',passed:true,audioResults});await fail.close();
 // 损坏存档必须明确可恢复，存储写失败持续可见。
 const st=await browser.newContext();const q=await open(st,'/');await q.evaluate(()=>localStorage.setItem('ludo-original-session-v1','{损坏'));await q.reload();await q.waitForFunction(()=>window.ludo.snapshot().assetsReady);assert.match(await q.locator('#warning').textContent(),/存档读取失败/);
 await setup(q,'quick',2);await q.evaluate(()=>{Storage.prototype.setItem=function(){throw new Error('测试存储拒绝');};});await act(q,'roll');await q.waitForTimeout(250);assert.match(await q.locator('#warning').textContent(),/存档写入失败/);report.results.push({name:'损坏存档诊断与持续存储失败提示',passed:true});await st.close();
}
async function fullGame(mode,seed,touch) {
 const name=mode+(touch?'-320-touch':'-desktop');const ctx=await browser.newContext({viewport:touch?{width:320,height:568}:{width:1100,height:900},isMobile:touch,hasTouch:touch,recordVideo:{dir:out+'/video',size:touch?{width:320,height:568}:{width:550,height:450}}});const page=await open(ctx,`/independent/ludo/index.html?seed=${seed}`);
 await setup(page,mode,2,touch);await screenshot(page,name+'-start');
 const bounds=await page.locator('#stage').boundingBox();assert.ok(bounds.x>=0&&bounds.y>=0);const buttonSizes=await page.locator('#hud button').evaluateAll(els=>els.map(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})));assert.ok(buttonSizes.every(b=>b.width>=44&&b.height>=44));
 let aiStream=(await snap(page)).session.game.rng.ai,seen=new Set(),rollingRecovery=false,movingRecovery=false,capturePaused=false,homePaused=false,winPaused=false,lastAction=0;
 const deadline=Date.now()+700000;
 while(Date.now()<deadline) {
  const state=await snap(page),s=state.session;
  if(s.phase==='result')break;
  if(s.phase==='ready') {await act(page,'roll',touch);continue;}
  if(s.phase==='choosing') {
    const g=clone(s.game);g.rng.ai=clone(aiStream);const index=chooseAI(g);aiStream=clone(g.rng.ai);const hits=await page.evaluate(()=>window.ludo.coordinates()),hit=hits.find(h=>h.i===index),isolated=hit&&hits.every(h=>h===hit||h.i===index||Math.hypot(h.x-hit.x,h.y-hit.y)>68);
    if(isolated){const box=await page.locator('canvas').boundingBox(),x=box.x+hit.x*box.width/720,y=box.y+hit.y*box.height/1280;if(touch)await page.touchscreen.tap(x,y);else await page.mouse.click(x,y);}else await act(page,'token-'+index,touch);continue;
  }
  let kind=s.phase;
  if(kind==='moving') {let offset=0;for(const segment of s.segments){if(s.elapsed<offset+segment.ms){kind=segment.kind;break;}offset+=segment.ms;}}
  const pauseFlag=(kind==='return'||kind==='capture')&&!capturePaused||kind==='home'&&!homePaused||kind==='celebrating'&&!winPaused;
  if(pauseFlag) {if(kind==='return'||kind==='capture')capturePaused=true;if(kind==='home')homePaused=true;if(kind==='celebrating')winPaused=true;await act(page,'restart',touch);const frozen=(await snap(page)).session;await page.waitForTimeout(100);assert.equal((await snap(page)).session.elapsed,frozen.elapsed);await act(page,'cancel',touch);continue;}
  if(!seen.has(kind)&&['rolling','walk','capture','return','home','celebrating'].includes(kind)) {
    seen.add(kind);await captureAnimation(page,name,kind,kind==='celebrating'?8:kind==='capture'?2:5,kind==='rolling'?65:kind==='walk'?25:kind==='return'||kind==='capture'?15:55);continue;
  }
  // 已选冻结事务刷新重放，不能重复吃子/奖励。只读取快照、不写局面。
  if(!movingRecovery&&s.phase==='moving'&&s.segments.length>=3&&!s.plan.capture) {
    movingRecovery=true;const original=clone(s.plan),gameBefore=clone(s.game);
    await act(page,'settings',touch);await page.reload();await page.waitForFunction(()=>window.ludo.snapshot().assetsReady);await act(page,'continue',touch);
    const restored=await snap(page);assert.deepEqual(restored.session.plan,original);assert.deepEqual(restored.session.game,gameBefore);report.results.push({name:name+'走子刷新恢复冻结事务',passed:true});continue;
  }
  if(s.game.action>lastAction){lastAction=s.game.action;assertGame(s.game);}
  await page.waitForTimeout(22);
 }
 const final=await snap(page);for(const e of final.events)if(e.kind==='动画段'&&e.segmentKind)seen.add(e.segmentKind);assert.equal(final.session.phase,'result',name+'未自然完成');assert.notEqual(final.session.game.winner,null);assert.ok(seen.has('rolling')&&seen.has('walk')&&seen.has('home')&&seen.has('celebrating'));assert.ok(seen.has('return'),name+'没有自然吃子回营证据');
 await screenshot(page,name+'-result');await writeFile(`${out}/${name}-events.json`,JSON.stringify(final.events,null,2));
 const actions=final.events.filter(e=>e.kind==='动作提交');assert.equal(new Set(actions.map(e=>e.action)).size,actions.length,'动作重复提交');
 const landings=final.events.filter(e=>e.kind==='落地');assert.ok(landings.length>actions.length);
 report.results.push({name:name+'完整自然对局到结算',passed:true,seed,winner:final.session.game.winner,actions:actions.length,turns:final.session.game.turn,seen:[...seen],buttonSizes,landings:landings.length,recovery:{movingRecovery,capturePaused,homePaused,winPaused}});
 await act(page,'again',touch);assert.equal((await snap(page)).session.game.action,0);assert.equal((await snap(page)).session.game.winner,null);await screenshot(page,name+'-again');
 if(!touch){await page.setViewportSize({width:780,height:720});await screenshot(page,name+'-resized');}
 const videoPath=await page.video()?.path();if(videoPath)report.results.push({name:name+'连续正常速度录像',passed:true,path:videoPath});
 await ctx.close();
}
try {
 const executablePath=process.env.CHROMIUM_PATH||['/usr/bin/chromium','/usr/bin/chromium-browser','/opt/google/chrome/chrome'].find(p=>existsSync(p));
 browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{channel:'chromium'}),args:['--no-sandbox'],ignoreDefaultArgs:['--disable-back-forward-cache']});report.browser=browser.version();
 await resourceChecks();await lifecycle();
 const candidates=JSON.parse(await readFile('evidence/rule-games.json','utf8')).browserSeeds;
 await Promise.all([fullGame('classic',candidates.classic.seed,false),fullGame('quick',candidates.quick.seed,true)]);
 assert.deepEqual(await distMap(),before,'验收不得修改最终dist');assert.equal((await fingerprint()).sha256,source.sha256);assert.deepEqual(errors,[],'浏览器错误');
 report.passed=true;report.requests=requests;report.distHashes=before;console.log('真实浏览器验收通过：两模式完整自然对局、320/390触摸、桌面鼠标、五类正常速度动画与恢复。');
} catch(error) {report.passed=false;report.error=error.stack;console.error('浏览器验收失败：',error);process.exitCode=1;}
finally {report.errors=errors;report.finished=new Date().toISOString();await writeFile(`${out}/report.json`,JSON.stringify(report,null,2));await browser?.close();await new Promise(r=>server.close(r));}
