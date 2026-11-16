import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import {
  createMatch,
  dispatch,
  makeAction,
  legalMoves,
  targetProgress,
  cellId,
  SAFE,
  bonusReasons,
  ownersFor,
} from '../src/rules.js';
import { chooseMove } from '../src/ai.js';
import { createRng, bounded, raw, seedFromSearch } from '../src/rng.js';
import { validateState, SaveStore, loadMatch, MATCH_KEY } from '../src/storage.js';
import { TaskGate } from '../src/lifecycle.js';
import { geometry, holes, movementPath, nativePoint } from '../src/map.js';
import { createTimeline, sampleClip } from '../src/timeline.js';
import { verifyAssets, hash } from '../scripts/verify-assets.mjs';
const manifest = JSON.parse(await readFile('public/assets/visual-manifest.json'));
const geo = geometry(manifest);
const make = (mode = 'classic', count = 2, seed = 1) =>
  createMatch({
    mode,
    seats: ownersFor(count).map((owner, i) => ({ owner, type: i ? 'ai' : 'human' })),
    seed,
    matchId: '测试局',
  });

test('美术白名单与五个复用模块（仅授权标识和提示差异）', async () => {
  await verifyAssets();
  const baseline = JSON.parse(await readFile('design/reuse-baseline.json'));
  for (const file of baseline.files) {
    let data = await readFile(file.path, 'utf8');
    if (file.path.endsWith('rules.js'))
      data = data
        .replaceAll('ludo-classic-reskin-1', 'amber-ludo-1')
        .replaceAll('当前玩家', '当前商队');
    if (file.path.endsWith('storage.js'))
      data = data
        .replaceAll('ludo-classic-reskin:', 'amber-caravan-api:')
        .replaceAll('ludo-classic-reskin-1', 'amber-ludo-1')
        .replaceAll('玩家', '商队');
    assert.equal(hash(data), file.sha256, file.path);
  }
});
test('公共P、私道、终点与实际16圆孔坐标', async () => {
  const calibration = JSON.parse(
    await readFile('reference-assets/camp-calibration.json'),
  );
  assert.deepEqual(holes, calibration.holes_px);
  const grid = manifest.board.prototype_grid;
  assert.equal(new Set(grid.public_path.map((p) => p.join(','))).size, 52);
  assert.deepEqual(grid.safe, SAFE);
  for (let owner = 0; owner < 4; owner++) {
    const piece = { owner, id: `${owner}:1`, progress: -1 };
    assert.deepEqual(geo.point(piece), nativePoint(...holes[owner][0]));
    for (let progress = 0; progress <= 56; progress++) {
      const expected =
        progress <= 50
          ? grid.public_path[(owner * 13 + progress) % 52]
          : grid.private_paths[owner][progress - 51];
      assert.deepEqual(geo.coordinates[cellId(owner, progress)], expected);
    }
    const path = movementPath(piece, 0, 56, geo);
    for (let i = 1; i < path.length; i++) {
      assert(Math.abs(path[i].x - path[i - 1].x) < 23);
      assert(Math.abs(path[i].y - path[i - 1].y) < 23);
    }
  }
});
test('出营、精确到家、超点与已归家', () => {
  for (let dice = 1; dice < 6; dice++)
    assert.equal(targetProgress({ progress: -1 }, dice), null);
  assert.equal(targetProgress({ progress: -1 }, 6), 0);
  assert.equal(targetProgress({ progress: 50 }, 1), 51);
  assert.equal(targetProgress({ progress: 55 }, 1), 56);
  assert.equal(targetProgress({ progress: 55 }, 2), null);
  assert.equal(targetProgress({ progress: 56 }, 6), null);
});
test('安全格、普通敌叠子全吃、经过不吃、同色叠子与奖励', () => {
  const s = make();
  s.currentPlayer = 0;
  s.phase = 'awaitMove';
  s.dice = 2;
  s.pieces[0].progress = 1;
  s.pieces[4].progress = (3 - 26 + 52) % 52;
  s.pieces[5].progress = s.pieces[4].progress;
  const move = legalMoves(s).find((m) => m.pieceId === '0:1');
  assert.equal(move.capturedIds.length, 2);
  const next = dispatch(s, makeAction(s, 'MOVE', '0:1')).state;
  assert.equal(next.pieces[4].progress, -1);
  assert.equal(next.pieces[5].progress, -1);
  assert.equal(next.currentPlayer, 0);
  assert.equal(next.stats.bonusCount, 1);
  s.dice = 1;
  assert.equal(legalMoves(s)[0].capturedIds.length, 0);
  s.pieces[0].progress = 6;
  s.dice = 2;
  s.pieces[4].progress = (8 - 26 + 52) % 52;
  assert.equal(legalMoves(s)[0].capturedIds.length, 0);
  assert.deepEqual(bonusReasons(true, true, true), ['six', 'capture', 'home']);
  assert.deepEqual(bonusReasons(true, true, true, true), []);
});
test('RNG复现、拒绝采样、合法AI/MOVE不消耗随机与第三连六', () => {
  assert.deepEqual(raw(createRng(123)), raw(createRng(123)));
  let calls = 0;
  const value = bounded(createRng(1), 6, (rng) => ({
    value: calls++ === 0 ? 0xffffffff : 5,
    rng: { ...rng, rawDrawCount: calls },
  }));
  assert.equal(calls, 2);
  assert.equal(value.value, 5);
  assert.equal(seedFromSearch('?seed=no').seed, null);
  let s = make('quick');
  s.currentPlayer = 0;
  s.phase = 'awaitMove';
  s.dice = 3;
  const rng = structuredClone(s.rng);
  chooseMove(s);
  assert.deepEqual(dispatch(s, makeAction(s, 'MOVE', '0:1')).state.rng, rng);
  // 用真实RNG寻找连续第三个六；不依靠修改规则抽骰接口。
  let found = false;
  for (let seed = 0; seed < 2000 && !found; seed++) {
    s = make('classic', 2, seed);
    for (let i = 0; i < 200; i++) {
      const result = dispatch(
        s,
        makeAction(s, s.phase === 'awaitRoll' ? 'ROLL' : 'MOVE', chooseMove(s)?.pieceId),
      );
      s = result.state;
      if (s.lastEvent.skipReason === 'tripleSix') {
        assert.equal(s.lastEvent.dice, 6);
        assert.equal(s.sixStreak, 0);
        found = true;
        break;
      }
    }
  }
  assert(found);
});
test('经典/快速×2/3/4席完整合法对局，revision唯一增长', async () => {
  const summaries = [];
  for (const mode of ['classic', 'quick'])
    for (const count of [2, 3, 4])
      for (const seed of [1, 2, 42]) {
        let s = make(mode, count, seed),
          replay = make(mode, count, seed),
          actions = 0;
        while (s.phase !== 'finished' && actions < 20000) {
          const old = s,
            type = s.phase === 'awaitRoll' ? 'ROLL' : 'MOVE',
            move = chooseMove(s);
          const result = dispatch(s, makeAction(s, type, move?.pieceId));
          assert(result.ok);
          s = result.state;
          validateState(s);
          // 相同seed和逐条合法动作重放，不重新选择AI动作或消费额外随机。
          const repeated = dispatch(replay, makeAction(replay, type, move?.pieceId));
          assert(repeated.ok);
          replay = repeated.state;
          assert.deepEqual(replay, s);
          assert.equal(s.revision, old.revision + 1);
          if (type === 'MOVE') assert.deepEqual(s.rng, old.rng);
          assert(!dispatch(s, makeAction(old, type, move?.pieceId)).ok);
          actions++;
        }
        assert.equal(s.phase, 'finished', `${mode}/${count}/${seed}`);
        assert.equal(
          s.pieces.filter((p) => p.owner === s.winner && p.progress === 56).length,
          mode === 'classic' ? 4 : 1,
        );
        assert.deepEqual(replay.rng, s.rng);
        assert.equal(replay.winner, s.winner);
        summaries.push({
          mode,
          count,
          seed,
          actions,
          replayedActions: actions,
          replayIdentical: true,
          winner: s.winner,
          stats: s.stats,
        });
      }
  await writeFile('evidence/rules-summary.json', JSON.stringify(summaries, null, 2));
});
test('独立存档、损坏拒绝、持续失败提示与恢复', () => {
  const map = new Map(),
    io = {
      getItem: (k) => map.get(k) || null,
      setItem: (k, v) => map.set(k, v),
      removeItem: (k) => map.delete(k),
    };
  const store = new SaveStore(io),
    s = make();
  assert(store.save(s));
  assert.deepEqual(loadMatch(io).state, s);
  map.set(MATCH_KEY, 'bad');
  assert(loadMatch(io).error);
  io.setItem = () => {
    throw Error('禁用');
  };
  assert(!store.save(s));
  assert(store.error);
  io.setItem = (k, v) => map.set(k, v);
  assert(store.save(s));
  assert.equal(store.error, null);
  const old = { ...s, rulesVersion: 'amber-ludo-1' };
  assert.throws(() => validateState(old));
});
test('时间轴真实时长设计、弧线中间位置、取消与旧AI令牌', () => {
  const before = make('quick');
  before.phase = 'awaitMove';
  before.currentPlayer = 0;
  before.dice = 3;
  const after = dispatch(before, makeAction(before, 'MOVE', '0:1')).state;
  const tl = createTimeline();
  tl.start(before, after, geo, 0);
  assert.equal(tl.active.clips[0].duration, 330);
  const positions = [55, 165, 275].map((t) => tl.sample(t).positions[0]);
  assert.equal(new Set(positions.map((p) => `${p.x},${p.y}`)).size, 3);
  assert(positions.every((p) => p.u === 0.5));
  tl.cancel();
  assert.equal(tl.sample(400), null);
  assert(!tl.advance(400));
  const dice = sampleClip({ kind: 'dice', duration: 25000 / 30, actor: 0 }, 400);
  assert.equal(dice.frameId, 12);
  let callback,
    called = 0;
  const gate = new TaskGate({
    setTimeout: (fn) => {
      callback = fn;
      return 1;
    },
    clearTimeout: () => {},
  });
  gate.schedule(
    before,
    100,
    () => true,
    () => called++,
  );
  gate.cancel();
  callback();
  assert.equal(called, 0);
});
test('吃子逆路30ms与末100ms cubic缓出端点/中点', () => {
  const clip = {
    kind: 'capture',
    duration: 160,
    paths: [
      {
        pieceId: '2:1',
        duration: 160,
        points: [
          { x: 60, y: 0, progress: 2 },
          { x: 30, y: 0, progress: 1 },
          { x: 0, y: 0, progress: 0 },
          { x: 100, y: 80, progress: -1 },
        ],
      },
    ],
  };
  const point = (time) => sampleClip(clip, time).positions[0];
  assert.equal(point(15).x, 45);
  assert.equal(point(30).x, 30);
  assert.equal(point(60).x, 0);
  assert.equal(point(60).y, 0);
  assert.equal(point(110).x, 87.5);
  assert.equal(point(110).y, 70);
  assert.equal(point(160).x, 100);
  assert.equal(point(160).y, 80);
  assert.equal(point(200).x, 100);
  assert.equal(sampleClip(clip, 160).fraction, 1);
  assert(point(135).x - point(110).x < point(110).x - point(85).x);
});
test('四起点/四星、私道不交叉、无路跳过与经典唯一终局', () => {
  for (const cell of SAFE) {
    const s = make('classic', 4);
    s.currentPlayer = 0;
    s.phase = 'awaitMove';
    s.dice = 1;
    const progress = cell === 0 ? 51 : cell - 1;
    if (cell === 0) {
      s.currentPlayer = 3;
      s.pieces.find((p) => p.owner === 3).progress = 12;
    } else s.pieces[0].progress = progress;
    const owner = s.currentPlayer;
    const enemy = (owner + 2) % 4;
    s.pieces.find((p) => p.owner === enemy).progress = (cell - 13 * enemy + 52) % 52;
    assert(legalMoves(s).find((m) => m.to === cell || m.cell === cell)?.safe);
    assert(legalMoves(s).every((m) => !m.capturedIds.length));
  }
  const s = make();
  s.currentPlayer = 0;
  s.phase = 'awaitMove';
  s.dice = 1;
  s.pieces[0].progress = 50;
  s.pieces[4].progress = 50;
  assert.equal(legalMoves(s)[0].cell, 52);
  assert.equal(legalMoves(s)[0].capturedIds.length, 0);
  s.pieces[0].progress = 55;
  s.pieces[1].progress = 56;
  s.pieces[2].progress = 56;
  s.pieces[3].progress = 56;
  const final = dispatch(s, makeAction(s, 'MOVE', '0:1')).state;
  assert.equal(final.phase, 'finished');
  assert.equal(final.winner, 0);
  assert.equal(final.stats.bonusCount, 0);
  assert.deepEqual(final.lastEvent.bonusReasons, []);
  assert(!dispatch(final, makeAction(final, 'ROLL')).ok);
  let noMove = false;
  for (let seed = 1; seed < 30 && !noMove; seed++) {
    const start = make('classic', 2, seed);
    const next = dispatch(start, makeAction(start, 'ROLL')).state;
    if (next.lastEvent.dice !== 6) {
      assert.equal(next.phase, 'awaitRoll');
      assert.equal(next.lastEvent.skipReason, 'noMove');
      assert.notEqual(next.currentPlayer, start.currentPlayer);
      noMove = true;
    }
  }
  assert(noMove);
});
test('减少动态与正常演出都不能改变相同合法轨迹的状态/RNG/胜者', () => {
  let normal = make('quick', 4, 42),
    reduced = structuredClone(normal),
    budget = 0;
  const timeline = createTimeline();
  while (normal.phase !== 'finished' && budget++ < 10000) {
    const type = normal.phase === 'awaitRoll' ? 'ROLL' : 'MOVE',
      id = chooseMove(normal)?.pieceId;
    const next = dispatch(normal, makeAction(normal, type, id)).state;
    reduced = dispatch(reduced, makeAction(reduced, type, id)).state;
    timeline.start(normal, next, geo, 0);
    for (let time = 0; timeline.active && time < 5000; time += 17) {
      timeline.sample(time);
      timeline.advance(time);
    }
    timeline.cancel();
    normal = next;
    assert.deepEqual(normal, reduced);
  }
  assert.equal(normal.phase, 'finished');
});
