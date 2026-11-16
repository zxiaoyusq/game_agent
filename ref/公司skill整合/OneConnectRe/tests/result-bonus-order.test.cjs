const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
function setup() {
  let progress = 3, now = 0, listener, original = 0, shown = 0, jobs = [];
  const actions = Object.create({callback() { original++; }}), cr = {plugins_: {Famobi: function () {}}};
  cr.plugins_.Famobi.prototype.acts = actions;
  const r = {running_layout: {name: 'game'}, all_global_vars: [{name: 'level', data: 3}], types: {t5: {instances: []}}};
  const document = {hidden: false, addEventListener() {}};
  const window = {cr, cr_getC2Runtime: () => r, oneConnectProgress: {get: () => progress},
    oneConnectResultPanelCandidate: {create: () => ({show() { shown++; }, hide() {}})},
    addEventListener(name, fn) { if (name === 'oneconnect:event') listener = fn; },
    setTimeout(fn) { jobs.push(fn); }};
  vm.runInNewContext(fs.readFileSync(process.argv[2] || 'tools/result_bridge_candidate.js', 'utf8'),
    {window, document, cr, console, Number, Array, Object, Math, Date: {now: () => now}});
  window.oneConnectResultBridgeCandidate.install();
  return {actions, r, document, get original() { return original; }, get shown() { return shown; },
    setProgress: n => { progress = n; }, advance: n => { now += n; }, run: () => { assert(jobs.length); jobs.shift()(); },
    send: type => listener({detail: {type}})};
}
const early = setup(); early.actions.callback('levelSuccess');
assert.equal(early.original, 0, 'early callback must not bypass candidate panel');
early.setProgress(4); early.run(); assert.equal(early.shown, 1); assert.equal(early.original, 0);
const timeout = setup(); timeout.actions.callback('levelSuccess'); timeout.advance(3000); timeout.run();
assert.equal(timeout.original, 1, 'missing bonus must resume native flow'); assert.equal(timeout.shown, 0);
const cancel = setup(); cancel.actions.callback('levelSuccess'); cancel.send('game.round_ready'); cancel.run();
assert.equal(cancel.original, 0, 'old callback must not affect a new round'); assert.equal(cancel.shown, 0);
const duplicate = setup(); duplicate.actions.callback('levelSuccess'); duplicate.setProgress(4); duplicate.actions.callback('levelSuccess');
duplicate.run(); assert.equal(duplicate.shown, 1, 'duplicate callback cannot open two panels');
const hidden = setup(); hidden.actions.callback('levelSuccess'); hidden.document.hidden = true; hidden.advance(4000); hidden.run();
assert.equal(hidden.original, 0, 'background time cannot consume the fallback'); hidden.document.hidden = false;
hidden.run(); hidden.advance(2600); hidden.run(); assert.equal(hidden.original, 1);
const board = setup(); board.actions.callback('levelSuccess'); board.r.types.t5.instances.push({}); board.run();
assert.equal(board.original, 0, 'rebuilt board cancels the stale callback');
const failure = setup(); failure.actions.callback('levelSuccess'); failure.actions.callback('levelFail'); failure.run();
assert.equal(failure.shown, 1, 'failure opens immediately'); assert.equal(failure.original, 0, 'stale success was cancelled');
const unrelated = setup(); unrelated.actions.callback('other'); assert.equal(unrelated.original, 1);
console.log('early success waits for bonus or safely falls back PASS');
