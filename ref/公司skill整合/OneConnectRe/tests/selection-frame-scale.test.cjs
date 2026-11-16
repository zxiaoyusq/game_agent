const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function Action(){}Action.prototype.run_object=function(){if(this.spawn)this.runtime.createRow.push(this.spawn);return 'native'};
const cr={action:Action},window={cr},tile={width:75,height:75},runtime={createRow:[],types:{t5:{getCurrentSol:()=>({getObjects:()=>[tile]})}}};
vm.runInNewContext(fs.readFileSync(process.argv[2]||'tools/selection_frame_candidate.js','utf8'),{window,cr,Number,Array,Math,Set});window.oneConnectSelectionFrameCandidate.install();
const sine={movement:2,initialValue:108,mag:5},mark={type:{name:'t28'},behavior_insts:[sine],set_bbox_changed(){this.changed=true}};
assert.equal(Action.prototype.run_object.call({sid:881765380413314,runtime,spawn:mark}),'native');assert.equal(mark.width,84.375);assert.equal(mark.height,84.375);assert.equal(sine.initialValue,mark.width);assert.equal(sine.mag,5*75/96);assert(mark.changed);
tile.width=96;tile.height=96;const mark2={type:{name:'t28'},behavior_insts:[{movement:2,initialValue:108,mag:5}],set_bbox_changed(){}};Action.prototype.run_object.call({sid:881765380413314,runtime,spawn:mark2});assert.equal(mark2.width,108);assert.equal(mark.width,84.375,'previous marks are not resized');
console.log('native selection mark and pulse track tile dimensions PASS');
