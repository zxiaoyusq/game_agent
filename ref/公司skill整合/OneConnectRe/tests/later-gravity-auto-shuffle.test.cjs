const assert=require('node:assert/strict'),levels=require('../config/levels.json').levels;
for(const [level,movement] of [[17,'gravity_left'],[22,'gravity_up'],[24,'gravity_right']]){let e=levels.find(x=>x.level===level);assert(e&&e.movement===movement);assert.equal(e.autoShuffle,'free',`level ${level} must use free automatic shuffle`)}
console.log('later gravity levels enable free automatic shuffle PASS');
