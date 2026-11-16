const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function run(progress) {
  let shown;
  const actions = Object.create({ callback() {} });
  const cr = { plugins_: { Famobi: function Famobi() {} } };
  cr.plugins_.Famobi.prototype.acts = actions;
  const runtime = { running_layout: { name: 'game' }, all_global_vars: [{ name: 'level', data: 3 }, { name: 'score', data: 500 }], types: { t5: { instances: [] } } };
  const window = {
    cr,
    cr_getC2Runtime: () => runtime,
    oneConnectProgress: { get: () => 4 },
    oneConnectFlyStarScoreCandidate: { rating: () => ({ count: 24, stars: 2 }) },
    oneConnectStarProgressCandidate: progress,
    oneConnectResultPanelCandidate: { create: () => ({ show(value) { shown = value; }, hide() {} }) },
    localStorage: {},
  };
  vm.runInNewContext(fs.readFileSync('tools/result_bridge_candidate.js', 'utf8'), { window, cr, document: {}, console: { warn() {} }, Number, Date });
  window.oneConnectResultBridgeCandidate.install();
  actions.callback('levelSuccess');
  return shown.stars;
}

assert.equal(run({ record() { throw new Error('storage blocked'); } }), 2, 'a storage error must not erase the current result');
assert.equal(run(null), 2, 'unavailable persistence must not erase the current result');
console.log('result stars remain visible when persistence is unavailable PASS');
