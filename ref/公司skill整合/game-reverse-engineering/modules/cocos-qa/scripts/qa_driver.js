/* Blockudoku headless QA driver (Chrome CDP) */
const fs = require('fs');
const path = require('path');

const CDP_PORT = 9224;
const SHOT_DIR = process.env.SHOT_DIR || path.join(__dirname, 'qa_shots');
fs.mkdirSync(SHOT_DIR, { recursive: true });

const results = [];
function check(name, ok, extra) {
  results.push({ name, ok, extra });
  console.log((ok ? 'PASS' : 'FAIL') + ' | ' + name + (extra ? ' | ' + JSON.stringify(extra) : ''));
}

async function getWsUrl() {
  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
  const list = await res.json();
  const page = list.find((t) => t.type === 'page' && t.url.indexOf('index.html') >= 0);
  if (!page) throw new Error('page target not found: ' + JSON.stringify(list.map((t) => t.url)));
  return page.webSocketDebuggerUrl;
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    const c = new CDP(ws);
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id) {
        const p = c.pending.get(msg.id);
        if (p) { c.pending.delete(msg.id); msg.error ? p.rej(new Error(JSON.stringify(msg.error))) : p.res(msg.result); }
      } else if (msg.method) {
        c.events.push(msg);
      }
    };
    return c;
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async eval(expression, awaitPromise = false) {
    const r = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise });
    if (r.exceptionDetails) throw new Error('eval exception: ' + JSON.stringify(r.exceptionDetails.exception));
    return r.result ? r.result.value : undefined;
  }
  async waitFor(expr, timeoutMs = 15000, label = expr) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const v = await this.eval(expr);
        if (v) return v;
      } catch (e) { /* expression may fail before boot */ }
      await new Promise((r) => setTimeout(r, 150));
    }
    throw new Error('waitFor timeout: ' + label);
  }
  async sleep(ms) { await new Promise((r) => setTimeout(r, ms)); }
  async screenshot(name) {
    const r = await this.send('Page.captureScreenshot', { format: 'png' });
    const file = path.join(SHOT_DIR, name + '.png');
    fs.writeFileSync(file, Buffer.from(r.data, 'base64'));
    return file;
  }
  consoleErrors() {
    return this.events.filter((e) =>
      (e.method === 'Runtime.exceptionThrown') ||
      (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error'));
  }
}

async function main() {
  const cdp = await CDP.connect(await getWsUrl());
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  // Force a 720x1280 (9:16) viewport so the SHOW_ALL canvas has no black
  // letterbox bars, then reload to let the engine re-fit.
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 720, height: 1280, deviceScaleFactor: 1, mobile: false,
  });
  await cdp.send('Page.reload');

  // ---- boot & main menu ----
  await cdp.waitFor(`!!(window.cc && cc.find('Canvas') && cc.find('Canvas/MainMenu') && window.__bootReady)`, 30000, 'boot');
  const menu = await cdp.eval(`(() => {
    const m = cc.find('Canvas/MainMenu');
    return {
      logo: !!m.getChildByName('logo'),
      newGame: !!m.getChildByName('btn_new_game'),
      settings: !!m.getChildByName('btn_settings'),
      howto: !!m.getChildByName('btn_howto'),
      sound: !!m.getChildByName('btn_sound'),
      active: m.active,
    };
  })()`);
  check('main menu reachable', menu.logo && menu.newGame && menu.settings && menu.howto && menu.active, menu);

  // ---- tutorial overlay ----
  const tut = await cdp.eval(`(() => {
    const ov = cc.find('Canvas/TutorialOverlay');
    if (!ov) return { exists: false };
    const text = ov.getChildByName('tutText').getComponent(cc.Label).string;
    return { exists: ov.active, text, hasHand: !!ov.getChildByName('hand'), hasSkip: !!ov.getChildByName('btn_tut_skip') };
  })()`);
  check('tutorial overlay shows on first launch', tut.exists && tut.text.length > 0 && tut.hasHand && tut.hasSkip, tut);
  await cdp.eval(`cc.find('Canvas/TutorialOverlay/btn_tut_next').emit('click')`);
  await cdp.eval(`cc.find('Canvas/TutorialOverlay/btn_tut_next').emit('click')`);
  await cdp.eval(`cc.find('Canvas/TutorialOverlay/btn_tut_next').emit('click')`);
  await cdp.sleep(300);
  const tutGone = await cdp.eval(`!cc.find('Canvas/TutorialOverlay').active`);
  check('tutorial completes and hides', tutGone);
  await cdp.screenshot('01_main_menu');

  // ---- start new game ----
  await cdp.eval(`cc.find('Canvas/MainMenu/btn_new_game').emit('click')`);
  await cdp.waitFor(`!!window.__blockudoku && !!cc.find('Canvas/GameScene') && cc.find('Canvas/GameScene').active`, 15000, 'game scene');
  const init = await cdp.eval(`(() => {
    const s = window.__blockudoku.getState();
    const board = cc.find('Canvas/GameScene/Board');
    const tray = cc.find('Canvas/GameScene/Tray');
    return {
      score: s.score, trayLen: s.tray.length, tray: s.tray,
      cellCount: board.children.length - 1,
      slotCount: tray.children.length,
      gameOver: s.gameOver,
    };
  })()`);
  check('new game: 81 cells + 3 slots + score 0', init.cellCount === 81 && init.slotCount === 3 && init.trayLen === 3 && init.score === 0 && !init.gameOver, init);

  // ---- 1:1 layout metrics (original: cell 38, board 356, slot 100, spacing 110) ----
  const layout = await cdp.eval(`(() => {
    const cell = cc.find('Canvas/GameScene/Board/cell_0_0');
    const bg = cc.find('Canvas/GameScene/Board/boardBg');
    const slot0 = cc.find('Canvas/GameScene/Tray/slot_0');
    const slot2 = cc.find('Canvas/GameScene/Tray/slot_2');
    const hud = cc.find('Canvas/GameScene/HUD');
    return {
      cellW: cell.getContentSize().width, cellH: cell.getContentSize().height,
      boardW: bg.getContentSize().width, boardH: bg.getContentSize().height,
      slotW: slot0.getContentSize().width, slotH: slot0.getContentSize().height,
      slotGap: slot2.position.x - slot0.position.x,
      hudY: hud.position.y,
      cellPitch: cell.position.x - cc.find('Canvas/GameScene/Board/cell_0_1').position.x,
    };
  })()`);
  check('1:1 layout: cell 38px, board 356, slot 100, spacing 110',
    layout.cellW === 38 && layout.cellH === 38 && layout.boardW === 356 && layout.boardH === 356 &&
    layout.slotW === 100 && layout.slotH === 100 && layout.slotGap === 220 && Math.abs(layout.cellPitch) === 38, layout);
  await cdp.screenshot('02_game_start');

  // ---- simple placement ----
  const placed = await cdp.eval(`window.__blockudoku.placeAt(0, 0, 0)`);
  check('place block at (0,0)', !!placed.placed, placed);
  if (placed.placed) {
    check('score gain = block cell count', placed.gain === placed.outOfMatch && placed.outOfMatch > 0, placed);
  }
  // color consistency: placed cells must keep the tray color (boardColor == blockColor[slot])
  const colorCons = await cdp.eval(`(() => {
    const s = window.__blockudoku.getState();
    const pat = window.__blockudoku.game.tray;
    const placedCells = [];
    for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) {
      if (s.board[r][c] !== 0) placedCells.push(s.boardColor[r][c]);
    }
    return { trayColor: s.blockColor[0], placed: placedCells, allMatch: placedCells.length > 0 && placedCells.every((v) => v === s.blockColor[0]) };
  })()`);
  check('color consistency: placed block keeps tray color', colorCons.allMatch, colorCons);
  await cdp.sleep(300);
  await cdp.screenshot('03_after_place');

  // ---- line clear (+10) ----
  const line = await cdp.eval(`(() => {
    window.__blockudoku.startNew();
    const b = [];
    for (let r = 0; r < 9; r++) { b.push(new Array(9).fill(0)); }
    for (let c = 0; c < 6; c++) b[0][c] = 1;
    window.__blockudoku.setBoard(b);
    window.__blockudoku.setTray(['HorizontalLine3', 'Square2x2', 'VerticalLine2']);
    return window.__blockudoku.placeAt(0, 0, 6);
  })()`);
  check('line clear: +3 cells +10 match', line.placed && line.gain === 13 && line.groups === 1 && line.matched === 9, line);
  const lineBoard = await cdp.eval(`window.__blockudoku.getState().board[0].join('')`);
  check('row 0 cleared', lineBoard === '000000000', lineBoard);
  check('score after line clear = 13', await cdp.eval('window.__blockudoku.getState().score') === 13, await cdp.eval('window.__blockudoku.getState().score'));

  // ---- streak (2+ groups) ----
  const streak = await cdp.eval(`(() => {
    window.__blockudoku.startNew();
    const b = [];
    for (let r = 0; r < 9; r++) b.push(new Array(9).fill(0));
    // row5 full except (5,3),(5,4); row6 full except (6,3),(6,4); col3 full except (5,3),(6,3)
    for (let c = 0; c < 9; c++) {
      if (c !== 3 && c !== 4) b[5][c] = 1;
      if (c !== 3 && c !== 4) b[6][c] = 1;
    }
    for (let r = 0; r < 9; r++) if (r !== 5 && r !== 6) b[r][3] = 1;
    window.__blockudoku.setBoard(b);
    window.__blockudoku.setTray(['Square2x2', 'VerticalLine2', 'HorizontalLine3']);
    return window.__blockudoku.placeAt(0, 5, 3);
  })()`);
  check('streak: 3 groups simultaneously', streak.placed && streak.groups === 3, streak);
  if (streak.placed) {
  check('streak+combo: 4 cells + 30 match + 27 streak + 25 GreekPi = 86', streak.placed && streak.score === 86 && streak.gain === 86 && streak.combo === 'GreekPi', streak);
  }
  await cdp.sleep(350);
  await cdp.screenshot('04_streak');

  // ---- game over detection logic ----
  const detect = await cdp.eval(`(() => {
    window.__blockudoku.startNew();
    const b = [];
    for (let r = 0; r < 9; r++) b.push(new Array(9).fill(1));
    b[8][7] = 0; b[8][8] = 0;
    window.__blockudoku.setBoard(b);
    window.__blockudoku.setTray(['HorizontalLine3', 'VerticalLine3', 'Square2x2']);
    return { canPlaceAny: window.__blockudoku.canPlaceAny() };
  })()`);
  check('game over detection: no piece fits anywhere', detect.canPlaceAny === false, detect);

  // ---- natural game over via greedy fill ----
  const fill = await cdp.eval(`(() => {
    window.__blockudoku.startNew();
    let steps = 0;
    while (steps < 2000) {
      if (window.__blockudoku.getState().gameOver) return { gameOver: true, score: window.__blockudoku.getState().score, steps };
      let placedAny = false;
      outer:
      for (let slot = 0; slot < 3; slot++) {
        for (let r = 0; r < 9; r++) {
          for (let c = 0; c < 9; c++) {
            const res = window.__blockudoku.placeAt(slot, r, c);
            if (res.placed) { placedAny = true; break outer; }
          }
        }
      }
      if (!placedAny) break;
      steps++;
    }
    return { gameOver: window.__blockudoku.getState().gameOver, score: window.__blockudoku.getState().score, steps, stopped: true };
  })()`);
  check('greedy fill placed pieces', fill.steps > 0, fill);
  await cdp.waitFor(`window.__blockudoku.getState().gameOver === true`, 8000, 'game over state');
  check('game over detected', true);
  await cdp.waitFor(`!!cc.find('Canvas/GameScene/PopupLayer/gameOverPanel')`, 8000, 'game over panel');
  const records = await cdp.eval(`window.__blockudoku.getRecords()`);
  const scoreNow = await cdp.eval(`window.__blockudoku.getState().score`);
  check('best score recorded', records.best === scoreNow && scoreNow > 0, { best: records.best, score: scoreNow });
  await cdp.sleep(400);
  await cdp.screenshot('05_game_over');

  const revive = await cdp.eval(`(() => {
    const btn = cc.find('Canvas/GameScene/PopupLayer/gameOverPanel/btn_second_chance');
    if (!btn) return { clicked: false };
    btn.emit('click');
    return { clicked: true };
  })()`);
  check('second chance button present', revive.clicked, revive);
  await cdp.sleep(500);
  const after = await cdp.eval(`(() => {
    const s = window.__blockudoku.getState();
    const full = s.board.every((row) => row.every((v) => v === 0));
    return { boardEmpty: full, score: s.score, gameOver: s.gameOver, panelGone: !cc.find('Canvas/GameScene/PopupLayer/gameOverPanel') };
  })()`);
  check('second chance: board cleared, score kept', after.boardEmpty && after.score === scoreNow && !after.gameOver && after.panelGone, after);
  await cdp.screenshot('06_after_revive');

  // ---- back to menu + continue ----
  await cdp.eval(`cc.find('Canvas/GameScene/HUD/btn_back').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/MainMenu').active === true`, 8000, 'menu shown again');
  const menu2 = await cdp.eval(`(() => ({
    menuActive: cc.find('Canvas/MainMenu').active,
    contActive: cc.find('Canvas/MainMenu/btn_continue').active,
    best: cc.find('Canvas/MainMenu/bestScore').getComponent(cc.Label).string,
  }))()`);
  check('back to menu: continue available + best shown', menu2.menuActive && menu2.contActive && parseInt(menu2.best, 10) === scoreNow, menu2);
  await cdp.screenshot('07_menu_after_back');

  await cdp.eval(`cc.find('Canvas/MainMenu/btn_continue').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/GameScene').active === true && window.__blockudoku.getState().score === ${scoreNow}`, 8000, 'continue resumes');
  check('continue resumes saved score', true, { score: await cdp.eval('window.__blockudoku.getState().score') });

  // ---- sound toggle ----
  const snd = await cdp.eval(`(() => {
    const on1 = cc.AudioManager.audioEnabled;
    window.__blockudoku.sound(false);
    const on2 = cc.AudioManager.audioEnabled;
    window.__blockudoku.sound(true);
    const on3 = cc.AudioManager.audioEnabled;
    return { on1, on2, on3 };
  })()`);
  check('sound toggle works', snd.on1 === true && snd.on2 === false && snd.on3 === true, snd);

  // ---- settings & howto panels ----
  await cdp.eval(`cc.find('Canvas/GameScene/HUD/btn_back').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/MainMenu').active === true`, 8000, 'menu');
  await cdp.eval(`cc.find('Canvas/MainMenu/btn_settings').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/SettingsPanel').active === true`, 5000, 'settings panel');
  check('settings panel opens', true);
  await cdp.screenshot('08_settings');
  await cdp.eval(`cc.find('Canvas/SettingsPanel/btn_close_settings').emit('click')`);
  await cdp.eval(`cc.find('Canvas/MainMenu/btn_howto').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/HowToPanel').active === true`, 5000, 'howto panel');
  check('howto panel opens', true);
  await cdp.screenshot('09_howto');
  await cdp.eval(`cc.find('Canvas/HowToPanel/btn_close_howto').emit('click')`);

  // ---- settings: music & vibration toggles ----
  const snd2 = await cdp.eval(`(() => {
    const before = { music: cc.AudioManager.musicEnabled };
    cc.find('Canvas/SettingsPanel/btn_music_toggle').emit('click');
    const musicOff = { music: cc.AudioManager.musicEnabled, stored: localStorage.getItem('blockudokuMusic') };
    cc.find('Canvas/SettingsPanel/btn_music_toggle').emit('click');
    const musicOn = cc.AudioManager.musicEnabled;
    cc.find('Canvas/SettingsPanel/btn_vibration_toggle').emit('click');
    const vibOff = localStorage.getItem('blockudokuVibration');
    cc.find('Canvas/SettingsPanel/btn_vibration_toggle').emit('click');
    const vibOn = localStorage.getItem('blockudokuVibration');
    return { before, musicOff, musicOn, vibOff, vibOn };
  })()`);
  check('music toggle persists + AudioManager sync', snd2.before.music === true && snd2.musicOff.music === false && snd2.musicOff.stored === '0' && snd2.musicOn === true, snd2);
  check('vibration toggle persists', snd2.vibOff === '0' && snd2.vibOn === '1', snd2);
  await cdp.eval(`cc.find('Canvas/SettingsPanel/btn_close_settings').emit('click')`);

  // ---- stats panel ----
  await cdp.eval(`cc.find('Canvas/MainMenu/btn_stats').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/StatsPanel').active === true`, 5000, 'stats panel');
  const stats = await cdp.eval(`(() => {
    const p = cc.find('Canvas/StatsPanel');
    return {
      best: p.getChildByName('bestValue').getComponent(cc.Label).string,
      games: p.getChildByName('gamesValue').getComponent(cc.Label).string,
      placements: p.getChildByName('placementsValue').getComponent(cc.Label).string,
      clears: p.getChildByName('clearsValue').getComponent(cc.Label).string,
    };
  })()`);
  check('stats panel shows records + per-game stats', parseInt(stats.best, 10) === scoreNow && parseInt(stats.games, 10) >= 1 && parseInt(stats.placements, 10) > 0, stats);
  await cdp.screenshot('10_stats');
  await cdp.eval(`cc.find('Canvas/StatsPanel/btn_close_stats').emit('click')`);

  // ---- daily challenge ----
  await cdp.eval(`cc.find('Canvas/MainMenu/btn_daily').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/DailyPanel').active === true`, 5000, 'daily panel');
  const dailyCal = await cdp.eval(`(() => {
    const p = cc.find('Canvas/DailyPanel');
    return {
      title: p.getChildByName('title').getComponent(cc.Label).string,
      hasDays: !!p.getChildByName('day_1'),
      hasPlay: !!p.getChildByName('btn_play_daily'),
    };
  })()`);
  check('daily panel: calendar + play today', dailyCal.title === 'DAILY CHALLENGE' && dailyCal.hasDays && dailyCal.hasPlay, dailyCal);
  await cdp.screenshot('11_daily');
  await cdp.eval(`cc.find('Canvas/DailyPanel/btn_play_daily').emit('click')`);
  await cdp.waitFor(`cc.find('Canvas/GameScene').active === true && window.__blockudoku.getState().mode === 'daily'`, 8000, 'daily game starts');
  const dailyStart = await cdp.eval(`window.__blockudoku.getState()`);
  check('daily mode starts with target', dailyStart.mode === 'daily' && dailyStart.dailyTarget >= 200 && dailyStart.score === 0, dailyStart);
  const targetNow = dailyStart.dailyTarget;

  // reach target -> TARGET REACHED + daily result saved with stars
  const dailyDone = await cdp.eval(`(() => {
    window.__blockudoku.setScore(${targetNow});
    window.__blockudoku.setTray(['Single', 'Single', 'Single']);
    const res = window.__blockudoku.placeAt(0, 0, 0);
    return { placed: res.placed, reached: window.__blockudoku.game.dailyTargetReached };
  })()`);
  check('daily target reached flags celebration', dailyDone.placed && dailyDone.reached, dailyDone);
  await cdp.eval(`window.__blockudoku.forceGameOver()`);
  await cdp.waitFor(`!!window.__blockudoku.getDaily()`, 8000, 'daily result saved');
  const dailyRes = await cdp.eval(`window.__blockudoku.getDaily()`);
  check('daily result saved with stars', dailyRes && dailyRes.score >= targetNow && dailyRes.stars >= 1, dailyRes);
  await cdp.waitFor(`!!cc.find('Canvas/GameScene/PopupLayer/gameOverPanel')`, 8000, 'daily game over panel');
  const dailyPanel = await cdp.eval(`(() => {
    const p = cc.find('Canvas/GameScene/PopupLayer/gameOverPanel');
    return {
      title: p.getChildByName('title').getComponent(cc.Label).string,
      target: p.getChildByName('target').getComponent(cc.Label).string,
      stars: [0, 1, 2].map((i) => p.getChildByName('star_' + i).opacity).join(','),
    };
  })()`);
  check('daily game over panel: title/target/stars', dailyPanel.title === 'DAILY CHALLENGE' && dailyPanel.target.indexOf('TARGET') === 0 && dailyPanel.stars.indexOf('255') === 0, dailyPanel);
  await cdp.screenshot('12_daily_result');

  // ---- undo / return block ----
  await cdp.eval(`window.__blockudoku.startNew()`);
  const undo = await cdp.eval(`(() => {
    window.__blockudoku.game._selectSlot(1);
    const selBefore = window.__blockudoku.game.selectedSlot;
    window.__blockudoku.undo();
    return { selBefore, selAfter: window.__blockudoku.game.selectedSlot };
  })()`);
  check('undo returns selected piece to tray', undo.selBefore === 1 && undo.selAfter === -1, undo);

  // ---- all clear ----
  const ac = await cdp.eval(`(() => {
    window.__blockudoku.startNew();
    const b = [];
    for (let r = 0; r < 9; r++) b.push(new Array(9).fill(1));
    b[8][8] = 0;
    window.__blockudoku.setBoard(b);
    window.__blockudoku.setTray(['Single', 'Square2x2', 'HorizontalLine3']);
    const res = window.__blockudoku.placeAt(0, 8, 8);
    return {
      placed: res.placed,
      allCleared: res.allCleared,
      combo: res.combo,
      comboScore: res.comboScore,
      groups: res.groups,
      empty: window.__blockudoku.getState().board.every((row) => row.every((v) => v === 0)),
    };
  })()`);
  check('all-clear: placement empties whole board', ac.placed && ac.allCleared && ac.empty && ac.groups >= 3, ac);
  check('all-clear awards combo bonus', ac.combo && ac.comboScore > 0, ac);
  await cdp.screenshot('13_all_clear');

  // ---- console errors ----
  const errs = cdp.consoleErrors();
  check('zero console errors', errs.length === 0, errs.map((e) => e.params && e.params.args ? e.params.args.map((a) => a.value || a.description).join(' ') : e.params.exceptionDetails));

  const failed = results.filter((r) => !r.ok);
  console.log('----');
  console.log(`TOTAL ${results.length} checks, ${results.length - failed.length} passed, ${failed.length} failed`);
  process.exit(failed.length > 0 ? 1 : 0);
}

main().catch((e) => { console.error('QA DRIVER ERROR:', e); process.exit(2); });
