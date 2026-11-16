const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
class El{constructor(){this.children=[];this.listeners={};this.style={};this.dataset={};this.hidden=false;this.classList={toggle(){}};}setAttribute(){}appendChild(x){this.children.push(x);return x;}append(...x){this.children.push(...x);}querySelector(selector){return this.children.find(x=>x.className===selector.slice(1))||null;}addEventListener(n,f){(this.listeners[n]??=[]).push(f);}focus(){} }
const body=new El(),head=new El(),document={body,head,createElement:()=>new El(),addEventListener(){}};
const cr={plugins_:{Touch:function(){}}};cr.plugins_.Touch.prototype.cnds={OnTouchObject:()=>true,OnTouchStart:()=>true,OnTapGestureObject:()=>true};
const window={cr,cr_getC2Runtime:()=>({running_layout:{name:'menu'}}),GAMESNACKS:{isAudioEnabled:()=>true,handleAudioUpdates(){}}};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/home_settings_candidate.js','utf8'),{window,document,requestAnimationFrame(){}});
window.oneConnectHomeSettingsCandidate.install();
const [launcher,overlay]=body.children;
for(const el of [launcher,overlay]) for(const type of ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click']){
 let stopped=false;for(const cb of el.listeners[type]||[])cb({stopPropagation(){stopped=true;},target:null});assert(stopped,type+' must not reach game document listeners');
}
assert.equal(overlay.hidden,false,'test opened the settings dialog');assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'play'}),false,'visible settings blocks underlying game touch');
assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchStart(),false,'visible settings blocks generic touch');assert.equal(cr.plugins_.Touch.prototype.cnds.OnTapGestureObject(),false,'visible settings blocks object tap gestures');
overlay.hidden=true;assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'play'}),true,'game touch resumes after closing');assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchStart(),true,'generic touch resumes after closing');
console.log('settings overlay intercepts pointer, touch and mouse input PASS');
