const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');const sandbox={};vm.runInNewContext(fs.readFileSync('tools/board_solver.js','utf8'),sandbox);const {solveBoard}=sandbox;
const levels=JSON.parse(fs.readFileSync('config/five-movement-validation.json','utf8')).levels;
for(const item of levels){const out=solveBoard(item.board,item.level,10000);assert.equal(out.status,'solved');assert.equal(out.moves.length,36);assert.equal(out.mode,['static','fall_down','fall_up','move_right','move_left'][item.level-1]);}
assert.equal(solveBoard([[1,1]],1,0).status,'unknown');assert.equal(solveBoard([[1,2],[2,1]],1,100).status,'unsolvable');assert.equal(solveBoard([[1,2]],1,100).status,'unsolvable');assert.throws(()=>solveBoard([[true,true]],1,100));
console.log('board solver JS: five modes and bounded results PASS');
