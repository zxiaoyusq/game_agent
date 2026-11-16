const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.children=[];this.style={};this.hidden=false;}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
(async()=>{
 let event,finish,busy=false;const life={state:()=>({busy}),request(){busy=true;return new Promise(r=>finish=r)},cancel(){},setProvider(){}};
 const rt={running_layout:{name:'game'},all_global_vars:[{name:'level',data:1}]};
 const window={oneConnectRewardLifecycle:{create:()=>life},cr_getC2Runtime:()=>rt,addEventListener:(_,fn)=>{event=fn}};
 const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return true}};cr.action.prototype.run_system=function(){};
 const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:text=>({textContent:text})};
 vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'tool-reward-candidate.js'),'utf8'),{window,document,cr,Date,Number,Promise,Error,console});
 const reward=window.oneConnectToolRewardCandidate;reward.install();assert(reward.open('hint'));
 const root=document.body.children[0],panel=root.children[0],watch=panel.children[2],close=panel.children[4];watch.onclick();close.onclick({type:'click'});assert.equal(root.hidden,false,'ordinary close remains locked while provider is active');
 event({detail:{type:'game.round_ready'}});assert.equal(root.hidden,true,'scene change dismisses stale dialog even while cancellation is pending');
 assert.equal(reward.open('shuffle'),false,'cannot reopen while prior lifecycle is still busy');
 busy=false;finish({status:'cancelled'});await Promise.resolve();assert.equal(root.hidden,true);assert(reward.open('shuffle'));
 watch.onclick();event({detail:{type:'screen.SCREEN_BONUS'}});assert.equal(root.hidden,true,'gift screen also dismisses the pending dialog');
 console.log('scene changes dismiss pending ad dialog without reopening a busy lifecycle PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
