const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const dir=process.argv[2];if(!dir)throw Error('candidate game directory required');
let fail=false, values=new Map();
const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>{if(fail)throw Error('quota');values.set(k,v)}};
const w={localStorage:storage};w.window=w;
for(const file of ['layout-candidate.js','hammer-runtime.js'])vm.runInNewContext(fs.readFileSync(path.join(dir,file),'utf8'),w);
for(const inventory of [w.oneConnectThemeInventoryCandidate,w.oneConnectHammer]){
 const count=()=>inventory.count?inventory.count():inventory.state().count;
 assert.equal(count(),2);fail=true;assert.equal(inventory.credit(2),true);
 assert.equal(count(),4,'reward remains usable in memory');assert.equal(inventory.rewardPersisted(),false,'storage failure is visible');
 const revision=inventory.rewardRevision();assert.equal(inventory.retryRewardSave(2,revision),'retry');
 fail=false;assert.equal(inventory.retryRewardSave(2,revision),'saved');assert.equal(inventory.rewardPersisted(),true);assert.equal(count(),4);
 assert.equal(inventory.credit(2),true);assert.equal(inventory.rewardPersisted(),true);assert.equal(count(),6);
}
// Local changes during a transient failure are included in the later write.
fail=true;assert.equal(w.oneConnectHammer.credit(2),true);const rev=w.oneConnectHammer.rewardRevision();
assert.equal(w.oneConnectHammer.credit(2),true);fail=false;
assert.equal(w.oneConnectHammer.retryRewardSave(6,rev),'saved');
assert.equal(values.get('oneconnect.hammer.candidate.v1'),'10');
// The stored value may have changed in another context; do not overwrite it.
fail=true;assert.equal(w.oneConnectHammer.credit(2),true);fail=false;
values.set('oneconnect.hammer.candidate.v1','7');
assert.equal(w.oneConnectHammer.retryRewardSave(10,w.oneConnectHammer.rewardRevision()),'conflict');
assert.equal(values.get('oneconnect.hammer.candidate.v1'),'7');
console.log('theme and hammer distinguish in-memory rewards from durable writes PASS');
