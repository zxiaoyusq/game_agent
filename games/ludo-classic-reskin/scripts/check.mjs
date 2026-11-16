import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm, readdir, access } from 'node:fs/promises';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { join, resolve } from 'node:path';
import assert from 'node:assert/strict';
import { createMatch, dispatch, makeAction, ownersFor } from '../src/rules.js';
import { chooseMove } from '../src/ai.js';
import { hash, verifyAssets } from './verify-assets.mjs';
import { unzipOwn } from './zip.mjs';
import { lifecycleChecks, hiddenChecks } from './browser-lifecycle.mjs';
import { inputRegression } from './browser-regression.mjs';
const checkStarted = performance.now();
const animationEvents = [];
const getTools = () => ({ start, reduced, snapshot, input, stable });
const execute = promisify(execFile);
const output = 'evidence';
await mkdir(`${output}/screenshots`, { recursive: true });
await mkdir(`${output}/frames`, { recursive: true });
const errors = [],
  trajectories = [],
  animationResults = [];
let browser, nativeBrowser;
const mime = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.mp3': 'audio/mpeg',
};
const server = createServer(async (req, res) => {
  try {
    const name = decodeURIComponent(req.url.split('?')[0]);
    const path = resolve('dist', `.${name === '/' ? '/index.html' : name}`);
    assert(path.startsWith(resolve('dist') + '/'));
    const data = await readFile(path);
    res.writeHead(200, {
      'content-type':
        mime[path.slice(path.lastIndexOf('.'))] || 'application/octet-stream',
      'cache-control': 'no-store',
    });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end('未找到资源');
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const url = `http://127.0.0.1:${server.address().port}`;
const snapshot = (page) => page.evaluate(() => window.ludo.observe());
async function stable(page) {
  await page.waitForFunction(
    () => window.ludo?.observe().ready && !window.ludo.observe().busy,
  );
}
async function reduced(page, value) {
  await page.locator('#settings-button').click();
  await page.locator('#reduced').setChecked(value);
  await page.locator('#close').click();
}
async function start(page, mode, count, players, seed) {
  await page.goto(`${url}/index.html?seed=${seed}`);
  await page.waitForFunction(() => window.ludo?.observe().ready);
  await page.locator('#mode').selectOption(mode);
  await page.locator('#count').selectOption(String(count));
  await page.locator('#players').selectOption(players);
  await page.locator('#start').click();
  await stable(page);
}
function plan(mode, count, seed, players = 'human') {
  let s = createMatch({
    mode,
    seats: ownersFor(count).map((owner, i) => ({
      owner,
      type: players === 'ai' && i ? 'ai' : 'human',
    })),
    seed,
    matchId: '规划',
  });
  const actions = [];
  while (s.phase !== 'finished' && actions.length < 10000) {
    const type = s.phase === 'awaitRoll' ? 'ROLL' : 'MOVE',
      move = chooseMove(s);
    const result = dispatch(s, makeAction(s, type, move?.pieceId));
    assert(result.ok);
    actions.push({
      type,
      pieceId: move?.pieceId,
      actor: s.currentPlayer,
      event: result.state.lastEvent,
    });
    s = result.state;
  }
  assert.equal(s.phase, 'finished');
  return { actions, state: s };
}
async function input(page, observation, canvasMove = false, touch = false) {
  const s = observation.state;
  if (s.phase === 'awaitRoll') {
    if (touch) await page.locator(`#dice-${s.currentPlayer}`).tap();
    else await page.locator(`#dice-${s.currentPlayer}`).click();
  } else {
    const move = chooseMove(s);
    if (canvasMove) {
      const point = observation.positions.find((p) => p.pieceId === move.pieceId);
      const rect = await page.locator('canvas').boundingBox();
      const x = rect.x + (point.x * rect.width) / 360,
        y = rect.y + ((point.y - 10) * rect.height) / 600;
      if (touch) await page.touchscreen.tap(x, y);
      else await page.mouse.click(x, y);
    } else {
      const locator = page.locator(`#piece-${move.pieceId.split(':')[1]}`);
      if (touch) await locator.tap();
      else await locator.click();
    }
  }
}
// 测试采样器只读Canvas和观测副本；真实rAF时间，不改时间、规则或页面visibility。
async function beginSampling(page) {
  await page.evaluate(() => {
    window.__samples = [];
    window.__sampling = true;
    let previous = {},
      selected = {};
    const sample = () => {
      if (!window.__sampling) return;
      const observation = window.ludo.observe(),
        a = observation.animation;
      if (a) {
        const canvas = document.querySelector('canvas'),
          ctx = canvas.getContext('2d');
        const scale = canvas.width / 360;
        const roi =
          a.kind === 'dice' ? [a.x - 32, a.y - 40, 64, 80] : [12, 126, 336, 336];
        const bytes = ctx.getImageData(
          Math.floor(roi[0] * scale),
          Math.floor(roi[1] * scale),
          Math.floor(roi[2] * scale),
          Math.floor(roi[3] * scale),
        ).data;
        let difference = 0;
        const old = previous[a.kind];
        if (old)
          for (let i = 0; i < bytes.length; i += 4)
            if (
              bytes[i] !== old[i] ||
              bytes[i + 1] !== old[i + 1] ||
              bytes[i + 2] !== old[i + 2]
            )
              difference++;
        previous[a.kind] = new Uint8ClampedArray(bytes);
        const bucket = Math.floor(a.elapsed / (a.kind === 'capture' ? 45 : 50));
        const key = `${a.kind}:${bucket}`;
        const image = !selected[key];
        selected[key] = true;
        window.__samples.push({
          time: performance.now(),
          kind: a.kind,
          elapsed: a.elapsed,
          duration: a.clip.duration,
          frameId: a.frameId,
          positions: a.positions,
          fraction: a.fraction,
          roi,
          difference,
          png: image ? canvas.toDataURL('image/png') : null,
        });
      }
      requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  });
}
async function endSampling(page, label) {
  const samples = await page.evaluate(() => {
    window.__sampling = false;
    return window.__samples;
  });
  for (const kind of new Set(samples.map((s) => s.kind))) {
    const frames = samples.filter((s) => s.kind === kind);
    const images = frames.filter((s) => s.png);
    for (let i = 0; i < images.length; i++) {
      await writeFile(
        `${output}/frames/${label}-${kind}-${String(i).padStart(2, '0')}.png`,
        Buffer.from(images[i].png.split(',')[1], 'base64'),
      );
    }
    animationResults.push({
      label,
      kind,
      frames: frames.map(({ png, ...data }) => data),
      imageCount: images.length,
    });
  }
  return samples;
}
async function fullGame(page, mode, count, players, seed, animations = false) {
  await start(page, mode, count, players, seed);
  await reduced(page, true);
  const doneKinds = new Set();
  let steps = 0,
    canvasUsed = false;
  while (steps < 8000) {
    await stable(page);
    let o = await snapshot(page),
      s = o.state;
    if (s.phase === 'finished') break;
    if (s.seats.find((seat) => seat.owner === s.currentPlayer).type === 'ai') {
      await page.waitForTimeout(15);
      continue;
    }
    const move = chooseMove(s);
    const candidate =
      s.phase === 'awaitRoll'
        ? 'dice'
        : move.capturedIds.length
          ? 'capture'
          : move.to === 56
            ? 'home'
            : move.from >= 0 && move.to - move.from >= 3
              ? 'walk'
              : null;
    const record = animations && candidate && !doneKinds.has(candidate);
    if (record) {
      await reduced(page, false);
      o = await snapshot(page);
      await beginSampling(page);
    }
    const revision = o.state.revision;
    await input(page, o, !canvasUsed && s.phase === 'awaitMove' && o.legal.length === 1);
    if (s.phase === 'awaitMove' && o.legal.length === 1) canvasUsed = true;
    await stable(page);
    const next = await snapshot(page);
    assert(next.state.revision > revision);
    trajectories.push({
      mode,
      count,
      seed,
      revision: next.state.revision,
      event: next.state.lastEvent,
    });
    if (record) {
      const frames = await endSampling(page, `${mode}-${revision}`);
      const events = next.events.filter((e) => e.revision === revision + 1);
      animationEvents.push(...events);
      for (const kind of new Set(frames.map((f) => f.kind))) {
        const group = frames.filter((f) => f.kind === kind);
        assert(
          group.filter((f) => f.difference > 0).length >= 2,
          `${kind}缺少实际像素变化`,
        );
        const first = events.find((e) => e.kind === kind && e.stage === 'start');
        const end = events.find((e) => e.kind === kind && e.stage === 'end');
        assert(first && end, `${kind}缺少实际绘制起止事件`);
        assert(
          Math.abs(end.time - first.time - group[0].duration) < 80,
          `${kind}真实时间不符`,
        );
        if (kind === 'home') assert(group[0].duration >= 300 && group[0].duration <= 450);
        if (kind === 'victory')
          assert(group[0].duration >= 800 && group[0].duration <= 1200);
      }
      const relevant = frames.filter((f) => f.kind === candidate);
      assert(relevant.length >= 3, `缺少${candidate}中间帧`);
      assert(
        relevant.filter((f) => f.difference > 0).length >= 2,
        `${candidate}没有ROI变化`,
      );
      if (candidate === 'dice') {
        assert(new Set(relevant.map((f) => f.frameId)).size >= 3);
        assert(relevant[0].duration >= 600 && relevant[0].duration <= 900);
      }
      if (candidate === 'walk') {
        assert(new Set(relevant.map((f) => f.positions[0].stepIndex)).size >= 3);
        assert(
          new Set(relevant.map((f) => `${f.positions[0].x},${f.positions[0].y}`)).size >=
            3,
        );
        assert(relevant.some((f) => f.positions[0].u > 0.2 && f.positions[0].u < 0.8));
      }
      if (candidate === 'capture') {
        assert(
          next.state.lastEvent.capturedIds.every(
            (id) => next.state.pieces.find((p) => p.id === id).progress === -1,
          ),
        );
        for (const id of next.state.lastEvent.capturedIds) {
          const positions = relevant.flatMap((f) =>
            f.positions.filter((p) => p.pieceId === id),
          );
          assert(
            new Set(positions.map((p) => `${p.x},${p.y}`)).size >= 3,
            '被吃棋子没有逆路中间位置',
          );
          assert(positions.some((p) => p.u > 0.1 && p.u < 0.9));
        }
      }
      doneKinds.add(candidate);
      if (frames.some((f) => f.kind === 'victory')) doneKinds.add('victory');
      if (next.state.phase !== 'finished') await reduced(page, true);
    }
    steps++;
  }
  const final = await snapshot(page);
  assert.equal(final.state.phase, 'finished', `${mode}UI没有完成`);
  assert.equal(
    final.state.pieces.filter((p) => p.owner === final.state.winner && p.progress === 56)
      .length,
    mode === 'classic' ? 4 : 1,
  );
  await page.screenshot({ path: `${output}/screenshots/${mode}-result.png` });
  if (animations)
    for (const kind of ['dice', 'walk', 'capture', 'home', 'victory'])
      assert(doneKinds.has(kind), `缺少自然动画${kind}`);
  return {
    mode,
    count,
    players,
    seed,
    steps,
    winner: final.state.winner,
    stats: final.state.stats,
    canvasUsed,
  };
}
async function packageCheck() {
  const scratch = 'evidence/package-rebuild';
  await rm(scratch, { recursive: true, force: true });
  await mkdir(scratch, { recursive: true });
  const names = await unzipOwn(
    'releases/ludo-classic-reskin-source.zip',
    `${scratch}/source`,
  );
  assert(!names.some((n) => /node_modules|reference-inputs|audit-art|\.env/.test(n)));
  const distNames = await unzipOwn(
    'releases/ludo-classic-reskin-dist.zip',
    `${scratch}/dist`,
  );
  await execute(process.execPath, ['scripts/build.mjs'], {
    cwd: resolve(scratch, 'source'),
    env: { ...process.env, REBUILD_ONLY: '1' },
  });
  await execute(process.execPath, ['--test', 'tests/core.test.mjs'], {
    cwd: resolve(scratch, 'source'),
  });
  for (const name of distNames) {
    assert.equal(
      hash(await readFile(`dist/${name}`)),
      hash(await readFile(`${scratch}/source/dist/${name}`)),
      `解包重建不一致：${name}`,
    );
    assert.equal(
      hash(await readFile(`dist/${name}`)),
      hash(await readFile(`${scratch}/dist/${name}`)),
    );
  }
  await writeFile(
    'evidence/packages.json',
    JSON.stringify(
      {
        sourceEntries: names.length,
        distEntries: distNames.length,
        rebuildIdentical: true,
      },
      null,
      2,
    ),
  );
  await rm(scratch, { recursive: true, force: true });
}
try {
  await verifyAssets();
  await packageCheck();
  let executablePath;
  for (const candidate of [
    process.env.CHROMIUM_PATH,
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    chromium.executablePath(),
  ].filter(Boolean)) {
    try {
      await access(candidate);
      executablePath = candidate;
      break;
    } catch {}
  }
  browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ['--no-sandbox'],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: 'evidence/video', size: { width: 720, height: 800 } },
  });
  const regressions = await inputRegression(browser, getTools(), url);
  await writeFile('evidence/input-regression.json', JSON.stringify(regressions, null, 2));
  const page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('requestfailed', (request) => errors.push(request.url()));
  page.on('request', (request) =>
    assert(
      request.url().startsWith(url) || request.url().startsWith('data:'),
      '外网请求',
    ),
  );
  await page.goto(`${url}/index.html?seed=1`);
  await page.waitForFunction(() => window.ludo?.observe().ready);
  await page.screenshot({ path: 'evidence/screenshots/B01-menu.png' });
  // 快速种子轨迹自然形成吃子；不把规划局写入页面。
  let seed = 1;
  while (!plan('quick', 4, seed).actions.some((a) => a.event.capturedIds.length)) seed++;
  const quick = await fullGame(page, 'quick', 4, 'human', seed, true);
  await page.reload();
  await page.locator('#resume').click();
  await stable(page);
  assert.equal((await snapshot(page)).state.phase, 'finished');
  await page.locator('#again').click();
  assert(await page.locator('#menu').isVisible());
  const classic = await fullGame(page, 'classic', 2, 'ai', 1);
  const lifecycle = await lifecycleChecks(page, getTools(), seed);
  await writeFile('evidence/lifecycle.json', JSON.stringify(lifecycle, null, 2));
  // 三席配置与轮转。
  await start(page, 'quick', 3, 'human', 5);
  await reduced(page, true);
  const actors = new Set();
  for (let i = 0; i < 12; i++) {
    const o = await snapshot(page);
    actors.add(o.state.currentPlayer);
    await input(page, o);
    await stable(page);
  }
  assert.equal(actors.size, 3);
  // 正常速度重复输入、暂停、刷新与观察副本隔离。
  await reduced(page, false);
  let o = await snapshot(page);
  while (o.state.phase !== 'awaitRoll') {
    await input(page, o);
    await stable(page);
    o = await snapshot(page);
  }
  const old = o.state;
  const dice = page.locator(`#dice-${old.currentPlayer}`);
  await dice.focus();
  await page.keyboard.press('Enter');
  await page.waitForTimeout(100);
  const committed = (await snapshot(page)).state;
  assert.equal(committed.revision, old.revision + 1);
  const box = await dice.boundingBox();
  for (let i = 0; i < 10; i++)
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  assert.equal((await snapshot(page)).state.revision, committed.revision);
  await page.locator('#pause').click();
  await page.waitForTimeout(2100);
  assert.equal((await snapshot(page)).state.revision, committed.revision);
  assert(!(await snapshot(page)).busy);
  await page.locator('#pause').click();
  await page.reload();
  await page.locator('#resume').click();
  await stable(page);
  assert.deepEqual((await snapshot(page)).state, committed);
  assert(!(await snapshot(page)).busy);
  await page.evaluate(() => {
    const copy = window.ludo.observe();
    copy.state.pieces[0].progress = 56;
    copy.state.rng.state = 0;
  });
  assert.deepEqual((await snapshot(page)).state, committed);
  const focus = page.locator('#settings-button');
  await focus.focus();
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'pause');
  await page.keyboard.press('Shift+Tab');
  await page.waitForTimeout(100);
  assert(await focus.evaluate((el) => el === document.activeElement));
  await page.keyboard.press('Space');
  assert(await page.locator('#settings').isVisible());
  await page.locator('#close').click();
  assert(await focus.evaluate((el) => el === document.activeElement));
  // 存档写失败通过浏览器存储故障实现，不改游戏入口。
  const failureContext = await browser.newContext();
  await failureContext.addInitScript(() => {
    Storage.prototype.setItem = function () {
      throw new DOMException('禁止存储', 'QuotaExceededError');
    };
  });
  const failure = await failureContext.newPage();
  await start(failure, 'quick', 2, 'human', 1);
  assert((await failure.locator('#error').textContent()).includes('进度未保存'));
  await failureContext.close();
  const layouts = [];
  for (const viewport of [
    { width: 390, height: 844 },
    { width: 320, height: 568 },
    { width: 360, height: 640 },
  ]) {
    const mobile = await browser.newContext({
      viewport,
      deviceScaleFactor: viewport.width === 320 ? 1 : 2,
      hasTouch: true,
      isMobile: true,
    });
    const p = await mobile.newPage();
    p.on('pageerror', (error) => errors.push(error.message));
    await start(p, 'quick', 2, 'human', 1);
    await reduced(p, true);
    for (let i = 0; i < 6; i++) {
      await stable(p);
      const obs = await snapshot(p);
      await input(p, obs, false, true);
    }
    await stable(p);
    const dimensions = await p.evaluate(() => ({
      scroll: document.documentElement.scrollHeight,
      height: innerHeight,
      rect: document.querySelector('canvas').getBoundingClientRect().toJSON(),
      buttons: [...document.querySelectorAll('#controls button:not([hidden])')].map(
        (b) => ({
          width: b.getBoundingClientRect().width,
          height: b.getBoundingClientRect().height,
        }),
      ),
    }));
    assert(dimensions.scroll <= dimensions.height);
    assert(dimensions.rect.y >= 0 && dimensions.rect.bottom <= viewport.height + 1);
    assert(dimensions.buttons.every((b) => b.width >= 44 && b.height >= 44));
    layouts.push({ viewport, ...dimensions });
    if (viewport.width === 390) await p.screenshot({ path: 'evidence/mobile.png' });
    await mobile.close();
  }
  // 默认上下文、原生Chromium进程与可信后台事件，真实等待2秒。
  const profile = resolve('evidence/cdp-profile');
  await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  await mkdir(profile, { recursive: true });
  nativeBrowser = spawn(
    executablePath,
    [
      '--headless=new',
      '--no-sandbox',
      '--remote-debugging-port=0',
      `--user-data-dir=${profile}`,
      'about:blank',
    ],
    { stdio: 'ignore' },
  );
  let port;
  for (let i = 0; i < 100; i++) {
    try {
      port = Number(
        (await readFile(`${profile}/DevToolsActivePort`, 'utf8')).split('\n')[0],
      );
      break;
    } catch {
      await new Promise((r) => setTimeout(r, 50));
    }
  }
  assert(port, '原生Chromium没有启动');
  const cdpBrowser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`, {
    noDefaults: true,
  });
  const nativeContext = cdpBrowser.contexts()[0];
  const foreground = await nativeContext.newPage(),
    background = await nativeContext.newPage();
  await background.goto('about:blank');
  await foreground.bringToFront();
  await start(foreground, 'quick', 2, 'ai', 1);
  await reduced(foreground, false);
  await stable(foreground);
  let nativeState = await snapshot(foreground);
  if (nativeState.state.phase === 'awaitRoll' && nativeState.state.currentPlayer === 0)
    await input(foreground, nativeState);
  await background.bringToFront();
  await foreground.waitForFunction(() => document.hidden);
  const hiddenStart = await snapshot(foreground);
  await new Promise((r) => setTimeout(r, 2200));
  const hiddenEnd = await snapshot(foreground);
  assert.deepEqual(hiddenEnd.state, hiddenStart.state);
  assert(hiddenEnd.visibility.some((e) => e.hidden && e.isTrusted));
  assert(!hiddenEnd.busy);
  await foreground.bringToFront();
  await foreground.waitForFunction(() => !document.hidden);
  const hidden = await hiddenChecks(foreground, background, getTools(), seed);
  await writeFile('evidence/visibility.json', JSON.stringify(hidden, null, 2));
  const exit = new Promise((resolve) => nativeBrowser.once('exit', resolve));
  await cdpBrowser.close();
  nativeBrowser.kill();
  await exit;
  nativeBrowser = null;
  await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  assert.deepEqual(errors, []);
  await writeFile(
    'evidence/animation-pixels.json',
    JSON.stringify(animationResults, null, 2),
  );
  await writeFile('evidence/trajectories.json', JSON.stringify(trajectories, null, 2));
  await writeFile(
    'evidence/animation-events.json',
    JSON.stringify(animationEvents, null, 2),
  );
  await writeFile(
    'evidence/browser-summary.json',
    JSON.stringify(
      {
        passed: true,
        browser: browser.version(),
        quick,
        classic,
        layouts,
        errors,
        visibilityTrusted: true,
        packagesRebuilt: true,
        durationMs: performance.now() - checkStarted,
      },
      null,
      2,
    ),
  );
  await context.close();
  console.log(
    '浏览器验收通过：经典人机/快速4人完整自然对局、五类正常动画ROI/连续帧、三席/手机/生命周期、解包重建',
  );
} catch (error) {
  await writeFile(
    'evidence/browser-failure.json',
    JSON.stringify(
      { passed: false, error: error.stack, errors, animationResults },
      null,
      2,
    ),
  );
  console.error('浏览器验收失败：', error);
  process.exitCode = 1;
} finally {
  if (nativeBrowser) nativeBrowser.kill();
  if (browser) await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
