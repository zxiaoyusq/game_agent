const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=process.argv[2];assert(source,'pass generated tutorial-first.js path');
const entry=JSON.parse(fs.readFileSync('config/levels.json','utf8')).levels.find(x=>x.level===1);
const el=()=>({style:{},children:[],appendChild(x){this.children.push(x)},setAttribute(){}});let listener,actions=0,events=[];
const rt={all_global_vars:[{name:'level',data:1}],running_layout:{name:'game'}};
const w={oneConnectLevels:{levels:[entry]},localStorage:{getItem:()=>null,setItem(){}},cr_getC2Runtime:()=>rt,addEventListener:(_,fn)=>listener=fn,oneConnectHost:{emit:(type,detail)=>events.push({type,detail})}};
const cr={plugins_:{Touch:function(){}},action:function(){}};cr.plugins_.Touch.prototype.cnds={OnTouchObject:()=>true};cr.action.prototype.run_system=()=>actions++;
const document={createElement:el,body:{appendChild(){}}};
vm.runInNewContext(fs.readFileSync(source,'utf8'),{window:w,document,cr,Date,Number,Array,Math,requestAnimationFrame(){}});
w.oneConnectTutorial.install();const send=(type,detail={})=>listener({detail:{type,detail}});
for(const stop of ['game.board_configured','game.round_ready','game.level_win','game.level_fail']){
  send('game.board_configured',{level:1});assert.equal(w.oneConnectTutorial.state().active,true);
  send('game.match',{level:2,source:'normal'});assert.equal(w.oneConnectTutorial.state().step,0,'other levels cannot advance the guide');
  assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'t26'}),false);
  cr.action.prototype.run_system.call({sid:367702696840255});assert.equal(actions,0,'tutorial freezes timer while active');
  send(stop,{level:2});assert.equal(w.oneConnectTutorial.state().active,false,`guide releases on ${stop}`);
  assert.equal(cr.plugins_.Touch.prototype.cnds.OnTouchObject({name:'t26'}),true,'tools are available after exit');
  cr.action.prototype.run_system.call({sid:367702696840255});assert.equal(actions,1,'timer resumes after exit');actions=0;
}
assert.equal(events.filter(e=>e.type==='tutorial.cancelled').length,4);
console.log('first tutorial releases gates on round change PASS');
