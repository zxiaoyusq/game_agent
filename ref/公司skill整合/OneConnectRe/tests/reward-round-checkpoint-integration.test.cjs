const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
if(!process.argv[2])throw Error('Pass the candidate game directory to test');
class El{constructor(){this.children=[];this.hidden=false;this.style={};}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
async function run(kind){
 let now=10000,values=new Map(),listeners={};const emit=(type,detail={})=>(listeners['oneconnect:event']||[]).forEach(fn=>fn({detail:{type,detail}}));
 const vars=[['level',8],['ROWS_COUNT',2],['COLUMNS_COUNT',2],['timer',100],['score',100],['tip',0],['shuffle',0]].map(([name,data])=>({name,data}));
 const entry={level:8,seconds:196,movement:'static',boardSize:{rows:2,cols:2}},tiles=[{uid:1,instance_vars:[1,1,1,0]},{uid:2,instance_vars:[1,1,2,0]},{uid:3,instance_vars:[2,2,1,0]},{uid:4,instance_vars:[2,2,2,0]}],arr=Array.from({length:4},()=>Array.from({length:4},()=>[0]));for(const t of tiles)arr[t.instance_vars[2]][t.instance_vars[1]][0]=t.uid;
 const runtime={running_layout:{name:'game'},all_global_vars:vars,types:{t0:{instances:[{cx:4,cy:4,arr}]},t5:{instances:tiles},t32:{instances:[{instance_vars:[0,0,0,0]}]},t25:{instances:[]}}};
 const cr={plugins_:{Touch:function(){},Spritefont2:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return false}};cr.plugins_.Spritefont2.prototype.acts={SetText(){}};cr.action.prototype.run_system=function(){};
 const document={body:new El(),head:new El(),hidden:false,createElement:()=>new El(),createTextNode:text=>({textContent:text}),addEventListener(){}};
 const localStorage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
 const window={cr,document,localStorage,Date:{now:()=>now},cr_getC2Runtime:()=>runtime,oneConnectLevels:{levels:[entry]},oneConnectGravityRuntime:{state:()=>({moving:false})},oneConnectLevelScoreCandidate:{baseline:()=>null,matchScore:()=>null,match(){},restore(){}},oneConnectFlyStarScoreCandidate:{snapshot:()=>null,restore(){}},addEventListener:(n,f)=>(listeners[n]??=[]).push(f),setInterval(){},oneConnectHost:{emit}};window.window=window;
 const ctx={...window,window,cr,document,localStorage,Date:window.Date,Number,Promise,Error,Set,Map,setTimeout,clearTimeout,console};
 const dir=process.argv[2];for(const f of ['round-save-model.js','round-save.js','reward-lifecycle.js','tool-reward-candidate.js'])vm.runInNewContext(fs.readFileSync(dir+'/'+f,'utf8'),ctx);
 window.oneConnectRoundSave.install();window.oneConnectToolRewardCandidate.install();emit('game.board_configured',{level:8});now+=1000;
 if(kind==='shuffle'){assert(window.oneConnectRoundSave.capture());emit('game.match',{level:8});}
 let cb;const reward=window.oneConnectToolRewardCandidate;reward.setProvider({show(c){cb=c}});assert(reward.open(kind));const root=document.body.children[0],watch=root.children[0].children[2];watch.onclick();
 if(kind==='hint'){assert(values.has('oneconnect.round.score-candidate.v1'),'pre-ad capture establishes a stable fallback');emit('game.match',{level:8});}
 cb.earned({verified:true});cb.earned({verified:true});cb.closed();await Promise.resolve();
 const saved=JSON.parse(values.get('oneconnect.round.score-candidate.v1'));assert.equal(saved[kind==='hint'?'tip':'shuffle'],2);assert.equal(vars.find(v=>v.name===(kind==='hint'?'tip':'shuffle')).data,2);
 assert(window.oneConnectRoundSaveModel.validate(saved,entry),'checkpoint remains a valid restorable snapshot');
 const restored=window.oneConnectRoundSave.restore(entry);assert(restored);assert.equal(restored[kind==='hint'?'tip':'shuffle'],2,'reload path restores exactly the credited amount');
}
(async()=>{await run('hint');await run('shuffle');console.log('reward callbacks checkpoint both counters on unstable boards PASS')})().catch(e=>{console.error(e);process.exitCode=1});
