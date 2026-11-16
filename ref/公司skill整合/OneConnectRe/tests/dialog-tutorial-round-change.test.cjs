const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const dir=process.argv[2];assert(dir,'pass generated game directory');
for(const [file,level,key] of [['tutorial-third.js',3,'oneConnectThirdGuide'],['tutorial-seventh.js',7,'oneConnectSeventhGuide']]){
 let listener,events=[];const el=()=>({style:{},appendChild(){},setAttribute(){},addEventListener(){}});
 const rt={all_global_vars:[{name:'level',data:level},{name:'pause',data:0}],running_layout:{name:'game'}};
 const w={cr_getC2Runtime:()=>rt,addEventListener:(_,fn)=>listener=fn,oneConnectHost:{emit:type=>events.push(type)},requestAnimationFrame(){}};
 const cr={action:function(){}};cr.action.prototype.run_system=()=>{};
 const document={createElement:el,body:{appendChild(){}},querySelector:()=>null};
 vm.runInNewContext(fs.readFileSync(path.join(dir,file),'utf8'),{window:w,document,cr,localStorage:{getItem:()=>null,setItem(){}},requestAnimationFrame(){}});
 w[key].install();const send=(type,detail={})=>listener({detail:{type,detail}});
 for(const stop of ['game.board_configured','game.round_ready','game.level_win','game.level_fail']){
  send('game.board_configured',{level});assert.equal(w[key].state().active,true);
  send(stop,{level:level+1});assert.equal(w[key].state().active,false,`${file} releases on ${stop}`);
 }
 assert.equal(events.filter(x=>x==='tutorial.cancelled').length,4);
}
console.log('dialog tutorials release on round change PASS');
