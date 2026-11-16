import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { newState, collect, restart, restore, saveData, targetPoint, isHit, animationScale } from '../public/rules.js';
const config = JSON.parse(await readFile('public/assets/visual-config.json', 'utf8'));
test('五次采集唯一胜利，重开及旧状态独立', () => {
  const initial = newState(); let state = initial;
  for (let count = 1; count <= 5; count++) {
    state = collect(state); assert.equal(state.count, count);
    assert.equal(state.targetIndex, Math.min(count, 4));
    assert.equal(state.phase, count === 5 ? 'won' : 'playing');
  }
  assert.equal(collect(state), state); assert.equal(initial.count, 0);
  assert.deepEqual(restart(state), newState(1));
});
test('全部有效进度恢复，非持久字段丢弃', () => {
  let state = newState();
  for (let count = 0; count <= 5; count++) {
    assert.deepEqual(restore(JSON.stringify({ ...saveData(state), roundId: 999 })).state, { ...state, roundId: 0 });
    assert.equal(restore(JSON.stringify(saveData(state))).invalid, false); state = collect(state);
  }
  assert.deepEqual(restore(null), { state: newState(), invalid: false });
});
test('损坏、未知版本、类型及规则越界存档拒绝', () => {
  for (const raw of ['{', 'null', '[]', '42', ...[
    { version: 2, count: 0, targetIndex: 0, phase: 'playing' },
    { version: 1, count: '2', targetIndex: 2, phase: 'playing' },
    { version: 1, count: 1.5, targetIndex: 1, phase: 'playing' },
    { version: 1, count: -1, targetIndex: 0, phase: 'playing' },
    { version: 1, count: 6, targetIndex: 4, phase: 'won' },
    { version: 1, count: 5, targetIndex: 4, phase: 'playing' },
    { version: 1, count: 2, targetIndex: 1, phase: 'playing' }
  ].map(JSON.stringify)]) assert.deepEqual(restore(raw), { state: newState(), invalid: true });
});
test('三尺寸五位置不同且目标在安全区域，命中半径固定', () => {
  for (const [width,height] of [[288,360],[358,360],[480,420]]) {
    const points = [];
    for (let count = 0; count < 5; count++) {
      const point = targetPoint({ targetIndex: count },width,height,config); points.push(point);
      assert(point.x >= 40 && point.x <= width - 40 && point.y >= 40 && point.y <= height - 40);
      assert(isHit({ x: point.x + 32, y: point.y },point));
      assert(!isHit({ x: point.x + 32.01, y: point.y },point));
    }
    assert.equal(new Set(points.map(JSON.stringify)).size,5);
  }
});
test('缩放关键帧及边界', () => {
  assert.equal(animationScale(0),0.9); assert.equal(animationScale(0.6),1.06);
  assert.equal(animationScale(1),1); assert.equal(animationScale(5),1);
  for (let t = 0; t <= 1; t += 0.01) assert(animationScale(t) >= 0.9 && animationScale(t) <= 1.06);
});
