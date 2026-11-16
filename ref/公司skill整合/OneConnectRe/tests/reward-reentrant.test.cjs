const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const window={};vm.runInNewContext(fs.readFileSync('tools/reward_lifecycle_candidate.js','utf8'),{window,Promise,Set,Number,Error,setTimeout,clearTimeout});
(async()=>{let callbacks,credits=0;const life=window.oneConnectRewardLifecycle.create({loadTimeoutMs:100,grant(){credits++;callbacks.earned({verified:true});callbacks.closed();return true}});
life.setProvider({show(cb){callbacks=cb;cb.earned({verified:true});cb.closed()}});
assert.equal((await life.request('hint:1')).status,'rewarded');assert.equal(credits,1,'reentrant reward callbacks cannot credit twice');
let attempts=0;const fails=window.oneConnectRewardLifecycle.create({loadTimeoutMs:100,grant(){attempts++;throw Error('failure after unknown side effects')}});
fails.setProvider({show(cb){cb.earned({verified:true});cb.earned({verified:true});cb.closed()}});
assert.equal((await fails.request('hammer:1')).status,'closed');assert.equal(attempts,1,'failed grant with unknown side effects must not be repeated');
console.log('reentrant earned callbacks are credited once PASS');})().catch(e=>{console.error(e);process.exitCode=1});
