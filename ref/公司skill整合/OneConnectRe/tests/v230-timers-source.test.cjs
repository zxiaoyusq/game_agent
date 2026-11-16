const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const game=process.argv[2],csv=process.argv[3];assert(game&&csv,'provide candidate game directory and source cfgLevels.csv');
const source=fs.readFileSync(csv,'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/).map(line=>line.split(',')),headers=source.shift(),levelCol=headers.indexOf('level'),timeCol=headers.indexOf('time');assert(levelCol>=0&&timeCol>=0,'source must contain level and time columns');
const rows=new Map(source.filter(x=>/^\d+$/.test(x[levelCol])&&/^\d+$/.test(x[timeCol])).map(x=>[Number(x[levelCol]),Number(x[timeCol])]));assert.equal(rows.size,500,'source inventory should cover expected 500 levels');
const context={window:{}};vm.runInNewContext(fs.readFileSync(game+'/level-config.js','utf8'),context);vm.runInNewContext(fs.readFileSync(game+'/level-timers.js','utf8'),context);const configured=context.window.oneConnectLevels.levels,timers=context.window.oneConnectTimerByLevel;
for(const [level,seconds] of rows)assert.equal(timers[level],seconds,`fallback level ${level}`);
for(const entry of configured)if(rows.has(entry.level))assert.equal(entry.seconds,rows.get(entry.level),`configured level ${entry.level}`);
assert.notEqual(configured.find(x=>x.level===2).timed,false,'level 2 must not disable its configured timer');
console.log(`${configured.length} configured level times and ${rows.size} fallback times match source PASS`);
