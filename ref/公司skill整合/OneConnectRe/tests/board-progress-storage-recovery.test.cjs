const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.children=[];this.style={};this.attributes={};}setAttribute(k,v){this.attributes[k]=v}removeAttribute(k){delete this.attributes[k]}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}}
let raw=JSON.stringify({version:1,level:2,score:12}),failRead=true,failWrite=false,reads=0;
const localStorage={getItem(){reads++;if(failRead)throw Error('temporary');return raw},setItem(k,v){if(failWrite)throw Error('temporary');raw=v}};
const listeners={},document={body:new El(),visibilityState:'visible',createElement:()=>new El()},window={addEventListener(n,f){listeners[n]=f}};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/board_progress_candidate.js','utf8'),{window,document,localStorage,Number,JSON,Math});
window.oneConnectFlyStarScoreCandidate={progress:()=>({stars:1,fraction:.5})};
const update=window.oneConnectBoardProgressCandidate.update,rt={running_layout:{name:'game'},all_global_vars:[{name:'level',data:1}]},area={left:0,top:0,width:100,height:20};
update(rt,area);update(rt,area);assert.equal(reads,1,'failed reads must not retry each frame');assert.equal(document.body.children[0].children[0].style.visibility,'hidden','unavailable player track is hidden');assert.equal(document.body.children[0].children.length,4,'star track is absent');
failRead=false;listeners.visibilitychange();update(rt,area);const root=document.body.children[0];assert.equal(root.attributes['aria-valuenow'],'12','foreground return reloads persisted progress');
failWrite=true;listeners['oneconnect:event']({detail:{type:'game.match'}});update(rt,area);assert.equal(root.style.display,'block');assert.equal(root.children[0].style.visibility,'hidden');assert.equal(root.attributes['aria-valuenow'],undefined);
failWrite=false;listeners['oneconnect:event']({detail:{type:'game.board_configured'}});update(rt,area);assert.equal(root.children[0].style.visibility,'visible');assert.equal(root.attributes['aria-valuenow'],'12','failed write must not invent a saved match');
listeners['oneconnect:event']({detail:{type:'game.match'}});assert.equal(JSON.parse(raw).score,13);
raw='{bad json';listeners.storage({key:null});update(rt,area);listeners.visibilitychange();update(rt,area);assert.equal(raw,'{bad json','invalid saved data must never be overwritten on recovery');
console.log('board progress recovers storage without inventing or overwriting data PASS');
