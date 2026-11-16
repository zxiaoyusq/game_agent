const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path');
const dir=process.argv[2];assert(dir,'pass generated game directory');
for(const [file,level,key] of [['tutorial-fifth.js',5,'oneConnectFifthGuide'],['tutorial-tenth.js',10,'oneConnectTenthGuide']]){
  let listener,frames=[],events=[],body=[];const element=()=>({style:{},children:[],appendChild(child){this.children.push(child)}});
  const runtime={all_global_vars:[{name:'level',data:level},{name:'pause',data:0}],running_layout:{name:'game'},types:{t26:{instances:[]}}};
  const w={window:null,cr_getC2Runtime:()=>runtime,addEventListener:(_,fn)=>listener=fn,oneConnectHost:{emit(type){events.push(type)}},requestAnimationFrame:fn=>frames.push(fn)};w.window=w;
  const cr={plugins_:{Touch:function(){}},condition:function(){},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject:()=>true};cr.condition.prototype.run_system=()=>false;cr.action.prototype.run_system=()=>{};
  const document={createElement:element,body:{appendChild(child){body.push(child)}},head:{appendChild(){}}};
  const context={window:w,document,cr,localStorage:{getItem:()=>null,setItem(){}},requestAnimationFrame:w.requestAnimationFrame};
  vm.runInNewContext(fs.readFileSync(path.join(dir,file),'utf8'),context);w[key].install();
  const fire=(type,data={})=>listener({detail:{type,detail:data}});
  for(const stop of ['game.board_configured','game.round_ready','game.level_win','game.level_fail']){
    fire('game.board_configured',{level});assert.equal(w[key].state().active,true,`${file} starts`);
    fire(stop,{level:level+1});assert.equal(w[key].state().active,false,`${file} releases on ${stop}`);
  }
  if(level===5){fire('game.board_configured',{level});for(let i=0;i<=250;i++){const frame=frames.shift();assert(frame,'missing target keeps waiting until timeout');frame(i*20);if(i===0){assert.equal(body[0].style.display,'block');assert.equal(body[0].children[1].textContent,'Getting hint ready...')}}assert.equal(w[key].state().active,false,'missing target releases input');assert(events.includes('tutorial.cancelled'),'downstream locks are released');assert(events.includes('candidate.tutorial5_target_missing'),'missing target is observable');assert.equal(frames.length,0,'timeout stops scheduling');}
}
console.log('tool tutorial round-change cleanup PASS');
