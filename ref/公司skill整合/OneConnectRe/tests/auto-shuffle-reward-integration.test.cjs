const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
class El{constructor(){this.children=[];this.hidden=false;this.style={}}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
const dir=process.argv[2],file=(source,candidate)=>dir?path.join(dir,candidate):source;
const cr={action:function(){},condition:function(){},plugins_:{Touch:function(){}}};cr.action.prototype.run_object=function(){};cr.action.prototype.run_system=function(){};cr.condition.prototype.run_system=function(){return true};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return true}};
const level={name:'level',data:1},tip={name:'tip',data:0},shuffle={name:'shuffle',data:0},pause={name:'pause',data:0};
const runtime={running_layout:{name:'game'},all_global_vars:[level,tip,shuffle,pause],types:{t5:{instances:[]}}};let listeners=[],timer;
const document={head:new El(),body:new El(),createElement:()=>new El(),createTextNode:t=>({textContent:t}),addEventListener(){}};
const window={cr,cr_getC2Runtime:()=>runtime,c2_callFunction(){},oneConnectLevels:{levels:[{level:1,autoShuffle:'free'}]},oneConnectHost:{emit(type,detail){listeners.forEach(f=>f({detail:{type,detail}}))}},oneConnectRewardLifecycle:{create:()=>({state:()=>({busy:false}),cancel(){}})},setTimeout(fn,ms){if(ms===5000)timer=fn;return ms},clearTimeout(){},addEventListener(name,fn){if(name==='oneconnect:event')listeners.push(fn)},requestAnimationFrame(){}};
const ctx={window,document,cr,Date,Number,Array,Promise,Error,Map,console};
for(const [source,candidate] of [['tools/auto_shuffle_candidate.js','auto-shuffle.js'],['tools/shuffle_motion_candidate.js','shuffle-motion-candidate.js'],['tools/tool_reward_candidate.js','tool-reward-candidate.js']])vm.runInNewContext(fs.readFileSync(file(source,candidate),'utf8'),ctx);
window.oneConnectAutoShuffle.install();window.oneConnectShuffleMotionCandidate.install();window.oneConnectToolRewardCandidate.install();
const touch=frame=>cr.plugins_.Touch.prototype.cnds.OnTouchObject.call({runtime},{name:'t26',getCurrentSol:()=>({getObjects:()=>[{cur_frame:frame}]})});
cr.action.prototype.run_object.call({runtime,sid:484278472184714});assert.equal(touch(0),false);assert.equal(window.oneConnectToolRewardCandidate.state().open,false,'automatic shuffle must not open refill');
timer();assert.equal(touch(0),false);assert.equal(window.oneConnectToolRewardCandidate.state().open,true,'empty stock opens refill after shuffle expires');
console.log('auto shuffle and refill input wrappers compose in installation order PASS');
