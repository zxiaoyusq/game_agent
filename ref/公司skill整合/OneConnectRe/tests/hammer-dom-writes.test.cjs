const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=process.argv[2];assert(source,'pass generated hammer-runtime.js path');
let writes=0,frames=[],elements=[];
class El{constructor(){this._text='';this._disabled=false;this.style=new Proxy({}, {set(o,k,v){if(k!=='cssText')writes++;o[k]=v;return true}});this.children=[];elements.push(this)}set textContent(v){writes++;this._text=v}get textContent(){return this._text}set disabled(v){writes++;this._disabled=v}get disabled(){return this._disabled}setAttribute(){}addEventListener(){}appendChild(x){this.children.push(x)}}
const level={name:'level',data:7},pause={name:'pause',data:0},runtime={running_layout:{name:'game'},all_global_vars:[level,pause],types:{t5:{instances:[{instance_vars:[1,1,1,0]},{instance_vars:[1,1,2,0]}]}}};
const w={cr_getC2Runtime:()=>runtime,addEventListener(){},requestAnimationFrame:f=>frames.push(f)};
const document={createElement:()=>new El(),body:{appendChild(){}}};
vm.runInNewContext(fs.readFileSync(source,'utf8'),{window:w,document,localStorage:{getItem:()=>null,setItem(){}},Date,Number,Array,Math});
w.oneConnectHammer.install();const tick=()=>{const f=frames.shift();assert(f);f()};tick();const stable=writes;for(let i=0;i<10;i++)tick();assert.equal(writes,stable,'unchanged frames do not write DOM properties');
w.oneConnectHammer.credit(2);tick();assert.equal(elements[1].textContent,'4','count still updates');pause.data=1;tick();assert.equal(elements[0].style.display,'none','pause still hides the button');pause.data=0;tick();assert.equal(elements[0].style.display,'flex','resume restores the button');
console.log('hammer skips redundant DOM writes and updates state PASS');
