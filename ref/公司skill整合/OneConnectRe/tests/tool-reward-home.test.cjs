const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.hidden=false;this.style={};}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
(async()=>{
 const level={name:'level',data:1},tip={name:'tip',data:0};let event,callbacks;
 const runtime={running_layout:{name:'game'},all_global_vars:[level,tip],types:{t25:{instances:[]}}};
 const cr={plugins_:{Touch:function(){},Spritefont2:function(){}},action:function(){}};
 cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return false}};cr.plugins_.Spritefont2.prototype.acts={SetText(){}};cr.action.prototype.run_system=function(){};
 const window={cr,cr_getC2Runtime:()=>runtime,addEventListener(name,fn){if(name==='oneconnect:event')event=fn}};
 const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:text=>({textContent:text})};
 const ctx={window,document,cr,console,Date,Number,Promise,Error,Set,setTimeout,clearTimeout};
 for(const file of ['tools/reward_lifecycle_candidate.js',process.argv[2]||'tools/tool_reward_candidate.js'])vm.runInNewContext(fs.readFileSync(file,'utf8'),ctx);
 const reward=window.oneConnectToolRewardCandidate;reward.install();reward.setProvider({show(cb){callbacks=cb}});
 assert.equal(reward.open('hint'),true);const root=document.body.children[0];root.children[0].children[2].onclick();
 runtime.running_layout.name='menu';event({detail:{type:'screen.SCREEN_HOME'}});
 assert.equal(root.hidden,true,'returning home closes the reward overlay');
 assert.equal(reward.state().busy,false,'returning home cancels pending request');
 callbacks.earned({verified:true});callbacks.closed();await Promise.resolve();assert.equal(tip.data,0,'late callback does not credit the abandoned round');
 runtime.running_layout.name='game';event({detail:{type:'game.round_ready'}});assert.equal(reward.open('hint'),true,'a new round can open the reward dialog');
 root.children[0].children[4].onclick();
 console.log('reward overlay closes and pending request cancels on home PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
