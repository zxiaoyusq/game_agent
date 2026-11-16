/**
 * 真实 Chromium 验收。只经界面开始、掷骰、移动和重开，不注入局面或胜利状态。
 * 固定随机源只用于复现骰子顺序；AI 选择函数只读取快照，动作仍通过按钮点击。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';
import { createServer } from '../scripts/serve.mjs';
import { chooseMove } from '../src/ai.mjs';
import { legalMoves } from '../src/rules.mjs';

const root = path.resolve(import.meta.dirname, '..');
const evidence = path.join(root, 'evidence');
await fs.mkdir(evidence, { recursive: true });
const server = createServer(path.join(root, 'dist'));
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
const checks = [];
const errors = [];
const failedRequests = [];
const externalRequests = [];
const targetMeasurements = [];
const result = { status: 'FAIL', checks, errors, failedRequests, externalRequests, targetMeasurements, viewports: [{width:1440,height:1000},{width:360,height:640},{width:390,height:844}], sourceSha256: {} };

async function createPage(viewport) {
  const context = await browser.newContext({ viewport, reducedMotion: 'no-preference', isMobile: viewport.width < 500, hasTouch: viewport.width < 500 });
  // 每次载入从同一伪随机序列起步，正式代码仍走自己的拒绝采样掷骰流程。
  await context.addInitScript(() => {
    let seed = 1;
    const nativeGetRandomValues = crypto.getRandomValues.bind(crypto);
    Object.defineProperty(crypto, 'getRandomValues', { value(array) {
      if (!(array instanceof Uint8Array) || array.length !== 1) return nativeGetRandomValues(array);
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      array[0] = seed >>> 24;
      return array;
    } });
  });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
  page.on('response', response => { if (response.status() >= 400) failedRequests.push({ url: response.url(), status: response.status() }); });
  page.on('request', request => { if (!request.url().startsWith(origin + '/') && !/^(data:|blob:)/.test(request.url())) externalRequests.push(request.url()); });
  await page.goto(origin, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => !!window.amberCaravan);
  return page;
}
const snapshot = page => page.evaluate(() => window.amberCaravan.snapshot());
async function settled(page) { await page.waitForFunction(() => !window.amberCaravan.snapshot().busy); }
async function screenshot(page, name) { await page.screenshot({ path: path.join(evidence, name), type: 'jpeg', quality: 82, fullPage: true }); }
async function choose(page, selector) { await page.locator(selector).click(); }
async function start(page, { mode = 'quick', count = 2, play = 'local' } = {}) {
  await choose(page, `[data-mode="${mode}"]`);
  await choose(page, `[data-count="${count}"]`);
  await choose(page, `[data-play="${play}"]`);
  await choose(page, '[data-action="start"]');
  await settled(page);
  const state = await snapshot(page);
  assert.equal(state.screen, 'game');
  assert.equal(state.game.mode, mode);
  assert.equal(state.game.players.length, count);
  assert.deepEqual(state.game.players.map(player => player.kind), Array.from({ length: count }, (_, index) => play === 'solo' && index > 0 ? 'ai' : 'human'));
  return state;
}
async function returnLobby(page) {
  const state = await snapshot(page);
  if (!state.modal) await choose(page, '[data-action="pause"]');
  await choose(page, '[data-action="lobby"]');
  assert.equal((await snapshot(page)).screen, 'lobby');
}
async function checkWidth(page, label) {
  const widths = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, document: document.documentElement.scrollWidth }));
  assert.ok(widths.body <= widths.viewport && widths.document <= widths.viewport, `${label}横向溢出：${JSON.stringify(widths)}`);
}
async function measureButtons(page, label) {
  const measures = await page.locator('button').evaluateAll(buttons => buttons.filter(button => {
    const box = button.getBoundingClientRect();
    return box.width > 0 && box.height > 0 && !button.closest('[inert]');
  }).map(button => {
    const box = button.getBoundingClientRect();
    return { label: button.getAttribute('aria-label') || button.textContent.trim().slice(0, 30), width: box.width, height: box.height };
  }));
  for (const button of measures) assert.ok(button.width >= 43.99 && button.height >= 43.99, `${label}按钮小于44px：${JSON.stringify(button)}`);
  targetMeasurements.push({ label, measures });
}

try {
  for (const file of ['index.html', ...(await fs.readdir(path.join(root, 'src'))).sort().map(name => `src/${name}`)]) {
    const source = await fs.readFile(path.join(root, file));
    const built = await fs.readFile(path.join(root, 'dist', file));
    assert.deepEqual(built, source, `构建产物与源码不一致：${file}`);
    result.sourceSha256[file] = createHash('sha256').update(source).digest('hex');
  }
  const page = await createPage({ width: 1440, height: 1000 });
  await checkWidth(page, '桌面大厅');
  await screenshot(page, 'desktop-lobby.jpg');
  await choose(page, '[data-action="settings"]');
  await choose(page, '[data-action="fast"]');
  assert.equal((await snapshot(page)).settings.fast, true);
  // 关闭按钮起始焦点、反向Tab到末项、正向Tab回首项，最后Escape恢复。
  await page.locator('.modal-close').focus();
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.locator('.modal button').last().evaluate(element => element === document.activeElement), true);
  await page.keyboard.press('Tab');
  assert.equal(await page.locator('.modal-close').evaluate(element => element === document.activeElement), true);
  await page.keyboard.press('Escape');
  assert.equal((await snapshot(page)).modal, null);
  assert.equal(await page.locator('#app').getAttribute('inert'), null);
  checks.push('设置切换可保存，弹窗Tab/Shift+Tab焦点闭环和Escape关闭通过');

  await start(page, { mode: 'classic', count: 3, play: 'solo' });
  await choose(page, '#roll-button');
  await page.waitForFunction(() => window.amberCaravan.snapshot().game.stats.rolls >= 3);
  await choose(page, '[data-action="pause"]');
  const paused = (await snapshot(page)).game;
  await page.waitForTimeout(250);
  assert.deepEqual((await snapshot(page)).game, paused);
  await choose(page, '.primary[data-action="close"]');
  assert.equal((await snapshot(page)).modal, null);
  checks.push('三人经典人机局：人类与两支电脑商队真实轮流掷骰；暂停期间局面稳定并可恢复');
  await returnLobby(page);
  await start(page, { mode: 'classic', count: 4, play: 'local' });
  assert.deepEqual((await snapshot(page)).game.players.map(player => player.id), [0, 1, 2, 3]);
  checks.push('四人经典好友同屏配置及四个独立阵营通过');
  await returnLobby(page);

  // 全局从新局开始，重新载入仅重置随机源；不写localStorage、不改内部状态。
  await page.reload({ waitUntil: 'networkidle' });
  await start(page);
  const opening = (await snapshot(page)).game;
  assert.deepEqual(opening.players.map(player => player.id), [0, 2]);
  assert.deepEqual(opening.players[0].tokens, [0, 0, -1, -1]);
  await screenshot(page, 'desktop-game.jpg');
  let rollsClicked = 0;
  let movesClicked = 0;
  while (true) {
    await settled(page);
    const state = (await snapshot(page)).game;
    if (state.phase === 'won') break;
    assert.ok(state.stats.rolls < 3000, '完整快局超过3000次掷骰，疑似停滞');
    if (state.phase === 'roll') {
      await choose(page, '#roll-button');
      rollsClicked++;
      await page.waitForFunction(previous => window.amberCaravan.snapshot().game.stats.rolls > previous, state.stats.rolls);
      if (rollsClicked === 1) { await settled(page); await screenshot(page, 'desktop-game.jpg'); }
    } else {
      const index = chooseMove(state);
      assert.ok(legalMoves(state).includes(index));
      await choose(page, `.token-choices [data-token="${index}"]`);
      movesClicked++;
      await page.waitForFunction(previous => window.amberCaravan.snapshot().game.stats.moves > previous, state.stats.moves);
    }
  }
  await page.waitForSelector('[aria-label="旅程结算"]');
  const won = (await snapshot(page)).game;
  assert.ok(won.players.find(player => player.id === won.winner).homeUnlocked);
  assert.equal(won.players.find(player => player.id === won.winner).finished, 1);
  assert.ok(won.stats.captures >= 1);
  assert.equal(won.stats.rolls, rollsClicked);
  assert.equal(won.stats.moves, movesClicked);
  await screenshot(page, 'victory.jpg');
  result.completedMatch = { seed: 1, rollsClicked, movesClicked, winner: won.winner, captures: won.stats.captures, finished: won.players.map(player => player.finished) };
  checks.push(`两人快局从新局真实点击到结算：${rollsClicked}次掷骰、${movesClicked}次落子、${won.stats.captures}次吃子；未注入局面或胜利`);

  await page.reload({ waitUntil: 'networkidle' });
  await choose(page, '[data-action="resume"]');
  await page.waitForSelector('[aria-label="旅程结算"]');
  assert.deepEqual((await snapshot(page)).game, won);
  checks.push('已获胜局面刷新后可以再次查看结算，不会遗漏赢家或重复计数');

  await choose(page, '[data-action="again"]');
  const restarted = (await snapshot(page)).game;
  assert.equal(restarted.stats.rolls, 0);
  assert.equal(restarted.phase, 'roll');
  assert.deepEqual(restarted.players.map(player => player.tokens), [[0, 0, -1, -1], [0, 0, -1, -1]]);
  await choose(page, '#roll-button');
  await settled(page);
  const afterRoll = (await snapshot(page)).game;
  if (afterRoll.phase === 'move') {
    await choose(page, `.token-choices [data-token="${chooseMove(afterRoll)}"]`);
    await settled(page);
  }
  const beforeReload = (await snapshot(page)).game;
  await page.reload({ waitUntil: 'networkidle' });
  assert.equal((await snapshot(page)).screen, 'lobby');
  await choose(page, '[data-action="resume"]');
  assert.deepEqual((await snapshot(page)).game, beforeReload);
  assert.equal((await snapshot(page)).settings.fast, true);
  checks.push('胜利后再来一局重置完整局面；刷新经继续旅程精确恢复棋子、回合、历史、统计及设置');

  await choose(page, '[data-action="rules"]');
  assert.match(await page.locator('[role="dialog"]').innerText(), /连续第三个六点/);
  await page.keyboard.press('Escape');
  assert.equal((await snapshot(page)).modal, null);
  await page.close();

  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }]) {
    const mobile = await createPage(viewport);
    await checkWidth(mobile, `${viewport.width}大厅`);
    if (viewport.width === 390) {
      const startBounds = await mobile.locator('[data-action="start"]').boundingBox();
      assert.ok(startBounds.y + startBounds.height <= viewport.height, '390×844大厅开始按钮未在首屏完整呈现');
    }
    await measureButtons(mobile, `${viewport.width}大厅`);
    await start(mobile);
    assert.equal(await mobile.evaluate(() => scrollY), 0, '移动端开局应回到棋盘顶部');
    await checkWidth(mobile, `${viewport.width}棋盘`);
    await measureButtons(mobile, `${viewport.width}局内`);
    await choose(mobile, '#roll-button');
    await settled(mobile);
    const before = (await snapshot(mobile)).game;
    assert.equal(before.phase, 'move');
    if (viewport.width === 360) {
      await mobile.locator('.board-token.is-legal').first().focus();
      assert.equal(await mobile.locator('.route-preview polyline').count(), 1);
      await mobile.keyboard.press('Enter');
    } else {
      // 触摸直接落在SVG棋子上；主完整局已覆盖等效的大编号按钮。
      await mobile.locator('.board-token.is-legal').last().tap();
    }
    await settled(mobile);
    assert.equal((await snapshot(mobile)).game.stats.moves, 1);
    await choose(mobile, '[data-action="settings"]');
    await measureButtons(mobile, `${viewport.width}设置`);
    await mobile.keyboard.press('Escape');
    await choose(mobile, '#roll-button');
    await settled(mobile);
    await mobile.locator('.board-heading span').click();
    await mobile.evaluate(() => scrollTo(0, 0));
    await screenshot(mobile, viewport.width === 390 ? 'mobile-game.jpg' : 'mobile-small-game.jpg');
    checks.push(`${viewport.width}×${viewport.height}移动视口真实掷骰与落子、开局回顶部、弹窗、44px按钮和无横向溢出通过`);
    await mobile.close();
  }
  const denied = await createPage({ width: 390, height: 844 });
  await denied.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('浏览器策略拒绝存储', 'SecurityError'); } }));
  await denied.reload({ waitUntil: 'networkidle' });
  assert.match(await denied.locator('#notice').innerText(), /无法读取/);
  await start(denied);
  assert.equal((await snapshot(denied)).saveFailed, true);
  await choose(denied, '#roll-button');
  await settled(denied);
  assert.equal((await snapshot(denied)).game.stats.rolls, 1);
  assert.match(await denied.locator('#notice').innerText(), /未能保存/);
  await denied.close();
  checks.push('SVG棋子触摸、键盘路径预览与Enter落子通过；浏览器拒绝存储时仍能开局掷骰并持续显示保存失败');
  assert.deepEqual(errors, [], '浏览器出现JS错误');
  assert.deepEqual(failedRequests, [], '资源请求失败');
  assert.deepEqual(externalRequests, [], '产物发生外部网络请求');
  checks.push('390×844大厅开始按钮在首屏完整可见；所有资源随包载入，无JS错误、失败资源或外部网络请求');
  result.status = 'PASS';
  result.browser = await browser.version();
  console.log(JSON.stringify({ status: result.status, checks, completedMatch: result.completedMatch }, null, 2));
} catch (error) {
  result.failure = error.stack;
  console.error(error);
  process.exitCode = 1;
} finally {
  await fs.writeFile(path.join(evidence, 'browser-results.json'), JSON.stringify(result, null, 2));
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
