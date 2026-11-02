export const SIZE = 6;
export const SHAPES = Object.freeze({
  dot: [[0, 0]],
  bar2: [[0, 0], [1, 0]],
  bar3: [[0, 0], [1, 0], [2, 0]],
  square: [[0, 0], [1, 0], [0, 1], [1, 1]],
  corner: [[0, 0], [0, 1], [1, 1]]
});

export function emptyBoard() {
  return Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
}

// 使用显式种子供块，不筛选可放形状，也不承诺随机局面可解。
export function drawBatch(seed) {
  let nextSeed = seed >>> 0;
  const keys = Object.keys(SHAPES);
  const pending = Array.from({ length: 3 }, () => {
    nextSeed = (Math.imul(nextSeed, 1664525) + 1013904223) >>> 0;
    return keys[Math.floor((nextSeed / 4294967296) * keys.length)];
  });
  return { pending, seed: nextSeed };
}

export function createGame(seed = 1) {
  return { board: emptyBoard(), ...drawBatch(seed), score: 0, status: 'playing' };
}

export function canPlace(board, shapeId, x, y) {
  const cells = SHAPES[shapeId];
  return Boolean(cells && Number.isInteger(x) && Number.isInteger(y) &&
    cells.every(([dx, dy]) => {
      const col = x + dx;
      const row = y + dy;
      return col >= 0 && col < SIZE && row >= 0 && row < SIZE && board[row][col] === 0;
    }));
}

export function isGameOver(board, pending) {
  return !pending.some(shapeId => {
    for (let y = 0; y < SIZE; y++) {
      for (let x = 0; x < SIZE; x++) {
        if (canPlace(board, shapeId, x, y)) return true;
      }
    }
    return false;
  });
}

export function place(state, slot, x, y) {
  const shapeId = state.pending[slot];
  if (state.status !== 'playing' || !Number.isInteger(slot) || slot < 0 ||
      slot >= state.pending.length || !canPlace(state.board, shapeId, x, y)) {
    return { ok: false, state };
  }
  const board = state.board.map(row => [...row]);
  for (const [dx, dy] of SHAPES[shapeId]) board[y + dy][x + dx] = 1;
  // 所有满行满列先从同一放置后棋盘识别，再统一清除交集。
  const rows = [];
  const cols = [];
  for (let i = 0; i < SIZE; i++) {
    if (board[i].every(cell => cell === 1)) rows.push(i);
    if (board.every(row => row[i] === 1)) cols.push(i);
  }
  const cleared = new Set();
  for (const row of rows) for (let col = 0; col < SIZE; col++) cleared.add(row * SIZE + col);
  for (const col of cols) for (let row = 0; row < SIZE; row++) cleared.add(row * SIZE + col);
  for (const index of cleared) board[Math.floor(index / SIZE)][index % SIZE] = 0;
  let pending = state.pending.filter((_, index) => index !== slot);
  let seed = state.seed;
  if (pending.length === 0) ({ pending, seed } = drawBatch(seed));
  const scoreDelta = SHAPES[shapeId].length + cleared.size * 10;
  const nextState = {
    board, pending, seed, score: state.score + scoreDelta,
    status: isGameOver(board, pending) ? 'over' : 'playing'
  };
  return { ok: true, state: nextState, rows, cols, clearedCount: cleared.size, scoreDelta };
}
