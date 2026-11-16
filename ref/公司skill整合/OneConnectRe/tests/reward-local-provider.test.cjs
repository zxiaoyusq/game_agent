const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const jobs = [];
const window = {};
vm.runInNewContext(fs.readFileSync('examples/reward-local-provider.js', 'utf8'), {
  window, setTimeout: fn => jobs.push(fn), Number, Error
});
const make = window.oneConnectLocalRewardProvider.create;
function run(mode) {
  const calls = [];
  const provider = make({mode, delayMs: 0});
  const callbacks = Object.fromEntries(['shown', 'earned', 'closed', 'cancelled', 'error'].map(k => [k, p => calls.push([k, p])]));
  provider.show(callbacks, 7);
  assert.equal(calls.length, 0, 'simulation is asynchronous');
  while (jobs.length) jobs.shift()();
  return calls;
}
let result = run('reward');
assert.deepEqual(result.map(x => x[0]), ['shown', 'earned', 'closed']);
assert.equal(result[1][1].verified, true);
assert.equal(result[1][1].simulated, true);
assert.deepEqual(run('closed').map(x => x[0]), ['shown', 'closed']);
assert.deepEqual(run('cancelled').map(x => x[0]), ['shown', 'cancelled']);
assert.deepEqual(run('error').map(x => x[0]), ['error']);
assert.throws(() => make({mode: 'unknown'}));
assert.throws(() => make({mode: 'reward', delayMs: -1}));
// Exercise the real lifecycle contract, without loading the helper in the game.
(async () => {
  const context = {window: {}, setTimeout, clearTimeout, Promise, Set, Number, Error};
  vm.runInNewContext(fs.readFileSync('examples/reward-local-provider.js', 'utf8'), context);
  vm.runInNewContext(fs.readFileSync('tools/reward_lifecycle_candidate.js', 'utf8'), context);
  let stock = 0;
  const life = context.window.oneConnectRewardLifecycle.create({loadTimeoutMs: 1000, grant: () => { stock += 2; return true; }});
  for (const [mode, status] of [['reward', 'rewarded'], ['closed', 'closed'], ['cancelled', 'cancelled'], ['error', 'error']]) {
    life.setProvider(context.window.oneConnectLocalRewardProvider.create({mode, delayMs: 0}));
    assert.equal((await life.request(mode)).status, status);
  }
  assert.equal(stock, 2, 'only the rewarded case grants two');
  console.log('explicit local reward provider scenarios PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
