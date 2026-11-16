const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');let c={};vm.runInNewContext(fs.readFileSync('tools/board_solver.js','utf8'),c);let solve=c.solveBoard;
assert.equal(solve([[1,1],[2,2]],1,0,'static',[[[0,0],[0,1]],[[1,0],[1,1]]]).status,'solved');
for(const bad of [[],[[[0,0],[1,1]]],[[[0,0],[0,0]]],[[[0,0],[0,1]]],[[[0,0],[0,1]],[[5,0],[1,1]]]])assert.equal(solve([[1,1],[2,2]],1,0,'static',bad).status,'unknown');
assert.equal(solve([[1,2],[1,2]],1,0,'gravity_up',[[[0,0],[1,0]],[[0,1],[1,1]]]).status,'solved');
assert.equal(solve([[1,2],[1,2]],1,0,'gravity_up',[[[0,0],[1,0]],[[1,1],[0,1]]]).status,'solved');
let blocked=[[2,2,2,2,2],[2,1,2,1,2],[2,2,2,2,2],[2,2,2,2,2]];assert.equal(solve(blocked,1,0,'static',[[[1,1],[1,3]]]).status,'unknown');
let original=[[1,1],[2,2]];solve(original,1,0,'static',[[[0,0],[0,1]],[[1,0],[1,1]]]);assert.deepEqual(original,[[1,1],[2,2]],'verification must not mutate input');
console.log('candidate path requires valid matching, links, bounds and complete clearance PASS');
