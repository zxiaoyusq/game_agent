const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.children=[];this.style={};this.attributes={};}setAttribute(k,v){this.attributes[k]=v}removeAttribute(k){delete this.attributes[k]}appendChild(x){this.children.push(x)}append(...x){this.children.push(...x)}}
const key='oneconnect.user-level.candidate.v1',values=new Map([[key,JSON.stringify({version:1,level:2,score:12})]]),listeners={};
const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v)};
const document={body:new El(),createElement:()=>new El()},window={addEventListener:(n,f)=>{listeners[n]=f}};
vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'board-progress-candidate.js'),'utf8'),{window,document,localStorage:storage,Number,JSON,Math});
const update=window.oneConnectBoardProgressCandidate.update,rt={running_layout:{name:'game'}},area={left:0,top:0,width:100,height:20};
update(rt,area);const root=document.body.children[0];assert.equal(root.attributes['aria-valuenow'],'12');
const crop=root.children[1],fillArt=crop.children[0].children[0];assert.match(crop.style.cssText,/left:3%;.*width:94%/);assert.equal(fillArt.style.width,'94px','fill art follows the visible track width');
values.clear();listeners.storage({key:null});update(rt,area);assert.equal(root.attributes['aria-valuenow'],'0');
listeners['oneconnect:event']({detail:{type:'game.match'}});assert.deepEqual(JSON.parse(values.get(key)),{version:1,level:0,score:1},'match must not restore stale progress');
console.log('external storage clear invalidates progress cache PASS');
