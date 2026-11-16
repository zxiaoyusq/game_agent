const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.style={};this.attrs={};}setAttribute(k,v){this.attrs[k]=v}removeAttribute(k){delete this.attrs[k]}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}}
let calls=0;const window={addEventListener(){},oneConnectFlyStarScoreCandidate:{progress:()=>{calls++;return {stars:1,fraction:.5}}}},document={body:new El(),createElement:()=>new El()};
vm.runInNewContext(fs.readFileSync('tools/board_progress_candidate.js','utf8'),{window,document,localStorage:{getItem:()=>null},Number,JSON,Math});
const update=window.oneConnectBoardProgressCandidate.update,r={running_layout:{name:'game'},all_global_vars:[{name:'level',data:5}]},area={left:0,top:80,width:200,height:20};
update(r,area);const root=document.body.children[0];assert.equal(root.children.length,4,'only the level track and its labels remain');assert.equal(calls,0,'disabled star scoring must not be queried');
update({running_layout:{name:'menu'}},area);assert.equal(root.style.display,'none');
console.log('level track renders without an in-game star track PASS');
