const assert=require('node:assert/strict'),levels=require('../config/levels.json').levels;
for(const level of [18,26,27,29]){let e=levels.find(x=>x.level===level);assert(e&&e.movement==='static');assert.equal(e.autoShuffle,'free',`level ${level} must use the free automatic shuffle policy`)}
console.log('later static levels enable free automatic shuffle PASS');
