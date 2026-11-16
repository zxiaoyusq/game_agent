const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let writes=0,frames=[],rect={left:0,top:0,right:390,bottom:844};
class El{constructor(){this.children=[];this.dataset={};this._hidden=false;this.style=new Proxy({}, {set(o,k,v){if(k!=='cssText')writes++;o[k]=v;return true}})}set hidden(v){writes++;this._hidden=v}get hidden(){return this._hidden}setAttribute(){}appendChild(x){this.children.push(x);return x}append(...x){this.children.push(...x)}addEventListener(){}focus(){}}
const body=new El(),document={body,head:new El(),createElement:()=>new El(),addEventListener(){}};
const rt={running_layout:{name:'menu'},canvas:{getBoundingClientRect:()=>rect}},w={innerWidth:390,innerHeight:844,cr_getC2Runtime:()=>rt};
vm.runInNewContext(fs.readFileSync('tools/home_settings_candidate.js','utf8'),{window:w,document,requestAnimationFrame:f=>frames.push(f),Math});w.oneConnectHomeSettingsCandidate.install();
const tick=()=>{const f=frames.shift();assert(f);f()};tick();const stable=writes;for(let i=0;i<10;i++)tick();assert.equal(writes,stable,'static menu must not write unchanged button styles');
rect={...rect,right:350};tick();assert.equal(body.children[0].style.left,'290px','button moves after canvas changes');rt.running_layout.name='game';tick();assert.equal(body.children[0].hidden,true,'button hides outside menu');
console.log('settings launcher avoids redundant writes but responds to changes PASS');
