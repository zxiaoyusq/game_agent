const {execFileSync}=require('child_process'),fs=require('fs'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const pages=await(await fetch('http://127.0.0.1:19223/json')).json(),page=pages.find(x=>x.type==='page'),desc=JSON.parse(page.description),ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no});
 let id=0,pending=new Map(),errors=[],current='setup';ws.onmessage=e=>{let m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown'){let d=m.params.exceptionDetails;errors.push({target:current,text:d.exception?.description||d.text,url:d.url||''})}let q=pending.get(m.id);if(q){pending.delete(m.id);m.error?q.no(m.error):q.ok(m.result)}};
 function call(method,params={}){return new Promise((ok,no)=>{let n=++id;pending.set(n,{ok,no});ws.send(JSON.stringify({id:n,method,params}))})}
 async function val(expression,awaitPromise=false){let r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
 async function wait(expression){for(let i=0;i<600;i++){try{if(await val(expression))return}catch{}await sleep(100)}throw Error('timeout '+expression)}
 async function tap(x,y){let d=await val('({width:innerWidth,height:innerHeight})');execFileSync('C:/Program Files/ADB/adb.exe',['-s','127.0.0.1:16448','shell','input','tap',String(Math.round(x*desc.width/d.width)),String(Math.round(desc.screenY+y*desc.height/d.height))]);await sleep(500)}
 let out=[];await call('Runtime.enable');
 for(let run=0;run<4;run++)for(let target of (run%2?['game','baseline']:['baseline','game'])){
  current=target;let url='http://127.0.0.1:18749/'+target+'/game.html';
  if(target==='game'){await call('Page.navigate',{url});await wait("window.cr_getC2Runtime?.()?.running_layout?.name==='menu'");await val("localStorage.setItem('oneconnect.currentLevel.v1','13');localStorage.removeItem('oneconnect.round.v1')")}
  let start=Date.now();await call('Page.navigate',{url});await wait("window.cr_getC2Runtime?.()?.running_layout?.name==='menu'");let menuMs=Date.now()-start;await sleep(1000);await tap(await val('innerWidth/2'),await val('innerHeight*.628'));
  if(target==='baseline'){await sleep(800);await tap(await val('innerWidth*0.22'),await val('innerHeight*.625'))}
  await wait('cr_getC2Runtime().types.t5.instances.length===72');await sleep(1800);
  let sample=await val(`new Promise(resolve=>{let start=performance.now(),previous=start,delta=[];function tick(t){delta.push(t-previous);previous=t;if(t-start<5000)requestAnimationFrame(tick);else{delta.shift();delta.sort((a,b)=>a-b);resolve({frames:delta.length,fps:1000*delta.length/(t-start),p95Ms:delta[Math.floor(delta.length*.95)],runtimeFps:cr_getC2Runtime().fps,tiles:cr_getC2Runtime().types.t5.instances.length})}}requestAnimationFrame(tick)})`,true);
  let rec={target,run,menuMs,sample,warmup:run===0};out.push(rec);console.log(JSON.stringify(rec));
 }
 fs.writeFileSync('tests/evidence/mumu_warm_fallback_performance.json',JSON.stringify({revision:process.env.OC_REVISION,scope:'warm local HTTP WebView, idle 72 tile board; not AHA preinstalled or active gameplay',results:out,exceptions:errors},null,2)+'\n');console.log('Exceptions:',JSON.stringify(errors));ws.close();
})().catch(e=>{console.error(e);process.exit(1)});
