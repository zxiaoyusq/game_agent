const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');

class Element {
  constructor() { this.style = {}; this.children = []; this.hidden = false; this.textContent = ''; this.listeners = {}; }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { this.children.push(...children); }
  setAttribute() {}
  addEventListener(name, fn) { this.listeners[name] = fn; }
}

(async () => {
  let event, resolveFirst, resolveSecond, busy = false;
  const first = new Promise(resolve => { resolveFirst = resolve; });
  const second = new Promise(resolve => { resolveSecond = resolve; });
  let calls = 0;
  const lifecycle = {
    state: () => ({ busy }),
    request: () => { busy = true; return ++calls === 1 ? first : second; },
    cancel: () => { busy = false; resolveFirst({ status: 'cancelled' }); },
    setProvider() {},
  };
  const body = new Element(), head = new Element();
  const runtime = { running_layout: { name: 'game' }, all_global_vars: [{ name: 'level', data: 1 }] };
  const window = { cr_getC2Runtime: () => runtime, oneConnectRewardLifecycle: { create: () => lifecycle }, addEventListener: (_, fn) => { event = fn; } };
  const cr = { plugins_: { Touch: function() {} }, action: function() {} };
  cr.plugins_.Touch.prototype.cnds = { OnTouchObject() { return false; } };
  let actions=0;cr.action.prototype.run_system = function() { actions++; };
  const document = { body, head, createElement: () => new Element(), createTextNode: value => ({ textContent: value }) };
  vm.runInNewContext(fs.readFileSync('tools/tool_reward_candidate.js', 'utf8'), { window, document, cr, Date, Number, Promise, Error });
  const candidate = window.oneConnectToolRewardCandidate;
  candidate.install();
  candidate.open('hint');
  const root = body.children[0], panel = root.children[0], watch = panel.children[2], status = panel.children[3];
  cr.action.prototype.run_system.call({sid:367702696840255});assert.equal(actions,0,'timer action is blocked while dialog is visible');
  cr.action.prototype.run_system.call({sid:1});assert.equal(actions,1,'unrelated actions continue');
  for (const name of ['mousedown','mouseup','pointerdown','pointerup','touchstart','touchend','click']) {
    let stopped = false; root.listeners[name]({stopPropagation(){stopped = true;}});
    assert.equal(stopped, true, `${name} must not reach the board`);
  }
  watch.onclick();
  event({ detail: { type: 'game.board_configured' } });
  candidate.open('shuffle');
  watch.onclick();
  await Promise.resolve();
  assert.equal(watch.disabled, true, 'cancelled previous request must not unlock a new request');
  assert.equal(status.textContent, '', 'cancelled previous request must not update new dialog');
  assert.equal(root.hidden, false);
  busy = false;
  resolveSecond({ status: 'rewarded' });
  await Promise.resolve();
  assert.equal(root.hidden, true);
  cr.action.prototype.run_system.call({sid:367702696840255});assert.equal(actions,2,'timer action resumes after dialog closes');
  console.log('reward dialog ignores previous request after reopening PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
