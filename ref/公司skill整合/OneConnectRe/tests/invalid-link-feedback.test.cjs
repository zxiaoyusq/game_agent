const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.attrs={};this.children=[];this.style={};this.removed=false}setAttribute(k,v){this.attrs[k]=String(v)}appendChild(x){this.children.push(x)}remove(){this.removed=true}animate(frames,options){this.animation={frames,options};return{cancel(){}}}}
const body=new El(),document={body,createElementNS:()=>new El()},listeners={},timers=new Map();let next=0,cancelled=0;
const canvas={animate(frames,options){this.animation={frames,options};return{cancel(){cancelled++}}}},runtime={running_layout:{name:'game'},canvas};
const window={cr_getC2Runtime:()=>runtime,addEventListener:(name,fn)=>listeners[name]=fn};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/invalid_link_feedback_candidate.js','utf8'),{window,document,Number,Math,Array,setTimeout(fn){timers.set(++next,fn);return next},clearTimeout(id){timers.delete(id)}});
window.oneConnectInvalidLinkFeedbackCandidate.install();const emit=(type,detail)=>listeners['oneconnect:event']({detail:{type,detail}});
emit('candidate.invalid_link',{points:[{x:10,y:20},{x:90,y:60}]});const svg=body.children[0];assert.equal(svg.children.length,3);assert.equal(svg.children[0].attrs.x1,'10');assert.equal(svg.children[0].attrs.x2,'90');assert.equal((+svg.children[1].attrs.y1 + +svg.children[1].attrs.y2)/2,40,'cross is centered between the tiles');assert.equal(svg.children[1].animation.options.duration,60,'cross uses the verified entrance duration');
assert.deepEqual(svg.animation,canvas.animation,'feedback overlay and board share the same shake timing and displacement');
emit('game.auto_shuffle_start');assert(svg.removed,'auto shuffle clears failed-link feedback');assert.equal(cancelled,1);assert.equal(timers.size,0);
emit('candidate.invalid_link',{points:[{x:NaN,y:20},{x:90,y:60}]});assert.equal(body.children.length,1,'invalid coordinates produce no overlay');
emit('candidate.invalid_link',{points:[{x:10,y:20},{x:90,y:60}]});const second=body.children[1];timers.get(next)();assert(second.removed,'feedback is removed after its display duration');
console.log('failed-link line, cross, shake and cleanup PASS');
