const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class El{constructor(){this.children=[];this.style={};this.hidden=false}appendChild(v){this.children.push(v);return v}append(...v){this.children.push(...v)}setAttribute(){}addEventListener(){}}
const hint={name:'tip',data:0},shuffle={name:'shuffle',data:0},level={name:'level',data:5};
const rt={running_layout:{name:'game'},all_global_vars:[hint,shuffle,level,{name:'pause',data:0}]};
const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject:()=>true,OnTouchStart:()=>true,OnTapGestureObject:()=>true};cr.action.prototype.run_system=()=>{};
let fifth=true,tenth=false;
const window={cr,cr_getC2Runtime:()=>rt,addEventListener(){},oneConnectFifthGuide:{state:()=>({active:fifth})},oneConnectTenthGuide:{state:()=>({active:tenth})},oneConnectRewardLifecycle:{create:()=>({state:()=>({busy:false})})}};
const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:()=>({})};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/tool_reward_candidate.js','utf8'),{window,document,cr,Date,Number,Promise,Error});
const reward=window.oneConnectToolRewardCandidate;reward.install();
const touch=frame=>cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'t26',getCurrentSol:()=>({getObjects:()=>[{cur_frame:frame}]})});
assert.equal(touch(1),true,'fifth tutorial may use a free hint with zero stock');assert.equal(reward.state().open,false);
fifth=false;tenth=true;assert.equal(touch(0),true,'tenth tutorial may use free shuffle with zero stock');assert.equal(reward.state().open,false);
tenth=false;
for(const name of ['oneConnectSecondGuide','oneConnectThirdGuide','oneConnectSeventhGuide']){
 window[name]={state:()=>({active:true})};assert.equal(touch(1),false,name+' blocks hint');assert.equal(touch(0),false,name+' blocks shuffle');assert.equal(reward.state().open,false,name+' does not open a reward dialog');delete window[name];
}
rt.all_global_vars.find(v=>v.name==='pause').data=1;
assert.equal(touch(1),false,'paused hint touch must not reach the native event');assert.equal(touch(0),false,'paused shuffle touch must not reach the native event');assert.equal(reward.state().open,false,'paused touch must not open the reward dialog');
rt.all_global_vars.find(v=>v.name==='pause').data=0;
window.oneConnectTenthGuide={};assert.doesNotThrow(()=>touch(1),'an unavailable guide state must not break tool input');assert.equal(reward.state().open,true);document.body.children[0].children[0].children[4].onclick();
tenth=false;assert.equal(touch(1),false,'outside tutorial the empty hint opens a reward dialog');assert.equal(reward.state().open,true);
assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'t5'}),false,'open reward dialog blocks underlying board touch');
assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'t22'}),false,'open reward dialog blocks underlying pause controls');
assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchStart(),false,'open reward dialog blocks generic touch');assert.equal(cr.plugins_.Touch.prototype.cnds.OnTapGestureObject(),false,'open reward dialog blocks tap gestures');
console.log('reward interception respects free tool tutorials PASS');
