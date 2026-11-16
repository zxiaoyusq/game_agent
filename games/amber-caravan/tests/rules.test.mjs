import test from 'node:test';
import assert from 'node:assert/strict';
import {
  FINISH, HOME_ENTRY, createGame, getTokenCell, isSafeCell,
  legalMoves, moveToken, rollDice, validateGame,
} from '../src/rules.mjs';
import { chooseMove } from '../src/ai.mjs';

const players = [
  { id: 0, name: '绿洲商队', kind: 'human' },
  { id: 2, name: '赤陶商队', kind: 'ai' },
];
const game = (mode = 'classic') => createGame({ mode, players });

/** 测试夹具只安排待测边界；所有动作均通过正式规则函数执行。 */
function movePhase(tokens, dice, mode = 'classic') {
  const state = game(mode);
  state.players[0].tokens = tokens;
  state.players[0].finished = tokens.filter((step) => step === FINISH).length;
  state.phase = 'move';
  state.dice = dice;
  return state;
}

test('两至四方配置和快局出发位置有明确校验', () => {
  assert.equal(validateGame(game()), true);
  assert.deepEqual(game('quick').players[0].tokens, [0, 0, -1, -1]);
  assert.equal(game('quick').players[0].homeUnlocked, false);
  assert.throws(() => createGame({ players: [players[0]] }), /两至四/);
  assert.throws(() => createGame({ players: [players[0], players[0]] }), /互不重复/);
  assert.throws(() => createGame({ mode: 'unknown', players }), /模式/);
  assert.throws(() => createGame({ players: [{ ...players[0], kind: 'remote' }, players[1]] }), /控制方式/);
});

test('六点才能出营，出营后额外掷骰；无棋可动自动换人', () => {
  const initial = game();
  const unchanged = structuredClone(initial);
  const skipped = rollDice(initial, 3);
  assert.equal(skipped.turn, 1);
  assert.equal(skipped.phase, 'roll');
  assert.deepEqual(initial, unchanged);
  const six = rollDice(initial, 6);
  assert.deepEqual(legalMoves(six), [0, 1, 2, 3]);
  const moved = moveToken(six, 0);
  assert.equal(moved.players[0].tokens[0], 0);
  assert.equal(moved.turn, 0);
  assert.equal(moved.phase, 'roll');
  assert.equal(moved.sixStreak, 1);
});

test('连续第三个六点罚停，不撤销前两次移动；换人后计数归零', () => {
  let state = game();
  state = moveToken(rollDice(state, 6), 0);
  state = moveToken(rollDice(state, 6), 0);
  const before = [...state.players[0].tokens];
  state = rollDice(state, 6);
  assert.equal(state.turn, 1);
  assert.equal(state.sixStreak, 0);
  assert.deepEqual(state.players[0].tokens, before);
  assert.equal(state.stats.moves, 2);
  assert.match(state.message, /连续三次/);
});

test('重复点击和非法走法无副作用，骰子范围错误明确失败', () => {
  const state = rollDice(game(), 6);
  assert.throws(() => rollDice(state, 5), /当前不能掷骰/);
  assert.equal(moveToken(state, 99), state);
  assert.equal(moveToken(state, '0'), state);
  assert.throws(() => rollDice(game(), 7), /1 至 6/);
  assert.throws(() => rollDice(game(), 1.5), /整数/);
});

test('归航路径跳过外圈末格，终点必须精确抵达', () => {
  assert.equal(HOME_ENTRY, 51);
  assert.equal(FINISH, 56);
  let state = movePhase([50, 54, 56, -1], 3);
  assert.deepEqual(legalMoves(state), [0]);
  const next = moveToken(state, 0);
  assert.equal(next.players[0].tokens[0], 53);
  assert.equal(getTokenCell(0, 53), null);
  state = movePhase([55, -1, -1, -1], 1);
  const arrived = moveToken(state, 0);
  assert.equal(arrived.players[0].finished, 1);
  assert.equal(arrived.phase, 'roll');
  assert.equal(arrived.turn, 0);
});

test('单枚敌棋被截获后回营，双方状态与奖励一致', () => {
  const state = movePhase([2, -1, -1, -1], 2);
  state.players[1].tokens[0] = 30; // 阵营 2 的进度 30 对应全局格 4。
  const before = structuredClone(state);
  const next = moveToken(state, 0);
  assert.equal(next.players[1].tokens[0], -1);
  assert.equal(next.players[0].captures, 1);
  assert.equal(next.stats.captures, 1);
  assert.equal(next.turn, 0);
  assert.equal(next.phase, 'roll');
  assert.deepEqual(next.lastAction.captured, [{ playerId: 2, tokenIndex: 0 }]);
  assert.deepEqual(state, before);
});

test('安全驿站可共存，双子保护阻止落点但不阻挡跨越', () => {
  const safe = movePhase([6, -1, -1, -1], 2);
  safe.players[1].tokens[0] = 34;
  const protectedResult = moveToken(safe, 0);
  assert.equal(protectedResult.players[1].tokens[0], 34);
  assert.equal(protectedResult.players[0].captures, 0);
  assert.equal(protectedResult.turn, 1);
  const stack = movePhase([2, 1, -1, -1], 2);
  stack.players[1].tokens = [30, 30, -1, -1];
  assert.deepEqual(legalMoves(stack), [1]);
  stack.dice = 3;
  assert.deepEqual(legalMoves(stack), [0]);
  assert.equal(isSafeCell(null), false);
});

