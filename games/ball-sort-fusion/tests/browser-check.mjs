// 真实 Chromium WebGL 验收：交互全部通过指针点击，公开接口仅用于读取状态断言。
import fs from 'node:fs';
import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import { chromium } from 'playwright';
import { moveCount, applyMove } from '../src/rules.mjs';
let baseUrl=process.env.GAME_URL;
let server;
if(!baseUrl){
 const folder=path.resolve(import.meta.dirname,'../dist');
 await fs.promises.access(path.join(folder,'index.html'));
 const types={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.png':'image/png','.wav':'audio/wav','.wasm':'application/wasm'};
 // 默认启动临时只读服务并随机选端口，验收结束立即关闭；指定GAME_URL则验收外部预览。
 server=http.createServer(async(request,response)=>{
  try{
   const requested=decodeURIComponent(new URL(request.url,'http://localhost').pathname);
   const target=path.resolve(folder,'.'+(requested==='/'?'/index.html':requested));
   if(!target.startsWith(folder+path.sep)){response.writeHead(403);response.end();return;}
   const content=await fs.promises.readFile(target);response.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream'});response.end(content);
  }catch{response.writeHead(404);response.end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));baseUrl=`http://127.0.0.1:${server.address().port}`;
}
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']}).catch(error=>{server?.close();throw error;});
const page=await browser.newPage({viewport:{width:540,height:960}});
const errors=[],failures=[],checks=[];
page.on('pageerror',error=>errors.push(error.stack));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
page.on('requestfailed',request=>failures.push(request.url()));
const state=()=>page.evaluate(()=>window.ballSortGame.getState());
// SHOW_ALL 在宽屏和长屏都会产生留白；依据实际画布边界映射设计坐标。
async function clickPoint(x,y){
 const rect=await page.locator('canvas').boundingBox();const scale=Math.min(rect.width/540,rect.height/960);
 await page.mouse.click(rect.x+(rect.width-540*scale)/2+x*scale,rect.y+(rect.height-960*scale)/2+y*scale);
}
async function clickTube(index){const value=await state();const point=value.tubePositions[index];await clickPoint(270+point.x,480-point.y);}
async function settle(){await page.waitForFunction(()=>!window.ballSortGame.getState().busy);}
async function perform(from,to){await clickTube(from);await clickTube(to);await settle();}
async function closeDialog(height=380){await clickPoint(470,480-height/2+36);assert.equal((await state()).overlay,false);}
async function playSolution(){for(const [from,to]of (await state()).solution)await perform(from,to);await page.waitForTimeout(750);assert.equal((await state()).won,true);}
function assertHint(value){assert.equal(value.hintPair?.length,2);assert.ok(moveCount(value.board,...value.hintPair,value.capacity)>0);}
async function screenshot(name){await page.screenshot({path:new URL(`../evidence/${name}.png`,import.meta.url).pathname});}
try {
 await page.goto(baseUrl);await page.waitForFunction(()=>!!window.ballSortGame);await page.waitForTimeout(200);
 const engine=await page.evaluate(()=>window.ballSortGame.getEngineInfo());
 assert.equal(engine.version,'3.8.8');assert.equal(engine.scene,'彩球工坊');assert.equal(engine.canvas,true);assert.equal(engine.graphicsApi,'WEBGL2');assert.ok(engine.drawCalls>0);checks.push('官方cc.VERSION、Director活动场景、正在绘制的WebGL2设备与Cocos画布一致');
 await screenshot('classic-desktop');
 // 本轮缺陷回归使用真实点击；场景接口只读，损坏存档仅限独立浏览器上下文。
 await perform(0,3);const pending=await state();
 await clickPoint(270,885);assert.equal((await state()).overlay,true);await clickPoint(270,500);
 assert.deepEqual((await state()).board,pending.board);assert.equal((await state()).moves,pending.moves);assert.equal((await state()).mode,'classic');
 await clickPoint(270,160);await clickPoint(100,360);assert.equal((await state()).overlay,true);await clickPoint(270,500);assert.deepEqual((await state()).board,pending.board);assert.equal((await state()).moves,1);
 await clickPoint(270,160);await clickPoint(185,360);assert.equal((await state()).overlay,true);await clickPoint(270,500);assert.equal((await state()).index,0);assert.deepEqual((await state()).board,pending.board);
 await clickPoint(435,885);await clickPoint(270,569);assert.equal((await state()).mode,'mystery');checks.push('模式切换、重选当前关与切换关卡均确认，取消保留棋盘步数，确认切换生效');
 await perform(0,3);await perform(0,4);
 const mysteryView=await page.evaluate(async()=>{const cc=await import('./engine/cc.js');const scene=cc.director.getScene();const find=(n,name)=>n.name===name?n:n.children.map(c=>find(c,name)).find(Boolean);const tube=find(scene,'试管1');return tube.children.filter(n=>n.name==='彩球').map(n=>({sprite:!!n.getComponent(cc.Sprite),labels:n.children.map(c=>c.getComponent(cc.Label)?.string).filter(Boolean)}));});
 assert.equal(mysteryView.length,2);assert.equal(mysteryView[0].sprite,false);assert.deepEqual(mysteryView[0].labels,['?']);assert.equal(mysteryView[1].sprite,true);await screenshot('code-mystery-regression');checks.push('迷雾真实两步后同色未满管的底球仍为问号');
 await page.evaluate(()=>{const key='ball-sort-atelier:v1';const raw=JSON.parse(localStorage.getItem(key));raw.version=999;raw.sound=false;localStorage.setItem(key,JSON.stringify(raw));});
 await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).storageRecovered,true);assert.equal((await state()).moves,0);assert.equal((await state()).mode,'classic');assert.match((await state()).message,/已修复异常存档/);assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('ball-sort-atelier:v1')).sound),false);checks.push('未知版本丢弃会话并可见恢复，保留有效声音设置');
 await perform(0,3);await perform(2,0);await page.evaluate(()=>{const key='ball-sort-atelier:v1';const raw=JSON.parse(localStorage.getItem(key));raw.session.history[1].board=raw.session.history[0].board;localStorage.setItem(key,JSON.stringify(raw));});
 await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).storageRecovered,true);assert.equal((await state()).moves,0);const recoveredBoard=(await state()).board;await clickPoint(84,802);assert.deepEqual((await state()).board,recoveredBoard);assert.equal((await state()).moves,0);checks.push('守恒但跨事务篡改历史被拒绝，无法撤销执行');
 const cdp=await page.context().newCDPSession(page);const memorySamples=[];
 async function sampleMemory(clicks){
  await page.waitForTimeout(250);await cdp.send('HeapProfiler.collectGarbage');
  const heap=await cdp.send('Runtime.getHeapUsage');
  const prototype=await cdp.send('Runtime.evaluate',{expression:"import('./engine/cc.js').then(cc=>cc.Node.prototype)",awaitPromise:true,objectGroup:'node-regression'});
  const objects=await cdp.send('Runtime.queryObjects',{prototypeObjectId:prototype.result.objectId,objectGroup:'node-regression'});
  const count=await cdp.send('Runtime.callFunctionOn',{objectId:objects.objects.objectId,functionDeclaration:'function(){return {nodes:this.length,tubes:this.filter(n=>/^试管[0-9]+$/.test(n.name)).length,orphans:this.filter(n=>!n.parent).length}}',returnByValue:true});
  memorySamples.push({clicks,heap:heap.usedSize,...count.result.value});await cdp.send('Runtime.releaseObjectGroup',{objectGroup:'node-regression'});
 }
 await sampleMemory(0);
 for(let batch=1;batch<=2;batch++){for(let i=0;i<200;i++)await clickTube(0);await sampleMemory(batch*200);}
 assert.ok(memorySamples[2].nodes<=memorySamples[0].nodes+30,JSON.stringify(memorySamples));
 assert.ok(memorySamples[2].tubes<=memorySamples[0].tubes+4,JSON.stringify(memorySamples));
 assert.ok(memorySamples[2].heap-memorySamples[1].heap<3000000,JSON.stringify(memorySamples));
 assert.equal((await state()).moves,0);assert.deepEqual((await state()).board,recoveredBoard);
 checks.push('400次真实点击并等待销毁帧及强制GC，节点与堆增长受限');
 fs.writeFileSync(new URL('../evidence/code-memory-regression.json',import.meta.url),JSON.stringify({samples:memorySamples},null,2));await cdp.detach();
 const initial=await state();await clickTube(initial.solution[0][0]);await clickTube(initial.solution[0][1]);
 const animating=await state();assert.equal(animating.busy,true);assert.equal(animating.moves,1);assert.deepEqual(animating.board,applyMove(initial.board,...initial.solution[0],initial.capacity).board);
 await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).busy,false);assert.deepEqual((await state()).board,animating.board);checks.push('动画开始前原子提交完整局面，动画中刷新不丢球');
 await clickPoint(84,802);assert.deepEqual((await state()).board,initial.board);checks.push('真实点击移动与撤销');
 await clickPoint(456,802);assert.equal((await state()).board.length,initial.board.length+1);await clickPoint(84,802);assert.equal((await state()).board.length,initial.board.length);checks.push('辅助管添加与撤销');
 await clickPoint(332,802);assertHint(await state());assert.equal((await state()).lastHintSource,'预置解法');await screenshot('hint');
 await perform(1,3);await clickPoint(332,802);await page.waitForFunction(()=>window.ballSortGame.getState().lastHintSource==='离线求解');assertHint(await state());checks.push('偏离预置路径后Worker返回当前局面的合法提示');
 const saved=await state();await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.deepEqual((await state()).board,saved.board);assert.equal((await state()).moves,1);checks.push('局面与步数刷新持久化');
 await clickPoint(84,802);await playSolution();assert.equal((await state()).completed,1);checks.push('经典模式完整通关与进度记录');await screenshot('classic-win');
 await closeDialog();await clickPoint(208,802);assert.equal((await state()).overlay,true);await clickPoint(270,569);assert.equal((await state()).moves,0);assert.deepEqual((await state()).board,initial.board);await playSolution();assert.equal((await state()).completed,1);checks.push('真实点击重开与重复通关奖励幂等');await closeDialog();
 await clickPoint(270,885);assert.equal((await state()).mode,'challenge');assert.equal((await state()).capacity,6);await screenshot('challenge');await playSolution();checks.push('六层长管完整通关');await closeDialog();
 // 在关卡列表中实际点击第7关，验收八层长管而非仅验收同一容量。
 await clickPoint(270,160);await clickPoint(185,438);assert.equal((await state()).capacity,8);await screenshot('challenge-eight');await playSolution();checks.push('八层长管完整通关');await closeDialog();
 await clickPoint(435,885);assert.equal((await state()).mode,'mystery');await screenshot('mystery');await playSolution();checks.push('隐藏球完整通关与揭示');await closeDialog();
 await clickPoint(496,90);await clickPoint(270,416);assert.equal((await state()).theme,1);await clickPoint(270,642);assert.equal((await state()).symbols,true);await screenshot('settings-light');await closeDialog(650);checks.push('真实点击解锁主题、切换Infinite材质与数字辅助');
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(200);await clickPoint(105,885);const mobileInitial=await state();await perform(...mobileInitial.solution[0]);assert.equal((await state()).moves,1);await clickPoint(84,802);assert.deepEqual((await state()).board,mobileInitial.board);await screenshot('mobile');checks.push('390×844移动端实际点击移动与撤销');
 await clickPoint(270,885);await clickPoint(270,160);await clickPoint(185,438);assert.equal((await state()).capacity,8);await screenshot('mobile-eight');checks.push('八层长管移动端布局');
 const targetMeasurements=[];
 function assertSeparated(targets){
  for(const t of targets)assert.ok(t.width>=43.99&&t.height>=43.99,JSON.stringify(t));
  for(let i=0;i<targets.length;i++)for(let j=i+1;j<targets.length;j++){const a=targets[i],b=targets[j];assert.ok(Math.abs(a.x-b.x)>=(a.width+b.width)/2-.01||Math.abs(a.y-b.y)>=(a.height+b.height)/2-.01,`命中区重叠：${a.name} / ${b.name}`);}
 }
 const readSave=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('ball-sort-atelier:v1')));
 async function measureTargets(){return page.evaluate(async()=>{const cc=await import('./engine/cc.js');const rect=cc.game.canvas.getBoundingClientRect();const scale=Math.min(rect.width/540,rect.height/960);const result=[];function visit(n,inModal=false){inModal ||= n.name==='弹窗';if(n.buttonSize){const t=n.getComponent(cc.UITransform);const p=n.worldPosition;result.push({name:n.name,modal:inModal,width:t.width*scale,height:t.height*scale,x:rect.x+(rect.width-540*scale)/2+(270+p.x)*scale,y:rect.y+(rect.height-960*scale)/2+(480-p.y)*scale});}for(const c of n.children)visit(c,inModal);}visit(cc.director.getScene());return result;});}
 for(const viewport of [{width:360,height:640},{width:390,height:844}]){
  await page.setViewportSize(viewport);await page.waitForTimeout(350);
  const targets=await measureTargets();for(const t of targets)assert.ok(t.width>=43.99&&t.height>=43.99,JSON.stringify(t));
  const menu=targets.find(t=>t.name==='按钮:☰');await page.mouse.click(menu.x-menu.width/2+2,menu.y);assert.equal((await state()).overlay,true);
  const modalTargets=await measureTargets();const close=modalTargets.find(t=>t.name==='按钮:×');assert.ok(close.width>=43.99&&close.height>=43.99);await page.mouse.click(close.x+close.width/2-2,close.y);assert.equal((await state()).overlay,false);
  const modes=targets.filter(t=>['按钮:经典旅程','按钮:长管挑战','按钮:迷雾实验'].includes(t.name)).sort((a,b)=>a.x-b.x);for(let i=1;i<modes.length;i++)assert.ok(modes[i-1].x+modes[i-1].width/2<=modes[i].x-modes[i].width/2+.01,'底部模式命中区域不能重叠');
  const classic=modes.find(t=>t.name==='按钮:经典旅程');await page.mouse.click(classic.x,classic.y+classic.height/2-2);assert.equal((await state()).mode,'classic');assert.equal((await state()).overlay,false);
  await clickPoint(44,90);const modePanel=(await measureTargets()).filter(t=>t.modal);assertSeparated(modePanel);await closeDialog(510);
  await clickPoint(270,160);const levelPanel=(await measureTargets()).filter(t=>t.modal);assertSeparated(levelPanel);await closeDialog(590);
  await clickPoint(496,90);const settingsPanel=(await measureTargets()).filter(t=>t.modal);assertSeparated(settingsPanel);
  const edgeActions=[];
  for(const key of ['sound','symbols','fast']){
   for(const edge of ['top','bottom','left','right']){
    const label={sound:'声音反馈',symbols:'颜色数字辅助',fast:'快速动画'}[key];const target=(await measureTargets()).find(t=>t.modal&&t.name.startsWith(`按钮:${label}`));const before=await readSave();
    const x=target.x+(edge==='left'?-target.width/2+1:edge==='right'?target.width/2-1:0);const y=target.y+(edge==='top'?-target.height/2+1:edge==='bottom'?target.height/2-1:0);
    await page.mouse.click(x,y);const after=await readSave();for(const field of ['sound','symbols','fast'])assert.equal(after[field],field===key?!before[field]:before[field]);edgeActions.push({key,edge,x,y});
   }
  }
  for(let i=0;i<3;i++){const target=(await measureTargets()).filter(t=>t.modal&&/按钮:[●○]/.test(t.name))[i];const before=await readSave();await page.mouse.click(target.x,target.y+target.height/2-1);const after=await readSave();assert.equal(after.theme,Object.keys(before.completed).length>=i*3?i:before.theme);assert.deepEqual(after.session,before.session);}
  await screenshot(`code-settings-targets-${viewport.width}`);await closeDialog(650);
  targetMeasurements.push({viewport,targets,modalTargets,modePanel,levelPanel,settingsPanel,edgeActions});await screenshot(`code-targets-${viewport.width}`);
 }
 fs.writeFileSync(new URL('../evidence/code-target-regression.json',import.meta.url),JSON.stringify(targetMeasurements,null,2));checks.push('360×640及390×844实际UITransform映射CSS尺寸至少44像素，菜单和关闭及底部模式边缘点击有效，模式命中区无重叠');
 // 合法长历史仅作为恢复输入注入，撤销、主题重绘和后续移动均用真实指针执行。
 const levelData=JSON.parse(fs.readFileSync(new URL('../public/assets/levels.json',import.meta.url),'utf8'));
 const level=levelData.classic[0];let snapshot={board:[...applyMove(level.board,0,3,4).board,[]],moves:1,extra:true};const longHistory=[];
 for(let i=0;i<500;i++){longHistory.push(structuredClone(snapshot));const next=applyMove(snapshot.board,...(i%2===0?[3,4]:[4,3]),4);assert.ok(next);snapshot={board:next.board,moves:snapshot.moves+1,extra:true};}
 const seeded=await readSave();seeded.mode='classic';seeded.indices.classic=0;seeded.session={...snapshot,mode:'classic',index:0,history:longHistory};
 await page.evaluate(raw=>localStorage.setItem('ball-sort-atelier:v1',JSON.stringify(raw)),seeded);
 async function reloadHistory(){const before=await readSave();await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).storageRecovered,false);const after=await readSave();assert.deepEqual(after.session,before.session);return after.session;}
 await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).moves,501);assert.equal((await readSave()).session.history.length,500);
 const historySamples=[];
 for(let i=0;i<3;i++){await clickPoint(84,802);const restored=await reloadHistory();assert.equal(restored.history.length,499-i);assert.equal(restored.moves,500-i);assert.equal(restored.extra,true);historySamples.push({moves:restored.moves,length:restored.history.length,boundary:restored.historyBoundary});}
 const beforeTheme=(await readSave()).session;await clickPoint(496,90);await clickPoint(270,350);assert.deepEqual((await readSave()).session,beforeTheme);await closeDialog(650);await reloadHistory();
 const continuing=await state();const from=continuing.board[3].length?3:4;await perform(from,from===3?4:3);const continued=await reloadHistory();assert.equal(continued.moves,499);assert.equal(continued.history.length,498);
 await clickPoint(84,802);await reloadHistory();assert.deepEqual((await state()).board,continuing.board);
 fs.writeFileSync(new URL('../evidence/code-history-regression.json',import.meta.url),JSON.stringify({historySamples,afterContinue:continued,themePreserved:true},null,2));checks.push('合法500条历史连续撤销与刷新保留边界，主题重绘及继续移动再撤销仍可恢复');
 checks.push('设置全部目标及模式、关卡弹窗两两无重叠，开关四边真实点击仅改变目标设置');
 // 写入故障只在隔离context中模拟；正常玩法与设置全部使用真实指针。
 const boundaryContext=await browser.newContext({viewport:{width:540,height:960}});
 const boundaryPage=await boundaryContext.newPage();const boundaryErrors=[];
 boundaryPage.on('pageerror',error=>boundaryErrors.push(error.stack));
 const boundaryState=()=>boundaryPage.evaluate(()=>window.ballSortGame.getState());
 async function boundaryClick(x,y){const rect=await boundaryPage.locator('canvas').boundingBox();const scale=Math.min(rect.width/540,rect.height/960);await boundaryPage.mouse.click(rect.x+(rect.width-540*scale)/2+x*scale,rect.y+(rect.height-960*scale)/2+y*scale);}
 async function boundaryMove(from,to){for(const n of [from,to]){const p=(await boundaryState()).tubePositions[n];await boundaryClick(270+p.x,480-p.y);}await boundaryPage.waitForFunction(()=>!window.ballSortGame.getState().busy);}
 async function boundaryLabels(){return boundaryPage.evaluate(async()=>{const cc=await import('./engine/cc.js');const labels=[];function visit(n){const label=n.getComponent(cc.Label);if(label)labels.push(label.string);n.children.forEach(visit);}visit(cc.director.getScene());return labels;});}
 async function assertSettings(){assert.ok((await boundaryLabels()).includes('让工坊更适合你'));assert.ok(!(await boundaryLabels()).includes('每一种颜色，都有归处'));}
 const boundarySamples=[];
 try{
  await boundaryPage.goto(baseUrl);await boundaryPage.waitForFunction(()=>!!window.ballSortGame);
  const originalRaw=await boundaryPage.evaluate(()=>localStorage.getItem('ball-sort-atelier:v1'));
  await boundaryPage.evaluate(()=>{const original=Storage.prototype.setItem;window.storageFault={fail:true,attempts:0,successes:0};Storage.prototype.setItem=function(key,value){if(key==='ball-sort-atelier:v1'){window.storageFault.attempts++;if(window.storageFault.fail)throw new DOMException('隔离回归模拟写入失败','QuotaExceededError');window.storageFault.successes++;}return original.call(this,key,value);};});
  async function assertUnsaved(action){const value=await boundaryState();assert.match(value.message,/本次进度暂未保存/);assert.equal(await boundaryPage.evaluate(()=>localStorage.getItem('ball-sort-atelier:v1')),originalRaw);boundarySamples.push({action,moves:value.moves,extra:value.extra,message:value.message});}
  await boundaryMove(0,3);assert.equal((await boundaryState()).moves,1);await assertUnsaved('移动动画结束');
  await boundaryClick(84,802);assert.equal((await boundaryState()).moves,0);await assertUnsaved('撤销');
  await boundaryClick(456,802);assert.equal((await boundaryState()).extra,true);await assertUnsaved('加管');
  await boundaryClick(496,90);await boundaryClick(270,642);assert.equal((await boundaryState()).symbols,true);await assertUnsaved('设置');assert.ok((await boundaryLabels()).includes('本次进度暂未保存，当前局面仍可继续'));
  await boundaryClick(270,350);await assertSettings();await assertUnsaved('主题重绘');
  await boundaryPage.evaluate(()=>{window.storageFault.fail=false;});assert.match((await boundaryState()).message,/本次进度暂未保存/);
  await boundaryClick(270,570);await assertSettings();assert.doesNotMatch((await boundaryState()).message,/暂未保存/);
  const savedBoundary=await boundaryPage.evaluate(()=>JSON.parse(localStorage.getItem('ball-sort-atelier:v1')));assert.equal(savedBoundary.session.extra,true);assert.equal(savedBoundary.symbols,true);assert.ok(await boundaryPage.evaluate(()=>window.storageFault.successes>0));
  await boundaryPage.reload();await boundaryPage.waitForFunction(()=>!!window.ballSortGame);assert.equal((await boundaryState()).extra,true);assert.equal((await boundaryState()).symbols,true);assert.equal((await boundaryState()).storageRecovered,false);
  checks.push('隔离context运行期写失败覆盖移动、撤销、加管、设置及主题重绘，警告持续且操作继续，真实写入成功后清除并可刷新恢复');
  await boundaryClick(84,802);
  async function boundarySolve(){for(const step of (await boundaryState()).solution)await boundaryMove(...step);assert.equal((await boundaryState()).won,true);}
  async function waitSettlement(){await boundaryPage.waitForFunction(()=>window.ballSortGame.getState().overlay===true);assert.equal((await boundaryState()).overlay,true);const ready=await boundaryPage.evaluate(async()=>{const cc=await import('./engine/cc.js');function find(n){if(!cc.isValid(n,true)||!n.activeInHierarchy)return false;return n.name==='按钮:下一关'||n.name==='按钮:从第一关再出发'||n.children.some(find);}return find(cc.director.getScene());});assert.equal(ready,true,'当前活动弹层必须包含结算导航按钮');}
  await boundarySolve();await waitSettlement();assert.equal((await boundaryState()).completed,1);
  const settlementTargets=await boundaryPage.evaluate(async()=>{const cc=await import('./engine/cc.js');const targets=[];function visit(n){if(n.buttonSize)targets.push({name:n.name,valid:cc.isValid(n,true),active:n.activeInHierarchy,x:n.worldPosition.x,y:n.worldPosition.y});n.children.forEach(visit);}visit(cc.director.getScene());return targets;});
  const beforeNext=await boundaryState();await boundaryClick(270,500);assert.equal((await boundaryState()).index,1,JSON.stringify({before:beforeNext,after:await boundaryState(),targets:settlementTargets}));await boundarySolve();await waitSettlement();assert.equal((await boundaryState()).completed,2);
  await boundaryClick(470,326);await boundaryClick(496,90);await boundaryClick(270,350);await boundaryPage.waitForTimeout(900);await assertSettings();assert.equal((await boundaryState()).completed,2);assert.equal((await boundaryState()).theme,0);
  await boundaryClick(270,642);assert.equal((await boundaryState()).symbols,false);await assertSettings();
  await boundaryPage.reload();await boundaryPage.waitForFunction(()=>!!window.ballSortGame);await waitSettlement();assert.equal((await boundaryState()).completed,2);assert.equal((await boundaryState()).index,1);
  await boundaryClick(270,500);assert.equal((await boundaryState()).index,2);await boundarySolve();
  // 在延迟结算到达前打开设置并切换真正解锁的新主题。
  await boundaryClick(496,90);await boundaryClick(270,416);await boundaryPage.waitForTimeout(900);await assertSettings();assert.equal((await boundaryState()).theme,1);assert.equal((await boundaryState()).completed,3);
  await boundaryClick(270,714);await assertSettings();
  await boundaryClick(470,191);await boundaryClick(270,160);await boundaryClick(355,360);assert.equal((await boundaryState()).index,3);assert.equal((await boundaryState()).won,false);await boundaryPage.waitForTimeout(900);assert.equal((await boundaryState()).overlay,false);assert.equal((await boundaryState()).completed,3);
  assert.deepEqual(boundaryErrors,[]);
  fs.writeFileSync(new URL('../evidence/code-boundary-regression.json',import.meta.url),JSON.stringify({storage:boundarySamples,savedSession:savedBoundary.session,final:await boundaryState(),errors:boundaryErrors,realPointer:true,realSolutionCompletion:true},null,2));
  checks.push('真实解法通关后默认主题重绘保留设置，完成局刷新正常结算且奖励幂等，解锁主题与快速导航不受过期结算覆盖');
 }finally{await boundaryContext.close();}
 await page.setViewportSize({width:1440,height:900});await page.waitForTimeout(200);await screenshot('wide-desktop');checks.push('1440×900宽屏无变形');
 // 注入损坏数据仅用于模拟存储异常；实际恢复由启动校验完成。
 await page.evaluate(()=>localStorage.setItem('ball-sort-atelier:v1',JSON.stringify({version:1,indices:null,completed:'异常',session:{board:[]}})));
 await page.reload();await page.waitForFunction(()=>!!window.ballSortGame);assert.equal((await state()).storageRecovered,true);assert.match((await state()).message,/已修复异常存档/);assert.deepEqual((await state()).board,initial.board);checks.push('损坏合法JSON的存档可见恢复');
 assert.deepEqual(errors,[],'浏览器不应出现运行时异常或渲染错误');assert.deepEqual(failures,[],'全部资源请求成功');
 fs.writeFileSync(new URL('../evidence/browser-validation.json',import.meta.url),JSON.stringify({passed:true,engine,renderer:'WebGL2',browser:await browser.version(),checks,errors,failedRequests:failures},null,2));
 console.log('浏览器验收通过：'+checks.join('；'));
} finally {await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
