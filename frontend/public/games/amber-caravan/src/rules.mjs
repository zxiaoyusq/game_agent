/**
 * 琥珀商路的纯规则：只接收、返回可序列化数据，不操作 DOM、计时器或随机数。
 * 棋子进度：-1 为营地，0..50 为外圈，51..55 为归航道，56 为终点。
 * 快局未解锁时走完整的 52 格外圈；外圈最后一格由 outerLast 单独标记，
 * 避免吃子解锁后把同在进度 51 的另一枚棋子瞬移进归航道。
 */
export const TRACK_LENGTH = 52;
export const HOME_ENTRY = 51;
export const FINISH = 56;
export const SAFE_CELLS = Object.freeze([0, 8, 13, 21, 26, 34, 39, 47]);
const MODES = new Set(['classic', 'quick']);

export function isSafeCell(cell) {
  return Number.isInteger(cell) && SAFE_CELLS.includes(cell);
}

/** 外圈棋子返回全局格号；营地、归航道和终点返回 null。 */
export function getTokenCell(playerId, progress, outerLast = false) {
  if (progress < 0 || (progress >= HOME_ENTRY && !outerLast)) return null;
  return (playerId * 13 + progress) % TRACK_LENGTH;
}

/** 配置在边界处完整校验，运行中只通过以下纯函数修改状态。 */
export function createGame({ mode = 'classic', players } = {}) {
  if (!MODES.has(mode)) throw new TypeError('未知对局模式');
  if (!Array.isArray(players) || players.length < 2 || players.length > 4) {
    throw new TypeError('对局需要两至四位玩家');
  }
  const ids = new Set();
  const participants = players.map((player) => {
    if (!Number.isInteger(player.id) || player.id < 0 || player.id > 3 || ids.has(player.id)) {
      throw new TypeError('玩家阵营必须是互不重复的 0 至 3');
    }
    if (!['human', 'ai'].includes(player.kind) || typeof player.name !== 'string' || !player.name.trim()) {
      throw new TypeError('玩家需要有效名称和控制方式');
    }
    ids.add(player.id);
    return {
      id: player.id,
      name: player.name.trim().slice(0, 40),
      kind: player.kind,
      tokens: mode === 'quick' ? [0, 0, -1, -1] : [-1, -1, -1, -1],
      outerLast: [false, false, false, false],
      homeUnlocked: mode === 'classic',
      captures: 0,
      finished: 0,
    };
  });
  return {
    version: 1,
    mode,
    players: participants,
    turn: 0,
    phase: 'roll',
    dice: null,
    sixStreak: 0,
    winner: null,
    message: `${participants[0].name}，掷骰开启商路`,
    history: [],
    stats: { rolls: 0, moves: 0, captures: 0 },
    lastAction: null,
  };
}

/** 用于读档边界；不修补坏档，避免把无效局面静默转成另一局。 */
export function validateGame(state) {
  if (!state || state.version !== 1 || !MODES.has(state.mode)) return false;
  if (!Array.isArray(state.players) || state.players.length < 2 || state.players.length > 4) return false;
  if (!Number.isInteger(state.turn) || state.turn < 0 || state.turn >= state.players.length) return false;
  if (!['roll', 'move', 'won'].includes(state.phase)) return false;
  if (state.dice !== null && (!Number.isInteger(state.dice) || state.dice < 1 || state.dice > 6)) return false;
  if (state.phase === 'move' && state.dice === null) return false;
  if (!Number.isInteger(state.sixStreak) || state.sixStreak < 0 || state.sixStreak > 2) return false;
  if (state.sixStreak > 0 && state.dice !== 6) return false;
  if (state.phase === 'move' && state.dice === 6 && state.sixStreak === 0) return false;
  if (typeof state.message !== 'string' || !Array.isArray(state.history) || state.history.length > 8 || state.history.some((entry) => typeof entry !== 'string')) return false;
  if (!state.stats || ['rolls', 'moves', 'captures'].some((key) => !Number.isSafeInteger(state.stats[key]) || state.stats[key] < 0)) return false;
  const ids = new Set();
  for (const player of state.players) {
    if (!player || typeof player !== 'object') return false;
    if (!Number.isInteger(player.id) || player.id < 0 || player.id > 3 || ids.has(player.id)) return false;
    if (typeof player.name !== 'string' || !player.name.trim() || player.name.length > 40 || !['human', 'ai'].includes(player.kind)) return false;
    ids.add(player.id);
    if (!Array.isArray(player.tokens) || player.tokens.length !== 4 || player.tokens.some((step) => !Number.isInteger(step) || step < -1 || step > FINISH)) return false;
    if (!Array.isArray(player.outerLast) || player.outerLast.length !== 4 || player.outerLast.some((flag, index) => typeof flag !== 'boolean' || (flag && player.tokens[index] !== 51))) return false;
    if (typeof player.homeUnlocked !== 'boolean' || !Number.isSafeInteger(player.captures) || player.captures < 0) return false;
    if (state.mode === 'classic' && (!player.homeUnlocked || player.outerLast.some(Boolean))) return false;
    if (state.mode === 'quick' && player.homeUnlocked !== (player.captures > 0)) return false;
    if (!player.homeUnlocked && player.tokens.some((step, index) => step > 51 || (step === 51 && !player.outerLast[index]))) return false;
    if (player.finished !== player.tokens.filter((step) => step === FINISH).length) return false;
  }
  const winners = state.players.filter((player) => player.finished >= (state.mode === 'quick' ? 1 : 4));
  if (state.phase === 'won') return winners.length === 1 && state.winner === winners[0].id && state.players[state.turn].id === state.winner;
  if (state.phase === 'move' && legalMoves(state).length === 0) return false;
  return state.winner === null && winners.length === 0;
}

