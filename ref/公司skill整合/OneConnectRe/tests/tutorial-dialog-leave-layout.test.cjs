const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
if(!process.argv[2])throw Error('Pass candidate tutorial JS and level');const level=Number(process.argv[3]);assert([3,7].includes(level));
class El{constructor(){this.style={};this.children=[];}appendChild(e){this.children.push(e)}setAttribute(){}addEventListener(){}}
let listener,frames=[],events=[];const runtime={running_layout:{name:'game'},all_global_vars:[{name:'pause',data:0}]};
const document={body:new El(),createElement:()=>new El(),querySelector:()=>null},window={document,localStorage:{getItem:()=>null},cr_getC2Runtime:()=>runtime,addEventListener:(_,f)=>listener=f,requestAnimationFrame:f=>frames.push(f),oneConnectHost:{emit:(type,detail)=>events.push({type,detail})}};window.window=window;
const cr={action:function(){}};cr.action.prototype.run_system=()=>true;
vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),{window,document,cr,localStorage:window.localStorage,requestAnimationFrame:window.requestAnimationFrame});
const guide=window[level===3?'oneConnectThirdGuide':'oneConnectSeventhGuide'];guide.install();listener({detail:{type:'game.board_configured',detail:{level}}});assert(guide.state().active);assert.equal(events[0].type,'tutorial.start');
listener({detail:{type:'screen.SCREEN_BONUS'}});assert.equal(guide.state().active,false,'bonus cancels guide');assert.equal(events.at(-1).type,'tutorial.cancelled');listener({detail:{type:'game.board_configured',detail:{level}}});assert(guide.state().active);
runtime.running_layout={name:'menu'};frames.shift()();assert.equal(guide.state().active,false);assert.equal(events.at(-1).type,'tutorial.cancelled');assert.equal(events.at(-1).detail.level,level);assert.equal(document.body.children[0].style.display,'none');assert.equal(frames.length,0,'stale guide must stop scheduling');
runtime.running_layout={name:'game'};listener({detail:{type:'game.board_configured',detail:{level}}});assert(guide.state().active,'unfinished tutorial may restart on next round');assert.equal(frames.length,1);
console.log('level '+level+' tutorial releases state and frame scheduling on exit PASS');
