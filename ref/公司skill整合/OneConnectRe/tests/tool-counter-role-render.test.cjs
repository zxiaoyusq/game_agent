const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.children=[];this.style={};this.textContent=''}setAttribute(){}append(...x){this.children.push(...x)}appendChild(x){this.children.push(x)}addEventListener(){}get lastElementChild(){return this.children.at(-1)}}
let frame;const document={body:new El(),createElement:()=>new El(),getElementById:()=>null};
const shuffle={uid:902,instance_vars:[3],text:'5'},hint={uid:946,instance_vars:[4],text:'2'},wrong={uid:2,instance_vars:[2],text:'999'};
const runtime={running_layout:{name:'game'},canvas:{getBoundingClientRect:()=>({left:0,top:0,width:400,height:800})},all_global_vars:[{name:'COLUMNS_COUNT',data:12},{name:'ROWS_COUNT',data:6},{name:'level',data:8},{name:'pause',data:0}],types:{t5:{instances:[]},t25:{instances:[wrong,shuffle,hint]}}};
const rect=()=>({left:0,top:0,width:100,height:50});
const window={cr_getC2Runtime:()=>runtime,addEventListener(){},oneConnectLayoutGeometry:{calculate:()=>({header:rect(),progress:rect(),board:rect(),banner:rect(),tools:[rect(),rect(),rect(),rect()]})},oneConnectLayoutAdapter:{moveHud(){},moveTools(){},movePause(){},setToolsHidden(){},restore(){}}};window.window=window;
const localStorage={getItem:()=>null,setItem(){}};
vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'layout-candidate.js'),'utf8'),{window,document,localStorage,requestAnimationFrame:f=>frame=f,clearTimeout(){},setTimeout(){},Date,Number,Array,Object,Math});
window.oneConnectLayoutCandidate.install();frame();
assert.equal(document.body.children[2].children[1].textContent,'5');assert.equal(document.body.children[3].children[1].textContent,'2');
shuffle.text='4';hint.text='7';frame();assert.equal(document.body.children[2].children[1].textContent,'4');assert.equal(document.body.children[3].children[1].textContent,'7');
runtime.types.t25.instances=[{uid:2,instance_vars:[],text:'3'},{uid:46,instance_vars:[],text:'6'}];frame();
assert.equal(document.body.children[2].children[1].textContent,'3');assert.equal(document.body.children[3].children[1].textContent,'6');
console.log('candidate overlay renders rebuilt tool counters by role PASS');
