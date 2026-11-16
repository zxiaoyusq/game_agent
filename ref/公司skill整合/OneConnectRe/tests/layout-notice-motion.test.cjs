const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.style={};this.children=[];this.handlers={}}setAttribute(){}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}addEventListener(n,f){this.handlers[n]=f}getBoundingClientRect(){return {top:700}}}
let timer,opened=0,closed=0;const runtime={running_layout:{name:'game'},all_global_vars:[{name:'pause',data:0}],canvas:{getBoundingClientRect:()=>({left:0,top:0,width:400,height:800})}};
const window={addEventListener(){},cr_getC2Runtime:()=>runtime,oneConnectTutorialMotion:{open(){opened++},close(_el,opts,done){closed++;assert.equal(opts.durationMs,160);done()}},matchMedia:()=>({matches:false})};
const document={body:new El(),createElement:()=>new El(),getElementById:()=>null},context={window,document,Date,Number,Array,Object,Math,RangeError,localStorage:{getItem:()=>null},setTimeout:(fn,ms)=>{timer={fn,ms};return 1},clearTimeout(){},requestAnimationFrame(){}};
vm.runInNewContext(fs.readFileSync('tools/layout_candidate.js','utf8'),context);window.oneConnectLayoutCandidate.install();
const notice=document.body.children[4],button=document.body.children[5];button.handlers.click({preventDefault(){},stopPropagation(){}});
assert.equal(notice.style.display,'block');assert.equal(opened,1);assert.equal(timer.ms,1640);timer.fn();assert.equal(closed,1);assert.equal(notice.style.display,'none');
console.log('tool notice opens and closes with motion PASS');
