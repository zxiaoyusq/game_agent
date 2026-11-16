const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let now=0,timers=[],animations=[],moving=false,switching=false,random=0;const listeners={};
class El{constructor(tag){this.tag=tag;this.style={};this.children=[]}setAttribute(){}appendChild(e){this.children.push(e)}append(...items){this.children.push(...items)}addEventListener(){}querySelector(tag){return this.children.find(x=>x.tag===tag)||null}animate(frames,options){const a={target:this,frames,options,cancel(){this.cancelled=true}};animations.push(a);return a}}
const hammer=new El('button');hammer.style.display='none';hammer.append(new El('img'));
const runtime={running_layout:{name:'game'},all_global_vars:[{name:'pause',data:0},{name:'level',data:1}]};
const window={addEventListener:(type,fn)=>listeners[type]=fn,setTimeout:(fn,ms)=>{const timer={fn,ms};timers.push(timer);return timer},clearTimeout:timer=>{timers=timers.filter(x=>x!==timer)},cr_getC2Runtime:()=>runtime,oneConnectGravityRuntime:{state:()=>({moving})},oneConnectThemeSwitchCandidate:{isAnimating:()=>switching}};
const document={body:new El('body'),createElement:tag=>new El(tag),getElementById:id=>id==='oc-hammer'?hammer:null,hidden:false},Date={now:()=>now};
const deterministicMath=Object.create(Math);deterministicMath.random=()=>random;
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/layout_candidate.js','utf8'),{window,document,Date,Number,Array,Object,Math:deterministicMath,RangeError,localStorage:{getItem:()=>null},setTimeout(){},clearTimeout(){},requestAnimationFrame(){}});
window.oneConnectLayoutCandidate.install();
function fire(){const timer=timers.shift();assert.equal(timer.ms,4000,'each interval is four seconds');timer.fn()}
fire();assert.equal(animations.length,1);const first=animations[0];assert.equal(first.target.tag,'img');assert.equal(first.options.iterations,3);assert.equal(first.frames[0].easing,'cubic-bezier(0,0,.4,1)');assert.equal(first.frames[1].easing,'cubic-bezier(.6,0,1,1)');assert.equal(first.frames[1].transform,'translateY(-18%)');assert.equal(first.frames[2].transform,'translateY(0)');assert.equal(timers.length,0,'the next interval waits until the three jumps finish');first.onfinish();assert.equal(timers.length,1);
moving=true;fire();assert.equal(animations.length,1,'no jump during board movement');moving=false;fire();assert.equal(animations.length,2);
runtime.all_global_vars[0].data=1;animations[1].onfinish();fire();assert.equal(animations.length,2,'no jump while paused');
runtime.all_global_vars[0].data=0;random=.99;fire();assert.notEqual(animations[2].target,hammer.children[0],'a locked hammer cannot be chosen');animations[2].onfinish();
runtime.all_global_vars[1].data=7;hammer.style.display='flex';random=.26;fire();assert.equal(animations[3].target,hammer.children[0],'the unlocked hammer artwork can be chosen even when no inventory is specified');
listeners['oneconnect:event']({detail:{type:'game.board_configured'}});assert.equal(animations[3].cancelled,true,'a new round cancels the old icon movement');assert.equal(timers.length,1,'a new round starts one fresh interval');assert.equal(timers[0].ms,4000);
switching=true;fire();assert.equal(animations.length,4,'no idle icon jump during a theme transition');
console.log('unlocked tool icon jumps three times, then waits four seconds PASS');