/** 计算候选落点：快局门未打开时可以继续绕圈，不会卡死在门前。 */
function destination(player, tokenIndex, dice) {
  const from = player.tokens[tokenIndex];
  if (from === FINISH) return null;
  if (from === -1) return dice === 6 ? { progress: 0, outerLast: false } : null;
  if (!player.homeUnlocked || player.outerLast[tokenIndex]) {
    const progress = (from + dice) % TRACK_LENGTH;
    return { progress, outerLast: progress === 51 };
  }
  const progress = from + dice;
  return progress <= FINISH ? { progress, outerLast: false } : null;
}

/** 叠棋形成商队保护：不可落到敌方双子，经过该格仍然合法。 */
function enemiesAt(state, player, cell) {
  if (cell === null) return [];
  const enemies = [];
  for (const opponent of state.players) {
    if (opponent.id === player.id) continue;
    opponent.tokens.forEach((progress, tokenIndex) => {
      if (getTokenCell(opponent.id, progress, opponent.outerLast[tokenIndex]) === cell) {
        enemies.push({ playerId: opponent.id, tokenIndex });
      }
    });
  }
  return enemies;
}

export function legalMoves(state) {
  if (state.phase !== 'move' || !Number.isInteger(state.dice)) return [];
  const player = state.players[state.turn];
  return player.tokens.flatMap((_, tokenIndex) => {
    const target = destination(player, tokenIndex, state.dice);
    if (!target) return [];
    const cell = getTokenCell(player.id, target.progress, target.outerLast);
    if (!isSafeCell(cell) && enemiesAt(state, player, cell).length >= 2) return [];
    return [tokenIndex];
  });
}

function record(state, message) {
  state.message = message;
  state.history = [...state.history, message].slice(-8);
}

function nextPlayer(state) {
  state.turn = (state.turn + 1) % state.players.length;
  state.phase = 'roll';
  state.sixStreak = 0;
}

/** 随机值由调用者提供，确保 AI 与人类共用同一公平骰子。 */
export function rollDice(state, value) {
  if (!Number.isInteger(value) || value < 1 || value > 6) throw new RangeError('骰子必须是 1 至 6 的整数');
  if (state.phase !== 'roll') throw new Error('当前不能掷骰，请先完成选子或开始新局');
  const next = structuredClone(state);
  const player = next.players[next.turn];
  next.dice = value;
  next.stats.rolls += 1;
  next.sixStreak = value === 6 ? next.sixStreak + 1 : 0;
  next.lastAction = { type: 'roll', playerId: player.id, roll: value };
  if (next.sixStreak === 3) {
    nextPlayer(next);
    record(next, `${player.name} 连续三次掷出 6，休息一回合`);
    return next;
  }
  next.phase = 'move';
  if (legalMoves(next).length === 0) {
    nextPlayer(next);
    record(next, `${player.name} 掷出 ${value}，没有可走的商队`);
  } else {
    record(next, `${player.name} 掷出 ${value}，选择一支商队`);
  }
  return next;
}

export function moveToken(state, tokenIndex) {
  if (!Number.isInteger(tokenIndex) || !legalMoves(state).includes(tokenIndex)) return state;
  const next = structuredClone(state);
  const player = next.players[next.turn];
  const from = player.tokens[tokenIndex];
  const fromOuterLast = player.outerLast[tokenIndex];
  const target = destination(player, tokenIndex, next.dice);
  const cell = getTokenCell(player.id, target.progress, target.outerLast);
  const captured = isSafeCell(cell) ? [] : enemiesAt(next, player, cell);
  for (const hit of captured) {
    const opponent = next.players.find((candidate) => candidate.id === hit.playerId);
    opponent.tokens[hit.tokenIndex] = -1;
    opponent.outerLast[hit.tokenIndex] = false;
  }
  player.tokens[tokenIndex] = target.progress;
  player.outerLast[tokenIndex] = target.outerLast;
  player.captures += captured.length;
  if (captured.length > 0) player.homeUnlocked = true;
  const arrived = target.progress === FINISH;
  if (arrived) player.finished += 1;
  next.stats.moves += 1;
  next.stats.captures += captured.length;
  const bonus = next.dice === 6 || captured.length > 0 || arrived;
  next.lastAction = {
    type: 'move', playerId: player.id, tokenIndex, from, to: target.progress,
    fromOuterLast, outerLast: target.outerLast, captured, roll: next.dice, bonus,
  };
  const action = captured.length > 0 ? '截获对手商队，归航之门已开启' : arrived ? '一支商队成功归航' : from === -1 ? '商队出发' : `前进 ${next.dice} 格`;
  if (player.finished >= (next.mode === 'quick' ? 1 : 4)) {
    next.phase = 'won';
    next.winner = player.id;
    record(next, `${player.name} 赢得本次商路之旅！`);
  } else if (bonus) {
    next.phase = 'roll';
    record(next, `${player.name} ${action}，再掷一次`);
  } else {
    nextPlayer(next);
    record(next, `${player.name} ${action}`);
  }
  return next;
}
