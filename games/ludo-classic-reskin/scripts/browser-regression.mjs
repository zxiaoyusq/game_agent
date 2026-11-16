import assert from 'node:assert/strict';

export async function inputRegression(browser, tools, url) {
  const { start, reduced, snapshot, input, stable } = tools;
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
  });
  const page = await context.newPage();
  const checks = [];
  try {
    await start(page, 'quick', 2, 'human', 1);
    await reduced(page, true);
    // 非当前席位鼠标、键盘、真实触摸均不能消费revision/RNG。
    let before = await snapshot(page);
    const wrongOwner = before.state.seats.find(
      (seat) => seat.owner !== before.state.currentPlayer,
    ).owner;
    const wrong = page.locator(`#dice-${wrongOwner}`);
    const clickSeat = async (locator) => {
      const box = await locator.boundingBox();
      assert(box);
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    };
    const tapSeat = async (locator) => {
      const box = await locator.boundingBox();
      assert(box);
      await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
    };
    await clickSeat(wrong);
    await wrong.focus();
    await page.keyboard.press('Enter');
    await page.keyboard.press('Space');
    await tapSeat(wrong);
    assert.deepEqual((await snapshot(page)).state, before.state);
    checks.push({
      kind: 'wrong-owner',
      revision: before.state.revision,
      rng: before.state.rng,
      inputs: ['mouse', 'Enter', 'Space', 'touch'],
    });
    let oldOwner;
    for (let budget = 0; budget < 30; budget++) {
      before = await snapshot(page);
      oldOwner = before.state.currentPlayer;
      await input(page, before);
      await stable(page);
      if ((await snapshot(page)).state.currentPlayer !== oldOwner) break;
      assert(budget < 29, '未自然轮转');
    }
    before = await snapshot(page);
    assert.notEqual(before.state.currentPlayer, oldOwner);
    const stale = page.locator(`#dice-${oldOwner}`);
    await clickSeat(stale);
    await stale.focus();
    await page.keyboard.press('Enter');
    await tapSeat(stale);
    assert.deepEqual((await snapshot(page)).state, before.state);
    checks.push({
      kind: 'reduced-stale-owner',
      oldOwner,
      currentOwner: before.state.currentPlayer,
      revision: before.state.revision,
    });

    // 延迟一件真实PNG请求，保持存档以同时检查开始/继续门禁。
    let release, requested;
    const held = new Promise((resolve) => {
      release = resolve;
    });
    const reached = new Promise((resolve) => {
      requested = resolve;
    });
    await page.route('**/assets/board-cross.png', async (route) => {
      requested();
      await held;
      await route.continue();
    });
    await page.goto(`${url}/index.html?seed=1`, { waitUntil: 'domcontentloaded' });
    await reached;
    assert(!(await snapshot(page)).ready);
    assert(await page.locator('#start').isDisabled());
    assert(await page.locator('#resume').isDisabled());
    // 原生按钮disabled之外，直接click事件也必须被start.ready拒绝。
    await page.locator('#start').dispatchEvent('click');
    await page.locator('#resume').dispatchEvent('click');
    assert.equal((await snapshot(page)).state, null);
    release();
    await page.waitForFunction(() => window.ludo.observe().ready);
    assert(await page.locator('#start').isEnabled());
    assert(await page.locator('#resume').isEnabled());
    await page.locator('#resume').click();
    await stable(page);
    assert.deepEqual((await snapshot(page)).state, before.state);
    checks.push({
      kind: 'delayed-image',
      path: 'assets/board-cross.png',
      startDisabled: true,
      resumeDisabled: true,
      readyResumeIdentical: true,
    });
  } finally {
    await context.close();
  }
  return checks;
}
