const assert=require('node:assert/strict'),http=require('node:http'),path=require('node:path');
const {chromium}=require('C:/Users/nenghong.zhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const server=http.createServer((req,res)=>{res.writeHead(200,{'Content-Type':'text/html'});res.end('<!doctype html><title>inventory transaction test</title>')});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/`;
 let browser;
 try{
  browser=await chromium.launch({headless:true,channel:'chrome'});const context=await browser.newContext(),a=await context.newPage(),b=await context.newPage();
  await a.goto(url);await a.evaluate(()=>localStorage.setItem('oneconnect.hammer.candidate.v1','3'));await b.goto(url);
  for(const page of [a,b]){await page.addScriptTag({path:path.resolve('examples/inventory-idb-candidate.js')});await page.evaluate(()=>window.inventory=oneConnectInventoryIDBExperiment.create({database:'test-inventory',legacyKey:'oneconnect.hammer.candidate.v1'}));}
  assert.equal((await a.evaluate(()=>inventory.get())).count,3);
  const duplicate=await Promise.all([a.evaluate(()=>inventory.grant('claim-a')),b.evaluate(()=>inventory.grant('claim-a'))]);
  assert.deepEqual(duplicate.sort(),['already_claimed','granted']);
  assert.deepEqual((await Promise.all([a.evaluate(()=>inventory.grant('claim-b')),b.evaluate(()=>inventory.consume())])).sort(),['granted','used']);
  assert.equal((await a.evaluate(()=>inventory.get())).count,6);
  const failed=await a.evaluate(async()=>{const old=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){throw Error('injected failure')};try{await inventory.grant('claim-c');return false}catch(_){return true}finally{IDBObjectStore.prototype.put=old}});
  assert(failed);assert.equal((await b.evaluate(()=>inventory.get())).count,6);assert.equal(await b.evaluate(()=>inventory.grant('claim-c')),'granted');
  await a.reload();await a.addScriptTag({path:path.resolve('examples/inventory-idb-candidate.js')});
  assert.equal(await a.evaluate(async()=>{let x=oneConnectInventoryIDBExperiment.create({database:'test-inventory',legacyKey:'oneconnect.hammer.candidate.v1'});return (await x.get()).count}),8);
  const edge=await a.evaluate(async()=>{
   localStorage.setItem('theme-test','998');let x=oneConnectInventoryIDBExperiment.create({database:'test-theme',legacyKey:'theme-test'});
   const full=await x.grant('too-many'),count=(await x.get()).count;const reserved=await x.reserve('capacity'),pendingFull=await x.grant('also-too-many'),refunded=await x.resolve('capacity',false);
   localStorage.setItem('bad-test','broken');let y=oneConnectInventoryIDBExperiment.create({database:'test-bad',legacyKey:'bad-test'});
   let rejected=false;try{await y.get()}catch(_){rejected=true}return {full,count,rejected,reserved,pendingFull,refunded};
  });
  assert.deepEqual(edge,{full:'full',count:998,rejected:true,reserved:'reserved',pendingFull:'full',refunded:'refunded'});
  await a.addScriptTag({path:path.resolve('tools/reward_lifecycle_candidate.js')});
  await a.addScriptTag({path:path.resolve('examples/reward-idb-bridge-candidate.js')});
  const bridge=await a.evaluate(async()=>{
   const ledger=oneConnectInventoryIDBExperiment.create({database:'test-inventory',legacyKey:'oneconnect.hammer.candidate.v1'});
   async function attempt(claim,proof){const life=oneConnectRewardLifecycle.create({loadTimeoutMs:1000,grant:oneConnectRewardIDBBridgeExperiment.create(ledger)});life.setProvider({show(cb){cb.earned(proof);cb.closed()}});return (await life.request(claim)).status;}
   return {first:await attempt('local-1',{verified:true,transactionId:'platform-1'}),duplicate:await attempt('local-2',{verified:true,transactionId:'platform-1'}),missing:await attempt('local-3',{verified:true}),unverified:await attempt('local-4',{verified:false,transactionId:'platform-2'}),count:(await ledger.get()).count};
  });
  assert.deepEqual(bridge,{first:'rewarded',duplicate:'rewarded',missing:'closed',unverified:'closed',count:10});
  await a.evaluate(()=>window.inventory=oneConnectInventoryIDBExperiment.create({database:'test-inventory',legacyKey:'oneconnect.hammer.candidate.v1'}));
  const reserves=await Promise.all([a.evaluate(()=>inventory.reserve('op-1','board-before')),b.evaluate(()=>inventory.reserve('op-1','board-before'))]);
  assert.deepEqual(reserves.sort(),['already_pending','reserved']);assert.equal((await a.evaluate(()=>inventory.get())).count,9);
  assert.equal(await b.evaluate(()=>inventory.reserve('op-1','other-board')),'operation_conflict');
  assert.equal(await b.evaluate(()=>inventory.reserve('op-other','board-before')),'operation_busy');
  await a.reload();await a.addScriptTag({path:path.resolve('examples/inventory-idb-candidate.js')});
  await a.evaluate(()=>window.inventory=oneConnectInventoryIDBExperiment.create({database:'test-inventory',legacyKey:'oneconnect.hammer.candidate.v1'}));
  assert.deepEqual((await a.evaluate(()=>inventory.get())).operations[0],{id:'op-1',status:'pending',context:'board-before'});
  const refunds=await Promise.all([a.evaluate(()=>inventory.resolve('op-1',false)),b.evaluate(()=>inventory.resolve('op-1',false))]);
  assert.deepEqual(refunds.sort(),['already_refunded','refunded']);assert.equal((await a.evaluate(()=>inventory.get())).count,10);
  assert.equal(await a.evaluate(()=>inventory.reserve('op-2')),'reserved');assert.equal(await b.evaluate(()=>inventory.resolve('op-2',true)),'committed');
  assert.equal(await a.evaluate(()=>inventory.resolve('op-2',false)),'already_committed');assert.equal((await a.evaluate(()=>inventory.get())).count,9);
  await a.addScriptTag({path:path.resolve('game/round-save-model.js')});await a.addScriptTag({path:path.resolve('examples/hammer-ledger-idb/round-evidence.js')});
  const proof=await a.evaluate(async()=>{
   const ledger=oneConnectInventoryIDBExperiment.create({database:'test-evidence',legacyKey:'missing-evidence-key'});
   const entry={level:8,seconds:196,movement:'static',boardSize:{rows:2,cols:2},generator:{mask:[[1,1],[1,1]],typeCount:2}};
   const before={version:1,level:8,config:oneConnectRoundSaveModel.fingerprint(entry),rows:2,cols:2,board:[[1,2],[1,2]],timer:100,score:100,tip:2,shuffle:1};
   await ledger.reserve('evidence-op',oneConnectHammerRoundEvidence.context(before,entry));const op=(await ledger.get()).operations[0];
   const unchanged=oneConnectHammerRoundEvidence.classify(op,before,entry,true);
   const withoutProof=oneConnectHammerRoundEvidence.classify(op,{...before,board:[[0,2],[0,2]]},entry,true);
   const marked=oneConnectHammerRoundEvidence.classify(op,{...before,board:[[0,2],[0,2]],hammerOperationId:'evidence-op'},entry,true);
   return {unchanged,withoutProof,marked};
  });
  assert.deepEqual(proof,{unchanged:'refund',withoutProof:'unknown',marked:'commit'});
  console.log('isolated IDB migration, concurrent +2 claims, consume, rollback and reload PASS');
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1});
