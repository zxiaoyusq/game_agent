const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
 let done,timer,cleared=0,finished=false;
 const sdk={showAd(kind,callback){assert.equal(kind,'Interstitial');done=callback;}},w={top:{h5_sdk:sdk},setTimeout:f=>(timer=f,42),clearTimeout:id=>{assert.equal(id,42);cleared++}};w.window=w;
 vm.runInNewContext(fs.readFileSync('game/host-adapter.js','utf8'),w);
 const request=w.oneConnectHost.showInterstitialFor('fail');request.then(()=>{finished=true});await Promise.resolve();assert.equal(finished,false,'callback provider must not finish on undefined return');
 done();assert.equal((await request).status,'returned');assert.equal(cleared,1);done();assert.equal(w.oneConnectHost.events().filter(x=>x.type==='ad.returned').length,1);
 const second=w.oneConnectHost.showInterstitialFor('fail');timer();assert.equal((await second).status,'timeout');done();assert.equal(w.oneConnectHost.events().filter(x=>x.type==='ad.returned').length,1,'late callback must not finish twice');
 console.log('interstitial waits for host callback and settles once on timeout PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
