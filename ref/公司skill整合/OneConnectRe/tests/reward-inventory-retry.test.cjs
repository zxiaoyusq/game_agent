const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const dir=process.argv[2];if(!dir)throw Error('candidate game directory required');
class El{constructor(){this.children=[];this.style={};this.hidden=false;}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
(async()=>{
 let fail=true,cb,id=0;const values=new Map(),timers=new Map(),events=[];
 const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>{if(fail)throw Error('quota');values.set(k,v)}};
 const rt={running_layout:{name:'game'},all_global_vars:[{name:'level',data:8}],types:{t25:{instances:[]}}};
 const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return false}};cr.action.prototype.run_system=function(){};
 const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:text=>({textContent:text})};
 const w={localStorage:storage,cr,cr_getC2Runtime:()=>rt,addEventListener(){},oneConnectHost:{emit:(type,data)=>events.push({type,data})}};w.window=w;
 const ctx={window:w,document,localStorage:storage,cr,console,Date,Number,Promise,Error,Set,setTimeout:(fn,ms)=>{timers.set(++id,{fn,ms});return id},clearTimeout:n=>timers.delete(n)};
 for(const file of ['layout-candidate.js','reward-lifecycle.js','tool-reward-candidate.js'])vm.runInNewContext(fs.readFileSync(path.join(dir,file),'utf8'),ctx);
 const reward=w.oneConnectToolRewardCandidate;reward.install();reward.setProvider({show(x){cb=x}});
 assert(reward.open('theme'));document.body.children[0].children[0].children[2].onclick();cb.earned({verified:true});cb.closed();await Promise.resolve();
 assert.equal(w.oneConnectThemeInventoryCandidate.count(),4);assert(events.some(e=>e.type==='candidate.reward_save_deferred'));
 function runRetry(){const item=[...timers.entries()].find(([,t])=>t.ms===5000);assert(item,'failed write schedules retry');timers.delete(item[0]);item[1].fn();}
 assert(reward.open('theme'));document.body.children[0].children[0].children[2].onclick();cb.earned({verified:true});cb.closed();await Promise.resolve();
 assert.equal([...timers.values()].filter(t=>t.ms===5000).length,1,'multiple failed rewards share a single retry');
 fail=false;runRetry();
 assert.equal(values.get('oneconnect.theme-tool.candidate.v1'),'6');assert.equal(w.oneConnectThemeInventoryCandidate.count(),6);
 assert(!events.some(e=>e.type==='candidate.reward_save_retry_stopped'),'successful shared retry does not report a false conflict');
 // A newer external value must not be overwritten by the delayed retry.
 fail=true;assert(reward.open('theme'));document.body.children[0].children[0].children[2].onclick();cb.earned({verified:true});cb.closed();await Promise.resolve();
 fail=false;values.set('oneconnect.theme-tool.candidate.v1','9');runRetry();
 assert.equal(values.get('oneconnect.theme-tool.candidate.v1'),'9');assert(events.some(e=>e.type==='candidate.reward_save_retry_stopped'&&e.data.reason==='conflict'));
 assert.equal([...timers.values()].filter(t=>t.ms===5000).length,0,'conflict stops retries');
 fail=true;assert(reward.open('theme'));document.body.children[0].children[0].children[2].onclick();cb.earned({verified:true});cb.closed();await Promise.resolve();
 assert.equal([...timers.values()].filter(t=>t.ms===5000).length,1);
 fail=false;assert(reward.open('theme'));document.body.children[0].children[0].children[2].onclick();cb.earned({verified:true});cb.closed();await Promise.resolve();
 assert.equal([...timers.values()].filter(t=>t.ms===5000).length,0,'successful later credit cancels the obsolete retry');
 console.log('verified theme reward is saved after transient storage failure without double credit PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
