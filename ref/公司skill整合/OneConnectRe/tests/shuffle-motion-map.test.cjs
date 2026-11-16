const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');const moduleStub={exports:{}};
vm.runInNewContext(fs.readFileSync('tools/shuffle_motion_map.js','utf8'),{module:moduleStub,Number,Array,Map,Set});const map=moduleStub.exports.map;
const before=[{uid:1,kind:1,x:0,y:0},{uid:2,kind:2,x:10,y:0},{uid:3,kind:1,x:20,y:0},{uid:4,kind:2,x:30,y:0}];
const after=[{...before[0],kind:2},{...before[1],kind:1},{...before[2],kind:2},{...before[3],kind:1}];
const result=map(before,after);assert.equal(result.length,4);for(const m of result){assert.equal(before.find(x=>x.uid===m.sourceUid).kind,m.kind);assert.equal(after.find(x=>x.uid===m.targetUid).kind,m.kind)}
assert.equal(new Set(result.map(x=>x.sourceUid)).size,4);assert.equal(map(before,after.slice(1)),null);
assert.equal(map(before,after.map((x,i)=>i?x:{...x,kind:9})),null);assert.equal(map(before,[...after.slice(0,3),after[0]]),null);
console.log('shuffle visual mapping preserves kinds and rejects mismatched boards PASS');
