/**
 * 琥珀商路棋盘：只从已提交的规则状态生成画面，不修改局面。
 * 静态航道与动态棋子共用同一套坐标，避免显示落点与实际规则分离。
 */
const CELL = 38;
const ORIGIN = 35;
const FINISH = 56;
// 容器只记住上次呈现状态，用于新动作动画；状态本身仍归规则层管理。
const renderedStates = new WeakMap();
const SAFE_CELLS = new Set([0, 8, 13, 21, 26, 34, 39, 47]);

export const PALETTE = Object.freeze([
  { color: '#168277', deep: '#11564e', light: '#d2e8de', name: '玉泉庭', symbol: '叶' },
  { color: '#d66b55', deep: '#974434', light: '#f3dace', name: '珊瑚庭', symbol: '花' },
  { color: '#c99429', deep: '#916516', light: '#f4e4b8', name: '日曜庭', symbol: '日' },
  { color: '#6468a6', deep: '#424875', light: '#dddff0', name: '星月庭', symbol: '月' },
]);

// 标准棋盘的52个外环格。四个相邻棋盘臂的角接处以细航线连接。
const GRID_TRACK = [
  [1, 6], [2, 6], [3, 6], [4, 6], [5, 6],
  [6, 5], [6, 4], [6, 3], [6, 2], [6, 1], [6, 0], [7, 0], [8, 0],
  [8, 1], [8, 2], [8, 3], [8, 4], [8, 5],
  [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6], [14, 7], [14, 8],
  [13, 8], [12, 8], [11, 8], [10, 8], [9, 8],
  [8, 9], [8, 10], [8, 11], [8, 12], [8, 13], [8, 14], [7, 14], [6, 14],
  [6, 13], [6, 12], [6, 11], [6, 10], [6, 9],
  [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8], [0, 7], [0, 6],
];

function cellPoint([x, y]) {
  return { x: ORIGIN + (x + 0.5) * CELL, y: ORIGIN + (y + 0.5) * CELL };
}

export const TRACK = Object.freeze(GRID_TRACK.map(point => Object.freeze(cellPoint(point))));
export const HOME_LANES = Object.freeze([
  [[1, 7], [2, 7], [3, 7], [4, 7], [5, 7]],
  [[7, 1], [7, 2], [7, 3], [7, 4], [7, 5]],
  [[13, 7], [12, 7], [11, 7], [10, 7], [9, 7]],
  [[7, 13], [7, 12], [7, 11], [7, 10], [7, 9]],
].map(lane => Object.freeze(lane.map(point => Object.freeze(cellPoint(point))))));

const COURTYARDS = [[42, 42], [378, 42], [378, 378], [42, 378]];
const TERMINALS = [{ x: 286, y: 320 }, { x: 320, y: 286 }, { x: 354, y: 320 }, { x: 320, y: 354 }];

/** 快局尚未吃子时，outerLast 将进度51解释成外环末格，而非归家道。 */
export function tokenPoint(playerId, progress, index = 0, outerLast = false) {
  if (!Number.isInteger(playerId) || playerId < 0 || playerId > 3) throw new RangeError('棋盘阵营编号无效');
  if (progress < 0) {
    const [x, y] = COURTYARDS[playerId];
    return { x: x + 68 + (index % 2) * 80, y: y + 110 + Math.floor(index / 2) * 65 };
  }
  if (progress === FINISH) {
    const point = TERMINALS[playerId];
    return { x: point.x + (index % 2 ? 7 : -7), y: point.y + (index < 2 ? -7 : 7) };
  }
  if (progress <= 50 || (progress === 51 && outerLast)) return { ...TRACK[(playerId * 13 + progress) % 52] };
  if (progress >= 51 && progress <= 55) return { ...HOME_LANES[playerId][progress - 51] };
  throw new RangeError('棋子进度无效');
}

