const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
if(!process.argv[2])throw Error('candidate game directory required');
class El{constructor(){this.style={};this.children=[]}setAttribute(){}appendChild(x){this.children.push(x)}addEventListener(){}}
const listeners={},storage={getItem(){return null},setItem(){}},document={body:new El(),head:new El(),createElement:()=>new El()};
let frame;const rt={running_layout:{name:'game'},all_global_vars:[{name:'level',data:7},{name:'pause',data:0}],types:{t5:{instances:[{instance_vars:[0,0,0,0]},{instance_vars:[0,0,0,0]}]}}};
const w={localStorage:storage,cr_getC2Runtime:()=>rt,addEventListener:(n,fn)=>{(listeners[n]??=[]).push(fn)},requestAnimationFrame(fn){frame=fn}};w.window=w;
vm.runInNewContext(fs.readFileSync(path.join(process.argv[2],'hammer-runtime.js'),'utf8'),{window:w,document,localStorage:storage,Number,Date,Math});
w.oneConnectHammer.install();assert.equal(w.oneConnectHammer.use().status,'unavailable','ready before victory reaches the model check');
for(const fn of listeners['oneconnect:event'])fn({detail:{type:'game.level_win'}});
assert.equal(w.oneConnectHammer.use().status,'busy','hammer is blocked immediately on victory');frame();assert.equal(document.body.children[0].style.display,'none','hammer is hidden on next draw');
for(const fn of listeners['oneconnect:event'])fn({detail:{type:'game.board_configured'}});
assert.equal(w.oneConnectHammer.use().status,'unavailable','new board restores readiness');
console.log('hammer locks on victory and resets for next board PASS');
