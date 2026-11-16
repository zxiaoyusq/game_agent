const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.children=[];this.hidden=false;this.style={}}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}setAttribute(){}addEventListener(){}}
(async()=>{let listeners=[],callbacks;const tip={name:'tip',data:0},rt={running_layout:{name:'game'},all_global_vars:[{name:'level',data:1},tip],types:{t25:{instances:[]}}};
const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject(){return true}};cr.action.prototype.run_system=function(){};
const window={cr_getC2Runtime:()=>rt,addEventListener(n,f){if(n==='oneconnect:event')listeners.push(f)},oneConnectHost:{emit(){}},oneConnectRoundSave:{capture(){return false}}};
const document={body:new El(),head:new El(),createElement:()=>new El(),createTextNode:t=>({textContent:t})},ctx={window,document,cr,Date,Number,Promise,Error,Set,setTimeout,clearTimeout,console};
for(const file of ['reward-lifecycle.js','tool-reward-candidate.js'])vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],file),'utf8'),ctx);
const reward=window.oneConnectToolRewardCandidate;reward.install();reward.setProvider({show(cb){callbacks=cb}});assert(reward.open('hint'));const watch=document.body.children[0].children[0].children[2];watch.onclick();callbacks.shown();
listeners.forEach(f=>f({detail:{type:'game.level_win'}}));callbacks.earned({verified:true});callbacks.closed();await Promise.resolve();assert.equal(tip.data,0,'late callback after victory cancellation does not credit a completed round');assert.equal(reward.open('hint'),false);
listeners.forEach(f=>f({detail:{type:'game.board_configured'}}));assert(reward.open('hint'));watch.onclick();callbacks.shown();callbacks.earned({verified:true});callbacks.closed();await Promise.resolve();assert.equal(tip.data,2,'verified reward before round end credits once');
console.log('reward callback ordering across victory is explicitly bounded PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
