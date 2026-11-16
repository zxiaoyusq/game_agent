const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function Action(){}Action.prototype.run_object=function(){};Action.prototype.run_system=function(){};
const tween={tweened:1,target:'96,96',tween_list:{default:{targetparam1:96,targetparam2:96}}};
const tile={behavior_insts:[tween]},rt={all_global_vars:[{name:'level',data:8}],types:{t5:{getCurrentSol:()=>({getObjects:()=>[tile]})}}};
const window={cr:{action:Action},oneConnectLevels:{levels:[{level:8,boardSize:{rows:8,cols:8,itemSize:75,spacing:5,offsetX:320,offsetY:35}}]},oneConnectHost:{emit(){}}};window.window=window;
vm.runInNewContext(fs.readFileSync('game/board-hooks.js','utf8'),window);window.oneConnectBoard.install();
Action.prototype.run_system.call({sid:511736629732629,runtime:rt});assert.equal(tween.target,'75,75');assert.equal(tween.tween_list.default.targetparam1,75);assert.equal(tween.tween_list.default.targetparam2,75);
console.log('configured tile size is used by spawn tween PASS');
