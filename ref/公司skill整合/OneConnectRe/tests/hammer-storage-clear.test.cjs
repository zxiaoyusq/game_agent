const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.style={};this.children=[]}setAttribute(){}appendChild(x){this.children.push(x)}addEventListener(){}}
const listeners={},values=new Map();let fail=true;
const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>{if(fail)throw Error('quota');values.set(k,v)}};
const document={body:new El(),createElement:()=>new El()};
const w={localStorage:storage,addEventListener:(n,fn)=>{(listeners[n]??=[]).push(fn)},requestAnimationFrame(){}};w.window=w;
vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'hammer-runtime.js'),'utf8'),{window:w,document,localStorage:storage,Number,Date,Math});
w.oneConnectHammer.install();assert(w.oneConnectHammer.credit(2));const revision=w.oneConnectHammer.rewardRevision();
fail=false;for(const fn of listeners.storage)fn({key:null});
assert.equal(w.oneConnectHammer.retryRewardSave(2,revision),'conflict');assert.equal(values.size,0);
console.log('hammer rejects pending retry after external storage clear PASS');
