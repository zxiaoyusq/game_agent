const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
class Element {
  constructor() { this.children = []; this.hidden = false; this.style = {}; }
  appendChild(value) { this.children.push(value); return value; }
  append(...values) { this.children.push(...values); }
  setAttribute() {} addEventListener() {}
}
(async () => {
  const tip = {name: 'tip', data: 0}, shuffle = {name: 'shuffle', data: 0}, level = {name: 'level', data: 3};
  let hammer = 0, theme = 0;
  const runtime = {running_layout: {name: 'game'}, all_global_vars: [tip, shuffle, level], types: {t25: {instances: []}}};
  const cr = {plugins_: {Touch: function () {}}, action: function () {}};
  cr.plugins_.Touch.prototype.cnds = {OnTouchObject() { return false; }}; cr.action.prototype.run_system = function () {};
  const window = {cr, cr_getC2Runtime: () => runtime, addEventListener() {},
    oneConnectHammer: {credit(n) { hammer += n; return true; }},
    oneConnectThemeInventoryCandidate: {credit(n) { theme += n; return true; }}};
  const document = {body: new Element(), head: new Element(), createElement: () => new Element(), createTextNode: text => ({textContent: text})};
  const context = {window, document, cr, console, Date, Number, Promise, Error, Set, setTimeout, clearTimeout};
  const dir = process.argv[2];
  const files = dir ? ['examples/reward-local-provider.js', path.join(dir, 'reward-lifecycle.js'), path.join(dir, 'tool-reward-candidate.js')]
                    : ['examples/reward-local-provider.js', 'tools/reward_lifecycle_candidate.js', 'tools/tool_reward_candidate.js'];
  for (const file of files)
    vm.runInNewContext(fs.readFileSync(file, 'utf8'), context);
  const reward = window.oneConnectToolRewardCandidate;
  reward.install();
  const root = document.body.children[0], watch = root.children[0].children[2];
  for (const kind of ['hint', 'shuffle', 'hammer', 'theme']) {
    reward.setProvider(window.oneConnectLocalRewardProvider.create({mode: 'reward', delayMs: 0}));
    assert.equal(reward.open(kind), true);
    watch.onclick();
    await new Promise(resolve => setTimeout(resolve, 10));
    assert.equal(root.hidden, true);
  }
  assert.deepEqual([tip.data, shuffle.data, hammer, theme], [2, 2, 2, 2]);
  for (const mode of ['closed', 'cancelled', 'error']) {
    reward.setProvider(window.oneConnectLocalRewardProvider.create({mode, delayMs: 0}));
    assert.equal(reward.open('hint'), true); watch.onclick();
    await new Promise(resolve => setTimeout(resolve, 10));
    assert.equal(tip.data, 2, mode + ' must not grant');
    root.children[0].children[4].onclick();
  }
  console.log('local provider through four-tool reward entry PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
