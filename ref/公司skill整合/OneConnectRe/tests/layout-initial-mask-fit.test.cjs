const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class El{constructor(){this.style={};this.children=[]}setAttribute(){}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}addEventListener(){}get lastElementChild(){return this.children.at(-1)}}
let frames=[],board={left:20,top:200,width:360,height:400};const layer={scale:1,layerToCanvas(x,y,isX){return isX?200+(x-200)*this.scale:400+(y-400)*this.scale}};
const vars=[['COLUMNS_COUNT',4],['ROWS_COUNT',4],['ITEM_SIZE',50],['ITEM_SPACING',0],['level',2],['pause',0]].map(([name,data])=>({name,data}));
const tile={x:175,y:375,layer,instance_vars:[0,2,2]},runtime={running_layout:{name:'game'},all_global_vars:vars,types:{t5:{instances:[tile]},t25:{instances:[]}},canvas:{width:400,height:800,getBoundingClientRect:()=>({left:35,top:70,width:400,height:800})}};
const area=()=>({left:0,top:0,width:40,height:30}),window={addEventListener(){},cr_getC2Runtime:()=>runtime,oneConnectToolUnlock:{unlocked(){return true}},oneConnectLevels:{levels:[{level:2,generator:{mask:[[0,0,0,0],[0,1,1,0],[0,1,1,0],[0,0,0,0]]}}]},oneConnectLayoutAdapter:{restore(){},moveHud(){},moveTools(){},movePause(){},setToolsHidden(){}},oneConnectLayoutGeometry:{calculate(){return{header:area(),progress:area(),board:{left:100,top:300,width:200,height:200},fitArea:{...board},banner:area(),tools:Array.from({length:4},area)}}}};
function Action(){}Action.prototype.run_system=function(){layer.scale=1};window.cr={action:Action};
const document={body:new El(),createElement:()=>new El(),getElementById:()=>null};vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/layout_candidate.js','utf8'),{window,cr:window.cr,document,localStorage:{getItem:()=>null},Number,Array,Object,Date,Math,RangeError,setTimeout(){},clearTimeout(){},requestAnimationFrame:f=>frames.push(f)});
window.oneConnectLayoutCandidate.install();frames.shift()();assert.equal(layer.scale,3.6,'fit uses occupied initial shape and canvas-relative bounds even when the canvas is offset');
Action.prototype.run_system.call({sid:913642290917496,runtime});assert.equal(layer.scale,3.6,'native portrait layout must not overwrite fitted board scale');
tile.x=225;tile.y=425;tile.instance_vars=[0,3,3];frames.shift()();assert.equal(layer.scale,3.6,'remaining tiles do not trigger a new scale');
console.log('board fitting uses stable initial mask bounds PASS');
const geometryContext={module:{exports:{}},Number,Math,RangeError};
vm.runInNewContext(fs.readFileSync('tools/in_game_layout.js','utf8'),geometryContext);
const geometry=geometryContext.module.exports.calculate({width:400,height:900,rows:12,cols:4,bannerHeight:0});
assert.ok(geometry.fitArea.width>geometry.board.width,'initial shape may use the full available board width');
assert.ok(geometry.fitArea.top+geometry.fitArea.height<=geometry.tools[0].top,'board fit area stays above the tools');
