const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
let now = 0, jobs = [], shown = 0, calls = 0;
const actions = Object.create({callback() { calls++; }}), cr = {plugins_: {Famobi: function () {}}};
cr.plugins_.Famobi.prototype.acts = actions;
const runtime = {running_layout: {name: 'game'}, all_global_vars: [{name: 'level', data: 3}],
  types: {t5: {instances: []}, t32: {instances: [{instance_vars: [0, 0, 0, 72]}]}}};
const dir = process.argv[2], key = dir ? 'oneconnect.currentLevel.candidate.v1' : 'oneconnect.currentLevel.v1';
const values = new Map([[key, '3']]);
const window = {cr, cr_getC2Runtime: () => runtime, localStorage: {getItem: k => values.get(k) ?? null, setItem: (k, v) => values.set(k, v)},
  oneConnectResultPanelCandidate: {create: () => ({show() { shown++; }, hide() {}})},
  addEventListener() {}, setTimeout: f => jobs.push(f)};
const context = {window, cr, document: {hidden: false, addEventListener() {}}, Date: {now: () => now}, console, Number, Array, Object, Math};
for (const f of dir ? [dir + '/level-progress.js', dir + '/result-bridge-candidate.js'] : ['game/level-progress.js', 'tools/result_bridge_candidate.js'])
  vm.runInNewContext(fs.readFileSync(f, 'utf8'), context);
window.oneConnectResultBridgeCandidate.install(); actions.callback('levelSuccess');
now = 3000; jobs.shift()();
assert.equal(window.oneConnectProgress.get(), 4, 'a verified cleared board advances the frontier before fallback');
assert.equal(values.get(key), '4');
assert.equal(shown, 1, 'verified timeout can show the result'); assert.equal(calls, 0);
// An incomplete count must never be promoted to a verified win by the fallback.
const invalidActions = Object.create({callback() { calls++; }}), invalidCr = {plugins_: {Famobi: function () {}}};
invalidCr.plugins_.Famobi.prototype.acts = invalidActions;
runtime.types.t32.instances[0].instance_vars[3] = 71; values.set(key, '3'); jobs = []; now = 0;
const invalidWindow = {...window, cr: invalidCr};
const invalidContext = {...context, window: invalidWindow, cr: invalidCr};
for (const f of dir ? [dir + '/level-progress.js', dir + '/result-bridge-candidate.js'] : ['game/level-progress.js', 'tools/result_bridge_candidate.js'])
  vm.runInNewContext(fs.readFileSync(f, 'utf8'), invalidContext);
invalidWindow.oneConnectResultBridgeCandidate.install(); invalidActions.callback('levelSuccess');
now = 3000; jobs.shift()();
assert.equal(invalidWindow.oneConnectProgress.get(), 3, 'incomplete board count must not advance');
assert.equal(calls, 1, 'unverified timeout returns to native flow');
console.log('bonus timeout preserves cleared-level progress PASS');
