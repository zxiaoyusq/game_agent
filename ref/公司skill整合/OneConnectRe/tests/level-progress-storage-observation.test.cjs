const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
const events = [], runtime = {running_layout: {name: 'game'}, all_global_vars: [{name: 'level', data: 1}],
  types: {t5: {instances: []}, t32: {instances: [{instance_vars: [0, 0, 0, 72]}]}}};
const window = {cr_getC2Runtime: () => runtime, localStorage: {getItem: () => null, setItem: () => { throw Error('quota'); }},
  oneConnectHost: {emit: (name, detail) => events.push({name, detail})}};
vm.runInNewContext(fs.readFileSync(process.argv[2] || 'game/level-progress.js', 'utf8'), {window, Number, Array});
window.oneConnectProgress.recordCleared();
assert.equal(window.oneConnectProgress.get(), 2, 'memory fallback remains usable');
assert.equal(events.length, 1);
assert.equal(events[0].name, 'candidate.progress_save_deferred');
assert.equal(events[0].detail.level, 2);
console.log('progress write failure is observable without losing in-memory progress PASS');
