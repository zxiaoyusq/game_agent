const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class El{constructor(){this.style={};this.children=[];this.handlers={}}setAttribute(){}appendChild(el){this.children.push(el)}addEventListener(name,fn){this.handlers[name]=fn}}
let listener,timer,done,opens=0,reloads=0,suspended=false;const document={body:new El(),createElement:()=>new El(),getElementById:()=>null};
const window={addEventListener:(_n,fn)=>listener=fn,setTimeout:fn=>timer=fn,cr_setSuspended:v=>suspended=v,location:{reload(){reloads++}},oneConnectUiMotion:{open(){opens++},close(_screen,_card,callback){done=callback}}};
vm.runInNewContext(fs.readFileSync('game/board-error.js','utf8'),{window,document});listener({detail:{type:'config.gravity_error'}});
assert.equal(opens,1,'error card opens with motion');timer();assert.equal(suspended,true);const home=document.body.children[0].children[0].children.find(el=>el.textContent==='HOME');assert(home,'error card has a home button');home.handlers.click();assert.equal(reloads,0,'reload waits for the close animation');done();assert.equal(reloads,1);
console.log('board error remains visible and reload follows close motion PASS');
