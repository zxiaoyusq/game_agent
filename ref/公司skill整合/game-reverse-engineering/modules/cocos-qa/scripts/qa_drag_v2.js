/* Drag-feel probe: real CDP touch events -> verify smoothing + snap + placement */
const http = require('http');

function getJson(url) {
  return new Promise((res, rej) => http.get(url, (r) => {
    let d = ''; r.on('data', (c) => d += c); r.on('end', () => res(JSON.parse(d)));
  }).on('error', rej));
}

async function main() {
  const list = await getJson('http://127.0.0.1:9224/json');
  const page = list.find((t) => t.type === 'page' && t.url.indexOf('index.html') >= 0);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => { ws.onopen = r; });
  let id = 0; const pending = new Map();
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id) {
      const p = pending.get(m.id);
      if (p) { pending.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); }
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const i = ++id; pending.set(i, { res, rej });
    ws.send(JSON.stringify({ id: i, method, params }));
  });
  const evalJs = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error('eval: ' + JSON.stringify(r.exceptionDetails));
    return r.result ? r.result.value : undefined;
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // design (origin centre, y up) -> CSS pixels (origin top-left) on a 720x1280 viewport
  const toView = (x, y) => ({ x: x + 360, y: 640 - y });

  await evalJs(`cc.find('Canvas/MainMenu/btn_new_game').emit('click')`);
  await sleep(600);
  console.log('scene active:', await evalJs(`cc.find('Canvas/GameScene').active && !!window.__blockudoku`));

  await send('Emulation.setTouchEmulationEnabled', { enabled: false, maxTouchPoints: 1 });

  const trayInfo = await evalJs(`(() => {
    const tray = cc.find('Canvas/GameScene/Tray');
    const s0 = cc.find('Canvas/GameScene/Tray/slot_0');
    const wp = tray.convertToWorldSpaceAR(cc.v2(s0.position.x, s0.position.y));
    const g = window.__blockudoku.game;
    return JSON.stringify({
      slotWorld: { x: wp.x, y: wp.y },
      blockColor: g._blockColor,
      tray0: g.tray[0],
    });
  })()`);
  const info = JSON.parse(trayInfo);
  console.log('tray info:', JSON.stringify(info));

  const start = toView(info.slotWorld.x, info.slotWorld.y);
  console.log('touchStart at view', JSON.stringify(start));
  await send('Input.dispatchMouseEvent', {
    type: 'mousePressed', x: start.x, y: start.y, button: 'left', clickCount: 1,
  });
  await sleep(120);
  const picked = await evalJs(`(() => {
    const g = window.__blockudoku.game;
    const dp = g._dragPiece;
    return JSON.stringify({
      active: g._dragActive,
      selected: g.selectedSlot,
      hasPiece: !!dp,
      piecePos: dp ? { x: Math.round(dp.position.x), y: Math.round(dp.position.y) } : null,
    });
  })()`);
  console.log('after touchStart:', picked);

  // drag to board cell (row 4, col 2): design pos (2-4)*38=-76, (4-4)*38=0 -> board world (0+ -76, 120+0)
  const target = toView(-76, 120);
  await send('Input.dispatchMouseEvent', {
    type: 'mouseMoved', x: target.x, y: target.y, button: 'left',
  });
  await sleep(60);
  await send('Input.dispatchMouseEvent', {
    type: 'mouseMoved', x: target.x + 10, y: target.y + 10, button: 'left',
  });
  await sleep(60);
  const mid = await evalJs(`(() => {
    const g = window.__blockudoku.game;
    const dp = g._dragPiece;
    return JSON.stringify({
      piecePos: dp ? { x: Math.round(dp.position.x), y: Math.round(dp.position.y) } : null,
      target: g._dragTarget ? { x: Math.round(g._dragTarget.x), y: Math.round(g._dragTarget.y) } : null,
      preview: g._dragPreview ? g._dragPreview.length : 0,
    });
  })()`);
  console.log('mid drag:', mid);

  // move back to exact cell and release
  await send('Input.dispatchMouseEvent', {
    type: 'mouseMoved', x: target.x, y: target.y, button: 'left',
  });
  await sleep(80);
  await send('Input.dispatchMouseEvent', {
    type: 'mouseReleased', x: target.x, y: target.y, button: 'left', clickCount: 1,
  });
  await sleep(400);
  const after = await evalJs(`(() => {
    const s = window.__blockudoku.getState();
    let placed = 0;
    for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) if (s.board[r][c]) placed++;
    return JSON.stringify({ score: s.score, placedCells: placed, selected: window.__blockudoku.game.selectedSlot });
  })()`);
  console.log('after release:', after);

  const ok = JSON.parse(after).placedCells > 0;
  console.log('DRAG PLACE ' + (ok ? 'OK' : 'FAIL'));
  ws.close();
  process.exit(ok ? 0 : 1);
}

main().catch((e) => { console.error('ERR', e); process.exit(2); });