test('经典需要四枚归航；快局解锁后一枚即获胜', () => {
  const classic = movePhase([55, 56, 56, 56], 1);
  const won = moveToken(classic, 0);
  assert.equal(won.phase, 'won');
  assert.equal(won.winner, 0);
  assert.equal(validateGame(won), true);
  assert.equal(moveToken(won, 0), won);
  assert.throws(() => rollDice(won, 1), /当前不能掷骰/);
  const quick = movePhase([55, 0, -1, -1], 1, 'quick');
  quick.players[0].captures = 1;
  quick.players[0].homeUnlocked = true;
  assert.equal(moveToken(quick, 0).phase, 'won');
});

test('快局未解锁时绕外圈，不因归航门锁而产生死局', () => {
  let state = movePhase([50, 0, -1, -1], 1, 'quick');
  state = moveToken(state, 0);
  assert.equal(state.players[0].tokens[0], 51);
  assert.equal(state.players[0].outerLast[0], true);
  assert.equal(getTokenCell(0, 51, true), 51);
  assert.equal(getTokenCell(0, 51, false), null);
  assert.equal(validateGame(state), true);
  state.turn = 0;
  state = moveToken(rollDice(state, 2), 0);
  assert.equal(state.players[0].tokens[0], 1);
  assert.equal(state.players[0].outerLast[0], false);
  assert.equal(state.players[0].homeUnlocked, false);
});

test('吃子解锁时外圈末格的另一枚商队不瞬移，下一步正常绕圈', () => {
  const state = movePhase([2, 51, 50, -1], 2, 'quick');
  state.players[0].outerLast[1] = true;
  state.players[1].tokens[0] = 30;
  let next = moveToken(state, 0);
  assert.equal(next.players[0].homeUnlocked, true);
  assert.equal(next.players[0].outerLast[1], true);
  assert.equal(validateGame(next), true);
  const entered = moveToken(rollDice(next, 1), 2);
  assert.equal(entered.players[0].tokens[2], 51);
  assert.equal(entered.players[0].outerLast[2], false);
  next = moveToken(rollDice(next, 2), 1);
  assert.equal(next.players[0].tokens[1], 1);
  assert.equal(next.players[0].outerLast[1], false);
});

test('四个阵营的外圈坐标转换保持相同规则', () => {
  for (let id = 0; id < 4; id += 1) {
    assert.equal(getTokenCell(id, 0), id * 13);
    assert.equal(getTokenCell(id, 50), (id * 13 + 50) % 52);
    assert.equal(getTokenCell(id, -1), null);
    assert.equal(getTokenCell(id, 56), null);
  }
});

test('AI 优先获胜、截获解锁，且不改变输入局面', () => {
  const state = movePhase([2, 0, -1, -1], 2, 'quick');
  state.players[1].tokens[0] = 30;
  const before = structuredClone(state);
  assert.equal(chooseMove(state), 0);
  assert.deepEqual(state, before);
  const end = movePhase([55, 0, -1, -1], 1, 'quick');
  end.players[0].captures = 1;
  end.players[0].homeUnlocked = true;
  assert.equal(chooseMove(end), 0);
  assert.equal(chooseMove(game()), null);
});

test('存档拒绝结构损坏、越界棋子、伪胜利和锁门路径歧义', () => {
  const mutations = [
    (state) => { state.players[0] = null; },
    (state) => { state.turn = 8; },
    (state) => { state.players[0].tokens[0] = 57; },
    (state) => { state.players[0].tokens[0] = 55.5; },
    (state) => { state.players[0].outerLast = []; },
    (state) => { state.players[0].outerLast[0] = true; },
    (state) => { state.players[0].finished = 4; },
    (state) => { state.winner = 0; state.phase = 'won'; },
    (state) => { state.dice = 0; },
    (state) => { state.stats.rolls = -1; },
    (state) => { state.players[0].homeUnlocked = false; },
  ];
  for (const mutate of mutations) {
    const state = game();
    mutate(state);
    assert.equal(validateGame(state), false);
  }
  const locked = game('quick');
  locked.players[0].tokens[0] = 51;
  assert.equal(validateGame(locked), false);
});

test('48 局真实规则自博弈均能从新局走到获胜，覆盖两种模式与两至四人', () => {
  const results = [];
  for (const mode of ['classic', 'quick']) {
    for (const count of [2, 3, 4]) {
      for (let seed = 1; seed <= 8; seed += 1) {
        let random = seed * 1831565813;
        const ids = count === 2 ? [0, 2] : count === 3 ? [0, 1, 2] : [0, 1, 2, 3];
        let state = createGame({ mode, players: ids.map((id) => ({ id, name: `商队${id}`, kind: 'ai' })) });
        let actions = 0;
        while (state.phase !== 'won' && actions < 12000) {
          if (state.phase === 'roll') {
            random ^= random << 13;
            random ^= random >>> 17;
            random ^= random << 5;
            state = rollDice(state, (random >>> 0) % 6 + 1);
          } else {
            const choice = chooseMove(state);
            assert.ok(legalMoves(state).includes(choice), `无合法 AI 走法：${mode}/${count}/${seed}`);
            state = moveToken(state, choice);
          }
          actions += 1;
          assert.equal(validateGame(state), true, `非法状态：${mode}/${count}/${seed}/${actions}`);
        }
        assert.equal(state.phase, 'won', `对局未结束：${mode}/${count}/${seed}`);
        assert.ok(state.history.length <= 8);
        results.push({ mode, count, seed, actions, rolls: state.stats.rolls, captures: state.stats.captures, winner: state.winner });
      }
    }
  }
  assert.equal(results.length, 48);
  assert.ok(results.every((result) => result.rolls > 0));
});
