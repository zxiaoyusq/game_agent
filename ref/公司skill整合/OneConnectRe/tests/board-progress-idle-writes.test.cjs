const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let writes=0;class El{constructor(){this.children=[];this.style=new Proxy({}, {set(o,k,v){writes++;o[k]=v;return true}})}setAttribute(){}removeAttribute(){}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}}
const body=new El(),document={body,createElement:()=>new El()},window={addEventListener(){}},localStorage={getItem:()=>null};
vm.runInNewContext(fs.readFileSync('tools/board_progress_candidate.js','utf8'),{window,document,localStorage,Number,JSON,Math});
const update=window.oneConnectBoardProgressCandidate.update,game={running_layout:{name:'game'}},area={left:10,top:20,width:100,height:20};
update(game,area);const first=writes;for(let i=0;i<10;i++)update(game,area);assert.equal(writes,first,'unchanged progress must not rewrite styles');
update(game,{...area,width:110});assert.equal(writes,first+2,'only track width and fill width change');
update({running_layout:{name:'menu'}},area);const hidden=writes;update({running_layout:{name:'menu'}},area);assert.equal(writes,hidden,'hidden state should not be rewritten');
console.log('board progress idle style writes PASS');
