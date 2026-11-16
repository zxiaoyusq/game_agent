const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');if(!process.argv[2])throw Error('Pass candidate tutorial-third.js');
class El{constructor(){this.style={};this.children=[];this.listeners={};}appendChild(e){this.children.push(e)}setAttribute(){}addEventListener(n,f){this.listeners[n]=f}}
let listener,frames=[],events=[],saved=null;const runtime={running_layout:{name:'game'},all_global_vars:[{name:'pause',data:0}],types:{}};
const document={body:new El(),createElement:()=>new El()},storage={getItem:()=>saved,setItem:(_,v)=>saved=v},window={document,localStorage:storage,cr_getC2Runtime:()=>runtime,addEventListener:(_,f)=>listener=f,oneConnectHost:{emit:(type,detail)=>events.push({type,detail})}};window.window=window;
const cr={action:function(){}};cr.action.prototype.run_system=()=>true;
vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),{window,document,cr,localStorage:storage,oneConnectHost:window.oneConnectHost,requestAnimationFrame:f=>frames.push(f)});
const guide=window.oneConnectThirdGuide;guide.install();listener({detail:{type:'game.board_configured',detail:{level:3}}});frames.shift()();const overlay=document.body.children[0];assert.equal(overlay.style.display,'block','explanation remains visible without target controls');
assert.equal(overlay.children[0].style.display,'none');assert.equal(overlay.style.background,'rgba(4,10,30,.72)','missing target retains the dim');
runtime.canvas={width:400,height:800,getBoundingClientRect:()=>({left:0,top:0,width:400,height:800})};const layer={layerToCanvas:(x,y,horizontal)=>horizontal?x:y};runtime.types={t25:{instances:[{instance_vars:[1],x:100,y:100,width:50,layer}]},t24:{instances:[{cur_frame:1,x:50,y:100}]}};frames.shift()();assert.equal(overlay.children[0].style.display,'block');assert.equal(overlay.style.background,'','restored highlight replaces fallback dim');
runtime.types={};frames.shift()();assert.equal(overlay.children[0].style.display,'none');assert.equal(overlay.style.background,'rgba(4,10,30,.72)');
overlay.listeners.click({preventDefault(){},stopPropagation(){}});assert.equal(guide.state().active,false);assert.equal(saved,'done');assert.equal(events.at(-1).type,'tutorial.complete');assert.equal(events.at(-1).detail.level,3);
console.log('third tutorial remains dismissible when highlight targets are missing PASS');
