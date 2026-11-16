const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('tools/haptics_candidate.js','utf8');
function create(saved,available=true){
 const calls=[],writes=[];
 const window={document:{hidden:false},localStorage:{getItem:()=>saved,setItem:(k,v)=>writes.push([k,v])},navigator:available?{vibrate:n=>{calls.push(n);return true}}:{}};
 vm.runInNewContext(source,{window,Number});return {api:window.oneConnectHapticsCandidate,calls,writes,window};
}
let a=create('0');assert.equal(a.api.enabled(),false);assert.equal(a.api.pulse(20),false);assert.equal(a.calls.length,0);
assert.equal(a.api.setEnabled(true),true);assert.equal(a.api.pulse(20),true);assert.deepEqual(a.calls,[20]);assert.equal(a.writes[0][1],'1');
a.window.document.hidden=true;assert.equal(a.api.pulse(20),false);a.window.document.hidden=false;
assert.equal(a.api.pulse(1001),false);assert.equal(a.api.setEnabled(false),true);assert.deepEqual(a.calls,[20,0]);
let b=create(null,false);assert.equal(b.api.supported(),false);assert.equal(b.api.pulse(20),false);
console.log('haptics preference, visibility, support and limits PASS');
