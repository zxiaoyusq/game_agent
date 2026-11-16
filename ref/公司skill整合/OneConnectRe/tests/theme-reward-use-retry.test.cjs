const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(tag){this.tag=tag;this.style={};this.children=[];this.handlers={};this.attrs={};}setAttribute(k,v){this.attrs[k]=v}append(...n){this.children.push(...n)}appendChild(n){this.children.push(n)}addEventListener(n,fn){(this.handlers[n]??=[]).push(fn)}}
const values=new Map(),listeners={};let fail=true;
const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>{if(fail)throw Error('quota');values.set(k,v)}};
const pause={name:'pause',data:0},rt={running_layout:{name:'game'},all_global_vars:[{name:'theme',data:0},pause],types:{}};let switches=0,pending;
const cr={plugins_:{Sprite:function(){}}};cr.plugins_.Sprite.prototype.acts={};
const document={body:new El('body'),createElement:t=>new El(t),getElementById:()=>null};
const w={cr,localStorage:storage,cr_getC2Runtime:()=>rt,addEventListener:(n,fn)=>{(listeners[n]??=[]).push(fn)},oneConnectThemeSwitchCandidate:{animateSwitch:(_r,_t,_a,done)=>{switches++;pending=done;return {status:'started'}}},oneConnectHost:{emit(){}}};w.window=w;
const ctx={window:w,document,cr,localStorage:storage,requestAnimationFrame(){},setTimeout(){},clearTimeout(){},Date,Number,Array,Object,Math};
vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'layout-candidate.js'),'utf8'),ctx);
w.oneConnectLayoutCandidate.install();const inv=w.oneConnectThemeInventoryCandidate;
assert(inv.credit(2));const rev=inv.rewardRevision();assert.equal(inv.count(),4);
const button=document.body.children.find(e=>e.tag==='button');assert(button);
pause.data=1;for(const fn of button.handlers.click)fn({stopPropagation(){}});assert.equal(switches,0);assert.equal(inv.count(),4,'pause prevents consuming a tool');
pause.data=0;rt.running_layout.name='menu';for(const fn of button.handlers.click)fn({stopPropagation(){}});assert.equal(switches,0);assert.equal(inv.count(),4,'leaving the game prevents consuming a tool');rt.running_layout.name='game';
for(const fn of button.handlers.click)fn({stopPropagation(){}});assert.equal(inv.count(),4,'starting the animation must not consume inventory');pending({status:'unavailable'});assert.equal(inv.count(),4,'failed theme switch must not consume inventory');
for(const fn of button.handlers.click)fn({stopPropagation(){}});assert.equal(inv.count(),4,'inventory waits for a successful completion');pending({status:'switched',theme:1,tiles:2});
assert.equal(inv.count(),3,'actual theme button consumes one item while storage fails');
fail=false;assert.equal(inv.retryRewardSave(2,rev),'saved');assert.equal(values.get('oneconnect.theme-tool.candidate.v1'),'3');
// An observed external event invalidates the retry even if its value later matches.
fail=true;assert(inv.credit(2));const rev2=inv.rewardRevision();fail=false;
for(const fn of listeners.storage)fn({key:'oneconnect.theme-tool.candidate.v1'});
assert.equal(inv.retryRewardSave(3,rev2),'conflict');assert.equal(values.get('oneconnect.theme-tool.candidate.v1'),'3');
// localStorage.clear() reports key=null; it must invalidate outstanding retries.
fail=true;assert(inv.credit(2));const rev3=inv.rewardRevision();fail=false;values.clear();
for(const fn of listeners.storage)fn({key:null});
assert.equal(inv.retryRewardSave(3,rev3),'conflict');assert.equal(values.size,0);
console.log('theme button consumption is included in retry; external event rejects stale retry PASS');
