const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class El{constructor(){this.style={};this.children=[];}setAttribute(){}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}addEventListener(){}get lastElementChild(){return this.children.at(-1)}}
let frames=[],projections=0,board={left:20,top:200,width:360,height:400};
const layer={scale:1,layerToCanvas(x,y,isX){projections++;return isX?200+(x-200)*this.scale:400+(y-400)*this.scale}};
const vars=[['COLUMNS_COUNT',4],['ROWS_COUNT',4],['ITEM_SIZE',50],['ITEM_SPACING',0],['level',2],['pause',0]].map(([name,data])=>({name,data}));
const runtime={running_layout:{name:'game'},all_global_vars:vars,types:{t5:{instances:[{x:125,y:325,layer,instance_vars:[0,1,1]}]},t25:{instances:[]}},canvas:{width:400,height:800,getBoundingClientRect:()=>({left:0,top:0,width:400,height:800})}};
const area=()=>({left:0,top:0,width:40,height:30}),w={addEventListener(){},cr_getC2Runtime:()=>runtime,oneConnectLayoutAdapter:{restore(){},moveHud(){},moveTools(){},movePause(){},setToolsHidden(){}},oneConnectLayoutGeometry:{calculate(){return{header:area(),progress:area(),board:{...board},banner:area(),tools:Array.from({length:4},area)}}}};
const document={body:new El(),createElement:()=>new El(),getElementById:()=>null};
vm.runInNewContext(fs.readFileSync('tools/layout_candidate.js','utf8'),{window:w,document,localStorage:{getItem:()=>null},Number,Array,Object,Date,Math,RangeError,setTimeout(){},clearTimeout(){},requestAnimationFrame:f=>frames.push(f)});
w.oneConnectLayoutCandidate.install();frames.shift()();assert.equal(layer.scale,1.8,'small board should grow to available width');
const initialProjections=projections;runtime.canvas.width=800;runtime.canvas.height=1600;runtime.isRetina=true;runtime.devicePixelRatio=2;frames.shift()();assert(projections>initialProjections,'backing size changes must recompute board fit');assert.equal(layer.scale,1.8);
board={left:120,top:200,width:160,height:400};w.oneConnectLayoutCandidate.configure({safeArea:{top:1}});frames.shift()();assert.equal(layer.scale,.8,'large board should shrink to available width');
console.log('board fit grows and shrinks within available bounds PASS');
