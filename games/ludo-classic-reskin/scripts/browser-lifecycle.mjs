import assert from 'node:assert/strict';
import { chooseMove } from '../src/ai.js';

// 局面只能从菜单和真实输入生成；复用自然种子轨迹定位风险动作。
export async function lifecycleChecks(page, tools, seed) {
  const { start, reduced, snapshot, input, stable } = tools;
  const results = [];
  for (const kind of ['dice', 'walk', 'capture']) {
    for (const operation of ['pause', 'refresh', 'restart']) {
      await start(page, 'quick', 4, 'human', seed);
      await reduced(page, true);
      for (let budget = 0; budget < 2000; budget++) {
        const o = await snapshot(page),
          s = o.state,
          m = chooseMove(s);
        const target =
          kind === 'dice'
            ? s.phase === 'awaitRoll'
            : s.phase === 'awaitMove' &&
              (kind === 'capture'
                ? m.capturedIds.length > 0
                : m.from >= 0 && m.to - m.from >= 3 && !m.capturedIds.length);
        if (target) break;
        await input(page, o);
        await stable(page);
        assert(budget < 1999, '未找到自然生命周期轨迹');
      }
      await reduced(page, false);
      let before = await snapshot(page);
      await input(page, before);
      await page.waitForFunction(
        (kind) => window.ludo.observe().animation?.kind === kind,
        kind,
      );
      let submitted = await snapshot(page);
      assert.equal(submitted.state.revision, before.state.revision + 1);
      // mouse连点与真实CDP触控多指取消共同走页面输入。
      const rect = await page.locator('canvas').boundingBox();
      const diceBox = await page
        .locator(`#dice-${before.state.currentPlayer}`)
        .boundingBox();
      const pieceBox = await page.locator('#piece-1').boundingBox();
      assert(diceBox && pieceBox);
      const center = (box) => ({ x: box.x + box.width / 2, y: box.y + box.height / 2 });
      const targets = [center(diceBox), center(pieceBox)];
      const point = { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
      for (let i = 0; i < 10; i++)
        await page.mouse.click(targets[i % 2].x, targets[i % 2].y);
      const session = await page.context().newCDPSession(page);
      await session.send('Emulation.setTouchEmulationEnabled', {
        enabled: true,
        maxTouchPoints: 2,
      });
      await session.send('Input.dispatchTouchEvent', {
        type: 'touchStart',
        touchPoints: [
          { x: point.x, y: point.y, id: 1 },
          { x: point.x + 8, y: point.y, id: 2 },
        ],
      });
      await session.send('Input.dispatchTouchEvent', {
        type: 'touchCancel',
        touchPoints: [],
      });
      await session.detach();
      assert.deepEqual((await snapshot(page)).state, submitted.state);
      let interrupt = await snapshot(page);
      let naturalRetries = 0;
      // 若调度错过窗口，从菜单重新自然准备；不把已结束演出当成中断。
      while (!interrupt.busy || interrupt.animation?.kind !== kind) {
        assert(naturalRetries++ < 2, '重复输入后未命中动画窗口');
        await start(page, 'quick', 4, 'human', seed);
        await reduced(page, true);
        for (let budget = 0; budget < 2000; budget++) {
          const o = await snapshot(page),
            s = o.state,
            m = chooseMove(s);
          if (
            kind === 'dice'
              ? s.phase === 'awaitRoll'
              : s.phase === 'awaitMove' &&
                (kind === 'capture'
                  ? m.capturedIds.length > 0
                  : m.from >= 0 && m.to - m.from >= 3 && !m.capturedIds.length)
          )
            break;
          await input(page, o);
          await stable(page);
          assert(budget < 1999);
        }
        await reduced(page, false);
        before = await snapshot(page);
        await input(page, before);
        await page.waitForFunction(
          (kind) =>
            window.ludo.observe().busy && window.ludo.observe().animation?.kind === kind,
          kind,
        );
        submitted = await snapshot(page);
        interrupt = submitted;
      }
      assert(interrupt.busy);
      assert.equal(interrupt.animation.kind, kind);
      if (operation === 'pause') {
        await page.locator('#pause').click();
        await page.waitForTimeout(2100);
        assert.deepEqual((await snapshot(page)).state, submitted.state);
        assert(!(await snapshot(page)).busy);
        await page.locator('#pause').click();
      } else if (operation === 'refresh') {
        await page.reload();
        await page.waitForFunction(() => window.ludo?.observe().ready);
        await page.locator('#resume').click();
        await stable(page);
        assert.deepEqual((await snapshot(page)).state, submitted.state);
        assert(!(await snapshot(page)).busy);
        assert.equal((await snapshot(page)).events.length, 0, '刷新重播旧动作');
      } else {
        await page.locator('#settings-button').click();
        await page.locator('#restart').click();
        await page.locator('#start').click();
        const next = (await snapshot(page)).state;
        await page.waitForTimeout(2100);
        assert.notEqual(next.matchId, submitted.state.matchId);
        assert.deepEqual((await snapshot(page)).state, next);
      }
      results.push({
        kind,
        operation,
        clicks: 10,
        targets,
        naturalRetries,
        interrupt: {
          busy: interrupt.busy,
          kind: interrupt.animation.kind,
          elapsed: interrupt.animation.elapsed,
        },
        before: before.state.revision,
        submitted: submitted.state.revision,
        stats: submitted.state.stats,
      });
    }
  }
  return results;
}

export async function hiddenChecks(foreground, background, tools, seed) {
  const { start, reduced, snapshot, input, stable } = tools;
  const results = [];
  for (const kind of ['dice', 'walk', 'capture']) {
    await foreground.bringToFront();
    await start(foreground, 'quick', 4, 'human', seed);
    await reduced(foreground, true);
    for (let i = 0; i < 2000; i++) {
      const o = await snapshot(foreground),
        s = o.state,
        m = chooseMove(s);
      if (
        kind === 'dice'
          ? s.phase === 'awaitRoll'
          : s.phase === 'awaitMove' &&
            (kind === 'capture'
              ? m.capturedIds.length > 0
              : m.from >= 0 && m.to - m.from >= 3 && !m.capturedIds.length)
      )
        break;
      await input(foreground, o);
      await stable(foreground);
      assert(i < 1999);
    }
    await reduced(foreground, false);
    await input(foreground, await snapshot(foreground));
    await foreground.waitForFunction(
      (kind) => window.ludo.observe().animation?.kind === kind,
      kind,
    );
    const interrupt = await snapshot(foreground);
    assert(interrupt.busy);
    assert.equal(interrupt.animation.kind, kind);
    await background.bringToFront();
    await foreground.waitForFunction(() => document.hidden);
    const before = await snapshot(foreground);
    await new Promise((r) => setTimeout(r, 2200));
    const after = await snapshot(foreground);
    assert.deepEqual(after.state, before.state);
    assert(!after.busy);
    assert(after.visibility.some((e) => e.isTrusted && e.hidden));
    results.push({
      kind,
      interrupt: {
        busy: interrupt.busy,
        kind: interrupt.animation.kind,
        elapsed: interrupt.animation.elapsed,
      },
      visibility: after.visibility,
      revision: after.state.revision,
    });
  }
  await foreground.bringToFront();
  await start(foreground, 'quick', 2, 'ai', 1);
  await reduced(foreground, false);
  // 正常动画结束后450ms AI等待提供切后台窗口；必须明确到达AI回合。
  let ai;
  for (let i = 0; i < 50; i++) {
    const o = await snapshot(foreground);
    const isAi =
      o.state.seats.find((s) => s.owner === o.state.currentPlayer).type === 'ai';
    if (isAi && !o.busy) {
      ai = o;
      break;
    }
    if (!isAi && !o.busy) await input(foreground, o);
    await stable(foreground);
  }
  assert(ai, '未自然到达AI回合');
  assert.equal(ai.state.seats.find((s) => s.owner === ai.state.currentPlayer).type, 'ai');
  await background.bringToFront();
  await foreground.waitForFunction(() => document.hidden);
  const before = await snapshot(foreground);
  assert.deepEqual(before.state, ai.state, '错过AI等待窗口');
  await new Promise((r) => setTimeout(r, 2200));
  const hidden = await snapshot(foreground);
  assert.deepEqual(hidden.state, before.state);
  assert(hidden.visibility.some((e) => e.hidden && e.isTrusted));
  await foreground.bringToFront();
  await foreground.waitForFunction(() => !document.hidden);
  await foreground.waitForFunction(
    (revision) => window.ludo.observe().state.revision > revision,
    before.state.revision,
  );
  const resumed = await snapshot(foreground);
  assert.equal(resumed.state.lastEvent.actor, before.state.currentPlayer);
  results.push({
    kind: 'ai',
    owner: before.state.currentPlayer,
    revision: before.state.revision,
    resumedRevision: resumed.state.revision,
    visibility: resumed.visibility,
  });
  return results;
}
