const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.hidden=false;this.style={};}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
(async()=>{
  const tip={name:'tip',data:0},shuffle={name:'shuffle',data:0},level={name:'level',data:1};let hammer=0,theme=0,callback,event;const deferred=[];
  const runtime={running_layout:{name:'game'},all_global_vars:[tip,shuffle,level],types:{t25:{instances:[]}}};
  const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return false}};cr.action.prototype.run_system=function(){};
  const window={cr,cr_getC2Runtime:()=>runtime,addEventListener(name,fn){if(name==='oneconnect:event')event=fn},oneConnectHost:{emit(type,data){if(type==='candidate.reward_save_deferred')deferred.push(data.kind)}},oneConnectHammer:{credit(n){hammer+=n;return true},rewardPersisted(){return false}},oneConnectThemeInventoryCandidate:{credit(n){theme+=n;return true},rewardPersisted(){return false}}};
  const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:text=>({textContent:text})};
  const ctx={window,document,cr,console,Date,Number,Promise,Error,Set,setTimeout,clearTimeout};
  for(const file of ['tools/reward_lifecycle_candidate.js','tools/tool_reward_candidate.js'])vm.runInNewContext(fs.readFileSync(file,'utf8'),ctx);
  const reward=window.oneConnectToolRewardCandidate;reward.install();reward.setProvider({show(cb){callback=cb}});
  const root=document.body.children[0],watch=root.children[0].children[2];
  for(const kind of ['hint','shuffle','hammer','theme']){
    assert.equal(reward.open(kind),true);watch.onclick();callback.earned({verified:false});
    assert.deepEqual([tip.data,shuffle.data,hammer,theme],kind==='hint'?[0,0,0,0]:kind==='shuffle'?[2,0,0,0]:kind==='hammer'?[2,2,0,0]:[2,2,2,0]);
    callback.earned({verified:true});callback.earned({verified:true});callback.closed();await Promise.resolve();assert.equal(root.hidden,true);
  }
  assert.deepEqual([tip.data,shuffle.data,hammer,theme],[2,2,2,2]);
  assert.deepEqual(deferred,['hint','shuffle','hammer','theme'],'failed saves are observable for all four tools');
  assert.equal(reward.open('hint'),true);watch.onclick();let prior=callback;
  event({detail:{type:'game.round_ready',detail:{level:1}}});prior.earned({verified:true});prior.closed();await Promise.resolve();
  assert.equal(tip.data,2,'late reward cannot credit a restarted unconfigured round');assert.equal(root.hidden,true);
  assert.equal(reward.open('hint'),true);watch.onclick();level.data=2;
  callback.earned({verified:true});callback.closed();await Promise.resolve();
  assert.equal(tip.data,2,'late reward cannot credit a different level');
  console.log('four tools require verified callback and credit exactly two PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
