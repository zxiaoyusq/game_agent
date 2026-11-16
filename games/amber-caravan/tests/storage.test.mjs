import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, legalMoves, moveToken, rollDice } from '../src/rules.mjs';
import { chooseMove } from '../src/ai.mjs';
import { loadSave, saveGame, SAVE_KEY } from '../src/storage.mjs';

const players = [
  { id: 0, name: '翡翠商队', kind: 'human' },
  { id: 2, name: '琥珀商队', kind: 'ai' },
];
const settings = { sound: false, fast: true };

/** 内存存储只替代浏览器 I/O；局面与后续动作仍调用生产规则。 */
function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
  };
}

test('首次打开没有存档，能够使用默认偏好开始', () => {
  assert.deepEqual(loadSave(memoryStorage()), { game: null, settings: { sound: true, fast: false } });
});

test('选子阶段恢复保留骰子、连六和合法走法，重复刷新不会多行动', () => {
  const storage = memoryStorage();
  const original = rollDice(createGame({ players }), 6);
  assert.equal(saveGame(original, settings, storage), true);
  const first = loadSave(storage);
  const second = loadSave(storage);
  assert.deepEqual(first, { game: original, settings });
  assert.deepEqual(second, first);
  assert.deepEqual(legalMoves(first.game), [0, 1, 2, 3]);
  assert.deepEqual(moveToken(first.game, 2), moveToken(original, 2));
});

test('AI 回合恢复后沿同一局面继续，读档不替 AI 执行任何动作', () => {
  const storage = memoryStorage();
  let original = rollDice(createGame({ players }), 2);
  assert.equal(original.players[original.turn].kind, 'ai');
  original = rollDice(original, 6);
  saveGame(original, settings, storage);
  const restored = loadSave(storage).game;
  assert.equal(restored.stats.rolls, 2);
  assert.equal(restored.stats.moves, 0);
  assert.equal(chooseMove(restored), chooseMove(original));
  assert.deepEqual(moveToken(restored, chooseMove(restored)), moveToken(original, chooseMove(original)));
});

test('快局锁门外圈末格与解锁后保留的外圈末格可精确恢复', () => {
  const storage = memoryStorage();
  for (const unlocked of [false, true]) {
    const original = createGame({ mode: 'quick', players });
    original.players[0].tokens = [51, 0, -1, -1];
    original.players[0].outerLast[0] = true;
    original.players[0].homeUnlocked = unlocked;
    original.players[0].captures = unlocked ? 1 : 0;
    original.stats.captures = unlocked ? 1 : 0;
    assert.equal(saveGame(original, settings, storage), true);
    const restored = loadSave(storage).game;
    assert.deepEqual(restored, original);
    const next = moveToken(rollDice(restored, 2), 0);
    assert.equal(next.players[0].tokens[0], 1);
    assert.equal(next.players[0].outerLast[0], false);
    assert.equal(next.players[0].finished, 0);
  }
});

test('正常完成一局后的结算、计数和赢家可完整恢复', () => {
  const storage = memoryStorage();
  let state = createGame({ mode: 'quick', players });
  let seed = 49271;
  let actions = 0;
  while (state.phase !== 'won' && actions < 10000) {
    if (state.phase === 'roll') {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      state = rollDice(state, seed % 6 + 1);
    } else state = moveToken(state, chooseMove(state));
    actions += 1;
  }
  assert.equal(state.phase, 'won');
  assert.equal(saveGame(state, settings, storage), true);
  assert.deepEqual(loadSave(storage), { game: state, settings });
});

test('损坏 JSON、版本和不可行局面均明确告警，不产生伪续局', () => {
  const storage = memoryStorage();
  const invalidStates = [
    { ...createGame({ players }), phase: 'move', dice: 1 },
    { ...createGame({ players }), sixStreak: 2, dice: 1 },
    { ...rollDice(createGame({ players }), 6), sixStreak: 0 },
  ];
  const rawValues = [
    '{损坏', 'null', '[]',
    JSON.stringify({ version: 8, game: null }),
    JSON.stringify({ version: 1, game: false }),
    JSON.stringify({ version: 1 }),
    ...invalidStates.map((game) => JSON.stringify({ version: 1, game, settings })),
  ];
  for (const raw of rawValues) {
    storage.setItem(SAVE_KEY, raw);
    const loaded = loadSave(storage);
    assert.equal(loaded.game, null);
    assert.match(loaded.warning, /无法读取/);
    assert.deepEqual(loaded.settings, { sound: true, fast: false });
  }
});

test('偏好独立于游戏保存，偏好字段损坏使用安全默认值', () => {
  const storage = memoryStorage();
  assert.equal(saveGame(null, settings, storage), true);
  assert.deepEqual(loadSave(storage), { game: null, settings });
  storage.setItem(SAVE_KEY, JSON.stringify({ version: 1, game: null, settings: { sound: 'false', fast: 'true' } }));
  assert.deepEqual(loadSave(storage).settings, { sound: true, fast: false });
});

test('存储写满或待保存局面损坏时报告失败，并保留上一份可续局记录', () => {
  const storage = memoryStorage();
  const original = createGame({ players });
  saveGame(original, settings, storage);
  const previous = storage.getItem(SAVE_KEY);
  assert.equal(saveGame({ ...original, turn: 99 }, settings, storage), false);
  assert.equal(storage.getItem(SAVE_KEY), previous);
  const full = { ...storage, setItem() { throw new DOMException('配额不足', 'QuotaExceededError'); } };
  assert.equal(saveGame(rollDice(original, 6), settings, full), false);
  assert.equal(storage.getItem(SAVE_KEY), previous);
  assert.deepEqual(loadSave(storage).game, original);
});

test('禁用 localStorage 属性本身也不会让启动崩溃，写入失败可被界面感知', () => {
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  try {
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      get() { throw new DOMException('禁止使用存储', 'SecurityError'); },
    });
    const loaded = loadSave();
    assert.equal(loaded.game, null);
    assert.match(loaded.warning, /无法读取/);
    assert.equal(saveGame(createGame({ players }), settings), false);
  } finally {
    if (previous) Object.defineProperty(globalThis, 'localStorage', previous);
    else delete globalThis.localStorage;
  }
});
