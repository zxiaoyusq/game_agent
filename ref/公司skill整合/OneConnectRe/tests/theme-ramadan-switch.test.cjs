const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const moduleStub={exports:{}};vm.runInNewContext(fs.readFileSync('tools/theme_switch_candidate.js','utf8'),{module:moduleStub,globalThis:{}});const {switchTheme}=moduleStub.exports;
function tile(frame){return {cur_frame:frame,instance_vars:[],cur_animation:{name:'t0'},getAnimationByName(n){return n==='t3'?{name:'t3',frames:Array(20)}:{name:'t0',frames:Array(30)}}};}
const theme={name:'theme',data:0},tiles=[tile(0),tile(19)],runtime={running_layout:{name:'game'},all_global_vars:[theme],types:{t5:{instances:tiles}}};
const actions={SetAnim(name){this.cur_animation=this.getAnimationByName(name)}};
assert.equal(switchTheme(runtime,3,actions).status,'switched');assert.equal(theme.data,3);assert.deepEqual(tiles.map(x=>x.cur_frame),[0,19]);
theme.data=0;for(const x of tiles)x.cur_animation={name:'t0'};tiles[1].cur_frame=20;
assert.equal(switchTheme(runtime,3,actions).status,'unavailable');assert.equal(theme.data,0);assert.deepEqual(tiles.map(x=>x.cur_animation.name),['t0','t0'],'missing frame cannot partially switch a board');
assert.equal(switchTheme(runtime,4,actions).status,'invalid_theme');
console.log('Ramadan switch preserves frame IDs and rejects unsupported boards PASS');
