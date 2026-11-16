import { drawSprite } from './assets.js';
import {
  colors,
  paints,
  labels,
  board,
  nativeScale,
  gridPoint,
  seats,
  cellSize,
} from './map.js';
import { legalMoves, cellId, homeCount } from './rules.js';
export function createRenderer(canvas, assets, geo) {
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const sprite = (path, x, y, scale) =>
    drawSprite(ctx, assets, `assets/${path}.png`, x, y, scale);
  const text = (value, x, y, size = 14, color = '#fff8db') => {
    ctx.fillStyle = color;
    ctx.font = `bold ${size}px system-ui`;
    ctx.textAlign = 'center';
    ctx.fillText(value, x, y);
  };
  function boardLayers() {
    const bg = assets.images.get('assets/background-edited.png');
    const scale = Math.max(360 / bg.width, 600 / bg.height);
    ctx.drawImage(
      bg,
      (360 - bg.width * scale) / 2,
      (600 - bg.height * scale) / 2,
      bg.width * scale,
      bg.height * scale,
    );
    const assembly = assets.manifest.board.source_assembly;
    const sourcePoint = ([x, y]) => ({
      x: 180 + (x - 0.639) * nativeScale,
      y: board.y + board.height / 2 - (y + 20) * nativeScale,
    });
    let p = sourcePoint(assembly.frame.position);
    sprite('board-frame', p.x, p.y, nativeScale);
    for (const camp of assembly.camps) {
      p = sourcePoint(camp.position);
      ctx.globalAlpha = camp.owner === 3 ? 250 / 255 : 1;
      sprite(`camp-${camp.color}`, p.x, p.y, nativeScale);
    }
    ctx.globalAlpha = 1;
    sprite('board-cross', 180, board.y + board.height / 2, nativeScale);
    const grid = assets.manifest.board.prototype_grid;
    for (const index of grid.stars) {
      p = gridPoint(...grid.public_path[index]);
      sprite('marker-star', p.x, p.y, nativeScale);
    }
    for (let owner = 0; owner < 4; owner++) {
      p = gridPoint(...grid.public_path[13 * owner]);
      sprite(`arrow-${colors[owner]}`, p.x, p.y, nativeScale);
    }
  }
  function pieceDraw(piece, position, scale = 1) {
    const image = assets.images.get(`assets/token-${colors[piece.owner]}.png`);
    const w = image.width * nativeScale * scale,
      h = image.height * nativeScale * scale;
    // 底座锚点与孔位对齐；原透明边缘和高光全部保留。
    ctx.drawImage(image, position.x - w * 0.5, position.y - h * 0.82, w, h);
  }
  function positionsFor(state, timeline, sample) {
    const list = state.pieces.map((piece) => ({ piece, ...geo.point(piece), scale: 1 }));
    if (timeline) {
      const event = timeline.after.lastEvent;
      const kind = sample.kind;
      if (['walk', 'impact'].includes(kind)) {
        for (const id of event.capturedIds) {
          const item = list.find((p) => p.piece.id === id);
          Object.assign(item, geo.point(timeline.before.pieces.find((p) => p.id === id)));
        }
      }
      for (const animated of sample.positions)
        Object.assign(
          list.find((p) => p.piece.id === animated.pieceId),
          animated,
        );
    }
    // 同格棋子使用小幅非重叠排布，编号入口解决选择歧义。
    const groups = new Map();
    for (const item of list) {
      if (sample?.positions.some((p) => p.pieceId === item.piece.id)) continue;
      if (item.piece.progress < 0) continue;
      const key = cellId(item.piece.owner, item.piece.progress);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(item);
    }
    for (const group of groups.values())
      if (group.length > 1)
        group.forEach((p, i) => {
          p.x += (i - (group.length - 1) / 2) * 5;
          p.y += (i % 2) * 3;
        });
    return list;
  }
  return {
    positions: [],
    render(state, timeline, sample, now, reduced, paused) {
      const dpr = canvas.width / 360;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, 360, 600);
      boardLayers();
      text('LUDO', 180, 29, 22, '#ffea9a');
      sprite('ui-settings', 332, 24, 0.46);
      if (!state) return;
      const legal = legalMoves(state);
      const pulse =
        reduced || paused ? 1 : 0.875 + 0.125 * Math.sin((now * Math.PI * 2) / 1400);
      const positions = positionsFor(state, timeline, sample);
      this.positions = positions.map((p) => ({
        pieceId: p.piece.id,
        x: p.x,
        y: p.y,
        width: 20,
        height: 31,
      }));
      for (const p of positions) {
        if (!timeline && legal.some((m) => m.pieceId === p.piece.id)) {
          ctx.globalAlpha = pulse;
          sprite('effect-selected', p.x, p.y, 0.48);
          ctx.globalAlpha = 1;
        }
        pieceDraw(p.piece, p, p.scale);
      }
      if (sample?.kind === 'walk') {
        const index = sample.positions[0].stepIndex;
        if (sample.positions[0].u < 0.7 && index > 0) {
          const point = sample.clip.path[index];
          ctx.globalAlpha = 1 - sample.positions[0].u;
          sprite('effect-landing', point.x, point.y, 0.5);
          ctx.globalAlpha = 1;
        }
      }
      for (const seat of state.seats) {
        const spot = seats[seat.owner];
        ctx.globalAlpha = seat.owner === state.currentPlayer ? pulse : 0.7;
        sprite(`hud-seat-${colors[seat.owner]}`, spot.x, spot.y, 0.39);
        ctx.globalAlpha = 1;
        sprite(seat.type === 'ai' ? 'hud-bot' : 'hud-human', spot.x, spot.y + 1, 0.34);
        text(
          `${labels[seat.owner]}${seat.type === 'ai' ? ' · 电脑' : ' · 玩家'} ${homeCount(state, seat.owner)}`,
          spot.x,
          spot.y + 40,
          10,
        );
        sprite(`hud-seat-${colors[seat.owner]}`, spot.diceX, spot.y, 0.39);
        const rolling = sample?.kind === 'dice' && sample.clip.actor === seat.owner;
        if (rolling)
          drawSprite(
            ctx,
            assets,
            assets.manifest.dice.sequence[sample.frameId].path,
            sample.x,
            sample.y,
            0.43,
          );
        else {
          const dice = seat.owner === state.lastEvent?.actor ? state.lastEvent.dice : 1;
          sprite(`dice-face-${dice}`, spot.diceX, spot.y, 0.43);
        }
      }
      if (sample?.kind === 'impact' || sample?.kind === 'home') {
        const point = sample.clip.point;
        const u = sample.fraction;
        ctx.globalAlpha = Math.sin(u * Math.PI) * 0.45;
        ctx.fillStyle = sample.kind === 'home' ? paints[sample.clip.owner] : '#fff';
        ctx.beginPath();
        ctx.arc(point.x, point.y, cellSize * (0.2 + 0.55 * u), 0, Math.PI * 2);
        ctx.fill();
        sprite('effect-landing', point.x, point.y, 0.6 + u * 0.3);
        ctx.globalAlpha = 1;
      }
      if (sample?.kind === 'victory') {
        const u = sample.fraction;
        ctx.save();
        ctx.beginPath();
        ctx.rect(12, 126, 336, 336);
        ctx.clip();
        for (let i = 0; i < 24; i++) {
          const angle = i * 2.39996,
            speed = 70 + ((i * 17) % 80);
          const x = 180 + Math.cos(angle) * speed * u;
          const y = 265 + Math.sin(angle) * speed * u + 90 * u * u;
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(angle + u * 6);
          ctx.globalAlpha = Math.min(1, (1 - u) / 0.3);
          ctx.fillStyle = paints[i % 4];
          ctx.fillRect(-2, -3, 4, 6);
          ctx.restore();
        }
        ctx.restore();
      }
      if (state.phase === 'finished' && !timeline) {
        ctx.fillStyle = '#31144aeb';
        ctx.fillRect(64, 235, 232, 116);
        text(`${labels[state.winner]}队获胜`, 180, 271, 24, '#ffed9b');
        sprite('ui-confirm', 180, 318, 0.72);
        text('再来一局', 180, 323, 16);
      }
      if (paused) text('已暂停', 180, 53, 13);
    },
  };
}
