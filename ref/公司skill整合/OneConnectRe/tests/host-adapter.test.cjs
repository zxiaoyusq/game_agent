const assert = require('node:assert/strict');
const fs = require('node:fs'); const vm = require('node:vm');
const code = fs.readFileSync('game/host-adapter.js','utf8');
function boot(provider){let w={console,top:{},addEventListener(){}}; if(provider)w.top.h5_sdk=provider;w.window=w;vm.runInNewContext(code,w);return w.oneConnectHost;}
(async()=>{let host=boot();assert.equal((await host.showAd('Interstitial')).status,'unavailable');host.loadingCompleted();assert.equal(host.events().filter(e=>e.type==='ad.request').length,1);let calls=[];host=boot({showGameLoadingCompleted(){calls.push('ready')},showAd(k){calls.push(k);throw Error('down')}});host.loadingCompleted();assert.equal((await host.showAd('Interstitial')).status,'error');assert.deepEqual(calls,['ready','Interstitial']);assert.equal(host.events().at(-1).type,'ad.error');console.log('host adapter PASS')})().catch(e=>{console.error(e);process.exit(1)});