function escapeText(value) {
  return String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function starPoints(x, y, outer, inner, count = 8) {
  return Array.from({ length: count * 2 }, (_, index) => {
    const angle = -Math.PI / 2 + Math.PI * index / count;
    const radius = index % 2 === 0 ? outer : inner;
    return `${(x + Math.cos(angle) * radius).toFixed(2)},${(y + Math.sin(angle) * radius).toFixed(2)}`;
  }).join(' ');
}

const STYLES = `
.ludo-board { display:block; width:100%; height:auto; overflow:visible; user-select:none; -webkit-tap-highlight-color:transparent; }
.ludo-board text { font-family:inherit; pointer-events:none; }
.ludo-board .board-token { outline:none; cursor:default; }
.ludo-board .board-token.is-legal { cursor:pointer; }
.ludo-board .token-glow { opacity:0; }
.ludo-board .is-legal .token-glow { opacity:1; animation:board-breathe 1.8s ease-in-out infinite; }
.ludo-board .board-token:focus-visible .focus-ring { opacity:1; }
.ludo-board .focus-ring { opacity:0; }
.ludo-board .board-token.is-legal:hover .token-figure { filter:brightness(1.14); }
.ludo-board .route-preview { pointer-events:none; }
@keyframes board-breathe { 50% { opacity:.4; } }
@media (prefers-reduced-motion:reduce) { .ludo-board .is-legal .token-glow { animation:none; } }
`;

function definitions() {
  return `<defs>
    <linearGradient id="board-ivory" x2="0.8" y2="1"><stop stop-color="#fffdf3"/><stop offset=".48" stop-color="#f7f0dc"/><stop offset="1" stop-color="#e2cf9f"/></linearGradient>
    <linearGradient id="board-brass" x2=".7" y2="1"><stop stop-color="#edce82"/><stop offset=".35" stop-color="#b28c42"/><stop offset=".7" stop-color="#f5df9f"/><stop offset="1" stop-color="#967037"/></linearGradient>
    <linearGradient id="board-tile" x2=".25" y2="1"><stop stop-color="#fffef8"/><stop offset="1" stop-color="#eee7d5"/></linearGradient>
    <radialGradient id="board-center"><stop stop-color="#fff9dc"/><stop offset="1" stop-color="#e6d39c"/></radialGradient>
    <filter id="board-shadow" x="-15%" y="-15%" width="130%" height="145%"><feDropShadow dx="0" dy="11" stdDeviation="9" flood-color="#443b25" flood-opacity=".2"/></filter>
    <filter id="token-shadow" x="-50%" y="-50%" width="200%" height="220%"><feDropShadow dx="0" dy="2" stdDeviation="1.8" flood-color="#40321d" flood-opacity=".3"/></filter>
    <pattern id="board-inlay" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M10 2 13 7 18 10 13 13 10 18 7 13 2 10 7 7Z" fill="none" stroke="#ac8742" stroke-width=".8" opacity=".26"/></pattern>
    ${PALETTE.map((palette, id) => `<linearGradient id="port-${id}" x2=".5" y2="1"><stop stop-color="${palette.light}"/><stop offset="1" stop-color="#faf3df"/></linearGradient>
      <linearGradient id="gem-${id}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${palette.light}"/><stop offset=".28" stop-color="${palette.color}"/><stop offset="1" stop-color="${palette.deep}"/></linearGradient>`).join('')}
  </defs>`;
}

function portMark(id, x, y) {
  const color = PALETTE[id].deep;
  const common = `stroke="${color}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"`;
  if (id === 0) return `<g ${common}><path d="M${x} ${y + 8}V${y - 7}m0 10c-12-2-11-11-11-11 12 0 11 11 11 11m0-3c11-1 11-10 11-10-11 0-11 10-11 10"/></g>`;
  if (id === 1) return `<g ${common}><path d="M${x} ${y - 12}Q${x + 12} ${y - 8} ${x + 9} ${y}Q${x + 12} ${y + 11} ${x} ${y + 10}Q${x - 12} ${y + 11} ${x - 9} ${y}Q${x - 12} ${y - 8} ${x} ${y - 12}Z"/><circle cx="${x}" cy="${y}" r="3"/></g>`;
  if (id === 2) return `<g ${common}><polygon points="${starPoints(x, y, 13, 8)}"/><circle cx="${x}" cy="${y}" r="4"/></g>`;
  return `<g ${common}><path d="M${x + 7} ${y - 11}A12 12 0 1 0 ${x + 11} ${y + 7}A11 11 0 0 1 ${x + 7} ${y - 11}Z"/><path d="M${x + 10} ${y - 7}v7m-3.5-3.5h7"/></g>`;
}

function renderCourtyard(id, player, current) {
  const [x, y] = COURTYARDS[id];
  const palette = PALETTE[id];
  const name = player ? player.name : palette.name;
  return `<g class="courtyard" data-player="${id}">
    <rect x="${x}" y="${y}" width="220" height="220" rx="22" fill="url(#port-${id})" stroke="${current ? palette.color : '#d3c4a2'}" stroke-width="${current ? 2.8 : 1}"/>
    <rect x="${x + 6}" y="${y + 6}" width="208" height="208" rx="17" fill="none" stroke="${palette.color}" opacity=".28"/>
    <path d="M${x + 22} ${y + 63}H${x + 198}" stroke="${palette.color}" opacity=".24"/>
    <path d="M${x + 14} ${y + 14}h22m-22 0v22m184-22h-22m22 0v22m0 148v22h-22m-148 0h-22v-22" fill="none" stroke="${palette.color}" stroke-width="1.6" opacity=".4"/>
    ${portMark(id, x + 39, y + 37)}
    <text x="${x + 62}" y="${y + 35}" font-size="14" fill="${palette.deep}" font-weight="700">${escapeText(name)}</text>
    <text x="${x + 62}" y="${y + 50}" font-size="8.5" letter-spacing="2" fill="${palette.deep}" opacity=".7">${['JADE', 'CORAL', 'AMBER', 'INDIGO'][id]} · ${player ? (player.kind === 'ai' ? '旅伴' : '旅人') : '庭院'}</text>
    ${Array.from({ length: 4 }, (_, index) => {
      const point = tokenPoint(id, -1, index);
      return `<circle cx="${point.x}" cy="${point.y}" r="24" fill="#fffaf0" fill-opacity=".7" stroke="${palette.color}" stroke-opacity=".18"/>
        <polygon points="${starPoints(point.x, point.y, 17, 13)}" fill="none" stroke="${palette.color}" stroke-opacity=".2" stroke-width=".7"/>`;
    }).join('')}
    ${!player ? `<text x="${x + 110}" y="${y + 145}" text-anchor="middle" font-size="10" fill="${palette.deep}" opacity=".6">静候旅人</text>` : ''}
  </g>`;
}

function renderTile(point, fill, stroke, mark = '') {
  return `<g><rect x="${point.x - 17.5}" y="${point.y - 17.5}" width="35" height="35" rx="7" fill="${fill}" stroke="${stroke}" stroke-width=".8"/>
    <path d="M${point.x - 11} ${point.y - 14}h22" stroke="#fff" stroke-opacity=".65" stroke-linecap="round"/>${mark}</g>`;
}

function renderTrack() {
  const cells = TRACK.map((point, index) => {
    const start = index % 13 === 0;
    const palette = PALETTE[Math.floor(index / 13)];
    const safe = SAFE_CELLS.has(index);
    const mark = safe ? `<polygon points="${starPoints(point.x, point.y, 9, 5.2)}" fill="${start ? palette.color : '#c2a15d'}" opacity="${start ? '.75' : '.65'}"/>` : '';
    return renderTile(point, start ? palette.light : 'url(#board-tile)', '#d2c6ad', mark);
  }).join('');
  const lanes = HOME_LANES.map((lane, id) => lane.map((point, index) => renderTile(point, PALETTE[id].light, PALETTE[id].color + '55',
    `<circle cx="${point.x}" cy="${point.y}" r="${index === 4 ? 4 : 2.2}" fill="${PALETTE[id].color}" opacity=".55"/>`)).join('')).join('');
  // 连续的底层线路让相邻棋盘臂的角接处也能明确跟踪。
  const route = [...TRACK, TRACK[0]].map(point => `${point.x},${point.y}`).join(' ');
  return `<polyline points="${route}" fill="none" stroke="#c8b887" stroke-width="3"/>${cells}${lanes}`;
}

/** 快局的闭门状态直接标在回家入口，避免仅靠文字说明隐藏规则。 */
function renderLockedGates(state) {
  if (state.mode !== 'quick') return '';
  return state.players.filter(player => !player.homeUnlocked).map(player => {
    const point = HOME_LANES[player.id][0];
    const color = PALETTE[player.id].deep;
    return `<g aria-hidden="true" transform="translate(${point.x} ${point.y})">
      <rect x="-7" y="-2" width="14" height="11" rx="3" fill="${color}" opacity=".7"/>
      <path d="M-4-2v-3a4 4 0 0 1 8 0v3" fill="none" stroke="${color}" stroke-width="2" opacity=".7"/>
      <circle cx="0" cy="3" r="1.5" fill="#fff6dc"/>
    </g>`;
  }).join('');
}

function renderCenter() {
  return `<g>
    <rect x="266" y="266" width="108" height="108" rx="20" fill="url(#board-center)" stroke="#b79857"/>
    ${[
      ['271,271 309,309 309,331 271,369', 0],
      ['271,271 309,309 331,309 369,271', 1],
      ['369,271 331,309 331,331 369,369', 2],
      ['271,369 309,331 331,331 369,369', 3],
    ].map(([points, id]) => `<polygon points="${points}" fill="${PALETTE[id].color}" opacity=".24"/>`).join('')}
    <polygon points="${starPoints(320, 320, 44, 32)}" fill="url(#board-brass)" stroke="#9e783a"/>
    <polygon points="${starPoints(320, 320, 34, 25)}" fill="#fff8e3" stroke="#c2a362"/>
    <circle cx="320" cy="320" r="22" fill="none" stroke="#d1b675"/>
    <path d="M320 296 325 315 344 320 325 325 320 344 315 325 296 320 315 315Z" fill="#af8842"/>
    <path d="M320 302 320 320 338 320 323 323Z" fill="#e7ce87"/>
    <circle cx="320" cy="320" r="4" fill="#fff4cc" stroke="#a67d38"/>
  </g>`;
}

/** 宝石、棱面、底座分别绘制，在小屏上仍可区分颜色和棋子编号。 */
function renderGem(id, index, finished) {
  const scale = finished ? 0.68 : 1;
  return `<g class="token-figure" transform="scale(${scale})" filter="url(#token-shadow)">
    <ellipse cx="0" cy="13" rx="16" ry="7" fill="#846333" opacity=".2"/>
    <path d="M-15 7Q-15 17 0 18Q15 17 15 7Z" fill="url(#board-brass)" stroke="#9d793d" stroke-width=".8"/>
    <ellipse cx="0" cy="7" rx="15" ry="6" fill="#f2d99c" stroke="#bd984e" stroke-width=".8"/>
    <path d="M0-21 12-11 11 5Q0 14-11 5L-12-11Z" fill="url(#gem-${id})" stroke="${PALETTE[id].deep}" stroke-width="1.1"/>
    <path d="M0-21-4-8-11 5M0-21 4-8 11 5M-12-11-4-8 4-8 12-11M-4-8 0 10 4-8" fill="none" stroke="#fffdf0" stroke-opacity=".27" stroke-width="1"/>
    <path d="M-8-12-1-17" stroke="#fff" stroke-opacity=".85" stroke-width="2" stroke-linecap="round"/>
    <text x="0" y="3.8" text-anchor="middle" font-family="Georgia,serif" font-size="11" font-weight="700" fill="#fffdf0" stroke="${PALETTE[id].deep}" stroke-width=".3" paint-order="stroke">${index + 1}</text>
  </g>`;
}

function positionedTokens(state) {
  const tokens = state.players.flatMap(player => player.tokens.map((progress, index) => ({
    player, index, progress,
    point: tokenPoint(player.id, progress, index, player.outerLast?.[index] ?? false),
  })));
  const occupancy = new Map();
  for (const token of tokens) {
    if (token.progress < 0 || token.progress === FINISH) continue;
    const key = `${token.point.x}:${token.point.y}`;
    const group = occupancy.get(key) ?? [];
    group.push(token);
    occupancy.set(key, group);
  }
  // 共格棋子轻微错位并缩小，不隐藏任何一枚；选择区另有完整尺寸按钮。
  for (const group of occupancy.values()) {
    if (group.length < 2) continue;
    group.forEach((token, index) => {
      const columns = group.length > 4 ? 3 : 2;
      const rows = Math.ceil(group.length / columns);
      token.point = { x: token.point.x + (index % columns - (columns - 1) / 2) * 13,
        y: token.point.y + (Math.floor(index / columns) - (rows - 1) / 2) * 12 };
      token.stackScale = group.length > 4 ? 0.5 : 0.7;
    });
  }
  return tokens;
}

/** 原子渲染：监听器绑定新节点，旧局事件随旧SVG移除，不保留异步回调。 */
export function renderBoard(container, state, { legalTokens = [], onToken = () => {}, onPreview = () => {} } = {}) {
  const previous = renderedStates.get(container);
  renderedStates.set(container, state);
  const current = state.players[state.turn];
  const allowed = new Set(state.phase === 'move' ? legalTokens : []);
  const tokens = positionedTokens(state);
  container.innerHTML = `<svg class="ludo-board" viewBox="0 0 640 640" role="group" aria-label="琥珀商路棋盘，点击发光的合法棋子移动">
    <style>${STYLES}</style>${definitions()}
    <rect x="20" y="24" width="600" height="600" rx="37" fill="#c3a063" filter="url(#board-shadow)"/>
    <rect x="17" y="14" width="606" height="606" rx="37" fill="url(#board-ivory)" stroke="#ad8a48" stroke-width="1.5"/>
    <rect x="24" y="21" width="592" height="592" rx="31" fill="url(#board-inlay)" stroke="#e8d5a6"/>
    <rect x="33" y="30" width="574" height="574" rx="23" fill="#f4ecd8" stroke="#bda46c"/>
    ${COURTYARDS.map((_, id) => renderCourtyard(id, state.players.find(player => player.id === id), current?.id === id && state.phase !== 'won')).join('')}
    ${renderTrack()}${renderLockedGates(state)}${renderCenter()}
    <g class="route-preview" aria-hidden="true"></g>
    ${tokens.map(token => {
      const legal = token.player.id === current?.id && allowed.has(token.index);
      const label = `${token.player.name}，${token.index + 1}号棋子，${token.progress < 0 ? '在庭院' : token.progress === FINISH ? '已归家' : '行进中'}${legal ? '，可移动' : ''}`;
      return `<g class="board-token${legal ? ' is-legal' : ''}" transform="translate(${token.point.x} ${token.point.y}) scale(${token.stackScale ?? 1})" data-token="${token.index}" data-owner="${token.player.id}" role="button" tabindex="${legal ? '0' : '-1'}" aria-label="${escapeText(label)}" aria-disabled="${!legal}">
        <circle class="token-glow" r="22" fill="#f9da67" fill-opacity=".32" stroke="#bd8830" stroke-width="1.6" stroke-dasharray="3 3"/>
        <circle class="focus-ring" r="25" fill="none" stroke="#173e46" stroke-width="2.5"/>
        <circle r="22" fill="transparent"/>
        ${renderGem(token.player.id, token.index, token.progress === FINISH)}
      </g>`;
    }).join('')}
  </svg>`;

  const preview = container.querySelector('.route-preview');
  const showPreview = index => {
    const progress = current.tokens[index];
    const path = [tokenPoint(current.id, progress, index, current.outerLast?.[index] ?? false)];
    let target = progress < 0 ? 0 : progress + state.dice;
    const staysOutside = !current.homeUnlocked || current.outerLast?.[index];
    if (staysOutside && target > 51) target %= 52;
    // 逐格预览沿规则线路走，快局未解锁时在外环闭合。
    if (progress >= 0) {
      for (let step = 1; step <= state.dice; step++) {
        const next = staysOutside ? (progress + step) % 52 : progress + step;
        if (next > FINISH) break;
        path.push(tokenPoint(current.id, next, index, staysOutside && next === 51));
      }
    } else path.push(tokenPoint(current.id, 0, index));
    const landing = path.at(-1);
    const color = PALETTE[current.id].deep;
    preview.innerHTML = `<polyline points="${path.map(point => `${point.x},${point.y}`).join(' ')}" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="5 4" stroke-linecap="round" opacity=".75"/>
      <circle cx="${landing.x}" cy="${landing.y}" r="16" fill="${PALETTE[current.id].light}" fill-opacity=".8" stroke="${color}" stroke-width="2"/>
      <path d="M${landing.x - 5} ${landing.y}h10m-5-5v10" stroke="${color}" stroke-width="2"/>`;
    onPreview(index, target);
  };
  const clearPreview = () => { preview.innerHTML = ''; onPreview(null, null); };
  animateMove(container, previous, state, tokens);
  container.querySelectorAll('.board-token.is-legal').forEach(element => {
    const index = Number(element.dataset.token);
    element.addEventListener('click', () => onToken(index));
    element.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onToken(index); }
    });
    element.addEventListener('pointerenter', () => showPreview(index));
    element.addEventListener('pointerleave', clearPreview);
    element.addEventListener('focus', () => showPreview(index));
    element.addEventListener('blur', clearPreview);
  });
}


