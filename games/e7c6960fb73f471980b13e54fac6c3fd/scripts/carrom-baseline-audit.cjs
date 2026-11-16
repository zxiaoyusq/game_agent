const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const source = fs.readFileSync('reference-inputs/carrom-baseline-game.js', 'utf8');
const hash = crypto.createHash('sha256').update(Buffer.from(source)).digest('hex');
assert.equal(hash, '2a036140fcf41e307b604373d307ff4014d061eef4bee5fb9504b90424b3460e');
const lines = source.split('\n');
const segment = (first, last) => lines.slice(first - 1, last).join('\n');
const decoder = source.slice(0, source.indexOf('var src =')) + segment(12139, 12149) + segment(12484, 13516) + '\nvar _0x157421 = _0x3797;';
const results = [];
function createContext(turn = true, foul = false) {
  const events = [];
  const tweens = [];
  const timers = [];
  const parent = { removeChild() {} };
  const context = { console, Math: Object.create(Math), events, tweens, timers,
    _0x209883: turn, _0x530863: foul, _0x5d148e: 0,
    _0x3e4566: [], _0x2a9c75: [], _0x3231b3: [], _0x31089b: [],
    _0x4268e2: false, _0x5ebd99: false, _0x3fddb3: true,
    _0x4d3bf1: 8, _0x41f634: 8, _0x1a373b: 0, _0x55e693: true,
    _0x539ff8: {x: 0, y: 0}, _0x25b85f: {x: 100, y: 0},
    _0x337f1a: {}, _0x4efd2a: {x: 50, y: 50}, _0x24c0ca: {x: 0, y: 0},
    _0x3e9ee1: 0, _0x55e1a0: 162, _0x187453: 483, _0x429ae3: 421,
    _0x133600: 21.76, _0x3ce1ab: 15,
    _0x2fc10d: [{x:0,y:0},{x:200,y:0},{x:0,y:200},{x:200,y:200}],
    _0x28fba8: {play() {}},
    PIXI: {utils: {TextureCache: {check_filled: {}}}},
    GameSnacks: {score: {update(value) { events.push(['score', value]); }}},
    Tweener: {addTween(target, props, options) { tweens.push({target, props, options}); }, remove() {}},
    _0x54f71d() {}, _0x89ccbb() {}, _0x56abf7() {return false;},
    _0x338c29(callback, delay) { timers.push({callback, delay}); },
    _0x47e567(win) {events.push(['result', win]);},
    _0x52e61d() {events.push(['queenReturn']);},
    _0x5e7a5f() {events.push(['turn', 'player']);},
    _0x50a0ff() {events.push(['turn', 'opponent']);},
    _0x1f3ae5() {},
    _0xcf7ce5: {addChild(value) {value.parent = parent;}, addChildZ(value) {value.parent = parent;}},
    _0x54e9a5: function(type) {this._type = type; this.removeFromWorld = () => {};},
    makeDisc(type, pocket) {return {type, _type: type === 'player' ? 1 : 2, ...context._0x2fc10d[pocket], parent, update() {}, removeFromWorld() {}};}
  };
  context.Math.random = () => 0.5;
  vm.createContext(context);
  vm.runInContext(decoder, context, {timeout: 1000});
  vm.runInContext(segment(5770, 5783) + segment(5846, 5853) + segment(5617, 5623) + segment(4652, 4659) + segment(3796, 3843) + segment(3052, 3107) + segment(3159, 3437) + '\nfunction scanColors() {var _0xcaac96 = _0x157421;\n' + segment(5160, 5490) + '\n}', context);
  return context;
}
function finish(context, early = false) {
  context._0xbdafb3();
  const before = [context._0x4d3bf1, context._0x41f634];
  if (early) context.timers.splice(0).forEach(item => item.callback());
  const pending = context.tweens.splice(0);
  for (const item of pending) {Object.assign(item.target, item.props); if (item.options.onComplete) item.options.onComplete(item.target);}
  if (!early) context.timers.splice(0).forEach(item => item.callback());
  return {before, scores: [context._0x4d3bf1, context._0x41f634], events: context.events};
}
for (const turn of [true, false]) {
  for (let playerPocket = 0; playerPocket < 4; playerPocket++) {
    for (let opponentPocket = 0; opponentPocket < 4; opponentPocket++) {
      const c = createContext(turn);
      c._0x3e4566.push(c.makeDisc('player', playerPocket));
      c._0x2a9c75.push(c.makeDisc('oponent', opponentPocket));
      c.scanColors();
      const queue = c._0x31089b.map(disc => disc.type);
      assert.deepEqual(queue, ['player']);
      const outcome = finish(c);
      assert.deepEqual(outcome.scores, [9, 8]);
      assert.deepEqual(outcome.events.find(event => event[0] === 'result'), ['result', true]);
      results.push({case: 'same-step', turn, playerPocket, opponentPocket, queue, ...outcome});
    }
  }
}
for (const order of [['player', 'oponent'], ['oponent', 'player']]) {
  const c = createContext();
  const p = c.makeDisc('player', 0);
  const o = c.makeDisc('oponent', 1);
  p.x = o.x = 1000; p.y = o.y = 1000;
  c._0x3e4566.push(p); c._0x2a9c75.push(o);
  for (const type of order) {Object.assign(type === 'player' ? p : o, c._0x2fc10d[type === 'player' ? 0 : 1]); c.scanColors();}
  const queue = c._0x31089b.map(disc => disc.type);
  const outcome = finish(c);
  assert.equal(outcome.events.find(event => event[0] === 'result')[1], order[0] === 'player');
  results.push({case: 'different-steps', order, queue, ...outcome});
}
for (const turn of [true, false]) {
  for (const ownPocketed of [false, true]) {
    const c = createContext(turn, true);
    const type = turn ? 'player' : 'oponent';
    if (ownPocketed) {
      c._0x31089b.push(c.makeDisc(type, 0));
      c._0x5ebd99 = true;
    }
    const outcome = finish(c);
    assert.equal(outcome.scores[turn ? 0 : 1], ownPocketed ? 8 : 7);
    assert.equal(outcome.events.some(event => event[0] === 'result'), false);
    results.push({case: 'striker-foul', turn, ownPocketed, ...outcome});
  }
}
const empty = createContext();
let emptyError;
try {empty._0x3d12d7();} catch (error) {emptyError = {name: error.name, message: error.message};}
assert.equal(emptyError.name, 'TypeError');
results.push({case: 'empty-target', error: emptyError});
for (const early of [false, true]) {
  const c = createContext();
  c._0x31089b.push(c.makeDisc('player', 0));
  const outcome = finish(c, early);
  assert.equal(outcome.events.some(event => event[0] === 'result'), !early);
  results.push({case: 'callback-order', settlementBeforeScore: early, ...outcome});
}
fs.mkdirSync('evidence', {recursive: true});
fs.writeFileSync('evidence/carrom-baseline-audit.json', JSON.stringify({baselineSha256: hash, scope: '原函数片段隔离执行，动画、物理和界面使用替身，未启动完整游戏', cases: results.length, results}, null, 2));
console.log('隔离验证通过，共 ' + results.length + ' 个用例。证据写入 evidence/carrom-baseline-audit.json');
