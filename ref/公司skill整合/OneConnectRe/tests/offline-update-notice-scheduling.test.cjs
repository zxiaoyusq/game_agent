const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let tick,event,frames=0,waiting=true;const notice={style:{},setAttribute(){}};
 const runtime={running_layout:{name:'menu'}};
 const document={createElement:()=>notice,body:{appendChild(){}}};
 const location={protocol:'https:',hostname:'example.test',href:'https://example.test/game/game.html'};
 const navigator={serviceWorker:{getRegistration:()=>Promise.resolve({active:{scriptURL:'https://example.test/game/offline-worker.js'},waiting:waiting?{}:null})}};
 const ctx={document,location,navigator,URL,Promise,window:{cr_getC2Runtime:()=>runtime,addEventListener(name,fn){if(name==='oneconnect:event')event=fn}},setInterval(fn){tick=fn},requestAnimationFrame(){frames++}};
 vm.runInNewContext(fs.readFileSync(process.argv[2]||'game/offline-update-notice.js','utf8'),ctx);
 assert.equal(frames,0,'update notice must not schedule a continuous animation frame loop');
 tick();await new Promise(resolve=>setImmediate(resolve));assert.equal(notice.style.display,'block','waiting update is shown in menu');
 runtime.running_layout.name='game';event({detail:{type:'game.level_start'}});assert.equal(notice.style.display,'none','notice hides immediately when a level starts');tick();await new Promise(resolve=>setImmediate(resolve));assert.equal(notice.style.display,'none','notice stays hidden during gameplay');
 runtime.running_layout.name='menu';waiting=false;tick();await new Promise(resolve=>setImmediate(resolve));assert.equal(notice.style.display,'none','notice hides when no update waits');
 console.log('offline notice updates on periodic checks without a per-frame loop PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