/**
 * 规则先提交，表现再插值；无动画完成回调，因此离开对局或重绘不会复活旧动作。
 * 只对相邻的真实移动计数播放一次，读档和普通设置重绘均保持静止。
 */
function animateMove(container, previous, state, currentTokens) {
  if (!previous || state.stats?.moves !== previous.stats?.moves + 1 || state.lastAction?.type !== 'move') return;
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
  const action = state.lastAction;
  const player = previous.players.find(item => item.id === action.playerId);
  const token = currentTokens.find(item => item.player.id === action.playerId && item.index === action.tokenIndex);
  const node = container.querySelector(`[data-owner="${action.playerId}"][data-token="${action.tokenIndex}"]`);
  if (!player || !token || !node?.animate) return;
  const fromToken = positionedTokens(previous).find(item => item.player.id === action.playerId && item.index === action.tokenIndex);
  const points = [fromToken.point];
  if (action.from < 0) points.push(token.point);
  else {
    const staysOutside = !player.homeUnlocked || action.fromOuterLast;
    for (let step = 1; step <= action.roll; step++) {
      const progress = staysOutside ? (action.from + step) % 52 : action.from + step;
      points.push(tokenPoint(action.playerId, progress, action.tokenIndex, staysOutside && progress === 51));
    }
    points[points.length - 1] = token.point;
  }
  node.animate(points.map(point => ({ translate: `${point.x - token.point.x}px ${point.y - token.point.y}px` })), {
    duration: 380, easing: 'ease-in-out', fill: 'none',
  });
  // 吃子与抵达终点用轻量扩散环反馈；不引入位图特效或额外资源请求。
  if (action.captured.length > 0 || action.to === FINISH) {
    const ring = node.querySelector('.focus-ring');
    ring?.animate([{ opacity: 1, r: '17px', stroke: '#d4a53d' }, { opacity: 0, r: '40px', stroke: '#f1dc9b' }], {
      duration: 620, easing: 'ease-out', fill: 'none',
    });
  }
}
