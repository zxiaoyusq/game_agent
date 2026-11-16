const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const file=process.argv[2];assert(file,'pass the candidate fifth-level guide');
class El{constructor(){this.style={};this.children=[]}appendChild(e){this.children.push(e)}}
let listener,stored={},events=[];const runtime={running_layout:{name:'game'},all_global_vars:[{name:'level',data:5},{name:'tip',data:2},{name:'pause',data:0}]};
const cr={plugins_:{Touch:function(){}},condition:function(){},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject:()=>true};cr.condition.prototype.run_system=()=>false;cr.action.prototype.run_system=()=>true;
const document={body:new El(),head:new El(),createElement:()=>new El()},storage={getItem:key=>stored[key]||null,setItem:(key,value)=>{stored[key]=value}};
const window={cr,localStorage:storage,cr_getC2Runtime:()=>runtime,addEventListener:(_n,fn)=>listener=fn,oneConnectHost:{emit:(type,detail)=>events.push({type,detail})}};window.window=window;
vm.runInNewContext(fs.readFileSync(file,'utf8'),{window,document,cr,localStorage:storage,requestAnimationFrame(){},innerWidth:400,innerHeight:800,Number,Date});
window.oneConnectFifthGuide.install();listener({detail:{type:'game.board_configured',detail:{level:5}}});assert.equal(window.oneConnectFifthGuide.state().active,true);
cr.action.prototype.run_system.call({sid:946296122197588,runtime});
assert.equal(window.oneConnectFifthGuide.state().active,false,'clicking the target completes the guide');
assert.equal(document.body.children[0].style.display,'none','the overlay and its animations are hidden');
assert(events.some(x=>x.type==='tutorial.complete'&&x.detail.level===5));
assert(Object.values(stored).includes('done'));
console.log('fifth-level target closes and completes the guide PASS');
