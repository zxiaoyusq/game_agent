import test from 'node:test';
import assert from 'node:assert/strict';
import { emptyBoard, createGame, drawBatch, canPlace, isGameOver, place } from './rules.mjs';

function fixture(pending = ['dot']) {
  return { board: emptyBoard(), pending, seed: 7, score: 0, status: 'playing' };
}

test('越界、重叠和无效槽位拒绝，输入保持不变', () => {
  const state = fixture(['square']);
  state.board[0][0] = 1;
  const before = structuredClone(state);
  for (const [slot, x, y] of [[0, 5, 5], [0, -1, 0], [0, 0, 0], [0, 0.5, 1], [9, 1, 1]]) {
    const result = place(state, slot, x, y);
    assert.equal(result.ok, false);
    assert.equal(result.state, state);
    assert.deepEqual(state, before);
  }
});

test('合法放置只消费选定形状，增加占格分且不修改输入', () => {
  const state = fixture(['bar2', 'dot']);
  const before = structuredClone(state);
  const result = place(state, 0, 4, 5);
  const expected = emptyBoard();
  expected[5][4] = expected[5][5] = 1;
  assert.equal(result.ok, true);
  assert.deepEqual(result.state.board, expected);
  assert.deepEqual(result.state.pending, ['dot']);
  assert.equal(result.state.seed, 7);
  assert.equal(result.state.score, 2);
  assert.equal(result.state.status, 'playing');
  assert.equal(result.clearedCount, 0);
  assert.deepEqual(state, before);
});

test('同时满行满列统一清除，交叉格只计一次，清除后判断终局', () => {
  const state = fixture(['dot', 'square']);
  for (let i = 1; i < 6; i++) { state.board[0][i] = 1; state.board[i][0] = 1; }
  const before = structuredClone(state);
  const result = place(state, 0, 0, 0);
  assert.equal(result.ok, true);
  assert.deepEqual(result.rows, [0]);
  assert.deepEqual(result.cols, [0]);
  assert.equal(result.clearedCount, 11);
  assert.equal(result.scoreDelta, 111);
  assert.equal(result.state.score, 111);
  assert.deepEqual(result.state.board, emptyBoard());
  assert.deepEqual(result.state.pending, ['square']);
  assert.equal(result.state.status, 'playing');
  assert.deepEqual(state, before);
});

test('终局按所有待放形状判断，合法放置后可以自然失败', () => {
  const state = fixture(['dot', 'square']);
  state.board = Array.from({ length: 6 }, (_, y) => Array.from({ length: 6 }, (_, x) => (x + y) % 2));
  assert.equal(isGameOver(state.board, ['square']), true);
  assert.equal(isGameOver(state.board, ['square', 'dot']), false);
  const result = place(state, 0, 0, 0);
  assert.equal(result.ok, true);
  assert.equal(result.clearedCount, 0);
  assert.equal(result.state.status, 'over');
  assert.deepEqual(result.state.pending, ['square']);
  assert.equal(result.state.score, 1);
  const ended = structuredClone(result.state);
  assert.equal(place(result.state, 0, 0, 0).ok, false);
  assert.deepEqual(result.state, ended);
});

test('整组耗尽才补三块，种子可复现，补充后重新判定', () => {
  assert.deepEqual(drawBatch(1), { pending: ['bar2', 'bar2', 'bar3'], seed: 2165703038 });
  assert.deepEqual(createGame(1), { board: emptyBoard(), pending: ['bar2', 'bar2', 'bar3'], seed: 2165703038, score: 0, status: 'playing' });
  const state = fixture();
  const result = place(state, 0, 5, 5);
  assert.equal(result.ok, true);
  assert.deepEqual(result.state.pending, drawBatch(7).pending);
  assert.equal(result.state.seed, drawBatch(7).seed);
  assert.equal(result.state.pending.length, 3);
  assert.equal(result.state.status, 'playing');
  assert.equal(canPlace(result.state.board, 'dot', 5, 5), false);
  assert.deepEqual(place(state, 0, 5, 5), result);
});
